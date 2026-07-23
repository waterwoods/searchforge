"""P26H — QA ephemeral fixture runner (test infrastructure only).

Creates tagged workbench_test cases for the Golden Customer Flow harness.
Never mutates Camry/shared seeds. Cleanup is scoped to harness_run_id only.

Enablement (all required for prod-like runtimes):
  ENABLE_P26H_FIXTURE_RUNNER=1
  UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1

Support export auth still applies on HTTP routes.
"""

from __future__ import annotations

import os
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Final

DEMO_NAME: Final[str] = "p26h_ephemeral"
_TRUTHY: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})

# Process-local intake store for inprocess / no-DB fixture runs (idempotency within a harness).
_FIXTURE_MEMORY_STORE: Any = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _truthy(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in _TRUTHY


def fixture_runner_enabled() -> bool:
    """Explicit dual-flag enable — never accidental in production."""
    if not _truthy("ENABLE_P26H_FIXTURE_RUNNER"):
        return False
    if not _truthy("UNIFIED_INTAKE_QA_FIXTURE_SURFACE"):
        return False
    return True


def fixture_runner_status() -> dict[str, Any]:
    from services.fiqa_api.db.service_record_settings import is_production_mode
    from services.fiqa_api.security.support_export_gate import support_export_secret_configured

    enabled = fixture_runner_enabled()
    prod_like = is_production_mode()
    return {
        "ok": True,
        "enabled": enabled,
        "demo_name": DEMO_NAME,
        "production_like": prod_like,
        "support_key_configured": support_export_secret_configured(),
        "require_support_key": prod_like,
        "notes": (
            "Requires ENABLE_P26H_FIXTURE_RUNNER=1 and UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1. "
            "Prod-like runtimes also require UNIFIED_INTAKE_SUPPORT_API_KEY."
        ),
    }


def assert_fixture_runner_allowed(*, require_support_key_in_prod: bool = True) -> None:
    """Raise ValueError with stable codes when the runner must refuse."""
    from services.fiqa_api.db.service_record_settings import is_production_mode
    from services.fiqa_api.security.support_export_gate import support_export_secret_configured

    if not _truthy("ENABLE_P26H_FIXTURE_RUNNER"):
        raise ValueError("p26h_fixture_runner_disabled")
    if not _truthy("UNIFIED_INTAKE_QA_FIXTURE_SURFACE"):
        raise ValueError("p26h_fixture_surface_disabled")
    if require_support_key_in_prod and is_production_mode() and not support_export_secret_configured():
        raise ValueError("p26h_fixture_support_key_required")


def _mask_token(token: str) -> str:
    t = (token or "").strip()
    if len(t) <= 16:
        return "h5t1_…"
    return f"{t[:8]}…{t[-6:]}"


def _environment_label() -> str:
    if _truthy("UNIFIED_INTAKE_QA_FIXTURE_SURFACE"):
        return "qa"
    env = (os.getenv("ENV") or "local").strip().lower() or "local"
    return env


def new_harness_run_id() -> str:
    return f"p26h_{_utc_now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:10]}"


def _tag_case(case: dict[str, Any], *, harness_run_id: str) -> dict[str, Any]:
    out = dict(case)
    out["workbench_test"] = True
    out["demo_name"] = DEMO_NAME
    out["demo_flags"] = {"demo_name": DEMO_NAME, "p26h_ephemeral": True}
    out["harness_run_id"] = harness_run_id
    out["harness_created_at"] = str(out.get("harness_created_at") or _utc_now_iso())
    out["harness_environment"] = _environment_label()
    out["harness_cleanup_eligible"] = True
    out["exclude_from_production_metrics"] = True
    return out


def _upsert_case_json(case_id: str, case: dict[str, Any]) -> None:
    """Insert or replace a case in the local JSON store (fixture seeding only)."""
    from services.fiqa_api.inbox_triage.case_store import (
        _read_payload,
        _sort_recent,
        _write_payload,
    )

    payload = _read_payload()
    cases = payload.get("cases") or []
    replaced = False
    for index, existing in enumerate(cases):
        if existing.get("case_id") == case_id:
            cases[index] = case
            replaced = True
            break
    if not replaced:
        cases.append(case)
    payload["cases"] = _sort_recent(cases)
    _write_payload(payload)


def _is_run_case(case: dict[str, Any], harness_run_id: str) -> bool:
    if str(case.get("harness_run_id") or "").strip() != harness_run_id:
        return False
    if str(case.get("demo_name") or "").strip() != DEMO_NAME:
        return False
    if not bool(case.get("workbench_test")):
        return False
    if not bool(case.get("harness_cleanup_eligible", True)):
        return False
    return True


def list_run_case_ids(harness_run_id: str) -> list[str]:
    """List case IDs tagged for this harness run (JSON + Postgres when available)."""
    run_id = (harness_run_id or "").strip()
    if not run_id:
        return []
    ids: list[str] = []

    # Postgres path (QA Cloud SQL)
    try:
        from services.fiqa_api.db.service_record_settings import (
            db_primary_reads_enabled,
            service_record_database_url,
        )

        if service_record_database_url() and (
            db_primary_reads_enabled() or _truthy("UNIFIED_INTAKE_DB_PRIMARY_WRITES")
        ):
            from services.fiqa_api.db.service_record_repository import service_record_connection

            with service_record_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT record_id FROM service_records
                        WHERE COALESCE(extra->>'demo_name', '') = %s
                          AND COALESCE(extra->>'harness_run_id', '') = %s
                          AND COALESCE(extra->>'workbench_test', 'false') IN ('true', 't', '1')
                          AND COALESCE(extra->>'harness_cleanup_eligible', 'true') IN ('true', 't', '1')
                        """,
                        (DEMO_NAME, run_id),
                    )
                    ids.extend(str(row[0]) for row in cur.fetchall())
    except Exception:
        pass

    # JSON / local path
    try:
        from services.fiqa_api.inbox_triage.case_store import list_all_cases

        for case in list_all_cases():
            if _is_run_case(case, run_id):
                cid = str(case.get("case_id") or "").strip()
                if cid and cid not in ids:
                    ids.append(cid)
    except Exception:
        pass
    return ids


def create_run() -> dict[str, Any]:
    assert_fixture_runner_allowed()
    run_id = new_harness_run_id()
    return {
        "ok": True,
        "harness_run_id": run_id,
        "demo_name": DEMO_NAME,
        "environment": _environment_label(),
        "created_at": _utc_now_iso(),
    }


def _create_claim_via_real_contracts(
    *,
    command_id: str,
    idempotency_key: str,
    session_id: str,
    accident_description: str,
) -> dict[str, Any]:
    """Prefer Postgres-backed StartClaim; fall back to in-memory Cap2 for no-DB local."""
    global _FIXTURE_MEMORY_STORE
    from services.fiqa_api.db.service_record_settings import service_record_database_url
    from services.fiqa_api.inbox_triage.h5_task_token import (
        issue_h5_intake_form_token,
        verify_h5_task_token,
    )
    from services.fiqa_api.inbox_triage.p20_customer_start_claim import (
        normalize_customer_actor_identity,
        start_customer_claim,
    )

    if service_record_database_url():
        result = start_customer_claim(
            command_id=command_id,
            idempotency_key=idempotency_key,
            session_id=session_id,
            accident_description=accident_description,
            accident_datetime="2026-07-18 10:00",
            accident_location="停车场",
            injury_status="no",
            is_test=True,
            office_id="p26h_ephemeral",
            tenant_id="p26h_ephemeral",
        )
        # One Active Case: same identity may resume the existing Active Case.
        # Fixture create must treat resumed as success (return that case), not 503.
        if result.get("outcome") not in ("accepted", "replayed", "resumed"):
            raise RuntimeError(
                f"create_claim_failed:{result.get('error_code') or result.get('outcome')}"
            )
        case_id = str(result.get("case_id") or "").strip()
        token = str(result.get("resume_token") or "").strip()
        if not case_id and token:
            claims = verify_h5_task_token(token)
            case_id = str(claims.case_id if claims else "").strip()
        if not case_id:
            raise RuntimeError("create_claim_missing_case_id")
        if not token:
            from services.fiqa_api.inbox_triage.p20_customer_launch import (
                issue_customer_launch_token,
            )

            token = issue_customer_launch_token(case_id=case_id).token
        return {**result, "case_id": case_id, "resume_token": token}

    # No DB URL: still exercise Cap2 CreateClaim contracts via ephemeral memory store.
    from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
        InMemoryIntakeStore,
        P20CaseIntakeCommandService,
    )

    if _FIXTURE_MEMORY_STORE is None:
        _FIXTURE_MEMORY_STORE = InMemoryIntakeStore()
    svc = P20CaseIntakeCommandService(_FIXTURE_MEMORY_STORE)
    actor = normalize_customer_actor_identity(session_id)
    result = svc.create_claim(
        broker_id=actor,
        office_id="p26h_ephemeral",
        tenant_id="p26h_ephemeral",
        command_id=command_id,
        idempotency_key=idempotency_key,
        actor="customer",
        inputs={
            "is_test": True,
            "accident_description": accident_description,
            "accident_datetime": "2026-07-18 10:00",
            "accident_location": "停车场",
            "injury_status": "no",
            "title": "QA Customer Claim intake",
        },
    )
    if result.get("outcome") not in ("accepted", "replayed", "resumed"):
        raise RuntimeError(
            f"create_claim_failed:{result.get('error_code') or result.get('outcome')}"
        )
    case_id = str(result["case_id"])
    token = issue_h5_intake_form_token(case_id=case_id, nonce=f"p26h-{session_id[-12:]}")
    # Seed JSON case store so subsequent fixture ops use real case_store contracts.
    case = dict(_FIXTURE_MEMORY_STORE.cases[case_id])
    _upsert_case_json(case_id, case)
    return {
        **result,
        "case_id": case_id,
        "resume_token": token,
    }


def create_fresh_claim(
    *,
    harness_run_id: str,
    suffix: str = "fresh",
    session_id: str | None = None,
    idempotency_key: str | None = None,
    accident_description: str = "停车场倒车碰撞，前保险杠受损",
) -> dict[str, Any]:
    """Create a unique test claim via Cap2 customer CreateClaim + tag for cleanup."""
    assert_fixture_runner_allowed()
    run_id = (harness_run_id or "").strip()
    if not run_id.startswith("p26h_"):
        raise ValueError("invalid_harness_run_id")

    from services.fiqa_api.inbox_triage.case_store import (
        _persist_case_after_update,
        get_case_by_id,
    )
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    # Stable command_id when caller supplies idempotency_key so Cap2 replay works.
    idem = (idempotency_key or "").strip() or f"p26h-fx-idem-{uuid.uuid4().hex}"
    command_id = (
        f"p26h-fx-cmd-{idem}"
        if idempotency_key
        else f"p26h-fx-{suffix}-{uuid.uuid4().hex[:12]}"
    )
    sess = session_id or f"p26h-{run_id[-10:]}-{suffix}"
    result = _create_claim_via_real_contracts(
        command_id=command_id,
        idempotency_key=idem,
        session_id=sess,
        accident_description=accident_description,
    )
    case_id = str(result.get("case_id") or "").strip()
    token = str(result.get("resume_token") or "").strip()
    if not case_id or not token:
        raise RuntimeError("create_claim_missing_case_or_token")

    case = get_case_for_read(case_id)
    if case is None:
        case = get_case_by_id(case_id)
    if case is None and _FIXTURE_MEMORY_STORE is not None:
        case = dict(_FIXTURE_MEMORY_STORE.cases.get(case_id) or {})
    if not case:
        raise RuntimeError(f"case_unreadable:{case_id}")

    tagged = _tag_case(case, harness_run_id=run_id)
    outcome = str(result.get("outcome") or "").strip().lower()
    if outcome != "resumed":
        # Clear broker/stale carriers for a true fresh claim only.
        # Resumed Active Case must keep evidence / Request More truth intact.
        tagged["p20_slice1_projection"] = {
            "case_id": case_id,
            "workflow_state": "intake",
            "customer_next_action": None,
            "broker_next_action": {"action_type": "none", "status": "none"},
            "open_request": None,
        }
        tagged.setdefault("case_attachments", [])
        tagged.setdefault("claim_attachment_slots", {})
        tagged.setdefault(
            "claim_evidence_summary",
            {"received_slots": [], "missing_required_slots": []},
        )
        tagged.setdefault("timeline_events", [])
        tagged["active_case_id"] = None
    if not _persist_case_after_update(case_id, tagged):
        _upsert_case_json(case_id, tagged)
    if _FIXTURE_MEMORY_STORE is not None:
        _FIXTURE_MEMORY_STORE.cases[case_id] = tagged

    # Read-after-write: harness tags must survive the durable store (PG extra bag).
    verified = get_case_for_read(case_id) or get_case_by_id(case_id)
    if verified is None or not _is_run_case(verified, run_id):
        raise RuntimeError(
            "fixture_tag_not_durable:"
            f"harness_run_id={run_id!r} case_id={case_id!r} "
            f"stored_run={None if verified is None else verified.get('harness_run_id')!r}"
        )

    return {
        "ok": True,
        "harness_run_id": run_id,
        "case_id": case_id,
        "resume_token": token,
        "resume_token_masked": _mask_token(token),
        "outcome": result.get("outcome"),
        "command_id": command_id,
        "idempotency_key": idem,
        "session_id": sess,
    }


def register_test_evidence(
    *,
    harness_run_id: str,
    case_id: str,
    slot: str,
) -> dict[str, Any]:
    """Register test-safe canonical evidence on a tagged case (no real customer upload bytes)."""
    assert_fixture_runner_allowed()
    run_id = (harness_run_id or "").strip()
    cid = (case_id or "").strip()
    slot_norm = (slot or "").strip().lower()
    if slot_norm not in ("policy_or_insurance_card", "scene_photo", "customer_damage_photo"):
        raise ValueError("unsupported_test_slot")

    from services.fiqa_api.inbox_triage.case_store import (
        append_claim_timeline_event,
        append_h5_gcs_attachment_metadata,
        build_claim_timeline_event,
        record_claim_evidence_slot_received,
    )
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    case = get_case_for_read(cid)
    if case is None or not _is_run_case(case, run_id):
        raise ValueError("fixture_case_not_in_run")

    attachment_id = f"att_p26h_{uuid.uuid4().hex[:12]}"
    upload_id = f"p26h_up_{uuid.uuid4().hex[:12]}"
    meta = {
        "attachment_id": attachment_id,
        "source": "h5_task",
        "msgtype": "image",
        "storage_uri": f"gs://p26h-ephemeral-test/{run_id}/{cid}/{attachment_id}.jpg",
        "mime_type": "image/jpeg",
        "size_bytes": 128,
        "filename": f"{slot_norm}.jpg",
        "bound_case_id": cid,
        "binding_confidence": "high",
        "slot_assignment": slot_norm,
        "evidence_status": "confirmed",
        "h5_upload_id": upload_id,
        "created_by": "customer",
        "created_by_channel": "p26h_fixture",
        "eligible_for_ocr": False,
    }
    updated = append_h5_gcs_attachment_metadata(cid, meta)
    if updated is None:
        raise RuntimeError("evidence_attach_failed")
    if record_claim_evidence_slot_received(cid, slot=slot_norm, attachment_id=attachment_id) is None:
        raise RuntimeError("evidence_slot_failed")
    append_claim_timeline_event(
        cid,
        build_claim_timeline_event(
            event_type="evidence_uploaded",
            source_channel="h5_task",
            actor="customer",
            attachment_id=attachment_id,
            metadata={"category": slot_norm, "harness_run_id": run_id},
        ),
    )
    return {
        "ok": True,
        "harness_run_id": run_id,
        "case_id": cid,
        "slot": slot_norm,
        "attachment_id": attachment_id,
    }


def patch_vehicle_facts(*, harness_run_id: str, case_id: str) -> dict[str, Any]:
    assert_fixture_runner_allowed()
    run_id = (harness_run_id or "").strip()
    cid = (case_id or "").strip()
    from services.fiqa_api.inbox_triage.case_store import (
        append_claim_timeline_event,
        build_claim_timeline_event,
        patch_case_known_facts,
    )
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    case = get_case_for_read(cid)
    if case is None or not _is_run_case(case, run_id):
        raise ValueError("fixture_case_not_in_run")
    patch_case_known_facts(
        cid,
        {"own_vehicle_info": "2020 Toyota Camry", "vin": "1HGCM82633A004352"},
        source="customer_task",
    )
    append_claim_timeline_event(
        cid,
        build_claim_timeline_event(
            event_type="h5_step_complete",
            source_channel="h5_task",
            actor="customer",
            metadata={"step": "vehicle_other_party", "harness_run_id": run_id},
        ),
    )
    return {"ok": True, "case_id": cid, "harness_run_id": run_id}


def create_broker_followup(*, harness_run_id: str, case_id: str) -> dict[str, Any]:
    assert_fixture_runner_allowed()
    run_id = (harness_run_id or "").strip()
    cid = (case_id or "").strip()
    from services.fiqa_api.inbox_triage.case_store import _persist_case_after_update
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
        SLICE1_CAPABILITY_VERSION,
        default_slice1_service,
    )
    from services.fiqa_api.wecom.claim_state import CLAIM_PHASE_BROKER_REVIEW

    case = get_case_for_read(cid)
    if case is None or not _is_run_case(case, run_id):
        raise ValueError("fixture_case_not_in_run")
    case = dict(case)
    case["claim_phase"] = CLAIM_PHASE_BROKER_REVIEW
    case["slice1_capability_version"] = SLICE1_CAPABILITY_VERSION
    case["p20_slice1_capability_version"] = SLICE1_CAPABILITY_VERSION
    if not _persist_case_after_update(cid, case):
        _upsert_case_json(cid, case)

    def _compat_followup() -> dict[str, Any]:
        from services.fiqa_api.inbox_triage.case_store import apply_p20_slice1_compat_projection

        item_id = f"item_p26h_{uuid.uuid4().hex[:10]}"
        slice1 = {
            "case_id": cid,
            "workflow_state": "broker_more_requested",
            "aggregate_version": 1,
            "customer_next_action": {
                "action_type": "provide_evidence",
                "title": "上传保险卡",
                "required_input": "policy_or_insurance_card",
                "status": "active",
                "request_item_id": item_id,
                "request_id": f"req_p26h_{uuid.uuid4().hex[:8]}",
                "instructions": "请补一张更清晰的保险卡",
            },
            "broker_next_action": {
                "action_type": "wait_for_customer_item",
                "status": "waiting_for_customer",
            },
            "open_request": {
                "status": "open",
                "request_id": f"req_p26h_{uuid.uuid4().hex[:8]}",
                "active_item": {
                    "item_type": "policy_or_insurance_card",
                    "label": "上传保险卡",
                    "status": "active",
                    "request_item_id": item_id,
                },
                "queued_items": [],
                "items": [],
            },
        }
        applied = apply_p20_slice1_compat_projection(
            cid,
            {
                "claim_phase": "broker_needs_more_info",
                "p20_slice1_projection": slice1,
                "slice1_projection": slice1,
            },
        )
        if applied is None:
            tagged = dict(get_case_for_read(cid) or case)
            tagged.update(
                {
                    "claim_phase": "broker_needs_more_info",
                    "p20_slice1_projection": slice1,
                    "slice1_projection": slice1,
                }
            )
            _upsert_case_json(cid, tagged)
        return {"outcome": "accepted", "customer_projection": slice1, "fallback": "compat_projection"}

    from services.fiqa_api.inbox_triage.case_close import (
        ERROR_CASE_CLOSED_READ_ONLY,
        case_is_closed_history,
    )

    # Never invent Request More on History via compat fallback.
    if case_is_closed_history(case):
        return {
            "ok": False,
            "harness_run_id": run_id,
            "case_id": cid,
            "outcome": "rejected",
            "error_code": ERROR_CASE_CLOSED_READ_ONLY,
            "projection": None,
        }

    cmd = f"p26h-fx-followup-{uuid.uuid4().hex[:12]}"
    try:
        result = default_slice1_service().accept_request_more(
            case_id=cid,
            broker_id="office:p26h_ephemeral",
            command_id=cmd,
            idempotency_key=cmd,
            expected_case_version=0,
            requested_items=[
                {
                    "request_item_id": f"item_p26h_{uuid.uuid4().hex[:10]}",
                    "item_type": "policy_or_insurance_card",
                    "label": "补充保险卡",
                    "instructions": "请补一张更清晰的保险卡",
                    "required": True,
                    "position": 1,
                }
            ],
            reason="P26H ephemeral exceptional follow-up",
        )
    except ValueError as exc:
        code = str(exc).strip() or "broker_followup_failed"
        if code == ERROR_CASE_CLOSED_READ_ONLY:
            return {
                "ok": False,
                "harness_run_id": run_id,
                "case_id": cid,
                "outcome": "rejected",
                "error_code": ERROR_CASE_CLOSED_READ_ONLY,
                "projection": None,
            }
        result = _compat_followup()
    except Exception:
        result = _compat_followup()

    # Closed / illegal rejections must surface — never rewrite to accepted via compat.
    if result.get("outcome") != "accepted":
        error_code = str(result.get("error_code") or result.get("outcome") or "rejected")
        if error_code == ERROR_CASE_CLOSED_READ_ONLY or case_is_closed_history(
            get_case_for_read(cid) or case
        ):
            return {
                "ok": False,
                "harness_run_id": run_id,
                "case_id": cid,
                "outcome": "rejected",
                "error_code": ERROR_CASE_CLOSED_READ_ONLY,
                "projection": result.get("customer_projection") or result.get("broker_projection"),
            }
        result = _compat_followup()
    return {
        "ok": True,
        "harness_run_id": run_id,
        "case_id": cid,
        "outcome": result.get("outcome"),
        "projection": result.get("customer_projection") or result.get("broker_projection"),
    }

def inspect_case(*, harness_run_id: str, case_id: str) -> dict[str, Any]:
    assert_fixture_runner_allowed()
    run_id = (harness_run_id or "").strip()
    cid = (case_id or "").strip()
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
    from services.fiqa_api.inbox_triage.constitution_projection import (
        ConstitutionInputs,
        build_constitution_projection,
    )

    case = get_case_for_read(cid)
    if case is None or not _is_run_case(case, run_id):
        raise ValueError("fixture_case_not_in_run")
    slice1 = case.get("p20_slice1_projection") if isinstance(case.get("p20_slice1_projection"), dict) else None
    projection = build_constitution_projection(ConstitutionInputs(case=case, slice1=slice1))
    # Canonical claim timeline lives in claim_timeline; some fixtures also use timeline_events.
    timeline: list[Any] = []
    if isinstance(case.get("claim_timeline"), list):
        timeline.extend(case["claim_timeline"])
    if isinstance(case.get("timeline_events"), list):
        timeline.extend(case["timeline_events"])
    return {
        "ok": True,
        "harness_run_id": run_id,
        "case_id": cid,
        "claim_phase": case.get("claim_phase"),
        "workbench_test": bool(case.get("workbench_test")),
        "demo_name": case.get("demo_name"),
        "attachment_count": len(case.get("case_attachments") or []),
        "timeline_event_types": [
            str(e.get("event_type") or "") for e in timeline if isinstance(e, dict)
        ][-20:],
        "constitution_projection": projection,
        "known_facts_keys": sorted((case.get("known_facts") or {}).keys()),
    }


def issue_expired_token(*, harness_run_id: str, case_id: str) -> dict[str, Any]:
    assert_fixture_runner_allowed()
    run_id = (harness_run_id or "").strip()
    cid = (case_id or "").strip()
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
    from services.fiqa_api.inbox_triage.h5_task_token import (
        issue_h5_intake_form_token,
        verify_h5_task_token,
    )

    case = get_case_for_read(cid)
    if case is None or not _is_run_case(case, run_id):
        raise ValueError("fixture_case_not_in_run")
    now = 1_000_000.0
    token = issue_h5_intake_form_token(case_id=cid, now=now, ttl_seconds=60)
    rejected = verify_h5_task_token(token, now=now + 120) is None
    return {
        "ok": True,
        "harness_run_id": run_id,
        "case_id": cid,
        "expired_token_masked": _mask_token(token),
        "rejected_as_expected": rejected,
    }


def cleanup_run(harness_run_id: str) -> dict[str, Any]:
    """Delete only cases tagged for this harness_run_id + demo_name + workbench_test."""
    assert_fixture_runner_allowed()
    run_id = (harness_run_id or "").strip()
    if not run_id.startswith("p26h_"):
        raise ValueError("invalid_harness_run_id")
    from services.fiqa_api.inbox_triage.case_store import delete_case
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    deleted: list[str] = []
    refused: list[str] = []
    for cid in list_run_case_ids(run_id):
        case = get_case_for_read(cid)
        if case is None or not _is_run_case(case, run_id):
            refused.append(cid)
            continue
        # Hard refuse untagged / wrong demo
        if str(case.get("demo_name") or "") == "camry_golden_qa":
            refused.append(cid)
            continue
        if delete_case(cid):
            deleted.append(cid)
        else:
            refused.append(cid)
    return {
        "ok": len(refused) == 0,
        "harness_run_id": run_id,
        "deleted_case_ids": deleted,
        "refused_case_ids": refused,
        "cleanup": "PASS" if len(refused) == 0 else "PARTIAL",
    }


def cleanup_stale(*, max_age_hours: int = 24) -> dict[str, Any]:
    assert_fixture_runner_allowed()
    cutoff = _utc_now() - timedelta(hours=max(1, int(max_age_hours)))
    stale_runs: set[str] = set()

    def _consider(case: dict[str, Any]) -> None:
        if str(case.get("demo_name") or "") != DEMO_NAME:
            return
        if not bool(case.get("workbench_test")):
            return
        if not bool(case.get("harness_cleanup_eligible", True)):
            return
        run_id = str(case.get("harness_run_id") or "").strip()
        created = str(case.get("harness_created_at") or case.get("created_at") or "").strip()
        if not run_id or not created:
            return
        try:
            ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except Exception:
            return
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts <= cutoff:
            stale_runs.add(run_id)

    try:
        from services.fiqa_api.inbox_triage.case_store import list_all_cases

        for case in list_all_cases():
            _consider(case)
    except Exception:
        pass

    results = [cleanup_run(run_id) for run_id in sorted(stale_runs)]
    return {
        "ok": all(r.get("ok") for r in results) if results else True,
        "stale_run_count": len(stale_runs),
        "runs": results,
    }


def safe_public_case_view(payload: dict[str, Any]) -> dict[str, Any]:
    """Redact raw resume tokens from durable/status payloads."""
    out = deepcopy(payload)
    if "resume_token" in out:
        out["resume_token_masked"] = _mask_token(str(out.get("resume_token") or ""))
        # Keep token only for authorized one-shot harness callers; strip from status dumps.
        # Callers that need the token read create_fresh_claim response directly.
    if "expired_token" in out:
        out.pop("expired_token", None)
    return out
