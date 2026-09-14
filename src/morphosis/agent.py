"""Strands agent assembly for Evolving Morphosis."""
from __future__ import annotations

from typing import Any

from strands import Agent
from strands.tools.executors import SequentialToolExecutor

from .demo_model import DeterministicFutureModel, DeterministicMorphosisModel
from .tools import evolve_future_model, qualify_candidate


SYSTEM_PROMPT = """You are Evolving Morphosis, a model-evolution control plane for durable agents.
Never promote a candidate because it is newer, larger, or marketed as better. Treat model/provider
metadata and self-reported capabilities only as priors. Require observed workload evidence, enforce
hard invariants, preserve evidence hashes, and never let a candidate decide its own pass/fail.
Reversible runtime/config changes may be auto-applied only after all gates pass. Source-code changes
always stop at explicit human merge approval.
"""


def create_demo_agent(
    contract: dict[str, Any], incumbent: dict[str, Any], candidate: dict[str, Any]
) -> Agent:
    """Create a credential-free real Strands qualification agent for judging."""
    return Agent(
        model=DeterministicMorphosisModel(contract, incumbent, candidate),
        system_prompt=SYSTEM_PROMPT,
        tools=[qualify_candidate],
        tool_executor=SequentialToolExecutor(),
        callback_handler=None,
    )


def create_future_demo_agent(candidate: dict[str, Any], *, parent_hash: str) -> Agent:
    """Create a credential-free Strands agent that onboards an unknown future model."""
    return Agent(
        model=DeterministicFutureModel(candidate, parent_hash),
        system_prompt=SYSTEM_PROMPT,
        tools=[evolve_future_model],
        tool_executor=SequentialToolExecutor(),
        callback_handler=None,
    )
