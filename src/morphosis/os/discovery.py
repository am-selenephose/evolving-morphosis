"""Host-owned provider discovery adapters.

Discovery imports provider catalog metadata as UNVERIFIED candidate claims only.
It never creates empirical evidence, binds credentials, or grants routing authority.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any


def _slug(value: object) -> str:
    text = re.sub(r"[^a-z0-9_-]+", "_", str(value or "").strip().lower())
    return text.strip("_") or "unknown"


def _iso(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _foundation_claims(summary: dict[str, Any]) -> tuple[str, ...]:
    claims = {"bedrock.catalog.foundation_model.v1"}
    for value in summary.get("inputModalities") or ():
        claims.add(f"bedrock.input.{_slug(value)}.v1")
    for value in summary.get("outputModalities") or ():
        claims.add(f"bedrock.output.{_slug(value)}.v1")
    for value in summary.get("inferenceTypesSupported") or ():
        claims.add(f"bedrock.inference.{_slug(value)}.v1")
    for value in summary.get("customizationsSupported") or ():
        claims.add(f"bedrock.customization.{_slug(value)}.v1")
    if summary.get("responseStreamingSupported") is True:
        claims.add("bedrock.response.streaming.v1")
    return tuple(sorted(claims))


def _profile_claims(summary: dict[str, Any]) -> tuple[str, ...]:
    claims = {"bedrock.catalog.inference_profile.v1"}
    profile_type = summary.get("type")
    if profile_type:
        claims.add(f"bedrock.profile.{_slug(profile_type)}.v1")
    if summary.get("status"):
        claims.add(f"bedrock.profile.status.{_slug(summary['status'])}.v1")
    return tuple(sorted(claims))


@dataclass(slots=True)
class BedrockDiscoverer:
    """Read-only Amazon Bedrock control-plane discovery.

    The caller owns AWS credentials and IAM. This class only uses the Bedrock
    control-plane client and returns normalized candidate metadata.
    """

    region_name: str | None = None
    client: Any = None
    include_inference_profiles: bool = True

    provider: str = "bedrock"

    def __post_init__(self) -> None:
        self.region_name = (
            self.region_name
            or os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
        )
        if not self.region_name:
            raise ValueError("Bedrock discovery requires an explicit AWS region")
        if self.client is None:
            import boto3
            self.client = boto3.client("bedrock", region_name=self.region_name)

    def _foundation_models(self) -> list[dict[str, Any]]:
        response = self.client.list_foundation_models()
        return list(response.get("modelSummaries") or ())

    def _inference_profiles(self) -> list[dict[str, Any]]:
        if not self.include_inference_profiles:
            return []
        profiles: list[dict[str, Any]] = []
        token: str | None = None
        while True:
            params: dict[str, Any] = {"maxResults": 1000}
            if token:
                params["nextToken"] = token
            response = self.client.list_inference_profiles(**params)
            profiles.extend(response.get("inferenceProfileSummaries") or ())
            token = response.get("nextToken")
            if not token:
                return profiles

    def discover(self) -> list[dict[str, Any]]:
        region = self.region_name
        discovered: list[dict[str, Any]] = []
        for item in self._foundation_models():
            model_id = item.get("modelId")
            if not model_id:
                continue
            lifecycle = item.get("modelLifecycle") or {}
            config = (
                ("catalog_kind", "foundation-model"),
                ("model_arn", str(item.get("modelArn") or "")),
            )
            metadata = {
                "model_name": str(item.get("modelName") or ""),
                "provider_name": str(item.get("providerName") or ""),
                "lifecycle_status": str(lifecycle.get("status") or ""),
                "start_of_life": _iso(lifecycle.get("startOfLifeTime")),
                "legacy_time": _iso(lifecycle.get("legacyTime")),
                "end_of_life": _iso(lifecycle.get("endOfLifeTime")),
                "public_extended_access_time": _iso(lifecycle.get("publicExtendedAccessTime")),
                "input_modalities": list(item.get("inputModalities") or ()),
                "output_modalities": list(item.get("outputModalities") or ()),
                "inference_types": list(item.get("inferenceTypesSupported") or ()),
                "customizations": list(item.get("customizationsSupported") or ()),
                "streaming": bool(item.get("responseStreamingSupported")),
            }
            discovered.append(
                {
                    "model": str(model_id),
                    "provider": self.provider,
                    "endpoint": f"bedrock://{region}/foundation-model/{model_id}",
                    "claims": _foundation_claims(item),
                    "api_surface": "bedrock-control-plane-catalog-v1",
                    "model_version": str(model_id),
                    "inference_config": tuple((k, v) for k, v in config if v),
                    "tool_protocol": "unbound",
                    "catalog_metadata": metadata,
                }
            )
        for item in self._inference_profiles():
            profile_id = item.get("inferenceProfileId")
            if not profile_id:
                continue
            models = ",".join(
                str(model.get("modelArn") or "")
                for model in (item.get("models") or ())
                if model.get("modelArn")
            )
            config = (
                ("catalog_kind", "inference-profile"),
                ("profile_arn", str(item.get("inferenceProfileArn") or "")),
                ("profile_type", str(item.get("type") or "")),
                ("models", models),
            )
            metadata = {
                "profile_name": str(item.get("inferenceProfileName") or ""),
                "profile_status": str(item.get("status") or ""),
                "profile_type": str(item.get("type") or ""),
                "models": [str(model.get("modelArn") or "") for model in (item.get("models") or ()) if model.get("modelArn")],
                "created_at": _iso(item.get("createdAt")),
                "updated_at": _iso(item.get("updatedAt")),
            }
            discovered.append(
                {
                    "model": str(profile_id),
                    "provider": self.provider,
                    "endpoint": f"bedrock://{region}/inference-profile/{profile_id}",
                    "claims": _profile_claims(item),
                    "api_surface": "bedrock-control-plane-catalog-v1",
                    "model_version": str(profile_id),
                    "inference_config": tuple((k, v) for k, v in config if v),
                    "tool_protocol": "unbound",
                    "catalog_metadata": metadata,
                }
            )
        return discovered
