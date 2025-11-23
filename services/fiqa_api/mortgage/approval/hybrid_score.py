"""
hybrid_score.py - Hybrid Rule + ML Approval Score Combination
==============================================================

This module implements the hybrid combination of rule-based and ML-based approval scores.
"""

import logging
from typing import Literal

from services.fiqa_api.mortgage.schemas import ApprovalScore

logger = logging.getLogger(__name__)




def combine_rule_and_ml(
    rule_approval: ApprovalScore,
    approve_prob: float,
) -> ApprovalScore:
    """
    Combine rule-based and ML-based approval scores using a weighted hybrid approach.
    
    Strategy:
    - Convert ML probability to a 0-100 scale (ml_score = approve_prob * 100)
    - If rule bucket is "borderline", give ML more influence (50/50 split)
    - If rule bucket is "likely" or "unlikely", keep rule as primary (70% rule, 30% ML)
    - Recompute final bucket based on combined score
    - Update reasons list if bucket changes
    
    Args:
        rule_approval: Rule-based ApprovalScore
        approve_prob: ML prediction probability (0-1) for "approve" class
    
    Returns:
        Combined ApprovalScore with updated score, bucket, and reasons
    """
    # Convert ML probability to 0-100 scale
    ml_score = approve_prob * 100.0
    
    # Determine weights based on rule bucket
    if rule_approval.bucket == "borderline":
        # Borderline cases: give ML more influence
        rule_weight = 0.5
        ml_weight = 0.5
    else:
        # Likely/unlikely cases: keep rule as primary
        rule_weight = 0.7
        ml_weight = 0.3
    
    # Combine scores
    final_score_value = rule_weight * rule_approval.score + ml_weight * ml_score
    
    # Clamp to 0-100 and round to 1 decimal
    final_score_value = float(min(100.0, max(0.0, round(final_score_value, 1))))
    
    # Recompute bucket based on final score
    if final_score_value >= 70:
        final_bucket = "likely"
    elif final_score_value >= 40:
        final_bucket = "borderline"
    else:
        final_bucket = "unlikely"
    
    # Build reasons list
    final_reasons = list(rule_approval.reasons)  # Start with rule-based reasons
    
    # Add ML adjustment tag if bucket changed
    if final_bucket != rule_approval.bucket:
        if final_bucket == "borderline":
            final_reasons.append("ml_borderline_adjustment")
        else:
            final_reasons.append("ml_adjusted")
    
    # Limit reasons list length (keep first 5 to avoid bloat)
    final_reasons = final_reasons[:5]
    
    return ApprovalScore(
        score=final_score_value,
        bucket=final_bucket,
        reasons=final_reasons,
    )

