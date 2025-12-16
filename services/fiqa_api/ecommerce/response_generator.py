"""
response_generator.py - LLM-based Customer Response Generator

Minimal LLM layer for generating natural customer support replies.
This module only handles phrasing - business logic (refund eligibility, amounts)
remains in the tools layer.
"""

import os
import logging
from time import perf_counter
from typing import Optional

from pydantic import BaseModel, Field

from services.fiqa_api.clients import get_openai_client
from services.fiqa_api.observability.metrics import LLMCallMetric, extract_llm_usage

logger = logging.getLogger(__name__)

# Default LLM model configuration
DEFAULT_LLM_MODEL = os.getenv("ECOMMERCE_LLM_MODEL", "gpt-4o-mini")
DEFAULT_LLM_TIMEOUT = float(os.getenv("ECOMMERCE_LLM_TIMEOUT", "8.0"))


class EcommerceResponseFacts(BaseModel):
    """
    Structured facts that the LLM uses to generate customer replies.
    
    All business decisions (refund amount, eligibility) are already made by tools.
    This model only contains the facts to be communicated to the customer.
    """
    
    order_id: str = Field(..., description="Order ID")
    order_status: Optional[str] = Field(None, description="Order status")
    refund_eligible: Optional[bool] = Field(None, description="Whether refund is eligible")
    refund_amount: Optional[float] = Field(None, description="Refund amount if eligible")
    currency: Optional[str] = Field(None, description="Currency code (e.g., USD)")
    refund_reason: Optional[str] = Field(None, description="Human-readable refund reason")
    policy_summary: Optional[str] = Field(None, description="Brief policy reference")
    additional_notes: Optional[str] = Field(None, description="Additional context if needed")


def _call_llm(prompt: str, model: str = DEFAULT_LLM_MODEL, timeout: float = DEFAULT_LLM_TIMEOUT, metrics_list: Optional[list] = None) -> str:
    """
    Internal helper to call LLM API.
    
    Args:
        prompt: Complete prompt string (system + user)
        model: Model name
        timeout: Request timeout in seconds
        metrics_list: Optional list to collect LLM call metrics
    
    Returns:
        Generated text response
    
    Raises:
        Exception: If LLM call fails
    """
    client = get_openai_client()
    if not client:
        raise ValueError("OpenAI client not available. Check OPENAI_API_KEY environment variable.")
    
    start = perf_counter()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful and polite customer support agent for an ecommerce platform. "
                               "Generate concise, professional, and empathetic customer replies in English."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=300,
            timeout=timeout
        )
        
        end = perf_counter()
        latency_ms = (end - start) * 1000.0
        usage_info = extract_llm_usage(response)
        
        # Log metric
        metric = LLMCallMetric(
            component="response_generator",
            model=model,
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
        
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            raise ValueError("Empty response from LLM")
            
    except Exception as e:
        end = perf_counter()
        latency_ms = (end - start) * 1000.0
        
        # Log failed metric
        metric = LLMCallMetric(
            component="response_generator",
            model=model,
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
        logger.warning(f"LLM call failed: {e}")
        raise


def _generate_fallback_response(facts: EcommerceResponseFacts) -> str:
    """
    Generate a rule-based fallback response when LLM is unavailable.
    
    This maintains the original template-based behavior as a safety net.
    """
    if facts.refund_eligible and facts.refund_amount is not None:
        currency = facts.currency or "$"
        return (
            f"Your refund request for order {facts.order_id} has been processed. "
            f"The estimated refund amount is {currency}{facts.refund_amount:.2f}. "
            f"{f'Reason: {facts.refund_reason}' if facts.refund_reason else ''}"
            f"{f' (Policy: {facts.policy_summary})' if facts.policy_summary else ''}"
        ).strip()
    
    elif facts.refund_eligible is False:
        return (
            f"We apologize, but order {facts.order_id} currently does not meet refund eligibility requirements. "
            f"Possible reasons include: exceeding the refund time window, order status not meeting refund policy, etc. "
            f"If you need further assistance, please contact our customer service team."
        )
    
    else:
        return (
            f"Unable to process your refund request for order {facts.order_id} at this time. "
            f"Please try again later or contact customer service for assistance."
        )


def generate_customer_reply(facts: EcommerceResponseFacts, metrics_list: Optional[list] = None) -> str:
    """
    Generate a natural customer support reply using LLM.
    
    This function takes structured facts (order, refund eligibility, amount, etc.)
    and generates a polite, professional customer reply in English.
    
    Business logic (refund eligibility, amounts) should already be determined
    by the tools layer. This function only handles phrasing.
    
    Args:
        facts: EcommerceResponseFacts instance containing order and refund information
    
    Returns:
        Natural language customer reply string
    
    Notes:
        - If LLM call fails, falls back to rule-based template response
        - Never modifies refund amounts or eligibility - only communicates existing facts
    """
    # Construct prompt with facts
    facts_dict = facts.model_dump(exclude_none=True)
    
    prompt = f"""Generate a polite and professional customer support reply based on the following refund request facts:

Order ID: {facts.order_id}
Order Status: {facts.order_status or 'Not specified'}
Refund Eligible: {facts.refund_eligible}
{f'Refund Amount: {facts.currency or "$"}{facts.refund_amount:.2f}' if facts.refund_amount is not None else ''}
{f'Refund Reason: {facts.refund_reason}' if facts.refund_reason else ''}
{f'Policy Reference: {facts.policy_summary}' if facts.policy_summary else ''}

Requirements:
- Do NOT modify or change the refund amount or eligibility status
- Explain clearly why the refund can or cannot be processed
- Keep the reply concise (2-3 sentences)
- Be professional, empathetic, and helpful
- Use English only

Generate the customer support reply:"""
    
    try:
        reply = _call_llm(prompt, metrics_list=metrics_list)
        
        # Validate that reply is not empty
        if not reply or not reply.strip():
            logger.warning("LLM returned empty response, using fallback")
            return _generate_fallback_response(facts)
        
        return reply
        
    except Exception as e:
        logger.warning(f"LLM call failed, using fallback response: {e}")
        return _generate_fallback_response(facts)

