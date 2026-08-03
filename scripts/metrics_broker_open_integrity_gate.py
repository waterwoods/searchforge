#!/usr/bin/env python3
"""Metrics V1 integrity gate — broker_first_opened must not be created by reads.

Cloud QA only. Creates one fresh isolated case, proves read-only ops stay clean,
then stamps via dedicated activity POST (Workbench contract).
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CLOUD_QA_API = "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app"
PRODUCTION_API = "https://fiqa-api-g7zatxrycq-uw.a.run.app"


def _utc() -> str:
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
    import urllib.error
    import urllib.request

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
        self.rows.append({"step": name, "status": status, "detail": detail, "at": _utc()})
        print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))

    def failed(self) -> bool:
        return any(r["status"] == "FAIL" for r in self.rows)


def _api_headers() -> dict[str, str]:
    key = (os.getenv("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    h = {"Accept": "application/json", "X-Case-Activity-Record": "0"}
    if key:
        h["X-Unified-Intake-Api-Key"] = key
    return h


def _support_headers() -> dict[str, str]:
    key = (os.getenv("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    h = {"Accept": "application/json"}
    if key:
        h["X-Unified-Intake-Support-Key"] = key
    return h


def _timing_blank(case: dict[str, Any], field: str) -> bool:
    bag = case.get("case_activity_timing") if isinstance(case.get("case_activity_timing"), dict) else {}
    return not str(case.get(field) or "").strip() and not str(bag.get(field) or "").strip()


def main() -> int:
    _load_qa_env()
    api = CLOUD_QA_API
    _assert_qa(api)
    rec = Rec()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "docs" / "evidence" / "real-usage-timing-v1" / f"{stamp}-integrity"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Isolated demo invite + start-claim (support issue path, same as Stage 2 preflight)
    session_id = f"wx_integrity_{uuid.uuid4().hex[:16]}"
    sh = _support_headers()
    code, issued = _http(
        "POST",
        f"{api}/api/inbox/support/demo-invite/issue",
        headers=sh,
        body={"office_id": "chen_kui", "scenario_id": "chen_camry"},
    )
    if code >= 400 or not isinstance(issued, dict) or not issued.get("token"):
        rec.add("issue_invite", "FAIL", f"http={code} body={str(issued)[:200]}")
        _write(out_dir, rec, {})
        return 1
    rec.add("issue_invite", "PASS", f"invite={issued.get('invite_id')}")
    token = str(issued["token"])
    code, redeem = _http(
        "POST",
        f"{api}/api/h5/demo-invite/redeem",
        headers=_api_headers(),
        body={"token": token, "session_id": session_id, "office_id": "chen_kui"},
    )
    if code >= 400:
        rec.add("redeem", "FAIL", f"http={code}")
        _write(out_dir, rec, {})
        return 1
    rec.add("redeem", "PASS")

    cmd = f"cmd_integrity_{uuid.uuid4().hex[:12]}"
    start_body = {
        "command_id": cmd,
        "idempotency_key": cmd,
        "session_id": session_id,
        "accident_description": "Integrity gate Camry rear-end in parking lot, no injuries.",
        "accident_datetime": "yesterday afternoon",
        "accident_location": "San Jose parking lot",
        "injury_status": "no",
        "is_test": True,
        "policy_context_choice": "CONFIRM_EXISTING",
    }
    code, start = _http(
        "POST",
        f"{api}/api/h5/customer/start-claim",
        headers=_api_headers(),
        body=start_body,
    )
    if code >= 400 or not isinstance(start, dict) or not start.get("ok"):
        rec.add("start_claim", "FAIL", f"http={code} body={str(start)[:200]}")
        _write(out_dir, rec, {"start": start})
        return 1
    resume_token = str(start.get("resume_token") or "")
    rec.add("start_claim", "PASS", f"outcome={start.get('outcome')}")

    # Resolve case_id via intake info
    if not resume_token:
        rec.add("resume_token", "FAIL", "missing resume_token")
        _write(out_dir, rec, {"start": start})
        return 1
    code, intake = _http("GET", f"{api}/api/h5/tasks/{resume_token}/intake", headers=_api_headers())
    if code >= 400 or not isinstance(intake, dict):
        rec.add("intake_info", "FAIL", f"http={code}")
        _write(out_dir, rec, {})
        return 1
    case_id = str(intake.get("case_id") or "").strip()
    if not case_id:
        rec.add("case_id", "FAIL", "missing from intake")
        _write(out_dir, rec, {"intake": intake})
        return 1
    rec.add("case_id", "PASS", case_id)

    # 2) Before broker UI open — timing blank on GET
    code, case0 = _http("GET", f"{api}/api/inbox/cases/{case_id}", headers=_api_headers())
    if code >= 400 or not isinstance(case0, dict):
        rec.add("get_before_open", "FAIL", f"http={code}")
        _write(out_dir, rec, {})
        return 1
    if not _timing_blank(case0, "broker_first_opened_at"):
        rec.add("blank_before_open", "FAIL", f"already set: {case0.get('broker_first_opened_at')}")
    else:
        rec.add("blank_before_open", "PASS")
    # Snapshot customer stamps after create (customer path may already stamp open/action).
    cust_open_0 = str(case0.get("customer_intake_opened_at") or "")
    cust_act_0 = str(case0.get("customer_first_action_at") or "")

    # 3) Read-only / support operations
    from tools.export_case_value_metrics import compute_case_value_metrics, fetch_case

    exported = fetch_case(api, case_id)
    row = compute_case_value_metrics(exported)
    if row.get("broker_first_opened_at"):
        rec.add("exporter_blank", "FAIL", row["broker_first_opened_at"])
    else:
        rec.add("export_blank", "PASS")

    # Second GET (script/API inspection)
    code, case1 = _http("GET", f"{api}/api/inbox/cases/{case_id}", headers=_api_headers())
    if code >= 400:
        rec.add("get_again", "FAIL", f"http={code}")
    elif not _timing_blank(case1 if isinstance(case1, dict) else {}, "broker_first_opened_at"):
        rec.add("get_again_no_stamp", "FAIL", str((case1 or {}).get("broker_first_opened_at")))
    else:
        rec.add("get_again_no_stamp", "PASS")

    # Support manifest / inspection if available
    code, _manifest = _http(
        "GET",
        f"{api}/api/inbox/support/deployment-manifest",
        headers=_support_headers(),
    )
    rec.add("support_manifest", "PASS" if code < 400 else "WARN", f"http={code}")

    code, case2 = _http("GET", f"{api}/api/inbox/cases/{case_id}", headers=_api_headers())
    case2 = case2 if isinstance(case2, dict) else {}
    if not _timing_blank(case2, "broker_first_opened_at"):
        rec.add("after_readonly_still_blank", "FAIL", str(case2.get("broker_first_opened_at")))
    else:
        rec.add("after_readonly_still_blank", "PASS")

    # Customer stamps must not appear solely from broker GETs if they were blank
    # (If start-claim already stamped them, values may be non-blank — that is customer path.)
    cust_open_1 = str(case2.get("customer_intake_opened_at") or "")
    cust_act_1 = str(case2.get("customer_first_action_at") or "")
    if not cust_open_0 and cust_open_1:
        rec.add("readonly_no_customer_open", "FAIL", "GET created customer_intake_opened")
    else:
        rec.add("readonly_no_customer_open", "PASS", "unchanged_or_preexisting")
    if not cust_act_0 and cust_act_1:
        rec.add("readonly_no_customer_action", "FAIL", "GET created customer_first_action")
    else:
        rec.add("readonly_no_customer_action", "PASS", "unchanged_or_preexisting")

    # 4) Dedicated Workbench activity POST (simulates successful detail render)
    post_headers = {**_api_headers()}
    post_headers.pop("X-Case-Activity-Record", None)
    code, act1 = _http(
        "POST",
        f"{api}/api/inbox/cases/{case_id}/activity/broker-first-opened",
        headers=post_headers,
        body={},
    )
    if code >= 400 or not isinstance(act1, dict) or not act1.get("ok"):
        rec.add("activity_post", "FAIL", f"http={code} body={str(act1)[:240]}")
        _write(out_dir, rec, {"case_id": case_id, "act1": act1})
        return 1
    ts1 = str(act1.get("broker_first_opened_at") or act1.get("created_at") or "")
    if not ts1.endswith("Z") or "T" not in ts1:
        rec.add("server_timestamp", "FAIL", ts1)
    else:
        rec.add("server_timestamp", "PASS", ts1)
    if str(act1.get("actor_role") or "") != "broker":
        rec.add("actor_role", "FAIL", str(act1.get("actor_role")))
    else:
        rec.add("actor_role", "PASS", "broker")
    if str(act1.get("source_surface") or "") != "broker_workbench":
        rec.add("source_surface", "FAIL", str(act1.get("source_surface")))
    else:
        rec.add("source_surface", "PASS", "broker_workbench")
    if not act1.get("recorded"):
        rec.add("first_record", "FAIL", "expected recorded=true on first post")
    else:
        rec.add("first_record", "PASS")

    # 5) Idempotent reopen
    code, act2 = _http(
        "POST",
        f"{api}/api/inbox/cases/{case_id}/activity/broker-first-opened",
        headers=post_headers,
        body={},
    )
    ts2 = str((act2 or {}).get("broker_first_opened_at") or (act2 or {}).get("created_at") or "") if isinstance(act2, dict) else ""
    if ts2 != ts1:
        rec.add("idempotent_reopen", "FAIL", f"{ts1} vs {ts2}")
    else:
        rec.add("idempotent_reopen", "PASS", ts2)
    if isinstance(act2, dict) and not act2.get("duplicate") and act2.get("recorded"):
        rec.add("duplicate_flag", "FAIL", str(act2))
    else:
        rec.add("duplicate_flag", "PASS")

    # 6) Exporter returns same timestamp (still read-only GET)
    exported2 = fetch_case(api, case_id)
    row2 = compute_case_value_metrics(exported2)
    if row2.get("broker_first_opened_at") != ts1:
        rec.add("export_matches", "FAIL", f"{row2.get('broker_first_opened_at')} vs {ts1}")
    else:
        rec.add("export_matches", "PASS", ts1)

    # 7) GET still does not create customer events beyond preexisting; no PII in activity response
    safe_keys = set(act1.keys())
    banned = {"accident_description", "raw_token", "token", "openid", "person_link_key", "customer_phone"}
    if safe_keys & banned:
        rec.add("no_pii_payload", "FAIL", str(safe_keys & banned))
    else:
        rec.add("no_pii_payload", "PASS")

    # Final GET after export
    code, case3 = _http("GET", f"{api}/api/inbox/cases/{case_id}", headers=_api_headers())
    case3 = case3 if isinstance(case3, dict) else {}
    if str(case3.get("broker_first_opened_at") or "") not in (ts1, ""):
        # attach may surface the field
        bag = case3.get("case_activity_timing") if isinstance(case3.get("case_activity_timing"), dict) else {}
        if str(bag.get("broker_first_opened_at") or "") != ts1 and str(case3.get("broker_first_opened_at") or "") != ts1:
            rec.add("get_after_stamp", "FAIL", str(case3.get("broker_first_opened_at")))
        else:
            rec.add("get_after_stamp", "PASS", ts1)
    else:
        rec.add("get_after_stamp", "PASS", str(case3.get("broker_first_opened_at") or ts1))

    evidence = {
        "case_id": case_id,
        "session_id_prefix": session_id[:24],
        "broker_first_opened_at": ts1,
        "export_row": row2,
        "activity_first": {k: act1.get(k) for k in ("ok", "recorded", "duplicate", "created_at", "actor_role", "source_surface", "schema_version")},
        "activity_second": {k: (act2 or {}).get(k) for k in ("ok", "recorded", "duplicate", "created_at")} if isinstance(act2, dict) else {},
        "steps": rec.rows,
        "verdict": "PASS" if not rec.failed() else "FAIL",
        "at": _utc(),
    }
    _write(out_dir, rec, evidence)
    print(f"\nEvidence: {out_dir}")
    print("VERDICT:", evidence["verdict"])
    return 1 if rec.failed() else 0


def _write(out_dir: Path, rec: Rec, evidence: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "steps.json").write_text(json.dumps(rec.rows, indent=2) + "\n", encoding="utf-8")
    payload = dict(evidence)
    payload.setdefault("steps", rec.rows)
    (out_dir / "integrity-report.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Metrics broker_first_opened integrity",
        "",
        f"- Verdict: **{payload.get('verdict', 'UNKNOWN')}**",
        f"- Case: `{payload.get('case_id', '')}`",
        f"- broker_first_opened_at: `{payload.get('broker_first_opened_at', '')}`",
        "",
        "## Steps",
        "",
    ]
    for row in rec.rows:
        md.append(f"- [{row['status']}] {row['step']}: {row.get('detail', '')}")
    (out_dir / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
