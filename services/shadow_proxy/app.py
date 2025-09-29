import os, asyncio
import httpx
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

PRIMARY=os.getenv("PRIMARY_URL","http://rag-api:8080")
CANARY=os.getenv("CANARY_URL", PRIMARY)
MIRROR_RATE=float(os.getenv("MIRROR_RATE","0.1"))

app=FastAPI(title="searchforge-shadow-proxy")
MIR=Counter("shadow_mirrored_total","mirrored reqs")
LAT=Histogram("shadow_proxy_request_duration_seconds","proxy latency")

@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.api_route("/{path:path}", methods=["GET","POST"])
async def proxy(path:str, request:Request):
    q = str(request.query_params) or ""
    url = f"{PRIMARY}/{path}"
    async with httpx.AsyncClient(timeout=5) as c:
        with LAT.time():
            primary = await c.request(request.method, url, params=request.query_params)
    # mirror best-effort
    try:
        if MIRROR_RATE>0:
            asyncio.create_task(httpx.AsyncClient(timeout=5).request(request.method, f"{CANARY}/{path}", params=request.query_params))
            MIR.inc()
    except: pass
    return Response(content=primary.content, status_code=primary.status_code, media_type=primary.headers.get("content-type","application/json"))
