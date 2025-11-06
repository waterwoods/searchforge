"""
LabOps Agent Runner - Autonomous COMBO Experiment Orchestration
================================================================
V1 agent that runs one COMBO experiment end-to-end:
  Plan → Execute → Judge → Apply → Report

Flow:
1. Health Gate: Check dependencies
2. Execute: Run lab script with config
3. Judge: Fetch report and decide (pass/edge/fail)
4. Apply: POST flags if pass; log rollback otherwise
5. Report: Write ≤60-line summary to reports/LABOPS_AGENT_SUMMARY.txt
6. History: Append run metadata to state/history.jsonl
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.labops.tools.ops_client import OpsClient
from agents.labops.tools.report_parser import ReportParser
from agents.labops.policies.decision import DecisionEngine, DecisionThresholds


class LabOpsAgent:
    """V1 LabOps Agent for autonomous COMBO experiments."""
    
    def __init__(self, config: Dict[str, Any], dry_run: bool = False, auto_apply: bool = False):
        """
        Initialize agent.
        
        Args:
            config: Experiment configuration from plan_combo.yaml
            dry_run: If True, don't execute actual commands
            auto_apply: If True, automatically apply flags on PASS; otherwise print curl command
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
        
        self.run_metadata = {
            "start_time": datetime.now().isoformat(),
            "config": config,
            "dry_run": dry_run,
            "auto_apply": auto_apply
        }
    
    def run(self) -> Dict[str, Any]:
        """
        Execute full agent lifecycle.
        执行完整的 Agent 生命周期：健康检查→实验→判断→应用→报告
        
        Returns:
            Run result with verdict and actions taken
        """
        print("=" * 70)
        print("LABOPS AGENT V1 - COMBO EXPERIMENT")
        print("=" * 70)
        print()
        
        # Phase 1: Health Gate
        print("[Phase 1/5] Health Gate")
        health_result = self._health_gate()
        if not health_result["ok"]:
            self._write_summary(health_result)
            self._append_history(health_result)
            return health_result
        
        print(f"✓ All dependencies healthy\n")
        
        # Phase 2: Execute
        print("[Phase 2/5] Execute Experiment")
        exec_result = self._execute_experiment()
        if not exec_result["ok"]:
            self._write_summary(exec_result)
            self._append_history(exec_result)
            return exec_result
        
        print(f"✓ Experiment completed\n")
        
        # Phase 3: Judge
        print("[Phase 3/5] Judge Results")
        judge_result = self._judge_results()
        if not judge_result["ok"]:
            self._write_summary(judge_result)
            self._append_history(judge_result)
            return judge_result
        
        verdict = judge_result["decision"]["verdict"]
        print(f"✓ Verdict: {verdict.upper()}\n")
        
        # Phase 4: Apply (if pass)
        print("[Phase 4/5] Apply Flags")
        apply_result = self._apply_flags(judge_result)
        print(f"✓ Flags: {apply_result['message']}\n")
        
        # Phase 5: Report
        print("[Phase 5/5] Generate Report")
        final_result = {
            "ok": True,
            "phase": "complete",
            "health": health_result,
            "execution": exec_result,
            "judgment": judge_result,
            "application": apply_result,
            "end_time": datetime.now().isoformat()
        }
        
        self._write_summary(final_result)
        self._append_history(final_result)
        
        print("✓ Report written to reports/LABOPS_AGENT_SUMMARY.txt\n")
        print("=" * 70)
        print(f"AGENT RUN COMPLETE - Verdict: {verdict.upper()}")
        print("=" * 70)
        
        return final_result
    
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
        """Phase 2: Run lab script with COMBO config.
        执行实验：调用 run_lab_headless.sh 运行 COMBO 实验
        """
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
        """Phase 3: Fetch report and make decision.
        判断结果：获取报告并决策 PASS/EDGE/FAIL
        """
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
        """Phase 4: Apply flags if verdict is PASS.
        应用配置：PASS 时写入 flags，否则输出回滚命令
        """
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
            
            # Generate curl command for manual application
            import json
            base_url = self.config.get("base_url", "http://localhost:8011")
            payload = {}
            if control_flags:
                payload["control"] = control_flags
            if routing_flags:
                payload["routing"] = routing_flags
            
            curl_cmd = f"curl -X POST {base_url}/ops/flags \\\n"
            curl_cmd += f"  -H 'Content-Type: application/json' \\\n"
            curl_cmd += f"  -d '{json.dumps(payload, indent=2)}'"
            
            # Safe apply gate: only apply if --auto-apply flag is set
            if not self.auto_apply:
                print(f"  ⚠️  SAFE APPLY MODE: Flags NOT applied automatically")
                print(f"  ✓ Verdict: PASS (manual apply required)")
                print(f"\n  To apply these flags, run:\n")
                print(f"  {curl_cmd}\n")
                
                return {
                    "ok": True,
                    "applied": False,
                    "message": "PASS verdict - manual apply required (use --auto-apply to enable)",
                    "verdict": verdict,
                    "curl_command": curl_cmd,
                    "safe_mode": True
                }
            
            # Auto-apply mode: Actually apply the flags
            try:
                result = self.client.apply_flags(
                    control=control_flags,
                    routing=routing_flags
                )
                
                if result.get("ok"):
                    # Generate rollback command
                    rollback_cmd = self.decision_engine.generate_rollback_command(self.config)
                    
                    print(f"  ✓ Flags applied successfully (--auto-apply enabled)")
                    print(f"  Rollback: See summary for command")
                    
                    return {
                        "ok": True,
                        "applied": True,
                        "message": "Flags applied (PASS verdict + auto-apply)",
                        "verdict": verdict,
                        "rollback_command": rollback_cmd,
                        "curl_command": curl_cmd
                    }
                else:
                    return {
                        "ok": False,
                        "applied": False,
                        "error": "flag_application_failed",
                        "message": f"Failed to apply flags: {result}",
                        "verdict": verdict
                    }
            
            except Exception as e:
                return {
                    "ok": False,
                    "applied": False,
                    "error": str(e),
                    "message": f"Exception applying flags: {e}",
                    "verdict": verdict
                }
        
        else:
            # EDGE or FAIL: Don't apply, just log rollback recommendation
            rollback_cmd = self.decision_engine.generate_rollback_command(self.config)
            
            print(f"  ✗ Flags NOT applied ({verdict.upper()} verdict)")
            print(f"  Rollback recommendation logged")
            
            return {
                "ok": True,
                "applied": False,
                "message": f"No flags applied ({verdict} verdict)",
                "verdict": verdict,
                "rollback_command": rollback_cmd,
                "safe_mode": False
            }
    
    def _write_summary(self, result: Dict[str, Any]) -> None:
        """Phase 5: Write ≤60-line summary to reports/LABOPS_AGENT_SUMMARY.txt.
        生成报告：输出 ≤60 行总结到报告文件
        """
        project_root = Path(__file__).parent.parent.parent
        report_path = project_root / "reports" / "LABOPS_AGENT_SUMMARY.txt"
        
        lines = []
        lines.append("=" * 60)
        lines.append("LABOPS AGENT V1 - EXECUTION SUMMARY")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        lines.append("")
        
        # Inputs
        lines.append("INPUTS")
        lines.append("-" * 60)
        cfg = self.config["experiment"]
        lines.append(f"QPS: {cfg['qps']}, Window: {cfg['window_sec']}s, Rounds: {cfg['rounds']}")
        lines.append(f"Flow: {cfg['flow_policy']}, Target P95: {cfg['target_p95']}ms")
        lines.append(f"Conc Cap: {cfg['conc_cap']}, Batch Cap: {cfg['batch_cap']}")
        lines.append(f"Routing: {cfg['routing_mode']}, TopK Threshold: {cfg['topk_threshold']}")
        lines.append(f"Time Budget: {self.config['time_budget']}s")
        lines.append("")
        
        # Results
        if result.get("phase") == "health_gate" and not result.get("ok"):
            lines.append("RESULT: HEALTH GATE FAILED")
            lines.append("-" * 60)
            lines.append(f"Reason: {result.get('reason', 'Unknown')}")
            lines.append("")
            lines.append("VERDICT: BLOCKED")
            lines.append("Next Step: Fix dependencies and retry")
        
        elif result.get("phase") in ["execute", "judge"] and not result.get("ok"):
            lines.append(f"RESULT: {result['phase'].upper()} FAILED")
            lines.append("-" * 60)
            lines.append(f"Error: {result.get('error', 'Unknown')}")
            lines.append(f"Reason: {result.get('reason', 'Unknown')}")
            lines.append("")
            lines.append("VERDICT: ERROR")
            lines.append("Next Step: Check logs and retry")
        
        else:
            # Full run
            judgment = result.get("judgment", {})
            metrics = judgment.get("metrics", {})
            decision = judgment.get("decision", {})
            application = result.get("application", {})
            
            lines.append("RESULTS")
            lines.append("-" * 60)
            lines.append(f"ΔP95: {metrics.get('delta_p95_pct', 0):+.1f}%")
            lines.append(f"ΔQPS: {metrics.get('delta_qps_pct', 0):+.1f}%")
            lines.append(f"Error Rate: {metrics.get('error_rate_pct', 0):.2f}%")
            
            if judgment.get("ab_imbalance") is not None:
                lines.append(f"AB Imbalance: {judgment['ab_imbalance']:.1f}%")
            
            lines.append("")
            lines.append("VERDICT")
            lines.append("-" * 60)
            verdict = decision.get("verdict", "unknown").upper()
            lines.append(f"Decision: {verdict}")
            lines.append(f"Reason: {decision.get('reason', 'N/A')}")
            lines.append(f"Flags Applied: {'YES' if application.get('applied') else 'NO'}")
            
            if decision.get("warnings"):
                lines.append("")
                lines.append("Warnings:")
                for warn in decision["warnings"]:
                    lines.append(f"  - {warn}")
            
            lines.append("")
            lines.append("NEXT STEP")
            lines.append("-" * 60)
            
            if verdict == "PASS":
                lines.append("✓ Configuration applied to production")
                lines.append("Monitor metrics for 24h")
            elif verdict == "EDGE":
                lines.append("Manual review recommended")
                lines.append("Consider extended test or parameter tuning")
            else:
                lines.append("Configuration rejected")
                lines.append("Review parameters and retry")
            
            # Apply command (if safe mode)
            if application.get("curl_command"):
                lines.append("")
                lines.append("APPLY COMMAND")
                lines.append("-" * 60)
                for line in application["curl_command"].split('\n'):
                    lines.append(line)
            
            # Rollback command
            if application.get("rollback_command"):
                lines.append("")
                lines.append("ROLLBACK")
                lines.append("-" * 60)
                for line in application["rollback_command"].split('\n'):
                    lines.append(line)
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("END OF SUMMARY")
        lines.append("=" * 60)
        
        # Limit to 60 lines
        summary_text = "\n".join(lines[:60])
        
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(summary_text)
    
    def _append_history(self, result: Dict[str, Any]) -> None:
        """Append run metadata to state/history.jsonl."""
        history_path = Path(__file__).parent / "state" / "history.jsonl"
        history_path.parent.mkdir(exist_ok=True)
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "config": self.config,
            "result": result,
            "verdict": result.get("judgment", {}).get("decision", {}).get("verdict", "error")
        }
        
        with open(history_path, 'a') as f:
            f.write(json.dumps(record) + '\n')


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    
    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LabOps Agent V1")
    parser.add_argument("--config", default="agents/labops/plan/plan_combo.yaml",
                        help="Path to config file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run mode (no actual execution)")
    parser.add_argument("--auto-apply", action="store_true",
                        help="Automatically apply flags on PASS (default: safe mode, print curl only)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last checkpoint (not yet implemented)")
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        # Try relative to project root
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / args.config
    
    if not config_path.exists():
        print(f"❌ Config file not found: {args.config}")
        return 1
    
    config = load_config(config_path)
    
    # Run agent
    agent = LabOpsAgent(config, dry_run=args.dry_run, auto_apply=args.auto_apply)
    result = agent.run()
    
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

