"""
Notice Retrieval — Light retrieval-assisted explanation for notice and document confusion.

Two retrieval-assisted paths:
1. **Notice confusion** — "what does payment failed mean?" → notice_interpretation, dmv_sr22
2. **Document confusion** — "declaration page是什么?", "garaging proof是什么意思?" → declaration_page_garaging

Retrieval assists explanation only. Rules/config still drive:
- Intent detection, handoff threshold, next-question logic, case state.

Runtime stability:
- Retrieval requires EMBED_READY (embedder warmup) and Qdrant availability.
- If either is not ready, returns None and template-only fallback is used.
- Use retrieval_ready() to check before expecting retrieval-augmented replies.

See: docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

COLLECTION_NAME = "auto_insurance_demo_core"
MIN_SCORE = 0.45
MAX_SNIPPET_CHARS = 80


def retrieval_ready() -> bool:
    """
    Check if retrieval dependencies (embedder + Qdrant) are ready.
    Use this for diagnostics and health checks.
    Returns True only when both embedder and Qdrant are available.
    """
    if os.getenv("NOTICE_RETRIEVAL_ENABLED", "1").lower() in ("0", "false", "off"):
        return False
    try:
        from services.fiqa_api.clients import EMBED_READY, get_qdrant_client
        if not EMBED_READY:
            return False
        get_qdrant_client()
        return True
    except Exception:
        return False


def _extract_query_from_message(text: str) -> str:
    """Derive a retrieval query from customer message. Prefer explicit notice terms."""
    t = (text or "").strip().lower()
    # If they mention specific terms, use those
    notice_terms = [
        "payment failed", "autopay failed", "cancel pending", "cancellation pending",
        "last notice", "final notice", "non-payment", "overdue", "past due",
        "what does", "what do i", "什么意思", "看不懂", "怎么办",
    ]
    for term in notice_terms:
        if term in t:
            # Use a clean query
            if "payment" in term or "cancel" in term or "notice" in term:
                return f"What does {term} mean?"
            if "什么意思" in t or "what does" in t:
                # Extract quoted part if any
                m = re.search(r'["\']([^"\']+)["\']', t) or re.search(r"what does (.+?) mean", t)
                if m:
                    return f"What does {m.group(1).strip()} mean?"
                return "What does this insurance notice mean?"
    return "What does this insurance notice mean? Is it urgent?"


def retrieve_notice_explanation(customer_message: str) -> Optional[str]:
    """
    Retrieve a brief knowledge-backed snippet for notice confusion.

    Returns a short string to augment the reply (e.g. "根据常见情况，'payment failed'
    一般意思是付款被拒，需要尽快处理。") or None if retrieval fails or returns nothing useful.

    Safe: catches all exceptions, returns None on any failure.
    Fallback: when retrieval is unavailable (warmup, Qdrant down, etc.), returns None
    and the caller uses template-only reply.
    """
    if os.getenv("NOTICE_RETRIEVAL_ENABLED", "1").lower() in ("0", "false", "off"):
        return None

    try:
        from services.fiqa_api.clients import (
            EMBED_READY,
            EmbeddingUnreadyError,
            get_embedder,
            get_qdrant_client,
        )
        from services.fiqa_api.utils.qdrant_adapter import qdrant_search
    except ImportError as e:
        logger.debug(f"Notice retrieval: import failed: {e}")
        return None

    # Fast path: embedder not ready (warmup in progress) — skip retrieval, use template
    if not EMBED_READY:
        logger.info(
            "[NOTICE_RETRIEVAL] Embedder warming up — using template-only fallback for notice explanation"
        )
        return None

    embedder = None
    client = None
    try:
        embedder = get_embedder()
        client = get_qdrant_client()
    except EmbeddingUnreadyError:
        logger.info(
            "[NOTICE_RETRIEVAL] Embedder not ready — using template-only fallback for notice explanation"
        )
        return None
    except Exception as e:
        logger.info(f"[NOTICE_RETRIEVAL] Client init failed ({type(e).__name__}) — using template fallback: {e}")
        return None

    if embedder is None or client is None:
        return None

    query = _extract_query_from_message(customer_message)
    try:
        vec = embedder.encode([query])[0]
        if hasattr(vec, "tolist"):
            vec = vec.tolist()

        results = qdrant_search(
            client=client,
            collection_name=COLLECTION_NAME,
            query_vector=vec,
            limit=5,
            with_payload=True,
        )

        if not results:
            return None

        # Prefer knowledge chunks (topic notice_interpretation or dmv_sr22)
        for r in results:
            score = getattr(r, "score", None)
            if score is None and isinstance(r, dict):
                score = r.get("score", 0.0)
            score = float(score or 0.0)
            if score < MIN_SCORE:
                continue
            if isinstance(r, dict):
                payload = r.get("payload", r)
            else:
                payload = getattr(r, "payload", None) or {}
            topic = payload.get("topic", "")
            if topic not in ("notice_interpretation", "dmv_sr22"):
                continue
            text = payload.get("text") or payload.get("title") or ""
            if not text:
                continue
            # Strip markdown, take first sentence or first N chars
            clean = re.sub(r"\*\*|\#|\[|\]|\(|\)", "", text)
            clean = clean.replace("\n", " ").strip()
            if len(clean) > MAX_SNIPPET_CHARS:
                clean = clean[:MAX_SNIPPET_CHARS].rsplit(" ", 1)[0] + "..."
            return clean
    except Exception as e:
        logger.info(f"[NOTICE_RETRIEVAL] Search failed ({type(e).__name__}) — using template fallback: {e}")
        return None

    return None


def format_retrieval_augment(snippet: str, language: str) -> str:
    """
    Format a retrieval snippet into a brief augment for the reply.
    Returns a string to prepend before the template, or empty if not suitable.
    """
    if not snippet or len(snippet) < 20:
        return ""
    if language == "zh":
        return f"根据常见情况，{snippet} "
    return f"Based on common cases, {snippet} "


# --- Second path: document explanation (declaration page, garaging proof) ---

DOCUMENT_TOPIC = "declaration_page_garaging"
DOCUMENT_MAX_SNIPPET_CHARS = 100


def _extract_document_query(text: str) -> Optional[str]:
    """Derive retrieval query when customer asks about document meaning."""
    t = (text or "").strip().lower()
    doc_terms = [
        ("declaration page", "declaration page", "decl page", "dec page", "保单首页"),
        ("garaging proof", "garaging", "proof of garaging", "车辆停放", "停放地址"),
    ]
    has_question = any(x in t for x in ("什么", "是什么意思", "what is", "what does", "why", "为什么", "怎么"))
    for terms_tuple in doc_terms:
        if any(term in t for term in terms_tuple):
            if "declaration" in t or "dec" in t or "decl" in t or "保单首页" in t:
                return "What is declaration page? Why do they need it?"
            if "garaging" in t or "停放" in t:
                return "What is garaging proof? Why do they need it?"
            return "What is declaration page or garaging proof? Why does the carrier need these documents?"
    if has_question and ("缺" in t or "补" in t or "需要" in t or "need" in t or "request" in t):
        return "Why does the carrier need declaration page or garaging proof?"
    return None


def retrieve_document_explanation(customer_message: str) -> Optional[str]:
    """
    Retrieve a brief knowledge-backed snippet for document confusion (declaration page, garaging proof).

    Returns a short string to augment the reply, or None if retrieval fails or message is not document-related.

    Safe: catches all exceptions, returns None on any failure.
    Fallback: when retrieval is unavailable, returns None and caller uses template-only reply.
    """
    query = _extract_document_query(customer_message)
    if not query:
        return None

    if os.getenv("NOTICE_RETRIEVAL_ENABLED", "1").lower() in ("0", "false", "off"):
        return None

    try:
        from services.fiqa_api.clients import (
            EMBED_READY,
            EmbeddingUnreadyError,
            get_embedder,
            get_qdrant_client,
        )
        from services.fiqa_api.utils.qdrant_adapter import qdrant_search
    except ImportError as e:
        logger.debug(f"Document retrieval: import failed: {e}")
        return None

    if not EMBED_READY:
        logger.info(
            "[DOCUMENT_RETRIEVAL] Embedder warming up — using template-only fallback for document explanation"
        )
        return None

    embedder = None
    client = None
    try:
        embedder = get_embedder()
        client = get_qdrant_client()
    except EmbeddingUnreadyError:
        logger.info(
            "[DOCUMENT_RETRIEVAL] Embedder not ready — using template-only fallback"
        )
        return None
    except Exception as e:
        logger.info(f"[DOCUMENT_RETRIEVAL] Client init failed ({type(e).__name__}) — using template fallback: {e}")
        return None

    if embedder is None or client is None:
        return None

    try:
        vec = embedder.encode([query])[0]
        if hasattr(vec, "tolist"):
            vec = vec.tolist()

        results = qdrant_search(
            client=client,
            collection_name=COLLECTION_NAME,
            query_vector=vec,
            limit=5,
            with_payload=True,
        )

        if not results:
            return None

        for r in results:
            score = getattr(r, "score", None)
            if score is None and isinstance(r, dict):
                score = r.get("score", 0.0)
            score = float(score or 0.0)
            if score < MIN_SCORE:
                continue
            if isinstance(r, dict):
                payload = r.get("payload", r)
            else:
                payload = getattr(r, "payload", None) or {}
            topic = payload.get("topic", "")
            if topic != DOCUMENT_TOPIC:
                continue
            text = payload.get("text") or payload.get("title") or ""
            if not text:
                continue
            clean = re.sub(r"\*\*|\#|\[|\]|\(|\)", "", text)
            clean = clean.replace("\n", " ").strip()
            if len(clean) > DOCUMENT_MAX_SNIPPET_CHARS:
                clean = clean[:DOCUMENT_MAX_SNIPPET_CHARS].rsplit(" ", 1)[0] + "..."
            return clean
    except Exception as e:
        logger.info(f"[DOCUMENT_RETRIEVAL] Search failed ({type(e).__name__}) — using template fallback: {e}")
        return None

    return None
