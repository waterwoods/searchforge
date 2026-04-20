#!/usr/bin/env python3
"""
Bounded Add-Car pre/post-submit reply regression (in-process, no server).

Guards two-layer standard oracles from TRUTH_LAYER_REPLY_LAYER_INDUSTRIAL_STANDARD_SPRINT:
- Pre-submit: office-receipt / in-queue wording must not appear without persisted formal submit truth.
- Post-submit: replies must not nag for portal formal submit when formal_submitted_at + handed_off context is supplied.

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_pre_post_submit_reply_regression.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append

# Office receipt / queue claims — forbidden unless post-submit truth (spec D).
FORBIDDEN_PRE_SUBMIT_OFFICE_ZH = (
    "已到办公室",
    "已进办公室队列",
    "办公室已正式收到记录",
    "资料已到办公室",
    "已交办公室",
    "办公室已收到",  # close receipt claim; pre-submit handoff should use "正式提交后" framing instead
)

# After office-visible submit, must not instruct customer to do portal formal submit again.
POST_SUBMIT_FORMAL_SUBMIT_NAG = (
    "请在入口完成「正式提交办公室」",
    "待您在入口正式提交办公室后",
    "下一步是在入口正式提交办公室",
    "请在入口完成正式提交",
)

CLIENT = "chen_kui"

# Pilot contract: quote handoff requires truth-complete VIN + ZIP + calendar delivery + primary_driver;
# relative-only pickup (e.g. 下周一) does not satisfy delivery_date.
_FULL_ADD_CAR = (
    "客户要加一台2021 Tesla Model Y，VIN 1HGCM82633A123456，ZIP 90210，2026年4月20日提车，主驾是我自己，"
    "姓名张三电话4155550100，问今天能不能先出报价"
)


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)


def _ok(msg: str) -> None:
    print(f"PASS: {msg}")


def _any_substr(hay: str, needles: tuple[str, ...]) -> list[str]:
    return [n for n in needles if n in (hay or "")]


def test_pre_submit_handoff_no_office_receipt_language() -> bool:
    os.environ["LLM_GENERATION_ENABLED"] = "0"
    r = triage_conversation(_FULL_ADD_CAR, [], client_id=CLIENT, reply_truth_context=None)
    if not r.get("handoff_ready"):
        _fail("expected handoff_ready for full add-car fixture")
        return False
    draft = r.get("client_reply_draft") or ""
    bad = _any_substr(draft, FORBIDDEN_PRE_SUBMIT_OFFICE_ZH)
    if bad:
        _fail(f"pre-submit draft contains forbidden office-receipt phrasing {bad}: …{draft[:200]}…")
        return False
    _ok("pre-submit handoff: no forbidden office-receipt phrases (truth_context=None)")
    return True


def test_post_submit_followup_no_formal_submit_nag() -> bool:
    os.environ["LLM_GENERATION_ENABLED"] = "0"
    ctx = {"formal_submitted_at": "2026-03-01T12:00:00Z", "lifecycle_status": "handed_off"}
    prior_cust = _FULL_ADD_CAR
    prior_sys = "（系统已回复：要点已齐，待正式提交）"
    r = triage_conversation(
        "那商业险保额我想从30万调到50万，会影响多少？",
        [{"role": "customer", "text": prior_cust}, {"role": "system", "text": prior_sys}],
        client_id=CLIENT,
        reply_truth_context=ctx,
    )
    draft = r.get("client_reply_draft") or ""
    bad = _any_substr(draft, POST_SUBMIT_FORMAL_SUBMIT_NAG)
    if bad:
        _fail(f"post-submit follow-up must not nag formal submit; found {bad}: …{draft[:240]}…")
        return False
    _ok("post-submit follow-up: no portal formal-submit nag lines")
    return True


def test_append_with_truth_context_no_formal_submit_nag() -> bool:
    os.environ["LLM_GENERATION_ENABLED"] = "0"
    src = f"[客户] {_FULL_ADD_CAR}\n\n[系统] 测试占位回复。"
    ctx = {"formal_submitted_at": "2026-03-01T12:00:00Z", "lifecycle_status": "handed_off"}
    r = triage_for_append(
        src,
        "我再确认一下，ZIP还是90210对吧？",
        client_id=CLIENT,
        reply_truth_context=ctx,
    )
    draft = r.get("client_reply_draft") or ""
    bad = _any_substr(draft, POST_SUBMIT_FORMAL_SUBMIT_NAG)
    if bad:
        _fail(f"append+truth_context must not nag formal submit; found {bad}: …{draft[:240]}…")
        return False
    _ok("triage_for_append + reply_truth_context: no formal-submit nag")
    return True


def test_formal_submit_this_turn_allows_submitted_phrasing() -> bool:
    """Sanity: the submit turn may use post-submit family (not a forbidden early receipt without persist)."""
    os.environ["LLM_GENERATION_ENABLED"] = "0"
    ctx = {"formal_submit_this_turn": True}
    r = triage_conversation(_FULL_ADD_CAR, [], client_id=CLIENT, reply_truth_context=ctx)
    draft = r.get("client_reply_draft") or ""
    # Should not use the strongest forbidden pre-submit receipt lines without real persist —
    # formal_submit_this_turn is the API contract for this turn.
    if "已进办公室队列" in draft and "正式提交" not in draft:
        _fail("unexpected draft shape for formal_submit_this_turn")
        return False
    _ok("formal_submit_this_turn context accepted (smoke shape)")
    return True


def main() -> int:
    failed = 0
    for fn in (
        test_pre_submit_handoff_no_office_receipt_language,
        test_post_submit_followup_no_formal_submit_nag,
        test_append_with_truth_context_no_formal_submit_nag,
        test_formal_submit_this_turn_allows_submitted_phrasing,
    ):
        if not fn():
            failed += 1
    if failed:
        print(f"\n{failed} check(s) failed", file=sys.stderr)
        return 1
    print("\nAll pre/post-submit reply regression checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
