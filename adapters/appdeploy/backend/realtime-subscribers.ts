import { db, error, json, ws } from '@appdeploy/sdk';

const SUBSCRIPTIONS_TABLE = 'entity_subscriptions';
type SubscriptionRecord = { id:string; entity_type:string; entity_id:string; connection_id:string; created_at:number };
async function listSubscriptions(): Promise<SubscriptionRecord[]> { const { items } = await db.list(SUBSCRIPTIONS_TABLE,{limit:500}); return items as SubscriptionRecord[]; }
export async function removeSubscriptionsByConnection(connectionId:string) { const items=await listSubscriptions(); const ids=items.filter((item)=>item.connection_id===connectionId).map((item)=>item.id); if(ids.length) await db.delete(SUBSCRIPTIONS_TABLE,ids); }
async function addSubscription(entityType:string,entityId:string,connectionId:string) { const items=await listSubscriptions(); const exists=items.some((item)=>item.entity_type===entityType&&item.entity_id===entityId&&item.connection_id===connectionId); if(!exists) await db.add(SUBSCRIPTIONS_TABLE,[{entity_type:entityType,entity_id:entityId,connection_id:connectionId,created_at:Date.now()}]); }
async function removeSubscription(entityType:string,entityId:string,connectionId:string) { const items=await listSubscriptions(); const ids=items.filter((item)=>item.entity_type===entityType&&item.entity_id===entityId&&item.connection_id===connectionId).map((item)=>item.id); if(ids.length) await db.delete(SUBSCRIPTIONS_TABLE,ids); }
export async function notifySubscribers(entityType:string,entityId:string,payload:unknown) { const items=await listSubscriptions(); const targets=Array.from(new Set(items.filter((item)=>item.entity_type===entityType&&item.entity_id===entityId).map((item)=>item.connection_id))); if(!targets.length) return; await ws.send(targets,{v:1,type:'entity.update',payload:{entity_type:entityType,entity_id:entityId,data:payload}}); }
export const realtimeSubscriptionRoutes = {
  'POST /api/subscriptions':[async({body})=>{const payload=(body||{}) as Record<string,string>; if(!payload.entity_type||!payload.entity_id||!payload.connection_id) return error('entity_type, entity_id, connection_id are required',400); await addSubscription(payload.entity_type,payload.entity_id,payload.connection_id); return json({ok:true});}],
  'POST /api/subscriptions/remove':[async({body})=>{const payload=(body||{}) as Record<string,string>; if(!payload.entity_type||!payload.entity_id||!payload.connection_id) return error('entity_type, entity_id, connection_id are required',400); await removeSubscription(payload.entity_type,payload.entity_id,payload.connection_id); return json({ok:true});}],
};
