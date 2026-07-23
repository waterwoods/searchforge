"""P28 Voice Story metrics — frozen definitions from ADR §4."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def emit_voice_metric(event: str, **fields: Any) -> None:
    """Structured log sink for STT success rate, duration, edit distance, completion."""
    payload = {"event": event, **fields}
    logger.info("p28_voice_metric %s", payload)


def normalized_levenshtein(a: str, b: str) -> tuple[int, float]:
    """Character-level Levenshtein; returns (raw_distance, normalized 0..1)."""
    left = a or ""
    right = b or ""
    if left == right:
        return 0, 0.0
    if not left or not right:
        dist = max(len(left), len(right))
        return dist, 1.0
    # Classic DP (story lengths are bounded by CLAIM_MAX_DESCRIPTION_LENGTH).
    prev = list(range(len(right) + 1))
    for i, ca in enumerate(left, start=1):
        cur = [i]
        for j, cb in enumerate(right, start=1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            cur.append(min(ins, delete, sub))
        prev = cur
    dist = prev[-1]
    norm = dist / max(len(left), len(right))
    return dist, round(norm, 6)
