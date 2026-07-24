"""
P3-B Slice 1 — Broker Workbench list projection (findability).

Exposes only the fields brokers need to locate a case in 2–3 seconds.
Never uses raw OpenID / full person_link_key as the primary identity.
"""

from __future__ import annotations

import re
from typing import Any

from services.fiqa_api.inbox_triage.case_ref import ensure_case_ref, normalize_case_ref

# Manufactured / placeholder names must not appear as "broker-confirmed" identity.
_PLACEHOLDER_CUSTOMER_NAMES = frozenset(
    {
        "",
        "qa customer",
        "founder qa customer",
        "test customer",
        "wecom customer",
        "企业微信客户",
        "微信客户",
    }
)

_STAGE_CUSTOMER_LABELS = {
    "customer_action_needed": "等待客户补充",
    "waiting_broker": "等待办公室审核",
    "waiting": "处理中",
    "history": "已归档",
}

_BROKER_STEP_LABELS = {
    "review_ready": "客户已完成，请审核",
    "waiting_for_customer": "等待客户补充",
    "waiting_customer": "等待客户补充",
    "waiting_broker": "等待办公室审核",
    "broker_review": "等待办公室审核",
    "need_info": "等待客户补充",
    "ready": "可以处理",
    "holding": "暂缓处理",
    "done": "已完成",
}

_INTERNAL_ACTION_CODES = frozenset(
    {
        "BROKER_REVIEW",
        "READY",
        "NEED_INFO",
        "DONE",
        "HOLDING",
        "REVIEW_READY",
        "WAITING_FOR_CUSTOMER",
        "WAITING_CUSTOMER",
        "WAITING_BROKER",
    }
)


def phone_last_four(phone: str | None) -> str | None:
    digits = re.sub(r"\D", "", str(phone or ""))
    if len(digits) < 4:
        return None
    return digits[-4:]


def policy_suffix(policy_number: str | None) -> str | None:
    raw = str(policy_number or "").strip()
    if not raw:
        return None
    compact = re.sub(r"\s+", "", raw)
    if len(compact) <= 4:
        return compact
    return compact[-4:]


def person_link_display_suffix(person_link_key: str | None) -> str | None:
    """Short opaque suffix for display — never the full key."""
    key = str(person_link_key or "").strip()
    if not key:
        return None
    # Prefer trailing alnum; keep 4 chars for scannability.
    alnum = re.sub(r"[^A-Za-z0-9]", "", key)
    if len(alnum) >= 4:
        return alnum[-4:].lower()
    if len(key) >= 4:
        return key[-4:].lower()
    return key.lower() or None


def extract_qa_label(case: dict[str, Any]) -> str | None:
    facts = case.get("known_facts") if isinstance(case.get("known_facts"), dict) else {}
    for source in (
        case.get("qa_label"),
        facts.get("qa_label"),
        (case.get("demo_flags") or {}).get("qa_label") if isinstance(case.get("demo_flags"), dict) else None,
    ):
        label = str(source or "").strip()
        if label:
            return label[:80]
    return None


def is_test_case(case: dict[str, Any]) -> bool:
    if bool(case.get("workbench_test")):
        return True
    proj = case.get("p20_case_intake_projection")
    if isinstance(proj, dict) and bool(proj.get("is_test")):
        return True
    return False


def _customer_identity(case: dict[str, Any]) -> dict[str, Any]:
    extra = case.get("extra") if isinstance(case.get("extra"), dict) else {}
    identity = extra.get("customer_identity")
    return identity if isinstance(identity, dict) else {}


def _looks_like_technical_identity(name: str | None) -> bool:
    """Reject OpenID / wx_* / opaque link keys as broker-facing primary names."""
    trimmed = str(name or "").strip()
    if not trimmed:
        return False
    lower = trimmed.lower()
    if lower.startswith("wx_") or lower.startswith("plk_") or lower.startswith("sim_"):
        return True
    if "openid" in lower:
        return True
    # Typical WeChat openid shape (not shown to brokers).
    if re.match(r"^o[\w-]{20,}$", trimmed):
        return True
    return False


def _is_real_customer_name(name: str | None) -> bool:
    trimmed = str(name or "").strip()
    if not trimmed:
        return False
    if trimmed.lower() in _PLACEHOLDER_CUSTOMER_NAMES:
        return False
    if trimmed.startswith("微信客户 ·") or trimmed.startswith("微信客户·"):
        return False
    if re.match(r"^企业微信客户（尾号 .+）$", trimmed):
        return False
    if _looks_like_technical_identity(trimmed):
        return False
    return True


def resolve_customer_display_name(case: dict[str, Any]) -> str:
    """
    Broker-facing priority (only fields that exist today):

    1. office/broker remark-style identity fields when present
       (extra.customer_identity.broker_manual_display_name / wecom_remark)
    2. meaningful customer_name (broker-entered or confirmed real name)
    3. WeCom nickname (extra.customer_identity.wecom_nickname) when present
    4. 微信客户 · <opaque suffix or phone last four>

    Never uses raw OpenID, wx_*, or full person_link_key as the primary label.
    Mini Program claim cases typically only have (2) or (4) today.
    """
    identity = _customer_identity(case)
    for key in ("broker_manual_display_name", "wecom_remark"):
        remark = str(identity.get(key) or "").strip()
        if _is_real_customer_name(remark):
            return remark[:80]

    name = str(case.get("customer_name") or "").strip()
    if _is_real_customer_name(name):
        return name

    nickname = str(identity.get("wecom_nickname") or "").strip()
    if _is_real_customer_name(nickname):
        return nickname[:80]

    suffix = person_link_display_suffix(str(case.get("person_link_key") or ""))
    if not suffix:
        # WeCom external userid may already be masked in API responses; try known facts.
        facts = case.get("known_facts") if isinstance(case.get("known_facts"), dict) else {}
        suffix = person_link_display_suffix(str(facts.get("identity_suffix") or ""))
    if suffix:
        return f"微信客户 · {suffix}"
    last4 = phone_last_four(str(case.get("customer_phone") or ""))
    if last4:
        return f"微信客户 · {last4}"
    return "微信客户"


def resolve_vehicle_summary(case: dict[str, Any]) -> str | None:
    for key in ("primary_vehicle_summary", "own_vehicle_info"):
        val = case.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:120]
    facts = case.get("known_facts") if isinstance(case.get("known_facts"), dict) else {}
    for key in ("own_vehicle_info", "vehicle_summary", "vehicle"):
        val = facts.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:120]
    brief = case.get("claim_case_brief") if isinstance(case.get("claim_case_brief"), dict) else {}
    key_facts = brief.get("key_facts") if isinstance(brief.get("key_facts"), dict) else {}
    for key in ("own_vehicle_info", "claim_vehicle"):
        val = key_facts.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:120]
    packet = case.get("p16_broker_packet") if isinstance(case.get("p16_broker_packet"), dict) else {}
    vehicles = packet.get("vehicles") if isinstance(packet.get("vehicles"), list) else []
    if vehicles and isinstance(vehicles[0], dict):
        v = vehicles[0]
        ymm = " ".join(
            str(v.get(k) or "").strip() for k in ("year", "make", "model") if str(v.get(k) or "").strip()
        ).strip()
        if ymm:
            return ymm[:120]
    return None


def _constitution_customer_action_label(case: dict[str, Any]) -> str | None:
    proj = case.get("constitution_projection")
    if not isinstance(proj, dict):
        return None
    customer = proj.get("customer") if isinstance(proj.get("customer"), dict) else {}
    today = customer.get("today")
    if isinstance(today, str) and today.strip():
        return today.strip()
    if isinstance(today, dict):
        label = str(today.get("label") or today.get("title") or "").strip()
        if label:
            return label
    stage = str(proj.get("current_stage") or customer.get("current_stage") or "").strip()
    if stage in _STAGE_CUSTOMER_LABELS:
        return _STAGE_CUSTOMER_LABELS[stage]
    return None


def _constitution_broker_action_label(case: dict[str, Any]) -> str | None:
    proj = case.get("constitution_projection")
    if not isinstance(proj, dict):
        return None
    broker = proj.get("broker") if isinstance(proj.get("broker"), dict) else {}
    next_action = broker.get("next_action") if isinstance(broker.get("next_action"), dict) else {}
    label = str(next_action.get("label") or "").strip()
    if label:
        return label
    queue = broker.get("queue_summary") if isinstance(broker.get("queue_summary"), dict) else {}
    qlabel = str(queue.get("label") or "").strip()
    if qlabel:
        return qlabel
    return None


def resolve_customer_current_action_label(case: dict[str, Any]) -> str:
    label = _constitution_customer_action_label(case)
    if label:
        return label
    display_status = str(case.get("display_status") or "").strip()
    if display_status and display_status.upper() not in {
        "BROKER_REVIEW",
        "READY",
        "NEED_INFO",
        "DONE",
        "HOLDING",
    }:
        return display_status
    waiting = str(case.get("waiting_on") or "").strip().lower()
    if waiting == "client":
        return "等待客户补充"
    if waiting == "broker":
        return "等待办公室审核"
    return "处理中"


def _humanize_broker_step(raw: str | None) -> str | None:
    """Map internal codes / English stubs to broker-facing Chinese; drop opaque codes."""
    val = str(raw or "").strip()
    if not val:
        return None
    if val in {"暂无动作", "无动作", "—", "-"}:
        return None
    lower = val.lower().replace(" ", "_")
    if lower in _BROKER_STEP_LABELS:
        return _BROKER_STEP_LABELS[lower]
    if val.upper() in _INTERNAL_ACTION_CODES:
        mapped = _BROKER_STEP_LABELS.get(val.lower())
        return mapped
    # snake_case / SCREAMING_SNAKE status tokens are not broker language.
    if re.fullmatch(r"[a-z][a-z0-9_]{2,40}", val) and "_" in val:
        return _BROKER_STEP_LABELS.get(val)
    if re.fullmatch(r"[A-Z][A-Z0-9_]{2,40}", val):
        return _BROKER_STEP_LABELS.get(val.lower())
    # Long English internal ops copy → keep short Chinese fallback later.
    if val[:1].isascii() and "request more" in val.lower():
        return "客户补充中，必要时再 Request More"
    if val[:1].isascii() and "completing default intake" in val.lower():
        return "客户填写中"
    return val[:80]


def resolve_broker_next_action_label(case: dict[str, Any]) -> str:
    label = _humanize_broker_step(_constitution_broker_action_label(case))
    if label:
        return label
    for key in ("office_broker_next_step", "broker_next_step"):
        mapped = _humanize_broker_step(str(case.get(key) or "").strip())
        if mapped:
            return mapped
    return "打开案件核对"


def resolve_latest_meaningful_summary(case: dict[str, Any]) -> str:
    for key in ("demo_summary", "conversation_summary", "office_case_title"):
        val = str(case.get(key) or "").strip()
        if val:
            return val[:160]
    claim_summary = case.get("claim_summary")
    if isinstance(claim_summary, dict):
        parts = [
            str(claim_summary.get(k) or "").strip()
            for k in ("accident_datetime", "accident_location", "accident_description")
            if str(claim_summary.get(k) or "").strip()
        ]
        if parts:
            return " · ".join(parts)[:160]
    facts = case.get("known_facts") if isinstance(case.get("known_facts"), dict) else {}
    desc = str(facts.get("accident_description") or "").strip()
    if desc:
        return desc[:160]
    return str(case.get("display_title") or "理赔案件").strip()[:160]


def resolve_queue_filter_bucket(case: dict[str, Any]) -> str:
    """Return active | waiting_customer | waiting_broker for Workbench filters."""
    proj = case.get("constitution_projection")
    stage = ""
    if isinstance(proj, dict):
        stage = str(proj.get("current_stage") or "").strip()
        customer = proj.get("customer") if isinstance(proj.get("customer"), dict) else {}
        if not stage:
            stage = str(customer.get("current_stage") or "").strip()
    if stage == "customer_action_needed":
        return "waiting_customer"
    if stage == "waiting_broker":
        return "waiting_broker"
    waiting = str(case.get("waiting_on") or "").strip().lower()
    if waiting == "client":
        return "waiting_customer"
    if waiting == "broker":
        return "waiting_broker"
    display = str(case.get("display_status") or "").lower()
    if "等待客户" in display or "waiting customer" in display or "broker_more" in display:
        return "waiting_customer"
    if "等待经纪" in display or "等待审核" in display or "broker review" in display:
        return "waiting_broker"
    return "active"


def build_workbench_list_projection(case: dict[str, Any]) -> dict[str, Any]:
    """Build additive list projection; mutates case only to stamp missing case_ref."""
    if not isinstance(case, dict):
        raise TypeError("build_workbench_list_projection requires a case dict")
    existing = normalize_case_ref(str(case.get("case_ref") or ""))
    if existing:
        case_ref = existing
        case["case_ref"] = existing
    else:
        case_ref = ensure_case_ref(case)
    phone4 = phone_last_four(str(case.get("customer_phone") or ""))
    qa_label = extract_qa_label(case)
    is_test = is_test_case(case)
    return {
        "case_ref": case_ref,
        "customer_display_name": resolve_customer_display_name(case),
        "phone_last_four": phone4,
        "policy_suffix": policy_suffix(str(case.get("policy_number") or "")),
        "vehicle_summary": resolve_vehicle_summary(case),
        "qa_label": qa_label,
        "is_test": is_test,
        "customer_current_action_label": resolve_customer_current_action_label(case),
        "broker_next_action_label": resolve_broker_next_action_label(case),
        "latest_meaningful_summary": resolve_latest_meaningful_summary(case),
        "updated_at": str(case.get("updated_at") or case.get("created_at") or ""),
        "filter_bucket": resolve_queue_filter_bucket(case),
    }


def attach_workbench_list_projection(case: dict[str, Any]) -> dict[str, Any]:
    case["workbench_list"] = build_workbench_list_projection(case)
    # Top-level case_ref for simple clients / search.
    case["case_ref"] = case["workbench_list"]["case_ref"]
    return case


def case_matches_workbench_search(case: dict[str, Any], query: str) -> bool:
    q = str(query or "").strip().lower()
    if not q:
        return True
    wl = case.get("workbench_list") if isinstance(case.get("workbench_list"), dict) else {}
    haystacks = [
        str(wl.get("case_ref") or case.get("case_ref") or ""),
        str(case.get("case_id") or ""),
        str(wl.get("customer_display_name") or ""),
        str(case.get("customer_name") or ""),
        str(case.get("customer_phone") or ""),
        str(wl.get("phone_last_four") or ""),
        str(wl.get("policy_suffix") or ""),
        str(case.get("policy_number") or ""),
        str(wl.get("vehicle_summary") or ""),
        str(wl.get("qa_label") or ""),
        str(wl.get("latest_meaningful_summary") or ""),
        str(wl.get("broker_next_action_label") or ""),
        str(wl.get("customer_current_action_label") or ""),
        str(case.get("contact_note") or ""),
    ]
    # Short case_id fragment (not used for uniqueness, but searchable).
    cid = str(case.get("case_id") or "")
    if cid.startswith("case_") and len(cid) > 5:
        haystacks.append(cid[5:13])
    blob = " ".join(h for h in haystacks if h).lower()
    digits_q = re.sub(r"\D", "", q)
    if digits_q and digits_q in re.sub(r"\D", "", blob):
        return True
    return q in blob
