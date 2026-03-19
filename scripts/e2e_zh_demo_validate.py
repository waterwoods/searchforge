#!/usr/bin/env python3
"""Validate E2E Chinese demo responses and generate report."""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

OUT_DIR = Path(os.environ.get("OUT_DIR", "."))
INSURER_DOMAINS = ["geico.com", "progressive.com", "nationwide.com", "travelers.com", "libertymutual.com", "usaa.com"]
GOV_DOMAINS = ["dmv.ca.gov", "insurance.ca.gov", "ca.gov"]


def domain_type(domain):
    d = (domain or "").lower()
    if any(x in d for x in GOV_DOMAINS):
        return "gov"
    if any(x in d for x in INSURER_DOMAINS):
        return "insurer"
    return "other"


def check_citations(sources):
    if not sources:
        return 0, 0
    gov = sum(1 for s in sources if domain_type(s.get("domain", "")) == "gov")
    ins = sum(1 for s in sources if domain_type(s.get("domain", "")) == "insurer")
    return gov, ins


def main():
    results = []
    all_pass = True
    for i in range(1, 7):
        f = OUT_DIR / f"q{i}.json"
        r = {"q": i, "pass": False, "checks": {}, "error": None}
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            r["error"] = str(e)
            r["checks"]["parse"] = "FAIL"
            results.append(r)
            all_pass = False
            continue

        ok = data.get("ok", False)
        r["checks"]["ok"] = "PASS" if ok else "FAIL"
        r["checks"]["detected_lang"] = (
            "PASS"
            if data.get("detected_lang") in ("zh", "zh-CN", "zh-Hans")
            else f"FAIL (got {data.get('detected_lang')})"
        )
        r["checks"]["translation_applied"] = (
            "PASS"
            if data.get("translation_applied") is True
            else f"FAIL (got {data.get('translation_applied')})"
        )
        q_used = data.get("question_used", "")
        r["checks"]["translated_query_nonempty"] = "PASS" if (q_used and len(q_used) > 2) else "FAIL"
        sources = data.get("sources", data.get("items", []))
        r["checks"]["results_ge_3"] = "PASS" if len(sources) >= 3 else f"FAIL (got {len(sources)})"
        gov, ins = check_citations(sources)
        r["citations_gov"] = gov
        r["citations_insurer"] = ins
        r["checks"]["citations_ge_2"] = (
            "PASS" if (gov + ins) >= 2 else f"FAIL (gov={gov}, insurer={ins})"
        )
        r["checks"]["title_zh_note"] = "query-only"

        fails = [k for k, v in r["checks"].items() if isinstance(v, str) and v.startswith("FAIL")]
        r["pass"] = len(fails) == 0
        if not r["pass"]:
            all_pass = False
        results.append(r)

    lines = []
    lines.append("# E2E Chinese Demo Verification Report")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().isoformat()}")
    lines.append(f"**Output dir**: `{OUT_DIR}`")
    lines.append("")
    lines.append("## Checklist (per query)")
    lines.append("")
    lines.append("| Q | ok | detected_lang | translation_applied | results≥3 | citations≥2 |")
    lines.append("|---|----|---------------|---------------------|-----------|-------------|")
    for r in results:
        c = r.get("checks", {})
        ok_s = "✅" if r.get("pass") else "❌"
        dl = "✅" if c.get("detected_lang") == "PASS" else "❌"
        ta = "✅" if c.get("translation_applied") == "PASS" else "❌"
        r3 = "✅" if c.get("results_ge_3") == "PASS" else "❌"
        cit = "✅" if c.get("citations_ge_2") == "PASS" else "❌"
        lines.append(f"| {r['q']} | {ok_s} | {dl} | {ta} | {r3} | {cit} |")
    lines.append("")
    lines.append("## Detailed checks")
    lines.append("")
    for r in results:
        lines.append(f"### Q{r['q']}")
        for k, v in r.get("checks", {}).items():
            lines.append(f"- {k}: {v}")
        if r.get("citations_gov") is not None:
            lines.append(f"- citations: gov={r['citations_gov']}, insurer={r['citations_insurer']}")
        if r.get("error"):
            lines.append(f"- error: {r['error']}")
        lines.append("")
    lines.append("## Final result")
    lines.append("")
    if all_pass:
        lines.append("**PASS** - All 6 queries passed all checks.")
    else:
        fails = [r for r in results if not r.get("pass")]
        root = "See detailed checks above."
        if any("translation" in str(r.get("checks", {})).lower() for r in fails):
            root = "TRANSLATION_ENABLED=1 and TRANSLATION_PROVIDER=argos not set, or argostranslate not installed. Fix: set -a; source .env.cloudrun; set +a; ensure TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos"
        if any("results_ge_3" in str(r.get("checks", {})) for r in fails):
            root = "Collection auto_insurance_demo_core may be empty. Run: bash scripts/run_demo_ingest_oneclick.sh --run-dir results/auto_insurance_discovery/runs/<latest>"
        lines.append(f"**FAIL** - {len(fails)} query/queries failed. Root cause: {root}")
    lines.append("")
    lines.append("## Raw responses")
    lines.append("")
    lines.append("See q1.json .. q6.json in this directory.")
    lines.append("")

    (OUT_DIR / "E2E_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"  Report: {OUT_DIR / 'E2E_REPORT.md'}")
    print(f"  Result: {'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
