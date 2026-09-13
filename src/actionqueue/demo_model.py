"""Credential-free deterministic model used to prove the Strands agent loop locally."""

from __future__ import annotations

import json
import ast
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any

from pydantic import BaseModel
from strands.models import Model
from strands.types.content import Messages, SystemContentBlock
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolChoice, ToolSpec

from actionqueue.core import render_markdown


class DeterministicDemoModel(Model):
    """Select ActionQueue tools deterministically for offline demos and tests."""

    def __init__(self, packet: dict[str, Any], now_iso: str) -> None:
        self.config: dict[str, Any] = {"model_id": "actionqueue-deterministic-demo-v1"}
        self.packet = packet
        self.now_iso = now_iso
        self.turn = 0

    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        return dict(self.config)

    async def structured_output(
        self, output_model: type[BaseModel], prompt: Messages, system_prompt: str | None = None, **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        raise NotImplementedError("The deterministic demo uses the normal Strands tool loop")
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
        tool_results: list[dict[str, Any]] = []
        for message in messages:
            for block in message.get("content", []):
                if "toolResult" in block:
                    tool_results.append(block["toolResult"])

        if self.turn == 0:
            self.turn += 1
            async for event in self._tool_call(
                "analyze_opportunity_packet",
                "analyze-1",
                {"packet": self.packet, "now_iso": self.now_iso},
            ):
                yield event
            return
        self.turn += 1
        block = tool_results[-1]["content"][0]
        content = block.get("json")
        if content is None:
            content = ast.literal_eval(block["text"])
        report = render_markdown(content)
        async for event in self._text(f"ActionQueue completed with all consequential actions gated.\n\n{report}"):
            yield event

    async def _tool_call(self, name: str, call_id: str, arguments: dict[str, Any]) -> AsyncIterable[StreamEvent]:
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockStart": {"start": {"toolUse": {"name": name, "toolUseId": call_id}}}}
        yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(arguments)}}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "tool_use"}}

    async def _text(self, text: str) -> AsyncIterable[StreamEvent]:
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockStart": {"start": {}}}
        yield {"contentBlockDelta": {"delta": {"text": text}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}
