"""
Canary Executor for Configuration Deployments

This module implements the canary execution system with 90/10 traffic splitting,
metrics collection, and automatic rollback capabilities.
"""

import time
import json
import threading
import random
import uuid
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from .config_manager import ConfigManager, ConfigVersion
from .metrics_collector import MetricsCollector, record_search_metrics
from .slo_monitor import SLOMonitor

logger = logging.getLogger(__name__)


@dataclass
class CanaryResult:
    """Represents the result of a canary deployment."""
    deployment_id: str
    start_time: str
    end_time: Optional[str]
    status: str  # "running", "promoted", "rolled_back", "failed"
    active_config: str
    candidate_config: str
    last_good_config: str
    traffic_split: Dict[str, float]  # {"active": 0.9, "candidate": 0.1}
    metrics_summary: Dict[str, Any]
    rollback_reason: Optional[str]
    total_requests: int
    duration_seconds: Optional[float]


class CanaryExecutor:
    """
    Executes canary deployments with traffic splitting and monitoring.
    
    Features:
    - 90/10 traffic splitting between active and candidate configurations
    - Real-time metrics collection and SLO monitoring
    - Automatic rollback on SLO violations
    - Manual promotion/rollback capabilities
    - Comprehensive result reporting
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, 
                 metrics_collector: Optional[MetricsCollector] = None,
                 slo_monitor: Optional[SLOMonitor] = None,
                 traffic_split: Dict[str, float] = None):
        """
        Initialize the canary executor.
        
        Args:
            config_manager: Configuration manager instance
            metrics_collector: Metrics collector instance
            slo_monitor: SLO monitor instance
            traffic_split: Traffic split configuration (default: 90/10)
        """
        self.config_manager = config_manager or ConfigManager()
        if metrics_collector is None:
            from .metrics_collector import get_metrics_collector
            self.metrics_collector = get_metrics_collector()
        else:
            self.metrics_collector = metrics_collector
        
        if slo_monitor is None:
            from .slo_monitor import get_slo_monitor
            self.slo_monitor = get_slo_monitor()
        else:
            self.slo_monitor = slo_monitor
        
        # Traffic split configuration
        self.traffic_split = traffic_split or {"active": 0.9, "candidate": 0.1}
        
        # Execution state
        self._execution_lock = threading.Lock()
        self._is_running = False
        self._current_result: Optional[CanaryResult] = None
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # Set up rollback callback
        self.slo_monitor.set_rollback_callback(self._on_rollback_triggered)
        
        logger.info(f"CanaryExecutor initialized with traffic split: {self.traffic_split}")
    
    def start_canary(self, candidate_config_name: str, 
                    deployment_id: Optional[str] = None) -> CanaryResult:
        """
        Start a canary deployment with the specified candidate configuration.
        
        Args:
            candidate_config_name: Name of the candidate configuration
            deployment_id: Optional deployment ID (generated if not provided)
            
        Returns:
            CanaryResult object representing the deployment
            
        Raises:
            ValueError: If canary is already running or candidate config doesn't exist
            FileNotFoundError: If candidate configuration is not found
        """
        with self._execution_lock:
            if self._is_running:
                raise ValueError("Canary deployment is already running")
            
            # Validate candidate configuration exists
            try:
                candidate_config = self.config_manager.load_preset(candidate_config_name)
            except FileNotFoundError:
                raise FileNotFoundError(f"Candidate configuration '{candidate_config_name}' not found")
            
            # Generate deployment ID if not provided
            if not deployment_id:
                deployment_id = f"canary_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Start canary deployment
            self.config_manager.start_canary(candidate_config_name)
            
            # Create result object
            self._current_result = CanaryResult(
                deployment_id=deployment_id,
                start_time=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                end_time=None,
                status="running",
                active_config=self.config_manager.state.active_config,
                candidate_config=candidate_config_name,
                last_good_config=self.config_manager.state.last_good_config,
                traffic_split=self.traffic_split.copy(),
                metrics_summary={},
                rollback_reason=None,
                total_requests=0,
                duration_seconds=None
            )
            
            self._is_running = True
            self._stop_monitoring.clear()
            
            # Start monitoring thread
            self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self._monitoring_thread.start()
            
            logger.info(f"Started canary deployment {deployment_id} with candidate '{candidate_config_name}'")
            
            return self._current_result
    
    def stop_canary(self, promote: bool = False, reason: Optional[str] = None) -> CanaryResult:
        """
        Stop the current canary deployment.
        
        Args:
            promote: If True, promote candidate to active; if False, rollback
            reason: Optional reason for stopping the canary
            
        Returns:
            CanaryResult object with final status
            
        Raises:
            ValueError: If no canary deployment is running
        """
        # Check config manager state first
        config_state = self.config_manager.get_canary_status()
        
        with self._execution_lock:
            # Sync state if needed
            if config_state['status'] == 'running' and not self._current_result:
                self._is_running = True
                self._current_result = CanaryResult(
                    deployment_id=f"synced_{int(time.time())}",
                    start_time=config_state.get('canary_start_time', time.strftime("%Y-%m-%dT%H:%M:%SZ")),
                    end_time=None,
                    status="running",
                    active_config=config_state['active_config'],
                    candidate_config=config_state['candidate_config'],
                    last_good_config=config_state['last_good_config'],
                    traffic_split=self.traffic_split,
                    metrics_summary={},
                    rollback_reason=None,
                    total_requests=0,
                    duration_seconds=None
                )
            
            if not self._is_running or not self._current_result:
                raise ValueError("No canary deployment is currently running")
            
            # Stop monitoring
            self._stop_monitoring.set()
            if self._monitoring_thread and self._monitoring_thread.is_alive():
                self._monitoring_thread.join(timeout=5.0)
            
            # Update result
            self._current_result.end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            self._current_result.duration_seconds = time.time() - time.mktime(
                time.strptime(self._current_result.start_time, "%Y-%m-%dT%H:%M:%SZ")
            )
            
            if promote:
                # Promote candidate configuration
                self.config_manager.promote_candidate()
                self._current_result.status = "promoted"
                logger.info(f"Promoted canary deployment {self._current_result.deployment_id}")
            else:
                # Rollback to last good configuration
                rollback_reason = reason or "Manual rollback"
                self.config_manager.rollback_candidate(rollback_reason)
                self._current_result.status = "rolled_back"
                self._current_result.rollback_reason = rollback_reason
                logger.info(f"Rolled back canary deployment {self._current_result.deployment_id}: {rollback_reason}")
            
            # Final metrics summary
            self._current_result.metrics_summary = self._get_metrics_summary()
            
            self._is_running = False
            
            return self._current_result
    
    def execute_search(self, query: str, collection_name: str = "documents", 
                      trace_id: Optional[str] = None, **kwargs) -> Tuple[Any, str]:
        """
        Execute a search request with canary traffic splitting.
        
        Args:
            query: Search query
            collection_name: Collection name to search
            trace_id: Optional trace ID (generated if not provided)
            **kwargs: Additional arguments for search pipeline
            
        Returns:
            Tuple of (search_results, config_name_used)
        """
        if not self._is_running or not self._current_result:
            # No canary running, use active configuration
            active_config, _ = self.config_manager.get_current_configs()
            return self._execute_search_with_config(query, collection_name, active_config, trace_id, **kwargs)
        
        # Generate trace ID if not provided
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        # Determine which configuration to use based on traffic split
        config_name = self._select_config_for_request()
        
        # Load the appropriate configuration
        if config_name == "active":
            config = self.config_manager.load_preset(self._current_result.active_config)
        else:  # candidate
            config = self.config_manager.load_preset(self._current_result.candidate_config)
        
        # Execute search with selected configuration
        results = self._execute_search_with_config(query, collection_name, config, trace_id, **kwargs)
        
        # Update request count
        with self._execution_lock:
            if self._current_result:
                self._current_result.total_requests += 1
        
        return results, config.name
    
    def _select_config_for_request(self) -> str:
        """
        Select which configuration to use for a request based on traffic split.
        
        Returns:
            "active" or "candidate"
        """
        rand = random.random()
        if rand < self.traffic_split["candidate"]:
            return "candidate"
        else:
            return "active"
    
    def _execute_search_with_config(self, query: str, collection_name: str, 
                                   config: ConfigVersion, trace_id: str, **kwargs) -> Any:
        """
        Execute search with a specific configuration.
        
        Args:
            query: Search query
            collection_name: Collection name
            config: Configuration to use
            trace_id: Trace ID for the request
            **kwargs: Additional arguments
            
        Returns:
            Search results
        """
        # Set environment variables for the search pipeline
        import os
        os.environ["LATENCY_GUARD"] = str(config.macro_knobs["latency_guard"])
        os.environ["RECALL_BIAS"] = str(config.macro_knobs["recall_bias"])
        
        # Create search pipeline from config
        from modules.search.search_pipeline import SearchPipeline
        
        pipeline_config = {
            "retriever": config.retriever,
            "reranker": config.reranker
        }
        
        pipeline = SearchPipeline(pipeline_config)
        
        # Execute search
        start_time = time.perf_counter()
        results = pipeline.search(query, collection_name, trace_id=trace_id, **kwargs)
        end_time = time.perf_counter()
        
        # Calculate metrics
        latency_ms = (end_time - start_time) * 1000.0
        recall_at_10 = min(1.0, len(results) / 10.0)  # Simplified recall calculation
        
        # Record metrics
        record_search_metrics(
            trace_id=trace_id,
            latency_ms=latency_ms,
            recall_at_10=recall_at_10,
            config_name=config.name,
            slo_p95_ms=config.slo["p95_ms"]
        )
        
        return results
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop for SLO violations."""
        logger.info("Started canary monitoring loop")
        
        while not self._stop_monitoring.is_set():
            try:
                # Get completed metrics buckets
                completed_buckets = self.metrics_collector.get_completed_buckets()
                
                if completed_buckets:
                    # Process buckets for SLO violations
                    violations = self.slo_monitor.process_buckets(completed_buckets)
                    
                    if violations:
                        logger.warning(f"Detected {len(violations)} SLO violations")
                
                # Sleep for a short interval
                self._stop_monitoring.wait(1.0)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)
        
        logger.info("Stopped canary monitoring loop")
    
    def _on_rollback_triggered(self, reason: str) -> None:
        """Callback for automatic rollback triggered by SLO monitor."""
        logger.error(f"Automatic rollback triggered: {reason}")
        
        # Stop canary with rollback
        try:
            self.stop_canary(promote=False, reason=reason)
        except ValueError:
            # Canary might already be stopped
            pass
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of metrics for the canary deployment."""
        if not self._current_result:
            return {}
        
        # Get metrics for both configurations
        active_summary = self.metrics_collector.get_summary_stats(
            self._current_result.active_config, window_minutes=10
        )
        candidate_summary = self.metrics_collector.get_summary_stats(
            self._current_result.candidate_config, window_minutes=10
        )
        
        return {
            "active_config": active_summary,
            "candidate_config": candidate_summary,
            "traffic_split": self.traffic_split,
            "total_requests": self._current_result.total_requests
        }
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current canary deployment status.
        
        Returns:
            Dictionary with current status information
        """
        # Check config manager state first
        config_state = self.config_manager.get_canary_status()
        
        with self._execution_lock:
            # If config manager says running but executor doesn't have a result, sync state
            if config_state['status'] == 'running' and not self._current_result:
                self._is_running = True
                self._current_result = CanaryResult(
                    deployment_id=f"synced_{int(time.time())}",
                    start_time=config_state.get('canary_start_time', time.strftime("%Y-%m-%dT%H:%M:%SZ")),
                    end_time=None,
                    status="running",
                    active_config=config_state['active_config'],
                    candidate_config=config_state['candidate_config'],
                    last_good_config=config_state['last_good_config'],
                    traffic_split=self.traffic_split,
                    metrics_summary={},
                    rollback_reason=None,
                    total_requests=0,
                    duration_seconds=None
                )
            
            # If config manager says not running but executor thinks it is, sync state
            elif config_state['status'] != 'running' and self._is_running:
                self._is_running = False
                self._current_result = None
            
            if not self._is_running or not self._current_result:
                return {
                    "is_running": False,
                    "status": "idle"
                }
            
            return {
                "is_running": True,
                "deployment_id": self._current_result.deployment_id,
                "status": self._current_result.status,
                "active_config": self._current_result.active_config,
                "candidate_config": self._current_result.candidate_config,
                "traffic_split": self._current_result.traffic_split,
                "total_requests": self._current_result.total_requests,
                "start_time": self._current_result.start_time,
                "duration_seconds": time.time() - time.mktime(
                    time.strptime(self._current_result.start_time, "%Y-%m-%dT%H:%M:%SZ")
                ) if self._current_result.start_time else None
            }
    
    def export_result_to_json(self, output_file: str) -> None:
        """
        Export the current canary result to a JSON file.
        
        Args:
            output_file: Output file path
        """
        # Try to sync state first
        config_state = self.config_manager.get_canary_status()
        
        if not self._current_result and config_state['status'] in ['promoted', 'rolled_back']:
            # Create a result from config state for completed deployments
            self._current_result = CanaryResult(
                deployment_id=f"exported_{int(time.time())}",
                start_time=config_state.get('canary_start_time', time.strftime("%Y-%m-%dT%H:%M:%SZ")),
                end_time=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                status=config_state['status'],
                active_config=config_state['active_config'],
                candidate_config=config_state.get('candidate_config', ''),
                last_good_config=config_state['last_good_config'],
                traffic_split=self.traffic_split,
                metrics_summary={},
                rollback_reason=None,
                total_requests=0,
                duration_seconds=None
            )
        
        if not self._current_result:
            raise ValueError("No canary result to export")
        
        export_data = asdict(self._current_result)
        
        try:
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Exported canary result to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export canary result to {output_file}: {e}")
            raise
    
    def get_metrics_export(self, output_file: str) -> None:
        """
        Export metrics to JSON file.
        
        Args:
            output_file: Output file path
        """
        self.metrics_collector.export_buckets_to_json(output_file)
    
    def get_violations_export(self, output_file: str) -> None:
        """
        Export SLO violations to JSON file.
        
        Args:
            output_file: Output file path
        """
        self.slo_monitor.export_violations_to_json(output_file)


# Global canary executor instance
_global_canary_executor: Optional[CanaryExecutor] = None


def get_canary_executor() -> CanaryExecutor:
    """Get the global canary executor instance."""
    global _global_canary_executor
    if _global_canary_executor is None:
        _global_canary_executor = CanaryExecutor()
    return _global_canary_executor
