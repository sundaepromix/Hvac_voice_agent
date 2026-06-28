#!/usr/bin/env bash
# Re-point the Vapi assistant's custom-LLM (model) + server URLs at a base host.
#
#   scripts/repoint-vapi.sh https://api.workflowauth.com
#
# Reads VAPI_API_KEY, VAPI_WEBHOOK_SECRET, NEXT_PUBLIC_VAPI_ASSISTANT_ID from
# the repo-root .env. Vapi auto-appends "/chat/completions" to model.url, so we
# point it at the secret-in-path route that survives that append cleanly.
set -euo pipefail

BASE="${1:-}"
if [ -z "$BASE" ]; then
  echo "usage: $0 https://api.yourdomain.com"
  exit 1
fi
BASE="${BASE%/}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || { echo "no .env at $ENV_FILE"; exit 1; }
getenv() { grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2-; }

export VAPI_KEY="$(getenv VAPI_API_KEY)"
export VAPI_SECRET="$(getenv VAPI_WEBHOOK_SECRET)"
export VAPI_AID="$(getenv NEXT_PUBLIC_VAPI_ASSISTANT_ID)"
export MODEL_URL="$BASE/api/calls/vapi/k/$VAPI_SECRET"
export SERVER_URL="$BASE/api/calls/webhooks/vapi/"

if [ -z "$VAPI_KEY" ] || [ -z "$VAPI_AID" ]; then
  echo "Missing VAPI_API_KEY or NEXT_PUBLIC_VAPI_ASSISTANT_ID in .env"
  exit 1
fi

echo "Pointing assistant $VAPI_AID at:"
echo "  model.url  = $MODEL_URL"
echo "  server.url = $SERVER_URL"

node -e '
const https=require("https");
const {VAPI_KEY,VAPI_AID,VAPI_SECRET,MODEL_URL,SERVER_URL}=process.env;
function once(method,path,body){return new Promise((res,rej)=>{const data=body?JSON.stringify(body):null;const r=https.request({host:"api.vapi.ai",path,method,headers:{Authorization:"Bearer "+VAPI_KEY,"Content-Type":"application/json",...(data?{"Content-Length":Buffer.byteLength(data)}:{})}},resp=>{let b="";resp.on("data",c=>b+=c);resp.on("end",()=>res({status:resp.statusCode,body:b}));});r.on("error",rej);r.setTimeout(30000,()=>r.destroy(new Error("timeout")));if(data)r.write(data);r.end();});}
async function req(m,p,b){let e;for(let i=0;i<4;i++){try{return await once(m,p,b);}catch(x){e=x;await new Promise(r=>setTimeout(r,2000));}}throw e;}
(async()=>{
  const g=await req("GET","/assistant/"+VAPI_AID);
  if(g.status>=300){console.error("GET failed",g.status,g.body.slice(0,300));process.exit(1);}
  const a=JSON.parse(g.body);
  const model=a.model||{};
  model.url=MODEL_URL;
  const patch={model,server:{url:SERVER_URL,secret:VAPI_SECRET}};
  const p=await req("PATCH","/assistant/"+VAPI_AID,patch);
  if(p.status>=300){console.error("PATCH failed",p.status,p.body.slice(0,400));process.exit(1);}
  const o=JSON.parse(p.body);
  console.log("OK ("+p.status+")");
  console.log("  model.url  =",o.model&&o.model.url);
  console.log("  server.url =",o.server&&o.server.url);
})().catch(e=>{console.error("ERR",e.message);process.exit(1);});
'
