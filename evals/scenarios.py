"""
Evaluation scenario definitions placeholder.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Scenario:
    name: str
    parameters: Dict[str, object]


def load_default_scenarios() -> List[Scenario]:
    return []

