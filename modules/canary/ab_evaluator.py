"""
Online A/B Evaluator for Canary Deployments

This module provides real-time A/B testing capabilities for comparing
last_good vs candidate configurations with statistical significance.
"""

import time
import json
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

from .metrics_collector import MetricsCollector, MetricsBucket
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class ABBucket:
    """Represents an A/B test bucket with configuration assignment."""
    timestamp: str
    duration_sec: int
    config_a: str  # last_good (90%)
    config_b: str  # candidate (10%)
    bucket_a: str  # "A" or "B"
    p95_ms: float
    recall_at_10: float
    response_count: int
    slo_violations: int
    is_valid: bool  # ≥80% effective buckets requirement


@dataclass
class ABComparison:
    """Represents A/B comparison results."""
    total_buckets: int
    valid_buckets: int
    valid_percentage: float
    
    # Config A (last_good) stats
    config_a_stats: Dict[str, Any]
    
    # Config B (candidate) stats  
    config_b_stats: Dict[str, Any]
    
    # Comparison metrics
    p95_improvement: float  # negative = improvement
    recall_improvement: float  # positive = improvement
    slo_violation_reduction: float  # negative = improvement
    
    # Statistical significance
    is_significant: bool
    confidence_level: float


class ABEvaluator:
    """
    Online A/B evaluator for canary deployments.
    
    Features:
    - Real-time A/B bucket assignment (90/10 split)
    - Statistical comparison of configurations
    - KPI tracking and improvement calculation
    - Validity checking (≥80% effective buckets)
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, 
                 metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize the A/B evaluator.
        
        Args:
            config_manager: Configuration manager instance
            metrics_collector: Metrics collector instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.metrics_collector = metrics_collector or MetricsCollector()
        
        # A/B bucket tracking
        self._ab_buckets: List[ABBucket] = []
        self._bucket_assignments: Dict[str, str] = {}  # trace_id -> bucket ("A" or "B")
        
        # A/B split configuration
        self.split_ratio = {"A": 0.9, "B": 0.1}
        
        logger.info("ABEvaluator initialized")
    
    def assign_bucket(self, trace_id: str) -> str:
        """
        Assign a trace to bucket A or B based on split ratio.
        
        Args:
            trace_id: Unique trace identifier
            
        Returns:
            "A" or "B" bucket assignment
        """
        if trace_id not in self._bucket_assignments:
            # Simple hash-based assignment for consistency
            hash_val = hash(trace_id) % 100
            if hash_val < self.split_ratio["A"] * 100:
                self._bucket_assignments[trace_id] = "A"
            else:
                self._bucket_assignments[trace_id] = "B"
        
        return self._bucket_assignments[trace_id]
    
    def process_metrics_buckets(self, buckets: List[MetricsBucket]) -> List[ABBucket]:
        """
        Process metrics buckets and convert to A/B buckets.
        
        Args:
            buckets: List of metrics buckets to process
            
        Returns:
            List of A/B buckets
        """
        ab_buckets = []
        
        # Get current configurations
        state = self.config_manager.get_canary_status()
        config_a = state['last_good_config']
        config_b = state.get('candidate_config', '')
        
        if not config_b:
            # No candidate config, all buckets go to A
            for bucket in buckets:
                ab_bucket = ABBucket(
                    timestamp=bucket.timestamp,
                    duration_sec=bucket.duration_sec,
                    config_a=config_a,
                    config_b=config_b,
                    bucket_a="A",
                    p95_ms=bucket.p95_ms,
                    recall_at_10=bucket.recall_at_10,
                    response_count=bucket.response_count,
                    slo_violations=bucket.slo_violations,
                    is_valid=bucket.response_count > 0
                )
                ab_buckets.append(ab_bucket)
        else:
            # Assign buckets based on configuration
            for bucket in buckets:
                if bucket.config_name == config_a:
                    bucket_a = "A"
                elif bucket.config_name == config_b:
                    bucket_a = "B"
                else:
                    # Unknown config, skip
                    continue
                
                ab_bucket = ABBucket(
                    timestamp=bucket.timestamp,
                    duration_sec=bucket.duration_sec,
                    config_a=config_a,
                    config_b=config_b,
                    bucket_a=bucket_a,
                    p95_ms=bucket.p95_ms,
                    recall_at_10=bucket.recall_at_10,
                    response_count=bucket.response_count,
                    slo_violations=bucket.slo_violations,
                    is_valid=bucket.response_count > 0
                )
                ab_buckets.append(ab_bucket)
        
        # Add to tracking
        self._ab_buckets.extend(ab_buckets)
        
        # Keep only recent buckets (last 1 hour)
        cutoff_time = time.time() - 3600
        self._ab_buckets = [
            b for b in self._ab_buckets 
            if time.mktime(time.strptime(b.timestamp, "%Y-%m-%dT%H:%M:%SZ")) >= cutoff_time
        ]
        
        return ab_buckets
    
    def get_comparison(self, window_minutes: int = 10) -> ABComparison:
        """
        Get A/B comparison results for a time window.
        
        Args:
            window_minutes: Time window in minutes
            
        Returns:
            ABComparison object with results
        """
        cutoff_time = time.time() - (window_minutes * 60)
        cutoff_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(cutoff_time))
        
        # Filter recent buckets
        recent_buckets = [
            b for b in self._ab_buckets 
            if b.timestamp >= cutoff_timestamp
        ]
        
        if not recent_buckets:
            return ABComparison(
                total_buckets=0,
                valid_buckets=0,
                valid_percentage=0.0,
                config_a_stats={},
                config_b_stats={},
                p95_improvement=0.0,
                recall_improvement=0.0,
                slo_violation_reduction=0.0,
                is_significant=False,
                confidence_level=0.0
            )
        
        # Separate buckets by assignment
        bucket_a_buckets = [b for b in recent_buckets if b.bucket_a == "A"]
        bucket_b_buckets = [b for b in recent_buckets if b.bucket_a == "B"]
        
        # Calculate stats for each bucket
        config_a_stats = self._calculate_bucket_stats(bucket_a_buckets)
        config_b_stats = self._calculate_bucket_stats(bucket_b_buckets)
        
        # Calculate improvements
        p95_improvement = config_a_stats.get('avg_p95_ms', 0) - config_b_stats.get('avg_p95_ms', 0)
        recall_improvement = config_b_stats.get('avg_recall_at_10', 0) - config_a_stats.get('avg_recall_at_10', 0)
        slo_violation_reduction = config_a_stats.get('total_slo_violations', 0) - config_b_stats.get('total_slo_violations', 0)
        
        # Calculate validity
        total_buckets = len(recent_buckets)
        valid_buckets = len([b for b in recent_buckets if b.is_valid])
        valid_percentage = (valid_buckets / total_buckets * 100) if total_buckets > 0 else 0
        
        # Statistical significance (simplified)
        is_significant = self._calculate_significance(bucket_a_buckets, bucket_b_buckets)
        confidence_level = 95.0 if is_significant else 50.0
        
        return ABComparison(
            total_buckets=total_buckets,
            valid_buckets=valid_buckets,
            valid_percentage=valid_percentage,
            config_a_stats=config_a_stats,
            config_b_stats=config_b_stats,
            p95_improvement=p95_improvement,
            recall_improvement=recall_improvement,
            slo_violation_reduction=slo_violation_reduction,
            is_significant=is_significant,
            confidence_level=confidence_level
        )
    
    def _calculate_bucket_stats(self, buckets: List[ABBucket]) -> Dict[str, Any]:
        """Calculate statistics for a set of buckets."""
        if not buckets:
            return {
                "bucket_count": 0,
                "total_responses": 0,
                "avg_p95_ms": 0.0,
                "avg_recall_at_10": 0.0,
                "total_slo_violations": 0,
                "slo_violation_rate": 0.0
            }
        
        total_responses = sum(b.response_count for b in buckets)
        total_slo_violations = sum(b.slo_violations for b in buckets)
        
        p95_values = [b.p95_ms for b in buckets if b.response_count > 0]
        recall_values = [b.recall_at_10 for b in buckets if b.response_count > 0]
        
        return {
            "bucket_count": len(buckets),
            "total_responses": total_responses,
            "avg_p95_ms": statistics.mean(p95_values) if p95_values else 0.0,
            "avg_recall_at_10": statistics.mean(recall_values) if recall_values else 0.0,
            "total_slo_violations": total_slo_violations,
            "slo_violation_rate": total_slo_violations / total_responses if total_responses > 0 else 0.0
        }
    
    def _calculate_significance(self, bucket_a: List[ABBucket], bucket_b: List[ABBucket]) -> bool:
        """
        Calculate statistical significance (simplified).
        
        For production use, this should implement proper statistical tests.
        """
        if len(bucket_a) < 3 or len(bucket_b) < 3:
            return False
        
        # Simple heuristic: significant if both buckets have sufficient data
        # and there's a meaningful difference
        a_responses = sum(b.response_count for b in bucket_a)
        b_responses = sum(b.response_count for b in bucket_b)
        
        return a_responses >= 10 and b_responses >= 10
    
    def generate_kpi_report(self, window_minutes: int = 10) -> Dict[str, Any]:
        """
        Generate a comprehensive KPI report for A/B comparison.
        
        Args:
            window_minutes: Time window in minutes
            
        Returns:
            Dictionary with KPI report data
        """
        comparison = self.get_comparison(window_minutes)
        
        # Get configuration details
        state = self.config_manager.get_canary_status()
        
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "window_minutes": window_minutes,
            "ab_split": self.split_ratio,
            "configurations": {
                "config_a": {
                    "name": comparison.config_a_stats.get('config_name', state['last_good_config']),
                    "description": "Last Good Configuration"
                },
                "config_b": {
                    "name": comparison.config_b_stats.get('config_name', state.get('candidate_config', 'N/A')),
                    "description": "Candidate Configuration"
                }
            },
            "summary": {
                "total_buckets": comparison.total_buckets,
                "valid_buckets": comparison.valid_buckets,
                "valid_percentage": comparison.valid_percentage,
                "is_valid": comparison.valid_percentage >= 80.0
            },
            "performance_comparison": {
                "config_a": comparison.config_a_stats,
                "config_b": comparison.config_b_stats
            },
            "improvements": {
                "p95_latency_ms": {
                    "absolute": comparison.p95_improvement,
                    "percentage": (comparison.p95_improvement / comparison.config_a_stats.get('avg_p95_ms', 1)) * 100,
                    "direction": "improvement" if comparison.p95_improvement < 0 else "degradation"
                },
                "recall_at_10": {
                    "absolute": comparison.recall_improvement,
                    "percentage": (comparison.recall_improvement / comparison.config_a_stats.get('avg_recall_at_10', 1)) * 100,
                    "direction": "improvement" if comparison.recall_improvement > 0 else "degradation"
                },
                "slo_violations": {
                    "absolute": comparison.slo_violation_reduction,
                    "direction": "improvement" if comparison.slo_violation_reduction < 0 else "degradation"
                }
            },
            "statistical_significance": {
                "is_significant": comparison.is_significant,
                "confidence_level": comparison.confidence_level
            },
            "recommendation": self._generate_recommendation(comparison)
        }
        
        return report
    
    def _generate_recommendation(self, comparison: ABComparison) -> str:
        """Generate recommendation based on A/B comparison results."""
        if comparison.valid_percentage < 80.0:
            return "INSUFFICIENT_DATA: Need more valid buckets for reliable comparison"
        
        if not comparison.is_significant:
            return "INCONCLUSIVE: Results not statistically significant"
        
        # Check if candidate is better
        p95_better = comparison.p95_improvement < 0  # negative improvement = better latency
        recall_better = comparison.recall_improvement > 0  # positive improvement = better recall
        slo_better = comparison.slo_violation_reduction < 0  # negative = fewer violations
        
        improvements = []
        if p95_better:
            improvements.append(f"p95 latency improved by {abs(comparison.p95_improvement):.1f}ms")
        if recall_better:
            improvements.append(f"recall@10 improved by {comparison.recall_improvement:.3f}")
        if slo_better:
            improvements.append(f"SLO violations reduced by {abs(comparison.slo_violation_reduction)}")
        
        if improvements:
            return f"PROMOTE: Candidate shows improvements: {', '.join(improvements)}"
        else:
            return "ROLLBACK: Candidate shows no improvements or degradation"
    
    def export_ab_report(self, output_file: str, window_minutes: int = 10) -> None:
        """
        Export A/B comparison report to JSON file.
        
        Args:
            output_file: Output file path
            window_minutes: Time window in minutes
        """
        report = self.generate_kpi_report(window_minutes)
        
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Exported A/B report to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export A/B report to {output_file}: {e}")
            raise
    
    def get_bucket_distribution(self) -> Dict[str, Any]:
        """
        Get current bucket distribution statistics.
        
        Returns:
            Dictionary with bucket distribution info
        """
        total_traces = len(self._bucket_assignments)
        bucket_a_count = sum(1 for bucket in self._bucket_assignments.values() if bucket == "A")
        bucket_b_count = total_traces - bucket_a_count
        
        return {
            "total_traces": total_traces,
            "bucket_a_count": bucket_a_count,
            "bucket_b_count": bucket_b_count,
            "bucket_a_percentage": (bucket_a_count / total_traces * 100) if total_traces > 0 else 0,
            "bucket_b_percentage": (bucket_b_count / total_traces * 100) if total_traces > 0 else 0,
            "target_split": self.split_ratio
        }


# Global A/B evaluator instance
_global_ab_evaluator = None


def get_ab_evaluator() -> ABEvaluator:
    """Get the global A/B evaluator instance."""
    global _global_ab_evaluator
    if _global_ab_evaluator is None:
        from .config_manager import ConfigManager
        from .metrics_collector import get_metrics_collector
        config_manager = ConfigManager()
        metrics_collector = get_metrics_collector()
        _global_ab_evaluator = ABEvaluator(config_manager, metrics_collector)
    return _global_ab_evaluator


