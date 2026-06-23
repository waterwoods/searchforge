"""
P16 OCR Kill Test — AI extraction adapters.

Supports: openai | gemini | dry_run
Selected via P16_OCR_PROVIDER env or --provider CLI flag.
"""
import base64
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Extraction prompt
# ─────────────────────────────────────────────

EXTRACTION_PROMPT = """You are an AI assistant helping a California auto insurance broker.

Your task: extract 8 core add-car fields from the attached document image(s).

Extract ONLY these fields:
- customer_name: Full legal name of vehicle buyer/owner
- phone: Customer phone number (10-digit US)
- vin: Vehicle Identification Number (17 characters, uppercase)
- year: Vehicle model year (4 digits, e.g. 2023)
- make_model: Vehicle make and model combined (e.g. "Toyota Camry")
- garaging_zip: ZIP code where vehicle will be primarily garaged (5 digits)
- primary_driver: Name of primary driver (may differ from buyer)
- delivery_or_effective_date: Delivery date or insurance effective date (ISO YYYY-MM-DD if possible)

CRITICAL RULES:
1. NEVER invent values. If a field is not visible in the document, leave value as empty string "".
2. If you are uncertain, set needs_confirmation to true.
3. If you see TWO different VINs, TWO different vehicles, or conflicting data — report ALL values in conflicts_found.
4. VIN must be exactly 17 characters (A-Z, 0-9, excluding I/O/Q). Report raw if unsure.
5. If the document appears to be unrelated to auto insurance or vehicle purchase, set document_type to "unrelated".
6. If a second vehicle is detected, set second_vehicle_detected to true.
7. INSURANCE CARD RULE: If the document is an insurance card (document_type == insurance_card):
   - Leave garaging_zip EMPTY (""). Insurance cards show the agent or insurer address, never the garaging ZIP. Garaging ZIP comes from the intake form only.
   - Leave phone EMPTY (""). Any phone on an insurance card belongs to the agent or insurer, not the customer.
   - Do NOT use agency address, insurer address, or any P.O. Box as customer address or garaging ZIP.
   - Named insured(s) listed on the card ARE valid for customer_name.
   - VIN, year, make/model, and effective date on the card ARE valid fields to extract.

Also identify:
- document_type: one of [dealer_paperwork, purchase_contract, vin_photo, registration, insurance_card, dealer_email, mixed_pdf, blurry_photo, unrelated, unknown]
- second_vehicle_detected: boolean
- conflicts_found: list of {field, value_a, source_a, value_b, source_b, notes}

Respond ONLY with valid JSON matching this exact schema:
{
  "document_type": "",
  "second_vehicle_detected": false,
  "fields": {
    "customer_name": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": true, "notes": ""},
    "phone": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": true, "notes": ""},
    "vin": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": true, "notes": ""},
    "year": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": true, "notes": ""},
    "make_model": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": true, "notes": ""},
    "garaging_zip": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": true, "notes": ""},
    "primary_driver": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": true, "notes": ""},
    "delivery_or_effective_date": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": true, "notes": ""}
  },
  "conflicts_found": []
}

Confidence scale: 0.0 = not present, 0.5 = uncertain, 0.9 = high confidence, 1.0 = exact visible text.
"""


# ─────────────────────────────────────────────
# Image loading
# ─────────────────────────────────────────────

def _load_image_b64(path: Path) -> tuple[str, str]:
    """Return (base64_data, mime_type) for an image file.

    HEIC files are converted to JPEG via pillow-heif before encoding.
    Falls back to raw bytes if conversion fails (model will attempt to parse).
    """
    suffix = path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}

    if suffix in (".heic", ".heif"):
        try:
            import io
            import pillow_heif
            from PIL import Image
            pillow_heif.register_heif_opener()
            img = Image.open(path)
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=92)
            data = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
            logger.info(f"HEIC converted to JPEG for {path.name}: {len(buf.getvalue())} bytes")
            return data, "image/jpeg"
        except Exception as e:
            # pillow_heif unavailable or conversion failed.
            # Do NOT send raw HEIC bytes as image/jpeg — OpenAI/Gemini will reject with 400.
            # Raise so the caller can surface a clear warning rather than silently corrupt.
            logger.error(f"HEIC conversion failed for {path.name}: {e} — pillow-heif may not be installed")
            raise RuntimeError(
                f"Cannot process HEIC file '{path.name}': pillow-heif conversion failed ({e}). "
                "Install pillow-heif or convert the photo to JPG before uploading."
            ) from e

    mime = mime_map.get(suffix, "image/jpeg")
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, mime


def _pdf_to_images(path: Path) -> list[tuple[str, str]]:
    """
    Convert PDF pages to base64 images.

    Tries: pymupdf (fitz) → pdf2image → fallback (extract text only).
    Returns list of (base64_data, mime_type).
    """
    # Try pymupdf
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(path))
        images = []
        for page_num in range(min(len(doc), 8)):  # cap at 8 pages
            page = doc[page_num]
            mat = fitz.Matrix(2.0, 2.0)  # 2x scale for readability
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
            images.append((b64, "image/png"))
        doc.close()
        return images
    except ImportError:
        pass

    # Try pdf2image
    try:
        from pdf2image import convert_from_path
        import io
        pages = convert_from_path(str(path), dpi=200, first_page=1, last_page=8)
        images = []
        for page in pages:
            buf = io.BytesIO()
            page.save(buf, format="PNG")
            b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
            images.append((b64, "image/png"))
        return images
    except (ImportError, Exception):
        pass

    # Last resort: return empty — caller will note PDF could not be rendered
    return []


def _prepare_file(path: Path) -> list[tuple[str, str, str]]:
    """
    Prepare file as list of (base64, mime_type, label) tuples.
    For multi-page PDFs, returns one entry per page.
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        images = _pdf_to_images(path)
        if not images:
            logger.warning(f"Could not render PDF to images: {path}. Install pymupdf or pdf2image.")
            return []
        return [(b64, mime, f"{path.name} p{i+1}") for i, (b64, mime) in enumerate(images)]
    else:
        b64, mime = _load_image_b64(path)
        return [(b64, mime, path.name)]


# ─────────────────────────────────────────────
# PDF text-layer VIN (prefer over Vision OCR for native PDFs)
# ─────────────────────────────────────────────

_VIN_STRUCTURAL = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


def try_pdf_text_layer_vin(path: Path) -> str:
    """
    Extract a structurally valid 17-char VIN from a PDF's embedded text layer.

    Returns empty string when the file is not a PDF, has no text layer, or no
    valid VIN is found. Scanned/image-only PDFs fall through to Vision OCR.
    """
    if path.suffix.lower() != ".pdf":
        return ""
    from .local_ocr_extractor import _extract_text_from_pdf, _extract_vin
    from .normalizers import normalize_vin

    text = _extract_text_from_pdf(path)
    if not text.strip():
        return ""
    raw, _conf = _extract_vin(text)
    vin = normalize_vin(raw)
    if _VIN_STRUCTURAL.match(vin):
        return vin
    return ""


def _apply_pdf_text_vin_preference(file_path: Path, result: dict) -> dict:
    """
    When PDF text layer yields a valid VIN, prefer it over Vision OCR output.

    Vision extraction still runs for all other fields; this only overrides vin.
    """
    from .normalizers import normalize_vin

    pdf_vin = try_pdf_text_layer_vin(file_path)
    if not pdf_vin:
        return result

    fields = result.setdefault("fields", {})
    vin_field = fields.get("vin") or {}
    vision_vin = normalize_vin((vin_field.get("value") or "").strip())
    if vision_vin == pdf_vin:
        return result

    note_parts = ["VIN from PDF text layer."]
    if vision_vin and vision_vin != pdf_vin:
        note_parts.append(f"Vision OCR had '{vision_vin}'.")

    fields["vin"] = {
        "value": pdf_vin,
        "confidence": 0.99,
        "source_quote": "PDF text layer",
        "needs_confirmation": False,
        "notes": " ".join(note_parts),
    }
    logger.info(
        "PDF text-layer VIN override for %s: %s (vision had %s)",
        file_path.name,
        pdf_vin,
        vision_vin or "(empty)",
    )
    return result


# ─────────────────────────────────────────────
# JSON extraction helper
# ─────────────────────────────────────────────

def _parse_extraction_json(raw: str) -> Optional[dict]:
    """Extract and parse JSON from model response."""
    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Try to find JSON block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Try to find outermost {}
    m = re.search(r"(\{.*\})", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


# ─────────────────────────────────────────────
# OpenAI adapter
# ─────────────────────────────────────────────

class OpenAIExtractor:
    MODEL = "gpt-4o"
    # Rough cost estimate: $0.005 per image (gpt-4o vision)
    COST_PER_IMAGE_USD = 0.005

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def extract(self, file_path: Path) -> dict:
        """Extract fields from a single file. Returns raw extraction dict."""
        parts = _prepare_file(file_path)
        if not parts:
            return {
                "document_type": "unknown",
                "second_vehicle_detected": False,
                "fields": {f: {"value": "", "confidence": 0.0, "source_quote": "",
                               "needs_confirmation": True, "notes": "File could not be processed"}
                           for f in ["customer_name", "phone", "vin", "year", "make_model",
                                     "garaging_zip", "primary_driver", "delivery_or_effective_date"]},
                "conflicts_found": [],
                "_error": f"Could not render file: {file_path.name}",
                "_cost_images": 0,
            }

        content = [{"type": "text", "text": EXTRACTION_PROMPT}]
        for b64, mime, label in parts:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{b64}",
                    "detail": "high",
                },
            })
            content.append({"type": "text", "text": f"[Document: {label}]"})

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": content}],
            temperature=0.0,
            max_tokens=2048,
        )
        raw_text = response.choices[0].message.content or ""
        result = _parse_extraction_json(raw_text)
        if result is None:
            result = {
                "document_type": "unknown",
                "second_vehicle_detected": False,
                "fields": {},
                "conflicts_found": [],
                "_parse_error": True,
                "_raw_response": raw_text[:500],
            }
        result["_cost_images"] = len(parts)
        result["_model"] = self.MODEL
        return _apply_pdf_text_vin_preference(file_path, result)

    def cost_per_image(self) -> float:
        return self.COST_PER_IMAGE_USD


# ─────────────────────────────────────────────
# Gemini adapter
# ─────────────────────────────────────────────

class GeminiExtractor:
    MODEL = "gemini-2.0-flash"
    COST_PER_IMAGE_USD = 0.0005  # much cheaper

    def __init__(self):
        try:
            import google.generativeai as genai
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            genai.configure(api_key=api_key)
            self.genai = genai
            self.model = genai.GenerativeModel(self.MODEL)
        except ImportError:
            raise ImportError("google-generativeai not installed. pip install google-generativeai")

    def extract(self, file_path: Path) -> dict:
        import PIL.Image
        import io

        parts = _prepare_file(file_path)
        if not parts:
            return {
                "document_type": "unknown",
                "second_vehicle_detected": False,
                "fields": {},
                "conflicts_found": [],
                "_error": f"Could not render file: {file_path.name}",
                "_cost_images": 0,
            }

        content_parts = [EXTRACTION_PROMPT]
        for b64, mime, label in parts:
            img_bytes = base64.b64decode(b64)
            img = PIL.Image.open(io.BytesIO(img_bytes))
            content_parts.append(img)
            content_parts.append(f"[Document: {label}]")

        response = self.model.generate_content(content_parts)
        raw_text = response.text or ""
        result = _parse_extraction_json(raw_text)
        if result is None:
            result = {
                "document_type": "unknown",
                "second_vehicle_detected": False,
                "fields": {},
                "conflicts_found": [],
                "_parse_error": True,
                "_raw_response": raw_text[:500],
            }
        result["_cost_images"] = len(parts)
        result["_model"] = self.MODEL
        return _apply_pdf_text_vin_preference(file_path, result)

    def cost_per_image(self) -> float:
        return self.COST_PER_IMAGE_USD


# ─────────────────────────────────────────────
# Dry-run adapter (no API calls)
# ─────────────────────────────────────────────

class DryRunExtractor:
    """
    Returns a realistic-looking empty extraction for testing pipeline logic.
    Does not call any API.
    """
    MODEL = "dry_run"
    COST_PER_IMAGE_USD = 0.0

    def extract(self, file_path: Path) -> dict:
        logger.info(f"[DRY RUN] Simulating extraction for {file_path.name}")
        return {
            "document_type": "unknown",
            "second_vehicle_detected": False,
            "fields": {
                "customer_name": {"value": "", "confidence": 0.0, "source_quote": "",
                                  "needs_confirmation": True, "notes": "dry_run — no API call made"},
                "phone": {"value": "", "confidence": 0.0, "source_quote": "",
                          "needs_confirmation": True, "notes": ""},
                "vin": {"value": "", "confidence": 0.0, "source_quote": "",
                        "needs_confirmation": True, "notes": ""},
                "year": {"value": "", "confidence": 0.0, "source_quote": "",
                         "needs_confirmation": True, "notes": ""},
                "make_model": {"value": "", "confidence": 0.0, "source_quote": "",
                               "needs_confirmation": True, "notes": ""},
                "garaging_zip": {"value": "", "confidence": 0.0, "source_quote": "",
                                 "needs_confirmation": True, "notes": ""},
                "primary_driver": {"value": "", "confidence": 0.0, "source_quote": "",
                                   "needs_confirmation": True, "notes": ""},
                "delivery_or_effective_date": {"value": "", "confidence": 0.0, "source_quote": "",
                                               "needs_confirmation": True, "notes": ""},
            },
            "conflicts_found": [],
            "_cost_images": 0,
            "_model": "dry_run",
            "_dry_run": True,
        }

    def cost_per_image(self) -> float:
        return 0.0


# ─────────────────────────────────────────────
# Provider factory
# ─────────────────────────────────────────────

def get_extractor(provider: str = "auto"):
    """
    Return an extractor instance based on provider name.

    provider: "auto" | "openai" | "gemini" | "dry_run"

    "auto" picks the first available: openai → gemini → dry_run
    """
    provider = provider.lower().strip()

    if provider == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set. Cannot use openai provider.")
        return OpenAIExtractor()

    if provider == "gemini":
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not set.")
        return GeminiExtractor()

    if provider == "dry_run":
        return DryRunExtractor()

    if provider == "auto":
        if os.environ.get("OPENAI_API_KEY"):
            logger.info("Auto-selected provider: openai")
            return OpenAIExtractor()
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if key:
            logger.info("Auto-selected provider: gemini")
            try:
                return GeminiExtractor()
            except ImportError:
                pass
        env_provider = os.environ.get("P16_OCR_PROVIDER", "").lower()
        if env_provider and env_provider != "auto":
            return get_extractor(env_provider)
        logger.warning("No API keys found. Falling back to dry_run mode.")
        return DryRunExtractor()

    raise ValueError(f"Unknown provider: {provider}. Use: auto | openai | gemini | dry_run")
