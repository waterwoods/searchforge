#!/usr/bin/env python3
"""
Reactivity Metrics - WII and TAI calculation for live dashboard
Computes real-time indices with minimal overhead (<1ms per refresh)
"""
import time
from collections import deque
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import statistics


@dataclass
class ReactivitySnapshot:
    """Snapshot of reactivity metrics at a point in time"""
    timestamp: float
    wii: float  # Wind Intensity Index (0-100)
    tai: float  # Tuner Activity Index (0-100)
    wii_components: Dict[str, float]  # Breakdown for debugging
    tai_components: Dict[str, float]  # Breakdown for debugging


class ReactivityMetrics:
    """
    Efficient sliding-window calculator for WII and TAI indices.
    
    WII (Wind Intensity Index): Measures auto-traffic load intensity
      - QPS (queries per second)
      - Burstiness (variance in request timing)
      - Cache miss rate
      
    TAI (Tuner Activity Index): Measures auto-tuner adjustment activity
      - Parameter delta magnitude
      - Adjustment frequency
      - Emergency mode transitions
    """
    
    def __init__(self, window_sec: float = 30.0, max_history: int = 10):
        """
        Initialize reactivity metrics tracker.
        
        Args:
            window_sec: Sliding window size in seconds (default 30s)
            max_history: Maximum number of snapshots to retain (default 10)
        """
        self.window_sec = window_sec
        self.max_history = max_history
        
        # Sliding window buffers (timestamp, value)
        self.qps_buffer: deque = deque()  # (ts, count)
        self.cache_buffer: deque = deque()  # (ts, is_hit)
        self.tuner_buffer: deque = deque()  # (ts, delta_magnitude)
        
        # History of computed snapshots
        self.history: deque = deque(maxlen=max_history)
        
        # Calibration constants (tunable via env or config)
        self.wii_weights = {
            "qps": 0.4,
            "burstiness": 0.3,
            "cache_miss": 0.3
        }
        self.tai_weights = {
            "delta_magnitude": 0.5,
            "frequency": 0.5
        }
        
        # Normalization constants (based on typical values)
        self.qps_max = 20.0  # Typical max QPS
        self.delta_max = 50.0  # Typical max parameter delta
        self.freq_max = 0.1  # Max frequency (adjustments/sec)
        
    def _evict_old_samples(self, buffer: deque, current_time: float) -> None:
        """Remove samples older than window from buffer"""
        cutoff = current_time - self.window_sec
        while buffer and buffer[0][0] < cutoff:
            buffer.popleft()
    
    def feed_query(self, timestamp: Optional[float] = None, cache_hit: bool = True) -> None:
        """
        Record a query event.
        
        Args:
            timestamp: Event timestamp (default: current time)
            cache_hit: Whether this query hit the cache
        """
        ts = timestamp or time.time()
        self.qps_buffer.append((ts, 1))
        self.cache_buffer.append((ts, 1 if cache_hit else 0))
        
        # Evict old samples
        self._evict_old_samples(self.qps_buffer, ts)
        self._evict_old_samples(self.cache_buffer, ts)
    
    def feed_tuner_action(self, delta_magnitude: float, timestamp: Optional[float] = None) -> None:
        """
        Record a tuner parameter adjustment.
        
        Args:
            delta_magnitude: Magnitude of parameter change (e.g., |new - old|)
            timestamp: Event timestamp (default: current time)
        """
        ts = timestamp or time.time()
        self.tuner_buffer.append((ts, delta_magnitude))
        
        # Evict old samples
        self._evict_old_samples(self.tuner_buffer, ts)
    
    def _compute_wii(self, current_time: float) -> Tuple[float, Dict[str, float]]:
        """
        Compute Wind Intensity Index (WII).
        
        Returns:
            (wii_score, components_dict)
        """
        # 1. QPS component
        if len(self.qps_buffer) == 0:
            qps = 0.0
        else:
            time_span = max(0.1, current_time - self.qps_buffer[0][0])
            qps = len(self.qps_buffer) / time_span
        qps_normalized = min(1.0, qps / self.qps_max)
        
        # 2. Burstiness component (coefficient of variation)
        if len(self.qps_buffer) < 2:
            burstiness = 0.0
        else:
            # Inter-arrival times
            timestamps = [ts for ts, _ in self.qps_buffer]
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            if intervals:
                mean_interval = statistics.mean(intervals)
                if mean_interval > 0:
                    std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0.0
                    cv = std_interval / mean_interval
                    burstiness = min(1.0, cv)  # Higher CV = more bursty
                else:
                    burstiness = 0.0
            else:
                burstiness = 0.0
        
        # 3. Cache miss rate component
        if len(self.cache_buffer) == 0:
            cache_miss_rate = 0.0
        else:
            hits = sum(val for _, val in self.cache_buffer)
            total = len(self.cache_buffer)
            cache_miss_rate = 1.0 - (hits / total)
        
        # Weighted combination
        wii_score = (
            qps_normalized * self.wii_weights["qps"] +
            burstiness * self.wii_weights["burstiness"] +
            cache_miss_rate * self.wii_weights["cache_miss"]
        )
        wii_score = wii_score * 100.0  # Scale to 0-100
        
        components = {
            "qps": round(qps, 2),
            "qps_normalized": round(qps_normalized, 3),
            "burstiness": round(burstiness, 3),
            "cache_miss_rate": round(cache_miss_rate, 3),
            "raw_score": round(wii_score, 2)
        }
        
        return wii_score, components
    
    def _compute_tai(self, current_time: float) -> Tuple[float, Dict[str, float]]:
        """
        Compute Tuner Activity Index (TAI).
        
        Returns:
            (tai_score, components_dict)
        """
        if len(self.tuner_buffer) == 0:
            return 0.0, {
                "actions": 0,
                "avg_delta": 0.0,
                "frequency": 0.0,
                "raw_score": 0.0
            }
        
        # 1. Delta magnitude component (average of recent deltas)
        deltas = [val for _, val in self.tuner_buffer]
        avg_delta = statistics.mean(deltas)
        delta_normalized = min(1.0, avg_delta / self.delta_max)
        
        # 2. Frequency component (actions per second)
        time_span = max(0.1, current_time - self.tuner_buffer[0][0])
        frequency = len(self.tuner_buffer) / time_span
        freq_normalized = min(1.0, frequency / self.freq_max)
        
        # Weighted combination
        tai_score = (
            delta_normalized * self.tai_weights["delta_magnitude"] +
            freq_normalized * self.tai_weights["frequency"]
        )
        tai_score = tai_score * 100.0  # Scale to 0-100
        
        components = {
            "actions": len(self.tuner_buffer),
            "avg_delta": round(avg_delta, 2),
            "frequency": round(frequency, 4),
            "delta_normalized": round(delta_normalized, 3),
            "freq_normalized": round(freq_normalized, 3),
            "raw_score": round(tai_score, 2)
        }
        
        return tai_score, components
    
    def compute(self, timestamp: Optional[float] = None) -> ReactivitySnapshot:
        """
        Compute current WII and TAI scores.
        
        Args:
            timestamp: Current time (default: time.time())
            
        Returns:
            ReactivitySnapshot with current scores and components
        """
        ts = timestamp or time.time()
        
        # Evict old samples from all buffers
        self._evict_old_samples(self.qps_buffer, ts)
        self._evict_old_samples(self.cache_buffer, ts)
        self._evict_old_samples(self.tuner_buffer, ts)
        
        # Compute indices
        wii_score, wii_components = self._compute_wii(ts)
        tai_score, tai_components = self._compute_tai(ts)
        
        # Create snapshot
        snapshot = ReactivitySnapshot(
            timestamp=ts,
            wii=round(wii_score, 1),
            tai=round(tai_score, 1),
            wii_components=wii_components,
            tai_components=tai_components
        )
        
        # Add to history
        self.history.append(snapshot)
        
        return snapshot
    
    def get_sparkline_data(self) -> Dict[str, List[Tuple[int, float]]]:
        """
        Get sparkline data for dashboard (last N snapshots).
        
        Returns:
            Dict with 'wii' and 'tai' arrays of [timestamp_ms, value]
        """
        wii_data = []
        tai_data = []
        
        for snapshot in self.history:
            ts_ms = int(snapshot.timestamp * 1000)
            wii_data.append([ts_ms, snapshot.wii])
            tai_data.append([ts_ms, snapshot.tai])
        
        return {
            "wii": wii_data,
            "tai": tai_data
        }
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current state for dashboard JSON.
        
        Returns:
            Dict with current scores, sparkline data, and debug info
        """
        if not self.history:
            # No data yet
            return {
                "wii": 0.0,
                "tai": 0.0,
                "wii_sparkline": [],
                "tai_sparkline": [],
                "debug": {
                    "wii_components": {},
                    "tai_components": {},
                    "window_sec": self.window_sec,
                    "samples": {
                        "qps": 0,
                        "cache": 0,
                        "tuner": 0
                    }
                }
            }
        
        latest = self.history[-1]
        sparklines = self.get_sparkline_data()
        
        return {
            "wii": latest.wii,
            "tai": latest.tai,
            "wii_sparkline": sparklines["wii"],
            "tai_sparkline": sparklines["tai"],
            "debug": {
                "wii_components": latest.wii_components,
                "tai_components": latest.tai_components,
                "window_sec": self.window_sec,
                "samples": {
                    "qps": len(self.qps_buffer),
                    "cache": len(self.cache_buffer),
                    "tuner": len(self.tuner_buffer)
                }
            }
        }
    
    def reset(self) -> None:
        """Clear all buffers and history"""
        self.qps_buffer.clear()
        self.cache_buffer.clear()
        self.tuner_buffer.clear()
        self.history.clear()


# Global instance (singleton pattern)
_global_tracker: Optional[ReactivityMetrics] = None


def get_global_tracker() -> ReactivityMetrics:
    """Get or create the global reactivity metrics tracker"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ReactivityMetrics()
    return _global_tracker


def reset_global_tracker() -> None:
    """Reset the global tracker"""
    global _global_tracker
    if _global_tracker is not None:
        _global_tracker.reset()


