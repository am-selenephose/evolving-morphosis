from datetime import datetime, timezone

import pytest

from morphosis.os.application import MorphosisApplication
from morphosis.os.discovery import BedrockDiscoverer


class FakeBedrock:
    def __init__(self):
        self.profile_calls = []

    def list_foundation_models(self):
        return {
            "modelSummaries": [
                {
                    "modelId": "vendor.alpha-v1:0",
                    "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/vendor.alpha-v1:0",
                    "modelName": "Vendor Alpha",
                    "providerName": "Vendor",
                    "inputModalities": ["TEXT", "IMAGE"],
                    "outputModalities": ["TEXT"],
                    "responseStreamingSupported": True,
                    "customizationsSupported": ["FINE_TUNING"],
                    "inferenceTypesSupported": ["ON_DEMAND"],
                    "modelLifecycle": {
                        "status": "ACTIVE",
                        "startOfLifeTime": datetime(2026, 1, 1, tzinfo=timezone.utc),
                    },
                }
            ]
        }

    def list_inference_profiles(self, **kwargs):
        self.profile_calls.append(kwargs)
        if "nextToken" not in kwargs:
            return {
                "inferenceProfileSummaries": [
                    {
                        "inferenceProfileId": "us.vendor.alpha-v1:0",
                        "inferenceProfileArn": "arn:aws:bedrock:us-east-1:123:inference-profile/us.vendor.alpha-v1:0",
                        "inferenceProfileName": "US Vendor Alpha",
                        "models": [
                            {
                                "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/vendor.alpha-v1:0"
                            }
                        ],
                        "status": "ACTIVE",
                        "type": "SYSTEM_DEFINED",
                    }
                ],
                "nextToken": "page-2",
            }
        assert kwargs["nextToken"] == "page-2"
        return {
            "inferenceProfileSummaries": [
                {
                    "inferenceProfileId": "app-profile-1",
                    "inferenceProfileArn": "arn:aws:bedrock:us-east-1:123:application-inference-profile/app-profile-1",
                    "inferenceProfileName": "App Profile",
                    "models": [
                        {
                            "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/vendor.alpha-v1:0"
                        }
                    ],
                    "status": "ACTIVE",
                    "type": "APPLICATION",
                }
            ]
        }


def discoverer():
    return BedrockDiscoverer(region_name="us-east-1", client=FakeBedrock())


def test_bedrock_discovery_normalizes_foundation_models_and_paginated_profiles():
    adapter = discoverer()
    candidates = adapter.discover()
    assert len(candidates) == 3
    foundation = candidates[0]
    assert foundation["provider"] == "bedrock"
    assert foundation["endpoint"] == "bedrock://us-east-1/foundation-model/vendor.alpha-v1:0"
    assert "bedrock.catalog.foundation_model.v1" in foundation["claims"]
    assert "bedrock.input.text.v1" in foundation["claims"]
    assert "bedrock.input.image.v1" in foundation["claims"]
    assert "bedrock.output.text.v1" in foundation["claims"]
    assert "bedrock.response.streaming.v1" in foundation["claims"]
    assert adapter.client.profile_calls == [
        {"maxResults": 1000},
        {"maxResults": 1000, "nextToken": "page-2"},
    ]


def test_catalog_discovery_imports_only_unknown_claims_and_never_evidence(tmp_path):
    adapter = discoverer()
    app = MorphosisApplication(
        tmp_path / "catalog.db",
        discoverers={"bedrock": adapter},
        clock=lambda: "2026-09-22T00:00:00Z",
    )
    imported = app.command("discover", {"provider": "bedrock"})
    assert len(imported) == 3
    snapshot = app.snapshot()
    assert len(snapshot["models"]) == 3
    assert snapshot["evidence"] == []
    assert snapshot["qualifications"] == []
    assert all(model["status"] == "UNKNOWN" for model in snapshot["models"])
    assert all(cap["status"] == "UNKNOWN" for cap in snapshot["capabilities"])

    claims = list(app.ledger.replay()["claims"].values())
    assert claims
    assert {claim["source"] for claim in claims} == {"provider-catalog-metadata"}

    result = app.command("evaluate", {"surface_id": imported[0]["surface_id"]})
    assert result["decision"]["outcome"] == "HOLD"
    assert result["probe_runs"] == []
    assert app.snapshot()["evidence"] == []


def test_discovery_is_host_installed_and_request_cannot_supply_provider_config(tmp_path):
    app = MorphosisApplication(tmp_path / "none.db", clock=lambda: "2026-09-22T00:00:00Z")
    with pytest.raises(ValueError, match="discoverer is not installed"):
        app.command("discover", {"provider": "bedrock"})
    with pytest.raises(ValueError, match="unsupported command fields"):
        app.command("discover", {"provider": "bedrock", "region": "eu-west-1"})
