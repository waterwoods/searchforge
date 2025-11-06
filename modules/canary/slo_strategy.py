"""
SLO Strategy and Alert Integration for Canary Deployments

This module provides configurable SLO strategies and alert integration
for monitoring canary deployment health.
"""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from .slo_monitor import SLOMonitor, SLORule, SLOViolation
from .audit_logger import AuditLogger, AuditEventType

logger = logging.getLogger(__name__)


@dataclass
class SLOStrategy:
    """Represents an SLO strategy configuration."""
    name: str
    description: str
    rules: List[Dict[str, Any]]
    alert_config: Dict[str, Any]
    rollback_config: Dict[str, Any]
    enabled: bool = True


@dataclass
class AlertConfig:
    """Represents alert configuration."""
    enabled: bool = True
    console_alerts: bool = True
    file_alerts: bool = True
    violations_file: str = "reports/canary/violations.json"
    console_red_text: bool = True


@dataclass
class RollbackConfig:
    """Represents rollback configuration."""
    consecutive_buckets: int = 2
    auto_rollback: bool = True
    rollback_delay_seconds: int = 0
    max_rollbacks_per_hour: int = 5


class SLOStrategyManager:
    """
    Manages SLO strategies and alert integration.
    
    Features:
    - Configurable SLO strategies in JSON format
    - Console and file-based alerts
    - Automatic rollback configuration
    - Strategy persistence and loading
    """
    
    def __init__(self, strategies_dir: str = "configs/slo_strategies"):
        """
        Initialize the SLO strategy manager.
        
        Args:
            strategies_dir: Directory containing SLO strategy files
        """
        self.strategies_dir = Path(strategies_dir)
        self.strategies_dir.mkdir(parents=True, exist_ok=True)
        
        # Default SLO strategy
        self.default_strategy = self._create_default_strategy()
        
        # Current active strategy
        self.active_strategy: Optional[SLOStrategy] = None
        
        # Alert configuration
        self.alert_config = AlertConfig()
        
        # Rollback tracking
        self._rollback_count = 0
        self._last_rollback_time = 0
        
        logger.info(f"SLOStrategyManager initialized with strategies_dir={self.strategies_dir}")
    
    def _create_default_strategy(self) -> SLOStrategy:
        """Create the default SLO strategy."""
        return SLOStrategy(
            name="default_canary_slo",
            description="Default SLO strategy for canary deployments",
            rules=[
                {
                    "name": "p95_latency",
                    "metric": "p95_ms",
                    "operator": "le",
                    "threshold": 1200.0,
                    "consecutive_buckets": 2
                },
                {
                    "name": "recall_at_10",
                    "metric": "recall_at_10",
                    "operator": "ge",
                    "threshold": 0.30,
                    "consecutive_buckets": 2
                }
            ],
            alert_config={
                "enabled": True,
                "console_alerts": True,
                "file_alerts": True,
                "violations_file": "reports/canary/violations.json",
                "console_red_text": True
            },
            rollback_config={
                "consecutive_buckets": 2,
                "auto_rollback": True,
                "rollback_delay_seconds": 0,
                "max_rollbacks_per_hour": 5
            }
        )
    
    def save_strategy(self, strategy: SLOStrategy) -> None:
        """
        Save an SLO strategy to file.
        
        Args:
            strategy: SLO strategy to save
        """
        strategy_file = self.strategies_dir / f"{strategy.name}.json"
        
        strategy_data = asdict(strategy)
        
        try:
            with open(strategy_file, 'w') as f:
                json.dump(strategy_data, f, indent=2)
            logger.info(f"Saved SLO strategy '{strategy.name}' to {strategy_file}")
        except Exception as e:
            logger.error(f"Failed to save SLO strategy '{strategy.name}': {e}")
            raise
    
    def load_strategy(self, strategy_name: str) -> SLOStrategy:
        """
        Load an SLO strategy from file.
        
        Args:
            strategy_name: Name of the strategy to load
            
        Returns:
            SLOStrategy object
            
        Raises:
            FileNotFoundError: If strategy file doesn't exist
        """
        strategy_file = self.strategies_dir / f"{strategy_name}.json"
        
        if not strategy_file.exists():
            raise FileNotFoundError(f"SLO strategy '{strategy_name}' not found in {self.strategies_dir}")
        
        try:
            with open(strategy_file, 'r') as f:
                strategy_data = json.load(f)
            
            return SLOStrategy(**strategy_data)
        except Exception as e:
            logger.error(f"Failed to load SLO strategy '{strategy_name}': {e}")
            raise
    
    def list_strategies(self) -> List[str]:
        """
        List available SLO strategies.
        
        Returns:
            List of strategy names
        """
        strategy_files = list(self.strategies_dir.glob("*.json"))
        return [f.stem for f in strategy_files]
    
    def set_active_strategy(self, strategy_name: str) -> None:
        """
        Set the active SLO strategy.
        
        Args:
            strategy_name: Name of the strategy to activate
        """
        try:
            self.active_strategy = self.load_strategy(strategy_name)
            logger.info(f"Activated SLO strategy: {strategy_name}")
        except FileNotFoundError:
            logger.warning(f"SLO strategy '{strategy_name}' not found, using default")
            self.active_strategy = self.default_strategy
    
    def get_active_strategy(self) -> SLOStrategy:
        """
        Get the currently active SLO strategy.
        
        Returns:
            Active SLO strategy
        """
        if self.active_strategy is None:
            self.active_strategy = self.default_strategy
        return self.active_strategy
    
    def apply_strategy_to_monitor(self, slo_monitor: SLOMonitor) -> None:
        """
        Apply the active strategy to an SLO monitor.
        
        Args:
            slo_monitor: SLO monitor to configure
        """
        strategy = self.get_active_strategy()
        
        # Clear existing rules
        for rule in strategy.rules:
            slo_monitor.remove_slo_rule(rule["name"])
        
        # Add new rules
        for rule_config in strategy.rules:
            rule = SLORule(
                name=rule_config["name"],
                metric=rule_config["metric"],
                operator=rule_config["operator"],
                threshold=rule_config["threshold"],
                consecutive_buckets=rule_config["consecutive_buckets"]
            )
            slo_monitor.add_slo_rule(rule)
        
        logger.info(f"Applied SLO strategy '{strategy.name}' to monitor with {len(strategy.rules)} rules")
    
    def handle_slo_violation(self, violation: SLOViolation, audit_logger: AuditLogger) -> bool:
        """
        Handle an SLO violation according to the active strategy.
        
        Args:
            violation: SLO violation to handle
            audit_logger: Audit logger for recording events
            
        Returns:
            True if rollback was triggered, False otherwise
        """
        strategy = self.get_active_strategy()
        
        # Send alerts
        self._send_alerts(violation, strategy)
        
        # Check if rollback should be triggered
        if self._should_rollback(violation, strategy):
            return self._trigger_rollback(violation, audit_logger, strategy)
        
        return False
    
    def _send_alerts(self, violation: SLOViolation, strategy: SLOStrategy) -> None:
        """Send alerts for an SLO violation."""
        alert_config = strategy.alert_config
        
        if not alert_config.get("enabled", True):
            return
        
        # Console alert with red text
        if alert_config.get("console_alerts", True):
            red_start = "\033[91m" if alert_config.get("console_red_text", True) else ""
            red_end = "\033[0m" if alert_config.get("console_red_text", True) else ""
            
            print(f"{red_start}🚨 SLO VIOLATION ALERT 🚨{red_end}")
            print(f"{red_start}Rule: {violation.rule_name}{red_end}")
            print(f"{red_start}Value: {violation.metric_value} vs Threshold: {violation.threshold}{red_end}")
            print(f"{red_start}Config: {violation.config_name}{red_end}")
            print(f"{red_start}Consecutive Failures: {violation.consecutive_failures}{red_end}")
            print(f"{red_start}Timestamp: {violation.timestamp}{red_end}")
            print()
        
        # File alert
        if alert_config.get("file_alerts", True):
            violations_file = alert_config.get("violations_file", "reports/canary/violations.json")
            self._write_violation_to_file(violation, violations_file)
    
    def _write_violation_to_file(self, violation: SLOViolation, violations_file: str) -> None:
        """Write violation to JSON file."""
        violation_data = {
            "timestamp": violation.timestamp,
            "rule_name": violation.rule_name,
            "metric_value": violation.metric_value,
            "threshold": violation.threshold,
            "config_name": violation.config_name,
            "consecutive_failures": violation.consecutive_failures,
            "action_taken": violation.action_taken
        }
        
        violations_path = Path(violations_file)
        violations_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing violations
        violations = []
        if violations_path.exists():
            try:
                with open(violations_path, 'r') as f:
                    violations = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                violations = []
        
        # Add new violation
        violations.append(violation_data)
        
        # Keep only recent violations (last 100)
        violations = violations[-100:]
        
        # Write back to file
        try:
            with open(violations_path, 'w') as f:
                json.dump(violations, f, indent=2)
            logger.info(f"Wrote SLO violation to {violations_file}")
        except Exception as e:
            logger.error(f"Failed to write violation to {violations_file}: {e}")
    
    def _should_rollback(self, violation: SLOViolation, strategy: SLOStrategy) -> bool:
        """Determine if a rollback should be triggered."""
        rollback_config = strategy.rollback_config
        
        if not rollback_config.get("auto_rollback", True):
            return False
        
        # Check consecutive buckets threshold
        consecutive_threshold = rollback_config.get("consecutive_buckets", 2)
        if violation.consecutive_failures < consecutive_threshold:
            return False
        
        # Check rollback rate limiting
        if self._is_rollback_rate_limited(rollback_config):
            logger.warning("Rollback rate limited, skipping automatic rollback")
            return False
        
        return True
    
    def _is_rollback_rate_limited(self, rollback_config: Dict[str, Any]) -> bool:
        """Check if rollback is rate limited."""
        max_rollbacks = rollback_config.get("max_rollbacks_per_hour", 5)
        if max_rollbacks <= 0:
            return False
        
        current_time = time.time()
        hour_ago = current_time - 3600
        
        # Reset counter if it's been more than an hour
        if current_time - self._last_rollback_time > 3600:
            self._rollback_count = 0
        
        return self._rollback_count >= max_rollbacks
    
    def _trigger_rollback(self, violation: SLOViolation, audit_logger: AuditLogger, 
                         strategy: SLOStrategy) -> bool:
        """Trigger a rollback due to SLO violation."""
        rollback_config = strategy.rollback_config
        
        # Apply rollback delay if configured
        delay_seconds = rollback_config.get("rollback_delay_seconds", 0)
        if delay_seconds > 0:
            logger.info(f"Applying rollback delay of {delay_seconds} seconds")
            time.sleep(delay_seconds)
        
        # Update rollback tracking
        self._rollback_count += 1
        self._last_rollback_time = time.time()
        
        # Log rollback event
        audit_logger.log_canary_rollback(
            deployment_id=f"auto_rollback_{int(time.time())}",
            candidate_config=violation.config_name,
            reason=f"SLO violation: {violation.rule_name} failed for {violation.consecutive_failures} consecutive buckets",
            metrics_summary={},
            user_id="system"
        )
        
        logger.error(f"🚨 AUTOMATIC ROLLBACK TRIGGERED 🚨")
        logger.error(f"Reason: SLO violation in {violation.rule_name}")
        logger.error(f"Config: {violation.config_name}")
        logger.error(f"Consecutive failures: {violation.consecutive_failures}")
        
        return True
    
    def get_violations_summary(self, violations_file: str = "reports/canary/violations.json") -> Dict[str, Any]:
        """
        Get summary of recent SLO violations.
        
        Args:
            violations_file: Path to violations file
            
        Returns:
            Dictionary with violations summary
        """
        violations_path = Path(violations_file)
        
        if not violations_path.exists():
            return {
                "total_violations": 0,
                "recent_violations": 0,
                "rules_violated": [],
                "configs_violated": []
            }
        
        try:
            with open(violations_path, 'r') as f:
                violations = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "total_violations": 0,
                "recent_violations": 0,
                "rules_violated": [],
                "configs_violated": []
            }
        
        # Filter recent violations (last hour)
        cutoff_time = time.time() - 3600
        recent_violations = []
        
        for violation in violations:
            try:
                violation_time = time.mktime(time.strptime(violation["timestamp"], "%Y-%m-%dT%H:%M:%SZ"))
                if violation_time >= cutoff_time:
                    recent_violations.append(violation)
            except (ValueError, KeyError):
                continue
        
        # Extract unique rules and configs
        rules_violated = list(set(v["rule_name"] for v in violations if "rule_name" in v))
        configs_violated = list(set(v["config_name"] for v in violations if "config_name" in v))
        
        return {
            "total_violations": len(violations),
            "recent_violations": len(recent_violations),
            "rules_violated": rules_violated,
            "configs_violated": configs_violated,
            "last_violation": violations[-1]["timestamp"] if violations else None
        }


# Global SLO strategy manager instance
_global_slo_strategy_manager = None


def get_slo_strategy_manager() -> SLOStrategyManager:
    """Get the global SLO strategy manager instance."""
    global _global_slo_strategy_manager
    if _global_slo_strategy_manager is None:
        _global_slo_strategy_manager = SLOStrategyManager()
    return _global_slo_strategy_manager


