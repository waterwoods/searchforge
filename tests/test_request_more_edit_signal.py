"""AI Request More pilot signal — did the broker edit the AI draft before sending?

Covers the whole path the broker actually walks: deterministic missing set →
draft assist → SaveRequestDraft → SendRequest → durable telemetry, plus the
normalization rules that decide what counts as an edit.
"""

from __future__ import annotations

import copy
import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_send_request_command_service import (
    InMemorySendRequestStore,
    P20SendRequestCommandService,
)
from services.fiqa_api.inbox_triage.request_more_assistant import service as assist_service
from services.fiqa_api.inbox_triage.request_more_assistant.edit_signal import (
    customer_facing_signature,
    evaluate_send_signal,
    extract_stored_send_signals,
    normalize_ai_provenance,
    normalize_customer_text,
    summarize_send_signals,
)
from services.fiqa_api.inbox_triage.request_more_assistant.flags import (
    office_allowed,
    resolve_pilot_office_id,
)
from services.fiqa_api.routes import inbox_triage as routes
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

CASE_ID = "case_edit_signal"
PILOT_OFFICE = "chen_kui"

VIN_ONLY_FACTS = {
    "vehicle_year": "2019",
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry",
    "policy_number": "QA-SYNTH-POLICY",
    "accident_description": "停车场倒车轻微剐蹭（合成测试数据）",
    "accident_datetime": "2026-08-01 下午",
    "accident_location": "QA 测试停车场",
    "injury_status": "no",
}

AI_VIN_DRAFT = {
    "draft_text": "您好，麻烦补充一下车辆的 VIN 车架号，方便我们继续处理。谢谢！",
    "items": [
        {
            "field_key": "vin",
            "label": "车架号 VIN",
            "instructions": "在挡风玻璃左下角或车门内侧标签上可以找到。",
        }
    ],
    "_provider": "openai",
    "_model": "gpt-4o-mini",
}

AI_VIN_DRAFT_V2 = {
    "draft_text": "您好，还差一个 VIN 车架号，麻烦您拍一张给我们，谢谢！",
    "items": [
        {
            "field_key": "vin",
            "label": "车架号 VIN（第二版）",
            "instructions": "挡风玻璃左下角即可看到。",
        }
    ],
    "_provider": "openai",
    "_model": "gpt-4o-mini",
}

AI_TWO_ITEM_DRAFT = {
    "draft_text": "您好，还需要 VIN 车架号和保险卡照片，麻烦补充一下，谢谢！",
    "items": [
        {
            "field_key": "vin",
            "label": "车架号 VIN",
            "instructions": "挡风玻璃左下角。",
        },
        {
            "field_key": "policy_or_insurance_card",
            "label": "保险卡",
            "instructions": "拍一张保险卡正面照片。",
        },
    ],
    "_provider": "openai",
    "_model": "gpt-4o-mini",
}


def _case(**overrides) -> dict:
    row = {
        "case_id": CASE_ID,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "client_id": PILOT_OFFICE,
        "workbench_test": True,
        "known_facts": dict(VIN_ONLY_FACTS),
    }
    row.update(overrides)
    return row


class Harness:
    """Broker Workbench against in-memory intake + send stores."""

    def __init__(self, monkeypatch, *, case: dict | None = None):
        for name in (
            "REQUEST_MORE_ASSISTANT_ENABLED",
            "REQUEST_MORE_ASSISTANT_LLM",
            "REQUEST_MORE_ASSISTANT_OFFICE_ALLOWLIST",
        ):
            monkeypatch.delenv(name, raising=False)
        self.case = case or _case()
        # Ownership fields the created aggregate would otherwise blank out.
        self._office_stamp = {
            key: self.case[key]
            for key in ("asserted_org_id", "client_id")
            if self.case.get(key)
        }
        self.intake_store = InMemoryIntakeStore(cases={CASE_ID: self.case})
        self.intake = P20CaseIntakeCommandService(self.intake_store)
        self.send_store = InMemorySendRequestStore(
            cases=self.intake_store.cases,
            intake_aggregates=self.intake_store.aggregates,
            drafts=self.intake_store.drafts,
        )
        self.send = P20SendRequestCommandService(self.send_store)

        app = FastAPI()
        app.include_router(routes.router)
        monkeypatch.setattr(routes, "default_case_intake_service", lambda: self.intake)
        monkeypatch.setattr(routes, "default_send_request_service", lambda: self.send)
        monkeypatch.setattr(
            routes, "get_case_for_read", lambda cid: self.case if cid == CASE_ID else None
        )
        monkeypatch.setattr(routes, "assert_case_office_access_allowed", lambda *_a, **_k: None)
        monkeypatch.setattr(routes, "assert_case_client_access_allowed", lambda *_a, **_k: None)
        monkeypatch.setattr(routes, "assert_support_export_authorized", lambda *_a, **_k: None)
        monkeypatch.setattr(routes, "client_asserted_office_id", lambda _req: None)
        monkeypatch.setattr(routes, "resolve_server_client_id", lambda: PILOT_OFFICE)
        self.client = TestClient(app)
        self._seq = 0

        created = self.intake.create_claim(
            broker_id=f"client:{PILOT_OFFICE}",
            office_id=None,
            tenant_id=PILOT_OFFICE,
            command_id="cmd_create_edit_signal",
            idempotency_key="idem_create_edit_signal",
            inputs={"is_test": True, "known_facts": dict(VIN_ONLY_FACTS)},
        )
        self._rekey(created["case_id"])

    def _rekey(self, real_case_id: str) -> None:
        """Give the created aggregate the fixed case id the route reads."""
        if real_case_id == CASE_ID:
            return
        row = self.intake_store.cases.pop(real_case_id)
        row["case_id"] = CASE_ID
        row.update(self._office_stamp)
        self.intake_store.cases[CASE_ID] = row
        self.case.update(row)
        aggregate = self.intake_store.aggregates.pop(real_case_id)
        aggregate.case_id = CASE_ID
        self.intake_store.aggregates[CASE_ID] = aggregate
        self.send_store.cases = self.intake_store.cases
        self.send_store.intake_aggregates = self.intake_store.aggregates
        self.send_store.drafts = self.intake_store.drafts

    def ids(self, prefix: str) -> dict[str, str]:
        self._seq += 1
        return {
            "command_id": f"cmd_{prefix}_{self._seq:04d}",
            "idempotency_key": f"idem_{prefix}_{self._seq:04d}",
        }

    @property
    def version(self) -> int:
        return int(self.intake.fetch_projection(CASE_ID)["aggregate_version"])

    def confirm(self, *field_keys: str) -> None:
        for field_key in field_keys:
            self.intake.update_fact_status(
                case_id=CASE_ID,
                broker_id=f"client:{PILOT_OFFICE}",
                expected_case_version=self.version,
                field_key=field_key,
                status="confirmed",
                reason="QA synthetic broker confirmation",
                **self.ids("fact"),
            )

    def missing_keys(self) -> list[str]:
        checklist = self.intake.fetch_projection(CASE_ID)["missing_information_checklist"]
        return [row["field_key"] for row in checklist if row.get("suggested_for_request")]

    def assist(self, *, prefer_template: bool = False) -> dict:
        response = self.client.post(
            f"/api/inbox/cases/{CASE_ID}/request-draft-assist",
            json={"prefer_template": prefer_template},
        )
        assert response.status_code == 200, response.text
        return response.json()

    def save(self, items: list[dict], *, receipt: dict | None = None, **ids) -> dict:
        payload = {
            **(ids or self.ids("save")),
            "expected_case_version": self.version,
            "items": items,
        }
        if receipt is not None:
            payload["ai_draft"] = receipt
        response = self.client.post(f"/api/inbox/cases/{CASE_ID}/request-draft", json=payload)
        assert response.status_code in (200, 201), response.text
        return response.json()

    def send_request(self, draft_id: str, **ids) -> dict:
        response = self.client.post(
            f"/api/inbox/cases/{CASE_ID}/send-request",
            json={
                **(ids or self.ids("send")),
                "expected_case_version": self.version,
                "request_draft_id": draft_id,
            },
        )
        assert response.status_code in (200, 201), response.text
        return response.json()

    def stored_signal(self) -> dict:
        response = self.client.get(f"/api/inbox/support/request-more-ai-signal/{CASE_ID}")
        assert response.status_code == 200, response.text
        return response.json()


def _draft_items_from_assist(assist: dict, *, mutate=None) -> list[dict]:
    """Exactly what the Workbench sends back for the drafted items."""
    items = []
    for index, item in enumerate(assist["items"], start=1):
        row = {
            "field_key": item["field_key"],
            "item_type": item["item_type"],
            "label": item["label"],
            "instructions": item.get("instructions", ""),
            "required": True,
            "position": index,
            "request_mode": item.get("request_mode") or "request_missing",
            "selected": True,
        }
        items.append(mutate(row) if mutate else row)
    return items


def _vin_only(harness: Harness) -> None:
    harness.confirm(
        "vehicle_information",
        "policy_or_insurance_card",
        "accident_description",
        "accident_datetime",
        "accident_location",
        "injury_status",
    )
    assert harness.missing_keys() == ["vin"]


def _enable_real_llm(monkeypatch, payload=AI_VIN_DRAFT) -> None:
    monkeypatch.setenv("REQUEST_MORE_ASSISTANT_ENABLED", "1")
    monkeypatch.setenv("REQUEST_MORE_ASSISTANT_LLM", "1")
    monkeypatch.setenv("REQUEST_MORE_ASSISTANT_OFFICE_ALLOWLIST", PILOT_OFFICE)
    monkeypatch.setattr(assist_service, "_call_openai", lambda _ctx: copy.deepcopy(payload))


# --------------------------------------------------------------------------
# Normalization / signature rules
# --------------------------------------------------------------------------


def test_normalization_folds_whitespace_and_width_but_not_wording():
    assert normalize_customer_text("  车架号   VIN \n 谢谢 ") == "车架号 VIN 谢谢"
    assert normalize_customer_text("车架号\u3000VIN") == normalize_customer_text("车架号 VIN")
    assert normalize_customer_text("车架号\u200bVIN") == "车架号VIN"
    assert normalize_customer_text("请补充VIN") != normalize_customer_text("请补充车架号")


def test_signature_ignores_item_order_but_tracks_wording():
    a = [
        {"field_key": "vin", "label": "VIN", "instructions": "挡风玻璃左下角"},
        {"field_key": "policy_or_insurance_card", "label": "保险卡", "instructions": "正面照片"},
    ]
    reordered = list(reversed(a))
    assert customer_facing_signature(a) == customer_facing_signature(reordered)

    reworded = copy.deepcopy(a)
    reworded[0]["instructions"] = "车门内侧标签"
    assert customer_facing_signature(a) != customer_facing_signature(reworded)


def test_provenance_rejects_anything_the_server_did_not_issue():
    assert normalize_ai_provenance(None) is None
    assert normalize_ai_provenance({"draft_signature": "not-a-digest"}) is None
    cleaned = normalize_ai_provenance(
        {
            "draft_signature": "a" * 64,
            "ai_used": True,
            "missing_item_count": 10**9,
            "note": "客户张先生的电话 555-0100",
        }
    )
    assert cleaned is not None
    assert "note" not in cleaned
    assert cleaned["missing_item_count"] == 999


# --------------------------------------------------------------------------
# Pilot office resolution
# --------------------------------------------------------------------------


def test_pilot_office_prefers_persisted_case_ownership():
    assert resolve_pilot_office_id({"asserted_org_id": "office_a", "client_id": "office_b"}) == "office_a"
    assert resolve_pilot_office_id({"client_id": "chen_kui"}) == "chen_kui"
    assert resolve_pilot_office_id({}, "office_header") == "office_header"


def test_pilot_office_falls_back_to_deployment_client_pack(monkeypatch):
    monkeypatch.delenv("CLIENT_ID", raising=False)
    assert resolve_pilot_office_id({}) == PILOT_OFFICE


def test_office_allowlist_admits_only_the_approved_office(monkeypatch):
    monkeypatch.setenv("REQUEST_MORE_ASSISTANT_OFFICE_ALLOWLIST", PILOT_OFFICE)
    assert office_allowed(PILOT_OFFICE) is True
    assert office_allowed("some_other_office") is False
    assert office_allowed(None) is False


# --------------------------------------------------------------------------
# 1 / 3 — send unchanged, and whitespace-only differences
# --------------------------------------------------------------------------


def test_ai_draft_sent_unchanged_is_not_an_edit(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist()
    assert assist["draft_used_ai"] is True
    assert assist["used_fallback"] is False
    receipt = assist["ai_draft_receipt"]

    saved = harness.save(_draft_items_from_assist(assist), receipt=receipt)
    draft_id = saved["broker_projection"]["request_draft"]["draft_id"]
    sent = harness.send_request(draft_id)

    signal = sent["ai_request_more"]
    assert signal["ai_used"] is True
    assert signal["used_fallback"] is False
    assert signal["draft_edited_before_send"] is False
    assert signal["signal_reason"] == "compared"
    assert signal["model_provider"] == "openai"
    assert signal["model_name"] == "gpt-4o-mini"
    assert signal["missing_item_count"] == 1
    assert signal["request_id"]


def test_whitespace_only_change_is_not_an_edit(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist()
    items = _draft_items_from_assist(
        assist,
        mutate=lambda row: {
            **row,
            "label": f"  {row['label']}  ",
            "instructions": row["instructions"].replace("。", "。 ") + "\n",
        },
    )
    saved = harness.save(items, receipt=assist["ai_draft_receipt"])
    sent = harness.send_request(saved["broker_projection"]["request_draft"]["draft_id"])

    assert sent["ai_request_more"]["draft_edited_before_send"] is False


# --------------------------------------------------------------------------
# 2 — broker rewrites the wording
# --------------------------------------------------------------------------


def test_broker_rewording_is_recorded_as_an_edit(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist()
    items = _draft_items_from_assist(
        assist,
        mutate=lambda row: {**row, "instructions": "陈总办公室已核对，请拍一张车架号照片。"},
    )
    saved = harness.save(items, receipt=assist["ai_draft_receipt"])
    sent = harness.send_request(saved["broker_projection"]["request_draft"]["draft_id"])

    signal = sent["ai_request_more"]
    assert signal["ai_used"] is True
    assert signal["draft_edited_before_send"] is True
    assert signal["signal_reason"] == "compared"


def test_edit_is_still_measured_when_the_client_omits_the_receipt(monkeypatch):
    """A broker who hand-edits after drafting does not re-send the receipt."""
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist()
    harness.save(_draft_items_from_assist(assist), receipt=assist["ai_draft_receipt"])
    edited = harness.save(
        _draft_items_from_assist(assist, mutate=lambda row: {**row, "label": "车架号（手工改）"})
    )
    sent = harness.send_request(edited["broker_projection"]["request_draft"]["draft_id"])

    assert sent["ai_request_more"]["ai_used"] is True
    assert sent["ai_request_more"]["draft_edited_before_send"] is True


# --------------------------------------------------------------------------
# 4 — regenerated draft is compared against the latest draft
# --------------------------------------------------------------------------


def test_regenerated_draft_is_compared_against_the_latest_version(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    first = harness.assist()
    harness.save(_draft_items_from_assist(first), receipt=first["ai_draft_receipt"])

    monkeypatch.setattr(assist_service, "_call_openai", lambda _ctx: copy.deepcopy(AI_VIN_DRAFT_V2))
    second = harness.assist()
    assert second["ai_draft_receipt"]["draft_signature"] != first["ai_draft_receipt"]["draft_signature"]

    saved = harness.save(_draft_items_from_assist(second), receipt=second["ai_draft_receipt"])
    sent = harness.send_request(saved["broker_projection"]["request_draft"]["draft_id"])

    signal = sent["ai_request_more"]
    assert signal["draft_edited_before_send"] is False
    assert signal["assist_id"] == second["ai_draft_receipt"]["assist_id"]


# --------------------------------------------------------------------------
# 5 / 6 / 12 — template, fallback, and a non-allowlisted office
# --------------------------------------------------------------------------


def test_broker_chosen_template_does_not_claim_ai_adoption(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist(prefer_template=True)
    assert assist["authority"] == "office_template"
    assert assist["draft_used_ai"] is False
    assert assist["used_fallback"] is False

    saved = harness.save(_draft_items_from_assist(assist), receipt=assist["ai_draft_receipt"])
    sent = harness.send_request(saved["broker_projection"]["request_draft"]["draft_id"])

    signal = sent["ai_request_more"]
    assert signal["ai_used"] is False
    assert signal["used_fallback"] is False
    assert signal["draft_edited_before_send"] is None
    assert signal["signal_reason"] == "ai_not_adopted"
    # The comparison still happened; it is just not an AI adoption claim.
    assert signal["sent_matches_assist_draft"] is True


def test_fallback_template_is_not_reported_as_a_successful_ai_draft(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    def _boom(_ctx):
        raise TimeoutError("provider_timeout")

    monkeypatch.setattr(assist_service, "_call_openai", _boom)
    assist = harness.assist()
    assert assist["used_fallback"] is True
    assert assist["fallback_reason"] == "timeout"

    saved = harness.save(_draft_items_from_assist(assist), receipt=assist["ai_draft_receipt"])
    sent = harness.send_request(saved["broker_projection"]["request_draft"]["draft_id"])

    signal = sent["ai_request_more"]
    assert signal["ai_used"] is False
    assert signal["used_fallback"] is True
    assert signal["fallback_reason"] == "timeout"
    assert signal["draft_edited_before_send"] is None


def test_office_outside_the_allowlist_gets_the_deterministic_template(monkeypatch):
    harness = Harness(monkeypatch, case=_case(asserted_org_id="office_not_in_pilot"))
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist()
    assert assist["draft_used_ai"] is False
    assert assist["authority"] == "office_template"
    assert assist["fallback_reason"] == "assistant_disabled"
    assert assist["ai_draft_receipt"]["ai_used"] is False


def test_hand_built_draft_reports_no_receipt(monkeypatch):
    harness = Harness(monkeypatch)
    _vin_only(harness)

    saved = harness.save(
        [
            {
                "field_key": "vin",
                "item_type": "vin",
                "label": "车架号",
                "instructions": "请提供车架号",
                "required": True,
                "position": 1,
                "selected": True,
            }
        ]
    )
    sent = harness.send_request(saved["broker_projection"]["request_draft"]["draft_id"])

    signal = sent["ai_request_more"]
    assert signal["ai_used"] is False
    assert signal["draft_edited_before_send"] is None
    assert signal["signal_reason"] == "no_ai_draft_receipt"


# --------------------------------------------------------------------------
# 7 — multiple missing items
# --------------------------------------------------------------------------


def test_comparison_stays_stable_across_multiple_missing_items(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch, AI_TWO_ITEM_DRAFT)
    harness.confirm(
        "vehicle_information",
        "accident_description",
        "accident_datetime",
        "accident_location",
        "injury_status",
    )
    assert harness.missing_keys() == ["vin", "policy_or_insurance_card"]

    assist = harness.assist()
    assert assist["missing_item_count"] == 2
    assert assist["draft_used_ai"] is True

    # Reversed order, same wording — reordering is not a wording edit.
    items = list(reversed(_draft_items_from_assist(assist)))
    for position, row in enumerate(items, start=1):
        row["position"] = position
    saved = harness.save(items, receipt=assist["ai_draft_receipt"])
    sent = harness.send_request(saved["broker_projection"]["request_draft"]["draft_id"])

    signal = sent["ai_request_more"]
    assert signal["draft_edited_before_send"] is False
    assert signal["missing_item_count"] == 2
    assert signal["sent_item_count"] == 2


# --------------------------------------------------------------------------
# 8 / 9 — retry, replay, idempotency
# --------------------------------------------------------------------------


def test_double_send_records_the_signal_exactly_once(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist()
    saved = harness.save(_draft_items_from_assist(assist), receipt=assist["ai_draft_receipt"])
    draft_id = saved["broker_projection"]["request_draft"]["draft_id"]

    ids = harness.ids("send_retry")
    first = harness.send_request(draft_id, **ids)
    assert first["outcome"] == "accepted"
    request_id = first["slice1_projection"]["open_request"]["request_id"]

    retry = harness.client.post(
        f"/api/inbox/cases/{CASE_ID}/send-request",
        json={**ids, "expected_case_version": first["aggregate_version"] - 1, "request_draft_id": draft_id},
    )
    assert retry.status_code == 200
    assert retry.json()["outcome"] == "replayed"
    assert retry.json()["slice1_projection"]["open_request"]["request_id"] == request_id

    stored = harness.stored_signal()
    assert len(stored["send_signals"]) == 1
    assert stored["summary"]["sends_recorded"] == 1
    assert stored["summary"]["ai_drafts_sent"] == 1


def test_second_send_of_an_open_request_is_still_rejected(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist()
    saved = harness.save(_draft_items_from_assist(assist), receipt=assist["ai_draft_receipt"])
    draft_id = saved["broker_projection"]["request_draft"]["draft_id"]
    harness.send_request(draft_id)

    duplicate = harness.client.post(
        f"/api/inbox/cases/{CASE_ID}/send-request",
        json={
            **harness.ids("send_dup"),
            "expected_case_version": harness.version,
            "request_draft_id": draft_id,
        },
    )
    assert duplicate.status_code == 422
    assert duplicate.json()["detail"]["error_code"] in {
        "open_request_exists",
        "customer_access_exists",
    }


# --------------------------------------------------------------------------
# 10 / 11 — read-only assist, no draft text in logs
# --------------------------------------------------------------------------


def test_draft_assist_stays_read_only(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    before_version = harness.version
    before_cases = copy.deepcopy(harness.intake_store.cases)

    assist = harness.assist()

    assert assist["lifecycle_mutated"] is False
    assert harness.version == before_version
    assert harness.intake_store.cases == before_cases
    assert harness.intake_store.drafts == {}
    assert harness.send_store.groups == {}
    assert harness.send_store.access_by_case == {}


def test_telemetry_logs_carry_digests_not_customer_wording(monkeypatch, caplog):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist()
    saved = harness.save(_draft_items_from_assist(assist), receipt=assist["ai_draft_receipt"])

    with caplog.at_level(logging.INFO):
        harness.send_request(saved["broker_projection"]["request_draft"]["draft_id"])

    lines = [r.getMessage() for r in caplog.records if "request_more_ai_send_signal" in r.getMessage()]
    assert len(lines) == 1
    payload = json.loads(lines[0].split(" ", 1)[1])
    assert payload["ai_used"] is True
    assert payload["draft_edited_before_send"] is False
    blob = lines[0]
    for secret in (
        assist["draft_text"],
        assist["items"][0]["label"],
        assist["items"][0]["instructions"],
    ):
        assert secret not in blob
    # The digest itself must not travel in the log line either.
    assert assist["ai_draft_receipt"]["draft_signature"] not in blob


def test_stored_signal_never_contains_draft_text(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist()
    saved = harness.save(_draft_items_from_assist(assist), receipt=assist["ai_draft_receipt"])
    harness.send_request(saved["broker_projection"]["request_draft"]["draft_id"])

    stored = harness.stored_signal()
    blob = json.dumps(stored, ensure_ascii=False)
    assert assist["draft_text"] not in blob
    assert assist["items"][0]["instructions"] not in blob
    assert stored["draft_provenance"]["ai_used"] is True
    assert stored["pilot_office_id"] == PILOT_OFFICE


# --------------------------------------------------------------------------
# Durable read-back + summary
# --------------------------------------------------------------------------


def test_stored_signal_answers_every_pilot_question(monkeypatch):
    harness = Harness(monkeypatch)
    _enable_real_llm(monkeypatch)
    _vin_only(harness)

    assist = harness.assist()
    saved = harness.save(_draft_items_from_assist(assist), receipt=assist["ai_draft_receipt"])
    sent = harness.send_request(saved["broker_projection"]["request_draft"]["draft_id"])
    request_id = sent["slice1_projection"]["open_request"]["request_id"]

    stored = harness.stored_signal()
    row = stored["send_signals"][0]
    assert row["ai_used"] is True
    assert row["used_fallback"] is False
    assert row["draft_edited_before_send"] is False
    assert row["missing_item_count"] == 1
    assert row["request_id"] == request_id
    assert row["command_id"]
    assert row["source_draft_id"] == saved["broker_projection"]["request_draft"]["draft_id"]
    assert stored["summary"]["broker_edit_rate"] == 0.0


def test_signal_extraction_deduplicates_the_two_send_events():
    events = [
        {"event_id": "e1", "event_type": "broker_request_more_created",
         "evidence": {"ai_request_more": {"request_id": "req_1", "ai_used": True}}},
        {"event_id": "e2", "event_type": "request_sent",
         "evidence": {"ai_request_more": {"request_id": "req_1", "ai_used": True}}},
        {"event_id": "e3", "event_type": "request_draft_saved", "evidence": {}},
    ]
    signals = extract_stored_send_signals(events)
    assert len(signals) == 1
    assert signals[0]["event_type"] == "broker_request_more_created"


def test_summary_counts_only_ai_sends():
    signals = [
        {"ai_used": True, "draft_edited_before_send": False},
        {"ai_used": True, "draft_edited_before_send": True},
        {"ai_used": True, "draft_edited_before_send": True},
        {"ai_used": False, "used_fallback": True, "draft_edited_before_send": None},
        {"ai_used": False, "draft_edited_before_send": None},
    ]
    summary = summarize_send_signals(signals)
    assert summary["sends_recorded"] == 5
    assert summary["ai_drafts_sent"] == 3
    assert summary["sent_unchanged"] == 1
    assert summary["sent_edited"] == 2
    assert summary["fallback_sends"] == 1
    assert summary["non_ai_sends"] == 2
    assert summary["broker_edit_rate"] == round(2 / 3, 4)


def test_summary_reports_no_rate_without_ai_sends():
    assert summarize_send_signals([])["broker_edit_rate"] is None


def test_evaluate_send_signal_is_pure():
    provenance = {
        "draft_signature": customer_facing_signature([{"field_key": "vin", "label": "VIN", "instructions": "x"}]),
        "ai_used": True,
        "used_fallback": False,
        "missing_item_count": 1,
    }
    items = [{"field_key": "vin", "label": "VIN", "instructions": "x"}]
    snapshot = copy.deepcopy((provenance, items))
    evaluate_send_signal(provenance=provenance, sent_items=items)
    assert (provenance, items) == snapshot
