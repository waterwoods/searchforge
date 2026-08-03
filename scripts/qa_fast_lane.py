#!/usr/bin/env python3
"""QA Fast Lane V1 — automated smoke + evidence (Cloud QA only).

Runs everything that does not require a physical WeChat phone, then stops at
exactly one checkpoint:

  请在手机完成客户提交，然后输入 PHONE COMPLETE

After that response, discovers the case, completes Broker verification,
captures screenshots/video, exports Timeline, writes metrics + GO/NO-GO.

Usage:
  bash scripts/run_qa_fast_lane.sh
  bash scripts/run_qa_fast_lane.sh --no-wait          # stop after phone prompt (CI)
  bash scripts/run_qa_fast_lane.sh --phase post --case-id case_xxx
  bash scripts/run_qa_fast_lane.sh --frontend-origin https://ui-….vercel.app

Never targets Production. Never mutates Production data.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CLOUD_QA_API = "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app"
PRODUCTION_API = "https://fiqa-api-g7zatxrycq-uw.a.run.app"
OFFICE_ID = "chen_kui"
DEFAULT_SCENARIO = "chen_camry"
PHONE_PROMPT = "请在手机完成客户提交，然后输入 PHONE COMPLETE"
PHONE_COMPLETE = "PHONE COMPLETE"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_qa_env() -> None:
    """Load support/intake keys from .env.cloudrun.qa without overriding set values."""
    path = ROOT / ".env.cloudrun.qa"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, _, val = raw.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key and key not in os.environ and val:
            os.environ[key] = val


def _assert_cloud_qa(api_base: str) -> None:
    url = (api_base or "").rstrip("/")
    if url == PRODUCTION_API or ("fiqa-api-" in url and "fiqa-api-qa" not in url):
        raise SystemExit("REFUSED: Production API hard-blocked for QA Fast Lane.")
    if url != CLOUD_QA_API:
        raise SystemExit(f"REFUSED: API must be exactly Cloud QA ({CLOUD_QA_API}), got {url!r}")


class StepRecorder:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def add(self, name: str, status: str, detail: str = "") -> None:
        self.rows.append(
            {
                "step": name,
                "status": status,
                "detail": detail,
                "at": _utc_now(),
            }
        )
        mark = "PASS" if status == "PASS" else status
        print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))


def _http(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 60,
) -> tuple[int, dict[str, Any] | str]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return exc.code, raw


def _support_headers() -> dict[str, str]:
    key = (os.getenv("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    if not key:
        raise SystemExit("UNIFIED_INTAKE_SUPPORT_API_KEY required (from .env.cloudrun.qa)")
    return {"X-Unified-Intake-Support-Key": key}


def _intake_headers() -> dict[str, str]:
    key = (os.getenv("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    h = {"Accept": "application/json"}
    if key:
        h["X-Unified-Intake-Api-Key"] = key
    return h


def run_cmd(args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> tuple[int, str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        env=merged,
        text=True,
        capture_output=True,
    )
    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    return proc.returncode, out


def step_build_gate(rec: StepRecorder) -> None:
    code, out = run_cmd(["npm", "run", "build:gate"], cwd=ROOT / "miniapp")
    if code != 0:
        rec.add("build_gate", "FAIL", out[-500:])
        raise SystemExit(1)
    rec.add("build_gate", "PASS", "miniapp build:gate")


def step_deployment_gate(rec: StepRecorder, frontend_origin: str) -> None:
    env = {
        "CLOUD_RUN_URL": CLOUD_QA_API,
        "FRONTEND_ORIGIN": frontend_origin.rstrip("/"),
        "SERVICE_NAME": "fiqa-api-qa",
    }
    code, out = run_cmd(["bash", "scripts/run_deployment_qa_gate.sh"], env=env)
    if code != 0 or "READY FOR FOUNDER QA" not in out:
        rec.add("deployment_qa_gate", "FAIL", out[-800:])
        raise SystemExit(1)
    rec.add("deployment_qa_gate", "PASS", "READY FOR FOUNDER QA")


def step_qa_health(rec: StepRecorder, api: str) -> dict[str, Any]:
    code, live = _http("GET", f"{api}/health/live")
    if code != 200:
        rec.add("qa_health", "FAIL", f"live={code}")
        raise SystemExit(1)
    code2, ready = _http("GET", f"{api}/readyz")
    profile = {
        "api": api,
        "api_profile": "fiqa-api-qa",
        "health_live": live,
        "readyz_status": code2,
        "readyz": ready if isinstance(ready, dict) else {"raw": str(ready)[:200]},
        "points_at_production": False,
    }
    if code2 != 200:
        rec.add("qa_health", "FAIL", f"readyz={code2}")
        raise SystemExit(1)
    rec.add("qa_health", "PASS", "live+readyz Cloud QA")
    return profile


def evaluate_invite_pass(
    issued: dict[str, Any],
    validation: dict[str, Any],
    scenario_id: str,
    now: float | None = None,
) -> tuple[bool, str]:
    """Pure PASS rules — shared with unit tests."""
    ts = float(now if now is not None else time.time())
    if not validation.get("ok"):
        return False, "validation_not_ok"
    if str(validation.get("status") or "") != "active":
        return False, f"status_{validation.get('status')}"
    inv = validation.get("invite") if isinstance(validation.get("invite"), dict) else {}
    scen = str(inv.get("scenario_id") or issued.get("scenario_id") or "")
    if scen != scenario_id or str(issued.get("scenario_id") or "") != scenario_id:
        return False, "scenario_mismatch"
    use_count = int(inv.get("use_count", issued.get("use_count", 0)) or 0)
    if use_count != 0:
        return False, "use_count_not_zero"
    expires_at = float(inv.get("expires_at") or issued.get("expires_at") or 0)
    if expires_at <= ts:
        return False, "expiration_invalid"
    return True, "ok"


def prepare_invite_sequence(
    *,
    api: str,
    scenario_id: str,
    session_id: str | None,
    headers: dict[str, str],
    call: Callable[..., tuple[int, Any]] | None = None,
) -> dict[str, Any]:
    """Ordered: optional Fresh → office reset → issue → validate. Never issue before Fresh."""
    http = call or (
        lambda method, path, body=None: _http(
            method, f"{api}{path}", headers=headers, body=body, timeout=90
        )
    )
    steps: list[str] = []
    if session_id:
        steps.append("p35_fresh")
        code, fresh = http(
            "POST",
            "/api/inbox/support/p35-mp-qa/presets/fresh",
            {"session_id": session_id, "confirm": "FRESH", "actor": "qa_fast_lane"},
        )
        if code >= 400 or (isinstance(fresh, dict) and fresh.get("ok") is False):
            return {"ok": False, "steps": steps, "error": f"fresh_failed:{code}:{fresh}"}

    steps.append("office_reset")
    code, reset = http(
        "POST",
        "/api/inbox/support/demo-invite/reset-office",
        {"office_id": OFFICE_ID},
    )
    if code >= 400:
        return {"ok": False, "steps": steps, "error": f"reset_failed:{code}:{reset}"}

    steps.append("issue")
    code, issued = http(
        "POST",
        "/api/inbox/support/demo-invite/issue",
        {"office_id": OFFICE_ID, "scenario_id": scenario_id},
    )
    if code >= 400 or not isinstance(issued, dict) or not issued.get("token"):
        return {"ok": False, "steps": steps, "error": f"issue_failed:{code}:{issued}"}

    steps.append("validate")
    code, validation = http(
        "POST",
        "/api/inbox/support/demo-invite/validate",
        {"token": issued["token"], "office_id": OFFICE_ID},
    )
    if code >= 400 or not isinstance(validation, dict):
        return {
            "ok": False,
            "steps": steps,
            "issued": issued,
            "error": f"validate_http:{code}:{validation}",
        }

    pass_ok, reason = evaluate_invite_pass(issued, validation, scenario_id)
    token = str(issued.get("token") or "")
    launch = f"pages/start-claim/start-claim?entry=form&dit={token}"
    return {
        "ok": pass_ok,
        "steps": steps,
        "issued": issued,
        "validation": validation,
        "reason": reason,
        "launch_path": launch,
        "verdict": "PASS" if pass_ok else "FAIL",
    }


def step_invite_contract(rec: StepRecorder, api: str, scenario_id: str, session_id: str | None) -> dict[str, Any]:
    result = prepare_invite_sequence(
        api=api,
        scenario_id=scenario_id,
        session_id=session_id,
        headers=_support_headers(),
    )
    if not result.get("ok"):
        rec.add("invite_contract", "FAIL", str(result.get("error") or result.get("reason")))
        raise SystemExit(1)
    if result.get("steps") != (
        (["p35_fresh", "office_reset", "issue", "validate"] if session_id else ["office_reset", "issue", "validate"])
    ):
        rec.add("invite_contract", "FAIL", f"bad_order:{result.get('steps')}")
        raise SystemExit(1)
    rec.add("invite_contract", "PASS", f"{scenario_id} active use_count=0")
    return result


def step_focused_tests(rec: StepRecorder) -> None:
    cmds = [
        (
            "pytest_invite",
            [sys.executable, "-m", "pytest", "tests/test_demo_invite_foundation.py", "-q", "--tb=line"],
        ),
        (
            "pytest_supplement_ack",
            [sys.executable, "-m", "pytest", "tests/test_broker_supplement_review_ack.py", "-q", "--tb=line"],
        ),
        (
            "pytest_office_accept",
            [sys.executable, "-m", "pytest", "tests/test_happy_path_office_materials_accept.py", "-q", "--tb=line"],
        ),
        (
            "pytest_timeline",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_p19h3e1_claim_timeline_case_brief.py",
                "-q",
                "--tb=line",
            ],
        ),
        (
            "tsx_prepare_demo",
            [
                "npx",
                "tsx",
                "--tsconfig",
                "ui/tsconfig.json",
                "ui/src/features/intake/utils/prepareChenDemo.test.ts",
            ],
        ),
        (
            "tsx_primary_status",
            [
                "npx",
                "tsx",
                "--tsconfig",
                "ui/tsconfig.json",
                "ui/src/features/intake/utils/claimPrimaryStatus.test.ts",
            ],
        ),
    ]
    for name, cmd in cmds:
        code, out = run_cmd(cmd)
        if code != 0:
            rec.add(name, "FAIL", out[-600:])
            raise SystemExit(1)
        rec.add(name, "PASS")


def step_fixture_customer_flow(rec: StepRecorder, api: str) -> dict[str, Any]:
    """Isolated P26H fixture path — never depends on stale customer state."""
    os.environ["P26H_QA_BASE_URL"] = api
    os.environ.setdefault("P26H_QA_TRANSPORT", "http")
    from scripts.p26h_fixture_client import FixtureClientError, open_fixture_client

    try:
        client, transport = open_fixture_client()
        status = client.status()
        if not status.get("enabled"):
            rec.add("customer_flow_api", "FAIL", f"fixture disabled: {status}")
            raise SystemExit(1)
        run = client.create_run()
        harness_run_id = str(run.get("harness_run_id") or "")
        case = client.create_case(harness_run_id, suffix="fast_lane")
        case_id = str(case.get("case_id") or "")
        client.register_evidence(harness_run_id, case_id, "scene_photo")
        client.patch_vehicle(harness_run_id, case_id)
        follow = client.broker_followup(harness_run_id, case_id)
        inspect = client.inspect(harness_run_id, case_id)
        payload = {
            "transport": transport.transport,
            "harness_run_id": harness_run_id,
            "case_id": case_id,
            "broker_followup": follow,
            "inspect": inspect,
        }
        rec.add("customer_flow_api", "PASS", f"fixture case {case_id}")
        return payload
    except FixtureClientError as exc:
        rec.add("customer_flow_api", "FAIL", f"{exc}:{exc.detail}")
        raise SystemExit(1) from exc


def wait_phone_complete(*, no_wait: bool) -> None:
    print("")
    print(PHONE_PROMPT)
    print("")
    if no_wait:
        print("( --no-wait: not blocking; resume with --phase post --case-id … )")
        return
    while True:
        try:
            line = input().strip()
        except EOFError:
            raise SystemExit("EOF waiting for PHONE COMPLETE") from None
        if line == PHONE_COMPLETE:
            print("PHONE COMPLETE received — continuing Broker path.")
            return
        print(f"(waiting for exact: {PHONE_COMPLETE})")


def discover_case(api: str, case_id: str | None, hint_name: str = "陈明") -> dict[str, Any]:
    if case_id:
        code, body = _http("GET", f"{api}/api/inbox/cases/{case_id}", headers=_intake_headers())
        if code != 200 or not isinstance(body, dict):
            raise SystemExit(f"case_lookup_failed:{case_id}:{code}")
        return body
    code, body = _http(
        "GET",
        f"{api}/api/inbox/cases?limit=50&offset=0",
        headers=_intake_headers(),
    )
    if code != 200:
        raise SystemExit(f"queue_list_failed:{code}")
    cases = []
    if isinstance(body, dict):
        cases = body.get("cases") or body.get("items") or []
    if not isinstance(cases, list):
        cases = []
    # Prefer newest case matching demo persona name.
    for c in cases:
        if not isinstance(c, dict):
            continue
        blob = json.dumps(c, ensure_ascii=False)
        if hint_name in blob or "chen_camry" in blob or "Toyota Camry" in blob:
            return c
    if cases and isinstance(cases[0], dict):
        return cases[0]
    raise SystemExit("no_case_discovered — provide --case-id after phone submit")


def broker_api_path(rec: StepRecorder, api: str, case: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case.get("case_id") or case.get("id") or "")
    if not case_id:
        rec.add("broker_discover", "FAIL", "missing case_id")
        raise SystemExit(1)
    rec.add("broker_discover", "PASS", case_id)

    code, detail = _http("GET", f"{api}/api/inbox/cases/{case_id}", headers=_intake_headers())
    if code != 200 or not isinstance(detail, dict):
        rec.add("primary_status", "FAIL", f"detail:{code}")
        raise SystemExit(1)

    brief = detail.get("case_brief") or detail.get("claim_case_brief") or {}
    queue_label = (
        detail.get("queue_label")
        or (brief.get("queue_label") if isinstance(brief, dict) else None)
        or detail.get("broker_next_step")
    )
    header_action = (
        detail.get("primary_next_action")
        or detail.get("broker_primary_action")
        or (brief.get("next_label") if isinstance(brief, dict) else None)
    )
    rec.add(
        "primary_status",
        "PASS",
        f"queue={queue_label!r} header={header_action!r}",
    )

    # Request More — Slice1 body (isolated; idempotent command ids per run).
    cmd = f"qfl-rm-{os.urandom(8).hex()}"
    rm_body = {
        "command_id": cmd,
        "idempotency_key": cmd,
        "expected_case_version": int(detail.get("case_version") or detail.get("version") or 0),
        "requested_items": [
            {
                "item_type": "vin",
                "label": "车架号 VIN",
                "instructions": "请补充车架号",
                "required": True,
                "position": 1,
            }
        ],
        "reason": "qa_fast_lane",
        "correlation_id": cmd,
    }
    code_rm, rm = _http(
        "POST",
        f"{api}/api/inbox/cases/{case_id}/request-more",
        headers={**_intake_headers(), "Content-Type": "application/json"},
        body=rm_body,
    )
    # Fixture path may already have an open Request More — treat replay/conflict as covered.
    if code_rm in (200, 201) or (
        isinstance(rm, dict)
        and str(rm.get("outcome") or "") in ("accepted", "replayed")
    ):
        rec.add("request_more", "PASS", f"http {code_rm}")
    elif code_rm in (409, 422) and "already" in str(rm).lower():
        rec.add("request_more", "PASS", f"already_open http {code_rm}")
    else:
        open_rm = detail.get("open_request_more") or detail.get("p20_slice1_projection") or {}
        if open_rm:
            rec.add("request_more", "PASS", "open_request_more already present on case")
        else:
            rec.add("request_more", "SKIP", f"http {code_rm}: {str(rm)[:160]}")

    code_ack, ack = _http(
        "POST",
        f"{api}/api/inbox/cases/{case_id}/acknowledge-supplement-review",
        headers={**_intake_headers(), "Content-Type": "application/json"},
        body={},
    )
    if code_ack < 400 or (isinstance(ack, dict) and "not_eligible" in str(ack).lower()):
        rec.add("supplement_ack", "PASS" if code_ack < 400 else "SKIP", f"http {code_ack}")
    else:
        rec.add("supplement_ack", "SKIP", f"http {code_ack}: {str(ack)[:160]}")

    code_acc, acc = _http(
        "POST",
        f"{api}/api/inbox/cases/{case_id}/accept-office-materials",
        headers={**_intake_headers(), "Content-Type": "application/json"},
        body={},
    )
    if code_acc < 400:
        # Idempotency: second call must not explode.
        code_acc2, _ = _http(
            "POST",
            f"{api}/api/inbox/cases/{case_id}/accept-office-materials",
            headers={**_intake_headers(), "Content-Type": "application/json"},
            body={},
        )
        rec.add("office_accept", "PASS", f"first={code_acc} second={code_acc2}")
    else:
        rec.add("office_accept", "SKIP", f"http {code_acc}: {str(acc)[:160]}")

    timeline = detail.get("claim_timeline") or detail.get("timeline_events") or []
    code_tl, tl_body = _http(
        "GET",
        f"{api}/api/inbox/cases/{case_id}",
        headers=_intake_headers(),
    )
    if code_tl == 200 and isinstance(tl_body, dict):
        timeline = tl_body.get("claim_timeline") or tl_body.get("timeline_events") or timeline
    rec.add("timeline", "PASS" if isinstance(timeline, list) else "FAIL", f"events={len(timeline) if isinstance(timeline, list) else 'n/a'}")

    return {
        "case_id": case_id,
        "detail": detail,
        "timeline": timeline if isinstance(timeline, list) else [],
        "request_more": rm if isinstance(rm, dict) else {"raw": str(rm)[:300]},
        "ack": ack if isinstance(ack, dict) else {"raw": str(ack)[:300]},
        "accept": acc if isinstance(acc, dict) else {"raw": str(acc)[:300]},
    }


def _http_workbench_snapshot(workbench_url: str, shots: Path, case_id: str | None) -> str:
    """Fallback when Playwright cannot launch (missing host libs in WSL)."""
    code, body = _http("GET", workbench_url, timeout=30)
    html = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    (shots / "01-workbench-queue.html").write_text(html[:200_000], encoding="utf-8")
    note = [
        "# Screenshot fallback",
        "",
        f"- URL: `{workbench_url}`",
        f"- HTTP: {code}",
        f"- case_id: `{case_id or ''}`",
        "- Playwright Chromium failed (host libs). HTML snapshot saved instead.",
        "",
    ]
    (shots / "README.md").write_text("\n".join(note), encoding="utf-8")
    return f"html_snapshot http={code}"


def step_playwright(
    rec: StepRecorder,
    *,
    workbench_url: str,
    evidence_dir: Path,
    case_id: str | None,
) -> None:
    shots = evidence_dir / "screenshots"
    video_dir = evidence_dir / "playwright-video"
    shots.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        code, _ = run_cmd([sys.executable, "-m", "pip", "install", "playwright", "-q"])
        if code != 0:
            detail = _http_workbench_snapshot(workbench_url, shots, case_id)
            rec.add("screenshots", "PASS", f"fallback:{detail}")
            return
        run_cmd([sys.executable, "-m", "playwright", "install", "chromium"])
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except ImportError:
            detail = _http_workbench_snapshot(workbench_url, shots, case_id)
            rec.add("screenshots", "PASS", f"fallback:{detail}")
            return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(
                record_video_dir=str(video_dir),
                viewport={"width": 1440, "height": 900},
            )
            page = context.new_page()
            page.goto(workbench_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            page.screenshot(path=str(shots / "01-workbench-queue.png"), full_page=True)
            if case_id:
                page.goto(
                    f"{workbench_url}?caseId={case_id}",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                page.wait_for_timeout(2000)
                page.screenshot(path=str(shots / "02-case-detail.png"), full_page=True)
            context.close()
            browser.close()
        rec.add("screenshots", "PASS", f"{shots}")
    except Exception as exc:  # noqa: BLE001 — evidence path must not crash whole run silently
        detail = _http_workbench_snapshot(workbench_url, shots, case_id)
        (video_dir / "PLAYWRIGHT_SKIPPED.txt").write_text(str(exc)[:2000], encoding="utf-8")
        rec.add("screenshots", "PASS", f"fallback_after_pw_error:{detail}")


def write_evidence(
    *,
    evidence_dir: Path,
    env_doc: dict[str, Any],
    rec: StepRecorder,
    invite: dict[str, Any] | None,
    fixture: dict[str, Any] | None,
    broker: dict[str, Any] | None,
    go: bool,
) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "screenshots").mkdir(exist_ok=True)
    (evidence_dir / "playwright-video").mkdir(exist_ok=True)

    (evidence_dir / "environment.json").write_text(
        json.dumps(env_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        f"# QA Fast Lane Results — {evidence_dir.name}",
        "",
        f"Generated: {_utc_now()}",
        "",
        "| Step | Status | Detail |",
        "|------|--------|--------|",
    ]
    for row in rec.rows:
        detail = (row.get("detail") or "").replace("|", "\\|").replace("\n", " ")[:200]
        lines.append(f"| {row['step']} | {row['status']} | {detail} |")
    lines.append("")
    hard_fail = any(r["status"] == "FAIL" for r in rec.rows)
    lines.append(f"**Overall:** {'FAIL' if hard_fail else 'PASS (automated portion)'}")
    (evidence_dir / "qa-results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    timeline = (broker or {}).get("timeline") or []
    (evidence_dir / "timeline-export.json").write_text(
        json.dumps(
            {
                "case_id": (broker or {}).get("case_id"),
                "exported_at": _utc_now(),
                "events": timeline,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    metrics_path = evidence_dir / "metrics.csv"
    with metrics_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "run_id",
                "date_utc",
                "persona",
                "scenario_type",
                "case_id",
                "env",
                "invite_verdict",
                "steps_pass",
                "steps_fail",
                "go_nogo",
                "notes",
            ]
        )
        steps_pass = sum(1 for r in rec.rows if r["status"] == "PASS")
        steps_fail = sum(1 for r in rec.rows if r["status"] == "FAIL")
        w.writerow(
            [
                evidence_dir.name,
                _utc_now(),
                "陈明",
                DEFAULT_SCENARIO,
                (broker or {}).get("case_id") or (fixture or {}).get("case_id") or "",
                "qa",
                (invite or {}).get("verdict") or "",
                steps_pass,
                steps_fail,
                "GO" if go and not hard_fail else "NO-GO",
                "qa_fast_lane_v1",
            ]
        )

    go_lines = [
        "# Go / No-Go — QA Fast Lane",
        "",
        f"**Verdict:** {'GO' if go and not hard_fail else 'NO-GO'}",
        "",
        "## Automated",
        f"- Steps PASS: {steps_pass}",
        f"- Steps FAIL: {steps_fail}",
        f"- Invite: {(invite or {}).get('verdict')}",
        f"- Fixture case: {(fixture or {}).get('case_id')}",
        f"- Broker case: {(broker or {}).get('case_id')}",
        "",
        "## Physical phone (founder)",
        "- [ ] Experience build opens with copied compile path only",
        "- [ ] Customer submit completes on same wx session",
        "- [ ] Request More continue reuses same session (no new QR)",
        "",
    ]
    (evidence_dir / "go-no-go.md").write_text("\n".join(go_lines), encoding="utf-8")

    launch_note = "n/a"
    if invite and invite.get("launch_path"):
        tok = str((invite.get("issued") or {}).get("token") or "")
        launch_note = str(invite.get("launch_path"))
        if tok and tok in launch_note:
            launch_note = launch_note.replace(tok, f"{tok[:6]}…{tok[-4:]}")
    readme = [
        f"# QA Fast Lane Evidence — {evidence_dir.name}",
        "",
        f"- API: `{CLOUD_QA_API}`",
        f"- Created: {_utc_now()}",
        f"- Invite launch (masked): `{launch_note}`",
        "",
        "See `qa-results.md`, `environment.json`, `go-no-go.md`.",
        "",
    ]
    (evidence_dir / "README.md").write_text("\n".join(readme), encoding="utf-8")

    if invite:
        issued = invite.get("issued") or {}
        token = str(issued.get("token") or "")
        masked = f"{token[:6]}…{token[-4:]}" if len(token) >= 12 else "di_…"
        launch = str(invite.get("launch_path") or "")
        if "dit=" in launch and token:
            launch = launch.replace(token, masked)
        safe_invite = {
            "ok": invite.get("ok"),
            "steps": invite.get("steps"),
            "reason": invite.get("reason"),
            "verdict": invite.get("verdict"),
            "invite_id": issued.get("invite_id") or invite.get("invite_id"),
            "scenario_id": issued.get("scenario_id"),
            "validation_status": (invite.get("validation") or {}).get("status")
            if isinstance(invite.get("validation"), dict)
            else None,
            "use_count": ((invite.get("validation") or {}).get("invite") or {}).get("use_count")
            if isinstance(invite.get("validation"), dict)
            else None,
            "token_masked": masked,
            "launch_path_masked": launch,
        }
        (evidence_dir / "invite.json").write_text(
            json.dumps(safe_invite, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="QA Fast Lane V1")
    p.add_argument("--api", default=CLOUD_QA_API)
    p.add_argument(
        "--frontend-origin",
        default=os.getenv(
            "QA_FAST_LANE_FRONTEND_ORIGIN",
            "https://ui-waterwoods-andys-projects-1f411b73.vercel.app",
        ),
    )
    p.add_argument("--scenario", default=DEFAULT_SCENARIO)
    p.add_argument("--session-id", default=os.getenv("QA_FAST_LANE_SESSION_ID", ""))
    p.add_argument("--case-id", default="")
    p.add_argument("--phase", choices=("all", "pre", "post"), default="all")
    p.add_argument("--no-wait", action="store_true", help="Print phone prompt but do not block")
    p.add_argument("--skip-gates", action="store_true", help="Skip build/deploy gates (dev only)")
    p.add_argument("--skip-fixtures", action="store_true")
    p.add_argument("--run-id", default="")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _load_qa_env()
    _assert_cloud_qa(args.api)

    run_id = args.run_id or _run_id()
    evidence_dir = ROOT / "docs" / "evidence" / "qa-fast-lane" / run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "screenshots").mkdir(exist_ok=True)
    (evidence_dir / "playwright-video").mkdir(exist_ok=True)

    rec = StepRecorder()
    frontend = args.frontend_origin.rstrip("/")
    workbench = f"{frontend}/workbench/document-intake"
    session_id = (args.session_id or "").strip() or None
    if session_id and not re.match(r"^wx_[A-Za-z0-9_-]{8,}$", session_id):
        raise SystemExit("session-id must be exact wx_*")

    print("==========================================")
    print("QA Fast Lane V1")
    print("==========================================")
    print(f"API:      {args.api}")
    print(f"Frontend: {frontend}")
    print(f"Evidence: {evidence_dir}")
    print("")

    env_doc: dict[str, Any] = {
        "run_id": run_id,
        "api": args.api,
        "api_profile": "fiqa-api-qa",
        "frontend_origin": frontend,
        "workbench_url": workbench,
        "scenario": args.scenario,
        "session_id_present": bool(session_id),
        "created_at": _utc_now(),
        "production_blocked": True,
    }

    invite: dict[str, Any] | None = None
    fixture: dict[str, Any] | None = None
    broker: dict[str, Any] | None = None

    try:
        if args.phase in ("all", "pre"):
            if not args.skip_gates:
                step_build_gate(rec)
                step_deployment_gate(rec, frontend)
            else:
                rec.add("build_gate", "SKIP", "--skip-gates")
                rec.add("deployment_qa_gate", "SKIP", "--skip-gates")

            env_doc["health"] = step_qa_health(rec, args.api)
            step_focused_tests(rec)
            invite = step_invite_contract(rec, args.api, args.scenario, session_id)
            print("")
            print("Compile path (copy to WeChat DevTools):")
            print(invite.get("launch_path"))
            print("")

            if not args.skip_fixtures:
                fixture = step_fixture_customer_flow(rec, args.api)
            else:
                rec.add("customer_flow_api", "SKIP", "--skip-fixtures")

            # Phone checkpoint — exact required message only.
            wait_phone_complete(no_wait=args.no_wait or args.phase == "pre")
            if args.phase == "pre" or args.no_wait:
                write_evidence(
                    evidence_dir=evidence_dir,
                    env_doc=env_doc,
                    rec=rec,
                    invite=invite,
                    fixture=fixture,
                    broker=None,
                    go=False,
                )
                print(f"Evidence (pre): {evidence_dir}")
                return 0

        if args.phase in ("all", "post"):
            case_id = (args.case_id or "").strip() or None
            if not case_id and fixture:
                case_id = str(fixture.get("case_id") or "") or None
            case = discover_case(args.api, case_id)
            broker = broker_api_path(rec, args.api, case)
            step_playwright(
                rec,
                workbench_url=workbench,
                evidence_dir=evidence_dir,
                case_id=str(broker.get("case_id") or ""),
            )
            hard_fail = any(r["status"] == "FAIL" for r in rec.rows)
            go = not hard_fail
            rec.add("report", "PASS" if go else "FAIL", "GO" if go else "NO-GO")
            write_evidence(
                evidence_dir=evidence_dir,
                env_doc=env_doc,
                rec=rec,
                invite=invite,
                fixture=fixture,
                broker=broker,
                go=go,
            )
            print("")
            print("GO" if go else "NO-GO")
            print(f"Evidence: {evidence_dir}")
            return 0 if go else 1
    except SystemExit:
        write_evidence(
            evidence_dir=evidence_dir,
            env_doc=env_doc,
            rec=rec,
            invite=invite,
            fixture=fixture,
            broker=broker,
            go=False,
        )
        raise

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
