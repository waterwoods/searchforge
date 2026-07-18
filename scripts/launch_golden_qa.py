#!/usr/bin/env python3
"""
P25 — Launch Golden QA (reset + Preview prep + status).

One Founder action:
  bash scripts/launch_golden_qa.sh --qa

Or via support API / Workbench QA Tools.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Final

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.camry_golden_qa import ARTIFACT_DIR, reset_golden_qa  # noqa: E402
from scripts.golden_qa_preview import (  # noqa: E402
    clear_devtools_preview_tokens,
    prepare_devtools_preview,
    preview_has_session_token,
)

STATUS_PATH: Final[Path] = ARTIFACT_DIR / "launch_status.json"
LOCK = threading.Lock()
_LAUNCH_IN_FLIGHT = False

STATUS_IDLE = "idle"
STATUS_RUNNING_RESET = "running_reset"
STATUS_PREPARING_PREVIEW = "preparing_preview"
STATUS_READY = "ready_to_scan"
STATUS_FAILED = "failed"


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_status(payload: dict[str, Any]) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def read_launch_status() -> dict[str, Any]:
    if not STATUS_PATH.exists():
        return {
            "status": STATUS_IDLE,
            "case_id": None,
            "expires_at": None,
            "token_masked": None,
            "preview_prepared": False,
            "last_run_utc": None,
            "failure_reason": None,
            "report_relpath": None,
            "devtools_hint": None,
        }
    try:
        data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"status": STATUS_IDLE}
    except Exception:
        return {"status": STATUS_IDLE, "failure_reason": "status_unreadable"}


def public_status_view(raw: dict[str, Any] | None = None) -> dict[str, Any]:
    """Safe fields for Workbench UI — never includes raw token."""
    data = dict(raw or read_launch_status())
    return {
        "status": data.get("status") or STATUS_IDLE,
        "case_id": data.get("case_id"),
        "expires_at": data.get("expires_at"),
        "token_masked": data.get("token_masked"),
        "preview_prepared": bool(data.get("preview_prepared")),
        "last_run_utc": data.get("last_run_utc"),
        "failure_reason": data.get("failure_reason"),
        "report_relpath": data.get("report_relpath"),
        "devtools_hint": data.get("devtools_hint"),
        "target": data.get("target"),
        "launch_in_flight": bool(_LAUNCH_IN_FLIGHT),
    }


def launch_golden_qa(
    *,
    target: str = "qa",
    prepare_preview: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    """
    Reset Golden Case, optionally inject DevTools Preview compile query.
    Concurrent launches are rejected unless force=True after prior failure/ready.
    """
    global _LAUNCH_IN_FLIGHT

    with LOCK:
        if _LAUNCH_IN_FLIGHT and not force:
            current = public_status_view()
            current["ok"] = False
            current["failure_reason"] = current.get("failure_reason") or "launch_already_in_progress"
            return current
        _LAUNCH_IN_FLIGHT = True

    try:
        _write_status(
            {
                "status": STATUS_RUNNING_RESET,
                "case_id": None,
                "expires_at": None,
                "token_masked": None,
                "preview_prepared": False,
                "last_run_utc": _utc_now_iso(),
                "failure_reason": None,
                "report_relpath": None,
                "devtools_hint": None,
                "target": target,
            }
        )

        handoff = reset_golden_qa(target=target, reseed=True, dry_run=False)
        case_id = str(handoff.get("case_id") or "")
        token = str(handoff.get("token") or "")
        expires_at = handoff.get("expires_at")
        token_masked = handoff.get("token_masked")

        preview_meta: dict[str, Any] = {"preview_prepared": False}
        if prepare_preview:
            _write_status(
                {
                    "status": STATUS_PREPARING_PREVIEW,
                    "case_id": case_id,
                    "expires_at": expires_at,
                    "token_masked": token_masked,
                    "preview_prepared": False,
                    "last_run_utc": _utc_now_iso(),
                    "failure_reason": None,
                    "report_relpath": "docs/evidence/golden_qa/last_reset/handoff.json",
                    "devtools_hint": None,
                    "target": target,
                }
            )
            try:
                preview_meta = prepare_devtools_preview(token)
            except Exception as exc:
                # Reset succeeded; Preview prep failed — still useful, mark ready with warning
                status = {
                    "ok": True,
                    "status": STATUS_READY,
                    "case_id": case_id,
                    "expires_at": expires_at,
                    "token_masked": token_masked,
                    "preview_prepared": False,
                    "last_run_utc": _utc_now_iso(),
                    "failure_reason": f"preview_prepare_failed:{exc}",
                    "report_relpath": "docs/evidence/golden_qa/last_reset/handoff.json",
                    "devtools_hint": "Reset OK — set DevTools compile query from handoff or re-run with local repo.",
                    "target": target,
                    # Support-only one-shot for local Vite apply (not shown in product UI)
                    "devtools_launch_query": f"token={token}",
                    "mini_program_path": f"pages/entry/entry?token={token}",
                }
                _write_status({k: v for k, v in status.items() if k not in ("devtools_launch_query", "mini_program_path")})
                # Keep launch query only in memory return for authorized callers
                return status

        status = {
            "ok": True,
            "status": STATUS_READY,
            "case_id": case_id,
            "expires_at": expires_at,
            "token_masked": token_masked,
            "preview_prepared": bool(preview_meta.get("preview_prepared")),
            "last_run_utc": _utc_now_iso(),
            "failure_reason": None,
            "report_relpath": "docs/evidence/golden_qa/last_reset/handoff.json",
            "devtools_hint": preview_meta.get("devtools_hint"),
            "target": target,
            "devtools_launch_query": f"token={token}",
            "mini_program_path": f"pages/entry/entry?token={token}",
        }
        safe = {k: v for k, v in status.items() if k not in ("devtools_launch_query", "mini_program_path")}
        _write_status(safe)
        return status
    except Exception as exc:
        failed = {
            "ok": False,
            "status": STATUS_FAILED,
            "case_id": None,
            "expires_at": None,
            "token_masked": None,
            "preview_prepared": False,
            "last_run_utc": _utc_now_iso(),
            "failure_reason": str(exc)[:500],
            "report_relpath": None,
            "devtools_hint": None,
            "target": target,
        }
        _write_status(failed)
        return failed
    finally:
        with LOCK:
            _LAUNCH_IN_FLIGHT = False


def golden_qa_launch_enabled() -> bool:
    """Explicit enable, or local/dev runtime. Production-like requires ENABLE_GOLDEN_QA_LAUNCH=1."""
    raw = (os.getenv("ENABLE_GOLDEN_QA_LAUNCH") or "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    env = (os.getenv("ENV") or "").strip().lower()
    if env in ("development", "dev", "local", "test"):
        return True
    # Cloud Run / prod-like: require explicit opt-in
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="P25 Launch Golden QA")
    parser.add_argument("--qa", action="store_true", help="QA Cloud SQL (default if neither set)")
    parser.add_argument("--local", action="store_true", help="Local JSON store")
    parser.add_argument("--no-prepare-preview", action="store_true")
    parser.add_argument("--clear-preview", action="store_true", help="Only clear session tokens")
    parser.add_argument("--status", action="store_true", help="Print launch status JSON")
    args = parser.parse_args()

    if args.clear_preview:
        result = clear_devtools_preview_tokens()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1

    if args.status:
        print(json.dumps(public_status_view(), ensure_ascii=False, indent=2))
        return 0

    target = "local" if args.local else "qa"
    result = launch_golden_qa(
        target=target,
        prepare_preview=not args.no_prepare_preview,
    )
    # CLI may print compile line for operator convenience (session terminal only)
    public = public_status_view(result)
    print(json.dumps(public, ensure_ascii=False, indent=2))
    if result.get("ok") and result.get("mini_program_path"):
        print()
        print("Ready for Preview:")
        print(f"  {result['mini_program_path']}")
        if result.get("preview_prepared"):
            print("  DevTools compile mode already injected (gitignored).")
        print("  Next: 清缓存 → Preview → scan QR once")
    if preview_has_session_token():
        print("  Note: session token present in project.private.config.json — cleared by build:gate")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    # Allow --qa without requiring another target flag
    if "--qa" not in sys.argv and "--local" not in sys.argv and not any(
        a in sys.argv for a in ("--status", "--clear-preview", "-h", "--help")
    ):
        sys.argv.append("--qa")
    raise SystemExit(main())
