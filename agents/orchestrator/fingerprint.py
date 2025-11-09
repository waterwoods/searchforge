"""
Fingerprint utilities for experiment reproducibility and idempotency.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.orchestrator.flow import ExperimentPlan


def get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        repo_root = Path(__file__).parent.parent.parent
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=str(repo_root),
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:12]
    except Exception:
        pass
    return "unknown"


def compute_data_fingerprint(dataset: str, sample_size: int, config: Dict[str, Any]) -> str:
    """Compute fingerprint for dataset and sampling configuration."""
    data_key = {
        "dataset": dataset,
        "sample_size": sample_size,
        "seed": config.get("grid", {}).get("seed", 42),
    }
    data_str = json.dumps(data_key, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()[:16]


def compute_policy_hash(policies_path: str) -> str:
    """Compute hash of policies file."""
    try:
        path = Path(policies_path)
        if path.exists():
            content = path.read_bytes()
            return hashlib.sha256(content).hexdigest()[:16]
    except Exception:
        pass
    return "unknown"


def compute_args_hash(plan: "ExperimentPlan") -> str:
    """Compute hash of experiment plan arguments."""
    plan_dict = plan.to_dict()
    # Exclude metadata that doesn't affect execution
    plan_dict.pop("metadata", None)
    plan_str = json.dumps(plan_dict, sort_keys=True)
    return hashlib.sha256(plan_str.encode()).hexdigest()[:16]


def compute_fingerprints(
    plan: "ExperimentPlan",
    config: Dict[str, Any],
) -> Dict[str, str]:
    """Compute all fingerprints for an experiment run."""
    return {
        "data_fingerprint": compute_data_fingerprint(
            plan.dataset, plan.sample_size, config
        ),
        "code_commit": get_git_commit(),
        "policy_hash": compute_policy_hash(config.get("policies_path", "configs/policies.json")),
        "args_hash": compute_args_hash(plan),
    }

