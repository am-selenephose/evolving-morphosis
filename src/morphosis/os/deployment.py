"""Admission above routing; stage checks execute the compiled adapter independently."""
from dataclasses import dataclass
from typing import Protocol
from .schemas import digest

STAGES=('PROPOSED','VALIDATED','SANDBOXED','QUALIFIED','SHADOW','CANARY','RAMP','PROMOTED')

@dataclass(frozen=True, slots=True)
class TrafficPolicy:
    enabled: bool=False
    canary_fraction: float=0.05
    ramp_fraction: float=0.25
    min_shadow_samples: int=20
    min_canary_samples: int=20
    min_ramp_samples: int=20
    max_mismatch_rate: float=0.0
    production: bool=False

    def validate(self):
        if not 0<=self.canary_fraction<=self.ramp_fraction<=1:
            raise ValueError('traffic fractions must satisfy 0 <= canary <= ramp <= 1')
        if min(self.min_shadow_samples,self.min_canary_samples,self.min_ramp_samples)<1:
            raise ValueError('live traffic sample minimums must be positive')
        if not 0<=self.max_mismatch_rate<=1:
            raise ValueError('live traffic mismatch rate must be between 0 and 1')
        return self

    def fraction(self,stage):
        return {'SHADOW':0.0,'CANARY':self.canary_fraction,'RAMP':self.ramp_fraction}.get(stage,1.0)

    def minimum(self,stage):
        return {'SHADOW':self.min_shadow_samples,'CANARY':self.min_canary_samples,'RAMP':self.min_ramp_samples}.get(stage,0)


class DeploymentController(Protocol):
    def check(self,bundle,at_stage,adapter,transport)->dict:...

class ReferenceDeploymentController:
    def check(self,bundle,at_stage,adapter,transport):
        cases=[{'tool':'lookup','arguments':{'deployment_case':i,'stage':at_stage}} for i in range(3)]
        outputs=[]
        for case in cases:
            try:outputs.append(adapter(transport(case)))
            except (ValueError,TypeError,KeyError):outputs.append(None)
        return {'stage':at_stage,'passed':outputs==cases,'input_hash':digest(cases),'output_hash':digest(outputs),
            'backend':'executed-reference-replay','production_traffic':False,'sample_count':len(cases)}

class QualifiedRouter:
    def __init__(self,application):self.application=application
    def select(self,workload_id):
        s=self.application.snapshot();active=s['deployment']['active_bundle']
        if not active:raise ValueError('no qualified routing admission')
        bundle=self.application.revision(active)
        if bundle['workload_contract']['workload_id']!=workload_id:raise ValueError('workload not admitted')
        decision=self.application.command('qualify',{'surface_id':bundle['surface_id'],'workload_id':workload_id})
        if decision['outcome'] not in ('PROMOTE_TO_SHADOW','PROMOTE_TO_CANARY','PROMOTE'):raise ValueError('routing evidence expired or degraded')
        return bundle

    def invoke(self,workload_id,value):
        from .compiler import compile_ir
        from .schemas import MorphIR,ModelSurface,ProbeSpec
        bundle=self.select(workload_id)
        application=self.application
        surface=ModelSurface.model_validate({k:v for k,v in next(s for s in application.snapshot()['models'] if s['surface_id']==bundle['surface_id']).items() if k not in ('status','capabilities')})
        spec=ProbeSpec(probe_id='qualified-serving',surface_id=surface.surface_id,capability_id=bundle['adaptation']['capability_id'])
        raw=application.executor.execute(spec,application._transport(surface),value)
        return compile_ir(MorphIR.model_validate(bundle['adaptation']))(raw)
