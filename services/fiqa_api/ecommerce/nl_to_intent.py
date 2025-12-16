"""
nl_to_intent.py - Natural Language to Intent and Slots Parser

This module provides LLM-based parsing of user messages to extract structured
intent and slot information for the ecommerce after-sales agent.

The parser extracts:
- intent: refund, return, exchange, or other
- order_id: Order identifier if mentioned
- reason_type: Refund reason category (DAMAGED_OR_DEFECTIVE, NO_LONGER_WANTED, OTHER)
- reason_description: Detailed description of the reason
"""

import json
import logging
import os
from time import perf_counter
from typing import Optional, Literal

from pydantic import BaseModel, ValidationError

from services.fiqa_api.clients import get_openai_client
from services.fiqa_api.observability.metrics import LLMCallMetric, extract_llm_usage

logger = logging.getLogger(__name__)

# Default LLM model configuration
DEFAULT_LLM_MODEL = os.getenv("ECOMMERCE_LLM_MODEL", "gpt-4o-mini")
DEFAULT_LLM_TIMEOUT = float(os.getenv("ECOMMERCE_LLM_TIMEOUT", "8.0"))


class EcommerceNLParseResult(BaseModel):
    """
    Structured result from NL parsing.
    
    This model represents the extracted intent and slots from user messages.
    """
    intent: Literal["refund", "return", "exchange", "other"]
    order_id: Optional[str] = None
    reason_type: Optional[Literal["DAMAGED_OR_DEFECTIVE", "NO_LONGER_WANTED", "OTHER"]] = None
    reason_description: Optional[str] = None


class EcommerceNLParseError(Exception):
    """Custom exception raised when NL parsing fails."""
    pass


def parse_user_message(
    user_message: str,
    default_order_id: Optional[str] = None,
    metrics_list: Optional[list] = None
) -> EcommerceNLParseResult:
    """
    Parse user message to extract intent and slots using LLM.
    
    Args:
        user_message: User's natural language message
        default_order_id: Optional order ID from request (used as hint)
    
    Returns:
        EcommerceNLParseResult with extracted intent and slots
    
    Raises:
        EcommerceNLParseError: If LLM call fails or response cannot be parsed
    """
    client = get_openai_client()
    if not client:
        raise EcommerceNLParseError(
            "OpenAI client not available. Check OPENAI_API_KEY environment variable."
        )
    
    # Construct prompt
    system_prompt = (
        "You are an assistant that extracts structured intent and fields from "
        "ecommerce after-sales messages. Return a JSON object with the following fields:\n"
        "- intent: one of 'refund', 'return', 'exchange', or 'other'\n"
        "- order_id: order identifier if mentioned (normalize to uppercase, strip whitespace)\n"
        "- reason_type: one of 'DAMAGED_OR_DEFECTIVE', 'NO_LONGER_WANTED', or 'OTHER' if applicable, null otherwise\n"
        "- reason_description: brief description of the reason if provided, null otherwise\n\n"
        "Rules:\n"
        "- If intent cannot be determined, use 'other'\n"
        "- Extract order_id from the message if mentioned (e.g., 'order A10001', 'A10001')\n"
        "- Set reason_type to null if not clearly mentioned\n"
        "- Return valid JSON only, no additional text"
    )
    
    user_prompt = f"User message: {user_message}"
    if default_order_id:
        user_prompt += f"\n\nHint: Default order ID from request: {default_order_id}"
    
    start = perf_counter()
    try:
        # Call LLM with JSON mode
        response = client.chat.completions.create(
            model=DEFAULT_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=200,
            timeout=DEFAULT_LLM_TIMEOUT
        )
        
        end = perf_counter()
        latency_ms = (end - start) * 1000.0
        usage_info = extract_llm_usage(response)
        
        # Log metric
        metric = LLMCallMetric(
            component="nl_to_intent",
            model=DEFAULT_LLM_MODEL,
            prompt_tokens=usage_info["prompt_tokens"],
            completion_tokens=usage_info["completion_tokens"],
            total_tokens=usage_info["total_tokens"],
            latency_ms=latency_ms,
            success=True,
            error_message=None,
        )
        logger.info(f"LLM_CALL_METRIC: {metric.model_dump_json()}")
        # Collect metric if metrics_list provided
        if metrics_list is not None:
            metrics_list.append(metric.model_dump())
        
        if not response.choices or len(response.choices) == 0:
            raise EcommerceNLParseError("Empty response from LLM")
        
        content = response.choices[0].message.content
        if not content:
            raise EcommerceNLParseError("Empty content in LLM response")
        
        # Parse JSON response
        try:
            llm_data = json.loads(content)
        except json.JSONDecodeError as e:
            # Try to extract JSON from text if wrapped
            logger.warning(f"Failed to parse JSON directly, attempting extraction: {e}")
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                llm_data = json.loads(content[start:end + 1])
            else:
                raise EcommerceNLParseError(f"Invalid JSON in LLM response: {e}")
        
        # Normalize order_id if present
        if "order_id" in llm_data and llm_data["order_id"]:
            llm_data["order_id"] = str(llm_data["order_id"]).strip().upper()
        
        # Use default_order_id if parsed order_id is empty
        if not llm_data.get("order_id") and default_order_id:
            llm_data["order_id"] = str(default_order_id).strip().upper()
        
        # Validate and create result
        try:
            result = EcommerceNLParseResult(**llm_data)
            return result
        except ValidationError as e:
            raise EcommerceNLParseError(f"Validation failed for parsed result: {e}")
            
    except EcommerceNLParseError:
        raise
    except Exception as e:
        end = perf_counter()
        latency_ms = (end - start) * 1000.0
        
        # Log failed metric
        metric = LLMCallMetric(
            component="nl_to_intent",
            model=DEFAULT_LLM_MODEL,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency_ms=latency_ms,
            success=False,
            error_message=str(e),
        )
        logger.info(f"LLM_CALL_METRIC: {metric.model_dump_json()}")
        # Collect metric if metrics_list provided
        if metrics_list is not None:
            metrics_list.append(metric.model_dump())
        logger.error(f"LLM call failed during NL parsing: {e}", exc_info=True)
        raise EcommerceNLParseError(f"LLM call failed: {e}")
