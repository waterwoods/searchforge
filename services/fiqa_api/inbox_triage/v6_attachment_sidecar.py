"""V6: Run OCR after attachment write and merge signals into case JSON (non-blocking)."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def extract_ocr_from_inline_base64(
    image_base64: str,
    content_type: str | None,
) -> tuple[str, dict[str, Any], str] | None:
    """
    Decode a base64 image and run the same OCR + field parse path as saved attachments.
    Returns (raw_text, structured_fields, engine) or None on skip/failure.
    """
    try:
        raw_bytes = base64.b64decode((image_base64 or "").strip(), validate=True)
    except Exception:
        return None
    if not raw_bytes:
        return None
    try:
        from services.fiqa_api.inbox_triage.image_input_pipeline import extract_text_from_image_bytes
        from services.fiqa_api.inbox_triage.parse_ocr_text_to_fields import parse_ocr_text_to_fields

        ocr = extract_text_from_image_bytes(raw_bytes, content_type=content_type)
        parsed = parse_ocr_text_to_fields(ocr.raw_text)
        sf = parsed.get("structured_fields") if isinstance(parsed.get("structured_fields"), dict) else {}
        return (ocr.raw_text or "", sf, ocr.engine)
    except Exception:
        logger.debug("inline base64 OCR failed (non-fatal)", exc_info=True)
        return None


def _merge_structured_by_confidence(
    existing: dict[str, Any] | None,
    incoming: dict[str, Any],
) -> dict[str, Any]:
    out = dict(existing or {})
    for k, v in incoming.items():
        if not isinstance(v, dict):
            continue
        c_new = float(v.get("confidence") or 0.0)
        if k not in out:
            out[k] = v
            continue
        old = out[k]
        if not isinstance(old, dict):
            out[k] = v
            continue
        c_old = float(old.get("confidence") or 0.0)
        if c_new >= c_old:
            out[k] = v
    return out


def merge_v6_ocr_signals(
    prior: dict[str, Any] | None,
    *,
    raw_text: str,
    structured_fields: dict[str, Any],
    engine: str,
    attachment_id: str,
) -> dict[str, Any]:
    prev = dict(prior or {})
    merged_sf = _merge_structured_by_confidence(
        prev.get("structured_fields") if isinstance(prev.get("structured_fields"), dict) else {},
        structured_fields,
    )
    hist = list(prev.get("attachment_history") or [])
    if not isinstance(hist, list):
        hist = []
    hist.append(
        {
            "attachment_id": attachment_id,
            "engine": engine,
            "raw_len": len(raw_text or ""),
        }
    )
    return {
        "structured_fields": merged_sf,
        "last_raw_text": (raw_text or "")[:8000],
        "last_engine": engine,
        "attachment_history": hist[-20:],
    }


def run_v6_ocr_for_saved_attachment(
    *,
    prior_signals: dict[str, Any] | None,
    attachment_id: str,
    file_path: Path,
    content_type: str | None,
) -> dict[str, Any] | None:
    """
    Returns merged v6_ocr_signals for the case or None if skipped/failed.
    """
    try:
        from services.fiqa_api.inbox_triage.image_input_pipeline import extract_text_from_image_bytes
        from services.fiqa_api.inbox_triage.parse_ocr_text_to_fields import parse_ocr_text_to_fields

        ct = (content_type or "").lower()
        if "pdf" in ct or file_path.suffix.lower() == ".pdf":
            return merge_v6_ocr_signals(
                prior_signals,
                raw_text="",
                structured_fields={},
                engine="pdf_skipped",
                attachment_id=attachment_id,
            )
        blob = file_path.read_bytes()
        ocr = extract_text_from_image_bytes(blob, content_type=content_type)
        parsed = parse_ocr_text_to_fields(ocr.raw_text)
        sf = parsed.get("structured_fields") if isinstance(parsed.get("structured_fields"), dict) else {}
        return merge_v6_ocr_signals(
            prior_signals,
            raw_text=ocr.raw_text,
            structured_fields=sf,
            engine=ocr.engine,
            attachment_id=attachment_id,
        )
    except Exception:
        logger.debug("V6 OCR sidecar failed (non-fatal)", exc_info=True)
        return None
