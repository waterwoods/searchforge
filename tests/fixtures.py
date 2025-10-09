"""
Test fixtures for AutoTuner Brain

Provides factory functions and test data for consistent test setup.
"""

import random
import numpy as np
from typing import Dict, Any, Optional
from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, Action


def make_input(**overrides) -> TuningInput:
    """
    Create a TuningInput with sane defaults, allowing overrides.
    
    Default values:
    - p95_ms=180, recall_at10=0.80, qps=10
    - params={ef:256, Ncand_max:400, rerank_mult:20, T:500}
    - slo={p95_ms:150, recall_at10:0.80}
    - guards={cooldown:False, stable:False}
    """
    defaults = {
        "p95_ms": 180.0,
        "recall_at10": 0.80,
        "qps": 10.0,
        "params": {
            "ef": 256,
            "Ncand_max": 400,
            "rerank_mult": 20,
            "T": 500
        },
        "slo": SLO(p95_ms=150.0, recall_at10=0.80),
        "guards": Guards(cooldown=False, stable=False),
        "near_T": False,
        "last_action": None,
        "adjustment_count": 0
    }
    
    # Apply overrides
    for key, value in overrides.items():
        if key in defaults:
            if isinstance(defaults[key], dict) and isinstance(value, dict):
                defaults[key].update(value)
            else:
                defaults[key] = value
    
    return TuningInput(**defaults)


def make_action(kind: str, step: float = 32.0, reason: str = "test", age_sec: float = 0.0) -> Action:
    """Create an Action with specified parameters."""
    return Action(kind=kind, step=step, reason=reason, age_sec=age_sec)


def make_slo(p95_ms: float = 150.0, recall_at10: float = 0.80) -> SLO:
    """Create an SLO with specified targets."""
    return SLO(p95_ms=p95_ms, recall_at10=recall_at10)


def make_guards(cooldown: bool = False, stable: bool = False) -> Guards:
    """Create Guards with specified flags."""
    return Guards(cooldown=cooldown, stable=stable)


# Test sequences for simulating improve/regress outcomes
IMPROVE_SEQUENCE = [
    {"p95_ms": 200.0, "recall_at10": 0.75},  # Initial: high latency, low recall
    {"p95_ms": 180.0, "recall_at10": 0.80},  # Better latency
    {"p95_ms": 160.0, "recall_at10": 0.82},  # Even better
    {"p95_ms": 150.0, "recall_at10": 0.85},  # Meeting SLO
]

REGRESS_SEQUENCE = [
    {"p95_ms": 120.0, "recall_at10": 0.85},  # Initial: good performance
    {"p95_ms": 140.0, "recall_at10": 0.82},  # Slight degradation
    {"p95_ms": 160.0, "recall_at10": 0.78},  # More degradation
    {"p95_ms": 180.0, "recall_at10": 0.75},  # Poor performance
]

OSCILLATE_SEQUENCE = [
    {"p95_ms": 160.0, "recall_at10": 0.80},
    {"p95_ms": 140.0, "recall_at10": 0.82},
    {"p95_ms": 160.0, "recall_at10": 0.80},
    {"p95_ms": 140.0, "recall_at10": 0.82},
    {"p95_ms": 160.0, "recall_at10": 0.80},
]


def set_random_seed(seed: int = 0):
    """Set random seeds for deterministic testing."""
    random.seed(seed)
    np.random.seed(seed)


def create_param_variations() -> list:
    """Create parameter variations for testing boundary conditions."""
    return [
        # Normal range
        {"ef": 128, "Ncand_max": 800, "rerank_mult": 4, "T": 600},
        # Lower bounds
        {"ef": 64, "Ncand_max": 500, "rerank_mult": 2, "T": 200},
        # Upper bounds  
        {"ef": 256, "Ncand_max": 2000, "rerank_mult": 6, "T": 1200},
        # Edge cases
        {"ef": 65, "Ncand_max": 501, "rerank_mult": 3, "T": 201},
        {"ef": 255, "Ncand_max": 1999, "rerank_mult": 5, "T": 1199},
    ]


def create_slo_variations() -> list:
    """Create SLO variations for testing different targets."""
    return [
        make_slo(p95_ms=100.0, recall_at10=0.90),   # Tight SLOs
        make_slo(p95_ms=200.0, recall_at10=0.70),   # Loose SLOs
        make_slo(p95_ms=150.0, recall_at10=0.80),   # Default SLOs
    ]


# Memory-related test fixtures
class MockMemory:
    """Mock memory for testing memory hook behavior."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.sweet_spots = {}
        self.lookup_count = 0
    
    def query(self, bucket_id: str):
        """Mock query that returns predefined sweet spots."""
        self.lookup_count += 1
        return self.sweet_spots.get(bucket_id)
    
    def default_bucket_of(self, inp):
        """Mock bucket ID generation."""
        return f"bucket_{hash(str(inp.params)) % 1000}"
    
    def add_sweet_spot(self, bucket_id: str, ef: int, meets_slo: bool = True, age_s: float = 100.0):
        """Add a mock sweet spot."""
        from modules.autotuner.brain.contracts import SweetSpot
        self.sweet_spots[bucket_id] = SweetSpot(
            ef=ef, T=500, meets_slo=meets_slo, age_s=age_s,
            ewma_p95=120.0, ewma_recall=0.85
        )
    
    def is_stale(self, bucket_id: str, ttl_s: float = 900.0) -> bool:
        """Mock is_stale method."""
        sweet_spot = self.sweet_spots.get(bucket_id)
        if not sweet_spot:
            return True
        return sweet_spot.age_s > ttl_s


# Multi-knob test fixtures
def make_multi_knob_input(**overrides) -> TuningInput:
    """
    Create a TuningInput optimized for multi-knob testing.
    
    Default values:
    - p95_ms=180, recall_at10=0.80, qps=10
    - params={ef:256, candidate_k:400, rerank_k:20, threshold_T:0.2}
    - slo={p95_ms:150, recall_at10:0.80}
    """
    defaults = {
        "p95_ms": 180.0,
        "recall_at10": 0.80,
        "qps": 10.0,
        "params": {
            "ef": 256,
            "candidate_k": 400,
            "rerank_k": 20,
            "threshold_T": 0.2
        },
        "slo": SLO(p95_ms=150.0, recall_at10=0.80),
        "guards": Guards(cooldown=False, stable=False),
        "near_T": False,
        "last_action": None,
        "adjustment_count": 0
    }
    
    # Apply overrides
    for key, value in overrides.items():
        if key in defaults:
            if isinstance(defaults[key], dict) and isinstance(value, dict):
                defaults[key].update(value)
            else:
                defaults[key] = value
    
    return TuningInput(**defaults)


def make_multi_knob_action(updates: dict, mode: str = "atomic", reason: str = "test") -> Action:
    """Create a multi-knob Action with specified updates."""
    return Action(
        kind="multi_knob",
        step=0.0,
        reason=reason,
        updates=updates,
        mode=mode
    )


def make_macros(L: float = 0.0, R: float = 0.0) -> dict:
    """Create macro indicators for testing."""
    return {"L": L, "R": R}
