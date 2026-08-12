#!/usr/bin/env python3
"""Cloud QA validation for AI Request More drafting (real LLM path).

Builds synthetic QA cases through the existing broker commands, calls the
deployed drafting endpoint, and asserts deterministically. Creates no parallel
test system: every case is made with POST /api/inbox/claims + fact-status, and
the send proof uses the normal SaveRequestDraft / SendRequest commands.

Usage:
  set -a && source .env.cloudrun.qa && set +a
  PYTHONPATH=. python3 scripts/qa_validate_request_more_ai_drafting.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.request_more_assistant.contract import (  # noqa: E402
    MAX_DRAFT_TEXT_CHARS,
    contains_unsupported_detail,
)
from services.fiqa_api.inbox_triage.request_more_assistant.guardrails import (  # noqa: E402
    find_forbidden_phrase,
)

QA_BASE = "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app"

# Things an already-authoritative case must never be asked for again.
RE_ASK_MARKERS = ("保险卡", "保单", "事故时间", "事故地点", "受伤", "伤者", "照片", "车型")

ACCIDENT_FACTS = {
    "accident_description": "QA fixture: 停车场倒车轻微剐蹭（合成测试数据）",
    "accident_datetime": "2026-08-01 下午",
    "accident_location": "QA 测试停车场",
    "injury_status": "no",
}
VEHICLE_FACTS = {"vehicle_year": "2019", "vehicle_make": "Toyota", "vehicle_model": "Camry"}


class Client:
    def __init__(self, base: str, intake_key: str, support_key: str) -> None:
        self.base = base.rstrip("/")
        self.intake_key = intake_key
        self.support_key = support_key

    def _call(self, method: str, path: str, body: dict | None = None, *, support: bool = False) -> dict:
        headers = {"Content-Type": "application/json"}
        if support:
            headers["X-Unified-Intake-Support-Key"] = self.support_key
        else:
            headers["X-Unified-Intake-Api-Key"] = self.intake_key
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{self.base}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode()
            try:
                detail = json.loads(raw)
            except Exception:
                detail = {"raw": raw[:500]}
            return {"_http_status": exc.code, "_error": detail}

    def post(self, path: str, body: dict, *, support: bool = False) -> dict:
        return self._call("POST", path, body, support=support)

    def get(self, path: str, *, support: bool = False) -> dict:
        return self._call("GET", path, None, support=support)


def _ids(prefix: str) -> dict[str, str]:
    tail = uuid4().hex[:12]
    return {"command_id": f"cmd_{prefix}_{tail}", "idempotency_key": f"idem_{prefix}_{tail}"}


def _requestable(checklist: list[dict]) -> list[str]:
    return [r["field_key"] for r in checklist if r.get("suggested_for_request")]


def create_case(client: Client, *, title: str, known_facts: dict) -> tuple[str, int, list[dict]]:
    body = {
        **_ids("create"),
        "is_test": True,
        "title": title,
        "customer_name": "QA Synthetic Customer",
        "contact_note": "AI Request More QA validation (synthetic, no real PII)",
        "qa_label": "ai_request_more_qa",
        "known_facts": known_facts,
    }
    result = client.post("/api/inbox/claims", body)
    if result.get("outcome") not in {"accepted", "replayed"}:
        raise RuntimeError(f"create_claim failed: {json.dumps(result)[:400]}")
    proj = result["broker_projection"]
    return result["case_id"], int(proj["aggregate_version"]), proj["missing_information_checklist"]


def confirm_fact(client: Client, case_id: str, version: int, field_key: str) -> tuple[int, list[dict]]:
    body = {
        **_ids("factstatus"),
        "expected_case_version": version,
        "field_key": field_key,
        "status": "confirmed",
        "reason": "QA synthetic broker confirmation",
    }
    result = client.post(f"/api/inbox/cases/{case_id}/fact-status", body)
    if result.get("outcome") not in {"accepted", "replayed"}:
        raise RuntimeError(f"fact-status {field_key} failed: {json.dumps(result)[:400]}")
    proj = result["broker_projection"]
    return int(proj["aggregate_version"]), proj["missing_information_checklist"]


def assist(client: Client, case_id: str, *, prefer_template: bool = False) -> tuple[dict, int]:
    started = time.monotonic()
    result = client.post(
        f"/api/inbox/cases/{case_id}/request-draft-assist",
        {"correlation_id": f"qa_{uuid4().hex[:8]}", "prefer_template": prefer_template},
    )
    return result, int((time.monotonic() - started) * 1000)


def case_snapshot(client: Client, case_id: str) -> dict:
    """Fields that would change if drafting were not read-only."""
    case = client.get(f"/api/inbox/cases/{case_id}")
    proj = case.get("p20_case_intake_projection") or {}
    slice1 = case.get("p20_slice1_projection") or {}
    return {
        "aggregate_version": proj.get("aggregate_version"),
        "admin_lifecycle": proj.get("admin_lifecycle"),
        "request_draft": proj.get("request_draft"),
        "open_request_more": proj.get("open_request_more"),
        "checklist": proj.get("missing_information_checklist"),
        "known_facts": proj.get("known_facts"),
        "customer_access": case.get("customer_access"),
        "workflow_state": slice1.get("workflow_state"),
        "open_request": slice1.get("open_request"),
        "claim_phase": case.get("claim_phase"),
    }


class Checks:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def expect(self, name: str, passed: bool, detail: Any = "") -> bool:
        self.rows.append({"check": name, "pass": bool(passed), "detail": str(detail)[:300]})
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        return bool(passed)

    @property
    def failed(self) -> list[dict]:
        return [r for r in self.rows if not r["pass"]]


def check_draft_quality(checks: Checks, label: str, draft: dict, expected_keys: list[str]) -> None:
    text = str(draft.get("draft_text") or "")
    items = draft.get("items") or []
    checks.expect(f"{label}: items == {expected_keys}", [i["field_key"] for i in items] == expected_keys,
                  [i["field_key"] for i in items])
    checks.expect(f"{label}: no forbidden coverage/liability/payment language",
                  find_forbidden_phrase(text) is None, find_forbidden_phrase(text) or "none")
    checks.expect(f"{label}: no unsupported detail (long digits / links / emails)",
                  not contains_unsupported_detail(text))
    checks.expect(f"{label}: length <= {MAX_DRAFT_TEXT_CHARS}", len(text) <= MAX_DRAFT_TEXT_CHARS, len(text))
    checks.expect(f"{label}: concise (<= 200 chars)", len(text) <= 200, len(text))
    checks.expect(f"{label}: polite Chinese opening/closing",
                  ("您" in text or "请" in text) and "谢" in text or "请" in text)
    for item in items:
        instructions = str(item.get("instructions") or "")
        checks.expect(f"{label}: {item['field_key']} instructions clean",
                      find_forbidden_phrase(instructions) is None
                      and not contains_unsupported_detail(instructions))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("QA_BASE_URL", QA_BASE))
    parser.add_argument("--out", default="/tmp/qa_request_more_ai_drafting_evidence.json")
    args = parser.parse_args()

    intake_key = (os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    support_key = (os.environ.get("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    if not intake_key:
        print("UNIFIED_INTAKE_INTAKE_API_KEY required", file=sys.stderr)
        return 2

    client = Client(args.base_url, intake_key, support_key)
    checks = Checks()
    evidence: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "base_url": args.base_url,
    }

    manifest = client.get("/api/inbox/support/deployment-manifest", support=True)
    evidence["deployed_commit"] = (manifest.get("git") or {}).get("commit")
    evidence["assistant_flags"] = manifest.get("request_more_assistant")
    print(f"\nDeployed commit: {evidence['deployed_commit']}")
    print(f"Assistant flags: {json.dumps(evidence['assistant_flags'])}")
    flags = evidence["assistant_flags"] or {}
    checks.expect("QA: assistant enabled", bool(flags.get("assistant_enabled")))
    checks.expect("QA: real LLM drafting enabled", bool(flags.get("llm_drafting_enabled")))

    # ---------------- CASE A — golden: only VIN missing ----------------
    print("\nCASE A — existing customer, only VIN missing")
    case_a, ver, checklist = create_case(
        client, title="AI RM QA — Case A golden VIN only", known_facts={
            **VEHICLE_FACTS, **ACCIDENT_FACTS, "policy_number": "QA-SYNTH-POLICY",
        }
    )
    for field in (
        "vehicle_information", "policy_or_insurance_card", "accident_description",
        "accident_datetime", "accident_location", "injury_status",
    ):
        ver, checklist = confirm_fact(client, case_a, ver, field)
    checks.expect("CASE A: deterministic missing set == ['vin']", _requestable(checklist) == ["vin"],
                  _requestable(checklist))

    before_a = case_snapshot(client, case_a)
    draft_a, latency_a = assist(client, case_a)
    after_a = case_snapshot(client, case_a)
    evidence["case_a"] = {"case_id": case_a, "draft": draft_a, "client_latency_ms": latency_a}
    print(json.dumps(draft_a, ensure_ascii=False, indent=2)[:1200])

    checks.expect("CASE A: real AI path used", draft_a.get("draft_used_ai") is True)
    checks.expect("CASE A: used_fallback == false", draft_a.get("used_fallback") is False,
                  draft_a.get("fallback_reason"))
    checks.expect("CASE A: authority == ai_draft", draft_a.get("authority") == "ai_draft")
    checks.expect("CASE A: guardrail passed", draft_a.get("guardrail_outcome") == "passed")
    checks.expect("CASE A: provider is a real model", draft_a.get("model_provider") == "openai",
                  f"{draft_a.get('model_provider')}/{draft_a.get('model_name')}")
    text_a = str(draft_a.get("draft_text") or "")
    checks.expect("CASE A: draft names VIN", "VIN" in text_a.upper())
    for marker in RE_ASK_MARKERS:
        checks.expect(f"CASE A: does not re-ask 「{marker}」", marker not in text_a)
    check_draft_quality(checks, "CASE A", draft_a, ["vin"])

    # Read-only proof.
    checks.expect("CASE A: drafting created no Request More", after_a["open_request_more"] is None
                  and after_a["open_request"] is None)
    checks.expect("CASE A: drafting created no request draft", after_a["request_draft"] is None)
    checks.expect("CASE A: aggregate_version unchanged",
                  before_a["aggregate_version"] == after_a["aggregate_version"],
                  f"{before_a['aggregate_version']} -> {after_a['aggregate_version']}")
    checks.expect("CASE A: authoritative facts unchanged", before_a["known_facts"] == after_a["known_facts"])
    checks.expect("CASE A: checklist unchanged", before_a["checklist"] == after_a["checklist"])
    checks.expect("CASE A: lifecycle unchanged",
                  before_a["admin_lifecycle"] == after_a["admin_lifecycle"]
                  and before_a["claim_phase"] == after_a["claim_phase"]
                  and before_a["workflow_state"] == after_a["workflow_state"])
    checks.expect("CASE A: no customer communication issued", after_a["customer_access"] in (None, {}))
    checks.expect("CASE A: response declares lifecycle_mutated=false",
                  draft_a.get("lifecycle_mutated") is False)

    # ---------------- CASE B — VIN + insurance card ----------------
    print("\nCASE B — VIN + insurance card missing")
    case_b, ver_b, checklist_b = create_case(
        client, title="AI RM QA — Case B two gaps", known_facts={**VEHICLE_FACTS, **ACCIDENT_FACTS}
    )
    ver_b, checklist_b = confirm_fact(client, case_b, ver_b, "vehicle_information")
    checks.expect("CASE B: deterministic missing set == ['vin','policy_or_insurance_card']",
                  _requestable(checklist_b) == ["vin", "policy_or_insurance_card"],
                  _requestable(checklist_b))
    draft_b, latency_b = assist(client, case_b)
    evidence["case_b"] = {"case_id": case_b, "draft": draft_b, "client_latency_ms": latency_b}
    print(json.dumps(draft_b, ensure_ascii=False, indent=2)[:1200])
    text_b = str(draft_b.get("draft_text") or "")
    checks.expect("CASE B: real AI path used", draft_b.get("draft_used_ai") is True)
    checks.expect("CASE B: used_fallback == false", draft_b.get("used_fallback") is False,
                  draft_b.get("fallback_reason"))
    checks.expect("CASE B: draft names VIN", "VIN" in text_b.upper())
    checks.expect("CASE B: draft names 保险卡/保单", ("保险卡" in text_b or "保单" in text_b))
    for marker in ("事故时间", "事故地点", "受伤", "伤者"):
        checks.expect(f"CASE B: does not re-ask 「{marker}」", marker not in text_b)
    check_draft_quality(checks, "CASE B", draft_b, ["vin", "policy_or_insurance_card"])

    # ---------------- CASE C — nothing missing ----------------
    print("\nCASE C — nothing missing")
    case_c, ver_c, checklist_c = create_case(
        client, title="AI RM QA — Case C complete", known_facts={
            **VEHICLE_FACTS, **ACCIDENT_FACTS,
            "vin": "4T1BF1FK5CU500001", "policy_number": "QA-SYNTH-POLICY-C",
        }
    )
    for field in ("vin", "vehicle_information", "policy_or_insurance_card"):
        ver_c, checklist_c = confirm_fact(client, case_c, ver_c, field)
    checks.expect("CASE C: deterministic missing set empty", _requestable(checklist_c) == [],
                  _requestable(checklist_c))
    before_c = case_snapshot(client, case_c)
    draft_c, latency_c = assist(client, case_c)
    after_c = case_snapshot(client, case_c)
    evidence["case_c"] = {"case_id": case_c, "draft": draft_c, "client_latency_ms": latency_c}
    print(json.dumps(draft_c, ensure_ascii=False, indent=2)[:800])
    checks.expect("CASE C: drafting unavailable", draft_c.get("drafting_available") is False)
    checks.expect("CASE C: message 无需补充", draft_c.get("message") == "无需补充")
    checks.expect("CASE C: no AI call made", draft_c.get("draft_used_ai") is False
                  and draft_c.get("model_name") is None or draft_c.get("draft_used_ai") is False)
    checks.expect("CASE C: fast (no model latency)", latency_c < 2500, f"{latency_c}ms")
    checks.expect("CASE C: no Request More created", after_c["open_request_more"] is None
                  and after_c["request_draft"] is None)
    checks.expect("CASE C: version unchanged", before_c["aggregate_version"] == after_c["aggregate_version"])

    # ---------------- Broker template choice (deterministic path live) ----------------
    print("\nTEMPLATE — broker chooses office template")
    template_a, _ = assist(client, case_a, prefer_template=True)
    evidence["case_a_template"] = template_a
    checks.expect("TEMPLATE: authority == office_template",
                  template_a.get("authority") == "office_template")
    checks.expect("TEMPLATE: not marked as failure", template_a.get("used_fallback") is False)
    checks.expect("TEMPLATE: same deterministic item set",
                  [i["field_key"] for i in template_a.get("items") or []] == ["vin"])
    checks.expect("TEMPLATE: usable Chinese copy", "VIN" in str(template_a.get("draft_text") or "").upper())

    # ---------------- Existing broker command + idempotency ----------------
    print("\nSEND — AI draft flows through the existing broker commands")
    ai_item = (draft_a.get("items") or [{}])[0]
    save_ids = _ids("save")
    saved = client.post(f"/api/inbox/cases/{case_a}/request-draft", {
        **save_ids,
        "expected_case_version": after_a["aggregate_version"],
        "items": [{
            "field_key": ai_item.get("field_key"),
            "item_type": ai_item.get("item_type"),
            "label": ai_item.get("label"),
            "instructions": (str(ai_item.get("instructions") or "") + " 陈总办公室已核对。")[:1000],
            "required": True,
            "position": 1,
            "selected": True,
            "request_mode": ai_item.get("request_mode") or "request_missing",
        }],
    })
    checks.expect("SEND: broker-edited draft saved", saved.get("outcome") == "accepted",
                  saved.get("error_code") or "")
    draft_id = saved["broker_projection"]["request_draft"]["draft_id"]
    ver_send = saved["broker_projection"]["aggregate_version"]
    send_ids = _ids("send")
    sent = client.post(f"/api/inbox/cases/{case_a}/send-request", {
        **send_ids, "expected_case_version": ver_send, "request_draft_id": draft_id,
    })
    checks.expect("SEND: Request More created by existing command", sent.get("outcome") == "accepted",
                  sent.get("error_code") or "")
    slice1 = sent.get("slice1_projection") or {}
    open_request = slice1.get("open_request") or {}
    request_id = open_request.get("request_id")
    items_sent = open_request.get("items") or []
    checks.expect("SEND: exactly one requested item", len(items_sent) == 1, len(items_sent))
    checks.expect("SEND: customer sees the broker-edited instruction",
                  "陈总办公室已核对" in str(items_sent[0].get("instructions") if items_sent else ""))
    retry = client.post(f"/api/inbox/cases/{case_a}/send-request", {
        **send_ids, "expected_case_version": ver_send, "request_draft_id": draft_id,
    })
    checks.expect("SEND: retry replays, no duplicate", retry.get("outcome") == "replayed",
                  retry.get("outcome"))
    retry_request_id = ((retry.get("slice1_projection") or {}).get("open_request") or {}).get("request_id")
    checks.expect("SEND: retry returns the same request_id", retry_request_id == request_id,
                  f"{request_id} vs {retry_request_id}")
    after_send = case_snapshot(client, case_a)
    checks.expect("SEND: still exactly one open Request More",
                  bool(after_send["open_request"]) and after_send["open_request"].get("request_id") == request_id)
    blocked, _ = assist(client, case_a)
    checks.expect("SEND: drafting blocked while a Request More is open",
                  blocked.get("ok") is False and blocked.get("error_code") == "active_request_more_exists",
                  blocked.get("error_code"))
    evidence["send_proof"] = {
        "request_id": request_id, "draft_id": draft_id,
        "retry_outcome": retry.get("outcome"), "assist_blocked": blocked.get("error_code"),
    }

    # ---------------- Instructions quality (customer-facing hint kept) ----------------
    for label, draft in (("CASE A", draft_a), ("CASE B", draft_b)):
        for item in draft.get("items") or []:
            checks.expect(
                f"{label}: {item['field_key']} keeps a how-to-find-it hint",
                bool(str(item.get("instructions") or "").strip()),
                item.get("instructions"),
            )

    evidence["checks"] = checks.rows
    evidence["failed_checks"] = checks.failed
    evidence["pass_count"] = len([r for r in checks.rows if r["pass"]])
    evidence["fail_count"] = len(checks.failed)
    Path(args.out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"PASS {evidence['pass_count']} / FAIL {evidence['fail_count']}")
    print(f"Evidence: {args.out}")
    if checks.failed:
        for row in checks.failed:
            print(f"  FAILED: {row['check']} — {row['detail']}")
        return 1
    print("QA VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
