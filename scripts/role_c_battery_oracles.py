"""
Bounded heuristics for Role C Add-Car battery (engineering validation only).

Aligned with docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md:
Truth / Intent / Reply / State(timing) warnings — not perfect detectors, useful signals.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

# --- Truth layer: office receipt before formal submit (see run_pre_post_submit_reply_regression.py) ---
FORBIDDEN_PRE_SUBMIT_OFFICE_ZH = (
    "已到办公室",
    "已进办公室队列",
    "办公室已正式收到记录",
    "资料已到办公室",
    "已交办公室",
    "办公室已收到",
)

POST_SUBMIT_FORMAL_SUBMIT_NAG = (
    "请在入口完成「正式提交办公室」",
    "待您在入口正式提交办公室后",
    "下一步是在入口正式提交办公室",
    "请在入口完成正式提交",
)

# Reply layer: sounds like materials/contact tail when question may be different (weak signal)
CONTACT_GAP_TAIL_MARKERS = (
    "若姓名或电话尚未",
    "办公室后续联系时可能会先确认联系方式",
    "name or phone isn't clear",
)

GENERIC_INTENT = "generic_followup"


def _norm_stem(text: str, n: int = 96) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip().lower())
    return t[:n]


def _any_substr(hay: str, needles: tuple[str, ...]) -> list[str]:
    return [n for n in needles if n in (hay or "")]


def warnings_for_turn(
    *,
    turn_number: int,
    customer_text: str,
    reply_text: str,
    tri: dict[str, Any],
    post_submit_truth: bool,
    injected_formal_submit: bool,
    prev_intent_family: str | None,
    recent_reply_stems: list[str],
) -> list[dict[str, Any]]:
    """
    turn_number: 1-based index of customer turns (excluding inject rows).
    """
    out: list[dict[str, Any]] = []
    still = tri.get("still_needed_fields") or []
    if not isinstance(still, list):
        still = []
    still_l = [str(x).lower() for x in still]
    hr = bool(tri.get("handoff_ready"))
    life = str(tri.get("lifecycle_status") or "").strip()
    draft = reply_text or ""
    ac = tri.get("add_car_turn_intent") or {}
    intent_family = (
        str(ac.get("intent_family") or "").strip() if isinstance(ac, dict) else ""
    )

    if injected_formal_submit:
        out.append(
            {
                "code": "STATE_INFO",
                "layer": "state",
                "message": "Injected formal-submit persist turn (truth-chain)",
            }
        )

    # -------- TRUTH_WARN --------
    # Formal-submit inject turn may legitimately use post-submit phrasing; do not flag.
    if not post_submit_truth and not injected_formal_submit:
        bad = _any_substr(draft, FORBIDDEN_PRE_SUBMIT_OFFICE_ZH)
        if bad:
            out.append(
                {
                    "code": "TRUTH_PRE_SUBMIT_OFFICE_RECEIPT",
                    "layer": "truth",
                    "message": "Reply contains office-receipt style wording without post-submit truth",
                    "detail": bad[:3],
                }
            )

    # Pre-submit only; turns 1–3 may finish quote slots without contact in the bubble (MATURE_INTAKE).
    # Longer threads (turn 4+): handoff_ready vs contact gap is broker-trust critical.
    if (
        hr
        and still
        and any(k in still_l for k in ("name", "phone"))
        and not post_submit_truth
        and turn_number >= 4
    ):
        out.append(
            {
                "code": "TRUTH_HANDOFF_READY_CONTACT_GAP",
                "layer": "truth",
                "message": "handoff_ready while name/phone still in still_needed_fields",
                "detail": [x for x in still if str(x).lower() in ("name", "phone")],
            }
        )

    # -------- REPLY_WARN --------
    if post_submit_truth:
        nag = _any_substr(draft, POST_SUBMIT_FORMAL_SUBMIT_NAG)
        if nag:
            out.append(
                {
                    "code": "REPLY_POST_SUBMIT_FORMAL_NAG",
                    "layer": "reply",
                    "message": "Post-submit reply still nags for portal formal submit",
                    "detail": nag[:3],
                }
            )

    stem = _norm_stem(draft)
    if stem and len(recent_reply_stems) >= 3:
        last3 = recent_reply_stems[-3:]
        if all(s == stem for s in last3):
            out.append(
                {
                    "code": "REPLY_REPEATED_BLOCK",
                    "layer": "reply",
                    "message": "Same reply stem repeated for 4 consecutive turns",
                    "detail": stem[:80],
                }
            )

    if post_submit_truth:
        # Suspicious: contact-gap tail when intent is not generic / office question
        if intent_family and intent_family not in (
            GENERIC_INTENT,
            "office_receipt_question",
            "materials_claim",
        ):
            if _any_substr(draft, CONTACT_GAP_TAIL_MARKERS):
                out.append(
                    {
                        "code": "REPLY_CONTACT_GAP_TAIL_MISMATCH",
                        "layer": "reply",
                        "message": "Contact-gap reassurance tail present while intent family is not generic/receipt/materials",
                        "detail": intent_family,
                    }
                )

    # -------- INTENT_WARN --------
    if turn_number >= 7 and intent_family == GENERIC_INTENT:
        if len((customer_text or "").strip()) > 48:
            out.append(
                {
                    "code": "INTENT_LATE_GENERIC",
                    "layer": "intent",
                    "message": "Late turn (>=7) classified as generic_followup on a long customer line",
                }
            )

    if prev_intent_family and intent_family:
        if prev_intent_family == intent_family == GENERIC_INTENT and turn_number >= 5:
            # Same generic as previous — weak signal unless customer is short ack
            if len((customer_text or "").strip()) > 35:
                out.append(
                    {
                        "code": "INTENT_STICKY_GENERIC",
                        "layer": "intent",
                        "message": "generic_followup repeated while customer message is non-trivial",
                    }
                )

    # -------- STATE_WARN --------
    if post_submit_truth and life == "collecting":
        out.append(
            {
                "code": "STATE_POST_SUBMIT_LIFECYCLE_COLLECTING",
                "layer": "state",
                "message": "Runner has case_id (post-submit truth) but lifecycle_status is collecting",
            }
        )

    return out


def aggregate_run_summary(
    per_turn: list[list[dict[str, Any]]],
    labels: list[str],
) -> dict[str, Any]:
    by_layer: dict[str, int] = {}
    codes: dict[str, int] = {}
    turns_hit: list[int] = []
    for i, ws in enumerate(per_turn, start=1):
        if not ws:
            continue
        # Skip INFO-only turns for "issue" count
        serious = [w for w in ws if not str(w.get("code") or "").endswith("_INFO")]
        if not serious:
            continue
        turns_hit.append(i)
        for w in serious:
            layer = str(w.get("layer") or "unknown")
            by_layer[layer] = by_layer.get(layer, 0) + 1
            c = str(w.get("code") or "")
            codes[c] = codes.get(c, 0) + 1

    top_codes = sorted(codes.items(), key=lambda x: -x[1])[:8]
    return {
        "turns_with_warnings": turns_hit,
        "warning_count_by_layer": by_layer,
        "warning_codes_top": [{"code": k, "count": v} for k, v in top_codes],
        "labels": labels,
    }


def customer_fingerprint(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="replace")).hexdigest()[:12]
