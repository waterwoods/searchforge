#!/usr/bin/env python3

"""
job_hunter_report.py - Generate a human-readable shortlist report from scored jobs.

- Input: scored jobs JSON (output of job_hunter_agent.py)
- Filtering: keep only high-priority jobs (A and high-score B)
- Output: Markdown file with a shortlist of recommended jobs for manual review
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.jobhunter.preferences_store import load_preferences


def default_scored_path() -> Path:
    """Get default path for scored jobs file (today's date)."""
    today = datetime.now().strftime("%Y%m%d")
    return Path(f"data/jobhunter/scored/jobs_scored_{today}.json")


def default_report_path() -> Path:
    """Get default path for report file (today's date)."""
    today = datetime.now().strftime("%Y%m%d")
    return Path(f"reports/jobhunter/job_shortlist_{today}.md")


def load_scored_jobs(path: Path) -> List[Dict[str, Any]]:
    """Load scored jobs from a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Scored jobs file not found: {path}")
    
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("Expected a list of scored jobs (list of objects)")
    
    return data


def filter_scored_jobs(
    items: List[Dict[str, Any]],
    min_match_score: int,
    include_b: bool = True,
    use_preferences: bool = False,
) -> List[Dict[str, Any]]:
    """
    Keep only high-priority jobs:
    - Always keep A with match_score >= min_match_score
    - Optionally keep B with match_score >= min_match_score (if include_b=True)
    - Drop C and low-score jobs
    
    If use_preferences=True, applies preference-based re-ranking:
    - Loads user preference ratings (1-5)
    - Calculates final_score = match_score + preference_bonus
    - preference_bonus = (user_rating - 3) * 0.7
    - Sorts by category, then final_score, then seniority_score
    """
    result: List[Dict[str, Any]] = []
    
    # Load preferences if requested
    preferences = {}
    if use_preferences:
        try:
            preferences = load_preferences()
            print(f"Loaded {len(preferences)} preference ratings for re-ranking")
        except Exception as e:
            print(f"Warning: Failed to load preferences: {e}. Proceeding without preference re-ranking.")
            preferences = {}
    
    for item in items:
        score = item.get("score") or {}
        category = score.get("category")
        match_score = score.get("match_score")
        
        if category not in ("A", "B"):
            continue
        
        if not isinstance(match_score, (int, float)):
            continue
        
        if match_score < min_match_score:
            continue
        
        if category == "B" and not include_b:
            continue
        
        # Calculate final_score with preference bonus if applicable
        base_score = float(match_score)
        preference_bonus = 0.0
        
        if use_preferences:
            job_id = item.get("job", {}).get("job_id")
            if job_id and job_id in preferences:
                user_rating = preferences[job_id].user_rating
                # preference_bonus = (rating - 3) * 0.7
                # So 5 -> +1.4, 4 -> +0.7, 3 -> 0, 2 -> -0.7, 1 -> -1.4
                preference_bonus = (user_rating - 3) * 0.7
        
        final_score = base_score + preference_bonus
        item["_final_score"] = final_score
        item["_preference_record"] = preferences.get(item.get("job", {}).get("job_id")) if use_preferences else None
        
        result.append(item)
    
    # Sort: best first
    if use_preferences:
        # Sort by category, then final_score (desc), then seniority_score (desc)
        result.sort(
            key=lambda x: (
                x.get("score", {}).get("category", ""),
                -x.get("_final_score", 0.0),
                -x.get("score", {}).get("seniority_score", 0),
            ),
            reverse=True,
        )
    else:
        # Original sort: category, match_score, seniority_score
        result.sort(
            key=lambda x: (
                x.get("score", {}).get("category", ""),
                -x.get("score", {}).get("match_score", 0),
                -x.get("score", {}).get("seniority_score", 0),
            ),
            reverse=True,
        )
    
    return result


def render_markdown_report(
    items: List[Dict[str, Any]],
    min_match_score: int,
    use_preferences: bool = False,
) -> str:
    """Render a Markdown shortlist from filtered scored jobs."""
    lines: List[str] = []
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines.append("# JobHunter Shortlist Report")
    lines.append("")
    lines.append(f"_Generated at: {now_str}_")
    lines.append(f"_Filter: match_score >= {min_match_score}_")
    if use_preferences:
        lines.append("_Ranking uses both model match_score and your personal preference ratings (if available)._")
    lines.append("")
    
    if not items:
        lines.append("No jobs matched the filter criteria.")
        return "\n".join(lines)
    
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total shortlisted jobs: **{len(items)}**")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    
    for idx, item in enumerate(items, start=1):
        job = item.get("job", {})
        score = item.get("score", {})
        
        title = job.get("title", "Unknown Title")
        company = job.get("company", "Unknown Company")
        location = job.get("location") or "Location not specified"
        url = job.get("url", "")
        
        category = score.get("category", "?")
        match_score = score.get("match_score", "?")
        seniority_score = score.get("seniority_score", "?")
        compensation_tier = score.get("compensation_tier", "unknown")
        reasons = (score.get("reasons") or "").strip()
        talk_track = (score.get("talk_track") or "").strip()
        
        lines.append(f"### {idx}. {title} — {company}")
        lines.append("")
        lines.append(f"- **Category:** {category}")
        lines.append(f"- **Match score:** {match_score}/10")
        lines.append(f"- **Seniority score:** {seniority_score}/10")
        lines.append(f"- **Compensation tier:** {compensation_tier}")
        lines.append(f"- **Location:** {location}")
        if url:
            lines.append(f"- **Link:** {url}")
        
        # Show user rating if available
        preference_record = item.get("_preference_record")
        if preference_record:
            rating_str = f"User rating: {preference_record.user_rating}/5"
            if preference_record.tags:
                tags_str = ", ".join(preference_record.tags)
                rating_str += f" (tags: {tags_str})"
            lines.append(f"- **{rating_str}**")
        
        lines.append("")
        
        if reasons:
            lines.append("**Why this job was shortlisted:**")
            lines.append("")
            lines.append(f"> {reasons}")
            lines.append("")
        
        if talk_track:
            lines.append("**How you might talk about your experience for this job:**")
            lines.append("")
            lines.append(f"> {talk_track}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def run_job_hunter_report(
    input_file: Path,
    output_file: Path,
    min_match_score: int = 8,
    include_b: bool = True,
    use_preferences: bool = False,
) -> int:
    """
    Run the job hunter report generation pipeline programmatically.
    
    Args:
        input_file: Path to scored jobs JSON file (output from job_hunter_agent)
        output_file: Path to output Markdown report file
        min_match_score: Minimum match_score (1-10) to include a job in the shortlist
        include_b: Whether to include B category jobs if they meet the score threshold
        use_preferences: Whether to apply preference-based re-ranking
    
    Returns:
        Number of shortlisted jobs
    """
    items = load_scored_jobs(input_file)
    filtered = filter_scored_jobs(
        items,
        min_match_score=min_match_score,
        include_b=include_b,
        use_preferences=use_preferences,
    )
    
    md = render_markdown_report(
        filtered,
        min_match_score=min_match_score,
        use_preferences=use_preferences,
    )
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(md, encoding="utf-8")
    
    print(f"Shortlist report written to: {output_file}")
    print(f"Shortlisted jobs: {len(filtered)}")
    
    return len(filtered)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a shortlist Markdown report from scored jobs."
    )
    
    parser.add_argument(
        "--input-file",
        type=str,
        default="",
        help="Path to scored jobs JSON file (output from job_hunter_agent).",
    )
    
    parser.add_argument(
        "--output-file",
        type=str,
        default="",
        help="Path to output Markdown report file.",
    )
    
    parser.add_argument(
        "--min-match-score",
        type=int,
        default=8,
        help="Minimum match_score (1-10) to include a job in the shortlist.",
    )
    
    parser.add_argument(
        "--include-b",
        dest="include_b",
        action="store_true",
        help="Include B category jobs if they meet the score threshold (default).",
    )
    
    parser.add_argument(
        "--no-include-b",
        dest="include_b",
        action="store_false",
        help="Exclude B category jobs (only keep A).",
    )
    
    parser.add_argument(
        "--use-preferences",
        dest="use_preferences",
        action="store_true",
        help="Apply preference-based re-ranking using user ratings (RLHF-style).",
    )
    
    parser.set_defaults(include_b=True, use_preferences=False)
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file) if args.input_file else default_scored_path()
    output_path = Path(args.output_file) if args.output_file else default_report_path()
    
    run_job_hunter_report(
        input_file=input_path,
        output_file=output_path,
        min_match_score=args.min_match_score,
        include_b=args.include_b,
        use_preferences=args.use_preferences,
    )


if __name__ == "__main__":
    main()
