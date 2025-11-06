"""
LabOps Agent Runner V3 - LLM Explainer + Code Navigation
=========================================================
V3 agent with LLM-powered explanations (auto-fallback to rules) and code navigation.

Flow:
  Plan → Execute → Judge → Apply → Explain (LLM) + Code Nav

Features:
- LLM 解释（优先）：使用 gpt-4o-mini 等便宜模型
- 规则回退：无 API Key 时自动降级
- 代码指路：提供可点击的代码位置
- 超时保护：8s 超时自动回退
- 离线可跑：完全无 LLM 依赖也能正常运行
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.labops.tools.ops_client import OpsClient
from agents.labops.tools.report_parser import ReportParser
from agents.labops.policies.decision import DecisionEngine, DecisionThresholds
from agents.labops.v3.explainers.explainer_llm import LLMExplainer
from agents.labops.v3.code_nav import CodeNavigator


class LabOpsAgentV3:
    """V3 LabOps Agent - LLM explainer with code navigation."""
    
    def __init__(self, config: Dict[str, Any], dry_run: bool = False, auto_apply: bool = False):
        """
        Initialize Agent V3.
        
        Args:
            config: Experiment configuration
            dry_run: If True, don't execute actual commands
            auto_apply: If True, automatically apply flags on PASS
        """
        self.config = config
        self.dry_run = dry_run
        self.auto_apply = auto_apply
        
        self.client = OpsClient(
            base_url=config.get("base_url", "http://localhost:8011"),
            timeout=config.get("timeout", 30)
        )
        
        self.parser = ReportParser()
        
        thresholds = DecisionThresholds(
            pass_delta_p95_max=config["thresholds"]["pass_delta_p95_max"],
            edge_delta_p95_max=config["thresholds"]["edge_delta_p95_max"],
            max_error_rate=config["thresholds"]["max_error_rate"],
            ab_balance_warn=config["thresholds"]["ab_balance_warn"]
        )
        self.decision_engine = DecisionEngine(thresholds)
        
        # V3: Add LLM explainer and code navigator
        project_root = Path(__file__).parent.parent.parent.parent
        self.explainer = LLMExplainer(project_root)
        self.navigator = CodeNavigator(project_root)
        
        self.run_metadata = {
            "start_time": datetime.now().isoformat(),
            "config": config,
            "dry_run": dry_run,
            "auto_apply": auto_apply,
            "version": "v3"
        }
    
    def run(self) -> Dict[str, Any]:
        """
        Execute full Agent V3 lifecycle.
        
        Returns:
            Run result with verdict, LLM explanation, code navigation
        """
        print("=" * 70)
        print("LABOPS AGENT V3 - COMBO EXPERIMENT (LLM + Code Nav)")
        print("=" * 70)
        print()
        
        # Phase 1: Health Gate (reuse from V1/V2)
        print("[Phase 1/5] Health Gate")
        health_result = self._health_gate()
        if not health_result["ok"]:
            # V3: Add LLM explanation + code nav even on failure
            explanation = self.explainer.explain(health_result, include_code_nav=True)
            health_result["explanation"] = explanation
            
            self._write_summary_v3(health_result)
            self._append_history_v3(health_result)
            return health_result
        
        print(f"✓ All dependencies healthy\n")
        
        # Phase 2: Execute (reuse from V1/V2)
        print("[Phase 2/5] Execute Experiment")
        exec_result = self._execute_experiment()
        if not exec_result["ok"]:
            explanation = self.explainer.explain(exec_result, include_code_nav=True)
            exec_result["explanation"] = explanation
            
            self._write_summary_v3(exec_result)
            self._append_history_v3(exec_result)
            return exec_result
        
        print(f"✓ Experiment completed\n")
        
        # Phase 3: Judge (reuse from V1/V2)
        print("[Phase 3/5] Judge Results")
        judge_result = self._judge_results()
        if not judge_result["ok"]:
            explanation = self.explainer.explain(judge_result, include_code_nav=True)
            judge_result["explanation"] = explanation
            
            self._write_summary_v3(judge_result)
            self._append_history_v3(judge_result)
            return judge_result
        
        verdict = judge_result["decision"]["verdict"]
        print(f"✓ Verdict: {verdict.upper()}\n")
        
        # Phase 4: Apply (reuse from V1/V2)
        print("[Phase 4/5] Apply Flags")
        apply_result = self._apply_flags(judge_result)
        print(f"✓ Flags: {apply_result['message']}\n")
        
        # Phase 5: Explain with LLM + Code Nav (NEW in V3)
        print("[Phase 5/5] Generate LLM Explanation + Code Nav")
        final_result = {
            "ok": True,
            "phase": "complete",
            "health": health_result,
            "execution": exec_result,
            "judgment": judge_result,
            "application": apply_result,
            "config": self.config,
            "end_time": datetime.now().isoformat()
        }
        
        explanation = self.explainer.explain(final_result, include_code_nav=True)
        final_result["explanation"] = explanation
        
        mode = explanation.get("mode", "unknown")
        bullet_count = len(explanation.get("bullets", []))
        code_nav_count = len(explanation.get("code_nav", []))
        
        print(f"✓ Generated {bullet_count} bullets ({mode} mode)")
        if code_nav_count > 0:
            print(f"✓ Found {code_nav_count} code locations")
        print()
        
        # Write V3 report and history
        self._write_summary_v3(final_result)
        self._append_history_v3(final_result)
        
        print("✓ Report written to reports/LABOPS_AGENT_V3_SUMMARY.txt\n")
        print("=" * 70)
        print(f"AGENT V3 RUN COMPLETE - Verdict: {verdict.upper()} ({mode} mode)")
        print("=" * 70)
        
        return final_result
    
    # Reuse V1/V2 methods (health, execute, judge, apply)
    def _health_gate(self) -> Dict[str, Any]:
        """Phase 1: Check dependencies health."""
        try:
            health = self.client.check_health()
            
            if not health.get("ok"):
                return {
                    "ok": False,
                    "phase": "health_gate",
                    "error": "dependencies_unhealthy",
                    "details": health,
                    "reason": f"Dependencies unhealthy: {health.get('health', {}).get('reasons', [])}"
                }
            
            # Check Redis and Qdrant
            health_status = health.get("health", {})
            redis_ok = health_status.get("redis", {}).get("ok", False)
            qdrant_ok = health_status.get("qdrant", {}).get("ok", False)
            
            if not (redis_ok and qdrant_ok):
                return {
                    "ok": False,
                    "phase": "health_gate",
                    "error": "dependencies_unhealthy",
                    "redis": redis_ok,
                    "qdrant": qdrant_ok,
                    "reason": f"Redis OK: {redis_ok}, Qdrant OK: {qdrant_ok}"
                }
            
            return {
                "ok": True,
                "phase": "health_gate",
                "redis": redis_ok,
                "qdrant": qdrant_ok
            }
        
        except Exception as e:
            return {
                "ok": False,
                "phase": "health_gate",
                "error": "connection_failed",
                "reason": str(e)
            }
    
    def _execute_experiment(self) -> Dict[str, Any]:
        """Phase 2: Run lab script with COMBO config."""
        cfg = self.config["experiment"]
        
        # Build script arguments
        args = f"combo --with-load"
        args += f" --qps {cfg['qps']}"
        args += f" --window {cfg['window_sec']}"
        args += f" --rounds {cfg['rounds']}"
        args += f" --seed {cfg['seed']}"
        args += f" --flow-policy {cfg['flow_policy']}"
        args += f" --target-p95 {cfg['target_p95']}"
        args += f" --conc-cap {cfg['conc_cap']}"
        args += f" --batch-cap {cfg['batch_cap']}"
        args += f" --routing-mode {cfg['routing_mode']}"
        args += f" --topk-threshold {cfg['topk_threshold']}"
        
        if self.config["time_budget"] > 0:
            args += f" --time-budget {self.config['time_budget']}"
        
        print(f"Running: ./scripts/run_lab_headless.sh {args}")
        print()
        
        result = self.client.run_lab_script(
            script_args=args,
            time_budget=self.config["time_budget"],
            dry_run=self.dry_run
        )
        
        if not result["ok"]:
            return {
                "ok": False,
                "phase": "execute",
                "error": "script_failed",
                "reason": result.get("error", "Unknown"),
                "returncode": result.get("returncode", -1)
            }
        
        return {
            "ok": True,
            "phase": "execute",
            "script_args": args,
            "returncode": result.get("returncode", 0),
            "dry_run": result.get("dry_run", False)
        }
    
    def _judge_results(self) -> Dict[str, Any]:
        """Phase 3: Fetch report and make decision."""
        try:
            # Try API first
            mini_report = self.client.get_lab_report_mini()
            
            if mini_report.get("ok"):
                metrics = self.parser.parse_mini_endpoint(mini_report)
            else:
                # Fallback to file
                print("  API returned no report, trying file fallback...")
                report_text = self.client.read_report_file("combo")
                
                if not report_text:
                    return {
                        "ok": False,
                        "phase": "judge",
                        "error": "no_report",
                        "reason": "No report available from API or file"
                    }
                
                metrics = self.parser.parse_text_report(report_text)
            
            # Validate metrics
            if not self.parser.validate_metrics(metrics):
                return {
                    "ok": False,
                    "phase": "judge",
                    "error": "invalid_metrics",
                    "metrics": metrics,
                    "reason": "Parsed metrics failed validation"
                }
            
            # Check AB balance
            full_report = self.client.get_lab_report_full()
            ab_imbalance = None
            if full_report.get("ok"):
                report_text = full_report.get("report", "")
                ab_imbalance = self.parser.extract_ab_balance(report_text)
            
            # Make decision
            decision = self.decision_engine.decide(metrics, ab_imbalance)
            
            print(f"  Metrics: ΔP95={metrics['delta_p95_pct']:+.1f}%, "
                  f"ΔQPS={metrics['delta_qps_pct']:+.1f}%, "
                  f"Err={metrics['error_rate_pct']:.2f}%")
            
            if ab_imbalance is not None:
                print(f"  AB Imbalance: {ab_imbalance:.1f}%")
            
            if decision["warnings"]:
                for warn in decision["warnings"]:
                    print(f"  ⚠️  {warn}")
            
            print(f"  Decision: {decision['verdict'].upper()} - {decision['reason']}")
            
            return {
                "ok": True,
                "phase": "judge",
                "metrics": metrics,
                "ab_imbalance": ab_imbalance,
                "decision": decision
            }
        
        except Exception as e:
            return {
                "ok": False,
                "phase": "judge",
                "error": "judge_exception",
                "reason": str(e)
            }
    
    def _apply_flags(self, judge_result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Apply flags if verdict is PASS."""
        decision = judge_result["decision"]
        verdict = decision["verdict"]
        
        if self.dry_run:
            return {
                "ok": True,
                "applied": False,
                "message": "DRY-RUN: No flags applied",
                "verdict": verdict
            }
        
        if decision.get("apply_flags"):
            # PASS: Generate configuration
            cfg = self.config["experiment"]
            
            control_flags = {
                "policy": cfg["flow_policy"],
                "target_p95_ms": cfg["target_p95"],
                "max_concurrency": cfg["conc_cap"],
                "max_batch_size": cfg["batch_cap"]
            }
            
            routing_flags = {
                "enabled": True,
                "policy": cfg["routing_mode"],
                "topk_threshold": cfg["topk_threshold"]
            }
            
            # Generate curl command
            base_url = self.config.get("base_url", "http://localhost:8011")
            payload = {}
            if control_flags:
                payload["control"] = control_flags
            if routing_flags:
                payload["routing"] = routing_flags
            
            curl_cmd = f"curl -X POST {base_url}/ops/flags \\\n"
            curl_cmd += f"  -H 'Content-Type: application/json' \\\n"
            curl_cmd += f"  -d '{json.dumps(payload, indent=2)}'"
            
            # Safe apply gate
            if not self.auto_apply:
                print(f"  ⚠️  SAFE APPLY MODE: Flags NOT applied automatically")
                print(f"  ✓ Verdict: PASS (manual apply required)")
                
                return {
                    "ok": True,
                    "applied": False,
                    "message": "PASS verdict - manual apply required",
                    "verdict": verdict,
                    "curl_command": curl_cmd,
                    "safe_mode": True
                }
            
            # Auto-apply mode
            try:
                result = self.client.apply_flags(
                    control=control_flags,
                    routing=routing_flags
                )
                
                if result.get("ok"):
                    rollback_cmd = self.decision_engine.generate_rollback_command(self.config)
                    
                    print(f"  ✓ Flags applied successfully")
                    
                    return {
                        "ok": True,
                        "applied": True,
                        "message": "Flags applied (PASS + auto-apply)",
                        "verdict": verdict,
                        "rollback_command": rollback_cmd,
                        "curl_command": curl_cmd
                    }
                else:
                    return {
                        "ok": False,
                        "applied": False,
                        "error": "flag_application_failed",
                        "message": f"Failed to apply flags",
                        "verdict": verdict
                    }
            
            except Exception as e:
                return {
                    "ok": False,
                    "applied": False,
                    "error": str(e),
                    "message": f"Exception applying flags",
                    "verdict": verdict
                }
        
        else:
            # EDGE or FAIL
            rollback_cmd = self.decision_engine.generate_rollback_command(self.config)
            
            print(f"  ✗ Flags NOT applied ({verdict.upper()})")
            
            return {
                "ok": True,
                "applied": False,
                "message": f"No flags applied ({verdict})",
                "verdict": verdict,
                "rollback_command": rollback_cmd,
                "safe_mode": False
            }
    
    def _write_summary_v3(self, result: Dict[str, Any]) -> None:
        """Write V3 summary (≤60 lines) to LABOPS_AGENT_V3_SUMMARY.txt."""
        try:
            project_root = Path(__file__).parent.parent.parent.parent
            report_path = project_root / "reports" / "LABOPS_AGENT_V3_SUMMARY.txt"
            
            lines = []
            lines.append("=" * 60)
            lines.append("LABOPS AGENT V3 - EXECUTION SUMMARY (LLM + Code Nav)")
            lines.append("=" * 60)
            lines.append("")
            lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
            
            explanation = result.get("explanation", {})
            exp_mode = explanation.get("mode", "unknown")
            lines.append(f"Explainer: {exp_mode.upper()}")
            
            if explanation.get("latency_ms"):
                lines.append(f"LLM Latency: {explanation['latency_ms']:.0f} ms")
            
            lines.append("")
            
            # Inputs
            lines.append("INPUTS")
            lines.append("-" * 60)
            cfg = self.config.get("experiment", {})
            lines.append(f"QPS: {cfg.get('qps')}, Window: {cfg.get('window_sec')}s")
            lines.append(f"Flow: {cfg.get('flow_policy')}, Target P95: {cfg.get('target_p95')}ms")
            lines.append(f"Routing: {cfg.get('routing_mode')}")
            lines.append("")
            
            # Results
            if result.get("phase") == "health_gate" and not result.get("ok"):
                lines.append("RESULT: HEALTH GATE FAILED")
                lines.append("-" * 60)
                lines.append(f"Reason: {result.get('reason', 'Unknown')}")
                lines.append("")
                lines.append("VERDICT: BLOCKED")
            
            elif result.get("phase") in ["execute", "judge"] and not result.get("ok"):
                lines.append(f"RESULT: {result.get('phase', '').upper()} FAILED")
                lines.append("-" * 60)
                lines.append(f"Error: {result.get('error', 'Unknown')}")
                lines.append("")
                lines.append("VERDICT: ERROR")
            
            else:
                # Full run
                judgment = result.get("judgment", {})
                metrics = judgment.get("metrics", {})
                decision = judgment.get("decision", {})
                
                lines.append("RESULTS")
                lines.append("-" * 60)
                lines.append(f"ΔP95: {metrics.get('delta_p95_pct', 0):+.1f}%")
                lines.append(f"ΔQPS: {metrics.get('delta_qps_pct', 0):+.1f}%")
                lines.append(f"Error Rate: {metrics.get('error_rate_pct', 0):.2f}%")
                lines.append("")
                
                verdict = decision.get("verdict", "unknown").upper()
                lines.append("VERDICT")
                lines.append("-" * 60)
                lines.append(f"Decision: {verdict}")
                lines.append(f"Reason: {decision.get('reason', 'N/A')}")
                lines.append("")
            
            # V3: Add LLM Explanation
            if explanation.get("bullets"):
                lines.append(f"EXPLANATION ({exp_mode.upper()})")
                lines.append("-" * 60)
                for bullet in explanation["bullets"][:6]:
                    lines.append(f"• {bullet}")
                lines.append("")
            
            # V3: Add Code Navigation
            code_nav = explanation.get("code_nav", [])
            if code_nav:
                lines.append("CODE LOCATIONS")
                lines.append("-" * 60)
                for i, loc in enumerate(code_nav[:3], 1):
                    context = loc.get("context", "相关代码")
                    file_path = loc.get("file", "")
                    line_num = loc.get("line", 0)
                    lines.append(f"{i}. [{context}] {file_path}:{line_num}")
                lines.append("")
            
            lines.append("=" * 60)
            lines.append("END OF SUMMARY")
            lines.append("=" * 60)
            
            # Limit to 60 lines
            summary_text = "\n".join(lines[:60])
            
            report_path.parent.mkdir(exist_ok=True)
            report_path.write_text(summary_text)
        
        except Exception as e:
            # V3: Never fail on file write
            print(f"  ⚠️  Failed to write summary: {e}")
    
    def _append_history_v3(self, result: Dict[str, Any]) -> None:
        """Append run to V3 history (history_v3.jsonl)."""
        try:
            history_path = Path(__file__).parent.parent / "state" / "history_v3.jsonl"
            history_path.parent.mkdir(exist_ok=True)
            
            explanation = result.get("explanation", {})
            
            record = {
                "timestamp": datetime.now().isoformat(),
                "config": self.config,
                "result": {
                    "ok": result.get("ok"),
                    "phase": result.get("phase"),
                    "verdict": result.get("judgment", {}).get("decision", {}).get("verdict", "error"),
                    "explainer_mode": explanation.get("mode", "unknown"),
                    "bullets_count": len(explanation.get("bullets", [])),
                    "code_nav_count": len(explanation.get("code_nav", []))
                },
                "version": "v3"
            }
            
            with open(history_path, 'a') as f:
                f.write(json.dumps(record) + '\n')
        
        except Exception as e:
            # V3: Never fail on history write
            print(f"  ⚠️  Failed to write history: {e}")


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    
    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    """CLI entry point for V3."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LabOps Agent V3 (LLM + Code Nav)")
    parser.add_argument("--config", default="agents/labops/plan/plan_combo.yaml",
                        help="Path to config file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run mode")
    parser.add_argument("--auto-apply", action="store_true",
                        help="Auto-apply flags on PASS")
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        project_root = Path(__file__).parent.parent.parent.parent
        config_path = project_root / args.config
    
    if not config_path.exists():
        print(f"❌ Config file not found: {args.config}")
        return 1
    
    config = load_config(config_path)
    
    # Run agent V3
    agent = LabOpsAgentV3(config, dry_run=args.dry_run, auto_apply=args.auto_apply)
    result = agent.run()
    
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

