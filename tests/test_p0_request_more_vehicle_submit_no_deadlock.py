"""P0 regression: Request More vehicle submit must not nested-persist under Slice1 lock.

Confirmed incident: upsert(..., persist=True) opened a second DB connection that
tried FOR UPDATE on the same service_records row held by Slice1 accept(),
self-deadlocking the QA instance for ~60s (Cloud Run 504) and blocking the
async event loop (/health/live, office queue, case GET).
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from unittest.mock import patch

from services.fiqa_api.inbox_triage.claim_vehicle_identity import ClaimVehicleIdentityService
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    GROUP_STATUS_COMPLETED,
    ITEM_STATUS_SATISFIED,
    InMemorySlice1Store,
    P20Slice1CommandService,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

CASE = "case_p0_deadlock"
VALID_VIN = "1HGCM82633A004352"
# Well under Cloud Run's 60s request timeout; hang would fail this gate.
_SUBMIT_DEADLINE_S = 2.0


def _case(case_id: str = CASE) -> dict:
    return {
        "case_id": case_id,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-23T06:00:00Z",
        "slice1_capability_version": 1,
        "known_facts": {},
    }


def _svc(case_id: str = CASE):
    vehicle = ClaimVehicleIdentityService()
    store = InMemorySlice1Store({case_id: _case(case_id)})
    return P20Slice1CommandService(store, vehicle_service=vehicle), store, vehicle


def _create_vehicle_info(svc: P20Slice1CommandService, case_id: str = CASE) -> dict:
    return svc.accept_request_more(
        case_id=case_id,
        broker_id="office:p0",
        command_id="cmd-create-vi-p0",
        idempotency_key="idem-create-vi-p0",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "item_vi_p0",
                "item_type": "vehicle_information",
                "label": "车辆信息",
                "instructions": "请补充车辆信息",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need vehicle information",
        request_id="req_vi_p0",
    )


def _create_vin(svc: P20Slice1CommandService, case_id: str = CASE) -> dict:
    return svc.accept_request_more(
        case_id=case_id,
        broker_id="office:p0",
        command_id="cmd-create-vin-p0",
        idempotency_key="idem-create-vin-p0",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "item_vin_p0",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "Provide VIN",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN",
        request_id="req_vin_p0",
    )


def _create_policy_card(svc: P20Slice1CommandService, case_id: str = CASE) -> dict:
    return svc.accept_request_more(
        case_id=case_id,
        broker_id="office:p0",
        command_id="cmd-create-card-p0",
        idempotency_key="idem-create-card-p0",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "item_card_p0",
                "item_type": "policy_or_insurance_card",
                "label": "Insurance Card",
                "instructions": "Upload insurance card",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need insurance card",
        request_id="req_card_p0",
    )


def _vehicle_fact() -> dict:
    return {
        "field": "vehicle_information",
        "year": "2020",
        "make": "Toyota",
        "model": "Camry",
        "vin": VALID_VIN,
        "final": True,
    }


def test_vehicle_information_submit_calls_upsert_with_persist_false():
    svc, store, vehicle = _svc()
    created = _create_vehicle_info(svc)
    with patch.object(vehicle, "upsert", wraps=vehicle.upsert) as upsert:
        result = svc.submit_request_item(
            case_id=CASE,
            customer_id="h5:p0",
            active_request_item_id="item_vi_p0",
            command_id="cmd-vi-submit-p0",
            idempotency_key="idem-vi-submit-p0",
            expected_case_version=created["aggregate_version"],
            fact=_vehicle_fact(),
        )
    assert result["outcome"] == "accepted"
    assert upsert.called
    assert upsert.call_args.kwargs.get("persist") is False
    assert store.items["item_vi_p0"].status == ITEM_STATUS_SATISFIED
    assert store.groups["req_vi_p0"].status == GROUP_STATUS_COMPLETED
    facts = store.cases[CASE]["known_facts"]
    assert facts.get("vehicle_information") == "2020 Toyota Camry"
    assert facts.get("vehicle_vin") == VALID_VIN


def test_vehicle_submit_does_not_open_nested_case_store_persist():
    """No second lock path: patch_case_known_facts / persist_case_append must not run."""
    svc, store, _vehicle = _svc()
    created = _create_vehicle_info(svc)

    def _boom(*_a, **_k):
        raise AssertionError("nested case_store persist must not run under Slice1 accept()")

    with (
        patch(
            "services.fiqa_api.inbox_triage.case_store.patch_case_known_facts",
            side_effect=_boom,
        ),
        patch(
            "services.fiqa_api.db.service_record_repository.persist_case_append",
            side_effect=_boom,
        ),
    ):
        result = svc.submit_request_item(
            case_id=CASE,
            customer_id="h5:p0",
            active_request_item_id="item_vi_p0",
            command_id="cmd-vi-no-nested",
            idempotency_key="idem-vi-no-nested",
            expected_case_version=created["aggregate_version"],
            fact=_vehicle_fact(),
        )
    assert result["outcome"] == "accepted"
    # Facts persisted exactly once via Slice1 store / legacy projection path.
    assert store.cases[CASE]["known_facts"].get("vehicle_information") == "2020 Toyota Camry"
    assert store.cases[CASE]["known_facts"].get("vehicle_vin") == VALID_VIN


def test_vehicle_submit_completes_under_timeout_even_if_nested_persist_would_block():
    """Timeout gate: if persist=True returns, nested persist sleep would miss deadline."""
    svc, _store, _vehicle = _svc()
    created = _create_vehicle_info(svc)

    def _blocking_persist(*_a, **_k):
        time.sleep(30)
        return None

    with patch(
        "services.fiqa_api.inbox_triage.case_store.patch_case_known_facts",
        side_effect=_blocking_persist,
    ):
        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(
                svc.submit_request_item,
                case_id=CASE,
                customer_id="h5:p0",
                active_request_item_id="item_vi_p0",
                command_id="cmd-vi-timeout-gate",
                idempotency_key="idem-vi-timeout-gate",
                expected_case_version=created["aggregate_version"],
                fact=_vehicle_fact(),
            )
            try:
                result = fut.result(timeout=_SUBMIT_DEADLINE_S)
            except FuturesTimeout as exc:
                fut.cancel()
                raise AssertionError(
                    "vehicle Request More submit exceeded "
                    f"{_SUBMIT_DEADLINE_S}s — nested persist deadlock likely restored"
                ) from exc
        elapsed = time.monotonic() - started
    assert result["outcome"] == "accepted"
    assert elapsed < _SUBMIT_DEADLINE_S


def test_vehicle_submit_keeps_concurrent_health_probe_responsive():
    """While submit runs, a concurrent probe must still complete quickly."""
    svc, _store, _vehicle = _svc()
    created = _create_vehicle_info(svc)
    probe_latencies: list[float] = []
    barrier = threading.Barrier(2)

    def _submit():
        barrier.wait(timeout=2)
        return svc.submit_request_item(
            case_id=CASE,
            customer_id="h5:p0",
            active_request_item_id="item_vi_p0",
            command_id="cmd-vi-concurrent",
            idempotency_key="idem-vi-concurrent",
            expected_case_version=created["aggregate_version"],
            fact=_vehicle_fact(),
        )

    def _health_probe():
        barrier.wait(timeout=2)
        t0 = time.monotonic()
        # Stand-in for /health/live + office queue responsiveness on the API process.
        ok = True
        probe_latencies.append(time.monotonic() - t0)
        return ok

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_submit = pool.submit(_submit)
        fut_health = pool.submit(_health_probe)
        health_ok = fut_health.result(timeout=_SUBMIT_DEADLINE_S)
        result = fut_submit.result(timeout=_SUBMIT_DEADLINE_S)

    assert health_ok is True
    assert result["outcome"] == "accepted"
    assert probe_latencies and probe_latencies[0] < 0.25


def test_vehicle_submit_replay_does_not_duplicate_facts():
    svc, store, _vehicle = _svc()
    created = _create_vehicle_info(svc)
    first = svc.submit_request_item(
        case_id=CASE,
        customer_id="h5:p0",
        active_request_item_id="item_vi_p0",
        command_id="cmd-vi-replay",
        idempotency_key="idem-vi-replay",
        expected_case_version=created["aggregate_version"],
        fact=_vehicle_fact(),
    )
    assert first["outcome"] == "accepted"
    facts_after = dict(store.cases[CASE]["known_facts"])
    version_after = store.aggregates[CASE].aggregate_version

    replay = svc.submit_request_item(
        case_id=CASE,
        customer_id="h5:p0",
        active_request_item_id="item_vi_p0",
        command_id="cmd-vi-replay",
        idempotency_key="idem-vi-replay",
        expected_case_version=created["aggregate_version"],
        fact=_vehicle_fact(),
    )
    assert replay["outcome"] == "replayed"
    assert store.cases[CASE]["known_facts"] == facts_after
    assert store.aggregates[CASE].aggregate_version == version_after
    vi_items = [i for i in store.items.values() if i.item_type == "vehicle_information"]
    assert len(vi_items) == 1


def test_vin_submit_also_uses_persist_false():
    svc, store, vehicle = _svc()
    created = _create_vin(svc)
    with patch.object(vehicle, "upsert", wraps=vehicle.upsert) as upsert:
        result = svc.submit_request_item(
            case_id=CASE,
            customer_id="h5:p0",
            active_request_item_id="item_vin_p0",
            command_id="cmd-vin-submit-p0",
            idempotency_key="idem-vin-submit-p0",
            expected_case_version=created["aggregate_version"],
            fact={"field": "vin", "value": VALID_VIN, "vin": VALID_VIN},
        )
    assert result["outcome"] == "accepted"
    assert upsert.call_args.kwargs.get("persist") is False
    assert store.cases[CASE]["known_facts"].get("vehicle_vin") == VALID_VIN


def test_non_vehicle_request_more_item_unaffected():
    svc, store, vehicle = _svc()
    created = _create_policy_card(svc)
    with patch.object(vehicle, "upsert", wraps=vehicle.upsert) as upsert:
        result = svc.submit_request_item(
            case_id=CASE,
            customer_id="h5:p0",
            active_request_item_id="item_card_p0",
            command_id="cmd-card-submit-p0",
            idempotency_key="idem-card-submit-p0",
            expected_case_version=created["aggregate_version"],
            evidence={"attachment_id": "att_card_p0"},
        )
    assert result["outcome"] == "accepted"
    assert not upsert.called
    assert store.items["item_card_p0"].status == ITEM_STATUS_SATISFIED
    assert store.groups["req_card_p0"].status == GROUP_STATUS_COMPLETED


def test_source_contains_persist_false_guard():
    """Static guard so the one-line fix cannot silently flip back to True."""
    from pathlib import Path

    src = Path("services/fiqa_api/inbox_triage/p20_slice1_command_service.py").read_text(
        encoding="utf-8"
    )
    assert "persist=False" in src
    # The dangerous nested persist must not reappear on the Slice1 submit path.
    assert "persist=True" not in src
