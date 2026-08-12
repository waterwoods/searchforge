"""AI Request More drafting V1 — deterministic gaps, AI wording, broker confirm.

The deterministic Cap2 checklist owns *what* is missing; the model may only
rephrase it. Every test below protects one of those two boundaries.
"""

from __future__ import annotations

import copy
import json

import pytest

from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_missing_information import (
    FACT_STATUS_CONFIRMED,
    derive_missing_information_checklist,
)
from services.fiqa_api.inbox_triage.policy_context_confirm import (
    CHOICE_CORRECT,
    FACT_VALUE_CONFIRMED,
    SOURCE_CUSTOMER_CONFIRMED,
)
from services.fiqa_api.inbox_triage.request_more_assistant.contract import (
    AUTHORITY_AI_DRAFT,
    AUTHORITY_TEMPLATE,
    NOTHING_MISSING_ZH,
    derive_request_more_missing_items,
)
from services.fiqa_api.inbox_triage.request_more_assistant.guardrails import (
    OUTCOME_EXTRA_ITEM,
    OUTCOME_FORBIDDEN_LANGUAGE,
    OUTCOME_MISSING_ITEM,
    OUTCOME_UNSUPPORTED_DETAIL,
)
from services.fiqa_api.inbox_triage.request_more_assistant.service import (
    ERROR_ACTIVE_REQUEST_MORE,
    draft_request_more,
)


@pytest.fixture(autouse=True)
def _hermetic_assistant_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flag posture is per-test, never inherited from the operator's shell."""
    for name in (
        "REQUEST_MORE_ASSISTANT_ENABLED",
        "REQUEST_MORE_ASSISTANT_LLM",
        "REQUEST_MORE_ASSISTANT_OFFICE_ALLOWLIST",
        "REQUEST_MORE_ASSISTANT_DETERMINISTIC_FALLBACK",
        "REQUEST_MORE_ASSISTANT_MODEL",
        "REQUEST_MORE_ASSISTANT_TIMEOUT_SECONDS",
        "REQUEST_MORE_ASSISTANT_MAX_RETRIES",
    ):
        monkeypatch.delenv(name, raising=False)


def _confirmed(value: str, *, source: str = "broker_command") -> dict[str, object]:
    return {"status": FACT_STATUS_CONFIRMED, "value": value, "source": source}


def _known_customer_case(*, with_vin: bool = False) -> dict[str, object]:
    """Existing customer: confirmed vehicle, policy context, accident story."""
    known_facts: dict[str, object] = {
        "vehicle_year": "2019",
        "vehicle_make": "Toyota",
        "vehicle_model": "Camry",
        "accident_description": "在停车场倒车时与另一辆车轻微剐蹭",
        "accident_datetime": "2026-08-01 下午三点",
        "accident_location": "洛杉矶某超市停车场",
        "injury_status": "no",
    }
    if with_vin:
        known_facts["vin"] = "4T1BF1FK5CU511111"
    return {
        "case_id": "case_known_customer",
        "known_facts": known_facts,
        # Customer confirmed the existing policy context — no card upload needed.
        "policy_context": {"status": "confirmed", "customer_choice": CHOICE_CORRECT},
    }


def _known_customer_fact_records(*, vin_confirmed: bool = False) -> dict[str, object]:
    records: dict[str, object] = {
        "vehicle_information": _confirmed("2019 Toyota Camry"),
        "policy_or_insurance_card": _confirmed(
            FACT_VALUE_CONFIRMED, source=SOURCE_CUSTOMER_CONFIRMED
        ),
        "accident_description": _confirmed("在停车场倒车时与另一辆车轻微剐蹭"),
        "accident_datetime": _confirmed("2026-08-01 下午三点"),
        "accident_location": _confirmed("洛杉矶某超市停车场"),
        "injury_status": _confirmed("no"),
    }
    if vin_confirmed:
        records["vin"] = _confirmed("4T1BF1FK5CU511111")
    return records


def _checklist_for(case: dict[str, object], facts: dict[str, object]) -> list[dict[str, object]]:
    return derive_missing_information_checklist(facts, case=case)


def _good_caller(context: dict[str, object]) -> dict[str, object]:
    items = list(context["items"])  # type: ignore[index]
    lines = "\n".join(
        f"{index}. {item['customer_label']}" for index, item in enumerate(items, start=1)
    )
    return {
        "draft_text": f"您好，为了继续处理您的案件，目前还需要：\n{lines}\n请方便时在这里补充上传，谢谢。",
        "items": [
            {
                "field_key": item["field_key"],
                "label": item["customer_label"],
                "instructions": "请方便时补充这一项，谢谢。",
            }
            for item in items
        ],
        "_provider": "test",
        "_model": "stub-v1",
    }


# 1 / 8 — golden regression: existing customer, only VIN missing.


def test_golden_existing_customer_only_vin_missing_asks_vin_only():
    case = _known_customer_case()
    facts = _known_customer_fact_records()
    checklist = _checklist_for(case, facts)

    missing = derive_request_more_missing_items(checklist)
    assert [item["field_key"] for item in missing] == ["vin"]

    result = draft_request_more(case=case, checklist=checklist, llm_caller=_good_caller)

    assert result["ok"] is True
    assert result["drafting_available"] is True
    assert result["missing_item_count"] == 1
    assert [item["field_key"] for item in result["items"]] == ["vin"]
    assert result["authority"] == AUTHORITY_AI_DRAFT
    assert result["draft_used_ai"] is True
    assert result["used_fallback"] is False
    assert "VIN" in result["draft_text"]
    for already_authoritative in ("保险卡", "保单", "事故时间", "事故地点", "受伤", "车型"):
        assert already_authoritative not in result["draft_text"]


def test_confirmed_facts_never_enter_the_missing_set():
    case = _known_customer_case(with_vin=True)
    facts = _known_customer_fact_records(vin_confirmed=True)
    checklist = _checklist_for(case, facts)
    assert derive_request_more_missing_items(checklist) == []


# 2 — VIN + insurance card missing.


def test_vin_and_insurance_card_missing_requests_both_without_extras():
    case = {
        "case_id": "case_two_gaps",
        "known_facts": {
            "vehicle_make": "Toyota",
            "vehicle_model": "Camry",
            "accident_description": "追尾",
            "accident_datetime": "2026-08-01",
            "accident_location": "405 高速",
            "injury_status": "no",
        },
    }
    facts = {
        "vehicle_information": _confirmed("2019 Toyota Camry"),
        "accident_description": _confirmed("追尾"),
    }
    checklist = _checklist_for(case, facts)

    result = draft_request_more(case=case, checklist=checklist, llm_caller=_good_caller)

    assert [item["field_key"] for item in result["items"]] == [
        "vin",
        "policy_or_insurance_card",
    ]
    assert result["used_fallback"] is False
    assert "VIN" in result["draft_text"]
    assert "保险卡" in result["draft_text"]


# 3 — nothing missing.


def test_no_missing_items_disables_drafting_and_creates_nothing():
    case = _known_customer_case(with_vin=True)
    facts = _known_customer_fact_records(vin_confirmed=True)

    result = draft_request_more(
        case=case, checklist=_checklist_for(case, facts), llm_caller=_good_caller
    )

    assert result["ok"] is True
    assert result["drafting_available"] is False
    assert result["missing_item_count"] == 0
    assert result["items"] == []
    assert result["message"] == NOTHING_MISSING_ZH
    assert result["lifecycle_mutated"] is False


# 4 / 5 / 6 / 7 / 8 — guardrails and failure fallback.


def _single_gap_setup() -> tuple[dict[str, object], list[dict[str, object]]]:
    case = _known_customer_case()
    checklist = _checklist_for(case, _known_customer_fact_records())
    return case, checklist


def test_ai_invented_item_is_rejected_and_falls_back_to_template():
    case, checklist = _single_gap_setup()

    def caller(_context: dict[str, object]) -> dict[str, object]:
        return {
            "draft_text": "您好，还需要 VIN 和驾照照片。",
            "items": [
                {"field_key": "vin", "label": "车辆 VIN", "instructions": ""},
                {"field_key": "drivers_license", "label": "驾照照片", "instructions": ""},
            ],
        }

    result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)

    assert result["used_fallback"] is True
    assert result["guardrail_outcome"] == OUTCOME_EXTRA_ITEM
    assert result["authority"] == AUTHORITY_TEMPLATE
    assert [item["field_key"] for item in result["items"]] == ["vin"]
    assert "驾照" not in result["draft_text"]


def test_ai_dropping_a_required_item_falls_back_to_template():
    case = {
        "case_id": "case_two_gaps",
        "known_facts": {"vehicle_make": "Toyota", "vehicle_model": "Camry"},
    }
    checklist = _checklist_for(case, {"vehicle_information": _confirmed("2019 Toyota Camry")})

    def caller(_context: dict[str, object]) -> dict[str, object]:
        return {
            "draft_text": "您好，目前还需要车辆 VIN。",
            "items": [{"field_key": "vin", "label": "车辆 VIN", "instructions": ""}],
        }

    result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)

    assert result["used_fallback"] is True
    assert result["guardrail_outcome"] == OUTCOME_MISSING_ITEM
    assert [item["field_key"] for item in result["items"]] == [
        "vin",
        "policy_or_insurance_card",
    ]
    assert "保险卡" in result["draft_text"]


def test_llm_timeout_falls_back_to_deterministic_template():
    case, checklist = _single_gap_setup()

    def caller(_context: dict[str, object]) -> dict[str, object]:
        raise TimeoutError("provider_timeout")

    result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)

    assert result["ok"] is True
    assert result["used_fallback"] is True
    assert result["fallback_reason"] == "timeout"
    assert result["draft_used_ai"] is False
    assert "VIN" in result["draft_text"]


def test_invalid_model_json_falls_back_to_deterministic_template():
    case, checklist = _single_gap_setup()

    def caller(_context: dict[str, object]) -> dict[str, object]:
        raise ValueError("invalid_model_json")

    result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)
    assert result["fallback_reason"] == "invalid_json"
    assert result["authority"] == AUTHORITY_TEMPLATE


def test_non_dict_model_output_falls_back_to_deterministic_template():
    case, checklist = _single_gap_setup()
    result = draft_request_more(
        case=case, checklist=checklist, llm_caller=lambda _ctx: ["not", "a", "dict"]
    )
    assert result["used_fallback"] is True
    assert result["guardrail_outcome"] == "invalid_shape"


def test_coverage_language_is_blocked():
    case, checklist = _single_gap_setup()

    def caller(_context: dict[str, object]) -> dict[str, object]:
        return {
            "draft_text": "您好，这次事故全责在对方，保险公司会赔，请补充车辆 VIN。",
            "items": [{"field_key": "vin", "label": "车辆 VIN", "instructions": ""}],
        }

    result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)

    assert result["used_fallback"] is True
    assert result["guardrail_outcome"] == OUTCOME_FORBIDDEN_LANGUAGE
    assert "全责" not in result["draft_text"]


def test_unsupported_case_detail_is_blocked():
    case, checklist = _single_gap_setup()

    def caller(_context: dict[str, object]) -> dict[str, object]:
        return {
            "draft_text": "您好，请补充车辆 VIN，保单号 987654321 已确认。",
            "items": [{"field_key": "vin", "label": "车辆 VIN", "instructions": ""}],
        }

    result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)
    assert result["guardrail_outcome"] == OUTCOME_UNSUPPORTED_DETAIL
    assert result["used_fallback"] is True


def test_draft_text_must_still_name_every_required_item():
    case, checklist = _single_gap_setup()

    def caller(_context: dict[str, object]) -> dict[str, object]:
        return {
            "draft_text": "您好，麻烦补充一下资料，谢谢。",
            "items": [{"field_key": "vin", "label": "车辆 VIN", "instructions": ""}],
        }

    result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)
    assert result["guardrail_outcome"] == "item_not_represented_in_text"
    assert result["used_fallback"] is True


def test_intro_only_draft_is_rejected_when_the_list_is_left_out():
    """QA defect: the model wrote a lead-in and left the items to the array."""
    case = {
        "case_id": "case_two_gaps",
        "known_facts": {"vehicle_make": "Toyota", "vehicle_model": "Camry"},
    }
    checklist = _checklist_for(case, {"vehicle_information": _confirmed("2019 Toyota Camry")})

    def caller(context: dict[str, object]) -> dict[str, object]:
        return {
            "draft_text": "尊敬的客户，为了完成您的索赔申请，请您提供以下缺失的信息：",
            "items": [
                {"field_key": item["field_key"], "label": item["customer_label"], "instructions": ""}
                for item in context["items"]  # type: ignore[index]
            ],
        }

    result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)
    assert result["used_fallback"] is True
    assert result["guardrail_outcome"] == "item_not_represented_in_text"
    # The broker still gets a complete, sendable message.
    assert "VIN" in result["draft_text"]
    assert "保险卡" in result["draft_text"]


def test_observability_line_carries_bounded_metadata_and_no_customer_text(caplog):
    case, checklist = _single_gap_setup()
    secret_text = "您好，为了继续处理您的案件，还需要车辆 VIN，谢谢。"

    def caller(_context: dict[str, object]) -> dict[str, object]:
        return {
            "draft_text": secret_text,
            "items": [{"field_key": "vin", "label": "车辆 VIN", "instructions": "在行驶证上。"}],
        }

    with caplog.at_level("INFO"):
        result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)

    line = next(r.getMessage() for r in caplog.records if "request_more_ai_draft" in r.getMessage())
    payload = json.loads(line.split("request_more_ai_draft ", 1)[1])
    assert payload["draft_used_ai"] is True
    assert payload["used_fallback"] is False
    assert payload["guardrail_outcome"] == "passed"
    assert payload["missing_item_count"] == 1
    assert isinstance(payload["latency_ms"], int)
    # Operators can debug without reading customer content.
    assert secret_text not in line
    assert result["case_id"] not in line


def test_blank_ai_instructions_keep_the_office_how_to_find_it_hint():
    case, checklist = _single_gap_setup()

    def caller(_context: dict[str, object]) -> dict[str, object]:
        return {
            "draft_text": "您好，为了继续处理您的案件，还需要车辆 VIN，谢谢。",
            "items": [{"field_key": "vin", "label": "车辆 VIN", "instructions": "  "}],
        }

    result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)
    assert result["draft_used_ai"] is True
    assert result["used_fallback"] is False
    assert "17" in result["items"][0]["instructions"]


def test_ai_instructions_are_kept_when_the_model_supplies_them():
    case, checklist = _single_gap_setup()

    def caller(_context: dict[str, object]) -> dict[str, object]:
        return {
            "draft_text": "您好，为了继续处理您的案件，还需要车辆 VIN，谢谢。",
            "items": [
                {"field_key": "vin", "label": "车辆 VIN", "instructions": "在行驶证上可以找到。"}
            ],
        }

    result = draft_request_more(case=case, checklist=checklist, llm_caller=caller)
    assert result["items"][0]["instructions"] == "在行驶证上可以找到。"


def test_model_receives_the_office_template_as_the_baseline_to_improve():
    """Without a baseline shape the model invents its own and drops the list."""
    case = {
        "case_id": "case_two_gaps",
        "known_facts": {"vehicle_make": "Toyota", "vehicle_model": "Camry"},
    }
    checklist = _checklist_for(case, {"vehicle_information": _confirmed("2019 Toyota Camry")})
    captured: dict[str, object] = {}

    def caller(context: dict[str, object]) -> dict[str, object]:
        captured.update(context)
        return _good_caller(context)

    draft_request_more(case=case, checklist=checklist, llm_caller=caller)

    baseline = str(captured.get("office_template_draft") or "")
    assert baseline.startswith("您好")
    assert "车辆 VIN" in baseline
    assert "保险卡照片" in baseline


# 11 — open Request More.


def test_open_request_more_blocks_new_ai_draft():
    case, checklist = _single_gap_setup()
    result = draft_request_more(
        case=case,
        checklist=checklist,
        open_request_more={"request_id": "req_1", "status": "open"},
        llm_caller=_good_caller,
    )
    assert result["ok"] is False
    assert result["error_code"] == ERROR_ACTIVE_REQUEST_MORE
    assert result["drafting_available"] is False
    assert result["lifecycle_mutated"] is False


# 12 — drafting mutates nothing.


def test_ai_drafting_mutates_no_case_truth():
    case, checklist = _single_gap_setup()
    case_before = copy.deepcopy(case)
    checklist_before = copy.deepcopy(checklist)

    draft_request_more(case=case, checklist=checklist, llm_caller=_good_caller)

    assert case == case_before
    assert checklist == checklist_before


# 9 / 10 — broker edit + existing send command remain authoritative.


def test_broker_edited_ai_draft_is_what_the_existing_command_persists():
    store = InMemoryIntakeStore()
    service = P20CaseIntakeCommandService(store)
    created = service.create_claim(
        broker_id="office:demo",
        office_id="demo-office",
        tenant_id="tenant-demo",
        command_id="cmd-create-ai-draft",
        idempotency_key="idem-create-ai-draft",
        inputs={"is_test": True, "customer_name": "QA Customer"},
    )
    case_id = created["case_id"]
    projection = created["broker_projection"]

    ai = draft_request_more(
        case=store.cases[case_id],
        checklist=projection["missing_information_checklist"],
        case_id=case_id,
        llm_caller=_good_caller,
    )
    aggregate_version_after_draft = service.fetch_projection(case_id)["aggregate_version"]
    assert aggregate_version_after_draft == created["aggregate_version"]

    vin_item = next(item for item in ai["items"] if item["field_key"] == "vin")
    broker_edited = {
        "field_key": vin_item["field_key"],
        "item_type": vin_item["item_type"],
        "label": vin_item["label"],
        "instructions": "陈总补充：VIN 在挡风玻璃左下角。",
        "position": 1,
        "required": True,
        "selected": True,
    }
    saved = service.save_request_draft(
        case_id=case_id,
        broker_id="office:demo",
        command_id="cmd-save-ai-draft",
        idempotency_key="idem-save-ai-draft",
        expected_case_version=aggregate_version_after_draft,
        items=[broker_edited],
    )
    assert saved["outcome"] == "accepted"
    persisted = saved["broker_projection"]["request_draft"]["items"]
    assert len(persisted) == 1
    assert persisted[0]["instructions"] == "陈总补充：VIN 在挡风玻璃左下角。"

    replay = service.save_request_draft(
        case_id=case_id,
        broker_id="office:demo",
        command_id="cmd-save-ai-draft",
        idempotency_key="idem-save-ai-draft",
        expected_case_version=aggregate_version_after_draft,
        items=[broker_edited],
    )
    assert replay["outcome"] == "replayed"


# 13 — template path stays available when the assistant is switched off.


def test_assistant_kill_switch_still_returns_office_template(monkeypatch):
    monkeypatch.setenv("REQUEST_MORE_ASSISTANT_ENABLED", "0")
    case, checklist = _single_gap_setup()

    result = draft_request_more(case=case, checklist=checklist)

    assert result["ok"] is True
    assert result["used_fallback"] is True
    assert result["fallback_reason"] == "assistant_disabled"
    assert result["authority"] == AUTHORITY_TEMPLATE
    assert "VIN" in result["draft_text"]


def test_llm_disabled_by_default_returns_office_template():
    case, checklist = _single_gap_setup()
    result = draft_request_more(case=case, checklist=checklist)
    assert result["fallback_reason"] == "llm_disabled"
    assert result["draft_used_ai"] is False
    assert result["items"][0]["field_key"] == "vin"
    assert result["items"][0]["instructions"]


def test_safe_context_excludes_vin_and_pii():
    case = _known_customer_case(with_vin=True)
    case["customer_name"] = "陈先生"
    case["customer_phone"] = "6265551234"
    captured: dict[str, object] = {}

    def caller(context: dict[str, object]) -> dict[str, object]:
        captured.update(context)
        return _good_caller(context)

    facts = _known_customer_fact_records()
    draft_request_more(case=case, checklist=_checklist_for(case, facts), llm_caller=caller)

    blob = str(captured)
    assert "4T1BF1FK5CU511111" not in blob
    assert "6265551234" not in blob
    assert "陈先生" not in blob
    assert captured["vehicle_summary"] == "Toyota Camry"
