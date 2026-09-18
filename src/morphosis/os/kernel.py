"""Independent authority: no candidate input can configure this object."""
from dataclasses import dataclass
from .schemas import PolicyDecision, ProbeSpec

@dataclass(frozen=True)
class PolicyKernel:
    version: str='constitutional-kernel-v3.1'
    evaluator: str='morphosis-reference-v3.1'
    automatic_classes: tuple[str,...]=('runtime','config')

    def probe(self,p:ProbeSpec):
        unsafe=p.network or p.source_write or bool(p.secrets) or bool(p.tools) or p.evaluator!=self.evaluator
        return PolicyDecision(outcome='DENY_PROBE' if unsafe else 'ALLOW_PROBE',
            reasons=('UNSAFE_PROBE',) if unsafe else ('BOUNDED_TYPED_INTERPRETER',),evidence=(p.digest(),))

    def evolution(self,decision,verification,*,source_patch,rollback,contract):
        refs=(decision.digest(),verification.digest(),contract.digest())
        if source_patch is not None or contract.human_approval_required:
            return PolicyDecision(outcome='REQUIRE_HUMAN_APPROVAL',reasons=('SOURCE_MERGE_AUTHORITY' if source_patch is not None else 'CONTRACT_APPROVAL',),evidence=refs)
        if not rollback:return PolicyDecision(outcome='HOLD',reasons=('ROLLBACK_REQUIRED',),evidence=refs)
        if decision.outcome not in ('PROMOTE_TO_SHADOW','PROMOTE_TO_CANARY','PROMOTE') or not verification.passed:
            return PolicyDecision(outcome='REJECT',reasons=('QUALIFICATION_REQUIRED',),evidence=refs)
        return PolicyDecision(outcome='AUTO_APPLY_RUNTIME',reasons=('EVIDENCE_AND_PROGRESSIVE_CHECKS_REQUIRED',),evidence=refs)
