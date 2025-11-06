"""
Control plugin for app_main integration.

Manages control flow shaping: signals, policy, actuators.
Provides hot-reload from Redis and fail-safe operation.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import time
import json

from modules.control.signals import P95Signal, QueueDepthSignal
from modules.control.policy import AIMDPolicy, PIDPolicy
from modules.control.actuators import ConcurrencyActuator, BatchSizeActuator

logger = logging.getLogger(__name__)


class ControlPlugin:
    """
    Control flow shaping plugin.
    
    Integrates signals, policy, and actuators into a unified control loop.
    """
    
    def __init__(self):
        # Signals
        self.signals = {
            "p95": P95Signal(target_ms=100.0),
            "queue_depth": QueueDepthSignal(max_depth=100)
        }
        
        # Policies
        self.policies = {
            "aimd": AIMDPolicy(),
            "pid": PIDPolicy()
        }
        self.active_policy = "aimd"
        
        # Actuators
        self.actuators = {
            "concurrency": ConcurrencyActuator(),
            "batch_size": BatchSizeActuator()
        }
        
        # Configuration
        self.enabled_signals = {"p95", "queue_depth"}
        self.enabled_actuators = {"concurrency", "batch_size"}
        
        # Decision log (last 200)
        self.decisions: List[Dict[str, Any]] = []
        self.max_decisions = 200
        
        # Control loop state
        self.loop_running = False
        self.loop_task: Optional[asyncio.Task] = None
        self.loop_interval = 10  # seconds
        
        # Redis/memory mode
        self.redis_available = False
        self.storage_backend = "memory"
    
    async def start_control_loop(self):
        """Start the control loop."""
        if self.loop_running:
            logger.warning("Control loop already running")
            return
        
        self.loop_running = True
        self.loop_task = asyncio.create_task(self._control_loop())
        logger.info("Control loop started")
    
    async def stop_control_loop(self):
        """Stop the control loop."""
        if not self.loop_running:
            return
        
        self.loop_running = False
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Control loop stopped")
    
    async def _control_loop(self):
        """Main control loop."""
        while self.loop_running:
            try:
                await self._tick()
                await asyncio.sleep(self.loop_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Control loop error: {e}")
                await asyncio.sleep(self.loop_interval)
    
    async def _tick(self):
        """Single control loop iteration."""
        start_time = time.time()
        
        # 1. Read signals
        signal_readings = {}
        for name in self.enabled_signals:
            if name in self.signals:
                result = await self.signals[name].safe_read()
                if result["ok"]:
                    signal_readings[name] = result["value"]
        
        if not signal_readings:
            return  # No valid signals
        
        # 2. Make policy decision
        policy = self.policies.get(self.active_policy)
        if not policy:
            return
        
        decision = await policy.decide(signal_readings)
        
        # 3. Apply actuators
        actuator_results = []
        if decision["action"] != "hold":
            for name in self.enabled_actuators:
                if name in self.actuators:
                    result = await self.actuators[name].apply(
                        decision["adjustment"],
                        decision["reason"]
                    )
                    actuator_results.append(result)
        
        # 4. Log decision
        decision_record = {
            "timestamp": start_time,
            "signals": signal_readings,
            "policy": self.active_policy,
            "decision": decision,
            "actuators": actuator_results,
            "duration_ms": (time.time() - start_time) * 1000
        }
        
        self.decisions.append(decision_record)
        if len(self.decisions) > self.max_decisions:
            self.decisions = self.decisions[-self.max_decisions:]
        
        logger.debug(f"Control tick: {decision['action']} @ {decision['adjustment']:.2f}x")
    
    async def set_policy(self, policy_name: str) -> Dict[str, Any]:
        """Switch active policy."""
        if policy_name not in self.policies:
            return {
                "ok": False,
                "error": "unknown_policy",
                "available": list(self.policies.keys())
            }
        
        old_policy = self.active_policy
        self.active_policy = policy_name
        
        # Reset policy state
        if hasattr(self.policies[policy_name], "reset"):
            self.policies[policy_name].reset()
        
        return {
            "ok": True,
            "old_policy": old_policy,
            "new_policy": policy_name
        }
    
    async def set_flags(self, flags: Dict[str, Any]) -> Dict[str, Any]:
        """Update feature flags."""
        changes = []
        
        if "signals" in flags:
            self.enabled_signals = set(flags["signals"])
            changes.append(f"signals={flags['signals']}")
        
        if "actuators" in flags:
            self.enabled_actuators = set(flags["actuators"])
            changes.append(f"actuators={flags['actuators']}")
        
        if "policy" in flags:
            result = await self.set_policy(flags["policy"])
            if result["ok"]:
                changes.append(f"policy={flags['policy']}")
        
        return {
            "ok": True,
            "changes": changes
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get control plugin status."""
        return {
            "enabled": self.loop_running,
            "policy": self.active_policy,
            "signals": {
                name: sig.get_status()
                for name, sig in self.signals.items()
            },
            "enabled_signals": list(self.enabled_signals),
            "actuators": {
                name: act.get_status()
                for name, act in self.actuators.items()
            },
            "enabled_actuators": list(self.enabled_actuators),
            "decision_count": len(self.decisions),
            "storage_backend": self.storage_backend
        }
    
    def get_decisions(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Get recent decisions."""
        return self.decisions[-limit:]


# Global instance
_control_plugin: Optional[ControlPlugin] = None


def get_control_plugin() -> ControlPlugin:
    """Get or create control plugin instance."""
    global _control_plugin
    if _control_plugin is None:
        _control_plugin = ControlPlugin()
    return _control_plugin

