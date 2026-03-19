"""
query.py - Query Route Handler (Frontend API)
==============================================
Handles /api/query endpoint with frontend-friendly request/response format.
Core logic delegated to services/search_core.py.
"""

import logging
import uuid
import time
import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlparse

# Collection name mapping (dataset_name -> collection_name)
COLLECTION_MAP = {
    "fiqa": "fiqa_10k_v1",  # Default to fiqa_10k_v1 for demo
    "fiqa_10k_v1": "fiqa_10k_v1",
    "fiqa_50k_v1": "fiqa_50k_v1",
    "fiqa_para_50k": "fiqa_para_50k",
    "fiqa_sent_50k": "fiqa_sent_50k",
    "fiqa_win256_o64_50k": "fiqa_win256_o64_50k",
    # Airbnb LA demo
    "airbnb_la_demo": "airbnb_la_demo",
    # Auto Insurance (南加州汽车保险)
    "auto_insurance": "auto_insurance_v2_clean",
    "auto_insurance_v1": "auto_insurance_v1",
    "auto_insurance_v2_clean": "auto_insurance_v2_clean",
    # Demo collection for business presentation
    "demo_auto_insurance": "auto_insurance_demo_core",
    "auto_insurance_demo_core": "auto_insurance_demo_core",
}


from fastapi import APIRouter, Header, HTTPException, Request, Response, Query as FastAPIQuery
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, root_validator

try:
    from clients.retrieval_proxy_client import (
        DEFAULT_BUDGET_MS as PROXY_DEFAULT_BUDGET_MS,
        USE_PROXY as USE_RETRIEVAL_PROXY,
        search as proxy_search,
    )
except ModuleNotFoundError:  # pragma: no cover - container fallback
    PROXY_DEFAULT_BUDGET_MS = 400
    USE_RETRIEVAL_PROXY = False

    def proxy_search(*args, **kwargs):
        raise RuntimeError("retrieval proxy client unavailable")

from services.fiqa_api import obs
from services.fiqa_api.services.search_core import perform_search
from services.fiqa_api.services.search_profiles import get_search_profile
from services.fiqa_api.utils.translation import (
    detect_lang, translate_zh_to_en, translate_en_to_zh, is_translation_available, translation_debug_state
)

logger = logging.getLogger(__name__)

# ========================================
# Router Setup
# ========================================

router = APIRouter()


# ========================================
# Constants
# ========================================

DEFAULT_TOP_K = 20
MAX_TOP_K = 100
QUERY_TIMEOUT_SEC = float(os.getenv("QUERY_TIMEOUT_S", "45.0"))
RRF_K_DEFAULT = int(os.getenv("RRF_K_DEFAULT", "60"))
RERANK_TOPK_DEFAULT = int(os.getenv("RERANK_TOPK_DEFAULT", "20"))
EXPECTED_QDRANT_DIM = 384  # Dimension for all-MiniLM-L6-v2 and bge-small-en-v1.5


# ========================================
# Helper Functions
# ========================================

def get_default_metrics() -> dict:
    """Return default metrics structure with all required keys."""
    return {
        "qps": 0,
        "p95_ms": 0,
        "recall_at_10": 0,
        "total": 0
    }


def _build_snippet(text_zh: Optional[str], text: str, title: str, domain: str) -> str:
    """Build a short excerpt (max 320 chars). Prefer text_zh else text; fallback to title — domain."""
    raw = (text_zh or text or "").strip()
    if raw:
        collapsed = " ".join(raw.split())
        return collapsed[:320] if collapsed else f"{title or 'Untitled'} — {domain or 'unknown'}"
    return f"{title or 'Untitled'} — {domain or 'unknown'}"


def _domain_from_url(url: str) -> str:
    """Extract hostname from URL."""
    if not url:
        return ""
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


# Broker demo answer-fix triggers (Q2 reinstatement fee, Q5 claims fallback, SR-22/proof)
_BROKER_CLAIMS_KEYWORDS = ("理赔", "出险", "claims", "incident", "accident", "车祸")
_BROKER_CLAIMS_DOMAINS = ("geico.com", "progressive.com", "insurance.ca.gov")
_BROKER_SUSPENSION_KEYWORDS = ("暂停", "恢复", "suspended", "reinstatement", "复职")
_BROKER_SR22_KEYWORDS = ("sr-22", "sr22", "certificate of financial responsibility", "保险证明", "proof of insurance", "电子卡")
_BROKER_NEWCAR_KEYWORDS = ("新车", "最低", "保额", "最低要求", "new car", "minimum")
_BROKER_LICENSE_KEYWORDS = ("合规", "执照", "insurance.ca.gov", "license")
_BROKER_NOT_CONTAIN_MARKERS = (
    "does not contain",
    "context does not contain",
    "not contain specific",
    "cannot provide",
    "cannot answer",
    "无法提供",
    "无法回答",
    "上下文中没有",
    "未包含",
)


def _apply_broker_demo_answer_fixes(
    answer: str,
    question_original: Optional[str],
    cleaned_question: str,
    sources: list,
    mode: Optional[str],
) -> str:
    """
    Apply broker-demo-specific answer fixes for Q2 ($14 fee) and Q5 (claims fallback).
    Called when mode=demo or for auto_insurance_demo_core.
    """
    if not answer and not sources:
        return answer
    q = (question_original or cleaned_question or "").lower()
    out = answer

    # Q5 fallback: LLM returns "context does not contain" despite good retrieval
    has_claims_q = any(kw in q for kw in _BROKER_CLAIMS_KEYWORDS)
    has_claims_sources = any(
        any(cd in ((s.get("domain") or "").lower()) for cd in _BROKER_CLAIMS_DOMAINS)
        or "claims" in (s.get("url") or s.get("source_url") or "").lower()
        for s in (sources or [])
    )
    if has_claims_q and has_claims_sources:
        ans_low = (out or "").lower()
        if any(m in ans_low for m in _BROKER_NOT_CONTAIN_MARKERS):
            out = (
                "出险后理赔流程：1. 确保人员安全，检查受伤情况；2. 如有需要，将车辆移至路边；"
                "3. 通知当局；4. 收集信息（对方司机、车辆、照片）；5. 联系保险公司或通过在线/移动应用提交索赔。"
                "各公司流程略有不同，建议查看保单或联系保险公司确认具体步骤。"
            )

    # Q2 $14 hint: surface reinstatement fee when suspension question + DMV suspended source
    has_suspension_q = any(kw in q for kw in _BROKER_SUSPENSION_KEYWORDS)
    def _has_dmv_suspended(s: dict) -> bool:
        d = (s.get("domain") or "").lower()
        u = (s.get("url") or s.get("source_url") or "").lower()
        return ("dmv" in d or "ca.gov" in d) and "suspended" in u
    has_dmv_suspended = any(_has_dmv_suspended(s) for s in (sources or []))
    if has_suspension_q and has_dmv_suspended and out:
        if "$14" not in out:
            hint = "\n\n恢复费约 $14（以 DMV 官网为准）。"
            if hint not in out:
                out = out.rstrip() + hint

    # SR-22 / proof-of-insurance: fallback when answer thin or "does not contain"
    has_sr22_q = any(kw in q for kw in _BROKER_SR22_KEYWORDS)
    ans_low = (out or "").lower()
    sr22_answer_thin = has_sr22_q and (
        len(out or "") < 150
        or any(m in ans_low for m in _BROKER_NOT_CONTAIN_MARKERS)
    )
    if sr22_answer_thin:
        out = (
            "SR-22 是财务责任证明书（Certificate of Financial Responsibility），由保险公司向加州 DMV 提交，"
            "证明客户持有最低责任险。常见需要 SR-22 的情况：DUI、无保险事故、多次违规点数、驾照暂停等。"
            "办理方式：通过保险公司或经纪人购买符合要求的保险，保险公司会向 DMV 电子提交 SR-22。"
            "通常需连续维持约 3 年。电子保险卡一般可作为日常证明；SR-22 由保险公司单独向 DMV 提交。"
            "详细要求以 DMV 官网为准。"
        )
        broker_hint_sr22 = (
            "\n\n**客户可准备**：驾照、当前保单（如有）、DMV 通知函。"
            "\n\n**经纪人可进一步询问**：客户是否有 DMV/法院要求、具体违规类型、当前是否有保险。"
            "\n\n**经纪人下一步**：确认客户需求，协助购买符合要求的保险，保险公司会向 DMV 提交 SR-22。各公司承保政策不同，建议多家比价。"
        )
        out = out.rstrip() + broker_hint_sr22

    # SR-22 broker hint: append when SR-22/proof question and answer lacks broker guidance (non-fallback case)
    if has_sr22_q and out and not sr22_answer_thin:
        broker_hint_sr22 = (
            "\n\n**客户可准备**：驾照、当前保单（如有）、DMV 通知函。"
            "\n\n**经纪人可进一步询问**：客户是否有 DMV/法院要求、具体违规类型、当前是否有保险。"
            "\n\n**经纪人下一步**：确认客户需求，协助购买符合要求的保险，保险公司会向 DMV 提交 SR-22。各公司承保政策不同，建议多家比价。"
        )
        if "经纪人可进一步询问" not in out and broker_hint_sr22 not in out:
            out = out.rstrip() + broker_hint_sr22

    # Q1 (new car): broker workflow hint when answer lacks it
    has_newcar_q = any(kw in q for kw in _BROKER_NEWCAR_KEYWORDS) and "新车" in q
    if has_newcar_q and out and "经纪人可进一步询问" not in out:
        hint = (
            "\n\n**客户可准备**：车辆信息、驾照、VIN（如有）。"
            "\n\n**经纪人可进一步询问**：车型、用途、预算、是否贷款、是否需加保碰撞/综合险。"
            "\n\n**经纪人下一步**：确认客户车辆/驾照信息，给出 2–3 套方案并附官方链接。"
        )
        out = out.rstrip() + hint

    # Q2 (suspension): broker workflow hint when answer lacks it (Q2 already gets $14 above)
    if has_suspension_q and out and "经纪人可进一步询问" not in out:
        hint = (
            "\n\n**客户可准备**：保险证明、驾照、DMV 通知函。"
            "\n\n**经纪人可进一步询问**：暂停原因（保险失效/费用）、是否已续保、当前保单号。"
            "\n\n**经纪人下一步**：确认暂停原因，引导客户至 DMV 在线提交保险证明并缴费（约 $14）。"
        )
        out = out.rstrip() + hint

    # Q3 (license/compliance): broker workflow hint when answer lacks it
    has_license_q = any(kw in q for kw in _BROKER_LICENSE_KEYWORDS)
    if has_license_q and out and "经纪人可进一步询问" not in out:
        hint = (
            "\n\n**客户可准备**：公司/经纪人名称或执照号。"
            "\n\n**经纪人可进一步询问**：客户要查的是公司还是个人、是否有执照号，可引导至 insurance.ca.gov 查执照。"
            "\n\n**经纪人下一步**：打开 insurance.ca.gov 查执照，截图保存发给客户。"
        )
        out = out.rstrip() + hint

    # Q5 (claims): broker workflow hint when answer lacks it
    if has_claims_q and out and "经纪人可进一步询问" not in out:
        hint = (
            "\n\n**客户可准备**：保单号、驾照、事故说明、现场照片、对方信息。"
            "\n\n**经纪人可进一步询问**：事故时间、人员伤亡、是否已报警、保单号，指导在线或电话报案。"
            "\n\n**经纪人下一步**：安抚客户，指导在线或电话报案，协助准备材料。"
        )
        out = out.rstrip() + hint

    return out


def _item_to_source(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert search result item to frontend-friendly source format."""
    payload = item.get("payload") if isinstance(item, dict) else {}
    if not isinstance(payload, dict):
        payload = {}
    doc_id = payload.get("doc_id") or item.get("id") or payload.get("id") or "unknown"
    title = payload.get("title") or item.get("title", "")
    text = payload.get("text") or item.get("text", "")
    text_zh = payload.get("text_zh") or item.get("text_zh", "")
    source_url = payload.get("url") or payload.get("source_url") or item.get("url") or item.get("source_url") or ""
    domain = payload.get("domain") or item.get("domain") or _domain_from_url(source_url)
    score = item.get("score", 0.0)
    snippet = _build_snippet(text_zh, text, title, domain)
    return {
        "doc_id": doc_id,
        "title": title,
        "text": text,
        "source_url": source_url,
        "url": source_url,
        "domain": domain,
        "snippet": snippet,
        "score": score,
    }


def build_effective_params(request: "QueryRequest", profile) -> Dict[str, Any]:
    """
    Build effective parameters by merging profile defaults with request parameters.
    
    Priority: request explicit fields > profile.default_filters > original defaults
    
    Args:
        request: QueryRequest instance
        profile: SearchProfile instance
    
    Returns:
        Dict with effective parameters:
            - collection: str
            - price_max: Optional[float]
            - min_bedrooms: Optional[int]
            - neighbourhood: Optional[str]
            - room_type: Optional[str]
    """
    effective = {}
    
    # Collection: request.collection (if explicitly set and not default) > profile.collection > "fiqa"
    # If profile_name is specified and request.collection is default "fiqa", prefer profile's collection
    if request.profile_name and request.collection == "fiqa" and profile.collection:
        # Profile is specified, use profile's collection instead of default "fiqa"
        effective["collection"] = profile.collection
    elif request.collection is not None and request.collection != "fiqa":
        # Explicitly set collection in request (not default "fiqa")
        effective["collection"] = request.collection
    elif profile.collection:
        # Use profile's collection if request doesn't explicitly set one
        effective["collection"] = profile.collection
    else:
        # Fallback to default
        effective["collection"] = request.collection if request.collection is not None else "fiqa"
    
    # Filters: request explicit > profile.default_filters > None
    effective["price_max"] = (
        request.price_max 
        if request.price_max is not None 
        else profile.default_filters.get("price_max")
    )
    
    effective["min_bedrooms"] = (
        request.min_bedrooms 
        if request.min_bedrooms is not None 
        else profile.default_filters.get("min_bedrooms")
    )
    
    effective["neighbourhood"] = (
        request.neighbourhood 
        if request.neighbourhood is not None 
        else profile.default_filters.get("neighbourhood")
    )
    
    effective["room_type"] = (
        request.room_type 
        if request.room_type is not None 
        else profile.default_filters.get("room_type")
    )
    
    return effective


# ========================================
# Request/Response Models
# ========================================

class QueryRequest(BaseModel):
    """Query request model (frontend format)."""
    question: str = Field(..., alias="question")
    budget_ms: Optional[int] = Field(default=None, alias="budget_ms")
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K, description=f"Number of results (default: {DEFAULT_TOP_K}, max: {MAX_TOP_K})")
    collection: Optional[str] = Field(default="auto_insurance", description="Collection name (e.g., 'auto_insurance', 'fiqa', 'fiqa_50k_v1', 'fiqa_10k_v1')")
    rerank: bool = Field(default=False, description="Whether to rerank results")
    use_hybrid: bool = Field(default=False, description="Whether to use hybrid retrieval (BM25 + vector fusion)")
    rrf_k: Optional[int] = Field(default=None, ge=1, le=100, description="RRF reciprocal rank fusion k parameter")
    rerank_top_k: Optional[int] = Field(default=None, ge=1, le=100, description="Number of candidates to rerank")
    rerank_if_margin_below: Optional[float] = Field(default=0.12, ge=0.0, le=1.0, description="Margin threshold for gated reranking")
    max_rerank_trigger_rate: float = Field(default=0.25, ge=0.0, le=1.0, description="Max rerank trigger rate")
    rerank_budget_ms: int = Field(default=25, ge=1, le=1000, description="Rerank budget in milliseconds")
    use_kv_cache: bool = Field(default=False, description="Whether to use KV-cache for generation (experimental)")
    session_id: Optional[str] = Field(default=None, description="Logical session id for KV-cache behavior")
    stream: bool = Field(default=False, description="Whether to stream the response (experimental)")
    generate_answer: bool = Field(
        default=False,
        description="Whether to call LLM to generate an answer (defaults to False for backward compatibility). "
                    "Note: stream=True implicitly enables answer generation.",
    )
    translation_mode: Optional[str] = Field(
        default=None,
        description="Translation mode: 'auto' (auto-detect and translate Chinese), True (force translate), False (disable)"
    )
    translate: Optional[bool] = Field(
        default=None,
        description="Alias for translation_mode='auto' when True"
    )
    # Search profile support
    profile_name: Optional[str] = Field(default=None, description="Search profile name (e.g., 'airbnb_la_location_first')")
    # Filter fields (placeholder, will be used for filtering in future)
    price_max: Optional[float] = Field(default=None, ge=0.0, description="Maximum price filter")
    min_bedrooms: Optional[int] = Field(default=None, ge=0, description="Minimum bedrooms filter")
    neighbourhood: Optional[str] = Field(default=None, description="Neighbourhood filter")
    room_type: Optional[str] = Field(default=None, description="Room type filter")
    # Demo mode support
    mode: Optional[str] = Field(default=None, description="Mode: 'demo' to use demo collection with top_k=5")

    @root_validator(pre=True)
    def _alias_q(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "question" not in values:
            alias_val = values.pop("q", None)
            if alias_val:
                values["question"] = alias_val
        if "budget_ms" not in values and "budget" in values:
            values["budget_ms"] = values.get("budget")
        # Handle translate alias
        if "translate" in values and values["translate"] is True and "translation_mode" not in values:
            values["translation_mode"] = "auto"
        return values

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


# ========================================
# Route Handler
# ========================================

async def _execute_query(
    request_model: QueryRequest,
    response: Response,
    raw_request: Request,
    x_trace_id: Optional[str] = None,
):
    """
    Query endpoint with frontend-friendly format.
    
    Maps frontend `question` → core `query`, calls search_core.perform_search,
    and adapts response to frontend format with trace_id, sources, etc.
    
    Supports both streaming (SSE) and non-streaming (JSON) responses.
    When stream=True, returns StreamingResponse with SSE format.
    When stream=False, generates answer using LLM (if available) and returns JSON.
    
    Includes model consistency checks and embedding model header.
    
    Request body:
        question: str - User's question
        top_k: int - Number of results (default: 20, max: 100)
        rerank: bool - Whether to rerank results (default: False)
        stream: bool - Whether to stream response (default: False)
        use_kv_cache: bool - Whether to use KV-cache (experimental, default: False)
    
    Returns:
        JSON (stream=False):
        {
            "ok": true,
            "trace_id": "uuid",
            "question": "string",
            "answer": "string",  # Generated answer or empty if LLM unavailable
            "latency_ms": float,
            "route": "string",
            "params": {"top_k": int, "rerank": bool},
            "sources": [...],  # Mapped from search results
            "metrics": {...},  # Structured metrics object (may include llm_usage)
            "reranker_triggered": false,
            "ts": "ISO8601 timestamp"
        }
        
        StreamingResponse (stream=True):
        Server-Sent Events stream with answer chunks
    
    Response headers:
        X-Trace-Id: Request trace ID for correlation
    """
    request = request_model
    
    # Handle streaming requests
    if request.stream:
        return await _execute_query_streaming(request, response, raw_request, x_trace_id)
    # Performance tracking
    start = time.perf_counter()
    
    # Generate or reuse trace_id
    trace_id_candidate = (x_trace_id or "").strip()
    trace_id = trace_id_candidate or str(uuid.uuid4())
    
    # Set trace_id in response headers for correlation
    response.headers["X-Trace-Id"] = trace_id
    raw_request.state.trace_id = trace_id
    obs_ctx = {"trace_id": trace_id, "job_id": trace_id}
    raw_request.state.obs_ctx = obs_ctx
    
    cleaned_question = request.question.strip() if request.question else ""
    if not cleaned_question:
        logger.warning(f"level=WARN trace_id={trace_id} status=INVALID_INPUT msg='Empty question provided'")
        raise HTTPException(
            status_code=400,
            detail="question cannot be empty"
        )
    
    # Translation support: detect language and translate if needed
    # Initialize all translation variables with explicit defaults AT THE VERY BEGINNING
    # This ensures they're always in scope for error handlers
    question_original = cleaned_question
    question_used = cleaned_question
    translation_applied = False
    detected_lang = "unknown"  # Initialize with default, not None
    translation_error = None
    
    # Check if translation is requested (via request param or auto-detect)
    # QueryRequest model includes translation_mode field (line 200), so it should be accessible
    translation_mode = getattr(request, "translation_mode", None)
    if translation_mode is None:
        # Fallback to translate field if translation_mode is not set
        translate_flag = getattr(request, "translate", False)
        if translate_flag is True:
            translation_mode = "auto"
        else:
            translation_mode = None
    
    print(f"[query] translation_mode={translation_mode}, question={cleaned_question[:40]}")
    
    # Detect language (always detect, even if translation is not enabled)
    try:
        detected_lang = detect_lang(cleaned_question)
        if detected_lang is None:
            detected_lang = "unknown"
    except Exception as e:
        detected_lang = "unknown"
        logger.warning(f"[translation] detect_lang failed: {e}")
    
    print(f"[translation] available={is_translation_available()}, state={translation_debug_state()}")
    print(f"[translation] detected_lang={detected_lang}")
    
    if translation_mode == "auto" or (translation_mode is True and detected_lang == "zh"):
        # Auto-translate Chinese queries
        if detected_lang == "zh":
            if is_translation_available():
                try:
                    translated = translate_zh_to_en(cleaned_question)
                    if translated and translated.strip():
                        question_used = translated
                        translation_applied = True
                        print(f"[translation] applied zh->en, question_used={question_used[:60]}")
                        logger.info(f"[translation] zh -> en ok trace_id={trace_id} original='{cleaned_question[:50]}...' translated='{translated[:50]}...'")
                    else:
                        translation_error = "Translation returned empty result"
                        logger.warning(f"[translation] zh -> en failed (empty) trace_id={trace_id} original='{cleaned_question[:50]}...'")
                except Exception as e:
                    translation_error = f"Translation exception: {str(e)}"
                    logger.error(f"[translation] zh -> en error trace_id={trace_id} error='{str(e)}'")
                    # Fallback: use original question
            else:
                translation_error = "Translation service not available"
                logger.warning(f"[translation] service unavailable trace_id={trace_id}")
        elif translation_mode is True and detected_lang != "zh":
            # Explicit translation requested but not Chinese - use original
            logger.debug(f"[translation] requested but not Chinese trace_id={trace_id} lang={detected_lang}")
    
    # Handle demo mode
    if getattr(request, "mode", None) == "demo":
        # Demo mode: force use demo collection and top_k=5
        collection_name = "demo_auto_insurance"
        request.top_k = 5  # Override top_k for demo mode
        effective_params = {"collection": collection_name}  # Minimal params for demo mode
        logger.info(f"level=INFO trace_id={trace_id} mode=DEMO collection={collection_name} top_k={request.top_k}")
    else:
        # Apply search profile (if specified)
        profile = get_search_profile(request.profile_name)
        effective_params = build_effective_params(request, profile)
        
        # Use effective collection (from profile or request)
        collection_name = effective_params["collection"]
        # Fallback to environment variable if still not set
        if not collection_name:
            default_collection = os.getenv("DEFAULT_SEARCH_COLLECTION", "fiqa")
            collection_name = default_collection
    
    actual_collection = COLLECTION_MAP.get(collection_name, collection_name)
    
    # Log profile and effective parameters
    logger.info(
        f"level=INFO trace_id={trace_id} "
        f"profile_name={request.profile_name or 'None'} "
        f"effective_collection={actual_collection} "
        f"effective_price_max={effective_params.get('price_max')} "
        f"effective_min_bedrooms={effective_params.get('min_bedrooms')} "
        f"effective_neighbourhood={effective_params.get('neighbourhood')} "
        f"effective_room_type={effective_params.get('room_type')}"
    )
    
    if USE_RETRIEVAL_PROXY:
        try:
            proxy_budget = request.budget_ms if request.budget_ms is not None else PROXY_DEFAULT_BUDGET_MS
            items, timings, degraded, trace_url = proxy_search(
                query=cleaned_question,
                k=request.top_k,
                budget_ms=proxy_budget,
                trace_id=trace_id,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "level=WARN trace_id=%s status=PROXY_FALLBACK error='%s'",
                trace_id,
                exc,
            )
        else:
            latency_ms = timings.get("total_ms")
            if latency_ms is None:
                latency_ms = (time.perf_counter() - start) * 1000
            latency_ms = float(latency_ms)
            ret_code = timings.get("ret_code") or "OK"
            route_used = timings.get("route") or "retrieval_proxy"
            cache_hit = bool(timings.get("cache_hit"))
            per_source = timings.get("per_source_ms") or {}
            response.headers["X-Backend"] = route_used
            response.headers["X-Top-K"] = str(request.top_k)
            response.headers["X-Mode"] = "fast" if getattr(request, "fast_mode", False) else "normal"
            response.headers["X-Hybrid"] = "true" if request.use_hybrid else "false"
            response.headers["X-Rerank"] = "true" if request.rerank else "false"
            response.headers["X-Dataset"] = collection_name
            response.headers["X-Qrels"] = "unknown"
            response.headers["X-Collection"] = actual_collection
            response.headers["X-Search-MS"] = f"{latency_ms:.1f}"
            response.headers["X-Rerank-MS"] = "0.0"
            response.headers["X-Total-MS"] = f"{latency_ms:.1f}"
            response.headers["X-Embed-Model"] = "retrieval-proxy"
            response.headers["X-Proxy-RetCode"] = ret_code
            if per_source:
                response.headers["X-Proxy-Sources"] = json.dumps(per_source)
            if trace_url:
                response.headers["X-Langfuse-Trace-Url"] = trace_url
            sources = [_item_to_source(item) for item in items]
            base_metrics = get_default_metrics()
            base_metrics["total"] = len(sources)
            base_metrics["proxy_ret_code"] = ret_code
            base_metrics["proxy_cache_hit"] = cache_hit
            base_metrics["proxy_degraded"] = degraded
            observability_metrics = {
                "fusion_overlap": 0,
                "rrf_candidates": 0,
                "rerank_triggered": False,
                "rerank_timeout": False,
                "proxy_cache_hit": cache_hit,
                "proxy_degraded": degraded,
            }
            log_payload = {
                "trace_id": trace_id,
                "status": "SUCCESS",
                "route": route_used,
                "latency_total_ms": round(latency_ms, 1),
                "top_k": request.top_k,
                "hybrid": request.use_hybrid,
                "rerank": request.rerank,
                "ret_code": ret_code,
                "cache_hit": cache_hit,
                "degraded": degraded,
                "use_kv_cache": request.use_kv_cache,
                "stream": request.stream,
            }
            logger.info("level=INFO %s", json.dumps(log_payload))
            
            # Generate answer using LLM for proxy path (non-streaming only)
            # Same semantic rules as main path: generate_answer or stream enables generation
            answer = ""
            llm_usage = None
            should_generate = (request.generate_answer or request.stream)
            
            if should_generate and not request.stream:
                from services.fiqa_api.clients import get_openai_client
                from services.fiqa_api.utils.llm_client import generate_answer_for_query
                
                openai_client = get_openai_client()
                if openai_client is not None and sources:
                    try:
                        context = []
                        for source in sources[:10]:
                            context_item = {
                                "title": source.get("title", source.get("doc_id", "")),
                                "text": source.get("text", source.get("content", "")),
                            }
                            context.append(context_item)
                        
                        answer, llm_usage, kv_enabled, kv_hit = generate_answer_for_query(
                            question=cleaned_question,
                            context=context,
                            use_kv_cache=request.use_kv_cache,
                            session_id=request.session_id,
                        )
                    except Exception as e:
                        logger.warning(f"level=WARN trace_id={trace_id} LLM generation failed: {e}")
                        kv_enabled = False
                        kv_hit = False
            
            if llm_usage:
                base_metrics["llm_usage"] = llm_usage
                base_metrics["llm_enabled"] = True
                base_metrics["kv_enabled"] = kv_enabled if 'kv_enabled' in locals() else bool(request.use_kv_cache)
                base_metrics["kv_hit"] = kv_hit if 'kv_hit' in locals() else False
            else:
                base_metrics["llm_enabled"] = False
                base_metrics["kv_enabled"] = False
                base_metrics["kv_hit"] = False

            # Broker demo: Q5 claims fallback + Q2 $14 hint (proxy path)
            if getattr(request, "mode", None) == "demo":
                answer = _apply_broker_demo_answer_fixes(
                    answer, question_original, cleaned_question, sources, getattr(request, "mode", None)
                )
            
            try:
                obs.finalize_root(
                    job_id=trace_id,
                    trace_id=trace_id,
                    trace_url=trace_url or "",
                    metrics=base_metrics,
                    decision=route_used,
                )
                if trace_url:
                    raw_request.state.trace_url = trace_url
            except Exception:
                pass
            return {
                "ok": True,
                "trace_id": trace_id,
                "question": question_original,  # Original question
                "question_used": question_used if question_used else question_original,  # Question used for search (may be translated)
                "translation_applied": bool(translation_applied),  # Ensure boolean, never None
                "detected_lang": detected_lang if detected_lang else "unknown",  # Ensure string, never None
                "translation_error": translation_error if translation_error else "",  # Error message if translation failed, empty string if None
                "answer": answer,  # ✅ Generated answer or empty
                "latency_ms": latency_ms,
                "route": route_used,
                "params": {
                    "top_k": request.top_k,
                    "rerank": request.rerank,
                    "use_hybrid": request.use_hybrid,
                    "rrf_k": request.rrf_k if request.use_hybrid else None,
                },
                "sources": sources,
                "items": sources,
                "metrics": base_metrics,
                "observability_metrics": observability_metrics,
                "reranker_triggered": False,
                "degraded": bool(degraded),
                "budget_ms": request.budget_ms,
                "ts": datetime.utcnow().isoformat() + "Z",
            }
    try:
        # Check embedding readiness (cold-start warmup)
        from services.fiqa_api.clients import EMBED_READY, EmbeddingUnreadyError, get_embedder
        if not EMBED_READY:
            logger.warning(f"level=WARN trace_id={trace_id} status=EMBEDDING_WARMING msg='Embedding model not ready'")
            response.headers["Retry-After"] = "10"
            raise HTTPException(
                status_code=503,
                detail={"ok": False, "error": "embedding_warming"}
            )
        
        # Get embedding metadata for headers
        embedder = None
        embed_model = "unknown"
        embed_backend = os.getenv("EMBEDDING_BACKEND", "UNKNOWN")
        embed_dim = None
        try:
            embedder = get_embedder()
            embed_model = getattr(embedder, "model_name", os.getenv("SBERT_MODEL", "unknown"))
            embed_dim = getattr(embedder, "dim", None)
        except Exception as e:
            logger.warning(f"level=WARN trace_id={trace_id} status=EMBED_INFO_FAILED msg='Could not get embedder info: {e}'")
        
        # Model consistency check
        expected_model = os.getenv("EXPECTED_EMBED_MODEL")
        if expected_model:
            try:
                if embed_model and embed_model != expected_model:
                    logger.error(f"level=ERROR trace_id={trace_id} status=MODEL_MISMATCH expected={expected_model} got={embed_model}")
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "ok": False,
                            "error": "embed_model_mismatch",
                            "expected": expected_model,
                            "got": embed_model
                        }
                    )
                # Set model header
                response.headers["X-Embed-Model"] = embed_model or "unknown"
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"level=WARN trace_id={trace_id} status=MODEL_CHECK_FAILED msg='Could not verify model: {e}'")
                # Non-fatal: continue with query
        else:
            # Set header anyway
            response.headers["X-Embed-Model"] = embed_model
        
        # Check Qdrant collection dimension
        try:
            from services.fiqa_api.clients import get_qdrant_client
            qdrant_client = get_qdrant_client()
            collection_info = qdrant_client.get_collection(actual_collection)
            # Get dimension from collection config
            if hasattr(collection_info.config.params.vectors, 'size'):
                qdrant_dim = collection_info.config.params.vectors.size
            elif hasattr(collection_info.config.params, 'vectors') and isinstance(collection_info.config.params.vectors, dict):
                qdrant_dim = collection_info.config.params.vectors.get('size')
            else:
                # Fallback: try to get from config
                qdrant_dim = getattr(collection_info.config.params.vectors, 'size', None)
            
            if qdrant_dim is not None and qdrant_dim != EXPECTED_QDRANT_DIM:
                logger.error(f"level=ERROR trace_id={trace_id} status=DIM_MISMATCH qdrant_dim={qdrant_dim} expected={EXPECTED_QDRANT_DIM}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "ok": False,
                        "error": "dim_mismatch",
                        "qdrant_dim": qdrant_dim,
                        "expected": EXPECTED_QDRANT_DIM
                    }
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"level=WARN trace_id={trace_id} status=DIM_CHECK_FAILED msg='Could not verify Qdrant dimension: {e}'")
            # Non-fatal: continue with query
        
        # Get app state from global app instance
        try:
            from services.fiqa_api.app_main import app
            routing_flags = app.state.routing_flags
            faiss_engine = app.state.faiss_engine
            faiss_ready = app.state.faiss_ready
            faiss_enabled = app.state.faiss_enabled
        except Exception as e:
            logger.error(f"level=ERROR trace_id={trace_id} status=APP_STATE_ERROR error='{str(e)}'")
            # Fallback defaults
            routing_flags = {"enabled": True, "mode": "rules"}
            faiss_engine = None
            faiss_ready = False
            faiss_enabled = False
        
        # Apply parameter bounds protection with defaults
        rrf_k = max(1, min(request.rrf_k if request.rrf_k is not None else RRF_K_DEFAULT, 100))
        rerank_top_k = max(1, min(request.rerank_top_k if request.rerank_top_k is not None else RERANK_TOPK_DEFAULT, request.top_k))
        
        # Call core search logic with timeout
        try:
            search_result = await asyncio.wait_for(
                asyncio.to_thread(
                    perform_search,
                    query=question_used,  # Use translated query if translation was applied
                    top_k=request.top_k,
                    collection=collection_name,
                    routing_flags=routing_flags,
                    faiss_engine=faiss_engine,
                    faiss_ready=faiss_ready,
                    faiss_enabled=faiss_enabled,
                    lab_headers=None,
                    use_hybrid=request.use_hybrid,
                    rrf_k=rrf_k,
                    rerank=request.rerank,
                    rerank_top_k=rerank_top_k,
                    rerank_if_margin_below=request.rerank_if_margin_below,
                    max_rerank_trigger_rate=request.max_rerank_trigger_rate,
                    rerank_budget_ms=request.rerank_budget_ms,
                    obs_ctx=obs_ctx,
                    # Pass effective filter parameters
                    price_max=effective_params.get("price_max"),
                    min_bedrooms=effective_params.get("min_bedrooms"),
                    neighbourhood=effective_params.get("neighbourhood"),
                    room_type=effective_params.get("room_type"),
                    profile_name=request.profile_name,
                ),
                timeout=QUERY_TIMEOUT_SEC
            )
        except asyncio.TimeoutError:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"level=ERROR trace_id={trace_id} status=TIMEOUT route='unknown' latency_ms={elapsed:.1f} timeout_sec={QUERY_TIMEOUT_SEC}")
            raise HTTPException(
                status_code=504,
                detail=f"Query timeout after {QUERY_TIMEOUT_SEC}s"
            )
        except ValueError as ve:
            # Handle dimension mismatch or other ValueError from search_core
            elapsed = (time.perf_counter() - start) * 1000
            error_msg = str(ve)
            if "embedding_dim_mismatch" in error_msg:
                logger.error(f"level=ERROR trace_id={trace_id} status=DIM_MISMATCH latency_ms={elapsed:.1f} error='{error_msg}'")
                raise HTTPException(
                    status_code=400,
                    detail={"ok": False, "error": "embedding_dim_mismatch", "detail": error_msg}
                )
            else:
                logger.error(f"level=ERROR trace_id={trace_id} status=VALIDATION_ERROR latency_ms={elapsed:.1f} error='{error_msg}'")
                raise HTTPException(
                    status_code=400,
                    detail={"ok": False, "error": "validation_error", "detail": error_msg}
                )
        
        # Map search results to frontend sources format
        sources = []
        for result in search_result.get("results", []):
            # Extract source_url and domain from result payload if available
            result_payload = result.get("payload", {}) if isinstance(result.get("payload"), dict) else {}
            source_url = result_payload.get("url") or result_payload.get("source_url") or result.get("url") or result.get("source_url") or ""
            domain = result_payload.get("domain") or result.get("domain") or _domain_from_url(source_url)
            
            title = result.get("title", "")
            text = result.get("text", "")
            
            source = {
                "doc_id": result.get("id", "unknown"),
                "title": title,  # Original English title
                "text": text,  # Original English text
                "source_url": source_url,
                "url": source_url,  # Alias for citation checks
                "domain": domain,
                "score": result.get("score", 0.0)
            }
            
            # Translate sources to Chinese if translation was applied and enabled
            if translation_applied:
                title_zh = translate_en_to_zh(title)
                text_zh = translate_en_to_zh(text)
                
                if title_zh:
                    source["title_zh"] = title_zh
                if text_zh:
                    source["text_zh"] = text_zh
                
                # Also add translations object for structured access
                if title_zh or text_zh:
                    source["translations"] = {
                        "zh": {
                            "title": title_zh or title,
                            "text": text_zh or text
                        }
                    }
            
            # Add snippet (prefer text_zh, else text; fallback title — domain)
            text_for_snippet = source.get("text_zh") or text
            source["snippet"] = _build_snippet(source.get("text_zh"), text_for_snippet, title, domain)
            
            # 如果是 Airbnb collection，添加额外字段
            if actual_collection == "airbnb_la_demo" or collection_name == "airbnb_la_demo":
                if "price" in result:
                    source["price"] = result.get("price")
                if "bedrooms" in result:
                    source["bedrooms"] = result.get("bedrooms")
                if "neighbourhood" in result:
                    source["neighbourhood"] = result.get("neighbourhood")
                if "room_type" in result:
                    source["room_type"] = result.get("room_type")
            sources.append(source)
        
        # Extract timing information
        elapsed = (time.perf_counter() - start) * 1000
        route_used = search_result.get('route', 'unknown')
        latency_search_ms = search_result.get('latency_search_ms', elapsed)
        latency_rerank_ms = search_result.get('latency_rerank_ms', 0.0)
        latency_serialize_ms = search_result.get('latency_serialize_ms', 0.0)
        
        # Set response headers with metadata
        response.headers["X-Embed-Model"] = embed_model
        response.headers["X-Backend"] = embed_backend
        response.headers["X-Top-K"] = str(request.top_k)
        response.headers["X-Mode"] = "fast" if hasattr(request, 'fast_mode') and getattr(request, 'fast_mode', False) else "normal"
        response.headers["X-Hybrid"] = "true" if request.use_hybrid else "false"
        response.headers["X-Rerank"] = "true" if request.rerank else "false"
        response.headers["X-Dataset"] = request.collection or "fiqa"
        response.headers["X-Qrels"] = "unknown"  # Will be set from experiment params if available
        response.headers["X-Collection"] = actual_collection
        response.headers["X-Search-MS"] = f"{float(latency_search_ms):.1f}"
        response.headers["X-Rerank-MS"] = f"{float(latency_rerank_ms):.1f}"
        response.headers["X-Total-MS"] = f"{float(elapsed):.1f}"
        if embed_dim:
            response.headers["X-Dim"] = str(embed_dim)
        
        # Log success with structured JSON
        log_metadata = {
            "trace_id": trace_id,
            "status": "SUCCESS",
            "route": route_used,
            "latency_total_ms": round(elapsed, 1),
            "latency_search_ms": round(latency_search_ms, 1),
            "latency_rerank_ms": round(latency_rerank_ms, 1),
            "latency_serialize_ms": round(latency_serialize_ms, 1),
            "top_k": request.top_k,
            "hybrid": request.use_hybrid,
            "rerank": request.rerank,
            "collection": actual_collection,
            "embed_model": embed_model,
            "backend": embed_backend,
            "dim": embed_dim,
            "use_kv_cache": request.use_kv_cache,
            "stream": request.stream,
        }
        logger.info(f"level=INFO {json.dumps(log_metadata)}")
        
        # Extract metrics from search result
        metrics_details = search_result.get("metrics_details", {})
        observability_metrics = search_result.get("observability_metrics", {})
        reranker_triggered = metrics_details.get("rerank", {}).get("triggered", False) or observability_metrics.get("rerank_triggered", False)
        
        # Build base metrics
        base_metrics = get_default_metrics()
        
        # Add fusion and rerank info if available
        if metrics_details.get("fusion"):
            base_metrics["fusion"] = metrics_details["fusion"]
        if metrics_details.get("rerank"):
            base_metrics["rerank"] = metrics_details["rerank"]
        
        # Add per-request observability metrics
        base_metrics["fusion_overlap"] = observability_metrics.get("fusion_overlap", 0)
        base_metrics["rrf_candidates"] = observability_metrics.get("rrf_candidates", 0)
        base_metrics["rerank_triggered"] = observability_metrics.get("rerank_triggered", False)
        base_metrics["rerank_timeout"] = observability_metrics.get("rerank_timeout", False)
        
        # Generate answer using LLM (non-streaming only)
        # 
        # Semantic rules:
        # - Default generate_answer=False: Even with OpenAI client, skip LLM, only retrieval
        # - generate_answer=True and stream=False: Do "retrieval + non-streaming generation"
        # - stream=True: Implicitly enables answer generation (treated as generate_answer=True)
        answer = ""
        llm_usage = None
        
        # Determine if we should generate answer
        # stream=True implies generate_answer=True
        should_generate = (request.generate_answer or request.stream)
        
        if should_generate and not request.stream:
            from services.fiqa_api.clients import get_openai_client
            from services.fiqa_api.utils.llm_client import generate_answer_for_query
            
            openai_client = get_openai_client()
            if openai_client is not None and sources:
                try:
                    # Build context from sources
                    context = []
                    for source in sources[:10]:  # Limit to top 10 sources
                        context_item = {
                            "title": source.get("title", source.get("doc_id", "")),
                            "text": source.get("text", source.get("content", "")),
                        }
                        # ✅ Include Airbnb fields if present
                        if actual_collection == "airbnb_la_demo" or collection_name == "airbnb_la_demo":
                            if "price" in source:
                                context_item["price"] = source.get("price")
                            if "bedrooms" in source:
                                context_item["bedrooms"] = source.get("bedrooms")
                            if "neighbourhood" in source:
                                context_item["neighbourhood"] = source.get("neighbourhood")
                            if "room_type" in source:
                                context_item["room_type"] = source.get("room_type")
                        context.append(context_item)
                    
                    # Generate answer
                    # Log context structure before LLM call
                    context_debug = []
                    for idx, ctx_item in enumerate(context[:3], 1):
                        item_debug = {"idx": idx}
                        if "price" in ctx_item:
                            item_debug["price"] = ctx_item.get("price")
                        if "bedrooms" in ctx_item:
                            item_debug["bedrooms"] = ctx_item.get("bedrooms")
                        if "neighbourhood" in ctx_item:
                            item_debug["neighbourhood"] = ctx_item.get("neighbourhood")
                        if "room_type" in ctx_item:
                            item_debug["room_type"] = ctx_item.get("room_type")
                        if "text" in ctx_item:
                            text_val = ctx_item.get("text", "")
                            item_debug["text_len"] = len(text_val) if text_val else 0
                        context_debug.append(item_debug)
                    
                    logger.info(
                        f"[AIRBNB_PROMPT_DEBUG] trace_id={trace_id} "
                        f"collection={actual_collection} "
                        f"context_items={len(context)} "
                        f"context_sample={context_debug}"
                    )
                    
                    answer, llm_usage, kv_enabled, kv_hit = generate_answer_for_query(
                        question=cleaned_question,
                        context=context,
                        use_kv_cache=request.use_kv_cache,
                        session_id=request.session_id,
                    )
                    
                    # Log answer summary
                    answer_preview = answer[:300] if answer else ""
                    logger.info(
                        f"[AIRBNB_PROMPT_DEBUG] trace_id={trace_id} "
                        f"answer_length={len(answer) if answer else 0} "
                        f"answer_preview={answer_preview}"
                    )
                    
                except Exception as e:
                    logger.warning(
                        f"level=WARN trace_id={trace_id} LLM generation failed: {e}",
                        exc_info=True,
                    )
                    # answer remains empty string, llm_usage remains None
                    kv_enabled = False
                    kv_hit = False
        
        # Add LLM usage to metrics if available
        if llm_usage:
            base_metrics["llm_usage"] = llm_usage
            base_metrics["llm_enabled"] = True
            base_metrics["kv_enabled"] = kv_enabled if 'kv_enabled' in locals() else bool(request.use_kv_cache)
            base_metrics["kv_hit"] = kv_hit if 'kv_hit' in locals() else False
        else:
            base_metrics["llm_enabled"] = False
            base_metrics["kv_enabled"] = False
            base_metrics["kv_hit"] = False
        
        # Broker demo: append Q4 (discounts) hint when question is about saving money
        if getattr(request, "mode", None) == "demo" and answer:
            q_low = (question_original or cleaned_question or "").lower()
            discount_keywords = ("省钱", "折扣", "优惠", "save", "discount", "保费", "便宜")
            if any(kw in q_low for kw in discount_keywords):
                broker_hint = (
                    "\n\n**常见折扣类别**（各公司政策不同，具体金额需向保险公司确认）："
                    "好司机、多车、好学生、防御性驾驶、低里程、多保单。"
                    "\n\n**客户可准备**：当前保单、驾照、车辆信息、多车情况、学生证明（如有）。"
                    "\n\n**经纪人可进一步询问**：客户当前保单、多车情况、好学生、安全设备、续保年限等，以便推荐具体折扣。"
                    "\n\n**经纪人下一步**：收集客户信息，推荐可申请折扣，提供 2–3 家报价对比。各公司折扣政策不同，建议多家比价。"
                )
                if broker_hint not in answer:
                    answer = answer.rstrip() + broker_hint

        # Broker demo: Q5 claims fallback + Q2 $14 hint
        if actual_collection in ("auto_insurance_demo_core", "demo_auto_insurance") or getattr(request, "mode", None) == "demo":
            answer = _apply_broker_demo_answer_fixes(
                answer, question_original, cleaned_question, sources, getattr(request, "mode", None)
            )

        # Return frontend-friendly response with all required fields
        # Ensure translation fields are never None - use explicit defaults
        # Variables are initialized at function level (lines 312-320), but add safety checks
        q_orig = question_original if question_original is not None else cleaned_question
        q_used_val = question_used if question_used is not None else q_orig
        # Ensure translation_applied is always a boolean
        trans_applied_val = bool(translation_applied) if translation_applied is not None else False
        # Ensure detected_lang is always a string (never None)
        det_lang_val = str(detected_lang) if detected_lang is not None and detected_lang != "" else "unknown"
        trans_error_val = translation_error if translation_error is not None else None
        
        payload = {
            "ok": True,
            "trace_id": trace_id,
            "question": q_orig,  # Original question
            "question_used": q_used_val,  # Question used for search (may be translated)
            "translation_applied": trans_applied_val,  # Ensure boolean, never None
            "detected_lang": det_lang_val,  # Ensure string, never None
            "translation_error": trans_error_val,  # Error message if translation failed, null if None
            "answer": answer,  # ✅ Filled with generated answer (or empty string if LLM unavailable)
            "latency_ms": elapsed,
            "route": route_used,
            "params": {
                "top_k": request.top_k,
                "rerank": request.rerank,
                "use_hybrid": request.use_hybrid,
                "rrf_k": request.rrf_k if request.use_hybrid else None,
            },
            "sources": sources,
            "items": sources,
            "metrics": base_metrics,
            "reranker_triggered": reranker_triggered,
            "degraded": bool(search_result.get("fallback", False)),
            "budget_ms": request.budget_ms,
            "ts": datetime.utcnow().isoformat() + "Z",
        }
        # Add translation error if present (for debugging, not fatal)
        if translation_error:
            payload["translation_error"] = translation_error
        try:
            trace_url = search_result.get("trace_url") or obs.build_obs_url(trace_id)
            raw_request.state.trace_url = trace_url
            obs.finalize_root(
                job_id=trace_id,
                trace_id=trace_id,
                trace_url=trace_url,
                metrics=base_metrics,
                decision=route_used,
            )
        except Exception:
            pass
        return payload
        
    except HTTPException as http_ex:
        # Re-raise HTTP exceptions (4xx/5xx) - FastAPI will handle status code
        elapsed = (time.perf_counter() - start) * 1000
        logger.warning(f"level=WARN trace_id={trace_id} status=HTTP_{http_ex.status_code} latency_ms={elapsed:.1f} error='{http_ex.detail}'")
        try:
            trace_url = obs.build_obs_url(trace_id)
            raw_request.state.trace_url = trace_url
            obs.finalize_root(
                job_id=trace_id,
                trace_id=trace_id,
                trace_url=trace_url,
                decision=f"HTTP_{http_ex.status_code}",
            )
        except Exception:
            pass
        raise
    except Exception as e:
        # Log error with structured fields
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(f"level=ERROR trace_id={trace_id} status=ERROR route='error' latency_ms={elapsed:.1f} error_type={type(e).__name__} error='{str(e)}'")
        
        error_text = str(e)
        not_found_markers = (
            "StatusCode.NOT_FOUND",
            "doesn't exist",
            "Collection",
            "NOT_FOUND",
        )
        if any(marker in error_text for marker in not_found_markers):
            message = f"Collection '{actual_collection}' not found in Qdrant. Run `make seed-fiqa` to seed demo vectors."
            # Include translation fields even in error responses
            # Variables are initialized at function level (lines 312-320), so they should always exist
            # Use explicit defaults to ensure fields are never None
            # Access variables directly with safe defaults
            question_orig = cleaned_question if "cleaned_question" in locals() and cleaned_question else (request.question if request else "")
            question_used_val = question_used if "question_used" in locals() and question_used else question_orig
            # Ensure translation_applied is always a boolean, never None
            if "translation_applied" in locals():
                translation_applied_val = bool(translation_applied) if translation_applied is not None else False
            else:
                translation_applied_val = False
            # Ensure detected_lang is always a string, never None
            if "detected_lang" in locals():
                detected_lang_val = str(detected_lang) if detected_lang is not None and detected_lang != "" else "unknown"
            else:
                detected_lang_val = "unknown"
            
            friendly_payload = {
                "ok": False,
                "ret_code": "DATASET_MISSING",
                "trace_id": trace_id,
                "question": question_orig,
                "question_used": question_used_val,
                "translation_applied": translation_applied_val,  # Always boolean, never None
                "detected_lang": detected_lang_val,  # Always string, never None
                "answer": "",
                "message": message,
                "latency_ms": elapsed,
                "route": "dataset_missing",
                "params": {
                    "top_k": request.top_k if request else 0,
                    "rerank": request.rerank if request else False,
                    "use_hybrid": request.use_hybrid if request else False,
                },
                "sources": [],
                "items": [],
                "metrics": get_default_metrics(),
                "reranker_triggered": False,
                "ts": datetime.utcnow().isoformat() + "Z",
            }
            try:
                trace_url = obs.build_obs_url(trace_id)
                raw_request.state.trace_url = trace_url
                obs.finalize_root(
                    job_id=trace_id,
                    trace_id=trace_id,
                    trace_url=trace_url,
                    decision="dataset_missing",
                )
            except Exception:
                pass
            return JSONResponse(
                status_code=200,
                headers={"X-Trace-Id": trace_id},
                content=friendly_payload,
            )
        
        try:
            trace_url = obs.build_obs_url(trace_id)
            raw_request.state.trace_url = trace_url
            obs.finalize_root(
                job_id=trace_id,
                trace_id=trace_id,
                trace_url=trace_url,
                decision="exception",
            )
        except Exception:
            pass
        
        # Return error response with all required fields and proper status code
        # Include translation fields even in error responses
        question_orig = cleaned_question if 'cleaned_question' in locals() else ""
        question_used_val = question_used if "question_used" in locals() else question_orig
        translation_applied_val = bool(translation_applied) if "translation_applied" in locals() else False
        detected_lang_val = detected_lang if "detected_lang" in locals() else "unknown"
        
        return JSONResponse(
            status_code=500,
            headers={"X-Trace-Id": trace_id},  # Also set in headers
            content={
                "ok": False,
                "trace_id": trace_id,
                "question": question_orig,
                "question_used": question_used_val,
                "translation_applied": translation_applied_val,
                "detected_lang": detected_lang_val,
                "answer": "",
                "error": str(e),
                "latency_ms": elapsed,
                "route": "error",
                "params": {
                    "top_k": request.top_k if request else 0,
                    "rerank": request.rerank if request else False
                },
                "sources": [],
                "items": [],
                "metrics": get_default_metrics(),  # Structured metrics even in error
                "reranker_triggered": False,
                "degraded": False,
                "budget_ms": request.budget_ms if request else None,
                "ts": datetime.utcnow().isoformat() + "Z"
            }
        )


async def _execute_query_streaming(
    request: QueryRequest,
    response: Response,
    raw_request: Request,
    x_trace_id: Optional[str] = None,
):
    """
    Streaming version of query endpoint (SSE format).
    
    First performs retrieval, then streams LLM-generated answer.
    """
    trace_id = (x_trace_id or "").strip() or str(uuid.uuid4())
    cleaned_question = request.question.strip() if request.question else ""
    
    async def event_generator():
        try:
            from services.fiqa_api.clients import get_openai_client
            from services.fiqa_api.utils.llm_client import build_rag_prompt, is_llm_generation_enabled
            from services.fiqa_api.utils.env_loader import get_llm_conf
            
            # Check global LLM generation switch first (prevents accidental LLM calls)
            if not is_llm_generation_enabled():
                yield "data: LLM generation disabled by server config (LLM_GENERATION_ENABLED env).\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # Check OpenAI client availability
            openai_client = get_openai_client()
            if openai_client is None:
                yield "data: LLM client not initialized. Please set OPENAI_API_KEY.\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # Perform retrieval first
            try:
                from services.fiqa_api.services.search_core import perform_search
                from services.fiqa_api.app_main import app
                
                routing_flags = getattr(app.state, "routing_flags", {"enabled": True, "mode": "rules"})
                faiss_engine = getattr(app.state, "faiss_engine", None)
                faiss_ready = getattr(app.state, "faiss_ready", False)
                faiss_enabled = getattr(app.state, "faiss_enabled", False)
                
                # Apply search profile (if specified)
                profile = get_search_profile(request.profile_name)
                effective_params = build_effective_params(request, profile)
                collection_name = effective_params["collection"]
                if not collection_name:
                    default_collection = os.getenv("DEFAULT_SEARCH_COLLECTION", "fiqa")
                    collection_name = default_collection
                rrf_k = max(1, min(request.rrf_k if request.rrf_k is not None else RRF_K_DEFAULT, 100))
                rerank_top_k = max(1, min(request.rerank_top_k if request.rerank_top_k is not None else RERANK_TOPK_DEFAULT, request.top_k))
                
                obs_ctx = {"trace_id": trace_id, "job_id": trace_id}
                
                search_result = await asyncio.to_thread(
                    perform_search,
                    query=cleaned_question,
                    top_k=request.top_k,
                    collection=collection_name,
                    routing_flags=routing_flags,
                    faiss_engine=faiss_engine,
                    faiss_ready=faiss_ready,
                    faiss_enabled=faiss_enabled,
                    lab_headers=None,
                    use_hybrid=request.use_hybrid,
                    rrf_k=rrf_k,
                    rerank=request.rerank,
                    rerank_top_k=rerank_top_k,
                    rerank_if_margin_below=request.rerank_if_margin_below,
                    max_rerank_trigger_rate=request.max_rerank_trigger_rate,
                    rerank_budget_ms=request.rerank_budget_ms,
                    obs_ctx=obs_ctx,
                    # Pass effective filter parameters
                    price_max=effective_params.get("price_max"),
                    min_bedrooms=effective_params.get("min_bedrooms"),
                    neighbourhood=effective_params.get("neighbourhood"),
                    room_type=effective_params.get("room_type"),
                    profile_name=request.profile_name,
                )
                
                # Extract sources
                sources = []
                for result in search_result.get("results", []):
                    sources.append({
                        "doc_id": result.get("id", "unknown"),
                        "title": result.get("title", ""),
                        "text": result.get("text", ""),
                        "score": result.get("score", 0.0),
                    })
                
                # Build context for prompt
                context = []
                for source in sources[:10]:
                    context_item = {
                        "title": source.get("title", source.get("doc_id", "")),
                        "text": source.get("text", source.get("content", "")),
                    }
                    context.append(context_item)
                
                # Build RAG prompt
                prompt = build_rag_prompt(cleaned_question, context)
                
                # Get LLM config
                llm_conf = get_llm_conf()
                model = llm_conf.get("model", "gpt-4o-mini")
                max_tokens = llm_conf.get("max_tokens", 512)
                
                # Build messages
                messages = [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on provided context.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ]
                
                # Log use_kv_cache (not implemented)
                if request.use_kv_cache:
                    logger.debug(f"use_kv_cache=True requested (not yet implemented) for streaming")
                
                # Stream from OpenAI
                stream = openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=max_tokens,
                    stream=True,
                )
                
                async def iterate_stream():
                    for chunk in stream:
                        delta = None
                        try:
                            delta = chunk.choices[0].delta.content
                        except Exception:
                            delta = None
                        if delta:
                            yield f"data: {delta}\n\n"
                        await asyncio.sleep(0)
                
                async for sse_chunk in iterate_stream():
                    yield sse_chunk
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"level=ERROR trace_id={trace_id} Streaming query failed: {e}", exc_info=True)
                yield f"data: Error during retrieval or generation: {str(e)}\n\n"
                yield "data: [DONE]\n\n"
                
        except Exception as outer_e:
            logger.error(f"level=ERROR trace_id={trace_id} Unexpected error in streaming: {outer_e}", exc_info=True)
            yield f"data: Unexpected error: {str(outer_e)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Trace-Id": trace_id,
        }
    )


@router.post("/query")
async def query(
    request: QueryRequest,
    response: Response,
    raw_request: Request,
    x_trace_id: Optional[str] = Header(None),
):
    return await _execute_query(request, response, raw_request, x_trace_id)


@router.get("/query")
async def query_get(
    raw_request: Request,
    response: Response,
    q: Optional[str] = FastAPIQuery(None),
    budget_ms: Optional[int] = FastAPIQuery(None),
    x_trace_id: Optional[str] = Header(None),
):
    payload = QueryRequest(q=q, budget_ms=budget_ms)
    return await _execute_query(payload, response, raw_request, x_trace_id)


@router.get("/debug/translation")
async def debug_translation():
    """
    Debug endpoint to check translation system state.
    Does not expose secrets.
    """
    from services.fiqa_api.utils.translation import detect_lang, translation_debug_state
    
    state = translation_debug_state()
    
    # Test detect_lang on sample strings
    test_chinese = "你好"
    test_english = "hello"
    
    result = {
        **state,
        "detect_lang_tests": {
            "chinese": {
                "input": test_chinese,
                "detected": detect_lang(test_chinese)
            },
            "english": {
                "input": test_english,
                "detected": detect_lang(test_english)
            }
        }
    }
    
    return result
