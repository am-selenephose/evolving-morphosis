"""Capability state is a time- and surface-scoped fold of immutable observations."""
from datetime import datetime
from math import sqrt
from .schemas import CapabilityState

def date(value):return datetime.fromisoformat(value.replace('Z','+00:00'))

class CapabilityGraph:
    def derive(self,surface_id,capability_id,observations,*,now,definitions=(),_visited=()):
        definition=next((d for d in definitions if d.capability_id==capability_id),None)
        dependencies=definition.dependencies if definition else ()
        empty=dict(surface_id=surface_id,capability_id=capability_id,dependencies=dependencies)
        if capability_id in _visited:return CapabilityState(**empty,status='CONFLICTED')
        rows=[o for o in observations if o.surface_id==surface_id and o.capability_id==capability_id and date(o.observed_at)<=date(now)<date(o.expires_at)]
        if not rows:return CapabilityState(**empty)
        # Repeating a probe or resubmitting the same evidence cannot inflate confidence.
        rows=list({(o.probe_id,o.family):o for o in rows}.values())
        statuses={r.status for r in rows}; hashes=tuple(sorted(r.digest() for r in rows))
        if len(statuses)>1:return CapabilityState(**empty,status='CONFLICTED',evidence=hashes,contradictory_evidence=hashes)
        status=rows[0].status
        families={r.family for r in rows if r.source=='independent-evaluator'}
        samples=sum(r.sample_count for r in rows if r.source=='independent-evaluator')
        successes=sum(r.passed_count for r in rows if r.source=='independent-evaluator')
        if samples and any(r.sample_count>1 for r in rows):
            rate=successes/samples;z=1.96
            confidence=(rate+z*z/(2*samples)-z*sqrt(rate*(1-rate)/samples+z*z/(4*samples*samples)))/(1+z*z/samples)
        else:confidence=min(.99,sum(r.confidence for r in rows)/len(rows))
        if len(families)<2:confidence=min(confidence,.65)
        for dep in dependencies:
            if self.derive(surface_id,dep,observations,now=now,definitions=definitions,_visited=(*_visited,capability_id)).status!='SUPPORTED':status='DEGRADED'
        if definition:
            for conflict in definition.conflicts:
                if any(r.capability_id==conflict and r.surface_id==surface_id and r.status=='SUPPORTED' and date(now)<date(r.expires_at) for r in observations):status='CONFLICTED'
        return CapabilityState(**empty,status=status,confidence=confidence,score=sum(r.score for r in rows)/len(rows),evidence=hashes)
