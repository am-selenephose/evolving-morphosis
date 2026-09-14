"""Command-line demo for Evolving Morphosis."""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .agent import create_demo_agent

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Qualify candidate models with Evolving Morphosis")
    parser.add_argument("--contract", type=Path, default=ROOT / "fixtures/morphosis_contract.json")
    parser.add_argument("--candidates", type=Path, default=ROOT / "fixtures/morphosis_candidates.json")
    args = parser.parse_args()
    asyncio.run(_run(args.contract, args.candidates))


if __name__ == "__main__":
    main()
