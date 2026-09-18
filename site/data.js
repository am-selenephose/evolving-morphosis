/** Navigation is presentation configuration; domain state only comes from Python projections. */
export const navItems=[['overview','Overview'],['evolution','Evolution Lab'],['models','Model Ecosystem'],['agents','Agents'],['evaluation','Evaluation'],['deployments','Deployments'],['observability','Observability'],['datasets','Datasets'],['infrastructure','Infrastructure'],['settings','Settings']];
export class ProjectionClient {
 constructor({live=false,fetcher=globalThis.fetch.bind(globalThis),eventSource=globalThis.EventSource}={}){this.live=live;this.fetcher=fetcher;this.EventSource=eventSource;this.sequence=0;this.snapshot=null;this.onSnapshot=()=>{};this.onEvent=()=>{};this.onStatus=()=>{};this.pending=null;this.dirty=false;}
 async json(url,options){const r=await this.fetcher(url,options);const body=await r.json();if(!r.ok)throw new Error(body.error||`Request failed (${r.status})`);return body;}
 apply(snapshot){if(!snapshot||typeof snapshot!=='object')throw new Error('Invalid backend projection');this.snapshot=snapshot;this.sequence=Math.max(this.sequence,Number(snapshot.sequence)||0);this.onSnapshot(snapshot);return snapshot;}
 async load(){if(this.live)return this.refresh();const [snapshot,events]=await Promise.all([this.json('generated/system.json'),this.json('generated/events.json')]);if(!snapshot.events)snapshot.events=Array.isArray(events)?events:(events.events||[]);return this.apply(snapshot);}
 refresh(){if(this.pending)return this.pending;this.pending=(async()=>{do{this.dirty=false;this.apply(await this.json('/api/v1/system'));}while(this.dirty);return this.snapshot;})().finally(()=>{this.pending=null});return this.pending;}
 async acceptEvent(event){const seq=Number(event.sequence);if(!Number.isFinite(seq)||seq<=this.sequence)return;this.sequence=seq;this.onEvent(event);if(this.pending)this.dirty=true;return this.refresh();}
 connect(){if(!this.live||!this.EventSource)return;this.stream=new this.EventSource('/api/v1/events');this.stream.addEventListener('domain',event=>{try{this.acceptEvent(JSON.parse(event.data)).catch(error=>this.onStatus(error.message));}catch(error){this.onStatus(error.message)}});this.stream.onopen=()=>this.onStatus('LOCAL EVENT STREAM');this.stream.onerror=()=>this.onStatus('RECONNECTING · last projection retained');}
 async command(name,payload){if(!this.live){if(name!=='evaluate')throw new Error('Open local live mode (?live=1) to execute this command. Backend replay is read-only.');const scenarios=await this.json('generated/scenarios.json');const scenario=(scenarios.scenarios||scenarios)[payload.surface_id];if(!scenario)throw new Error('No backend-generated replay exists for this surface. Open local live mode to evaluate it.');for(const event of scenario.events||[])this.onEvent(event);this.apply(scenario.snapshot);return scenario.result;}
 const command_id=globalThis.crypto?.randomUUID?.()||`ui-${Date.now()}-${Math.random().toString(36).slice(2)}`;
 const result=await this.json('/api/v1/commands',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,payload,command_id})});await this.refresh();return result;}
 dispose(){this.stream?.close();}
}

/** Presentation formatting only: badges reflect explicit serialized fields, never event-name inference. */
export function humanize(value){return String(value??'').replace(/([a-z0-9])([A-Z])/g,'$1 $2').replace(/([A-Z])([A-Z][a-z])/g,'$1 $2').replace(/[_-]+/g,' ');}
export function presentEvent(event){const value=event?.payload?.mutation?.value||{};return {title:humanize(event?.event_type||'Domain event'),status:value.outcome??value.stage??value.status??(typeof value.passed==='boolean'?(value.passed?'PASSED':'FAILED'):null)};}
