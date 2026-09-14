"""Credential-free Strands models used to prove Morphosis tool loops."""
from __future__ import annotations

import ast
import json
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any

from pydantic import BaseModel
from strands.models import Model
from strands.types.content import Messages, SystemContentBlock
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolChoice, ToolSpec


def _decode_tool_result(block: dict[str, Any]) -> Any:
    content = block.get("json")
    if content is not None:
        return content
    text = block["text"]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return ast.literal_eval(text)


class DeterministicMorphosisModel(Model):
    """Drive a real Strands qualification tool call without external credentials."""

    def __init__(self, contract: dict[str, Any], incumbent: dict[str, Any], candidate: dict[str, Any]) -> None:
        self.config: dict[str, Any] = {"model_id": "morphosis-deterministic-demo-v1"}
        self.contract = contract
        self.incumbent = incumbent
        self.candidate = candidate
        self.turn = 0

    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        return dict(self.config)

    async def structured_output(
        self, output_model: type[BaseModel], prompt: Messages, system_prompt: str | None = None, **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        raise NotImplementedError("Morphosis demo uses the normal Strands tool loop")
        yield {}

    async def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        *,
        tool_choice: ToolChoice | None = None,
        system_prompt_content: list[SystemContentBlock] | None = None,
        invocation_state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        tool_results = _collect_tool_results(messages)
        if self.turn == 0:
            self.turn += 1
            async for event in _tool_call(
                "qualify_candidate",
                "qualify-1",
                {"contract": self.contract, "incumbent": self.incumbent, "candidate": self.candidate},
            ):
                yield event
            return

        self.turn += 1
        result = _decode_tool_result(tool_results[-1]["content"][0])
        text = (
            f"Morphosis verdict: {result['verdict']}\n"
            f"Candidate: {result['candidate']}\n"
            f"Workload: {result['workload_id']}\n"
            f"Reasons: {'; '.join(result['reasons'])}\n"
            f"Decision evidence: {result['decision_evidence_hash']}"
        )
        async for event in _text(text):
            yield event


class DeterministicFutureModel(Model):
    """Drive the unknown-future-model evolution tool through a real Strands loop."""

    def __init__(self, candidate: dict[str, Any], parent_hash: str) -> None:
        self.config: dict[str, Any] = {"model_id": "morphosis-future-demo-v2"}
        self.candidate = candidate
        self.parent_hash = parent_hash
        self.turn = 0

    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        return dict(self.config)

    async def structured_output(
        self, output_model: type[BaseModel], prompt: Messages, system_prompt: str | None = None, **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        raise NotImplementedError("Morphosis future demo uses the normal Strands tool loop")
        yield {}

    async def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        *,
        tool_choice: ToolChoice | None = None,
        system_prompt_content: list[SystemContentBlock] | None = None,
        invocation_state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        tool_results = _collect_tool_results(messages)
        if self.turn == 0:
            self.turn += 1
            async for event in _tool_call(
                "evolve_future_model",
                "evolve-1",
                {"candidate": self.candidate, "parent_hash": self.parent_hash},
            ):
                yield event
            return

        self.turn += 1
        result = _decode_tool_result(tool_results[-1]["content"][0])
        text = (
            f"Future model lane: {result['identity']['lane']}\n"
            f"Model: {result['identity']['model_id']}\n"
            f"Novel capability: {result['observed_capability']['capability_id']}\n"
            f"Claim status: {result['claimed_capability']['status']} / {result['claimed_capability']['proof_state']}\n"
            f"Observed status: {result['observed_capability']['status']}\n"
            f"Adaptation: {result['adaptation']['mode']}\n"
            f"Adaptation proof: {result['adaptation_verification']['proof_state']}\n"
            f"Adaptation score: {result['adaptation_verification']['score']:.3f}\n"
            f"Runtime gate: {result['runtime_bundle']['approval']}\n"
            f"Source gate: {result['source_bundle']['approval']}\n"
            f"Evolution bundle: {result['runtime_bundle']['bundle_hash']}"
        )
        async for event in _text(text):
            yield event


def _collect_tool_results(messages: Messages) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for message in messages:
        for block in message.get("content", []):
            if "toolResult" in block:
                results.append(block["toolResult"])
    return results


async def _tool_call(name: str, call_id: str, arguments: dict[str, Any]) -> AsyncIterable[StreamEvent]:
    yield {"messageStart": {"role": "assistant"}}
    yield {"contentBlockStart": {"start": {"toolUse": {"name": name, "toolUseId": call_id}}}}
    yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(arguments)}}}}
    yield {"contentBlockStop": {}}
    yield {"messageStop": {"stopReason": "tool_use"}}


async def _text(text: str) -> AsyncIterable[StreamEvent]:
    yield {"messageStart": {"role": "assistant"}}
    yield {"contentBlockStart": {"start": {}}}
    yield {"contentBlockDelta": {"delta": {"text": text}}}
    yield {"contentBlockStop": {}}
    yield {"messageStop": {"stopReason": "end_turn"}}
