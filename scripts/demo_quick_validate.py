#!/usr/bin/env python3
"""
Quick demo validator: checks 3 JSON response files with per-rule validation.
Validates: results count, sources, snippets, gov+insurer diversity.
Called by demo_quick_validate.sh.
Usage: python3 demo_quick_validate.py <out_dir> <q1.json> <q2.json> <q3.json>
"""
import json
import sys
from pathlib import Path
from typing import List, Tuple

GOV_DOMAINS = ("dmv.ca.gov", "insurance.ca.gov")
INSURER_DOMAINS = (
    "geico.com", "progressive.com", "usaa.com", "nationwide.com",
    "libertymutual.com", "travelers.com", "allstate.com", "aaa.com",
)


def _is_gov(domain: str) -> bool:
    d = (domain or "").lower()
    return d.endswith(".ca.gov") or d in GOV_DOMAINS


def _is_insurer(domain: str) -> bool:
    d = (domain or "").lower()
    return any(ins in d for ins in INSURER_DOMAINS)


def _get_domain(source: dict) -> str:
    return (source.get("domain") or "").strip() or _domain_from_url(
        source.get("source_url") or source.get("url") or ""
    )


def _domain_from_url(url: str) -> str:
    if not url:
        return ""
    try:
        from urllib.parse import urlparse
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def validate_response(path: Path, q_label: str) -> Tuple[bool, List[Tuple[str, bool, str]], List[str]]:
    """
    Validate a single response file.
    Returns: (all_passed, [(rule_name, passed, detail), ...], domains_list)
    """
    rules = []
    domains = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, [("read_json", False, str(e))], []

    if not data.get("ok"):
        rules.append(("ok", False, f"API ok=false: {data.get('error', data)}"))
        return False, rules, []

    # API uses "sources"; some may use "results"
    sources = data.get("sources") or data.get("results") or []
    results_count = len(sources)

    for s in sources:
        d = _get_domain(s)
        if d:
            domains.append(d)

    # Rule 1: results count >= 3
    r1 = results_count >= 3
    rules.append(("results>=3", r1, f"count={results_count}"))

    # Rule 2: sources/citations >= 2
    r2 = len(sources) >= 2
    rules.append(("sources>=2", r2, f"count={len(sources)}"))

    # Rule 3: at least 2 with non-empty snippet (or text as fallback)
    snippet_count = sum(1 for s in sources if (s.get("snippet") or s.get("text") or "").strip())
    r3 = snippet_count >= 2
    rules.append(("snippets>=2", r3, f"count={snippet_count}"))

    # Rule 4: at least 1 gov domain
    gov_count = sum(1 for d in domains if _is_gov(d))
    r4 = gov_count >= 1
    rules.append(("gov_domain", r4, f"domains with .ca.gov/dmv/insurance: {gov_count}"))

    # Rule 5: at least 1 insurer domain
    insurer_count = sum(1 for d in domains if _is_insurer(d))
    r5 = insurer_count >= 1
    rules.append(("insurer_domain", r5, f"domains from insurer list: {insurer_count}"))

    all_passed = r1 and r2 and r3 and r4 and r5
    return all_passed, rules, domains


def main():
    if len(sys.argv) != 5:
        print("Usage: demo_quick_validate.py <out_dir> <q1.json> <q2.json> <q3.json>", file=sys.stderr)
        sys.exit(2)

    out_dir = Path(sys.argv[1])
    paths = [Path(p) for p in sys.argv[2:5]]
    questions = [
        "我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？",
        "我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？",
        "客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？",
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Demo Quick Validate Report",
        "",
        "## Summary",
        "",
    ]

    all_pass = True
    for i, (path, q) in enumerate(zip(paths, questions), 1):
        passed, rules, domains = validate_response(path, f"Q{i}")
        if not passed:
            all_pass = False

        status = "✅ PASS" if passed else "❌ FAIL"
        lines.append(f"### Q{i} {status}")
        lines.append("")
        lines.append(f"**Question:** {q[:60]}...")
        lines.append("")
        lines.append("**Domains returned:** " + (", ".join(domains) if domains else "(none)"))
        lines.append("")
        lines.append("**Rules:**")
        for rule_name, rule_passed, detail in rules:
            r_status = "✅" if rule_passed else "❌"
            lines.append(f"- {r_status} `{rule_name}`: {detail}")
        lines.append("")

    lines.insert(4, f"**Overall: {'PASS' if all_pass else 'FAIL'}**")
    lines.insert(5, "")

    report_path = out_dir / "REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
