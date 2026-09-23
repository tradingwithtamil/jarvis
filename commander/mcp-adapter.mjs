import http from 'node:http';
const UP='https://45-67-52-142.sslip.io/jarvis/mcp';
const server=http.createServer(async(req,res)=>{
  try{
    if(req.method!=='POST'||req.url!=='/mcp'){res.writeHead(404);res.end();return}
    let raw='';for await(const c of req)raw+=c;
    let msg=raw?JSON.parse(raw):{},zero=msg.id===0;
    if(zero)msg={...msg,id:1};
    const h={'content-type':'application/json'};
    for(const k of ['authorization','accept','mcp-protocol-version','mcp-session-id'])if(req.headers[k])h[k]=req.headers[k];
    const r=await fetch(UP,{method:'POST',headers:h,body:JSON.stringify(msg),signal:AbortSignal.timeout(70000)});
    let t=await r.text();
    if(r.status===202){res.writeHead(202);res.end();return}
    if(zero&&t){const j=JSON.parse(t);if(j.id===1)j.id=0;t=JSON.stringify(j)}
    const oh={'content-type':r.headers.get('content-type')||'application/json'};
    for(const k of ['mcp-session-id','mcp-protocol-version']){const v=r.headers.get(k);if(v)oh[k]=v}
    res.writeHead(r.status,oh);res.end(t);
  }catch(e){res.writeHead(502,{'content-type':'application/json'});res.end(JSON.stringify({error:String(e.message||e)}))}
});
server.listen(8794,'127.0.0.1',()=>console.error('Jarvis MCP compatibility adapter listening on 127.0.0.1:8794'));