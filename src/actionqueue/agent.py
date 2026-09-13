"""ActionQueue Strands agent assembly."""

from __future__ import annotations

from typing import Any

from strands import Agent
from strands.tools.executors import SequentialToolExecutor

from actionqueue.demo_model import DeterministicDemoModel
from actionqueue.tools import analyze_opportunity_packet


SYSTEM_PROMPT = """You are ActionQueue, a professional-work triage agent.
Use tools to normalize and deduplicate supplied opportunity evidence. Never submit, publish,
send, sign, spend, or claim identity. Surface consequential actions as explicit human approval
gates, preserve source URLs and evidence hashes, and finish with a concise review report.
"""


def create_demo_agent(packet: dict[str, Any], now_iso: str) -> Agent:
    """Create a credential-free Strands agent for deterministic verification."""
    return Agent(
        model=DeterministicDemoModel(packet, now_iso),
        system_prompt=SYSTEM_PROMPT,
        tools=[analyze_opportunity_packet],
        tool_executor=SequentialToolExecutor(),
        callback_handler=None,
    )
