#!/usr/bin/env python3
"""
P16 Real Customer Test Case — Andy BMW X5 (Nanxin Li)

Runs both uploaded iPhone photos through the P16 extraction pipeline
using the OpenAI provider and reports the full Trusted Packet result.

Usage:
    PYTHONPATH=. python3 scripts/run_p16_andy_bmw_test.py
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

# ── Ground truth for comparison ──────────────────────────────────────────────
GROUND_TRUTH = {
    "vin": "5UXZV4C56BL402905",
    "year": "2011",
    "make": "BMW",
    "model": "X5",
    "make_model": "BMW X5",
    "named_insured": ["Nanxin Li", "Maochen Li"],
    "plate": "6NGL971",
}

TEST_CASE_DIR = REPO_ROOT / "test_data" / "p16_real_docs" / "andy_bmw_x5"
FILES = [
    TEST_CASE_DIR / "smog_check_vir.png",
    TEST_CASE_DIR / "insurance_card.png",
]

# ── VIN validation helper ─────────────────────────────────────────────────────
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
    print("\n" + "═" * 65)
    print("  P16 REAL CUSTOMER TEST — ANDY BMW X5")
    print("  Customer: Nanxin Li / Maochen Li")
    print("  Vehicle:  2011 BMW X5  VIN: 5UXZV4C56BL402905")
    print("═" * 65)

    # Verify files
    for f in FILES:
        if not f.exists():
            print(f"\n  ❌ File not found: {f}")
            sys.exit(1)
        print(f"  ✓ File: {f.name}  ({f.stat().st_size // 1024} KB)")

    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n  ❌ OPENAI_API_KEY not set.")
        sys.exit(1)

    # Initialize extractor
    print(f"\n  Initializing OpenAI extractor (gpt-4o)…")
    extractor = get_extractor("openai")
    print(f"  ✓ Provider: {extractor.MODEL}")

    # Run extraction
    print(f"\n  Running extraction on {len(FILES)} file(s)…")
    start = time.time()
    result = process_case(
        case_id="andy_bmw_x5_nanxin_li",
        files=FILES,
        extractor=extractor,
        verbose=True,
    )
    elapsed = time.time() - start
    print(f"  ✓ Extraction complete in {elapsed:.1f}s")

    # Helper to get extracted value
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

    # Extract key fields
    vin_ext = get_val("vin")
    year_ext = get_val("year")
    mm_ext = get_val("make_model")
    name_ext = get_val("customer_name")
    zip_ext = get_val("garaging_zip")

    # VIN validation
    vin_valid, vin_status = validate_vin(vin_ext)
    vin_matches_gt = vin_ext.upper().strip() == GROUND_TRUTH["vin"].upper() if vin_ext else False

    # YMM match
    def ymm_pass() -> bool:
        if not year_ext or not mm_ext:
            return False
        year_ok = year_ext.strip() == GROUND_TRUTH["year"]
        mm_lower = mm_ext.lower()
        make_ok = GROUND_TRUTH["make"].lower() in mm_lower
        model_ok = GROUND_TRUTH["model"].lower() in mm_lower
        return year_ok and make_ok and model_ok

    # Named insured match
    def name_pass() -> bool:
        if not name_ext:
            return False
        name_lower = name_ext.lower()
        for n in GROUND_TRUTH["named_insured"]:
            words = n.lower().split()
            if all(w in name_lower for w in words):
                return True
        return False

    # Source attribution
    vin_source = get_source("vin")
    name_source = get_source("customer_name")
    mm_source = get_source("make_model")

    # Determine PASS/FAIL
    vin_pass = vin_matches_gt
    ymm_ok = ymm_pass()
    name_ok = name_pass()
    source_ok = bool(vin_source)  # at least VIN has a source file

    all_pass = vin_pass and ymm_ok and name_ok

    # ── Build output ──────────────────────────────────────────────────────────
    print("\n" + "─" * 65)
    print("  EXTRACTION RESULTS")
    print("─" * 65)
    print(f"  VIN extracted:        {vin_ext!r}  [conf: {get_conf('vin'):.0%}]")
    print(f"  VIN expected:         {GROUND_TRUTH['vin']!r}")
    print(f"  VIN match:            {'✅ PASS' if vin_pass else '❌ FAIL'}")
    print(f"  VIN format valid:     {vin_status}")
    print()
    print(f"  Year extracted:       {year_ext!r}  [conf: {get_conf('year'):.0%}]")
    print(f"  Make/Model extracted: {mm_ext!r}  [conf: {get_conf('make_model'):.0%}]")
    print(f"  YMM match:            {'✅ PASS' if ymm_ok else '❌ FAIL'}")
    print()
    print(f"  Named insured ext:    {name_ext!r}  [conf: {get_conf('customer_name'):.0%}]")
    print(f"  Named insured exp:    {GROUND_TRUTH['named_insured']!r}")
    print(f"  Named insured match:  {'✅ PASS' if name_ok else '❌ FAIL'}")
    print()
    print(f"  Source — VIN:         {vin_source or '(not attributed)'}")
    print(f"  Source — Name:        {name_source or '(not attributed)'}")
    print(f"  Source — YMM:         {mm_source or '(not attributed)'}")
    print(f"  Source attribution:   {'✅ OK' if source_ok else '⚠ NO SOURCE'}")
    print()
    print(f"  Conflicts:            {[c.field for c in result.conflicts] or '(none)'}")
    print(f"  Packet ready:         {'✅ YES' if result.packet_ready else '❌ NO'}")
    print(f"  Readiness reason:     {result.packet_readiness_reason}")
    print(f"  Missing fields:       {result.missing_fields or '(none)'}")
    print(f"  Doc types detected:   {result.document_types_detected}")
    print(f"  Model used:           {result.model_used}")
    print(f"  Cost estimate:        ${result.cost_estimate_usd or 0:.4f}")
    print(f"  Runtime:              {elapsed:.1f}s")

    # ── Packet draft ──────────────────────────────────────────────────────────
    print("\n" + "─" * 65)
    print("  COPY PACKET OUTPUT")
    print("─" * 65)
    print(result.quote_ready_packet_draft)

    # ── Final verdict ─────────────────────────────────────────────────────────
    issues = []
    if not vin_pass:
        issues.append(f"VIN mismatch: extracted {vin_ext!r}, expected {GROUND_TRUTH['vin']!r}")
    if not vin_valid:
        issues.append(f"VIN format invalid: {vin_status}")
    if not ymm_ok:
        issues.append(f"YMM mismatch: extracted year={year_ext!r} make_model={mm_ext!r}")
    if not name_ok:
        issues.append(f"Named insured mismatch: extracted {name_ext!r}")
    if not source_ok:
        issues.append("VIN has no source attribution")
    if result.conflicts:
        issues.append(f"Conflicts detected: {[c.field for c in result.conflicts]}")

    verdict = "PASS" if all_pass else "FAIL"

    print("═" * 65)
    print(f"\nTEST_STATUS:      {'✅ COMPLETE — extraction ran successfully' if not result.error else f'❌ ERROR: {result.error}'}")
    print(f"\nEXTRACTED_PACKET:")
    print(f"  VIN:             {vin_ext}")
    print(f"  Year:            {year_ext}")
    print(f"  Make/Model:      {mm_ext}")
    print(f"  Named Insured:   {name_ext}")
    print(f"  Garaging ZIP:    {zip_ext or '(not found — expected, not in docs)'}")
    print(f"  VIN Source File: {vin_source}")
    print(f"  VIN Warning:     {vin_status} | Matches GT: {vin_matches_gt}")
    print(f"\nEXPECTED_PACKET:")
    print(f"  VIN:             {GROUND_TRUTH['vin']}")
    print(f"  Year:            {GROUND_TRUTH['year']}")
    print(f"  Make/Model:      {GROUND_TRUTH['make_model']}")
    print(f"  Named Insured:   {' / '.join(GROUND_TRUTH['named_insured'])}")
    print(f"  Plate:           {GROUND_TRUTH['plate']}")
    print(f"\nPASS_FAIL:        {verdict}")
    print(f"\nISSUES:")
    if issues:
        for iss in issues:
            print(f"  • {iss}")
    else:
        print("  (none — all fields matched ground truth)")
    print(f"\nNEXT_ACTION:")
    if all_pass:
        print("  ✅ Extraction quality confirmed on real iPhone photos.")
        print("  ✅ VIN, YMM, and named insured extracted correctly.")
        print("  ✅ Safe to run first Chen Kui pilot case with real customer docs.")
    else:
        print("  ❌ Review ISSUES above before using this case for pilot.")
        if not vin_pass:
            print("  → Re-check VIN extraction; ensure image is clear enough.")
        if not name_ok:
            print("  → Named insured may need broker cross-check from insurance card.")
    print("═" * 65 + "\n")

    # Save results as JSON artifact
    artifact_dir = REPO_ROOT / "artifacts" / "p16_accuracy_eval"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "test_case": "andy_bmw_x5_nanxin_li",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provider": extractor.MODEL,
        "ground_truth": GROUND_TRUTH,
        "extracted": {
            "vin": vin_ext,
            "year": year_ext,
            "make_model": mm_ext,
            "customer_name": name_ext,
            "garaging_zip": zip_ext,
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
            "source_attribution": "pass" if source_ok else "fail",
            "vin_format_valid": vin_valid,
            "vin_warning": vin_status,
        },
        "packet_ready": result.packet_ready,
        "packet_readiness_reason": result.packet_readiness_reason,
        "missing_fields": result.missing_fields,
        "conflicts": [c.field for c in result.conflicts],
        "verdict": verdict,
        "issues": issues,
        "runtime_s": round(elapsed, 2),
        "cost_usd": result.cost_estimate_usd,
    }
    out_path = artifact_dir / "andy_bmw_x5_result.json"
    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"  Artifact saved: {out_path}\n")


if __name__ == "__main__":
    run()
