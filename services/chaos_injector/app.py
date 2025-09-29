from fastapi import FastAPI
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
CHAOS=Counter("chaos_events_total","chaos events",["type","status"])
app=FastAPI(title="searchforge-chaos")
@app.post("/chaos/latency") def latency(): CHAOS.labels("latency","injected").inc(); return {"ok":1}
@app.post("/chaos/packet-loss") def pl(): CHAOS.labels("packet-loss","injected").inc(); return {"ok":1}
@app.post("/chaos/disconnect") def disc(): CHAOS.labels("disconnect","injected").inc(); return {"ok":1}
@app.get("/metrics") def m(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
