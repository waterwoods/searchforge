"""
Metrics Collector for Canary Deployments

This module collects and aggregates performance metrics for canary deployments,
including latency, recall, and SLO violations.
"""

import time
import json
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricsBucket:
    """Represents a time bucket of metrics."""
    timestamp: str
    duration_sec: int
    p95_ms: float
    recall_at_10: float
    response_count: int
    slo_violations: int
    config_name: str


@dataclass
class SearchMetrics:
    """Represents metrics for a single search request."""
    trace_id: str
    timestamp: float
    latency_ms: float
    recall_at_10: float
    config_name: str
    slo_violated: bool


class MetricsCollector:
    """
    Collects and aggregates metrics for canary deployments.
    
    Features:
    - Collects metrics from search requests
    - Aggregates metrics into time buckets (default 5 seconds)
    - Calculates p95 latency and average recall
    - Tracks SLO violations
    - Thread-safe operations
    """
    
    def __init__(self, bucket_duration_sec: int = 5):
        """
        Initialize the metrics collector.
        
        Args:
            bucket_duration_sec: Duration of each metrics bucket in seconds
        """
        self.bucket_duration_sec = bucket_duration_sec
        self._metrics_lock = threading.Lock()
        self._current_buckets: Dict[str, List[SearchMetrics]] = defaultdict(list)
        self._completed_buckets: List[MetricsBucket] = []
        self._start_time = time.time()
        
        logger.info(f"MetricsCollector initialized with bucket_duration={bucket_duration_sec}s")
    
    def record_search(self, trace_id: str, latency_ms: float, recall_at_10: float, 
                     config_name: str, slo_p95_ms: float) -> None:
        """
        Record metrics for a single search request.
        
        Args:
            trace_id: Unique trace ID for the request
            latency_ms: Request latency in milliseconds
            recall_at_10: Recall@10 for this request
            config_name: Configuration name used for this request
            slo_p95_ms: SLO threshold for p95 latency
        """
        slo_violated = latency_ms > slo_p95_ms
        
        metrics = SearchMetrics(
            trace_id=trace_id,
            timestamp=time.time(),
            latency_ms=latency_ms,
            recall_at_10=recall_at_10,
            config_name=config_name,
            slo_violated=slo_violated
        )
        
        with self._metrics_lock:
            self._current_buckets[config_name].append(metrics)
        
        logger.debug(f"Recorded metrics for {config_name}: latency={latency_ms:.2f}ms, recall={recall_at_10:.3f}")
    
    def _create_bucket(self, config_name: str, metrics: List[SearchMetrics], 
                      bucket_start_time: float) -> MetricsBucket:
        """Create a metrics bucket from a list of metrics."""
        if not metrics:
            return MetricsBucket(
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(bucket_start_time)),
                duration_sec=self.bucket_duration_sec,
                p95_ms=0.0,
                recall_at_10=0.0,
                response_count=0,
                slo_violations=0,
                config_name=config_name
            )
        
        latencies = [m.latency_ms for m in metrics]
        recalls = [m.recall_at_10 for m in metrics]
        slo_violations = sum(1 for m in metrics if m.slo_violated)
        
        # Calculate p95 latency
        if len(latencies) >= 2:
            p95_ms = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        else:
            p95_ms = latencies[0] if latencies else 0.0
        
        # Calculate average recall
        avg_recall = statistics.mean(recalls) if recalls else 0.0
        
        return MetricsBucket(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(bucket_start_time)),
            duration_sec=self.bucket_duration_sec,
            p95_ms=p95_ms,
            recall_at_10=avg_recall,
            response_count=len(metrics),
            slo_violations=slo_violations,
            config_name=config_name
        )
    
    def get_completed_buckets(self) -> List[MetricsBucket]:
        """
        Get all completed metrics buckets and start new buckets.
        
        Returns:
            List of completed MetricsBucket objects
        """
        current_time = time.time()
        bucket_start_time = int(current_time / self.bucket_duration_sec) * self.bucket_duration_sec
        
        with self._metrics_lock:
            completed_buckets = []
            
            for config_name, metrics in self._current_buckets.items():
                if metrics:
                    # Create bucket for completed time period
                    bucket = self._create_bucket(config_name, metrics, bucket_start_time)
                    completed_buckets.append(bucket)
                    
                    # Clear the metrics for this config
                    self._current_buckets[config_name] = []
            
            # Add to completed buckets list
            self._completed_buckets.extend(completed_buckets)
            
            # Keep only recent buckets (last 1 hour)
            cutoff_time = current_time - 3600
            self._completed_buckets = [
                b for b in self._completed_buckets 
                if time.mktime(time.strptime(b.timestamp, "%Y-%m-%dT%H:%M:%SZ")) >= cutoff_time
            ]
        
        return completed_buckets
    
    def get_recent_buckets(self, config_name: str, count: int = 10) -> List[MetricsBucket]:
        """
        Get recent metrics buckets for a specific configuration.
        
        Args:
            config_name: Configuration name to filter by
            count: Number of recent buckets to return
            
        Returns:
            List of recent MetricsBucket objects
        """
        with self._metrics_lock:
            config_buckets = [b for b in self._completed_buckets if b.config_name == config_name]
            return config_buckets[-count:] if count > 0 else config_buckets
    
    def get_all_buckets(self, config_name: Optional[str] = None) -> List[MetricsBucket]:
        """
        Get all metrics buckets, optionally filtered by configuration.
        
        Args:
            config_name: Optional configuration name to filter by
            
        Returns:
            List of MetricsBucket objects
        """
        with self._metrics_lock:
            if config_name:
                return [b for b in self._completed_buckets if b.config_name == config_name]
            return self._completed_buckets.copy()
    
    def get_summary_stats(self, config_name: str, window_minutes: int = 10) -> Dict[str, Any]:
        """
        Get summary statistics for a configuration over a time window.
        
        Args:
            config_name: Configuration name
            window_minutes: Time window in minutes
            
        Returns:
            Dictionary with summary statistics
        """
        cutoff_time = time.time() - (window_minutes * 60)
        cutoff_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(cutoff_time))
        
        with self._metrics_lock:
            recent_buckets = [
                b for b in self._completed_buckets 
                if b.config_name == config_name and b.timestamp >= cutoff_timestamp
            ]
        
        if not recent_buckets:
            return {
                "config_name": config_name,
                "window_minutes": window_minutes,
                "bucket_count": 0,
                "total_responses": 0,
                "avg_p95_ms": 0.0,
                "avg_recall_at_10": 0.0,
                "total_slo_violations": 0,
                "slo_violation_rate": 0.0
            }
        
        total_responses = sum(b.response_count for b in recent_buckets)
        total_slo_violations = sum(b.slo_violations for b in recent_buckets)
        
        p95_values = [b.p95_ms for b in recent_buckets if b.response_count > 0]
        recall_values = [b.recall_at_10 for b in recent_buckets if b.response_count > 0]
        
        return {
            "config_name": config_name,
            "window_minutes": window_minutes,
            "bucket_count": len(recent_buckets),
            "total_responses": total_responses,
            "avg_p95_ms": statistics.mean(p95_values) if p95_values else 0.0,
            "avg_recall_at_10": statistics.mean(recall_values) if recall_values else 0.0,
            "total_slo_violations": total_slo_violations,
            "slo_violation_rate": total_slo_violations / total_responses if total_responses > 0 else 0.0
        }
    
    def export_buckets_to_json(self, output_file: str, config_name: Optional[str] = None) -> None:
        """
        Export metrics buckets to a JSON file.
        
        Args:
            output_file: Output file path
            config_name: Optional configuration name to filter by
        """
        buckets = self.get_all_buckets(config_name)
        
        export_data = {
            "export_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bucket_duration_sec": self.bucket_duration_sec,
            "total_buckets": len(buckets),
            "buckets": [asdict(bucket) for bucket in buckets]
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Exported {len(buckets)} buckets to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export buckets to {output_file}: {e}")
            raise
    
    def reset(self) -> None:
        """Reset all collected metrics."""
        with self._metrics_lock:
            self._current_buckets.clear()
            self._completed_buckets.clear()
            self._start_time = time.time()
        
        logger.info("Metrics collector reset")


# Global metrics collector instance
_global_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


def record_search_metrics(trace_id: str, latency_ms: float, recall_at_10: float, 
                         config_name: str, slo_p95_ms: float) -> None:
    """Record metrics for a search request using the global collector."""
    collector = get_metrics_collector()
    collector.record_search(trace_id, latency_ms, recall_at_10, config_name, slo_p95_ms)


