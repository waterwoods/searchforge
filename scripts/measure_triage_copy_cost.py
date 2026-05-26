#!/usr/bin/env python3
"""
DIAGNOSTIC / TEMPORARY — triage session persistence copy + serialization microbench.

Purpose: quantify deepcopy / json.dumps / helper costs for docs/sprints
TRIAGERESULT_DEEPCOPY_COST_DISCOVERY.md — not for CI or prod.

Safe to delete after sprint; does not mutate runtime behavior.

Usage:
  PYTHONPATH=. python3 scripts/measure_triage_copy_cost.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from copy import deepcopy
from typing import Any, Callable


def _import_session_helpers():
    from services.fiqa_api.inbox_triage.session_store import (
        _extract_workflow_state,
        _in_progress_session_payload_unchanged,
    )

    return _extract_workflow_state, _in_progress_session_payload_unchanged


def _build_triage_result(*, bulky: bool) -> dict[str, Any]:
    """Structured dict resembling a live triage `result` with workflow keys."""
    nested = {
        "issue_category": "add_vehicle",
        "vehicle_key": "v1",
        "reply_html": "<p>...</p>",
        "collected_hints": [{"k": i, "v": "x" * (40 if bulky else 8)} for i in range(30 if bulky else 6)],
        "extras": {"flags": ["a", "b", "c"], "meta": {f"k{i}": i for i in range(50 if bulky else 10)}},
    }
    return {
        "collection_stage": "mid",
        "follow_up_type": None,
        "handoff_ready": False,
        "case_creation_suggested": False,
        "collected_fields": ["driver_name", "vin", "zip"] + ([f"f{i}" for i in range(80)] if bulky else []),
        "still_needed_fields": (["needs_x"] * 40) if bulky else ["needs_x", "needs_y"],
        "human_confirmation_required": False,
        "human_confirmation_fields": [],
        "next_best_question": "Who is the primary driver?",
        "lifecycle_status": "intake",
        "triage_mode": "conversation",
        "conversion_stage": "explore",
        "last_conversion_turn_index": 3,
        "action_ready": False,
        "intake_flow_milestone": None,
        "case_id": None,
        "conversation_id": "sess-placeholder",
        "structured": nested,
        "route_perf": {"triage_ms": 12.5, "session_ms": 2.1},
        "assist": {"mode": "off", "snippets": []},
    }


def _normalize_turn_clone(turn: dict[str, Any]) -> dict[str, Any]:
    """Mirror production _normalize_turn output shape (minimal; no module import)."""
    role = str(turn.get("role") or "customer").strip().lower()
    if role not in ("customer", "system"):
        role = "customer"
    text = str(turn.get("text") or turn.get("content") or "").strip()
    out = {"role": role, "text": text}
    if role == "system" and "triageResult" in turn:
        out["triageResult"] = turn["triageResult"]
    elif role == "system" and "triage_result" in turn:
        out["triageResult"] = turn["triage_result"]
    return out


def build_session_payload(
    *,
    n_turns: int,
    triage_result: dict[str, Any],
    extract_workflow_state: Callable[[dict[str, Any]], dict[str, Any]],
    session_id: str = "measure-session",
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """
    Returns (repo_row_like dict for deepcopy/json benches, normalized_turns, workflow_state).

    Alternating customer/system; even indices customer, odd indices system with shared triageResult.
    """
    normalized_turns: list[dict[str, Any]] = []
    pair_i = 0
    for t_idx in range(n_turns):
        if t_idx % 2 == 0:
            normalized_turns.append(
                _normalize_turn_clone(
                    {"role": "customer", "text": f"User message {pair_i} " + ("x" * 32)}
                )
            )
        else:
            normalized_turns.append(
                _normalize_turn_clone(
                    {
                        "role": "system",
                        "text": f"Assistant reply {pair_i} " + ("y" * 48),
                        "triageResult": triage_result,
                    }
                )
            )
            pair_i += 1
    workflow_state = extract_workflow_state(triage_result)
    row: dict[str, Any] = {
        "session_id": session_id,
        "turns": normalized_turns,
        "workflow_state": workflow_state,
        "updated_at": "2026-05-07T12:00:00Z",
    }
    return row, normalized_turns, workflow_state


def _pctile_ms(samples_ms: list[float], p: float) -> float:
    if not samples_ms:
        return 0.0
    xs = sorted(samples_ms)
    k = max(0, min(len(xs) - 1, int(round((p / 100.0) * (len(xs) - 1)))))
    return xs[k]


def bench_loop(
    name: str,
    fn: Callable[[], None],
    *,
    repeats: int,
    warmup: int = 3,
) -> dict[str, float]:
    for _ in range(warmup):
        fn()
    samples: list[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    return {
        "op": name,
        "p50_ms": _pctile_ms(samples, 50),
        "p95_ms": _pctile_ms(samples, 95),
        "max_ms": max(samples),
        "mean_ms": statistics.fmean(samples),
    }


def _payload_json_bytes(row: dict[str, Any]) -> int:
    return len(json.dumps(row, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8"))


def main() -> int:
    extract_workflow_state, in_progress_payload_unchanged = _import_session_helpers()

    repeats = max(100, min(1000, int(sys.argv[1]) if len(sys.argv) > 1 else 500))

    scenarios = (
        ("small", 3, False),
        ("medium", 20, False),
        ("large", 100, False),
        ("large_fat_blob", 100, True),
    )

    print(f"# measure_triage_copy_cost.py repeats={repeats} (diag)\n")

    for label, n_turns, bulky in scenarios:
        triage = _build_triage_result(bulky=bulky)
        row, normalized_turns, workflow_state = build_session_payload(
            n_turns=n_turns,
            triage_result=triage,
            extract_workflow_state=extract_workflow_state,
        )
        turns_count = len(normalized_turns)
        last_triage = triage
        for t in reversed(normalized_turns):
            if isinstance(t, dict) and "triageResult" in t:
                last_triage = t["triageResult"]
                break

        jb = _payload_json_bytes(row)
        raw_pre_read = {
            **row,
            "turns": deepcopy(normalized_turns),
            "workflow_state": {**workflow_state},
        }

        def op_deepcopy_row() -> None:
            deepcopy(row)

        def op_deepcopy_last_triage() -> None:
            deepcopy(last_triage)

        def op_json_dump_row() -> None:
            json.dumps(row, sort_keys=True, default=str, ensure_ascii=False)

        def op_extract() -> None:
            extract_workflow_state(triage)

        def op_unchanged_fast() -> None:
            in_progress_payload_unchanged(row, normalized_turns, workflow_state)

        def op_unchanged_structural_miss() -> None:
            shorter = normalized_turns[:-1]
            in_progress_payload_unchanged(raw_pre_read, shorter, workflow_state)

        def op_explicit_double_dump() -> None:
            json.dumps(normalized_turns, sort_keys=True, default=str, ensure_ascii=False)
            json.dumps(normalized_turns, sort_keys=True, default=str, ensure_ascii=False)

        benches = (
            bench_loop("deepcopy(row)", op_deepcopy_row, repeats=repeats),
            bench_loop("deepcopy(last triageResult)", op_deepcopy_last_triage, repeats=repeats),
            bench_loop("json.dumps(row)", op_json_dump_row, repeats=repeats),
            bench_loop("_extract_workflow_state", op_extract, repeats=repeats),
            bench_loop("_in_progress unchanged (hits ==)", op_unchanged_fast, repeats=repeats),
            bench_loop("_in_progress unchanged (length miss)", op_unchanged_structural_miss, repeats=repeats),
            bench_loop("double json.dumps (parity upper bound)", op_explicit_double_dump, repeats=repeats),
        )

        print(f"## {label}  ({turns_count} turns, bulky={bulky})")
        print(f"    json_serializable_bytes ~= {jb}")
        for b in benches:
            print(
                f"    {b['op']:<45} p50={b['p50_ms']:.4f}ms p95={b['p95_ms']:.4f}ms max={b['max_ms']:.4f}ms"
            )

        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
