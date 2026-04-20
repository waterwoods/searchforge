"""
V6: Map raw OCR text → structured field candidates + per-field confidence.

No network calls — pure regex/heuristics. Safe for insurance card / registration / VIN label photos.
"""

from __future__ import annotations

import re
from typing import Any

from services.fiqa_api.inbox_triage.add_car_vehicle_signals import _VIN_17_RE

# Common US auto insurers (substring match, case-insensitive)
_INSURER_MARKERS: tuple[tuple[str, str], ...] = (
    ("state farm", "State Farm"),
    ("geico", "GEICO"),
    ("progressive", "Progressive"),
    ("allstate", "Allstate"),
    ("farmers", "Farmers"),
    ("usaa", "USAA"),
    ("liberty mutual", "Liberty Mutual"),
    ("travelers", "Travelers"),
    ("nationwide", "Nationwide"),
    ("mercury", "Mercury"),
    ("aaa", "AAA Insurance"),
    ("the hartford", "The Hartford"),
)

# Year near vehicle language
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _confidence_from_match_len(field: str, raw_len: int, base: float) -> float:
    if raw_len <= 0:
        return 0.0
    # Short junk → downweight
    if field == "vin" and raw_len != 17:
        return max(0.15, base * 0.4)
    return min(0.95, base + min(0.12, raw_len / 200.0))


def parse_ocr_text_to_fields(raw_text: str) -> dict[str, Any]:
    """
    Returns:
      {
        "structured_fields": { field_id: { "value", "confidence", "source": "ocr_regex" } },
        "raw_text_snippet": str,
        "insurance_provider_guess": str | None,
      }
    """
    text = (raw_text or "").strip()
    if not text:
        return {
            "structured_fields": {},
            "raw_text_snippet": "",
            "insurance_provider_guess": None,
        }

    structured: dict[str, Any] = {}
    snippet = text[:2000]

    vin_m = _VIN_17_RE.search(text.replace(" ", "").replace("\n", ""))
    if not vin_m:
        vin_m = _VIN_17_RE.search(text)
    if vin_m:
        vin = vin_m.group(1).upper()
        structured["vin"] = {
            "value": vin,
            "confidence": _confidence_from_match_len("vin", len(vin), 0.78),
            "source": "ocr_regex",
        }

    z_m = re.search(r"\b(9[0-9]{4})(?:-\d{4})?\b", text)
    if z_m:
        z = z_m.group(1)
        if len(z) == 5:
            structured["zip"] = {
                "value": z,
                "confidence": 0.62,
                "source": "ocr_regex",
            }

    y_m = _YEAR_RE.search(text)
    if y_m:
        try:
            y = int(y_m.group(0))
            if 1980 <= y <= 2030:
                structured["year"] = {
                    "value": str(y),
                    "confidence": 0.58,
                    "source": "ocr_regex",
                }
        except ValueError:
            pass

    # Make/model: line with year + two+ tokens (heuristic)
    for line in text.splitlines():
        lm = re.search(r"\b(19|20)\d{2}\b", line)
        if not lm:
            continue
        rest = line[lm.end() :].strip()
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-]+|\S+", rest)
        if len(tokens) >= 2:
            mm = " ".join(tokens[:4])[:80]
            structured["make_model"] = {
                "value": mm.strip(),
                "confidence": 0.52,
                "source": "ocr_regex",
            }
            break

    tl = text.lower()
    insurer_guess: str | None = None
    for needle, label in _INSURER_MARKERS:
        if needle in tl:
            insurer_guess = label
            structured["insurance_provider_guess"] = {
                "value": label,
                "confidence": 0.45,
                "source": "ocr_keyword",
            }
            break

    # Name: INSURED / NAMED INSURED line
    for pat in (
        r"(?:named\s+insured|insured|policyholder)\s*[:\s]+\s*(.+?)(?:\n|$)",
        r"(?:name)\s*[:\s]+\s*([A-Za-z][A-Za-z\s,\-\.]{4,60})",
    ):
        nm = re.search(pat, text, re.IGNORECASE)
        if nm:
            name = re.sub(r"\s+", " ", nm.group(1).strip())[:80]
            if len(name) >= 3:
                structured["primary_name_guess"] = {
                    "value": name,
                    "confidence": 0.40,
                    "source": "ocr_regex",
                }
                break

    return {
        "structured_fields": structured,
        "raw_text_snippet": snippet,
        "insurance_provider_guess": insurer_guess,
    }
