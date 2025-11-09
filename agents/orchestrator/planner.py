"""
Planner module responsible for constructing experiment execution plans.

Milestone M0 only requires a skeletal implementation so that unit tests and
integration points can be wired. Detailed planning logic will be implemented in
subsequent milestones.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Sequence

if TYPE_CHECKING:
    from agents.orchestrator.flow import ExperimentPlan


@dataclass
class GridTask:
    config_id: str
    parameters: Dict[str, Any]


@dataclass
class GridBatch:
    batch_id: str
    tasks: List[GridTask]
    concurrency: int


def _normalize_list(values: Any) -> List[Any]:
    if values is None:
        return []
    if isinstance(values, (list, tuple, set)):
        return list(values)
    return [values]


def _normalize_mmr(value: Any) -> Dict[str, Any]:
    if isinstance(value, bool):
        return {"mmr": value, "mmr_lambda": 0.3 if value else 0.0}
    if value is None:
        return {"mmr": False, "mmr_lambda": 0.0}
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid mmr configuration: {value}") from exc
    if num <= 0:
        return {"mmr": False, "mmr_lambda": 0.0}
    return {"mmr": True, "mmr_lambda": num}


def _sorted_unique_numeric(values: Iterable[Any], *, cast=int) -> List[int]:
    result = sorted({cast(v) for v in values})
    if not result:
        raise ValueError("Grid search values cannot be empty.")
    return result


def make_grid(plan: "ExperimentPlan", cfg: Dict[str, Any]) -> List[GridBatch]:
    """Create deterministic grid batches from plan and config."""
    grid_cfg = cfg.get("grid") or {}
    reflection_cfg = cfg.get("reflection") or {}

    sample = int(grid_cfg.get("sample", plan.sample_size))
    if plan.concurrency is not None:
        concurrency = int(plan.concurrency)
    else:
        concurrency = int(grid_cfg.get("concurrency") or 1)
    if concurrency <= 0:
        raise ValueError("Grid concurrency must be positive.")

    search_space = plan.search_space or {}
    top_k_values = _normalize_list(search_space.get("top_k") or grid_cfg.get("top_k"))
    mmr_values = _normalize_list(search_space.get("mmr") or grid_cfg.get("mmr"))
    ef_search_values = _normalize_list(search_space.get("ef_search") or grid_cfg.get("ef_search"))

    top_k_values = _sorted_unique_numeric(top_k_values, cast=int)
    ef_search_values = _sorted_unique_numeric(ef_search_values, cast=int)

    # Deterministic ordering for mmr entries: disabled first, then ascending lambda.
    mmr_entries: List[Dict[str, Any]] = []
    for value in mmr_values:
        mmr_entries.append(_normalize_mmr(value))
    mmr_entries = sorted(
        mmr_entries,
        key=lambda item: (item["mmr"], item["mmr_lambda"] if item["mmr"] else 0.0),
    )

    tasks: List[GridTask] = []
    for top_k in top_k_values:
        for mmr_entry in mmr_entries:
            for ef_search in ef_search_values:
                mmr_flag = mmr_entry["mmr"]
                mmr_lambda = mmr_entry["mmr_lambda"]
                config_id_parts = [
                    plan.dataset,
                    f"k{top_k}",
                    f"ef{ef_search}",
                    "mmr" if mmr_flag else "nommr",
                ]
                if mmr_flag:
                    config_id_parts.append(f"l{mmr_lambda}".replace(".", "p"))
                config_id = "-".join(config_id_parts)
                parameters = {
                    "dataset": plan.dataset,
                    "sample": sample,
                    "top_k": top_k,
                    "ef_search": ef_search,
                    "mmr": mmr_flag,
                    "mmr_lambda": mmr_lambda if mmr_flag else 0.0,
                    "budget": plan.budget,
                    "concurrency": concurrency,
                    "reflection": reflection_cfg,
                }
                tasks.append(GridTask(config_id=config_id, parameters=parameters))

    batches: List[GridBatch] = []
    for index in range(0, len(tasks), concurrency):
        batch_tasks = tasks[index : index + concurrency]
        batch_id = f"grid-batch-{index // concurrency + 1:02d}"
        batches.append(GridBatch(batch_id=batch_id, tasks=batch_tasks, concurrency=concurrency))

    return batches

@dataclass
class PlannedStage:
    name: str
    parameters: Dict[str, Any]


def build_initial_plan(plan: ExperimentPlan) -> List[PlannedStage]:
    """Return placeholder stage plan for the orchestrator."""
    return [
        PlannedStage(name="smoke", parameters={"sample": plan.sample_size}),
        PlannedStage(name="grid", parameters={}),
        PlannedStage(name="ab", parameters={}),
        PlannedStage(name="select", parameters={}),
        PlannedStage(name="publish", parameters={}),
    ]

