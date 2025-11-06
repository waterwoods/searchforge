"""
Decision Policy - Pass/Edge/Fail rules for experiment results
=============================================================
Implements decision logic based on ΔP95, error rate, and balance checks.

Rules:
- PASS: ΔP95 ≤ -10% AND error_rate < 1%
- EDGE: ΔP95 in (-10%, -5%] AND error_rate < 1%
- FAIL: Otherwise
"""

from typing import Dict, Any, Literal
from dataclasses import dataclass


@dataclass
class DecisionThresholds:
    """Configurable thresholds for decision making."""
    
    # P95 improvement thresholds (negative = improvement)
    pass_delta_p95_max: float = -10.0  # Must improve by ≥10%
    edge_delta_p95_max: float = -5.0   # Edge case: 5-10% improvement
    
    # Error rate threshold
    max_error_rate: float = 1.0  # <1% errors required
    
    # AB balance warning threshold
    ab_balance_warn: float = 5.0  # Warn if imbalance >5%
    
    # QPS change thresholds (informational)
    qps_drop_warn: float = -20.0  # Warn if QPS drops >20%


Decision = Literal["pass", "edge", "fail"]


class DecisionEngine:
    """Decision engine for experiment verdicts."""
    
    def __init__(self, thresholds: DecisionThresholds = None):
        self.thresholds = thresholds or DecisionThresholds()
    
    def decide(self, metrics: Dict[str, float], ab_imbalance: float = None) -> Dict[str, Any]:
        """
        Make decision based on experiment metrics.
        决策引擎：根据阈值判断 PASS/EDGE/FAIL
        
        Args:
            metrics: Parsed metrics (delta_p95_pct, delta_qps_pct, error_rate_pct)
            ab_imbalance: A/B sample imbalance percentage (0-50)
        
        Returns:
            {
                "verdict": "pass" | "edge" | "fail",
                "reason": str,
                "apply_flags": bool,
                "warnings": list[str],
                "summary": str
            }
        """
        delta_p95 = metrics["delta_p95_pct"]
        delta_qps = metrics["delta_qps_pct"]
        error_rate = metrics["error_rate_pct"]
        
        warnings = []
        
        # Check AB balance
        if ab_imbalance is not None and ab_imbalance > self.thresholds.ab_balance_warn:
            warnings.append(f"AB imbalance: {ab_imbalance:.1f}% (>{self.thresholds.ab_balance_warn}%)")
        
        # Check QPS drop
        if delta_qps < self.thresholds.qps_drop_warn:
            warnings.append(f"QPS drop: {delta_qps:.1f}% (<{self.thresholds.qps_drop_warn}%)")
        
        # Check error rate
        if error_rate >= self.thresholds.max_error_rate:
            return {
                "verdict": "fail",
                "reason": f"Error rate too high: {error_rate:.2f}% (≥{self.thresholds.max_error_rate}%)",
                "apply_flags": False,
                "warnings": warnings,
                "summary": f"FAIL: Error rate {error_rate:.2f}% exceeds {self.thresholds.max_error_rate}%"
            }
        
        # Decision based on ΔP95
        if delta_p95 <= self.thresholds.pass_delta_p95_max:
            # PASS: Strong improvement
            return {
                "verdict": "pass",
                "reason": f"P95 improved by {abs(delta_p95):.1f}% (≥{abs(self.thresholds.pass_delta_p95_max)}%)",
                "apply_flags": True,
                "warnings": warnings,
                "summary": f"PASS: ΔP95 {delta_p95:+.1f}% (err {error_rate:.2f}%)"
            }
        
        elif delta_p95 <= self.thresholds.edge_delta_p95_max:
            # EDGE: Moderate improvement
            return {
                "verdict": "edge",
                "reason": f"P95 improved by {abs(delta_p95):.1f}% (5-10% range)",
                "apply_flags": False,
                "warnings": warnings,
                "summary": f"EDGE: ΔP95 {delta_p95:+.1f}% in ({self.thresholds.pass_delta_p95_max}, {self.thresholds.edge_delta_p95_max}]"
            }
        
        else:
            # FAIL: Insufficient improvement or regression
            if delta_p95 > 0:
                reason = f"P95 regressed by {delta_p95:.1f}%"
            else:
                reason = f"P95 improvement {abs(delta_p95):.1f}% below threshold ({abs(self.thresholds.edge_delta_p95_max)}%)"
            
            return {
                "verdict": "fail",
                "reason": reason,
                "apply_flags": False,
                "warnings": warnings,
                "summary": f"FAIL: ΔP95 {delta_p95:+.1f}% (threshold: {self.thresholds.edge_delta_p95_max}%)"
            }
    
    def generate_rollback_command(self, config: Dict[str, Any]) -> str:
        """
        Generate rollback command for flags.
        
        Args:
            config: Experiment configuration
        
        Returns:
            curl command to rollback flags
        """
        # Extract baseline configuration
        flow_policy = config.get("flow_policy", "aimd")
        
        rollback = {
            "control": {
                "policy": flow_policy,
                "enabled_actuators": []  # Disable control
            },
            "routing": {
                "enabled": False,
                "manual_backend": "qdrant"  # Force Qdrant
            }
        }
        
        import json
        cmd = f"""curl -X POST http://localhost:8011/ops/flags \\
  -H 'Content-Type: application/json' \\
  -d '{json.dumps(rollback)}'"""
        
        return cmd

