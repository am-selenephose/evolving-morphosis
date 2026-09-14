"""Command-line demos for Evolving Morphosis."""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .agent import create_demo_agent, create_future_demo_agent

ROOT = Path(__file__).resolve().parents[2]


async def _run(contract_path: Path, candidates_path: Path) -> None:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    models = json.loads(candidates_path.read_text(encoding="utf-8"))
    print("EVOLVING MORPHOSIS")
    print(f"workload: {contract['workload_id']}")
    print("rule: newer is never trusted without evidence\n")
    for candidate in models["candidates"]:
        agent = create_demo_agent(contract, models["incumbent"], candidate)
        result = await agent.invoke_async("Qualify this candidate against the workload contract.")
        print(str(result))
        print("-" * 72)


async def _run_future(candidate_path: Path, parent_hash: str) -> None:
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    print("EVOLVING MORPHOSIS — FUTURE MODEL BOOTSTRAP")
    print("rule: self-report is a prior; independent evidence controls promotion\n")
    agent = create_future_demo_agent(candidate, parent_hash=parent_hash)
    result = await agent.invoke_async("Onboard this unknown future model.")
    print(str(result))


def main() -> None:
    parser = argparse.ArgumentParser(description="Qualify and evolve model integrations with Evolving Morphosis")
    parser.add_argument("--contract", type=Path, default=ROOT / "fixtures/morphosis_contract.json")
    parser.add_argument("--candidates", type=Path, default=ROOT / "fixtures/morphosis_candidates.json")
    parser.add_argument("--future-model", type=Path, default=None)
    parser.add_argument("--parent-hash", default="9" * 64)
    args = parser.parse_args()
    if args.future_model is not None:
        asyncio.run(_run_future(args.future_model, args.parent_hash))
    else:
        asyncio.run(_run(args.contract, args.candidates))


if __name__ == "__main__":
    main()
