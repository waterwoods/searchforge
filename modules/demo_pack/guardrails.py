"""
Demo Pack Guardrails

Implements PASS/FAIL gating logic for demo pack results validation.
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import warnings

class GuardrailStatus(Enum):
    """Guardrail status enumeration."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    UNKNOWN = "UNKNOWN"

@dataclass
class GuardrailResult:
    """Result of a guardrail check."""
    status: GuardrailStatus
    message: str
    details: Dict[str, Any]
    criteria_met: bool

@dataclass
class GuardrailCriteria:
    """Guardrail criteria configuration."""
    delta_p95_positive: bool = True
    p_value_significant: float = 0.05
    recall_acceptable: float = -0.01
    safety_rate_min: float = 0.99
    apply_rate_min: float = 0.95
    insufficient_buckets_threshold: int = 10
    insufficient_duration_threshold: int = 300

class DemoPackGuardrails:
    """Guardrails system for demo pack validation."""
    
    def __init__(self, criteria: Optional[GuardrailCriteria] = None):
        self.criteria = criteria or GuardrailCriteria()
        self.warnings: List[str] = []
    
    def evaluate_scenario(self, comparison_data: Dict[str, Any], 
                         run_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a scenario against all guardrails.
        
        Args:
            comparison_data: Scenario comparison metrics
            run_params: Run parameters (duration, buckets, etc.)
            
        Returns:
            Dictionary with guardrail results and overall status
        """
        self.warnings.clear()
        
        # Extract metrics
        delta_p95 = comparison_data.get("delta_p95_ms", 0)
        p_value = comparison_data.get("p_value", 1.0)
        delta_recall = comparison_data.get("delta_recall", 0)
        safety_rate = comparison_data.get("safety_rate", 0.99)  # Default
        apply_rate = comparison_data.get("apply_rate", 0.95)    # Default
        
        # Check each criterion
        results = {
            "delta_p95_check": self._check_delta_p95(delta_p95),
            "p_value_check": self._check_p_value(p_value),
            "recall_check": self._check_recall(delta_recall),
            "safety_check": self._check_safety(safety_rate),
            "apply_rate_check": self._check_apply_rate(apply_rate)
        }
        
        # Check run parameters for warnings
        param_warnings = self._check_run_parameters(run_params)
        self.warnings.extend(param_warnings)
        
        # Determine overall status
        overall_status = self._determine_overall_status(results)
        
        # Calculate pass/fail criteria summary
        criteria_summary = {
            "delta_p95_positive": results["delta_p95_check"].criteria_met,
            "p_value_significant": results["p_value_check"].criteria_met,
            "recall_acceptable": results["recall_check"].criteria_met,
            "safety_rate": results["safety_check"].criteria_met,
            "apply_rate": results["apply_rate_check"].criteria_met
        }
        
        return {
            "overall_status": overall_status.value,
            "overall_pass": overall_status == GuardrailStatus.PASS,
            "criteria_summary": criteria_summary,
            "detailed_results": {k: v.__dict__ for k, v in results.items()},
            "warnings": self.warnings,
            "color": self._get_status_color(overall_status)
        }
    
    def _check_delta_p95(self, delta_p95: float) -> GuardrailResult:
        """Check if delta P95 is positive (multi-knob better)."""
        if self.criteria.delta_p95_positive:
            criteria_met = delta_p95 > 0
            if criteria_met:
                return GuardrailResult(
                    status=GuardrailStatus.PASS,
                    message=f"ΔP95 is positive: {delta_p95:.2f} ms (multi-knob better)",
                    details={"delta_p95": delta_p95, "threshold": 0},
                    criteria_met=True
                )
            else:
                return GuardrailResult(
                    status=GuardrailStatus.FAIL,
                    message=f"ΔP95 is negative: {delta_p95:.2f} ms (single-knob better)",
                    details={"delta_p95": delta_p95, "threshold": 0},
                    criteria_met=False
                )
        else:
            return GuardrailResult(
                status=GuardrailStatus.PASS,
                message="ΔP95 check disabled",
                details={"delta_p95": delta_p95},
                criteria_met=True
            )
    
    def _check_p_value(self, p_value: float) -> GuardrailResult:
        """Check if p-value is statistically significant."""
        if p_value is None:
            return GuardrailResult(
                status=GuardrailStatus.UNKNOWN,
                message="P-value not available",
                details={"p_value": None},
                criteria_met=False
            )
        
        criteria_met = p_value < self.criteria.p_value_significant
        if criteria_met:
            return GuardrailResult(
                status=GuardrailStatus.PASS,
                message=f"P-value is significant: {p_value:.3f} < {self.criteria.p_value_significant}",
                details={"p_value": p_value, "threshold": self.criteria.p_value_significant},
                criteria_met=True
            )
        else:
            return GuardrailResult(
                status=GuardrailStatus.FAIL,
                message=f"P-value is not significant: {p_value:.3f} ≥ {self.criteria.p_value_significant}",
                details={"p_value": p_value, "threshold": self.criteria.p_value_significant},
                criteria_met=False
            )
    
    def _check_recall(self, delta_recall: float) -> GuardrailResult:
        """Check if recall drop is acceptable."""
        criteria_met = delta_recall >= self.criteria.recall_acceptable
        if criteria_met:
            return GuardrailResult(
                status=GuardrailStatus.PASS,
                message=f"Recall drop acceptable: {delta_recall:.3f} ≥ {self.criteria.recall_acceptable}",
                details={"delta_recall": delta_recall, "threshold": self.criteria.recall_acceptable},
                criteria_met=True
            )
        else:
            return GuardrailResult(
                status=GuardrailStatus.FAIL,
                message=f"Recall drop too large: {delta_recall:.3f} < {self.criteria.recall_acceptable}",
                details={"delta_recall": delta_recall, "threshold": self.criteria.recall_acceptable},
                criteria_met=False
            )
    
    def _check_safety(self, safety_rate: float) -> GuardrailResult:
        """Check if safety rate is above minimum threshold."""
        criteria_met = safety_rate >= self.criteria.safety_rate_min
        if criteria_met:
            return GuardrailResult(
                status=GuardrailStatus.PASS,
                message=f"Safety rate acceptable: {safety_rate:.3f} ≥ {self.criteria.safety_rate_min}",
                details={"safety_rate": safety_rate, "threshold": self.criteria.safety_rate_min},
                criteria_met=True
            )
        else:
            return GuardrailResult(
                status=GuardrailStatus.FAIL,
                message=f"Safety rate too low: {safety_rate:.3f} < {self.criteria.safety_rate_min}",
                details={"safety_rate": safety_rate, "threshold": self.criteria.safety_rate_min},
                criteria_met=False
            )
    
    def _check_apply_rate(self, apply_rate: float) -> GuardrailResult:
        """Check if apply rate is above minimum threshold."""
        criteria_met = apply_rate >= self.criteria.apply_rate_min
        if criteria_met:
            return GuardrailResult(
                status=GuardrailStatus.PASS,
                message=f"Apply rate acceptable: {apply_rate:.3f} ≥ {self.criteria.apply_rate_min}",
                details={"apply_rate": apply_rate, "threshold": self.criteria.apply_rate_min},
                criteria_met=True
            )
        else:
            return GuardrailResult(
                status=GuardrailStatus.FAIL,
                message=f"Apply rate too low: {apply_rate:.3f} < {self.criteria.apply_rate_min}",
                details={"apply_rate": apply_rate, "threshold": self.criteria.apply_rate_min},
                criteria_met=False
            )
    
    def _check_run_parameters(self, run_params: Dict[str, Any]) -> List[str]:
        """Check run parameters for warnings."""
        warnings = []
        
        # Check duration
        duration = run_params.get("duration_sec", 0)
        if duration < self.criteria.insufficient_duration_threshold:
            warnings.append(
                f"Duration too short: {duration}s < {self.criteria.insufficient_duration_threshold}s. "
                "Consider longer runs for more reliable results."
            )
        
        # Check buckets
        buckets = run_params.get("buckets_generated", 0)
        if buckets < self.criteria.insufficient_buckets_threshold:
            warnings.append(
                f"Insufficient buckets: {buckets} < {self.criteria.insufficient_buckets_threshold}. "
                "Consider longer runs or higher QPS for better statistical power."
            )
        
        # Check QPS
        qps = run_params.get("qps", 0)
        if qps < 5:
            warnings.append(
                f"Low QPS: {qps}. Consider higher QPS for more responsive tuning."
            )
        
        return warnings
    
    def _determine_overall_status(self, results: Dict[str, GuardrailResult]) -> GuardrailStatus:
        """Determine overall guardrail status from individual results."""
        # Count failures and warnings
        failures = 0
        warnings = 0
        
        for result in results.values():
            if result.status == GuardrailStatus.FAIL:
                failures += 1
            elif result.status == GuardrailStatus.WARNING:
                warnings += 1
        
        # Determine overall status
        if failures > 0:
            return GuardrailStatus.FAIL
        elif warnings > 0 or self.warnings:
            return GuardrailStatus.WARNING
        else:
            return GuardrailStatus.PASS
    
    def _get_status_color(self, status: GuardrailStatus) -> str:
        """Get CSS color class for status."""
        color_map = {
            GuardrailStatus.PASS: "pass",
            GuardrailStatus.FAIL: "fail",
            GuardrailStatus.WARNING: "warning",
            GuardrailStatus.UNKNOWN: "info"
        }
        return color_map.get(status, "info")
    
    def get_recommendations(self, evaluation_result: Dict[str, Any]) -> List[str]:
        """Get recommendations based on guardrail evaluation."""
        recommendations = []
        
        detailed_results = evaluation_result.get("detailed_results", {})
        warnings = evaluation_result.get("warnings", [])
        
        # Add recommendations based on failures
        for check_name, result in detailed_results.items():
            if not result.get("criteria_met", False):
                if check_name == "delta_p95_check":
                    recommendations.append(
                        "Multi-knob tuning is not improving latency. Consider adjusting parameter ranges or tuning strategy."
                    )
                elif check_name == "p_value_check":
                    recommendations.append(
                        "Results are not statistically significant. Increase experiment duration or QPS for better power."
                    )
                elif check_name == "recall_check":
                    recommendations.append(
                        "Recall is dropping too much. Consider adjusting recall-related parameters or SLO thresholds."
                    )
                elif check_name == "safety_check":
                    recommendations.append(
                        "Safety rate is too low. Review parameter bounds and safety mechanisms."
                    )
                elif check_name == "apply_rate_check":
                    recommendations.append(
                        "Apply rate is too low. Check cooldown periods and guard conditions."
                    )
        
        # Add recommendations based on warnings
        for warning in warnings:
            if "Duration too short" in warning:
                recommendations.append("Increase experiment duration for more reliable results.")
            elif "Insufficient buckets" in warning:
                recommendations.append("Increase experiment duration or QPS for better statistical power.")
            elif "Low QPS" in warning:
                recommendations.append("Consider higher QPS for more responsive tuning behavior.")
        
        return recommendations

# Default guardrails instance
default_guardrails = DemoPackGuardrails()

def evaluate_scenario_guardrails(comparison_data: Dict[str, Any], 
                                run_params: Dict[str, Any],
                                criteria: Optional[GuardrailCriteria] = None) -> Dict[str, Any]:
    """
    Convenience function to evaluate scenario guardrails.
    
    Args:
        comparison_data: Scenario comparison metrics
        run_params: Run parameters
        criteria: Optional custom criteria
        
    Returns:
        Guardrail evaluation result
    """
    guardrails = DemoPackGuardrails(criteria)
    result = guardrails.evaluate_scenario(comparison_data, run_params)
    result["recommendations"] = guardrails.get_recommendations(result)
    return result
