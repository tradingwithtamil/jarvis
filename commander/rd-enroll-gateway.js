const http=require('http'),fs=require('fs'),crypto=require('crypto');
const ROOT=__dirname,CFG=JSON.parse(fs.readFileSync(ROOT+'/config.json','utf8').replace(/^\\uFEFF/,''));
const PORT=CFG.rdEnrollPort||8794,STATE_PATH=ROOT+'/rd-enroll-state.json';
const RD_BASE=CFG.rdPublicBase||'https://45-67-52-142.sslip.io/rd';
const RELAY='http://127.0.0.1:8792',PIN_HASH=CFG.mcpOwnerPinHash||'';
let S={pending:{}};try{S=Object.assign(S,JSON.parse(fs.readFileSync(STATE_PATH,'utf8')))}catch{}
const now=()=>Date.now(),rnd=()=>crypto.randomBytes(36).toString('base64url'),sha=s=>crypto.createHash('sha256').update(String(s)).digest('hex');
const save=()=>fs.writeFileSync(STATE_PATH,JSON.stringify(S,null,2),'utf8');
const clean=()=>{const t=now();for(const [k,v] of Object.entries(S.pending||{}))if(v.expiresAt<t)delete S.pending[k]};
const json=(res,n,o)=>{const x=JSON.stringify(o);res.writeHead(n,{'content-type':'application/json','content-length':Buffer.byteLength(x),'cache-control':'no-store'});res.end(x)};
const html=(res,n,x)=>{res.writeHead(n,{'content-type':'text/html; charset=utf-8','content-length':Buffer.byteLength(x),'cache-control':'no-store','x-frame-options':'DENY'});res.end(x)};
const body=async req=>{let s='';for await(const c of req){s+=c;if(s.length>200000)throw Error('body too large')}return s};
const form=s=>Object.fromEntries(new URLSearchParams(s));
const esc=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function findByCode(code){return Object.entries(S.pending).find(([,v])=>v.code===String(code||'').trim())}
async function relayEnroll(v){
  const r=await fetch(RELAY+'/api/enroll-device',{method:'POST',headers:{'content-type':'application/json','authorization':'Bearer '+CFG.adminToken},body:JSON.stringify({deviceId:v.deviceId,name:v.name,platform:v.platform,version:v.version,meta:{fingerprint:v.fingerprint}}),signal:AbortSignal.timeout(15000)});
  const t=await r.text();let j={};try{j=JSON.parse(t)}catch{}if(!r.ok)throw Error(j.error||('HTTP '+r.status));return j;
}
function page(code,v,msg){
  const notice=msg?'<p style="color:#67e8ad">'+esc(msg)+'</p>':'';
  const formHtml=msg?'':'<form method="post" action="'+RD_BASE+'/device/approve"><input type="hidden" name="code" value="'+esc(code)+'"><input name="pin" inputmode="numeric" placeholder="Owner PIN" required><button>Approve Device</button></form>';
  return '<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>RD Commander Approval</title><style>body{font-family:system-ui;background:#08111a;color:#eaf2f8;display:grid;place-items:center;min-height:100vh;margin:0}.c{width:min(560px,calc(100% - 32px));padding:28px;border:1px solid #294154;border-radius:18px;background:#0b1721}input,button{padding:12px 14px;border-radius:10px;border:1px solid #34506a;margin-top:10px}input{width:100%;box-sizing:border-box;background:#071018;color:white}button{background:#36d399;color:#06120d;font-weight:800}.muted{color:#91a8b9}</style><div class="c"><h1>RD Commander</h1><p>Approve this device?</p><p><b>'+esc(v.name)+'</b><br><span class="muted">ID: '+esc(v.deviceId)+'<br>Platform: '+esc(v.platform)+'<br>Fingerprint: '+esc(String(v.fingerprint||'').slice(0,16))+'…</span></p>'+notice+formHtml+'</div>';
}
async function requestDevice(req,res){
  const x=JSON.parse((await body(req))||'{}');
  const deviceId=String(x.deviceId||'').trim(),name=String(x.name||'').trim(),fingerprint=String(x.fingerprint||'').trim();
  if(!/^[A-Za-z0-9._-]{3,120}$/.test(deviceId)||!name||name.length>160||!/^[0-9a-f]{32,128}$/i.test(fingerprint))return json(res,400,{error:'invalid_device'});
  const claim=rnd(),code=String(crypto.randomInt(100000,1000000));
  S.pending[sha(claim)]={code,deviceId,name,platform:String(x.platform||'win32'),version:String(x.version||'0.1.1'),fingerprint,createdAt:now(),expiresAt:now()+10*60*1000,approved:false,agentToken:null};
  clean();save();
  return json(res,201,{ok:true,claim,code,approvalUrl:RD_BASE+'/device/approve?code='+code,expiresAt:new Date(now()+10*60*1000).toISOString()});
}
function status(req,res,u){
  const claim=String(u.searchParams.get('claim')||''),v=S.pending[sha(claim)];
  if(!v)return json(res,404,{error:'claim_not_found'});
  if(v.expiresAt<now()){delete S.pending[sha(claim)];save();return json(res,410,{error:'claim_expired'})}
  if(!v.approved)return json(res,200,{ok:true,state:'pending',expiresAt:new Date(v.expiresAt).toISOString()});
  return json(res,200,{ok:true,state:'approved',deviceId:v.deviceId,agentToken:v.agentToken,relayUrl:'https://45-67-52-142.sslip.io/jarvis'});
}
async function approveGet(req,res,u){
  const code=String(u.searchParams.get('code')||'').trim();
  if(!code)return html(res,200,'<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>RD Commander Approval</title><style>body{font-family:system-ui;background:#08111a;color:#eaf2f8;display:grid;place-items:center;min-height:100vh;margin:0}.c{width:min(520px,calc(100% - 32px));padding:28px;border:1px solid #294154;border-radius:18px;background:#0b1721}input,button{padding:12px 14px;border-radius:10px;border:1px solid #34506a;margin-top:10px}input{width:100%;box-sizing:border-box;background:#071018;color:white}button{background:#36d399;color:#06120d;font-weight:800}</style><div class="c"><h1>RD Commander</h1><p>Enter the 6-digit code shown on the new PC / VPS.</p><form method="get" action="'+RD_BASE+'/device/approve"><input name="code" inputmode="numeric" maxlength="6" placeholder="Device code" required><button>Continue</button></form></div>');
  const hit=findByCode(code);
  if(!hit)return html(res,404,'<h2>Enrollment code not found or expired.</h2>');
  const [,v]=hit;if(v.expiresAt<now())return html(res,410,'<h2>Enrollment code expired.</h2>');
  return html(res,200,page(code,v,v.approved?'Already approved. Return to the new PC.':''));
}
async function approvePost(req,res){
  const f=form(await body(req)),hit=findByCode(f.code);
  if(!hit)return html(res,404,'<h2>Enrollment code not found or expired.</h2>');
  const [key,v]=hit;if(v.expiresAt<now())return html(res,410,'<h2>Enrollment code expired.</h2>');
  if(!PIN_HASH||sha(f.pin||'')!==PIN_HASH)return html(res,403,'<h2>Invalid owner PIN</h2>');
  if(!v.approved){const issued=await relayEnroll(v);v.agentToken=issued.agentToken;v.approved=true;v.approvedAt=now();S.pending[key]=v;save();}
  return html(res,200,page(v.code,v,'Approved. RD Commander will finish installation automatically on the new PC.'));
}
http.createServer(async(req,res)=>{try{
  clean();const u=new URL(req.url,'http://x');
  if(req.method==='GET'&&u.pathname==='/health')return json(res,200,{ok:true,name:'RD Commander Enrollment Gateway',version:'0.1.0'});
  if(req.method==='POST'&&u.pathname==='/device/request')return requestDevice(req,res);
  if(req.method==='GET'&&u.pathname==='/device/status')return status(req,res,u);
  if(req.method==='GET'&&u.pathname==='/device/approve')return approveGet(req,res,u);
  if(req.method==='POST'&&u.pathname==='/device/approve')return approvePost(req,res);
  return json(res,404,{error:'not_found'});
}catch(e){json(res,500,{error:String(e.message||e)})}}).listen(PORT,'127.0.0.1',()=>console.log('RD Commander Enrollment Gateway online',PORT));