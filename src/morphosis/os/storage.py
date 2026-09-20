"""SQLite command transactions, content-addressed artifacts, and hash-chained events."""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

from .schemas import DomainEvent, digest

SCHEMA_VERSION = 1


class ArtifactStore(Protocol):
    def put(self, value: dict) -> str: ...
    def get(self, artifact_hash: str) -> dict: ...


class EvolutionLedger(Protocol):
    def events(self, after: int = 0) -> list: ...
    def verify(self) -> bool: ...


class EventBus(Protocol):
    def events(self, after: int = 0) -> list: ...


class StateStore(Protocol):
    def replay(self) -> dict: ...


class SQLiteLedger:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ":memory:":
            target = Path(self.path).expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)
            self.path = str(target)
        self.connection = sqlite3.connect(
            self.path,
            check_same_thread=False,
            isolation_level=None,
            timeout=5.0,
        )
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA busy_timeout=5000")
        self.connection.execute("PRAGMA wal_autocheckpoint=1000")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events(
                sequence INTEGER PRIMARY KEY,
                body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS artifacts(
                hash TEXT PRIMARY KEY,
                body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS commands(
                id TEXT PRIMARY KEY,
                input_hash TEXT NOT NULL,
                result TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_commands_input_hash ON commands(input_hash);
            """
        )
        self.connection.execute(
            "INSERT OR IGNORE INTO metadata(key,value) VALUES('schema_version',?)",
            (str(SCHEMA_VERSION),),
        )
        version = int(
            self.connection.execute(
                "SELECT value FROM metadata WHERE key='schema_version'"
            ).fetchone()[0]
        )
        if version != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported ledger schema version {version}; expected {SCHEMA_VERSION}"
            )
        self.lock = threading.RLock()
        self._closed = False

    def _ensure_open(self):
        if self._closed:
            raise RuntimeError("ledger is closed")

    @contextmanager
    def transaction(self):
        self._ensure_open()
        with self.lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                yield
                self.connection.execute("COMMIT")
            except BaseException:
                self.connection.execute("ROLLBACK")
                raise

    def put(self, value):
        self._ensure_open()
        key = digest(value)
        body = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        self.connection.execute(
            "INSERT OR IGNORE INTO artifacts VALUES(?,?)",
            (key, body),
        )
        return key

    def get(self, key):
        self._ensure_open()
        row = self.connection.execute(
            "SELECT body FROM artifacts WHERE hash=?",
            (key,),
        ).fetchone()
        if not row:
            raise ValueError("artifact not found")
        value = json.loads(row[0])
        if digest(value) != key:
            raise ValueError("artifact tampering")
        return value

    def events(self, after=0):
        self._ensure_open()
        if after < 0:
            raise ValueError("event cursor must be non-negative")
        with self.lock:
            return [
                json.loads(row[0])
                for row in self.connection.execute(
                    "SELECT body FROM events WHERE sequence>? ORDER BY sequence",
                    (after,),
                )
            ]

    def verify(self):
        self._ensure_open()
        try:
            previous = "0" * 64
            for sequence, event in enumerate(self.events(), 1):
                DomainEvent.model_validate(event)
                if event["sequence"] != sequence or event["previous_hash"] != previous:
                    return False
                body = {k: v for k, v in event.items() if k != "event_hash"}
                if digest(body) != event["event_hash"]:
                    return False
                for key in event["evidence"]:
                    self.get(key)
                previous = event["event_hash"]
            return True
        except (ValueError, KeyError, TypeError):
            return False

    def append(self, event_type, aggregate_id, payload, now, correlation, evidence=()):
        self._ensure_open()
        row = self.connection.execute(
            "SELECT sequence,body FROM events ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        sequence = row[0] + 1 if row else 1
        prior = json.loads(row[1]) if row else None
        body = dict(
            event_type=event_type,
            timestamp=now,
            aggregate_id=aggregate_id,
            correlation_id=correlation,
            causation_id=prior["event_id"] if prior else None,
            schema_version="3.0",
            sequence=sequence,
            payload=payload,
            evidence=list(evidence),
            previous_hash=prior["event_hash"] if prior else "0" * 64,
        )
        body["event_id"] = digest(body)
        body["event_hash"] = digest(body)
        event = DomainEvent(**body).json_value()
        self.connection.execute(
            "INSERT INTO events VALUES(?,?)",
            (
                sequence,
                json.dumps(
                    event,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
        )
        return event

    def replay(self):
        self._ensure_open()
        if not self.verify():
            raise ValueError("ledger integrity verification failed")
        state = {}
        for event in self.events():
            mutation = event["payload"].get("mutation")
            if mutation:
                state.setdefault(mutation["collection"], {})[mutation["id"]] = mutation[
                    "value"
                ]
        return state

    def health(self) -> dict:
        if self._closed:
            return {
                "ready": False,
                "integrity": "closed",
                "schema_version": SCHEMA_VERSION,
                "error": "ledger is closed",
            }
        try:
            with self.lock:
                quick = self.connection.execute("PRAGMA quick_check").fetchone()[0]
                counts = {
                    "events": self.connection.execute(
                        "SELECT COUNT(*) FROM events"
                    ).fetchone()[0],
                    "artifacts": self.connection.execute(
                        "SELECT COUNT(*) FROM artifacts"
                    ).fetchone()[0],
                    "commands": self.connection.execute(
                        "SELECT COUNT(*) FROM commands"
                    ).fetchone()[0],
                }
                schema_version = int(
                    self.connection.execute(
                        "SELECT value FROM metadata WHERE key='schema_version'"
                    ).fetchone()[0]
                )
            integrity = "ok" if quick == "ok" and self.verify() else "failed"
            return {
                "ready": integrity == "ok",
                "integrity": integrity,
                "schema_version": schema_version,
                "path": self.path,
                **counts,
            }
        except (sqlite3.Error, ValueError, RuntimeError) as exc:
            return {
                "ready": False,
                "integrity": "failed",
                "schema_version": SCHEMA_VERSION,
                "path": self.path,
                "error": str(exc),
            }

    def close(self) -> None:
        if self._closed:
            return
        with self.lock:
            if self.path != ":memory:":
                try:
                    self.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                except sqlite3.Error:
                    pass
            self.connection.close()
            self._closed = True
