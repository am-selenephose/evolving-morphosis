"""Runtime configuration for the Morphosis service.

Configuration is explicit, environment-aware, and intentionally small. Domain
policy remains in morphosis.os.kernel; these settings only control the service
process and local persistence.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    value = default if raw is None else int(raw)
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True, slots=True)
class ServiceSettings:
    host: str = "127.0.0.1"
    port: int = 8765
    db_path: str = "morphosis.sqlite"
    site_dir: str | None = None
    transport_config: str | None = None
    seed_reference: bool = False
    log_level: str = "info"
    request_max_bytes: int = 131_072
    sse_heartbeat_seconds: int = 10
    allowed_origins: tuple[str, ...] = ()
    expose_docs: bool = True

    @classmethod
    def from_env(cls) -> "ServiceSettings":
        origins = tuple(
            value.strip()
            for value in os.getenv("MORPHOSIS_ALLOWED_ORIGINS", "").split(",")
            if value.strip()
        )
        docs = not _bool("MORPHOSIS_DISABLE_DOCS", False)
        return cls(
            host=os.getenv("MORPHOSIS_HOST", "127.0.0.1"),
            port=_int("MORPHOSIS_PORT", 8765, minimum=1, maximum=65535),
            db_path=os.getenv("MORPHOSIS_DB", "morphosis.sqlite"),
            site_dir=os.getenv("MORPHOSIS_SITE_DIR") or None,
            transport_config=os.getenv("MORPHOSIS_TRANSPORTS_FILE") or None,
            seed_reference=_bool("MORPHOSIS_SEED_REFERENCE", False),
            log_level=os.getenv("MORPHOSIS_LOG_LEVEL", "info").lower(),
            request_max_bytes=_int(
                "MORPHOSIS_REQUEST_MAX_BYTES",
                131_072,
                minimum=1_024,
                maximum=4_194_304,
            ),
            sse_heartbeat_seconds=_int(
                "MORPHOSIS_SSE_HEARTBEAT_SECONDS",
                10,
                minimum=1,
                maximum=120,
            ),
            allowed_origins=origins,
            expose_docs=docs,
        ).validate()

    def validate(self) -> "ServiceSettings":
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if self.log_level not in {"critical", "error", "warning", "info", "debug"}:
            raise ValueError("unsupported log level")
        if "*" in self.allowed_origins:
            raise ValueError("wildcard CORS origin is intentionally forbidden")
        if self.site_dir is not None and not Path(self.site_dir).expanduser().exists():
            raise ValueError("configured site directory does not exist")
        if self.transport_config is not None and not Path(self.transport_config).expanduser().is_file():
            raise ValueError("configured transport file does not exist")
        return self

    def with_overrides(self, **values) -> "ServiceSettings":
        return replace(self, **{k: v for k, v in values.items() if v is not None}).validate()

    def resolved_site_dir(self) -> Path:
        if self.site_dir:
            return Path(self.site_dir).expanduser().resolve()
        return Path(__file__).resolve().parents[3] / "site"
