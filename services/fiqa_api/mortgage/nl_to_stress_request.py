"""
nl_to_stress_request.py - Natural Language to StressCheckRequest Converter
==========================================================================

This module provides a natural language understanding (NLU) layer that:
1. Uses an LLM to extract mortgage-related fields from English queries
2. Converts extracted values into a partial StressCheckRequest
3. Identifies missing and low-confidence fields

The LLM is ONLY responsible for identifying which fields the user mentioned
and their raw values/units. All numeric conversions and defaulting rules
are done in Python.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Union, Dict

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("mortgage_agent")

# NLU-specific timeout (15-20 seconds for LLM calls)
NLU_TIMEOUT_SEC = 18.0
NLU_MAX_RETRIES = 2
NLU_RETRY_BACKOFF_SEC = 0.5

# Required fields for running a meaningful stress check
# Note: We use "list_price" to match StressCheckRequest, but the LLM extracts "home_price"
REQUIRED_FIELDS = ["income_monthly", "list_price"]


# ========================================
# NLU Models (LLM Output Schema)
# ========================================


class ExtractedField(BaseModel):
    """A single field extracted from user text by the LLM."""

    field: Literal[
        "income_monthly",
        "income_annual",
        "home_price",
        "list_price",  # Alias for home_price (both map to list_price in PartialStressRequest)
        "down_payment_amount",
        "down_payment_pct",
        "interest_rate_annual",
        "loan_term_years",
        "zip_code",
        "state",
    ] = Field(..., description="Field name from allowed whitelist")
    value: Union[float, int, str] = Field(..., description="Raw value as extracted")
    unit: Optional[str] = Field(
        None,
        description="Unit identifier, e.g. 'per_year', 'per_month', 'usd', 'percent', 'k_usd', 'million_usd'",
    )
    source_text: Optional[str] = Field(
        None, description="Original text snippet that mentioned this field"
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score (0-1), if provided by LLM"
    )


class NLUResult(BaseModel):
    """Complete NLU extraction result from the LLM."""

    extracted_fields: List[ExtractedField] = Field(
        default_factory=list, description="List of extracted fields"
    )
    intent_type: Literal["new_plan", "adjust_existing", "ask_explanation", "unknown"] = Field(
        default="unknown", description="User intent classification"
    )
    raw_user_text: str = Field(..., description="Original user input text")


# ========================================
# Bridge Models (Python-side Output)
# ========================================


@dataclass
class PartialStressRequest:
    """Partial StressCheckRequest with only fields that might be filled from NLU."""

    income_monthly: Optional[float] = None
    other_debt_monthly: Optional[float] = None
    list_price: Optional[float] = None  # Maps to StressCheckRequest.list_price
    down_payment_pct: Optional[float] = None
    interest_rate_annual: Optional[float] = None
    loan_term_years: Optional[int] = None
    zip_code: Optional[str] = None
    state: Optional[str] = None


@dataclass
class NLToStressRequestOutput:
    """Final output: partial request + missing/low-confidence fields."""

    partial_request: PartialStressRequest
    missing_required_fields: List[str] = field(default_factory=list)
    low_confidence_fields: List[str] = field(default_factory=list)
    intent_type: str = "unknown"


# ========================================
# LLM Extraction
# ========================================


def extract_fields_with_llm(
    user_text: str, conversation_history: Optional[List[Dict[str, str]]] = None, request_id: Optional[str] = None
) -> NLUResult:
    """
    Use LLM to extract mortgage-related fields from English text.
    
    Implements retry logic for timeout and transient 5xx errors.

    Args:
        user_text: User's natural language query
        conversation_history: Optional list of previous conversation turns,
            each as a dict with "role" ("user" or "assistant") and "content" (str)

    Returns:
        NLUResult with extracted fields, or empty result on error
    """
    from services.fiqa_api.clients import get_openai_client
    from services.fiqa_api.utils.env_loader import get_llm_conf
    from services.fiqa_api.utils.llm_client import is_llm_generation_enabled
    
    try:
        import httpx
        TimeoutException = httpx.TimeoutException
    except ImportError:
        # httpx not available, use TimeoutError as fallback
        TimeoutException = TimeoutError

    # Check if LLM generation is enabled
    if not is_llm_generation_enabled():
        logger.info("[NLU] LLM generation disabled, returning empty result")
        return NLUResult(extracted_fields=[], intent_type="unknown", raw_user_text=user_text)

    # Get OpenAI client
    openai_client = get_openai_client()
    if openai_client is None:
        logger.warning("[NLU] OpenAI client not available")
        return NLUResult(extracted_fields=[], intent_type="unknown", raw_user_text=user_text)

    # Get LLM configuration
    try:
        llm_conf = get_llm_conf()
        model = llm_conf.get("model", "gpt-4o-mini")
        max_tokens = llm_conf.get("max_tokens", 512)
    except Exception as e:
        logger.warning(f"[NLU] Failed to load LLM config: {e}")
        return NLUResult(extracted_fields=[], intent_type="unknown", raw_user_text=user_text)

    # Build system prompt
    system_prompt = """You are a mortgage information extraction assistant. Your job is to extract mortgage-related fields from user queries.

CRITICAL RULES:
1. ONLY extract fields that the user explicitly mentioned. Do NOT guess or infer values.
2. Use ONLY the allowed field names from this list:
   - income_monthly: Monthly income
   - income_annual: Annual income
   - home_price: Home purchase price (also accept "list_price" as alias)
   - down_payment_amount: Down payment as absolute amount
   - down_payment_pct: Down payment as percentage
   - interest_rate_annual: Annual interest rate
   - loan_term_years: Loan term in years
   - zip_code: ZIP code (5 digits)
   - state: State code (2 letters)

3. For each field, extract:
   - value: The numeric or string value as mentioned
   - unit: The unit identifier (e.g., "k_usd_per_year", "usd_per_month", "percent_annual", "k_usd", "million_usd")
   - source_text: The exact phrase from the user text that mentioned this field (optional but helpful)
   - confidence: Your confidence (0-1) that this extraction is correct (optional)

4. Unit examples:
   - "$150k a year" → value: 150, unit: "k_usd_per_year"
   - "6k per month" → value: 6, unit: "k_usd_per_month"
   - "20% down" → value: 20, unit: "percent" (or "percent_absolute" if 0-100 scale)
   - "750k home" → value: 750, unit: "k_usd"
   - "6.5% interest" → value: 6.5, unit: "percent_annual"
   - "30 year loan" → value: 30, unit: "years"

5. Intent classification:
   - "new_plan": User wants to check a new mortgage scenario
   - "adjust_existing": User wants to modify an existing plan
   - "ask_explanation": User is asking a question/explanation
   - "unknown": Cannot determine intent

6. Output format: Return ONLY a valid JSON object matching this schema:
{
  "extracted_fields": [
    {
      "field": "income_annual",
      "value": 150,
      "unit": "k_usd_per_year",
      "source_text": "$150k a year",
      "confidence": 0.95
    }
  ],
  "intent_type": "new_plan",
  "raw_user_text": "[original user text]"
}

Do NOT include any explanatory text outside the JSON object."""

    # Build user prompt
    user_prompt = f"Extract mortgage fields from this query:\n\n{user_text}"

    # Build messages (include conversation history if provided)
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        # Add history as previous user/assistant turns
        # Limit to last 6 messages (3 turns) to keep context manageable
        max_history_messages = 6
        recent_history = conversation_history[-max_history_messages:] if len(conversation_history) > max_history_messages else conversation_history
        
        for hist_item in recent_history:
            role = hist_item.get("role", "user")
            content = hist_item.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_prompt})

    # Retry loop for timeout and transient errors
    last_exception = None
    nlu_start = time.perf_counter()
    for attempt in range(NLU_MAX_RETRIES + 1):
        try:
            # Call OpenAI API with JSON response format and explicit timeout
            response = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                timeout=NLU_TIMEOUT_SEC,
            )

            content = response.choices[0].message.content or "{}"
            logger.debug(f"[NLU] LLM raw response: {content[:500]}")

            # Parse JSON
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"[NLU] Failed to parse JSON response: {e}")
                # Try to extract JSON from text if wrapped
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1 and end > start:
                    parsed = json.loads(content[start : end + 1])
                else:
                    raise

            # Validate with Pydantic
            nlu_result = NLUResult(**parsed)
            # Ensure raw_user_text matches input
            nlu_result.raw_user_text = user_text
            nlu_duration_ms = (time.perf_counter() - nlu_start) * 1000
            logger.info(
                f'{{"event": "nl_parse", "request_id": "{request_id or "unknown"}", '
                f'"duration_ms": {nlu_duration_ms:.1f}, "intent_type": "{nlu_result.intent_type}", '
                f'"missing_fields": {[f for f in ["income_monthly", "list_price"] if f not in [ef.field for ef in nlu_result.extracted_fields]]}}}'
            )
            return nlu_result

        except ValidationError as e:
            # Don't retry on validation errors
            logger.warning(f"[NLU] Pydantic validation failed: {e}")
            return NLUResult(extracted_fields=[], intent_type="unknown", raw_user_text=user_text)
        
        except (TimeoutException, TimeoutError) as e:
            last_exception = e
            nlu_duration_ms = (time.perf_counter() - nlu_start) * 1000
            if attempt < NLU_MAX_RETRIES:
                logger.warning(
                    f'{{"event": "nl_llm_error", "request_id": "{request_id or "unknown"}", '
                    f'"error_type": "timeout", "attempt": {attempt + 1}, "duration_ms": {nlu_duration_ms:.1f}}}'
                )
                time.sleep(NLU_RETRY_BACKOFF_SEC)
            else:
                logger.warning(
                    f'{{"event": "nl_llm_error", "request_id": "{request_id or "unknown"}", '
                    f'"error_type": "timeout", "attempts_exhausted": true, "duration_ms": {nlu_duration_ms:.1f}}}'
                )
        
        except Exception as e:
            # Check if it's a transient 5xx error (API error)
            is_transient = False
            error_str = str(e).lower()
            if "500" in error_str or "502" in error_str or "503" in error_str or "504" in error_str:
                is_transient = True
            
            if is_transient and attempt < NLU_MAX_RETRIES:
                last_exception = e
                logger.warning(f"[NLU] Transient error on attempt {attempt + 1}/{NLU_MAX_RETRIES + 1}, retrying after {NLU_RETRY_BACKOFF_SEC}s: {e}")
                time.sleep(NLU_RETRY_BACKOFF_SEC)
            else:
                # Non-retryable error or all retries exhausted
                nlu_duration_ms = (time.perf_counter() - nlu_start) * 1000
                logger.warning(
                    f'{{"event": "nl_llm_error", "request_id": "{request_id or "unknown"}", '
                    f'"error_type": "{type(e).__name__}", "duration_ms": {nlu_duration_ms:.1f}}}',
                    exc_info=True
                )
                return NLUResult(extracted_fields=[], intent_type="unknown", raw_user_text=user_text)
        

    # All retries exhausted
    nlu_duration_ms = (time.perf_counter() - nlu_start) * 1000
    logger.warning(
        f'{{"event": "nl_llm_error", "request_id": "{request_id or "unknown"}", '
        f'"error_type": "all_retries_exhausted", "duration_ms": {nlu_duration_ms:.1f}}}'
    )
    # Return safe degraded result
    return NLUResult(extracted_fields=[], intent_type="unknown", raw_user_text=user_text)


# ========================================
# Unit Conversion Helpers
# ========================================


def parse_money_with_unit(value: Union[float, int], unit: Optional[str]) -> float:
    """
    Parse a money value with unit into absolute USD.
    
    Handles:
    - k/thousand style units (300k, 6k per month)
    - million style units (1.2 million)
    - Plain USD amounts

    Examples:
        - 150, "k_usd" → 150_000
        - 1.5, "million_usd" → 1_500_000
        - 750, "k_usd" → 750_000
        - 300000, "usd" → 300000
        - 300, "thousand" → 300_000

    Args:
        value: Numeric value
        unit: Unit identifier

    Returns:
        Absolute USD amount
    """
    if unit is None:
        # Assume USD if no unit
        return float(value)

    unit_lower = unit.lower()

    # Handle "k", "k_usd", "thousand", "thousand_usd" → multiply by 1000
    if "k_usd" in unit_lower or unit_lower == "k" or "thousand" in unit_lower:
        return float(value) * 1000.0

    # Handle "million" or "million_usd" → multiply by 1_000_000
    if "million" in unit_lower:
        return float(value) * 1_000_000.0

    # Handle plain "usd" → return as-is
    if "usd" in unit_lower and "k" not in unit_lower and "million" not in unit_lower and "thousand" not in unit_lower:
        return float(value)

    # Default: assume USD
    logger.debug(f"[NLU] Unknown money unit '{unit}', treating as USD")
    return float(value)


def parse_percent(value: Union[float, int], unit: Optional[str]) -> float:
    """
    Parse a percentage value into a 0-1 fraction.
    
    Handles percentages expressed as:
    - 0.06 (fraction)
    - 6 or 6% (percentage, normalized to 0.06)
    
    For interest_rate_annual: treat 6 as 6% (0.06) unless explicitly marked as fraction.

    Examples:
        - 6, "percent" → 0.06
        - 20, "percent" → 0.20
        - 0.06, "fraction" → 0.06
        - 6, None → 0.06 (assume percent if >= 1)

    Args:
        value: Numeric value
        unit: Unit identifier

    Returns:
        Fraction between 0 and 1
    """
    val_float = float(value)

    if unit is None:
        # If no unit, assume it's already a fraction if < 1, otherwise percent
        # This handles cases like "6" for interest rate (treat as 6%)
        if val_float < 1.0:
            return val_float
        else:
            return val_float / 100.0

    unit_lower = unit.lower()

    # If unit contains "fraction" or "decimal", return as-is
    if "fraction" in unit_lower or "decimal" in unit_lower:
        return val_float

    # If unit contains "percent" or "%", divide by 100
    if "percent" in unit_lower or "%" in unit_lower:
        return val_float / 100.0

    # If value is < 1, assume fraction; otherwise assume percent
    if val_float < 1.0:
        return val_float
    else:
        return val_float / 100.0


def parse_income_to_monthly(value: Union[float, int], unit: Optional[str]) -> float:
    """
    Convert income value to monthly amount.

    Examples:
        - 150, "k_usd_per_year" → 150_000 / 12 = 12_500
        - 6, "k_usd_per_month" → 6_000
        - 6000, "usd_per_month" → 6000

    Args:
        value: Income value
        unit: Unit identifier

    Returns:
        Monthly income in USD
    """
    if unit is None:
        # Assume monthly if no unit
        return float(value)

    unit_lower = unit.lower()

    # If per_year or per_year in unit, convert to monthly
    if "per_year" in unit_lower or "annual" in unit_lower or "yearly" in unit_lower:
        annual_amount = parse_money_with_unit(value, unit.replace("_per_year", "").replace("_annual", "").replace("_yearly", ""))
        return annual_amount / 12.0

    # If per_month or monthly, just parse money
    if "per_month" in unit_lower or "monthly" in unit_lower:
        return parse_money_with_unit(value, unit.replace("_per_month", "").replace("_monthly", ""))

    # Default: assume monthly
    logger.debug(f"[NLU] Unknown income unit '{unit}', treating as monthly USD")
    return parse_money_with_unit(value, unit)


# ========================================
# NLU Result to Partial Request Conversion
# ========================================


def nlu_result_to_partial_request(nlu: NLUResult) -> NLToStressRequestOutput:
    """
    Convert NLUResult to PartialStressRequest with unit conversions.

    Args:
        nlu: NLU extraction result

    Returns:
        NLToStressRequestOutput with partial request and missing/low-confidence fields
    """
    partial = PartialStressRequest()

    # Track which fields we filled
    filled_fields = set()
    low_confidence_fields_list = []

    # Process each extracted field
    for field_obj in nlu.extracted_fields:
        field_name = field_obj.field
        value = field_obj.value
        unit = field_obj.unit
        confidence = field_obj.confidence or 1.0

        # Mark as low confidence if confidence < 0.7
        if confidence < 0.7:
            low_confidence_fields_list.append(field_name)

        try:
            if field_name == "income_annual":
                partial.income_monthly = parse_income_to_monthly(value, unit)
                filled_fields.add("income_monthly")
                logger.debug(f"[NLU] Converted income_annual {value} ({unit}) → monthly {partial.income_monthly}")

            elif field_name == "income_monthly":
                partial.income_monthly = parse_income_to_monthly(value, unit)
                filled_fields.add("income_monthly")
                logger.debug(f"[NLU] Set income_monthly {value} ({unit}) → {partial.income_monthly}")

            elif field_name == "home_price" or field_name == "list_price":
                # Map both "home_price" and "list_price" from LLM to "list_price" in PartialStressRequest
                # This ensures consistency with StressCheckRequest.list_price
                partial.list_price = parse_money_with_unit(value, unit)
                filled_fields.add("list_price")
                logger.debug(f"[NLU] Mapped {field_name} {value} ({unit}) → list_price {partial.list_price}")

            elif field_name == "down_payment_amount":
                # If we also have list_price, we can compute down_payment_pct
                if partial.list_price is not None and partial.list_price > 0:
                    down_payment_abs = parse_money_with_unit(value, unit)
                    partial.down_payment_pct = down_payment_abs / partial.list_price
                    filled_fields.add("down_payment_pct")
                    logger.debug(
                        f"[NLU] Computed down_payment_pct from amount: {down_payment_abs} / {partial.list_price} = {partial.down_payment_pct}"
                    )
                # Otherwise, we can't use this field without list_price
                logger.debug(f"[NLU] Ignored down_payment_amount (no list_price available)")

            elif field_name == "down_payment_pct":
                # Normalize to 0-1 fraction
                pct_fraction = parse_percent(value, unit)
                partial.down_payment_pct = pct_fraction
                filled_fields.add("down_payment_pct")
                logger.debug(f"[NLU] Set down_payment_pct {value} ({unit}) → {partial.down_payment_pct}")

            elif field_name == "interest_rate_annual":
                # Normalize to 0-1 fraction (e.g., 6% → 0.06)
                partial.interest_rate_annual = parse_percent(value, unit)
                filled_fields.add("interest_rate_annual")
                logger.debug(f"[NLU] Set interest_rate_annual {value} ({unit}) → {partial.interest_rate_annual}")

            elif field_name == "loan_term_years":
                partial.loan_term_years = int(value)
                filled_fields.add("loan_term_years")
                logger.debug(f"[NLU] Set loan_term_years {value} → {partial.loan_term_years}")

            elif field_name == "zip_code":
                # Normalize ZIP code (remove spaces, ensure 5 digits)
                zip_str = str(value).strip().replace(" ", "")
                if len(zip_str) == 5 and zip_str.isdigit():
                    partial.zip_code = zip_str
                    filled_fields.add("zip_code")
                    logger.debug(f"[NLU] Set zip_code {value} → {partial.zip_code}")
                else:
                    logger.warning(f"[NLU] Invalid ZIP code format: {zip_str}")

            elif field_name == "state":
                # Normalize state code (uppercase, 2 letters)
                state_str = str(value).strip().upper()
                if len(state_str) == 2 and state_str.isalpha():
                    partial.state = state_str
                    filled_fields.add("state")
                    logger.debug(f"[NLU] Set state {value} → {partial.state}")
                else:
                    logger.warning(f"[NLU] Invalid state code format: {state_str}")

        except Exception as e:
            logger.warning(f"[NLU] Failed to process field {field_name}: {e}")
            # Mark as low confidence if processing failed
            low_confidence_fields_list.append(field_name)

    # Compute missing required fields
    missing_required = []
    for req_field in REQUIRED_FIELDS:
        if req_field not in filled_fields:
            # Check if the field is None in partial request
            if getattr(partial, req_field, None) is None:
                missing_required.append(req_field)

    # Build low confidence list (deduplicate)
    low_confidence_set = set(low_confidence_fields_list)
    low_confidence_list = list(low_confidence_set)

    return NLToStressRequestOutput(
        partial_request=partial,
        missing_required_fields=missing_required,
        low_confidence_fields=low_confidence_list,
        intent_type=nlu.intent_type,
    )


# ========================================
# Public API
# ========================================


def nl_to_stress_request(
    user_text: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    request_id: Optional[str] = None,
) -> NLToStressRequestOutput:
    """
    High-level entry point: convert natural language to partial StressCheckRequest.

    Steps:
    1. Call LLM to extract fields
    2. Convert to PartialStressRequest with unit normalization
    3. Compute missing/low-confidence fields

    Args:
        user_text: User's natural language query
        conversation_history: Optional list of previous conversation turns,
            each as a dict with "role" ("user" or "assistant") and "content" (str)

    Returns:
        NLToStressRequestOutput with partial request and metadata
    """
    # Step 1: Extract fields with LLM
    nlu_result = extract_fields_with_llm(user_text, conversation_history, request_id=request_id)

    # Step 2 & 3: Convert to partial request and compute missing fields
    output = nlu_result_to_partial_request(nlu_result)

    logger.info(
        f"[NLU] Processed query: intent={output.intent_type}, "
        f"filled={len([f for f in dir(output.partial_request) if not f.startswith('_') and getattr(output.partial_request, f) is not None])}, "
        f"missing={len(output.missing_required_fields)}, "
        f"low_confidence={len(output.low_confidence_fields)}"
    )

    return output

