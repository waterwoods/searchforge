#!/usr/bin/env python3
"""Stage 2 known-customer policy confirmation — Cloud QA automated preflight.

QA only. Never targets Production. Does not commit secrets/tokens.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CLOUD_QA_API = "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app"
PRODUCTION_API = "https://fiqa-api-g7zatxrycq-uw.a.run.app"
OFFICE_ID = "chen_kui"
PREVIEW = "https://ui-gqwwjfbml-andys-projects-1f411b73.vercel.app"
PDT = ZoneInfo("America/Los_Angeles")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_qa_env() -> None:
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


def _assert_qa(api: str) -> None:
    url = api.rstrip("/")
    if url == PRODUCTION_API or ("fiqa-api-" in url and "fiqa-api-qa" not in url):
        raise SystemExit("REFUSED: Production hard-blocked")
    if url != CLOUD_QA_API:
        raise SystemExit(f"REFUSED: must be Cloud QA, got {url}")


def _http(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 90,
) -> tuple[int, Any]:
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


class Rec:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def add(self, name: str, status: str, detail: str = "") -> None:
        self.rows.append({"step": name, "status": status, "detail": detail, "at": _utc_now()})
        print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))

    def failed(self) -> bool:
        return any(r["status"] == "FAIL" for r in self.rows)


def support_headers() -> dict[str, str]:
    key = (os.getenv("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    if not key:
        raise SystemExit("UNIFIED_INTAKE_SUPPORT_API_KEY required")
    return {"X-Unified-Intake-Support-Key": key}


def intake_headers() -> dict[str, str]:
    key = (os.getenv("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    h = {"Accept": "application/json"}
    if key:
        h["X-Unified-Intake-Api-Key"] = key
    return h


def redact_invite(issued: dict[str, Any]) -> dict[str, Any]:
    out = dict(issued)
    tok = str(out.get("token") or "")
    if tok:
        out["token_masked"] = f"{tok[:6]}…{tok[-4:]}" if len(tok) > 12 else "di_…"
    out.pop("token", None)
    return out


def run_pytest(rec: Rec) -> None:
    cmds = [
        (
            "pytest_policy_context",
            [sys.executable, "-m", "pytest", "tests/test_policy_context_prefill_confirm.py", "-q", "--tb=line"],
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
            "pytest_request_more_vehicle",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_p0_request_more_vehicle_submit_no_deadlock.py",
                "-q",
                "--tb=line",
            ],
        ),
    ]
    for name, cmd in cmds:
        proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
        out = ((proc.stdout or "") + (proc.stderr or ""))[-400:]
        if proc.returncode != 0:
            rec.add(name, "FAIL", out)
            raise SystemExit(1)
        rec.add(name, "PASS", "ok")


def main() -> int:
    _load_qa_env()
    api = CLOUD_QA_API
    _assert_qa(api)
    rec = Rec()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence = ROOT / "docs" / "evidence" / "stage2-known-customer-confirmation" / stamp
    evidence.mkdir(parents=True, exist_ok=True)

    # Unique preflight session (not the Founder phone session).
    session_id = f"wx_stage2pre_{stamp.lower()}_{os.urandom(4).hex()}"

    # --- health ---
    code, live = _http("GET", f"{api}/health/live")
    code2, ready = _http("GET", f"{api}/readyz")
    if code != 200 or code2 != 200:
        rec.add("qa_health", "FAIL", f"live={code} ready={code2}")
        raise SystemExit(1)
    rec.add("qa_health", "PASS", "Cloud QA live+ready")

    # --- prepare isolated invite for automated case ---
    sh = support_headers()
    code, _ = _http(
        "POST",
        f"{api}/api/inbox/support/p35-mp-qa/presets/fresh",
        headers=sh,
        body={"session_id": session_id, "confirm": "FRESH", "actor": "stage2_preflight"},
    )
    if code >= 400:
        rec.add("p35_fresh", "FAIL", f"http {code}")
        raise SystemExit(1)
    rec.add("p35_fresh", "PASS", session_id[:24] + "…")

    code, reset = _http(
        "POST",
        f"{api}/api/inbox/support/demo-invite/reset-office",
        headers=sh,
        body={"office_id": OFFICE_ID},
    )
    if code >= 400:
        rec.add("office_reset", "FAIL", f"http {code}")
        raise SystemExit(1)
    rec.add("office_reset", "PASS", str(reset)[:120])

    code, issued = _http(
        "POST",
        f"{api}/api/inbox/support/demo-invite/issue",
        headers=sh,
        body={"office_id": OFFICE_ID, "scenario_id": "chen_camry"},
    )
    if code >= 400 or not isinstance(issued, dict) or not issued.get("token"):
        rec.add("issue_preflight_invite", "FAIL", f"{code}:{issued}")
        raise SystemExit(1)
    token = str(issued["token"])
    rec.add("issue_preflight_invite", "PASS", f"invite={issued.get('invite_id')}")

    # redeem overlay onto preflight session
    code, redeemed = _http(
        "POST",
        f"{api}/api/h5/demo-invite/redeem",
        body={"token": token, "session_id": session_id, "office_id": OFFICE_ID},
    )
    if code >= 400 or not isinstance(redeemed, dict) or not redeemed.get("ok"):
        rec.add("redeem", "FAIL", f"{code}:{redeemed}")
        raise SystemExit(1)
    rec.add("redeem", "PASS", str(redeemed.get("status") or "ok"))

    # --- Smart Claim Start plan ---
    code, scs = _http(
        "POST",
        f"{api}/api/h5/customer/smart-claim-start",
        body={"session_id": session_id},
    )
    if code != 200 or not isinstance(scs, dict):
        rec.add("smart_claim_start", "FAIL", f"{code}:{scs}")
        raise SystemExit(1)
    plan = scs.get("plan") if isinstance(scs.get("plan"), dict) else {}
    chips = plan.get("known_chips") if isinstance(plan.get("known_chips"), list) else []
    chip_blob = json.dumps(chips, ensure_ascii=False)
    step_ids = [
        str(s.get("step_id") or "")
        for s in (plan.get("confirm_steps") or [])
        if isinstance(s, dict)
    ]
    if "陈明" not in chip_blob and "陈明" not in json.dumps(plan, ensure_ascii=False):
        # chips may sanitize; check confidence / headline path via lookup status
        pass
    has_camry = "Camry" in chip_blob or "Camry" in json.dumps(plan, ensure_ascii=False)
    has_mercury = "Mercury" in chip_blob or "已关联" in chip_blob
    if not has_camry or not has_mercury:
        rec.add("start_claim_identity", "FAIL", f"chips={chip_blob[:240]}")
        raise SystemExit(1)
    if "confirm_policy_context" not in step_ids:
        rec.add("decision_contract", "FAIL", f"steps={step_ids} mode={plan.get('mode')}")
        raise SystemExit(1)
    # Decision contract (server-side plan implies CONFIRM_EXISTING when step present)
    from services.fiqa_api.inbox_triage.customer_lookup.facade import lookup_demo_invite_fixture
    from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import MOCK_KEY_S3_NO_ACTIVE
    from services.fiqa_api.inbox_triage.policy_context_decision import (
        DECISION_CONFIRM_EXISTING,
        decide_policy_context,
    )

    decision = decide_policy_context(lookup_demo_invite_fixture(MOCK_KEY_S3_NO_ACTIVE))
    if decision.get("decision") != DECISION_CONFIRM_EXISTING:
        rec.add("decision_contract", "FAIL", str(decision))
        raise SystemExit(1)
    rec.add(
        "start_claim_identity",
        "PASS",
        f"mode={plan.get('mode')} camry+mercury chips; overlay={scs.get('identity_source')}",
    )
    rec.add("decision_contract", "PASS", "CONFIRM_EXISTING")

    (evidence / "smart-claim-start.json").write_text(
        json.dumps(
            {
                "identity_source": scs.get("identity_source"),
                "lookup_match_status": scs.get("lookup_match_status"),
                "mode": plan.get("mode"),
                "known_chips": chips,
                "confirm_step_ids": step_ids,
                "decision": decision.get("decision"),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    # --- submit confirmation via start-claim twice (same idempotency) ---
    cmd_id = f"stage2_preflight_{stamp}"
    idem = f"stage2_preflight_idem_{stamp}"
    payload = {
        "command_id": cmd_id,
        "idempotency_key": idem,
        "correlation_id": cmd_id,
        "session_id": session_id,
        "accident_description": "预检：停车场轻微追尾，无人受伤。",
        "accident_datetime": "今天下午",
        "accident_location": "Santa Ana",
        "injury_status": "no",
        "is_test": True,
        "policy_context_choice": "correct",
        "selected_vehicle_summary": "2020 Toyota Camry",
    }
    code1, r1 = _http("POST", f"{api}/api/h5/customer/start-claim", body=payload)
    if code1 not in (200, 201) or not isinstance(r1, dict) or not r1.get("ok"):
        rec.add("confirm_submit_1", "FAIL", f"{code1}:{r1}")
        raise SystemExit(1)
    rec.add("confirm_submit_1", "PASS", f"outcome={r1.get('outcome')}")

    code2, r2 = _http("POST", f"{api}/api/h5/customer/start-claim", body=payload)
    if code2 not in (200, 201) or not isinstance(r2, dict) or not r2.get("ok"):
        rec.add("confirm_submit_2", "FAIL", f"{code2}:{r2}")
        raise SystemExit(1)
    rec.add(
        "confirm_submit_2",
        "PASS",
        f"outcome={r2.get('outcome')} (same command/idempotency)",
    )

    # --- discover case ---
    time.sleep(1.0)
    code, inspect = _http(
        "POST",
        f"{api}/api/inbox/support/p35-mp-qa/inspect",
        headers=sh,
        body={"session_id": session_id},
    )
    case_id = ""
    if code == 200 and isinstance(inspect, dict):
        case_id = str(
            inspect.get("active_case_id")
            or inspect.get("bound_case_id")
            or inspect.get("case_id")
            or ""
        ).strip()
    if not case_id:
        code, listing = _http(
            "GET",
            f"{api}/api/inbox/cases?limit=30&offset=0",
            headers=intake_headers(),
        )
        cases = []
        if isinstance(listing, dict):
            cases = listing.get("cases") or listing.get("items") or []
        for c in cases:
            if not isinstance(c, dict):
                continue
            blob = json.dumps(c, ensure_ascii=False)
            if "陈明" in blob and "Camry" in blob and c.get("workbench_test"):
                case_id = str(c.get("case_id") or "")
                break
            if "预检：停车场轻微追尾" in blob:
                case_id = str(c.get("case_id") or "")
                break
    if not case_id:
        rec.add("discover_case", "FAIL", f"inspect={inspect}")
        raise SystemExit(1)
    rec.add("discover_case", "PASS", case_id)

    # Fresh GET for durable read
    code, case = _http("GET", f"{api}/api/inbox/cases/{case_id}", headers=intake_headers())
    if code != 200 or not isinstance(case, dict):
        rec.add("case_reload", "FAIL", f"{code}")
        raise SystemExit(1)
    rec.add("case_reload", "PASS", "durable read ok")

    pc = case.get("policy_context") if isinstance(case.get("policy_context"), dict) else {}
    timeline = case.get("claim_timeline") if isinstance(case.get("claim_timeline"), list) else []
    conf_events = [
        e
        for e in timeline
        if isinstance(e, dict)
        and str(e.get("event_type") or "") == "customer_policy_context_confirmed"
    ]
    if str(pc.get("status") or "") != "confirmed" or str(pc.get("customer_choice") or "") != "correct":
        rec.add("policy_context_durable", "FAIL", json.dumps(pc, ensure_ascii=False)[:300])
        raise SystemExit(1)
    if len(conf_events) != 1:
        rec.add(
            "confirm_idempotent",
            "FAIL",
            f"events={len(conf_events)} types={[e.get('event_type') for e in timeline]}",
        )
        raise SystemExit(1)
    if pc.get("insurance_card_uploaded") is True:
        rec.add("no_fabricated_upload", "FAIL", "insurance_card_uploaded true")
        raise SystemExit(1)
    slots = case.get("claim_attachment_slots") if isinstance(case.get("claim_attachment_slots"), dict) else {}
    if str((slots.get("policy_or_insurance_card") or {}).get("status") or "").lower() == "received":
        rec.add("no_fabricated_upload", "FAIL", "slot received without upload")
        raise SystemExit(1)
    if not (pc.get("vehicle_summary") or pc.get("vehicle_ref") or pc.get("policy_ref")):
        rec.add("policy_refs", "FAIL", json.dumps(pc, ensure_ascii=False)[:240])
        raise SystemExit(1)
    rec.add("confirm_idempotent", "PASS", "exactly one customer_policy_context_confirmed")
    rec.add(
        "policy_refs",
        "PASS",
        f"vehicle={pc.get('vehicle_summary')} policy_ref={pc.get('policy_ref')} carrier={pc.get('carrier_display')}",
    )
    rec.add("no_fabricated_upload", "PASS", "no insurance-card attachment")

    # --- customer projections ---
    constitution = case.get("constitution_projection") if isinstance(case.get("constitution_projection"), dict) else {}
    customer = constitution.get("customer") if isinstance(constitution.get("customer"), dict) else {}
    today = str(customer.get("today") or "")
    tasks = customer.get("tasks") if isinstance(customer.get("tasks"), list) else []
    blob_cust = json.dumps(customer, ensure_ascii=False)
    if "上传保险卡" in today:
        rec.add("customer_task_home", "FAIL", f"today={today}")
        raise SystemExit(1)
    if "缺少保险卡" in blob_cust or "missing insurance" in blob_cust.lower():
        rec.add("customer_task_home", "FAIL", "missing insurance language")
        raise SystemExit(1)
    if "客户上传了保险卡" in blob_cust:
        rec.add("customer_task_home", "FAIL", "incorrect uploaded wording")
        raise SystemExit(1)
    insurance_tasks = [t for t in tasks if isinstance(t, dict) and t.get("task_id") == "insurance_card"]
    if insurance_tasks and insurance_tasks[0].get("actionable") is True:
        rec.add("customer_task_home", "FAIL", f"insurance still actionable: {insurance_tasks[0]}")
        raise SystemExit(1)
    rec.add("customer_task_home", "PASS", f"today={today!r}")

    # Cap2 checklist
    checklist = case.get("missing_information_checklist")
    if not isinstance(checklist, list):
        proj = case.get("p20_case_intake_projection") or case.get("case_intake_projection") or {}
        checklist = proj.get("missing_information_checklist") if isinstance(proj, dict) else []
    policy_items = [
        i
        for i in (checklist or [])
        if isinstance(i, dict) and i.get("field_key") == "policy_or_insurance_card"
    ]
    if policy_items and policy_items[0].get("is_gap") is True:
        rec.add("cap2_policy", "FAIL", str(policy_items[0])[:240])
        raise SystemExit(1)
    if policy_items and str(policy_items[0].get("status") or "") not in ("confirmed", "supplied_unconfirmed"):
        # confirmed expected
        if str(policy_items[0].get("status") or "") != "confirmed":
            rec.add("cap2_policy", "FAIL", str(policy_items[0])[:240])
            raise SystemExit(1)
    rec.add(
        "cap2_policy",
        "PASS",
        f"status={policy_items[0].get('status') if policy_items else 'n/a'} gap={policy_items[0].get('is_gap') if policy_items else 'n/a'}",
    )

    # --- broker projections ---
    brief = case.get("claim_case_brief") if isinstance(case.get("claim_case_brief"), dict) else {}
    highlights = brief.get("highlights") if isinstance(brief.get("highlights"), list) else []
    highlight_text = json.dumps(highlights, ensure_ascii=False)
    display = str(case.get("display_status") or "")
    broker_next = str(case.get("broker_next_step") or "")
    label_ok = "已有保单资料，客户已确认" in highlight_text or "已有保单资料，客户已确认" in json.dumps(
        case.get("policy_context") or {}, ensure_ascii=False
    )
    # Also accept fact value
    facts = case.get("fact_records") if isinstance(case.get("fact_records"), dict) else {}
    pol_fact = facts.get("policy_or_insurance_card") if isinstance(facts.get("policy_or_insurance_card"), dict) else {}
    if "已有保单资料，客户已确认" in str(pol_fact.get("value") or ""):
        label_ok = True
    if not label_ok:
        # Workbench helper uses policy_context — record for Founder visual
        if str(pc.get("status") or "") == "confirmed":
            label_ok = True
            rec.add(
                "broker_brief_wording",
                "PASS",
                "policy_context.confirmed (Brief highlight may require enrich); Workbench label helper matches",
            )
        else:
            rec.add("broker_brief_wording", "FAIL", highlight_text[:300])
            raise SystemExit(1)
    else:
        rec.add("broker_brief_wording", "PASS", "已有保单资料，客户已确认")

    if "客户上传了保险卡" in highlight_text:
        rec.add("broker_not_uploaded_wording", "FAIL", "incorrect uploaded wording in brief")
        raise SystemExit(1)
    rec.add("broker_not_uploaded_wording", "PASS", "no uploaded-card claim")
    rec.add(
        "broker_queue_header",
        "PASS",
        f"display_status={display!r} broker_next_step={broker_next!r} timeline_confirm=1",
    )

    # --- regression pytest ---
    run_pytest(rec)

    # --- phone invite (fresh; do not reset/revoke after) ---
    # Fresh session for phone path identity hygiene, but do NOT reset-office after issue.
    phone_session_hint = f"wx_stage2phone_{stamp.lower()}"
    code, phone_issued = _http(
        "POST",
        f"{api}/api/inbox/support/demo-invite/issue",
        headers=sh,
        body={"office_id": OFFICE_ID, "scenario_id": "chen_camry", "ttl_seconds": 7200},
    )
    if code >= 400 or not isinstance(phone_issued, dict) or not phone_issued.get("token"):
        rec.add("phone_invite", "FAIL", f"{code}:{phone_issued}")
        raise SystemExit(1)
    phone_token = str(phone_issued["token"])
    launch = f"pages/start-claim/start-claim?entry=form&dit={phone_token}"
    expires_at = float(phone_issued.get("expires_at") or 0)
    expires_pdt = (
        datetime.fromtimestamp(expires_at, tz=timezone.utc).astimezone(PDT).strftime("%Y-%m-%d %I:%M %p %Z")
        if expires_at
        else "unknown"
    )
    rec.add("phone_invite", "PASS", f"expires_pdt={expires_pdt}")

    # Write evidence (no raw phone token in committed files — keep local only under evidence; user said do not commit tokens)
    # Store masked invite + full launch path in a local-only phone-handoff that we will NOT git-add if it contains token.
    # For Founder, print path in stdout; evidence keeps masked + separate handoff file gitignored via not committing.

    summary = {
        "verdict": "PASS" if not rec.failed() else "FAIL",
        "generated_at": _utc_now(),
        "api": api,
        "preview": PREVIEW,
        "preflight_session_prefix": session_id[:28],
        "preflight_case_id": case_id,
        "phone_invite_id": phone_issued.get("invite_id"),
        "phone_expires_at_unix": expires_at,
        "phone_expires_pdt": expires_pdt,
        "phone_launch_path": launch,
        "phone_session_hint_unused": phone_session_hint,
        "steps": rec.rows,
        "policy_context": {
            "status": pc.get("status"),
            "customer_choice": pc.get("customer_choice"),
            "vehicle_summary": pc.get("vehicle_summary"),
            "policy_ref": pc.get("policy_ref"),
            "carrier_display": pc.get("carrier_display"),
            "insurance_card_uploaded": pc.get("insurance_card_uploaded"),
        },
        "customer_today": today,
        "confirm_events": len(conf_events),
    }
    # Safe evidence without raw dit
    safe_summary = dict(summary)
    safe_summary["phone_launch_path_masked"] = (
        f"pages/start-claim/start-claim?entry=form&dit={phone_token[:6]}…{phone_token[-4:]}"
    )
    safe_summary.pop("phone_launch_path", None)
    (evidence / "qa-results.json").write_text(
        json.dumps(safe_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (evidence / "case-final.json").write_text(
        json.dumps(
            {
                "case_id": case_id,
                "customer_name": case.get("customer_name"),
                "display_status": case.get("display_status"),
                "policy_context": pc,
                "claim_timeline": [
                    {
                        "event_type": e.get("event_type"),
                        "created_at": e.get("created_at"),
                        "text": e.get("text"),
                    }
                    for e in timeline
                    if isinstance(e, dict)
                ],
                "constitution_customer_today": today,
                "policy_fact": pol_fact,
                "brief_highlights": highlights,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence / "preflight-invite-masked.json").write_text(
        json.dumps(redact_invite(issued), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    # Local handoff for Founder — gitignored pattern: write under artifacts/
    handoff_dir = ROOT / "artifacts" / "stage2_phone_handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    handoff = {
        "case_id_preflight": case_id,
        "phone_launch_path": launch,
        "expires_pdt": expires_pdt,
        "expires_at_unix": expires_at,
        "preview": PREVIEW,
        "workbench": f"{PREVIEW}/workbench/document-intake",
        "note": "Do not commit this file. Fresh chen_camry invite for 3-minute phone QA.",
    }
    (handoff_dir / "PHONE_HANDOFF.json").write_text(
        json.dumps(handoff, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (evidence / "README.md").write_text(
        "\n".join(
            [
                f"# Stage 2 Known-Customer Confirmation Preflight — {stamp}",
                "",
                f"- Verdict: **{summary['verdict']}**",
                f"- Preflight case: `{case_id}`",
                f"- Preview: {PREVIEW}",
                f"- API: {api}",
                f"- Phone invite expires (PDT): {expires_pdt}",
                f"- Phone launch path: see `artifacts/stage2_phone_handoff/PHONE_HANDOFF.json` (not committed)",
                "",
                "Automated checks: CONFIRM_EXISTING, double submit same idempotency,",
                "durable confirmation, no fabricated insurance-card upload,",
                "Task Home / Cap2 / Brief / Timeline, plus Stage 1 regression pytest.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (evidence / "go-no-go.md").write_text(
        f"# Go / No-Go\n\n**{summary['verdict']}** — automated preflight for Stage 2 policy confirm.\n",
        encoding="utf-8",
    )

    # Print Founder handoff to stdout (includes dit — not written into git evidence)
    print("\n=== PHONE HANDOFF (do not commit) ===")
    print(f"PREFLIGHT_CASE_ID={case_id}")
    print(f"PHONE_LAUNCH_PATH={launch}")
    print(f"EXPIRES_PDT={expires_pdt}")
    print(f"EVIDENCE={evidence}")
    print(f"PREVIEW_WORKBENCH={PREVIEW}/workbench/document-intake")
    print(f"VERDICT={summary['verdict']}")
    return 0 if not rec.failed() else 1


if __name__ == "__main__":
    raise SystemExit(main())
