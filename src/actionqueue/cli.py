"""Command-line entry point for ActionQueue."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from actionqueue.agent import create_demo_agent


def main() -> None:
    """Run the offline Strands demonstration against a JSON fixture."""
    parser = argparse.ArgumentParser(description="Build a gated action queue from an opportunity packet")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--now", required=True, help="ISO-8601 reference time")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    result = asyncio.run(
        create_demo_agent(packet, args.now).invoke_async("Analyze this opportunity packet and produce the review report.")
    )
    text = str(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
