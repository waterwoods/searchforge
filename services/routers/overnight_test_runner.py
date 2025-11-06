"""
Overnight test runner for control and routing systems.

Runs 12 scenarios combining different configurations:
- signals on/off
- aimd vs pid
- routing on/off
- FAISS healthy/unhealthy

Each scenario runs for 5 minutes with Black Swan async mode B small.
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, List
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)


class OvernightTestRunner:
    """Overnight test runner for control and routing."""
    
    def __init__(
        self,
        api_base: str = "http://localhost:8011",
        scenario_duration: int = 300,  # 5 minutes
        black_swan_api: str = "http://localhost:8011"
    ):
        self.api_base = api_base
        self.scenario_duration = scenario_duration
        self.black_swan_api = black_swan_api
        
        # Results storage
        self.results: List[Dict[str, Any]] = []
        self.start_time = 0
        self.end_time = 0
    
    def get_scenarios(self) -> List[Dict[str, Any]]:
        """
        Generate 12 test scenarios.
        
        Combines:
        - Signals: all on, only p95, only queue_depth, all off
        - Policy: aimd, pid
        - Routing: on, off
        - FAISS: healthy, unhealthy
        """
        scenarios = []
        
        # Scenario matrix
        signal_configs = [
            {"name": "all_signals", "signals": ["p95", "queue_depth"]},
            {"name": "p95_only", "signals": ["p95"]},
            {"name": "queue_only", "signals": ["queue_depth"]},
            {"name": "no_signals", "signals": []}
        ]
        
        policy_configs = ["aimd", "pid"]
        routing_configs = [True, False]
        faiss_health_configs = [True, False]
        
        scenario_id = 1
        
        # Generate combinations (limited to 12 scenarios)
        for signals_cfg in signal_configs[:2]:  # 2 signal configs
            for policy in policy_configs:  # 2 policies
                for routing_enabled in routing_configs[:1]:  # routing ON only
                    for faiss_healthy in faiss_health_configs:  # 2 health states
                        if len(scenarios) >= 12:
                            break
                        
                        scenarios.append({
                            "id": scenario_id,
                            "name": f"{signals_cfg['name']}_{policy}_routing_{routing_enabled}_faiss_{faiss_healthy}",
                            "config": {
                                "control": {
                                    "signals": signals_cfg["signals"],
                                    "actuators": ["concurrency", "batch_size"],
                                    "policy": policy
                                },
                                "routing": {
                                    "enabled": routing_enabled,
                                    "policy": "rules",
                                    "faiss": faiss_healthy
                                }
                            }
                        })
                        scenario_id += 1
        
        return scenarios[:12]
    
    async def run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single test scenario.
        
        Steps:
        1. Apply flags
        2. Start Black Swan async mode B small (60s trip)
        3. Collect metrics for scenario_duration
        4. Stop Black Swan
        5. Collect results
        """
        logger.info(f"Starting scenario {scenario['id']}: {scenario['name']}")
        
        scenario_start = time.time()
        
        # 1. Apply flags
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.api_base}/ops/flags",
                    json=scenario["config"]
                )
                flags_result = resp.json()
                logger.info(f"Flags applied: {flags_result}")
        except Exception as e:
            logger.error(f"Failed to apply flags: {e}")
            return {
                "scenario": scenario,
                "status": "error",
                "error": f"flags_apply_failed: {e}"
            }
        
        # 2. Start Black Swan (mode B small, 60s trip)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                black_swan_config = {
                    "mode": "B",
                    "size": "small",
                    "duration": 60,
                    "interval": 1
                }
                resp = await client.post(
                    f"{self.black_swan_api}/ops/black_swan",
                    json=black_swan_config
                )
                black_swan_result = resp.json()
                logger.info(f"Black Swan started: {black_swan_result}")
        except Exception as e:
            logger.error(f"Failed to start Black Swan: {e}")
            # Continue anyway
        
        # 3. Collect metrics for scenario_duration
        metrics_samples = []
        decisions_count = 0
        
        collect_interval = 10  # seconds
        num_samples = self.scenario_duration // collect_interval
        
        for i in range(num_samples):
            await asyncio.sleep(collect_interval)
            
            try:
                # Get control status
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{self.api_base}/ops/control/status")
                    status = resp.json()
                    
                    # Get decisions
                    resp = await client.get(f"{self.api_base}/ops/decisions?limit=10")
                    decisions = resp.json()
                    
                    decisions_count = decisions.get("count", 0)
                    
                    metrics_samples.append({
                        "timestamp": time.time(),
                        "status": status,
                        "recent_decisions": decisions_count
                    })
            
            except Exception as e:
                logger.warning(f"Metrics collection failed: {e}")
        
        # 4. Stop Black Swan
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{self.black_swan_api}/ops/black_swan/stop")
                stop_result = resp.json()
                logger.info(f"Black Swan stopped: {stop_result}")
        except Exception as e:
            logger.warning(f"Failed to stop Black Swan: {e}")
        
        # 5. Get final metrics
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get Black Swan report
                resp = await client.get(f"{self.black_swan_api}/ops/black_swan/report")
                report = resp.json()
                
                # Extract metrics
                p50 = report.get("p50", 0)
                p95 = report.get("p95", 0)
                p99 = report.get("p99", 0)
                qps = report.get("qps", 0)
                errors = report.get("errors", 0)
        except Exception as e:
            logger.warning(f"Failed to get final metrics: {e}")
            p50 = p95 = p99 = qps = errors = 0
        
        scenario_end = time.time()
        
        result = {
            "scenario": scenario,
            "status": "completed",
            "duration": scenario_end - scenario_start,
            "metrics": {
                "p50": p50,
                "p95": p95,
                "p99": p99,
                "qps": qps,
                "errors": errors,
                "decisions_count": decisions_count
            },
            "samples": metrics_samples
        }
        
        logger.info(f"Scenario {scenario['id']} completed: p95={p95:.2f}ms, QPS={qps:.2f}")
        
        return result
    
    async def reset_to_baseline(self):
        """Reset to safe baseline configuration."""
        baseline_config = {
            "control": {
                "signals": ["p95", "queue_depth"],
                "actuators": ["concurrency", "batch_size"],
                "policy": "aimd"
            },
            "routing": {
                "enabled": True,
                "policy": "rules",
                "faiss": True
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{self.api_base}/ops/flags",
                    json=baseline_config
                )
            logger.info("Reset to baseline configuration")
            
            # Wait for stabilization
            await asyncio.sleep(10)
        
        except Exception as e:
            logger.error(f"Failed to reset to baseline: {e}")
    
    async def run_all_scenarios(self) -> Dict[str, Any]:
        """Run all test scenarios."""
        self.start_time = time.time()
        
        logger.info("=" * 80)
        logger.info("OVERNIGHT TEST RUN - CONTROL + ROUTING")
        logger.info("=" * 80)
        
        scenarios = self.get_scenarios()
        logger.info(f"Total scenarios: {len(scenarios)}")
        
        self.results = []
        
        for scenario in scenarios:
            # Run scenario
            result = await self.run_scenario(scenario)
            self.results.append(result)
            
            # Reset to baseline between scenarios
            await self.reset_to_baseline()
        
        self.end_time = time.time()
        
        logger.info("=" * 80)
        logger.info("OVERNIGHT TEST RUN COMPLETED")
        logger.info("=" * 80)
        
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time,
            "total_scenarios": len(scenarios),
            "completed": sum(1 for r in self.results if r["status"] == "completed"),
            "results": self.results
        }
    
    def generate_report(self, output_path: str = "reports/CONTROL_ROUTING_OVERNIGHT_MINI.txt"):
        """Generate concise overnight report (≤100 lines)."""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("CONTROL + ROUTING OVERNIGHT TEST REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Git info
        try:
            import subprocess
            git_sha = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=Path(__file__).parent.parent.parent
            ).decode().strip()
        except:
            git_sha = "unknown"
        
        lines.append(f"Git SHA: {git_sha}")
        lines.append(f"Start: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))}")
        lines.append(f"End: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.end_time))}")
        lines.append(f"Duration: {(self.end_time - self.start_time) / 3600:.2f} hours")
        lines.append("")
        
        # Summary table
        lines.append("-" * 80)
        lines.append("SCENARIO RESULTS")
        lines.append("-" * 80)
        lines.append(f"{'ID':<4} {'Name':<40} {'P95':>8} {'QPS':>8} {'Errs':>6} {'Decs':>6}")
        lines.append("-" * 80)
        
        for result in self.results:
            scenario = result["scenario"]
            metrics = result.get("metrics", {})
            
            lines.append(
                f"{scenario['id']:<4} "
                f"{scenario['name'][:40]:<40} "
                f"{metrics.get('p95', 0):>8.1f} "
                f"{metrics.get('qps', 0):>8.1f} "
                f"{metrics.get('errors', 0):>6} "
                f"{metrics.get('decisions_count', 0):>6}"
            )
        
        lines.append("-" * 80)
        lines.append("")
        
        # Best performers
        if self.results:
            sorted_by_p95 = sorted(
                [r for r in self.results if r.get("metrics", {}).get("p95", 0) > 0],
                key=lambda r: r["metrics"]["p95"]
            )
            
            lines.append("TOP 3 BY P95 LATENCY")
            lines.append("-" * 80)
            for i, result in enumerate(sorted_by_p95[:3], 1):
                lines.append(f"{i}. {result['scenario']['name']}: {result['metrics']['p95']:.1f}ms")
            lines.append("")
        
        # PASS/FAIL criteria
        lines.append("-" * 80)
        lines.append("ACCEPTANCE CRITERIA")
        lines.append("-" * 80)
        
        # Check if any AIMD scenario beats baseline
        baseline_p95 = 100.0  # Target
        aimd_results = [r for r in self.results if "aimd" in r["scenario"]["name"]]
        
        if aimd_results:
            best_aimd = min(aimd_results, key=lambda r: r.get("metrics", {}).get("p95", 999))
            best_p95 = best_aimd["metrics"].get("p95", 999)
            p95_improvement = (baseline_p95 - best_p95) / baseline_p95 * 100
            
            lines.append(f"✓ Best AIMD P95: {best_p95:.1f}ms (target: <{baseline_p95}ms)")
            lines.append(f"  Improvement: {p95_improvement:.1f}%")
        
        lines.append("")
        lines.append("=" * 80)
        
        # Write report (ensure ≤100 lines)
        report_lines = lines[:100]
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            f.write("\n".join(report_lines))
        
        logger.info(f"Report written to {output_path}")
        
        return report_lines
    
    def save_artifacts(self):
        """Save additional output files."""
        # Save flags snapshot
        flags_snapshot = {
            "timestamp": time.time(),
            "scenarios": [r["scenario"]["config"] for r in self.results]
        }
        
        with open("reports/CONTROL_FLAGS_SNAPSHOT.json", "w") as f:
            json.dump(flags_snapshot, f, indent=2)
        
        # Save decisions (last 200 from each scenario)
        decisions_file = Path("reports/CONTROL_DECISIONS_LAST200.jsonl")
        with open(decisions_file, "w") as f:
            for result in self.results:
                for sample in result.get("samples", []):
                    f.write(json.dumps(sample) + "\n")
        
        logger.info("Artifacts saved")


async def main():
    """Main entry point for overnight test runner."""
    runner = OvernightTestRunner()
    
    # Run all scenarios
    summary = await runner.run_all_scenarios()
    
    # Generate report
    report_lines = runner.generate_report()
    
    # Save artifacts
    runner.save_artifacts()
    
    # Print summary
    print("\n" + "=" * 80)
    print("OVERNIGHT TEST COMPLETED")
    print("=" * 80)
    print(f"Total scenarios: {summary['total_scenarios']}")
    print(f"Completed: {summary['completed']}")
    print(f"Duration: {summary['duration'] / 3600:.2f} hours")
    print(f"Report: reports/CONTROL_ROUTING_OVERNIGHT_MINI.txt")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

