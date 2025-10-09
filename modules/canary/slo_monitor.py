"""
SLO Monitor for Canary Deployments

This module monitors SLO violations and triggers automatic rollbacks
when canary deployments fail to meet service level objectives.
"""

import time
import json
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from collections import defaultdict, deque
import logging

from .metrics_collector import MetricsCollector, MetricsBucket
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class SLORule:
    """Represents an SLO rule with thresholds and conditions."""
    name: str
    metric: str  # "p95_ms", "recall_at_10", "slo_violations"
    operator: str  # "le", "ge", "lt", "gt", "eq"
    threshold: float
    consecutive_buckets: int  # Number of consecutive buckets that must fail


@dataclass
class SLOViolation:
    """Represents an SLO violation event."""
    timestamp: str
    rule_name: str
    metric_value: float
    threshold: float
    config_name: str
    consecutive_failures: int
    action_taken: str


class SLOMonitor:
    """
    Monitors SLO violations and triggers rollbacks.
    
    Features:
    - Configurable SLO rules
    - Monitors consecutive bucket failures
    - Automatic rollback on violation
    - Violation history tracking
    - Callback support for custom actions
    """
    
    def __init__(self, config_manager: ConfigManager, metrics_collector: MetricsCollector):
        """
        Initialize the SLO monitor.
        
        Args:
            config_manager: Configuration manager instance
            metrics_collector: Metrics collector instance
        """
        self.config_manager = config_manager
        self.metrics_collector = metrics_collector
        self._violations_lock = threading.Lock()
        self._violations: List[SLOViolation] = []
        self._failure_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Default SLO rules
        self.slo_rules = [
            SLORule(
                name="p95_latency",
                metric="p95_ms",
                operator="le",
                threshold=1200.0,
                consecutive_buckets=2
            ),
            SLORule(
                name="recall_at_10",
                metric="recall_at_10",
                operator="ge",
                threshold=0.30,
                consecutive_buckets=2
            )
        ]
        
        # Callbacks for custom actions
        self._rollback_callback: Optional[Callable[[str], None]] = None
        
        logger.info("SLOMonitor initialized with default rules")
    
    def set_rollback_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set a callback function to be called when a rollback is triggered.
        
        Args:
            callback: Function that takes a reason string as argument
        """
        self._rollback_callback = callback
    
    def add_slo_rule(self, rule: SLORule) -> None:
        """
        Add an SLO rule to monitor.
        
        Args:
            rule: SLO rule to add
        """
        self.slo_rules.append(rule)
        logger.info(f"Added SLO rule: {rule.name} ({rule.metric} {rule.operator} {rule.threshold})")
    
    def remove_slo_rule(self, rule_name: str) -> bool:
        """
        Remove an SLO rule by name.
        
        Args:
            rule_name: Name of the rule to remove
            
        Returns:
            True if rule was found and removed, False otherwise
        """
        for i, rule in enumerate(self.slo_rules):
            if rule.name == rule_name:
                del self.slo_rules[i]
                logger.info(f"Removed SLO rule: {rule_name}")
                return True
        return False
    
    def check_slo_violations(self, bucket: MetricsBucket) -> List[SLOViolation]:
        """
        Check a metrics bucket against SLO rules.
        
        Args:
            bucket: Metrics bucket to check
            
        Returns:
            List of SLO violations found
        """
        violations = []
        
        for rule in self.slo_rules:
            # Get metric value from bucket
            if rule.metric == "p95_ms":
                metric_value = bucket.p95_ms
            elif rule.metric == "recall_at_10":
                metric_value = bucket.recall_at_10
            elif rule.metric == "slo_violations":
                metric_value = bucket.slo_violations
            else:
                logger.warning(f"Unknown metric '{rule.metric}' in SLO rule '{rule.name}'")
                continue
            
            # Check if rule is violated
            violated = self._check_rule_violation(metric_value, rule.operator, rule.threshold)
            
            if violated:
                # Increment failure count
                self._failure_counts[bucket.config_name][rule.name] += 1
                consecutive_failures = self._failure_counts[bucket.config_name][rule.name]
                
                violation = SLOViolation(
                    timestamp=bucket.timestamp,
                    rule_name=rule.name,
                    metric_value=metric_value,
                    threshold=rule.threshold,
                    config_name=bucket.config_name,
                    consecutive_failures=consecutive_failures,
                    action_taken="none"
                )
                
                violations.append(violation)
                
                logger.warning(f"SLO violation: {rule.name} - {metric_value} {rule.operator} {rule.threshold} "
                             f"(consecutive failures: {consecutive_failures})")
                
                # Check if we should trigger rollback
                if consecutive_failures >= rule.consecutive_buckets:
                    # Handle through strategy manager if available
                    rollback_triggered = self._handle_violation_through_strategy(violation)
                    if rollback_triggered:
                        violation.action_taken = "rollback_triggered"
                    else:
                        violation.action_taken = "alert_sent"
            else:
                # Reset failure count if rule is satisfied
                self._failure_counts[bucket.config_name][rule.name] = 0
        
        return violations
    
    def _check_rule_violation(self, value: float, operator: str, threshold: float) -> bool:
        """Check if a metric value violates an SLO rule."""
        if operator == "le":
            return value > threshold
        elif operator == "ge":
            return value < threshold
        elif operator == "lt":
            return value >= threshold
        elif operator == "gt":
            return value <= threshold
        elif operator == "eq":
            return abs(value - threshold) > 1e-6
        else:
            logger.error(f"Unknown operator '{operator}' in SLO rule")
            return False
    
    def _handle_violation_through_strategy(self, violation: SLOViolation) -> bool:
        """
        Handle SLO violation through strategy manager.
        
        Args:
            violation: SLO violation to handle
            
        Returns:
            True if rollback was triggered, False otherwise
        """
        try:
            from .slo_strategy import get_slo_strategy_manager
            from .audit_logger import get_audit_logger
            
            strategy_manager = get_slo_strategy_manager()
            audit_logger = get_audit_logger()
            
            return strategy_manager.handle_slo_violation(violation, audit_logger)
        except ImportError:
            # Strategy manager not available, fall back to legacy rollback
            self._trigger_rollback(violation)
            return True
        except Exception as e:
            logger.error(f"Failed to handle violation through strategy: {e}")
            # Fall back to legacy rollback
            self._trigger_rollback(violation)
            return True
    
    def _trigger_rollback(self, violation: SLOViolation) -> None:
        """
        Trigger a rollback due to SLO violation.
        
        Args:
            violation: The SLO violation that triggered the rollback
        """
        reason = f"SLO violation: {violation.rule_name} failed for {violation.consecutive_failures} consecutive buckets"
        
        try:
            # Update violation with action taken
            violation.action_taken = "rollback"
            
            # Record violation
            with self._violations_lock:
                self._violations.append(violation)
            
            # Trigger rollback via config manager
            self.config_manager.rollback_candidate(reason)
            
            # Call custom callback if set
            if self._rollback_callback:
                self._rollback_callback(reason)
            
            logger.error(f"Triggered rollback: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to trigger rollback: {e}")
    
    def process_buckets(self, buckets: List[MetricsBucket]) -> List[SLOViolation]:
        """
        Process a list of metrics buckets for SLO violations.
        
        Args:
            buckets: List of metrics buckets to process
            
        Returns:
            List of SLO violations found
        """
        all_violations = []
        
        for bucket in buckets:
            violations = self.check_slo_violations(bucket)
            all_violations.extend(violations)
        
        return all_violations
    
    def get_violations(self, config_name: Optional[str] = None, 
                      rule_name: Optional[str] = None) -> List[SLOViolation]:
        """
        Get SLO violations, optionally filtered.
        
        Args:
            config_name: Optional configuration name to filter by
            rule_name: Optional rule name to filter by
            
        Returns:
            List of SLO violations
        """
        with self._violations_lock:
            violations = self._violations.copy()
        
        if config_name:
            violations = [v for v in violations if v.config_name == config_name]
        
        if rule_name:
            violations = [v for v in violations if v.rule_name == rule_name]
        
        return violations
    
    def get_failure_counts(self) -> Dict[str, Dict[str, int]]:
        """
        Get current failure counts for all configurations and rules.
        
        Returns:
            Dictionary mapping config_name -> rule_name -> failure_count
        """
        return dict(self._failure_counts)
    
    def reset_failure_counts(self, config_name: Optional[str] = None) -> None:
        """
        Reset failure counts for a configuration or all configurations.
        
        Args:
            config_name: Optional configuration name to reset, or None for all
        """
        if config_name:
            if config_name in self._failure_counts:
                self._failure_counts[config_name].clear()
        else:
            self._failure_counts.clear()
        
        logger.info(f"Reset failure counts for {config_name or 'all configurations'}")
    
    def export_violations_to_json(self, output_file: str) -> None:
        """
        Export SLO violations to a JSON file.
        
        Args:
            output_file: Output file path
        """
        violations = self.get_violations()
        
        export_data = {
            "export_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_violations": len(violations),
            "violations": [
                {
                    "timestamp": v.timestamp,
                    "rule_name": v.rule_name,
                    "metric_value": v.metric_value,
                    "threshold": v.threshold,
                    "config_name": v.config_name,
                    "consecutive_failures": v.consecutive_failures,
                    "action_taken": v.action_taken
                }
                for v in violations
            ]
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Exported {len(violations)} violations to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export violations to {output_file}: {e}")
            raise
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status and statistics.
        
        Returns:
            Dictionary with monitoring status
        """
        with self._violations_lock:
            total_violations = len(self._violations)
            recent_violations = len([v for v in self._violations 
                                   if time.time() - time.mktime(time.strptime(v.timestamp, "%Y-%m-%dT%H:%M:%SZ")) < 3600])
        
        return {
            "slo_rules": [
                {
                    "name": rule.name,
                    "metric": rule.metric,
                    "operator": rule.operator,
                    "threshold": rule.threshold,
                    "consecutive_buckets": rule.consecutive_buckets
                }
                for rule in self.slo_rules
            ],
            "failure_counts": dict(self._failure_counts),
            "total_violations": total_violations,
            "recent_violations_1h": recent_violations,
            "monitoring_active": True
        }


# Global SLO monitor instance
_global_slo_monitor: Optional[SLOMonitor] = None


def get_slo_monitor() -> SLOMonitor:
    """Get the global SLO monitor instance."""
    global _global_slo_monitor
    if _global_slo_monitor is None:
        from .config_manager import ConfigManager
        from .metrics_collector import get_metrics_collector
        config_manager = ConfigManager()
        metrics_collector = get_metrics_collector()
        _global_slo_monitor = SLOMonitor(config_manager, metrics_collector)
    return _global_slo_monitor
