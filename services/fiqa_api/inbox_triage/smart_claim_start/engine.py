"""Smart Claim Start engine — P4 Capability 03.

Single responsibility:
  LookupResult + PrefillResult → customer-ready SmartClaimStartPlan.

Rules (Founder principles):
  Never ask twice.
  Never surprise the customer.
  Never expose technical IDs.
  Keep one active claim.
  Customer primarily answers: What happened today?

Does not write CRM, cases, or identity. Consumes Cap 01/02 outputs only.
"""

from __future__ import annotations

from typing import Any

from services.fiqa_api.inbox_triage.claim_prefill.contract import PrefillResult
from services.fiqa_api.inbox_triage.customer_lookup.contract import LookupResult
from services.fiqa_api.inbox_triage.smart_claim_start.contract import (
    MUST_HAVE_ACCIDENT_KEYS,
    ConfirmStep,
    KnownChip,
    QuestionDecision,
    ScreenStep,
    SmartClaimStartPlan,
    StartMode,
    assert_smart_claim_start_plan_complete,
)

_LABEL_ZH: dict[str, str] = {
    "customer_name": "姓名",
    "phone": "电话",
    "driver": "驾驶人",
    "vehicle": "车辆",
    "vin": "车架号后四位",
    "license_plate": "车牌",
    "policy": "保单",
    "policy_number": "保单号",
    "insurance_company": "保险公司",
    "accident_story": "事故经过",
    "accident_time": "事故时间",
    "accident_location": "事故地点",
    "injury": "是否有人受伤",
    "damage": "车辆损伤（可选）",
    "photos": "现场照片（可选）",
    "email": "邮箱",
    "police_report": "警方报告",
    "documents": "证件资料",
}

_CHIP_FIELD_ORDER: tuple[str, ...] = (
    "customer_name",
    "phone",
    "vehicle",
    "license_plate",
    "policy",
    "insurance_company",
    "driver",
)


def _field_map(prefill: PrefillResult) -> dict[str, dict[str, Any]]:
    return {str(f.get("field_key")): dict(f) for f in (prefill.get("fields") or [])}


def _safe_display(value: Any) -> str:
    text = str(value or "").strip()
    # Never surface technical / mock IDs as customer copy.
    if (
        text.startswith("mock_")
        or text.startswith("wx_mock")
        or text.startswith("POL-MOCK")
        or text.startswith("case_mock")
    ):
        return ""
    return text


def _phone_chip_value(raw: Any) -> str:
    text = str(raw or "").strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 4:
        return f"尾号 {digits[-4:]}"
    return _safe_display(text)


def _policy_chip_value(
    prefill_fields: dict[str, dict[str, Any]], *, confirm_policy: bool
) -> str:
    carrier = _safe_display((prefill_fields.get("insurance_company") or {}).get("value"))
    if confirm_policy:
        return f"{carrier} · 可能已过期" if carrier else "请确认保单"
    if carrier:
        return f"{carrier} · 已关联"
    # Prefer never showing raw policy_ref; fall back to generic label.
    return "保单已关联"


def _build_known_chips(
    prefill_fields: dict[str, dict[str, Any]],
    *,
    confirm_vehicle: bool,
    confirm_policy: bool,
) -> list[KnownChip]:
    chips: list[KnownChip] = []
    for key in _CHIP_FIELD_ORDER:
        if key == "insurance_company":
            # Folded into policy chip — never a second technical chip.
            continue
        f = prefill_fields.get(key) or {}
        classification = f.get("classification")
        value = f.get("value")
        include = (
            classification == "AUTO_PREFILL"
            or bool(f.get("needs_confirm"))
            or (key == "vehicle" and confirm_vehicle)
            or (key == "policy" and confirm_policy)
        )
        if not include:
            continue
        if key == "policy":
            display = _policy_chip_value(prefill_fields, confirm_policy=confirm_policy)
        elif key == "vehicle" and confirm_vehicle:
            cands = list(f.get("candidates") or [])
            display = "请选择出险车辆" if cands else "请确认车辆"
        elif key == "phone":
            display = _phone_chip_value(value)
        else:
            display = _safe_display(value)
        if not display:
            continue
        if key == "vehicle" and confirm_vehicle:
            editability: str = "CONFIRM_REQUIRED"
        elif key == "policy" and confirm_policy:
            editability = "CONFIRM_REQUIRED"
        elif classification == "AUTO_PREFILL":
            editability = "EDIT_ON_REQUEST"
        else:
            editability = "CONFIRM_REQUIRED"
        chips.append(
            {
                "field_key": key,
                "label_zh": _LABEL_ZH.get(key, key),
                "value": display,
                "editability": editability,  # type: ignore[typeddict-item]
            }
        )
    return chips


def _question(
    field_key: str,
    visibility: str,
    reason_code: str,
    *,
    blocks_submit: bool,
) -> QuestionDecision:
    return {
        "field_key": field_key,
        "visibility": visibility,  # type: ignore[typeddict-item]
        "label_zh": _LABEL_ZH.get(field_key, field_key),
        "reason_code": reason_code,
        "blocks_submit": blocks_submit,
    }


def _accident_questions(*, include_optional_damage: bool = True) -> list[QuestionDecision]:
    qs: list[QuestionDecision] = [
        _question(k, "VISIBLE_REQUIRED", "accident_fact_must_have", blocks_submit=True)
        for k in MUST_HAVE_ACCIDENT_KEYS
    ]
    if include_optional_damage:
        qs.append(
            _question(
                "damage",
                "COLLAPSED_OPTIONAL",
                "optional_damage_not_enablement",
                blocks_submit=False,
            )
        )
    qs.append(
        _question(
            "photos",
            "COLLAPSED_OPTIONAL",
            "photos_after_or_optional",
            blocks_submit=False,
        )
    )
    for key in ("vin", "documents", "police_report", "email"):
        qs.append(
            _question(key, "BROKER_OWNED", "broker_or_request_more", blocks_submit=False)
        )
    return qs


def _screens_for_mode(mode: StartMode) -> list[ScreenStep]:
    base_entry: ScreenStep = {
        "screen_id": "entry_restore",
        "title_zh": "正在为您准备",
        "purpose": "Identity restore + shell before network detail",
        "primary_cta_zh": "",
    }
    if mode == "CONTINUE_ACTIVE":
        return [
            base_entry,
            {
                "screen_id": "one_active_case",
                "title_zh": "您已有一个正在处理的报案",
                "purpose": "Prevent duplicate claim; continue only",
                "primary_cta_zh": "继续当前报案",
            },
            {
                "screen_id": "task_home",
                "title_zh": "当前报案",
                "purpose": "Resume active case",
                "primary_cta_zh": "查看进度",
            },
        ]
    if mode == "CONTACT_BROKER":
        return [
            base_entry,
            {
                "screen_id": "contact_broker",
                "title_zh": "请联系保险顾问",
                "purpose": "Ambiguous identity — no silent start",
                "primary_cta_zh": "联系顾问",
            },
        ]

    screens: list[ScreenStep] = [base_entry]
    if mode == "MATCHED_CONFIRM_VEHICLE":
        screens.append(
            {
                "screen_id": "confirm_vehicle",
                "title_zh": "哪辆车出险？",
                "purpose": "Disambiguate multi-vehicle before accident facts",
                "primary_cta_zh": "确认车辆",
            }
        )
    if mode == "MATCHED_CONFIRM_POLICY":
        screens.append(
            {
                "screen_id": "confirm_policy",
                "title_zh": "请确认保单信息",
                "purpose": "Stale policy must not silently pretill as truth",
                "primary_cta_zh": "确认后继续",
            }
        )
    screens.extend(
        [
            {
                "screen_id": "known_context",
                "title_zh": "我们已了解您的信息",
                "purpose": "Show known chips; edit-on-request only",
                "primary_cta_zh": "信息无误，继续",
            },
            {
                "screen_id": "accident_facts",
                "title_zh": "今天发生了什么？",
                "purpose": "Only new accident Must Haves",
                "primary_cta_zh": "下一步",
            },
            {
                "screen_id": "photos_optional",
                "title_zh": "添加现场照片（可选）",
                "purpose": "Optional evidence; never blocks Start Claim",
                "primary_cta_zh": "跳过",
            },
            {
                "screen_id": "review_submit",
                "title_zh": "确认后提交",
                "purpose": "Review known + accident; one submit",
                "primary_cta_zh": "提交给顾问",
            },
            {
                "screen_id": "receipt",
                "title_zh": "已提交",
                "purpose": "Success + Home/Continue path",
                "primary_cta_zh": "返回首页",
            },
        ]
    )
    if mode == "BLANK_DEGRADE":
        # No known_context trust panel — go straight to accident facts.
        screens = [
            base_entry,
            {
                "screen_id": "accident_facts",
                "title_zh": "今天发生了什么？",
                "purpose": "Graceful blank Start Claim; no identity wall",
                "primary_cta_zh": "下一步",
            },
            {
                "screen_id": "photos_optional",
                "title_zh": "添加现场照片（可选）",
                "purpose": "Optional evidence",
                "primary_cta_zh": "跳过",
            },
            {
                "screen_id": "review_submit",
                "title_zh": "确认后提交",
                "purpose": "Review accident facts only",
                "primary_cta_zh": "提交给顾问",
            },
            {
                "screen_id": "receipt",
                "title_zh": "已提交",
                "purpose": "Success",
                "primary_cta_zh": "返回首页",
            },
        ]
    return screens


def _resolve_mode(lookup: LookupResult, prefill: PrefillResult) -> StartMode:
    """Prefer Cap 02 confirm flags over Cap 01 next_action when they disagree.

    Example: Cap 01 S3 fixture historically labels next_action confirm_vehicle
    even with a single AUTO vehicle — Cap 03 must not force a dead-end confirm.
    """
    status = str(lookup.get("match_status") or prefill.get("lookup_match_status") or "")
    next_action = str(
        lookup.get("next_action") or prefill.get("lookup_next_action") or ""
    )
    fields = _field_map(prefill)
    vehicle = fields.get("vehicle") or {}
    policy = fields.get("policy") or {}

    if status == "AMBIGUOUS_MATCH" or next_action == "contact_broker":
        return "CONTACT_BROKER"
    if next_action == "continue_active_case" or (
        lookup.get("active_case")
        and (lookup.get("active_case") or {}).get("resume_available")
    ):
        return "CONTINUE_ACTIVE"
    if status in ("NOT_FOUND", "UNMATCHED_IDENTITY", "LOOKUP_UNAVAILABLE"):
        return "BLANK_DEGRADE"

    vehicle_needs = bool(vehicle.get("needs_confirm")) or (
        next_action == "confirm_vehicle"
        and vehicle.get("classification") != "AUTO_PREFILL"
    )
    if vehicle_needs:
        return "MATCHED_CONFIRM_VEHICLE"

    policy_needs = (
        status == "STALE_POLICY"
        or next_action == "confirm_stale_policy"
        or bool(policy.get("needs_confirm"))
    )
    if policy_needs:
        return "MATCHED_CONFIRM_POLICY"

    if status == "MATCH_FOUND":
        return "MATCHED_KNOWN"
    return "BLANK_DEGRADE"


def _estimate_inputs(mode: StartMode, confirm_steps: list[ConfirmStep]) -> int:
    """Deliberate customer inputs: confirms + 4 Must Haves (damage/photos optional)."""
    if mode == "CONTINUE_ACTIVE":
        return 1  # tap Continue
    if mode == "CONTACT_BROKER":
        return 1  # tap Contact
    confirms = len(confirm_steps)
    must_haves = 4
    return confirms + must_haves


def build_smart_claim_start_plan(
    lookup: LookupResult,
    prefill: PrefillResult | None = None,
) -> SmartClaimStartPlan:
    """
    Build a customer-ready Smart Claim Start plan.

    If prefill is omitted, Cap 02 classification is computed by the caller;
    Cap 03 does not import Cap 02 engine by default to keep the seam explicit.
    Prefer passing both for Founder simulations.
    """
    if prefill is None:
        raise ValueError("PrefillResult is required (Cap 02). Cap 03 does not re-classify.")

    mode = _resolve_mode(lookup, prefill)
    fields = _field_map(prefill)
    confirm_vehicle = mode == "MATCHED_CONFIRM_VEHICLE"
    confirm_policy = mode == "MATCHED_CONFIRM_POLICY"

    confirm_steps: list[ConfirmStep] = []
    if confirm_vehicle:
        vehicle = fields.get("vehicle") or {}
        options = list(vehicle.get("candidates") or [])
        if not options:
            options = ["车辆 1", "车辆 2"]
        confirm_steps.append(
            {
                "step_id": "confirm_vehicle",
                "prompt_zh": "哪辆车出险？",
                "options": options,
                "required_before_accident": True,
                "reason_code": "multi_vehicle_disambiguation",
            }
        )
    if confirm_policy:
        confirm_steps.append(
            {
                "step_id": "confirm_policy",
                "prompt_zh": "系统显示保单可能已过期，请确认是否仍用此保单报案",
                "options": ["确认使用此保单", "联系顾问更新保单"],
                "required_before_accident": True,
                "reason_code": "stale_policy_confirm",
            }
        )

    known_chips = (
        []
        if mode in ("BLANK_DEGRADE", "CONTACT_BROKER", "CONTINUE_ACTIVE")
        else _build_known_chips(
            fields, confirm_vehicle=confirm_vehicle, confirm_policy=confirm_policy
        )
    )

    if mode == "CONTINUE_ACTIVE":
        questions: list[QuestionDecision] = [
            _question(k, "HIDDEN", "active_case_resume_no_reask", blocks_submit=False)
            for k in MUST_HAVE_ACCIDENT_KEYS
        ]
        headline = "您已有一个正在处理的报案"
        subtitle = "请先继续当前报案。如确需新的报案，请联系保险顾问。"
        confidence = "我们找到了您正在处理的报案"
        primary = "继续当前报案"
        secondary: str | None = "联系保险顾问"
        failure = "one_active_case_gate"
        photos = "HIDDEN_UNTIL_REQUEST_MORE"
        never_ask = list(prefill.get("auto_fields") or []) + list(MUST_HAVE_ACCIDENT_KEYS)
    elif mode == "CONTACT_BROKER":
        questions = [
            _question(k, "HIDDEN", "ambiguous_no_silent_start", blocks_submit=False)
            for k in MUST_HAVE_ACCIDENT_KEYS
        ]
        headline = "需要保险顾问协助确认身份"
        subtitle = "为避免用错保单或车辆，请先联系顾问后再报案。"
        confidence = "暂时无法自动确认您的信息"
        primary = "联系保险顾问"
        secondary = None
        failure = "ambiguous_match_contact_broker"
        photos = "HIDDEN_UNTIL_REQUEST_MORE"
        never_ask = []
    elif mode == "BLANK_DEGRADE":
        questions = _accident_questions()
        # Identity gaps are broker-owned — do not expand Must Haves.
        for key in ("customer_name", "phone", "vehicle", "policy"):
            questions.insert(
                0,
                _question(key, "BROKER_OWNED", "degrade_identity_broker", blocks_submit=False),
            )
        headline = "今天发生了什么？"
        subtitle = "先告诉我们事故情况。身份与保单信息如需补充，顾问会再联系您。"
        confidence = "我们会先记下事故情况"
        primary = "提交给顾问"
        secondary = "联系保险顾问"
        failure = "lookup_degrade_blank_claim"
        photos = "AFTER_SUBMIT_OPTIONAL"
        never_ask = []
    else:
        questions = _accident_questions()
        if confirm_vehicle:
            questions.insert(
                0,
                _question(
                    "vehicle",
                    "VISIBLE_CONFIRM",
                    "multi_vehicle_confirm",
                    blocks_submit=True,
                ),
            )
        if confirm_policy:
            questions.insert(
                0,
                _question(
                    "policy",
                    "VISIBLE_CONFIRM",
                    "stale_policy_confirm",
                    blocks_submit=True,
                ),
            )
        if mode == "MATCHED_CONFIRM_VEHICLE":
            headline = "确认车辆后，告诉我们今天发生了什么"
            subtitle = "我们已准备好您的姓名与联系方式；请先选择出险车辆。"
            confidence = "我们已了解您的部分信息"
        elif mode == "MATCHED_CONFIRM_POLICY":
            headline = "确认保单后，告诉我们今天发生了什么"
            subtitle = "保单信息可能需要您确认一下，然后只需补充事故事实。"
            confidence = "我们已准备好您的信息，请确认保单"
        else:
            headline = "今天发生了什么？"
            subtitle = "我们已准备好您的信息。您只需补充事故事实。"
            confidence = "我们已了解您"
        primary = "提交给顾问"
        secondary = "修改我的信息"
        failure = "matched_smart_start"
        photos = "AFTER_SUBMIT_OPTIONAL"
        never_ask = list(prefill.get("auto_fields") or [])

    edit_on_request = [
        c["field_key"]
        for c in known_chips
        if c.get("editability") == "EDIT_ON_REQUEST"
    ]

    reasons = list(prefill.get("reason_codes") or [])
    reasons.append(f"smart_start_mode:{mode}")

    plan: SmartClaimStartPlan = {
        "mode": mode,
        "headline_zh": headline,
        "subtitle_zh": subtitle,
        "confidence_signal": confidence,
        "known_chips": known_chips,
        "confirm_steps": confirm_steps,
        "questions": questions,
        "screens": _screens_for_mode(mode),
        "primary_cta_zh": primary,
        "secondary_cta_zh": secondary,
        "estimated_customer_inputs": _estimate_inputs(mode, confirm_steps),
        "never_ask_again": never_ask,
        "edit_on_request_fields": edit_on_request,
        "photos_placement": photos,  # type: ignore[typeddict-item]
        "failure_profile": failure,
        "lookup_match_status": str(
            prefill.get("lookup_match_status") or lookup.get("match_status") or ""
        ),
        "lookup_confidence": str(
            prefill.get("lookup_confidence") or lookup.get("lookup_confidence") or ""
        ),
        "lookup_next_action": str(
            prefill.get("lookup_next_action") or lookup.get("next_action") or ""
        ),
        "prefill_source": str(prefill.get("prefill_source") or "lookup_mock"),
        "reason_codes": reasons,
        "adapter_boundary": "consumes_LookupResult_and_PrefillResult_only",
    }
    assert_smart_claim_start_plan_complete(plan)
    return plan
