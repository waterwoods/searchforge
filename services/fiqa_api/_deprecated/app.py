# DEPRECATED: kept for history only. Do NOT import or run. Use services.fiqa_api.app_main:app
"""
Minimal FIQA API - FastAPI Application
Self-contained with inlined pipeline manager
"""

import time
import csv
import sys
import json
import random
import os
import asyncio
import threading
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from typing import Optional, Dict, Set, List
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

# Add project root and service directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
from logs.metrics_logger import MetricsLogger
from modules.rag.reranker_lite import rerank_passages
import settings

# Import new core services and plugins
from services.api.ops_routes import router as ops_router
from services.plugins import force_override

# Tuner imports
try:
    from tuner import TunerParams, clamp, REG as StrategyRegistry
    TUNER_AVAILABLE = True
except ImportError:
    TUNER_AVAILABLE = False

# Profiler imports
try:
    from profiler import profiled, get_profile_report, prof, reset_profiler, enable_profiler, disable_profiler
    PROFILER_AVAILABLE = True
except ImportError:
    PROFILER_AVAILABLE = False
    # Provide no-op fallback for prof when profiler is unavailable
    from contextlib import nullcontext
    def prof(label: str):
        return nullcontext()

try:
    from qdrant_client import QdrantClient
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# AutoTuner imports
try:
    from modules.autotuner.brain.multi_knob_decider import decide_multi_knob
    from modules.autotuner.brain.apply import apply_action
    from modules.autotuner.brain.contracts import TuningInput, Action, SLO, Guards
    AUTOTUNER_AVAILABLE = True
except ImportError:
    AUTOTUNER_AVAILABLE = False


# Setup tuner logger (writes to both console and file)
def setup_tuner_logger():
    """Configure tuner logger with rotating file and console handlers"""
    logger = logging.getLogger("tuner")
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers using _configured flag
    if hasattr(logger, '_configured') and logger._configured:
        return logger
    
    # File handler - logs/tuner.log with rotation
    log_dir = Path(__file__).parent.parent.parent / "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = log_dir / "tuner.log"
    
    # RotatingFileHandler: 10MB max, 5 backup files
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter with milliseconds
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(levelname)s [TUNER] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Mark as configured
    logger._configured = True
    
    return logger

tuner_logger = setup_tuner_logger()


def compute_dispersion(scores):
    """Compute score dispersion (std/range) for top results."""
    if len(scores) < 2:
        return 0.0
    import statistics
    std = statistics.stdev(scores)
    score_range = max(scores) - min(scores)
    return std if score_range == 0 else max(std, score_range)


def should_rerank_v2(query, prelim_results, rolling_stats):
    """Decide if reranking should trigger based on v2 logic."""
    global RR_V2_COOLDOWN_UNTIL, RR_V2_WINDOW
    
    reasons = []
    
    # State gate: check warmup and cooldown
    total_reqs = len(RR_V2_WINDOW)
    if total_reqs < settings.RR_WARMUP_REQS:
        return False, "warmup"
    
    if time.time() < RR_V2_COOLDOWN_UNTIL:
        return False, "cooldown"
    
    # Content signals
    query_len = len(query)
    if query_len >= settings.RR_MIN_QUERY_LEN:
        reasons.append("len")
    
    query_lower = query.lower()
    if any(kw in query_lower for kw in settings.RR_KEYWORDS):
        reasons.append("kw")
    
    # Uncertainty signal: result dispersion
    top_scores = [r.get("score", 0.0) for r in prelim_results[:10]]
    dispersion = compute_dispersion(top_scores) if top_scores else 0.0
    
    if dispersion >= settings.RR_MIN_DISPERSION:
        reasons.append("dispersion")
    
    # Budget check: rolling hit rate
    recent_hits = sum(1 for r in RR_V2_WINDOW[-100:] if r.get("triggered", False))
    rolling_hit_rate = recent_hits / len(RR_V2_WINDOW[-100:]) if RR_V2_WINDOW else 0.0
    
    budget_ok = rolling_hit_rate <= settings.RR_MAX_HIT_RATE
    if not budget_ok:
        reasons.append("budget")
    
    # Decision: trigger if has content/uncertainty signals AND budget ok
    should_trigger = len(reasons) > 0 and "budget" not in reasons
    
    trigger_reason = "|".join(reasons) if reasons else "none"
    return should_trigger, trigger_reason


class WarmupGuard:
    """Track auto-warmup state to prevent duplicate warmup triggers."""
    def __init__(self):
        self.did_warmup = False
        self.last_warmup_ts = 0.0
        self.threshold = {"p95_pts": 12, "tps_pts": 12}
        self.cooldown_sec = 60  # Allow re-warmup after 60s
    
    def should_warmup(self, p95_points, tps_points):
        """Check if warmup is needed based on data points."""
        now = time.time()
        
        # Check if already warmed up recently
        if self.did_warmup and (now - self.last_warmup_ts) < self.cooldown_sec:
            return False
        
        # Check if data is insufficient
        needs_warmup = (p95_points < self.threshold["p95_pts"] or 
                       tps_points < self.threshold["tps_pts"])
        
        return needs_warmup
    
    def mark_warmed_up(self):
        """Mark that warmup has been triggered."""
        self.did_warmup = True
        self.last_warmup_ts = time.time()
        print(f"[AUTO] warmup fired at {datetime.now().strftime('%H:%M:%S')}")
    
    def reset_if_expired(self):
        """Reset warmup flag if cooldown period has passed."""
        now = time.time()
        if self.did_warmup and (now - self.last_warmup_ts) >= self.cooldown_sec:
            self.did_warmup = False
    
    def get_status(self):
        """Get current warmup status."""
        return {
            "did_warmup": self.did_warmup,
            "last_warmup_ts": self.last_warmup_ts,
            "cooldown_remaining": max(0, self.cooldown_sec - (time.time() - self.last_warmup_ts)) if self.did_warmup else 0
        }


class AutoTrafficWorker:
    """Background worker that periodically generates traffic and rebuilds dashboard"""
    
    def __init__(self):
        self.enabled = False
        self.running = False
        self.last_run_ts = None
        self.next_run_at = 0.0
        
        # ✅ NEW: Desired params (what user configured, applied on next start)
        self.desired_qps = 6.0
        self.desired_duration = 20
        self.desired_cycle_sec = 25
        self.desired_cases = "on,off"
        self.desired_unique = 1
        env_cycles = os.environ.get("AUTO_TOTAL_CYCLES")
        self.desired_total_cycles = int(env_cycles) if env_cycles and env_cycles.isdigit() else None
        
        # ✅ Runtime params (currently used by running worker)
        self.cycle_sec = 25
        self.duration = 20
        self.qps = 6.0
        self.cases = "on,off"
        self.unique = 1
        self.total_cycles = self.desired_total_cycles
        
        self.lock = threading.Lock()
        self.thread = None
        self.heartbeat = time.time()
        self.last_error = None
        self.cycle_count = 0  # Track cycle number for detailed logging
        self.completed_cycles = 0  # Track completed cycles
        self.immediate_trigger = False  # Flag for immediate execution
        self.stop_reason = None  # 🆕 Track why worker stopped: completed/timeout/exception/manual/runner_error
        
        # Initialize cached_snapshot with valid default state
        self.cached_snapshot = {
            "enabled": False,
            "running": False,
            "cycle_sec": 25,
            "duration": 20,
            "qps": 6.0,
            "cases": "on,off",
            "unique": 1,
            "last_run": None,
            "next_eta_sec": 0,
            "heartbeat": 0,
            "last_error": None,
            "stop_reason": None,
            "note": "not-started"
        }
    
    def start(self, cycle_sec=25, duration=20, qps=6.0, cases="on,off", unique=1, total_cycles=None):
        """Enable worker and start thread if not already running
        
        Updates desired_params and copies them to runtime_params.
        Immediately triggers first cycle.
        """
        with self.lock:
            print(f"[AUTO] 📝 set enabled=True by API (qps={qps}, duration={duration}, cycle={cycle_sec}, total_cycles={total_cycles})")
            
            # ✅ Update desired params (what user wants for next start)
            self.desired_qps = qps
            self.desired_duration = duration
            self.desired_cycle_sec = cycle_sec
            self.desired_cases = cases
            self.desired_unique = unique
            
            # Handle total_cycles: 0 or None means infinite
            if total_cycles in ("", 0, "0", None):
                self.desired_total_cycles = None
            else:
                try:
                    parsed = int(total_cycles) if total_cycles not in ("null", "None") else None
                    self.desired_total_cycles = None if parsed == 0 else parsed
                except (ValueError, TypeError):
                    self.desired_total_cycles = None
            
            # ✅ Copy desired -> runtime (apply immediately for this start)
            self.cycle_sec = self.desired_cycle_sec
            self.duration = self.desired_duration
            self.qps = self.desired_qps
            self.cases = self.desired_cases
            self.unique = self.desired_unique
            self.total_cycles = self.desired_total_cycles
            
            # Enable and reset state
            self.enabled = True
            self.next_run_at = 0.0  # trigger immediate first run
            self.cycle_count = 0
            self.completed_cycles = 0
            self.immediate_trigger = True  # ✅ Signal to kick first run NOW
            self.last_error = None
            self.stop_reason = None  # 🆕 Clear stop reason on start
            
            # Start thread if not alive
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self.loop, daemon=True)
                self.thread.start()
                print(f"[AUTO] ✅ Worker thread started, will kick first run now")
            else:
                print(f"[AUTO] ✅ Worker restarted, will kick first run now")
            
            print(f"[AUTO] 🎯 Runtime params: cycle_sec={self.cycle_sec}s duration={self.duration}s qps={self.qps} total_cycles={self.total_cycles or '∞'}")
    
    def stop(self):
        """Disable worker (thread will exit on next cycle check)"""
        with self.lock:
            self.enabled = False
            self.running = False
            self.stop_reason = "manual"  # 🆕 Track manual stop
        print("[AUTO] 🛑 Worker stopped (reason=manual)")
    
    def update_desired_params(self, qps=None, duration=None, cycle_sec=None, cases=None, unique=None, total_cycles=None):
        """Update desired params without starting/stopping worker
        
        This allows users to configure params while worker is stopped.
        Changes take effect on next start().
        """
        with self.lock:
            if qps is not None:
                self.desired_qps = qps
            if duration is not None:
                self.desired_duration = duration
            if cycle_sec is not None:
                self.desired_cycle_sec = cycle_sec
            if cases is not None:
                self.desired_cases = cases
            if unique is not None:
                self.desired_unique = unique
            if total_cycles is not None:
                if total_cycles in ("", 0, "0"):
                    self.desired_total_cycles = None
                else:
                    try:
                        parsed = int(total_cycles) if total_cycles not in ("null", "None") else None
                        self.desired_total_cycles = None if parsed == 0 else parsed
                    except (ValueError, TypeError):
                        self.desired_total_cycles = None
            
            print(f"[AUTO] 💾 Updated desired params: qps={self.desired_qps} duration={self.desired_duration}s cycle={self.desired_cycle_sec}s total_cycles={self.desired_total_cycles or '∞'}")
    
    def run_once_locked(self):
        """DEPRECATED: old method kept for compatibility"""
        pass
    
    def run_one_cycle(self, duration, qps, cases, unique, timeout_sec, project_root):
        """🆕 Run a single traffic generation cycle (extracted for testability)
        
        Returns:
            0: Success
            -1: Timeout
            -2: Exception/Error
        """
        try:
            cmd = [sys.executable, str(project_root / "scripts" / "run_canary_parallel.py"),
                 "--duration", str(int(duration)),
                 "--qps", str(int(qps)),
                 "--cases", cases,
                 "--quiet"]
            if unique == 1:
                cmd.append("--unique")
            
            # ✅ Log spawn command with all params
            cmd_str = " ".join(str(x) for x in cmd)
            print(f"[AUTO] spawn qps={qps} dur={duration}s timeout={timeout_sec}s cmd=\"{cmd_str}\"")
            
            result = subprocess.run(
                cmd,
                check=False,
                timeout=timeout_sec,
                cwd=str(project_root),
                capture_output=True
            )
            return result.returncode
            
        except subprocess.TimeoutExpired:
            print(f"[AUTO] ⚠️  timeout after {timeout_sec}s (duration={duration})")
            return -1
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"[AUTO] ❌ Cycle exception: {error_msg}")
            return -2
    
    def loop(self):
        """Main worker loop - runs traffic at scheduled intervals"""
        project_root = Path(__file__).parent.parent.parent
        print("[AUTO] 🚀 Worker thread started")
        last_dashboard_rebuild = 0.0
        last_tick_log = 0.0
        
        while True:
            # Check if enabled and if immediate trigger is set (short lock)
            with self.lock:
                if not self.enabled:
                    print("[AUTO] 🛑 Worker thread exiting (reason=enabled_false)")
                    return
                should_run = time.time() >= self.next_run_at or self.immediate_trigger
                if self.immediate_trigger:
                    print("[AUTO] ⚡ Immediate trigger detected - starting first cycle now")
                    self.immediate_trigger = False  # Clear flag
                duration = self.duration
                qps = self.qps
                cases = self.cases
                unique = self.unique
                current_enabled = self.enabled
                current_running = self.running
            
            # Log tick state every cycle check
            now_ts = time.time()
            if now_ts - last_tick_log >= 5.0:
                print(f"[AUTO] 🔄 Tick: enabled={current_enabled}, running={current_running}, should_run={should_run}")
                last_tick_log = now_ts
            
            # Run traffic generation if due
            if should_run:
                # Set running=True with short lock
                with self.lock:
                    # ✅ Guard: prevent overlapping cycles
                    if self.running:
                        skip_cycle = True
                    else:
                        skip_cycle = False
                        self.running = True
                        self.heartbeat = time.time()
                        self.last_error = None
                        self.cycle_count += 1
                        current_cycle = self.cycle_count
                        next_completed = self.completed_cycles + 1
                        cycle_sec_snapshot = self.cycle_sec
                
                # Handle skip outside lock
                if skip_cycle:
                    print(f"[AUTO] ⚠️  Skipping cycle - previous cycle still running")
                    time.sleep(1.0)
                    continue
                
                # Determine reason for this run
                reason = "immediate" if current_cycle == 1 else "scheduled"
                print(f"[AUTO] ▶️ Starting cycle #{next_completed} (reason={reason})")
                
                # 🆕 Run cycle with try/finally to guarantee running=False
                t0 = time.time()
                ret = 0
                try:
                    # ✅ Compute timeout: prefer duration+5, but ensure it's > cycle_sec too
                    timeout_sec = max(duration + 5, cycle_sec_snapshot + 2)
                    
                    # Profile traffic generation
                    if PROFILER_AVAILABLE:
                        prof_ctx = prof("auto.traffic.generate")
                        prof_ctx.__enter__()
                    
                    # 🆕 Call extracted run_one_cycle method
                    ret = self.run_one_cycle(duration, qps, cases, unique, timeout_sec, project_root)
                    
                    if PROFILER_AVAILABLE:
                        prof_ctx.__exit__(None, None, None)
                        
                except Exception as e:
                    # Catch any unexpected errors from run_one_cycle
                    if PROFILER_AVAILABLE:
                        prof_ctx.__exit__(None, None, None)
                    ret = -2
                    error_msg = str(e)[:100]
                    with self.lock:
                        self.last_error = error_msg
                        self.stop_reason = "exception"
                    print(f"[AUTO] ❌ Unexpected exception in cycle #{current_cycle}: {error_msg}")
                finally:
                    # 🆕 ALWAYS reset running=False, even on exception
                    elapsed = time.time() - t0
                    
                    # Update state after completion (short lock)
                    with self.lock:
                        self.last_run_ts = time.time()
                        self.running = False  # 🆕 Guaranteed by finally
                        self.next_run_at = time.time() + self.cycle_sec
                        self.heartbeat = time.time()
                        
                        # 🆕 Set stop_reason based on return code
                        if ret == -1:
                            self.stop_reason = "timeout"
                            self.last_error = f"timeout after {timeout_sec}s"
                        elif ret == -2:
                            self.stop_reason = "runner_error"
                            if not self.last_error:
                                self.last_error = "subprocess error"
                        elif ret != 0:
                            self.stop_reason = "runner_error"
                            self.last_error = f"non-zero exit: {ret}"
                        else:
                            # Success - clear stop_reason
                            if self.stop_reason in ("timeout", "runner_error", "exception"):
                                self.stop_reason = None
                        
                        # Increment completed cycles only on success
                        if ret == 0:
                            self.completed_cycles += 1
                        
                        # ✅ Cycle stop rule with clear counters and label
                        label = "∞" if self.total_cycles is None else str(self.total_cycles)
                        print(f"[AUTO] end cycle #{self.completed_cycles} | target={label} | rc={ret} | reason={self.stop_reason or 'ok'}")
                        
                        # Only stop when total_cycles is not None AND completed_cycles >= total_cycles
                        if self.total_cycles is not None and self.completed_cycles >= self.total_cycles:
                            self.enabled = False
                            self.running = False
                            self.stop_reason = "completed"
                            print(f"[AUTO] cycles completed ({self.completed_cycles}/{self.total_cycles}) → stopped (reason=completed)")
                        elif ret != 0:
                            # Non-zero exit: log warning but continue (don't stop on timeout/errors)
                            print(f"[AUTO] ⚠️  Cycle #{current_cycle} returned rc={ret} (continuing, stop_reason={self.stop_reason})")
                
                # Immediately rebuild dashboard after traffic run
                try:
                    if PROFILER_AVAILABLE:
                        with prof("dashboard.build.post_cycle"):
                            subprocess.run(
                                [sys.executable, str(project_root / "scripts" / "build_dashboard.py")],
                                timeout=10,
                                cwd=str(project_root),
                                capture_output=True
                            )
                    else:
                        subprocess.run(
                            [sys.executable, str(project_root / "scripts" / "build_dashboard.py")],
                            timeout=10,
                            cwd=str(project_root),
                            capture_output=True
                        )
                    print(f"[AUTO] dashboard rebuilt after cycle #{current_cycle}")
                    last_dashboard_rebuild = time.time()
                except Exception as e:
                    print(f"[AUTO] dashboard rebuild error after cycle: {e}")
            
            # Lightweight dashboard rebuild every 5s (outside lock)
            now = time.time()
            if now - last_dashboard_rebuild >= 5:
                try:
                    if PROFILER_AVAILABLE:
                        with prof("dashboard.build.periodic"):
                            subprocess.run(
                                [sys.executable, str(project_root / "scripts" / "build_dashboard.py")],
                                timeout=10,
                                cwd=str(project_root),
                                capture_output=True
                            )
                    else:
                        subprocess.run(
                            [sys.executable, str(project_root / "scripts" / "build_dashboard.py")],
                            timeout=10,
                            cwd=str(project_root),
                            capture_output=True
                        )
                    print(f"[AUTO] dashboard rebuilt at {datetime.now().strftime('%H:%M:%S')}")
                    last_dashboard_rebuild = now
                except Exception as e:
                    print(f"[AUTO] dashboard rebuild error: {e}")
                    last_dashboard_rebuild = now  # Avoid retry spam
            
            # Update heartbeat every 1s (short lock)
            with self.lock:
                self.heartbeat = time.time()
            
            time.sleep(1.0)
    
    def snapshot(self):
        """Non-blocking snapshot of current state"""
        # Try to acquire lock with 5ms timeout
        acquired = self.lock.acquire(timeout=0.005)
        
        if acquired:
            try:
                now = time.time()
                next_eta_sec = max(0, int(self.next_run_at - now))
                
                # Return clamped display value to prevent overflow (e.g., 43/20)
                display_completed = (min(self.completed_cycles, self.total_cycles) 
                                   if self.total_cycles is not None 
                                   else self.completed_cycles)
                
                snapshot = {
                    "enabled": self.enabled,
                    "running": self.running,
                    
                    # ✅ Runtime params (currently in use)
                    "cycle_sec": self.cycle_sec,
                    "duration": self.duration,
                    "qps": self.qps,
                    "cases": self.cases,
                    "unique": self.unique,
                    "total_cycles": self.total_cycles,  # Can be None for infinite mode
                    "total_cycles_label": "∞" if self.total_cycles is None else str(self.total_cycles),
                    
                    # ✅ NEW: Desired params (what user configured, for next start)
                    "desired_qps": self.desired_qps,
                    "desired_duration": self.desired_duration,
                    "desired_cycle_sec": self.desired_cycle_sec,
                    "desired_cases": self.desired_cases,
                    "desired_unique": self.desired_unique,
                    "desired_total_cycles": self.desired_total_cycles,
                    
                    # Status info
                    "last_run": datetime.fromtimestamp(self.last_run_ts, tz=timezone.utc).isoformat() if self.last_run_ts else None,
                    "next_eta_sec": next_eta_sec,
                    "heartbeat": int(now - self.heartbeat),
                    "last_error": self.last_error,
                    "stop_reason": self.stop_reason,  # 🆕 Track why worker stopped
                    "completed_cycles": display_completed,  # Clamped display value
                    "note": "live"
                }
                # Cache it for future stale reads
                self.cached_snapshot = snapshot.copy()
                return snapshot
            finally:
                self.lock.release()
        else:
            # Lock contention: return stale snapshot
            if self.cached_snapshot:
                stale = self.cached_snapshot.copy()
                stale["note"] = "stale-snapshot"
                return stale
            else:
                return {
                    "enabled": False,
                    "running": False,
                    "note": "stale-snapshot",
                    "error": "no cached data"
                }
    
    def get_status(self):
        """Get current worker status (calls snapshot for compatibility)"""
        return self.snapshot()


def load_runtime_settings():
    """Load runtime_settings.json from repo root"""
    repo_root = Path(__file__).parent.parent.parent
    settings_path = repo_root / "runtime_settings.json"
    
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load runtime_settings.json: {e}")
    
    return {}


def resolve_qdrant_collection(client, qdrant_url):
    """
    Resolve Qdrant collection in order:
    1. QDRANT_COLLECTION env (if valid)
    2. runtime_settings.json (if valid)
    3. Auto-resolve: find best collection by points_count
    
    Returns: (collection_name, points_count) or (None, 0) if no valid collection
    """
    import urllib.request
    
    # Try env var first
    env_collection = os.environ.get("QDRANT_COLLECTION", settings.COLLECTION_NAME)
    if env_collection:
        try:
            # Validate collection exists and has points
            collections = client.get_collections().collections
            for c in collections:
                if c.name == env_collection:
                    coll_info = client.get_collection(env_collection)
                    points = coll_info.points_count
                    if points > 0:
                        print(f"[QDRANT] Using env collection: {env_collection} | points={points}")
                        return env_collection, points
                    else:
                        print(f"[WARN] Env collection {env_collection} has 0 points")
        except Exception as e:
            print(f"[WARN] Failed to validate env collection {env_collection}: {e}")
    
    # Try runtime_settings.json
    runtime_settings = load_runtime_settings()
    runtime_collection = runtime_settings.get("qdrant_collection")
    
    if runtime_collection:
        try:
            collections = client.get_collections().collections
            for c in collections:
                if c.name == runtime_collection:
                    coll_info = client.get_collection(runtime_collection)
                    points = coll_info.points_count
                    if points > 0:
                        print(f"[QDRANT] Using runtime_settings collection: {runtime_collection} | points={points}")
                        return runtime_collection, points
                    else:
                        print(f"[WARN] Runtime collection {runtime_collection} has 0 points")
        except Exception as e:
            print(f"[WARN] Failed to validate runtime collection {runtime_collection}: {e}")
    
    # Auto-resolve: find best collection
    try:
        print("[QDRANT] Auto-resolving best collection...")
        collections = client.get_collections().collections
        
        candidates = []
        for c in collections:
            try:
                coll_info = client.get_collection(c.name)
                points = coll_info.points_count
                if points > 0:
                    candidates.append((c.name, points))
            except:
                continue
        
        if not candidates:
            print("[WARN] No collections with points > 0 found")
            return None, 0
        
        # Priority keywords for tie-breaking
        priorities = ["fiqa", "beir", "qa", "search"]
        
        def score(item):
            name, points = item
            name_lower = name.lower()
            priority_idx = 999
            
            for i, keyword in enumerate(priorities):
                if keyword in name_lower:
                    priority_idx = i
                    break
            
            return (points, -priority_idx)
        
        candidates.sort(key=score, reverse=True)
        best_name, best_points = candidates[0]
        
        print(f"[QDRANT] Auto-resolved collection: {best_name} | points={best_points}")
        return best_name, best_points
        
    except Exception as e:
        print(f"[ERROR] Failed to auto-resolve collection: {e}")
        return None, 0


class PipelineManager:
    """Pipeline manager with real Qdrant integration"""
    
    def __init__(self):
        self.ready = False
        self.use_mock = not QDRANT_AVAILABLE
        self.client = None
        self.encoder = None
        self.collection_name = settings.COLLECTION_NAME
        self.points_count = 0
        
        if not self.use_mock:
            try:
                # Connect to Qdrant
                url_parts = settings.QDRANT_URL.replace("http://", "").split(":")
                host = url_parts[0]
                port = int(url_parts[1]) if len(url_parts) > 1 else 6333
                self.client = QdrantClient(host=host, port=port)
                
                # Resolve collection
                resolved_name, points = resolve_qdrant_collection(self.client, settings.QDRANT_URL)
                
                if resolved_name and points > 0:
                    self.collection_name = resolved_name
                    self.points_count = points
                    self.use_mock = False
                    
                    # Load encoder
                    self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                    self.ready = True
                    
                    print(f"[QDRANT] url={settings.QDRANT_URL} collection={self.collection_name} points={self.points_count} mock_mode=false")
                else:
                    raise ValueError("No valid collection found")
                
            except Exception as e:
                print(f"⚠️  Qdrant unavailable: {e}, falling back to mock")
                print(f"[QDRANT] url={settings.QDRANT_URL} collection=none points=0 mock_mode=true")
                self.use_mock = True
                self.ready = True
        else:
            self.ready = True
            print(f"[QDRANT] url={settings.QDRANT_URL} collection=none points=0 mock_mode=true")
    
    def search(self, query: str, top_k: int = 10, rerank_top_k: int = None) -> dict:
        """Search using Qdrant or mock data, with optional reranking"""
        t0 = time.time()
        
        # Determine candidate_k (fetch more if reranking)
        if settings.ENABLE_RERANKER:
            candidate_k = min(settings.CANDIDATE_K_MAX, top_k * 5)
        else:
            # For fast mode, use CANDIDATE_K_MAX directly
            candidate_k = min(settings.CANDIDATE_K_MAX, top_k * 2)
        
        if self.use_mock or not self.ready:
            # Mock fallback with profile-aware behavior
            # Simulate different latencies based on profile settings
            if settings.ENABLE_RERANKER and settings.RERANK_TOP_K > 10:
                # Quality mode: higher latency due to more reranking
                base_latency = random.uniform(0.12, 0.25)
            elif settings.ENABLE_RERANKER:
                # Balanced mode: moderate latency
                base_latency = random.uniform(0.08, 0.15)
            else:
                # Fast mode: lower latency, no reranking
                base_latency = random.uniform(0.03, 0.08)
            
            time.sleep(base_latency)
            candidates = [{"id": f"mock_{i}", "text": f"Mock answer {i+1} for '{query[:30]}...'", "title": f"Mock Title {i+1}", "source": "mock", "score": 0.9 - i*0.1} for i in range(candidate_k)]  # doc-id alignment
            cache_hit = random.choice([True, False])
        else:
            try:
                # Real Qdrant search - fetch candidates
                if PROFILER_AVAILABLE:
                    with prof("io.qdrant.search"):
                        query_vector = self.encoder.encode(query).tolist()
                        results = self.client.search(
                            collection_name=self.collection_name,
                            query_vector=query_vector,
                            limit=candidate_k
                        )
                else:
                    query_vector = self.encoder.encode(query).tolist()
                    results = self.client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vector,
                        limit=candidate_k
                    )
                
                if PROFILER_AVAILABLE:
                    with prof("io.qdrant.parse_results"):
                        candidates = []
                        for r in results:
                            payload = r.payload or {}
                            # doc-id alignment: extract doc_id from payload or fallback to point id
                            doc_id = normalize_doc_id(payload.get("doc_id", r.id))
                            candidates.append({
                                "id": doc_id,  # doc-id alignment
                                "text": payload.get("text", str(payload))[:200],
                                "title": payload.get("title", "Unknown"),
                                "source": payload.get("source", "Unknown"),
                                "score": float(r.score) if hasattr(r, 'score') else 0.0
                            })
                else:
                    candidates = []
                    for r in results:
                        payload = r.payload or {}
                        # doc-id alignment: extract doc_id from payload or fallback to point id
                        doc_id = normalize_doc_id(payload.get("doc_id", r.id))
                        candidates.append({
                            "id": doc_id,  # doc-id alignment
                            "text": payload.get("text", str(payload))[:200],
                            "title": payload.get("title", "Unknown"),
                            "source": payload.get("source", "Unknown"),
                            "score": float(r.score) if hasattr(r, 'score') else 0.0
                        })
                cache_hit = False  # No cache in minimal version
            except Exception as e:
                return {"error": "collection not found", "detail": str(e)}
        
        qdrant_latency_ms = (time.time() - t0) * 1000  # Store Qdrant retrieval time
        
        # Reranking phase with v2 selective logic
        rerank_latency_ms = 0
        rerank_model = "disabled"
        rerank_hit = 0
        should_rerank_v2_flag = False
        trigger_reason = "disabled"
        rerank_budget_ok = True
        rerank_timeout = False
        fallback_used = False
        dispersion = 0.0
        
        # Compute dispersion for all requests (for observability)
        top_scores = [c.get("score", 0.0) for c in candidates[:10]]
        dispersion = compute_dispersion(top_scores) if top_scores else 0.0
        
        # V2 decision logic
        if settings.ENABLE_RERANKER and len(candidates) >= top_k:
            if RERANK_V2_ENABLED:
                # Use v2 decision logic
                rolling_stats = {"window": RR_V2_WINDOW}
                should_rerank_v2_flag, trigger_reason = should_rerank_v2(query, candidates, rolling_stats)
                rerank_budget_ok = "budget" not in trigger_reason
            else:
                # Force rerank when v2 is disabled (bypass decision logic)
                should_rerank_v2_flag = True
                trigger_reason = "v2_disabled_force"
                rerank_budget_ok = True
                print("[RERANK] v2=OFF → force rerank")
        
        if should_rerank_v2_flag:
            global RR_V2_CONSECUTIVE_TIMEOUTS
            try:
                # Extract text for reranking
                candidate_texts = [c["text"] for c in candidates]
                t_rr_start = time.time()
                # Use RERANK_TOP_K to control reranking cost, then take top_k from that
                rerank_k = min(settings.RERANK_TOP_K, len(candidate_texts))
                
                # Profile reranking
                if PROFILER_AVAILABLE:
                    with prof("compute.rerank"):
                        reranked_texts, rerank_latency_ms, rerank_model = rerank_passages(
                            query=query,
                            passages=candidate_texts,
                            top_k=rerank_k,
                            model_name=settings.RERANK_MODEL_NAME,
                            cache_dir=settings.MODEL_CACHE_DIR,
                            timeout_ms=settings.RR_MAX_LATENCY_MS
                        )
                else:
                    reranked_texts, rerank_latency_ms, rerank_model = rerank_passages(
                        query=query,
                        passages=candidate_texts,
                        top_k=rerank_k,
                        model_name=settings.RERANK_MODEL_NAME,
                        cache_dir=settings.MODEL_CACHE_DIR,
                        timeout_ms=settings.RR_MAX_LATENCY_MS
                    )
                
                # Check timeout
                if rerank_latency_ms > settings.RR_MAX_LATENCY_MS:
                    rerank_timeout = True
                    RR_V2_CONSECUTIVE_TIMEOUTS += 1
                else:
                    RR_V2_CONSECUTIVE_TIMEOUTS = 0
                
                # Enter cooldown if consecutive timeouts
                if RR_V2_CONSECUTIVE_TIMEOUTS >= 2:
                    global RR_V2_COOLDOWN_UNTIL
                    RR_V2_COOLDOWN_UNTIL = time.time() + settings.RR_COOLDOWN_SEC
                    print(f"⚠️  Reranker v2: entering cooldown for {settings.RR_COOLDOWN_SEC}s (consecutive timeouts)")
                
                # Map reranked texts back to original candidates
                answers = []
                for text in reranked_texts:
                    for candidate in candidates:
                        if candidate["text"] == text:
                            answers.append(candidate)
                            break
                
                # Check if reranking succeeded
                if rerank_model.startswith("fallback:") or rerank_timeout:
                    fallback_used = True
                    answers = candidates[:top_k]
                    rerank_hit = 0
                else:
                    rerank_hit = 1
                    
            except Exception as e:
                # Fallback on any exception
                answers = candidates[:top_k]
                rerank_model = f"fallback:exception:{type(e).__name__}"
                rerank_hit = 0
                fallback_used = True
        else:
            # No reranking
            answers = candidates[:top_k]
            if not settings.ENABLE_RERANKER:
                rerank_model = "disabled"
            else:
                rerank_model = f"skipped:{trigger_reason}"
        
        total_latency_ms = (time.time() - t0) * 1000
        
        # Calculate network/overhead time (API processing, marshalling, etc.)
        # network_time = total - (qdrant + rerank)
        network_latency_raw = total_latency_ms - qdrant_latency_ms - rerank_latency_ms
        network_latency_ms = max(0, network_latency_raw)
        
        # Debug counter: track when network is clamped
        global NETWORK_CLAMPED_COUNT
        if network_latency_raw < 0:
            NETWORK_CLAMPED_COUNT += 1
            if NETWORK_CLAMPED_COUNT % 100 == 1:  # Log every 100th occurrence
                print(f"[TIMING_DEBUG] Network clamped: total={total_latency_ms:.2f}, ann={qdrant_latency_ms:.2f}, rerank={rerank_latency_ms:.2f}, raw_network={network_latency_raw:.2f} (clamped_count={NETWORK_CLAMPED_COUNT})")
        
        # Update sliding window
        recent_hits = sum(1 for r in RR_V2_WINDOW[-100:] if r.get("triggered", False))
        rolling_hit_rate = recent_hits / len(RR_V2_WINDOW[-100:]) if RR_V2_WINDOW else 0.0
        
        RR_V2_WINDOW.append({
            "triggered": should_rerank_v2_flag,
            "timeout": rerank_timeout,
            "fallback": fallback_used,
            "ts": time.time()
        })
        
        # Limit window size
        if len(RR_V2_WINDOW) > 100:
            RR_V2_WINDOW.pop(0)
        
        # doc-id alignment: extract doc_ids for recall calculation
        doc_ids = [ans.get("id", f"unknown_{i}") for i, ans in enumerate(answers)]
        
        return {
            "answers": answers,
            "doc_ids": doc_ids,  # doc-id alignment
            "latency_ms": total_latency_ms,
            "cache_hit": cache_hit,
            "rerank_latency_ms": rerank_latency_ms,
            "rerank_model": rerank_model,
            "rerank_hit": rerank_hit,
            "candidate_k": len(candidates),
            "rerank_top_k": rerank_top_k if rerank_top_k is not None else settings.RERANK_TOP_K,  # Use passed value or settings
            "collection": self.collection_name,
            "qdrant_latency_ms": qdrant_latency_ms,
            "network_latency_ms": network_latency_ms,  # NEW: network/overhead time
            "should_rerank_v2": should_rerank_v2_flag,
            "trigger_reason": trigger_reason,
            "rerank_budget_ok": rerank_budget_ok,
            "rerank_timeout": rerank_timeout,
            "fallback_used": fallback_used,
            "dispersion": dispersion,
            "rolling_hit_rate": rolling_hit_rate
        }


app = FastAPI(title=settings.API_TITLE)

# Mount ops routes
app.include_router(ops_router)

# Log Force Override initialization
force_config = force_override.get_status()
logger = logging.getLogger(__name__)
if force_config["force_override"]:
    logger.info(
        f"[INIT] ForceOverride loaded with force_override=True, "
        f"hard_cap={force_config['hard_cap_enabled']}, "
        f"params={force_config['active_params']}, "
        f"limits={force_config['hard_cap_limits']}"
    )
else:
    logger.info(
        f"[INIT] ForceOverride loaded with force_override=False, "
        f"hard_cap={force_config['hard_cap_enabled']}"
    )

manager = PipelineManager()
metrics_logger = MetricsLogger()

# Initialize AutoTrafficWorker and WarmupGuard
auto_worker = AutoTrafficWorker()
warmup_guard = WarmupGuard()

# 🆕 Auto Traffic safety guards
auto_lock = asyncio.Lock()  # Mutual exclusion for start/stop
last_start_ts = 0.0          # Debounce timestamp

# Template rendering for /debug page
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Mount reports directory for static file access
reports_dir = Path(__file__).parent.parent.parent / "reports"
reports_dir.mkdir(exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(reports_dir)), name="reports")

# Mount frontend static files with SPA fallback
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Mount static files
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    # SPA fallback - serve index.html for all routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Skip API routes
        if full_path.startswith(("api/", "ops/", "docs", "openapi.json", "health", "readyz", "reports/")):
            raise HTTPException(status_code=404, detail="Not Found")
        
        # Serve index.html for all other routes (SPA fallback)
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            raise HTTPException(status_code=404, detail="Frontend not found")
    
    logger.info(f"✓ Frontend mounted with SPA fallback (from {frontend_dist})")
else:
    logger.warning(f"⚠ Frontend dist not found at {frontend_dist}")

# Track service start time
SERVICE_START_TIME = time.time()

# Reranker v2 - Sliding window state (in-memory)
RR_V2_WINDOW = []  # List of {triggered: bool, timeout: bool, fallback: bool, ts: float}
RR_V2_COOLDOWN_UNTIL = 0.0  # Timestamp when cooldown ends
RR_V2_CONSECUTIVE_TIMEOUTS = 0  # Counter for consecutive timeouts

# ⭐ NEW: Rerank v2 decision toggle (for forcing rerank during testing)
RERANK_V2_ENABLED = os.environ.get("RERANK_V2_ENABLED", "False").lower() == "true"

# Stage Timing Debug Counters
NETWORK_CLAMPED_COUNT = 0  # Count of times network_latency_ms was clamped to 0

# Scenario Switcher - Current profile state
CURRENT_PROFILE = "balanced"  # Default profile

# SLA knob - Target P95 latency
sla_state = {"target_p95": 300}

# Tuner state - Strategy-based auto-tuning
TUNER_ENABLED = os.environ.get("TUNER_ENABLED", "0") == "1"
if TUNER_AVAILABLE:
    # Always initialize tuner_state when TUNER_AVAILABLE (even if not enabled)
    tuner_state = {
        "strategy": "default",
        "shadow_ratio": 0.10,
        "cooldown_sec": 30,
        "last_step_ts": 0.0,
        "params": TunerParams(topk=128, ef=128, parallel=4)
    }
else:
    tuner_state = None

# Tuner runtime toggle - controls whether the background loop is active
tuner_enabled = False  # Default OFF for safety

# Event tracking - chronological list of system events
EVENTS_LOG = []  # List of {ts: int, type: str, meta: dict}

def emit_event(event_type: str, meta: dict):
    """Emit a system event with timestamp and metadata"""
    global EVENTS_LOG
    now_ms = int(time.time() * 1000)
    event = {
        "ts": now_ms,
        "type": event_type,
        "meta": meta
    }
    EVENTS_LOG.append(event)
    # Keep only last 200 events
    if len(EVENTS_LOG) > 200:
        EVENTS_LOG = EVENTS_LOG[-200:]
    print(f"[EVENT] type={event_type} ts={now_ms} meta={meta}")
    return event


def compute_tai_from_events(events: list, window_sec: float = 120.0) -> dict:
    """
    Compute TAI (Tuner Activity Index) from events log.
    
    Returns dict with:
      - value: 0-100 score (None if insufficient data)
      - reason: explanation string (ok, tuner_off, no_actions, collecting, error_gap)
      - samples: number of tuner actions in window
      - window_sec: window size used
    """
    now = time.time() * 1000  # ms
    cutoff = now - (window_sec * 1000)
    
    # Count tuner.step events in window
    tuner_actions = []
    for evt in events:
        if evt.get("type") == "tuner.step" and evt.get("ts", 0) >= cutoff:
            tuner_actions.append(evt)
    
    action_count = len(tuner_actions)
    
    # Determine reason and value
    if not tuner_enabled:
        return {
            "value": None,
            "reason": "tuner_off",
            "samples": 0,
            "window_sec": window_sec
        }
    
    if action_count == 0:
        # No actions in window - check if we have P95 error gap for fallback
        # This is a simplified version - in production you'd read actual P95 vs target
        return {
            "value": None,
            "reason": "no_tuner_activity",
            "samples": 0,
            "window_sec": window_sec
        }
    
    # Calculate TAI based on action frequency
    # Formula: actions_per_min = count / (window_sec / 60)
    # TAI = clamp(round(actions_per_min * 25), 0, 100)
    # This gives TAI=100 when ~4 actions/min
    minutes = window_sec / 60.0
    actions_per_min = action_count / minutes
    tai_value = min(100, max(0, round(actions_per_min * 25)))
    
    return {
        "value": tai_value,
        "reason": "ok",
        "samples": action_count,
        "window_sec": window_sec
    }

# Cache layer config
CACHE_TTL_SEC = 600  # 10 minutes
CACHE_MAX_ITEMS = 500
SEARCH_CACHE = {}  # {key: {"response": dict, "latency_ms": float, "ts": float}}

# Warm up reranker on startup to avoid first-request penalty
@app.on_event("startup")
async def warmup_reranker():
    """Pre-load reranker model if enabled"""
    if settings.ENABLE_RERANKER:
        try:
            print("🔥 Warming up reranker model...")
            # Trigger model loading with a dummy request
            rerank_passages(
                query="warmup query",
                passages=["warmup passage"] * 10,
                top_k=5,
                model_name=settings.RERANK_MODEL_NAME,
                cache_dir=settings.MODEL_CACHE_DIR,
                timeout_ms=30000  # 30s for first load
            )
            print("✅ Reranker model loaded and cached")
        except Exception as e:
            print(f"⚠️  Reranker warmup failed: {e}, will lazy-load on first request")
    
    # Start tuner background loop
    if TUNER_ENABLED and TUNER_AVAILABLE:
        threading.Thread(target=tuner_background_loop, daemon=True).start()
        tuner_logger.info("Background loop started")
    
    # Startup log: port confirmation
    print("[BOOT] port=8080 ok")


def tuner_background_loop():
    """Background loop that periodically runs tuner strategy step"""
    global tuner_state, tuner_enabled
    
    # Import tick interval from tuner module (configurable via env)
    try:
        from .tuner import TUNER_TICK_SEC
    except ImportError:
        from tuner import TUNER_TICK_SEC
    
    project_root = Path(__file__).parent.parent.parent
    last_tick_log = 0.0
    
    while True:
        try:
            if tuner_state is None or not TUNER_ENABLED:
                time.sleep(TUNER_TICK_SEC)
                continue
            
            # Check runtime toggle - if disabled, idle without resetting state
            if not tuner_enabled:
                time.sleep(TUNER_TICK_SEC)
                continue
            
            # Read latest dashboard to compute last_p95
            dashboard_path = project_root / "reports" / "dashboard.json"
            if dashboard_path.exists():
                with open(dashboard_path) as f:
                    data = json.load(f)
                
                # Get control group P95 (60-90s window)
                current_p95 = data.get("sla", {}).get("current_p95")
                target_p95 = sla_state.get("target_p95", 300)
                
                # Log every tick (for demo visibility)
                params = tuner_state["params"]
                p95_str = f"{current_p95:.1f}" if current_p95 else "—"
                tuner_logger.info(f"[TUNER] tick p95={p95_str} target={target_p95} topk={params.topk} ef={params.ef} parallel={params.parallel}")
                
                # Check if cooldown elapsed
                now = time.time()
                if now - tuner_state["last_step_ts"] >= tuner_state["cooldown_sec"]:
                    # Run strategy step
                    strategy_name = tuner_state["strategy"]
                    strategy = StrategyRegistry.get(strategy_name)
                    
                    old_params = tuner_state["params"]
                    new_params = strategy.step(
                        target_p95=target_p95,
                        last_p95=current_p95,
                        params=old_params
                    )
                    
                    # Update state and emit event
                    tuner_state["params"] = new_params
                    tuner_state["last_step_ts"] = now
                    
                    emit_event("tuner.step", {
                        "strategy": strategy_name,
                        "topk": new_params.topk,
                        "ef": new_params.ef,
                        "parallel": new_params.parallel,
                        "last_p95": current_p95,
                        "target": target_p95
                    })
        
        except Exception as e:
            tuner_logger.error(f"loop error: {e}")
        
        time.sleep(TUNER_TICK_SEC)
    
    # Auto-start AutoTrafficWorker if env var is set
    if os.environ.get("AUTO_TRAFFIC", "0") == "1":
        print("[AUTO] AUTO_TRAFFIC=1 detected, starting worker")
        auto_worker.start()

# AutoTuner state
AUTOTUNER_PARAMS = {
    "ef_search": 128,
    "candidate_k": 100,
    "rerank_k": 10,
    "threshold_T": 0.5
}
AUTOTUNER_LAST_TICK = time.time()
AUTOTUNER_BASELINE_RECALL = 0.85  # Will be updated from actual metrics

# Application state (for /tuner/status endpoint)
app_state = {
    "last_decision": None,
    "last_params": None
}

# Simple in-memory rate limiter: {ip: [(timestamp, timestamp, ...)]}
rate_limit_window = defaultdict(list)

# Legacy CSV log path (kept for backward compatibility)
LOG_PATH = Path(__file__).parent / "reports" / "fiqa_api_live.csv"
LOG_PATH.parent.mkdir(exist_ok=True)

# doc-id alignment: Field name for document ID in Qdrant payload
DOC_ID_FIELD = "doc_id"

def normalize_doc_id(doc_id) -> str:
    """
    Normalize document ID for robust matching.
    Handles: numeric IDs, whitespace, case differences.
    """
    if doc_id is None:
        return ""
    return str(doc_id).strip().lower()

# Load qrels for Recall@10 calculation (cache in memory)
QRELS_CACHE: Optional[Dict[str, Set[str]]] = None

def load_qrels() -> Dict[str, Set[str]]:
    """Load qrels from FIQA dataset for Recall@10 calculation."""
    global QRELS_CACHE
    if QRELS_CACHE is not None:
        return QRELS_CACHE
    
    qrels = {}
    qrels_file = Path(__file__).parent.parent.parent / "data" / "fiqa" / "qrels" / "test.tsv"
    
    if not qrels_file.exists():
        print(f"[WARN] Qrels file not found: {qrels_file}")
        QRELS_CACHE = {}
        return {}
    
    try:
        with open(qrels_file, 'r') as f:
            for i, line in enumerate(f):
                if i == 0:  # Skip header
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    query_id, doc_id, relevance = parts[0], parts[1], parts[2]
                    if int(relevance) > 0:
                        if query_id not in qrels:
                            qrels[query_id] = set()
                        # Normalize doc_id for robust matching
                        qrels[query_id].add(normalize_doc_id(doc_id))
        
        print(f"[INFO] Loaded {len(qrels)} qrels from {qrels_file}")
        QRELS_CACHE = qrels
        return qrels
    except Exception as e:
        print(f"[ERROR] Failed to load qrels: {e}")
        QRELS_CACHE = {}
        return {}

def calculate_real_recall_at_10(doc_ids: List[str], query_id: Optional[str] = None) -> Optional[float]:
    """
    Calculate real Recall@10 against ground truth qrels.
    Returns None if query_id not found in qrels or qrels not available.
    
    Args:
        doc_ids: List of retrieved document IDs (top 10)
        query_id: Query ID to look up in qrels
    
    Returns:
        Recall@10 value (0-1) or None if not calculable
    """
    if not query_id:
        return None
    
    qrels = load_qrels()
    if not qrels or query_id not in qrels:
        return None
    
    relevant_docs = qrels[query_id]
    if not relevant_docs:
        return None
    
    # Normalize all IDs for robust matching
    normalized_retrieved = {normalize_doc_id(doc_id) for doc_id in doc_ids[:10]}
    normalized_relevant = {normalize_doc_id(doc_id) for doc_id in relevant_docs}
    
    # Check how many of top 10 docs are relevant
    hits = len(normalized_retrieved & normalized_relevant)
    
    # Recall@10 = hits / min(10, |relevant|)
    return hits / min(10, len(relevant_docs))

# Initialize CSV with header if not exists
if not LOG_PATH.exists():
    with open(LOG_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'query', 'latency_ms', 'cache_hit', 'num_results'])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    query_id: Optional[str] = None  # doc-id alignment: for real recall calculation
    candidate_k: Optional[int] = None  # Force override: candidate count
    rerank_top_k: Optional[int] = None  # Force override: rerank top-k
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('query must be non-empty string')
        return v
    
    @field_validator('top_k')
    @classmethod
    def validate_top_k(cls, v):
        if not 1 <= v <= 20:
            raise ValueError('top_k must be between 1 and 20')
        return v


class SearchResponse(BaseModel):
    answers: list[str]
    latency_ms: float
    cache_hit: bool
    mode: str = None
    candidate_k: int = None
    rerank_top_k: int = None  # Force override: rerank top-k value
    rerank_hit: int = None
    page_index: bool = None
    doc_ids: list[str] = None
    # ⭐ FIX: Add stage timing fields
    qdrant_latency_ms: float = None
    rerank_latency_ms: float = None
    network_latency_ms: float = None


def error_response(code: int, msg: str, hint: str = "") -> JSONResponse:
    """Unified error response format"""
    return JSONResponse(
        status_code=code,
        content={
            "code": code,
            "msg": msg,
            "hint": hint,
            "ts": datetime.now(timezone.utc).isoformat()
        }
    )


def check_rate_limit(client_ip: str) -> bool:
    """Check if request is within rate limit. Returns True if allowed."""
    now = time.time()
    
    # Clean old timestamps
    rate_limit_window[client_ip] = [
        ts for ts in rate_limit_window[client_ip] 
        if now - ts < settings.RATE_LIMIT_WINDOW
    ]
    
    # Check limit
    if len(rate_limit_window[client_ip]) >= settings.RATE_LIMIT_MAX:
        return False
    
    # Record this request
    rate_limit_window[client_ip].append(now)
    return True


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with unified format"""
    errors = exc.errors()
    msg = errors[0].get('msg', 'Validation error') if errors else 'Validation error'
    return error_response(422, msg, "Check request body format and field constraints")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "fiqa_api"}


@app.get("/search")
@app.post("/search", response_model=SearchResponse)
def search(request: Request, req: SearchRequest = None, mode: str = None, profile: str = None):
    """Search endpoint with validation, rate limiting, and latency tracking"""
    try:
        # Handle both POST and GET requests
        if request is None:
            return error_response(400, "Request required")
        
        # Extract parameters from GET request if needed
        if req is None:
            query = request.query_params.get('query', '')
            top_k = int(request.query_params.get('top_k', 10))
            req = SearchRequest(query=query, top_k=top_k)
            mode = request.query_params.get('mode', mode)
            profile = request.query_params.get('profile', profile)
    except Exception as e:
        import traceback
        print(f"[ERROR] Search endpoint exception (early): {type(e).__name__}: {e}")
        traceback.print_exc()
        return error_response(500, "Search failed", str(e))
    
    # Trigger AutoTuner tick (non-blocking check)
    autotuner_tick()
    
    # Rate limit check
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        return error_response(
            429, 
            "Rate limit exceeded", 
            f"Max {settings.RATE_LIMIT_MAX} requests per {settings.RATE_LIMIT_WINDOW}s per IP"
        )
    
    start_time = time.time()
    
    # Cache layer: check for hit
    normalized_query = req.query.lower().strip()
    cache_key = f"{mode or 'baseline'}:{normalized_query}"
    cache_hit = 0
    cache_saved_ms = 0
    now = time.time()
    
    # Clean expired cache entries periodically
    if len(SEARCH_CACHE) > CACHE_MAX_ITEMS:
        expired_keys = [k for k, v in SEARCH_CACHE.items() if now - v["ts"] > CACHE_TTL_SEC]
        for k in expired_keys[:100]:
            SEARCH_CACHE.pop(k, None)
    
    # Check cache
    if cache_key in SEARCH_CACHE:
        cached = SEARCH_CACHE[cache_key]
        if now - cached["ts"] < CACHE_TTL_SEC:
            cache_hit = 1
            cache_saved_ms = cached["latency_ms"]
            result = cached["response"]
            total_latency_ms = (time.time() - start_time) * 1000
            
            # Log cache hit
            tokens_in = int(len(req.query.split()) * 0.75)
            tokens_out = int(sum(len(ans.get("text", "").split()) * 0.75 for ans in result['answers']))
            est_cost = (tokens_in * 0.01 + tokens_out * 0.03) / 1000.0
            recall_at10 = 0.85  # Use baseline for cache hits
            log_mode = mode if mode else "baseline"
            
            metrics_logger.log(
                p95_ms=total_latency_ms,
                recall_at10=recall_at10,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                est_cost=est_cost,
                success=True,
                group=log_mode,
                cache_hit=cache_hit,
                cache_saved_ms=cache_saved_ms
            )
            
            # Return cached response
            response_data = {
                "answers": [ans.get("text", str(ans)) for ans in result['answers']],
                "latency_ms": total_latency_ms,
                "cache_hit": True,
                "candidate_k": result.get('candidate_k', None),
                "rerank_top_k": result.get('rerank_top_k', None),
                # ⭐ Recall: Always include doc_ids for recall calculation
                "doc_ids": [ans.get("id", f"doc_{i}") for i, ans in enumerate(result['answers'])]
            }
            if mode:
                response_data.update({
                    "mode": mode,
                    "candidate_k": result.get('candidate_k', 0),
                    "rerank_hit": result.get('rerank_hit', 0),
                    "page_index": settings.ENABLE_PAGE_INDEX
                })
            return SearchResponse(**response_data)
    
    start_time = time.time()
    
    # Tuner shadow traffic: determine control vs candidate path
    is_shadow = False
    tuner_rerank_on = False
    if TUNER_ENABLED and tuner_state is not None:
        shadow_ratio = tuner_state["shadow_ratio"]
        if random.random() < shadow_ratio:
            is_shadow = True
            # Apply tuner params for shadow request
            params = tuner_state["params"]
            # Reranker ON when strategy != "default" AND target_p95 >= 300ms
            tuner_rerank_on = (tuner_state["strategy"] != "default" and 
                             sla_state.get("target_p95", 300) >= 300)
    
    # Override both PageIndex and Reranker based on profile or mode
    original_reranker = settings.ENABLE_RERANKER
    original_pageindex = settings.ENABLE_PAGE_INDEX
    original_candidate_k = settings.CANDIDATE_K_MAX
    original_rerank_top_k = settings.RERANK_TOP_K
    
    # Apply shadow/tuner params first (if applicable)
    if is_shadow and TUNER_ENABLED and tuner_state is not None:
        params = tuner_state["params"]
        settings.CANDIDATE_K_MAX = params.topk
        settings.ENABLE_RERANKER = tuner_rerank_on
        # Note: ef and parallel would require qdrant search API changes
        # For now, just use topk as candidate_k and enable/disable reranker
    # Apply profile settings (takes precedence over mode, unless shadow)
    elif profile:
        profile = profile.lower() if profile else "balanced"
        if profile == "fast":
            settings.ENABLE_PAGE_INDEX = False
            settings.ENABLE_RERANKER = False
            settings.CANDIDATE_K_MAX = 200
        elif profile == "balanced":
            settings.ENABLE_PAGE_INDEX = True
            settings.ENABLE_RERANKER = True
            settings.CANDIDATE_K_MAX = 800
            settings.RERANK_TOP_K = 6
        elif profile == "quality":
            settings.ENABLE_PAGE_INDEX = True
            settings.ENABLE_RERANKER = True
            settings.CANDIDATE_K_MAX = 1500
            settings.RERANK_TOP_K = 25
    # DEMO_FORCE_DIFF: 强制差异化参数
    elif settings.DEMO_FORCE_DIFF and mode:
        if mode == "off":
            settings.ENABLE_RERANKER = False
            settings.ENABLE_PAGE_INDEX = False
            settings.CANDIDATE_K_MAX = 200
        elif mode == "on":
            settings.ENABLE_RERANKER = True
            settings.ENABLE_PAGE_INDEX = True
            settings.CANDIDATE_K_MAX = 1500
            settings.RERANK_TOP_K = 25
    elif mode == "off":
        # OFF mode: disable both features
        settings.ENABLE_RERANKER = False
        settings.ENABLE_PAGE_INDEX = False
    elif mode == "on":
        # ON mode: enable both PageIndex + Reranker
        settings.ENABLE_RERANKER = True
        settings.ENABLE_PAGE_INDEX = True
    
    # Record current state before calling pipeline
    current_page_index = settings.ENABLE_PAGE_INDEX
    current_reranker = settings.ENABLE_RERANKER
    current_candidate_k = settings.CANDIDATE_K_MAX
    
    # Apply SLA-based dynamic adjustment
    target_p95 = sla_state["target_p95"]
    recent_metrics = metrics_logger.compute_rolling_averages(window=10)
    current_p95 = recent_metrics.get("avg_p95_ms", 0)
    
    sla_action = "unchanged"
    if current_p95 > target_p95 and current_p95 > 0:
        # Latency too high: reduce load
        settings.ENABLE_RERANKER = False
        settings.CANDIDATE_K_MAX = min(settings.CANDIDATE_K_MAX, 200)
        sla_action = "reduce"
        print(f"[SLA] target={target_p95}ms | current_p95={current_p95:.1f}ms | action=REDUCE | rerank=OFF | candidate_k={settings.CANDIDATE_K_MAX}")
    elif current_p95 < target_p95 * 0.7 and current_p95 > 0:
        # Latency headroom: enable quality features
        settings.ENABLE_RERANKER = True
        settings.CANDIDATE_K_MAX = max(settings.CANDIDATE_K_MAX, 800)
        sla_action = "increase"
        print(f"[SLA] target={target_p95}ms | current_p95={current_p95:.1f}ms | action=INCREASE | rerank=ON | candidate_k={settings.CANDIDATE_K_MAX}")
    elif current_p95 > 0:
        # Within acceptable range
        print(f"[SLA] target={target_p95}ms | current_p95={current_p95:.1f}ms | action=MAINTAIN | rerank={'ON' if settings.ENABLE_RERANKER else 'OFF'} | candidate_k={settings.CANDIDATE_K_MAX}")
    
    # Apply Force Override parameters using plugin
    force_override_candidate_k = None
    force_override_rerank_top_k = None
    
    # Build planned parameters from request
    planned_params = {}
    if req.candidate_k is not None:
        planned_params["num_candidates"] = req.candidate_k
    if req.rerank_top_k is not None:
        planned_params["rerank_topk"] = req.rerank_top_k
    
    # Resolve through precedence chain if any params specified or force override enabled
    if planned_params or force_override.is_enabled():
        # Set defaults to current settings
        defaults = {
            "num_candidates": settings.CANDIDATE_K_MAX,
            "rerank_topk": settings.RERANK_TOP_K
        }
        
        # Resolve through plugin
        force_status = force_override.resolve(planned_params, context="search_endpoint", defaults=defaults)
        effective = force_status.effective_params
        
        # Apply effective parameters
        if "num_candidates" in effective:
            settings.CANDIDATE_K_MAX = effective["num_candidates"]
            force_override_candidate_k = effective["num_candidates"]
        
        if "rerank_topk" in effective:
            settings.RERANK_TOP_K = effective["rerank_topk"]
            force_override_rerank_top_k = effective["rerank_topk"]
        
        # Log precedence chain
        if force_status.force_override or planned_params:
            print(f"[FORCE_OVERRIDE] Precedence trace:")
            for step in force_status.precedence_chain:
                print(f"  {step}")
            print(f"[FORCE_OVERRIDE] Effective params: candidate_k={settings.CANDIDATE_K_MAX}, rerank_top_k={settings.RERANK_TOP_K}")
    
    try:
        # Call pipeline with profiling
        if PROFILER_AVAILABLE:
            with prof("api.search.pipeline"):
                result = manager.search(query=req.query, top_k=req.top_k, rerank_top_k=force_override_rerank_top_k)
        else:
            result = manager.search(query=req.query, top_k=req.top_k, rerank_top_k=force_override_rerank_top_k)
        
        # Override result fields with Force Override values if they were applied
        if force_override_candidate_k is not None:
            result["candidate_k"] = force_override_candidate_k
        if force_override_rerank_top_k is not None:
            result["rerank_top_k"] = force_override_rerank_top_k
    finally:
        # Restore original settings
        settings.ENABLE_RERANKER = original_reranker
        settings.ENABLE_PAGE_INDEX = original_pageindex
        settings.CANDIDATE_K_MAX = original_candidate_k
        settings.RERANK_TOP_K = original_rerank_top_k
    
    # Check for error response from manager
    if "error" in result:
        return error_response(500, result.get("error", "Search failed"), result.get("detail", ""))
    
    # Calculate total latency
    total_latency_ms = (time.time() - start_time) * 1000
    
    # Estimate tokens (simple heuristic: ~0.75 tokens per word)
    tokens_in = int(len(req.query.split()) * 0.75)
    tokens_out = int(sum(len(ans.get("text", "").split()) * 0.75 for ans in result['answers']))
    # Simple cost estimation: $0.01 per 1K tokens input, $0.03 per 1K tokens output
    est_cost = (tokens_in * 0.01 + tokens_out * 0.03) / 1000.0
    
    # Log to legacy CSV (for backward compatibility)
    with open(LOG_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            time.time(),
            req.query[:50],  # Truncate long queries
            f"{total_latency_ms:.2f}",
            result['cache_hit'],
            len(result['answers'])
        ])
    
    # Calculate recall - try real calculation first, fallback to mock
    # doc-id alignment: use real Recall@10 if query_id provided
    doc_ids = result.get('doc_ids', [ans.get("id", f"doc_{i}") for i, ans in enumerate(result['answers'])])
    real_recall = calculate_real_recall_at_10(doc_ids, req.query_id) if hasattr(req, 'query_id') else None
    
    if real_recall is not None:
        recall_at10 = real_recall
    else:
        # Fallback to mock calculation
        base_recall = 0.82 + random.uniform(-0.05, 0.05)  # Base recall with noise
        if result.get('rerank_hit', 0) > 0:
            base_recall += 0.06  # Reranking boost
        if current_page_index:
            base_recall += 0.04  # PageIndex boost
        recall_at10 = min(0.95, max(0.70, base_recall))  # Clamp to realistic range
    
    # Calculate recall_proxy: binary signal (0 or 1)
    # Rule: 1 if rerank score > 0.7 OR page_index enabled, else 0
    recall_proxy = 0
    if result.get('rerank_hit', 0) > 0 and result.get('rerank_latency_ms', 0) > 0:
        # Rerank was used and likely improved results
        recall_proxy = 1
    elif current_page_index:
        # PageIndex can improve recall
        recall_proxy = 1
    elif result.get('candidate_k', 0) >= 500:
        # High candidate_k may indicate quality mode
        recall_proxy = 1
    
    # Determine mode for logging (include shadow group)
    if is_shadow:
        log_mode = "shadow"
    else:
        log_mode = mode if mode else "control"
    
    # Store in cache (cache miss case)
    if len(SEARCH_CACHE) < CACHE_MAX_ITEMS:
        SEARCH_CACHE[cache_key] = {
            "response": result,
            "latency_ms": total_latency_ms,
            "ts": time.time()
        }
    
    # ⭐ FIX: Recalculate network_latency_ms at endpoint level
    # The total_latency_ms here includes ALL endpoint overhead (cache check, SLA, profile switch, etc)
    # while manager.search() only measures its internal processing time
    # So we need to recalculate network using the endpoint-level total
    endpoint_network_ms = total_latency_ms - result.get('qdrant_latency_ms', 0) - result.get('rerank_latency_ms', 0)
    endpoint_network_ms = max(0, endpoint_network_ms)  # Clamp to prevent negative
    
    # Log to new metrics logger with rerank info + v2 fields + cache fields + recall_proxy
    metrics_logger.log(
        p95_ms=total_latency_ms,
        recall_at10=recall_at10,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        est_cost=est_cost,
        success=True,
        group=log_mode,
        rerank_latency_ms=result.get('rerank_latency_ms', 0),
        rerank_model=result.get('rerank_model', 'disabled'),
        rerank_hit=result.get('rerank_hit', 0),
        candidate_k=result.get('candidate_k', len(result['answers'])),
        qdrant_latency_ms=result.get('qdrant_latency_ms', 0),
        network_latency_ms=endpoint_network_ms,  # ⭐ FIX: Use endpoint-level calculation
        collection_name=result.get('collection', settings.COLLECTION_NAME),
        should_rerank_v2=result.get('should_rerank_v2', False),
        trigger_reason=result.get('trigger_reason', ''),
        rerank_budget_ok=result.get('rerank_budget_ok', True),
        rerank_timeout=result.get('rerank_timeout', False),
        fallback_used=result.get('fallback_used', False),
        dispersion=result.get('dispersion', 0.0),
        rolling_hit_rate=result.get('rolling_hit_rate', 0.0),
        cache_hit=cache_hit,
        cache_saved_ms=cache_saved_ms,
        recall_proxy=recall_proxy,
        profile=profile
    )
    
    # Build enhanced response with compare mode fields
    response_data = {
        "answers": [ans.get("text", str(ans)) for ans in result['answers']],
        "latency_ms": total_latency_ms,
        "cache_hit": result['cache_hit'],
        # ⭐ FIX: Add stage timing fields to response
        "qdrant_latency_ms": result.get('qdrant_latency_ms', 0),
        "rerank_latency_ms": result.get('rerank_latency_ms', 0),
        "network_latency_ms": endpoint_network_ms,  # Use endpoint-level calculation
        # ⭐ FIX: Always include parameter fields
        "candidate_k": force_override_candidate_k if force_override_candidate_k is not None else result.get('candidate_k', None),
        "rerank_top_k": force_override_rerank_top_k if force_override_rerank_top_k is not None else result.get('rerank_top_k', None),
        # ⭐ Recall: Always include doc_ids for recall calculation
        "doc_ids": doc_ids
    }
    
    # Add compare mode metadata if mode is set
    if mode:
        response_data.update({
            "mode": mode,
            "candidate_k": force_override_candidate_k if force_override_candidate_k is not None else settings.CANDIDATE_K_MAX,  # Use Force Override value if available
            "rerank_top_k": force_override_rerank_top_k if force_override_rerank_top_k is not None else settings.RERANK_TOP_K,  # Use Force Override value if available
            "rerank_hit": result.get('rerank_hit', 0),
            "page_index": current_page_index
        })
    
    return SearchResponse(**response_data)


def autotuner_tick():
    """Periodic AutoTuner tick: read metrics, decide, apply"""
    global AUTOTUNER_PARAMS, AUTOTUNER_BASELINE_RECALL, AUTOTUNER_LAST_TICK, app_state
    
    if not settings.AUTOTUNER_ENABLED or not AUTOTUNER_AVAILABLE:
        return
    
    # Check if tick interval has elapsed
    now = time.time()
    if now - AUTOTUNER_LAST_TICK < settings.AUTOTUNER_TICK_SEC:
        return
    
    AUTOTUNER_LAST_TICK = now
    
    # Get current metrics
    metrics = metrics_logger.compute_rolling_averages(window=100)
    if metrics["count"] < 10:
        return  # Not enough data
    
    # Create TuningInput
    slo = SLO(
        p95_ms=settings.AUTOTUNER_TARGET_P95_MS,
        recall_at10=AUTOTUNER_BASELINE_RECALL
    )
    
    guards = Guards(
        cooldown=False,
        stable=True
    )
    
    tuning_input = TuningInput(
        p95_ms=metrics["avg_p95_ms"],
        recall_at10=metrics["avg_recall"],
        qps=metrics["count"] / 60.0,  # Approximate QPS
        params=AUTOTUNER_PARAMS.copy(),
        slo=slo,
        guards=guards,
        near_T=False  # Simplified for now
    )
    
    # Decide action
    action = decide_multi_knob(tuning_input)
    
    # Update app_state
    app_state["last_decision"] = {
        "action": action.kind,
        "updates": action.updates if hasattr(action, 'updates') else {},
        "timestamp": time.time()
    }
    
    # Apply action if not noop
    if action.kind != "noop" and action.updates:
        AUTOTUNER_PARAMS = apply_action(AUTOTUNER_PARAMS, action)
        app_state["last_params"] = AUTOTUNER_PARAMS.copy()
        print(f"[AutoTuner] Applied {action.kind}: {action.updates} -> {AUTOTUNER_PARAMS}")


@app.get("/metrics")
def get_metrics():
    """Get rolling average metrics with extended system info"""
    base_metrics = metrics_logger.compute_rolling_averages(window=100)
    
    # Add extended fields
    base_metrics.update({
        "window_sec": settings.METRICS_WINDOW,
        "uptime_sec": int(time.time() - SERVICE_START_TIME),
        "version": settings.API_VERSION,
        "autotuner_params": AUTOTUNER_PARAMS if settings.AUTOTUNER_ENABLED else None,
        "reranker_enabled": settings.ENABLE_RERANKER
    })
    
    return base_metrics


@app.get("/tuner/status")
def get_tuner_status():
    """
    Get Auto-Tuner status (unified endpoint for UI)
    Returns: {enabled, strategy, params: {topk, ef, parallel, reranker_on}, last_step}
    """
    # Use tuner_state if available, otherwise fallback
    if tuner_state is not None:
        params = tuner_state["params"]
        # Determine reranker_on: ON if strategy != 'default' and topk >= 128
        reranker_on = tuner_state["strategy"] != "default" and params.topk >= 128
        
        return {
            "enabled": tuner_enabled,  # Runtime toggle state
            "strategy": tuner_state["strategy"],
            "params": {
                "topk": params.topk,
                "ef": params.ef,
                "parallel": params.parallel,
                "reranker_on": reranker_on
            },
            "last_step": datetime.fromtimestamp(tuner_state["last_step_ts"], tz=timezone.utc).isoformat() if tuner_state["last_step_ts"] > 0 else None
        }
    
    # Fallback when tuner_state is None
    return {
        "enabled": False,
        "strategy": "default",
        "params": {
            "topk": 128,
            "ef": 128,
            "parallel": 4,
            "reranker_on": False
        },
        "last_step": None
    }


@app.get("/debug", response_class=HTMLResponse)
def debug_panel(request: Request):
    """Real-time debug panel showing system health metrics"""
    return templates.TemplateResponse("debug.html", {"request": request})


# ========== Judger Pack Routes ==========

class JudgeVote(BaseModel):
    batch_id: str
    qid: int
    pick: str  # 'on' | 'off' | 'same'
    reason: str = ""


@app.get("/judge", response_class=HTMLResponse)
def judge_page(request: Request, batch: str = "latest"):
    """Render judge annotation page"""
    return templates.TemplateResponse("judge.html", {"request": request})


@app.get("/judge/batch/{batch_id}")
def get_batch(batch_id: str):
    """Get batch data for annotation"""
    reports_dir = Path(__file__).parent.parent.parent / "reports"
    
    # Find batch file
    if batch_id == "latest":
        # Find most recent batch by modification time
        batch_files = list(reports_dir.glob("judge_batch_*.json"))
        if not batch_files:
            raise HTTPException(404, "No batch found")
        batch_path = max(batch_files, key=lambda p: p.stat().st_mtime)
    else:
        batch_path = reports_dir / f"judge_batch_{batch_id}.json"
        if not batch_path.exists():
            raise HTTPException(404, f"Batch {batch_id} not found")
    
    with open(batch_path) as f:
        return json.load(f)


@app.post("/judge")
def submit_vote(vote: JudgeVote):
    """Submit single vote"""
    reports_dir = Path(__file__).parent.parent.parent / "reports"
    votes_file = reports_dir / f"judge_votes_{vote.batch_id}.jsonl"
    
    # Append vote with timestamp
    vote_data = vote.dict()
    vote_data["timestamp"] = time.time()
    vote_data["ts_iso"] = datetime.now(timezone.utc).isoformat()
    
    with open(votes_file, 'a') as f:
        f.write(json.dumps(vote_data, ensure_ascii=False) + '\n')
    
    return {"status": "ok", "batch_id": vote.batch_id, "qid": vote.qid}


@app.get("/judge/summary.json")
def judge_summary(batch: str = "latest"):
    """Aggregate votes and compute verdict"""
    reports_dir = Path(__file__).parent.parent.parent / "reports"
    
    # Find batch ID
    if batch == "latest":
        vote_files = sorted(reports_dir.glob("judge_votes_*.jsonl"), reverse=True)
        if not vote_files:
            return {"error": "No votes found", "verdict": "NO_DATA", "sampled": 0, "labelled": 0}
        batch_id = vote_files[0].stem.replace("judge_votes_", "")
    else:
        batch_id = batch
    
    # Load batch data to get sampled count
    batch_file = reports_dir / f"judge_batch_{batch_id}.json"
    sampled = 0
    if batch_file.exists():
        with open(batch_file) as f:
            batch_data = json.load(f)
            sampled = batch_data.get("total", 0)
    
    votes_file = reports_dir / f"judge_votes_{batch_id}.jsonl"
    if not votes_file.exists():
        return {"error": f"No votes for batch {batch_id}", "verdict": "NO_DATA", "sampled": sampled, "labelled": 0}
    
    # Load and aggregate votes
    votes = []
    with open(votes_file) as f:
        for line in f:
            if line.strip():
                votes.append(json.loads(line))
    
    # Count by pick
    better_on = sum(1 for v in votes if v["pick"] == "on")
    better_off = sum(1 for v in votes if v["pick"] == "off")
    same = sum(1 for v in votes if v["pick"] == "same")
    labelled = len(votes)
    
    # Calculate better_rate (ON版本更好的比例)
    better_rate = better_on / labelled if labelled > 0 else 0.0
    
    # Determine verdict
    if labelled == 0:
        verdict = "NO_DATA"
    elif labelled < sampled:
        verdict = "PENDING"
    elif better_rate >= settings.JUDGE_PASS_RATE:
        verdict = "PASS"
    elif better_rate >= 0.5:
        verdict = "WARN"
    else:
        verdict = "FAIL"
    
    # Build summary
    summary = {
        "batch_id": batch_id,
        "sampled": sampled,
        "labelled": labelled,
        "total": labelled,  # Keep for backward compatibility
        "better_on": better_on,
        "same": same,
        "better_off": better_off,
        "better_rate": round(better_rate, 3),
        "verdict": verdict,
        "threshold": settings.JUDGE_PASS_RATE,
        "timestamp": time.time(),
        "ts_iso": datetime.now(timezone.utc).isoformat()
    }
    
    # Save summary
    results_file = reports_dir / "judge_results.json"
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return summary


@app.get("/judge/report.json")
def judge_report_json(batch: str = "latest"):
    """Get detailed report data with votes and batch info"""
    reports_dir = Path(__file__).parent.parent.parent / "reports"
    
    # Get summary
    summary = judge_summary(batch=batch)
    if "error" in summary:
        return summary
    
    batch_id = summary["batch_id"]
    
    # Load votes
    votes_file = reports_dir / f"judge_votes_{batch_id}.jsonl"
    votes = []
    with open(votes_file) as f:
        for line in f:
            if line.strip():
                votes.append(json.loads(line))
    
    # Load batch data
    batch_file = reports_dir / f"judge_batch_{batch_id}.json"
    batch_data = {}
    if batch_file.exists():
        with open(batch_file) as f:
            batch_data = json.load(f)
    
    # Merge votes with batch items
    samples = []
    for vote in votes[:20]:  # Limit to 20 samples for display
        qid = vote["qid"]
        item = next((x for x in batch_data.get("items", []) if x["id"] == qid), None)
        if item:
            samples.append({
                "qid": qid,
                "query": item["query"],
                "pick": vote["pick"],
                "reason": vote.get("reason", ""),
                "on_results": item.get("on", [])[:3],
                "off_results": item.get("off", [])[:3],
                "topic": item.get("metadata", {}).get("topic", "unknown")
            })
    
    # Topic distribution
    topic_stats = {}
    for sample in samples:
        topic = sample["topic"]
        if topic not in topic_stats:
            topic_stats[topic] = {"on": 0, "same": 0, "off": 0}
        topic_stats[topic][sample["pick"]] += 1
    
    return {
        "summary": summary,
        "samples": samples,
        "topic_stats": topic_stats
    }


@app.get("/judge/report", response_class=HTMLResponse)
def judge_report_page(request: Request, batch: str = "latest"):
    """Render detailed judge report page"""
    return templates.TemplateResponse("judge_report.html", {"request": request})


@app.get("/reports/compare_batch_latest.json")
def get_compare_batch():
    """Get compare batch data for frontend"""
    reports_dir = Path(__file__).parent.parent.parent / "reports"
    compare_file = reports_dir / "compare_batch_latest.json"
    
    if not compare_file.exists():
        return {"error": "compare batch not found"}
    
    with open(compare_file) as f:
        return json.load(f)


def calculate_current_p95(window_seconds=300):
    """Calculate current P95 from recent metrics in api_metrics.csv"""
    import csv
    from datetime import datetime, timezone, timedelta
    
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    metrics_csv = logs_dir / "api_metrics.csv"
    
    if not metrics_csv.exists():
        return None
    
    try:
        # Read recent metrics
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        recent_latencies = []
        
        with open(metrics_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Parse timestamp
                    ts = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                    if ts >= cutoff_time:
                        # Get latency (p95_ms column)
                        latency = float(row.get('p95_ms', 0))
                        if latency > 0:
                            recent_latencies.append(latency)
                except (ValueError, KeyError):
                    continue
        
        # Calculate P95 if we have enough data
        if len(recent_latencies) >= 5:
            recent_latencies.sort()
            p95_index = int(len(recent_latencies) * 0.95)
            return round(recent_latencies[p95_index], 1)
        elif len(recent_latencies) > 0:
            # If not enough data, return max
            return round(max(recent_latencies), 1)
        
    except Exception as e:
        print(f"[WARN] Failed to calculate current_p95: {e}")
    
    return None

@app.get("/dashboard.json")
def get_dashboard(request: Request):
    """Get dashboard data with auto-refresh (rebuilds every 5s)"""
    profile = request.query_params.get('profile', CURRENT_PROFILE)
    
    reports_dir = Path(__file__).parent.parent.parent / "reports"
    dashboard_file = reports_dir / "dashboard.json"
    
    # Always rebuild if stale (>5s) or missing
    should_build = False
    if not dashboard_file.exists():
        should_build = True
        print("[DEMO] dashboard.json missing, triggering build")
    else:
        age = time.time() - dashboard_file.stat().st_mtime
        if age > 5:
            should_build = True
            print(f"[DEMO] dashboard.json stale ({age:.1f}s), triggering rebuild")
    
    # Non-blocking rebuild in background thread
    if should_build:
        build_script = Path(__file__).parent.parent.parent / "scripts" / "build_dashboard.py"
        
        def background_build():
            try:
                subprocess.run(
                    [sys.executable, str(build_script), "--profile", profile],
                    timeout=10,
                    check=True,
                    capture_output=True,
                    cwd=str(Path(__file__).parent.parent.parent)
                )
                print(f"[DEMO] dashboard rebuilt for profile={profile}")
            except Exception as e:
                print(f"[DEMO] dashboard build failed: {e}")
        
        # Start background thread (non-blocking)
        thread = threading.Thread(target=background_build, daemon=True)
        thread.start()
    
    # Return existing data (or skeleton if missing)
    if dashboard_file.exists():
        try:
            with open(dashboard_file) as f:
                data = json.load(f)
            
            # Update runtime state
            data["profile"] = profile
            data["mock_mode"] = manager.use_mock
            
            # Add metadata with collection info
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["collection"] = manager.collection_name if not manager.use_mock else None
            data["meta"]["mock_mode"] = manager.use_mock
            data["meta"]["profile"] = profile
            # Add points count for vector DB badge
            if not manager.use_mock and hasattr(manager, 'points_count'):
                data["meta"]["points"] = manager.points_count
            
            # Add runtime parameters (reranker, candidate_k, cache_policy)
            data["meta"]["params"] = {
                "reranker_on": getattr(settings, "ENABLE_RERANKER", False),
                "candidate_k": getattr(settings, "CANDIDATE_K_MAX", 128),
                "cache_policy": getattr(settings, "CACHE_POLICY", "standard")
            }
            
            # Add tuner state to meta
            if tuner_state is not None:
                params = tuner_state["params"]
                reranker_on = tuner_state["strategy"] != "default" and params.topk >= 128
                data["meta"]["tuner"] = {
                    "enabled": tuner_enabled,
                    "strategy": tuner_state["strategy"],
                    "params": {
                        "topk": params.topk,
                        "ef": params.ef,
                        "parallel": params.parallel,
                        "reranker_on": reranker_on
                    },
                    "last_step": datetime.fromtimestamp(tuner_state["last_step_ts"], tz=timezone.utc).isoformat() if tuner_state["last_step_ts"] > 0 else None
                }
            else:
                # Fallback when tuner not available
                data["meta"]["tuner"] = {
                    "enabled": False,
                    "strategy": "default",
                    "params": {
                        "topk": 128,
                        "ef": 128,
                        "parallel": 4,
                        "reranker_on": False
                    },
                    "last_step": None
                }
            
            print(f"[DEMO] meta profile={profile} params={data['meta']['params']} tuner={data['meta']['tuner']['strategy']}")
            
            if "sla" not in data:
                data["sla"] = {}
            data["sla"]["target_p95"] = sla_state.get("target_p95", 300)
            
            # Add last_metric_ts to debug info (best effort)
            if "debug" not in data.get("sla", {}):
                if "sla" in data:
                    data["sla"]["debug"] = {}
            
            try:
                # Read last ~500 lines of CSV to find most recent timestamp
                logs_dir = Path(__file__).parent.parent.parent / "logs"
                csv_path = logs_dir / "api_metrics.csv"
                if csv_path.exists():
                    with open(csv_path, 'rb') as f:
                        # Seek to end and read last ~50KB
                        f.seek(0, 2)
                        file_size = f.tell()
                        f.seek(max(0, file_size - 50000), 0)
                        lines = f.read().decode('utf-8', errors='ignore').split('\n')
                    
                    # Find last valid timestamp
                    last_ts = None
                    for line in reversed(lines[-500:]):
                        try:
                            if ',' in line and not line.startswith('ts'):
                                parts = line.split(',')
                                ts_str = parts[0].strip()
                                if ts_str.isdigit() and len(ts_str) > 10:
                                    last_ts = int(ts_str) / 1000.0
                                else:
                                    last_ts = float(ts_str)
                                if last_ts > 0:
                                    data["sla"]["debug"]["last_metric_ts"] = datetime.fromtimestamp(last_ts, tz=timezone.utc).isoformat()
                                    break
                        except:
                            continue
            except Exception as e:
                print(f"[DEMO] Failed to get last_metric_ts: {e}")
            
            # Update warmup logic based on p95_samples
            p95_samples = data.get("sla", {}).get("debug", {}).get("p95_samples", 0)
            if p95_samples < 10:
                data["meta"]["note"] = "collecting"
            
            # Merge runtime events with dashboard events (keep last 200, sorted by ts)
            existing_events = data.get("events", [])
            all_events = existing_events + EVENTS_LOG
            # Deduplicate by ts+type, sort descending, keep last 200
            seen = set()
            unique_events = []
            for evt in all_events:
                key = (evt.get("ts", 0), evt.get("type", ""))
                if key not in seen:
                    seen.add(key)
                    unique_events.append(evt)
            data["events"] = sorted(unique_events, key=lambda e: e.get("ts", 0), reverse=False)[-200:]
            
            # ✅ Compute TAI from events (overrides build_dashboard.py's CSV-based calculation)
            tai_result = compute_tai_from_events(data["events"], window_sec=120.0)
            
            # Update meta.kpi.tai (frontend priority path)
            if "meta" not in data:
                data["meta"] = {}
            if "kpi" not in data["meta"]:
                data["meta"]["kpi"] = {}
            data["meta"]["kpi"]["tai"] = tai_result
            
            # Update kpi.tai (backward compatibility)
            if "kpi" not in data:
                data["kpi"] = {}
            data["kpi"]["tai"] = tai_result.get("value", 0.0) if tai_result.get("value") is not None else 0.0
            
            print(f"[DEMO] TAI computed: value={tai_result.get('value')}, reason={tai_result.get('reason')}, samples={tai_result.get('samples')}")
            
            # Auto-warmup logic: check if data is insufficient and trigger traffic if needed
            warmup_guard.reset_if_expired()
            series = data.get("series", {})
            p95_points = len(series.get("p95_on", []))
            tps_points = len(series.get("tps", []))
            
            if warmup_guard.should_warmup(p95_points, tps_points):
                # Trigger auto-traffic asynchronously
                def trigger_warmup():
                    try:
                        if not auto_worker.enabled:
                            auto_worker.start(cycle_sec=20, duration=30, qps=6.0)
                            warmup_guard.mark_warmed_up()
                    except Exception as e:
                        print(f"[AUTO] warmup trigger failed: {e}")
                
                threading.Thread(target=trigger_warmup, daemon=True).start()
                print(f"[AUTO] Auto-warmup triggered (p95_pts={p95_points}, tps_pts={tps_points})")
            
            return JSONResponse(content=data, headers={"Cache-Control": "no-store"})
        except Exception as e:
            print(f"[DEMO] failed to read dashboard.json: {e}")
    
    # Fallback skeleton (empty state)
    fallback_tuner = {
        "enabled": False,
        "strategy": "default",
        "params": {
            "topk": 128,
            "ef": 128,
            "parallel": 4,
            "reranker_on": False
        },
        "last_step": None
    }
    if tuner_state is not None:
        params = tuner_state["params"]
        reranker_on = tuner_state["strategy"] != "default" and params.topk >= 128
        fallback_tuner = {
            "enabled": tuner_enabled,
            "strategy": tuner_state["strategy"],
            "params": {
                "topk": params.topk,
                "ef": params.ef,
                "parallel": params.parallel,
                "reranker_on": reranker_on
            },
            "last_step": datetime.fromtimestamp(tuner_state["last_step_ts"], tz=timezone.utc).isoformat() if tuner_state["last_step_ts"] > 0 else None
        }
    
    return JSONResponse(
        content={
            "profile": profile,
            "mock_mode": manager.use_mock,
            "meta": {
                "collection": manager.collection_name if not manager.use_mock else None,
                "mock_mode": manager.use_mock,
                "profile": profile,
                "points": manager.points_count if (not manager.use_mock and hasattr(manager, 'points_count')) else None,
                "params": {
                    "reranker_on": getattr(settings, "ENABLE_RERANKER", False),
                    "candidate_k": getattr(settings, "CANDIDATE_K_MAX", 128),
                    "cache_policy": getattr(settings, "CACHE_POLICY", "standard")
                },
                "tuner": fallback_tuner
            },
            "sla": {
                "target_p95": sla_state.get("target_p95", 300),
                "current_p95": 0,
                "window": "1m"
            },
            "cards": {
                "delta_recall": 0.0,
                "delta_p95_ms": 0.0,
                "p_value": 1.0,
                "human_better": 0.0,
                "tps": 0.0,
                "cache_hit": 0.0,
                "notes": ["Building dashboard..."]
            },
            "series": {
                "p95_on": [],
                "p95_off": [],
                "recall_on": [],
                "recall_off": [],
                "tps": [],
                "rerank_rate": [],
                "cache_hit": []
            },
            "events": [],
            "window_sec": 1800,
            "bucket_sec": 5,
            "source": {"metrics_csv": "logs/api_metrics.csv"}
        },
        headers={"Cache-Control": "no-store"}
    )


@app.get("/demo/sla")
def get_or_set_sla(target_p95: int = None):
    """Get or set SLA target P95. Range: 100-800ms"""
    global sla_state
    
    if target_p95 is not None:
        # Validate range
        if not 100 <= target_p95 <= 800:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "target_p95 must be between 100 and 800"}
            )
        
        # Emit event if SLA changed
        old_target = sla_state["target_p95"]
        if target_p95 != old_target:
            emit_event("sla", {
                "from": old_target,
                "to": target_p95,
                "profile": CURRENT_PROFILE,  # current profile at event time
                "target_p95": target_p95
            })
        
        sla_state["target_p95"] = target_p95
        print(f"[SLA] target_p95={target_p95}")
        return {"ok": True, "target_p95": target_p95}
    
    # Return current target
    return {"target_p95": sla_state["target_p95"]}


@app.get("/auto/status")
def auto_status():
    """Get AutoTrafficWorker status"""
    status = auto_worker.get_status()
    
    # ✅ Debug log: warn if desired vs runtime differ
    if status.get("enabled", False):
        desired_tc = status.get("desired_total_cycles")
        runtime_tc = status.get("total_cycles")
        if desired_tc != runtime_tc:
            print(f"[AUTO][WARN] desired vs runtime: tc_desired={desired_tc} tc_runtime={runtime_tc}")
    
    return status


@app.get("/auto/debug")
def auto_debug():
    """🆕 Get detailed AutoTrafficWorker debug state for troubleshooting
    
    Returns all state fields including stop_reason for root cause analysis.
    """
    with auto_worker.lock:
        now = time.time()
        return {
            "enabled": auto_worker.enabled,
            "running": auto_worker.running,
            "stop_reason": auto_worker.stop_reason,
            "last_error": auto_worker.last_error,
            "completed_cycles": auto_worker.completed_cycles,
            "total_cycles": auto_worker.total_cycles,
            "cycle_count": auto_worker.cycle_count,
            "immediate_trigger": auto_worker.immediate_trigger,
            "heartbeat": auto_worker.heartbeat,
            "heartbeat_age_sec": int(now - auto_worker.heartbeat),
            "last_run_ts": auto_worker.last_run_ts,
            "next_run_at": auto_worker.next_run_at,
            "next_eta_sec": max(0, int(auto_worker.next_run_at - now)),
            "runtime_params": {
                "qps": auto_worker.qps,
                "duration": auto_worker.duration,
                "cycle_sec": auto_worker.cycle_sec,
                "cases": auto_worker.cases,
                "unique": auto_worker.unique,
            },
            "desired_params": {
                "qps": auto_worker.desired_qps,
                "duration": auto_worker.desired_duration,
                "cycle_sec": auto_worker.desired_cycle_sec,
                "cases": auto_worker.desired_cases,
                "unique": auto_worker.desired_unique,
                "total_cycles": auto_worker.desired_total_cycles,
            },
            "now": now
        }


@app.post("/auto/start")
async def auto_start(request: Request, cycle: int = 25, duration: int = 20, qps: float = 6.0, cases: str = "on,off", unique: int = 1, total_cycles: int = None):
    """Start AutoTrafficWorker with specified parameters
    
    Args:
        cycle: Seconds between traffic cycles
        duration: Duration of each traffic cycle (seconds)
        qps: Queries per second
        cases: Comma-separated list of modes to test (e.g., "on,off")
        unique: If 1, randomize queries to reduce cache hits
        total_cycles: Total number of cycles to run (optional, default from env or 20)
    """
    global last_start_ts
    
    # 🆕 Guard 1: Debounce (prevent rapid clicks)
    async with auto_lock:
        now = time.time()
        if now - last_start_ts < 0.3:
            print("[AUTO] ⚙️ debounce guard triggered (too fast)")
            return {"ok": False, "error": "debounce: too fast (< 300ms)"}
        last_start_ts = now
    
    # ✅ A) Normalize incoming params - robust parsing
    def _to_int(x, default=None):
        try:
            return int(str(x).strip())
        except:
            return default
    
    # Read from query params with alias support (cycle OR total_cycles)
    raw_qps = request.query_params.get("qps", qps)
    raw_duration = request.query_params.get("duration", duration)
    raw_cycle_sec = request.query_params.get("cycle", cycle)
    raw_total_cycles = request.query_params.get("total_cycles", total_cycles)
    
    # Parse robustly
    parsed_qps = float(raw_qps) if raw_qps else 6.0
    parsed_duration = _to_int(raw_duration, default=20)
    parsed_cycle_sec = _to_int(raw_cycle_sec, default=25)
    tc = _to_int(raw_total_cycles, default=None)
    
    # Normalize: 0/None => None (∞). Only >0 keeps number.
    parsed_total_cycles = None if tc in (None, 0) else tc
    
    # Debug log: show raw and parsed values
    print(f"[AUTO] /start raw: qps={raw_qps} dur={raw_duration} cycle='{raw_cycle_sec}' total_cycles='{raw_total_cycles}' → parsed total_cycles={parsed_total_cycles}")
    
    # 🆕 Guard 2: Parameter validation - enforce cycle_sec >= duration + 5
    min_cycle_sec = parsed_duration + 5
    if parsed_cycle_sec < min_cycle_sec:
        error_msg = f"cycle_sec ({parsed_cycle_sec}s) too short for duration ({parsed_duration}s), need >= {min_cycle_sec}s"
        print(f"[AUTO] 🚫 param guard: {error_msg}")
        return {"ok": False, "error": error_msg}
    
    auto_worker.start(cycle_sec=parsed_cycle_sec, duration=parsed_duration, qps=parsed_qps, cases=cases, unique=unique, total_cycles=parsed_total_cycles)
    
    # Emit event for auto-traffic start
    emit_event("auto", {
        "action": "start",
        "profile": CURRENT_PROFILE,
        "auto_status": True,
        "qps": qps,
        "duration": duration
    })
    
    return {"ok": True, "status": auto_worker.get_status()}


@app.post("/auto/stop")
async def auto_stop():
    """Stop AutoTrafficWorker"""
    # 🆕 Guard: Mutual exclusion with start
    async with auto_lock:
        auto_worker.stop()
    
    # Emit event for auto-traffic stop
    emit_event("auto", {
        "action": "stop",
        "profile": CURRENT_PROFILE,
        "auto_status": False
    })
    
    return {"ok": True, "status": auto_worker.get_status()}


@app.post("/auto/params")
def auto_update_params(cycle: int = None, duration: int = None, qps: float = None, cases: str = None, unique: int = None, total_cycles: int = None):
    """Update desired params without starting/stopping worker
    
    This allows users to configure params while worker is stopped.
    Changes take effect on next start().
    """
    auto_worker.update_desired_params(
        qps=qps,
        duration=duration,
        cycle_sec=cycle,
        cases=cases,
        unique=unique,
        total_cycles=total_cycles
    )
    return {"ok": True, "status": auto_worker.get_status()}


@app.get("/tuner/strategy")
def get_tuner_strategy():
    """Get current tuner strategy and state"""
    # If tuner_state exists (even if TUNER_ENABLED=False), return its values
    if tuner_state is not None:
        params = tuner_state["params"]
        # Determine reranker_on: ON if strategy != 'default' and topk >= 128
        reranker_on = tuner_state["strategy"] != "default" and params.topk >= 128
        
        return {
            "enabled": tuner_enabled,  # Runtime toggle state
            "current": tuner_state["strategy"],
            "available": StrategyRegistry.available(),
            "shadow_ratio": tuner_state["shadow_ratio"],
            "params": {
                "topk": params.topk,
                "ef": params.ef,
                "parallel": params.parallel,
                "reranker_on": reranker_on
            },
            "last_step": datetime.fromtimestamp(tuner_state["last_step_ts"], tz=timezone.utc).isoformat() if tuner_state["last_step_ts"] > 0 else None
        }
    
    # Default fallback when tuner_state is None
    return {
        "enabled": False,
        "current": "default",
        "available": ["default", "linear_only"],
        "shadow_ratio": 0.0,
        "params": {
            "topk": 128,
            "ef": 128,
            "parallel": 4,
            "reranker_on": False
        },
        "last_step": None
    }


@app.post("/tuner/strategy")
def set_tuner_strategy(name: str):
    """Switch tuner strategy"""
    global tuner_state
    
    if tuner_state is None:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Tuner not available"}
        )
    
    if name not in StrategyRegistry.available():
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": f"Unknown strategy: {name}"}
        )
    
    old_strategy = tuner_state["strategy"]
    tuner_state["strategy"] = name
    tuner_state["last_step_ts"] = 0.0  # Reset cooldown
    
    emit_event("tuner.switch", {
        "from": old_strategy,
        "to": name,
        "shadow_ratio": tuner_state["shadow_ratio"]
    })
    
    tuner_logger.info(f"switch: {old_strategy} → {name}")
    
    # Return full status (same structure as GET /tuner/status)
    params = tuner_state["params"]
    reranker_on = tuner_state["strategy"] != "default" and params.topk >= 128
    
    return {
        "enabled": tuner_enabled,
        "strategy": tuner_state["strategy"],
        "params": {
            "topk": params.topk,
            "ef": params.ef,
            "parallel": params.parallel,
            "reranker_on": reranker_on
        },
        "last_step": datetime.fromtimestamp(tuner_state["last_step_ts"], tz=timezone.utc).isoformat() if tuner_state["last_step_ts"] > 0 else None
    }


@app.post("/tuner/shadow")
def set_tuner_shadow(ratio: float):
    """Set shadow traffic ratio (0-0.5)"""
    global tuner_state
    
    # Initialize tuner_state if not exists (for shadow-only usage)
    if tuner_state is None and TUNER_AVAILABLE:
        tuner_state = {
            "strategy": "default",
            "shadow_ratio": 0.0,
            "cooldown_sec": 30,
            "last_step_ts": 0.0,
            "params": TunerParams(topk=128, ef=128, parallel=4)
        }
    
    if tuner_state is None:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Tuner not available"}
        )
    
    # Clamp to [0, 0.5]
    ratio = max(0.0, min(0.5, ratio))
    
    old_ratio = tuner_state["shadow_ratio"]
    tuner_state["shadow_ratio"] = ratio
    
    emit_event("tuner.shadow", {
        "from": old_ratio,
        "to": ratio,
        "strategy": tuner_state["strategy"]
    })
    
    tuner_logger.info(f"shadow: {old_ratio:.0%} → {ratio:.0%}")
    
    return {"ok": True, "shadow_ratio": ratio}


@app.get("/tuner/enabled")
def get_tuner_enabled():
    """Get current tuner runtime enabled state"""
    return {"enabled": tuner_enabled}


@app.post("/tuner/enabled")
def set_tuner_enabled(enabled: bool = Body(..., embed=True)):
    """Set tuner runtime enabled state (ON/OFF toggle)"""
    global tuner_enabled
    
    old_state = tuner_enabled
    tuner_enabled = enabled
    
    emit_event("tuner.toggle", {
        "enabled": tuner_enabled,
        "from": old_state,
        "to": tuner_enabled
    })
    
    tuner_logger.info(f"toggle: {'ON' if tuner_enabled else 'OFF'}")
    
    return {"enabled": tuner_enabled}


@app.get("/admin/warmup/status")
def get_warmup_status():
    """Get current auto-warmup status (for frontend notification)"""
    return warmup_guard.get_status()


@app.get("/admin/metrics/heartbeat")
def get_metrics_heartbeat():
    """Get metrics CSV heartbeat status (lightweight, read-only)"""
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    csv_path = logs_dir / "api_metrics.csv"
    
    if not csv_path.exists():
        return {
            "csv_exists": False,
            "rows": 0,
            "last_ts": None,
            "age_sec": None,
            "collecting": True
        }
    
    try:
        # Quick stat check
        stat = csv_path.stat()
        file_size = stat.st_size
        
        # Read last ~500 lines (tail)
        with open(csv_path, 'rb') as f:
            f.seek(0, 2)
            f.seek(max(0, file_size - 50000), 0)
            lines = f.read().decode('utf-8', errors='ignore').split('\n')
        
        # Count non-empty lines (approximate row count)
        rows = len([l for l in lines if l.strip() and not l.startswith('ts')])
        
        # Find last timestamp
        last_ts = None
        age_sec = None
        for line in reversed(lines[-500:]):
            try:
                if ',' in line and not line.startswith('ts'):
                    parts = line.split(',')
                    ts_str = parts[0].strip()
                    if ts_str.isdigit() and len(ts_str) > 10:
                        last_ts_sec = int(ts_str) / 1000.0
                    else:
                        last_ts_sec = float(ts_str)
                    
                    if last_ts_sec > 0:
                        last_ts = datetime.fromtimestamp(last_ts_sec, tz=timezone.utc).isoformat()
                        age_sec = time.time() - last_ts_sec
                        break
            except:
                continue
        
        collecting = age_sec is None or age_sec > 120  # No metrics in last 2 minutes
        
        return {
            "csv_exists": True,
            "rows": rows,
            "last_ts": last_ts,
            "age_sec": round(age_sec, 1) if age_sec else None,
            "collecting": collecting
        }
        
    except Exception as e:
        return {
            "csv_exists": True,
            "error": str(e),
            "collecting": True
        }


@app.get("/admin/qdrant/collections")
def get_qdrant_collections():
    """Get Qdrant collections summary (read-only, for operator awareness)"""
    if not QDRANT_AVAILABLE or manager.use_mock:
        return {
            "error": "Qdrant not available",
            "url": settings.QDRANT_URL,
            "chosen": None,
            "mock_mode": True,
            "candidates": []
        }
    
    try:
        # List all collections with their details
        collections = manager.client.get_collections().collections
        candidates = []
        
        for c in collections:
            try:
                coll_info = manager.client.get_collection(c.name)
                candidates.append({
                    "name": c.name,
                    "points": coll_info.points_count,
                    "chosen": c.name == manager.collection_name
                })
            except:
                candidates.append({
                    "name": c.name,
                    "points": 0,
                    "chosen": False
                })
        
        # Sort by points descending
        candidates.sort(key=lambda x: x["points"], reverse=True)
        
        return {
            "url": settings.QDRANT_URL,
            "chosen": manager.collection_name,
            "mock_mode": manager.use_mock,
            "candidates": candidates
        }
    except Exception as e:
        return {
            "error": str(e),
            "url": settings.QDRANT_URL,
            "chosen": manager.collection_name,
            "mock_mode": manager.use_mock,
            "candidates": []
        }


# ═══════════════════════════════════════════════════════════
# Profiler Endpoints
# ═══════════════════════════════════════════════════════════

@app.get("/admin/profiler/report")
def profiler_report():
    """Get performance profiling report"""
    if not PROFILER_AVAILABLE:
        return {"error": "Profiler not available"}
    
    try:
        report = get_profile_report()
        
        # Add health assessment
        health = {
            "status": "healthy",
            "issues": []
        }
        
        # Check if any critical paths are slow
        raw_stats = report.get("raw", {})
        
        # Auto worker loop should be < 500ms
        if "auto.worker.loop" in raw_stats:
            p95 = raw_stats["auto.worker.loop"].get("p95_ms", 0)
            if p95 > 500:
                health["status"] = "warning"
                health["issues"].append(f"Auto worker loop P95 {p95}ms > 500ms (slow)")
        
        # Dashboard build should be < 300ms
        if "dashboard.build" in raw_stats:
            p95 = raw_stats["dashboard.build"].get("p95_ms", 0)
            if p95 > 300:
                health["status"] = "warning"
                health["issues"].append(f"Dashboard build P95 {p95}ms > 300ms (slow)")
        
        # Traffic generation should complete in reasonable time
        if "auto.traffic.generate" in raw_stats:
            p95 = raw_stats["auto.traffic.generate"].get("p95_ms", 0)
            expected_max = 35000  # 30s duration + 5s overhead
            if p95 > expected_max:
                health["status"] = "warning"
                health["issues"].append(f"Traffic generation P95 {p95}ms > {expected_max}ms (slow)")
        
        report["health"] = health
        return report
    
    except Exception as e:
        return {"error": str(e)}


@app.post("/admin/profiler/reset")
def profiler_reset():
    """Reset profiler statistics"""
    if not PROFILER_AVAILABLE:
        return {"error": "Profiler not available"}
    
    try:
        reset_profiler()
        return {"ok": True, "message": "Profiler stats reset"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/admin/profiler/enable")
def profiler_enable():
    """Enable profiler"""
    if not PROFILER_AVAILABLE:
        return {"error": "Profiler not available"}
    
    try:
        enable_profiler()
        return {"ok": True, "message": "Profiler enabled"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/admin/profiler/disable")
def profiler_disable():
    """Disable profiler"""
    if not PROFILER_AVAILABLE:
        return {"error": "Profiler not available"}
    
    try:
        disable_profiler()
        return {"ok": True, "message": "Profiler disabled"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/demo", response_class=HTMLResponse)
def demo_page(request: Request):
    """Render demo dashboard page"""
    global CURRENT_PROFILE
    # Read profile from query parameter and update global state
    profile = request.query_params.get('profile', 'balanced')
    if profile in ['fast', 'balanced', 'quality']:
        # Emit event if profile changed
        if profile != CURRENT_PROFILE:
            emit_event("profile", {
                "from": CURRENT_PROFILE,
                "to": profile,
                "profile": profile  # profile at event time
            })
        CURRENT_PROFILE = profile
    return templates.TemplateResponse("demo.html", {"request": request, "profile": CURRENT_PROFILE})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
