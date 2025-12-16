#!/usr/bin/env python3
"""
langchain_demo.py - LangChain demo for extracting personalized preferences from JobHunter jobs.
==============================================================================================

This script demonstrates using LangChain to analyze scored jobs and extract:
- Preference score (1-5)
- Top 3 reasons why you might like/dislike the job
- Keywords that describe the job

The script generates a comparison report showing three types of scores:
1. match_score: LLM-based hard matching score (1-10) from the JobHunter agent
2. model_preference_score: LangChain chain's soft preference analysis (1-5)
3. user_rating: Manual human rating (1-5) stored in preferences.json

This is a mini-RLHF / preference modeling demo: the model gives a second-opinion 
preference score, while human ratings serve as the final ground truth for 
comparing model vs human preferences and extracting per-job rationales.

Usage:
    python3 -m experiments.jobhunter.langchain_demo \
      --scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
      --top-k 10 \
      --output-file reports/jobhunter/langchain_prefs_demo_latest.md

Interview Summary:
    I built a small LangChain-based preference analysis pipeline on top of my 
    JobHunter agent to compare model vs human preferences and extract per-job 
    rationales. The pipeline analyzes high-scoring jobs and generates a report 
    that contrasts the LLM's match_score, the LangChain chain's preference_score, 
    and my own manual ratings to understand alignment and discrepancies.
"""

import sys
import json
import argparse
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from services.fiqa_api.clients import get_openai_client
from services.fiqa_api.jobhunter.preferences_store import load_preferences
from services.fiqa_api.jobhunter.schemas import JobPreferenceRecord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Default model
DEFAULT_MODEL = "gpt-4o-mini"

# Maximum description length to send to LLM
MAX_DESC_CHARS = 3000


def find_default_scored_file() -> Optional[Path]:
    """
    Find the default scored file (jobs_scored_data_ml_platform_latest.json).
    
    Returns:
        Path to the file if found, None otherwise
    """
    scored_dir = project_root / "data" / "jobhunter" / "scored"
    if not scored_dir.exists():
        return None
    
    # Look for jobs_scored_data_ml_platform_latest.json
    default_file = scored_dir / "jobs_scored_data_ml_platform_latest.json"
    if default_file.exists():
        return default_file
    
    # Fallback: find any *_latest.json file
    latest_files = list(scored_dir.glob("*_latest.json"))
    if latest_files:
        # Sort by modification time, return most recent
        latest_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return latest_files[0]
    
    return None


def load_user_preferences() -> Dict[str, JobPreferenceRecord]:
    """
    Load user preferences from preferences.json.
    
    Returns:
        Dictionary mapping job_id to JobPreferenceRecord
    """
    prefs = load_preferences()
    logger.info(f"Loaded {len(prefs)} user preference records")
    return prefs


def select_jobs_to_analyze(
    jobs: List[Dict[str, Any]],
    prefs: Dict[str, JobPreferenceRecord],
    top_k: int = 10,
    only_rated: bool = True,
) -> List[Dict[str, Any]]:
    """
    Select jobs to analyze based on filtering criteria.
    
    Strategy:
    - Only keep jobs with category == "A" and match_score >= 8
    - If only_rated=True, further filter to jobs that have user_rating in prefs
    - Sort by match_score (descending)
    - Take top_k jobs
    
    Args:
        jobs: List of scored job items (with 'job' and 'score' keys)
        prefs: Dictionary mapping job_id to JobPreferenceRecord
        top_k: Maximum number of jobs to return
        only_rated: If True, only include jobs that have been manually rated
        
    Returns:
        Filtered and sorted list of job items
    """
    # Filter: category == "A" and match_score >= 8
    filtered = []
    for job_item in jobs:
        score = job_item.get("score", {})
        category = score.get("category", "")
        match_score = score.get("match_score", 0)
        
        if category == "A" and match_score >= 8:
            filtered.append(job_item)
    
    logger.info(f"After filtering (category=A, match_score>=8): {len(filtered)} jobs")
    
    # If only_rated=True, further filter to jobs with user_rating
    if only_rated:
        rated_jobs = []
        for job_item in filtered:
            job = job_item.get("job", {})
            job_id = job.get("job_id", "")
            if job_id in prefs:
                rated_jobs.append(job_item)
        filtered = rated_jobs
        logger.info(f"After filtering to rated jobs only: {len(filtered)} jobs")
    
    # Sort by match_score (descending)
    filtered.sort(
        key=lambda x: (
            -x.get("score", {}).get("match_score", 0),
            -x.get("score", {}).get("seniority_score", 0),
        )
    )
    
    # Take top_k
    result = filtered[:top_k]
    logger.info(f"Selected top {len(result)} jobs for analysis")
    
    return result


def load_scored_jobs(path: Path) -> List[Dict[str, Any]]:
    """
    Load scored jobs from a JSON file.
    
    Args:
        path: Path to the scored jobs JSON file
        
    Returns:
        List of scored job dictionaries
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file contains invalid data
    """
    if not path.exists():
        raise FileNotFoundError(f"Scored jobs file not found: {path}")
    
    logger.info(f"Loading scored jobs from {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of scored jobs, got {type(data)}")
    
    logger.info(f"Loaded {len(data)} scored jobs")
    return data


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
    
    return description[:max_length] + "\n\n...[truncated]..."


def format_job_for_prompt(job_item: Dict[str, Any]) -> str:
    """
    Format a job item into a string for the LLM prompt.
    
    Args:
        job_item: Dictionary containing 'job' and 'score' keys
        
    Returns:
        Formatted string with job information
    """
    job = job_item.get("job", {})
    score = job_item.get("score", {})
    
    title = job.get("title", "Unknown Title")
    company = job.get("company", "Unknown Company")
    location = job.get("location") or "Not specified"
    description = truncate_description(job.get("description", ""))
    
    match_score = score.get("match_score", "?")
    seniority_score = score.get("seniority_score", "?")
    category = score.get("category", "?")
    why_shortlisted = score.get("reasons", "")
    
    formatted = f"""Job Information:
- Title: {title}
- Company: {company}
- Location: {location}
- Category: {category}
- Match Score: {match_score}/10
- Seniority Score: {seniority_score}/10
- Why Shortlisted: {why_shortlisted}

Job Description:
{description}"""
    
    return formatted


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM response to extract preference_score, keywords, and top_3_reasons.
    
    This function tries to extract structured data from the LLM output.
    It's lenient and will use defaults if parsing fails.
    
    Args:
        response_text: Raw text response from LLM
        
    Returns:
        Dictionary with preference_score, keywords, top_3_reasons, and raw_output
    """
    result = {
        "preference_score": 3,  # Default neutral score
        "keywords": [],
        "top_3_reasons": [],
        "raw_output": response_text,
    }
    
    # Try to extract preference_score (1-5)
    score_match = re.search(r'preference[_\s]*score[:\s]*(\d+)', response_text, re.IGNORECASE)
    if score_match:
        try:
            score = int(score_match.group(1))
            if 1 <= score <= 5:
                result["preference_score"] = score
        except ValueError:
            pass
    
    # Try to extract keywords (look for "keywords:" or "keywords" followed by a list)
    keywords_section = re.search(
        r'keywords?[:\s]*(?:\[|\n)?([^\n]+(?:,\s*[^\n]+)*)',
        response_text,
        re.IGNORECASE | re.MULTILINE
    )
    if keywords_section:
        keywords_text = keywords_section.group(1).strip()
        # Remove brackets and split by comma
        keywords_text = keywords_text.strip('[]')
        keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
        if keywords:
            result["keywords"] = keywords[:6]  # Limit to 6 keywords
    
    # Try to extract top_3_reasons (look for numbered list or bullet points)
    reasons = []
    # Pattern 1: Numbered list (1., 2., 3.)
    numbered_pattern = r'(?:reason|why)[:\s]*(?:\n)?(?:1[\.\)]\s*([^\n]+))(?:\n(?:2[\.\)]\s*([^\n]+)))?(?:\n(?:3[\.\)]\s*([^\n]+)))?'
    numbered_match = re.search(numbered_pattern, response_text, re.IGNORECASE | re.MULTILINE)
    if numbered_match:
        for group in numbered_match.groups():
            if group:
                reasons.append(group.strip())
    
    # Pattern 2: Bullet points (-, *, •)
    if not reasons:
        bullet_pattern = r'[-*•]\s*([^\n]+)'
        bullet_matches = re.findall(bullet_pattern, response_text)
        if bullet_matches:
            reasons = [m.strip() for m in bullet_matches[:3]]
    
    # Pattern 3: Look for "reasons:" section
    if not reasons:
        reasons_section = re.search(
            r'(?:top[_\s]*3[_\s]*)?reasons?[:\s]*(?:\n)?(.+?)(?:\n\n|\nkeywords|$)',
            response_text,
            re.IGNORECASE | re.DOTALL
        )
        if reasons_section:
            reasons_text = reasons_section.group(1).strip()
            # Split by newlines and take first 3 non-empty lines
            lines = [l.strip() for l in reasons_text.split('\n') if l.strip()]
            reasons = lines[:3]
    
    if reasons:
        result["top_3_reasons"] = reasons[:3]
    
    return result


def create_preference_chain(client: Any, model: str = DEFAULT_MODEL) -> Any:
    """
    Create a LangChain chain for analyzing job preferences.
    
    Args:
        client: OpenAI client instance
        model: OpenAI model name to use
        
    Returns:
        LangChain chain (prompt | llm_call | parse)
    """
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are helping analyze job postings to understand why someone might like or dislike them.

Given a job posting with its match score and why it was shortlisted, analyze it from a personal preference perspective.

Return your analysis in the following format:
- preference_score: A number from 1 to 5 (1 = would not like, 5 = would very much like)
- top_3_reasons: Three bullet points explaining why the person might like or dislike this job
- keywords: 3-6 keywords that describe what makes this job appealing or not (e.g., remote, infra, RLHF, K8s, LangGraph, high-comp, research-focused, etc.)

Be concise and focus on what would make someone personally interested or not interested in this role."""),
        ("user", "{job_info}")
    ])
    
    # Create LLM call function using existing OpenAI client
    def llm_call(prompt_value: Any) -> str:
        """Call OpenAI API and return content."""
        try:
            # Convert prompt value to messages format
            messages = prompt_value.to_messages()
            # Convert to OpenAI format
            openai_messages = []
            for msg in messages:
                # Map message types to OpenAI roles
                role_map = {
                    "system": "system",
                    "human": "user",
                    "ai": "assistant",
                }
                role = role_map.get(msg.type, "user")
                content = msg.content if hasattr(msg, "content") else str(msg)
                openai_messages.append({"role": role, "content": content})
            
            response = client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=0.3,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    # Create parsing function
    parse_fn = RunnableLambda(parse_llm_response)
    
    # Chain: prompt | llm_call | parse
    chain = prompt | RunnableLambda(llm_call) | parse_fn
    
    return chain


def analyze_job_with_chain(chain: Any, job_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Analyze a single job using the LangChain chain.
    
    Args:
        chain: LangChain chain for preference analysis
        job_item: Dictionary containing 'job' and 'score' keys
        
    Returns:
        Dictionary with analysis results, or None on error
    """
    try:
        job_info = format_job_for_prompt(job_item)
        result = chain.invoke({"job_info": job_info})
        return result
    except Exception as e:
        logger.warning(f"Failed to analyze job {job_item.get('job', {}).get('job_id', 'unknown')}: {e}")
        return None


def generate_markdown_report(
    jobs: List[Dict[str, Any]],
    analyses: List[Dict[str, Any]],
    prefs: Dict[str, JobPreferenceRecord],
    scored_file: Path,
    output_file: Path,
) -> str:
    """
    Generate a Markdown report from job analyses.
    
    Args:
        jobs: List of job items (with 'job' and 'score' keys)
        analyses: List of analysis results (one per job)
        scored_file: Path to the input scored file
        output_file: Path to the output report file
        
    Returns:
        Markdown report as string
    """
    lines = []
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines.append("# LangChain Preference Analysis Demo")
    lines.append("")
    lines.append(f"_Generated at: {now_str}_")
    lines.append(f"_Source file: {scored_file}_")
    lines.append(f"_Jobs analyzed: {len(jobs)}_")
    lines.append("")
    
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total jobs analyzed: **{len(jobs)}**")
    lines.append(f"- Successful analyses: **{sum(1 for a in analyses if a is not None)}**")
    lines.append("")
    
    # Summary table
    lines.append("### Summary Table")
    lines.append("")
    lines.append("| Job ID | Company | Title | Match Score | Model Pref | My Rating |")
    lines.append("|--------|---------|-------|-------------|------------|-----------|")
    
    for job_item, analysis in zip(jobs, analyses):
        job = job_item.get("job", {})
        score = job_item.get("score", {})
        
        job_id = job.get("job_id", "?")
        company = job.get("company", "?")
        title = job.get("title", "?")[:50]  # Truncate long titles
        match_score = score.get("match_score", "?")
        
        # Model preference score (from LangChain analysis)
        if analysis is not None:
            pref_score = analysis.get("preference_score", "-")
            if pref_score != "-":
                pref_score = f"{pref_score}/5"
        else:
            pref_score = "-"
        
        # User rating (from preferences)
        user_rating = "-"
        if job_id in prefs:
            user_rating = f"{prefs[job_id].user_rating}/5"
        
        lines.append(f"| {job_id} | {company} | {title} | {match_score}/10 | {pref_score} | {user_rating} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Detailed analysis for each job
    for idx, (job_item, analysis) in enumerate(zip(jobs, analyses), 1):
        job = job_item.get("job", {})
        score = job_item.get("score", {})
        
        title = job.get("title", "Unknown Title")
        company = job.get("company", "Unknown Company")
        location = job.get("location") or "Not specified"
        url = job.get("url", "")
        job_id = job.get("job_id", "?")
        
        match_score = score.get("match_score", "?")
        category = score.get("category", "?")
        
        lines.append(f"### {idx}. {title} — {company}")
        lines.append("")
        lines.append(f"- **Job ID:** {job_id}")
        lines.append(f"- **Location:** {location}")
        lines.append(f"- **Category:** {category}")
        lines.append(f"- **Match Score:** {match_score}/10")
        if url:
            lines.append(f"- **Link:** {url}")
        lines.append("")
        
        if analysis is None:
            lines.append("**Analysis:** Failed to analyze this job.")
            lines.append("")
            
            # Still show user rating even if analysis failed
            if job_id in prefs:
                lines.append(f"- **My Rating:** {prefs[job_id].user_rating}/5")
                lines.append("")
        else:
            pref_score = analysis.get("preference_score", "?")
            keywords = analysis.get("keywords", [])
            reasons = analysis.get("top_3_reasons", [])
            
            lines.append(f"- **Model Preference Score:** {pref_score}/5")
            
            # Show user rating
            if job_id in prefs:
                lines.append(f"- **My Rating:** {prefs[job_id].user_rating}/5")
            else:
                lines.append("- **My Rating:** (no manual rating yet)")
            
            lines.append("")
            
            if keywords:
                keywords_str = ", ".join(keywords)
                lines.append(f"- **Keywords:** {keywords_str}")
                lines.append("")
            
            if reasons:
                lines.append("**Top 3 Reasons:**")
                lines.append("")
                for reason in reasons:
                    lines.append(f"- {reason}")
                lines.append("")
            else:
                lines.append("**Reasons:** (Could not extract reasons from LLM response)")
                lines.append("")
            
            # Include raw output for debugging (collapsed in markdown)
            raw_output = analysis.get("raw_output", "")
            if raw_output:
                lines.append("<details>")
                lines.append("<summary>Raw LLM Output (for debugging)</summary>")
                lines.append("")
                lines.append("```")
                lines.append(raw_output)
                lines.append("```")
                lines.append("")
                lines.append("</details>")
                lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def print_preview_table(jobs: List[Dict[str, Any]], analyses: List[Dict[str, Any]]):
    """
    Print a simple preview table to the terminal.
    
    Args:
        jobs: List of job items
        analyses: List of analysis results
    """
    print("\n" + "=" * 80)
    print("Preview Table")
    print("=" * 80)
    print(f"{'Job ID':<15} {'Company':<20} {'Title':<40} {'Pref Score':<12}")
    print("-" * 80)
    
    for job_item, analysis in zip(jobs, analyses):
        if analysis is None:
            continue
        
        job = job_item.get("job", {})
        job_id = job.get("job_id", "?")
        company = job.get("company", "?")[:18]
        title = job.get("title", "?")[:38]
        pref_score = analysis.get("preference_score", "?")
        
        print(f"{job_id:<15} {company:<20} {title:<40} {pref_score}/5")
    
    print("=" * 80)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="LangChain demo for extracting personalized preferences from JobHunter jobs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 -m experiments.jobhunter.langchain_demo --top-k 3
  python3 -m experiments.jobhunter.langchain_demo \\
    --scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \\
    --top-k 10 \\
    --output-file reports/jobhunter/langchain_prefs_demo_latest.md
        """,
    )
    
    parser.add_argument(
        "--scored-file",
        type=str,
        default=None,
        help="Path to scored jobs JSON file (default: auto-find jobs_scored_data_ml_platform_latest.json)",
    )
    
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of top jobs to analyze (default: 10)",
    )
    
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Path to output Markdown report (default: reports/jobhunter/langchain_prefs_demo_YYYYMMDD.md)",
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use (default: {DEFAULT_MODEL})",
    )
    
    # Use a group to make --only-rated and --no-only-rated mutually exclusive
    # Default is True (only analyze rated jobs)
    parser.add_argument(
        "--only-rated",
        dest="only_rated",
        action="store_true",
        default=True,
        help="Only analyze jobs that have been manually rated (default: True). "
             "Use --no-only-rated to analyze all high-scoring jobs.",
    )
    
    parser.add_argument(
        "--no-only-rated",
        dest="only_rated",
        action="store_false",
        help="Analyze all high-scoring jobs, not just manually rated ones",
    )
    
    args = parser.parse_args()
    
    # Handle only_rated default: if neither flag was specified, default to True
    # (argparse will set it to None if both actions are defined but neither is used)
    if not hasattr(args, 'only_rated') or args.only_rated is None:
        args.only_rated = True
    
    # Determine input file
    if args.scored_file:
        scored_path = project_root / args.scored_file
    else:
        scored_path = find_default_scored_file()
        if scored_path is None:
            logger.error("Could not find default scored file. Please specify --scored-file")
            sys.exit(1)
    
    # Determine output file
    if args.output_file:
        output_path = project_root / args.output_file
    else:
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = project_root / "reports" / "jobhunter" / f"langchain_prefs_demo_{date_str}.md"
    
    # Load scored jobs
    try:
        all_jobs = load_scored_jobs(scored_path)
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load scored jobs: {e}")
        sys.exit(1)
    
    if not all_jobs:
        logger.error("No jobs found in the scored file")
        sys.exit(1)
    
    logger.info(f"Loaded {len(all_jobs)} total jobs from scored file")
    
    # Load user preferences
    try:
        prefs = load_user_preferences()
    except Exception as e:
        logger.warning(f"Failed to load user preferences: {e}. Continuing without preferences.")
        prefs = {}
    
    # Select jobs to analyze using the new filtering function
    top_jobs = select_jobs_to_analyze(
        all_jobs,
        prefs,
        top_k=args.top_k,
        only_rated=args.only_rated,
    )
    
    if not top_jobs:
        logger.error("No jobs selected for analysis. Try adjusting filters or --only-rated flag.")
        sys.exit(1)
    
    logger.info(f"Analyzing {len(top_jobs)} jobs")
    
    # Count how many have user_rating
    rated_count = sum(1 for job_item in top_jobs 
                     if job_item.get("job", {}).get("job_id", "") in prefs)
    logger.info(f"  - {rated_count} jobs have user_rating")
    
    # Get OpenAI client
    client = get_openai_client()
    if client is None:
        logger.error("Failed to get OpenAI client. Make sure OPENAI_API_KEY is set.")
        sys.exit(1)
    
    # Create LangChain chain
    try:
        chain = create_preference_chain(client, model=args.model)
        logger.info(f"Created LangChain chain with model {args.model}")
    except Exception as e:
        logger.error(f"Failed to create LangChain chain: {e}")
        sys.exit(1)
    
    # Analyze each job
    analyses = []
    for idx, job_item in enumerate(top_jobs, 1):
        job = job_item.get("job", {})
        job_id = job.get("job_id", "?")
        title = job.get("title", "?")
        company = job.get("company", "?")
        
        logger.info(f"Analyzing job {idx}/{len(top_jobs)}: {job_id} - {title} at {company}")
        
        analysis = analyze_job_with_chain(chain, job_item)
        analyses.append(analysis)
        
        if analysis:
            pref_score = analysis.get("preference_score", "?")
            logger.info(f"  → Preference score: {pref_score}/5")
    
    # Print preview table
    print_preview_table(top_jobs, analyses)
    
    # Generate and save report
    report_content = generate_markdown_report(top_jobs, analyses, prefs, scored_path, output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content, encoding="utf-8")
    
    logger.info(f"Report written to: {output_path}")
    logger.info("Done")


if __name__ == "__main__":
    main()
