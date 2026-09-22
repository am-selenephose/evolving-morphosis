import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from morphosis.os.application import MorphosisApplication
from morphosis.os.transports import (
    BedrockConverseBinding,
    HostTransportExecutor,
    HttpBridgeBinding,
    load_transport_bindings,
)
from morphosis.os.schemas import WorkloadContract


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


class FakeBedrockRuntime:
    def __init__(self):
        self.calls = []

    @staticmethod
    def _apply_patch(value):
        def one(item):
            document = json.loads(json.dumps(item["document"]))
            for patch in item["patch"]:
                document[patch["key"]] = patch["value"]
            return document
        return [one(item) for item in value] if isinstance(value, list) else one(value)

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        request = json.loads(kwargs["messages"][0]["content"][0]["text"])
        if request["contract"] == "json-patch-v1":
            output = self._apply_patch(request["input"])
        elif request["contract"] == "json-tool-v1":
            output = request["input"]
        else:
            raise AssertionError("unexpected semantic contract")
        return {"output": {"message": {"content": [{"text": json.dumps(output, ensure_ascii=False)}]}}}


class OneBedrockCandidate:
    endpoint = "bedrock://us-east-1/foundation-model/vendor.alpha-v1:0"

    def discover(self):
        return [{
            "model": "vendor.alpha-v1:0",
            "provider": "bedrock",
            "endpoint": self.endpoint,
            "claims": ["bedrock.catalog.foundation_model.v1"],
            "api_surface": "bedrock-control-plane-catalog-v1",
            "model_version": "vendor.alpha-v1:0",
            "inference_config": (("catalog_kind", "foundation-model"),),
            "tool_protocol": "unbound",
            "catalog_metadata": {"lifecycle_status": "ACTIVE"},
        }]


def test_bedrock_binding_is_exact_host_authority_and_requires_cost_estimate(tmp_path):
    path = tmp_path / "bedrock.json"
    path.write_text(json.dumps({"bindings": [{
        "kind": "bedrock-converse",
        "provider": "bedrock",
        "endpoint": OneBedrockCandidate.endpoint,
        "timeout_ms": 2500,
        "cost_per_request_usd": 0.001,
        "max_tokens": 4096,
    }]}))
    bindings = load_transport_bindings(path)
    binding = bindings[("bedrock", OneBedrockCandidate.endpoint)]
    assert isinstance(binding, BedrockConverseBinding)
    assert binding.region_name == "us-east-1"
    assert binding.model_id == "vendor.alpha-v1:0"

    missing_cost = tmp_path / "missing-cost.json"
    missing_cost.write_text(json.dumps({"bindings": [{
        "kind": "bedrock-converse",
        "provider": "bedrock",
        "endpoint": OneBedrockCandidate.endpoint,
    }]}))
    with pytest.raises(ValueError, match="cost estimate"):
        load_transport_bindings(missing_cost)


def test_bedrock_converse_end_to_end_requires_claim_then_independent_evidence(tmp_path):
    runtime = FakeBedrockRuntime()
    candidate = OneBedrockCandidate()
    binding = BedrockConverseBinding(
        provider="bedrock",
        endpoint=candidate.endpoint,
        timeout_ms=2500,
        cost_per_request_usd=0.001,
        max_tokens=4096,
    )
    executor = HostTransportExecutor(
        bedrock_client_factory=lambda region, timeout: runtime
    )
    app = MorphosisApplication(
        tmp_path / "bedrock.db",
        contract=WorkloadContract(allowed_providers=("bedrock",)),
        discoverers={"bedrock": candidate},
        transports={("bedrock", candidate.endpoint): binding},
        executor=executor,
        clock=lambda: "2026-09-22T00:00:00Z",
    )
    try:
        surface = app.command("discover", {"provider": "bedrock"})[0]
        assert app.command("evaluate", {"surface_id": surface["surface_id"]})["decision"]["outcome"] == "HOLD"

        claim = app.command("claim", {
            "surface_id": surface["surface_id"],
            "capability_id": "future.semantic_patch.v1",
        })
        assert claim["source"] == "request-proposed"

        result = app.command("evaluate", {"surface_id": surface["surface_id"]})
        assert result["decision"]["outcome"] == "PROMOTE_TO_SHADOW"
        assert len(result["probe_runs"]) == 3
        assert all(run["passed"] for run in result["probe_runs"])
        assert all(run["provenance"] == "host-managed-bedrock-converse" for run in result["probe_runs"])
        assert result["adaptation_verification"]["passed"] is True
        assert len(runtime.calls) == 6
        assert {call["modelId"] for call in runtime.calls} == {"vendor.alpha-v1:0"}
        assert all(call["inferenceConfig"]["temperature"] == 0 for call in runtime.calls)
    finally:
        app.close()
