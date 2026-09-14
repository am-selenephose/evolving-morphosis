"""Typed evidence primitives for model qualification."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ProbeObservation:
    name: str
    score: float
    passed: bool
    latency_ms: float
    evidence: str
    cost_usd: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("probe score must be between 0 and 1")
        if self.latency_ms < 0 or self.cost_usd < 0:
            raise ValueError("latency and cost cannot be negative")


@dataclass(frozen=True)
class QualificationPolicy:
    required_probes: tuple[str, ...]
    weights: Mapping[str, float]
    minimum_scores: Mapping[str, float] = field(default_factory=dict)
    promotion_margin: float = 0.02
    max_regression: float = 0.05


@dataclass(frozen=True)
class CapabilityManifest:
    model_id: str
    workload: str
    observations: tuple[ProbeObservation, ...]
    workload_score: float
    total_latency_ms: float
    total_cost_usd: float
    evidence_hash: str
