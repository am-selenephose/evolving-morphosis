import asyncio
from typing import Literal

from pydantic import BaseModel

from morphosis.demo_model import DeterministicMorphosisModel
from actionqueue.demo_model import DeterministicDemoModel


class StructuredFixture(BaseModel):
    name: str
    enabled: bool
    count: int
    mode: Literal["safe", "fast"]
    tags: list[str]


async def collect(model):
    events = []
    async for event in model.structured_output(StructuredFixture, []):
        events.append(event)
    return events


def test_morphosis_fixture_model_supports_structured_output():
    model = DeterministicMorphosisModel({}, {}, {})
    event = asyncio.run(collect(model))[-1]
    assert event["output"] == StructuredFixture(
        name="",
        enabled=False,
        count=0,
        mode="safe",
        tags=[],
    )


def test_actionqueue_fixture_model_supports_structured_output():
    model = DeterministicDemoModel({}, "2026-09-20T00:00:00Z")
    event = asyncio.run(collect(model))[-1]
    assert event["output"].mode == "safe"
