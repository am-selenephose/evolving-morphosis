"""Strands tools exposed to the Evolving Morphosis agent."""

from __future__ import annotations

from typing import Any

from strands import tool

from actionqueue.core import build_action_queue, render_markdown


@tool
async def analyze_opportunity_packet(packet: dict[str, Any], now_iso: str) -> dict[str, Any]:
    """Build a deduplicated evidence-backed queue without taking external action.

    Args:
        packet: JSON opportunity packet containing an opportunities list.
        now_iso: Explicit ISO-8601 reference time for reproducibility.

    Returns:
        Queue records, rejections, evidence hashes, and human approval gates.
    """
    return build_action_queue(packet, now_iso)


@tool
async def format_review_report(queue: dict[str, Any]) -> str:
    """Format a previously analyzed queue for human review.

    Args:
        queue: Output returned by analyze_opportunity_packet.

    Returns:
        Markdown report with explicit approval status.
    """
    return render_markdown(queue)
