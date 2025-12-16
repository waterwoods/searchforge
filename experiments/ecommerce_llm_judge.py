#!/usr/bin/env python3
"""
ecommerce_llm_judge.py - LLM-as-Judge for Ecommerce Agent Evaluation

This module provides an LLM-based judge that evaluates the quality and policy-alignment
of ecommerce agent interactions. It uses a stronger LLM (e.g., gpt-4o) to assess:
- Policy alignment (correct application of refund/return policies)
- Explanation quality (clarity of response)
- Helpfulness (usefulness to the user)
- Tone (professionalism and empathy)
- Hallucination risk (potential for false promises)
- Overall score and flagging recommendations

This is a separate evaluation layer that does not affect the agent's runtime logic.
"""

import os
import json
import logging
from time import perf_counter
from typing import Optional, Literal
from pydantic import BaseModel, Field, ValidationError

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.clients import get_openai_client
from services.fiqa_api.observability.metrics import LLMCallMetric, extract_llm_usage

logger = logging.getLogger(__name__)


class LLMJudgeError(Exception):
    """Custom exception for LLM judge errors."""
    pass


class LLMJudgeScore(BaseModel):
    """LLM judge scoring result model."""
    
    policy_alignment: Literal["pass", "fail", "uncertain"] = Field(
        ...,
        description="Whether the response correctly applies refund/return policies"
    )
    explanation_quality: int = Field(
        ...,
        ge=1,
        le=5,
        description="Quality of explanation (1-5 scale)"
    )
    helpfulness: int = Field(
        ...,
        ge=1,
        le=5,
        description="Helpfulness to the user (1-5 scale)"
    )
    tone: int = Field(
        ...,
        ge=1,
        le=5,
        description="Professionalism and empathy in tone (1-5 scale)"
    )
    hallucination_risk: Literal["low", "medium", "high"] = Field(
        ...,
        description="Risk of making false promises or incorrect claims"
    )
    overall_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Overall quality score (1-10 scale)"
    )
    should_flag: bool = Field(
        ...,
        description="Whether this case should be flagged for manual review"
    )
    comments: Optional[str] = Field(
        None,
        description="Additional comments or notes from the judge"
    )


def llm_judge_interaction(
    user_message: str,
    final_response: str,
    policy_context: Optional[str] = None,
    ground_truth_notes: Optional[str] = None,
) -> LLMJudgeScore:
    """
    Call a stronger LLM to judge the quality and policy-alignment of the interaction.
    
    Args:
        user_message: The user's original message/request
        final_response: The agent's final response to the user
        policy_context: Optional policy snippets or context retrieved by RAG
        ground_truth_notes: Optional ground truth notes for reference
    
    Returns:
        LLMJudgeScore with all evaluation dimensions
    
    Raises:
        LLMJudgeError: If LLM call fails or response cannot be parsed
    """
    # Get OpenAI client
    client = get_openai_client()
    if client is None:
        logger.error("OpenAI client not available, cannot perform LLM judgment")
        raise LLMJudgeError("OpenAI client not available")
    
    # Get model from environment variable, default to gpt-4o
    model = os.getenv("ECOMMERCE_JUDGE_MODEL", "gpt-4o")
    
    # Build system prompt
    system_prompt = """You are a calm and objective policy reviewer evaluating an ecommerce customer service interaction.

Your role is to assess:
1. Policy Alignment: Does the response correctly apply refund/return policies based on the provided policy context?
2. Explanation Quality: Is the response clear and easy to understand?
3. Helpfulness: Does the response actually help the user solve their problem?
4. Tone: Is the response professional, empathetic, and appropriate?
5. Hallucination Risk: Does the response make any false promises or incorrect claims that could mislead the user?

Focus on:
- Whether the agent correctly interprets and applies policy rules
- Whether the response explains the decision clearly
- Whether there are any risks of making promises that cannot be kept
- Overall quality and professionalism

Be strict but fair. Flag cases that have policy violations, unclear explanations, or high hallucination risk."""

    # Build user prompt
    user_prompt_parts = [
        "Evaluate the following customer service interaction:",
        "",
        f"User Message: {user_message}",
        "",
        f"Agent Response: {final_response}",
    ]
    
    if policy_context:
        user_prompt_parts.extend([
            "",
            "Policy Context:",
            policy_context,
        ])
    
    if ground_truth_notes:
        user_prompt_parts.extend([
            "",
            "Ground Truth Notes (for reference):",
            ground_truth_notes,
        ])
    
    user_prompt_parts.append(
        "\nProvide your evaluation as a JSON object with the following structure:\n"
        "- policy_alignment: 'pass', 'fail', or 'uncertain'\n"
        "- explanation_quality: integer 1-5\n"
        "- helpfulness: integer 1-5\n"
        "- tone: integer 1-5\n"
        "- hallucination_risk: 'low', 'medium', or 'high'\n"
        "- overall_score: integer 1-10\n"
        "- should_flag: boolean\n"
        "- comments: optional string with additional notes"
    )
    
    user_prompt = "\n".join(user_prompt_parts)
    
    start = perf_counter()
    try:
        # Call LLM with JSON mode
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent judgments
        )
        
        end = perf_counter()
        latency_ms = (end - start) * 1000.0
        usage_info = extract_llm_usage(response)
        
        # Log metric
        metric = LLMCallMetric(
            component="llm_judge",
            model=model,
            prompt_tokens=usage_info["prompt_tokens"],
            completion_tokens=usage_info["completion_tokens"],
            total_tokens=usage_info["total_tokens"],
            latency_ms=latency_ms,
            success=True,
            error_message=None,
        )
        logger.info(f"LLM_CALL_METRIC: {metric.model_dump_json()}")
        
        # Extract JSON from response
        content = response.choices[0].message.content
        if not content:
            raise LLMJudgeError("Empty response from LLM")
        
        # Parse JSON
        try:
            score_dict = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response content: {content}")
            raise LLMJudgeError(f"Invalid JSON in LLM response: {e}")
        
        # Validate and create LLMJudgeScore
        try:
            score = LLMJudgeScore(**score_dict)
            return score
        except ValidationError as e:
            logger.error(f"LLM response does not match expected schema: {e}")
            logger.error(f"Response dict: {score_dict}")
            raise LLMJudgeError(f"Invalid score schema: {e}")
    
    except LLMJudgeError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        end = perf_counter()
        latency_ms = (end - start) * 1000.0
        
        # Log failed metric
        metric = LLMCallMetric(
            component="llm_judge",
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency_ms=latency_ms,
            success=False,
            error_message=str(e),
        )
        logger.info(f"LLM_CALL_METRIC: {metric.model_dump_json()}")
        logger.error(f"Unexpected error during LLM judgment: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise LLMJudgeError(f"LLM judgment failed: {e}")


def get_safe_default_score() -> LLMJudgeScore:
    """
    Return a safe default score when LLM judgment fails.
    
    This represents a "worst case" score that flags the case for review.
    """
    return LLMJudgeScore(
        policy_alignment="uncertain",
        explanation_quality=1,
        helpfulness=1,
        tone=1,
        hallucination_risk="high",
        overall_score=0,
        should_flag=True,
        comments="LLM judgment failed, defaulting to flagged state",
    )
