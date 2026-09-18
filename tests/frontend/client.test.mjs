import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source = await readFile(new URL('../../site/data.js',import.meta.url),'utf8');
const {ProjectionClient,presentEvent}=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
test('event delivery deduplicates and ignores stale sequence without losing next snapshot',async()=>{
 const calls=[];const client=new ProjectionClient({live:true,fetcher:async url=>{calls.push(url);return {ok:true,json:async()=>({sequence:9,events:[]})}}});
 client.snapshot={sequence:5};client.sequence=5;let events=0;client.onEvent=()=>events++;
 await Promise.all([client.acceptEvent({sequence:7}),client.acceptEvent({sequence:7}),client.acceptEvent({sequence:6})]);
 assert.equal(events,1);assert.equal(calls.length,1);assert.equal(client.sequence,9);
});
test('static mode reads backend artifacts only and replays exact scenario trace',async()=>{
 const scenario={result:{outcome:'HOLD'},snapshot:{sequence:12,qualifications:[{outcome:'HOLD'}]},events:[{sequence:11,event_type:'QualificationHeld'},{sequence:12,event_type:'BundleCreated'}]};
 const calls=[];const files={'generated/system.json':{sequence:10},'generated/events.json':[], 'generated/scenarios.json':{'surface-a':scenario}};
 const client=new ProjectionClient({live:false,fetcher:async url=>{calls.push(url);return {ok:true,json:async()=>files[url]}}});
 await client.load();const seen=[];client.onEvent=e=>seen.push(e.sequence);
 assert.deepEqual(await client.command('evaluate',{surface_id:'surface-a'}),scenario.result);
 assert.deepEqual(client.snapshot,scenario.snapshot);assert.deepEqual(seen,[11,12]);assert.ok(calls.every(x=>!x.startsWith('/api')));
 await assert.rejects(()=>client.command('bootstrap',{model:'invented'}),/live mode/i);
 assert.equal(client.snapshot.qualifications[0].outcome,'HOLD');
});
test('live commands pass unchanged payload to canonical backend then refresh',async()=>{
 const calls=[];const client=new ProjectionClient({live:true,fetcher:async(url,options)=>{calls.push([url,options]);return {ok:true,json:async()=>url.includes('commands')?{outcome:'REJECT'}:{sequence:4}}}});
 const result=await client.command('evaluate',{surface_id:'canonical-id'});
 assert.equal(result.outcome,'REJECT');assert.equal(JSON.parse(calls[0][1].body).payload.surface_id,'canonical-id');assert.equal(calls[1][0],'/api/v1/system');
});

test('event presentation only exposes explicit canonical status fields',()=>{
 assert.deepEqual(presentEvent({event_type:'CandidatePromoted',payload:{}}),{title:'Candidate Promoted',status:null});
 assert.deepEqual(presentEvent({event_type:'QualificationCompleted',payload:{mutation:{value:{outcome:'HOLD'}}}}),{title:'Qualification Completed',status:'HOLD'});
 assert.equal(presentEvent({event_type:'ProbeCompleted',payload:{mutation:{value:{passed:false}}}}).status,'FAILED');
 assert.equal(presentEvent({event_type:'DeploymentCheckCompleted',payload:{mutation:{value:{stage:'CANARY',passed:true}}}}).status,'CANARY');
});
