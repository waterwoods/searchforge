"""
jd_constraints.py - Constraint Checker for Job Descriptions
===========================================================

This module provides functionality to check basic constraints in job descriptions,
such as:
- Remote vs onsite/hybrid work requirements
- Location restrictions (must reside in specific state/city)
- Heavy travel requirements

This is a rule-based checker (not LLM-based) that uses simple string matching
and regex patterns to identify constraint flags.

[改动标记 - Step 1]
- check_basic_constraints(): 强化硬/软条件区分，添加 hard_block 和 hard_reasons 逻辑

[Quick Filter]
- _estimate_profile_mismatch(): Cheap heuristic to detect obvious profile/JD mismatches
- check_basic_constraints(): Wires profile mismatch check and sets skip_deep_analysis flag
"""

import re
import logging
from typing import Optional, Tuple

from services.fiqa_api.jobhunter.schemas import JobJDInput, ConstraintCheckResult

logger = logging.getLogger(__name__)


def quick_role_filter(
    profile_id: str | None,
    jd_text: str,
) -> Tuple[Optional[int], list[str], bool]:
    """
    Quick role filter: Pure keyword-based rule to detect if JD is Data Engineering / LLM Engineering related.
    
    This is a lightweight, rule-based filter that uses keyword counting to identify
    obvious non-target roles (e.g., financial sales, insurance advisor) early,
    before running expensive LLM analysis.
    
    Args:
        profile_id: Profile identifier (e.g., "data_engineer_gcp", "llm_agent", "data_eng", "agent")
        jd_text: Job description text (will be lowercased internally)
    
    Returns:
        Tuple of (score, reasons, skip):
        - score: Profile mismatch score (0-10, lower = worse match, None = no clear signal)
        - reasons: List of human-readable explanation strings
        - skip: Whether we should skip deep LLM analysis (True only for strong mismatches)
    
    Decision Logic:
        - If non_tech_count >= 3 AND data_count == 0 OR role_score <= -2:
          → Strong mismatch, skip_deep_analysis = True
        - Otherwise: Allow through (don't skip, even if borderline)
    
    Note:
        This filter is conservative - it only skips in extreme cases to avoid
        accidentally filtering out interesting but borderline roles.
    """
    jd_lower = jd_text.lower()
    
    # Normalize profile_id
    if profile_id:
        profile_id_lower = profile_id.lower()
        if "data" in profile_id_lower and ("engineer" in profile_id_lower or "eng" in profile_id_lower):
            profile_id = "data_engineer_gcp"
        elif "llm" in profile_id_lower or "agent" in profile_id_lower:
            profile_id = "llm_agent"
    
    # Data Engineering / LLM Engineering keywords (combined for both profiles)
    data_keywords = [
        # Core data engineering terms
        "data engineer", "data engineering", "etl", "data pipeline", "data pipelines",
        "data warehouse", "data warehousing", "data quality", "data observability",
        "data modeling", "data modeling", "data infrastructure", "data platform",
        # Cloud data platforms
        "bigquery", "snowflake", "redshift", "databricks", "data lake", "data lakehouse",
        "gcp", "aws", "azure", "cloud storage", "cloud data",
        # Data tools & frameworks
        "airflow", "spark", "dbt", "sql", "python", "pyspark", "scala",
        "dataflow", "pub/sub", "cloud composer", "composer",
        "streaming", "stream processing", "batch processing", "real-time processing",
        # ML/LLM engineering terms
        "machine learning", "ml ops", "mlops", "llm", "large language model",
        "rag", "retrieval augmented generation", "feature store", "model serving",
        "langgraph", "langchain", "agent", "agents", "multi-agent", "agentic",
        "evaluation", "safeguards", "guardrails", "orchestration", "system health",
        "prompt engineering", "fine-tuning", "embedding", "vector database",
    ]
    
    # Non-target role keywords (sales, financial advisor, insurance, etc.)
    non_target_keywords = [
        # Sales & business development
        "sales", "prospect", "prospects", "leads", "cold call", "client engagement",
        "customer acquisition", "business development", "revenue generation",
        "client relationship", "relationship management", "account management",
        "consultant", "consultants",  # Sales consultants, financial consultants, etc.
        "solar consultant", "financial consultant",  # Common non-tech consultant roles
        # Financial advisor / wealth management
        "financial advisor", "financial specialist", "financial planner",
        "wealth management", "wealth advisor", "retirement planning", "estate planning",
        "commissions", "commission", "portfolio", "portfolios",
        "investment", "investments", "trading", "trader", "broker", "brokerage",
        "mutual funds", "stocks", "bonds", "securities", "financial products",
        "licensed", "series 7", "series 63", "cfp", "certified financial planner",
        # Insurance
        "insurance", "insurance agent", "insurance advisor", "insurance sales",
        # Real estate
        "real estate agent", "real estate broker", "mortgage broker",
        # Other non-tech roles
        "clients", "client", "customer service", "customer support",
        "customer", "customers",  # Add customer/customers as keywords
    ]
    
    # Count keyword occurrences
    data_count = sum(1 for kw in data_keywords if kw in jd_lower)
    non_tech_count = sum(1 for kw in non_target_keywords if kw in jd_lower)
    
    # Calculate role_score: positive = more data/tech, negative = more sales/finance
    role_score = data_count - non_tech_count
    
    # [DEBUG] Log keyword counts for troubleshooting
    logger.info(
        f"[ROLE_FILTER] profile_id={profile_id}, "
        f"data_count={data_count}, non_tech_count={non_tech_count}, "
        f"role_score={role_score}"
    )
    
    # Decision: Strong mismatch (skip deep analysis)
    # Rule: non_tech_count >= 2 AND (data_count == 0 OR role_score <= -1)
    # Note: Lowered threshold to be more sensitive to sales/financial roles
    # This works even when profile_id is None - we check for obvious non-target roles regardless
    if non_tech_count >= 2 and (data_count == 0 or role_score <= -1):
        reasons = [
            f"JD appears to be a non-target role (e.g., financial sales, insurance advisor). "
            f"Detected {non_tech_count} non-tech keywords vs {data_count} data/tech keywords."
        ]
        logger.info(
            f"[ROLE_FILTER] STRONG MISMATCH detected: "
            f"non_tech_count={non_tech_count}, data_count={data_count}, "
            f"role_score={role_score}, skip_deep_analysis=True"
        )
        return (-10, reasons, True)  # Use -10 to indicate strong mismatch
    
    # Decision: Possible match or borderline (don't skip, let LLM decide)
    # For borderline cases, we still allow through to avoid false negatives
    if non_tech_count >= 2 and data_count > 0:
        # Some non-tech keywords but also has data keywords - borderline case
        logger.info(
            f"[ROLE_FILTER] Borderline case: "
            f"non_tech_count={non_tech_count}, data_count={data_count}, "
            f"role_score={role_score}, skip_deep_analysis=False (allowing through)"
        )
        return (None, [], False)  # No clear signal, let LLM decide
    
    # Decision: No clear signal (likely a tech role or neutral)
    logger.debug(
        f"[ROLE_FILTER] No clear mismatch signal: "
        f"data_count={data_count}, non_tech_count={non_tech_count}, "
        f"role_score={role_score}, skip_deep_analysis=False"
    )
    return (None, [], False)


def _estimate_profile_mismatch(
    jd_text: str,
    candidate_profile: str,
    profile_id: Optional[str] = None,
) -> Tuple[Optional[int], list[str], bool]:
    """
    Legacy wrapper for quick_role_filter (for backward compatibility).
    
    This function auto-detects profile_id from candidate_profile text and calls
    quick_role_filter. It's kept for backward compatibility with existing code.
    
    Args:
        jd_text: Job description text
        candidate_profile: Candidate profile text (used to auto-detect profile_id)
        profile_id: Optional profile identifier (e.g., "data_engineer_gcp", "llm_agent")
    
    Returns:
        Tuple of (score, reasons, skip) - same as quick_role_filter
    """
    profile_lower = candidate_profile.lower() if candidate_profile else ""
    
    # Auto-detect profile_id from profile text if not provided
    if not profile_id:
        if "data engineer" in profile_lower or "data engineering" in profile_lower or "gcp" in profile_lower:
            profile_id = "data_engineer_gcp"
        elif "llm" in profile_lower or "agent" in profile_lower or "langgraph" in profile_lower:
            profile_id = "llm_agent"
    
    # Call quick_role_filter
    return quick_role_filter(profile_id=profile_id, jd_text=jd_text)


def check_basic_constraints(
    jd_input: JobJDInput,
    candidate_profile: str | None = None,
    profile_id: Optional[str] = None,
) -> ConstraintCheckResult:
    """
    Check basic constraints in a job description.
    
    Identifies hard blocks and soft flags for:
    - Remote vs onsite/hybrid work mode
    - Location restrictions (must reside in specific state/city)
    - Heavy travel requirements (>30-50% travel)
    
    This implementation is conservative - it only sets hard_block=True for
    clearly incompatible constraints. Most issues are flagged as soft_flags.
    
    Args:
        jd_input: JobJDInput instance containing the job description
        candidate_profile: Optional candidate profile text (e.g., contains "remote-first", "US timezone")
        profile_id: Optional profile identifier (e.g., "data_engineer_gcp", "llm_agent")
                    Used for profile mismatch detection
        
    Returns:
        ConstraintCheckResult with hard_block, soft_flags, reasons, tags, and profile_mismatch fields
    """
    result = ConstraintCheckResult()
    
    if not jd_input.description:
        return result
    
    # Normalize text for matching
    desc_lower = jd_input.description.lower()
    profile_lower = (candidate_profile or "").lower()
    
    # Check work mode: remote vs onsite/hybrid
    # Patterns that indicate remote-friendly
    remote_indicators = [
        "remote",
        "remote-friendly",
        "remote first",
        "remote-first",
        "work from home",
        "wfh",
        "fully remote",
        "100% remote",
    ]
    
    # Patterns that indicate onsite requirement
    onsite_indicators = [
        "onsite only",
        "on-site only",
        "must be onsite",
        "must be on-site",
        "required to be in office",
        "office-based",
        "no remote",
        "not remote",
    ]
    
    # Patterns that indicate hybrid
    hybrid_indicators = [
        "hybrid",
        "hybrid model",
        "hybrid work",
        "mix of remote and onsite",
        "mix of remote and on-site",
    ]
    
    # Check for work mode mentions
    has_remote = any(indicator in desc_lower for indicator in remote_indicators)
    has_onsite_only = any(indicator in desc_lower for indicator in onsite_indicators)
    has_hybrid = any(indicator in desc_lower for indicator in hybrid_indicators)
    
    # Check candidate profile for remote preference
    profile_remote_first = any(
        kw in profile_lower
        for kw in ["remote-first", "remote first", "prefer remote", "remote preferred"]
    )
    
    # Flag work mode constraints
    # [Step 1] 硬条件：如果 JD 明确要求 onsite only 且候选人是 remote-first，设为硬阻塞
    if has_onsite_only and profile_remote_first:
        result.hard_block = True
        result.hard_reasons.append("Job explicitly requires 'onsite only', but candidate profile indicates remote-first preference")
        result.soft_flags.append("onsite_only")
        result.tags.append("onsite_only")
        result.reasons.append("Job requires onsite work, but candidate profile indicates remote-first preference")
    
    # [Step 1] 软条件：hybrid 与 remote-first 的冲突通常是软条件（可能可以协商）
    if has_hybrid and profile_remote_first:
        result.soft_flags.append("hybrid_required")
        result.tags.append("hybrid_required")
        result.reasons.append("Job requires hybrid work, but candidate prefers fully remote")
    
    # Check location restrictions (must reside in...)
    # Common patterns: "must reside in", "required to work and reside in", "must be located in"
    location_patterns = [
        r"must reside in (?:the state of |the state of )?([a-z\s]+)",
        r"required to work and reside in (?:the state of |the state of )?([a-z\s]+)",
        r"must be located in (?:the state of |the state of )?([a-z\s]+)",
        r"candidates must be (?:based in|located in) (?:the state of |the state of )?([a-z\s]+)",
        r"must live in (?:the state of |the state of )?([a-z\s]+)",
    ]
    
    location_restrictions = []
    for pattern in location_patterns:
        matches = re.finditer(pattern, desc_lower, re.IGNORECASE)
        for match in matches:
            location_text = match.group(1).strip()
            # Clean up common trailing words
            location_text = re.sub(r"\s+or\s+.*$", "", location_text)
            location_text = re.sub(r"\.$", "", location_text)
            if location_text and len(location_text) < 50:  # Sanity check
                location_restrictions.append(location_text)
    
    # Also check location field if available
    if jd_input.location:
        location_lower = jd_input.location.lower()
        # Check if location implies a state/city restriction (not "remote" or "anywhere")
        if "remote" not in location_lower and "anywhere" not in location_lower:
            # Try to extract state from location
            # Common patterns: "San Francisco, CA", "CA", "California"
            state_pattern = r",\s*([a-z]{2})\b|california|texas|new york|florida"
            state_match = re.search(state_pattern, location_lower, re.IGNORECASE)
            if state_match:
                state_name = state_match.group(1) if state_match.group(1) else state_match.group(0)
                location_restrictions.append(state_name)
    
    if location_restrictions:
        # Remove duplicates while preserving order
        seen = set()
        unique_restrictions = []
        for loc in location_restrictions:
            loc_normalized = loc.lower().strip()
            if loc_normalized not in seen:
                seen.add(loc_normalized)
                unique_restrictions.append(loc)
        
        location_str = ", ".join(unique_restrictions[:3])  # Limit to first 3
        # [Step 1] 硬条件：如果 JD 明确要求必须居住在特定地区且不支持 remote，设为硬阻塞
        # 检查 JD 是否明确说 "no remote" 或 "onsite only" 与 location restriction 同时出现
        if has_onsite_only and profile_remote_first:
            # 已经在上面处理了，这里只需要标记 location restriction
            pass
        elif not has_remote and "remote" not in desc_lower:
            # JD 中没有提到 remote，且有地理位置限制，可能是硬条件（如果有 profile）
            if profile_remote_first:
                result.hard_block = True
                result.hard_reasons.append(f"Job requires candidate to reside/work in: {location_str}, and JD does not mention remote work option")
        
        result.soft_flags.append("location_restriction")
        result.tags.append(f"must_reside_{unique_restrictions[0].lower().replace(' ', '_')[:20]}")
        result.reasons.append(f"Job requires candidate to reside/work in: {location_str}")
    
    # Check travel requirements
    # Patterns: "up to 50% travel", "30-40% travel", "heavy travel", "extensive travel"
    travel_patterns = [
        r"(\d+)\s*%\s*travel",
        r"up to (\d+)\s*%\s*travel",
        r"(\d+)-(\d+)\s*%\s*travel",
        r"(\d+)\s*to\s*(\d+)\s*%\s*travel",
    ]
    
    travel_percentages = []
    for pattern in travel_patterns:
        matches = re.finditer(pattern, desc_lower, re.IGNORECASE)
        for match in matches:
            # Extract percentage numbers
            groups = match.groups()
            if groups[0].isdigit():
                travel_percentages.append(int(groups[0]))
            if len(groups) > 1 and groups[1] and groups[1].isdigit():
                travel_percentages.append(int(groups[1]))
    
    # Also check for qualitative travel mentions
    heavy_travel_keywords = [
        "heavy travel",
        "extensive travel",
        "frequent travel",
        "significant travel",
        "travel required",
        "willingness to travel",
    ]
    
    has_heavy_travel_keywords = any(kw in desc_lower for kw in heavy_travel_keywords)
    
    # Flag travel if > 30% or heavy travel mentioned
    max_travel = max(travel_percentages) if travel_percentages else 0
    if max_travel > 30 or has_heavy_travel_keywords:
        result.soft_flags.append("heavy_travel")
        result.tags.append("heavy_travel")
        if max_travel > 0:
            result.reasons.append(f"Job requires {max_travel}% travel or more")
        else:
            result.reasons.append("Job mentions heavy/extensive travel requirements")
        
        # If candidate profile indicates remote-first, this is a bigger concern
        if profile_remote_first:
            result.reasons.append("Heavy travel conflicts with remote-first work preference")
    
    # [Quick Filter] Check for obvious profile/JD mismatch using quick_role_filter
    # This runs even if candidate_profile is None (uses profile_id only)
    if jd_input.description:
        # Use quick_role_filter directly (it doesn't need candidate_profile text)
        mismatch_score, mismatch_reasons, should_skip = quick_role_filter(
            profile_id=profile_id,
            jd_text=jd_input.description,
        )
        
        # Always set skip_deep_analysis if quick_role_filter says so
        if should_skip:
            result.skip_deep_analysis = True
            result.profile_mismatch_score = mismatch_score if mismatch_score is not None else 1
            result.profile_mismatch_reasons = mismatch_reasons
            
            logger.info(
                f"[ROLE_FILTER] Final result: score={mismatch_score}, "
                f"skip_deep_analysis=True, reasons={mismatch_reasons}"
            )
        elif mismatch_score is not None:
            # Set score and reasons even if not skipping (for informational purposes)
            result.profile_mismatch_score = mismatch_score
            result.profile_mismatch_reasons = mismatch_reasons
            logger.debug(
                f"[ROLE_FILTER] Mismatch score set but not skipping: "
                f"score={mismatch_score}, reasons={mismatch_reasons}"
            )
        else:
            logger.debug(
                f"[ROLE_FILTER] No clear mismatch signal detected "
                f"(profile_id={profile_id})"
            )
    
    # [Step 1] hard_block 逻辑已在上面实现，这里只保留日志
    logger.debug(
        f"Constraint check completed: hard_block={result.hard_block}, "
        f"hard_reasons={result.hard_reasons}, "
        f"soft_flags={result.soft_flags}, tags={result.tags}, "
        f"skip_deep_analysis={result.skip_deep_analysis}"
    )
    
    return result
