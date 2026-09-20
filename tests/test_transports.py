import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from morphosis.os.application import MorphosisApplication
from morphosis.os.transports import (
    HostTransportExecutor,
    HttpBridgeBinding,
    load_transport_bindings,
)


class BridgeHandler(BaseHTTPRequestHandler):
    authorization = None

    def log_message(self, *_):
        return

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length))
        type(self).authorization = self.headers.get("Authorization")
        raw = json.dumps({"output": body["input"]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def test_host_managed_http_bridge_executes_exact_registered_surface(tmp_path, monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), BridgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.server_port}/probe"
    monkeypatch.setenv("MORPHOSIS_TEST_TOKEN", "bridge-secret")
    binding = HttpBridgeBinding(
        provider="external",
        endpoint=endpoint,
        auth_env="MORPHOSIS_TEST_TOKEN",
        cost_per_request_usd=0.001,
    )
    app = MorphosisApplication(
        tmp_path / "external.db",
        executor=HostTransportExecutor(),
        transports={("external", endpoint): binding},
        clock=lambda: "2026-09-20T00:00:00Z",
    )
    try:
        surface = app.command(
            "bootstrap",
            {
                "model": "external-test-model",
                "provider": "external",
                "endpoint": endpoint,
                "claims": ["core.tool_use.v1"],
            },
        )
        spec = app.command(
            "propose_probe",
            {
                "surface_id": surface["surface_id"],
                "capability_id": "core.tool_use.v1",
            },
        )
        run = app.command("run_probe", {"probe_id": spec["probe_id"]})
        assert run["passed"] is True
        assert run["provenance"] == "host-managed-http-bridge"
        assert run["cost_usd"] == 0.001
        assert run["latency_ms"] >= 0
        assert BridgeHandler.authorization == "Bearer bridge-secret"
    finally:
        app.close()
        server.shutdown()
        server.server_close()


def test_transport_loader_is_exact_and_rejects_unsafe_http(tmp_path):
    path = tmp_path / "transports.json"
    path.write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "provider": "vendor",
                        "endpoint": "https://bridge.example/v1/probe",
                        "timeout_ms": 2500,
                    }
                ]
            }
        )
    )
    bindings = load_transport_bindings(path)
    assert ("vendor", "https://bridge.example/v1/probe") in bindings

    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "provider": "vendor",
                        "endpoint": "http://bridge.example/v1/probe",
                    }
                ]
            }
        )
    )
    with pytest.raises(ValueError, match="HTTPS"):
        load_transport_bindings(bad)
