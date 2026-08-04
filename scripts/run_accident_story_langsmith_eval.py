#!/usr/bin/env python3
"""Run accident-story golden dataset evaluators (local / CI).

Always runs offline deterministic evals against fixtures.
When LANGSMITH_API_KEY / LANGCHAIN_API_KEY is set, also emits LangSmith traces
(node instrumentation via maybe_traceable). Never uploads raw story text in metadata.

Usage:
  PYTHONPATH=. python3 scripts/run_accident_story_langsmith_eval.py
  PYTHONPATH=. python3 scripts/run_accident_story_langsmith_eval.py --dataset accident_story_v1
  PYTHONPATH=. python3 scripts/run_accident_story_langsmith_eval.py --write-report
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "accident_story_langgraph"
REPORT_DIR = ROOT / "docs" / "evidence" / "langsmith-pr-b"


def _llm_caller_for(mode: str) -> Callable[[str], dict[str, Any]] | None:
    mode = str(mode or "").strip().lower()
    if not mode:
        return None

    def invalid(_text: str) -> dict[str, Any]:
        raise ValueError("invalid_model_json")

    def timeout(_text: str) -> dict[str, Any]:
        raise TimeoutError("timeout")

    def hallucinated(_text: str) -> dict[str, Any]:
        # validate_model_proposals raises; extract node catches → fallback
        return {"coverage_decision": "liable", "injury_status": "no"}

    return {
        "invalid_json": invalid,
        "timeout": timeout,
        "hallucinated": hallucinated,
    }.get(mode)


def load_fixtures() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        body = json.loads(path.read_text(encoding="utf-8"))
        body.setdefault("id", path.stem)
        body["_path"] = str(path.relative_to(ROOT))
        rows.append(body)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Accident-story LangSmith / golden eval")
    parser.add_argument("--dataset", default="accident_story_v1")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--fixture", default="", help="Run a single fixture id/stem")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    from services.fiqa_api.inbox_triage.accident_story_assistant.evaluators import (
        run_evaluators,
    )
    from services.fiqa_api.inbox_triage.accident_story_assistant.graph import (
        propose_from_story,
    )
    from services.fiqa_api.observability.langsmith_tracing import tracing_enabled

    fixtures = load_fixtures()
    if args.fixture:
        fixtures = [f for f in fixtures if f.get("id") == args.fixture or Path(f["_path"]).stem == args.fixture]
        if not fixtures:
            print(f"No fixture matched: {args.fixture}", file=sys.stderr)
            return 2

    print(f"dataset={args.dataset} fixtures={len(fixtures)} tracing_enabled={tracing_enabled()}")

    results: list[dict[str, Any]] = []
    failures = 0
    for fx in fixtures:
        fid = str(fx.get("id") or "unknown")
        expect = fx.get("expect") if isinstance(fx.get("expect"), dict) else {}
        caller = _llm_caller_for(str(fx.get("llm_mode") or ""))
        try:
            proposal = propose_from_story(
                raw_story=str(fx.get("raw_story") or ""),
                command_id=f"cmd_eval_{fid}"[:40],
                idempotency_key=f"idem_eval_{fid}"[:40],
                llm_caller=caller,
                scenario=fid,
            )
            evals = run_evaluators(proposal, expect)
        except Exception as exc:
            proposal = {}
            evals = [{"evaluator": "runtime", "ok": False, "detail": str(exc)}]
        ok = all(bool(e.get("ok")) for e in evals)
        if not ok:
            failures += 1
        failed = [e for e in evals if not e.get("ok")]
        row = {
            "id": fid,
            "ok": ok,
            "question_count": len(proposal.get("followup_questions") or []),
            "missing": list(proposal.get("missing_required_facts") or []),
            "injury_status": proposal.get("injury_status"),
            "used_fallback": bool(proposal.get("used_fallback")),
            "evaluators": evals,
            "failed": failed,
        }
        results.append(row)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {fid} q={row['question_count']} missing={row['missing']} injury={row['injury_status']}")
        for e in failed:
            print(f"  - {e['evaluator']}: {e['detail']}")

    total = len(results)
    passed = total - failures
    rate = (passed / total * 100.0) if total else 0.0
    print(f"\nSUMMARY {passed}/{total} ({rate:.1f}%) failures={failures}")

    if args.write_report or True:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report = {
            "stamp": stamp,
            "dataset": args.dataset,
            "tracing_enabled": tracing_enabled(),
            "langsmith_key_present": bool(
                os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
            ),
            "total": total,
            "passed": passed,
            "failed": failures,
            "pass_rate": round(rate, 2),
            "results": results,
            "redaction_policy": "docs/evidence/langsmith-pr-b/REDACTION_POLICY.md",
        }
        out = REPORT_DIR / "latest-eval-report.json"
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md = REPORT_DIR / "latest-eval-report.md"
        lines = [
            f"# Accident Story Golden Eval — {stamp}",
            "",
            f"**Dataset:** `{args.dataset}`  ",
            f"**Pass rate:** {passed}/{total} ({rate:.1f}%)  ",
            f"**Tracing enabled:** {tracing_enabled()}  ",
            "",
            "| Fixture | Result | Questions | Missing | Injury | Fallback |",
            "|---------|--------|-----------|---------|--------|----------|",
        ]
        for r in results:
            lines.append(
                f"| `{r['id']}` | {'PASS' if r['ok'] else 'FAIL'} | {r['question_count']} | "
                f"`{','.join(r['missing'])}` | {r['injury_status']} | {r['used_fallback']} |"
            )
        fail_rows = [r for r in results if not r["ok"]]
        lines.extend(["", "## Failures", ""])
        if not fail_rows:
            lines.append("None.")
        else:
            for r in fail_rows:
                lines.append(f"### `{r['id']}`")
                for e in r["failed"]:
                    lines.append(f"- `{e['evaluator']}`: {e['detail']}")
                lines.append("")
        md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {out}")
        print(f"Wrote {md}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
