#!/usr/bin/env python3
"""
P16 Insurance Card Retest — Andy BMW X5 (Nanxin Li)

Tests the real iPhone photo of a California Evidence of Liability Insurance card
through the existing P16 extraction + packet pipeline.

Key validation targets:
  - VIN: 5UXZV4C56BL402905
  - Year: 2011  Make: BMW  Model: X5
  - Named insured: NANXIN LI / MAOCHEN LI
  - Policy number: 870247490  (note: not in current 8-field schema)
  - Effective date: 2026-03-23
  - Expiration date: 2026-09-23  (not in current 8-field schema)
  - Agent ZIP 92606 must NOT propagate to garaging ZIP

Usage:
    PYTHONPATH=. python3 scripts/run_p16_insurance_card_retest.py
"""
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.fiqa_api.ocr_kill_test.extractor import get_extractor
from services.fiqa_api.ocr_kill_test.packet_builder import process_case

# ── Ground truth ──────────────────────────────────────────────────────────────
GROUND_TRUTH = {
    "vin": "5UXZV4C56BL402905",
    "year": "2011",
    "make": "BMW",
    "model": "X5",
    "make_model": "BMW X5",
    "named_insured": ["Nanxin Li", "Maochen Li"],
    "policy_number": "870247490",
    "effective_date": "2026-03-23",
    "expiration_date": "2026-09-23",
    "agent_zip": "92606",
    "garaging_zip_expected": "",   # NOT to be filled from this doc
}

TEST_IMAGE = (
    REPO_ROOT
    / "test_data"
    / "p16_real_docs"
    / "andy_bmw_x5"
    / "retest_insurance_card"
    / "insurance_card_retest.png"
)

# ── VIN validation ─────────────────────────────────────────────────────────────
VALID_VIN_CHARS = set("ABCDEFGHJKLMNPRSTUVWXYZ0123456789")

def validate_vin(vin: str) -> tuple[bool, str]:
    if not vin:
        return False, "VIN is empty"
    vin = vin.upper().strip()
    if len(vin) != 17:
        return False, f"VIN length is {len(vin)}, expected 17"
    invalid = [c for c in vin if c not in VALID_VIN_CHARS]
    if invalid:
        return False, f"VIN contains invalid characters: {invalid}"
    return True, "VIN format valid (17 chars, no I/O/Q)"


def run():
    print("\n" + "═" * 70)
    print("  P16 INSURANCE CARD RETEST — ANDY BMW X5 (Nanxin Li)")
    print("  Document: California Evidence of Liability Insurance")
    print("  File: retest_insurance_card/insurance_card_retest.png")
    print("═" * 70)

    # Verify image
    if not TEST_IMAGE.exists():
        print(f"\n  ❌ Image not found: {TEST_IMAGE}")
        sys.exit(1)
    print(f"\n  ✓ Image: {TEST_IMAGE.name}  ({TEST_IMAGE.stat().st_size // 1024} KB)")
    print(f"  ✓ Format: PNG")

    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n  ❌ OPENAI_API_KEY not set.")
        sys.exit(1)

    # Initialize extractor
    print(f"\n  Initializing OpenAI extractor (gpt-4o)…")
    extractor = get_extractor("openai")
    print(f"  ✓ Provider: {extractor.MODEL}")

    # Run extraction — insurance card only
    print(f"\n  Running extraction on 1 file (insurance card only)…")
    start = time.time()
    result = process_case(
        case_id="andy_bmw_x5_insurance_card_retest",
        files=[TEST_IMAGE],
        extractor=extractor,
        verbose=True,
    )
    elapsed = time.time() - start
    print(f"  ✓ Extraction complete in {elapsed:.1f}s")

    # ── Field accessor helpers ─────────────────────────────────────────────────
    def get_val(field: str) -> str:
        ef = result.extracted_fields.get(field)
        if ef is None:
            return ""
        if hasattr(ef, "value"):
            return ef.value or ""
        if isinstance(ef, dict):
            return ef.get("value", "") or ""
        return str(ef)

    def get_source(field: str) -> str:
        ef = result.extracted_fields.get(field)
        if ef is None:
            return ""
        if hasattr(ef, "source_file"):
            return ef.source_file or ""
        if isinstance(ef, dict):
            return ef.get("source_file", "") or ""
        return ""

    def get_conf(field: str) -> float:
        ef = result.extracted_fields.get(field)
        if ef is None:
            return 0.0
        if hasattr(ef, "confidence"):
            return ef.confidence or 0.0
        if isinstance(ef, dict):
            return ef.get("confidence", 0.0) or 0.0
        return 0.0

    def get_notes(field: str) -> str:
        ef = result.extracted_fields.get(field)
        if ef is None:
            return ""
        if hasattr(ef, "notes"):
            return ef.notes or ""
        if isinstance(ef, dict):
            return ef.get("notes", "") or ""
        return ""

    # ── Extract values ─────────────────────────────────────────────────────────
    vin_ext = get_val("vin")
    year_ext = get_val("year")
    mm_ext = get_val("make_model")
    name_ext = get_val("customer_name")
    zip_ext = get_val("garaging_zip")
    eff_date_ext = get_val("delivery_or_effective_date")

    # ── VIN checks ─────────────────────────────────────────────────────────────
    vin_valid, vin_status = validate_vin(vin_ext)
    vin_matches_gt = (
        vin_ext.upper().strip() == GROUND_TRUTH["vin"].upper() if vin_ext else False
    )

    # ── YMM check ──────────────────────────────────────────────────────────────
    def ymm_pass() -> bool:
        if not year_ext or not mm_ext:
            return False
        year_ok = year_ext.strip() == GROUND_TRUTH["year"]
        mm_lower = mm_ext.lower()
        make_ok = GROUND_TRUTH["make"].lower() in mm_lower
        model_ok = GROUND_TRUTH["model"].lower() in mm_lower
        return year_ok and make_ok and model_ok

    # ── Named insured check ─────────────────────────────────────────────────────
    def name_pass() -> bool:
        if not name_ext:
            return False
        name_lower = name_ext.lower()
        for n in GROUND_TRUTH["named_insured"]:
            words = n.lower().split()
            if all(w in name_lower for w in words):
                return True
        return False

    # ── Effective date check (maps to delivery_or_effective_date) ─────────────
    def eff_date_pass() -> bool:
        if not eff_date_ext:
            return False
        # Accept 2026-03-23 or 03/23/2026 or 3/23/2026
        clean = eff_date_ext.strip()
        return (
            "2026-03-23" in clean
            or "03/23/2026" in clean
            or "3/23/2026" in clean
            or "03-23-2026" in clean
        )

    # ── Garaging ZIP safety check ───────────────────────────────────────────────
    # The agent address on the card is Irvine CA 92606.
    # The pipeline must NOT inject 92606 into garaging_zip.
    agent_zip_leak = zip_ext.strip() == GROUND_TRUTH["agent_zip"] if zip_ext else False

    # ── Source attribution check ────────────────────────────────────────────────
    vin_source = get_source("vin")
    name_source = get_source("customer_name")
    mm_source = get_source("make_model")
    source_ok = bool(vin_source)

    # ── Pass/fail aggregation ──────────────────────────────────────────────────
    vin_pass = vin_matches_gt
    ymm_ok = ymm_pass()
    name_ok = name_pass()
    eff_ok = eff_date_pass()
    zip_safe = not agent_zip_leak

    # Policy number and expiration date are NOT in the current 8-field schema.
    # We document this as a schema gap, not a test failure.
    policy_in_schema = False   # current schema does not have policy_number field
    expiry_in_schema = False   # current schema does not have expiration_date field

    all_pass = vin_pass and ymm_ok and name_ok and zip_safe

    # ── Print results ──────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("  EXTRACTION RESULTS")
    print("─" * 70)

    print(f"\n  [VIN]")
    print(f"    Extracted:   {vin_ext!r}  [conf: {get_conf('vin'):.0%}]")
    print(f"    Expected:    {GROUND_TRUTH['vin']!r}")
    print(f"    Match:       {'✅ PASS' if vin_pass else '❌ FAIL'}")
    print(f"    Format:      {vin_status}")
    print(f"    Source file: {vin_source or '(not attributed)'}")

    print(f"\n  [YEAR / MAKE / MODEL]")
    print(f"    Year extracted:      {year_ext!r}  [conf: {get_conf('year'):.0%}]")
    print(f"    Make/Model extracted:{mm_ext!r}  [conf: {get_conf('make_model'):.0%}]")
    print(f"    Expected:            {GROUND_TRUTH['year']} {GROUND_TRUTH['make_model']!r}")
    print(f"    Match:               {'✅ PASS' if ymm_ok else '❌ FAIL'}")

    print(f"\n  [NAMED INSURED]")
    print(f"    Extracted:  {name_ext!r}  [conf: {get_conf('customer_name'):.0%}]")
    print(f"    Expected:   {' / '.join(GROUND_TRUTH['named_insured'])!r}")
    print(f"    Match:      {'✅ PASS' if name_ok else '❌ FAIL'}")
    print(f"    Source:     {name_source or '(not attributed)'}")

    print(f"\n  [EFFECTIVE DATE]")
    print(f"    Extracted (delivery_or_effective_date): {eff_date_ext!r}  [conf: {get_conf('delivery_or_effective_date'):.0%}]")
    print(f"    Expected:   {GROUND_TRUTH['effective_date']!r}")
    print(f"    Match:      {'✅ PASS' if eff_ok else '❌ FAIL'}")

    print(f"\n  [POLICY NUMBER — schema gap]")
    print(f"    Expected:   {GROUND_TRUTH['policy_number']!r}")
    print(f"    In schema:  No (current 8-field schema does not include policy_number)")
    print(f"    Status:     ⚠ SCHEMA GAP — not extracted, not checked as pass/fail")

    print(f"\n  [EXPIRATION DATE — schema gap]")
    print(f"    Expected:   {GROUND_TRUTH['expiration_date']!r}")
    print(f"    In schema:  No (current schema maps delivery_or_effective_date only)")
    print(f"    Status:     ⚠ SCHEMA GAP — not extracted, not checked as pass/fail")

    print(f"\n  [GARAGING ZIP — agent ZIP leak test]")
    print(f"    Extracted garaging_zip: {zip_ext!r}  [conf: {get_conf('garaging_zip'):.0%}]")
    print(f"    Agent ZIP on card:      {GROUND_TRUTH['agent_zip']!r}")
    print(f"    Expected garaging_zip:  '' (not present in this document)")
    if agent_zip_leak:
        print(f"    Leak test:    ❌ FAIL — agent ZIP leaked into garaging_zip")
    elif zip_ext:
        print(f"    Leak test:    ⚠ WARNING — garaging_zip has unexpected value: {zip_ext!r}")
    else:
        print(f"    Leak test:    ✅ PASS — garaging_zip is empty, agent ZIP not leaked")

    print(f"\n  [SOURCE ATTRIBUTION]")
    print(f"    VIN source:    {vin_source or '(not attributed)'}")
    print(f"    Name source:   {name_source or '(not attributed)'}")
    print(f"    YMM source:    {mm_source or '(not attributed)'}")
    print(f"    Status:        {'✅ OK — at least VIN has source' if source_ok else '⚠ NO SOURCE FILE ATTRIBUTED'}")

    print(f"\n  [PACKET STATUS]")
    print(f"    Packet ready:       {'✅ YES' if result.packet_ready else '❌ NO'}")
    print(f"    Readiness reason:   {result.packet_readiness_reason}")
    print(f"    Missing fields:     {result.missing_fields or '(none)'}")
    print(f"    Conflicts:          {[c.field for c in result.conflicts] or '(none)'}")
    print(f"    Doc types detected: {result.document_types_detected}")
    print(f"    Model used:         {result.model_used}")
    print(f"    Cost estimate:      ${result.cost_estimate_usd or 0:.4f}")
    print(f"    Runtime:            {elapsed:.1f}s")

    # ── Copy packet output ─────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("  COPY PACKET OUTPUT (broker-readable)")
    print("─" * 70)
    print(result.quote_ready_packet_draft)

    # ── Issues list ────────────────────────────────────────────────────────────
    issues = []
    warnings = []

    if not vin_pass:
        issues.append(f"VIN mismatch: extracted {vin_ext!r}, expected {GROUND_TRUTH['vin']!r}")
    if not vin_valid:
        issues.append(f"VIN format invalid: {vin_status}")
    if not ymm_ok:
        issues.append(f"YMM mismatch: year={year_ext!r} make_model={mm_ext!r}")
    if not name_ok:
        issues.append(f"Named insured mismatch: extracted {name_ext!r}")
    if agent_zip_leak:
        issues.append(f"CRITICAL: Agent ZIP {GROUND_TRUTH['agent_zip']!r} leaked into garaging_zip")
    if not source_ok:
        issues.append("VIN has no source attribution")
    if result.conflicts:
        issues.append(f"Conflicts detected: {[c.field for c in result.conflicts]}")
    if not eff_ok:
        warnings.append(f"Effective date extracted as {eff_date_ext!r} — may not match expected {GROUND_TRUTH['effective_date']!r}")
    if zip_ext and not agent_zip_leak:
        warnings.append(f"garaging_zip has unexpected non-empty value: {zip_ext!r} — verify it is not agent ZIP")

    # Schema gaps — always flagged as informational
    warnings.append("SCHEMA GAP: policy_number (870247490) is not in the current 8-field extraction schema")
    warnings.append("SCHEMA GAP: expiration_date (2026-09-23) is not in the current 8-field extraction schema — only delivery_or_effective_date is captured")

    verdict = "PASS" if all_pass else "FAIL"

    # ── Final structured output ────────────────────────────────────────────────
    print("═" * 70)
    print(f"\nTEST_STATUS:       {'✅ COMPLETE — extraction ran successfully' if not result.error else f'❌ ERROR: {result.error}'}")
    print(f"\nIMAGE_FORMAT:      PNG  ({TEST_IMAGE.stat().st_size // 1024} KB, real iPhone photo)")
    print(f"\nEXTRACTION_TIME:   {elapsed:.1f}s  (provider: {result.model_used or extractor.MODEL})")

    print(f"\nEXPECTED_PACKET:")
    print(f"  VIN:              {GROUND_TRUTH['vin']}")
    print(f"  Year:             {GROUND_TRUTH['year']}")
    print(f"  Make:             {GROUND_TRUTH['make']}")
    print(f"  Model:            {GROUND_TRUTH['model']}")
    print(f"  Named Insured:    {' / '.join(GROUND_TRUTH['named_insured'])}")
    print(f"  Policy Number:    {GROUND_TRUTH['policy_number']}  (schema gap)")
    print(f"  Effective Date:   {GROUND_TRUTH['effective_date']}")
    print(f"  Expiration Date:  {GROUND_TRUTH['expiration_date']}  (schema gap)")
    print(f"  Garaging ZIP:     (empty — not in insurance card)")
    print(f"  Agent ZIP:        {GROUND_TRUTH['agent_zip']}  (on card — must NOT become garaging ZIP)")

    print(f"\nACTUAL_PACKET:")
    print(f"  VIN:              {vin_ext}")
    print(f"  Year:             {year_ext}")
    print(f"  Make/Model:       {mm_ext}")
    print(f"  Named Insured:    {name_ext}")
    print(f"  Effective Date:   {eff_date_ext}  (delivery_or_effective_date field)")
    print(f"  Garaging ZIP:     {zip_ext or '(empty)'}")
    print(f"  VIN Source File:  {vin_source or '(none)'}")
    print(f"  VIN Valid:        {vin_status}")
    print(f"  VIN Matches GT:   {vin_matches_gt}")
    print(f"  Conflicts:        {[c.field for c in result.conflicts] or '(none)'}")

    print(f"\nPASS_FAIL:         {verdict}")

    print(f"\nWARNINGS:")
    for w in warnings:
        print(f"  ⚠ {w}")

    print(f"\nCOPY_PACKET_OUTPUT:")
    for line in result.quote_ready_packet_draft.splitlines():
        print(f"  {line}")

    print(f"\nISSUES:")
    if issues:
        for iss in issues:
            print(f"  ❌ {iss}")
    else:
        print("  (none)")

    print(f"\nNEXT_ACTION:")
    if all_pass:
        print("  ✅ Insurance card extraction confirmed on real iPhone photo.")
        print("  ✅ VIN, YMM, named insured correct.  Agent ZIP not leaked.")
        print("  ⚠  Policy number and expiration date require schema extension (future sprint).")
        print("  ✅ This document type is safe for Chen Kui pilot intake.")
    else:
        print("  ❌ Review ISSUES above before using this case for pilot.")
        if not vin_pass:
            print("  → Re-check VIN extraction; confirm image quality.")
        if not name_ok:
            print("  → Named insured needs broker cross-check.")
        if agent_zip_leak:
            print("  → CRITICAL: Fix garaging ZIP extraction — agent ZIP must not be used.")
    print("═" * 70 + "\n")

    # ── Save artifact ──────────────────────────────────────────────────────────
    artifact_dir = REPO_ROOT / "artifacts" / "p16_accuracy_eval"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "test_case": "andy_bmw_x5_insurance_card_retest",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "image_file": str(TEST_IMAGE),
        "image_format": "PNG",
        "image_size_kb": TEST_IMAGE.stat().st_size // 1024,
        "provider": result.model_used or extractor.MODEL,
        "runtime_s": round(elapsed, 2),
        "cost_usd": result.cost_estimate_usd,
        "ground_truth": GROUND_TRUTH,
        "extracted": {
            "vin": vin_ext,
            "year": year_ext,
            "make_model": mm_ext,
            "customer_name": name_ext,
            "garaging_zip": zip_ext,
            "delivery_or_effective_date": eff_date_ext,
        },
        "sources": {
            "vin": vin_source,
            "customer_name": name_source,
            "make_model": mm_source,
        },
        "match_results": {
            "vin": "pass" if vin_pass else "fail",
            "ymm": "pass" if ymm_ok else "fail",
            "named_insured": "pass" if name_ok else "fail",
            "effective_date": "pass" if eff_ok else "fail",
            "garaging_zip_agent_leak": "fail" if agent_zip_leak else "pass",
            "source_attribution": "pass" if source_ok else "fail",
            "vin_format_valid": vin_valid,
            "vin_status": vin_status,
        },
        "schema_gaps": [
            "policy_number (870247490) — not in current 8-field schema",
            "expiration_date (2026-09-23) — schema only has delivery_or_effective_date",
        ],
        "packet_ready": result.packet_ready,
        "packet_readiness_reason": result.packet_readiness_reason,
        "missing_fields": result.missing_fields,
        "conflicts": [c.field for c in result.conflicts],
        "verdict": verdict,
        "issues": issues,
        "warnings": warnings,
        "quote_ready_packet_draft": result.quote_ready_packet_draft,
    }
    out_path = artifact_dir / "insurance_card_retest_result.json"
    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"  Artifact saved: {out_path}\n")


if __name__ == "__main__":
    run()
