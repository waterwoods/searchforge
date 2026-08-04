#!/usr/bin/env python3
"""Inspect / quarantine pre-redaction LangSmith runs (Accident Story).

Never prints secrets or raw story text. Writes redacted evidence only.

Usage:
  PYTHONPATH=. python3 scripts/quarantine_accident_story_langsmith_traces.py --inspect
  PYTHONPATH=. python3 scripts/quarantine_accident_story_langsmith_traces.py --delete-unsafe
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Keys that indicate raw state leakage from pre-fix LangGraph auto-traces.
_UNSAFE_INPUT_KEYS = frozenset(
    {
        "raw_story",
        "normalized_story",
        "incident_summary",
        "accident_description",
        "accident_time_text",
        "accident_location_text",
    }
)


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _looks_unsafe(run: object) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    inputs = getattr(run, "inputs", None) or {}
    outputs = getattr(run, "outputs", None) or {}
    name = str(getattr(run, "name", "") or "")

    def scan(obj: object, prefix: str) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = str(k)
                if key in _UNSAFE_INPUT_KEYS and isinstance(v, str) and len(v.strip()) > 0:
                    reasons.append(f"{prefix}.{key}")
                elif key == "proposed_facts" and isinstance(v, list):
                    for item in v[:5]:
                        if isinstance(item, dict) and isinstance(item.get("value"), str):
                            if len(str(item.get("value") or "")) > 20:
                                reasons.append(f"{prefix}.proposed_facts.value")
                                break
                else:
                    scan(v, f"{prefix}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:20]):
                scan(item, f"{prefix}[{i}]")

    scan(inputs, "inputs")
    scan(outputs, "outputs")
    # Bare LangGraph node names from pre-fix auto-instrumentation
    if name in {
        "normalize_story",
        "extract_fact_proposals",
        "validate_proposals",
        "derive_missing_facts",
        "draft_followup_questions",
        "apply_safety_guardrails",
        "build_customer_confirmation_proposal",
        "LangGraph",
    } and reasons:
        reasons.append(f"name:{name}")
    return (bool(reasons), sorted(set(reasons))[:12])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true", default=True)
    parser.add_argument("--delete-unsafe", action="store_true")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    _load_dotenv()

    out_dir = ROOT / "docs" / "evidence" / "pilot-canary-pr-d" / "langsmith-cleanup"
    out_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT") or ""
    report: dict = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "project_configured": bool(project),
        "project_name_len": len(project),
        "api_key_present": bool(api_key),
        "runs_scanned": 0,
        "unsafe_run_count": 0,
        "safe_redacted_run_count": 0,
        "deleted_count": 0,
        "delete_supported": False,
        "manual_cleanup_required": False,
        "unsafe_run_summaries": [],
        "note": "No raw story text or secrets included.",
    }

    if not api_key:
        report["status"] = "SKIPPED_NO_CREDENTIALS"
        report["optional_action"] = (
            "Configure LANGCHAIN_API_KEY + LANGCHAIN_PROJECT locally to inspect; "
            "never commit keys."
        )
        (out_dir / "CLEANUP_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"status": report["status"]}, indent=2))
        return 0

    from langsmith import Client

    client = Client()
    runs = list(client.list_runs(project_name=project, limit=max(1, min(args.limit, 500))))
    report["runs_scanned"] = len(runs)

    delete_fn = getattr(client, "delete_run", None)
    report["delete_supported"] = callable(delete_fn)

    for r in runs:
        unsafe, reasons = _looks_unsafe(r)
        name = str(getattr(r, "name", "") or "")
        rid = str(getattr(r, "id", "") or "")
        if name.startswith("accident_story.") and not unsafe:
            report["safe_redacted_run_count"] += 1
            continue
        if not unsafe:
            continue
        report["unsafe_run_count"] += 1
        summary = {
            "run_id_prefix": rid[:8],
            "name": name,
            "reason_keys": reasons,
            "start_time": str(getattr(r, "start_time", "") or "")[:32],
        }
        report["unsafe_run_summaries"].append(summary)
        if args.delete_unsafe and callable(delete_fn):
            try:
                delete_fn(rid)
                report["deleted_count"] += 1
            except Exception as exc:
                report["manual_cleanup_required"] = True
                summary["delete_error"] = type(exc).__name__

    if report["unsafe_run_count"] and report["deleted_count"] < report["unsafe_run_count"]:
        report["manual_cleanup_required"] = True
        report["manual_cleanup_action"] = (
            f"In LangSmith UI for project (name length={len(project)}): filter runs named "
            "normalize_story / LangGraph / extract_fact_proposals (pre-fix) and delete or "
            "move to a quarantine project. Approximate window: any run before pilot-safety "
            "commit 2ef3065 with bare node names and raw_story input keys."
        )

    report["status"] = (
        "CLEANED"
        if report["unsafe_run_count"] == 0
        or (report["deleted_count"] >= report["unsafe_run_count"] and report["unsafe_run_count"] > 0)
        else "INSPECTED_MANUAL_CLEANUP_NEEDED"
        if report["unsafe_run_count"]
        else "CLEAN"
    )
    # Prove current implementation safety with a synthetic marker run
    os.environ.setdefault("ACCIDENT_STORY_LANGSMITH_TRACING", "1")
    os.environ["ACCIDENT_STORY_LLM"] = "0"
    marker = f"CANARY_CLEANUP_MARKER_{int(datetime.now(timezone.utc).timestamp())}"
    from services.fiqa_api.inbox_triage.accident_story_assistant.service import (
        propose_accident_story,
        reset_accident_story_idempotency_for_tests,
    )

    reset_accident_story_idempotency_for_tests()
    propose_accident_story(
        raw_story=f"昨天追尾，没有受伤。{marker}",
        command_id=f"cmd_cleanup_{marker[-8:]}",
        idempotency_key=f"idem_cleanup_{marker[-8:]}",
        office_id="qa_canary_synth",
    )
    import time

    time.sleep(2)
    leaked = False
    for r in list(client.list_runs(project_name=project, limit=30)):
        blob = json.dumps(
            {
                "i": getattr(r, "inputs", None),
                "o": getattr(r, "outputs", None),
            },
            ensure_ascii=False,
            default=str,
        )
        if marker in blob:
            leaked = True
            break
    report["post_fix_marker_leaked"] = leaked
    report["post_fix_safe"] = not leaked

    (out_dir / "CLEANUP_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "README.md").write_text(
        """# LangSmith unsafe-trace cleanup (redacted)

See `CLEANUP_REPORT.json`. Secrets and raw stories are never written here.

Current runs named `accident_story.*` use process_inputs/outputs redaction and
LangGraph auto-trace suppression (`tracing_context(enabled=False)`).
""",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "unsafe_run_count": report["unsafe_run_count"],
                "deleted_count": report["deleted_count"],
                "post_fix_safe": report["post_fix_safe"],
                "manual_cleanup_required": report["manual_cleanup_required"],
            },
            indent=2,
        )
    )
    return 0 if report.get("post_fix_safe") else 1


if __name__ == "__main__":
    raise SystemExit(main())
