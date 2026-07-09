"""P19H-3e-1 — list_all_cases_for_read performance guard (no live DB)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage import case_truth_repository as ctr


def _stub_case(cid: str) -> dict:
    return {
        "case_id": cid,
        "case_status": "new",
        "issue_category": "claim_intake",
        "urgency": "high",
        "broker_next_step": "step",
        "client_prep": "",
        "client_reply_draft": "",
        "manual_followup_needed": False,
        "service_lane": "claim",
        "wecom_external_userid": "wm_perf",
        "created_at": "2026-01-02T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
    }


@pytest.fixture
def _pg_read_env(monkeypatch, tmp_path):
    store = tmp_path / "cases.json"
    store.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://invalid")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_READS", "1")


def test_list_all_batched_path_scales_without_per_case_full_load(monkeypatch, _pg_read_env):
    """Simulated per-case full hydration cost must not multiply by case count."""
    n = 200
    ids = [f"case_{i:03d}" for i in range(n)]
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.list_record_ids_recent",
        lambda _max_n: ids,
    )

    def _slow_full(_rid: str):
        time.sleep(0.01)
        return _stub_case(_rid)

    def _fast_batch(batch_ids: list[str]):
        return [_stub_case(rid) for rid in batch_ids]

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_full_case_from_postgres",
        _slow_full,
    )
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_workbench_queue_cases_from_postgres",
        _fast_batch,
    )

    t0 = time.perf_counter()
    rows = ctr.list_all_cases_for_read()
    elapsed = time.perf_counter() - t0

    assert len(rows) == n
    # N+1 with 10ms sleep would be ~2s+; batched stub path should stay well under 1s.
    assert elapsed < 1.0, f"list_all_cases_for_read took {elapsed:.2f}s — likely N+1 full hydration"
