#!/usr/bin/env python3
"""
filter_agent_jobs.py - Filter agent/RAG related jobs from scored jobs file
==========================================================================

This script filters jobs from a scored jobs JSON file that:
1. Have category == "A"
2. Have match_score >= 8
3. Contain agent/RAG related keywords in title, description, or score.reasons

Usage:
    python3 -m experiments.jobhunter.filter_agent_jobs \
        --input data/jobhunter/scored/jobs_scored_llm_core_latest.json \
        --output reports/jobhunter/jd_agent_jobs_selected_andy.md
"""

import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any

# Agent/RAG related keywords (case-insensitive)
AGENT_KEYWORDS = [
    "agent",
    "agentic",
    "tool use",
    "tools",
    "workflow",
    "orchestration",
    "retrieval",
    "RAG",
    "assistant",
    "copilot",
]


def contains_agent_keywords(text: str) -> bool:
    """Check if text contains any agent/RAG related keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in AGENT_KEYWORDS)


def filter_agent_jobs(scored_file: Path) -> List[Dict[str, Any]]:
    """
    Filter jobs that match agent/RAG criteria.
    
    Returns:
        List of job dictionaries with 'job' and 'score' keys
    """
    with open(scored_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of scored jobs, got {type(data)}")
    
    filtered_jobs = []
    
    for item in data:
        job = item.get("job", {})
        score = item.get("score", {})
        
        # Check category and match_score
        category = score.get("category")
        match_score = score.get("match_score", 0)
        
        if category != "A" or match_score < 8:
            continue
        
        # Check for agent keywords in various fields
        title = job.get("title", "")
        description = job.get("description", "")
        reasons = score.get("reasons", "")
        
        # Combine all text fields for keyword search
        combined_text = f"{title} {description} {reasons}"
        
        if contains_agent_keywords(combined_text):
            filtered_jobs.append(item)
    
    return filtered_jobs


def format_job_table(jobs: List[Dict[str, Any]]) -> str:
    """Format filtered jobs as a Markdown table."""
    lines = []
    lines.append("# Agent/RAG Jobs Selected for JD Analysis")
    lines.append("")
    lines.append("## Filter Criteria")
    lines.append("")
    lines.append("- Category: A")
    lines.append("- Match Score: >= 8")
    lines.append("- Contains agent/RAG keywords in title, description, or score.reasons")
    lines.append("")
    lines.append("## Selected Jobs")
    lines.append("")
    lines.append("| Job ID | Company | Title | Match Score | Link |")
    lines.append("|--------|---------|-------|-------------|------|")
    
    for item in jobs:
        job = item.get("job", {})
        score = item.get("score", {})
        
        job_id = job.get("job_id", "N/A")
        company = job.get("company", "N/A")
        title = job.get("title", "N/A")
        match_score = score.get("match_score", "N/A")
        url = job.get("url", "#")
        
        # Escape pipe characters in title
        title_escaped = title.replace("|", "\\|")
        
        lines.append(f"| {job_id} | {company} | {title_escaped} | {match_score} | [Link]({url}) |")
    
    lines.append("")
    lines.append(f"**Total:** {len(jobs)} jobs")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Filter agent/RAG related jobs from scored jobs file"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to scored jobs JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output Markdown file",
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / args.input if not Path(args.input).is_absolute() else Path(args.input)
    output_path = project_root / args.output if not Path(args.output).is_absolute() else Path(args.output)
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Filter jobs
    print(f"Reading scored jobs from {input_path}...")
    filtered_jobs = filter_agent_jobs(input_path)
    print(f"Found {len(filtered_jobs)} jobs matching criteria")
    
    # Format and save
    markdown = format_job_table(filtered_jobs)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Saved filtered jobs to {output_path}")
    
    # Print summary
    print("\nSelected jobs:")
    for item in filtered_jobs:
        job = item.get("job", {})
        score = item.get("score", {})
        print(f"  - {job.get('company')}: {job.get('title')} (score: {score.get('match_score')}, ID: {job.get('job_id')})")


if __name__ == "__main__":
    main()





