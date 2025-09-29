from fastapi import FastAPI, Query
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time

app = FastAPI(title="searchforge-rag-api")

REQS = Counter("rag_api_requests_total", "Total requests", ["route"])
LAT = Histogram("rag_api_request_duration_seconds", "Latency", ["route"])

@app.get("/health")
def health():
    REQS.labels("health").inc()
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/search")
def search(q: str = Query(...)):
    REQS.labels("search").inc()
    with LAT.labels("search").time():
        # placeholder result
        return {"query": q, "results": [{"id":"stub","score":0.9}], "qdrant_connected": False}
