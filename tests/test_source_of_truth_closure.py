"""
Source-of-truth closure: dual-write implies Postgres-first reads; mutations use the same read facade.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage import case_truth_repository as ctr
from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation


def test_dual_write_alone_enables_postgres_primary_reads(monkeypatch, tmp_path):
    """Production-style mirror: PG_DUAL_WRITE without DB_PRIMARY_READS still prefers PG for API reads."""
    store = tmp_path / "cases.json"
    store.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://invalid")
    monkeypatch.setenv("UNIFIED_INTAKE_PG_DUAL_WRITE", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)

    pg_case = {
        "case_id": "case_pg",
        "case_status": "new",
        "issue_category": "customer_question",
        "urgency": "medium",
        "broker_next_step": "step",
        "client_prep": "prep",
        "client_reply_draft": "draft",
        "manual_followup_needed": False,
        "created_at": "2026-01-02T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "case_messages": [],
        "case_activity": [],
        "source_text": "",
    }
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_full_case_from_postgres",
        lambda _rid: pg_case if _rid == "case_pg" else None,
    )

    c = ctr.get_case_for_read("case_pg")
    assert c is not None
    assert c["case_id"] == "case_pg"


def test_db_primary_reads_explicit_off_overrides_dual_write(monkeypatch, tmp_path):
    """Rollback: UNIFIED_INTAKE_DB_PRIMARY_READS=0 forces JSON-first even when dual-write is on."""
    store = tmp_path / "cases.json"
    store.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "case_json",
                        "case_status": "new",
                        "issue_category": "x",
                        "urgency": "low",
                        "broker_next_step": "b",
                        "client_prep": "c",
                        "client_reply_draft": "d",
                        "manual_followup_needed": False,
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://invalid")
    monkeypatch.setenv("UNIFIED_INTAKE_PG_DUAL_WRITE", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_READS", "0")

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_full_case_from_postgres",
        lambda _rid: {"case_id": "case_pg_only", "case_status": "new"},
    )

    c = ctr.get_case_for_read("case_json")
    assert c is not None
    assert c["case_id"] == "case_json"


def test_dual_write_json_fallback_when_pg_row_missing(monkeypatch, tmp_path):
    """Dual-write + default JSON read fallback: transition cases may exist only in JSON."""
    store = tmp_path / "cases.json"
    store.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "case_json_only",
                        "case_status": "new",
                        "issue_category": "x",
                        "urgency": "low",
                        "broker_next_step": "b",
                        "client_prep": "c",
                        "client_reply_draft": "d",
                        "manual_followup_needed": False,
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://invalid")
    monkeypatch.setenv("UNIFIED_INTAKE_PG_DUAL_WRITE", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_full_case_from_postgres",
        lambda _rid: None,
    )

    c = ctr.get_case_for_read("case_json_only")
    assert c is not None
    assert c["case_id"] == "case_json_only"


def test_load_case_for_mutation_calls_truth_repository(monkeypatch, tmp_path):
    """Mutations must not load a different store than GET /cases/{id} / append pre-load."""
    store = tmp_path / "cases.json"
    store.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))

    seen: list[str] = []

    def fake_get(cid: str):
        seen.append(cid)
        return {
            "case_id": cid,
            "case_status": "new",
            "issue_category": "x",
            "urgency": "low",
            "broker_next_step": "b",
            "client_prep": "c",
            "client_reply_draft": "d",
            "manual_followup_needed": False,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_truth_repository.get_case_for_read",
        fake_get,
    )
    out = _load_case_for_mutation("case_abc")
    assert seen == ["case_abc"]
    assert out is not None
    assert out["case_id"] == "case_abc"


def test_strict_pilot_list_recent_does_not_use_stale_json(monkeypatch, tmp_path):
    """Postgres-only case store: list must not fall back to JSON (even with READ_FALLBACK=1)."""
    store = tmp_path / "cases.json"
    store.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "case_stale_json",
                        "case_status": "new",
                        "issue_category": "x",
                        "urgency": "low",
                        "broker_next_step": "b",
                        "client_prep": "c",
                        "client_reply_draft": "d",
                        "manual_followup_needed": False,
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://invalid")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "0")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_READ_FALLBACK", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.list_record_ids_recent",
        lambda _lim, _off=0: [],
    )

    rows = ctr.list_recent_cases_for_read(limit=8)
    assert rows == []
