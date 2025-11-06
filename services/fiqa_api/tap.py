"""
Live Tap Mode - Unified request tracing for Black Swan demo.

Provides JSON logging of HTTP requests and semantic events to JSONL files
with minimal overhead (<2ms per request).
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import deque
import threading

# Configuration
TAP_ENABLED = os.getenv("TAP_ENABLED", "false").lower() == "true"
TAP_DIR = Path(__file__).parent.parent.parent / "logs"
TAP_BACKEND_FILE = TAP_DIR / "tap_backend.jsonl"
TAP_EVENTS_FILE = TAP_DIR / "tap_events.jsonl"
TAP_MAX_EVENTS_PER_RUN = 2000  # Truncate after 2k events per run_id
TAP_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB max file size

# Thread-safe in-memory buffer for recent events (for /tap/tail endpoint)
_backend_buffer = deque(maxlen=500)
_events_buffer = deque(maxlen=500)
_buffer_lock = threading.Lock()

# Statistics
_stats = {
    "enabled": TAP_ENABLED,
    "total_backend_logs": 0,
    "total_event_logs": 0,
    "truncated_runs": set(),
    "last_write_error": None,
    "overhead_ms_avg": 0.0,
    "overhead_samples": []
}


def ensure_tap_dir():
    """Create logs directory if it doesn't exist."""
    if TAP_ENABLED:
        TAP_DIR.mkdir(parents=True, exist_ok=True)


def rotate_if_needed(file_path: Path):
    """Rotate log file if it exceeds max size."""
    if not file_path.exists():
        return
    
    if file_path.stat().st_size > TAP_FILE_MAX_SIZE:
        # Rotate: rename current file with timestamp
        timestamp = int(time.time())
        backup_path = file_path.with_suffix(f".{timestamp}.jsonl")
        file_path.rename(backup_path)
        print(f"[TAP] Rotated {file_path.name} to {backup_path.name}")


def write_backend_log(
    ts: int,
    method: str,
    path: str,
    status: int,
    ms: float,
    run_id: Optional[str] = None,
    phase: Optional[str] = None,
    client: str = "unknown",
    body_size: int = 0,
    error_code: Optional[str] = None
):
    """
    Write a backend request log entry.
    
    Args:
        ts: Timestamp in milliseconds
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status: HTTP status code
        ms: Request duration in milliseconds
        run_id: Optional run_id for correlation
        phase: Optional phase (warmup, baseline, trip, recovery, etc.)
        client: Client identifier (frontend, script, curl, etc.)
        body_size: Request body size in bytes
        error_code: Optional error code
    """
    if not TAP_ENABLED:
        return
    
    start = time.time()
    
    try:
        ensure_tap_dir()
        rotate_if_needed(TAP_BACKEND_FILE)
        
        entry = {
            "ts": ts,
            "method": method,
            "path": path,
            "status": status,
            "ms": round(ms, 2),
            "client": client
        }
        
        if run_id:
            entry["run_id"] = run_id
        if phase:
            entry["phase"] = phase
        if body_size > 0:
            entry["body_size"] = body_size
        if error_code:
            entry["error_code"] = error_code
        
        # Write to file
        with open(TAP_BACKEND_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Add to in-memory buffer
        with _buffer_lock:
            _backend_buffer.append(entry)
        
        _stats["total_backend_logs"] += 1
        
        # Track overhead
        overhead_ms = (time.time() - start) * 1000
        _stats["overhead_samples"].append(overhead_ms)
        if len(_stats["overhead_samples"]) > 100:
            _stats["overhead_samples"] = _stats["overhead_samples"][-100:]
        _stats["overhead_ms_avg"] = sum(_stats["overhead_samples"]) / len(_stats["overhead_samples"])
        
    except Exception as e:
        _stats["last_write_error"] = str(e)
        print(f"[TAP] Error writing backend log: {e}")


def write_event_log(
    event: str,
    run_id: Optional[str] = None,
    phase: Optional[str] = None,
    progress: Optional[int] = None,
    message: Optional[str] = None,
    http: Optional[int] = None,
    client: str = "unknown",
    **kwargs
):
    """
    Write a semantic event log entry.
    
    Args:
        event: Event type (start, progress, complete, error, abort, click, poll, etc.)
        run_id: Optional run_id for correlation
        phase: Optional phase
        progress: Optional progress percentage
        message: Optional message
        http: Optional HTTP status code
        client: Client identifier (frontend, script, etc.)
        **kwargs: Additional event-specific fields
    """
    if not TAP_ENABLED:
        return
    
    start = time.time()
    
    try:
        ensure_tap_dir()
        rotate_if_needed(TAP_EVENTS_FILE)
        
        # Check run_id event limit
        if run_id and run_id in _stats["truncated_runs"]:
            return  # Already truncated, skip
        
        entry = {
            "ts": int(time.time() * 1000),
            "event": event,
            "client": client
        }
        
        if run_id:
            entry["run_id"] = run_id
        if phase:
            entry["phase"] = phase
        if progress is not None:
            entry["progress"] = progress
        if message:
            entry["message"] = message
        if http:
            entry["http"] = http
        
        # Add any additional fields
        entry.update(kwargs)
        
        # Write to file
        with open(TAP_EVENTS_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Add to in-memory buffer
        with _buffer_lock:
            _events_buffer.append(entry)
        
        _stats["total_event_logs"] += 1
        
        # Check if we've exceeded max events for this run_id
        if run_id:
            count = sum(1 for e in _events_buffer if e.get("run_id") == run_id)
            if count >= TAP_MAX_EVENTS_PER_RUN:
                _stats["truncated_runs"].add(run_id)
                print(f"[TAP] Truncated run_id {run_id} at {TAP_MAX_EVENTS_PER_RUN} events")
        
        # Track overhead
        overhead_ms = (time.time() - start) * 1000
        _stats["overhead_samples"].append(overhead_ms)
        if len(_stats["overhead_samples"]) > 100:
            _stats["overhead_samples"] = _stats["overhead_samples"][-100:]
        _stats["overhead_ms_avg"] = sum(_stats["overhead_samples"]) / len(_stats["overhead_samples"])
        
    except Exception as e:
        _stats["last_write_error"] = str(e)
        print(f"[TAP] Error writing event log: {e}")


def read_tail(file_type: str, n: int = 200) -> List[Dict[str, Any]]:
    """
    Read last N lines from tap file.
    
    Args:
        file_type: "backend" or "events"
        n: Number of lines to read (default: 200)
    
    Returns:
        List of log entries (most recent last)
    """
    if not TAP_ENABLED:
        return []
    
    # Use in-memory buffer for fast access
    with _buffer_lock:
        if file_type == "backend":
            return list(_backend_buffer)[-n:]
        elif file_type == "events":
            return list(_events_buffer)[-n:]
    
    return []


def get_timeline(run_id: Optional[str] = None, n: int = 500) -> List[Dict[str, Any]]:
    """
    Get unified timeline merging backend and event logs.
    
    Args:
        run_id: Optional run_id to filter by
        n: Maximum number of events to return
    
    Returns:
        List of unified timeline entries sorted by timestamp
    """
    if not TAP_ENABLED:
        return []
    
    timeline = []
    
    with _buffer_lock:
        # Merge backend logs
        for entry in _backend_buffer:
            if run_id is None or entry.get("run_id") == run_id:
                timeline.append({
                    "ts": entry["ts"],
                    "source": "backend",
                    "path": entry["path"],
                    "method": entry.get("method"),
                    "status": entry.get("status"),
                    "ms": entry.get("ms"),
                    "run_id": entry.get("run_id"),
                    "phase": entry.get("phase"),
                    "client": entry.get("client")
                })
        
        # Merge event logs
        for entry in _events_buffer:
            if run_id is None or entry.get("run_id") == run_id:
                timeline.append({
                    "ts": entry["ts"],
                    "source": "event",
                    "event": entry["event"],
                    "run_id": entry.get("run_id"),
                    "phase": entry.get("phase"),
                    "progress": entry.get("progress"),
                    "message": entry.get("message"),
                    "http": entry.get("http"),
                    "client": entry.get("client")
                })
    
    # Sort by timestamp and limit to n entries
    timeline.sort(key=lambda x: x["ts"])
    return timeline[-n:]


def get_health() -> Dict[str, Any]:
    """Get tap system health and statistics."""
    files = []
    
    if TAP_ENABLED:
        if TAP_BACKEND_FILE.exists():
            files.append({
                "name": TAP_BACKEND_FILE.name,
                "size": TAP_BACKEND_FILE.stat().st_size,
                "modified": int(TAP_BACKEND_FILE.stat().st_mtime)
            })
        if TAP_EVENTS_FILE.exists():
            files.append({
                "name": TAP_EVENTS_FILE.name,
                "size": TAP_EVENTS_FILE.stat().st_size,
                "modified": int(TAP_EVENTS_FILE.stat().st_mtime)
            })
    
    return {
        "enabled": TAP_ENABLED,
        "files": files,
        "stats": {
            "backend_logs": _stats["total_backend_logs"],
            "event_logs": _stats["total_event_logs"],
            "truncated_runs": len(_stats["truncated_runs"]),
            "overhead_ms_avg": round(_stats["overhead_ms_avg"], 3),
            "last_error": _stats["last_write_error"]
        },
        "buffer_sizes": {
            "backend": len(_backend_buffer),
            "events": len(_events_buffer)
        }
    }


# Initialize on module load
if TAP_ENABLED:
    ensure_tap_dir()
    print(f"[TAP] Enabled, logging to {TAP_DIR}")
else:
    print("[TAP] Disabled (set TAP_ENABLED=true to enable)")

