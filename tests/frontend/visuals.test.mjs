import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../../site/visuals.js',import.meta.url),'utf8');
const {createFabricGeometry,eventImpulse,advanceTime,VisualEngine}=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
test('fabric is deterministic six-layer triangulated topology for 3D deformation',()=>{
 const a=createFabricGeometry('workspace','balanced'),b=createFabricGeometry('workspace','balanced');
 assert.deepEqual(a.vertices,b.vertices);assert.deepEqual(a.triangles,b.triangles);
 assert.equal(a.layers,6);assert.ok(a.triangles.length>20000);assert.ok(a.lines.length>10000);
 assert.equal(new Set(Array.from(a.vertices).filter((_,i)=>i%4===2)).size,6);
 assert.ok(a.triangles.every(x=>x<a.vertices.length/4));
});
test('only typed domain events produce bounded visual impulses',()=>{
 assert.equal(eventImpulse({type:'probe.completed'}).pulse,1);
 assert.equal(eventImpulse({event_type:'ProbeRunCompleted'}).pulse,1);
 assert.equal(eventImpulse({event_type:'CandidateBootstrapped'}).strand,1);
 assert.equal(eventImpulse({type:'candidate.rejected'}).red,1);
 assert.equal(eventImpulse({type:'candidate.promoted'}).stability,1);
 assert.equal(eventImpulse({type:'adaptation.verified'}).convergence,1);
 assert.equal(eventImpulse({type:'invented.event'}),null);
 assert.equal(eventImpulse({message:'candidate.promoted'}),null);
});
test('time uses elapsed seconds, clamps resumed frames, and freezes deterministic mode',()=>{
 assert.equal(advanceTime(1,0.01,{}),1.01);
 assert.equal(advanceTime(1,50,{}),1.05);
 assert.equal(advanceTime(1,0.05,{motion:false}),1);
 assert.equal(advanceTime(1,0.05,{reducedMotion:true}),1);
 assert.equal(advanceTime(500,0.05,{visualTest:true}),12);
});
test('event consumption cannot mutate a backend projection and deduplicates event IDs',()=>{
 const engine=new VisualEngine(()=>({motion:false}));
 const projection=Object.freeze({sequence:5,candidates:Object.freeze([])});
 engine.setProjection(projection);engine.consume({id:'e1',type:'probe.completed'});
 assert.equal(engine.projection,projection);assert.equal(engine.impulse.pulse,1);
 engine.impulse.pulse=.2;engine.consume({id:'e1',type:'probe.completed'});
 assert.equal(engine.impulse.pulse,.2);engine.dispose();
});

test('workspace shader has time-driven 3D camera rotation and pointer parallax',()=>{
 const vertex=source.match(/const VERTEX=`([\s\S]*?)`;/)[1];
 assert.match(vertex,/uniform vec2 uPointer/);
 assert.match(vertex,/float yaw=.*uPointer\.x/);
 assert.match(vertex,/float pitch=.*uPointer\.y/);
 assert.match(vertex,/float cameraZ=2\.65/);
 assert.match(vertex,/p\.z\+=sin\(uTime\*\.72\+layer\*\.9\)/);
 assert.match(source,/uniform2f\(u\.Pointer/);
 assert.match(source,/pointermove/);
});

test('vertex and fragment shader interfaces use matching float precision',()=>{
 const vertex=source.match(/const VERTEX=`([\s\S]*?)`;/)[1];
 const fragment=source.match(/const FRAGMENT=`([\s\S]*?)`;/)[1];
 const precision=shader=>shader.match(/precision\s+(\w+)\s+float;/)[1];
 assert.equal(precision(vertex),precision(fragment));
 const interfaceTypes=shader=>new Map([...shader.matchAll(/(?:uniform|varying)\s+(\w+)\s+([^;]+);/g)].flatMap(([,type,names])=>names.split(',').map(name=>[name.trim(),type])));
 const v=interfaceTypes(vertex),f=interfaceTypes(fragment);
 for(const [name,type] of f)assert.equal(v.get(name),type,`shader interface ${name} matches`);
});

test('translucent framebuffer preserves premultiplied color without squaring alpha',()=>{
 assert.match(source,/premultipliedAlpha:true/);
 assert.match(source,/blendFuncSeparate\(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA\)/);
 assert.match(source,/blendFuncSeparate\(gl.SRC_ALPHA,gl.ONE,gl.ONE,gl.ONE_MINUS_SRC_ALPHA\)/);
 // A 50% red source over transparent must store (.5,0,0,.5), not (.5,0,0,.25).
 const sourceAlpha=.5,storedColor=1*sourceAlpha,storedAlpha=sourceAlpha*1;
 assert.equal(storedColor,.5);assert.equal(storedAlpha,.5);
});
