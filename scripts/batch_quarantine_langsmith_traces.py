#!/usr/bin/env python3
"""Bounded retry quarantine for historical unsafe LangSmith runs.

Never prints story content or secrets. Logs run id prefixes + status only.

Usage:
  PYTHONPATH=. python3 scripts/quarantine_accident_story_langsmith_traces.py --batch-redact --limit 200
"""
# Reuse module: append batch-redact mode by rewriting the script's main path.
# This file is a thin wrapper that imports and extends the existing quarantine tool.

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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


def _is_unsafe(run: object) -> bool:
    for blob in (getattr(run, "inputs", None) or {}, getattr(run, "outputs", None) or {}):
        if not isinstance(blob, dict):
            continue
        if blob.get("quarantined") and blob.get("redacted"):
            continue
        for k, v in blob.items():
            if k in _UNSAFE_INPUT_KEYS and isinstance(v, str) and v.strip():
                return True
            if k == "proposed_facts" and isinstance(v, list):
                for it in v[:3]:
                    if isinstance(it, dict) and isinstance(it.get("value"), str) and len(it["value"]) > 20:
                        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-redact", action="store_true")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    _load_dotenv()

    out_dir = ROOT / "docs" / "evidence" / "pilot-rehearsal-pr-e" / "langsmith-cleanup"
    out_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT") or ""
    report: dict = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "project_name_len": len(project),
        "api_key_present": bool(api_key),
        "runs_scanned": 0,
        "unsafe_found": 0,
        "already_quarantined": 0,
        "updated_ok": 0,
        "conflict_or_immutable": 0,
        "other_errors": 0,
        "statuses": [],
        "manual_cleanup_required": False,
        "manual_cleanup_instruction": "",
        "post_fix_safe": None,
        "note": "No raw story content logged.",
    }
    if not api_key:
        report["status"] = "SKIPPED_NO_CREDENTIALS"
        (out_dir / "BATCH_CLEANUP_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"status": report["status"]}, indent=2))
        return 0

    from langsmith import Client

    client = Client()
    runs = list(client.list_runs(project_name=project, limit=max(1, min(args.limit, 500))))
    report["runs_scanned"] = len(runs)
    redacted_payload = {"redacted": True, "quarantined": True, "reason": "pre_fix_raw_state"}

    for r in runs:
        rid = str(getattr(r, "id", "") or "")
        name = str(getattr(r, "name", "") or "")
        prefix = rid[:8]
        inputs = getattr(r, "inputs", None) or {}
        if isinstance(inputs, dict) and inputs.get("quarantined") and inputs.get("redacted"):
            report["already_quarantined"] += 1
            report["statuses"].append({"id_prefix": prefix, "name": name, "status": "already_quarantined"})
            continue
        if not _is_unsafe(r):
            continue
        report["unsafe_found"] += 1
        ok = False
        last_err = ""
        for attempt in range(max(1, args.max_attempts)):
            try:
                # Prefer tagging + redacting I/O; conflicts often mean immutable run.
                client.update_run(
                    rid,
                    inputs=redacted_payload,
                    outputs=redacted_payload,
                    tags=["quarantined_pre_fix_pii", "pilot_rehearsal_cleanup"],
                )
                ok = True
                break
            except Exception as exc:
                last_err = type(exc).__name__
                time.sleep(0.4 * (attempt + 1))
        if ok:
            report["updated_ok"] += 1
            report["statuses"].append({"id_prefix": prefix, "name": name, "status": "redacted"})
        elif last_err in ("LangSmithConflictError", "ConflictError", "HTTPError"):
            report["conflict_or_immutable"] += 1
            report["statuses"].append(
                {"id_prefix": prefix, "name": name, "status": "immutable_conflict", "error": last_err}
            )
        else:
            report["other_errors"] += 1
            report["statuses"].append(
                {"id_prefix": prefix, "name": name, "status": "error", "error": last_err or "unknown"}
            )

    remaining = report["conflict_or_immutable"] + report["other_errors"]
    report["manual_cleanup_required"] = remaining > 0
    if remaining:
        report["manual_cleanup_instruction"] = (
            f"LangSmith UI → project (name length={len(project)}) → filter runs named "
            "normalize_story / LangGraph / extract_fact_proposals / validate_proposals / "
            "derive_missing_facts / draft_followup_questions / apply_safety_guardrails / "
            "build_customer_confirmation_proposal created before 2026-08-04 (pre commit 2ef3065) "
            "→ Delete or move to quarantine project. New accident_story.* runs are already redacted."
        )

    # Prove current path still safe
    os.environ.setdefault("ACCIDENT_STORY_LANGSMITH_TRACING", "1")
    os.environ["ACCIDENT_STORY_LLM"] = "0"
    marker = f"REH_MARKER_{int(time.time())}"
    from services.fiqa_api.inbox_triage.accident_story_assistant.service import (
        propose_accident_story,
        reset_accident_story_idempotency_for_tests,
    )

    reset_accident_story_idempotency_for_tests()
    propose_accident_story(
        raw_story=f"昨天追尾，没有受伤。{marker}",
        command_id=f"cmd_reh_{marker[-8:]}",
        idempotency_key=f"idem_reh_{marker[-8:]}",
        office_id="qa_canary_synth",
    )
    time.sleep(2)
    leaked = False
    for r in list(client.list_runs(project_name=project, limit=40)):
        blob = json.dumps(
            {"i": getattr(r, "inputs", None), "o": getattr(r, "outputs", None)},
            ensure_ascii=False,
            default=str,
        )
        if marker in blob:
            leaked = True
            break
    report["post_fix_safe"] = not leaked
    report["status"] = (
        "CLEAN"
        if report["unsafe_found"] == 0 or (report["updated_ok"] + report["already_quarantined"]) >= report["unsafe_found"]
        else "PARTIAL_MANUAL_UI_REQUIRED"
    )
    # Cap status list for file size
    report["statuses"] = report["statuses"][:80]
    (out_dir / "BATCH_CLEANUP_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "unsafe_found": report["unsafe_found"],
                "updated_ok": report["updated_ok"],
                "already_quarantined": report["already_quarantined"],
                "conflict_or_immutable": report["conflict_or_immutable"],
                "post_fix_safe": report["post_fix_safe"],
                "manual_cleanup_required": report["manual_cleanup_required"],
            },
            indent=2,
        )
    )
    return 0 if report.get("post_fix_safe") else 1


if __name__ == "__main__":
    raise SystemExit(main())
