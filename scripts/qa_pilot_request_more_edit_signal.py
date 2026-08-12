#!/usr/bin/env python3
"""Cloud QA synthetic pilot for the AI Request More edit signal.

Walks the real broker path on the deployed service — create claim, confirm
facts, call the drafting endpoint, save the draft, send it — and then reads the
signal back out of durable storage. Nothing here bypasses lifecycle or
idempotency; every write is an existing broker command.

CASE A  only VIN missing, AI draft sent unchanged   -> edited = false
CASE B  only VIN missing, one sentence rewritten    -> edited = true
CASE C  VIN + insurance card, office template       -> ai_used = false

Usage:
  set -a && source .env.cloudrun.qa && set +a
  PYTHONPATH=. python3 scripts/qa_pilot_request_more_edit_signal.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

QA_BASE = "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app"
PRODUCTION_MARKERS = ("fiqa-api-g7zatxrycq", "//fiqa-api.")

VEHICLE_FACTS = {"vehicle_year": "2019", "vehicle_make": "Toyota", "vehicle_model": "Camry"}
ACCIDENT_FACTS = {
    "accident_description": "QA fixture: 停车场倒车轻微剐蹭（合成测试数据）",
    "accident_datetime": "2026-08-01 下午",
    "accident_location": "QA 测试停车场",
    "injury_status": "no",
}
BROKER_REWRITE = "陈总办公室已核对，麻烦您拍一张车架号照片发给我们。"


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


class Checks:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def expect(self, name: str, passed: bool, detail: Any = "") -> bool:
        self.rows.append({"check": name, "pass": bool(passed), "detail": str(detail)[:300]})
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        return bool(passed)

    @property
    def failed(self) -> list[dict]:
        return [row for row in self.rows if not row["pass"]]


def _ids(prefix: str) -> dict[str, str]:
    tail = uuid4().hex[:12]
    return {"command_id": f"cmd_{prefix}_{tail}", "idempotency_key": f"idem_{prefix}_{tail}"}


def _requestable(checklist: list[dict]) -> list[str]:
    return [row["field_key"] for row in checklist if row.get("suggested_for_request")]


def create_case(client: Client, *, title: str, known_facts: dict) -> tuple[str, int, list[dict]]:
    result = client.post(
        "/api/inbox/claims",
        {
            **_ids("create"),
            "is_test": True,
            "title": title,
            "customer_name": "QA Synthetic Customer",
            "contact_note": "AI Request More edit-signal pilot (synthetic, no real PII)",
            "qa_label": "ai_request_more_edit_signal",
            "known_facts": known_facts,
        },
    )
    if result.get("outcome") not in {"accepted", "replayed"}:
        raise RuntimeError(f"create_claim failed: {json.dumps(result)[:400]}")
    projection = result["broker_projection"]
    return (
        result["case_id"],
        int(projection["aggregate_version"]),
        projection["missing_information_checklist"],
    )


def confirm_fact(client: Client, case_id: str, version: int, field_key: str) -> tuple[int, list[dict]]:
    result = client.post(
        f"/api/inbox/cases/{case_id}/fact-status",
        {
            **_ids("factstatus"),
            "expected_case_version": version,
            "field_key": field_key,
            "status": "confirmed",
            "reason": "QA synthetic broker confirmation",
        },
    )
    if result.get("outcome") not in {"accepted", "replayed"}:
        raise RuntimeError(f"fact-status {field_key} failed: {json.dumps(result)[:400]}")
    projection = result["broker_projection"]
    return int(projection["aggregate_version"]), projection["missing_information_checklist"]


def draft_items_from_assist(assist: dict, *, rewrite_first: str | None = None) -> list[dict]:
    """What the Workbench posts back for the drafted items."""
    items: list[dict] = []
    for index, item in enumerate(assist.get("items") or [], start=1):
        instructions = str(item.get("instructions") or "")
        if rewrite_first and index == 1:
            instructions = rewrite_first
        items.append(
            {
                "field_key": item.get("field_key"),
                "item_type": item.get("item_type"),
                "label": item.get("label"),
                "instructions": instructions,
                "required": True,
                "position": index,
                "request_mode": item.get("request_mode") or "request_missing",
                "selected": True,
            }
        )
    return items


def save_and_send(
    client: Client,
    case_id: str,
    version: int,
    items: list[dict],
    receipt: dict | None,
) -> tuple[dict, dict]:
    payload = {**_ids("save"), "expected_case_version": version, "items": items}
    if receipt:
        payload["ai_draft"] = receipt
    saved = client.post(f"/api/inbox/cases/{case_id}/request-draft", payload)
    if saved.get("outcome") not in {"accepted", "replayed"}:
        raise RuntimeError(f"save_request_draft failed: {json.dumps(saved)[:400]}")
    projection = saved["broker_projection"]
    sent = client.post(
        f"/api/inbox/cases/{case_id}/send-request",
        {
            **_ids("send"),
            "expected_case_version": int(projection["aggregate_version"]),
            "request_draft_id": projection["request_draft"]["draft_id"],
        },
    )
    if sent.get("outcome") != "accepted":
        raise RuntimeError(f"send_request failed: {json.dumps(sent)[:400]}")
    return saved, sent


def run_case(
    client: Client,
    checks: Checks,
    *,
    label: str,
    title: str,
    known_facts: dict,
    confirm: tuple[str, ...],
    expect_missing: list[str],
    prefer_template: bool,
    rewrite_first: str | None,
) -> dict:
    print(f"\n{label}")
    case_id, version, checklist = create_case(client, title=title, known_facts=known_facts)
    for field_key in confirm:
        version, checklist = confirm_fact(client, case_id, version, field_key)
    checks.expect(
        f"{label}: deterministic missing set == {expect_missing}",
        _requestable(checklist) == expect_missing,
        _requestable(checklist),
    )

    assist = client.post(
        f"/api/inbox/cases/{case_id}/request-draft-assist",
        {"correlation_id": f"pilot_{uuid4().hex[:8]}", "prefer_template": prefer_template},
    )
    checks.expect(f"{label}: drafting available", assist.get("drafting_available") is True,
                  assist.get("error_code") or assist.get("message") or "")
    receipt = assist.get("ai_draft_receipt")
    checks.expect(f"{label}: server issued a draft receipt", isinstance(receipt, dict))
    checks.expect(
        f"{label}: assist stayed read-only",
        assist.get("lifecycle_mutated") is False,
    )

    after_assist = current_version(client, case_id)
    checks.expect(
        f"{label}: assist did not bump the case version",
        after_assist == version,
        f"{version} -> {after_assist}",
    )

    items = draft_items_from_assist(assist, rewrite_first=rewrite_first)
    saved, sent = save_and_send(client, case_id, after_assist, items, receipt)
    signal = sent.get("ai_request_more") or {}

    stored = client.get(f"/api/inbox/support/request-more-ai-signal/{case_id}", support=True)
    return {
        "case_id": case_id,
        "assist": {
            key: assist.get(key)
            for key in (
                "draft_used_ai",
                "used_fallback",
                "fallback_reason",
                "authority",
                "guardrail_outcome",
                "model_provider",
                "model_name",
                "missing_item_count",
                "latency_ms",
            )
        },
        "draft_text_preview_len": len(str(assist.get("draft_text") or "")),
        "send_signal": signal,
        "stored": stored,
        "saved_outcome": saved.get("outcome"),
        "sent_outcome": sent.get("outcome"),
    }


def current_version(client: Client, case_id: str) -> int:
    case = client.get(f"/api/inbox/cases/{case_id}")
    return int((case.get("p20_case_intake_projection") or {}).get("aggregate_version") or 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("QA_BASE_URL", QA_BASE))
    parser.add_argument("--out", default="/tmp/qa_request_more_edit_signal_evidence.json")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    if any(marker in base for marker in PRODUCTION_MARKERS):
        print(f"Refusing to run against a Production URL: {base}", file=sys.stderr)
        return 2

    intake_key = (os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    support_key = (os.environ.get("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    if not intake_key or not support_key:
        print(
            "UNIFIED_INTAKE_INTAKE_API_KEY and UNIFIED_INTAKE_SUPPORT_API_KEY required",
            file=sys.stderr,
        )
        return 2

    client = Client(base, intake_key, support_key)
    checks = Checks()
    evidence: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "base_url": base,
        "disclaimer": "SYNTHETIC QA — not a real broker metric",
    }

    manifest = client.get("/api/inbox/support/deployment-manifest", support=True)
    evidence["deployed_commit"] = (manifest.get("git") or {}).get("commit")
    evidence["assistant_flags"] = manifest.get("request_more_assistant")
    print(f"Deployed commit: {evidence['deployed_commit']}")
    print(f"Assistant flags: {json.dumps(evidence['assistant_flags'])}")
    flags = evidence["assistant_flags"] or {}
    checks.expect("QA: assistant enabled", bool(flags.get("assistant_enabled")))
    checks.expect("QA: real LLM drafting enabled", bool(flags.get("llm_drafting_enabled")))
    checks.expect("QA: office allowlist configured", bool(flags.get("office_allowlist_configured")),
                  f"count={flags.get('office_allowlist_count')}")

    confirm_all_but_vin = (
        "vehicle_information",
        "policy_or_insurance_card",
        "accident_description",
        "accident_datetime",
        "accident_location",
        "injury_status",
    )
    vin_only_facts = {**VEHICLE_FACTS, **ACCIDENT_FACTS, "policy_number": "QA-SYNTH-POLICY"}

    # ---- CASE A — AI draft sent unchanged ----
    case_a = run_case(
        client, checks,
        label="CASE A — AI draft sent unchanged",
        title="AI RM signal — Case A unchanged",
        known_facts=vin_only_facts,
        confirm=confirm_all_but_vin,
        expect_missing=["vin"],
        prefer_template=False,
        rewrite_first=None,
    )
    evidence["case_a"] = case_a
    sig_a = case_a["send_signal"]
    checks.expect("CASE A: real AI draft used", case_a["assist"]["draft_used_ai"] is True,
                  case_a["assist"]["fallback_reason"] or "")
    checks.expect("CASE A: no fallback", case_a["assist"]["used_fallback"] is False)
    checks.expect("CASE A: ai_used == true", sig_a.get("ai_used") is True)
    checks.expect("CASE A: draft_edited_before_send == false",
                  sig_a.get("draft_edited_before_send") is False, sig_a.get("signal_reason"))
    checks.expect("CASE A: signal linked to the send command",
                  bool(sig_a.get("request_id")) and bool(sig_a.get("command_id")))

    # ---- CASE B — broker rewrites one sentence ----
    case_b = run_case(
        client, checks,
        label="CASE B — broker rewrites one customer-facing sentence",
        title="AI RM signal — Case B edited",
        known_facts=vin_only_facts,
        confirm=confirm_all_but_vin,
        expect_missing=["vin"],
        prefer_template=False,
        rewrite_first=BROKER_REWRITE,
    )
    evidence["case_b"] = case_b
    sig_b = case_b["send_signal"]
    checks.expect("CASE B: real AI draft used", case_b["assist"]["draft_used_ai"] is True,
                  case_b["assist"]["fallback_reason"] or "")
    checks.expect("CASE B: ai_used == true", sig_b.get("ai_used") is True)
    checks.expect("CASE B: draft_edited_before_send == true",
                  sig_b.get("draft_edited_before_send") is True, sig_b.get("signal_reason"))

    # ---- CASE C — office template, two missing items ----
    case_c = run_case(
        client, checks,
        label="CASE C — broker chooses the office template (VIN + insurance card)",
        title="AI RM signal — Case C template",
        known_facts={**VEHICLE_FACTS, **ACCIDENT_FACTS},
        confirm=("vehicle_information",),
        expect_missing=["vin", "policy_or_insurance_card"],
        prefer_template=True,
        rewrite_first=None,
    )
    evidence["case_c"] = case_c
    sig_c = case_c["send_signal"]
    checks.expect("CASE C: authority == office_template",
                  case_c["assist"]["authority"] == "office_template")
    checks.expect("CASE C: template choice is not an AI failure",
                  case_c["assist"]["used_fallback"] is False)
    checks.expect("CASE C: ai_used == false", sig_c.get("ai_used") is False)
    checks.expect("CASE C: no AI adoption claimed",
                  sig_c.get("draft_edited_before_send") is None
                  and sig_c.get("signal_reason") == "ai_not_adopted",
                  sig_c.get("signal_reason"))
    checks.expect("CASE C: two items still compared stably", sig_c.get("sent_item_count") == 2)

    # ---- Durable read-back proof ----
    print("\nSTORED SIGNAL — read back from durable case events")
    for label, case in (("CASE A", case_a), ("CASE B", case_b), ("CASE C", case_c)):
        stored = case["stored"]
        rows = stored.get("send_signals") or []
        checks.expect(f"{label}: exactly one stored send signal", len(rows) == 1, len(rows))
        if not rows:
            continue
        row = rows[0]
        checks.expect(f"{label}: stored matches the send response",
                      row.get("draft_edited_before_send") == case["send_signal"].get("draft_edited_before_send")
                      and row.get("ai_used") == case["send_signal"].get("ai_used"))
        checks.expect(f"{label}: stored answers missing_item_count",
                      isinstance(row.get("missing_item_count"), int), row.get("missing_item_count"))
        checks.expect(f"{label}: stored links the request", bool(row.get("request_id")))
        checks.expect(f"{label}: pilot office recorded", bool(stored.get("pilot_office_id")),
                      stored.get("pilot_office_id"))
        blob = json.dumps(stored, ensure_ascii=False)
        checks.expect(f"{label}: stored signal carries no draft wording",
                      BROKER_REWRITE not in blob and "挡风玻璃" not in blob)

    # ---- Synthetic summary ----
    from services.fiqa_api.inbox_triage.request_more_assistant.edit_signal import (  # noqa: E402
        summarize_send_signals,
    )

    all_signals = [case_a["send_signal"], case_b["send_signal"], case_c["send_signal"]]
    summary = summarize_send_signals(all_signals)
    summary["label"] = "SYNTHETIC QA — not a real broker metric"
    cases = (case_a, case_b, case_c)
    # Case C asked for the office template, so the model was never attempted.
    summary["ai_drafts_attempted"] = sum(
        1 for case in cases if case["assist"]["fallback_reason"] != "assistant_disabled"
        and case is not case_c
    )
    summary["ai_drafts_successful"] = sum(1 for case in cases if case["assist"]["draft_used_ai"])
    evidence["synthetic_summary"] = summary
    checks.expect("SUMMARY: 2 AI drafts sent", summary["ai_drafts_sent"] == 2, summary["ai_drafts_sent"])
    checks.expect("SUMMARY: 1 unchanged", summary["sent_unchanged"] == 1)
    checks.expect("SUMMARY: 1 edited", summary["sent_edited"] == 1)
    checks.expect("SUMMARY: synthetic edit rate 0.5", summary["broker_edit_rate"] == 0.5,
                  summary["broker_edit_rate"])

    evidence["checks"] = checks.rows
    evidence["failed_checks"] = checks.failed
    evidence["pass_count"] = len([row for row in checks.rows if row["pass"]])
    evidence["fail_count"] = len(checks.failed)
    Path(args.out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n" + "=" * 62)
    print("SYNTHETIC QA SUMMARY — not a real broker metric")
    print(f"  AI drafts attempted   : {summary['ai_drafts_attempted']}")
    print(f"  AI drafts successful  : {summary['ai_drafts_successful']}")
    print(f"  fallback sends        : {summary['fallback_sends']}")
    print(f"  sent unchanged        : {summary['sent_unchanged']}")
    print(f"  sent edited           : {summary['sent_edited']}")
    print(f"  synthetic edit rate   : {summary['broker_edit_rate']}")
    print("=" * 62)
    print(f"PASS {evidence['pass_count']} / FAIL {evidence['fail_count']}")
    print(f"Evidence: {args.out}")
    if checks.failed:
        for row in checks.failed:
            print(f"  FAILED: {row['check']} — {row['detail']}")
        return 1
    print("EDIT SIGNAL PILOT VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
