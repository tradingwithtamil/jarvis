const http=require('http'),fs=require('fs'),crypto=require('crypto'),path=require('path');
const ROOT=__dirname,cfg=JSON.parse(fs.readFileSync(path.join(ROOT,'config.json'),'utf8')),STATE=path.join(ROOT,'state.json');
let state={devices:{},commands:{}};try{state=JSON.parse(fs.readFileSync(STATE,'utf8'))}catch{}
const persist=()=>{fs.writeFileSync(STATE,JSON.stringify(state,null,2),'utf8')};
const H=s=>crypto.createHash('sha256').update(String(s)).digest('hex');
const same=(a,b)=>{a=Buffer.from(String(a||''));b=Buffer.from(String(b||''));return a.length===b.length&&crypto.timingSafeEqual(a,b)};
const send=(res,n,o)=>{const x=JSON.stringify(o);res.writeHead(n,{'content-type':'application/json','content-length':Buffer.byteLength(x)});res.end(x)};
const read=async req=>{let s='';for await(const c of req){s+=c;if(s.length>2000000)throw Error('body too large')}return s?JSON.parse(s):{}};
const admin=(req,u)=>same((req.headers.authorization||'').replace(/^Bearer\s+/i,''),cfg.adminToken)||same(u.searchParams.get('token'),cfg.adminToken);
const agent=(req,id)=>state.devices[id]&&same(H((req.headers.authorization||'').replace(/^Bearer\s+/i,'')),state.devices[id].tokenHash);
const safeActions=new Set(['read_file','write_file','list_dir','system_status','http_check','trigger']);
function devices(){const n=Date.now();return Object.values(state.devices).map(d=>({deviceId:d.deviceId,name:d.name,platform:d.platform,version:d.version,status:d.lastSeen&&n-new Date(d.lastSeen).getTime()<45000?'online':'offline',lastSeen:d.lastSeen,meta:d.meta||{}}))}
function queue(deviceId,action,args){if(!safeActions.has(action))throw Error('action not allowed');const id=crypto.randomUUID();state.commands[id]={id,deviceId,action,args:args||{},status:'queued',createdAt:new Date().toISOString()};persist();return state.commands[id]}
function wait(id,ms){return new Promise(ok=>{const s=Date.now(),t=setInterval(()=>{const c=state.commands[id];if(!c){clearInterval(t);return ok({ok:false,error:'missing command'})}if(c.status==='done'||c.status==='error'){clearInterval(t);return ok(Object.assign({ok:c.status==='done'},c))}if(Date.now()-s>ms){clearInterval(t);ok({ok:false,id,status:c.status,error:'timeout'})}},250)})}
const tools=[
{name:'list_devices',description:'List RD Commander devices.',inputSchema:{type:'object',properties:{}}},
{name:'read_file',description:'Read a UTF-8 file from an allowlisted local path.',inputSchema:{type:'object',properties:{device_id:{type:'string'},path:{type:'string'}},required:['device_id','path']}},
{name:'write_file',description:'Write a UTF-8 file to an allowlisted local path.',inputSchema:{type:'object',properties:{device_id:{type:'string'},path:{type:'string'},content:{type:'string'},mode:{type:'string',enum:['rewrite','append']}},required:['device_id','path','content']}},
{name:'list_directory',description:'List an allowlisted local directory.',inputSchema:{type:'object',properties:{device_id:{type:'string'},path:{type:'string'}},required:['device_id','path']}},
{name:'system_status',description:'Get OS, RAM, uptime and disk status.',inputSchema:{type:'object',properties:{device_id:{type:'string'}},required:['device_id']}},
{name:'http_check',description:'Check an HTTP or HTTPS endpoint from the selected device.',inputSchema:{type:'object',properties:{device_id:{type:'string'},url:{type:'string'},timeout_ms:{type:'integer'}},required:['device_id','url']}},
{name:'trigger_action',description:'Trigger a pre-approved local maintenance action by name.',inputSchema:{type:'object',properties:{device_id:{type:'string'},name:{type:'string'}},required:['device_id','name']}}
];
async function mcp(req,res,u){if(!admin(req,u))return send(res,401,{error:'unauthorized'});const m=await read(req);if(!m.id&&m.method)return send(res,202,{});
let result;if(m.method==='initialize')result={protocolVersion:m.params&&m.params.protocolVersion||'2025-06-18',capabilities:{tools:{}},serverInfo:{name:'RD Commander',version:'0.1.2'}};
else if(m.method==='tools/list')result={tools:tools};
else if(m.method==='tools/call'){const n=m.params&&m.params.name,a=m.params&&m.params.arguments||{};if(n==='list_devices')result={content:[{type:'text',text:JSON.stringify(devices(),null,2)}]};
else{const map={read_file:'read_file',write_file:'write_file',list_directory:'list_dir',system_status:'system_status',http_check:'http_check',trigger_action:'trigger'},act=map[n];
if(!act)return send(res,200,{jsonrpc:'2.0',id:m.id,error:{code:-32601,message:'unknown tool'}});
if(!state.devices[a.device_id])result={content:[{type:'text',text:'unknown device'}],isError:true};
else{const c=queue(a.device_id,act,a),o=await wait(c.id,60000);result={content:[{type:'text',text:JSON.stringify(o,null,2)}],isError:!o.ok}}}}
else return send(res,200,{jsonrpc:'2.0',id:m.id,error:{code:-32601,message:'method not found'}});send(res,200,{jsonrpc:'2.0',id:m.id,result:result})}
http.createServer(async(req,res)=>{try{const u=new URL(req.url,'http://x');
if(req.method==='GET'&&u.pathname==='/health')return send(res,200,{ok:true,name:'RD Commander Relay',version:'0.1.2',devices:devices().length});
if(req.method==='POST'&&u.pathname==='/agent/register'){const b=await read(req);if(!b.deviceId||!b.name)return send(res,400,{error:'missing fields'});const ip=String(req.headers['x-forwarded-for']||req.socket.remoteAddress||'').split(',')[0].trim();const bootstrapOK=cfg.bootstrapEnabled&&same(req.headers['x-bootstrap-key'],cfg.bootstrapSecret);const pendingOK=cfg.pendingEnrollments&&cfg.pendingEnrollments[b.deviceId]===ip&&!state.devices[b.deviceId];if(!bootstrapOK&&!pendingOK)return send(res,403,{error:'registration disabled'});const tok=crypto.randomBytes(48).toString('base64url');state.devices[b.deviceId]={deviceId:b.deviceId,name:b.name,platform:b.platform,version:b.version,tokenHash:H(tok),registeredAt:new Date().toISOString(),lastSeen:new Date().toISOString(),meta:b.meta||{}};persist();return send(res,200,{ok:true,agentToken:tok})}
if(req.method==='POST'&&u.pathname==='/agent/heartbeat'){const b=await read(req);if(!agent(req,b.deviceId))return send(res,401,{error:'unauthorized'});Object.assign(state.devices[b.deviceId],{lastSeen:new Date().toISOString(),version:b.version,meta:b.meta||{}});persist();return send(res,200,{ok:true})}
if(req.method==='GET'&&u.pathname==='/agent/poll'){const id=u.searchParams.get('deviceId');if(!agent(req,id))return send(res,401,{error:'unauthorized'});const now=Date.now();for(const c of Object.values(state.commands))if(c.deviceId===id&&c.status==='dispatched'&&now-new Date(c.dispatchedAt).getTime()>120000)c.status='queued';const c=Object.values(state.commands).find(x=>x.deviceId===id&&x.status==='queued');if(!c)return send(res,200,{command:null});c.status='dispatched';c.dispatchedAt=new Date().toISOString();persist();return send(res,200,{command:c})}
if(req.method==='POST'&&u.pathname==='/agent/result'){const b=await read(req);if(!agent(req,b.deviceId))return send(res,401,{error:'unauthorized'});const c=state.commands[b.commandId];if(!c)return send(res,404,{error:'missing'});c.status=b.ok?'done':'error';c.completedAt=new Date().toISOString();c.output=String(b.output||'').slice(0,1500000);c.error=b.error?String(b.error).slice(0,10000):null;persist();return send(res,200,{ok:true})}
if(req.method==='GET'&&u.pathname==='/api/devices'){if(!admin(req,u))return send(res,401,{error:'unauthorized'});return send(res,200,{devices:devices()})}
if(req.method==='POST'&&u.pathname==='/api/command'){if(!admin(req,u))return send(res,401,{error:'unauthorized'});const b=await read(req);if(!state.devices[b.deviceId])return send(res,404,{error:'unknown device'});if(!safeActions.has(b.action))return send(res,400,{error:'action not allowed'});return send(res,202,{command:queue(b.deviceId,b.action,b.args)})}
if(req.method==='GET'&&u.pathname.startsWith('/api/command/')){if(!admin(req,u))return send(res,401,{error:'unauthorized'});const id=u.pathname.split('/').pop();return send(res,state.commands[id]?200:404,{command:state.commands[id]||null})}
if(req.method==='POST'&&u.pathname==='/mcp')return mcp(req,res,u);return send(res,404,{error:'not found'})
}catch(e){send(res,500,{error:String(e.message||e)})}}).listen(cfg.port||8792,cfg.host||'127.0.0.1',()=>console.log('RD Commander Relay online'));