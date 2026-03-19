#!/usr/bin/env python3
"""
Broker regression: run all 5 core broker scenarios and assess answers.
Usage: python3 scripts/broker_regression_all5.py [--port 8001] [--out PATH] [--report PATH]
"""
import argparse
import json
import sys
from pathlib import Path

import requests

QUESTIONS = [
    ("Q1", "我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？", "minimum insurance / new car"),
    ("Q2", "我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？", "suspended / reinstatement"),
    ("Q3", "客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？", "compliance / license lookup"),
    ("Q4", "客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？", "save money / discounts"),
    ("Q5", "出险后理赔流程是怎样的？", "claims / after accident"),
]

# Long-tail SR-22 / proof (LT03, LT04) - use with --longtail
LONGTAIL_QUESTIONS = [
    ("LT03", "什么是 SR-22？谁需要？怎么办理？", "SR-22 / proof of insurance"),
    ("LT04", "客户需要提供什么保险证明？电子卡可以吗？", "proof of insurance / electronic"),
]


def _write_report(results: list, path: str, all_pass: bool, ok_count: int, total: int, q2_ok: bool, q5_ok: bool, q4_ok: bool, workflow_ok: bool, lt03_ok: bool = None) -> None:
    """Write REPORT.md for pre-demo validation."""
    lines = [
        "# Broker Validation Report (Q1–Q5" + (" + LT03/LT04" if lt03_ok is not None else "") + ")",
        "",
        "## Summary",
        "",
        f"**Overall: {'PASS' if all_pass else 'FAIL'}**",
        "",
        f"- API ok: {ok_count}/{total}",
        f"- Q2 $14 fee: {'OK' if q2_ok else 'MISSING'}",
        f"- Q5 claims flow: {'OK' if q5_ok else 'CHECK'}",
        f"- Q4 discounts/broker/carrier: {'OK' if q4_ok else 'CHECK'}",
        f"- Q1–Q5 broker workflow (客户可准备 + 经纪人可进一步询问): {'OK' if workflow_ok else 'CHECK'}",
    ]
    if lt03_ok is not None:
        lines.append(f"- LT03 SR-22: {'OK' if lt03_ok else 'CHECK'}")
    lines.extend(["", "## Per-scenario", ""])
    for r in results:
        label = r.get("label", "?")
        scenario = r.get("scenario", "")
        ok = r.get("ok", False)
        err = r.get("error")
        if err:
            lines.append(f"### {label} ❌ FAIL")
            lines.append(f"**Scenario:** {scenario}")
            lines.append(f"**Error:** {err}")
        else:
            status = "✅ PASS" if ok else "❌ FAIL"
            lines.append(f"### {label} {status}")
            lines.append(f"**Scenario:** {scenario}")
            lines.append(f"**Sources:** {r.get('sources_count', 0)}")
            lines.append(f"**Domains:** {', '.join(r.get('domains', [])[:5]) or '(none)'}")
            if label == "Q2":
                lines.append(f"- $14 fee: {'✅' if r.get('q2_has_14') else '❌'}")
            if label in ("Q1", "Q2", "Q3", "Q5"):
                lines.append(f"- broker workflow (客户可准备 + 经纪人可进一步询问): {'✅' if r.get('has_broker_workflow') else '❌'}")
            if label == "Q4":
                lines.append(f"- discounts: {'✅' if r.get('q4_has_discounts') else '❌'}, broker hint: {'✅' if r.get('q4_has_broker_hint') else '❌'}, carrier note: {'✅' if r.get('q4_has_carrier_note') else '❌'}")
            if label == "Q5":
                lines.append(f"- claims flow: {'✅' if r.get('q5_has_claims_flow') else '❌'}, refusal: {'❌' if r.get('q5_has_refusal') else '✅'}")
            if label == "LT03":
                lines.append(f"- SR-22 content: {'✅' if r.get('lt03_has_sr22') else '❌'}, broker hint: {'✅' if r.get('lt03_has_broker_hint') else '❌'}")
            if label == "LT04":
                lines.append(f"- proof content: {'✅' if r.get('lt04_has_proof') else '❌'}")
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8001)
    p.add_argument("--out", type=str, default=None, help="Write JSON to this path")
    p.add_argument("--report", type=str, default=None, help="Write REPORT.md to this path")
    p.add_argument("--longtail", action="store_true", help="Add LT03 (SR-22) and LT04 (proof) questions")
    args = p.parse_args()
    base = f"http://127.0.0.1:{args.port}"

    questions_to_run = list(QUESTIONS)
    if args.longtail:
        questions_to_run.extend(LONGTAIL_QUESTIONS)

    results = []
    for label, q, scenario in questions_to_run:
        try:
            r = requests.post(
                f"{base}/api/query",
                json={
                    "question": q,
                    "mode": "demo",
                    "translation_mode": "auto",
                    "top_k": 5,
                    "generate_answer": True,
                },
                timeout=90,
            )
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.ConnectionError:
            print(f"ERROR: Backend not reachable at {base}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR {label}: {e}", file=sys.stderr)
            results.append({"label": label, "scenario": scenario, "ok": False, "error": str(e)})
            continue

        answer = data.get("answer") or ""
        sources = data.get("sources") or []
        domains = [s.get("domain") or "" for s in sources if s.get("domain")]

        # Quick checks for Q2/Q5/Q4 fixes
        q2_has_14 = "$14" in answer
        q5_has_claims_flow = "理赔" in answer or "索赔" in answer
        q5_has_refusal = any(m in (answer or "").lower() for m in ("does not contain", "cannot provide", "cannot answer"))
        q4_has_discounts = any(kw in (answer or "") for kw in ("折扣", "好司机", "多车", "好学生"))
        q4_has_broker_hint = "经纪人" in (answer or "") or "客户可准备" in (answer or "")
        q4_has_carrier_note = "各公司" in (answer or "") or "政策不同" in (answer or "")
        # Q1/Q2/Q3/Q5 workflow hints (broker next questions + client prep)
        has_broker_workflow = "经纪人可进一步询问" in (answer or "") and "客户可准备" in (answer or "")
        # LT03/LT04 SR-22 / proof checks
        lt03_has_sr22 = "sr-22" in (answer or "").lower() or "财务责任" in (answer or "") or "sr22" in (answer or "").lower()
        lt03_has_broker_hint = "经纪人可进一步询问" in (answer or "") or "客户可准备" in (answer or "")
        lt04_has_proof = "证明" in (answer or "") or "proof" in (answer or "").lower() or "电子" in (answer or "")

        result = {
            "label": label,
            "scenario": scenario,
            "ok": data.get("ok", False),
            "answer_len": len(answer),
            "sources_count": len(sources),
            "domains": domains[:5],
            "q2_has_14": q2_has_14,
            "q5_has_claims_flow": q5_has_claims_flow,
            "q5_has_refusal": q5_has_refusal,
            "q4_has_discounts": q4_has_discounts,
            "q4_has_broker_hint": q4_has_broker_hint,
            "q4_has_carrier_note": q4_has_carrier_note,
            "has_broker_workflow": has_broker_workflow,
            "lt03_has_sr22": lt03_has_sr22,
            "lt03_has_broker_hint": lt03_has_broker_hint,
            "lt04_has_proof": lt04_has_proof,
            "answer_preview": answer[:400] if answer else "",
        }
        results.append(result)
        q4_extra = f" discounts={q4_has_discounts} broker={q4_has_broker_hint}" if label == "Q4" else ""
        lt_extra = f" sr22={lt03_has_sr22} broker_hint={lt03_has_broker_hint}" if label == "LT03" else (f" proof={lt04_has_proof}" if label == "LT04" else "")
        wf_extra = f" workflow={has_broker_workflow}" if label in ("Q1", "Q2", "Q3", "Q5") else ""
        print(f"[{label}] sources={len(sources)} $14={q2_has_14} claims_flow={q5_has_claims_flow} refusal={q5_has_refusal}{q4_extra}{lt_extra}{wf_extra}")

    if args.out:
        Path(args.out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {args.out}")

    # Summary
    total = len(questions_to_run)
    ok_count = sum(1 for r in results if r.get("ok"))
    q2_ok = any(r.get("q2_has_14") for r in results if r.get("label") == "Q2")
    q5_ok = any(r.get("q5_has_claims_flow") and not r.get("q5_has_refusal") for r in results if r.get("label") == "Q5")
    q4_ok = any(
        r.get("q4_has_discounts") and r.get("q4_has_broker_hint") and r.get("q4_has_carrier_note")
        for r in results if r.get("label") == "Q4"
    )
    workflow_ok = all(
        r.get("has_broker_workflow") for r in results
        if r.get("label") in ("Q1", "Q2", "Q3", "Q5")
    )
    lt03_ok = None
    if args.longtail:
        lt03_ok = any(
            r.get("lt03_has_sr22") and r.get("lt03_has_broker_hint")
            for r in results if r.get("label") == "LT03"
        )
        all_pass = ok_count == total and q2_ok and q5_ok and q4_ok and workflow_ok and lt03_ok
        print(f"\nSummary: {ok_count}/{total} ok, Q2 $14={'OK' if q2_ok else 'MISSING'}, Q5 claims={'OK' if q5_ok else 'CHECK'}, Q4 discounts={'OK' if q4_ok else 'CHECK'}, workflow={'OK' if workflow_ok else 'CHECK'}, LT03 SR-22={'OK' if lt03_ok else 'CHECK'}")
    else:
        all_pass = ok_count == 5 and q2_ok and q5_ok and q4_ok and workflow_ok
        print(f"\nSummary: {ok_count}/5 ok, Q2 $14={'OK' if q2_ok else 'MISSING'}, Q5 claims={'OK' if q5_ok else 'CHECK'}, Q4 discounts={'OK' if q4_ok else 'CHECK'}, workflow={'OK' if workflow_ok else 'CHECK'}")

    if args.report:
        _write_report(results, args.report, all_pass, ok_count, total, q2_ok, q5_ok, q4_ok, workflow_ok, lt03_ok)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
