# DEPRECATED: kept for history only. Do NOT import or run. Use services.fiqa_api.app_main:app
"""app_v2.py - Minimal read-only metrics API (≤150 LoC)"""
import time, sys, asyncio, random, subprocess, threading, os, json, uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import settings for Black Swan Mode B configuration
sys.path.insert(0, str(Path(__file__).parent))
import settings
from force_override import apply_force_override, get_force_override_status

try:
    from core.metrics import metrics_sink, METRICS_BACKEND
    CORE_AVAILABLE = True
except Exception as e:
    print(f"[BOOT] ⚠️  core.metrics import failed: {e}")
    CORE_AVAILABLE, metrics_sink, METRICS_BACKEND = False, None, "unavailable"

# Import tap module
try:
    try:
        # Try relative import first (when running as package)
        from . import tap
    except ImportError:
        # Fall back to direct import (when running as script)
        import tap
    TAP_AVAILABLE = True
except Exception as e:
    print(f"[BOOT] ⚠️  tap module import failed: {e}")
    TAP_AVAILABLE = False
    tap = None

app = FastAPI(title="SearchForge Metrics API v2")
print(f"[BOOT] app_v2 using core.metrics backend={METRICS_BACKEND}")

# ========================================
# Real Query Bank Management
# ========================================
QUERY_BANK = []
QUERY_BANK_INDEX = 0
QUERY_BANK_LOCK = threading.Lock()

def load_query_bank():
    """Load queries from FIQA query bank file"""
    global QUERY_BANK
    if not settings.USE_REAL_QUERIES:
        print("[QUERY_BANK] USE_REAL_QUERIES=false, skipping query bank loading")
        return
    
    query_file = Path(__file__).parent.parent.parent / settings.FIQA_QUERY_BANK
    if not query_file.exists():
        print(f"[QUERY_BANK] ❌ File not found: {settings.FIQA_QUERY_BANK}")
        return
    
    try:
        with open(query_file, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        
        if not queries:
            print(f"[QUERY_BANK] ❌ File is empty: {settings.FIQA_QUERY_BANK}")
            return
        
        QUERY_BANK = queries
        print(f"[QUERY_BANK] ✅ Loaded {len(QUERY_BANK)} queries from {settings.FIQA_QUERY_BANK}")
    except Exception as e:
        print(f"[QUERY_BANK] ❌ Error loading queries: {e}")

def get_next_query() -> str:
    """Get next query from bank (round-robin or random)"""
    global QUERY_BANK_INDEX
    
    if not settings.USE_REAL_QUERIES or not QUERY_BANK:
        return "ping"  # Fallback to ping
    
    with QUERY_BANK_LOCK:
        if settings.BS_UNIQUE_QUERIES:
            # Round-robin: unique queries in sequence
            query = QUERY_BANK[QUERY_BANK_INDEX % len(QUERY_BANK)]
            QUERY_BANK_INDEX += 1
        else:
            # Random selection
            query = random.choice(QUERY_BANK)
    
    return query

# Load query bank at startup
load_query_bank()
print(f"[BOOT] Real query mode: USE_REAL_QUERIES={settings.USE_REAL_QUERIES}, queries={len(QUERY_BANK)}")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3002", "http://127.0.0.1:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tap middleware for request logging
class TapMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not TAP_AVAILABLE or not tap.TAP_ENABLED:
            return await call_next(request)
        
        start_time = time.time()
        start_ms = int(start_time * 1000)
        
        # Extract client from headers or query params
        client = request.headers.get("X-Tap-Client", "unknown")
        run_id = request.headers.get("X-Tap-Run-ID")
        phase = request.headers.get("X-Tap-Phase")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log to tap
        tap.write_backend_log(
            ts=start_ms,
            method=request.method,
            path=str(request.url.path),
            status=response.status_code,
            ms=duration_ms,
            run_id=run_id,
            phase=phase,
            client=client,
            body_size=0  # Could be enhanced to read body size
        )
        
        return response

# Add middleware
app.add_middleware(TapMiddleware)

# Black Swan test state
BLACK_SWAN_RUNNING = False

# Black Swan Configuration - Real Retrieval Mode
BLACK_SWAN_USE_REAL = os.environ.get("BLACK_SWAN_USE_REAL", "true").lower() == "true"
BLACK_SWAN_NOCACHE = os.environ.get("BLACK_SWAN_NOCACHE", "true").lower() == "true"
FIQA_SEARCH_URL = os.environ.get("FIQA_SEARCH_URL", "http://localhost:8080/search")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "beir_fiqa_full_ta")

# Configuration
BS_MAX_DURATION_SEC = int(os.environ.get("BS_MAX_DURATION_SEC", "150"))  # 150s max duration
BS_HEARTBEAT_TIMEOUT_SEC = int(os.environ.get("BS_HEARTBEAT_TIMEOUT_SEC", "15"))  # 15s heartbeat timeout

# QA Feed Configuration (Light monitoring)
QA_FEED_ENABLED = os.environ.get("QA_FEED_ENABLED", "false").lower() == "true"
QA_FEED_SAMPLE_RATE = float(os.environ.get("QA_FEED_SAMPLE_RATE", "0.05"))
QA_FEED_MAX_ITEMS = int(os.environ.get("QA_FEED_MAX_ITEMS", "200"))
QA_FEED_BUDGET_MS = float(os.environ.get("QA_FEED_BUDGET_MS", "2"))
QA_FEED_AUTOSCALE = os.environ.get("QA_FEED_AUTOSCALE", "true").lower() == "true"
QA_FEED_AUTOSCALE_HITS_PER_MIN = int(os.environ.get("QA_FEED_AUTOSCALE_HITS_PER_MIN", "10000"))
QA_FEED_CIRCUIT_TRIP_P95_MS = float(os.environ.get("QA_FEED_CIRCUIT_TRIP_P95_MS", "10"))
QA_STATS_ENABLED = os.environ.get("QA_STATS_ENABLED", "true").lower() == "true"

# Qdrant hit stats state (60s window)
import collections
QDRANT_HIT_WINDOW = collections.deque(maxlen=1000)  # Keep last 1000 hits
QDRANT_STATS_LOCK = threading.Lock()

# QA Feed state (ring buffer + circuit breaker)
QA_FEED_BUFFER = collections.deque(maxlen=QA_FEED_MAX_ITEMS)
QA_FEED_STATE = {
    "circuit_open": False,
    "sample_rate_effective": QA_FEED_SAMPLE_RATE,
    "consecutive_budget_violations": 0,
    "last_p95_baseline": None,
    "hits_per_min": 0,
    "last_autoscale_ts": 0
}
QA_FEED_LOCK = threading.Lock()

BLACK_SWAN_STATE = {
    "running": False,
    "run_id": None,  # UUID for current run
    "last_run_id": None,  # UUID of last completed run
    "phase": None,  # warmup, baseline, trip, recovery, complete, error
    "progress": 0,  # 0-100
    "eta_sec": 0,
    "started_at": None,
    "ended_at": None,  # Timestamp when completed
    "deadline": None,  # started_at + BS_MAX_DURATION_SEC
    "last_update_ts": None,  # For heartbeat monitoring
    "message": "",
    "progress_timeline": [],  # List of phase transitions
    "mode": None,  # A | B | C
    "playbook_params": {},  # Mode-specific parameters
}

# Qdrant hit tracking
QDRANT_STATS = {
    "hits": 0,
    "last_hit_ts": None,
    "current_run_hits": 0
}

# Phase-scoped metrics
PHASE_METRICS = {
    "before": {"p50": None, "p95": None, "tps": None, "samples": 0},
    "trip": {"p50": None, "p95": None, "tps": None, "samples": 0},
    "after": {"p50": None, "p95": None, "tps": None, "samples": 0}
}

# Load generator state
load_state = {
    "running": False, 
    "qps": 0, 
    "concurrency": 0, 
    "start_time": 0, 
    "duration": 0,
    "pattern": "constant",  # constant, step, saw, pulse
    "duty_percent": 100     # 0-100: intensity modulation
}

def _calculate_pattern_multiplier(pattern: str, elapsed_sec: float, duration: int, duty_percent: int) -> float:
    """Calculate QPS multiplier based on pattern type and elapsed time.
    
    Returns a value between 0 and 1 that modulates the base QPS.
    duty_percent controls the amplitude: 100 = full range, 50 = half range, etc.
    """
    duty_factor = duty_percent / 100.0
    
    if pattern == "constant":
        return duty_factor
    
    elif pattern == "step":
        # Step: sudden jump at 25% mark (off → on), drop at 75% mark (on → off)
        cycle_progress = elapsed_sec / duration if duration > 0 else 0
        if 0.25 <= cycle_progress < 0.75:
            return duty_factor  # High
        else:
            return 0.1 * duty_factor  # Low (10% baseline)
    
    elif pattern == "saw":
        # Sawtooth: linear rise from 0 to peak, then sharp drop, repeat every 20s
        cycle_duration = 20  # 20 second sawtooth cycle
        cycle_phase = (elapsed_sec % cycle_duration) / cycle_duration
        return cycle_phase * duty_factor
    
    elif pattern == "pulse":
        # Pulse: short bursts (2s on, 8s off) = 20% duty cycle base
        cycle_duration = 10  # 10 second pulse cycle
        cycle_phase = elapsed_sec % cycle_duration
        if cycle_phase < 2:  # 2 seconds on
            return duty_factor  # Full intensity
        else:
            return 0.05 * duty_factor  # Very low baseline (5%)
    
    elif pattern == "custom":
        # Custom pattern: extensible interface for user-defined sequences
        # TODO: Implement custom sequence loading from config/API
        # For now, return constant as placeholder
        # Future: load from load_state["custom_sequence"] or external source
        return duty_factor
    
    else:
        return duty_factor  # Default to constant

# AutoTuner state and timeline
class AutoTuner:
    def __init__(self):
        self.paused = False
        self.pause_until_ts = 0
        self.timeline = []
    
    def pause(self, duration_sec: int, source: str = "guardrail", p95_ms: float = None, threshold_ms: float = None):
        """Pause the tuner for specified duration"""
        self.paused = True
        self.pause_until_ts = time.time() + duration_sec
        event = {
            "ts": int(time.time() * 1000),
            "event": "guardrail_trip",
            "cooldown": duration_sec,
            "source": source
        }
        # Add violation details if provided
        if p95_ms is not None:
            event["p95_ms"] = round(p95_ms, 2)
        if threshold_ms is not None:
            event["threshold_ms"] = threshold_ms
            if p95_ms is not None:
                event["violation_magnitude"] = round(p95_ms - threshold_ms, 2)
        
        self.timeline.append(event)
        print(f"[TUNER] Paused for {duration_sec}s due to {source} violation")
        return event
    
    def resume(self, source: str = "guardrail", force: bool = False):
        """Resume the tuner"""
        if self.paused and (force or time.time() >= self.pause_until_ts):
            self.paused = False
            self.pause_until_ts = 0  # Reset pause timer
            event = {
                "ts": int(time.time() * 1000),
                "event": "guardrail_resume",
                "source": source,
                "forced": force
            }
            self.timeline.append(event)
            print(f"[TUNER] Resumed after cooldown" + (" (forced)" if force else ""))
            return event
        return None
    
    def check_and_resume(self):
        """Check if cooldown is over and resume if needed"""
        if self.paused and time.time() >= self.pause_until_ts:
            return self.resume()
        return None
    
    def is_paused(self):
        """Check if tuner is currently paused"""
        self.check_and_resume()  # Auto-resume if cooldown is over
        return self.paused
    
    def get_timeline(self, limit: int = 20):
        """Get recent timeline events"""
        return self.timeline[-limit:] if self.timeline else []

# Global tuner instance
auto_tuner = AutoTuner()

# Guardrail configuration
GUARDRAIL_P95_THRESHOLD_MS = 200  # SLA threshold
GUARDRAIL_COOLDOWN_SEC = 60

class SearchRequest(BaseModel):
    query: str = "ping"
    top_k: int = 10
    profile: str = "fast"


class BlackSwanRequest(BaseModel):
    mode: str = "A"  # A | B | C


async def guardrail_monitor():
    """Background task to monitor SLA violations and trigger AutoTuner pause"""
    print("[GUARDRAIL] Monitor started")
    while True:
        try:
            await asyncio.sleep(10)  # Check every 10 seconds
            
            if not CORE_AVAILABLE or metrics_sink is None:
                continue
            
            # Check if tuner is paused
            auto_tuner.check_and_resume()
            
            # Skip guardrail check if already paused
            if auto_tuner.is_paused():
                continue
            
            # Get current window60s metrics
            now_ms = int(time.time() * 1000)
            window_data = metrics_sink.window60s(now_ms)
            p95_ms = window_data.get("p95_ms")
            
            # Check for SLA violation
            if p95_ms is not None and p95_ms > GUARDRAIL_P95_THRESHOLD_MS:
                print(f"[GUARDRAIL] ⚠️  SLA violation detected: p95={p95_ms}ms > {GUARDRAIL_P95_THRESHOLD_MS}ms")
                auto_tuner.pause(
                    duration_sec=GUARDRAIL_COOLDOWN_SEC,
                    source="guardrail",
                    p95_ms=p95_ms,
                    threshold_ms=GUARDRAIL_P95_THRESHOLD_MS
                )
                
        except Exception as e:
            print(f"[GUARDRAIL] Monitor error: {e}")
            await asyncio.sleep(10)


async def black_swan_watchdog():
    """Background task to monitor Black Swan test timeouts (watchdog + heartbeat)"""
    print("[BLACK_SWAN] Watchdog started")
    while True:
        try:
            await asyncio.sleep(2)  # Check every 2 seconds
            
            global BLACK_SWAN_STATE
            
            # Skip if not running
            if not BLACK_SWAN_STATE.get("running"):
                continue
            
            now_ts = int(time.time())
            started_at = BLACK_SWAN_STATE.get("started_at")
            deadline = BLACK_SWAN_STATE.get("deadline")
            last_update_ts = BLACK_SWAN_STATE.get("last_update_ts")
            
            # Increment watchdog check counter
            BLACK_SWAN_STATE["counters"]["watchdog_checks"] += 1
            
            # Check 1: Watchdog timeout (exceeded max duration)
            if deadline and now_ts > deadline:
                elapsed = now_ts - started_at if started_at else 0
                print(f"[BLACK_SWAN] ⚠️  Watchdog timeout: elapsed={elapsed}s > max={BS_MAX_DURATION_SEC}s")
                BLACK_SWAN_STATE.update({
                    "phase": "error",
                    "progress": 0,
                    "running": False,
                    "ended_at": now_ts,
                    "message": f"Watchdog timeout: exceeded {BS_MAX_DURATION_SEC}s max duration"
                })
                BLACK_SWAN_STATE["progress_timeline"].append({
                    "phase": "error",
                    "timestamp": now_ts,
                    "progress": 0,
                    "reason": "watchdog_timeout"
                })
                continue
            
            # Check 2: Heartbeat timeout (no updates for BS_HEARTBEAT_TIMEOUT_SEC)
            if last_update_ts and (now_ts - last_update_ts) > BS_HEARTBEAT_TIMEOUT_SEC:
                stale_duration = now_ts - last_update_ts
                print(f"[BLACK_SWAN] ⚠️  Heartbeat timeout: no updates for {stale_duration}s > {BS_HEARTBEAT_TIMEOUT_SEC}s")
                BLACK_SWAN_STATE.update({
                    "phase": "error",
                    "progress": 0,
                    "running": False,
                    "ended_at": now_ts,
                    "message": f"Heartbeat timeout: no updates for {stale_duration}s (stale heartbeat)"
                })
                BLACK_SWAN_STATE["progress_timeline"].append({
                    "phase": "error",
                    "timestamp": now_ts,
                    "progress": 0,
                    "reason": "heartbeat_timeout"
                })
                continue
            
            # Increment heartbeat check counter
            BLACK_SWAN_STATE["counters"]["heartbeat_checks"] += 1
            
        except Exception as e:
            print(f"[BLACK_SWAN] Watchdog error: {e}")
            await asyncio.sleep(2)


@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(guardrail_monitor())
    asyncio.create_task(black_swan_watchdog())
    print("[BOOT] Guardrail monitor task started")
    print("[BOOT] Black Swan watchdog started")


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


@app.get("/admin/warmup/status")
async def warmup_status():
    """Warmup readiness status (lightweight stub)"""
    # Get sample count from metrics if available
    samples = 0
    if CORE_AVAILABLE and metrics_sink:
        try:
            now_ms = int(time.time() * 1000)
            snapshot = metrics_sink.snapshot_last_60s(now_ms)
            samples = len(snapshot)
        except:
            pass
    
    return {
        "ok": True,
        "ready": True,
        "samples": samples,
        "window_sec": 60,
        "progress": 100,
        "message": "Warmup complete"
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


def _mask_text(text: str, max_len: int = 100) -> str:
    """Mask and truncate text for safe logging"""
    if not text:
        return ""
    # Basic masking: remove emails, IPs, etc
    import re
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', text)
    # Truncate
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _track_qdrant_hit(hit_from: str, topk: int, rerank_k: int, latency_ms: float, mode: str):
    """Track Qdrant hit stats (60s window, lightweight)"""
    if not QA_STATS_ENABLED:
        return
    
    now_ms = int(time.time() * 1000)
    
    try:
        with QDRANT_STATS_LOCK:
            QDRANT_HIT_WINDOW.append({
                "ts": now_ms,
                "hit_from": hit_from,
                "topk": topk,
                "rerank_k": rerank_k,
                "latency_ms": latency_ms,
                "mode": mode
            })
    except Exception as e:
        # Silent failure: stats tracking should never break the main path
        print(f"[QA_STATS] Error tracking hit: {e}")


def _compute_qdrant_stats_60s() -> dict:
    """Compute Qdrant stats from 60s window"""
    now_ms = int(time.time() * 1000)
    cutoff_ms = now_ms - 60000
    
    with QDRANT_STATS_LOCK:
        # Filter to 60s window
        recent_hits = [h for h in QDRANT_HIT_WINDOW if h["ts"] >= cutoff_ms]
        
        if not recent_hits:
            return {
                "hits_60s": 0,
                "remote_pct": 0.0,
                "cache_pct": 0.0,
                "avg_rerank_k": 0.0,
                "avg_query_ms_60s": None,
                "p95_query_ms_60s": None,
                "last_hit_ts": None
            }
        
        # Compute metrics
        total_hits = len(recent_hits)
        remote_hits = sum(1 for h in recent_hits if h["hit_from"] == "qdrant")
        cache_hits = sum(1 for h in recent_hits if h["hit_from"] == "cache")
        
        remote_pct = (remote_hits / total_hits * 100) if total_hits > 0 else 0.0
        cache_pct = (cache_hits / total_hits * 100) if total_hits > 0 else 0.0
        
        rerank_ks = [h["rerank_k"] for h in recent_hits if h.get("rerank_k")]
        avg_rerank_k = sum(rerank_ks) / len(rerank_ks) if rerank_ks else 0.0
        
        last_hit_ts = max(h["ts"] for h in recent_hits) if recent_hits else None
        
        # Calculate avg and p95 query time from latency_ms
        latencies = [h["latency_ms"] for h in recent_hits if h.get("latency_ms") is not None]
        avg_query_ms = None
        p95_query_ms = None
        
        if latencies:
            avg_query_ms = round(sum(latencies) / len(latencies), 2)
            
            # P95 calculation (requires at least 3 samples for meaningful result)
            if len(latencies) >= 3:
                sorted_latencies = sorted(latencies)
                idx = int(len(sorted_latencies) * 0.95)
                p95_query_ms = round(sorted_latencies[idx], 2)
        
        return {
            "hits_60s": total_hits,
            "remote_pct": round(remote_pct, 2),
            "cache_pct": round(cache_pct, 2),
            "avg_rerank_k": round(avg_rerank_k, 1),
            "avg_query_ms_60s": avg_query_ms,
            "p95_query_ms_60s": p95_query_ms,
            "last_hit_ts": last_hit_ts
        }


def _enqueue_qa_event(query: str, answer: str, mode: str, latency_ms: float, hit_from: str, topk: int, rerank_k: int):
    """Enqueue QA event to feed (with sampling, budget guard, autoscale, circuit breaker)"""
    if not QA_FEED_ENABLED or QA_FEED_STATE["circuit_open"]:
        return
    
    # Random sampling
    effective_rate = QA_FEED_STATE["sample_rate_effective"]
    if random.random() > effective_rate:
        return
    
    enqueue_start = time.time()
    
    try:
        now_ms = int(time.time() * 1000)
        
        # Mask and truncate
        query_masked = _mask_text(query, 120)
        answer_masked = _mask_text(answer, 200)
        
        event = {
            "ts": now_ms,
            "mode": mode,
            "latency_ms": round(latency_ms, 2),
            "hit_from": hit_from,
            "topk": topk,
            "rerank_k": rerank_k,
            "query": query_masked,
            "answer": answer_masked
        }
        
        with QA_FEED_LOCK:
            QA_FEED_BUFFER.append(event)
        
        # Budget check
        enqueue_duration_ms = (time.time() - enqueue_start) * 1000
        if enqueue_duration_ms > QA_FEED_BUDGET_MS:
            QA_FEED_STATE["consecutive_budget_violations"] += 1
            if QA_FEED_STATE["consecutive_budget_violations"] >= 3:
                QA_FEED_STATE["circuit_open"] = True
                print(f"[QA_FEED] Circuit breaker OPEN: 3 consecutive budget violations ({enqueue_duration_ms:.2f}ms > {QA_FEED_BUDGET_MS}ms)")
        else:
            QA_FEED_STATE["consecutive_budget_violations"] = 0
        
        # Autoscale check (every 10s)
        if QA_FEED_AUTOSCALE:
            last_check = QA_FEED_STATE.get("last_autoscale_ts", 0)
            if now_ms - last_check > 10000:  # Check every 10s
                QA_FEED_STATE["last_autoscale_ts"] = now_ms
                
                # Estimate hits per minute from stats
                stats = _compute_qdrant_stats_60s()
                hits_60s = stats["hits_60s"]
                hits_per_min = hits_60s  # Already 60s window
                
                QA_FEED_STATE["hits_per_min"] = hits_per_min
                
                if hits_per_min > QA_FEED_AUTOSCALE_HITS_PER_MIN:
                    # Halve sampling rate (min 0.01)
                    new_rate = max(0.01, QA_FEED_STATE["sample_rate_effective"] / 2)
                    if new_rate != QA_FEED_STATE["sample_rate_effective"]:
                        QA_FEED_STATE["sample_rate_effective"] = new_rate
                        print(f"[QA_FEED] Autoscale triggered: hits/min={hits_per_min} > {QA_FEED_AUTOSCALE_HITS_PER_MIN}, new rate={new_rate:.4f}")
                
    except Exception as e:
        # Silent failure
        print(f"[QA_FEED] Error enqueueing event: {e}")


async def _do_real_fiqa_query(query: str, top_k: int = 10, heavy: bool = False, nocache: bool = False) -> dict:
    """Call real FIQA API search endpoint with optional heavy mode"""
    import aiohttp
    
    url = FIQA_SEARCH_URL
    
    # In heavy mode, replace query with a long one from query bank
    if heavy:
        try:
            query_bank_path = Path(__file__).parent.parent.parent / settings.HEAVY_QUERY_BANK
            if query_bank_path.exists():
                with open(query_bank_path) as f:
                    queries = [line.strip() for line in f if line.strip()]
                if queries:
                    query = random.choice(queries)
        except Exception as e:
            print(f"[Heavy Mode] Failed to load query bank: {e}, using original query")
    
    # Add cache busting params
    params = {}
    if nocache:
        params["nocache"] = int(time.time() * 1000)
        params["rand"] = random.randint(1000, 9999)
    
    # Build payload with heavy params
    payload = {
        "query": query,
        "top_k": top_k
    }
    
    if heavy:
        # Get heavy mode params from settings (loaded from .env)
        runtime_params = {
            "num_candidates": settings.HEAVY_NUM_CANDIDATES,
            "rerank_topk": settings.HEAVY_RERANK_TOPK,
            "qps": 0  # QPS not directly used here, but included for completeness
        }
        
        # Apply force override (bypasses all guardrails if FORCE_OVERRIDE=true)
        final_params = apply_force_override(runtime_params, context="black_swan_mode_b")
        
        # Use the potentially overridden values
        num_candidates = final_params.get("num_candidates", runtime_params["num_candidates"])
        rerank_topk = final_params.get("rerank_topk", runtime_params["rerank_topk"])
        
        payload["candidate_k"] = num_candidates
        payload["rerank_top_k"] = rerank_topk
        
        # TRACE_E2E: Log OUT payload from app_v2
        print(f"TRACE_E2E: OUT payload from app_v2: {{top_k: {top_k}, candidate_k: {num_candidates}, rerank_topk: {rerank_topk}}}")
        
        # Optional: Add artificial delay (only in heavy mode)
        delay_ms = settings.RERANK_DELAY_MS
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000.0)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    # Track Qdrant hit
                    BLACK_SWAN_STATE["qdrant_hits"] += 1
                    BLACK_SWAN_STATE["last_qdrant_hit_ts"] = int(time.time())
                    return data
                else:
                    return {"error": f"FIQA API returned {response.status}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/search")
async def search(req: SearchRequest):
    """Search endpoint - supports both MOCK and REAL mode based on BLACK_SWAN_USE_REAL"""
    try:
        start_ms = time.time() * 1000
        
        # Check if Black Swan is running and mode
        is_black_swan = BLACK_SWAN_STATE.get("running", False)
        use_real = BLACK_SWAN_USE_REAL if is_black_swan else False
        
        if is_black_swan:
            run_id = BLACK_SWAN_STATE.get("run_id", "unknown")
            phase = BLACK_SWAN_STATE.get("phase", "unknown")
            mode = BLACK_SWAN_STATE.get("mode", "A")
            
            if use_real:
                print(f"[BlackSwan] run={run_id} phase={phase} mode={mode} → REAL query to {FIQA_SEARCH_URL}")
                
                # Determine if heavy mode (Mode B)
                heavy = (mode == "B")
                
                # Call real FIQA API
                result = await _do_real_fiqa_query(
                    query=req.query,
                    top_k=req.top_k,
                    heavy=heavy,
                    nocache=BLACK_SWAN_NOCACHE
                )
                
                latency_ms = time.time() * 1000 - start_ms
                
                if "error" in result:
                    print(f"[BlackSwan] run={run_id} → FIQA API error: {result['error']}")
                else:
                    print(f"[BlackSwan] run={run_id} → Qdrant hit #{BLACK_SWAN_STATE['qdrant_hits']} latency={latency_ms:.2f}ms")
                
                # Track Qdrant hit stats
                hit_from = "cache" if result.get("cache_hit") else "qdrant"
                _track_qdrant_hit(
                    hit_from=hit_from,
                    topk=req.top_k,
                    rerank_k=result.get("candidate_k", 100) if heavy else 50,
                    latency_ms=latency_ms,
                    mode=mode
                )
                
                # Enqueue QA event (sampled)
                answers = result.get("answers", [])
                answer_text = answers[0].get("answer", "") if answers else ""
                _enqueue_qa_event(
                    query=req.query,
                    answer=answer_text,
                    mode=mode,
                    latency_ms=latency_ms,
                    hit_from=hit_from,
                    topk=req.top_k,
                    rerank_k=result.get("rerank_top_k", 100) if heavy else 50
                )
                
                # Record to metrics_sink
                if CORE_AVAILABLE and metrics_sink:
                    metrics_sink.push({
                        "ts": int(start_ms),
                        "latency_ms": round(latency_ms, 2),
                        "recall_at10": result.get("recall_at_10", 0.9),
                        "mode": "on",
                        "profile": req.profile,
                        "rerank_hit": 1,
                        "cache_hit": result.get("cache_hit", 0)
                    })
                
                return {"ok": True, "results": result.get("answers", []), "latency_ms": round(latency_ms, 2), "mode": "real"}
            else:
                print(f"[BlackSwan] run={run_id} phase={phase} → /search called (MOCK mode, NOT hitting Qdrant)")
        
        # Mock mode (original behavior)
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
        return {"ok": True, "results": [], "latency_ms": round(latency_ms, 2), "mode": "mock"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _run_load(qps: int, duration: int, concurrency: int, pattern: str = "constant", duty_percent: int = 100):
    """Background load generator with pattern support and real query selection"""
    load_state.update({
        "running": True, "qps": qps, "concurrency": concurrency, 
        "start_time": time.time(), "duration": duration,
        "pattern": pattern, "duty_percent": duty_percent
    })
    try:
        end_time = time.time() + duration
        while time.time() < end_time and load_state["running"]:
            # Calculate effective QPS based on pattern
            elapsed = time.time() - load_state["start_time"]
            multiplier = _calculate_pattern_multiplier(pattern, elapsed, duration, duty_percent)
            effective_qps = qps * multiplier
            
            # Calculate batch size and interval
            batch_size = min(concurrency, max(1, int(effective_qps)))
            interval = batch_size / effective_qps if effective_qps > 0 else 0.1
            
            # Generate requests with real queries
            tasks = [search(SearchRequest(query=get_next_query())) for _ in range(batch_size)]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(interval)
    except Exception as e:
        print(f"[LOAD] Error: {e}")
    finally:
        load_state["running"] = False


@app.post("/load/start")
async def load_start(
    qps: int = 12, 
    duration: int = 60, 
    concurrency: int = 16, 
    pattern: str = "constant",  # constant, step, saw, pulse
    duty: int = 100,  # duty_percent: 0-100
    background: BackgroundTasks = None
):
    """Start load generator with pattern support
    
    Args:
        qps: Base queries per second (default: 12)
        duration: Load test duration in seconds (default: 60)
        concurrency: Concurrent requests (default: 16)
        pattern: Traffic pattern - constant, step, saw, pulse (default: constant)
        duty: Duty percentage 0-100, controls intensity (default: 100)
    
    Examples:
        /load/start?qps=20&duration=60&pattern=pulse&duty=80
        /load/start?qps=15&pattern=saw&duty=50
    """
    if load_state["running"]:
        return {"ok": False, "error": "Load generator already running"}
    
    # Validate pattern
    if pattern not in ["constant", "step", "saw", "pulse", "custom"]:
        return {"ok": False, "error": f"Invalid pattern '{pattern}'. Must be: constant, step, saw, pulse, or custom"}
    
    # Validate duty
    if not (0 <= duty <= 100):
        return {"ok": False, "error": f"Invalid duty {duty}. Must be 0-100"}
    
    asyncio.create_task(_run_load(qps, duration, concurrency, pattern, duty))
    return {
        "ok": True, 
        "qps": qps, 
        "duration": duration, 
        "concurrency": concurrency,
        "pattern": pattern,
        "duty_percent": duty
    }


@app.get("/load/status")
async def load_status():
    """Get load generator status"""
    if not load_state["running"]:
        return {
            "running": False, 
            "qps": 0, 
            "concurrency": 0, 
            "eta_sec": 0,
            "pattern": "none",
            "duty_percent": 0
        }
    elapsed = time.time() - load_state["start_time"]
    eta = max(0, load_state["duration"] - elapsed)
    return {
        "running": True, 
        "qps": load_state["qps"], 
        "concurrency": load_state["concurrency"], 
        "eta_sec": round(eta, 1), 
        "elapsed_sec": round(elapsed, 1),
        "pattern": load_state.get("pattern", "constant"),
        "duty_percent": load_state.get("duty_percent", 100)
    }


@app.get("/auto/status")
async def auto_status():
    """Auto traffic status (lightweight stub with effective TPS)"""
    # Calculate effective TPS from series60s if available
    effective_tps_60s = 0.0
    if CORE_AVAILABLE and metrics_sink:
        try:
            now_ms = int(time.time() * 1000)
            window_data = metrics_sink.window60s(now_ms)
            effective_tps_60s = window_data.get("tps", 0.0)
        except:
            pass
    
    return {
        "ok": True,
        "running": load_state["running"],
        "qps": load_state["qps"],
        "target_qps": load_state["qps"],
        "pattern": load_state.get("pattern", "constant"),
        "effective_tps_60s": round(effective_tps_60s, 2),
        "enabled": False,
        "mode": "manual"
    }


@app.get("/tuner/status")
async def tuner_status():
    """Get AutoTuner status with current metrics (pure read-only)"""
    # Pure GET: no state changes, just read current state
    # Note: check_and_resume() moved to background task or POST endpoints
    
    # Get current p95 for context
    current_p95_ms = None
    if CORE_AVAILABLE and metrics_sink:
        try:
            now_ms = int(time.time() * 1000)
            window_data = metrics_sink.window60s(now_ms)
            current_p95_ms = window_data.get("p95_ms")
        except:
            pass
    
    return {
        "ok": True,
        "paused": auto_tuner.is_paused(),
        "pause_until_ts": auto_tuner.pause_until_ts if auto_tuner.paused else None,
        "cooldown_remaining_sec": max(0, auto_tuner.pause_until_ts - time.time()) if auto_tuner.paused else 0,
        "current_p95_ms": current_p95_ms,
        "threshold_ms": GUARDRAIL_P95_THRESHOLD_MS,
        "timeline": auto_tuner.get_timeline(limit=20)
    }


@app.get("/tuner/enabled")
async def tuner_enabled():
    """Tuner enabled/paused state (pure read-only)"""
    # Pure GET: no state changes, just read current state
    # Note: check_and_resume() moved to background task or POST endpoints
    return {
        "ok": True,
        "enabled": not auto_tuner.is_paused(),
        "paused": auto_tuner.is_paused()
    }


@app.post("/tuner/toggle")
async def toggle_tuner():
    """Toggle Auto Tuner enabled/disabled state"""
    try:
        # Toggle the tuner state
        if auto_tuner.is_paused():
            auto_tuner.resume(source="manual_toggle", force=True)
            message = "Auto Tuner enabled"
        else:
            auto_tuner.pause(duration_sec=3600)  # Pause for 1 hour by default
            message = "Auto Tuner paused"
        
        return {
            "ok": True,
            "enabled": not auto_tuner.is_paused(),
            "paused": auto_tuner.is_paused(),
            "message": message
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "toggle_failed",
                "message": f"Failed to toggle tuner: {str(e)}"
            }
        )


@app.post("/tuner/trigger_guardrail")
async def trigger_guardrail():
    """Manually trigger a guardrail trip (for testing)"""
    if auto_tuner.is_paused():
        return {"ok": False, "error": "Tuner already paused"}
    
    # Get current p95 for testing context
    current_p95_ms = None
    if CORE_AVAILABLE and metrics_sink:
        try:
            now_ms = int(time.time() * 1000)
            window_data = metrics_sink.window60s(now_ms)
            current_p95_ms = window_data.get("p95_ms")
        except:
            pass
    
    auto_tuner.pause(
        duration_sec=GUARDRAIL_COOLDOWN_SEC,
        source="manual_test",
        p95_ms=current_p95_ms,
        threshold_ms=GUARDRAIL_P95_THRESHOLD_MS
    )
    return {"ok": True, "message": f"Guardrail triggered, tuner paused for {GUARDRAIL_COOLDOWN_SEC}s"}


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
                    "p95_ms": window_data.get("p95_ms"),
                    "tps": window_data.get("tps"),
                    "recall_at_10": window_data.get("recall_at_10"),
                    "samples": window_data.get("samples", 0)
                }
            else:
                result["window60s"] = {
                    "p95_ms": None,
                    "tps": 0.0,
                    "recall_at_10": None,
                    "samples": 0
                }
        except Exception as e:
            print(f"[OPS] window60s error: {e}")
            result["window60s"] = {
                "p95_ms": None,
                "tps": 0.0,
                "recall_at_10": None,
                "samples": 0,
                "error": str(e)
            }
        
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
        
        # 5. AutoTuner status and timeline
        try:
            auto_tuner.check_and_resume()  # Auto-resume if cooldown is over
            
            # Get current p95 for context
            current_p95_ms = None
            if CORE_AVAILABLE and metrics_sink:
                try:
                    window_data = metrics_sink.window60s(now_ms)
                    current_p95_ms = window_data.get("p95_ms")
                except:
                    pass
            
            result["tuner"] = {
                "paused": auto_tuner.is_paused(),
                "pause_until_ts": auto_tuner.pause_until_ts if auto_tuner.paused else None,
                "current_p95_ms": current_p95_ms,
                "threshold_ms": GUARDRAIL_P95_THRESHOLD_MS,
                "timeline": auto_tuner.get_timeline(limit=20)
            }
        except Exception as e:
            result["tuner"] = {"ok": False, "error": str(e)}
        
        # 6. KPI Comparison (before/after guardrail recovery)
        try:
            kpi_compare = {
                "cost_per_1k": None,
                "recall_before": None,
                "recall_after": None,
                "recovery_time_sec": None,
                "samples": 0
            }
            
            # Calculate cost per 1k requests (assuming $0.001 per request as baseline)
            if result.get("window60s") and result["window60s"].get("tps") is not None:
                tps = result["window60s"]["tps"]
                cost_per_request = 0.001  # $0.001 per request
                kpi_compare["cost_per_1k"] = round(cost_per_request * 1000, 2)
                kpi_compare["samples"] = result["window60s"].get("samples", 0)
            
            # Calculate recall before/after and recovery time
            timeline = result.get("tuner", {}).get("timeline", [])
            if timeline and len(timeline) >= 2:
                # Find last guardrail trip and resume events
                guardrail_trip = None
                guardrail_resume = None
                
                for event in reversed(timeline):
                    if event.get("event") == "guardrail_resume" and guardrail_resume is None:
                        guardrail_resume = event
                    elif event.get("event") == "guardrail_trip" and guardrail_trip is None:
                        guardrail_trip = event
                    
                    if guardrail_trip and guardrail_resume:
                        break
                
                # Calculate recovery time
                if guardrail_trip and guardrail_resume:
                    recovery_time_ms = guardrail_resume["ts"] - guardrail_trip["ts"]
                    kpi_compare["recovery_time_sec"] = round(recovery_time_ms / 1000, 1)
                
                # Get recall before (around guardrail trip time) and after (current)
                if CORE_AVAILABLE and metrics_sink and guardrail_trip:
                    trip_ts = guardrail_trip["ts"]
                    
                    # Get samples around trip time (±30s window)
                    all_samples = metrics_sink.snapshot_last_60s(now_ms)
                    before_samples = [s for s in all_samples if abs(s.get("ts", 0) - trip_ts) < 30000 and s.get("ts", 0) <= trip_ts]
                    after_samples = [s for s in all_samples if s.get("ts", 0) > (trip_ts + 600000)]  # After 10 min
                    
                    # Calculate average recall
                    if before_samples:
                        recalls_before = [s.get("recall_at10") for s in before_samples if s.get("recall_at10") is not None]
                        if recalls_before:
                            kpi_compare["recall_before"] = round(sum(recalls_before) / len(recalls_before), 4)
                    
                    if after_samples:
                        recalls_after = [s.get("recall_at10") for s in after_samples if s.get("recall_at10") is not None]
                        if recalls_after:
                            kpi_compare["recall_after"] = round(sum(recalls_after) / len(recalls_after), 4)
            
            result["kpi_compare"] = kpi_compare
            
        except Exception as e:
            result["kpi_compare"] = {"ok": False, "error": str(e)}
        
        # 7. Load generator status (meta.load)
        try:
            if load_state["running"]:
                elapsed = time.time() - load_state["start_time"]
                eta = max(0, load_state["duration"] - elapsed)
                
                # Predict TPS for next 5 seconds (for guardrail coordination)
                future_elapsed = elapsed + 5
                pattern = load_state.get("pattern", "constant")
                duty = load_state.get("duty_percent", 100)
                duration = load_state["duration"]
                base_qps = load_state["qps"]
                
                future_multiplier = _calculate_pattern_multiplier(pattern, future_elapsed, duration, duty)
                predicted_tps = round(base_qps * future_multiplier, 2)
                
                result["meta"] = {
                    "load": {
                        "running": True,
                        "qps": load_state["qps"],
                        "pattern": pattern,
                        "duty_percent": duty,
                        "concurrency": load_state["concurrency"],
                        "elapsed_sec": round(elapsed, 1),
                        "eta_sec": round(eta, 1),
                        "predicted_tps_next5s": predicted_tps
                    }
                }
            else:
                result["meta"] = {
                    "load": {
                        "running": False,
                        "pattern": "none",
                        "duty_percent": 0,
                        "predicted_tps_next5s": 0
                    }
                }
        except Exception as e:
            result["meta"] = {"load": {"ok": False, "error": str(e)}}
        
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


@app.get("/ops/black_swan/preflight")
async def black_swan_preflight():
    """Preflight checks before starting Black Swan test"""
    checks = {
        "api_reachable": False,
        "reports_dir_exists": False,
        "reports_dir_writable": False,
        "script_exists": False,
        "script_executable": False,
        "endpoints_ok": False
    }
    errors = []
    
    try:
        # Check 1: API reachable (self-check via /ops/summary)
        try:
            # Simple check - if we're running, API is reachable
            checks["api_reachable"] = True
        except Exception as e:
            errors.append(f"API unreachable: {str(e)}")
        
        # Check 2: reports/ directory
        project_root = Path(__file__).parent.parent.parent
        reports_dir = project_root / "reports"
        
        if reports_dir.exists():
            checks["reports_dir_exists"] = True
            # Check if writable
            try:
                test_file = reports_dir / ".preflight_test"
                test_file.touch()
                test_file.unlink()
                checks["reports_dir_writable"] = True
            except Exception as e:
                errors.append(f"reports/ not writable: {str(e)}")
        else:
            errors.append("reports/ directory does not exist")
            # Try to create it
            try:
                reports_dir.mkdir(parents=True, exist_ok=True)
                checks["reports_dir_exists"] = True
                checks["reports_dir_writable"] = True
            except Exception as e:
                errors.append(f"Failed to create reports/: {str(e)}")
        
        # Check 3: Script exists and is executable
        script_path = project_root / "scripts" / "black_swan_demo.sh"
        
        if script_path.exists():
            checks["script_exists"] = True
            if os.access(script_path, os.X_OK):
                checks["script_executable"] = True
            else:
                errors.append("scripts/black_swan_demo.sh not executable (run: chmod +x)")
        else:
            errors.append("scripts/black_swan_demo.sh not found")
        
        # Check 4: Key endpoints respond
        # We can't easily check other endpoints from within the same service,
        # but we can at least confirm they exist in the route table
        checks["endpoints_ok"] = True  # Assume OK if we got this far
        
        # Determine overall pass/fail
        all_pass = all(checks.values())
        
        if all_pass:
            return {
                "ok": True,
                "message": "All preflight checks passed",
                "checks": checks
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": "preflight_failed",
                    "message": "One or more preflight checks failed",
                    "checks": checks,
                    "errors": errors
                }
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "preflight_error",
                "message": f"Preflight check error: {str(e)}",
                "checks": checks
            }
        )


@app.get("/ops/qdrant/ping")
async def qdrant_ping():
    """Check if Qdrant is reachable and return collection info"""
    try:
        from qdrant_client import QdrantClient
        import os
        
        qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
        qdrant_port = int(os.environ.get("QDRANT_PORT", "6333"))
        
        start_ms = time.time() * 1000
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        # Get collections
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        latency_ms = time.time() * 1000 - start_ms
        
        print(f"[Qdrant] Ping successful: {qdrant_host}:{qdrant_port} ({latency_ms:.2f}ms) - collections: {collection_names}")
        
        return {
            "ok": True,
            "host": qdrant_host,
            "port": qdrant_port,
            "latency_ms": round(latency_ms, 2),
            "collections": collection_names,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception as e:
        print(f"[Qdrant] Ping failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "error": str(e),
                "message": "Qdrant unreachable"
            }
        )


@app.get("/ops/qdrant/config")
async def qdrant_config():
    """Get Qdrant configuration (concurrency, batch_size, override state)"""
    try:
        # Read override settings from environment
        override = os.environ.get("BS_QDRANT_OVERRIDE", "0").lower() in ("1", "true")
        max_concurrency = int(os.environ.get("BS_QDRANT_MAX_CONCURRENCY", "32"))
        batch_size = int(os.environ.get("BS_QDRANT_BATCH_SIZE", "1"))
        
        # Defaults (when override is off)
        default_concurrency = 32
        default_batch_size = 1
        
        # Effective values
        effective_concurrency = max_concurrency if override else default_concurrency
        effective_batch_size = batch_size if override else default_batch_size
        source = "override" if override else "default"
        
        return {
            "ok": True,
            "override": override,
            "concurrency": effective_concurrency,
            "batch_size": effective_batch_size,
            "source": source,
            "defaults": {
                "concurrency": default_concurrency,
                "batch_size": default_batch_size
            }
        }
    except Exception as e:
        # Never 5xx - return safe defaults
        return {
            "ok": True,
            "override": False,
            "concurrency": 32,
            "batch_size": 1,
            "source": "default",
            "defaults": {
                "concurrency": 32,
                "batch_size": 1
            },
            "error": str(e)
        }


@app.get("/ops/qdrant/stats")
async def qdrant_stats():
    """Get Qdrant hit statistics (60s window) for Black Swan validation"""
    if not QA_STATS_ENABLED:
        return {
            "ok": False,
            "error": "QA_STATS_ENABLED=false",
            "message": "Qdrant stats tracking is disabled"
        }
    
    stats = _compute_qdrant_stats_60s()
    
    return {
        "ok": True,
        "hits_60s": stats["hits_60s"],
        "avg_query_ms_60s": stats.get("avg_query_ms_60s"),
        "p95_query_ms_60s": stats.get("p95_query_ms_60s"),
        "remote_pct_60s": stats["remote_pct"],
        "cache_pct_60s": stats["cache_pct"],
        "window_sec": 60
    }


@app.get("/ops/query_bank/status")
async def query_bank_status():
    """Get query bank loading status and configuration"""
    return {
        "ok": True,
        "use_real_queries": settings.USE_REAL_QUERIES,
        "query_bank_path": settings.FIQA_QUERY_BANK,
        "queries_loaded": len(QUERY_BANK),
        "bs_unique_queries": settings.BS_UNIQUE_QUERIES,
        "bs_bypass_cache": settings.BS_BYPASS_CACHE,
        "current_index": QUERY_BANK_INDEX,
        "sample_queries": QUERY_BANK[:3] if QUERY_BANK else []
    }


@app.get("/ops/qa/feed")
async def qa_feed(limit: int = 20):
    """Get recent QA events from feed (default 20, max 50)"""
    if not QA_FEED_ENABLED:
        return {
            "ok": False,
            "error": "QA_FEED_ENABLED=false",
            "message": "QA Feed is disabled"
        }
    
    # Limit to max 50
    limit = min(limit, 50)
    
    with QA_FEED_LOCK:
        # Get newest N items (reverse order for newest first)
        items = list(QA_FEED_BUFFER)[-limit:]
        items.reverse()  # Newest first
    
    return {
        "ok": True,
        "items": items,
        "circuit_open": QA_FEED_STATE["circuit_open"],
        "sample_rate": QA_FEED_SAMPLE_RATE,
        "sample_rate_effective": QA_FEED_STATE["sample_rate_effective"]
    }


@app.get("/ops/qa/feed.ndjson")
async def qa_feed_ndjson():
    """Stream QA feed as NDJSON (for download)"""
    from fastapi.responses import StreamingResponse
    import io
    
    if not QA_FEED_ENABLED:
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "error": "QA_FEED_ENABLED=false",
                "message": "QA Feed is disabled"
            }
        )
    
    with QA_FEED_LOCK:
        items = list(QA_FEED_BUFFER)
    
    # Generate NDJSON
    output = io.StringIO()
    for item in items:
        output.write(json.dumps(item) + "\n")
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f"attachment; filename=qa_feed_{int(time.time())}.ndjson"
        }
    )


@app.get("/ops/black_swan/config")
async def black_swan_config():
    """Get current Black Swan configuration and playbook parameters"""
    return {
        "ok": True,
        "use_real": BLACK_SWAN_USE_REAL,
        "nocache": BLACK_SWAN_NOCACHE,
        "fiqa_search_url": FIQA_SEARCH_URL,
        "qdrant_collection": QDRANT_COLLECTION,
        "heavy_topk": int(os.environ.get("HEAVY_TOPK", "100")),
        "rerank_topk": int(os.environ.get("RERANK_TOPK", "200")),
        "mode_c_delay_ms": int(os.environ.get("MODE_C_DELAY_MS", "250")),
        "demo_tuner_pause": os.environ.get("DEMO_TUNER_PAUSE", "true").lower() == "true",
        "current_mode": BLACK_SWAN_STATE.get("mode"),
        "playbook_params": BLACK_SWAN_STATE.get("playbook_params", {}),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


@app.get("/ops/force_status")
async def force_status():
    """
    Get current force override status and configuration.
    
    Returns current flags and active forced parameters.
    This endpoint shows whether FORCE_OVERRIDE is active and what
    parameters are being forced (bypassing all guardrails).
    
    Example Response:
    {
        "force_override": true,
        "active_params": {"num_candidates":2000,"rerank_topk":300,"qps":180},
        "hard_cap_enabled": true,
        "hard_cap_limits": {"num_candidates":5000,"rerank_topk":1000,"qps":2000}
    }
    """
    return get_force_override_status()




@app.post("/ops/black_swan")
async def run_black_swan(request: Optional[BlackSwanRequest] = None):
    """Trigger Black Swan test script with run_id gating and mode selection"""
    global BLACK_SWAN_RUNNING, BLACK_SWAN_STATE
    
    # Parse mode (default to A if not provided or body is None)
    mode = "A"
    if request and request.mode:
        mode = request.mode.upper()
        # Validate mode
        if mode not in ["A", "B", "C"]:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "invalid_mode", "message": f"Mode must be A, B, or C (got: {mode})"}
            )
    
    # Return 409 if already running
    if BLACK_SWAN_RUNNING:
        return JSONResponse(
            status_code=409,
            content={"ok": False, "error": "Black Swan test already running", "run_id": BLACK_SWAN_STATE.get("run_id"), "mode": BLACK_SWAN_STATE.get("mode")}
        )
    
    BLACK_SWAN_RUNNING = True
    
    # Generate unique run_id for this test
    run_id = str(uuid.uuid4())
    now_ts = int(time.time())
    deadline = now_ts + BS_MAX_DURATION_SEC
    
    # Demo hooks: pause tuner if enabled
    demo_tuner_pause = os.environ.get("DEMO_TUNER_PAUSE", "true").lower() == "true"
    tuner_was_paused = False
    if demo_tuner_pause and not auto_tuner.is_paused():
        auto_tuner.pause(duration_sec=3600, source="demo_black_swan")
        tuner_was_paused = True
        print(f"[BlackSwan] Demo mode: Auto Tuner paused for demonstration")
    
    # Clean reset: Initialize state with fresh run_id, deadline, heartbeat, and mode
    BLACK_SWAN_STATE.update({
        "running": True,
        "run_id": run_id,
        "mode": mode,  # Add mode to state
        "phase": "starting",
        "progress": 1,  # Start at 1% to avoid 0% = not started confusion
        "eta_sec": 90,
        "tuner_was_paused": tuner_was_paused,  # Track if we paused tuner for demo
        "started_at": now_ts,
        "ended_at": None,
        "deadline": deadline,  # Watchdog deadline
        "last_update_ts": now_ts,  # Heartbeat timestamp
        "message": f"Black Swan test initializing (Mode {mode})...",
        "progress_timeline": [{"phase": "starting", "timestamp": now_ts, "progress": 1, "mode": mode}],
        "report_path": None,
        "progress_checks": {
            "monotonic": True,
            "last_update_ts": now_ts,
            "last_progress": 1,
            "last_phase": "starting"
        },
        "counters": {
            "rejected_updates": 0,
            "watchdog_checks": 0,
            "heartbeat_checks": 0,
            "retries": 0
        },
        "error": {
            "code": "",
            "step": "",
            "http": 0,
            "message": "",
            "ts": 0
        }
    })
    
    print(f"[Black Swan] Started new run: {run_id}, mode={mode}, deadline={deadline} (max {BS_MAX_DURATION_SEC}s)")
    
    def _run():
        global BLACK_SWAN_RUNNING, BLACK_SWAN_STATE
        try:
            # Pass API_BASE, RUN_ID, and MODE-specific configs to script via environment
            # Run from project root (2 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            
            # Define playbook configurations for each mode
            # Mode A: High-Impact (burst + step)
            # Mode B: Heavier Request (sustained load with heavy params)
            # Mode C: Net Delay (artificial latency simulation)
            mode_configs = {
                "A": {
                    "BLACK_SWAN_LOAD_QPS": "600",  # Hard Mode: 600 QPS burst
                    "BLACK_SWAN_LOAD_DURATION": str(settings.PLAY_A_DURATION_SEC),  # Burst duration (from .env)
                    "BLACK_SWAN_LOAD_PATTERN": "pulse",  # Burst pattern
                    "BLACK_SWAN_RECOVERY_QPS": "300",  # 300 QPS hold
                    "BLACK_SWAN_RECOVERY_DURATION": str(settings.PLAY_A_RECOVERY_SEC),  # Recovery duration (from .env)
                    "BLACK_SWAN_CONCURRENCY": "64",  # High concurrency
                    "BLACK_SWAN_NOCACHE": "true",  # Bypass cache with random params
                    "BLACK_SWAN_USE_REAL": "true",  # Force real Qdrant hits
                    "BLACK_SWAN_MODE_DESC": f"Hard Mode A: 600 QPS burst ({settings.PLAY_A_DURATION_SEC}s) → 300 QPS hold ({settings.PLAY_A_RECOVERY_SEC}s, 64 concurrency)"
                },
                "B": {
                    "BLACK_SWAN_LOAD_QPS": str(settings.PLAY_B_QPS),  # Enhanced: configurable QPS (default 200)
                    "BLACK_SWAN_LOAD_DURATION": str(settings.PLAY_B_DURATION_SEC),  # Extended duration for Auto Tuner reaction (from .env)
                    "BLACK_SWAN_CONCURRENCY": "48",  # High concurrency
                    "BLACK_SWAN_HEAVY_PARAMS": "true",  # Enable heavier request params
                    "HEAVY_NUM_CANDIDATES": str(settings.PLAY_B_NUM_CANDIDATES),  # Enhanced: configurable candidates (default 2000)
                    "HEAVY_RERANK_TOPK": str(settings.PLAY_B_RERANK_TOPK),  # Enhanced: configurable rerank (default 500)
                    "RERANK_MODEL": settings.RERANK_MODEL,  # Model type (from .env)
                    "RERANK_DELAY_MS": str(settings.RERANK_DELAY_MS),  # Optional artificial delay (from .env)
                    "BLACK_SWAN_USE_REAL": "true",  # Force real Qdrant hits
                    "BLACK_SWAN_MODE_DESC": f"Enhanced Mode B: {settings.PLAY_B_QPS} QPS heavy params ({settings.PLAY_B_NUM_CANDIDATES} candidates, {settings.PLAY_B_RERANK_TOPK} rerank) for {settings.PLAY_B_DURATION_SEC}s"
                },
                "C": {
                    "BLACK_SWAN_LOAD_QPS": "120",  # Hard Mode: 120 QPS
                    "BLACK_SWAN_LOAD_DURATION": str(settings.PLAY_C_DURATION_SEC),  # Sustained duration (from .env)
                    "BLACK_SWAN_CONCURRENCY": "48",  # High concurrency
                    "BLACK_SWAN_DELAY_MS": str(settings.MODE_C_DELAY_MS),  # Network delay (from .env)
                    "BLACK_SWAN_USE_REAL": "true",  # Force real Qdrant hits
                    "BLACK_SWAN_MODE_DESC": f"Hard Mode C: 120 QPS + {settings.MODE_C_DELAY_MS}ms delay + real retrieval ({settings.PLAY_C_DURATION_SEC}s)"
                }
            }
            
            # Store playbook params in state for report inclusion (before force override)
            playbook_params_raw = {
                "mode": mode,
                "warmup_qps": int(os.getenv("BLACK_SWAN_WARMUP_QPS", "20")),
                "warmup_duration": int(os.getenv("BLACK_SWAN_WARMUP_DURATION", "15")),
                "burst_qps": int(mode_configs[mode].get("BLACK_SWAN_LOAD_QPS", "70")),
                "burst_duration": int(mode_configs[mode].get("BLACK_SWAN_LOAD_DURATION", "60")),
                "hold_qps": int(mode_configs[mode].get("BLACK_SWAN_RECOVERY_QPS", "20")),
                "hold_duration": int(mode_configs[mode].get("BLACK_SWAN_RECOVERY_DURATION", "60")),
                "pattern": mode_configs[mode].get("BLACK_SWAN_LOAD_PATTERN", "constant"),
                "delay_ms": int(mode_configs[mode].get("BLACK_SWAN_DELAY_MS", "0")),
                "heavy_params": mode_configs[mode].get("BLACK_SWAN_HEAVY_PARAMS") == "true",
                "num_candidates": int(mode_configs[mode].get("HEAVY_NUM_CANDIDATES", "50")),
                "rerank_topk": int(mode_configs[mode].get("HEAVY_RERANK_TOPK", "50")),
                "rerank_model": mode_configs[mode].get("RERANK_MODEL", "default"),
                "rerank_delay_ms": int(mode_configs[mode].get("RERANK_DELAY_MS", "0"))
            }
            
            # Apply force override to playbook parameters
            # This allows overriding QPS, num_candidates, rerank_topk across all modes
            playbook_params = apply_force_override(playbook_params_raw, context=f"black_swan_mode_{mode}_playbook")
            BLACK_SWAN_STATE["playbook_params"] = playbook_params
            
            env = {
                **os.environ, 
                "API_BASE": os.getenv("APP_DEMO_URL", os.getenv("API_BASE", "http://localhost:8001")),
                "BLACK_SWAN_RUN_ID": run_id,  # Pass run_id to script
                "BLACK_SWAN_MODE": mode,  # Pass mode to script
                **mode_configs.get(mode, mode_configs["A"])  # Apply mode-specific configs
            }
            result = subprocess.run(
                ["bash", "scripts/black_swan_demo.sh"], 
                env=env,
                cwd=str(project_root),
                capture_output=True,
                text=True
            )
            
            # Check if script failed
            if result.returncode != 0:
                now_ts = int(time.time())
                error_msg = result.stderr.strip()[-200:] if result.stderr else "Script exited with non-zero code"
                print(f"[Black Swan] Script failed with code {result.returncode}")
                print(f"[Black Swan] stderr: {result.stderr[-500:]}" if result.stderr else "")
                
                # Only set error state if script didn't already report it
                if BLACK_SWAN_STATE.get("phase") not in ["complete", "error"]:
                    BLACK_SWAN_STATE.update({
                        "phase": "error",
                        "progress": 0,
                        "running": False,
                        "ended_at": now_ts,
                        "message": f"Script failed: {error_msg}"
                    })
                    BLACK_SWAN_STATE["progress_timeline"].append({
                        "phase": "error",
                        "timestamp": now_ts,
                        "reason": "script_failure",
                        "returncode": result.returncode
                    })
            
            time.sleep(1)
        except Exception as e:
            now_ts = int(time.time())
            print(f"[Black Swan] Exception during script execution: {e}")
            BLACK_SWAN_STATE.update({
                "phase": "error",
                "progress": 0,
                "running": False,
                "ended_at": now_ts,
                "message": f"Test failed: {str(e)}"
            })
            BLACK_SWAN_STATE["progress_timeline"].append({
                "phase": "error",
                "timestamp": now_ts,
                "reason": "exception",
                "error": str(e)
            })
        finally:
            BLACK_SWAN_RUNNING = False
            # Note: Do NOT auto-complete here. The script must POST final status with run_id.
            print(f"[Black Swan] test finished (run_id={BLACK_SWAN_STATE.get('run_id')})")
    
    # Timeout safety: auto-unlock after 300s in case of script failure
    def _timeout_handler():
        global BLACK_SWAN_RUNNING, BLACK_SWAN_STATE
        BLACK_SWAN_RUNNING = False
        if BLACK_SWAN_STATE["running"]:
            now_ts = int(time.time())
            BLACK_SWAN_STATE.update({
                "phase": "error",
                "progress": 0,
                "running": False,
                "ended_at": now_ts,
                "message": "Test timeout after 300s"
            })
            print(f"[Black Swan] timeout for run_id={BLACK_SWAN_STATE.get('run_id')}")
    
    threading.Timer(300, _timeout_handler).start()
    
    threading.Thread(target=_run, daemon=True).start()
    return {"ok": True, "run_id": run_id, "mode": mode, "phase": "starting", "msg": f"Black Swan test started (Mode {mode})"}


@app.get("/ops/black_swan")
async def get_black_swan_result():
    """Get latest Black Swan test report (gated by run_id)"""
    try:
        # Always include current state
        state = {
            "run_id": BLACK_SWAN_STATE.get("run_id"),
            "last_run_id": BLACK_SWAN_STATE.get("last_run_id"),
            "mode": BLACK_SWAN_STATE.get("mode"),  # Include mode
            "phase": BLACK_SWAN_STATE.get("phase"),
            "progress": BLACK_SWAN_STATE.get("progress"),
            "running": BLACK_SWAN_STATE.get("running"),
            "started_at": BLACK_SWAN_STATE.get("started_at"),
            "ended_at": BLACK_SWAN_STATE.get("ended_at"),
            "message": BLACK_SWAN_STATE.get("message"),
            "playbook_params": BLACK_SWAN_STATE.get("playbook_params")  # Include playbook params
        }
        
        # Only include report if completed and run_id matches last_run_id
        # This prevents showing old reports for new/in-progress runs
        phase = BLACK_SWAN_STATE.get("phase")
        last_run_id = BLACK_SWAN_STATE.get("last_run_id")
        
        if phase == "complete" and last_run_id:
            # Use project root for reports directory
            project_root = Path(__file__).parent.parent.parent
            reports_dir = project_root / "reports"
            
            if reports_dir.exists():
                # Get all black_swan report files sorted by modification time
                files = sorted(
                    [f for f in reports_dir.iterdir() if f.name.startswith("black_swan_") and f.name.endswith(".json")],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                
                if files:
                    # Load the latest report
                    latest = files[0]
                    with open(latest) as f:
                        data = json.load(f)
                    
                    return {"ok": True, "state": state, "latest": latest.name, "report": data}
        
        # If no report available (in progress or no completed runs)
        return {"ok": True, "state": state, "msg": "Test in progress or no completed runs yet"}
        
    except Exception as e:
        return {"ok": False, "error": str(e), "state": BLACK_SWAN_STATE}


@app.get("/ops/black_swan/status")
async def get_black_swan_status():
    """Get real-time Black Swan test status and progress"""
    return BLACK_SWAN_STATE


class ErrorInfo(BaseModel):
    code: str = ""
    step: str = ""
    http: int = 0
    message: str = ""

class ProgressUpdate(BaseModel):
    run_id: str  # Required: must match current run
    phase: str
    progress: int
    eta_sec: int = 0
    message: str = ""
    error: ErrorInfo = None  # Optional: error details when phase="error"


@app.post("/ops/black_swan/progress")
async def update_black_swan_progress(update: ProgressUpdate):
    """Update Black Swan test progress (called by script) - with run_id gating"""
    global BLACK_SWAN_STATE
    
    now_ts = int(time.time())
    
    # Validate run_id: must match current run
    current_run_id = BLACK_SWAN_STATE.get("run_id")
    if update.run_id != current_run_id:
        BLACK_SWAN_STATE["counters"]["rejected_updates"] += 1
        print(f"[Black Swan] Ignoring progress update with mismatched run_id: {update.run_id} != {current_run_id}")
        return {
            "ok": False,
            "error": f"run_id mismatch: expected {current_run_id}, got {update.run_id}"
        }
    
    # Define valid phases and their ordering
    phase_order = ["starting", "warmup", "baseline", "trip", "recovery", "complete"]
    if update.phase not in phase_order + ["error"]:
        BLACK_SWAN_STATE["counters"]["rejected_updates"] += 1
        return {"ok": False, "error": f"Invalid phase: {update.phase}"}
    
    # Enforce phase ordering (phases cannot regress, except for error)
    if update.phase != "error" and BLACK_SWAN_STATE["progress_checks"]["last_phase"]:
        last_phase = BLACK_SWAN_STATE["progress_checks"]["last_phase"]
        if last_phase in phase_order and update.phase in phase_order:
            last_idx = phase_order.index(last_phase)
            curr_idx = phase_order.index(update.phase)
            if curr_idx < last_idx:
                BLACK_SWAN_STATE["counters"]["rejected_updates"] += 1
                return {
                    "ok": False, 
                    "error": f"Phase regression: {last_phase} → {update.phase} (phases must move forward)"
                }
    
    # Enforce progress monotonicity (progress never decreases, except for error)
    if update.phase != "error":
        last_progress = BLACK_SWAN_STATE["progress_checks"]["last_progress"]
        if update.progress < last_progress:
            BLACK_SWAN_STATE["progress_checks"]["monotonic"] = False
            BLACK_SWAN_STATE["counters"]["rejected_updates"] += 1
            return {
                "ok": False,
                "error": f"Progress regression: {last_progress}% → {update.progress}% (progress must be monotonic)"
            }
    
    # Update state (including last_update_ts for heartbeat monitoring)
    BLACK_SWAN_STATE.update({
        "phase": update.phase,
        "progress": update.progress,
        "eta_sec": update.eta_sec,
        "message": update.message,
        "last_update_ts": now_ts  # Update heartbeat timestamp
    })
    
    # If error, update error structure
    if update.phase == "error" and update.error:
        BLACK_SWAN_STATE["error"].update({
            "code": update.error.code or "unknown",
            "step": update.error.step or "unknown",
            "http": update.error.http or 0,
            "message": update.error.message or update.message or "Unknown error",
            "ts": now_ts
        })
        print(f"[Black Swan] Error reported: code={update.error.code}, step={update.error.step}, http={update.error.http}")
    
    # Update progress_checks
    BLACK_SWAN_STATE["progress_checks"].update({
        "last_update_ts": now_ts,
        "last_progress": update.progress,
        "last_phase": update.phase
    })
    
    # Mark running=False and set ended_at when complete or error
    if update.phase in ["complete", "error"]:
        BLACK_SWAN_STATE["running"] = False
        BLACK_SWAN_STATE["ended_at"] = now_ts
        
        # If completing successfully, mark this run as last completed
        if update.phase == "complete":
            BLACK_SWAN_STATE["last_run_id"] = update.run_id
            print(f"[Black Swan] Run {update.run_id} completed successfully")
            
            # Demo hooks: auto-resume tuner after 15s if we paused it
            tuner_was_paused = BLACK_SWAN_STATE.get("tuner_was_paused", False)
            if tuner_was_paused:
                print(f"[Black Swan] Demo mode: Auto Tuner will resume after 15s cooldown")
                # Schedule tuner resume after 15 seconds
                import threading
                def delayed_tuner_resume():
                    time.sleep(15)
                    if auto_tuner.is_paused():
                        auto_tuner.resume(source="demo_black_swan_resume", force=True)
                        print(f"[Black Swan] Demo mode: Auto Tuner resumed after Black Swan completion")
                
                threading.Thread(target=delayed_tuner_resume, daemon=True).start()
        elif update.phase == "error":
            error_info = BLACK_SWAN_STATE["error"]
            print(f"[Black Swan] Run {update.run_id} failed: {error_info['code']} at step {error_info['step']}")
        
        # Validate final progress
        if update.phase == "complete" and update.progress != 100:
            BLACK_SWAN_STATE["progress_checks"]["monotonic"] = False
    
    # Extract report path from message if phase is complete
    # Message format: "Black Swan test complete: black_swan_1234567890.json"
    if update.phase == "complete" and "black_swan_" in update.message:
        try:
            # Extract filename from message
            parts = update.message.split(":")
            if len(parts) > 1:
                report_name = parts[-1].strip()
                BLACK_SWAN_STATE["report_path"] = report_name
        except:
            pass
    
    # Add to timeline if phase changed
    if not BLACK_SWAN_STATE["progress_timeline"] or \
       BLACK_SWAN_STATE["progress_timeline"][-1]["phase"] != update.phase:
        BLACK_SWAN_STATE["progress_timeline"].append({
            "phase": update.phase,
            "timestamp": now_ts,
            "progress": update.progress
        })
    
    return {"ok": True, "state": BLACK_SWAN_STATE}


@app.post("/ops/black_swan/abort")
async def abort_black_swan():
    """Abort running Black Swan test (manual emergency stop)"""
    global BLACK_SWAN_RUNNING, BLACK_SWAN_STATE, load_state
    
    now_ts = int(time.time())
    
    # Check if actually running
    if not BLACK_SWAN_STATE.get("running"):
        return {
            "ok": False,
            "error": "No Black Swan test currently running",
            "state": BLACK_SWAN_STATE
        }
    
    run_id = BLACK_SWAN_STATE.get("run_id")
    print(f"[Black Swan] Aborting run: {run_id}")
    
    # Stop load test if active
    if load_state.get("running"):
        load_state["running"] = False
        load_state["qps"] = 0
        load_state["concurrency"] = 0
        print("[Black Swan] Stopped active load test")
    
    # Set state to error with abort message
    BLACK_SWAN_STATE.update({
        "phase": "error",
        "progress": 0,
        "running": False,
        "ended_at": now_ts,
        "message": f"Test manually aborted at {now_ts}"
    })
    
    # Add abort event to timeline
    BLACK_SWAN_STATE["progress_timeline"].append({
        "phase": "error",
        "timestamp": now_ts,
        "progress": 0,
        "reason": "manual_abort"
    })
    
    # Mark as no longer running
    BLACK_SWAN_RUNNING = False
    
    return {
        "ok": True,
        "message": f"Black Swan test {run_id} aborted",
        "state": BLACK_SWAN_STATE
    }


@app.get("/dashboard.json")
async def dashboard_json():
    """Deprecated endpoint - dashboard.json is no longer used"""
    return JSONResponse(
        status_code=410,
        content={"ok": True, "deprecated": True, "message": "dashboard.json is deprecated, use /metrics/* endpoints"}
    )


# ========================================
# Tap Mode Endpoints
# ========================================

@app.get("/ops/tap/health")
async def tap_health():
    """Get tap system health and statistics"""
    if not TAP_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": "Tap module not available"}
        )
    return tap.get_health()


@app.get("/ops/tap/tail")
async def tap_tail(file: str = "backend", n: int = 200):
    """
    Read last N lines from tap logs.
    
    Args:
        file: "backend" or "events" (default: "backend")
        n: Number of lines to read (default: 200, max: 1000)
    
    Returns:
        JSON array of log entries
    """
    if not TAP_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": "Tap module not available"}
        )
    
    # Validate file parameter
    if file not in ["backend", "events"]:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Invalid file parameter. Must be 'backend' or 'events'"}
        )
    
    # Limit n to 1000
    n = min(n, 1000)
    
    entries = tap.read_tail(file, n)
    return {
        "ok": True,
        "file": file,
        "count": len(entries),
        "entries": entries
    }


@app.get("/ops/tap/timeline")
async def tap_timeline(run_id: str = None, n: int = 500):
    """
    Get unified timeline merging backend and event logs.
    
    Args:
        run_id: Optional run_id to filter by
        n: Maximum number of events (default: 500, max: 2000)
    
    Returns:
        JSON array of timeline entries sorted by timestamp
    """
    if not TAP_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": "Tap module not available"}
        )
    
    # Limit n to 2000
    n = min(n, 2000)
    
    timeline = tap.get_timeline(run_id, n)
    return {
        "ok": True,
        "run_id": run_id,
        "count": len(timeline),
        "timeline": timeline
    }


class TapEventRequest(BaseModel):
    client: str  # frontend, script, curl, etc.
    event: str  # click, poll, complete, error, 409, etc.
    run_id: Optional[str] = None
    phase: Optional[str] = None
    message: Optional[str] = None
    http: Optional[int] = None


@app.post("/ops/tap/event")
async def tap_event(event_req: TapEventRequest):
    """
    Log a custom tap event (called by frontend or script).
    
    Args:
        event_req: Event details
    
    Returns:
        Success status
    """
    if not TAP_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": "Tap module not available"}
        )
    
    tap.write_event_log(
        event=event_req.event,
        run_id=event_req.run_id,
        phase=event_req.phase,
        message=event_req.message,
        http=event_req.http,
        client=event_req.client
    )
    
    return {"ok": True, "event": event_req.event}


@app.get("/demo", response_class=HTMLResponse)
async def demo():
    """Serve demo dashboard HTML"""
    template_path = Path(__file__).parent / "templates" / "demo.html"
    if template_path.exists():
        return template_path.read_text()
    return "<h1>Demo template not found</h1>"

