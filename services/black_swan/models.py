"""
Black Swan Async - Pydantic Models

Defines all data models for Black Swan async implementation:
- RunConfig: Configuration for a test run
- Phase: Test phase enumeration
- RunState: Current state of a test run
- Report: Final test report structure
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class Phase(str, Enum):
    """Test phases in order of execution."""
    WARMUP = "warmup"
    BASELINE = "baseline"
    TRIP = "trip"
    RECOVERY = "recovery"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELED = "canceled"


class RunMode(str, Enum):
    """Test modes with different stress patterns."""
    A = "A"  # High-Impact: burst + step pattern
    B = "B"  # Heavy Request: sustained load with heavy params
    C = "C"  # Net Delay: artificial latency simulation


class RunConfig(BaseModel):
    """Configuration for a Black Swan test run."""
    mode: RunMode = Field(default=RunMode.B, description="Test mode (A/B/C)")
    
    # Duration settings (in seconds)
    warmup_duration: int = Field(default=10, ge=5, le=300, description="Warmup duration (5-300s)")
    baseline_duration: int = Field(default=10, ge=5, le=300, description="Baseline duration (5-300s)")
    trip_duration: int = Field(default=60, ge=10, le=3600, description="Trip duration (10-3600s)")
    recovery_duration: int = Field(default=20, ge=10, le=600, description="Recovery duration (10-600s)")
    
    # Load settings
    warmup_qps: int = Field(default=20, ge=1, le=1000, description="Warmup QPS (1-1000)")
    baseline_qps: int = Field(default=50, ge=1, le=1000, description="Baseline QPS (1-1000)")
    trip_qps: int = Field(default=120, ge=1, le=2000, description="Trip QPS (1-2000)")
    recovery_qps: int = Field(default=50, ge=1, le=1000, description="Recovery QPS (1-1000)")
    
    # Concurrency & quality settings
    concurrency: int = Field(default=16, ge=1, le=256, description="Max concurrent requests (1-256)")
    
    # Query settings
    unique_queries: bool = Field(default=True, description="Use unique queries (round-robin)")
    bypass_cache: bool = Field(default=True, description="Add nocache parameters")
    
    # Heavy mode params (for mode B)
    candidate_k: Optional[int] = Field(default=None, ge=10, le=10000, description="Candidate K for retrieval")
    rerank_top_k: Optional[int] = Field(default=None, ge=1, le=1000, description="Rerank top K")
    
    # Additional overrides (applied via force_override)
    params: Dict[str, Any] = Field(default_factory=dict, description="Additional runtime parameters")
    
    class Config:
        use_enum_values = True


class Metrics(BaseModel):
    """Real-time metrics snapshot."""
    count: int = Field(default=0, description="Number of requests")
    qps: float = Field(default=0.0, description="Queries per second")
    p50_ms: Optional[float] = Field(default=None, description="P50 latency (ms)")
    p95_ms: Optional[float] = Field(default=None, description="P95 latency (ms)")
    p99_ms: Optional[float] = Field(default=None, description="P99 latency (ms)")
    max_ms: Optional[float] = Field(default=None, description="Max latency (ms)")
    error_rate: float = Field(default=0.0, description="Error rate (0-1)")
    errors: int = Field(default=0, description="Error count")


class GuardrailState(BaseModel):
    """Guardrail monitoring state."""
    enabled: bool = Field(default=True, description="Guardrails enabled")
    p95_threshold_ms: float = Field(default=200.0, description="P95 threshold (ms)")
    violated: bool = Field(default=False, description="Currently violated")
    violations: int = Field(default=0, description="Violation count")
    last_violation_ts: Optional[int] = Field(default=None, description="Last violation timestamp (ms)")


class WatchdogState(BaseModel):
    """Watchdog monitoring state."""
    enabled: bool = Field(default=True, description="Watchdog enabled")
    no_progress_threshold_sec: int = Field(default=30, description="No progress threshold (s)")
    p95_threshold_ms: float = Field(default=1000.0, description="P95 threshold for watchdog (ms)")
    triggered: bool = Field(default=False, description="Watchdog triggered")
    reason: Optional[str] = Field(default=None, description="Trigger reason")


class RunState(BaseModel):
    """Current state of a Black Swan test run."""
    run_id: str = Field(description="Unique run identifier")
    mode: RunMode = Field(description="Test mode")
    phase: Phase = Field(default=Phase.WARMUP, description="Current phase")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage (0-100)")
    eta_sec: int = Field(default=0, ge=0, description="Estimated time remaining (s)")
    
    # Timestamps (Unix epoch seconds)
    started_at: int = Field(description="Start timestamp")
    updated_at: int = Field(description="Last update timestamp")
    ended_at: Optional[int] = Field(default=None, description="End timestamp")
    
    # Phase timings
    phase_started_at: int = Field(description="Current phase start timestamp")
    phase_timers: Dict[str, int] = Field(default_factory=dict, description="Phase durations (seconds)")
    
    # Metrics
    metrics: Metrics = Field(default_factory=Metrics, description="Current metrics")
    
    # Guardrails & Watchdog
    guardrail_state: GuardrailState = Field(default_factory=GuardrailState)
    watchdog_state: WatchdogState = Field(default_factory=WatchdogState)
    
    # Force override precedence chain (for frontend display)
    precedence_chain: List[str] = Field(default_factory=list, description="Parameter precedence chain")
    
    # Messages & errors
    message: str = Field(default="", description="Current status message")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    class Config:
        use_enum_values = True


class PhaseReport(BaseModel):
    """Report for a single phase."""
    phase: str
    duration_sec: int
    metrics: Metrics
    qps_target: int
    qps_actual: float
    samples: int


class Report(BaseModel):
    """Final Black Swan test report."""
    run_id: str
    mode: RunMode
    timestamp: str  # ISO 8601
    
    # Configuration
    config: RunConfig
    
    # Phase reports
    warmup: PhaseReport
    baseline: PhaseReport
    trip: PhaseReport
    recovery: PhaseReport
    
    # Summary
    total_duration_sec: int
    total_requests: int
    total_errors: int
    
    # Force override info
    force_override_enabled: bool
    force_params: Dict[str, Any] = Field(default_factory=dict)
    hard_cap_enabled: bool
    hard_cap_limits: Dict[str, Any] = Field(default_factory=dict)
    precedence_chain: List[str] = Field(default_factory=list)
    
    # Guardrail events
    guardrail_violations: int = Field(default=0)
    watchdog_triggered: bool = Field(default=False)
    
    class Config:
        use_enum_values = True

