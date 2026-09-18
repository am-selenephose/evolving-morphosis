"""Authoritative immutable JSON contracts. Schema export is generated from these types."""
from __future__ import annotations
import hashlib
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


def digest(value):
    if isinstance(value, BaseModel): value=value.model_dump(mode='json')
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


class Record(BaseModel):
    model_config=ConfigDict(frozen=True,extra='forbid',allow_inf_nan=False)
    def digest(self): return digest(self)
    def json_value(self): return self.model_dump(mode='json')


class ModelSurface(Record):
    model: str=Field(min_length=1,max_length=160)
    provider: str=Field(min_length=1,max_length=120)
    endpoint: str=Field(min_length=1,max_length=500)
    api_surface: str='json-request-response-v1'
    adapter: str | None=None
    model_version: str='unspecified'
    inference_config: tuple[tuple[str,str],...]=()
    tool_protocol: str='json-tool-v1'
    observed_at: str
    lane: Literal['KNOWN_FAST_PATH','UNKNOWN_BOOTSTRAP']='UNKNOWN_BOOTSTRAP'
    surface_id: str


class CapabilityDefinition(Record):
    capability_id: str
    version: str='1'
    dependencies: tuple[str,...]=()
    conflicts: tuple[str,...]=()
    contract: str='json roundtrip preserving tool and arguments'


class CapabilityClaim(Record):
    surface_id: str
    capability_id: str=Field(pattern=r'^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+$',max_length=180)
    claimed_supported: bool=True
    source: str='candidate-self-report'


class CapabilityObservation(Record):
    sample_count: int=Field(default=1,ge=1)
    passed_count: int=Field(default=1,ge=0)
    workload_hash: str=''
    surface_id: str
    capability_id: str
    probe_id: str
    run_id: str
    family: str
    status: Literal['SUPPORTED','UNSUPPORTED','DEGRADED']
    confidence: float=Field(ge=0,le=1)
    score: float=Field(ge=0,le=1)
    observed_at: str
    expires_at: str
    source: str='independent-evaluator'
    provenance: str='reference-execution'
    evaluator_version: str='morphosis-reference-v3.1'
    parent_evidence: tuple[str,...]=()
    evidence_hash: str=''


class CapabilityState(Record):
    surface_id: str
    capability_id: str
    status: Literal['UNKNOWN','SUPPORTED','UNSUPPORTED','DEGRADED','CONFLICTED']='UNKNOWN'
    confidence: float=0
    score: float=0
    evidence: tuple[str,...]=()
    contradictory_evidence: tuple[str,...]=()
    dependencies: tuple[str,...]=()


class Assertion(Record):
    kind: Literal['json_object','roundtrip','tool_fidelity','reject_invalid']='roundtrip'


class ProbeSpec(Record):
    workload_hash: str=''
    probe_id: str
    surface_id: str
    capability_id: str
    source: Literal['built-in','system-generated','candidate-proposed']='system-generated'
    family: Literal['conformance','roundtrip','differential','metamorphic','adversarial','regression','negative','tool-use','structured-output','context-window','failure-recovery']='roundtrip'
    input_contract: str='json-tool-v1'
    expected_properties: tuple[str,...]=('preserve tool','preserve arguments')
    timeout_ms: int=Field(default=1000,gt=0,le=5000)
    memory_mb: int=Field(default=64,ge=32,le=128)
    max_bytes: int=Field(default=65536,ge=128,le=1048576)
    seed: int=17
    network: bool=False
    source_write: bool=False
    filesystem: Literal['temporary-only','none']='temporary-only'
    secrets: tuple[str,...]=()
    tools: tuple[str,...]=()
    assertions: tuple[Assertion,...]=(Assertion(),)
    evaluator: str='morphosis-reference-v3.1'


class ProbeRun(Record):
    sample_count: int=Field(default=1,ge=1)
    passed_count: int=Field(default=1,ge=0)
    run_id: str
    probe_id: str
    surface_id: str
    capability_id: str
    family: str
    passed: bool
    output_hash: str
    input_hash: str
    observed_at: str
    evaluator_version: str='morphosis-reference-v3.1'
    provenance: str='bounded-reference-interpreter'
    latency_ms: float
    cost_usd: float
    checks: tuple[str,...]
    source: str


class TransformNode(Record):
    op: str
    parameters: tuple[tuple[str,str],...]=()


class MorphIR(Record):
    surface_id: str
    capability_id: str
    mode: Literal['NATIVE','ADAPTED','COMPOSED','FALLBACK','UNSUPPORTED']='ADAPTED'
    nodes: tuple[TransformNode,...]=()
    author: Literal['system','candidate']='candidate'
    schema_version: str='3.0'


class AdaptationVerification(Record):
    surface_id: str
    adaptation_id: str
    passed: bool
    checks: tuple[tuple[str,bool],...]
    input_hash: str
    output_hash: str
    evaluator_version: str='morphosis-reference-v3.1'
    observed_at: str
    latency_overhead_ms: float=0
    cost_overhead_usd: float=0
    provenance: str='held-out-reference-corpus'


class WorkloadContract(Record):
    workload_id: str='tool-roundtrip'
    version: str='3.0'
    required: tuple[str,...]=('future.semantic_patch.v1',)
    optional: tuple[str,...]=()
    hard_invariants: tuple[str,...]=('safety','tool_fidelity','determinism')
    minimum_quality: float=Field(default=.9,ge=0,le=1)
    max_cost_usd: float=Field(default=.05,ge=0)
    max_latency_ms: float=Field(default=6000,ge=0)
    reliability_target: float=Field(default=.99,ge=0,le=1)
    failure_budget: float=Field(default=.01,ge=0,le=1)
    min_confidence: float=Field(default=.9,ge=0,le=1)
    max_regression: float=Field(default=.05,ge=0,le=1)
    promotion_margin: float=Field(default=.02,ge=0,le=1)
    incumbent_quality: float=Field(default=.9,ge=0,le=1)
    evidence_ttl_seconds: int=Field(default=86400,gt=0)
    allowed_providers: tuple[str,...]=('reference',)
    privacy: str='synthetic-data-only'
    data_residency: str='local'
    tools: tuple[str,...]=()
    human_approval_required: bool=False


class ObjectiveMeasurements(Record):
    quality: float=Field(default=1,ge=0,le=1)
    correctness: float=Field(default=1,ge=0,le=1)
    tool_fidelity: float=Field(default=1,ge=0,le=1)
    safety: float=Field(default=1,ge=0,le=1)
    reliability: float=Field(default=1,ge=0,le=1)
    determinism: float=Field(default=1,ge=0,le=1)
    confidence: float=Field(default=1,ge=0,le=1)
    latency_ms: float=Field(default=1,ge=0)
    cost_usd: float=Field(default=.001,ge=0)
    adaptation_complexity: int=Field(default=1,ge=0)
    operational_risk: float=Field(default=.05,ge=0,le=1)


class QualificationDecision(Record):
    outcome: Literal['PROMOTE','PROMOTE_TO_SHADOW','PROMOTE_TO_CANARY','HOLD','REQUALIFY','REJECT','ROLLBACK']
    reasons: tuple[str,...]
    measurements: ObjectiveMeasurements
    evidence: tuple[str,...]
    uncertainty: float
    regression: float
    workload_version: str


class PolicyDecision(Record):
    outcome: Literal['ALLOW_PROBE','DENY_PROBE','ALLOW_SANDBOX_RUN','AUTO_APPLY_RUNTIME','REQUIRE_HUMAN_APPROVAL','HOLD','REJECT','ROLLBACK']
    reasons: tuple[str,...]
    kernel_version: str='constitutional-kernel-v3.1'
    evidence: tuple[str,...]=()


class EvolutionBundle(Record):
    bundle_id: str
    schema_version: str='3.0'
    surface_id: str
    workload_contract: WorkloadContract
    parent_revisions: tuple[str,...]=()
    capability_evidence: tuple[str,...]
    probe_runs: tuple[str,...]
    adaptation: MorphIR
    adaptation_verification: AdaptationVerification
    qualification: QualificationDecision
    policy: PolicyDecision
    runtime_changes: tuple[tuple[str,str],...]
    source_patch: str | None=None
    rollback_recipe: str
    dependencies: tuple[str,...]
    artifact_hashes: tuple[str,...]
    evaluator_versions: tuple[str,...]=('morphosis-reference-v3.1',)
    provenance: str='local-reference-execution'
    created_at: str


class EvolutionTransaction(Record):
    transaction_id: str
    bundle_id: str
    stage: Literal['PROPOSED','VALIDATED','SANDBOXED','QUALIFIED','SHADOW','CANARY','RAMP','PROMOTED','REJECT','ROLLBACK']='PROPOSED'
    previous_bundle: str | None=None
    checks: tuple[str,...]=()


class DeploymentState(Record):
    active_bundle: str | None=None
    fallback_bundle: str | None=None
    admitted: tuple[str,...]=()
    backend: str='reference-replay (no production traffic)'


class TelemetryEvent(Record):
    surface_id: str
    schema_failures: int=Field(default=0,ge=0)
    tool_failures: int=Field(default=0,ge=0)
    policy_failures: int=Field(default=0,ge=0)
    latency_ms: float=Field(default=0,ge=0)
    cost_usd: float=Field(default=0,ge=0)
    quality: float=Field(default=1,ge=0,le=1)
    fingerprint: str | None=None


class DomainEvent(Record):
    event_id: str
    event_type: str
    timestamp: str
    aggregate_id: str
    correlation_id: str
    causation_id: str | None=None
    schema_version: str='3.0'
    sequence: int
    payload: dict
    evidence: tuple[str,...]=()
    previous_hash: str
    event_hash: str
