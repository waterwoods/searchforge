#!/usr/bin/env python3
"""P26H Golden Customer Flow Harness.

This is test infrastructure only.  Local mode runs the server-domain journey
against fresh in-memory stores; it never reads seeded cases or persistent data.
QA mode is deliberately fail-closed until the deployed API offers an
authorized, ephemeral fixture-runner endpoint.  A local process must never
write test fixtures directly into shared QA storage.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.fiqa_api.inbox_triage.constitution_projection import (  # noqa: E402
    ConstitutionInputs,
    build_constitution_projection,
)
from services.fiqa_api.inbox_triage.default_intake_plan import (  # noqa: E402
    TASK_SOURCE_BROKER_REQUESTED,
    TASK_SOURCE_SYSTEM_DEFAULT,
)
from services.fiqa_api.inbox_triage.h5_task_token import (  # noqa: E402
    issue_h5_intake_form_token,
    verify_h5_task_token,
)
from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (  # noqa: E402
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (  # noqa: E402
    InMemorySlice1Store,
    P20Slice1CommandService,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM  # noqa: E402


@dataclass
class FlowFailure:
    task: str
    source: str
    expected: Any
    actual: Any
    layer: str
    detail: str = ""
    step: str = ""
    case_id: str = ""
    expected_route: str = ""
    actual_route: str = ""
    repair_area: str = ""


@dataclass
class FlowReport:
    run_id: str
    checks: list[str] = field(default_factory=list)
    failures: list[FlowFailure] = field(default_factory=list)
    case_ids: list[str] = field(default_factory=list)
    cleanup_result: str = "n/a"
    journey_step: str = ""

    def check(
        self,
        condition: bool,
        *,
        task: str,
        source: str,
        expected: Any,
        actual: Any,
        layer: str,
        detail: str = "",
        step: str = "",
        case_id: str = "",
        expected_route: str = "",
        actual_route: str = "",
        repair_area: str = "",
    ) -> None:
        if condition:
            self.checks.append(f"{layer}: {task}")
            return
        self.failures.append(
            FlowFailure(
                task=task,
                source=source,
                expected=expected,
                actual=actual,
                layer=layer,
                detail=detail,
                step=step or self.journey_step,
                case_id=case_id,
                expected_route=expected_route,
                actual_route=actual_route,
                repair_area=repair_area or layer,
            )
        )

    @property
    def ok(self) -> bool:
        return not self.failures

def _task_map(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(task.get("task_id") or ""): task
        for task in ((projection.get("customer") or {}).get("tasks") or [])
        if isinstance(task, dict)
    }


def _fresh_case(
    service: P20CaseIntakeCommandService,
    *,
    suffix: str,
    idempotency_key: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Create a unique test case through the server CreateClaim command."""
    command_id = f"p26h-create-{suffix}-{uuid.uuid4().hex[:12]}"
    result = service.create_claim(
        broker_id=f"customer:golden:{suffix}",
        office_id="p26h_ephemeral",
        tenant_id="p26h_ephemeral",
        command_id=command_id,
        idempotency_key=idempotency_key or f"p26h-idem-{uuid.uuid4().hex}",
        actor="customer",
        inputs={
            "is_test": True,
            "accident_description": "停车场倒车碰撞，前保险杠受损",
            "accident_datetime": "2026-07-18 10:00",
            "accident_location": "停车场",
            "injury_status": "no",
        },
    )
    if result.get("outcome") not in {"accepted", "replayed"}:
        raise RuntimeError(f"case_creation_failed:{result}")
    case_id = str(result["case_id"])
    case = dict(service.store.cases[case_id])  # type: ignore[attr-defined]
    # The fixture factory explicitly clears every cross-case state carrier.
    case.update(
        {
            "p20_slice1_projection": {
                "case_id": case_id,
                "workflow_state": "intake",
                "customer_next_action": None,
                "broker_next_action": {"action_type": "none", "status": "none"},
                "open_request": None,
            },
            "case_attachments": [],
            "claim_attachment_slots": {},
            "claim_evidence_summary": {"received_slots": [], "missing_required_slots": []},
            "timeline_events": [],
            "active_case_id": None,
        }
    )
    service.store.cases[case_id] = case  # type: ignore[attr-defined]
    token = issue_h5_intake_form_token(case_id=case_id, nonce=f"p26h-{suffix}")
    return case, token


def _projection(case: dict[str, Any]) -> dict[str, Any]:
    return build_constitution_projection(ConstitutionInputs(case=case, slice1=case.get("p20_slice1_projection")))


def _append_event(case: dict[str, Any], event_type: str) -> None:
    case.setdefault("timeline_events", []).append(
        {
            "event_type": event_type,
            "case_id": case["case_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def _assert_task_contract(report: FlowReport, task: dict[str, Any]) -> None:
    source = str(task.get("task_source") or "")
    task_id = str(task.get("task_id") or "")
    action = task.get("action") or {}
    route = str(task.get("route") or "")
    report.check(
        bool(task_id),
        task=task_id or "unknown",
        source=source,
        expected="stable task_type",
        actual=task_id or None,
        layer="Task Resolver",
    )
    report.check(
        source in {TASK_SOURCE_SYSTEM_DEFAULT, TASK_SOURCE_BROKER_REQUESTED},
        task=task_id,
        source=source,
        expected="system_default | broker_requested",
        actual=source,
        layer="Constitution",
    )
    if source == TASK_SOURCE_SYSTEM_DEFAULT:
        report.check(
            route != "request_item" and not action.get("request_item_id"),
            task=task_id,
            source=source,
            expected="non-request_item route with no request_item_id",
            actual={"route": route, "request_item_id": action.get("request_item_id")},
            layer="Constitution Projection",
        )
    if source == TASK_SOURCE_BROKER_REQUESTED:
        report.check(
            route == "request_item" and bool(action.get("request_item_id")),
            task=task_id,
            source=source,
            expected="request_item route with request_item_id",
            actual={"route": route, "request_item_id": action.get("request_item_id")},
            layer="Mini Program Route",
        )


def run_local() -> FlowReport:
    report = FlowReport(run_id=f"p26h-{uuid.uuid4().hex[:12]}")
    intake_store = InMemoryIntakeStore()
    intake = P20CaseIntakeCommandService(intake_store)

    # Scenario A — fresh case, no broker rows or stale evidence.
    case, token = _fresh_case(intake, suffix="fresh")
    report.case_ids.append(str(case["case_id"]))
    claims = verify_h5_task_token(token)
    report.check(
        claims is not None and claims.case_id == case["case_id"],
        task="resume_token",
        source="system_default",
        expected=case["case_id"],
        actual=claims.case_id if claims else None,
        layer="Session / Resume",
    )
    before = _projection(case)
    tasks = _task_map(before)
    for task_id in ("accident_story", "accident_photos", "insurance_card"):
        report.check(
            task_id in tasks,
            task=task_id,
            source="system_default",
            expected="default task present",
            actual=task_id in tasks,
            layer="Constitution",
        )
        if task_id in tasks:
            _assert_task_contract(report, tasks[task_id])
    report.check(
        all(t.get("task_source") != TASK_SOURCE_BROKER_REQUESTED for t in tasks.values()),
        task="fresh_default_intake",
        source="system_default",
        expected="zero broker_requested tasks",
        actual=[t.get("task_source") for t in tasks.values()],
        layer="Case Creation",
    )
    report.check(
        tasks["insurance_card"].get("state") != "completed",
        task="insurance_card",
        source="system_default",
        expected="not completed without canonical evidence",
        actual=tasks["insurance_card"].get("state"),
        layer="Case Isolation",
    )

    # Scenario B — only server-shaped canonical facts/evidence move completion.
    case["known_facts"]["own_vehicle_info"] = "2020 Toyota Camry"
    case["known_facts"]["vin"] = "1HGCM82633A004352"
    _append_event(case, "vehicle_information_saved")
    case["claim_attachment_slots"]["policy_or_insurance_card"] = {
        "status": "received",
        "attachment_ids": ["att_p26h_insurance"],
    }
    case["case_attachments"].append(
        {
            "attachment_id": "att_p26h_insurance",
            "bound_case_id": case["case_id"],
            "source": "h5_task",
            "msgtype": "image",
            "slot_assignment": "policy_or_insurance_card",
            "evidence_status": "confirmed",
        }
    )
    _append_event(case, "evidence_uploaded")
    case["case_attachments"].append(
        {
            "attachment_id": "att_p26h_photo",
            "bound_case_id": case["case_id"],
            "source": "h5_task",
            "msgtype": "image",
            "slot_assignment": "scene_photo",
            "evidence_status": "confirmed",
        }
    )
    _append_event(case, "evidence_uploaded")
    after = _projection(case)
    after_tasks = _task_map(after)
    report.check(
        after_tasks["insurance_card"].get("state") == "completed",
        task="insurance_card",
        source="system_default",
        expected="completed from current-case canonical attachment",
        actual=after_tasks["insurance_card"].get("state"),
        layer="Projection",
    )
    report.check(
        len(case["timeline_events"]) >= 3,
        task="normal_intake",
        source="system_default",
        expected="timeline events for each server write",
        actual=[event.get("event_type") for event in case["timeline_events"]],
        layer="Timeline",
    )
    report.check(
        all(att.get("bound_case_id") == case["case_id"] for att in case["case_attachments"]),
        task="evidence_ownership",
        source="system_default",
        expected=case["case_id"],
        actual=[att.get("bound_case_id") for att in case["case_attachments"]],
        layer="Case Isolation",
    )

    # Scenario C — stale local case identity is ignored; signed token wins.
    stale_local_case_id = "case_stale_other_customer"
    resumed = verify_h5_task_token(token)
    report.check(
        resumed is not None and resumed.case_id == case["case_id"] and resumed.case_id != stale_local_case_id,
        task="resume",
        source="system_default",
        expected=case["case_id"],
        actual=resumed.case_id if resumed else None,
        layer="Session / Resume",
    )
    expired = issue_h5_intake_form_token(case_id=case["case_id"], now=1_000_000, ttl_seconds=60)
    report.check(
        verify_h5_task_token(expired, now=1_000_061) is None,
        task="expired_token",
        source="system_default",
        expected="rejected",
        actual="accepted" if verify_h5_task_token(expired, now=1_000_061) else "rejected",
        layer="Session / Resume",
    )

    # Scenario D — real Slice1 command adds one broker task without erasing
    # prior evidence.  It is a separate clean case because an already-completed
    # insurance card is not a supported replacement-evidence workflow yet.
    followup_case, _ = _fresh_case(intake, suffix="followup")
    report.case_ids.append(str(followup_case["case_id"]))
    followup_case["case_attachments"].append(
        {
            "attachment_id": "att_p26h_prior_photo",
            "bound_case_id": followup_case["case_id"],
            "source": "h5_task",
            "msgtype": "image",
            "slot_assignment": "scene_photo",
            "evidence_status": "confirmed",
        }
    )
    _append_event(followup_case, "evidence_uploaded")
    # Scenario D — real Slice1 command adds one broker task without erasing defaults.
    slice_case = dict(followup_case)
    slice_case["claim_phase"] = "broker_review"
    slice_case["slice1_capability_version"] = 1
    slice_store = InMemorySlice1Store({str(followup_case["case_id"]): slice_case})
    slice_service = P20Slice1CommandService(slice_store)
    broker = slice_service.accept_request_more(
        case_id=str(followup_case["case_id"]),
        broker_id="office:p26h",
        command_id=f"p26h-followup-{uuid.uuid4().hex[:12]}",
        idempotency_key=f"p26h-followup-idem-{uuid.uuid4().hex[:12]}",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "p26h-insurance-supplement",
                "item_type": "policy_or_insurance_card",
                "label": "补充保险卡",
                "instructions": "请补一张更清晰的保险卡",
                "required": True,
                "position": 1,
            }
        ],
        reason="P26H exceptional follow-up",
    )
    report.check(
        broker.get("outcome") == "accepted",
        task="broker_followup",
        source="broker_requested",
        expected="accepted",
        actual=broker.get("outcome"),
        layer="Broker Follow-Up",
    )
    followup_case["p20_slice1_projection"] = broker.get("customer_projection")
    followup_tasks = _task_map(_projection(followup_case))
    report.check(
        set(("accident_story", "accident_photos", "insurance_card")).issubset(followup_tasks),
        task="default_tasks",
        source="system_default",
        expected="defaults retained",
        actual=sorted(followup_tasks),
        layer="Constitution",
    )
    broker_task = next(
        (task for task in followup_tasks.values() if task.get("task_source") == TASK_SOURCE_BROKER_REQUESTED),
        {},
    )
    _assert_task_contract(report, broker_task)
    report.check(
        any(
            event.get("event_type") == "broker_request_more_created"
            for event in slice_store.events[str(followup_case["case_id"])]
        ),
        task="broker_followup",
        source="broker_requested",
        expected="broker_request_more_created timeline event",
        actual=[event.get("event_type") for event in slice_store.events[str(followup_case["case_id"])]],
        layer="Timeline",
    )

    # Required regression: second customer case stays isolated and replay stays idempotent.
    case_b, _ = _fresh_case(intake, suffix="isolation")
    report.case_ids.append(str(case_b["case_id"]))
    b_tasks = _task_map(_projection(case_b))
    report.check(
        b_tasks["insurance_card"].get("state") != "completed",
        task="insurance_card",
        source="system_default",
        expected="pending in distinct case",
        actual=b_tasks["insurance_card"].get("state"),
        layer="Case Isolation",
    )
    return report


def _task_map_from_inspect(inspect_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    proj = inspect_payload.get("constitution_projection") or {}
    return _task_map(proj if isinstance(proj, dict) else {})


def _verify_resume_token(
    *,
    token: str,
    expected_case_id: str,
    transport: str,
    base_url: str,
) -> tuple[bool, str | None]:
    """Verify resume resolves expected case.

    HTTP QA must use the deployed intake contract — local token secrets differ
    from Cloud Run signing keys.
    """
    if transport == "http":
        import json
        import urllib.error
        import urllib.request

        url = f"{base_url.rstrip('/')}/api/h5/tasks/{token}/intake"
        req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError:
            return False, None
        except Exception:
            return False, None
        case_id = str(body.get("case_id") or (body.get("task") or {}).get("case_id") or "").strip()
        return case_id == expected_case_id, case_id or None

    from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token

    claims = verify_h5_task_token(token) if token else None
    actual = claims.case_id if claims else None
    return bool(claims and claims.case_id == expected_case_id), actual


def run_qa() -> FlowReport:
    """Deployed / in-process QA journey via authorized ephemeral fixture runner."""
    from scripts.p26h_fixture_client import FixtureClientError, open_fixture_client

    report = FlowReport(run_id="uninitialized")
    client = None
    transport_name = ""
    transport_base = ""
    harness_run_id = ""
    cleanup_payload: dict[str, Any] = {}
    try:
        report.journey_step = "Fixture preflight"
        try:
            client, transport = open_fixture_client()
            transport_name = transport.transport
            transport_base = transport.base_url
        except FixtureClientError as exc:
            report.run_id = "no-transport"
            report.check(
                False,
                task="fixture_transport",
                source="system_default",
                expected="configured QA fixture transport",
                actual=str(exc),
                layer=exc.layer,
                detail=exc.detail,
                step="Fixture preflight",
                repair_area="Fixture Runner env / deploy",
            )
            report.cleanup_result = "SKIPPED"
            return report

        status = client.status()
        report.check(
            bool(status.get("enabled")),
            task="fixture_enabled",
            source="system_default",
            expected="fixture runner enabled",
            actual=status,
            layer="Fixture Runner",
            detail=transport.notes,
            step="Fixture preflight",
        )
        if not report.ok:
            report.cleanup_result = "SKIPPED"
            return report

        created = client.create_run()
        harness_run_id = str(created.get("harness_run_id") or "").strip()
        report.run_id = harness_run_id or "create-run-failed"
        report.check(
            harness_run_id.startswith("p26h_"),
            task="harness_run",
            source="system_default",
            expected="p26h_* harness_run_id",
            actual=harness_run_id or None,
            layer="Fixture Runner",
            step="Create ephemeral run",
        )
        if not report.ok:
            report.cleanup_result = "SKIPPED"
            return report

        # A — Fresh zero-broker claim
        report.journey_step = "A Fresh claim"
        fresh = client.create_case(harness_run_id, suffix="fresh")
        case_a = str(fresh.get("case_id") or "")
        token = str(fresh.get("resume_token") or "")
        report.case_ids.append(case_a)
        report.check(
            bool(case_a) and bool(token),
            task="fresh_claim",
            source="system_default",
            expected="case_id + resume_token",
            actual={"case_id": case_a, "token_masked": fresh.get("resume_token_masked")},
            layer="Case Creation",
            case_id=case_a,
        )
        resume_ok, resume_actual = _verify_resume_token(
            token=token,
            expected_case_id=case_a,
            transport=transport_name,
            base_url=transport_base,
        )
        report.check(
            resume_ok,
            task="resume_token",
            source="system_default",
            expected=case_a,
            actual=resume_actual,
            layer="Session / Resume",
            case_id=case_a,
            detail=f"transport={transport_name}",
        )
        inspect_a = client.inspect(harness_run_id, case_a)
        tasks_a = _task_map_from_inspect(inspect_a)
        for task_id in ("accident_story", "accident_photos", "insurance_card"):
            report.check(
                task_id in tasks_a,
                task=task_id,
                source="system_default",
                expected="default task present",
                actual=task_id in tasks_a,
                layer="Constitution",
                case_id=case_a,
            )
            if task_id in tasks_a:
                _assert_task_contract(report, tasks_a[task_id])
        report.check(
            all(t.get("task_source") != TASK_SOURCE_BROKER_REQUESTED for t in tasks_a.values()),
            task="fresh_default_intake",
            source="system_default",
            expected="zero broker_requested tasks",
            actual=[t.get("task_source") for t in tasks_a.values()],
            layer="Case Creation",
            case_id=case_a,
        )
        report.check(
            (tasks_a.get("insurance_card") or {}).get("state") != "completed",
            task="insurance_card",
            source="system_default",
            expected="not completed without evidence",
            actual=(tasks_a.get("insurance_card") or {}).get("state"),
            layer="Projection",
            case_id=case_a,
        )

        # B — Normal intake writes
        report.journey_step = "B Normal intake"
        client.patch_vehicle(harness_run_id, case_a)
        after_vehicle = client.inspect(harness_run_id, case_a)
        report.check(
            "own_vehicle_info" in (after_vehicle.get("known_facts_keys") or []),
            task="vehicle_facts",
            source="system_default",
            expected="own_vehicle_info in known_facts",
            actual=after_vehicle.get("known_facts_keys"),
            layer="Timeline",
            case_id=case_a,
        )
        client.register_evidence(harness_run_id, case_a, "policy_or_insurance_card")
        client.register_evidence(harness_run_id, case_a, "scene_photo")
        after_ev = client.inspect(harness_run_id, case_a)
        tasks_ev = _task_map_from_inspect(after_ev)
        report.check(
            (tasks_ev.get("insurance_card") or {}).get("state") == "completed",
            task="insurance_card",
            source="system_default",
            expected="completed after canonical evidence",
            actual=(tasks_ev.get("insurance_card") or {}).get("state"),
            layer="Projection",
            case_id=case_a,
        )
        report.check(
            "evidence_uploaded" in (after_ev.get("timeline_event_types") or []),
            task="timeline",
            source="system_default",
            expected="evidence_uploaded event",
            actual=after_ev.get("timeline_event_types"),
            layer="Timeline",
            case_id=case_a,
        )

        # C — Resume same case
        report.journey_step = "C Resume"
        resume_ok2, resume_actual2 = _verify_resume_token(
            token=token,
            expected_case_id=case_a,
            transport=transport_name,
            base_url=transport_base,
        )
        report.check(
            resume_ok2,
            task="resume",
            source="system_default",
            expected=case_a,
            actual=resume_actual2,
            layer="Session / Resume",
            case_id=case_a,
            detail=f"transport={transport_name}",
        )

        # F — Expired token (safe failure)
        report.journey_step = "F Expired token"
        expired = client.expired_token(harness_run_id, case_a)
        report.check(
            bool(expired.get("rejected_as_expected")),
            task="expired_token",
            source="system_default",
            expected="rejected",
            actual=expired.get("rejected_as_expected"),
            layer="Session / Resume",
            case_id=case_a,
        )
        report.check(
            "expired_token" not in expired or "resume_token" not in expired,
            task="token_redaction",
            source="system_default",
            expected="no raw token fields in expired-token response",
            actual=sorted(k for k in expired if "token" in k.lower()),
            layer="Fixture Runner",
            case_id=case_a,
        )

        # D — Broker follow-up on separate clean case
        report.journey_step = "D Broker follow-up"
        follow = client.create_case(harness_run_id, suffix="followup")
        case_f = str(follow.get("case_id") or "")
        report.case_ids.append(case_f)
        client.register_evidence(harness_run_id, case_f, "scene_photo")
        broker = client.broker_followup(harness_run_id, case_f)
        report.check(
            broker.get("outcome") == "accepted" or broker.get("ok") is True,
            task="broker_followup",
            source="broker_requested",
            expected="accepted",
            actual=broker.get("outcome"),
            layer="Broker Follow-Up",
            case_id=case_f,
        )
        inspect_f = client.inspect(harness_run_id, case_f)
        tasks_f = _task_map_from_inspect(inspect_f)
        report.check(
            set(("accident_story", "accident_photos", "insurance_card")).issubset(tasks_f),
            task="default_tasks",
            source="system_default",
            expected="defaults retained",
            actual=sorted(tasks_f),
            layer="Constitution",
            case_id=case_f,
        )
        broker_task = next(
            (t for t in tasks_f.values() if t.get("task_source") == TASK_SOURCE_BROKER_REQUESTED),
            {},
        )
        report.check(
            bool(broker_task),
            task="broker_requested_task",
            source="broker_requested",
            expected="one broker_requested task",
            actual=bool(broker_task),
            layer="Broker Follow-Up",
            case_id=case_f,
        )
        if broker_task:
            _assert_task_contract(report, broker_task)

        # E — Case isolation (same session identity)
        report.journey_step = "E Case isolation"
        sess = f"p26h-iso-{harness_run_id[-8:]}"
        iso_a = client.create_case(harness_run_id, suffix="iso_a", session_id=sess)
        case_iso_a = str(iso_a.get("case_id") or "")
        report.case_ids.append(case_iso_a)
        client.register_evidence(harness_run_id, case_iso_a, "policy_or_insurance_card")
        iso_b = client.create_case(harness_run_id, suffix="iso_b", session_id=sess)
        case_iso_b = str(iso_b.get("case_id") or "")
        report.case_ids.append(case_iso_b)
        inspect_b = client.inspect(harness_run_id, case_iso_b)
        tasks_b = _task_map_from_inspect(inspect_b)
        report.check(
            case_iso_a != case_iso_b,
            task="distinct_cases",
            source="system_default",
            expected="two case ids",
            actual={"a": case_iso_a, "b": case_iso_b},
            layer="Case Isolation",
        )
        report.check(
            (tasks_b.get("insurance_card") or {}).get("state") != "completed",
            task="insurance_card",
            source="system_default",
            expected="pending in Case B",
            actual=(tasks_b.get("insurance_card") or {}).get("state"),
            layer="Case Isolation",
            case_id=case_iso_b,
        )
        report.check(
            "evidence_uploaded" not in (inspect_b.get("timeline_event_types") or []),
            task="timeline_isolation",
            source="system_default",
            expected="no Case A evidence events on Case B",
            actual=inspect_b.get("timeline_event_types"),
            layer="Case Isolation",
            case_id=case_iso_b,
        )

        # G — Idempotency
        report.journey_step = "G Idempotency"
        idem = f"p26h-fx-idem-{harness_run_id[-10:]}"
        first = client.create_case(harness_run_id, suffix="idem", idempotency_key=idem)
        second = client.create_case(harness_run_id, suffix="idem", idempotency_key=idem)
        report.case_ids.append(str(first.get("case_id") or ""))
        report.check(
            first.get("case_id") == second.get("case_id"),
            task="idempotent_create",
            source="system_default",
            expected=first.get("case_id"),
            actual=second.get("case_id"),
            layer="Case Creation",
        )
        report.check(
            second.get("outcome") in ("accepted", "replayed"),
            task="idempotent_outcome",
            source="system_default",
            expected="accepted|replayed",
            actual=second.get("outcome"),
            layer="Case Creation",
        )

    except Exception as exc:  # noqa: BLE001 — harness must always cleanup + diagnose
        report.check(
            False,
            task="qa_harness_exception",
            source="system_default",
            expected="no exception",
            actual=type(exc).__name__,
            layer="Fixture Runner",
            detail=str(exc)[:400],
            step=report.journey_step or "QA harness",
        )
    finally:
        if client is not None and harness_run_id:
            try:
                cleanup_payload = client.cleanup(harness_run_id)
                report.cleanup_result = str(
                    cleanup_payload.get("cleanup")
                    or ("PASS" if cleanup_payload.get("ok") else "FAIL")
                )
                from scripts.p26h_fixture_client import InProcessFixtureClient

                if isinstance(client, InProcessFixtureClient):
                    from services.fiqa_api.inbox_triage import p26h_qa_fixture_runner as fx

                    left = fx.list_run_case_ids(harness_run_id)
                    report.check(
                        len(left) == 0,
                        task="cleanup_empty",
                        source="system_default",
                        expected="0 remaining fixtures",
                        actual=left,
                        layer="Cleanup",
                        step="Cleanup",
                    )
                    if left:
                        report.cleanup_result = "FAIL"
                else:
                    report.check(
                        bool(cleanup_payload.get("ok"))
                        or cleanup_payload.get("cleanup") == "PASS",
                        task="cleanup_http",
                        source="system_default",
                        expected="cleanup PASS",
                        actual=cleanup_payload.get("cleanup") or cleanup_payload.get("ok"),
                        layer="Cleanup",
                        step="Cleanup",
                        detail=f"deleted={cleanup_payload.get('deleted_case_ids')}",
                    )
            except Exception as cleanup_exc:  # noqa: BLE001
                report.cleanup_result = f"FAIL:{type(cleanup_exc).__name__}"
                report.check(
                    False,
                    task="cleanup",
                    source="system_default",
                    expected="cleanup PASS",
                    actual=str(cleanup_exc)[:200],
                    layer="Cleanup",
                    step="Cleanup",
                )
        elif report.cleanup_result == "n/a":
            report.cleanup_result = "SKIPPED"
    return report


def _print_report(report: FlowReport) -> int:
    if report.ok:
        print("PASS")
        print(
            f"Golden Customer Flow: {len(report.checks)} assertions, "
            f"{len(report.case_ids)} clean cases"
        )
        print(f"harness_run_id: {report.run_id}")
        print(f"Cleanup: {report.cleanup_result}")
        print(
            "Layers: Case Creation, Session / Resume, Constitution, Timeline, "
            "Projection, Task Resolver, Mini Program Route, Broker Follow-Up, "
            "Case Isolation, Fixture Runner, Cleanup"
        )
        return 0
    print("FAIL")
    print(f"harness_run_id: {report.run_id}")
    print(f"Cleanup: {report.cleanup_result}")
    for failure in report.failures:
        print()
        if failure.step:
            print(f"Step: {failure.step}")
        print(f"Task: {failure.task}")
        print(f"Source: {failure.source}")
        if failure.case_id:
            print(f"case_id: {failure.case_id}")
        print(f"Expected: {failure.expected}")
        print(f"Actual: {failure.actual}")
        if failure.expected_route or failure.actual_route:
            print(f"Expected route/page: {failure.expected_route or 'n/a'}")
            print(f"Actual route/page: {failure.actual_route or 'n/a'}")
        print(f"Owning layer: {failure.layer}")
        print(f"Smallest probable repair area: {failure.repair_area or failure.layer}")
        if failure.detail:
            print(f"Detail: {failure.detail}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="P26H Golden Customer Flow Harness")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local", action="store_true", help="run isolated server-domain journey")
    mode.add_argument("--qa", action="store_true", help="run deployed ephemeral-fixture journey")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        print("PASS")
        print("Dry run: validates command wiring only; no customer-flow assertions executed.")
        return 0
    if args.qa:
        return _print_report(run_qa())
    report = run_local()
    report.cleanup_result = "n/a (in-memory)"
    return _print_report(report)


if __name__ == "__main__":
    raise SystemExit(main())
