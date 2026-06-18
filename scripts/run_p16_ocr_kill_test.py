#!/usr/bin/env python3
"""
P16 OCR Kill Test Runner

Determines whether Upload-first Add-Car Packet Builder is technically viable.
Real customer images/PDFs → AI extraction → 8 core add-car fields → Quote-Ready Packet draft.

Usage:
    python scripts/run_p16_ocr_kill_test.py --input-dir test_assets/p16_ocr_kill_test --provider auto

Providers:
    auto     — picks openai if OPENAI_API_KEY set, else gemini, else dry_run
    openai   — requires OPENAI_API_KEY
    gemini   — requires GEMINI_API_KEY or GOOGLE_API_KEY
    dry_run  — no API calls, tests pipeline only

Output:
    artifacts/p16_ocr_kill_test/results.json
    artifacts/p16_ocr_kill_test/results.csv
    docs/trial/P16_OCR_KILL_TEST_REPORT.md
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── path setup ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.fiqa_api.ocr_kill_test.extractor import get_extractor
from services.fiqa_api.ocr_kill_test.packet_builder import process_case
from services.fiqa_api.ocr_kill_test.reporter import write_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

DEFAULT_INPUT_DIR = REPO_ROOT / "test_assets" / "p16_ocr_kill_test"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "p16_ocr_kill_test"
DEFAULT_REPORT_PATH = REPO_ROOT / "docs" / "trial" / "P16_OCR_KILL_TEST_REPORT.md"


# ── case discovery ────────────────────────────────────────────────────────

def discover_cases(input_dir: Path) -> list[tuple[str, list[Path]]]:
    """
    Returns list of (case_id, [file_paths]).

    Logic:
    - If subdirectories named case_XXX exist, each subdir = one case.
    - Files directly in root = single case named 'case_001'.
    - Empty dirs are skipped.
    """
    cases = []

    # Check for case_* subdirectories
    subdirs = sorted([d for d in input_dir.iterdir() if d.is_dir()
                      and not d.name.startswith(".")])

    for subdir in subdirs:
        files = sorted([
            f for f in subdir.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ])
        if files:
            cases.append((subdir.name, files))

    # Also pick up root-level files (no subdirectory)
    root_files = sorted([
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ])
    if root_files:
        cases.insert(0, ("case_root", root_files))

    return cases


# ── terminal summary ──────────────────────────────────────────────────────

def print_terminal_summary(
    provider: str,
    results,
    verdict: str,
    verdict_explanation: str,
    failure_modes: list[str],
    report_path: Path,
    output_dir: Path,
) -> None:
    n = len(results)
    ready = sum(1 for r in results if r.packet_ready)
    rate = f"{ready}/{n} ({ready/n:.0%})" if n else "0/0"

    vin_present = sum(
        1 for r in results
        if r.extracted_fields.get("vin") and
        hasattr(r.extracted_fields["vin"], "is_present") and
        r.extracted_fields["vin"].is_present()
    )
    vin_result = f"{vin_present}/{n} cases had VIN extracted" if n else "N/A"

    top_modes = "\n    ".join(failure_modes[:3]) if failure_modes else "(none)"

    print("\n" + "═" * 60)
    print("  P16 OCR KILL TEST COMPLETE")
    print("═" * 60)
    print(f"  PROVIDER:             {provider}")
    print(f"  CASES_TESTED:         {n}")
    print(f"  FILES_PROCESSED:      {sum(len(r.input_files) for r in results)}")
    print(f"  PACKET_READY_RATE:    {rate}")
    print(f"  VIN_EXTRACTION:       {vin_result}")
    print(f"  TOP_FAILURE_MODES:    {top_modes}")
    print(f"  REPORT_PATH:          {report_path}")
    print(f"  ARTIFACTS_DIR:        {output_dir}")
    print(f"  CERTIFICATION:        {verdict}")
    verdict_short = verdict_explanation[:80] + ("…" if len(verdict_explanation) > 80 else "")
    print(f"  NEXT_RECOMMENDED:     {verdict_short}")
    print("═" * 60 + "\n")


# ── main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="P16 OCR Kill Test — AI extraction of add-car fields from documents"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Folder containing test case files or subfolders. Default: {DEFAULT_INPUT_DIR}",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=os.environ.get("P16_OCR_PROVIDER", "auto"),
        choices=["auto", "openai", "gemini", "dry_run"],
        help="Vision provider. Default: auto (openai → gemini → dry_run)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for results.json and results.csv. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help=f"Path to write Markdown report. Default: {DEFAULT_REPORT_PATH}",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-file extraction details",
    )
    args = parser.parse_args()

    input_dir: Path = args.input_dir.resolve()
    output_dir: Path = args.output_dir.resolve()
    report_path: Path = args.report_path.resolve()

    # ── validate input dir ────────────────────────────────────────────────
    if not input_dir.exists():
        print(f"\n❌ Input directory not found: {input_dir}")
        print("   Create it and add test documents:")
        print(f"   mkdir -p {input_dir}/case_001")
        print(f"   cp your_document.pdf {input_dir}/case_001/")
        sys.exit(1)

    print(f"\n{'─'*60}")
    print(f"  P16 OCR Kill Test")
    print(f"  Input: {input_dir}")
    print(f"  Provider: {args.provider}")
    print(f"{'─'*60}")

    # ── discover cases ────────────────────────────────────────────────────
    cases = discover_cases(input_dir)

    if not cases:
        print("\n⚠  NO DOCUMENTS FOUND")
        print(f"\n   Searched: {input_dir}")
        print(f"   Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        print("\n   To add test documents:")
        print(f"   mkdir -p {input_dir}/case_001")
        print(f"   cp dealer_paperwork.jpg {input_dir}/case_001/")
        print(f"   cp purchase_contract.pdf {input_dir}/case_001/")
        print("\n   Then re-run:")
        print(f"   python scripts/run_p16_ocr_kill_test.py --provider auto")
        print("\n   For pipeline-only testing (no API):")
        print(f"   python scripts/run_p16_ocr_kill_test.py --provider dry_run")
        print()
        # Write empty artifacts so the runner always produces output
        output_dir.mkdir(parents=True, exist_ok=True)
        import json
        with open(output_dir / "results.json", "w") as f:
            json.dump({"meta": {"status": "no_files"}, "cases": []}, f, indent=2)
        sys.exit(0)

    print(f"\n  Found {len(cases)} case(s):")
    for cid, files in cases:
        print(f"    {cid}: {len(files)} file(s) — {', '.join(f.name for f in files[:3])}"
              + (" …" if len(files) > 3 else ""))

    # ── initialize extractor ──────────────────────────────────────────────
    print(f"\n  Initializing {args.provider} extractor…")
    try:
        extractor = get_extractor(args.provider)
        actual_provider = extractor.MODEL if hasattr(extractor, "MODEL") else args.provider
        print(f"  ✓ Provider ready: {actual_provider}")
    except Exception as e:
        print(f"\n❌ Failed to initialize provider '{args.provider}': {e}")
        print("   Try --provider dry_run to test pipeline without API calls.")
        sys.exit(1)

    if hasattr(extractor, "__class__") and extractor.__class__.__name__ == "DryRunExtractor":
        print("\n⚠  DRY RUN MODE — No API calls will be made.")
        print("   All fields will be empty. This tests pipeline logic only.")
        print("   To extract real data: set OPENAI_API_KEY and use --provider openai\n")

    # ── run extraction ────────────────────────────────────────────────────
    results = []
    wall_start = time.time()

    for i, (case_id, files) in enumerate(cases, 1):
        print(f"\n  [{i}/{len(cases)}] Processing {case_id}…")
        result = process_case(
            case_id=case_id,
            files=files,
            extractor=extractor,
            verbose=args.verbose,
        )
        results.append(result)

        status = "✅ READY" if result.packet_ready else "❌ NOT READY"
        missing_str = ", ".join(result.missing_fields[:4]) or "none"
        print(f"         Status: {status}")
        print(f"         Missing: {missing_str}")
        if result.conflicts:
            print(f"         Conflicts: {', '.join(c.field for c in result.conflicts)}")
        print(f"         Docs: {', '.join(result.document_types_detected) or 'unknown'}")
        print(f"         Runtime: {result.runtime_seconds:.1f}s")
        if result.cost_estimate_usd is not None:
            print(f"         Cost est: ~${result.cost_estimate_usd:.4f}")

    total_runtime = time.time() - wall_start

    # ── write artifacts ───────────────────────────────────────────────────
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": actual_provider,
        "input_dir": str(input_dir),
        "total_cases": len(results),
        "total_files": sum(len(r.input_files) for r in results),
        "total_runtime_seconds": round(total_runtime, 2),
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    from services.fiqa_api.ocr_kill_test.reporter import _failure_modes, write_report
    failure_modes = _failure_modes(results)
    verdict, verdict_explanation = write_report(results, meta, output_dir, report_path)

    print(f"\n  ✓ Results: {output_dir / 'results.json'}")
    print(f"  ✓ CSV:     {output_dir / 'results.csv'}")
    print(f"  ✓ Report:  {report_path}")

    # ── terminal summary ──────────────────────────────────────────────────
    print_terminal_summary(
        provider=actual_provider,
        results=results,
        verdict=verdict,
        verdict_explanation=verdict_explanation,
        failure_modes=failure_modes,
        report_path=report_path,
        output_dir=output_dir,
    )

    # Exit code: 0 = ran successfully (even if NO GO — that's valid data)
    sys.exit(0)


if __name__ == "__main__":
    main()
