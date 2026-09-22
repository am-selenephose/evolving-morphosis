// Organic surfaces are presentation only. No visual state is domain authority.
const TIERS={high:[112,28],balanced:[84,22],safe:[52,14],reduced:[60,16]};
export function createFabricGeometry(type='workspace',quality='balanced'){
 const [nu,nv]=TIERS[quality]||TIERS.balanced,layers=type==='workspace'?(quality==='safe'?4:quality==='balanced'?5:6):(quality==='safe'?2:3);
 const vertices=[],triangles=[],lines=[],nodes=[];
 for(let l=0;l<layers;l++)for(let v=0;v<=nv;v++)for(let u=0;u<=nu;u++){
  const i=vertices.length/4;vertices.push(u/nu,v/nv,l,Math.sin(i*127.1+311.7)*43758.5453%1);
  if(u<nu&&v<nv){const b=i+nu+1;triangles.push(i,b,i+1,i+1,b,b+1);}
  if(u<nu)lines.push(i,i+1);
  if(v<nv&&u%4===0)lines.push(i,i+nu+1);
  if(u>8&&u<nu-8&&v>2&&v<nv-2&&(u*7+v*13+l*19)%251===0)nodes.push(i);
 }
 return {layers,vertices:new Float32Array(vertices),triangles:new Uint16Array(triangles),lines:new Uint16Array(lines),nodes:new Uint16Array(nodes)};
}
export function advanceTime(time,delta,settings){
 if(settings.visualTest)return 12;
 if(settings.motion===false||settings.reducedMotion)return time;
 return time+Math.max(0,Math.min(delta,.05));
}
export function eventImpulse(event){
 const key=String(event?.type||event?.event_type||'').replace(/[._-]/g,'').toLowerCase();
 const map={candidatebootstrapped:{strand:1},candidatediscovered:{strand:1},modelregistered:{strand:1},surfaceregistered:{strand:1},proberuncompleted:{pulse:1},probecompleted:{pulse:1},proberun:{pulse:1},probestarted:{pulse:1},capabilityobserved:{pulse:1},adaptationverified:{convergence:1},candidaterejected:{red:1},qualificationrejected:{red:1},candidatepromoted:{stability:1},canarypromoted:{stability:1},deploymentpromoted:{stability:1},rollbackcompleted:{red:.7}};
 return map[key]||null;
}
const VERTEX=`
precision highp float;
attribute vec4 aFabric;
uniform float uTime,uWorkspace,uPass,uDpr,uMotion,uStrand,uSidebar;
uniform vec2 uPointer;
uniform vec4 uImpulse;
varying vec3 vPosition;
varying vec2 vUV;
varying float vLayer,vLight,vSeed,vDust;
vec3 surface(vec2 uv,float layer){
 float x=uv.x*2.-1.,v=uv.y*2.-1.;
 float phase=layer*1.13+uTime*.58;
 float fold=sin(x*4.7+phase)*.48+sin(x*9.1-layer*.7+v*2.8)*.15;
 float taper=pow(max(.001,1.-x*x),.62);
 float twist=v*1.9+sin(x*3.4+phase)*1.1;
 float z=sin(twist)*taper*.39+fold*.36;
 float y=cos(twist)*taper*.23+fold*.19;
 // Warped sheets have breadth in both y and z, with separately phased ridges.
 y+=v*.10+sin(v*5.+x*3.-phase)*.055;
 y+=sin(x*11.-uTime*1.85+layer)*.028*uMotion;
 y+=uImpulse.x*.026*sin(x*8.-uTime*3.);
 y+=uStrand*.025*sin(x*5.+layer);
 y-=uImpulse.w*.018*sin(x*11.-uTime*.8+layer);
 if(uWorkspace>.5){
  y+=(2.5-layer)*.245;
  y=y*(1.-uImpulse.y*.06)+.05;
  x=x*.48+.025+sin(layer*2.)*.024;
  z+=sin(layer)*.09;
 }else{
  if(uSidebar>.5){
   y=fold*.48+v*taper*.48+sin(x*2.3+layer)*.22-.02;
  }else{
   // Low central knot rising into the far-right arch of the locked visual composition.
   float arch=exp(-pow((x-.43)*3.8,2.));
   y=-.63+fold*.38+v*taper*.31+arch*.88;
   z+=sin(x*4.+layer)*.16;
  }
  x=uSidebar>.5?x*1.18+.22:x*.90+.40;
  z+=v*.16;
 }
 return vec3(x,y,z);
}
void main(){
 vec2 uv=aFabric.xy;float layer=aFabric.z;
 vec3 p=surface(uv,layer);
 vec3 dx=surface(uv+vec2(.001,0.),layer)-p;
 vec3 dy=surface(uv+vec2(0.,.001),layer)-p;
 vec3 normal=normalize(cross(dx,dy));
 float seed=abs(aFabric.w);
 vDust=0.;
 if(uPass>1.5&&uPass<2.5){
  // Reuse surface vertices for deterministic off-surface dust, with no extra buffers.
  float jitter=fract(sin(dot(uv,vec2(127.1,311.7))+layer*17.3)*43758.5453);
  p.xy+=vec2(seed-.5,jitter-.5)*.009;
  if(seed>.76){
   vDust=1.;
   float spread=uWorkspace>.5?.16:(uSidebar>.5?.85:1.30);
   p.y+=(jitter-.20)*spread;
   p.x+=(seed-.88)*(uWorkspace>.5?.3:1.3);
   p.z+=(jitter-.5)*.45;
  }
 }
 // Give the workspace a real moving camera transform instead of a flat 2D ribbon.
 float yaw=(sin(uTime*.43)*.10+uPointer.x*.12)*uMotion;
 float pitch=(cos(uTime*.31)*.045-uPointer.y*.07)*uMotion;
 float cy=cos(yaw),sy=sin(yaw),cx=cos(pitch),sx=sin(pitch);
 vec3 q=vec3(cy*p.x+sy*p.z,p.y,-sy*p.x+cy*p.z);
 p=vec3(q.x,cx*q.y-sx*q.z,sx*q.y+cx*q.z);
 if(uWorkspace>.5){
  p.z+=sin(uTime*.72+layer*.9)*.055*uMotion;
  p.y+=cos(uTime*.54+layer*.7)*.016*uMotion;
 }
 float cameraZ=2.65;
 float perspective=cameraZ/(cameraZ+p.z*.48);
 gl_Position=vec4(p.x*perspective,(p.y-p.z*.12)*perspective,p.z*.16,1.);
 vPosition=p;vUV=uv;vLayer=layer;vSeed=abs(aFabric.w);
 vLight=pow(1.-abs(normal.z),3.)*.8+pow(max(0.,dot(normal,normalize(vec3(-.3,.8,1.)))),9.);
 gl_PointSize=(uPass>2.5?9.5:(1.35+vSeed*1.35))*min(uDpr,1.5);
}`;
const FRAGMENT=`
precision highp float;
uniform float uPass,uWorkspace,uTime;
uniform vec4 uImpulse;
varying vec3 vPosition;
varying vec2 vUV;
varying float vLayer,vLight,vSeed,vDust;
void main(){
 float taper=pow(max(0.,sin(vUV.x*3.14159)),.6);
 float edge=pow(abs(vUV.y*2.-1.),12.);
 float pulse=uImpulse.x*exp(-pow((vUV.x-fract(uTime*.22))*13.,2.));
 vec3 wine=vec3(.46,.025,.16),pink=vec3(1.,.075,.37),pale=vec3(1.,.65,.82);
 vec3 color=mix(wine,pink,min(1.,vLight+edge*.5));
 color=mix(color,pale,min(.85,vLight*.94+edge*.65+pulse*.4));
 color=mix(color,vec3(.48,.015,.045),uImpulse.z*.65);
 float alpha;
 if(uPass<.5){alpha=(.035+vLight*.12+edge*.08)*taper;if(uWorkspace<.5)alpha*=.18;}
 else if(uPass<1.5){alpha=(.010+vLight*.055+edge*.08)*taper;if(uWorkspace<.5)alpha*=.65;}
 else if(uPass<2.5){float r=length(gl_PointCoord-.5)*2.;if(r>1.)discard;float disc=1.-smoothstep(.36,1.,r);alpha=(.22+vLight*.34)*taper*disc*mix(.82,.34,vDust);color=mix(pink,pale,min(.68,vLight*.24+disc*.12));}
 else{float r=length(gl_PointCoord-.5)*2.;if(r>1.)discard;float disc=1.-smoothstep(.12,1.,r);alpha=disc*.58*taper;color=mix(pink,pale,disc*.38);}
 gl_FragColor=vec4(color,alpha);
}`;
function compile(gl,type,source){const shader=gl.createShader(type);gl.shaderSource(shader,source);gl.compileShader(shader);if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS)){const message=gl.getShaderInfoLog(shader);gl.deleteShader(shader);throw Error(message);}return shader;}
function resource(gl,type,quality){
 const vertex=compile(gl,gl.VERTEX_SHADER,VERTEX),fragment=compile(gl,gl.FRAGMENT_SHADER,FRAGMENT),program=gl.createProgram();gl.attachShader(program,vertex);gl.attachShader(program,fragment);gl.linkProgram(program);gl.deleteShader(vertex);gl.deleteShader(fragment);
 if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
 const geometry=createFabricGeometry(type,quality),buffers={};
 for(const name of ['vertices','triangles','lines','nodes']){const buffer=gl.createBuffer();gl.bindBuffer(name==='vertices'?gl.ARRAY_BUFFER:gl.ELEMENT_ARRAY_BUFFER,buffer);gl.bufferData(name==='vertices'?gl.ARRAY_BUFFER:gl.ELEMENT_ARRAY_BUFFER,geometry[name],gl.STATIC_DRAW);buffers[name]=buffer;}
 const uniforms={};for(const name of ['Time','Workspace','Pass','Dpr','Motion','Impulse','Strand','Sidebar','Pointer'])uniforms[name]=gl.getUniformLocation(program,`u${name}`);
 return {program,geometry,buffers,uniforms,attribute:gl.getAttribLocation(program,'aFabric')};
}
function release(item){if(!item.resources)return;for(const buffer of Object.values(item.resources.buffers))item.gl.deleteBuffer(buffer);item.gl.deleteProgram(item.resources.program);item.resources=null;}
export class VisualEngine{
 constructor(getSettings=()=>({})){
  this.getSettings=getSettings;this.canvases=new Map();this.time=12;this.last=null;this.raf=0;this.running=false;this.projection=null;this.seen=new Set();this.impulse={pulse:0,convergence:0,red:0,stability:0,strand:0};this.dirty=true;this.autoCeiling='high';this.frameSamples=[];
  this.pointer={x:0,y:0,tx:0,ty:0};
  this.pointerMove=event=>{const w=Math.max(1,globalThis.innerWidth||1),h=Math.max(1,globalThis.innerHeight||1);this.pointer.tx=Math.max(-1,Math.min(1,event.clientX/w*2-1));this.pointer.ty=Math.max(-1,Math.min(1,event.clientY/h*2-1));};
  globalThis.addEventListener?.('pointermove',this.pointerMove,{passive:true});
  this.tick=this.tick.bind(this);this.visibility=()=>{this.last=null;if(globalThis.document?.hidden){cancelAnimationFrame(this.raf);this.raf=0;}else this.schedule();};
  globalThis.document?.addEventListener('visibilitychange',this.visibility);
  this.resizeObserver=typeof ResizeObserver==='function'?new ResizeObserver(entries=>{for(const entry of entries){const item=this.canvases.get(entry.target.id);if(item)this.sizeOne(item,entry.contentRect);}this.dirty=true;this.schedule();}):null;
  this.intersectionObserver=typeof IntersectionObserver==='function'?new IntersectionObserver(entries=>{for(const entry of entries){const item=this.canvases.get(entry.target.id);if(item)item.visible=entry.isIntersecting;}this.last=null;this.dirty=true;this.schedule();}):null;
  this.debug=typeof location!=='undefined'&&new URLSearchParams(location.search).get('debug')==='1';
  if(this.debug)this.performance={fps:0,frameTime:0,drawCalls:0,triangles:0,points:0,quality:'balanced',renderer:'WebGL'};
 }
 register(id,type){
  const canvas=document.getElementById(id);if(!canvas)return;
  const old=this.canvases.get(id);if(old?.canvas===canvas)return;if(old){release(old);this.resizeObserver?.unobserve(old.canvas);this.intersectionObserver?.unobserve(old.canvas);}
  let gl=null;
  try{gl=canvas.getContext('webgl',{alpha:true,antialias:true,premultipliedAlpha:true,powerPreference:'high-performance',failIfMajorPerformanceCaveat:false});}catch(error){this.attachFallback(canvas,type,error?.message||'WebGL initialization failed');return;}
  if(!gl){this.attachFallback(canvas,type,'WebGL unavailable');return;}
  const item={canvas,type,gl,visible:true,quality:null,forcedQuality:null,resources:null,w:0,h:0,lostContext:false,restoreCount:0,remeasureAttempts:0,failed:false};
  item.lost=event=>{event.preventDefault();item.resources=null;item.lostContext=true;item.restoreCount+=1;if(item.restoreCount>2){item.failed=true;this.attachFallback(canvas,type,'Repeated WebGL context loss');}};
  item.restored=()=>{if(item.failed)return;item.lostContext=false;item.quality=null;item.forcedQuality='safe';item.restoreCount+=1;if(item.restoreCount>2){item.failed=true;this.attachFallback(canvas,type,'Repeated WebGL restore');return;}this.clearFallback(canvas);this.dirty=true;this.schedule();};
  canvas.addEventListener('webglcontextlost',item.lost);canvas.addEventListener('webglcontextrestored',item.restored);
  this.canvases.set(id,item);this.resizeObserver?.observe(canvas);this.intersectionObserver?.observe(canvas);this.sizeOne(item,canvas.getBoundingClientRect());this.dirty=true;this.schedule();
 }
 attachFallback(canvas,type,reason='Visual renderer unavailable'){canvas.dataset.visualUnavailable=reason;canvas.dataset.visualType=type;canvas.parentElement?.classList.add('visual-fallback');globalThis.document?.documentElement?.setAttribute('data-visuals-ready','fallback');}
 clearFallback(canvas){delete canvas.dataset.visualUnavailable;canvas.parentElement?.classList.remove('visual-fallback');}
 sizeOne(item,rect){const width=Math.max(0,rect?.width||item.canvas.clientWidth||0),height=Math.max(0,rect?.height||item.canvas.clientHeight||0);if(width<2||height<2){if(item.remeasureAttempts<4){item.remeasureAttempts+=1;setTimeout(()=>{if(item.canvas.isConnected)this.sizeOne(item,item.canvas.getBoundingClientRect());},50*item.remeasureAttempts);}return;}item.remeasureAttempts=0;item.w=width;item.h=height;const requested=this.effectiveQuality(this.getSettings()?.quality||'balanced'),cap=requested==='high'?1.5:requested==='balanced'?1.25:1;item.dpr=Math.min(globalThis.devicePixelRatio||1,cap);const w=Math.max(1,Math.round(width*item.dpr)),h=Math.max(1,Math.round(height*item.dpr));if(item.canvas.width!==w||item.canvas.height!==h){item.canvas.width=w;item.canvas.height=h;}this.clearFallback(item.canvas);this.dirty=true;}
 effectiveQuality(requested='balanced'){const rank={safe:0,reduced:0,balanced:1,high:2};const reverse=['safe','balanced','high'];const cap=rank[this.autoCeiling]??2,current=rank[requested]??1;return reverse[Math.min(cap,current)];}
 resize(){for(const item of this.canvases.values())this.sizeOne(item,item.canvas.getBoundingClientRect());this.schedule();}
 setProjection(projection){this.projection=projection;this.dirty=true;this.schedule();}
 consume(event){const id=event?.id||event?.event_id;if(id&&this.seen.has(id))return;const impulse=eventImpulse(event);if(!impulse)return;if(id){this.seen.add(id);if(this.seen.size>2048)this.seen.delete(this.seen.values().next().value);}Object.assign(this.impulse,impulse);this.dirty=true;this.schedule();}
 schedule(){if(this.running&&!this.raf&&!globalThis.document?.hidden&&Array.from(this.canvases.values()).some(x=>x.visible&&x.w&&x.h))this.raf=requestAnimationFrame(this.tick);}
 start(){if(this.running)return;this.running=true;this.last=null;this.dirty=true;this.schedule();}
 stop(){this.running=false;if(this.raf)cancelAnimationFrame(this.raf);this.raf=0;this.last=null;}
 tick(timestamp){
  this.raf=0;if(!this.running||globalThis.document?.hidden)return;
  const settings=this.getSettings()||{},delta=this.last===null?0:Math.max(0,(timestamp-this.last)/1000);this.last=timestamp;
  this.time=advanceTime(this.time,delta,settings);const animated=settings.motion!==false&&!settings.reducedMotion&&!settings.visualTest;
  if(animated){this.pointer.x+=(this.pointer.tx-this.pointer.x)*.065;this.pointer.y+=(this.pointer.ty-this.pointer.y)*.065;}
  if(animated||this.dirty){this.draw(settings);this.dirty=false;}
  if(animated){const decay=Math.exp(-Math.min(delta,.05)*.65);for(const name in this.impulse)this.impulse[name]*=decay;this.schedule();}
 }
 draw(settings=this.getSettings()||{}){
  const begin=performance.now();let calls=0,triangles=0,points=0;
  for(const item of this.canvases.values()){
   if(!item.visible||!item.w||!item.h||item.lostContext||item.failed)continue;
   const gl=item.gl,quality=item.forcedQuality||this.effectiveQuality(TIERS[settings.quality]?settings.quality:'balanced');
   try{if(item.quality!==quality){release(item);item.resources=resource(gl,item.type,quality);item.quality=quality;}
   const r=item.resources,u=r.uniforms;
   gl.viewport(0,0,item.canvas.width,item.canvas.height);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.disable(gl.DEPTH_TEST);gl.enable(gl.BLEND);gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);gl.useProgram(r.program);
   gl.bindBuffer(gl.ARRAY_BUFFER,r.buffers.vertices);gl.enableVertexAttribArray(r.attribute);gl.vertexAttribPointer(r.attribute,4,gl.FLOAT,false,16,0);
   gl.uniform1f(u.Time,settings.visualTest?12:this.time);gl.uniform1f(u.Workspace,item.type==='workspace'?1:0);gl.uniform1f(u.Dpr,item.dpr);gl.uniform1f(u.Motion,settings.reducedMotion?0:1);
   gl.uniform1f(u.Sidebar,item.type==='sidebar'?1:0);
   gl.uniform2f(u.Pointer,settings.visualTest?0:this.pointer.x,settings.visualTest?0:this.pointer.y);
   gl.uniform1f(u.Strand,settings.visualTest?0:this.impulse.strand);
   gl.uniform4f(u.Impulse,settings.visualTest?0:this.impulse.pulse,settings.visualTest?0:this.impulse.convergence,settings.visualTest?0:this.impulse.red,settings.visualTest?0:this.impulse.stability);
   gl.uniform1f(u.Pass,0);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,r.buffers.triangles);gl.drawElements(gl.TRIANGLES,r.geometry.triangles.length,gl.UNSIGNED_SHORT,0);triangles+=r.geometry.triangles.length/3;
   gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);gl.uniform1f(u.Pass,1);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,r.buffers.lines);gl.drawElements(gl.LINES,r.geometry.lines.length,gl.UNSIGNED_SHORT,0);
   gl.uniform1f(u.Pass,2);gl.drawArrays(gl.POINTS,0,r.geometry.vertices.length/4);points+=r.geometry.vertices.length/4;
   gl.uniform1f(u.Pass,3);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,r.buffers.nodes);gl.drawElements(gl.POINTS,r.geometry.nodes.length,gl.UNSIGNED_SHORT,0);points+=r.geometry.nodes.length;calls+=4;
   }catch(error){item.failed=true;release(item);this.attachFallback(item.canvas,item.type,error?.message||'WebGL render failure');console.error('Morphosis visual fallback',item.type,error);continue;}
  }
  const frameTime=performance.now()-begin;if(frameTime<80)this.frameSamples.push(frameTime);if(this.frameSamples.length>60)this.frameSamples.shift();if(this.frameSamples.length===60){const avg=this.frameSamples.reduce((a,b)=>a+b,0)/this.frameSamples.length;if(avg>30&&this.autoCeiling==='balanced'){this.autoCeiling='safe';this.frameSamples=[];for(const item of this.canvases.values())item.quality=null;this.dirty=true;}else if(avg>20&&this.autoCeiling==='high'){this.autoCeiling='balanced';this.frameSamples=[];for(const item of this.canvases.values())item.quality=null;this.dirty=true;}}
  if(this.debug){Object.assign(this.performance,{frameTime,drawCalls:calls,triangles,points,quality:this.effectiveQuality(settings.quality||'balanced'),fps:this.last&&this.previousTimestamp?1000/(this.last-this.previousTimestamp):0});this.previousTimestamp=this.last;}
 }
 dispose(){this.stop();this.resizeObserver?.disconnect();this.intersectionObserver?.disconnect();globalThis.document?.removeEventListener('visibilitychange',this.visibility);globalThis.removeEventListener?.('pointermove',this.pointerMove);for(const item of this.canvases.values()){item.canvas.removeEventListener('webglcontextlost',item.lost);item.canvas.removeEventListener('webglcontextrestored',item.restored);release(item);}this.canvases.clear();this.seen.clear();}
}