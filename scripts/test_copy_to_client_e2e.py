#!/usr/bin/env python3
"""
E2E test: load demo_fallback.json answers, simulate buildHighlights extraction,
run copy-to-client filter, verify no broker-only content in output.

This tests the full flow: answer → bullets/steps (simplified extraction) → client copy.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FALLBACK = REPO / "ui" / "src" / "assets" / "demo_fallback.json"
BROKER_ONLY_MARKERS = ["经纪人可进一步询问", "经纪人下一步"]


def _contains_broker_only(text: str) -> bool:
    return any(m in text for m in BROKER_ONLY_MARKERS)


def extract_bullets_steps_simple(answer: str) -> tuple[list[str], list[str]]:
    """Simplified extraction similar to buildHighlights. Splits on 。；\n.
    Mirrors buildHighlights: always include 客户可准备 when present (even beyond first 5 steps)."""
    if not answer or not answer.strip():
        return [], []
    split_re = re.compile(r"[。；\n]+")
    parts = [p.strip() for p in split_re.split(answer) if p.strip() and len(p.strip()) >= 10]
    bullets = []
    seen = set()
    for p in parts:
        if p in seen or any(p in s or s in p for s in bullets):
            continue
        bullets.append(p)
        if len(bullets) >= 3:
            break
    step_kw = re.compile(r"步骤|建议|需要|提交|准备|前往|联系|支付|携带|查询|在线|官网")
    lines = [l.strip() for l in answer.split("\n") if l.strip()]
    step_lines = [l for l in lines if step_kw.search(l)]
    steps = list(step_lines[:5])
    # Ensure 客户可准备 always surfaced when present (matches buildHighlights)
    if "客户可准备" in answer and not any("客户可准备" in s for s in steps):
        prep_line = next((l for l in lines if "客户可准备" in l), None)
        if prep_line:
            steps.append(prep_line)
    return bullets, steps


def build_client_copy(bullets: list[str], steps: list[str]) -> str:
    """Filter and build client-ready text (matches demoCopy.ts logic)."""
    cb = [b for b in bullets if not _contains_broker_only(b)]
    cs = [s for s in steps if not _contains_broker_only(s)]
    # Extract 客户可准备 → 您可准备 section
    prep_items = [x for x in cb + cs if "客户可准备" in x]
    cb_no_prep = [b for b in cb if "客户可准备" not in b]
    cs_no_prep = [s for s in cs if "客户可准备" not in s]
    lines = ["【可直接转发给客户】", ""]
    quick = cb_no_prep[0] if cb_no_prep else (cb[0] if cb else "")
    if quick:
        lines.append(quick)
        lines.append("")
    for b in cb_no_prep[1:3]:
        lines.append(f"• {b}")
    if cb_no_prep[1:3]:
        lines.append("")
    if prep_items:
        import re
        t = re.sub(r"\*\*客户可准备\*\*[：:]\s*", "", prep_items[0]).replace("客户可准备：", "").replace("客户可准备:", "").strip()
        if t:
            lines.append("您可准备：")
            lines.append(t)
            lines.append("")
    if cs_no_prep:
        lines.append("建议您：")
        for i, s in enumerate(cs_no_prep[:4], 1):
            lines.append(f"{i}. {s}")
    return "\n".join(lines)


def main() -> int:
    if not FALLBACK.exists():
        print("SKIP: demo_fallback.json not found")
        return 0
    data = json.loads(FALLBACK.read_text(encoding="utf-8"))
    items = data.get("items", [])
    if len(items) < 5:
        print("SKIP: demo_fallback.json has < 5 items")
        return 0

    failed = []
    prep_failed = []
    for i, item in enumerate(items[:5]):
        ans = item.get("answer") or ""
        q = item.get("question", f"Q{i+1}")
        bullets, steps = extract_bullets_steps_simple(ans)
        out = build_client_copy(bullets, steps)
        if any(m in out for m in BROKER_ONLY_MARKERS):
            failed.append((q[:50], out[:200]))
        # When 客户可准备 is in answer, 您可准备 must be surfaced (buildHighlights reliability)
        if "客户可准备" in ans and "您可准备" not in out:
            prep_failed.append((q[:50], out[:200]))

    if failed:
        print("FAIL: broker-only content in client copy for:", [f[0] for f in failed])
        for q, o in failed:
            print("  Q:", q)
            print("  Output:", o)
        return 1
    if prep_failed:
        print("FAIL: 客户可准备 in answer but 您可准备 not surfaced for:", [p[0] for p in prep_failed])
        for q, o in prep_failed:
            print("  Q:", q)
            print("  Output:", o)
        return 1
    print("PASS: E2E copy-to-client excludes broker-only; 客户可准备 surfaced as 您可准备 for all 5")
    return 0


if __name__ == "__main__":
    sys.exit(main())
