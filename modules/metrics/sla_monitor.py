from __future__ import annotations
from dataclasses import dataclass
from typing import Deque, Literal, Tuple
from collections import deque
import time, os
import numpy as np

BreachLevel = Literal["none", "soft", "hard"]

@dataclass
class SlaTargets:
    p95_target_ms: float = 120.0
    p99_hard_ms: float = 250.0
    window_seconds: int = 30
    min_samples: int = 30
    enabled: bool = True  # global switch (config-level)

class SlaMonitor:
    """
    Sliding-window SLA monitor with a global enable switch.
    If disabled (by env or config), sampling is skipped and evaluate() returns ("none", 0, 0, 0).
    """
    def __init__(self, targets: SlaTargets):
        self.t = targets
        self.buf: Deque[Tuple[float, float]] = deque()
        # Environment override (highest priority)
        env_flag = os.getenv("AUTOTUNER_ENABLED")
        if env_flag is not None:
            self.t.enabled = env_flag.lower() in ("1", "true", "yes", "on")

    def feed(self, latency_ms: float, ts: float | None = None) -> None:
        if not self.t.enabled:
            return  # disabled: do not sample
        ts = ts or time.time()
        self.buf.append((ts, float(latency_ms)))
        cutoff = ts - self.t.window_seconds
        while self.buf and self.buf[0][0] < cutoff:
            self.buf.popleft()

    def _values(self):
        return np.array([v for _, v in self.buf], dtype=float)

    def evaluate(self) -> tuple[BreachLevel, float, float, int]:
        if not self.t.enabled:
            return "none", 0.0, 0.0, 0
        vals = self._values()
        n = int(vals.size)
        if n < self.t.min_samples:
            return "none", 0.0, 0.0, n
        p95 = float(np.percentile(vals, 95))
        p99 = float(np.percentile(vals, 99))
        if p99 >= self.t.p99_hard_ms:
            return "hard", p95, p99, n
        if p95 >= self.t.p95_target_ms:
            return "soft", p95, p99, n
        return "none", p95, p99, n