"""Host-managed transport bindings.

Candidate requests can name an endpoint, but network authority only exists when
an operator has registered the exact provider+endpoint pair in a local transport
configuration. No redirect following or ambient proxy credentials are allowed.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .probes import LocalReferenceSandbox
from .schemas import ProbeSpec


@dataclass(frozen=True, slots=True)
class HttpBridgeBinding:
    provider: str
    endpoint: str
    auth_env: str | None = None
    timeout_ms: int = 5000
    cost_per_request_usd: float = 0.0

    def validate(self) -> "HttpBridgeBinding":
        parsed = urlparse(self.endpoint)
        if parsed.username or parsed.password:
            raise ValueError("transport endpoint must not contain credentials")
        local = parsed.hostname in {"127.0.0.1", "::1", "localhost"}
        if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
            raise ValueError("HTTP transport must use HTTPS except for localhost")
        if not parsed.netloc:
            raise ValueError("transport endpoint must be absolute")
        if not 100 <= self.timeout_ms <= 30_000:
            raise ValueError("transport timeout must be between 100 and 30000 ms")
        if self.cost_per_request_usd < 0:
            raise ValueError("transport cost must be non-negative")
        if self.auth_env and not self.auth_env.replace("_", "").isalnum():
            raise ValueError("invalid auth environment variable name")
        return self


class HostTransportExecutor:
    """Execute installed reference transports or explicit HTTP bridge bindings."""

    def __init__(self):
        self.reference = LocalReferenceSandbox()
        self._last_latency_ms = 0.0
        self._last_cost_usd = 0.0
        self._last_provenance = "bounded-reference-interpreter"

    def execute(self, spec: ProbeSpec, transport, value):
        if isinstance(transport, str):
            output = self.reference.execute(spec, transport, value)
            self._last_latency_ms = 192.0
            self._last_cost_usd = 0.016
            self._last_provenance = "bounded-reference-interpreter"
            return output
        if not isinstance(transport, HttpBridgeBinding):
            raise ValueError("unrecognized host transport binding")
        binding = transport.validate()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "morphosis/0.3",
        }
        if binding.auth_env:
            secret = os.getenv(binding.auth_env)
            if not secret:
                raise ValueError("configured transport credential is unavailable")
            headers["Authorization"] = f"Bearer {secret}"

        envelope = {
            "schema": "morphosis.probe.v1",
            "probe": {
                "probe_id": spec.probe_id,
                "capability_id": spec.capability_id,
                "family": spec.family,
                "input_contract": spec.input_contract,
            },
            "input": value,
        }
        encoded = json.dumps(envelope, allow_nan=False).encode()
        if len(encoded) > spec.max_bytes:
            raise ValueError("transport request exceeds probe byte budget")

        started = time.perf_counter()
        timeout = min(spec.timeout_ms, binding.timeout_ms) / 1000
        with httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            response = client.post(binding.endpoint, headers=headers, content=encoded)
        self._last_latency_ms = (time.perf_counter() - started) * 1000
        self._last_cost_usd = binding.cost_per_request_usd
        self._last_provenance = "host-managed-http-bridge"

        if response.is_redirect:
            raise ValueError("transport redirect denied")
        response.raise_for_status()
        if len(response.content) > spec.max_bytes:
            raise ValueError("transport response exceeds probe byte budget")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("transport returned invalid JSON") from exc
        if not isinstance(payload, dict) or set(payload) != {"output"}:
            raise ValueError("transport response must contain exactly one output field")
        return payload["output"]

    def metrics(self, transport) -> tuple[float, float]:
        return self._last_latency_ms, self._last_cost_usd

    def provenance(self, transport) -> str:
        return self._last_provenance


def load_transport_bindings(path: str | Path) -> dict[tuple[str, str], HttpBridgeBinding]:
    raw = json.loads(Path(path).expanduser().read_text())
    if not isinstance(raw, dict) or set(raw) != {"bindings"}:
        raise ValueError("transport config must contain only a bindings array")
    rows = raw["bindings"]
    if not isinstance(rows, list):
        raise ValueError("transport bindings must be a list")
    bindings: dict[tuple[str, str], HttpBridgeBinding] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("transport binding must be an object")
        allowed = {
            "provider",
            "endpoint",
            "auth_env",
            "timeout_ms",
            "cost_per_request_usd",
        }
        if set(row) - allowed:
            raise ValueError("unsupported transport binding fields")
        if "provider" not in row or "endpoint" not in row:
            raise ValueError("transport provider and endpoint are required")
        binding = HttpBridgeBinding(**row).validate()
        key = (binding.provider, binding.endpoint)
        if key in bindings:
            raise ValueError("duplicate provider+endpoint transport binding")
        bindings[key] = binding
    return bindings
