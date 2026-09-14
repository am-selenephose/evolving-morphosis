"""Strands agent assembly for Evolving Morphosis."""
from __future__ import annotations

from typing import Any

from strands import Agent
from strands.tools.executors import SequentialToolExecutor

from .demo_model import DeterministicMorphosisModel
from .tools import qualify_candidate


SYSTEM_PROMPT = """You are Evolving Morphosis, a model-qualification control plane for agents.
Never promote a candidate because it is newer, larger, or marketed as better. Use observed
workload evidence, enforce hard invariants, preserve evidence hashes, and return one of
PROMOTE, HOLD, or REJECT. Model/provider metadata may inform discovery but cannot override
failed workload evidence or authorization boundaries.
"""


def create_demo_agent(
    contract: dict[str, Any], incumbent: dict[str, Any], candidate: dict[str, Any]
) -> Agent:
    """Create a credential-free real Strands agent for reproducible judging."""
    return Agent(
        model=DeterministicMorphosisModel(contract, incumbent, candidate),
        system_prompt=SYSTEM_PROMPT,
        tools=[qualify_candidate],
        tool_executor=SequentialToolExecutor(),
        callback_handler=None,
    )
