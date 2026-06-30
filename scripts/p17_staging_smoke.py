#!/usr/bin/env python3
"""P17 Phase 1 staging smoke — 3-upload consolidation + VIN conflict."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
BASE = os.environ.get(
    "P17_STAGING_URL", "https://fiqa-api-1013093472160.us-west1.run.app"
).rstrip("/")
DOCS = REPO / "test_data" / "p16_real_docs"

INTAKE_KEY = os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY", "").strip()
if not INTAKE_KEY:
    env_file = REPO / ".env.cloudrun"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("UNIFIED_INTAKE_INTAKE_API_KEY="):
                INTAKE_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

# Fresh 10-digit US phones (626-555-XXXX). 11-digit values break lookup/resolver.
_suffix = str(int(time.time()))[-4:]
PHONE_CONSOLIDATION = os.environ.get("P17_SMOKE_PHONE", f"626555{_suffix}")
PHONE_CONFLICT = os.environ.get("P17_CONFLICT_PHONE", f"626556{_suffix}")


def _multipart_extract(phone: str, file_specs: list[tuple[str, str]]) -> dict[str, Any]:
    """file_specs: [(disk_path, upload_filename), ...]"""
    boundary = "----P17SmokeBoundary7x"
    parts: list[bytes] = []
    for field, val in [
        ("customer_name", "P17 Smoke Test"),
        ("phone", phone),
        ("garaging_zip", "91776"),
        ("request_type", "add_vehicle"),
    ]:
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"\r\n\r\n{val}\r\n".encode()
        )
    for disk_path, upload_name in file_specs:
        data = Path(disk_path).read_bytes()
        header = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"files\"; filename=\"{upload_name}\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        parts.append(header + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(
        f"{BASE}/api/intake/add-car/extract",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Origin": "https://ui-smoky-beta.vercel.app",
        },
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            out = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        out = {"http_error": exc.code, "detail": exc.read().decode()[:800]}
    out["_elapsed_s"] = round(time.time() - t0, 1)
    return out


def _api_get(path: str) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{BASE}{path}",
        headers={
            "Accept": "application/json",
            "X-Unified-Intake-Api-Key": INTAKE_KEY,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _normalize_phone(p: str) -> str:
    return "".join(c for c in p if c.isdigit())


def _readiness_from_extract(resp: dict[str, Any]) -> str | None:
    pkt = resp.get("packet") or {}
    vin_val = (pkt.get("vin") or {}).get("value") if isinstance(pkt.get("vin"), dict) else None
    warnings = resp.get("warnings") or []
    still = []
    for key in ("vin", "year", "make", "model", "primary_driver", "effective_date"):
        field = pkt.get(key)
        if isinstance(field, dict) and not str(field.get("value") or "").strip():
            still.append(key)
    if any("Multiple VINs" in w for w in warnings):
        return "BROKER_REVIEW"
    if still:
        return "NEED_INFO"
    if vin_val:
        return "READY"
    return "NEED_INFO"


def _summarize_case(case: dict[str, Any]) -> dict[str, Any]:
    blob = case.get("p16_broker_packet") or {}
    pkt = blob.get("packet") or {}
    vin_field = pkt.get("vin")
    vin = vin_field.get("value") if isinstance(vin_field, dict) else vin_field
    return {
        "case_id": case.get("case_id"),
        "readiness_status": blob.get("readiness_status"),
        "merge_review_required": case.get("merge_review_required"),
        "conflict_state": case.get("conflict_state"),
        "vehicle_key": case.get("vehicle_key"),
        "evidence_events_count": len(case.get("evidence_events") or []),
        "evidence_filenames": [e.get("filename") for e in (case.get("evidence_events") or [])],
        "vin_in_packet": vin,
        "still_needed_fields": case.get("still_needed_fields"),
        "service_lane": case.get("service_lane"),
        "case_status": case.get("case_status"),
    }


def _inbox_open_rows_for_phone(phone: str) -> list[dict[str, Any]]:
    digits = _normalize_phone(phone)
    rows: list[dict[str, Any]] = []
    offset = 0
    while offset <= 500:
        data = _api_get(f"/api/inbox/cases?limit=50&offset={offset}")
        batch = data.get("cases") or []
        if not batch:
            break
        for case in batch:
            cp = _normalize_phone(str(case.get("customer_phone") or ""))
            if cp == digits and case.get("service_lane") == "add_car":
                if case.get("case_status") != "closed":
                    rows.append(case)
        if not data.get("has_more"):
            break
        offset += 50
    return rows


def _extract_summary(resp: dict[str, Any]) -> dict[str, Any]:
    pkt = resp.get("packet") or {}
    vin = (pkt.get("vin") or {}).get("value") if isinstance(pkt.get("vin"), dict) else None
    return {
        "case_id": resp.get("case_id"),
        "mock_mode": resp.get("mock_mode"),
        "model_used": resp.get("model_used"),
        "http_error": resp.get("http_error"),
        "readiness_inferred": _readiness_from_extract(resp),
        "vin": vin,
        "year": (pkt.get("year") or {}).get("value") if isinstance(pkt.get("year"), dict) else None,
        "make": (pkt.get("make") or {}).get("value") if isinstance(pkt.get("make"), dict) else None,
        "model": (pkt.get("model") or {}).get("value") if isinstance(pkt.get("model"), dict) else None,
        "warnings": resp.get("warnings"),
        "elapsed_s": resp.get("_elapsed_s"),
    }


def main() -> int:
    report: dict[str, Any] = {
        "staging_url": BASE,
        "phone_consolidation": PHONE_CONSOLIDATION,
        "phone_conflict": PHONE_CONFLICT,
    }

    # 1. Health
    with urllib.request.urlopen(f"{BASE}/health/live", timeout=20) as r:
        report["health_live"] = json.loads(r.read().decode())

    # 2. Mock path check — production should reject no-file upload
    mock_probe = _multipart_extract("6265559999", [])
    report["mock_path_check"] = {
        "http_error": mock_probe.get("http_error"),
        "mock_mode": mock_probe.get("mock_mode"),
        "real_extraction_required": mock_probe.get("http_error") == 422
        and "mock" not in str(mock_probe.get("detail", "")).lower(),
        "detail_snippet": str(mock_probe.get("detail", ""))[:200],
    }

    # 3. Three-upload consolidation (Honda Civic corpus — reg → PA → VIN proxy)
    uploads = [
        (
            "upload1_insurance_card",
            [(DOCS / "registrations/reg_002_ca_dmv.pdf", "insurance_card.pdf")],
        ),
        (
            "upload2_dec_page",
            [(DOCS / "purchase_agreements/pa_002_honda_civic.pdf", "dec_page.pdf")],
        ),
        (
            "upload3_vin_photo",
            [(DOCS / "registrations/reg_002_ca_dmv.pdf", "vehicle_registration.pdf")],
        ),
    ]
    consolidation_results: list[dict[str, Any]] = []
    for label, specs in uploads:
        resp = _multipart_extract(PHONE_CONSOLIDATION, specs)
        consolidation_results.append({"label": label, "files": [s[1] for s in specs], **_extract_summary(resp)})
    report["consolidation_uploads"] = consolidation_results

    case_ids = [u["case_id"] for u in consolidation_results if u.get("case_id")]
    unique_ids = set(case_ids)
    report["consolidation_case_ids"] = case_ids
    report["consolidation_same_case_id"] = len(unique_ids) == 1 and len(case_ids) == 3

    if case_ids:
        primary = case_ids[0]
        stored = _api_get(f"/api/inbox/cases/{urllib.parse.quote(primary)}")
        report["consolidation_stored_case"] = _summarize_case(stored)
        report["consolidation_inbox_open_rows"] = len(_inbox_open_rows_for_phone(PHONE_CONSOLIDATION))

    # 4. VIN conflict test — Toyota then BMW
    conflict_uploads = [
        (
            "conflict_upload1_vin_a",
            [(DOCS / "purchase_agreements/pa_001_toyota_camry.pdf", "insurance_card.pdf")],
        ),
        (
            "conflict_upload2_vin_b",
            [(DOCS / "purchase_agreements/pa_003_bmw_x5.pdf", "dec_page.pdf")],
        ),
    ]
    conflict_results: list[dict[str, Any]] = []
    for label, specs in conflict_uploads:
        resp = _multipart_extract(PHONE_CONFLICT, specs)
        conflict_results.append({"label": label, "files": [s[1] for s in specs], **_extract_summary(resp)})
    report["conflict_uploads"] = conflict_results

    conflict_ids = [u["case_id"] for u in conflict_results if u.get("case_id")]
    report["conflict_case_ids"] = conflict_ids
    report["conflict_same_case_id"] = len(set(conflict_ids)) == 1 and len(conflict_ids) == 2

    if conflict_ids:
        ccase = _api_get(f"/api/inbox/cases/{urllib.parse.quote(conflict_ids[0])}")
        report["conflict_stored_case"] = _summarize_case(ccase)

    # 5. Pass/fail
    stored = report.get("consolidation_stored_case") or {}
    cstored = report.get("conflict_stored_case") or {}
    checks = {
        "real_extraction_not_mock": all(
            u.get("mock_mode") is False for u in consolidation_results if not u.get("http_error")
        ),
        "same_case_id_3_uploads": report.get("consolidation_same_case_id"),
        "one_inbox_row": report.get("consolidation_inbox_open_rows") == 1,
        "evidence_events_3": stored.get("evidence_events_count") == 3,
        "readiness_progresses": stored.get("readiness_status") in ("READY", "NEED_INFO", "BROKER_REVIEW"),
        "conflict_same_case_id": report.get("conflict_same_case_id"),
        "conflict_broker_review": cstored.get("readiness_status") == "BROKER_REVIEW",
        "conflict_merge_review_flag": cstored.get("merge_review_required") is True,
        "conflict_vin_not_silent_overwrite": bool(cstored.get("vehicle_key")),
    }
    report["checks"] = checks
    report["verdict"] = "PASS" if all(checks.values()) else "FAIL"

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
