"""
Black Swan Async - State Management

Manages in-memory state with optional Redis mirroring for Black Swan test runs.
Thread-safe with asyncio locks for concurrent access.
"""

import time
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any
from .models import RunState, RunConfig, Phase, Metrics, GuardrailState, WatchdogState, RunMode
from .storage import get_storage

logger = logging.getLogger(__name__)


class BlackSwanState:
    """
    Thread-safe state manager for Black Swan test runs.
    
    Maintains state in memory with optional Redis mirroring.
    Provides atomic updates and consistent reads.
    """
    
    def __init__(self, enable_redis: bool = True):
        """
        Initialize state manager.
        
        Args:
            enable_redis: Enable Redis mirroring (default True)
        """
        self._lock = asyncio.Lock()
        self._state: Optional[RunState] = None
        self._config: Optional[RunConfig] = None
        
        # Storage backend (with graceful degradation)
        self._storage = get_storage(enabled=enable_redis)
        
        logger.info(f"[BS:STATE] Initialized (Redis: {self._storage.is_available()})")
    
    async def start_run(self, config: RunConfig) -> str:
        """
        Start a new test run.
        
        Args:
            config: Run configuration
            
        Returns:
            Generated run ID
            
        Raises:
            RuntimeError: If a run is already in progress
        """
        async with self._lock:
            # Check if run already in progress
            if self._state is not None and self._state.phase not in [Phase.COMPLETE, Phase.ERROR, Phase.CANCELED]:
                raise RuntimeError(f"Run already in progress: {self._state.run_id}")
            
            # Generate new run ID
            run_id = str(uuid.uuid4())
            now = int(time.time())
            
            # Create initial state
            self._state = RunState(
                run_id=run_id,
                mode=config.mode,
                phase=Phase.WARMUP,
                progress=0,
                eta_sec=config.warmup_duration + config.baseline_duration + config.trip_duration + config.recovery_duration,
                started_at=now,
                updated_at=now,
                phase_started_at=now,
                message=f"Starting {config.mode} test run"
            )
            
            self._config = config
            
            # Mirror to Redis
            await self._mirror_to_redis()
            
            logger.info(f"[BS:STATE] Started run {run_id} (mode={config.mode})")
            return run_id
    
    async def update(
        self,
        phase: Optional[Phase] = None,
        progress: Optional[int] = None,
        eta_sec: Optional[int] = None,
        metrics: Optional[Metrics] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
        guardrail_state: Optional[GuardrailState] = None,
        watchdog_state: Optional[WatchdogState] = None,
        precedence_chain: Optional[list] = None
    ) -> bool:
        """
        Update current state.
        
        Args:
            phase: New phase (optional)
            progress: Progress percentage (optional)
            eta_sec: ETA in seconds (optional)
            metrics: Current metrics (optional)
            message: Status message (optional)
            error: Error message (optional)
            guardrail_state: Guardrail state (optional)
            watchdog_state: Watchdog state (optional)
            precedence_chain: Parameter precedence chain (optional)
            
        Returns:
            True if updated successfully
        """
        async with self._lock:
            if self._state is None:
                logger.warning("[BS:STATE] Update called but no run in progress")
                return False
            
            now = int(time.time())
            
            # Update phase (and track timing)
            if phase is not None and phase != self._state.phase:
                # Record previous phase duration
                if self._state.phase:
                    duration = now - self._state.phase_started_at
                    # Handle both string and enum (use_enum_values=True converts to string)
                    phase_key = self._state.phase if isinstance(self._state.phase, str) else self._state.phase.value
                    self._state.phase_timers[phase_key] = duration
                
                self._state.phase = phase
                self._state.phase_started_at = now
                # Handle both string and enum
                phase_str = phase if isinstance(phase, str) else phase.value
                logger.info(f"[BS:STATE] Phase changed to {phase_str}")
            
            # Update other fields
            if progress is not None:
                self._state.progress = max(0, min(100, progress))
            
            if eta_sec is not None:
                self._state.eta_sec = max(0, eta_sec)
            
            if metrics is not None:
                self._state.metrics = metrics
            
            if message is not None:
                self._state.message = message
            
            if error is not None:
                self._state.error = error
                self._state.phase = Phase.ERROR
            
            if guardrail_state is not None:
                self._state.guardrail_state = guardrail_state
            
            if watchdog_state is not None:
                self._state.watchdog_state = watchdog_state
            
            if precedence_chain is not None:
                self._state.precedence_chain = precedence_chain
            
            # Update timestamp
            self._state.updated_at = now
            
            # Check if run ended
            if self._state.phase in [Phase.COMPLETE, Phase.ERROR, Phase.CANCELED, "complete", "error", "canceled"]:
                if self._state.ended_at is None:
                    self._state.ended_at = now
                    # Record final phase duration
                    duration = now - self._state.phase_started_at
                    # Handle both string and enum
                    phase_key = self._state.phase if isinstance(self._state.phase, str) else self._state.phase.value
                    self._state.phase_timers[phase_key] = duration
            
            # Mirror to Redis
            await self._mirror_to_redis()
            
            return True
    
    async def get_state(self) -> Optional[RunState]:
        """
        Get current state.
        
        Returns:
            Current state or None if no run in progress
        """
        async with self._lock:
            return self._state.copy() if self._state else None
    
    async def get_config(self) -> Optional[RunConfig]:
        """
        Get current configuration.
        
        Returns:
            Current config or None if no run in progress
        """
        async with self._lock:
            return self._config.copy() if self._config else None
    
    async def complete(self, message: str = "Run completed successfully") -> bool:
        """
        Mark run as complete.
        
        Args:
            message: Completion message
            
        Returns:
            True if marked complete
        """
        return await self.update(
            phase=Phase.COMPLETE,
            progress=100,
            eta_sec=0,
            message=message
        )
    
    async def cancel(self, reason: str = "Run canceled by user") -> bool:
        """
        Cancel current run.
        
        Args:
            reason: Cancellation reason
            
        Returns:
            True if canceled
        """
        return await self.update(
            phase=Phase.CANCELED,
            progress=0,
            eta_sec=0,
            message=reason
        )
    
    async def fail(self, error: str) -> bool:
        """
        Mark run as failed.
        
        Args:
            error: Error message
            
        Returns:
            True if marked failed
        """
        return await self.update(
            phase=Phase.ERROR,
            progress=0,
            eta_sec=0,
            error=error,
            message=f"Run failed: {error}"
        )
    
    async def _mirror_to_redis(self) -> None:
        """Mirror current state to Redis (non-blocking)."""
        if self._state is None:
            return
        
        # Convert to dict for JSON serialization
        state_dict = self._state.dict()
        
        # Save to Redis (fire and forget, don't block on errors)
        try:
            self._storage.save_status(state_dict)
        except Exception as e:
            # Log but don't fail
            logger.debug(f"[BS:STATE] Redis mirror failed (degraded mode): {e}")
    
    def is_available(self) -> bool:
        """Check if Redis storage is available."""
        return self._storage.is_available()


# Global state instance
_global_state: Optional[BlackSwanState] = None


def get_state(enable_redis: bool = True) -> BlackSwanState:
    """
    Get or create global state instance.
    
    Args:
        enable_redis: Enable Redis mirroring
        
    Returns:
        BlackSwanState instance
    """
    global _global_state
    
    if _global_state is None:
        _global_state = BlackSwanState(enable_redis=enable_redis)
    
    return _global_state

