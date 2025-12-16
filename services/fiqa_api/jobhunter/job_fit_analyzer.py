"""
job_fit_analyzer.py - Job Fit Analysis Module
==============================================

This module provides functionality to analyze how well a job description
matches a candidate's profile, identifying strengths, gaps, and actionable
next steps.

It compares the JD summary (gold/silver/bronze points, core skills) against
the candidate profile to produce a personalized fit assessment.

Job fit is computed with rules, not an LLM. Some skills are whitelisted as
'always strengths' for specific profiles (e.g. Data Engineer GCP) so they
never show up as gaps.
"""

import logging
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from services.fiqa_api.jobhunter.schemas import JobJDSummary

logger = logging.getLogger(__name__)

# Profile identifiers (must match front-end / profile loader)
PROFILE_LLM_AGENT = "llm_agent"
PROFILE_DATA_ENG_GCP = "data_engineer_gcp"

# Maximum number of strengths and gaps to show
MAX_ITEMS = 5


class JobFitSummary(BaseModel):
    """
    Personalized job fit analysis for a specific candidate.
    
    This model represents the comparison between a job description and
    a candidate profile, highlighting what matches and what's missing.
    """
    
    recommendation_for_candidate: Literal["APPLY", "MAYBE", "SKIP"] = Field(
        ...,
        description="Personalized recommendation for this candidate"
    )
    
    strengths: List[str] = Field(
        default_factory=list,
        description="List of strengths - points where the candidate matches well (✅)"
    )
    
    gaps: List[str] = Field(
        default_factory=list,
        description="List of gaps - key requirements missing from candidate profile (⚠️)"
    )
    
    action_items: List[str] = Field(
        default_factory=list,
        description="2-5 actionable next steps to address gaps"
    )


# Keywords that indicate strong matches (case-insensitive matching)
# Includes both LLM/Agent Engineer and Data Engineer keywords for profile matching.
# Extended Data Engineering keywords (data_engineering, big_data, data_quality, etc.) are
# specifically added to accurately match Andy's Data Engineer (GCP) profile, ensuring that
# data engineering roles with BigQuery/ETL/data quality requirements are correctly identified
# as strengths rather than gaps.
STRENGTH_KEYWORDS = [
    # General / Infrastructure
    "python", "gcp", "google cloud", "kubernetes", "k8s", "kubectl",
    "production", "infrastructure", "infra", "reliability", "security", "testing", "code quality",
    
    # LLM / Agent Engineering
    "llm", "large language model", "langgraph", "agent", "agents",
    "evaluation", "rag", "retrieval", "safeguards", "guardrails",
    "langchain", "multi-agent", "orchestration", "system health",
    
    # Data Engineering (extended keywords for Data Engineer profile matching)
    "data engineering", "data engineer", "etl", "elt", "data pipeline", "data pipelines",
    "big data", "large-scale data", "big data pipelines",
    "data warehouse", "data warehousing", "data platform",
    "data quality", "data observability", "data monitoring",
    "bigquery", "dataflow", "pub/sub", "cloud storage", "cloud composer",
    "airflow", "composer", "dbt", "data modeling",
    "distributed systems", "observability", "monitoring", "logging", "tracing", "sre",
    "data lineage", "data validation", "data testing", "great expectations",
    "streaming", "stream processing", "batch processing",
    
    # ML (shared)
    "ml", "machine learning",
]

# For these skills, if the profile claims them, we should NEVER treat them as gaps.
# This ensures that core profile skills (e.g. data_engineering for Data Engineer profile)
# are always shown as strengths, not gaps.
PROFILE_ALWAYS_STRENGTHS: dict[str, set[str]] = {
    PROFILE_DATA_ENG_GCP: {
        "data_engineering",
        "data engineer",
        "big_data",
        "big data",
        "data_quality",
        "data quality",
        "etl",
        "elt",
        "gcp",
        "google cloud",
        "bigquery",
    },
    # We can extend later for other profiles
}

# Keywords that indicate gaps (if frequently mentioned but not in profile)
# Note: Core data engineering skills (data_engineering, big_data, data_quality, etl, gcp, bigquery)
# are NOT in this list because they are handled by PROFILE_ALWAYS_STRENGTHS for specific profiles.
GAP_KEYWORDS = [
    "on-call", "oncall", "customer-facing", "customer facing",
    "sales", "business development", "billing", "payments",
    "public speaking", "developer advocacy", "advocacy",
    "tokenization", "tokenizer", "jax", "tpu", "tensorflow",
    "large-scale training", "pretraining", "pre-training", "finetune", "fine-tune",
    "pytorch", "torch", "model training", "training infrastructure",
    "full-time on-site", "extensive travel", "travel required",
    "early-stage startup", "startup", "unclear technical focus",
]

# Mapping from gap keywords to action item templates (English only)
GAP_TO_ACTION = {
    "large-scale training": "Build a small-scale pretraining/finetuning side project and add it to your resume",
    "pretraining": "Build a small-scale pretraining/finetuning side project and add it to your resume",
    "pre-training": "Build a small-scale pretraining/finetuning side project and add it to your resume",
    "finetune": "Build a small-scale pretraining/finetuning side project and add it to your resume",
    "fine-tune": "Build a small-scale pretraining/finetuning side project and add it to your resume",
    "model training": "Build a small-scale pretraining/finetuning side project and add it to your resume",
    "tokenization": "Read articles on tokenization and run experiments to understand tokenizer principles",
    "tokenizer": "Read articles on tokenization and run experiments to understand tokenizer principles",
    "customer-facing": "Prepare 1-2 stories about working with business/customers, emphasizing business value of technical solutions",
    "customer facing": "Prepare 1-2 stories about working with business/customers, emphasizing business value of technical solutions",
    "on-call": "Highlight existing SRE/incident handling experience and document on-call best practices",
    "oncall": "Highlight existing SRE/incident handling experience and document on-call best practices",
    "jax": "Learn JAX/TPU basics and create a simple JAX experimental project",
    "tpu": "Learn JAX/TPU basics and create a simple JAX experimental project",
    "agent platform": "Document existing ecommerce Agent + K8s deployment as a one-page technical case study",
    "agent framework": "Document existing ecommerce Agent + K8s deployment as a one-page technical case study",
}


def _normalize_text(text: str) -> str:
    """Normalize text for keyword matching (lowercase, strip)."""
    return text.lower().strip()


def _extract_keywords_from_text(text: str) -> List[str]:
    """
    Extract potential keywords from text by splitting on common delimiters.
    
    This is a simple heuristic - we look for words and phrases that might
    match our keyword lists.
    """
    # Normalize and split
    normalized = _normalize_text(text)
    # Split on common delimiters
    words = normalized.replace(",", " ").replace(".", " ").replace(":", " ").split()
    # Also check for multi-word phrases
    phrases = []
    for i in range(len(words)):
        # Single word
        phrases.append(words[i])
        # Two-word phrases
        if i < len(words) - 1:
            phrases.append(f"{words[i]} {words[i+1]}")
        # Three-word phrases (for things like "large-scale training")
        if i < len(words) - 2:
            phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
    return phrases


def _check_keyword_match(keyword: str, text: str) -> bool:
    """Check if a keyword appears in text (case-insensitive, substring match)."""
    normalized_text = _normalize_text(text)
    normalized_keyword = _normalize_text(keyword)
    return normalized_keyword in normalized_text


def _find_strengths(
    jd_summary: JobJDSummary,
    candidate_profile: str,
    profile_id: Optional[str] = None,
) -> List[str]:
    """
    Identify strengths by finding JD requirements that match candidate profile.
    
    Args:
        jd_summary: Job JD summary with gold/silver points and core skills
        candidate_profile: Candidate profile text
        profile_id: Optional profile identifier (e.g., "data_engineer_gcp")
        
    Returns:
        List of strength descriptions
    """
    strengths = []
    profile_lower = _normalize_text(candidate_profile)
    
    # Get always-strength keywords for this profile
    always_strengths = PROFILE_ALWAYS_STRENGTHS.get(profile_id or "", set())
    
    # Check core skills
    for skill in jd_summary.core_skills:
        skill_lower = _normalize_text(skill)
        # Check if any strength keyword matches
        for keyword in STRENGTH_KEYWORDS:
            if keyword in skill_lower or skill_lower in keyword:
                if _check_keyword_match(keyword, profile_lower):
                    strengths.append(f"Has core skill: {skill}")
                    break
        # Also check if this skill is in the always-strengths whitelist
        # Normalize for comparison (handle underscores vs spaces)
        skill_normalized = skill_lower.replace("_", " ").replace("-", " ")
        for always_kw in always_strengths:
            always_kw_normalized = always_kw.replace("_", " ").replace("-", " ")
            if (always_kw_normalized in skill_normalized or 
                skill_normalized in always_kw_normalized or
                always_kw_normalized == skill_normalized):
                if _check_keyword_match(skill, profile_lower):
                    strength_desc = f"Has core skill: {skill}"
                    if strength_desc not in strengths:
                        strengths.append(strength_desc)
                break
    
    # Check gold and silver points
    all_points = jd_summary.gold_points + jd_summary.silver_points
    for point in all_points:
        point_lower = _normalize_text(point)
        # Check if any strength keyword appears in both point and profile
        for keyword in STRENGTH_KEYWORDS:
            if keyword in point_lower and _check_keyword_match(keyword, profile_lower):
                # Avoid duplicates
                point_summary = point[:60] + "..." if len(point) > 60 else point
                strength_desc = f"Matches key requirement: {point_summary}"
                if strength_desc not in strengths:
                    strengths.append(strength_desc)
                    break
    
    # Limit to MAX_ITEMS
    return strengths[:MAX_ITEMS]


def _find_gaps(
    jd_summary: JobJDSummary,
    candidate_profile: str,
    profile_id: Optional[str] = None,
) -> List[str]:
    """
    Identify gaps by finding JD requirements that are missing from candidate profile.
    
    Args:
        jd_summary: Job JD summary with gold/silver points and core skills
        candidate_profile: Candidate profile text
        profile_id: Optional profile identifier (e.g., "data_engineer_gcp")
        
    Returns:
        List of gap descriptions
    """
    gaps = []
    profile_lower = _normalize_text(candidate_profile)
    
    # Get always-strength keywords for this profile
    always_strengths = PROFILE_ALWAYS_STRENGTHS.get(profile_id or "", set())
    if profile_id:
        logger.debug(f"Using profile_id: {profile_id}, always_strengths: {always_strengths}")
    
    # Collect all JD text
    all_jd_text = " ".join(
        jd_summary.gold_points + 
        jd_summary.silver_points + 
        jd_summary.core_skills +
        jd_summary.nice_to_have_skills
    )
    jd_text_lower = _normalize_text(all_jd_text)
    
    # Check for gap keywords that appear in JD but not in profile
    for gap_keyword in GAP_KEYWORDS:
        gap_lower = _normalize_text(gap_keyword)
        # If keyword appears in JD
        if gap_lower in jd_text_lower:
            # But not in profile (or very weakly mentioned)
            if not _check_keyword_match(gap_keyword, profile_lower):
                # Find the context where it appears
                for point in jd_summary.gold_points + jd_summary.silver_points:
                    if gap_lower in _normalize_text(point):
                        point_summary = point[:60] + "..." if len(point) > 60 else point
                        gap_desc = f"Missing: {gap_keyword} (mentioned in: {point_summary})"
                        if gap_desc not in gaps:
                            gaps.append(gap_desc)
                            break
    
    # Also check for skills in core_skills that don't match profile
    for skill in jd_summary.core_skills:
        skill_lower = _normalize_text(skill)
        
        # CRITICAL: Check if this skill is in the always-strengths whitelist
        # If so, NEVER mark it as a gap, even if it doesn't appear in profile text
        # (the profile claims it, so we trust that)
        is_always_strength = False
        if always_strengths:  # Only check if we have a whitelist for this profile
            for always_kw in always_strengths:
                # Normalize both for comparison (handle underscores vs spaces, case insensitive)
                always_kw_normalized = always_kw.lower().replace("_", " ").replace("-", " ").strip()
                skill_normalized = skill_lower.replace("_", " ").replace("-", " ").strip()
                # Check if they match (either contains the other, or exact match after normalization)
                # Also check original forms in case normalization loses information
                if (always_kw_normalized in skill_normalized or 
                    skill_normalized in always_kw_normalized or
                    always_kw_normalized == skill_normalized or
                    always_kw.lower() in skill_lower or
                    skill_lower in always_kw.lower()):
                    is_always_strength = True
                    logger.debug(f"Skill '{skill}' matches whitelist keyword '{always_kw}' for profile {profile_id}")
                    break
        
        if is_always_strength:
            # This skill should never be a gap for this profile
            logger.debug(f"Skipping gap check for whitelisted skill: {skill} (profile_id: {profile_id})")
            continue
        
        # Check if it's a gap keyword
        is_gap = False
        for gap_keyword in GAP_KEYWORDS:
            if gap_keyword in skill_lower or skill_lower in gap_keyword:
                if not _check_keyword_match(skill, profile_lower):
                    is_gap = True
                    break
        
        # Also check if it's not a strength keyword (might be a gap)
        if not is_gap:
            is_strength = False
            for strength_keyword in STRENGTH_KEYWORDS:
                if strength_keyword in skill_lower or skill_lower in strength_keyword:
                    is_strength = True
                    break
            # If it's neither a known strength nor gap, but appears in JD core skills
            # and not in profile, it might be a gap
            if not is_strength and not _check_keyword_match(skill, profile_lower):
                # Only add if it's a substantial skill (not too generic)
                if len(skill) > 3 and skill not in ["api", "ui", "ux", "web"]:
                    gaps.append(f"Missing core skill: {skill}")
    
    # Limit to MAX_ITEMS
    return gaps[:MAX_ITEMS]


def _generate_recommendation(
    jd_summary: JobJDSummary,
    candidate_profile: str,
    strengths: List[str],
    gaps: List[str],
) -> Literal["APPLY", "MAYBE", "SKIP"]:
    """
    Generate personalized recommendation based on strengths and gaps.
    
    Args:
        jd_summary: Job JD summary
        candidate_profile: Candidate profile text
        strengths: List of identified strengths
        gaps: List of identified gaps
        candidate_profile: Candidate profile text
        
    Returns:
        Recommendation: APPLY, MAYBE, or SKIP
    """
    profile_lower = _normalize_text(candidate_profile)
    
    # Check for strong negative signals
    jd_text = " ".join(
        jd_summary.gold_points + 
        jd_summary.silver_points +
        jd_summary.risks_or_red_flags
    ).lower()
    
    # If JD heavily emphasizes customer-facing/sales/advocacy and profile doesn't
    customer_facing_keywords = ["customer-facing", "sales", "business development", "advocacy", "public speaking"]
    jd_has_customer_focus = any(kw in jd_text for kw in customer_facing_keywords)
    profile_has_customer_focus = any(kw in profile_lower for kw in customer_facing_keywords)
    
    if jd_has_customer_focus and not profile_has_customer_focus:
        # Check if it's a major focus (appears multiple times)
        customer_focus_count = sum(jd_text.count(kw) for kw in customer_facing_keywords)
        if customer_focus_count >= 2:
            return "SKIP"
        else:
            return "MAYBE"
    
    # Check for travel/on-site requirements
    travel_keywords = ["extensive travel", "travel required", "full-time on-site", "on-site only"]
    if any(kw in jd_text for kw in travel_keywords):
        if "remote" not in profile_lower or "remote-friendly" not in profile_lower:
            # Profile doesn't emphasize remote preference, might be OK
            pass
        else:
            # Profile emphasizes remote, but JD requires travel/on-site
            return "MAYBE"
    
    # Count matches vs gaps
    strength_count = len(strengths)
    gap_count = len(gaps)
    
    # If most gold/silver points match, recommend APPLY
    total_key_points = len(jd_summary.gold_points) + len(jd_summary.silver_points)
    if total_key_points > 0:
        match_ratio = strength_count / max(total_key_points, 1)
        if match_ratio >= 0.6 and gap_count <= 1:
            return "APPLY"
        elif match_ratio >= 0.4 and gap_count <= 2:
            return "MAYBE"
        else:
            return "MAYBE"  # Default to MAYBE if unclear
    
    # Fallback: use original JD recommendation if available
    if jd_summary.recommendation in ["APPLY", "MAYBE", "SKIP"]:
        # Adjust based on our analysis
        if strength_count >= 2 and gap_count <= 1:
            return "APPLY"
        elif gap_count >= 3:
            return "SKIP"
        else:
            return jd_summary.recommendation
    
    return "MAYBE"


def _generate_action_items(gaps: List[str]) -> List[str]:
    """
    Generate actionable next steps based on identified gaps.
    
    Args:
        gaps: List of gap descriptions
        
    Returns:
        List of 2-5 action items
    """
    action_items = []
    gap_text_lower = " ".join(gaps).lower()
    
    # Map gaps to actions
    for gap_keyword, action_template in GAP_TO_ACTION.items():
        if gap_keyword in gap_text_lower:
            if action_template not in action_items:
                action_items.append(action_template)
    
    # If no specific actions found, add generic ones
    if not action_items:
        if "customer" in gap_text_lower or "sales" in gap_text_lower:
            action_items.append("Prepare 1-2 stories about working with business/customers, emphasizing business value of technical solutions")
        if "training" in gap_text_lower or "model" in gap_text_lower:
            action_items.append("Build a small-scale pretraining/finetuning side project and add it to your resume")
        if "on-call" in gap_text_lower or "oncall" in gap_text_lower:
            action_items.append("Highlight existing SRE/incident handling experience and document on-call best practices")
    
    # If still no actions, add a generic one
    if not action_items:
        action_items.append("Prepare relevant technical case studies or project experience descriptions for key gaps")
    
    # Limit to 2-5 items
    return action_items[:5]


def analyze_job_fit(
    jd_summary: JobJDSummary,
    candidate_profile: str,
    profile_id: Optional[str] = None,
) -> JobFitSummary:
    """
    Analyze how well a job description fits a candidate profile.
    
    This function compares the JD summary (gold/silver/bronze points, core skills)
    against the candidate profile to identify:
    - Strengths: Points where the candidate matches well
    - Gaps: Key requirements missing from the candidate profile
    - Action items: Next steps to address gaps
    
    Args:
        jd_summary: Job JD summary from the interpreter
        candidate_profile: Candidate profile text
        profile_id: Optional profile identifier (e.g., "data_engineer_gcp", "llm_agent")
                    Used to apply profile-specific rules (e.g., always-strength whitelists)
        
    Returns:
        JobFitSummary with personalized analysis
        
    Example:
        >>> from services.fiqa_api.jobhunter.jd_interpreter import interpret_job_jd
        >>> from services.fiqa_api.jobhunter.job_fit_analyzer import analyze_job_fit
        >>> 
        >>> jd = JobJDInput(description="...", candidate_profile="...")
        >>> summary = interpret_job_jd(jd)
        >>> fit = analyze_job_fit(summary, candidate_profile_text, profile_id="data_engineer_gcp")
        >>> print(fit.recommendation_for_candidate)
        'APPLY'
    """
    if not candidate_profile or not candidate_profile.strip():
        logger.warning("Empty candidate profile provided, returning default fit summary")
        return JobFitSummary(
            recommendation_for_candidate="MAYBE",
            strengths=[],
            gaps=[],
            action_items=["Provide candidate profile to get personalized fit analysis"],
        )
    
    # Find strengths and gaps (pass profile_id for profile-specific rules)
    strengths = _find_strengths(jd_summary, candidate_profile, profile_id=profile_id)
    gaps = _find_gaps(jd_summary, candidate_profile, profile_id=profile_id)
    
    # Generate recommendation
    recommendation = _generate_recommendation(jd_summary, candidate_profile, strengths, gaps)
    
    # Generate action items
    action_items = _generate_action_items(gaps)
    
    return JobFitSummary(
        recommendation_for_candidate=recommendation,
        strengths=strengths,
        gaps=gaps,
        action_items=action_items,
    )

