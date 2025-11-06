"""
Auto-Tuner Strategy System
Minimal, safe parameter tuning focused on P95 latency stability
"""
import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Demo visibility tuning (reversible via env)
TUNER_TICK_SEC = int(os.getenv("TUNER_TICK_SEC", "5"))  # Default 5s, set to 3 for fast demo
TUNER_STEP_K = int(os.getenv("TUNER_STEP_K", "16"))    # Default 16, larger for visible effects
TUNER_STEP_EF = int(os.getenv("TUNER_STEP_EF", "16"))  # Default 16, larger for visible effects
K_MIN = int(os.getenv("K_MIN", "16"))
K_MAX = int(os.getenv("K_MAX", "800"))
EF_MIN = int(os.getenv("EF_MIN", "16"))
EF_MAX = int(os.getenv("EF_MAX", "800"))


# Setup tuner logger (shared with app.py)
def get_tuner_logger():
    """Get or create tuner logger with rotating file handler"""
    logger = logging.getLogger("tuner")
    
    # If already configured, return it (check _configured flag)
    if hasattr(logger, '_configured') and logger._configured:
        return logger
    
    # Standalone configuration (if tuner.py is used independently)
    logger.setLevel(logging.INFO)
    
    log_dir = Path(__file__).parent.parent.parent / "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = log_dir / "tuner.log"
    
    # RotatingFileHandler: 10MB max, 5 backup files
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter with milliseconds
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(levelname)s [TUNER] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Mark as configured
    logger._configured = True
    
    return logger

tuner_logger = get_tuner_logger()


@dataclass
class TunerParams:
    """Tunable parameters for search pipeline"""
    topk: int = 128
    ef: int = 128
    parallel: int = 4


def clamp(params: TunerParams, bounds: dict = None) -> TunerParams:
    """Enforce parameter bounds (configurable via env for demo visibility)"""
    if bounds is None:
        bounds = {
            "topk": (K_MIN, K_MAX),
            "ef": (EF_MIN, EF_MAX),
            "parallel": (1, 16)
        }
    
    return TunerParams(
        topk=max(bounds["topk"][0], min(bounds["topk"][1], params.topk)),
        ef=max(bounds["ef"][0], min(bounds["ef"][1], params.ef)),
        parallel=max(bounds["parallel"][0], min(bounds["parallel"][1], params.parallel))
    )


class BaseStrategy(ABC):
    """Base class for tuning strategies"""
    
    @abstractmethod
    def name(self) -> str:
        """Return strategy name"""
        pass
    
    @abstractmethod
    def step(self, *, target_p95: int, last_p95: float | None, params: TunerParams) -> TunerParams:
        """
        Compute next parameter values based on current SLA state
        
        Args:
            target_p95: Target P95 latency in ms
            last_p95: Last observed P95 in ms (60-90s window), None if no data
            params: Current parameters
        
        Returns:
            New parameters (clamped to bounds)
        """
        pass


class DefaultStrategy(BaseStrategy):
    """No-op strategy: returns parameters unchanged"""
    
    def name(self) -> str:
        return "default"
    
    def step(self, *, target_p95: int, last_p95: float | None, params: TunerParams) -> TunerParams:
        """No changes"""
        return params


class LinearOnlyStrategy(BaseStrategy):
    """
    Conservative linear tuning strategy
    Goal: "先稳 P95 再换 Recall" - stabilize P95 first, then improve recall
    Only adjusts topk, ef, parallel (no reranker mode switching)
    """
    
    def name(self) -> str:
        return "linear_only"
    
    def step(self, *, target_p95: int, last_p95: float | None, params: TunerParams) -> TunerParams:
        """
        Adjust parameters based on P95 vs target (step sizes configurable via env for demo visibility)
        
        Logic:
        - If P95 > 1.1 * target: reduce load (decrease topk/ef/parallel)
        - If P95 < 0.8 * target: increase quality (increase topk/ef)
        - Otherwise: maintain current settings
        """
        if last_p95 is None:
            # No data yet, maintain current params
            tuner_logger.info(f"[TUNER] step hold (no P95 data) → topk={params.topk} ef={params.ef} parallel={params.parallel}")
            return params
        
        new_params = TunerParams(topk=params.topk, ef=params.ef, parallel=params.parallel)
        action = "HOLD"
        reason = "within_target"
        
        if last_p95 > 1.1 * target_p95:
            # Over SLA: reduce latency
            # Priority: reduce topk first, then ef, then parallel
            old_topk, old_ef = params.topk, params.ef
            new_params.topk = max(K_MIN, params.topk - TUNER_STEP_K)
            new_params.ef = max(EF_MIN, params.ef - TUNER_STEP_EF)
            if new_params.topk <= 48:
                # Only reduce parallel if already at low topk
                new_params.parallel = max(1, params.parallel - 1)
            
            action = "REDUCE"
            reason = f"p95_high ({last_p95:.1f} > {1.1*target_p95:.1f})"
            tuner_logger.info(f"[TUNER] step action={action} reason={reason} k:{old_topk}→{new_params.topk} ef:{old_ef}→{new_params.ef} parallel:{params.parallel}→{new_params.parallel}")
        
        elif last_p95 < 0.8 * target_p95:
            # Under SLA: improve quality
            # Priority: increase topk first (better recall), then ef
            old_topk, old_ef = params.topk, params.ef
            new_params.topk = min(K_MAX, params.topk + TUNER_STEP_K)
            new_params.ef = min(EF_MAX, params.ef + TUNER_STEP_EF)
            
            action = "INCREASE"
            reason = f"p95_low ({last_p95:.1f} < {0.8*target_p95:.1f})"
            tuner_logger.info(f"[TUNER] step action={action} reason={reason} k:{old_topk}→{new_params.topk} ef:{old_ef}→{new_params.ef} parallel:{params.parallel}→{new_params.parallel}")
        
        else:
            # Within acceptable range: maintain
            tuner_logger.info(f"[TUNER] step action=HOLD reason=within_target p95={last_p95:.1f} target={target_p95} topk={params.topk} ef={params.ef} parallel={params.parallel}")
        
        return clamp(new_params)


class StrategyRegistry:
    """Registry for tuning strategies"""
    
    _strategies = {
        "default": DefaultStrategy(),
        "linear_only": LinearOnlyStrategy()
    }
    
    @classmethod
    def get(cls, name: str) -> BaseStrategy:
        """Get strategy by name, fallback to default"""
        return cls._strategies.get(name, cls._strategies["default"])
    
    @classmethod
    def available(cls) -> list[str]:
        """List available strategy names"""
        return list(cls._strategies.keys())


# Singleton registry instance
REG = StrategyRegistry

