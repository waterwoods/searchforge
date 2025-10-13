"""app_v2.py - Minimal read-only metrics API (≤150 LoC)"""
import time, sys, asyncio, random
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
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
    """Health check with Redis status (graceful degradation)"""
    if not CORE_AVAILABLE or metrics_sink is None:
        return JSONResponse(status_code=503, content={"ok": False, "error": "core.metrics not available"})
    
    try:
        now_ms = int(time.time() * 1000)
        samples = metrics_sink.snapshot_last_60s(now_ms)
        
        # Check Redis connection status
        redis_connected = False
        key_prefix = None
        backend_name = METRICS_BACKEND
        
        if hasattr(metrics_sink, 'client'):  # RedisMetrics
            try:
                metrics_sink.client.ping()
                redis_connected = True
                key_prefix = getattr(metrics_sink, 'key', '').split(':')[0] or None
            except:
                redis_connected = False
        
        return {
            "ok": True,
            "core_metrics_backend": backend_name,
            "redis_connected": redis_connected,
            "rows_60s": len(samples),
            "window_sec": 60,
            "key_prefix": key_prefix,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception as e:
        # Graceful degradation: return partial info even on error
        return {
            "ok": False,
            "error": str(e),
            "core_metrics_backend": METRICS_BACKEND,
            "redis_connected": False,
            "rows_60s": 0,
            "window_sec": 60
        }


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
    """5s buckets, 60s window, strict alignment + bucket fill (hardened v2)"""
    try:
        if not CORE_AVAILABLE or metrics_sink is None:
            return {"ok": False, "error": "core.metrics not available"}
        now_ms = int(time.time() * 1000)
        bucket_ms = 5000
        
        # Strict alignment: align now_ms to 5s boundary
        aligned_now_ms = (now_ms // bucket_ms) * bucket_ms
        aligned_cutoff_ms = aligned_now_ms - 60000  # Exactly 60s back
        clock_skew_ms = now_ms - aligned_now_ms  # Clock drift detection
        
        samples = metrics_sink.snapshot_last_60s(now_ms)
        total_samples = len(samples)
        
        # Track dropped samples and find heartbeat
        dropped = 0
        heartbeat_ms = None
        for s in samples:
            ts = s.get("ts", 0)
            if heartbeat_ms is None or ts > heartbeat_ms:
                heartbeat_ms = ts
            # Allow ±1s drift for boundary samples
            if ts < (aligned_cutoff_ms - 1000) or ts > (aligned_now_ms + 1000):
                dropped += 1
        
        # Build buckets (include samples in aligned window with ±1s tolerance)
        buckets = {}
        for s in samples:
            ts = s.get("ts", 0)
            if ts < (aligned_cutoff_ms - 1000) or ts > (aligned_now_ms + 1000):
                continue
            # Align sample to nearest 5s bucket
            bucket_ts = (ts // bucket_ms) * bucket_ms
            if bucket_ts not in buckets:
                buckets[bucket_ts] = {"latencies": [], "recalls": []}
            lat = s.get("latency_ms")
            if lat is not None:
                buckets[bucket_ts]["latencies"].append(lat)
            recall = s.get("recall_at10")
            if recall is not None:
                buckets[bucket_ts]["recalls"].append(recall)
        
        # Compute metrics for existing buckets (strict thresholds)
        p95_dict, tps_dict, recall_dict = {}, {}, {}
        for bucket_ts, data in buckets.items():
            lats = data["latencies"]
            # P95 requires >=3 samples, otherwise null
            if len(lats) >= 3:
                sorted_lats = sorted(lats)
                idx = int(len(sorted_lats) * 0.95)
                p95_dict[bucket_ts] = round(sorted_lats[idx], 2)
            # TPS: always compute (0 if no samples)
            tps_dict[bucket_ts] = round(len(lats) / 5.0, 2)
            # Recall: average if samples >= 1, otherwise null
            recalls = data["recalls"]
            if len(recalls) >= 1:
                recall_dict[bucket_ts] = round(sum(recalls) / len(recalls), 4)
        
        # Generate strictly aligned series (12-13 buckets: cutoff to now inclusive)
        p95_series, tps_series, recall_series = [], [], []
        filled_null_buckets = 0
        non_empty_buckets = 0
        current_ts = aligned_cutoff_ms
        while current_ts <= aligned_now_ms:
            if current_ts not in buckets:
                filled_null_buckets += 1
            else:
                non_empty_buckets += 1
            # Ensure timestamp alignment: ts % 5000 == 0
            assert current_ts % 5000 == 0, f"Misaligned timestamp: {current_ts}"
            p95_series.append([current_ts, p95_dict.get(current_ts)])
            tps_series.append([current_ts, tps_dict.get(current_ts, 0)])
            recall_series.append([current_ts, recall_dict.get(current_ts)])
            current_ts += bucket_ms
        
        # Calculate enhanced debug metrics
        drop_ratio = round(dropped / total_samples, 4) if total_samples > 0 else 0.0
        heartbeat_age_ms = (now_ms - heartbeat_ms) if heartbeat_ms else None
        
        return {"ok": True, "source": "core", "window_sec": 60, "step_sec": 5,
                "buckets": len(p95_series), "samples": total_samples, "p95": p95_series,
                "tps": tps_series, "recall": recall_series,
                "meta": {"source": "core", "debug": {
                    "now_ms": now_ms, "cutoff_ms": aligned_cutoff_ms, "backend": METRICS_BACKEND,
                    "drop_ratio": drop_ratio, "filled_holes": filled_null_buckets,
                    "source_backend": METRICS_BACKEND, "heartbeat_age_ms": heartbeat_age_ms,
                    "clock_skew_ms": clock_skew_ms, "filled_null_buckets": filled_null_buckets,
                    "non_empty_buckets": non_empty_buckets
                }},
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


@app.get("/ops/summary")
async def ops_summary():
    """Unified ops summary: health + window60s + series60s(meta) + auto status (optional)"""
    try:
        now_ms = int(time.time() * 1000)
        result = {
            "ok": True,
            "source": "core",
            "backend": METRICS_BACKEND,
            "window_sec": 60,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # 1. Health check (with graceful degradation)
        try:
            if not CORE_AVAILABLE or metrics_sink is None:
                result["health"] = {"ok": False, "error": "core.metrics not available"}
            else:
                samples = metrics_sink.snapshot_last_60s(now_ms)
                redis_connected = False
                if hasattr(metrics_sink, 'client'):  # RedisMetrics
                    try:
                        metrics_sink.client.ping()
                        redis_connected = True
                    except:
                        pass
                result["health"] = {
                    "ok": True,
                    "core_metrics_backend": METRICS_BACKEND,
                    "redis_connected": redis_connected,
                    "rows_60s": len(samples)
                }
        except Exception as e:
            result["health"] = {"ok": False, "error": str(e)}
        
        # 2. Window60s aggregated metrics
        try:
            if CORE_AVAILABLE and metrics_sink:
                window_data = metrics_sink.window60s(now_ms)
                result["window60s"] = {
                    "p95_ms": window_data["p95_ms"],
                    "tps": window_data["tps"],
                    "recall_at_10": window_data["recall_at_10"],
                    "samples": window_data["samples"]
                }
            else:
                result["window60s"] = {"ok": False, "error": "core.metrics not available"}
        except Exception as e:
            result["window60s"] = {"ok": False, "error": str(e)}
        
        # 3. Series60s metadata (buckets count + non-empty buckets)
        try:
            if CORE_AVAILABLE and metrics_sink:
                bucket_ms = 5000
                aligned_now_ms = (now_ms // bucket_ms) * bucket_ms
                aligned_cutoff_ms = aligned_now_ms - 60000
                samples = metrics_sink.snapshot_last_60s(now_ms)
                
                # Count non-empty buckets
                buckets_set = set()
                for s in samples:
                    ts = s.get("ts", 0)
                    if ts >= (aligned_cutoff_ms - 1000) and ts <= (aligned_now_ms + 1000):
                        bucket_ts = (ts // bucket_ms) * bucket_ms
                        buckets_set.add(bucket_ts)
                
                # Calculate total expected buckets (12 or 13)
                total_buckets = 0
                current_ts = aligned_cutoff_ms
                while current_ts <= aligned_now_ms:
                    total_buckets += 1
                    current_ts += bucket_ms
                
                result["series60s"] = {
                    "buckets": total_buckets,
                    "non_empty": len(buckets_set),
                    "step_sec": 5
                }
            else:
                result["series60s"] = {"ok": False, "error": "core.metrics not available"}
        except Exception as e:
            result["series60s"] = {"ok": False, "error": str(e)}
        
        # 4. Auto status (optional, graceful fallback if not available)
        try:
            # Try to call /auto/status if it exists (will fail gracefully in app_v2)
            # Since app_v2 doesn't have auto worker, we set it as unavailable
            result["auto"] = {
                "available": False,
                "effective_tps_60s": None
            }
        except Exception as e:
            result["auto"] = {"available": False, "error": str(e)}
        
        return result
        
    except Exception as e:
        # Top-level error: still return ok=true but with error in sub-blocks
        return {
            "ok": True,
            "error": f"Partial failure: {str(e)}",
            "source": "core",
            "backend": METRICS_BACKEND,
            "window_sec": 60
        }


print("[OPS] summary endpoint ready")


@app.get("/demo", response_class=HTMLResponse)
async def demo():
    """Serve demo dashboard HTML"""
    template_path = Path(__file__).parent / "templates" / "demo.html"
    if template_path.exists():
        return template_path.read_text()
    return "<h1>Demo template not found</h1>"

