"""
P16 OCR Kill Test — packet readiness evaluator and packet draft generator.

Kill-test only. Not wired into production flows.
"""
import logging

logger = logging.getLogger(__name__)

from .schema import (
    ConflictRecord,
    ExtractedField,
    KillTestResult,
    CORE_FIELDS,
    REQUIRED_FOR_PACKET_READY,
)
from .normalizers import apply_normalizations


def _merge_extractions(per_file_results: list[dict], file_names: list[str]) -> dict:
    """
    Merge field extractions from multiple files into a single best-value dict.

    Strategy: take highest-confidence value per field.
    If two non-empty values disagree, record a conflict.
    """
    merged = {}
    conflicts = []

    for field in CORE_FIELDS:
        best = None
        best_source = ""
        all_values = []

        for result, fname in zip(per_file_results, file_names):
            raw_fields = result.get("fields", {})
            if field not in raw_fields:
                continue
            fdata = raw_fields[field]
            val = (fdata.get("value") or "").strip()
            conf = fdata.get("confidence", 0.0)
            if not val:
                continue
            all_values.append((val, conf, fname, fdata))
            if best is None or conf > best[1]:
                best = (val, conf, fname, fdata)
                best_source = fname

        if best is None:
            merged[field] = ExtractedField(
                value="",
                confidence=0.0,
                needs_confirmation=True,
                notes="Not found in any document",
            )
        else:
            fdata = best[3]
            merged[field] = ExtractedField(
                value=best[0],
                confidence=best[1],
                source_file=best_source,
                source_quote=fdata.get("source_quote", ""),
                needs_confirmation=fdata.get("needs_confirmation", True),
                notes=fdata.get("notes", ""),
            )

        # Check for conflicts
        unique_vals = list({v[0].upper() if field in ("vin",) else v[0] for v in all_values})
        if len(unique_vals) > 1:
            conflicts.append(ConflictRecord(
                field=field,
                values=[v[0] for v in all_values],
                sources=[v[2] for v in all_values],
                notes=f"Conflicting values found across {len(all_values)} sources",
            ))

    # Also pull cross-file conflicts from model-reported conflicts
    for result, fname in zip(per_file_results, file_names):
        for c in result.get("conflicts_found", []):
            field_name = c.get("field", "unknown")
            conflicts.append(ConflictRecord(
                field=field_name,
                values=[c.get("value_a", ""), c.get("value_b", "")],
                sources=[c.get("source_a", fname), c.get("source_b", fname)],
                notes=c.get("notes", "Model-reported conflict"),
            ))

    return {"fields": merged, "conflicts": conflicts}


def evaluate_packet_readiness(
    fields: dict[str, ExtractedField],
    conflicts: list[ConflictRecord],
    second_vehicle_detected: bool,
) -> tuple[bool, str]:
    """
    Returns (packet_ready: bool, reason: str).
    """
    missing = [f for f in REQUIRED_FOR_PACKET_READY if not fields.get(f, ExtractedField()).is_present()]

    if second_vehicle_detected:
        return False, "Second vehicle detected — cannot build single-vehicle packet until resolved"

    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    # Check for critical-field conflicts
    critical = {"vin", "year", "make_model"}
    critical_conflicts = [c for c in conflicts if c.field in critical]
    if critical_conflicts:
        cf_names = ", ".join(c.field for c in critical_conflicts)
        return False, f"Conflicting values for critical fields: {cf_names} — customer confirmation required"

    if not fields.get("vin", ExtractedField()).is_present():
        return False, "VIN is missing — cannot generate quote"

    return True, "All required fields present with no unresolved critical conflicts"


def build_packet_draft(
    case_id: str,
    fields: dict[str, ExtractedField],
    missing_fields: list[str],
    conflicts: list[ConflictRecord],
    packet_ready: bool,
    packet_readiness_reason: str,
    document_types: list[str],
    unrelated_docs: list[str],
    input_files: list[str],
) -> str:
    """Generate a human-readable quote-ready packet draft."""

    def fval(key: str) -> str:
        ef = fields.get(key, ExtractedField())
        if ef.is_present():
            conf_str = f" [conf: {ef.confidence:.0%}]" if ef.confidence < 0.8 else ""
            confirm_str = " ⚠ CONFIRM" if ef.needs_confirmation else ""
            return f"{ef.value}{conf_str}{confirm_str}"
        return "(not found)"

    still_needed = []
    for f in REQUIRED_FOR_PACKET_READY:
        ef = fields.get(f, ExtractedField())
        if not ef.is_present():
            still_needed.append(f.replace("_", " ").title())
    # Primary driver is surfaced but not blocking
    pd = fields.get("primary_driver", ExtractedField())
    if not pd.is_present():
        still_needed.append("Primary Driver (advisory)")

    conflict_lines = []
    for c in conflicts:
        vals_str = " vs ".join(c.values)
        conflict_lines.append(f"  • {c.field}: {vals_str} (sources: {', '.join(c.sources)})")

    source_lines = []
    for fname in input_files:
        relevant = [
            f"{k}: {ef.value}"
            for k, ef in fields.items()
            if ef.source_file == fname and ef.is_present()
        ]
        if relevant:
            source_lines.append(f"  {fname} → {'; '.join(relevant)}")
        else:
            source_lines.append(f"  {fname} → (no fields extracted)")

    if packet_ready:
        action = "✅ READY TO QUOTE — All required fields present. Send to carrier."
    elif conflicts:
        action = "⚠ BROKER REVIEW REQUIRED — Conflicting data must be resolved before quoting."
    elif still_needed:
        action = "📋 NEED CUSTOMER CLARIFICATION — Request missing information from customer."
    else:
        action = "⚠ BROKER REVIEW REQUIRED — Review extraction results."

    unrelated_str = ""
    if unrelated_docs:
        unrelated_str = f"\nUnrelated Documents Detected:\n  {chr(10).join(unrelated_docs)}\n"

    doc_type_str = ", ".join(document_types) if document_types else "unknown"

    draft = f"""ADD-CAR QUOTE PACKET
Case: {case_id}
Document Types: {doc_type_str}

────────────────────────────────────────
Customer:
  Name:   {fval("customer_name")}
  Phone:  {fval("phone")}

Vehicle:
  Year:              {fval("year")}
  Make / Model:      {fval("make_model")}
  VIN:               {fval("vin")}
  Garaging ZIP:      {fval("garaging_zip")}

Dates:
  Delivery / Effective Date: {fval("delivery_or_effective_date")}

Driver:
  Primary Driver: {fval("primary_driver")}

────────────────────────────────────────
Still Needed:
{chr(10).join(f"  • {s}" for s in still_needed) if still_needed else "  (none — packet complete)"}

Conflicts:
{chr(10).join(conflict_lines) if conflict_lines else "  (none detected)"}
{unrelated_str}
Source Evidence:
{chr(10).join(source_lines) if source_lines else "  (no files processed)"}

────────────────────────────────────────
Suggested Next Action:
  {action}

Packet Readiness: {"READY" if packet_ready else "NOT READY"}
Reason: {packet_readiness_reason}
────────────────────────────────────────
"""
    return draft


def process_case(
    case_id: str,
    files: list,
    extractor,
    verbose: bool = False,
) -> KillTestResult:
    """
    Run extraction on all files for a case, merge results, evaluate readiness.

    Returns a KillTestResult.
    """
    import time
    from pathlib import Path

    start = time.time()
    result = KillTestResult(case_id=case_id)
    result.input_files = [f.name if hasattr(f, "name") else str(f) for f in files]

    if not files:
        result.error = "No files in case"
        result.packet_readiness_reason = "No files provided"
        return result

    per_file_results = []
    doc_types = []
    unrelated_docs = []
    second_vehicle = False
    model_used = ""
    total_images = 0

    for fpath in files:
        fpath = Path(fpath)
        if verbose:
            print(f"    Extracting: {fpath.name}")
        try:
            extraction = extractor.extract(fpath)
            per_file_results.append(extraction)
            dt = extraction.get("document_type", "unknown")
            doc_types.append(dt)
            if dt == "unrelated":
                unrelated_docs.append(fpath.name)
            if extraction.get("second_vehicle_detected"):
                second_vehicle = True
            model_used = extraction.get("_model", model_used)
            total_images += extraction.get("_cost_images", 1)
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Extraction failed for {fpath.name}: {err_msg[:120]}")
            per_file_results.append({
                "document_type": "error",
                "second_vehicle_detected": False,
                "fields": {},
                "conflicts_found": [],
                "_error": err_msg,
            })
            doc_types.append("error")
            if result.error is None:
                result.error = f"{fpath.name}: {err_msg[:80]}"

    # Apply normalizations to all per-file fields
    for r in per_file_results:
        if "fields" in r:
            apply_normalizations(r["fields"])

    # Merge across files
    merged = _merge_extractions(per_file_results, result.input_files)
    fields = merged["fields"]
    conflicts = merged["conflicts"]

    # De-dupe conflicts by field
    seen_conflict_fields = set()
    unique_conflicts = []
    for c in conflicts:
        key = (c.field, tuple(sorted(c.values)))
        if key not in seen_conflict_fields:
            seen_conflict_fields.add(key)
            unique_conflicts.append(c)

    missing = [f for f in CORE_FIELDS if not fields.get(f, ExtractedField()).is_present()]
    packet_ready, reason = evaluate_packet_readiness(fields, unique_conflicts, second_vehicle)

    result.document_types_detected = list(dict.fromkeys(doc_types))
    result.extracted_fields = fields
    result.missing_fields = missing
    result.conflicts = unique_conflicts
    result.unrelated_documents = unrelated_docs
    result.second_vehicle_detected = second_vehicle
    result.packet_ready = packet_ready
    result.packet_readiness_reason = reason
    result.model_used = model_used
    result.runtime_seconds = time.time() - start

    # Cost estimate
    cost_per = extractor.cost_per_image() if hasattr(extractor, "cost_per_image") else 0.0
    result.cost_estimate_usd = round(total_images * cost_per, 4) if cost_per else None

    result.quote_ready_packet_draft = build_packet_draft(
        case_id=case_id,
        fields=fields,
        missing_fields=missing,
        conflicts=unique_conflicts,
        packet_ready=packet_ready,
        packet_readiness_reason=reason,
        document_types=result.document_types_detected,
        unrelated_docs=unrelated_docs,
        input_files=result.input_files,
    )

    return result
