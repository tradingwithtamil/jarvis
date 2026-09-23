const JSON_HEADERS={"content-type":"application/json; charset=utf-8","cache-control":"no-store"};
export default {
  async fetch(request,env){
    const url=new URL(request.url);
    if(url.pathname==="/health"){
      return new Response(JSON.stringify({ok:true,name:"RD Commander Download",version:"1.0.0",file:"RDCommander-Setup.exe"}),{headers:JSON_HEADERS});
    }
    if(url.pathname==="/download/RDCommander-Setup.exe"){
      const assetUrl=new URL("/download/RDCommander-Setup.exe",url.origin);
      const asset=await env.ASSETS.fetch(new Request(assetUrl,request));
      if(!asset.ok)return asset;
      const h=new Headers(asset.headers);
      h.set("content-type","application/vnd.microsoft.portable-executable");
      h.set("content-disposition",'attachment; filename="RDCommander-Setup.exe"');
      h.set("cache-control","public, max-age=300");
      h.set("x-content-type-options","nosniff");
      return new Response(asset.body,{status:asset.status,headers:h});
    }
    return env.ASSETS.fetch(request);
  }
};
