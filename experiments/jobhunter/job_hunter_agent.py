#!/usr/bin/env python3
"""
job_hunter_agent.py - LLM-based scoring and classification for job postings.
============================================================================

This script:

- Loads normalized job postings (JobPosting) from a JSON file.
- Uses an LLM to classify each job into A/B/C categories, assign scores, and generate explanations.
- Saves results (JobPosting + JobScore) into a scored JSON file.

Usage:
    python -m experiments.jobhunter.job_hunter_agent
    python -m experiments.jobhunter.job_hunter_agent --input-file data/jobhunter/normalized/jobs_20250310.json
    python -m experiments.jobhunter.job_hunter_agent --input-file data/jobhunter/normalized/jobs_20250310.json --limit 100
"""

import sys
import json
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Iterable

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.jobhunter.schemas import JobPosting, JobScore
from services.fiqa_api.clients import get_openai_client
from pydantic import ValidationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Default model for scoring
DEFAULT_MODEL = "gpt-4o-mini"

# Maximum description length to send to LLM (to avoid token limits)
MAX_DESC_CHARS = 4000

# Delay between API requests to reduce rate limit issues
REQUEST_SLEEP_SECONDS = 0.2


def load_job_postings(path: Path) -> List[JobPosting]:
    """
    Load job postings from a JSON file.
    
    Args:
        path: Path to the normalized jobs JSON file
        
    Returns:
        List of JobPosting instances
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file contains invalid data
    """
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    logger.info(f"Loading job postings from {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of job postings, got {type(data)}")
    
    postings = []
    for idx, item in enumerate(data):
        try:
            posting = JobPosting.model_validate(item)
            postings.append(posting)
        except ValidationError as e:
            logger.warning(f"Failed to validate job at index {idx}: {e}")
            continue
        except Exception as e:
            logger.warning(f"Unexpected error parsing job at index {idx}: {e}")
            continue
    
    logger.info(f"Loaded {len(postings)} job postings")
    return postings


def is_recent_job(job: JobPosting, max_age_days: int) -> bool:
    """
    Return True if the job is considered recent enough based on created_at/updated_at.
    
    - Prefer updated_at if available, otherwise fallback to created_at.
    - If both are missing or cannot be parsed, treat as NOT recent (return False).
    
    Args:
        job: JobPosting instance to check
        max_age_days: Maximum age in days (if <= 0, returns True for all jobs)
        
    Returns:
        True if the job is recent enough, False otherwise
    """
    if max_age_days <= 0:
        # No filtering requested
        return True
    
    ref_str = job.updated_at or job.created_at
    if not ref_str:
        return False
    
    try:
        # Greenhouse timestamps are usually ISO 8601, e.g. "2025-03-10T12:34:56Z"
        # Use fromisoformat with some normalization if needed.
        # If there is a trailing 'Z', replace it with '+00:00' to be ISO-compatible.
        ts_str = ref_str.replace("Z", "+00:00")
        ts = datetime.fromisoformat(ts_str)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except Exception:
        return False
    
    now = datetime.now(timezone.utc)
    age = now - ts
    return age <= timedelta(days=max_age_days)


def _normalize_list_arg(arg: str) -> list[str]:
    """
    Split a comma-separated CLI argument into a list of lowercased, stripped strings.
    
    Empty or whitespace-only entries are removed.
    
    Args:
        arg: Comma-separated string argument
        
    Returns:
        List of normalized strings (lowercased, stripped, non-empty)
    """
    if not arg:
        return []
    parts = [p.strip().lower() for p in arg.split(",")]
    return [p for p in parts if p]


def job_matches_company_filter(job: JobPosting, companies: Iterable[str]) -> bool:
    """
    Return True if the job's company matches any of the provided company filters.
    
    Matching is case-insensitive and uses substring match.
    If companies is empty, always return True.
    
    Args:
        job: JobPosting instance to check
        companies: Iterable of company names/slugs to match against
        
    Returns:
        True if the job matches any company filter, or if companies is empty
    """
    companies = list(companies)
    if not companies:
        return True
    
    company_name = (job.company or "").lower()
    return any(c in company_name for c in companies)


def get_keyword_preset(name: str) -> list[str]:
    """
    Return a list of preset keywords for the given preset name.
    
    Presets are intended to capture typical phrases in high-value roles:
    - 'llm_core': LLM / agent / RAG / applied AI roles
    - 'data_ml_platform': data / ML / platform / infra roles
    
    Matching is still done via job_matches_keyword_filter (case-insensitive substring).
    
    Args:
        name: Preset name (e.g., 'llm_core', 'data_ml_platform')
        
    Returns:
        List of keywords for the preset, or empty list if preset is unknown
    """
    if not name:
        return []
    
    name = name.strip().lower()
    
    if name == "llm_core":
        return [
            "llm",
            "large language model",
            "agent",
            "agentic",
            "rag",
            "retrieval-augmented",
            "ai engineer",
            "ml engineer",
            "applied scientist",
            "applied ai",
            "research engineer",
            "knowledge graph",
            "reasoning",
        ]
    
    if name == "data_ml_platform":
        return [
            "data platform",
            "data infrastructure",
            "ml platform",
            "ml infrastructure",
            "machine learning platform",
            "ml ops",
            "mlops",
            "feature store",
            "recommendation",
            "ranking",
            "search relevance",
            "search infrastructure",
            "distributed systems",
        ]
    
    # Unknown preset → no extra keywords
    return []


def job_matches_location_filter(job: JobPosting, location_filters: Iterable[str]) -> bool:
    """
    Return True if the job's location matches any of the given filters.
    
    Matching is done via case-insensitive substring match on the 'location' field.
    If no filters are provided, this function always returns True.
    
    Args:
        job: JobPosting instance to check
        location_filters: Iterable of location substrings to match against
        
    Returns:
        True if the job matches any location filter, or if location_filters is empty
    """
    location_filters = list(location_filters)
    if not location_filters:
        return True
    
    location = (job.location or "").strip().lower()
    if not location:
        # If we care about location and there is none, treat as non-match
        return False
    
    for pattern in location_filters:
        if pattern in location:
            return True
    return False


def job_matches_keyword_filter(job: JobPosting, keywords: Iterable[str]) -> bool:
    """
    Return True if the job's title or description contains any of the keywords.
    
    Matching is case-insensitive and uses substring match.
    If keywords is empty, always return True.
    
    Args:
        job: JobPosting instance to check
        keywords: Iterable of keywords to search for
        
    Returns:
        True if the job matches any keyword filter, or if keywords is empty
    """
    keywords = list(keywords)
    if not keywords:
        return True
    
    title = (job.title or "").lower()
    desc = (job.description or "").lower()
    text = f"{title}\n{desc}"
    return any(k in text for k in keywords)


def truncate_description(description: str, max_length: int = MAX_DESC_CHARS) -> str:
    """
    Truncate job description to avoid token limits.
    
    Args:
        description: Full job description
        max_length: Maximum length in characters
        
    Returns:
        Truncated description with ellipsis if needed
    """
    if not description:
        return ""
    
    if len(description) <= max_length:
        return description
    
    # Truncate to max_length and add indicator
    return description[:max_length] + "\n\n...[truncated]..."


def score_job_with_llm(
    client,
    job: JobPosting,
    model: str = DEFAULT_MODEL,
    timeout: float = 30.0,
) -> Optional[JobScore]:
    """
    Score a single job posting using an LLM.
    
    Args:
        client: OpenAI client instance
        job: JobPosting to score
        model: Model name to use
        timeout: Timeout in seconds for the API call
        
    Returns:
        JobScore instance on success, None on error (timeout, API error, parsing error, etc.)
    """
    # System prompt describing the candidate profile
    system_prompt = """You are helping a senior AI/ML/LLM engineer decide which jobs to prioritize.

The candidate:
- Has many years of experience in backend, data engineering, and cloud (GCP).
- Recently built production-style LLM/RAG/agent systems with LangGraph, evaluation, observability, and coding agents.
- Strong in: Python, backend, data engineering, cloud (GCP), RAG, LangGraph/agentic systems, observability, evaluation, coding agents.
- Wants high-impact roles focused on LLMs, agents, retrieval, and system design, not low-level CRUD work.

Your job is to classify job postings into:
- A: Strong match and high priority. The role aligns well with the candidate's experience in LLM/agent systems, backend/data engineering, and the tech stack matches.
- B: Relevant but not ideal. There's some alignment (e.g., related domain or tech stack), but there may be mismatches in seniority, focus area, or specific requirements.
- C: Not a good fit. The role is too junior, mostly front-end focused, not really about LLM/agents, or requires skills/experience the candidate doesn't have.

For each job, provide:
1. A category (A, B, or C)
2. A match_score (1-10): Overall how well the job matches the candidate's profile
3. A seniority_score (1-10): How well the seniority level matches (10 = perfect match, 1 = way too junior/senior)
4. A compensation_tier: "low", "mid", "high", or "unknown" based on the job description and company
5. A brief explanation (reasons) for the classification
6. A talk_track: A short paragraph suggesting how the candidate should talk about their experience and projects for this job

Return your response as a JSON object with these exact fields."""
    
    # Truncate job description before building prompt to keep prompt size reasonable
    desc = job.description or ""
    if len(desc) > MAX_DESC_CHARS:
        truncated_description = desc[:MAX_DESC_CHARS] + "\n\n...[truncated]..."
    else:
        truncated_description = desc
    
    user_prompt = f"""Evaluate this job posting:

Title: {job.title}
Company: {job.company}
Location: {job.location or 'Not specified'}
Source: {job.source}
URL: {job.url}
Department: {job.department or 'Not specified'}

Description:
{truncated_description}

Return a JSON object with the following fields:
- category: "A", "B", or "C"
- match_score: integer from 1 to 10
- seniority_score: integer from 1 to 10
- compensation_tier: one of "low", "mid", "high", "unknown"
- reasons: short explanation (2-3 sentences)
- talk_track: a short paragraph suggesting how the candidate should talk about their experience and projects for this job"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            timeout=timeout,
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
        
        data = json.loads(content)
        
        # Validate and create JobScore
        score = JobScore(
            job_id=job.job_id,
            category=data["category"],
            match_score=data["match_score"],
            seniority_score=data["seniority_score"],
            compensation_tier=data["compensation_tier"],
            reasons=data["reasons"],
            talk_track=data["talk_track"],
            raw_llm_output=data,
        )
        
        return score
        
    except json.JSONDecodeError as e:
        logger.warning("Failed to score job %s: JSON decode error: %s", job.job_id, e)
        if 'content' in locals():
            logger.debug("Raw response: %s", content[:500])
        return None
    
    except ValidationError as e:
        logger.warning("Failed to score job %s: Validation error: %s", job.job_id, e)
        return None
    
    except Exception as e:
        logger.warning("Failed to score job %s: %s", job.job_id, e)
        return None


def run_job_hunter(
    company_filters: list[str],
    keyword_preset: str,
    keyword_filters: list[str],
    location_filters: list[str],
    max_age_days: int,
    limit: Optional[int],
    output_file: Path,
    input_file: Optional[Path] = None,
    model: str = DEFAULT_MODEL,
) -> None:
    """
    Run the job hunter scoring pipeline programmatically.
    
    Args:
        company_filters: List of company names/slugs to filter by
        keyword_preset: Keyword preset name ('llm_core', 'data_ml_platform', or empty)
        keyword_filters: Additional manual keywords to filter by
        location_filters: List of location substrings to filter by
        max_age_days: Maximum age in days for jobs (0 = no filter)
        limit: Maximum number of jobs to score (None = no limit)
        output_file: Path to save scored jobs JSON
        input_file: Path to normalized jobs JSON (None = use today's default)
        model: OpenAI model to use for scoring
    """
    # Get current date string for defaults
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Determine input path
    if input_file is None:
        input_path = project_root / "data" / "jobhunter" / "normalized" / f"jobs_{date_str}.json"
    else:
        input_path = input_file
    
    # Load job postings
    try:
        jobs = load_job_postings(input_path)
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load job postings: {e}")
        raise
    
    if not jobs:
        logger.error("No job postings loaded")
        raise ValueError("No job postings loaded")
    
    # Apply recency filter if specified
    if max_age_days > 0:
        original_count = len(jobs)
        jobs = [job for job in jobs if is_recent_job(job, max_age_days)]
        logger.info(
            "Filtered jobs by max_age_days=%d: %d -> %d",
            max_age_days,
            original_count,
            len(jobs),
        )
    
    if not jobs:
        logger.warning("No jobs found after applying recency filter. Nothing to score.")
        return
    
    # Apply cheap pre-filters (company + location + keyword) before LLM scoring
    if location_filters:
        logger.info("Using location filters: %s", location_filters)
    
    # Extend keyword filters with preset, if any
    preset_keywords = get_keyword_preset(keyword_preset)
    if preset_keywords:
        # We want a simple union: original + preset, all lowercased
        keyword_filters = list(dict.fromkeys(keyword_filters + [k.lower() for k in preset_keywords]))
        logger.info(
            "Keyword preset '%s' applied. Total keywords: %d",
            keyword_preset,
            len(keyword_filters),
        )
    else:
        if keyword_preset:
            logger.warning(
                "Unknown keyword preset '%s' (no extra keywords applied).",
                keyword_preset,
            )
    
    filtered_jobs: list[JobPosting] = []
    for job in jobs:
        # Company filter
        if company_filters and not job_matches_company_filter(job, company_filters):
            continue
        # Location filter
        if location_filters and not job_matches_location_filter(job, location_filters):
            continue
        # Keyword filter
        if keyword_filters and not job_matches_keyword_filter(job, keyword_filters):
            continue
        filtered_jobs.append(job)
    
    logger.info(
        "Jobs after company/location/keyword filtering: %d -> %d",
        len(jobs),
        len(filtered_jobs),
    )
    jobs = filtered_jobs
    
    if not jobs:
        logger.warning("No jobs left after recency + company/location/keyword filtering. Nothing to score.")
        return
    
    # Apply limit if specified (after recency and company/keyword filters)
    if limit and limit > 0:
        jobs = jobs[:limit]
        logger.info(f"Limited to first {len(jobs)} jobs")
    
    # Get OpenAI client
    client = get_openai_client()
    if client is None:
        logger.error("Failed to get OpenAI client. Make sure OPENAI_API_KEY is set.")
        raise RuntimeError("Failed to get OpenAI client. Make sure OPENAI_API_KEY is set.")
    
    logger.info(f"Scoring {len(jobs)} jobs using model {model}")
    
    # Score each job
    results = []
    category_counts = {"A": 0, "B": 0, "C": 0}
    success_count = 0
    error_count = 0
    
    for idx, job in enumerate(jobs, 1):
        logger.info(f"Scoring job {idx}/{len(jobs)}: {job.job_id} - {job.title} at {job.company}")
        
        score = score_job_with_llm(client, job, model=model)
        
        if score is not None:
            category_counts[score.category] += 1
            success_count += 1
            
            results.append({
                "job": job.model_dump(),
                "score": score.model_dump(),
            })
            
            logger.info(f"  → Category: {score.category}, Match: {score.match_score}/10, Seniority: {score.seniority_score}/10")
        else:
            error_count += 1
            logger.warning(f"  → Skipped (no score due to LLM/API error)")
        
        # Small delay between requests to reduce rate limit issues
        time.sleep(REQUEST_SLEEP_SECONDS)
    
    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving results to {output_file}")
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("Summary:")
    logger.info(f"  Total jobs considered: {len(jobs)}")
    logger.info(f"  Successfully scored: {success_count}")
    logger.info(f"  Errors (skipped): {error_count}")
    logger.info(f"  Category A (strong match): {category_counts['A']}")
    logger.info(f"  Category B (related): {category_counts['B']}")
    logger.info(f"  Category C (not a fit): {category_counts['C']}")
    logger.info(f"  Output file: {output_file}")
    logger.info("=" * 60)
    logger.info("Done")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Score and classify job postings using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m experiments.jobhunter.job_hunter_agent
  python -m experiments.jobhunter.job_hunter_agent --input-file data/jobhunter/normalized/jobs_20250310.json
  python -m experiments.jobhunter.job_hunter_agent --input-file data/jobhunter/normalized/jobs_20250310.json --limit 100
  python -m experiments.jobhunter.job_hunter_agent --company-filter anthropic,databricks --max-age-days 45
  python -m experiments.jobhunter.job_hunter_agent --keyword-filter "llm,agent,rag,ai engineer" --max-age-days 45
  python -m experiments.jobhunter.job_hunter_agent --company-filter anthropic,databricks --keyword-filter "llm,agent,rag" --max-age-days 45 --limit 100
  python -m experiments.jobhunter.job_hunter_agent --company-filter anthropic,databricks --keyword-preset llm_core --max-age-days 45 --limit 50
  python -m experiments.jobhunter.job_hunter_agent --company-filter anthropic,databricks --keyword-preset data_ml_platform --max-age-days 45 --limit 50
  python -m experiments.jobhunter.job_hunter_agent --company-filter anthropic,databricks --keyword-filter "ai architect" --keyword-preset llm_core --max-age-days 45 --limit 50
  python -m experiments.jobhunter.job_hunter_agent --company-filter anthropic,databricks --keyword-preset data_ml_platform --location-filter "San Francisco,New York,Seattle,United States,Remote (US)" --max-age-days 45 --limit 50
        """,
    )
    
    # Get current date string for defaults
    date_str = datetime.now().strftime("%Y%m%d")
    
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help=f"Input JSON file with normalized jobs (default: data/jobhunter/normalized/jobs_{date_str}.json)",
    )
    
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help=f"Output JSON file for scored jobs (default: data/jobhunter/scored/jobs_scored_{date_str}.json)",
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of jobs to score (useful for testing, default: score all)",
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use (default: {DEFAULT_MODEL})",
    )
    
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=45,
        help="Maximum age (in days) for job postings to be considered. Older jobs are skipped.",
    )
    
    parser.add_argument(
        "--company-filter",
        type=str,
        default="",
        help=(
            "Optional comma-separated list of company names or slugs to keep. "
            "If provided, only jobs whose company matches (case-insensitive, substring) are kept."
        ),
    )
    
    parser.add_argument(
        "--keyword-filter",
        type=str,
        default="",
        help=(
            "Optional comma-separated list of keywords to filter jobs by. "
            "Keywords are matched (case-insensitive) against title and description."
        ),
    )
    
    parser.add_argument(
        "--keyword-preset",
        type=str,
        default="",
        help=(
            "Optional keyword preset to extend keyword filtering. "
            "Supported values: 'llm_core', 'data_ml_platform'. "
            "If provided, preset keywords are added on top of --keyword-filter."
        ),
    )
    
    parser.add_argument(
        "--location-filter",
        type=str,
        default="",
        help=(
            "Optional comma-separated list of substrings to filter job locations. "
            "Only jobs whose location contains at least one of these (case-insensitive) "
            "will be kept. Example: 'San Francisco,New York,Seattle,United States,Remote (US)'."
        ),
    )
    
    args = parser.parse_args()
    
    # Determine input and output paths
    if args.input_file:
        input_path = project_root / args.input_file
    else:
        input_path = None
    
    if args.output_file:
        output_path = project_root / args.output_file
    else:
        output_path = project_root / "data" / "jobhunter" / "scored" / f"jobs_scored_{date_str}.json"
    
    # Parse filters
    company_filters = _normalize_list_arg(args.company_filter)
    keyword_filters = _normalize_list_arg(args.keyword_filter)
    location_filters = _normalize_list_arg(args.location_filter)
    
    # Call the helper function
    try:
        run_job_hunter(
            company_filters=company_filters,
            keyword_preset=args.keyword_preset,
            keyword_filters=keyword_filters,
            location_filters=location_filters,
            max_age_days=args.max_age_days,
            limit=args.limit,
            output_file=output_path,
            input_file=input_path,
            model=args.model,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
