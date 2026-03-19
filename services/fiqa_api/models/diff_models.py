"""
diff_models.py - Diff Models for A/B Comparison
===============================================
V11: Pydantic models for comparing two experiment jobs.
"""

from typing import Dict, Any, List, Literal, Union
from pydantic import BaseModel, Field, field_validator


class DiffMetrics(BaseModel):
    """Metrics for a single job."""
    recall_at_10: float = Field(..., description="Recall@10 score")
    p95_ms: float = Field(..., description="95th percentile latency in milliseconds")
    cost_per_query: float = Field(..., description="Cost per query in USD")


class DiffMeta(BaseModel):
    """Metadata for diff comparison."""
    dataset_name: str = Field(..., description="Dataset name")
    schema_version: int = Field(..., description="Schema version")
    git_sha: str = Field(..., description="Git SHA")
    git_sha_source: Literal["env", "git", "unknown"] = Field(..., description="Source of git SHA")
    created_at: Dict[str, str] = Field(..., description="Created at timestamp for A and B jobs")
    
    @field_validator('created_at', mode='before')
    @classmethod
    def normalize_created_at(cls, v: Union[str, Dict[str, str]]) -> Dict[str, str]:
        """
        Backward compatibility: accept string (old format) or Dict[str, str] (new format).
        If string is provided, set both A and B to the same value.
        """
        if isinstance(v, str):
            # Old format: single string -> set both A and B
            return {"A": v, "B": v}
        elif isinstance(v, dict):
            # New format: already a dict
            return v
        else:
            raise ValueError(f"created_at must be str or Dict[str, str], got {type(v)}")


class DiffResponse(BaseModel):
    """Response model for diff endpoint (V11 contract)."""
    metrics: Dict[str, DiffMetrics] = Field(..., description="Metrics for both jobs (keys: 'A', 'B')")
    params_diff: Dict[str, List[Any]] = Field(default_factory=dict, description="Parameter differences (only keys with different values, format: [a, b])")
    meta: DiffMeta = Field(..., description="Metadata (dataset_name, schema_version, git_sha, created_at)")

