"""P19H-3j — H5 vs WeCom channel UX policy for customer supplement replies.

H5 is the formal structured task center (review + submit).
WeCom accepts quick supplements; H5 CTA appears only when it helps.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_DONE,
    derive_claim_phase,
    get_claim_missing_items,
    is_claim_summary_ready,
)


class SupplementH5CtaKind(str, Enum):
    """When to surface an H5 link in ordinary supplement acknowledgements."""

    NONE = "none"
    MISSING_ITEMS = "missing_items"
    READY_TO_SUBMIT = "ready_to_submit"


def _is_h5_intake_submitted(case: dict[str, Any]) -> bool:
    state = case.get("h5_intake_state") or {}
    if isinstance(state, dict) and str(state.get("submitted_at") or "").strip():
        return True
    from services.fiqa_api.wecom.claim_state import CLAIM_PHASE_INTAKE_READY_FOR_BROKER

    return derive_claim_phase(case) == CLAIM_PHASE_INTAKE_READY_FOR_BROKER


def count_important_missing_items(case: dict[str, Any]) -> int:
    """Missing required items from existing claim_state kernel (no new scoring)."""
    return len(get_claim_missing_items(case))


def is_ready_for_h5_submit(case: dict[str, Any]) -> bool:
    """Customer completed enough structured fields but has not submitted in H5."""
    if _is_h5_intake_submitted(case):
        return False
    from services.fiqa_api.inbox_triage.h5_task_intake import _current_step

    if _current_step(case) == "review":
        return True
    return is_claim_summary_ready(case)


def resolve_supplement_h5_cta(case: dict[str, Any]) -> tuple[SupplementH5CtaKind, int]:
    """Decide whether an ordinary supplement ack should include an H5 CTA."""
    if derive_claim_phase(case) == CLAIM_PHASE_BROKER_DONE:
        return SupplementH5CtaKind.NONE, 0

    # Post-submit: short ack by default; customer can reply 进度/链接 for H5.
    if _is_h5_intake_submitted(case):
        return SupplementH5CtaKind.NONE, 0

    missing_count = count_important_missing_items(case)

    if is_ready_for_h5_submit(case):
        return SupplementH5CtaKind.READY_TO_SUBMIT, missing_count

    if missing_count > 0:
        return SupplementH5CtaKind.MISSING_ITEMS, missing_count

    return SupplementH5CtaKind.NONE, 0


_PROGRESS_HINT = "如需查看全部资料，可回复「进度」或「链接」。"


def _append_compact_h5_cta(lines: list[str], *, label: str, url: str | None) -> None:
    lines.append(f"【{label}】")
    if url:
        lines.append(url)


def apply_supplement_h5_cta_lines(
    lines: list[str],
    *,
    case: dict[str, Any],
    h5_intake_url: str | None,
) -> None:
    """Append H5 CTA lines per channel UX policy (mutates lines in place)."""
    cta_kind, missing_count = resolve_supplement_h5_cta(case)
    url = (h5_intake_url or "").strip() or None

    if cta_kind == SupplementH5CtaKind.READY_TO_SUBMIT:
        lines.append("资料已经基本齐全，请打开事故资料页面确认并提交给陈总审核：")
        _append_compact_h5_cta(lines, label="提交给陈总审核", url=url)
        return

    if cta_kind == SupplementH5CtaKind.MISSING_ITEMS:
        lines.append(f"目前还缺 {missing_count} 项重要资料，建议打开事故资料页面继续填写：")
        _append_compact_h5_cta(lines, label="继续补充事故资料", url=url)
        return

    lines.append(_PROGRESS_HINT)


def build_claim_supplement_received_reply(
    *,
    case: dict[str, Any],
    h5_intake_url: str | None = None,
) -> str:
    """Short WeCom ack for text supplement — H5 CTA only when policy requires it."""
    lines = [
        "好的，已记录到您当前的事故资料里。",
        "陈总会查看这条补充。",
    ]
    apply_supplement_h5_cta_lines(lines, case=case, h5_intake_url=h5_intake_url)
    return "\n".join(lines)


def build_claim_media_supplement_ack(
    *,
    case: dict[str, Any],
    h5_intake_url: str | None = None,
) -> str:
    """Short WeCom ack for photo supplement — H5 CTA only when policy requires it."""
    lines = ["好的，照片已收到，并记录到您当前的事故资料里。"]
    cta_kind, missing_count = resolve_supplement_h5_cta(case)
    url = (h5_intake_url or "").strip() or None

    if cta_kind == SupplementH5CtaKind.READY_TO_SUBMIT:
        lines.append("资料已经基本齐全，请打开事故资料页面确认并提交给陈总审核：")
        _append_compact_h5_cta(lines, label="提交给陈总审核", url=url)
    elif cta_kind == SupplementH5CtaKind.MISSING_ITEMS:
        lines.append(f"还缺 {missing_count} 项资料，可继续补充：")
        _append_compact_h5_cta(lines, label="继续补充事故资料", url=url)
    else:
        lines.append(_PROGRESS_HINT)

    return "\n".join(lines)
