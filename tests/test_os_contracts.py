"""Cross-layer tests compare IDs, decisions, event chains and actual tool/HTTP loops."""
import asyncio
import importlib.util
import json
import threading
import urllib.request
from pathlib import Path
import pytest
from morphosis.os.application import MorphosisApplication


def require(name):
    assert importlib.util.find_spec(name),f'missing transport {name}'


def test_http_cli_and_strands_use_same_command_boundary(tmp_path):
    require('morphosis.os.api');require('morphosis.os.agents');require('morphosis.os.cli')
    from morphosis.os.api import server
    from morphosis.os.agents import command_tool
    from morphosis.os.cli import execute
    a=MorphosisApplication(tmp_path/'s.db',clock=lambda:'2026-09-15T00:00:00Z')
    payload={'model':'future-model-x','provider':'reference','endpoint':'reference://echo','claims':['future.semantic_patch.v1']}
    direct=a.command('bootstrap',payload,command_id='same')
    assert execute(a,'bootstrap',payload,'same')==direct
    bound=command_tool(a)
    assert asyncio.run(bound(name='bootstrap',payload=payload,command_id='same'))==direct
    http=server(a,port=0);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
    try:
        request=urllib.request.Request(f'http://127.0.0.1:{http.server_port}/api/v1/commands',
            data=json.dumps({'name':'bootstrap','payload':payload,'command_id':'same'}).encode(),headers={'Content-Type':'application/json'})
        assert json.load(urllib.request.urlopen(request))==direct
        assert json.load(urllib.request.urlopen(f'http://127.0.0.1:{http.server_port}/api/v1/system'))==a.snapshot()
    finally:http.shutdown();http.server_close()


def test_real_strands_v3_loop_writes_same_ledger(tmp_path):
    require('morphosis.os.agents')
    from morphosis.os.agents import create_reference_agent
    a=MorphosisApplication(tmp_path/'s.db',clock=lambda:'2026-09-15T00:00:00Z')
    result=asyncio.run(create_reference_agent(a).invoke_async('Evolve the reference model through the canonical services.'))
    assert result.stop_reason=='end_turn'
    assert a.snapshot()['deployment']['active_bundle']
    assert any(e['event_type']=='CandidatePromoted' for e in a.events())
    assert a.ledger.verify()


def test_export_matches_authoritative_schema_and_hashes(tmp_path):
    require('morphosis.export_demo')
    from morphosis.export_demo import export
    svg=tmp_path/'architecture.svg';a=export(tmp_path,svg)
    snapshot=json.loads((tmp_path/'system.json').read_text())
    assert snapshot==a.snapshot()
    assert json.loads((tmp_path/'events.json').read_text())==a.events()
    schemas=json.loads((tmp_path/'schemas.json').read_text())
    assert 'DomainEvent' in schemas and 'EvolutionBundle' in schemas and 'ModelSurface' in schemas
    architecture=json.loads((tmp_path/'architecture.json').read_text());markup=svg.read_text()
    assert all(f'id="node-{node["id"]}"' in markup for node in architecture['nodes'])
    assert 'EVOLUTION OS V3' in markup and markup.count('class="edge"')+markup.count('class="loop"')==len(architecture['edges'])
    from jsonschema import validate
    for e in snapshot['events']:validate(e,schemas['DomainEvent'])
    for b in snapshot['bundles']:validate(b,schemas['EvolutionBundle'])
    for s in snapshot['models']:validate({k:v for k,v in s.items() if k not in ('status','capabilities')},schemas['ModelSurface'])


def test_sse_resume_returns_only_new_events(tmp_path):
    require('morphosis.os.api')
    from morphosis.os.api import event_frames
    a=MorphosisApplication(tmp_path/'s.db')
    a.command('bootstrap',{'model':'x','provider':'reference','endpoint':'reference://echo','claims':['a.b.v1']})
    frames=event_frames(a,1)
    assert 'id: 1\n' not in frames and 'id: 2\n' in frames and 'event: domain' in frames
