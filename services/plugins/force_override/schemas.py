"""
Force Override Schemas
======================
Pydantic models for force override system.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ForceStatus(BaseModel):
    """
    Complete status of force override system including precedence trace.
    
    Precedence order:
    1. Request params (if provided)
    2. Force override (if enabled)
    3. Guardrails (placeholder - not yet implemented)
    4. Hard cap (if enabled)
    5. Defaults
    """
    
    ok: bool = Field(
        default=True,
        description="Whether the force status query was successful"
    )
    
    force_override: bool = Field(
        description="Whether FORCE_OVERRIDE is enabled"
    )
    
    hard_cap_enabled: bool = Field(
        description="Whether HARD_CAP is enabled"
    )
    
    planned_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters (e.g., from request)"
    )
    
    effective_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Final parameters after all overrides applied"
    )
    
    precedence_chain: List[str] = Field(
        default_factory=list,
        description="Ordered list of transformations applied (who overrode what)"
    )
    
    hard_cap_limits: Dict[str, Any] = Field(
        default_factory=dict,
        description="Active hard cap limits"
    )
    
    force_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Force override parameters from environment"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "force_override": True,
                "hard_cap_enabled": True,
                "planned_params": {"num_candidates": 100, "rerank_topk": 50, "qps": 60},
                "effective_params": {"num_candidates": 2000, "rerank_topk": 300, "qps": 180},
                "precedence_chain": [
                    "START: planned={'num_candidates': 100, 'rerank_topk': 50, 'qps': 60}",
                    "FORCE_OVERRIDE: num_candidates 100 → 2000",
                    "FORCE_OVERRIDE: rerank_topk 50 → 300",
                    "FORCE_OVERRIDE: qps 60 → 180",
                    "HARD_CAP: (no clamping needed)",
                    "END: effective={'num_candidates': 2000, 'rerank_topk': 300, 'qps': 180}"
                ],
                "hard_cap_limits": {"num_candidates": 5000, "rerank_topk": 1000, "qps": 2000},
                "force_params": {"num_candidates": 2000, "rerank_topk": 300, "qps": 180}
            }
        }


class OverrideEvent(BaseModel):
    """Event payload for force override events."""
    
    event_type: str = Field(
        description="Event type (e.g., 'force_override.applied')"
    )
    
    context: str = Field(
        description="Context where override was applied"
    )
    
    params_before: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters before override"
    )
    
    params_after: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters after override"
    )
    
    changes: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Detailed changes (key -> {from, to})"
    )

