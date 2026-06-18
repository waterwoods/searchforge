"""
P16 OCR Kill Test — report generator.

Produces:
  - results.json
  - results.csv
  - P16_OCR_KILL_TEST_REPORT.md (written to docs/trial/)
"""
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .schema import CORE_FIELDS, REQUIRED_FOR_PACKET_READY, ExtractedField, KillTestResult


def _go_decision(results: list[KillTestResult]) -> tuple[str, str]:
    """
    Returns (verdict, explanation).
    GO / CONDITIONAL GO / NO GO
    """
    n = len(results)
    if n == 0:
        return "NO GO", "No cases were tested."

    ready_count = sum(1 for r in results if r.packet_ready)
    ready_rate = ready_count / n

    # VIN extraction rate on cases that had VIN in any source
    vin_attempts = []
    for r in results:
        ef = r.extracted_fields.get("vin", ExtractedField()) if isinstance(r.extracted_fields, dict) else None
        if ef and isinstance(ef, ExtractedField):
            vin_attempts.append(ef)
    vin_present = [v for v in vin_attempts if v.is_present()]
    vin_rate = len(vin_present) / len(vin_attempts) if vin_attempts else None

    # Check for invented values (confidence > 0 but value looks suspicious)
    # Simple heuristic: if any field has value but source_quote is empty AND confidence > 0.5
    invented_flag = False
    for r in results:
        for fname, ef in r.extracted_fields.items():
            if isinstance(ef, ExtractedField):
                if ef.is_present() and not ef.source_quote and ef.confidence > 0.7:
                    invented_flag = True

    # Determine verdict
    provisional = n < 10

    if ready_rate >= 0.7 and (vin_rate is None or vin_rate >= 0.9) and not invented_flag:
        verdict = "GO"
        if provisional:
            verdict = "PROVISIONAL GO"
        explanation = (
            f"{ready_count}/{n} cases packet-ready ({ready_rate:.0%}). "
            f"VIN extraction: {f'{vin_rate:.0%}' if vin_rate is not None else 'N/A'}. "
            "No critical invented fields detected."
        )
    elif ready_rate >= 0.5:
        verdict = "CONDITIONAL GO"
        if provisional:
            verdict = "PROVISIONAL CONDITIONAL GO"
        explanation = (
            f"{ready_count}/{n} cases packet-ready ({ready_rate:.0%}). "
            f"VIN extraction: {f'{vin_rate:.0%}' if vin_rate is not None else 'N/A'}. "
            "Customer confirmation can address most gaps."
        )
    else:
        verdict = "NO GO"
        explanation = (
            f"Only {ready_count}/{n} cases packet-ready ({ready_rate:.0%}). "
            f"VIN extraction: {f'{vin_rate:.0%}' if vin_rate is not None else 'N/A'}. "
            "Extraction quality insufficient for production use."
        )

    if provisional:
        explanation += f" [PROVISIONAL — only {n}/10 cases tested]"

    return verdict, explanation


def _failure_modes(results: list[KillTestResult]) -> list[str]:
    """Identify top failure modes across all results."""
    modes = {}

    for r in results:
        for f in r.missing_fields:
            key = f"Missing field: {f}"
            modes[key] = modes.get(key, 0) + 1

        if r.second_vehicle_detected:
            modes["Second vehicle detected"] = modes.get("Second vehicle detected", 0) + 1

        if r.unrelated_documents:
            modes["Unrelated document in packet"] = modes.get("Unrelated document in packet", 0) + 1

        for c in r.conflicts:
            key = f"Conflict: {c.field}"
            modes[key] = modes.get(key, 0) + 1

        if r.error:
            modes[f"Processing error: {r.error[:60]}"] = modes.get(f"Processing error: {r.error[:60]}", 0) + 1

    sorted_modes = sorted(modes.items(), key=lambda x: x[1], reverse=True)
    return [f"{v}x {k}" for k, v in sorted_modes[:8]]


def save_json(results: list[KillTestResult], output_path: Path, meta: dict) -> None:
    data = {
        "meta": meta,
        "cases": [r.to_dict() for r in results],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_csv(results: list[KillTestResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in results:
        row = {
            "case_id": r.case_id,
            "packet_ready": r.packet_ready,
            "missing_fields": "; ".join(r.missing_fields),
            "conflicts": "; ".join(c.field for c in r.conflicts),
            "doc_types": "; ".join(r.document_types_detected),
            "second_vehicle": r.second_vehicle_detected,
            "runtime_s": r.runtime_seconds,
            "cost_usd": r.cost_estimate_usd,
            "model": r.model_used,
            "error": r.error or "",
        }
        for field in CORE_FIELDS:
            ef = r.extracted_fields.get(field, ExtractedField())
            if isinstance(ef, ExtractedField):
                row[f"{field}_value"] = ef.value
                row[f"{field}_conf"] = f"{ef.confidence:.2f}"
            else:
                row[f"{field}_value"] = ""
                row[f"{field}_conf"] = ""
        rows.append(row)

    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(
    results: list[KillTestResult],
    meta: dict,
    verdict: str,
    verdict_explanation: str,
    failure_modes: list[str],
) -> str:
    n = len(results)
    ready_count = sum(1 for r in results if r.packet_ready)
    total_files = sum(len(r.input_files) for r in results)
    provider = meta.get("provider", "unknown")
    ts = meta.get("timestamp", "")

    # Field extraction table
    field_rows = []
    for field in CORE_FIELDS:
        present = sum(
            1 for r in results
            if isinstance(r.extracted_fields.get(field), ExtractedField)
            and r.extracted_fields[field].is_present()
        )
        avg_conf = 0.0
        conf_vals = [
            r.extracted_fields[field].confidence
            for r in results
            if isinstance(r.extracted_fields.get(field), ExtractedField)
            and r.extracted_fields[field].is_present()
        ]
        if conf_vals:
            avg_conf = sum(conf_vals) / len(conf_vals)
        field_rows.append(
            f"| {field} | {present}/{n} | {avg_conf:.0%} |"
        )

    field_table = "\n".join(field_rows)

    # Missing fields table
    missing_counts: dict[str, int] = {}
    for r in results:
        for f in r.missing_fields:
            missing_counts[f] = missing_counts.get(f, 0) + 1
    missing_table = "\n".join(
        f"| {f} | {cnt}/{n} |"
        for f, cnt in sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)
    ) or "| (none) | — |"

    # Conflict table
    conflict_counts: dict[str, int] = {}
    for r in results:
        for c in r.conflicts:
            conflict_counts[c.field] = conflict_counts.get(c.field, 0) + 1
    conflict_table = "\n".join(
        f"| {f} | {cnt}/{n} |"
        for f, cnt in sorted(conflict_counts.items(), key=lambda x: x[1], reverse=True)
    ) or "| (none) | — |"

    # Per-case summary
    case_rows = []
    for r in results:
        ready_str = "✅ READY" if r.packet_ready else "❌ NOT READY"
        missing_str = ", ".join(r.missing_fields[:3]) + ("…" if len(r.missing_fields) > 3 else "")
        conflict_str = ", ".join(c.field for c in r.conflicts[:2])
        doc_str = ", ".join(r.document_types_detected[:2])
        case_rows.append(
            f"| {r.case_id} | {ready_str} | {doc_str or '—'} | {missing_str or '—'} | {conflict_str or '—'} |"
        )
    case_table = "\n".join(case_rows) or "| (no cases) | — | — | — | — |"

    failure_list = "\n".join(f"- {m}" for m in failure_modes) or "- None detected"

    # Time savings estimate
    avg_manual_minutes = 7
    time_saved_str = (
        f"~{ready_count * avg_manual_minutes} minutes saved across {ready_count} ready cases "
        f"(est. {avg_manual_minutes} min/case)"
    ) if ready_count > 0 else "0 minutes (no ready cases)"

    verdict_emoji = {"GO": "✅", "CONDITIONAL GO": "⚠️", "NO GO": "❌"}.get(
        verdict.replace("PROVISIONAL ", ""), "❓"
    )

    return f"""# P16 OCR Kill Test Report

**Generated:** {ts}  
**Provider:** {provider}  
**Status:** This is a kill-test report. Not a production deployment.

---

## Summary

| Metric | Value |
|--------|-------|
| Total cases tested | {n} |
| Total files processed | {total_files} |
| Provider used | {provider} |
| Packet-ready cases | {ready_count}/{n} ({f"{ready_count/n:.0%}" if n else "—"}) |
| Estimated time saved | {time_saved_str} |

---

## GO / NO GO Decision

### {verdict_emoji} {verdict}

{verdict_explanation}

---

## 4. Field-Level Extraction Table

| Field | Extracted (n/{n}) | Avg Confidence |
|-------|-------------------|----------------|
{field_table}

---

## 5. Missing Fields Table

| Field | Missing (n/{n}) |
|-------|-----------------|
{missing_table}

---

## 6. Conflict Table

| Field | Conflicts (n/{n}) |
|-------|-------------------|
{conflict_table}

---

## 7. Per-Case Results

| Case | Status | Doc Types | Missing Fields | Conflicts |
|------|--------|-----------|----------------|-----------|
{case_table}

---

## 8. Estimated Time Saved

{time_saved_str}

Manual add-car packet assembly baseline: ~{avg_manual_minutes} minutes/case (Chen Kui / Wu Xiaojie estimate).

---

## 9. Top Failure Modes

{failure_list}

---

## 10. Next Recommended Action

See: `docs/trial/P16_OCR_KILL_TEST_CERTIFICATION.md`

---

*Report auto-generated by `scripts/run_p16_ocr_kill_test.py`*  
*Artifacts: `artifacts/p16_ocr_kill_test/`*
"""


def write_report(
    results: list[KillTestResult],
    meta: dict,
    output_dir: Path,
    report_path: Path,
) -> tuple[str, str]:
    """
    Write all artifacts and return (verdict, verdict_explanation).
    """
    verdict, explanation = _go_decision(results)
    failure_modes = _failure_modes(results)

    save_json(results, output_dir / "results.json", meta)
    save_csv(results, output_dir / "results.csv")

    md = build_markdown_report(results, meta, verdict, explanation, failure_modes)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

    return verdict, explanation
