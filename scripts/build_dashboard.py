#!/usr/bin/env python3
"""
Dashboard Builder - 5s aggregation with full data contract
Reads logs/api_metrics.csv → reports/dashboard.json (atomic write)
"""
import json
import csv
import os
import sys
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
REPORTS = ROOT / "reports"
LOGS_DIR = ROOT / "logs"

# Add modules to path
sys.path.insert(0, str(ROOT))

# Import reactivity metrics
from modules.metrics.reactivity_metrics import ReactivityMetrics

# Demo visibility tuning (reversible via env)
DASH_P95_WINDOW = int(os.getenv("DASH_P95_WINDOW", "60"))  # Default 60s, aligned with /metrics/window60s
DASH_MIN_SAMPLES = int(os.getenv("DASH_MIN_SAMPLES", "3"))  # Minimum samples before fallback (relaxed from 10)


def load_csv_with_5s_aggregation(window_sec=1800, csv_path=None):
    """
    Load CSV and aggregate into 5-second buckets. Error-tolerant, skips invalid rows.
    Returns: (p95_on, p95_off, recall_on, recall_off, tps, rerank_rate, cache_hit, events, skipped_rows, stage_timing)
    """
    if csv_path is None:
        csv_path = LOGS_DIR / "api_metrics.csv"
    if not os.path.exists(csv_path):
        return [], [], [], [], [], [], [], [], 0, {}
    
    skipped_rows = 0
    
    try:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        print(f"[BUILD] CSV read error: {e}")
        return [], [], [], [], [], [], [], [], 0, {}
    
    if not rows:
        return [], [], [], [], [], [], [], [], 0, {}
    
    # Filter to recent window
    now = time.time()
    cutoff = now - window_sec
    
    # 5-second buckets
    p95_buckets = defaultdict(lambda: {"on": [], "off": []})
    recall_buckets = defaultdict(lambda: {"on": [], "off": []})
    tps_buckets = defaultdict(int)
    rerank_buckets = defaultdict(list)
    cache_buckets = defaultdict(list)
    
    # NEW: Stage timing buckets (for breakdown analysis)
    ann_buckets = defaultdict(list)
    rerank_time_buckets = defaultdict(list)
    network_buckets = defaultdict(list)
    total_buckets = defaultdict(list)  # For invariant checking
    
    events = []
    last_profile = None
    last_target_p95 = None
    
    for row in rows:
        try:
            # Parse timestamp (try both ms and ISO format)
            ts_val = row.get("ts", row.get("timestamp", "0"))
            try:
                ts = int(ts_val) / 1000.0 if ts_val.isdigit() and len(ts_val) > 10 else float(ts_val)
            except:
                ts = datetime.fromisoformat(row.get("timestamp", "").replace('Z', '+00:00')).timestamp()
            
            if ts < cutoff:
                continue
            
            # 5-second bucket
            bucket = int(ts // 5) * 5000  # bucket key in ms
            
            # Parse fields with fallbacks
            latency = float(row.get("latency_ms", row.get("p95_ms", 0)))
            recall = float(row.get("recall_at10", 0))
            mode = row.get("mode", row.get("group", "on")).lower()
            rerank = int(row.get("rerank", row.get("rerank_hit", 0)))
            cache_hit = int(row.get("cache_hit", 0))
            profile = row.get("profile", "balanced")
            
            # Aggregate by mode
            if mode in ["on", "off"]:
                if latency > 0:
                    p95_buckets[bucket][mode].append(latency)
                if recall > 0:
                    recall_buckets[bucket][mode].append(recall)
                tps_buckets[bucket] += 1
                rerank_buckets[bucket].append(rerank)
                cache_buckets[bucket].append(cache_hit)
                
                # NEW: Collect stage timing data
                ann_time = float(row.get("qdrant_latency_ms", 0))
                rerank_time = float(row.get("rerank_latency_ms", 0))
                network_time = float(row.get("network_latency_ms", 0))
                total_time = latency  # Use the same latency as above
                
                # Collect all timing data (including zeros for proper aggregation)
                ann_buckets[bucket].append(ann_time)
                rerank_time_buckets[bucket].append(rerank_time)
                network_buckets[bucket].append(network_time)
                total_buckets[bucket].append(total_time)
            
            # Track events (profile/SLA changes)
            if profile != last_profile and last_profile is not None:
                events.append({
                    "ts": bucket,  # Keep original bucket timestamp (ms)
                    "type": "profile",
                    "meta": {
                        "to": profile,
                        "profile": profile  # Profile at event time
                    }
                })
            last_profile = profile
            
        except (KeyError, ValueError, AttributeError):
            skipped_rows += 1
            continue
    
    def avg(lst):
        return sum(lst) / len(lst) if lst else 0.0
    
    def percentile(lst, p):
        """Calculate percentile (p95)"""
        if not lst or len(lst) < 3:  # Relaxed from 10 to 3
            return None
        sorted_lst = sorted(lst)
        idx = int(len(sorted_lst) * p)
        return sorted_lst[min(idx, len(sorted_lst) - 1)]
    
    # Build series arrays (using 60s window for consistency)
    p95_on = []
    p95_off = []
    recall_on = []
    recall_off = []
    tps = []
    rerank_rate = []
    cache_hit = []
    
    # Compute aggregation window (last 60s worth of buckets: 60s / 5s = 12 buckets)
    AGG_WINDOW_SEC = 60
    all_buckets = sorted(p95_buckets.keys())
    recent_buckets = all_buckets[-12:] if len(all_buckets) >= 12 else all_buckets
    
    for bucket in sorted(p95_buckets.keys()):
        # P95 (need >=10 samples)
        p95_on_val = percentile(p95_buckets[bucket]["on"], 0.95)
        p95_off_val = percentile(p95_buckets[bucket]["off"], 0.95)
        
        if p95_on_val is not None:
            p95_on.append([bucket, round(p95_on_val, 1)])
        if p95_off_val is not None:
            p95_off.append([bucket, round(p95_off_val, 1)])
        
        # Recall (need >=5 samples)
        recall_on_vals = recall_buckets[bucket]["on"]
        recall_off_vals = recall_buckets[bucket]["off"]
        
        if len(recall_on_vals) >= 5:
            recall_on.append([bucket, round(avg(recall_on_vals), 3)])
        if len(recall_off_vals) >= 5:
            recall_off.append([bucket, round(avg(recall_off_vals), 3)])
    
    for bucket in sorted(tps_buckets.keys()):
        # TPS (count / 5 seconds)
        tps.append([bucket, round(tps_buckets[bucket] / 5.0, 2)])
        
        # Rerank rate
        if rerank_buckets[bucket]:
            rerank_rate.append([bucket, round(avg(rerank_buckets[bucket]), 3)])
        
        # Cache hit rate
        if cache_buckets[bucket]:
            cache_hit.append([bucket, round(avg(cache_buckets[bucket]), 3)])
    
    # NEW: Compute stage timing statistics (UNIFIED 60s window to match Actual P95)
    stage_timing = {}
    STAGE_WINDOW_SEC = 60  # Match the P95 window for consistency
    recent_buckets = sorted(tps_buckets.keys())[-12:]  # Last 60s (12 * 5s)
    
    if recent_buckets:
        # Aggregate timing data from recent buckets
        all_ann = []
        all_rerank = []
        all_network = []
        all_total = []
        
        for bucket in recent_buckets:
            all_ann.extend(ann_buckets.get(bucket, []))
            all_rerank.extend(rerank_time_buckets.get(bucket, []))
            all_network.extend(network_buckets.get(bucket, []))
            all_total.extend(total_buckets.get(bucket, []))
        
        # Calculate number of samples
        samples_count = len(all_ann)  # Should be same for all
        
        # Calculate averages and percentiles
        ann_avg = avg(all_ann) if all_ann else 0
        rerank_avg = avg(all_rerank) if all_rerank else 0
        network_avg = avg(all_network) if all_network else 0
        total_avg_actual = avg(all_total) if all_total else 0
        
        # Calculate P95 values
        def p95(lst):
            if not lst or len(lst) < 3:  # Relaxed from 10 to 3
                return max(lst) if lst else 0
            sorted_lst = sorted(lst)
            return sorted_lst[int(len(sorted_lst) * 0.95)]
        
        ann_p95 = p95(all_ann)
        rerank_p95 = p95(all_rerank)
        network_p95 = p95(all_network)
        total_p95_actual = p95(all_total)
        
        # Compute sum and check invariant
        sum_avg = ann_avg + rerank_avg + network_avg
        sum_p95 = ann_p95 + rerank_p95 + network_p95
        
        # Calculate deviation (expect sum ≈ total)
        deviation_avg_pct = 0
        if total_avg_actual > 0:
            deviation_avg_pct = ((sum_avg - total_avg_actual) / total_avg_actual) * 100
        
        deviation_p95_pct = 0
        if total_p95_actual > 0:
            deviation_p95_pct = ((sum_p95 - total_p95_actual) / total_p95_actual) * 100
        
        # Count clamped network values (network == 0 but total > 0)
        clamped_network_rows = sum(1 for i in range(len(all_network)) if all_network[i] == 0 and all_total[i] > 0)
        
        stage_timing = {
            "window_sec": STAGE_WINDOW_SEC,
            "avg_ms": {
                "ann": round(ann_avg, 2),
                "rerank": round(rerank_avg, 2),
                "network": round(network_avg, 2),
                "total": round(total_avg_actual, 2)
            },
            "p95_ms": {
                "ann": round(ann_p95, 2),
                "rerank": round(rerank_p95, 2),
                "network": round(network_p95, 2),
                "total": round(total_p95_actual, 2)
            },
            "samples": samples_count,
            "clamped_network_rows": clamped_network_rows,
            "invariant": {
                "sum_avg_ms": round(sum_avg, 2),
                "sum_p95_ms": round(sum_p95, 2),
                "deviation_avg_pct": round(deviation_avg_pct, 2),
                "deviation_p95_pct": round(deviation_p95_pct, 2)
            }
        }
        
        # Backward compatibility fields (deprecated but kept for now)
        stage_timing["ann_avg_ms"] = stage_timing["avg_ms"]["ann"]
        stage_timing["ann_p95_ms"] = stage_timing["p95_ms"]["ann"]
        stage_timing["rerank_avg_ms"] = stage_timing["avg_ms"]["rerank"]
        stage_timing["rerank_p95_ms"] = stage_timing["p95_ms"]["rerank"]
        stage_timing["network_avg_ms"] = stage_timing["avg_ms"]["network"]
        stage_timing["network_p95_ms"] = stage_timing["p95_ms"]["network"]
        stage_timing["total_avg_ms"] = stage_timing["avg_ms"]["total"]
    
    return p95_on, p95_off, recall_on, recall_off, tps, rerank_rate, cache_hit, events, skipped_rows, stage_timing


def compute_actual_p95_1min():
    """
    Calculate actual P95 with robust fallback logic (window configurable via env for demo visibility).
    Returns: dict with {current_p95, p95_samples, window_sec, reason} or None if CSV missing
    """
    csv_path = LOGS_DIR / "api_metrics.csv"
    if not csv_path.exists():
        return None
    
    try:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        print(f"[BUILD] CSV read error: {e}")
        return None
    
    if not rows:
        return {"current_p95": None, "p95_samples": 0, "window_sec": DASH_P95_WINDOW, "reason": "no_data"}
    
    now = time.time()
    window_sec = DASH_P95_WINDOW  # Configurable via env
    cutoff = now - window_sec
    recent_latencies = []
    skipped = 0
    
    # Parse rows with robust field name handling
    for row in rows:
        try:
            # Handle multiple timestamp field names
            ts_val = row.get("ts") or row.get("timestamp") or "0"
            try:
                # Try milliseconds first
                if ts_val.isdigit() and len(ts_val) > 10:
                    ts = int(ts_val) / 1000.0
                else:
                    ts = float(ts_val)
            except:
                # Try ISO format
                try:
                    ts = datetime.fromisoformat(row.get("timestamp", "").replace('Z', '+00:00')).timestamp()
                except:
                    skipped += 1
                    continue
            
            # Only include recent samples
            if ts >= cutoff:
                # Handle multiple latency field names
                latency_str = row.get("latency_ms") or row.get("latency") or row.get("p95_ms") or "0"
                try:
                    latency = float(latency_str)
                    if latency > 0:
                        recent_latencies.append(latency)
                except:
                    skipped += 1
        except:
            skipped += 1
            continue
    
    p95_samples = len(recent_latencies)
    
    # Fallback: if window has < DASH_MIN_SAMPLES, use last 200 rows regardless of time
    if p95_samples < DASH_MIN_SAMPLES:
        fallback_latencies = []
        for row in rows[-200:]:
            try:
                latency_str = row.get("latency_ms") or row.get("latency") or row.get("p95_ms") or "0"
                latency = float(latency_str)
                if latency > 0:
                    fallback_latencies.append(latency)
            except:
                continue
        
        if len(fallback_latencies) >= DASH_MIN_SAMPLES:
            fallback_latencies.sort()
            p95_idx = int(len(fallback_latencies) * 0.95)
            result = {
                "current_p95": round(fallback_latencies[p95_idx], 1),
                "p95_samples": len(fallback_latencies),
                "window_sec": "fallback_200",
                "reason": "fallback"
            }
            print(f"[BUILD] p95_samples={result['p95_samples']} skipped={skipped} reason={result['reason']} (fallback to last 200 rows)")
            return result
        else:
            result = {
                "current_p95": None,
                "p95_samples": p95_samples,
                "window_sec": window_sec,
                "reason": "no_recent_samples"
            }
            print(f"[BUILD] p95_samples={p95_samples} skipped={skipped} reason={result['reason']}")
            return result
    
    # Normal case: sufficient samples in window
    recent_latencies.sort()
    p95_idx = int(len(recent_latencies) * 0.95)
    result = {
        "current_p95": round(recent_latencies[p95_idx], 1),
        "p95_samples": p95_samples,
        "window_sec": window_sec,
        "reason": "ok"
    }
    print(f"[BUILD] p95_samples={p95_samples} skipped={skipped} window={window_sec}s reason={result['reason']}")
    return result


def compute_cards(p95_on, p95_off, recall_on, recall_off, tps, cache_hit):
    """
    Compute KPI cards with 3-minute window for deltas.
    Requires sample sufficiency per 5s bucket: P95>=10, Recall>=5 samples per side.
    Returns: (delta_recall, delta_p95_ms, p_value, tps_val, cache_hit_val, notes, eligible_buckets)
    """
    notes = []
    eligible_buckets = 0
    
    # Helper: average of recent N points
    def recent_avg(series, n=36):  # 36 * 5s = 3 min
        if not series:
            return None
        recent = series[-n:]
        return sum(p[1] for p in recent) / len(recent)
    
    # Check sample sufficiency: count eligible buckets (both P95 and Recall have enough samples)
    # For P95: need >=10 samples per 5s bucket per side
    # For Recall: need >=5 samples per 5s bucket per side
    # We approximate by checking if we have points (which already passed the threshold check)
    
    # Count eligible buckets: buckets where both ON and OFF have data
    p95_buckets_on = {p[0] for p in p95_on}
    p95_buckets_off = {p[0] for p in p95_off}
    recall_buckets_on = {r[0] for r in recall_on}
    recall_buckets_off = {r[0] for r in recall_off}
    
    # A bucket is eligible if it has both P95 and Recall data for both ON and OFF
    all_buckets = p95_buckets_on | p95_buckets_off | recall_buckets_on | recall_buckets_off
    for bucket in all_buckets:
        has_p95 = bucket in p95_buckets_on and bucket in p95_buckets_off
        has_recall = bucket in recall_buckets_on and bucket in recall_buckets_off
        if has_p95 and has_recall:
            eligible_buckets += 1
    
    # Delta P95
    p95_on_avg = recent_avg(p95_on)
    p95_off_avg = recent_avg(p95_off)
    
    # Require minimum eligible buckets for reliable delta calculation
    min_eligible_buckets = 6  # At least 30 seconds of paired data
    
    if p95_on_avg is not None and p95_off_avg is not None and eligible_buckets >= min_eligible_buckets:
        delta_p95_ms = p95_on_avg - p95_off_avg
    else:
        delta_p95_ms = None
        notes.append(f"p95 insufficient (on={len(p95_on)}, off={len(p95_off)}, eligible={eligible_buckets})")
    
    # Delta Recall
    recall_on_avg = recent_avg(recall_on)
    recall_off_avg = recent_avg(recall_off)
    
    if recall_on_avg is not None and recall_off_avg is not None and eligible_buckets >= min_eligible_buckets:
        delta_recall = recall_on_avg - recall_off_avg
    else:
        delta_recall = None
        notes.append(f"recall insufficient (on={len(recall_on)}, off={len(recall_off)}, eligible={eligible_buckets})")
    
    # Simple t-test (Welch's t-test approximation)
    def welch_ttest(s1, s2):
        """Simplified Welch's t-test, returns p-value approximation"""
        if not s1 or not s2 or len(s1) < 20 or len(s2) < 20:
            return None
        
        vals1 = [p[1] for p in s1[-60:]]  # last 60 points
        vals2 = [p[1] for p in s2[-60:]]
        
        n1, n2 = len(vals1), len(vals2)
        mean1 = sum(vals1) / n1
        mean2 = sum(vals2) / n2
        
        var1 = sum((x - mean1) ** 2 for x in vals1) / (n1 - 1)
        var2 = sum((x - mean2) ** 2 for x in vals2) / (n2 - 1)
        
        if var1 == 0 and var2 == 0:
            return 1.0
        
        t_stat = abs(mean1 - mean2) / ((var1 / n1 + var2 / n2) ** 0.5)
        
        # Simple p-value approximation (conservative)
        if t_stat > 2.5:
            return 0.01
        elif t_stat > 2.0:
            return 0.05
        elif t_stat > 1.5:
            return 0.15
        else:
            return 0.5
    
    p_value = welch_ttest(p95_on, p95_off)
    if p_value is None:
        notes.append("p_value requires >=20 samples per group")
    
    # TPS (total requests / time window to align with /metrics/window60s)
    # Changed from: average of bucket TPS (incorrect for gaps)
    # To: sum of all requests in 60s / actual time span
    # Note: Each TPS bucket value = count/5s, so TPS*5 = count for that bucket
    if tps:
        if len(tps) > 0:
            latest_ts = tps[-1][0]  # Timestamp of last bucket (in ms)
            cutoff_ts = latest_ts - 60000  # 60 seconds ago
            recent_tps = [p for p in tps if p[0] >= cutoff_ts]
            
            if recent_tps:
                # Convert each bucket's TPS back to count: TPS * 5 seconds
                # Then sum total requests and divide by actual time span
                total_requests = sum(p[1] * 5 for p in recent_tps)  # TPS * 5s = count
                time_span_sec = (recent_tps[-1][0] - recent_tps[0][0]) / 1000.0 + 5.0  # +5 for last bucket duration
                tps_val = round(total_requests / time_span_sec, 2) if time_span_sec > 0 else None
            else:
                tps_val = None
        else:
            tps_val = None
    else:
        tps_val = None
    
    # Cache hit (average over 60s time window for consistency)
    if cache_hit:
        if len(cache_hit) > 0:
            latest_ts = cache_hit[-1][0]
            cutoff_ts = latest_ts - 60000
            recent_cache = [p for p in cache_hit if p[0] >= cutoff_ts]
            cache_hit_val = sum(p[1] for p in recent_cache) / len(recent_cache) if recent_cache else None
        else:
            cache_hit_val = None
    else:
        cache_hit_val = None
    
    return delta_recall, delta_p95_ms, p_value, tps_val, cache_hit_val, notes, eligible_buckets


def compute_reactivity_metrics():
    """
    Compute WII and TAI from recent CSV data.
    Uses 30s sliding window with last 10 snapshots for sparklines.
    
    Returns: dict with wii, tai, sparklines, and debug info
    """
    csv_path = LOGS_DIR / "api_metrics.csv"
    if not csv_path.exists():
        return {
            "wii": 0.0,
            "tai": 0.0,
            "wii_sparkline": [],
            "tai_sparkline": [],
            "debug": {
                "wii_components": {},
                "tai_components": {},
                "window_sec": 30,
                "samples": {"qps": 0, "cache": 0, "tuner": 0}
            }
        }
    
    # Initialize tracker with 30s window
    tracker = ReactivityMetrics(window_sec=30.0, max_history=10)
    
    try:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        print(f"[BUILD] Reactivity: CSV read error: {e}")
        return tracker.get_current_state()
    
    if not rows:
        return tracker.get_current_state()
    
    # Process recent data (last 60 seconds for enough context)
    now = time.time()
    cutoff = now - 60
    
    # Track tuner parameter changes for delta calculation
    last_params = {}
    
    for row in rows:
        try:
            # Parse timestamp
            ts_val = row.get("ts", row.get("timestamp", "0"))
            try:
                ts = int(ts_val) / 1000.0 if ts_val.isdigit() and len(ts_val) > 10 else float(ts_val)
            except:
                ts = datetime.fromisoformat(row.get("timestamp", "").replace('Z', '+00:00')).timestamp()
            
            if ts < cutoff:
                continue
            
            # Feed query event (for QPS and cache tracking)
            cache_hit = int(row.get("cache_hit", 0)) == 1
            tracker.feed_query(timestamp=ts, cache_hit=cache_hit)
            
            # Check for tuner parameter changes
            # Look for ef_search, topk, or other tuning params
            current_params = {}
            if "ef_search" in row:
                try:
                    current_params["ef_search"] = int(row["ef_search"])
                except:
                    pass
            if "topk" in row:
                try:
                    current_params["topk"] = int(row["topk"])
                except:
                    pass
            
            # Compute delta if params changed
            if current_params and last_params:
                for key in current_params:
                    if key in last_params:
                        delta = abs(current_params[key] - last_params[key])
                        if delta > 0:
                            tracker.feed_tuner_action(delta_magnitude=float(delta), timestamp=ts)
            
            last_params = current_params
            
        except (KeyError, ValueError, AttributeError):
            continue
    
    # Compute final snapshot every 5 seconds (aligned with dashboard refresh)
    # We'll compute multiple snapshots across the window for sparkline
    window_start = now - 30
    for t in range(0, 30, 3):  # Every 3 seconds = 10 snapshots
        snapshot_time = window_start + t
        if snapshot_time <= now:
            tracker.compute(timestamp=snapshot_time)
    
    # Get final state
    return tracker.get_current_state()


def get_collection_metadata():
    """
    Get current collection metadata by checking:
    1. runtime_settings.json
    2. QDRANT_COLLECTION env
    3. Default from settings
    
    Returns: (collection_name, mock_mode)
    """
    import os
    
    # Try runtime_settings.json first
    settings_path = ROOT / "runtime_settings.json"
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                data = json.load(f)
                collection = data.get("qdrant_collection")
                if collection:
                    return collection, False
        except:
            pass
    
    # Try env var
    collection = os.environ.get("QDRANT_COLLECTION", "beir_fiqa_full_ta")
    
    # Check if Qdrant is available by attempting a connection
    try:
        import urllib.request
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        req = urllib.request.Request(f"{qdrant_url}/collections", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            collections = [c["name"] for c in data.get("result", {}).get("collections", [])]
            
            # Check if our collection exists
            if collection in collections:
                return collection, False
            else:
                # Collection not found, but Qdrant is up
                return None, True
    except:
        # Qdrant unavailable
        return None, True


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', default='balanced', choices=['fast', 'balanced', 'quality'])
    args = parser.parse_args()
    
    profile = args.profile
    
    # Get collection metadata
    collection_name, mock_mode = get_collection_metadata()
    
    # Load data with 5s aggregation (try both possible CSV locations)
    csv_path = "logs/api_metrics.csv"
    if not os.path.exists(csv_path):
        csv_path = "services/fiqa_api/logs/api_metrics.csv"
    
    p95_on, p95_off, recall_on, recall_off, tps, rerank_rate, cache_hit, events, skipped_rows, stage_timing = load_csv_with_5s_aggregation(csv_path=csv_path)
    
    # Compute cards
    delta_recall, delta_p95_ms, p_value, tps_val, cache_hit_val, notes, eligible_buckets = compute_cards(
        p95_on, p95_off, recall_on, recall_off, tps, cache_hit
    )
    
    # Compute actual P95 (90s window with fallback)
    p95_result = compute_actual_p95_1min()
    
    # Extract values from result dict
    if p95_result:
        current_p95 = p95_result.get("current_p95")
        p95_samples = p95_result.get("p95_samples", 0)
        p95_reason = p95_result.get("reason", "unknown")
    else:
        current_p95 = None
        p95_samples = 0
        p95_reason = "csv_missing"
    
    # Determine if we're in "collecting" state (insufficient data)
    collecting = current_p95 is None or p95_samples < DASH_MIN_SAMPLES or len(p95_on) < 12 or len(tps) < 12
    
    # Fallback to canary data for human_better_rate
    human_better = 0.0
    canary_path = REPORTS / f"autotuner_canary_{profile}.json"
    if canary_path.exists():
        try:
            with open(canary_path) as f:
                canary = json.load(f)
                human_better = canary.get("human_better_rate", 0.0)
        except:
            pass
    
    # Try to read tuner state from runtime (lightweight)
    tuner_data = {"enabled": False, "strategy": "default", "shadow_ratio": 0.0, "params": {"topk": 128, "ef": 128, "parallel": 4}}
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:8000/tuner/strategy", method="GET")
        with urllib.request.urlopen(req, timeout=1) as resp:
            tuner_data = json.loads(resp.read().decode('utf-8'))
    except:
        pass  # Tuner not available, use defaults
    
    # Compute reactivity metrics (WII and TAI)
    reactivity = compute_reactivity_metrics()
    
    # Extract WII and TAI values with debug info
    wii_value = reactivity.get("wii", 0.0)
    tai_value = reactivity.get("tai", 0.0)
    wii_debug = reactivity.get("debug", {})
    
    # Determine WII/TAI collection reasons
    wii_reason = None
    tai_reason = None
    
    # Check if traffic is running (based on samples)
    if wii_debug.get("samples", {}).get("qps", 0) == 0:
        wii_reason = "auto_off"
    
    # Check if tuner is active (based on tuner samples)
    if not tuner_data.get("enabled", False):
        tai_reason = "tuner_off"
    elif wii_debug.get("samples", {}).get("tuner", 0) == 0:
        tai_reason = "no_tuner_activity"
    
    # Build dashboard JSON
    dashboard = {
        "profile": profile,
        "mock_mode": mock_mode,
        "meta": {
            "profile": profile,
            "collection": collection_name,
            "mock_mode": mock_mode,
            "note": "collecting" if collecting else "ready",
            "window_sec": 60,  # Dashboard aggregation window (aligned with /metrics/window60s)
            # params will be injected by app.py at runtime
            "stage_timing": stage_timing,  # NEW: Stage timing breakdown (ANN, Rerank, Network)
            "kpi": {
                "wii": {
                    "value": wii_value if wii_reason is None else None,
                    "reason": wii_reason,
                    "samples": wii_debug.get("samples", {}).get("qps", 0),
                    "window_sec": wii_debug.get("window_sec", 30)
                },
                "tai": {
                    "value": tai_value if tai_reason is None else None,
                    "reason": tai_reason,
                    "samples": wii_debug.get("samples", {}).get("tuner", 0),
                    "window_sec": wii_debug.get("window_sec", 30)
                }
            }
        },
        "tuner": tuner_data,
        "sla": {
            "target_p95": 300,  # Will be updated by app.py
            "current_p95": current_p95 if current_p95 is not None else None,
            "actual_p95": current_p95,  # Explicit null when insufficient data
            "window": f"{DASH_P95_WINDOW}s",
            "debug": {
                "p95_samples": p95_samples,
                "window_sec": DASH_P95_WINDOW if p95_reason == "ok" else (p95_result.get("window_sec", DASH_P95_WINDOW) if p95_result else DASH_P95_WINDOW),
                "reason": p95_reason,
                "last_metric_ts": None  # Will be updated by app.py
            }
        },
        "kpi": {
            "wii": wii_value,
            "tai": tai_value,
            "delta_recall": delta_recall if delta_recall is not None else None,
            "delta_p95_ms": delta_p95_ms if delta_p95_ms is not None else None,
            "p_value": p_value if p_value is not None else 1.0,
            "human_better": human_better,
            "tps": tps_val if tps_val is not None else 0.0,
            "cache_hit": cache_hit_val if cache_hit_val is not None else 0.0,
            "debug": {
                "p95_samples": p95_samples,
                "eligible_buckets": eligible_buckets,
                "reason": p95_reason if eligible_buckets == 0 else "ok",
                "notes": notes
            }
        },
        "cards": {
            "delta_recall": delta_recall if delta_recall is not None else None,
            "delta_p95_ms": delta_p95_ms if delta_p95_ms is not None else None,
            "p_value": p_value if p_value is not None else 1.0,
            "human_better": human_better,
            "tps": tps_val if tps_val is not None else 0.0,
            "cache_hit": cache_hit_val if cache_hit_val is not None else 0.0,
            "notes": notes,
            "eligible_buckets": eligible_buckets,
            "delta_recall_missing": delta_recall is None,
            "delta_p95_missing": delta_p95_ms is None
        },
        "series": {
            "p95_on": p95_on,
            "p95_off": p95_off,
            "recall_on": recall_on,
            "recall_off": recall_off,
            "tps": tps,
            "rerank_rate": rerank_rate,
            "cache_hit": cache_hit
        },
        "reactivity": {
            "wii": reactivity.get("wii", 0.0),
            "tai": reactivity.get("tai", 0.0),
            "wii_sparkline": reactivity.get("wii_sparkline", []),
            "tai_sparkline": reactivity.get("tai_sparkline", []),
            "debug": reactivity.get("debug", {})
        },
        "events": events,
        "window_sec": 1800,
        "bucket_sec": 5,
        "source": {
            "metrics_csv": "logs/api_metrics.csv",
            "canary": f"reports/autotuner_canary_{profile}.json"
        }
    }
    
    # Atomic write
    REPORTS.mkdir(exist_ok=True)
    tmp_path = REPORTS / "dashboard.json.tmp"
    final_path = REPORTS / "dashboard.json"
    
    with open(tmp_path, 'w') as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    
    os.replace(tmp_path, final_path)
    
    # Log output
    status = "collecting" if collecting else "ok"
    print(f"[BUILD] {status} | buckets={len(p95_on)+len(p95_off)} | p95_pts={len(p95_on)}/{len(p95_off)} | recall_pts={len(recall_on)}/{len(recall_off)} | eligible={eligible_buckets} | skipped={skipped_rows} | src=metrics/canary")
    print(f"[BUILD] deltas: eligible_buckets={eligible_buckets} p95_samples={p95_samples} reason={p95_reason if eligible_buckets == 0 else 'ok'}")
    print(f"[BUILD] WII={wii_value:.1f} (reason={wii_reason or 'ok'}, samples={wii_debug.get('samples', {}).get('qps', 0)})")
    print(f"[BUILD] TAI={tai_value:.1f} (reason={tai_reason or 'ok'}, samples={wii_debug.get('samples', {}).get('tuner', 0)})")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
