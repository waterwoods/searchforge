"""Concurrency hardening for high-risk case-document mutations.

A case is persisted as one document: ``persist_case_append`` overwrites the
scalar columns wholesale and shallow-merges the ``extra`` bag from whatever the
writer last read. So two writers that both load the same case and both persist
produce a lost update — the later write silently reverts the earlier writer's
sibling fields, and appends built from a stale list drop the other's entry.

These tests reproduce that race on the mutations a real pilot can actually hit
(customer supplement / photo upload vs broker action), and lock in
lock → re-read → mutate → persist for both storage paths.

Threaded tests exercise the JSON per-case lock; the paid-pilot Postgres path
goes through ``mutate_full_case_under_lock`` and is covered by the
repository-level ordering tests at the bottom of this file.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable

import pytest

from services.fiqa_api.inbox_triage import case_store as cs
from services.fiqa_api.inbox_triage.case_store import (
    ClaimBrokerDoneError,
    append_case_collected_fields,
    append_claim_timeline_event,
    append_h5_gcs_attachment_metadata,
    build_claim_timeline_event,
    get_case_by_id,
    mark_claim_broker_done,
    patch_case_known_facts,
    save_case,
    update_case_h5_intake_state,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)

# Widen the read → write window so an unserialized writer really does interleave.
# Without a lock both threads read the same version, both sleep, both persist,
# and one change is gone. With the lock the second thread waits and re-reads.
_RACE_WINDOW_SECONDS = 0.05


@pytest.fixture(autouse=True)
def _json_store(monkeypatch):
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


@pytest.fixture()
def widen_race_window(monkeypatch):
    """Delay every persist so a missing lock produces a real lost update."""
    original = cs._persist_case_after_update

    def _slow_persist(case_id: str, updated_case: dict[str, Any]) -> bool:
        time.sleep(_RACE_WINDOW_SECONDS)
        return original(case_id, updated_case)

    monkeypatch.setattr(cs, "_persist_case_after_update", _slow_persist)
    return _slow_persist


def _known_facts() -> dict[str, str]:
    return {
        "accident_description": "对方变道刮到我左前门",
        "accident_datetime": "今天上午10点",
        "accident_location": "Irvine Blvd",
        "injury_status": "no",
    }


def _claim_case(*, lane: str = SERVICE_LANE_CLAIM, **extra: Any) -> dict[str, Any]:
    stub: dict[str, Any] = {
        "issue_category": "claim_intake",
        "urgency": "medium",
        "broker_next_step": "Claim guided workflow",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "manual_followup_needed": False,
        "collected_fields": list(_known_facts().keys()),
        "still_needed_fields": [],
        "known_facts": _known_facts(),
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "guided_workflow_state": "collecting_text",
        "extracted_contact_name": "测试客户",
        "extracted_contact_phone": "9495550100",
        "slice1_capability_version": 1,
        "entry_channel": "mini_program",
    }
    stub.update(extra)
    return save_case("[客户] concurrency fixture", stub, service_lane=lane)


def _run_concurrently(*workers: Callable[[], Any]) -> list[Any]:
    """Start every worker at the same instant; return results in worker order."""
    barrier = threading.Barrier(len(workers))
    results: list[Any] = [None] * len(workers)
    errors: list[BaseException] = []
    guard = threading.Lock()

    def _wrap(index: int, fn: Callable[[], Any]) -> Callable[[], None]:
        def _inner() -> None:
            try:
                barrier.wait(timeout=10)
                results[index] = fn()
            except BaseException as exc:  # noqa: BLE001 — surface any worker failure
                with guard:
                    errors.append(exc)

        return _inner

    threads = [threading.Thread(target=_wrap(i, fn)) for i, fn in enumerate(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=20)
        assert not t.is_alive(), "worker thread deadlocked"
    assert errors == [], f"worker raised: {errors!r}"
    return results


def _timeline_types(case: dict[str, Any] | None) -> list[str]:
    return [str(e.get("event_type") or "") for e in ((case or {}).get("claim_timeline") or [])]


def _attachment_ids(case: dict[str, Any] | None) -> list[str]:
    return [
        str(a.get("attachment_id") or "")
        for a in ((case or {}).get("case_attachments") or [])
        if isinstance(a, dict)
    ]


# --- 1. Two concurrent writers must not erase each other -------------------


def test_concurrent_timeline_appends_keep_both_events(widen_race_window):
    """Customer photo event and broker note event race — neither may vanish."""
    cid = _claim_case()["case_id"]

    def _customer() -> None:
        append_claim_timeline_event(
            cid,
            build_claim_timeline_event(
                event_type="evidence_uploaded",
                source_channel="h5_task",
                actor="customer",
                message_id="msg_customer_evidence",
            ),
        )

    def _broker() -> None:
        append_claim_timeline_event(
            cid,
            build_claim_timeline_event(
                event_type="broker_note_added",
                source_channel="workbench",
                actor="broker",
                message_id="msg_broker_note",
            ),
        )

    _run_concurrently(_customer, _broker)

    types = _timeline_types(get_case_by_id(cid))
    assert types.count("evidence_uploaded") == 1
    assert types.count("broker_note_added") == 1


def test_concurrent_photo_uploads_keep_both_attachments(widen_race_window):
    """A phone can upload two photos at once; neither may be dropped."""
    cid = _claim_case()["case_id"]

    def _upload(upload_id: str, attachment_id: str) -> Callable[[], None]:
        def _inner() -> None:
            append_h5_gcs_attachment_metadata(
                cid,
                {
                    "attachment_id": attachment_id,
                    "source": "h5_task",
                    "h5_upload_id": upload_id,
                    "storage_uri": f"gs://bucket/{attachment_id}.jpg",
                    "slot_assignment": "damage_photo",
                },
            )

        return _inner

    _run_concurrently(_upload("up_1", "att_first"), _upload("up_2", "att_second"))

    ids = _attachment_ids(get_case_by_id(cid))
    assert "att_first" in ids
    assert "att_second" in ids


def test_concurrent_known_fact_patches_keep_both_fields(widen_race_window):
    """Customer supplement and broker correction race — both facts must land."""
    cid = _claim_case()["case_id"]

    def _customer() -> None:
        patch_case_known_facts(cid, {"vin": "1HGCM82633A004352"}, source="customer_task")

    def _broker() -> None:
        patch_case_known_facts(
            cid,
            {"policy_or_insurance_card": "card-on-file"},
            source="broker_confirmed",
            explicit_broker_action=True,
        )

    _run_concurrently(_customer, _broker)

    facts = (get_case_by_id(cid) or {}).get("known_facts") or {}
    assert facts.get("vin") == "1HGCM82633A004352"
    assert facts.get("policy_or_insurance_card") == "card-on-file"
    # Pre-existing facts survive both writers.
    assert facts.get("accident_description") == _known_facts()["accident_description"]


def test_concurrent_h5_intake_state_updates_keep_both_keys(widen_race_window):
    """The submit flag and the dedup keys live in one bag — a stale merge loses one."""
    cid = _claim_case()["case_id"]

    def _submit() -> None:
        update_case_h5_intake_state(cid, {"submitted": True, "submitted_at": "2026-08-12T10:00:00Z"})

    def _step() -> None:
        update_case_h5_intake_state(cid, {"last_step": "story", "task_revision": 7})

    _run_concurrently(_submit, _step)

    state = (get_case_by_id(cid) or {}).get("h5_intake_state") or {}
    assert state.get("submitted") is True
    assert state.get("submitted_at") == "2026-08-12T10:00:00Z"
    assert state.get("last_step") == "story"
    assert state.get("task_revision") == 7


def test_concurrent_collected_fields_keep_both(widen_race_window):
    cid = _claim_case()["case_id"]

    _run_concurrently(
        lambda: append_case_collected_fields(cid, ["vin"]),
        lambda: append_case_collected_fields(cid, ["policy_or_insurance_card"]),
    )

    collected = set((get_case_by_id(cid) or {}).get("collected_fields") or [])
    assert "vin" in collected
    assert "policy_or_insurance_card" in collected


# --- 2. A stale writer must not overwrite newer authoritative data ---------


def test_timeline_append_does_not_revert_concurrent_fact_write(widen_race_window):
    """Cross-field lost update: an append must not roll back another writer's facts.

    ``persist_case_append`` writes the whole document, so an unlocked timeline
    append persists the ``known_facts`` it read — reverting a fact the broker
    confirmed in between.
    """
    cid = _claim_case()["case_id"]

    def _append_event() -> None:
        append_claim_timeline_event(
            cid,
            build_claim_timeline_event(
                event_type="evidence_uploaded",
                source_channel="h5_task",
                actor="customer",
                message_id="msg_evidence_only",
            ),
        )

    def _confirm_fact() -> None:
        patch_case_known_facts(
            cid,
            {"vin": "JH4KA7561PC008269"},
            source="broker_confirmed",
            explicit_broker_action=True,
        )

    _run_concurrently(_append_event, _confirm_fact)

    final = get_case_by_id(cid)
    assert (final or {}).get("known_facts", {}).get("vin") == "JH4KA7561PC008269"
    assert _timeline_types(final).count("evidence_uploaded") == 1


def test_photo_upload_does_not_revert_concurrent_intake_state(widen_race_window):
    cid = _claim_case()["case_id"]

    def _upload() -> None:
        append_h5_gcs_attachment_metadata(
            cid,
            {
                "attachment_id": "att_race_photo",
                "source": "h5_task",
                "h5_upload_id": "up_race",
                "storage_uri": "gs://bucket/att_race_photo.jpg",
                "slot_assignment": "damage_photo",
            },
        )

    def _submit() -> None:
        update_case_h5_intake_state(cid, {"submitted": True, "submitted_at": "2026-08-12T11:00:00Z"})

    _run_concurrently(_upload, _submit)

    final = get_case_by_id(cid)
    assert "att_race_photo" in _attachment_ids(final)
    assert ((final or {}).get("h5_intake_state") or {}).get("submitted") is True


# --- 3. Duplicate / retry behaviour stays safe -----------------------------


def test_concurrent_duplicate_timeline_event_appended_once(widen_race_window):
    """Same message_id twice (client retry) must dedupe even under concurrency."""
    cid = _claim_case()["case_id"]

    def _append() -> None:
        append_claim_timeline_event(
            cid,
            build_claim_timeline_event(
                event_type="customer_photo",
                source_channel="h5_task",
                actor="customer",
                message_id="msg_retry_same",
            ),
        )

    _run_concurrently(_append, _append)

    assert _timeline_types(get_case_by_id(cid)).count("customer_photo") == 1


def test_concurrent_duplicate_upload_id_appended_once(widen_race_window):
    """Idempotency on h5_upload_id must be evaluated against the locked read."""
    cid = _claim_case()["case_id"]

    def _upload() -> None:
        append_h5_gcs_attachment_metadata(
            cid,
            {
                "attachment_id": "att_dedup_probe",
                "source": "h5_task",
                "h5_upload_id": "up_same",
                "storage_uri": "gs://bucket/att_dedup_probe.jpg",
                "slot_assignment": "damage_photo",
            },
        )

    _run_concurrently(_upload, _upload)

    ids = _attachment_ids(get_case_by_id(cid))
    assert ids.count("att_dedup_probe") == 1


# --- 4. Broker terminal action: one effect, one End Card -------------------


def test_concurrent_broker_done_one_event_and_one_end_card(monkeypatch, widen_race_window):
    """Two clicks must not stamp twice, duplicate the event, or double-send."""
    cid = _claim_case()["case_id"]
    sends: list[str] = []
    send_guard = threading.Lock()

    def _fake_send(case_id: str) -> dict[str, Any]:
        with send_guard:
            sends.append(case_id)
        return {"sent": True, "end_card_preview": "preview", "send_skipped": False}

    monkeypatch.setattr(
        "services.fiqa_api.wecom.claim_end_card.try_send_claim_end_card", _fake_send
    )

    results = _run_concurrently(
        lambda: mark_claim_broker_done(cid, source="workbench"),
        lambda: mark_claim_broker_done(cid, source="workbench"),
    )

    performed = [r for r in results if r.get("already_done") is False]
    replayed = [r for r in results if r.get("already_done") is True]
    assert len(performed) == 1
    assert len(replayed) == 1
    assert len(sends) == 1, "End Card must reach the customer exactly once"

    final = get_case_by_id(cid)
    assert _timeline_types(final).count("broker_done") == 1
    assert ((final or {}).get("claim_end_card_state") or {}).get("broker_done_at")


def test_broker_done_does_not_erase_concurrent_customer_photo(monkeypatch, widen_race_window):
    """The classic pair: broker closes the collection phase as the customer uploads."""
    cid = _claim_case()["case_id"]
    monkeypatch.setattr(
        "services.fiqa_api.wecom.claim_end_card.try_send_claim_end_card",
        lambda case_id: {"sent": False, "send_skipped": True, "end_card_preview": "p"},
    )

    def _customer_upload() -> None:
        append_h5_gcs_attachment_metadata(
            cid,
            {
                "attachment_id": "att_last_second",
                "source": "h5_task",
                "h5_upload_id": "up_last_second",
                "storage_uri": "gs://bucket/att_last_second.jpg",
                "slot_assignment": "damage_photo",
            },
        )

    _run_concurrently(_customer_upload, lambda: mark_claim_broker_done(cid, source="workbench"))

    final = get_case_by_id(cid)
    assert "att_last_second" in _attachment_ids(final), "customer photo lost to broker_done"
    assert ((final or {}).get("claim_end_card_state") or {}).get("broker_done_at")


# --- 5. Existing business gates still reject invalid transitions -----------


def test_broker_done_wrong_lane_still_raises_and_writes_nothing():
    cid = _claim_case(lane=SERVICE_LANE_ADD_CAR)["case_id"]

    with pytest.raises(ClaimBrokerDoneError, match="not_claim_lane"):
        mark_claim_broker_done(cid)

    final = get_case_by_id(cid)
    assert not ((final or {}).get("claim_end_card_state") or {}).get("broker_done_at")
    assert _timeline_types(final).count("broker_done") == 0


def test_broker_done_missing_case_returns_not_found():
    result = mark_claim_broker_done("case_does_not_exist")
    assert result["outcome"] == "case_not_found"
    assert result["case"] is None


def test_timeline_append_still_noop_for_non_claim_lane():
    cid = _claim_case(lane=SERVICE_LANE_ADD_CAR)["case_id"]
    out = append_claim_timeline_event(
        cid,
        build_claim_timeline_event(event_type="evidence_uploaded", message_id="msg_add_car"),
    )
    assert out is None
    assert _timeline_types(get_case_by_id(cid)) == []


def test_attachment_cap_still_enforced_and_aborts_write():
    cid = _claim_case()["case_id"]
    cap = cs.MAX_ATTACHMENTS_PER_CASE
    assert cap >= 1
    for index in range(cap):
        append_h5_gcs_attachment_metadata(
            cid,
            {
                "attachment_id": f"att_fill_{index}",
                "source": "h5_task",
                "h5_upload_id": f"up_fill_{index}",
                "storage_uri": f"gs://bucket/att_fill_{index}.jpg",
                "slot_assignment": "damage_photo",
            },
        )
    with pytest.raises(ValueError, match="maximum"):
        append_h5_gcs_attachment_metadata(
            cid,
            {
                "attachment_id": "att_overflow",
                "source": "h5_task",
                "h5_upload_id": "up_overflow",
                "storage_uri": "gs://bucket/att_overflow.jpg",
                "slot_assignment": "damage_photo",
            },
        )
    assert "att_overflow" not in _attachment_ids(get_case_by_id(cid))


def test_no_op_mutation_takes_the_lock_but_does_not_persist(monkeypatch):
    """A no-change mutator must not rewrite the whole document under the lock."""
    cid = _claim_case()["case_id"]
    before = get_case_by_id(cid)
    persists: list[str] = []
    original = cs._persist_case_after_update

    def _counting(case_id: str, updated_case: dict[str, Any]) -> bool:
        persists.append(case_id)
        return original(case_id, updated_case)

    monkeypatch.setattr(cs, "_persist_case_after_update", _counting)
    # Already present on the fixture case, so the merge changes nothing.
    append_case_collected_fields(cid, ["accident_description"])

    assert persists == []
    assert get_case_by_id(cid) == before


# --- 6. Postgres path: lock → re-read → mutate → persist -------------------


def _install_fake_lock(monkeypatch, locked_case: dict[str, Any], order: list[str]):
    """Route the PG branch through a probe that records the write order."""

    def _fake_mutate(case_id: str, mutator):
        order.append("lock_and_load")
        result, should_persist = mutator(locked_case)
        order.append("mutated" if should_persist else "no_change")
        if should_persist:
            order.append("persist_under_same_txn")
        return result

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.db_primary_writes_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.json_case_writes_enabled",
        lambda: False,
    )
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.mutate_full_case_under_lock",
        _fake_mutate,
    )


def _locked_claim_case(cid: str, **extra: Any) -> dict[str, Any]:
    """Authoritative state as it exists under the lock, not what a caller read."""
    base: dict[str, Any] = {
        "case_id": cid,
        "service_lane": SERVICE_LANE_CLAIM,
        "known_facts": _known_facts(),
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "claim_timeline": [],
        "case_attachments": [],
        "contact_note": "locked-authoritative-sibling",
        "customer_name": "FromLockedRead",
    }
    base.update(extra)
    return base


def test_db_path_timeline_append_mutates_locked_case(monkeypatch):
    cid = _claim_case()["case_id"]
    order: list[str] = []
    locked = _locked_claim_case(cid)
    _install_fake_lock(monkeypatch, locked, order)

    append_claim_timeline_event(
        cid,
        build_claim_timeline_event(
            event_type="evidence_uploaded", actor="customer", message_id="msg_db_path"
        ),
    )

    assert order == ["lock_and_load", "mutated", "persist_under_same_txn"]
    assert _timeline_types(locked) == ["evidence_uploaded"]
    # The sibling that only exists in the locked read is still intact.
    assert locked["contact_note"] == "locked-authoritative-sibling"


def test_db_path_fact_patch_mutates_locked_case(monkeypatch):
    cid = _claim_case()["case_id"]
    order: list[str] = []
    locked = _locked_claim_case(cid)
    _install_fake_lock(monkeypatch, locked, order)

    patch_case_known_facts(cid, {"vin": "5YJ3E1EA7JF006588"}, source="customer_task")

    assert order == ["lock_and_load", "mutated", "persist_under_same_txn"]
    assert locked["known_facts"]["vin"] == "5YJ3E1EA7JF006588"
    assert locked["customer_name"] == "FromLockedRead"


def test_db_path_photo_append_mutates_locked_case(monkeypatch):
    cid = _claim_case()["case_id"]
    order: list[str] = []
    # A photo already present only in the locked read must survive the append.
    locked = _locked_claim_case(
        cid,
        case_attachments=[
            {"attachment_id": "att_only_in_db", "source": "h5_task", "h5_upload_id": "up_db"}
        ],
    )
    _install_fake_lock(monkeypatch, locked, order)

    append_h5_gcs_attachment_metadata(
        cid,
        {
            "attachment_id": "att_new",
            "source": "h5_task",
            "h5_upload_id": "up_new",
            "storage_uri": "gs://bucket/att_new.jpg",
        },
    )

    assert order == ["lock_and_load", "mutated", "persist_under_same_txn"]
    assert _attachment_ids(locked) == ["att_only_in_db", "att_new"]


def test_db_path_duplicate_upload_id_does_not_persist(monkeypatch):
    """Idempotency decided against the locked read must skip the write entirely."""
    cid = _claim_case()["case_id"]
    order: list[str] = []
    locked = _locked_claim_case(
        cid,
        case_attachments=[
            {"attachment_id": "att_existing", "source": "h5_task", "h5_upload_id": "up_same"}
        ],
    )
    _install_fake_lock(monkeypatch, locked, order)

    append_h5_gcs_attachment_metadata(
        cid,
        {
            "attachment_id": "att_retry",
            "source": "h5_task",
            "h5_upload_id": "up_same",
            "storage_uri": "gs://bucket/att_retry.jpg",
        },
    )

    assert order == ["lock_and_load", "no_change"]
    assert _attachment_ids(locked) == ["att_existing"]


def test_db_path_broker_done_reevaluates_gate_under_lock(monkeypatch):
    """A case already done in the locked read must replay, not stamp again."""
    cid = _claim_case()["case_id"]
    order: list[str] = []
    locked = _locked_claim_case(
        cid,
        claim_end_card_state={"broker_done_at": "2026-08-12T09:00:00Z", "end_card_sent_at": "x"},
    )
    _install_fake_lock(monkeypatch, locked, order)
    sends: list[str] = []
    monkeypatch.setattr(
        "services.fiqa_api.wecom.claim_end_card.try_send_claim_end_card",
        lambda case_id: sends.append(case_id) or {"sent": True},
    )

    result = mark_claim_broker_done(cid)

    assert order == ["lock_and_load", "no_change"]
    assert result["already_done"] is True
    assert sends == [], "replay must not resend the End Card"


def test_db_path_broker_done_blocked_lane_aborts_before_persist(monkeypatch):
    cid = _claim_case()["case_id"]
    order: list[str] = []
    locked = _locked_claim_case(cid, service_lane=SERVICE_LANE_ADD_CAR)
    _install_fake_lock(monkeypatch, locked, order)

    with pytest.raises(ClaimBrokerDoneError, match="not_claim_lane"):
        mark_claim_broker_done(cid)

    assert order == ["lock_and_load"], "blocked gate must not reach persist"
    assert "broker_done" not in _timeline_types(locked)
