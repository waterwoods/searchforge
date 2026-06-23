"""
P16 Local OCR Extractor — uses EasyOCR (images) and PyMuPDF (PDFs).

This extractor is used for accuracy evaluation when cloud AI providers
(Gemini, OpenAI) are unavailable.

It represents the BASELINE / WORST-CASE extraction scenario:
  - PDFs: near-perfect text extraction via PyMuPDF
  - Images: real OCR errors via EasyOCR (1/I confusion, missing chars, etc.)

Production uses Gemini Flash 2.5, which should significantly outperform this baseline.
Results here represent a floor, not the production ceiling.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MODEL = "local_ocr_easyocr"
COST_PER_IMAGE_USD = 0.0

_reader = None


def _get_reader():
    """Lazy-init EasyOCR reader (loads model on first call)."""
    global _reader
    if _reader is None:
        import easyocr
        logger.info("Loading EasyOCR model (one-time)...")
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        logger.info("EasyOCR ready.")
    return _reader


def _extract_text_from_pdf(path: Path) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    try:
        import fitz
        doc = fitz.open(str(path))
        texts = []
        for page_num in range(min(len(doc), 8)):
            page = doc[page_num]
            texts.append(page.get_text())
        doc.close()
        return "\n".join(texts)
    except ImportError:
        logger.error("PyMuPDF (fitz) not available. pip install pymupdf")
        return ""
    except Exception as e:
        logger.error(f"PDF text extraction failed for {path}: {e}")
        return ""


def _extract_text_from_image(path: Path) -> str:
    """Extract text from an image using EasyOCR."""
    try:
        reader = _get_reader()
        results = reader.readtext(str(path))
        return "\n".join(r[1] for r in results)
    except Exception as e:
        logger.error(f"EasyOCR failed for {path}: {e}")
        return ""


# ── Field extraction via regex ───────────────────────────────────────────────

def _extract_vin(text: str) -> tuple[str, float]:
    """Extract VIN from text. Returns (value, confidence)."""
    # VIN pattern: 17 chars, no I/O/Q in standard VIN
    # But OCR may produce I for 1, so we look for 17-char alphanum strings
    vin_pattern = re.compile(r'\b([A-HJ-NPR-Z0-9]{17})\b', re.IGNORECASE)
    matches = vin_pattern.findall(text)

    # Also try with OCR-common confusables: 1 and I, 0 and O
    vin_loose = re.compile(r'\b([A-Z0-9I]{17})\b', re.IGNORECASE)
    loose_matches = vin_loose.findall(text)

    # Look for VIN: label context
    vin_labeled = re.compile(
        r'(?:VIN|Vehicle\s+Identification\s+Number)[:\s]+([A-Z0-9I]{17})',
        re.IGNORECASE
    )
    labeled = vin_labeled.findall(text)

    if labeled:
        vin = labeled[0].upper().replace('I', '1')  # fix common OCR confusion
        return vin, 0.85
    if matches:
        vin = matches[0].upper()
        return vin, 0.9
    if loose_matches:
        # Normalize: replace I with 1 where likely
        vin = loose_matches[0].upper()
        return vin, 0.7

    return "", 0.0


def _extract_year(text: str) -> tuple[str, float]:
    """Extract model year (4-digit year 2000-2030)."""
    # Look for year in YMM context
    ymm_year = re.compile(
        r'\b(20[012]\d)\s+(?:[A-Z][a-z]+|BMW|VW)',
        re.IGNORECASE
    )
    match = ymm_year.search(text)
    if match:
        return match.group(1), 0.9

    # Year / Make / Model label
    year_label = re.compile(
        r'(?:Year|Model\s+Year)[/\s:]+\s*(20[012]\d)',
        re.IGNORECASE
    )
    match = year_label.search(text)
    if match:
        return match.group(1), 0.95

    # Standalone year
    standalone = re.compile(r'\b(20[012]\d)\b')
    years = standalone.findall(text)
    # Filter to reasonable range
    vehicle_years = [y for y in years if 2000 <= int(y) <= 2030]
    if vehicle_years:
        return vehicle_years[0], 0.7

    return "", 0.0


def _extract_make_model(text: str) -> tuple[str, float]:
    """Extract vehicle make and model."""
    # Known makes
    makes = [
        "Toyota", "Honda", "Ford", "BMW", "Tesla", "Lexus", "Nissan",
        "Hyundai", "Chevrolet", "Chevy", "Kia", "Subaru", "Mazda",
        "Jeep", "Ram", "Dodge", "Chrysler", "Audi", "Mercedes", "Volkswagen"
    ]
    known_models = {
        "Toyota": ["Camry", "RAV4", "Corolla", "Highlander", "Prius", "Tacoma", "Tundra"],
        "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Odyssey", "Fit"],
        "BMW": ["330i", "X5", "X3", "530i", "M3", "M5"],
        "Tesla": ["Model 3", "Model Y", "Model S", "Model X"],
        "Lexus": ["RX 350", "ES 350", "NX 300", "GX 460"],
        "Nissan": ["Altima", "Sentra", "Rogue", "Pathfinder"],
        "Hyundai": ["Elantra", "Sonata", "Tucson", "Santa Fe"],
        "Ford": ["F-150", "F-250", "Explorer", "Escape", "Mustang", "Edge"],
        "Chevrolet": ["Equinox", "Malibu", "Silverado", "Traverse", "Tahoe"],
    }

    # First try labeled Make/Model
    mm_label = re.compile(
        r'(?:Make\s*/\s*Model|Make\s+/\s+Model|Model)[:\s]+([A-Z][a-zA-Z\s\-]{3,30})',
        re.IGNORECASE
    )
    match = mm_label.search(text)
    if match:
        return match.group(1).strip(), 0.85

    # Look for make followed by model
    for make in makes:
        if make.lower() in text.lower():
            models = known_models.get(make, [])
            for model in models:
                if model.lower() in text.lower():
                    return f"{make} {model}", 0.9
            # Make found but no specific model
            # Try to find model after make
            make_pattern = re.compile(
                rf'\b{re.escape(make)}\s+([A-Z][a-zA-Z0-9\-]{{2,15}})',
                re.IGNORECASE
            )
            m = make_pattern.search(text)
            if m:
                return f"{make} {m.group(1)}", 0.75
            return make, 0.5

    return "", 0.0


def _extract_customer_name(text: str) -> tuple[str, float]:
    """Extract customer/buyer name."""
    # Common label patterns
    patterns = [
        re.compile(r'(?:Buyer\s+Name|Registered\s+Owner|Customer\s+Name|Owner)[:\s]+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})', re.IGNORECASE),
        re.compile(r'(?:Name)[:\s]+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})', re.IGNORECASE),
    ]
    for p in patterns:
        match = p.search(text)
        if match:
            name = match.group(1).strip()
            # Basic sanity: 2-4 words, each capitalized
            words = name.split()
            if 1 < len(words) <= 4 and all(w[0].isupper() or w[0].isalpha() for w in words):
                return name, 0.85

    # WeChat style: look for Chinese names (common in corpus)
    # Pattern: 2-char or 3-char names in message context
    wechat_name = re.compile(
        r'(?:My\s+(?:name|car)|I(?:\'m|\s+am))[:\s]+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)',
        re.IGNORECASE
    )
    match = wechat_name.search(text)
    if match:
        return match.group(1).strip(), 0.75

    return "", 0.0


def _extract_garaging_zip(text: str) -> tuple[str, float]:
    """Extract 5-digit garaging/address ZIP code."""
    # Labeled ZIP
    labeled = re.compile(
        r'(?:ZIP|Zip\s+Code|Garaging\s+ZIP|Garaging\s+Address\s+ZIP|City[/\s]+ZIP)[:\s]+(\d{5})',
        re.IGNORECASE
    )
    match = labeled.search(text)
    if match:
        return match.group(1), 0.95

    # Address context: look for 5 digits at end of address line
    addr_zip = re.compile(
        r'\b(9[0-9]{4})\b'  # California ZIP codes start with 9
    )
    matches = addr_zip.findall(text)
    if matches:
        return matches[0], 0.75

    return "", 0.0


# ── Main extract function ────────────────────────────────────────────────────

def _make_empty_fields() -> dict:
    return {
        f: {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": True, "notes": ""}
        for f in ["customer_name", "phone", "vin", "year", "make_model",
                  "garaging_zip", "primary_driver", "delivery_or_effective_date"]
    }


def extract_local_ocr(file_path: Path) -> dict:
    """
    Extract fields from a file using local OCR (PyMuPDF + EasyOCR).
    Returns dict matching the standard extraction schema.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        raw_text = _extract_text_from_pdf(file_path)
        source = "pymupdf_text"
    else:
        raw_text = _extract_text_from_image(file_path)
        source = "easyocr"

    if not raw_text.strip():
        return {
            "document_type": "unknown",
            "second_vehicle_detected": False,
            "fields": _make_empty_fields(),
            "conflicts_found": [],
            "_model": MODEL,
            "_cost_images": 1,
            "_error": f"No text extracted from {file_path.name}",
        }

    # Infer document type from filename and content
    fname = file_path.name.lower()
    if "purchase" in fname or "pa_" in fname:
        doc_type = "purchase_contract"
    elif "window" in fname or "sticker" in fname or "ws_" in fname:
        doc_type = "dealer_paperwork"
    elif "reg" in fname:
        doc_type = "registration"
    elif "wechat" in fname:
        doc_type = "mixed_pdf"  # chat-style
    elif "vin" in fname:
        doc_type = "vin_photo"
    elif "dw_" in fname or "dealer" in fname or "worksheet" in fname:
        doc_type = "dealer_paperwork"
    else:
        doc_type = "unknown"

    # Extract fields
    vin, vin_conf = _extract_vin(raw_text)
    year, year_conf = _extract_year(raw_text)
    make_model, mm_conf = _extract_make_model(raw_text)
    name, name_conf = _extract_customer_name(raw_text)
    zip_code, zip_conf = _extract_garaging_zip(raw_text)

    def field(value, confidence, notes=""):
        has_val = bool(value.strip())
        return {
            "value": value,
            "confidence": confidence if has_val else 0.0,
            "source_quote": value if has_val else "",
            "needs_confirmation": confidence < 0.9 or not has_val,
            "notes": notes,
        }

    fields = {
        "customer_name": field(name, name_conf),
        "phone": field("", 0.0, "phone extraction not implemented in local_ocr"),
        "vin": field(vin, vin_conf),
        "year": field(year, year_conf),
        "make_model": field(make_model, mm_conf),
        "garaging_zip": field(zip_code, zip_conf),
        "primary_driver": field("", 0.0),
        "delivery_or_effective_date": field("", 0.0),
    }

    # Check for potential second vehicle (two different VINs in text)
    all_vins = re.findall(r'\b[A-HJ-NPR-Z0-9]{17}\b', raw_text, re.IGNORECASE)
    unique_vins = set(v.upper() for v in all_vins)
    second_vehicle = len(unique_vins) > 1

    conflicts = []
    if second_vehicle:
        vins = list(unique_vins)
        conflicts.append({
            "field": "vin",
            "value_a": vins[0],
            "source_a": file_path.name,
            "value_b": vins[1] if len(vins) > 1 else "",
            "source_b": file_path.name,
            "notes": "Multiple VINs detected in document",
        })

    return {
        "document_type": doc_type,
        "second_vehicle_detected": second_vehicle,
        "fields": fields,
        "conflicts_found": conflicts,
        "_model": MODEL,
        "_cost_images": 1,
        "_raw_text_length": len(raw_text),
        "_ocr_source": source,
    }


# ── Extractor adapter class ──────────────────────────────────────────────────

class LocalOCRExtractor:
    """
    Drop-in extractor using local OCR (EasyOCR + PyMuPDF).

    Used when cloud providers (Gemini, OpenAI) are unavailable.
    Represents a baseline/worst-case scenario for accuracy comparison.

    Production target: Gemini Flash 2.5 (expected to significantly outperform this).
    """
    MODEL = MODEL
    COST_PER_IMAGE_USD = COST_PER_IMAGE_USD

    def extract(self, file_path: Path) -> dict:
        return extract_local_ocr(file_path)

    def cost_per_image(self) -> float:
        return self.COST_PER_IMAGE_USD
