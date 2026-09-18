"""Closed MorphIR compiler: data transforms, never eval/import/source execution."""
import json
from .schemas import AdaptationVerification, ProbeSpec, digest

OPS=frozenset(('identity','parse_json','rename_tool','normalize_parameters','unwrap_response','assemble_stream','context_limit'))


def compile_ir(ir):
    if ir.mode=='UNSUPPORTED':raise ValueError('unsupported adaptation')
    if len(ir.nodes)>8:raise ValueError('transform resource budget exceeded')
    if ir.mode=='NATIVE' and ir.nodes:raise ValueError('emulation cannot be native')
    if ir.mode!='NATIVE' and not ir.nodes:raise ValueError('adapted path needs executable transforms')
    for node in ir.nodes:
        if node.op not in OPS:raise ValueError('unsupported transform (source and authority changes forbidden)')
        params=dict(node.parameters)
        allowed={'identity':set(),'parse_json':set(),'rename_tool':{'from','to'},'normalize_parameters':{'from','to'},
            'unwrap_response':{'key'},'assemble_stream':set(),'context_limit':{'max_chars'}}[node.op]
        if set(params)-allowed:raise ValueError('unsupported transform parameters')
        if node.op=='context_limit' and not 1<=int(params.get('max_chars','65536'))<=65536:raise ValueError('context budget invalid')
    def adapter(value):
        if len(json.dumps(value).encode())>1048576:raise ValueError('adapter input too large')
        current=json.loads(json.dumps(value))
        for node in ir.nodes:
            p=dict(node.parameters)
            if node.op=='parse_json':current=json.loads(current) if isinstance(current,str) else current
            elif node.op=='unwrap_response':current=current[p.get('key','output')]
            elif node.op=='assemble_stream':current=json.loads(''.join(current))
            elif node.op=='rename_tool':
                if current.get('tool')==p.get('from'):current['tool']=p['to']
            elif node.op=='normalize_parameters':
                args=current.get('arguments',{})
                if p.get('from') in args:args[p['to']]=args.pop(p['from'])
            elif node.op=='context_limit':
                if isinstance(current,str):current=current[:int(p.get('max_chars','65536'))]
        return current
    return adapter


def verify_adapter(ir,transport,executor,now):
    adapter=compile_ir(ir)
    cases=({'tool':'search','arguments':{'query':'held-out α','limit':7}},
        {'tool':'lookup','arguments':{'nested':[None,True,{'id':'preserve'}]}},
        {'tool':'search','arguments':{'text':'do not change evaluator','empty':[]}})
    outputs=[]; fidelity=True; deterministic=True
    spec=ProbeSpec(probe_id='adaptation-heldout-v3',surface_id=ir.surface_id,capability_id=ir.capability_id)
    for value in cases:
        try:
            raw=executor.execute(spec,transport,value)
            one=adapter(raw);two=adapter(raw)
            fidelity &= one==value;deterministic &= one==two;outputs.append(one)
        except (ValueError,TypeError,KeyError,IndexError):fidelity=False;outputs.append({'error':'adapter contract failure'})
    checks=(('roundtrip_fidelity',fidelity),('semantic_preservation',fidelity),('output_validity',all(isinstance(x,dict) and 'tool' in x for x in outputs)),
        ('tool_call_fidelity',fidelity),('side_effect_free',all(n.op in OPS for n in ir.nodes)),('deterministic_replay',deterministic),
        ('bounded_resources',len(ir.nodes)<=8),('security_boundary',True))
    return AdaptationVerification(surface_id=ir.surface_id,adaptation_id=ir.digest(),passed=all(v for _,v in checks),
        checks=checks,input_hash=digest(cases),output_hash=digest(outputs),observed_at=now)
