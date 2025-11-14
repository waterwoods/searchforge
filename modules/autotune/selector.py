"""Strategy selection shim for Bandit-free baseline."""

from typing import Dict


def select_strategy(metrics: Dict) -> str:
    """
    Select strategy arm based on current metrics snapshot.

    With Bandit disabled we always return the stable baseline arm so that
    downstream reports (.runs/*) keep a consistent JSON contract.
    """
    return "baseline"

