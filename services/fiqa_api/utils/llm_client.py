from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from services.fiqa_api import obs

logger = logging.getLogger(__name__)


def is_llm_generation_enabled() -> bool:
    """
    Check if LLM generation is enabled via environment variable.
    
    Reads LLM_GENERATION_ENABLED env var and returns True if it's set to
    any of: "1", "true", "yes", "on" (case-insensitive).
    
    Defaults to False for safety (prevents accidental LLM calls).
    
    Returns:
        True if LLM generation is enabled, False otherwise
    """
    value = os.getenv("LLM_GENERATION_ENABLED", "false").lower()
    return value in ("1", "true", "yes", "on")


class LLMDisabled(Exception):
    """Raised when LLM reflections are disabled or unavailable."""


def _render_prompt(summary: Dict[str, Any], suggestion: Dict[str, Any], baseline: Optional[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("Job metrics snapshot:")
    for key in ("p95_ms", "err_rate", "recall_at_10", "cost_tokens"):
        value = summary.get(key)
        lines.append(f"{key}: {value!r}")

    lines.append("")
    lines.append("Baseline metrics:")
    if baseline:
        for key in ("p95_ms", "err_rate", "recall_at_10"):
            lines.append(f"{key}: {baseline.get(key)!r}")
    else:
        lines.append("baseline: None")

    lines.append("")
    lines.append("Suggested changes:")
    changes = suggestion.get("changes", {}) if suggestion else {}
    if changes:
        for k, v in changes.items():
            lines.append(f"{k}: {v!r}")
    else:
        lines.append("changes: {}")

    lines.append("")
    lines.append(f"Expected effect: {suggestion.get('expected_effect')}")
    lines.append(f"Risk: {suggestion.get('risk')}")
    lines.append("")
    lines.append("Produce 2-6 operational bullets covering latency, quality, risk, and cost trends.")
    lines.append("Each bullet under 18 words; avoid redundant phrasing.")

    # limit prompt length for safety
    return "\n".join(lines[:24])


def _normalize_bullets(raw: str) -> List[str]:
    if not raw:
        return []
    raw_lines = [line.strip(" -•\t") for line in raw.splitlines()]
    bullets = [line for line in raw_lines if line]

    if len(bullets) < 2:
        combined = " ".join(bullets).split(". ")
        bullets = [part.strip().rstrip(".") for part in combined if part.strip()]

    bullets = [line[:200] for line in bullets]
    return bullets[:6]


def _estimate_cost(
    tokens_in: Optional[int],
    tokens_out: Optional[int],
    input_per_mtok: Optional[float],
    output_per_mtok: Optional[float],
) -> Optional[float]:
    if tokens_in is None and tokens_out is None:
        return None
    if input_per_mtok is None and output_per_mtok is None:
        return None

    total = 0.0
    if tokens_in is not None and input_per_mtok is not None:
        total += (tokens_in / 1_000_000.0) * input_per_mtok
    if tokens_out is not None and output_per_mtok is not None:
        total += (tokens_out / 1_000_000.0) * output_per_mtok

    return total if total > 0 else None


def reflect_with_llm(
    conf: Dict[str, Any],
    summary: Dict[str, Any],
    suggestion: Dict[str, Any],
    baseline: Optional[Dict[str, Any]],
    max_tokens: int = 256,
    obs_ctx: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    api_key = conf.get("api_key")
    model = conf.get("model")
    if not api_key or not model:
        raise LLMDisabled("LLM disabled: missing API key or model")

    client = OpenAI(api_key=api_key)

    prompt = _render_prompt(summary, suggestion, baseline)
    if obs_ctx is None:
        ctx_candidate = conf.get("obs_ctx")
        if isinstance(ctx_candidate, dict):
            obs_ctx = ctx_candidate

    response = obs.llm_call(
        obs_ctx,
        model=model,
        provider="openai",
        call_fn=client.chat.completions.create,
        messages=[
            {
                "role": "system",
                "content": "You are an SRE lead summarizing experiment telemetry for executives.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=max_tokens,
    )

    content = None
    if response.choices:
        content = response.choices[0].message.content

    tokens_in = getattr(getattr(response, "usage", None), "prompt_tokens", None)
    tokens_out = getattr(getattr(response, "usage", None), "completion_tokens", None)

    cost = _estimate_cost(tokens_in, tokens_out, conf.get("input_per_mtok"), conf.get("output_per_mtok"))

    points = _normalize_bullets(content or "")

    return {
        "points": points,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd_est": cost,
    }


def build_rag_prompt(question: str, context: List[Dict[str, Any]], max_context_items: int = 10) -> str:
    """
    Build RAG prompt from question and retrieved context.
    
    Args:
        question: User's question
        context: List of context items, each with at least "title" and "text" keys.
                 May also include structured fields like price, bedrooms, neighbourhood, room_type (for Airbnb).
        max_context_items: Maximum number of context items to include
    
    Returns:
        Formatted prompt string
    """
    context_lines = [
        "You are a helpful assistant that answers questions based on the provided context.",
        "The context may include structured fields such as Price, Bedrooms, Neighbourhood, and Room Type.",
        "When the question is about cost or property filters, you MUST use these structured fields first before relying on free-form text.",
        "Use ALL available information from the context to answer the question.",
        "If the context doesn't contain enough information, say so clearly. Do not make up information.\n",
        f"Question: {question}\n",
        "Context:",
    ]
    
    # Limit context items to prevent prompt overflow
    limited_context = context[:max_context_items]
    
    for i, item in enumerate(limited_context, 1):
        title = item.get("title", f"Document {i}")
        text = item.get("text", item.get("content", ""))
        # Truncate text if too long (800-1000 chars per item for better context)
        if len(text) > 1000:
            text = text[:1000] + "..."
        
        # Build context description with structured fields
        context_parts = [f"\n[{i}] {title}"]
        
        # Add structured fields for Airbnb listings (or other structured data)
        structured_info = []
        if "neighbourhood" in item and item.get("neighbourhood"):
            structured_info.append(f"Neighbourhood: {item['neighbourhood']}")
        if "room_type" in item and item.get("room_type"):
            structured_info.append(f"Room Type: {item['room_type']}")
        if "price" in item and item.get("price") is not None:
            price_val = item.get("price")
            if isinstance(price_val, (int, float)) and price_val > 0:
                structured_info.append(f"Price: ${price_val:.0f}/night")
        if "bedrooms" in item and item.get("bedrooms") is not None:
            bedrooms_val = item.get("bedrooms")
            if isinstance(bedrooms_val, (int, float)) and bedrooms_val > 0:
                bedrooms_str = f"{int(bedrooms_val)} bedroom{'s' if bedrooms_val > 1 else ''}"
                structured_info.append(f"Bedrooms: {bedrooms_str}")
        
        # Combine structured info and text
        if structured_info:
            # Use line breaks so structured fields are more salient to the LLM
            context_parts.append("\n".join(structured_info))
        if text:
            context_parts.append(text)
        
        context_lines.append("\n".join(context_parts))
    
    context_lines.append("\nAnswer based on the context above:")
    
    return "\n".join(context_lines)


def generate_answer_for_query(
    *,
    question: str,
    context: List[Dict[str, Any]],
    model: Optional[str] = None,
    use_kv_cache: bool = False,
    session_id: Optional[str] = None,
    temperature: Optional[float] = 0.2,
    max_tokens: Optional[int] = None,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[Dict[str, Any]], bool, bool]:
    """
    Generate answer for a query using retrieved context (non-streaming).
    
    This function uses the singleton OpenAI client from clients.py.
    If the client is unavailable or the call fails, it gracefully returns
    an empty answer and None usage without raising exceptions.
    
    Args:
        question: User's question
        context: List of context items from retrieval results. Each item should have
                 at least "title" and "text" (or "content") keys.
        model: LLM model name (default: from get_llm_conf() or "gpt-4o-mini")
        use_kv_cache: Whether to use KV-cache (logical session-based cache)
        session_id: Session identifier for KV-cache (required if use_kv_cache=True)
        temperature: Temperature for generation (default: 0.2)
        max_tokens: Maximum tokens for completion (default: from config or 512)
        extra_params: Additional parameters to pass to OpenAI API
    
    Returns:
        Tuple of (answer_text, usage_dict_or_none, kv_enabled, kv_hit)
        
        usage_dict format (if successful):
        {
            "prompt_tokens": int,
            "completion_tokens": int,
            "total_tokens": int,
            "cost_usd_est": float | None,
            "model": str,
            "use_kv_cache": bool,
        }
        
        kv_enabled: True if KV-cache was enabled (use_kv_cache=True and session_id provided)
        kv_hit: True if session had previous turns (num_turns > 0 before this call)
    """
    from services.fiqa_api.clients import get_openai_client
    from services.fiqa_api.utils.env_loader import get_llm_conf
    from services.fiqa_api.kv_session import get_kv_session_store
    
    # Initialize KV-cache state
    kv_enabled = False
    kv_hit = False
    session = None
    
    # Check if KV-cache should be used
    if use_kv_cache and session_id:
        kv_enabled = True
        session_store = get_kv_session_store()
        session = session_store.get_or_create(session_id)
        # kv_hit is True if session already has conversation history
        kv_hit = session.num_turns > 0
    
    # Check global LLM generation switch (prevents accidental LLM calls)
    if not is_llm_generation_enabled():
        logger.info("LLM generation disabled by LLM_GENERATION_ENABLED env, skipping LLM call.")
        return "", None, kv_enabled, kv_hit
    
    # Get OpenAI client (singleton)
    openai_client = get_openai_client()
    if openai_client is None:
        logger.debug("OpenAI client not available, skipping answer generation")
        return "", None, kv_enabled, kv_hit
    
    # Get LLM configuration
    try:
        llm_conf = get_llm_conf()
        default_model = model or llm_conf.get("model", "gpt-4o-mini")
        default_max_tokens = max_tokens or llm_conf.get("max_tokens", 512)
        input_per_mtok = llm_conf.get("input_per_mtok")
        output_per_mtok = llm_conf.get("output_per_mtok")
    except Exception as e:
        logger.warning(f"Failed to load LLM config, using defaults: {e}")
        default_model = model or "gpt-4o-mini"
        default_max_tokens = max_tokens or 512
        input_per_mtok = None
        output_per_mtok = None
    
    try:
        # Build RAG prompt
        prompt = build_rag_prompt(question, context)
        
        # Build messages with session history if KV-cache is enabled
        messages = []
        
        # Add conversation history from session if available
        if kv_enabled and session and session.messages:
            # Include previous conversation turns
            messages.extend(session.messages)
        
        # Add system message and current user prompt
        messages.append({
            "role": "system",
            "content": "You are a helpful assistant that answers questions based on provided context.",
        })
        messages.append({
            "role": "user",
            "content": prompt,
        })
        
        # ✅ Debug logging for Airbnb prompt inspection
        # Note: trace_id should be logged at query.py level for better context
        
        # Log context structure for debugging
        context_fields_summary = []
        for idx, ctx_item in enumerate(context[:5], 1):  # Log first 5 items
            fields_present = []
            if ctx_item.get("title"):
                fields_present.append("title")
            if ctx_item.get("text"):
                text_len = len(str(ctx_item.get("text", "")))
                fields_present.append(f"text({text_len} chars)")
            if "price" in ctx_item and ctx_item.get("price") is not None:
                fields_present.append(f"price(${ctx_item['price']:.0f}/night)")
            if "bedrooms" in ctx_item and ctx_item.get("bedrooms") is not None:
                fields_present.append(f"bedrooms({ctx_item['bedrooms']})")
            if "neighbourhood" in ctx_item and ctx_item.get("neighbourhood"):
                fields_present.append(f"neighbourhood({ctx_item['neighbourhood']})")
            if "room_type" in ctx_item and ctx_item.get("room_type"):
                fields_present.append(f"room_type({ctx_item['room_type']})")
            context_fields_summary.append(f"Doc{idx}:[{', '.join(fields_present)}]")
        
        # Log prompt preview (first 800 chars, no API keys)
        prompt_preview = prompt[:800] + ("..." if len(prompt) > 800 else "")
        # Sanitize any potential API keys (though there shouldn't be any in prompt)
        prompt_preview = prompt_preview.replace("sk-", "sk-REDACTED-")
        
        logger.info(
            f"[AIRBNB_PROMPT_DEBUG] "
            f"context_items={len(context)} "
            f"context_fields={'; '.join(context_fields_summary)} "
            f"prompt_length={len(prompt)} "
            f"prompt_preview={prompt_preview}"
        )
        
        # Prepare API parameters
        api_params = {
            "model": default_model,
            "messages": messages,
            "temperature": temperature or 0.2,
            "max_tokens": default_max_tokens,
        }
        
        # Log KV-cache usage
        if kv_enabled:
            logger.debug(f"KV-cache enabled: session_id={session_id}, kv_hit={kv_hit}, num_turns={session.num_turns if session else 0}")
        
        # Add extra params if provided
        if extra_params:
            api_params.update(extra_params)
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(**api_params)
        
        # Extract content
        answer = ""
        if response.choices and len(response.choices) > 0:
            answer = response.choices[0].message.content or ""
        
        # Extract token usage
        usage_obj = getattr(response, "usage", None)
        tokens_in = getattr(usage_obj, "prompt_tokens", None) if usage_obj else None
        tokens_out = getattr(usage_obj, "completion_tokens", None) if usage_obj else None
        tokens_total = getattr(usage_obj, "total_tokens", None) if usage_obj else None
        
        # Estimate cost
        cost_usd_est = _estimate_cost(tokens_in, tokens_out, input_per_mtok, output_per_mtok)
        
        # Update session with new conversation turn if KV-cache is enabled
        if kv_enabled and session and session_id:
            user_message = {"role": "user", "content": prompt}
            assistant_message = {"role": "assistant", "content": answer}
            tokens_delta = tokens_total or 0
            session_store = get_kv_session_store()
            session_store.update(session_id, user_message, assistant_message, tokens_delta)
        
        # Build usage dict
        usage_dict = {
            "prompt_tokens": tokens_in,
            "completion_tokens": tokens_out,
            "total_tokens": tokens_total,
            "cost_usd_est": cost_usd_est,
            "model": default_model,
            "use_kv_cache": use_kv_cache,
        }
        
        # Log generation result with usage info
        # Fix: Handle None cost_usd_est properly
        cost_val = cost_usd_est if cost_usd_est is not None else 0.0
        logger.info(
            f"LLM answer generated: tokens={tokens_total}, "
            f"prompt_tokens={tokens_in}, completion_tokens={tokens_out}, "
            f"cost=${cost_val:.6f}, model={default_model}, "
            f"kv_enabled={kv_enabled}, kv_hit={kv_hit}"
        )
        return answer, usage_dict, kv_enabled, kv_hit
        
    except Exception as e:
        logger.warning(f"LLM generation failed: {e}", exc_info=True)
        return "", None, kv_enabled, kv_hit


async def stream_answer_for_query(
    *,
    question: str,
    context: List[Dict[str, Any]],
    model: Optional[str] = None,
    use_kv_cache: bool = False,
    session_id: Optional[str] = None,
    temperature: Optional[float] = 0.2,
    max_tokens: Optional[int] = None,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[Dict[str, Any]], bool, bool, Optional[float]]:
    """
    Stream answer for a query using retrieved context.
    
    This function uses the singleton OpenAI client from clients.py.
    It streams the response and records the first token latency.
    
    Args:
        question: User's question
        context: List of context items from retrieval results. Each item should have
                 at least "title" and "text" (or "content") keys.
        model: LLM model name (default: from get_llm_conf() or "gpt-4o-mini")
        use_kv_cache: Whether to use KV-cache (logical session-based cache)
        session_id: Session identifier for KV-cache (required if use_kv_cache=True)
        temperature: Temperature for generation (default: 0.2)
        max_tokens: Maximum tokens for completion (default: from config or 512)
        extra_params: Additional parameters to pass to OpenAI API
    
    Returns:
        Tuple of (answer_text, usage_dict_or_none, kv_enabled, kv_hit, first_token_latency_ms)
        
        usage_dict format (if successful):
        {
            "prompt_tokens": int,
            "completion_tokens": int,
            "total_tokens": int,
            "cost_usd_est": float | None,
            "model": str,
            "use_kv_cache": bool,
        }
        
        kv_enabled: True if KV-cache was enabled (use_kv_cache=True and session_id provided)
        kv_hit: True if session had previous turns (num_turns > 0 before this call)
        first_token_latency_ms: Time in milliseconds until first token arrived (None if no tokens)
    """
    import time
    import asyncio
    from services.fiqa_api.clients import get_openai_client
    from services.fiqa_api.utils.env_loader import get_llm_conf
    from services.fiqa_api.kv_session import get_kv_session_store
    
    # Initialize KV-cache state
    kv_enabled = False
    kv_hit = False
    session = None
    
    # Check if KV-cache should be used
    if use_kv_cache and session_id:
        kv_enabled = True
        session_store = get_kv_session_store()
        session = session_store.get_or_create(session_id)
        # kv_hit is True if session already has conversation history
        kv_hit = session.num_turns > 0
    
    # Check global LLM generation switch (prevents accidental LLM calls)
    if not is_llm_generation_enabled():
        logger.info("LLM generation disabled by LLM_GENERATION_ENABLED env, skipping LLM call.")
        return "", None, kv_enabled, kv_hit, None
    
    # Get OpenAI client (singleton)
    openai_client = get_openai_client()
    if openai_client is None:
        logger.debug("OpenAI client not available, skipping answer generation")
        return "", None, kv_enabled, kv_hit, None
    
    # Get LLM configuration
    try:
        llm_conf = get_llm_conf()
        default_model = model or llm_conf.get("model", "gpt-4o-mini")
        default_max_tokens = max_tokens or llm_conf.get("max_tokens", 512)
        input_per_mtok = llm_conf.get("input_per_mtok")
        output_per_mtok = llm_conf.get("output_per_mtok")
    except Exception as e:
        logger.warning(f"Failed to load LLM config, using defaults: {e}")
        default_model = model or "gpt-4o-mini"
        default_max_tokens = max_tokens or 512
        input_per_mtok = None
        output_per_mtok = None
    
    try:
        # Build RAG prompt
        prompt = build_rag_prompt(question, context)
        
        # Build messages with session history if KV-cache is enabled
        messages = []
        
        # Add conversation history from session if available
        if kv_enabled and session and session.messages:
            # Include previous conversation turns
            messages.extend(session.messages)
        
        # Add system message and current user prompt
        messages.append({
            "role": "system",
            "content": "You are a helpful assistant that answers questions based on provided context.",
        })
        messages.append({
            "role": "user",
            "content": prompt,
        })
        
        # Prepare API parameters
        api_params = {
            "model": default_model,
            "messages": messages,
            "temperature": temperature or 0.2,
            "max_tokens": default_max_tokens,
            "stream": True,  # Enable streaming
        }
        
        # Log KV-cache usage
        if kv_enabled:
            logger.debug(f"KV-cache enabled (streaming): session_id={session_id}, kv_hit={kv_hit}, num_turns={session.num_turns if session else 0}")
        
        # Add extra params if provided
        if extra_params:
            api_params.update(extra_params)
        
        # Record start time
        stream_start_time = time.perf_counter()
        first_token_time: Optional[float] = None
        
        # Call OpenAI API with streaming
        stream = openai_client.chat.completions.create(**api_params)
        
        # Collect streamed content
        answer_parts = []
        tokens_in = None
        tokens_out = None
        tokens_total = None
        
        # Iterate through stream (OpenAI streaming is synchronous, but we run it in thread)
        def iterate_stream():
            nonlocal first_token_time, tokens_in, tokens_out, tokens_total
            for chunk in stream:
                # Check for first token
                if first_token_time is None:
                    try:
                        delta = chunk.choices[0].delta.content if chunk.choices else None
                        if delta:
                            first_token_time = time.perf_counter()
                    except Exception:
                        pass
                
                # Collect content
                try:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        answer_parts.append(delta)
                except Exception:
                    pass
                
                # Extract usage info (OpenAI streaming API provides usage in the final chunk)
                # Check both chunk.usage and chunk.choices[0].usage
                usage_obj = getattr(chunk, "usage", None)
                if not usage_obj and chunk.choices:
                    try:
                        usage_obj = getattr(chunk.choices[0], "usage", None)
                    except Exception:
                        pass
                
                if usage_obj:
                    tokens_in = getattr(usage_obj, "prompt_tokens", None)
                    tokens_out = getattr(usage_obj, "completion_tokens", None)
                    tokens_total = getattr(usage_obj, "total_tokens", None)
        
        # Run stream iteration in thread to avoid blocking
        await asyncio.to_thread(iterate_stream)
        
        # Combine answer parts
        answer = "".join(answer_parts)
        
        # Calculate first token latency
        first_token_latency_ms = None
        if first_token_time is not None:
            first_token_latency_ms = (first_token_time - stream_start_time) * 1000.0
        
        # Estimate cost (note: streaming doesn't always provide usage in final chunk)
        # We may need to estimate from tokens if not provided
        if tokens_in is None or tokens_out is None:
            # Fallback: estimate from answer length (rough approximation)
            # This is not ideal but streaming API doesn't always provide usage
            logger.debug("Streaming response didn't provide token usage, estimating from answer length")
            # Rough estimate: ~4 chars per token
            estimated_tokens_out = len(answer) // 4 if answer else 0
            tokens_out = estimated_tokens_out
            # Prompt tokens are harder to estimate, use a default
            tokens_in = len(prompt) // 4 if prompt else 0
            tokens_total = tokens_in + tokens_out
        
        cost_usd_est = _estimate_cost(tokens_in, tokens_out, input_per_mtok, output_per_mtok)
        
        # Update session with new conversation turn if KV-cache is enabled
        if kv_enabled and session and session_id:
            user_message = {"role": "user", "content": prompt}
            assistant_message = {"role": "assistant", "content": answer}
            tokens_delta = tokens_total or 0
            session_store = get_kv_session_store()
            session_store.update(session_id, user_message, assistant_message, tokens_delta)
        
        # Build usage dict
        usage_dict = {
            "prompt_tokens": tokens_in,
            "completion_tokens": tokens_out,
            "total_tokens": tokens_total,
            "cost_usd_est": cost_usd_est,
            "model": default_model,
            "use_kv_cache": use_kv_cache,
        }
        
        # Log generation result
        cost_val = cost_usd_est if cost_usd_est is not None else 0.0
        first_token_str = f"{first_token_latency_ms:.1f}ms" if first_token_latency_ms is not None else "N/A"
        logger.info(
            f"LLM answer streamed: tokens={tokens_total}, "
            f"prompt_tokens={tokens_in}, completion_tokens={tokens_out}, "
            f"cost=${cost_val:.6f}, model={default_model}, "
            f"kv_enabled={kv_enabled}, kv_hit={kv_hit}, "
            f"first_token_latency={first_token_str}"
        )
        return answer, usage_dict, kv_enabled, kv_hit, first_token_latency_ms
        
    except Exception as e:
        logger.warning(f"LLM streaming generation failed: {e}", exc_info=True)
        return "", None, kv_enabled, kv_hit, None

