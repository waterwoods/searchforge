"""
V6: Image → raw OCR text. Google Cloud Vision when configured; otherwise non-blocking stub.

Never raises to callers — returns empty text + low confidence on failure (flow continues).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OcrExtractResult:
    raw_text: str
    confidence: float  # 0–1 engine-level confidence
    engine: str
    detail: str | None = None


def _vision_rest_annotate(image_bytes: bytes) -> OcrExtractResult | None:
    """Optional REST path when GOOGLE_API_KEY is set (Vision API v1 images:annotate)."""
    api_key = (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_CLOUD_API_KEY") or "").strip()
    if not api_key:
        return None
    try:
        import base64
        import json

        import urllib.request

        body = {
            "requests": [
                {
                    "image": {"content": base64.b64encode(image_bytes).decode("ascii")},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION", "maxResults": 1}],
                }
            ]
        }
        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        texts = (
            (payload.get("responses") or [{}])[0]
            .get("fullTextAnnotation", {})
            .get("text")
        )
        if not texts:
            # fallback textAnnotations
            ann = ((payload.get("responses") or [{}])[0].get("textAnnotations") or [])
            texts = ann[0].get("description") if ann else ""
        raw = (texts or "").strip()
        return OcrExtractResult(
            raw_text=raw,
            confidence=0.88 if raw else 0.15,
            engine="google_vision_rest",
            detail=None,
        )
    except Exception as e:
        logger.info("V6 OCR REST failed (non-fatal): %s", e)
        return None


def _vision_sdk_annotate(image_bytes: bytes) -> OcrExtractResult | None:
    if (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "").strip() == "" and not (
        os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_CLOUD_API_KEY")
    ):
        return None
    try:
        from google.cloud import vision  # type: ignore[import-untyped]

        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        response = client.document_text_detection(image=image)
        if response.error.message:
            logger.info("Vision SDK error (non-fatal): %s", response.error.message)
            return None
        raw = (response.full_text_annotation.text or "").strip()
        return OcrExtractResult(
            raw_text=raw,
            confidence=0.9 if raw else 0.12,
            engine="google_vision_sdk",
            detail=None,
        )
    except Exception as e:
        logger.debug("Vision SDK unavailable or failed: %s", e)
        return None


def extract_text_from_image_bytes(
    image_bytes: bytes,
    *,
    content_type: str | None = None,
) -> OcrExtractResult:
    """
    Extract text from an image (jpg/png/gif/webp). PDF not supported here — returns empty.
    """
    ct = (content_type or "").lower()
    if "pdf" in ct:
        return OcrExtractResult(
            raw_text="",
            confidence=0.0,
            engine="skipped_pdf",
            detail="pdf_use_external_converter",
        )
    if not image_bytes:
        return OcrExtractResult(raw_text="", confidence=0.0, engine="empty", detail=None)

    if (os.environ.get("V6_OCR_FORCE_STUB") or "").strip() == "1":
        return OcrExtractResult(
            raw_text="",
            confidence=0.2,
            engine="stub_forced",
            detail=None,
        )

    for fn in (_vision_rest_annotate, _vision_sdk_annotate):
        out = fn(image_bytes)
        if out and out.raw_text:
            return out

    # Dev / no credentials: optional deterministic stub for tests
    if (os.environ.get("V6_OCR_STUB_TEXT") or "").strip():
        stub = os.environ["V6_OCR_STUB_TEXT"]
        return OcrExtractResult(raw_text=stub, confidence=0.5, engine="env_stub", detail=None)

    return OcrExtractResult(
        raw_text="",
        confidence=0.0,
        engine="none",
        detail="no_ocr_engine",
    )
