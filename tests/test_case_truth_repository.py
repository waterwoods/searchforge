from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage import case_truth_repository as ctr


def test_defaults_to_json_path(monkeypatch, tmp_path):
    store = tmp_path / "cases.json"
    store.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "case_a",
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
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)

    c = ctr.get_case_for_read("case_a")
    assert c is not None
    assert c["case_id"] == "case_a"


def test_db_primary_uses_postgres_case(monkeypatch, tmp_path):
    store = tmp_path / "cases.json"
    store.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://invalid")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_READS", "1")

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
    assert c["issue_category"] == "customer_question"


def test_db_primary_no_json_workbench_overlay_when_json_writes_off(monkeypatch, tmp_path):
    """Stale JSON must not override PG workbench flags when JSON case writes are disabled."""
    store = tmp_path / "cases.json"
    store.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "case_pg",
                        "case_status": "new",
                        "issue_category": "x",
                        "urgency": "low",
                        "broker_next_step": "b",
                        "client_prep": "c",
                        "client_reply_draft": "d",
                        "manual_followup_needed": False,
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:00Z",
                        "workbench_test": True,
                        "workbench_archived": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://invalid")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_READS", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "0")

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
        "workbench_test": False,
        "workbench_archived": False,
    }

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_full_case_from_postgres",
        lambda _rid: pg_case if _rid == "case_pg" else None,
    )

    c = ctr.get_case_for_read("case_pg")
    assert c is not None
    assert c["workbench_test"] is False
    assert c["workbench_archived"] is False


def test_db_primary_falls_back_to_json_when_no_pg_row(monkeypatch, tmp_path):
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
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_READS", "1")

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_full_case_from_postgres",
        lambda _rid: None,
    )

    c = ctr.get_case_for_read("case_json_only")
    assert c is not None
    assert c["case_id"] == "case_json_only"


def test_db_primary_no_fallback_returns_none(monkeypatch, tmp_path):
    store = tmp_path / "cases.json"
    store.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://invalid")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_READS", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_READ_FALLBACK", "0")

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_full_case_from_postgres",
        lambda _rid: None,
    )

    assert ctr.get_case_for_read("missing") is None


def test_strict_db_only_no_json_fallback_when_pg_missing(monkeypatch, tmp_path):
    """DB-primary writes + JSON off: stale JSON file must not masquerade as truth."""
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
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "0")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_full_case_from_postgres",
        lambda _rid: None,
    )

    assert ctr.get_case_for_read("case_json_only") is None


def test_list_recent_returns_empty_not_stale_json_when_pg_ids_fail_hydration(monkeypatch, tmp_path):
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
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_READS", "1")

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.list_record_ids_recent",
        lambda _lim, _off=0: ["case_bad"],
    )
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_full_case_from_postgres",
        lambda _rid: None,
    )

    rows = ctr.list_recent_cases_for_read(limit=8)
    assert rows == []


def test_json_path_count_and_pagination_offset(monkeypatch, tmp_path):
    """Workbench list: total_count and offset apply to JSON store when DB reads are off."""
    cases = []
    for i in range(5):
        cases.append(
            {
                "case_id": f"case_{i}",
                "case_status": "new",
                "issue_category": "x",
                "urgency": "low",
                "broker_next_step": "b",
                "client_prep": "c",
                "client_reply_draft": "d",
                "manual_followup_needed": False,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": f"2026-01-0{i + 1}T00:00:00Z",
            }
        )
    store = tmp_path / "cases.json"
    store.write_text(json.dumps({"cases": cases}), encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)

    assert ctr.count_cases_for_read() == 5
    p0 = ctr.list_recent_cases_for_read(limit=2, offset=0)
    assert len(p0) == 2
    assert p0[0]["case_id"] == "case_4"
    p2 = ctr.list_recent_cases_for_read(limit=2, offset=2)
    assert [c["case_id"] for c in p2] == ["case_2", "case_1"]
