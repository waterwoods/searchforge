"""app_v2.py - Minimal read-only metrics API (≤150 LoC)"""
import time, sys, asyncio, random
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from core.metrics import metrics_sink, METRICS_BACKEND
    CORE_AVAILABLE = True
except Exception as e:
    print(f"[BOOT] ⚠️  core.metrics import failed: {e}")
    CORE_AVAILABLE, metrics_sink, METRICS_BACKEND = False, None, "unavailable"

app = FastAPI(title="SearchForge Metrics API v2")
print(f"[BOOT] app_v2 using core.metrics backend={METRICS_BACKEND}")

# Load generator state
load_state = {"running": False, "qps": 0, "concurrency": 0, "start_time": 0, "duration": 0}

class SearchRequest(BaseModel):
    query: str = "ping"
    top_k: int = 10
    profile: str = "fast"


@app.get("/admin/health")
async def health():
    """Health check"""
    try:
        if not CORE_AVAILABLE or metrics_sink is None:
            return JSONResponse(status_code=503, content={"ok": False, "error": "core.metrics not available"})
        now_ms = int(time.time() * 1000)
        samples = metrics_sink.snapshot_last_60s(now_ms)
        return {"ok": True, "core_metrics_backend": METRICS_BACKEND, "rows_60s": len(samples), 
                "window_sec": 60, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/metrics/window60s")
async def window60s():
    """Aggregated 60s metrics"""
    try:
        if not CORE_AVAILABLE or metrics_sink is None:
            return {"ok": False, "error": "core.metrics not available"}
        now_ms = int(time.time() * 1000)
        result = metrics_sink.window60s(now_ms)
        return {"ok": True, "window_sec": result["window_sec"], "samples": result["samples"],
                "p95_ms": result["p95_ms"], "tps": result["tps"], "recall_at_10": result["recall_at_10"],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/metrics/series60s")
async def series60s():
    """5s buckets, 60s window, strict alignment + bucket fill"""
    try:
        if not CORE_AVAILABLE or metrics_sink is None:
            return {"ok": False, "error": "core.metrics not available"}
        now_ms = int(time.time() * 1000)
        cutoff_ms = now_ms - 60000
        bucket_ms = 5000
        samples = metrics_sink.snapshot_last_60s(now_ms)
        buckets = {}
        for s in samples:
            ts = s.get("ts", 0)
            if ts < cutoff_ms:
                continue
            bucket_ts = (ts // bucket_ms) * bucket_ms
            if bucket_ts not in buckets:
                buckets[bucket_ts] = {"latencies": [], "recalls": []}
            lat = s.get("latency_ms")
            if lat is not None:
                buckets[bucket_ts]["latencies"].append(lat)
            recall = s.get("recall_at10")
            if recall is not None:
                buckets[bucket_ts]["recalls"].append(recall)
        p95_dict, tps_dict, recall_dict = {}, {}, {}
        for bucket_ts, data in buckets.items():
            lats = data["latencies"]
            if len(lats) >= 3:
                sorted_lats = sorted(lats)
                idx = int(len(sorted_lats) * 0.95)
                p95_dict[bucket_ts] = round(sorted_lats[idx], 2)
            tps_dict[bucket_ts] = round(len(lats) / 5.0, 2)
            recalls = data["recalls"]
            if recalls:
                recall_dict[bucket_ts] = round(sum(recalls) / len(recalls), 4)
        aligned_now_ms = (now_ms // bucket_ms) * bucket_ms
        aligned_cutoff_ms = (cutoff_ms // bucket_ms) * bucket_ms
        p95_series, tps_series, recall_series = [], [], []
        current_ts = aligned_cutoff_ms
        while current_ts <= aligned_now_ms:
            p95_series.append([current_ts, p95_dict.get(current_ts)])
            tps_series.append([current_ts, tps_dict.get(current_ts, 0)])
            recall_series.append([current_ts, recall_dict.get(current_ts)])
            current_ts += bucket_ms
        return {"ok": True, "source": "core", "window_sec": 60, "step_sec": 5,
                "buckets": len(p95_series), "samples": len(samples), "p95": p95_series,
                "tps": tps_series, "recall": recall_series,
                "meta": {"source": "core", "debug": {"now_ms": now_ms, "cutoff_ms": cutoff_ms, "backend": METRICS_BACKEND}},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/search")
async def search(req: SearchRequest):
    """Minimal search endpoint (records metrics only)"""
    try:
        start_ms = time.time() * 1000
        await asyncio.sleep(random.uniform(0.01, 0.05))  # Simulate 10-50ms latency
        latency_ms = time.time() * 1000 - start_ms
        
        # Record to metrics_sink
        if CORE_AVAILABLE and metrics_sink:
            metrics_sink.push({
                "ts": int(start_ms),
                "latency_ms": round(latency_ms, 2),
                "recall_at10": round(random.uniform(0.85, 0.95), 4),
                "mode": "on",
                "profile": req.profile,
                "rerank_hit": 1,
                "cache_hit": 0
            })
        return {"ok": True, "results": [], "latency_ms": round(latency_ms, 2)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _run_load(qps: int, duration: int, concurrency: int):
    """Background load generator"""
    load_state.update({"running": True, "qps": qps, "concurrency": concurrency, 
                       "start_time": time.time(), "duration": duration})
    try:
        batch_size = min(concurrency, max(1, qps))  # Requests per batch
        interval = batch_size / qps if qps > 0 else 0.1  # Wait time between batches
        end_time = time.time() + duration
        while time.time() < end_time and load_state["running"]:
            tasks = [search(SearchRequest()) for _ in range(batch_size)]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(interval)
    except Exception as e:
        print(f"[LOAD] Error: {e}")
    finally:
        load_state["running"] = False


@app.post("/load/start")
async def load_start(qps: int = 12, duration: int = 60, concurrency: int = 16, background: BackgroundTasks = None):
    """Start load generator"""
    if load_state["running"]:
        return {"ok": False, "error": "Load generator already running"}
    asyncio.create_task(_run_load(qps, duration, concurrency))
    return {"ok": True, "qps": qps, "duration": duration, "concurrency": concurrency}


@app.get("/load/status")
async def load_status():
    """Get load generator status"""
    if not load_state["running"]:
        return {"running": False, "qps": 0, "concurrency": 0, "eta_sec": 0}
    elapsed = time.time() - load_state["start_time"]
    eta = max(0, load_state["duration"] - elapsed)
    return {"running": True, "qps": load_state["qps"], "concurrency": load_state["concurrency"], 
            "eta_sec": round(eta, 1), "elapsed_sec": round(elapsed, 1)}

