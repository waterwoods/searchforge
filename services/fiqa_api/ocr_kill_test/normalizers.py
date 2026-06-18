"""
P16 OCR Kill Test — field normalization utilities.

VIN → uppercase 17-char
Phone → 10-digit US
Date → YYYY-MM-DD
ZIP → 5-digit
"""
import re
from typing import Optional


def normalize_vin(raw: str) -> str:
    """Uppercase, strip whitespace/dashes, validate 17-char structure."""
    if not raw:
        return ""
    cleaned = re.sub(r"[\s\-_]", "", raw).upper()
    # VINs are exactly 17 chars using A-Z 0-9 excluding I, O, Q
    if re.match(r"^[A-HJ-NPR-Z0-9]{17}$", cleaned):
        return cleaned
    # Return cleaned even if not perfect — let confirmation flag catch it
    return cleaned


def normalize_phone(raw: str) -> str:
    """Strip to 10 digits (US). Returns empty string if not parseable."""
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits[0] == "1":
        digits = digits[1:]
    if len(digits) == 10:
        return digits
    return digits  # Return what we have; let confirmation flag catch it


def normalize_date(raw: str) -> str:
    """Best-effort ISO YYYY-MM-DD normalization."""
    if not raw:
        return ""
    # Already ISO
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw
    # MM/DD/YYYY or M/D/YYYY
    m = re.match(r"^(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})$", raw.strip())
    if m:
        month, day, year = m.group(1), m.group(2), m.group(3)
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    # YYYY/MM/DD
    m = re.match(r"^(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})$", raw.strip())
    if m:
        year, month, day = m.group(1), m.group(2), m.group(3)
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return raw  # Return as-is; flag for confirmation


def normalize_zip(raw: str) -> str:
    """Extract leading 5-digit ZIP."""
    if not raw:
        return ""
    m = re.search(r"\b(\d{5})(?:-\d{4})?\b", raw)
    if m:
        return m.group(1)
    return raw


def normalize_year(raw: str) -> str:
    """Extract 4-digit year in plausible range."""
    if not raw:
        return ""
    m = re.search(r"\b(19[5-9]\d|20[0-3]\d)\b", raw)
    if m:
        return m.group(1)
    return raw


def make_model_same(val_a: str, val_b: str) -> bool:
    """Return True if two make/model strings refer to the same base vehicle.

    Uses word-by-word prefix matching — one value must be a prefix of the other:
      Same:      'BMW X5' vs 'BMW X5 XDRIVE35I'
                 'Toyota Camry' vs 'Toyota Camry LE'
                 'Tesla Model Y' vs 'Tesla Model Y Long Range'
                 'Honda Civic' vs 'Honda Civic EX'
      Different: 'BMW X5' vs 'BMW X3'
                 'Toyota Camry' vs 'Toyota Corolla'
                 'Tesla Model 3' vs 'Tesla Model Y'
    """
    if not val_a or not val_b:
        return val_a == val_b
    a_words = val_a.upper().split()
    b_words = val_b.upper().split()
    shorter = a_words if len(a_words) <= len(b_words) else b_words
    longer = b_words if len(a_words) <= len(b_words) else a_words
    return longer[: len(shorter)] == shorter


_VIN_INVALID_CHARS = re.compile(r"[IOQ]")
_VIN_VALID_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


def _vin_warning(cleaned: str) -> str | None:
    """Return a human-readable warning if the cleaned VIN is malformed, else None."""
    if not cleaned:
        return "VIN is empty"
    if len(cleaned) != 17:
        return f"VIN must be 17 characters (got {len(cleaned)})"
    bad_chars = sorted(set(cleaned) & {"I", "O", "Q"})
    if bad_chars:
        return f"VIN contains invalid characters: {', '.join(bad_chars)}"
    if not _VIN_VALID_PATTERN.match(cleaned):
        return "VIN contains non-alphanumeric characters"
    return None


def apply_normalizations(fields: dict) -> dict:
    """
    Apply field-specific normalizations to a raw extraction dict.
    Returns the same dict with values normalized in-place.

    For VIN: if the cleaned value fails structural checks, sets
    needs_confirmation=True and appends a warning to notes.
    """
    normalizers = {
        "vin": normalize_vin,
        "phone": normalize_phone,
        "delivery_or_effective_date": normalize_date,
        "garaging_zip": normalize_zip,
        "year": normalize_year,
    }
    for field_name, fn in normalizers.items():
        if field_name in fields and fields[field_name].get("value"):
            original = fields[field_name]["value"]
            normalized = fn(original)
            if normalized != original:
                fields[field_name]["value"] = normalized
                existing_notes = fields[field_name].get("notes", "")
                fields[field_name]["notes"] = (
                    f"Normalized from '{original}'. {existing_notes}".strip()
                )

    # VIN structural validation — flag malformed VINs for confirmation
    if "vin" in fields and fields["vin"].get("value"):
        warning = _vin_warning(fields["vin"]["value"])
        if warning:
            fields["vin"]["needs_confirmation"] = True
            existing_notes = fields["vin"].get("notes", "")
            fields["vin"]["notes"] = (
                f"VIN warning: {warning}. {existing_notes}".strip()
            )

    return fields
