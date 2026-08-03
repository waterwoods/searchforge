"""Known-customer policy/vehicle context decision (Stage 2 Loop 1).

Deterministic contract — no AI, no CRM writes, no fabricated freshness.
Consumes Cap 01 LookupResult (+ optional selected vehicle) only.
"""

from __future__ import annotations

from typing import Any, Mapping

# Decision outcomes (product contract).
DECISION_CONFIRM_EXISTING = "CONFIRM_EXISTING"
DECISION_REQUIRE_UPLOAD = "REQUIRE_UPLOAD"
DECISION_FALLBACK = "FALLBACK"

# Customer choices (command payload).
CHOICE_CORRECT = "correct"
CHOICE_CHANGED = "changed"
CHOICE_UNCERTAIN = "uncertain"

CHOICE_LABELS_ZH = {
    CHOICE_CORRECT: "资料正确，继续",
    CHOICE_CHANGED: "信息有变化",
    CHOICE_UNCERTAIN: "我不确定",
}

LABEL_TO_CHOICE = {v: k for k, v in CHOICE_LABELS_ZH.items()}

EVENT_POLICY_CONTEXT_CONFIRMED = "customer_policy_context_confirmed"
EVENT_POLICY_CONTEXT_CHANGE_REPORTED = "customer_policy_context_change_reported"
EVENT_POLICY_CONTEXT_UNCERTAIN = "customer_policy_context_uncertain"

CONFIRM_STEP_ID = "confirm_policy_context"
CONFIRM_PROMPT_ZH = "已找到您的车辆和保单资料"


def normalize_customer_choice(raw: Any) -> str | None:
    text = str(raw or "").strip()
    if not text:
        return None
    if text in (CHOICE_CORRECT, CHOICE_CHANGED, CHOICE_UNCERTAIN):
        return text
    if text in LABEL_TO_CHOICE:
        return LABEL_TO_CHOICE[text]
    # Tolerate short aliases from clients.
    lowered = text.lower()
    if lowered in ("ok", "confirm", "confirmed", "yes"):
        return CHOICE_CORRECT
    if lowered in ("changed", "change", "更新", "有变化"):
        return CHOICE_CHANGED
    if lowered in ("uncertain", "unsure", "unknown", "不确定"):
        return CHOICE_UNCERTAIN
    return None


def _vehicle_summary(vehicle: Mapping[str, Any] | None) -> str:
    if not isinstance(vehicle, Mapping):
        return ""
    parts = [str(vehicle.get(k) or "").strip() for k in ("year", "make", "model")]
    return " ".join(p for p in parts if p).strip()


def _resolve_vehicle(
    lookup: Mapping[str, Any],
    *,
    selected_vehicle_ref: str | None = None,
    selected_vehicle_summary: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Return (vehicle_dict, reason_if_unresolved)."""
    vehicles = [v for v in (lookup.get("vehicles") or []) if isinstance(v, dict)]
    if not vehicles:
        return None, "vehicle_missing"
    if len(vehicles) == 1:
        return vehicles[0], None

    ref = str(selected_vehicle_ref or "").strip()
    summary = str(selected_vehicle_summary or "").strip()
    if ref:
        for v in vehicles:
            if str(v.get("vehicle_ref") or "").strip() == ref:
                return v, None
        return None, "selected_vehicle_not_in_lookup"
    if summary:
        for v in vehicles:
            if _vehicle_summary(v) == summary:
                return v, None
        return None, "selected_vehicle_summary_not_in_lookup"
    return None, "multi_vehicle_selection_required"


def decide_policy_context(
    lookup: Mapping[str, Any] | None,
    *,
    selected_vehicle_ref: str | None = None,
    selected_vehicle_summary: str | None = None,
) -> dict[str, Any]:
    """Minimal durable decision for insurance-card confirm vs upload.

    CONFIRM_EXISTING — known customer, fresh/active policy, resolved vehicle.
    REQUIRE_UPLOAD — missing / stale / conflicting / wrong-vehicle / untrusted.
    FALLBACK — lookup failure; keep manual upload path.
    """
    if not isinstance(lookup, Mapping) or not lookup:
        return {
            "decision": DECISION_FALLBACK,
            "reason_codes": ["lookup_missing"],
            "customer_safe_summary": None,
            "upload_reason_zh": "暂时无法读取已有保单，请上传保险卡。",
        }

    status = str(lookup.get("match_status") or "").strip()
    confidence = str(lookup.get("lookup_confidence") or "").strip().upper()
    policy = lookup.get("policy") if isinstance(lookup.get("policy"), Mapping) else None
    customer = lookup.get("customer") if isinstance(lookup.get("customer"), Mapping) else None
    prefill = lookup.get("prefill") if isinstance(lookup.get("prefill"), Mapping) else {}

    if status in ("LOOKUP_UNAVAILABLE", "NOT_FOUND", "UNMATCHED_IDENTITY", "AMBIGUOUS_MATCH"):
        return {
            "decision": DECISION_FALLBACK,
            "reason_codes": [f"lookup_status:{status or 'empty'}"],
            "customer_safe_summary": None,
            "upload_reason_zh": "暂时无法读取已有保单，请上传保险卡。",
        }

    vehicle, vehicle_reason = _resolve_vehicle(
        lookup,
        selected_vehicle_ref=selected_vehicle_ref,
        selected_vehicle_summary=selected_vehicle_summary,
    )
    if vehicle_reason == "multi_vehicle_selection_required":
        return {
            "decision": DECISION_REQUIRE_UPLOAD,
            "reason_codes": ["multi_vehicle_unselected"],
            "customer_safe_summary": None,
            "upload_reason_zh": "请先确认出险车辆；确认前仍需上传保险卡。",
            "requires_vehicle_selection": True,
        }
    if vehicle is None:
        return {
            "decision": DECISION_REQUIRE_UPLOAD,
            "reason_codes": [vehicle_reason or "vehicle_unresolved"],
            "customer_safe_summary": None,
            "upload_reason_zh": "未找到可靠的车辆资料，请上传保险卡。",
        }

    if status == "STALE_POLICY" or (
        isinstance(policy, Mapping)
        and (
            str(policy.get("freshness") or "").strip().lower() == "stale"
            or str(policy.get("status") or "").strip().lower() == "expired"
        )
    ):
        summary = _build_summary(customer, vehicle, policy, prefill)
        return {
            "decision": DECISION_REQUIRE_UPLOAD,
            "reason_codes": ["policy_stale_or_expired"],
            "customer_safe_summary": summary,
            "upload_reason_zh": "系统中的保单资料可能已过期，请上传最新保险卡。",
            "vehicle": dict(vehicle),
            "policy": dict(policy) if isinstance(policy, Mapping) else None,
        }

    if not isinstance(policy, Mapping):
        return {
            "decision": DECISION_REQUIRE_UPLOAD,
            "reason_codes": ["policy_missing"],
            "customer_safe_summary": _build_summary(customer, vehicle, None, prefill),
            "upload_reason_zh": "未找到已关联保单，请上传保险卡。",
            "vehicle": dict(vehicle),
            "policy": None,
        }

    carrier = str(policy.get("carrier_display") or "").strip()
    policy_ref = str(policy.get("policy_ref") or prefill.get("policy_number") or "").strip()
    freshness = str(policy.get("freshness") or "").strip().lower()
    policy_status = str(policy.get("status") or "").strip().lower()

    if not carrier or not policy_ref:
        return {
            "decision": DECISION_REQUIRE_UPLOAD,
            "reason_codes": ["policy_incomplete"],
            "customer_safe_summary": _build_summary(customer, vehicle, policy, prefill),
            "upload_reason_zh": "已有保单信息不完整，请上传保险卡。",
            "vehicle": dict(vehicle),
            "policy": dict(policy),
        }

    if freshness and freshness not in ("fresh", "current", "ok"):
        return {
            "decision": DECISION_REQUIRE_UPLOAD,
            "reason_codes": [f"policy_freshness:{freshness}"],
            "customer_safe_summary": _build_summary(customer, vehicle, policy, prefill),
            "upload_reason_zh": "保单新鲜度不足，请上传保险卡以便核对。",
            "vehicle": dict(vehicle),
            "policy": dict(policy),
        }

    if policy_status and policy_status not in ("active", "in_force", "current"):
        return {
            "decision": DECISION_REQUIRE_UPLOAD,
            "reason_codes": [f"policy_status:{policy_status}"],
            "customer_safe_summary": _build_summary(customer, vehicle, policy, prefill),
            "upload_reason_zh": "保单状态不可靠，请上传保险卡。",
            "vehicle": dict(vehicle),
            "policy": dict(policy),
        }

    if confidence == "LOW":
        return {
            "decision": DECISION_REQUIRE_UPLOAD,
            "reason_codes": ["lookup_confidence_low"],
            "customer_safe_summary": _build_summary(customer, vehicle, policy, prefill),
            "upload_reason_zh": "匹配把握不足，请上传保险卡以便确认。",
            "vehicle": dict(vehicle),
            "policy": dict(policy),
        }

    if status != "MATCH_FOUND":
        return {
            "decision": DECISION_REQUIRE_UPLOAD,
            "reason_codes": [f"match_status_not_confirmable:{status}"],
            "customer_safe_summary": _build_summary(customer, vehicle, policy, prefill),
            "upload_reason_zh": "无法安全确认已有保单，请上传保险卡。",
            "vehicle": dict(vehicle),
            "policy": dict(policy),
        }

    summary = _build_summary(customer, vehicle, policy, prefill)
    return {
        "decision": DECISION_CONFIRM_EXISTING,
        "reason_codes": ["known_customer_fresh_policy", "vehicle_resolved"],
        "customer_safe_summary": summary,
        "upload_reason_zh": None,
        "vehicle": dict(vehicle),
        "policy": dict(policy),
        "lookup_source": str(lookup.get("lookup_source") or ""),
        "lookup_confidence": confidence or "MEDIUM",
    }


def _build_summary(
    customer: Mapping[str, Any] | None,
    vehicle: Mapping[str, Any] | None,
    policy: Mapping[str, Any] | None,
    prefill: Mapping[str, Any] | None,
) -> dict[str, Any]:
    prefill = prefill if isinstance(prefill, Mapping) else {}
    customer = customer if isinstance(customer, Mapping) else {}
    vehicle = vehicle if isinstance(vehicle, Mapping) else {}
    policy = policy if isinstance(policy, Mapping) else {}
    name = str(
        prefill.get("customer_name") or customer.get("display_name") or ""
    ).strip()
    vehicle_summary = str(
        prefill.get("primary_vehicle_summary") or _vehicle_summary(vehicle) or ""
    ).strip()
    plate = str(vehicle.get("license_plate") or "").strip()
    plate_masked = ""
    if plate and len(plate) >= 3:
        plate_masked = f"{plate[:1]}***{plate[-2:]}"
    elif plate:
        plate_masked = "***"
    carrier = str(policy.get("carrier_display") or "").strip()
    policy_status = str(policy.get("status") or "").strip().lower()
    freshness = str(policy.get("freshness") or "").strip().lower()
    currentness = ""
    if policy_status == "active" and freshness in ("fresh", "current", "ok", ""):
        currentness = "已关联"
    elif policy_status == "expired" or freshness == "stale":
        currentness = "可能已过期"
    return {
        "customer_name": name or None,
        "vehicle_summary": vehicle_summary or None,
        "plate_masked": plate_masked or None,
        "carrier_display": carrier or None,
        "policy_currentness": currentness or None,
        "policy_ref_masked": _mask_policy_ref(
            str(policy.get("policy_ref") or prefill.get("policy_number") or "")
        ),
    }


def _mask_policy_ref(policy_ref: str) -> str | None:
    raw = str(policy_ref or "").strip()
    if not raw:
        return None
    if "MOCK" in raw.upper():
        # Never show mock internal refs to customers.
        return None
    if len(raw) <= 4:
        return "****"
    return f"…{raw[-4:]}"


def confirm_step_for_decision(decision: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Smart Claim Start confirm_step when CONFIRM_EXISTING is available."""
    if not isinstance(decision, Mapping):
        return None
    if str(decision.get("decision") or "") != DECISION_CONFIRM_EXISTING:
        return None
    summary = decision.get("customer_safe_summary") if isinstance(decision.get("customer_safe_summary"), dict) else {}
    detail_parts = [
        str(summary.get("customer_name") or "").strip(),
        str(summary.get("vehicle_summary") or "").strip(),
        str(summary.get("carrier_display") or "").strip(),
        str(summary.get("policy_currentness") or "").strip(),
    ]
    detail = " · ".join(p for p in detail_parts if p)
    prompt = CONFIRM_PROMPT_ZH if not detail else f"{CONFIRM_PROMPT_ZH}\n{detail}"
    return {
        "step_id": CONFIRM_STEP_ID,
        "prompt_zh": prompt,
        "options": [
            CHOICE_LABELS_ZH[CHOICE_CORRECT],
            CHOICE_LABELS_ZH[CHOICE_CHANGED],
            CHOICE_LABELS_ZH[CHOICE_UNCERTAIN],
        ],
        "required_before_accident": True,
        "reason_code": "known_customer_policy_context_confirm",
    }
