"""Constrained qualification: invariants and individual budgets precede improvement."""
from .schemas import QualificationDecision

def qualify(contract,measurements,evidence,*,adapter_passed,missing=(),provider_allowed=True):
    m=measurements; reasons=[]
    if any(getattr(m,k,0)<1 for k in contract.hard_invariants):reasons.append('HARD_INVARIANT')
    if m.cost_usd>contract.max_cost_usd:reasons.append('COST_BUDGET')
    if m.latency_ms>contract.max_latency_ms:reasons.append('LATENCY_BUDGET')
    if m.reliability<contract.reliability_target or 1-m.reliability>contract.failure_budget:reasons.append('RELIABILITY')
    if m.quality<contract.minimum_quality:reasons.append('QUALITY_MINIMUM')
    if contract.incumbent_quality-m.quality>contract.max_regression:reasons.append('REGRESSION')
    if not adapter_passed:reasons.append('ADAPTATION_VERIFICATION')
    if not provider_allowed:reasons.append('PROVIDER_POLICY')
    if reasons:outcome='REJECT'
    elif missing or m.confidence<contract.min_confidence:
        outcome='HOLD';reasons=['MISSING_OR_STALE_EVIDENCE' if missing else 'UNCERTAINTY']
    elif m.quality-contract.incumbent_quality<contract.promotion_margin:
        outcome='HOLD';reasons=['INSUFFICIENT_IMPROVEMENT']
    else:outcome='PROMOTE_TO_SHADOW';reasons=['CONSTRAINTS_PASS','QUALITY_IMPROVES','PROGRESSIVE_PROOF_REQUIRED']
    return QualificationDecision(outcome=outcome,reasons=tuple(reasons),measurements=m,evidence=tuple(evidence),
        uncertainty=1-m.confidence,regression=max(0,contract.incumbent_quality-m.quality),workload_version=contract.version)
