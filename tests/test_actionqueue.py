"""Deterministic unit and Strands integration tests."""

from __future__ import annotations

import json
import asyncio
import unittest
from pathlib import Path

from actionqueue.agent import create_demo_agent
from actionqueue.core import build_action_queue


ROOT = Path(__file__).resolve().parents[1]
PACKET = json.loads((ROOT / "fixtures/opportunities.json").read_text(encoding="utf-8"))
NOW = "2026-08-26T00:00:00Z"


class QueueTests(unittest.TestCase):
    def test_deduplication_expiry_validation_and_gates(self) -> None:
        result = build_action_queue(PACKET, NOW)
        self.assertEqual([item["id"] for item in result["queue"]], ["grant-alpha", "contract-beta"])
        self.assertEqual(
            result["rejected"],
            [
                {"id": "expired-gamma", "reason": "expired"},
                {"id": "grant-alpha-copy", "reason": "duplicate"},
                {
                    "id": "invalid-delta",
                    "reason": "missing:deadline,evidence,reward_usd,source_url",
                },
            ],
        )
        self.assertTrue(all(item["approval_required"] for item in result["queue"]))
        self.assertEqual(len(result["result_hash"]), 64)

    def test_replay_is_byte_stable(self) -> None:
        first = build_action_queue(PACKET, NOW)
        second = build_action_queue(PACKET, NOW)
        self.assertEqual(first, second)

    def test_real_strands_tool_loop(self) -> None:
        agent = create_demo_agent(PACKET, NOW)
        result = asyncio.run(agent.invoke_async("Analyze the packet."))
        text = str(result)
        self.assertIn("ActionQueue completed", text)
        self.assertIn("HUMAN APPROVAL REQUIRED", text)
        self.assertIn("`grant-alpha-copy`: duplicate", text)
        self.assertEqual(result.stop_reason, "end_turn")
        self.assertEqual(len(agent.messages), 4)


if __name__ == "__main__":
    unittest.main()
