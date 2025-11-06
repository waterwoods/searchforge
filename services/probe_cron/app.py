import os, time, threading, requests
from prometheus_client import Counter, Histogram, start_http_server

RAG = os.getenv("RAG_URL","http://rag-api:8080")
REQ = Counter("probe_requests_total","probe reqs",["query"])
FAIL= Counter("probe_failures_total","probe fails",["query"])
LAT = Histogram("probe_latency_seconds","probe latency",["query"])

QUERIES = ["laptop","headphones","ssd","monitor"]

def loop():
    while True:
        for q in QUERIES:
            t0=time.time()
            try:
                r = requests.get(f"{RAG}/search", params={"q":q}, timeout=2)
                r.raise_for_status()
                REQ.labels(q).inc()
            except Exception:
                FAIL.labels(q).inc()
            finally:
                LAT.labels(q).observe(time.time()-t0)
        time.sleep(5)

if __name__=="__main__":
    start_http_server(8001)
    threading.Thread(target=loop, daemon=True).start()
    while True: time.sleep(3600)
