"""Real Strands-loop proof for future-model onboarding."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from morphosis.agent import create_future_demo_agent

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "fixtures/future_model_x.json").read_text())


def test_strands_onboards_unknown_future_model_and_respects_merge_gate() -> None:
    agent = create_future_demo_agent(FIXTURE, parent_hash="9" * 64)
    result = asyncio.run(agent.invoke_async("Onboard this unknown future model."))
    text = str(result)

    assert "Future model lane: UNKNOWN_BOOTSTRAP" in text
    assert "future.semantic_patch.v1" in text
    assert "Observed status: SUPPORTED" in text
    assert "Runtime gate: AUTO_APPLY" in text
    assert "Source gate: HUMAN_APPROVAL_REQUIRED" in text
    assert result.stop_reason == "end_turn"
