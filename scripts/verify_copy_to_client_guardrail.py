#!/usr/bin/env python3
"""
Copy-to-client guardrail: verifies broker-only content is excluded from client-ready copy.

Contract (must match ui/src/utils/demoCopy.ts):
- BROKER_ONLY_MARKER = '经纪人可进一步询问'
- buildCopyTextClientReady filters bullets/steps containing this marker
- Client copy must NOT contain 经纪人可进一步询问

Run: python3 scripts/verify_copy_to_client_guardrail.py
Exit: 0 if pass, 1 if broker-only content would leak.
"""
import sys
from pathlib import Path

# Must match ui/src/utils/demoCopy.ts BROKER_ONLY_MARKERS
BROKER_ONLY_MARKERS = ["经纪人可进一步询问", "经纪人下一步"]


def _contains_broker_only(text: str) -> bool:
    return any(m in text for m in BROKER_ONLY_MARKERS)


CLIENT_PREP_MARKER = "客户可准备"


def _extract_prep_text(item: str) -> str:
    """Extract prep content from 客户可准备 line."""
    import re
    t = re.sub(r"\*\*客户可准备\*\*[：:]\s*", "", item)
    return t.replace("客户可准备：", "").replace("客户可准备:", "").strip()


def build_copy_text_client_ready_sim(
    question: str,
    bullets: list[str],
    steps: list[str],
    sources: list[dict],
) -> str:
    """Simulate buildCopyTextClientReady filter logic (must match demoCopy.ts)."""
    client_bullets = [b for b in bullets if not _contains_broker_only(b)]
    client_steps = [s for s in steps if not _contains_broker_only(s)]

    # Extract 客户可准备 → dedicated 您可准备 section
    prep_items = [x for x in client_bullets + client_steps if CLIENT_PREP_MARKER in x]
    bullets_no_prep = [b for b in client_bullets if CLIENT_PREP_MARKER not in b]
    steps_no_prep = [s for s in client_steps if CLIENT_PREP_MARKER not in s]

    lines = []
    lines.append("【可直接转发给客户】")
    lines.append("")
    quick = bullets_no_prep[0] if bullets_no_prep else (client_bullets[0] if client_bullets else "")
    if quick:
        lines.append(quick)
        lines.append("")
    for b in bullets_no_prep[1:3]:
        lines.append(f"• {b}")
    if bullets_no_prep[1:3]:
        lines.append("")
    if prep_items:
        prep_text = _extract_prep_text(prep_items[0])
        if prep_text:
            lines.append("您可准备：")
            lines.append(prep_text)
            lines.append("")
    if steps_no_prep:
        lines.append("建议您：")
        for i, s in enumerate(steps_no_prep[:4], 1):
            lines.append(f"{i}. {s}")
        lines.append("")
    if sources:
        lines.append("官方参考：")
        for s in sources[:2]:
            lines.append(s.get("url", ""))
    return "\n".join(lines)


def main() -> int:
    # Test 1: bullets/steps containing broker-only marker must be filtered
    bullets_with_broker = [
        "加州最低责任险：人身伤害 15,000/30,000，财产损失 5,000",
        "经纪人可进一步询问：车型、用途、预算、是否贷款、是否需加保碰撞/综合险。",
        "客户可准备：车辆信息、驾照、VIN（如有）",
    ]
    steps_with_broker = [
        "确认加州最低责任险要求",
        "经纪人可进一步询问：暂停原因（保险失效/费用）、是否已续保、当前保单号。",
        "按 DMV 指引提交保险证明/缴费",
    ]
    out = build_copy_text_client_ready_sim(
        "q", bullets_with_broker, steps_with_broker, []
    )
    if any(m in out for m in BROKER_ONLY_MARKERS):
        print("FAIL: broker-only content leaked into client copy")
        print("Output:", out[:500])
        return 1

    # Test 1b: 经纪人下一步 must be filtered (broker-only)
    bullets_with_next = ["加州最低责任险...", "经纪人下一步：确认客户车辆/驾照信息，给出 2–3 套方案。"]
    out1b = build_copy_text_client_ready_sim("q", bullets_with_next, [], [])
    if any(m in out1b for m in BROKER_ONLY_MARKERS):
        print("FAIL: 经纪人下一步 leaked into client copy")
        return 1

    # Test 2: 客户可准备 content surfaced as 您可准备 (client-useful)
    bullets_client_ok = [
        "加州最低责任险：人身伤害 15,000/30,000",
        "客户可准备：车辆信息、驾照、VIN（如有）",
    ]
    steps_client_ok = ["客户可准备：当前保单、驾照、多车情况、学生证明（如有）"]
    out2 = build_copy_text_client_ready_sim("q", bullets_client_ok, steps_client_ok, [])
    if "您可准备" not in out2 or "车辆信息" not in out2:
        print("FAIL: client-useful content (客户可准备) was incorrectly removed or not surfaced as 您可准备")
        return 1

    # Test 3: verify demoCopy.ts still has the filter
    demo_copy = Path(__file__).resolve().parent.parent / "ui" / "src" / "utils" / "demoCopy.ts"
    if not demo_copy.exists():
        print("WARN: demoCopy.ts not found, skipping source check")
    else:
        text = demo_copy.read_text(encoding="utf-8")
        if not any(m in text for m in BROKER_ONLY_MARKERS):
            print(f"FAIL: demoCopy.ts no longer contains BROKER_ONLY_MARKERS")
            return 1
        if "filter" not in text.lower() or "includes" not in text:
            print("FAIL: demoCopy.ts filter logic may have been removed")
            return 1

    print("PASS: copy-to-client excludes broker-only content; 客户可准备 surfaced as 您可准备")
    return 0


if __name__ == "__main__":
    sys.exit(main())
