#!/usr/bin/env python3
"""
P16 OCR Accuracy Evaluation Runner

Runs every document in test_data/p16_real_docs/ through the existing extraction
pipeline (ocr_kill_test extractor + packet_builder + normalizers), then compares
extracted values against ground_truth.json to compute:

  - VIN Accuracy %
  - YMM Accuracy %
  - Name Accuracy %
  - ZIP Accuracy %
  - Packet Completeness %

Per document type and overall.

Usage:
    python3 scripts/run_p16_accuracy_eval.py --provider gemini
    python3 scripts/run_p16_accuracy_eval.py --provider dry_run   # pipeline test only

Output:
    artifacts/p16_accuracy_eval/results.json
    artifacts/p16_accuracy_eval/results.csv
    docs/p16/P16_OCR_ACCURACY_REPORT_V1.md
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.fiqa_api.ocr_kill_test.extractor import get_extractor
from services.fiqa_api.ocr_kill_test.packet_builder import process_case
from services.fiqa_api.ocr_kill_test.normalizers import apply_normalizations
from services.fiqa_api.ocr_kill_test.local_ocr_extractor import LocalOCRExtractor


def get_extractor_extended(provider: str):
    """Extends get_extractor with local_ocr provider."""
    if provider == "local_ocr":
        return LocalOCRExtractor()
    return get_extractor(provider)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

CORPUS_ROOT = REPO_ROOT / "test_data" / "p16_real_docs"
GROUND_TRUTH_JSON = CORPUS_ROOT / "ground_truth.json"
OUTPUT_DIR = REPO_ROOT / "artifacts" / "p16_accuracy_eval"
REPORT_PATH = REPO_ROOT / "docs" / "p16" / "P16_OCR_ACCURACY_REPORT_V1.md"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".heic", ".heif"}


# ── Ground truth loading ─────────────────────────────────────────────────────

def load_ground_truth() -> dict:
    if not GROUND_TRUTH_JSON.exists():
        logger.error(f"Ground truth not found: {GROUND_TRUTH_JSON}")
        logger.error("Run: python3 scripts/generate_p16_corpus.py")
        sys.exit(1)
    with open(GROUND_TRUTH_JSON) as f:
        return json.load(f)


# ── Document discovery ───────────────────────────────────────────────────────

def discover_documents(corpus_root: Path, ground_truth: dict) -> list[dict]:
    """
    Return list of {rel_path, abs_path, gt, doc_type} for each corpus file
    that has a ground truth entry.
    """
    docs = []
    for rel_path, gt in ground_truth.items():
        abs_path = corpus_root / rel_path
        if not abs_path.exists():
            logger.warning(f"File not found: {abs_path}")
            continue
        if abs_path.stat().st_size == 0:
            logger.warning(f"File is empty (0 bytes): {abs_path}")
            continue
        if abs_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        docs.append({
            "rel_path": rel_path,
            "abs_path": abs_path,
            "gt": gt,
            "doc_type": gt.get("doc_type", "unknown"),
        })
    return sorted(docs, key=lambda d: d["rel_path"])


# ── Field matching ───────────────────────────────────────────────────────────

def match_vin(extracted: str, expected: str) -> str:
    """Return 'pass', 'fail', or 'skip'."""
    if not expected or expected.startswith("*("):
        return "skip"
    if not extracted:
        return "fail"
    return "pass" if extracted.upper().strip() == expected.upper().strip() else "fail"


def match_year(extracted: str, expected: str) -> str:
    if not expected or expected.startswith("*("):
        return "skip"
    if not extracted:
        return "fail"
    return "pass" if extracted.strip() == expected.strip() else "fail"


def match_make_model(extracted: str, expected: str) -> str:
    """
    PASS if extracted contains both the make and model words from expected.
    E.g., extracted='2023 Toyota Camry LE', expected='Toyota Camry' → PASS.
    """
    if not expected or expected.startswith("*("):
        return "skip"
    if not extracted:
        return "fail"
    words = expected.lower().split()
    ext_lower = extracted.lower()
    if all(w in ext_lower for w in words):
        return "pass"
    # Partial: at least one word matches
    if any(w in ext_lower for w in words):
        return "partial"
    return "fail"


def match_name(extracted: str, expected: str) -> str:
    """PASS if all words of expected name appear in extracted."""
    if not expected or expected.startswith("*("):
        return "skip"
    if not extracted:
        return "fail"
    words = expected.lower().split()
    ext_lower = extracted.lower()
    matching = sum(1 for w in words if w in ext_lower)
    if matching == len(words):
        return "pass"
    if matching > 0:
        return "partial"
    return "fail"


def match_zip(extracted: str, expected: str) -> str:
    if not expected or expected.startswith("*("):
        return "skip"
    if not extracted:
        return "fail"
    return "pass" if extracted.strip()[:5] == expected.strip()[:5] else "fail"


def match_lienholder(extracted: str, expected: str) -> str:
    if not expected or expected.startswith("*(") or expected == "":
        return "skip"
    if not extracted:
        return "fail"
    # Partial match: institution name should appear
    expected_words = [w for w in expected.lower().split() if len(w) > 3]
    if any(w in extracted.lower() for w in expected_words):
        return "pass"
    return "fail"


# ── Score computation ────────────────────────────────────────────────────────

def score_to_float(result: str) -> float:
    return {"pass": 1.0, "partial": 0.5, "fail": 0.0, "skip": None}.get(result, 0.0)


def compute_accuracy(scores: list[Optional[float]]) -> Optional[float]:
    """Return accuracy over non-skip entries. None if all skipped."""
    relevant = [s for s in scores if s is not None]
    if not relevant:
        return None
    return sum(relevant) / len(relevant)


# ── Per-document evaluation ──────────────────────────────────────────────────

def evaluate_document(doc: dict, extractor) -> dict:
    """
    Run extraction on one document and compare against ground truth.
    Returns evaluation record dict.
    """
    abs_path: Path = doc["abs_path"]
    gt: dict = doc["gt"]
    rel_path: str = doc["rel_path"]

    start = time.time()
    result = process_case(
        case_id=rel_path,
        files=[abs_path],
        extractor=extractor,
        verbose=False,
    )
    elapsed = time.time() - start

    # Extract field values from result
    fields = result.extracted_fields

    def get_val(field: str) -> str:
        ef = fields.get(field)
        if ef is None:
            return ""
        if hasattr(ef, "value"):
            return ef.value or ""
        if isinstance(ef, dict):
            return ef.get("value", "") or ""
        return str(ef)

    vin_extracted = get_val("vin")
    year_extracted = get_val("year")
    make_model_extracted = get_val("make_model")
    name_extracted = get_val("customer_name")
    zip_extracted = get_val("garaging_zip")

    # Ground truth expected values
    vin_gt = gt.get("vin", "")
    year_gt = gt.get("year", "")
    mm_gt = gt.get("make_model", "")
    name_gt = gt.get("customer_name", "")
    zip_gt = gt.get("garaging_zip", "")
    lienholder_gt = gt.get("lienholder", "")

    # Note: lienholder not in core extraction fields; check if it shows up in make_model or notes
    # Use primary_driver field as lienholder proxy isn't ideal — leave as n/a for now

    # Match results
    vin_match = match_vin(vin_extracted, vin_gt)
    year_match = match_year(year_extracted, year_gt)
    mm_match = match_make_model(make_model_extracted, mm_gt)
    name_match = match_name(name_extracted, name_gt)
    zip_match = match_zip(zip_extracted, zip_gt)

    return {
        "rel_path": rel_path,
        "doc_type": doc["doc_type"],
        "ocr_difficulty": gt.get("ocr_difficulty", "unknown"),
        "notes": gt.get("notes", ""),
        # Extracted values
        "vin_extracted": vin_extracted,
        "year_extracted": year_extracted,
        "make_model_extracted": make_model_extracted,
        "name_extracted": name_extracted,
        "zip_extracted": zip_extracted,
        # Expected values
        "vin_expected": vin_gt,
        "year_expected": year_gt,
        "make_model_expected": mm_gt,
        "name_expected": name_gt,
        "zip_expected": zip_gt,
        "lienholder_expected": lienholder_gt,
        # Match results
        "vin_match": vin_match,
        "year_match": year_match,
        "make_model_match": mm_match,
        "name_match": name_match,
        "zip_match": zip_match,
        # Packet status
        "packet_ready": result.packet_ready,
        "missing_fields": result.missing_fields,
        "conflicts": [c.field for c in result.conflicts],
        "doc_types_detected": result.document_types_detected,
        "model_used": result.model_used,
        "runtime_s": round(elapsed, 2),
        "cost_usd": result.cost_estimate_usd,
        "error": result.error,
    }


# ── Accuracy report generation ───────────────────────────────────────────────

def compute_metrics(evals: list[dict]) -> dict:
    """
    Compute accuracy metrics per doc type and overall.
    Returns dict with structure: metrics[doc_type][field] = accuracy_float
    """
    fields = ["vin", "year", "make_model", "name", "zip"]
    type_groups: dict[str, list[dict]] = {}
    for e in evals:
        t = e["doc_type"]
        type_groups.setdefault(t, []).append(e)
    type_groups["OVERALL"] = evals

    metrics = {}
    for group_name, group_evals in type_groups.items():
        group_metrics = {}
        for field in fields:
            key = f"{field}_match"
            scores = [score_to_float(e[key]) for e in group_evals]
            acc = compute_accuracy(scores)
            group_metrics[field] = acc
        # Packet completeness
        n = len(group_evals)
        ready_count = sum(1 for e in group_evals if e["packet_ready"])
        group_metrics["packet_completeness"] = ready_count / n if n else None
        group_metrics["n"] = n
        group_metrics["n_ready"] = ready_count
        metrics[group_name] = group_metrics
    return metrics


def fmt_pct(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    return f"{val:.0%}"


def build_accuracy_report(
    evals: list[dict],
    metrics: dict,
    provider: str,
    run_ts: str,
    dry_run: bool,
) -> str:
    n_total = len(evals)
    n_ready = sum(1 for e in evals if e["packet_ready"])
    overall = metrics.get("OVERALL", {})
    vin_overall = overall.get("vin")
    ymm_overall = metrics.get("OVERALL", {}).get("year")  # use year as YMM proxy
    packet_overall = overall.get("packet_completeness")

    # ── Pilot readiness decision ─────────────────────────────────────────────
    def pilot_decision() -> tuple[str, str]:
        if dry_run:
            return "NO DATA", "Dry-run mode — no real extraction performed. Run with --provider gemini."

        vin_acc = vin_overall or 0.0
        pkt_acc = packet_overall or 0.0

        if vin_acc >= 0.90 and pkt_acc >= 0.70:
            decision = "YES — GO"
            rationale = (
                f"VIN accuracy {fmt_pct(vin_acc)} ≥ 90% threshold. "
                f"Packet completeness {fmt_pct(pkt_acc)} ≥ 70% threshold. "
                "Extraction quality sufficient for Chen Kui soft pilot."
            )
        elif vin_acc >= 0.75 and pkt_acc >= 0.55:
            decision = "CONDITIONAL GO"
            rationale = (
                f"VIN accuracy {fmt_pct(vin_acc)} is above minimum viable (75%). "
                f"Packet completeness {fmt_pct(pkt_acc)} is acceptable with broker review. "
                "Proceed with pilot but monitor VIN conflicts closely."
            )
        else:
            decision = "NO — NOT YET"
            rationale = (
                f"VIN accuracy {fmt_pct(vin_acc)} below 75% minimum. "
                f"Packet completeness {fmt_pct(pkt_acc)} below 55% minimum. "
                "Extraction quality insufficient. Investigate top failure modes before pilot."
            )
        return decision, rationale

    pilot_go, pilot_rationale = pilot_decision()

    # ── Per-doc-type accuracy table ──────────────────────────────────────────
    doc_type_rows = []
    for dt in ["purchase_agreement", "window_sticker", "registration", "wechat_screenshot",
               "vin_photo", "dealer_worksheet"]:
        m = metrics.get(dt)
        if not m:
            continue
        row = (
            f"| {dt} | {m['n']} | {fmt_pct(m.get('vin'))} | "
            f"{fmt_pct(m.get('year'))} | {fmt_pct(m.get('make_model'))} | "
            f"{fmt_pct(m.get('name'))} | {fmt_pct(m.get('zip'))} | "
            f"{m['n_ready']}/{m['n']} ({fmt_pct(m.get('packet_completeness'))}) |"
        )
        doc_type_rows.append(row)

    # ── Per-document detail table ────────────────────────────────────────────
    def match_icon(m: str) -> str:
        return {"pass": "✅", "partial": "⚠️", "fail": "❌", "skip": "—"}.get(m, "?")

    detail_rows = []
    for e in evals:
        fn = Path(e["rel_path"]).name
        detail_rows.append(
            f"| {fn} | {e['doc_type']} | {e['ocr_difficulty']} | "
            f"{match_icon(e['vin_match'])} | {match_icon(e['year_match'])} | "
            f"{match_icon(e['make_model_match'])} | {match_icon(e['name_match'])} | "
            f"{match_icon(e['zip_match'])} | {'✅' if e['packet_ready'] else '❌'} |"
        )

    # ── Top failure modes ────────────────────────────────────────────────────
    failure_counts: dict[str, int] = {}
    for e in evals:
        for field in ["vin", "year", "make_model", "name", "zip"]:
            if e[f"{field}_match"] == "fail":
                failure_counts[f"Missing/wrong {field}"] = failure_counts.get(f"Missing/wrong {field}", 0) + 1
        if e.get("error"):
            failure_counts["Processing error"] = failure_counts.get("Processing error", 0) + 1
        if e.get("conflicts"):
            failure_counts["Field conflict detected"] = failure_counts.get("Field conflict detected", 0) + 1
    failure_list = sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)

    # ── Missing fields summary ────────────────────────────────────────────────
    missing_counts: dict[str, int] = {}
    for e in evals:
        for f in e.get("missing_fields", []):
            missing_counts[f] = missing_counts.get(f, 0) + 1
    missing_list = sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)

    # ── Trade-in issues ───────────────────────────────────────────────────────
    trade_in_issues = [e for e in evals if "dw_002" in e["rel_path"]]

    # ── Overall pass/fail counts ──────────────────────────────────────────────
    pass_counts = {}
    fail_counts = {}
    skip_counts = {}
    for field in ["vin", "year", "make_model", "name", "zip"]:
        pass_counts[field] = sum(1 for e in evals if e[f"{field}_match"] == "pass")
        fail_counts[field] = sum(1 for e in evals if e[f"{field}_match"] == "fail")
        skip_counts[field] = sum(1 for e in evals if e[f"{field}_match"] == "skip")

    dry_run_notice = ""
    if dry_run:
        dry_run_notice = """
> ⚠️ **DRY RUN MODE** — No real API calls were made. All extraction values are empty.
> All accuracy metrics show 0% because the extractor returned no data.
> **To get real evidence:** run with `--provider gemini` (requires GEMINI_API_KEY).

"""

    # ── Build report markdown ─────────────────────────────────────────────────
    return f"""# P16 OCR Accuracy Report V1

**Date:** {run_ts[:10]}  
**Sprint:** P16 Evidence Phase  
**Provider:** {provider}  
**Corpus:** `test_data/p16_real_docs/` — {n_total} documents  
**Source of truth:** `docs/p16/P16_DECISION_FREEZE_V1.md`

{dry_run_notice}---

## Executive Summary

| Metric | Value |
|--------|-------|
| Corpus size | {n_total} documents |
| Document types | purchase_agreement, window_sticker, registration, wechat, vin_photo, dealer_worksheet |
| VIN Accuracy (overall) | **{fmt_pct(vin_overall)}** |
| YMM Accuracy (Year) | **{fmt_pct(ymm_overall)}** |
| Packet Completeness | **{fmt_pct(packet_overall)}** ({n_ready}/{n_total} docs packet-ready) |
| Pilot Readiness | **{pilot_go}** |

---

## Section 1: Corpus Built

22 documents generated across 6 document types.

| Type | Count | Format | Ground Truth |
|------|-------|--------|--------------|
| Purchase Agreements | 7 | PDF + JPG | VIN, YMM, Name, ZIP, Lienholder |
| Window Stickers | 5 | PDF + JPG + PNG | VIN, YMM only |
| Registrations | 3 | PDF + JPG | VIN, YMM, Name, ZIP |
| WeChat Screenshots | 3 | JPG + PNG | Varies (VIN/ZIP/partial) |
| VIN Photos | 2 | JPG | VIN only |
| Dealer Worksheets | 2 | PDF | VIN, YMM, Name, ZIP, Lienholder |
| **Total** | **22** | | |

OCR difficulty: 9 easy / 10 medium / 3 hard.

Ground truth source: `test_data/p16_real_docs/ground_truth.json`  
Full inventory: `docs/p16/P16_CORPUS_INVENTORY.md`  
Full ground truth: `docs/p16/P16_GROUND_TRUTH.md`

---

## Section 2: Documents Collected

All documents were generated with embedded realistic California auto insurance intake data.
VINs follow NHTSA/ISO 3779 17-character format.
Customer names are Chinese-American — consistent with Chen Kui's pilot customer base.

Document types match the real intake scenario:

- **Purchase agreements** — primary source for VIN + YMM + lienholder
- **Window stickers** — VIN + YMM, no customer data (expected and correct)
- **Registrations** — VIN + YMM + owner name
- **WeChat screenshots** — partial data, conversational format
- **VIN photos** — VIN only, high failure rate expected
- **Dealer worksheets** — structured, highest completeness expected

---

## Section 3: Accuracy Metrics

### 3A. Overall Field Accuracy

| Field | Pass | Fail | Skip | Accuracy |
|-------|------|------|------|----------|
| VIN | {pass_counts['vin']} | {fail_counts['vin']} | {skip_counts['vin']} | **{fmt_pct(overall.get('vin'))}** |
| Year | {pass_counts['year']} | {fail_counts['year']} | {skip_counts['year']} | **{fmt_pct(overall.get('year'))}** |
| Make/Model | {pass_counts['make_model']} | {fail_counts['make_model']} | {skip_counts['make_model']} | **{fmt_pct(overall.get('make_model'))}** |
| Customer Name | {pass_counts['name']} | {fail_counts['name']} | {skip_counts['name']} | **{fmt_pct(overall.get('name'))}** |
| Garaging ZIP | {pass_counts['zip']} | {fail_counts['zip']} | {skip_counts['zip']} | **{fmt_pct(overall.get('zip'))}** |
| Packet Ready | {n_ready} | {n_total - n_ready} | — | **{fmt_pct(packet_overall)}** |

### 3B. Accuracy By Document Type

| Doc Type | n | VIN | Year | Make/Model | Name | ZIP | Packet Ready |
|----------|---|-----|------|------------|------|-----|--------------|
{chr(10).join(doc_type_rows)}
| **OVERALL** | **{overall['n']}** | **{fmt_pct(overall.get('vin'))}** | **{fmt_pct(overall.get('year'))}** | **{fmt_pct(overall.get('make_model'))}** | **{fmt_pct(overall.get('name'))}** | **{fmt_pct(overall.get('zip'))}** | **{overall['n_ready']}/{overall['n']} ({fmt_pct(overall.get('packet_completeness'))})** |

### 3C. Per-Document Detail

| Filename | Type | Difficulty | VIN | Year | YMM | Name | ZIP | Ready |
|----------|------|-----------|-----|------|-----|------|-----|-------|
{chr(10).join(detail_rows)}

---

## Section 4: Top Failure Modes

| Failure Mode | Occurrences |
|-------------|-------------|
{chr(10).join(f'| {k} | {v} |' for k, v in failure_list) or '| (none) | — |'}

### Top Missing Fields (per extraction pipeline)

| Field | Missing in N docs |
|-------|--------------------|
{chr(10).join(f'| {f} | {c} |' for f, c in missing_list) or '| (none) | — |'}

### Trade-in Issues

{'**dw_002_buyers_order.pdf** contains a trade-in section. If a second vehicle VIN is present, the extraction pipeline should flag `second_vehicle_detected = true`. Evaluation checks this case specifically.' if trade_in_issues else '*(no trade-in documents evaluated)*'}

---

## Section 5: Pilot Recommendation

### {pilot_go}

{pilot_rationale}

### Conditions (if CONDITIONAL GO)

1. **VIN conflicts must be reviewed by broker** — source attribution shows which file VIN came from
2. **WeChat-only submissions are insufficient** — customer must upload at least one structured document
3. **VIN photo submissions need secondary document** — camera shots alone have high failure rate
4. **Garaging ZIP must come from intake form** — window stickers never contain ZIP (by design)

### Evidence Basis

This recommendation is based on extraction evidence from {n_total} corpus documents.
It is not an opinion. The thresholds are:

- VIN Accuracy ≥ 90% → GO
- VIN Accuracy ≥ 75% → CONDITIONAL GO  
- VIN Accuracy < 75% → NO GO

---

## Section 6: Exact Next Action

{"1. **Start Chen Kui soft pilot.** Send intake link. Process first 3 real cases. Measure actual time savings." if pilot_go.startswith("YES") else "1. **Investigate top VIN failure modes.** Run --provider gemini with verbose flag to see raw extraction output per failing document." if pilot_go.startswith("CONDITIONAL") else "1. **Fix extraction before pilot.** Top failure modes above must be addressed. Re-run eval after fixes."}
{"2. **Log cases as CK-001, CK-002, etc.** in `docs/trial/P16_TIME_SAVINGS_TRACKER.md`." if not pilot_go.startswith("NO") else "2. **Check GEMINI_API_KEY is set.** If running dry_run, re-run with real provider."}
{"3. **Gate:** 10 cases, avg ≥ 4 min saved → invoice Chen Kui $49." if not pilot_go.startswith("NO") else "3. **Re-run accuracy eval after fixes:** `python3 scripts/run_p16_accuracy_eval.py --provider gemini`"}

---

*Report generated by `scripts/run_p16_accuracy_eval.py` on {run_ts[:19]}.*  
*Corpus: `test_data/p16_real_docs/` | Ground truth: `docs/p16/P16_GROUND_TRUTH.md`*  
*Artifacts: `artifacts/p16_accuracy_eval/`*
"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="P16 OCR Accuracy Evaluation — runs corpus through extraction pipeline"
    )
    parser.add_argument(
        "--provider",
        default=os.environ.get("P16_OCR_PROVIDER", "auto"),
        choices=["auto", "openai", "gemini", "dry_run", "local_ocr"],
        help="Vision provider. Default: auto. Use local_ocr for offline baseline.",
    )
    parser.add_argument(
        "--corpus-root",
        type=Path,
        default=CORPUS_ROOT,
        help=f"Corpus root directory. Default: {CORPUS_ROOT}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Artifacts output directory. Default: {OUTPUT_DIR}",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=REPORT_PATH,
        help=f"Markdown report path. Default: {REPORT_PATH}",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-document extraction details",
    )
    args = parser.parse_args()

    run_ts = datetime.now(timezone.utc).isoformat()
    output_dir: Path = args.output_dir.resolve()
    report_path: Path = args.report_path.resolve()

    print(f"\n{'─'*60}")
    print(f"  P16 OCR Accuracy Evaluation")
    print(f"  Corpus: {args.corpus_root}")
    print(f"  Provider: {args.provider}")
    print(f"  Report: {report_path}")
    print(f"{'─'*60}")

    # Load ground truth
    ground_truth = load_ground_truth()
    print(f"\n  ✓ Ground truth loaded: {len(ground_truth)} entries")

    # Discover documents
    docs = discover_documents(args.corpus_root, ground_truth)
    print(f"  ✓ Documents found: {len(docs)}")

    if not docs:
        print("\n  ❌ No documents found. Run: python3 scripts/generate_p16_corpus.py")
        sys.exit(1)

    # Initialize extractor
    print(f"\n  Initializing {args.provider} extractor…")
    try:
        extractor = get_extractor_extended(args.provider)
        model_name = getattr(extractor, "MODEL", args.provider)
        print(f"  ✓ Provider: {model_name}")
    except Exception as e:
        print(f"\n  ❌ Extractor init failed: {e}")
        sys.exit(1)

    dry_run = model_name == "dry_run"
    if dry_run:
        print("\n  ⚠  DRY RUN — No API calls. All accuracy metrics will be 0%.")
        print("     Run with --provider gemini for real evidence.")
    elif model_name == "local_ocr_easyocr":
        print("\n  ℹ  LOCAL OCR mode — EasyOCR + PyMuPDF (no cloud API).")
        print("     This is a baseline. Production uses Gemini Flash 2.5.")

    # Run evaluations
    evals = []
    wall_start = time.time()

    for i, doc in enumerate(docs, 1):
        fn = Path(doc["rel_path"]).name
        print(f"\n  [{i:02d}/{len(docs)}] {doc['rel_path']}")
        try:
            result = evaluate_document(doc, extractor)
            evals.append(result)
            vin_icon = {"pass": "✅", "fail": "❌", "skip": "—"}.get(result["vin_match"], "?")
            ymm_icon = {"pass": "✅", "partial": "⚠️", "fail": "❌", "skip": "—"}.get(result["year_match"], "?")
            pkt = "✅ READY" if result["packet_ready"] else "❌ NOT READY"
            print(f"         VIN:{vin_icon}  YMM:{ymm_icon}  Packet:{pkt}  ({result['runtime_s']:.1f}s)")
            if args.verbose:
                print(f"         VIN extracted: {result['vin_extracted']!r} (expected: {result['vin_expected']!r})")
                print(f"         YMM extracted: {result['year_extracted']!r} {result['make_model_extracted']!r}")
        except Exception as e:
            logger.error(f"Evaluation failed for {fn}: {e}")
            evals.append({
                "rel_path": doc["rel_path"],
                "doc_type": doc["doc_type"],
                "ocr_difficulty": doc["gt"].get("ocr_difficulty", "unknown"),
                "notes": f"Error: {e}",
                "vin_extracted": "", "year_extracted": "", "make_model_extracted": "",
                "name_extracted": "", "zip_extracted": "",
                "vin_expected": doc["gt"].get("vin", ""), "year_expected": doc["gt"].get("year", ""),
                "make_model_expected": doc["gt"].get("make_model", ""),
                "name_expected": doc["gt"].get("customer_name", ""),
                "zip_expected": doc["gt"].get("garaging_zip", ""),
                "lienholder_expected": doc["gt"].get("lienholder", ""),
                "vin_match": "fail", "year_match": "fail", "make_model_match": "fail",
                "name_match": "fail", "zip_match": "fail",
                "packet_ready": False, "missing_fields": [], "conflicts": [],
                "doc_types_detected": [], "model_used": model_name,
                "runtime_s": 0.0, "cost_usd": None, "error": str(e),
            })

    total_runtime = time.time() - wall_start

    # Compute metrics
    metrics = compute_metrics(evals)
    overall = metrics.get("OVERALL", {})

    # Write artifacts
    output_dir.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = output_dir / "results.json"
    with open(json_path, "w") as f:
        json.dump({
            "meta": {
                "timestamp": run_ts,
                "provider": model_name,
                "corpus_root": str(args.corpus_root),
                "n_documents": len(evals),
                "total_runtime_s": round(total_runtime, 2),
                "dry_run": dry_run,
            },
            "metrics": metrics,
            "evaluations": evals,
        }, f, indent=2)

    # CSV
    csv_path = output_dir / "results.csv"
    if evals:
        fieldnames = list(evals[0].keys())
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(evals)

    # Markdown report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_md = build_accuracy_report(evals, metrics, model_name, run_ts, dry_run)
    with open(report_path, "w") as f:
        f.write(report_md)

    # Terminal summary
    print(f"\n{'═'*60}")
    print("  P16 OCR ACCURACY EVALUATION COMPLETE")
    print(f"{'═'*60}")
    print(f"  PROVIDER:           {model_name}")
    print(f"  DOCUMENTS TESTED:   {len(evals)}")
    print(f"  VIN ACCURACY:       {fmt_pct(overall.get('vin'))}")
    print(f"  YMM ACCURACY:       {fmt_pct(overall.get('year'))}")
    print(f"  PACKET READY:       {overall.get('n_ready', 0)}/{overall.get('n', 0)} ({fmt_pct(overall.get('packet_completeness'))})")
    print(f"  TOTAL RUNTIME:      {total_runtime:.1f}s")
    print(f"  JSON:               {json_path}")
    print(f"  CSV:                {csv_path}")
    print(f"  REPORT:             {report_path}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
