"""
Experiment Configuration Models
================================
V10: Pydantic models for experiment configuration.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExperimentGroupConfig(BaseModel):
    """Configuration for a single experiment group."""
    model_config = ConfigDict(extra='forbid')
    
    name: str = Field(..., description="Experiment group name")
    use_hybrid: bool = Field(default=False, description="Enable hybrid search (BM25 + vector)")
    rrf_k: Optional[int] = Field(default=None, ge=1, le=1000, description="RRF fusion parameter")
    rerank: bool = Field(default=False, description="Enable reranking")
    rerank_top_k: Optional[int] = Field(default=None, ge=1, le=1000, description="Rerank candidate window")
    rerank_if_margin_below: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Rerank if score margin below threshold")
    max_rerank_trigger_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Max rerank trigger rate")
    rerank_budget_ms: Optional[int] = Field(default=None, ge=1, le=1000, description="Rerank budget in milliseconds")
    description: Optional[str] = Field(default=None, description="Human-readable description")


class ExperimentConfig(BaseModel):
    """V10: Complete experiment configuration for fiqa_suite_runner."""
    model_config = ConfigDict(extra='forbid')
    
    # Dataset settings
    base_url: str = Field(default="http://localhost:8011", description="Base API URL")
    dataset_name: str = Field(default="fiqa_10k_v1", description="Dataset name")
    qrels_name: str = Field(default="fiqa_qrels_10k_v1", description="Qrels name")
    qdrant_collection: str = Field(default="fiqa_10k_v1", description="Qdrant collection name")
    data_dir: str = Field(default="experiments/data/fiqa", description="Path to data directory")
    
    # Experiment parameters
    top_k: int = Field(default=50, ge=1, le=1000, description="Top-K retrieval parameter")
    repeats: int = Field(default=1, ge=1, le=10, description="Number of experiment repeats")
    warmup: int = Field(default=5, ge=0, le=100, description="Number of warmup queries")
    concurrency: int = Field(default=16, ge=1, le=256, description="Thread pool concurrency")
    sample: int = Field(default=200, ge=1, description="Sample N queries")
    
    # Fast mode settings
    fast_mode: bool = Field(default=False, description="Enable fast mode")
    fast_rrf_k: int = Field(default=40, ge=1, le=1000, description="RRF k for fast mode")
    fast_topk: int = Field(default=40, ge=1, le=1000, description="top_k for fast mode")
    fast_rerank_topk: int = Field(default=10, ge=1, le=1000, description="rerank_top_k for fast mode")
    
    # Experiment groups
    groups: List[ExperimentGroupConfig] = Field(default_factory=list, description="List of experiment groups to run")

