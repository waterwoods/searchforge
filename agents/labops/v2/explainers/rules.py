"""
Rule-based Explainer for Agent V2 - No LLM
==========================================
Generates human-readable explanations using template-based rules.

Sources:
- reports/LAB_*_MINI.txt (if available)
- reports/combo_autotune_summary.json (if available)
- Recent state/history_v2.jsonl entries
- Fallback: Deterministic templates based on metrics only
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class RuleBasedExplainer:
    """Rule-based explainer with no LLM dependencies."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "reports"
    
    def explain(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanation bullets from agent result.
        
        Args:
            result: Agent execution result
        
        Returns:
            {
                "bullets": List[str],  # ≤10 bullet points
                "sources": List[str],  # Files used
                "mode": "full" | "template"  # full=with files, template=fallback
            }
        """
        bullets = []
        sources = []
        
        # Extract metrics
        metrics = self._extract_metrics(result)
        if not metrics:
            return self._fallback_template(result)
        
        # Try to load external reports
        lab_reports = self._load_lab_reports()
        combo_summary = self._load_combo_summary()
        
        if lab_reports or combo_summary:
            sources.extend(lab_reports)
            if combo_summary:
                sources.append("combo_autotune_summary.json")
        
        # Generate bullets based on metrics and available data
        bullets = self._generate_bullets(metrics, result, lab_reports, combo_summary)
        
        mode = "full" if sources else "template"
        
        return {
            "bullets": bullets[:10],  # Limit to 10
            "sources": sources,
            "mode": mode
        }
    
    def _extract_metrics(self, result: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Extract core metrics from result."""
        try:
            judgment = result.get("judgment", {})
            if not judgment.get("ok"):
                return None
            
            metrics = judgment.get("metrics", {})
            return {
                "delta_p95_pct": metrics.get("delta_p95_pct", 0.0),
                "delta_qps_pct": metrics.get("delta_qps_pct", 0.0),
                "error_rate_pct": metrics.get("error_rate_pct", 0.0),
                "ab_imbalance": judgment.get("ab_imbalance"),
                "verdict": judgment.get("decision", {}).get("verdict", "unknown")
            }
        except Exception:
            return None
    
    def _load_lab_reports(self) -> List[str]:
        """Load LAB_*_MINI.txt reports if available."""
        loaded = []
        patterns = ["LAB_COMBO_REPORT_MINI.txt", "LAB_FLOW_REPORT_MINI.txt", "LAB_ROUTE_REPORT_MINI.txt"]
        
        for pattern in patterns:
            path = self.reports_dir / pattern
            if path.exists():
                loaded.append(pattern)
        
        return loaded
    
    def _load_combo_summary(self) -> bool:
        """Check if combo_autotune_summary.json exists."""
        path = self.reports_dir / "combo_autotune_summary.json"
        return path.exists()
    
    def _generate_bullets(self, metrics: Dict[str, float], result: Dict[str, Any],
                          lab_reports: List[str], combo_summary: bool) -> List[str]:
        """Generate explanation bullets using heuristics."""
        bullets = []
        
        delta_p95 = metrics["delta_p95_pct"]
        delta_qps = metrics["delta_qps_pct"]
        error_rate = metrics["error_rate_pct"]
        verdict = metrics["verdict"]
        ab_imbalance = metrics.get("ab_imbalance")
        
        # Rule 1: Overall verdict summary
        if verdict == "pass":
            bullets.append(f"✓ 实验通过：P95 延迟改善 {abs(delta_p95):.1f}%，达到 PASS 阈值（≥10%）")
        elif verdict == "edge":
            bullets.append(f"⚠ 边缘结果：P95 改善 {abs(delta_p95):.1f}%，处于 EDGE 区间（5-10%）")
        else:
            if delta_p95 > 0:
                bullets.append(f"✗ 实验失败：P95 延迟恶化 {delta_p95:.1f}%")
            else:
                bullets.append(f"✗ 实验失败：P95 改善不足（{abs(delta_p95):.1f}% < 5%）")
        
        # Rule 2: Error rate analysis
        if error_rate >= 1.0:
            bullets.append(f"❌ 错误率过高：{error_rate:.2f}% ≥ 1% 阈值，实验不可信")
        elif error_rate >= 0.5:
            bullets.append(f"⚠ 错误率偏高：{error_rate:.2f}%，建议检查日志")
        else:
            bullets.append(f"✓ 错误率正常：{error_rate:.2f}% < 1%")
        
        # Rule 3: QPS change analysis
        if delta_qps < -20:
            bullets.append(f"⚠ QPS 大幅下降 {abs(delta_qps):.1f}%，可能影响吞吐量")
        elif delta_qps < -10:
            bullets.append(f"QPS 轻微下降 {abs(delta_qps):.1f}%，属正常波动范围")
        elif delta_qps > 10:
            bullets.append(f"QPS 提升 {delta_qps:.1f}%，吞吐量有改善")
        else:
            bullets.append(f"QPS 基本稳定（{delta_qps:+.1f}%）")
        
        # Rule 4: AB balance check
        if ab_imbalance is not None and ab_imbalance > 5:
            bullets.append(f"⚠ AB 样本不平衡 {ab_imbalance:.1f}%，可能影响统计显著性")
        
        # Rule 5: Routing policy heuristics
        app_result = result.get("application", {})
        if app_result.get("applied"):
            bullets.append("✓ 配置已应用到生产环境，建议监控 24 小时")
        elif verdict == "pass" and app_result.get("safe_mode"):
            bullets.append("⚠ SAFE MODE：配置未自动应用，需手动执行 curl 命令")
        
        # Rule 6: FAISS routing specific (if detected in config)
        config = result.get("config", {})
        exp_cfg = config.get("experiment", {})
        routing_mode = exp_cfg.get("routing_mode", "")
        
        if "faiss" in routing_mode.lower() and delta_p95 <= -10:
            bullets.append("✓ FAISS 分流有效，P95 显著下降")
        elif routing_mode and delta_p95 <= -5:
            bullets.append(f"路由策略 '{routing_mode}' 有正面效果")
        
        # Rule 7: Flow control policy (if detected)
        flow_policy = exp_cfg.get("flow_policy", "")
        if flow_policy and delta_p95 <= -10:
            bullets.append(f"流控策略 '{flow_policy}' 对延迟优化显著")
        
        # Rule 8: Combo experiment indicator
        if combo_summary or "combo" in str(lab_reports).lower():
            bullets.append("组合实验（COMBO）模式：同时测试流控 + 路由")
        
        # Rule 9: Next steps based on verdict
        if verdict == "pass":
            bullets.append("建议：保持当前配置，持续监控核心指标（P95, QPS, Error Rate）")
        elif verdict == "edge":
            bullets.append("建议：延长测试窗口或调整参数后重测")
        else:
            bullets.append("建议：回滚配置，重新评估参数设置")
        
        return bullets
    
    def _fallback_template(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback template when no metrics available."""
        phase = result.get("phase", "unknown")
        
        if phase == "health_gate" and not result.get("ok"):
            bullets = [
                "❌ 健康检查失败：依赖服务不可用",
                f"原因：{result.get('reason', 'Unknown')}",
                "建议：检查 Redis 和 Qdrant 服务状态"
            ]
        elif phase in ["execute", "judge"] and not result.get("ok"):
            bullets = [
                f"❌ {phase.upper()} 阶段失败",
                f"错误：{result.get('error', 'Unknown')}",
                "建议：查看日志并重试"
            ]
        else:
            bullets = [
                "实验已执行，但缺少指标数据",
                "请检查报告文件和 API 响应"
            ]
        
        return {
            "bullets": bullets,
            "sources": [],
            "mode": "template"
        }


def explain_result(result: Dict[str, Any], project_root: Path = None) -> Dict[str, Any]:
    """
    Convenience function for explaining agent result.
    
    Args:
        result: Agent execution result
        project_root: Project root path (auto-detected if None)
    
    Returns:
        Explanation with bullets and sources
    """
    if project_root is None:
        # Auto-detect project root
        project_root = Path(__file__).parent.parent.parent.parent
    
    explainer = RuleBasedExplainer(project_root)
    return explainer.explain(result)

