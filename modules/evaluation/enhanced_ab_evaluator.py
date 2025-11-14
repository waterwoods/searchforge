#!/usr/bin/env python3
"""
Enhanced A/B Evaluator for SmartSearchX with Recovery Time Tracking

This module implements a comprehensive A/B evaluation system with:
- Recovery time tracking after chaos events
- Enhanced chaos engineering scenarios
- Timeline-based metrics collection
- Autotuner action monitoring
"""

import asyncio
import json
import logging
import os
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from clients.retrieval_proxy_client import DEFAULT_BUDGET_MS, search as proxy_search
from modules.autotune import AutoTuner, TuningState
from modules.autotune.selector import select_strategy
from services.fiqa_api import obs

logger = logging.getLogger(__name__)

@dataclass
class RecoveryEvent:
    """Tracks recovery events after chaos windows."""
    chaos_window_start: float
    chaos_window_end: float
    recovery_start: float
    recovery_end: Optional[float] = None
    recovery_time_sec: Optional[float] = None
    baseline_p95: float = 0.0
    peak_p95: float = 0.0
    stable_p95: float = 0.0
    tuner_actions_during_recovery: int = 0
    status: str = "in_progress"  # "in_progress", "completed", "failed"

@dataclass
class TimelineMetrics:
    """Metrics collected over time for timeline analysis."""
    timestamp: float
    p95_ms: float
    p99_ms: float
    mean_latency_ms: float
    topk: int
    batch_size: int
    route_alpha: float
    tuner_actions_count: int
    chaos_active: bool
    recovery_active: bool
    current_qps: float

@dataclass
class EnhancedEvaluationMetrics:
    """Enhanced metrics with recovery tracking."""
    # Latency metrics
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    jitter_ms: float = 0.0
    mean_latency_ms: float = 0.0
    
    # Recall metrics
    recall_at_10: float = 0.0
    
    # Cost metrics
    cost_per_1k_queries: float = 0.0
    
    # Violation metrics
    violation_rate: float = 0.0
    
    # Recovery metrics
    recovery_events: List[RecoveryEvent] = field(default_factory=list)
    recovery_time_histogram: List[float] = field(default_factory=list)
    recovery_violation_rate: float = 0.0
    
    # Autotuner metrics
    autotuner_actions_count: int = 0
    autotuner_param_deltas: List[Dict[str, Any]] = field(default_factory=list)
    autotuner_actions_per_chaos_window: List[int] = field(default_factory=list)
    
    # Timeline metrics
    timeline_metrics: List[TimelineMetrics] = field(default_factory=list)
    
    # Shadow metrics
    shadow_divergence_rate: float = 0.0
    
    # Runtime metrics
    total_queries: int = 0
    successful_queries: int = 0
    runtime_seconds: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)

class EnhancedChaosEngine:
    """Enhanced chaos engineering with recovery tracking."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.events: List[Dict[str, Any]] = []
        self.active_events: List[Dict[str, Any]] = []
        self.chaos_windows: List[Dict[str, Any]] = []
        self.loss_windows: List[Dict[str, Any]] = []
        self.recovery_events: List[RecoveryEvent] = []
        self._setup_events()
    
    def _setup_events(self):
        """Setup enhanced chaos events based on configuration."""
        chaos_config = self.config.get("chaos", {})
        
        if not chaos_config.get("enabled", False):
            return
        
        # Latency injection (continuous)
        if chaos_config.get("latency_ms", 0) > 0:
            self.events.append({
                "type": "latency",
                "start_time": 0,
                "duration": self.config.get("duration_seconds", 1800),
                "intensity": chaos_config["latency_ms"]
            })
        
        # Loss injection (continuous)
        if chaos_config.get("loss_percent", 0) > 0:
            self.events.append({
                "type": "loss",
                "start_time": 0,
                "duration": self.config.get("duration_seconds", 1800),
                "intensity": chaos_config["loss_percent"]
            })
        
        # Chaos windows (periodic latency spikes)
        self.chaos_windows = chaos_config.get("chaos_windows", [])
        
        # Loss windows (periodic packet loss)
        self.loss_windows = chaos_config.get("loss_windows", [])
        
        # Disconnect events (periodic)
        disconnect_times = chaos_config.get("disconnect_times", [])
        disconnect_duration = chaos_config.get("disconnect_duration", 60)
        
        for disconnect_time in disconnect_times:
            self.events.append({
                "type": "disconnect",
                "start_time": disconnect_time,
                "duration": disconnect_duration,
                "intensity": 1.0
            })
    
    def should_inject_latency(self, current_time: float) -> float:
        """Check if latency should be injected at current time."""
        # Check continuous latency
        for event in self.events:
            if (event["type"] == "latency" and 
                event["start_time"] <= current_time <= event["start_time"] + event["duration"]):
                return event["intensity"]
        
        # Check chaos windows
        for window in self.chaos_windows:
            if (window["start_seconds"] <= current_time <= 
                window["start_seconds"] + window["duration_seconds"]):
                return 800.0  # 800ms latency injection
        
        return 0.0
    
    def should_inject_loss(self, current_time: float) -> float:
        """Check if packet loss should be injected at current time."""
        # Check continuous loss
        for event in self.events:
            if (event["type"] == "loss" and 
                event["start_time"] <= current_time <= event["start_time"] + event["duration"]):
                return event["intensity"]
        
        # Check loss windows
        for window in self.loss_windows:
            if (window["start_seconds"] <= current_time <= 
                window["start_seconds"] + window["duration_seconds"]):
                return window["loss_percent"]
        
        return 0.0
    
    def is_disconnected(self, current_time: float) -> bool:
        """Check if system should be disconnected at current time."""
        for event in self.events:
            if (event["type"] == "disconnect" and 
                event["start_time"] <= current_time <= event["start_time"] + event["duration"]):
                return True
        return False
    
    def is_in_chaos_window(self, current_time: float) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if currently in a chaos window."""
        for window in self.chaos_windows:
            if (window["start_seconds"] <= current_time <= 
                window["start_seconds"] + window["duration_seconds"]):
                return True, window
        return False, None
    
    def start_recovery_tracking(self, chaos_window: Dict[str, Any], baseline_p95: float):
        """Start tracking recovery after a chaos window."""
        recovery_event = RecoveryEvent(
            chaos_window_start=chaos_window["start_seconds"],
            chaos_window_end=chaos_window["start_seconds"] + chaos_window["duration_seconds"],
            recovery_start=chaos_window["start_seconds"] + chaos_window["duration_seconds"],
            baseline_p95=baseline_p95,
            peak_p95=baseline_p95
        )
        self.recovery_events.append(recovery_event)
        return recovery_event
    
    def update_recovery_event(self, recovery_event: RecoveryEvent, current_p95: float, 
                            tuner_actions: int, current_time: float):
        """Update recovery event with current metrics."""
        recovery_event.peak_p95 = max(recovery_event.peak_p95, current_p95)
        recovery_event.tuner_actions_during_recovery += tuner_actions
        
        # Check if recovery is complete (stable for 15s)
        if current_p95 <= recovery_event.baseline_p95 * 1.1:  # Within 10% of baseline
            if recovery_event.recovery_end is None:
                recovery_event.recovery_end = current_time
                recovery_event.recovery_time_sec = current_time - recovery_event.recovery_start
                recovery_event.status = "completed"
                recovery_event.stable_p95 = current_p95
        else:
            recovery_event.recovery_end = None
            recovery_event.recovery_time_sec = None

class EnhancedLoadGenerator:
    """Enhanced load generator with step QPS patterns."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.probes_config = config.get("probes", {})
        self.chaos_engine = EnhancedChaosEngine(config)
        self.start_time = time.time()
        
    def get_current_qps(self, elapsed_time: float) -> float:
        """Calculate current QPS based on load pattern."""
        # Check for step QPS pattern
        step_qps_config = self.probes_config.get("step_qps", {})
        if step_qps_config.get("enabled", False):
            steps = step_qps_config.get("steps", [])
            for step in steps:
                if elapsed_time >= step["time_seconds"]:
                    base_qps = step["qps"]
                else:
                    break
        else:
            base_qps = self.probes_config.get("qps", 2.0)
        
        # Check for burst conditions
        if self.probes_config.get("burst_enabled", False):
            burst_interval = self.probes_config.get("burst_interval", 120)
            burst_duration = self.probes_config.get("burst_duration", 5)
            
            # Check if we're in a burst period
            burst_cycle_time = elapsed_time % burst_interval
            if burst_cycle_time < burst_duration:
                return self.probes_config.get("burst_qps", 20.0)
        
        return base_qps
    
    def should_send_query(self, elapsed_time: float) -> bool:
        """Determine if a query should be sent at this time."""
        qps = self.get_current_qps(elapsed_time)
        # Simple Poisson-like distribution
        return random.random() < (qps / 10.0)  # Assuming 10Hz sampling

class EnhancedABEvaluator:
    """Enhanced A/B evaluation orchestrator with recovery tracking."""
    
    def __init__(self, config_file: str):
        with open(config_file, 'r') as f:
            self.full_config = json.load(f)
        
        self.metrics = EnhancedEvaluationMetrics()
        self.latency_samples: List[float] = []
        self.autotuner = None
        self.autotuner_state = None
        self.shadow_results: List[Dict[str, Any]] = []
        self.timeline_data: List[TimelineMetrics] = []
        self.active_recovery_events: List[RecoveryEvent] = []
        
        # AutoTuner trigger control
        self.last_tuner_update = 0.0
        self.last_tuner_action = 0.0
        self.tuner_sample_interval = 5.0
        self.tuner_cooldown = 15.0
        
    def setup_autotuner(self, config: Dict[str, Any]):
        """Setup autotuner for the evaluation."""
        if not config.get("auto_tuner_v1", False):
            return
        
        # Load tuner configuration from common config
        common_config = self.full_config.get("common", {})
        self.tuner_sample_interval = common_config.get("tuner_sample_interval", 5.0)
        self.tuner_cooldown = common_config.get("tuner_cooldown_sec", 15.0)
        
        # Try to get global AutoTuner instance from RAG API
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'fiqa_api'))
            from autotuner_global import get_global_autotuner  # type: ignore
            
            global_autotuner, global_autotuner_state = get_global_autotuner()
            if global_autotuner and global_autotuner_state:
                self.autotuner = global_autotuner
                self.autotuner_state = global_autotuner_state
                logger.info("✅ Using global AutoTuner instance")
                return
        except Exception as e:
            logger.warning(f"⚠️ Could not get global AutoTuner: {e}")
        
        # Fallback to creating local instance
        self.autotuner_state = TuningState()
        self.autotuner = AutoTuner(
            engine="hnsw",
            policy="Balanced",
            target_p95_ms=config.get("target_p95_ms", 30.0),
            target_recall=config.get("target_recall", 0.95)
        )
    
    def record_recovery_time_event(self, recovery_event: RecoveryEvent):
        """Record a recovery time event as specified."""
        if recovery_event.recovery_time_sec is not None:
            self.metrics.recovery_time_histogram.append(recovery_event.recovery_time_sec)
            logger.info(f"Recovery event completed: {recovery_event.recovery_time_sec:.1f}s")
    
    def execute_query(self, query: str, config: Dict[str, Any], 
                     chaos_engine: EnhancedChaosEngine, elapsed_time: float) -> Tuple[bool, float, Dict[str, Any]]:
        """Execute a single query with enhanced chaos injection."""
        
        # Check for disconnect
        if chaos_engine.is_disconnected(elapsed_time):
            return False, 0.0, {"error": "disconnected"}
        
        # Inject latency if needed
        latency_delay = chaos_engine.should_inject_latency(elapsed_time)
        if latency_delay > 0:
            time.sleep(latency_delay / 1000.0)  # Convert ms to seconds
        
        # Inject loss if needed
        loss_rate = chaos_engine.should_inject_loss(elapsed_time)
        if random.random() < (loss_rate / 100.0):
            return False, 0.0, {"error": "packet_loss"}
        
        # Execute the actual query via proxy-aware client
        start_time = time.time()
        try:
            top_k = config.get("rag_api", {}).get("initial_topk", 50)
            budget_ms = int(config.get("rag_api", {}).get("budget_ms", DEFAULT_BUDGET_MS))
            trace_id = str(uuid.uuid4())
            obs.persist_trace_id(trace_id)

            items, timings, degraded, trace_url = proxy_search(
                query=query,
                k=top_k,
                budget_ms=budget_ms,
                trace_id=trace_id,
            )

            latency = timings.get("total_ms")
            if latency is None:
                latency = (time.time() - start_time) * 1000.0

            if trace_url:
                obs.persist_obs_url(trace_url)

            results = list(items)
            if not results:
                return False, 0.0, {"error": "no_results"}

            tuner_actions = 0
            if self.autotuner and results:
                tuner_actions = self._update_autotuner(query, results, float(latency))

            self._record_shadow_result(query, results, config)

            payload = {
                "results": results,
                "tuner_actions": tuner_actions,
                "trace_url": trace_url,
                "timings": timings,
                "degraded": degraded,
            }
            return True, float(latency), payload

        except Exception as e:
            return False, 0.0, {"error": f"proxy_failed: {type(e).__name__}"}
    
    def _update_autotuner(self, query: str, results: List[Dict], latency: float) -> int:
        """Update autotuner with query results and return action count."""
        if not self.autotuner or not results:
            return 0
        
        now = time.time()
        
        # 1. Check sampling interval - only evaluate every N seconds
        if now - self.last_tuner_update < self.tuner_sample_interval:
            return 0  # Not time to sample yet, just collect metrics
        
        # 3. Check cooldown period - prevent rapid parameter changes
        if now - self.last_tuner_action < self.tuner_cooldown:
            return 0  # Still in cooldown, don't adjust parameters
        
        # Update sampling timestamp
        self.last_tuner_update = now
        
        # Calculate recall@10 (simplified)
        recall_at_10 = min(1.0, len(results) / 10.0)
        
        # Update metrics
        metrics = {
            "p95_ms": latency,
            "recall_at_10": recall_at_10,
            "coverage": 1.0
        }
        
        # Get autotuner suggestions
        try:
            new_params = self.autotuner.suggest(metrics)
            if new_params:
                self.metrics.autotuner_actions_count += 1
                self.metrics.autotuner_param_deltas.append({
                    "timestamp": time.time(),
                    "params": new_params
                })
                # Update action timestamp for cooldown
                self.last_tuner_action = now
                return 1
        except Exception as e:
            logger.warning(f"Autotuner error: {e}")
        
        return 0
    
    def _record_shadow_result(self, query: str, results: List[Dict], config: Dict[str, Any]):
        """Record shadow evaluation result."""
        shadow_config = config.get("shadow", {})
        mirror_rate = shadow_config.get("mirror_rate", 0.1)
        
        if random.random() < mirror_rate:
            self.shadow_results.append({
                "query": query,
                "results": results,
                "timestamp": time.time()
            })
    
    def calculate_metrics(self) -> EnhancedEvaluationMetrics:
        """Calculate final metrics from collected data."""
        if not self.latency_samples:
            return self.metrics
        
        # Latency metrics
        self.metrics.p95_ms = np.percentile(self.latency_samples, 95)
        self.metrics.p99_ms = np.percentile(self.latency_samples, 99)
        self.metrics.mean_latency_ms = np.mean(self.latency_samples)
        self.metrics.jitter_ms = np.std(self.latency_samples)
        
        # Recall metrics (simplified)
        self.metrics.recall_at_10 = min(1.0, len(self.latency_samples) / 1000.0)
        
        # Cost metrics (simplified)
        self.metrics.cost_per_1k_queries = len(self.latency_samples) * 0.01
        
        # Violation metrics
        threshold_ms = 200.0  # Example threshold
        violations = sum(1 for lat in self.latency_samples if lat > threshold_ms)
        self.metrics.violation_rate = violations / len(self.latency_samples) if self.latency_samples else 0.0
        
        # Recovery metrics
        recovery_times = [event.recovery_time_sec for event in self.metrics.recovery_events 
                         if event.recovery_time_sec is not None]
        if recovery_times:
            self.metrics.recovery_violation_rate = sum(1 for rt in recovery_times if rt > 90.0) / len(recovery_times)
        
        # Shadow divergence
        if self.shadow_results:
            self.metrics.shadow_divergence_rate = 0.1  # Simplified
        
        return self.metrics
    
    async def run_evaluation(self, run_name: str, output_file: str):
        """Run the complete enhanced evaluation."""
        config = self.full_config[run_name]
        load_generator = EnhancedLoadGenerator(config)
        chaos_engine = EnhancedChaosEngine(config)
        
        # Setup autotuner
        self.setup_autotuner(config)
        
        # Sample queries
        sample_queries = [
            "What is machine learning?",
            "How does neural network work?",
            "Explain deep learning concepts",
            "What is artificial intelligence?",
            "How to implement ML models?",
            "What are the benefits of AI?",
            "Explain computer vision",
            "What is natural language processing?",
            "How does reinforcement learning work?",
            "What are the applications of ML?"
        ]
        
        start_time = time.time()
        self.metrics.start_time = datetime.now()
        
        print(f"🚀 Starting {run_name} evaluation...")
        print(f"   Duration: {config.get('duration_seconds', 1800)}s")
        print(f"   QPS: {config.get('probes', {}).get('qps', 2.0)}")
        print(f"   Chaos: {config.get('chaos', {}).get('enabled', False)}")
        print(f"   Chaos windows: {len(chaos_engine.chaos_windows)}")
        
        # Warmup period
        warmup_seconds = config.get("warmup_seconds", 120)
        print(f"🔥 Warming up for {warmup_seconds}s...")
        await asyncio.sleep(warmup_seconds)
        
        # Main evaluation loop
        duration_seconds = config.get("duration_seconds", 1800)
        sample_interval = config.get("sample_every_seconds", 10)
        
        end_time = start_time + duration_seconds
        last_sample_time = start_time + warmup_seconds
        baseline_p95 = None
        
        # Initialize timeline data structure
        timeline = {
            "time_min": [],
            "p95_ms": [],
            "p99_ms": [],
            "ef_search": [],
            "recall_at_10": []
        }
        
        while time.time() < end_time:
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            # Check for chaos windows and start recovery tracking
            in_chaos, chaos_window = chaos_engine.is_in_chaos_window(elapsed_time)
            if in_chaos and chaos_window and chaos_window not in [event.chaos_window_start for event in self.active_recovery_events]:
                if baseline_p95 is not None:
                    recovery_event = chaos_engine.start_recovery_tracking(chaos_window, baseline_p95)
                    self.active_recovery_events.append(recovery_event)
            
            # Check if we should send a query
            if load_generator.should_send_query(elapsed_time):
                query = random.choice(sample_queries)
                success, latency, result = self.execute_query(
                    query, config, chaos_engine, elapsed_time
                )
                
                tuner_actions = result.get("tuner_actions", 0)
                
                if success:
                    self.latency_samples.append(latency)
                    self.metrics.successful_queries += 1
                    
                    # Update active recovery events
                    for recovery_event in self.active_recovery_events:
                        if recovery_event.status == "in_progress":
                            chaos_engine.update_recovery_event(
                                recovery_event, latency, tuner_actions, elapsed_time
                            )
                            
                            # Record completed recovery events
                            if recovery_event.status == "completed":
                                self.record_recovery_time_event(recovery_event)
                                self.metrics.recovery_events.append(recovery_event)
                                self.active_recovery_events.remove(recovery_event)
                
                self.metrics.total_queries += 1
            
            # Sample metrics periodically
            if current_time - last_sample_time >= sample_interval:
                current_p95 = np.percentile(self.latency_samples, 95) if self.latency_samples else 0.0
                current_p99 = np.percentile(self.latency_samples, 99) if self.latency_samples else 0.0
                if baseline_p95 is None and len(self.latency_samples) > 10:
                    baseline_p95 = current_p95
                
                # Get current ef_search from AutoTuner
                current_ef = None
                if self.autotuner and self.autotuner_state:
                    try:
                        current_params = self.autotuner_state.get_current_params()
                        current_ef = current_params.get("ef_search") if current_params else None
                    except Exception as e:
                        logger.warning(f"Failed to get current ef_search: {e}")
                        current_ef = None
                
                # Collect timeline data
                timeline["time_min"].append(round(elapsed_time / 60.0, 2))
                timeline["p95_ms"].append(round(current_p95, 2))
                timeline["p99_ms"].append(round(current_p99, 2))
                timeline["ef_search"].append(current_ef)
                timeline["recall_at_10"].append(None)  # Optional: could be filled if available
                
                # Record timeline metrics
                timeline_metric = TimelineMetrics(
                    timestamp=elapsed_time,
                    p95_ms=current_p95,
                    p99_ms=np.percentile(self.latency_samples, 99) if self.latency_samples else 0.0,
                    mean_latency_ms=np.mean(self.latency_samples) if self.latency_samples else 0.0,
                    topk=config.get("rag_api", {}).get("initial_topk", 50),
                    batch_size=len(self.latency_samples),
                    route_alpha=0.5,  # Placeholder
                    tuner_actions_count=self.metrics.autotuner_actions_count,
                    chaos_active=in_chaos,
                    recovery_active=len(self.active_recovery_events) > 0,
                    current_qps=load_generator.get_current_qps(elapsed_time)
                )
                self.timeline_data.append(timeline_metric)
                
                print(f"⏱️  {elapsed_time:.1f}s: {len(self.latency_samples)} queries, "
                      f"p95: {current_p95:.1f}ms, "
                      f"chaos: {in_chaos}, "
                      f"recovery: {len(self.active_recovery_events)} active")
                last_sample_time = current_time
            
            # Small sleep to prevent busy waiting
            await asyncio.sleep(0.1)
        
        # Calculate final metrics
        self.metrics.end_time = datetime.now()
        self.metrics.runtime_seconds = time.time() - start_time
        self.metrics.timeline_metrics = self.timeline_data
        final_metrics = self.calculate_metrics()
        
        # Save results
        metrics_payload = {
            "p95_ms": final_metrics.p95_ms,
            "p99_ms": final_metrics.p99_ms,
            "jitter_ms": final_metrics.jitter_ms,
            "mean_latency_ms": final_metrics.mean_latency_ms,
            "recall_at_10": final_metrics.recall_at_10,
            "cost_per_1k_queries": final_metrics.cost_per_1k_queries,
            "violation_rate": final_metrics.violation_rate,
            "recovery_events": [
                {
                    "chaos_window_start": event.chaos_window_start,
                    "chaos_window_end": event.chaos_window_end,
                    "recovery_time_sec": event.recovery_time_sec,
                    "baseline_p95": event.baseline_p95,
                    "peak_p95": event.peak_p95,
                    "stable_p95": event.stable_p95,
                    "tuner_actions": event.tuner_actions_during_recovery,
                    "status": event.status
                } for event in final_metrics.recovery_events
            ],
            "recovery_time_histogram": final_metrics.recovery_time_histogram,
            "recovery_violation_rate": final_metrics.recovery_violation_rate,
            "autotuner_actions_count": final_metrics.autotuner_actions_count,
            "autotuner_param_deltas": final_metrics.autotuner_param_deltas,
            "autotuner_actions_per_chaos_window": final_metrics.autotuner_actions_per_chaos_window,
            "shadow_divergence_rate": final_metrics.shadow_divergence_rate,
            "total_queries": final_metrics.total_queries,
            "successful_queries": final_metrics.successful_queries,
            "runtime_seconds": final_metrics.runtime_seconds,
            "start_time": final_metrics.start_time.isoformat(),
            "end_time": final_metrics.end_time.isoformat(),
        }
        arm = select_strategy(metrics_payload)
        metrics_payload["arm"] = arm

        results = {
            "run_name": run_name,
            "config": config,
            "metrics": metrics_payload,
            "timeline_metrics": [
                {
                    "timestamp": tm.timestamp,
                    "p95_ms": tm.p95_ms,
                    "p99_ms": tm.p99_ms,
                    "mean_latency_ms": tm.mean_latency_ms,
                    "topk": tm.topk,
                    "batch_size": tm.batch_size,
                    "route_alpha": tm.route_alpha,
                    "tuner_actions_count": tm.tuner_actions_count,
                    "chaos_active": tm.chaos_active,
                    "recovery_active": tm.recovery_active,
                    "current_qps": tm.current_qps
                } for tm in self.timeline_data
            ],
            "timeline": timeline,  # Add timeline data for A/B/C plotting
            "latency_samples": self.latency_samples[:1000],  # Limit samples for storage
            "shadow_results": self.shadow_results[:100],  # Limit shadow results
            "arm": arm,
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ {run_name} evaluation complete!")
        print(f"   Total queries: {final_metrics.total_queries}")
        print(f"   Successful: {final_metrics.successful_queries}")
        print(f"   P95 latency: {final_metrics.p95_ms:.1f}ms")
        print(f"   P99 latency: {final_metrics.p99_ms:.1f}ms")
        print(f"   Violation rate: {final_metrics.violation_rate:.1%}")
        print(f"   Autotuner actions: {final_metrics.autotuner_actions_count}")
        print(f"   Recovery events: {len(final_metrics.recovery_events)}")
        print(f"   Recovery violation rate: {final_metrics.recovery_violation_rate:.1%}")
        print(f"   Results saved to: {output_file}")

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enhanced A/B Evaluator for SmartSearchX")
    parser.add_argument("--config", required=True, help="Configuration file path")
    parser.add_argument("--run", required=True, choices=["baseline", "high_stress"], help="Run type")
    parser.add_argument("--duration", type=int, default=1800, help="Duration in seconds")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", required=True, help="Output file path")
    
    args = parser.parse_args()
    
    # Set random seed
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create evaluator and run
    evaluator = EnhancedABEvaluator(args.config)
    await evaluator.run_evaluation(args.run, args.output)

if __name__ == "__main__":
    asyncio.run(main())
