"""Evolving Morphosis: evidence-driven model evolution for durable agents."""

__version__ = "0.3.0"

from .core import (
    CapabilityEvidence,
    CandidateProfile,
    PromotionDecision,
    WorkloadContract,
    build_profile,
    decide_candidate,
)
from .evolution import (
    AdaptationPlan,
    AdaptationVerification,
    CandidateIdentity,
    CapabilityRecord,
    CapabilityRegistry,
    EvolutionBundle,
    EvolutionChange,
    EvolutionOutcome,
    KnownAdapterRegistry,
    ProbeProposal,
    ProbeResult,
    apply_evolution,
    bootstrap_candidate,
    build_evolution_bundle,
    compile_adaptation,
    needs_requalification,
    verify_adaptation_proposal,
    verify_probe_proposal,
)
from .future_flow import FutureEvolutionReport, evaluate_future_candidate

__all__ = [
    "CapabilityEvidence",
    "CandidateProfile",
    "PromotionDecision",
    "WorkloadContract",
    "build_profile",
    "decide_candidate",
    "AdaptationPlan",
    "AdaptationVerification",
    "CandidateIdentity",
    "CapabilityRecord",
    "CapabilityRegistry",
    "EvolutionBundle",
    "EvolutionChange",
    "EvolutionOutcome",
    "KnownAdapterRegistry",
    "ProbeProposal",
    "ProbeResult",
    "apply_evolution",
    "bootstrap_candidate",
    "build_evolution_bundle",
    "compile_adaptation",
    "needs_requalification",
    "verify_adaptation_proposal",
    "verify_probe_proposal",
    "FutureEvolutionReport",
    "evaluate_future_candidate",
]
