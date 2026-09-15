"""Deterministic opportunity normalization, evidence scoring, and approval gating."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


REQUIRED_FIELDS = {"id", "title", "source_url", "deadline", "reward_usd", "evidence"}
SENSITIVE_ACTIONS = {"apply", "publish", "submit", "spend", "send", "sign"}


def canonical_hash(value: Any) -> str:
    """Return a stable SHA-256 hash for a JSON-compatible value."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _parse_deadline(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _priority(item: dict[str, Any], now: datetime) -> tuple[int, float, str]:
    deadline = _parse_deadline(item["deadline"])
    hours = max(0.0, (deadline - now).total_seconds() / 3600)
    urgency = 3 if hours <= 48 else 2 if hours <= 168 else 1
    evidence_strength = min(3, len(item["evidence"]))
    reward = float(item["reward_usd"])
    score = urgency * 100 + evidence_strength * 10 + min(reward, 9999) / 1000
    return (-int(score * 1000), deadline.timestamp(), item["id"])


def build_action_queue(packet: dict[str, Any], now_iso: str) -> dict[str, Any]:
    """Convert an opportunity packet into a deduplicated, evidence-backed queue."""
    now = _parse_deadline(now_iso)
    seen: set[str] = set()
    queue: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    for raw in packet.get("opportunities", []):
        missing = sorted(REQUIRED_FIELDS - raw.keys())
        if missing:
            rejected.append({"id": str(raw.get("id", "unknown")), "reason": f"missing:{','.join(missing)}"})
            continue
        fingerprint = canonical_hash({"title": raw["title"].strip().lower(), "source_url": raw["source_url"]})
        if fingerprint in seen:
            rejected.append({"id": raw["id"], "reason": "duplicate"})
            continue
        seen.add(fingerprint)
        if _parse_deadline(raw["deadline"]) <= now:
            rejected.append({"id": raw["id"], "reason": "expired"})
            continue
        requested = [str(action).lower() for action in raw.get("requested_actions", ["review"])]
        gated = sorted(set(requested) & SENSITIVE_ACTIONS)
        queue.append(
            {
                "id": raw["id"],
                "title": raw["title"],
                "source_url": raw["source_url"],
                "deadline": raw["deadline"],
                "reward_usd": float(raw["reward_usd"]),
                "evidence": raw["evidence"],
                "evidence_hash": canonical_hash(raw["evidence"]),
                "requested_actions": requested,
                "approval_required": bool(gated),
                "approval_reasons": [f"human approval required before {action}" for action in gated],
                "safe_next_step": raw.get("safe_next_step", "Review evidence and decide whether to proceed."),
            }
        )

    queue.sort(key=lambda item: _priority(item, now))
    result = {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "source_packet_hash": canonical_hash(packet),
        "queue": queue,
        "rejected": sorted(rejected, key=lambda item: item["id"]),
        "policy": {"default": "deny consequential actions", "approval_gate": sorted(SENSITIVE_ACTIONS)},
    }
    result["result_hash"] = canonical_hash(result)
    return result


def render_markdown(queue: dict[str, Any]) -> str:
    """Render the action queue as a human-reviewable Markdown report."""
    lines = ["# Evolving Morphosis report", "", f"Generated: {queue['generated_at']}", f"Result hash: `{queue['result_hash']}`", ""]
    for index, item in enumerate(queue["queue"], 1):
        gate = "HUMAN APPROVAL REQUIRED" if item["approval_required"] else "SAFE TO PREPARE"
        lines.extend(
            [
                f"## {index}. {item['title']}",
                "",
                f"- Status: **{gate}**",
                f"- Deadline: {item['deadline']}",
                f"- Listed reward: USD {item['reward_usd']:,.2f}",
                f"- Source: {item['source_url']}",
                f"- Evidence hash: `{item['evidence_hash']}`",
                f"- Safe next step: {item['safe_next_step']}",
            ]
        )
        for reason in item["approval_reasons"]:
            lines.append(f"- Gate: {reason}")
        lines.append("")
    if queue["rejected"]:
        lines.extend(["## Rejected records", ""])
        lines.extend(f"- `{item['id']}`: {item['reason']}" for item in queue["rejected"])
        lines.append("")
    return "\n".join(lines)

