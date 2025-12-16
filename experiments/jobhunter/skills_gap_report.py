#!/usr/bin/env python3
"""
skills_gap_report.py - Generate skills gap analysis from scored jobs
====================================================================

This script reads one or more scored jobs JSON files from the JobHunter pipeline,
aggregates all shortlisted A / high-score jobs, and produces a skills gap report
in Markdown format.

The report shows:
- What the market is repeatedly asking for (from these jobs)
- What you already have (hard-coded current skills)
- What gaps are worth closing next

Usage:
    python -m experiments.jobhunter.skills_gap_report
    python -m experiments.jobhunter.skills_gap_report --scored-files data/jobhunter/scored/jobs_scored_llm_core_20251208.json
    python -m experiments.jobhunter.skills_gap_report --scored-files data/jobhunter/scored/jobs_scored_llm_core_20251208.json,data/jobhunter/scored/jobs_scored_data_ml_platform_20251208.json --min-match-score 8
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Hard-coded current skills (can be updated later)
CURRENT_SKILLS = {
    "llm_agents": True,
    "rag_systems": True,
    "langgraph": True,
    "langchain": False,  # e.g. low experience
    "evaluation": True,
    "guardrails_safety": True,
    "ml_infra": False,
    "rlhf_rl": False,
    "data_engineering": True,
    "gcp": True,
    "kubernetes": False,
    "vector_db": True,
    "observability": True,
}

# Keyword mapping to normalized skill names
KEYWORD_MAP = {
    # evaluation
    "evaluation": "evaluation",
    "eval": "evaluation",
    "metrics": "evaluation",
    "evaluating": "evaluation",
    # rag_systems
    "rag": "rag_systems",
    "retrieval": "rag_systems",
    "retrieval augmented": "rag_systems",
    # langgraph
    "langgraph": "langgraph",
    "lang graph": "langgraph",
    # langchain
    "langchain": "langchain",
    "lang chain": "langchain",
    # ml_infra
    "infra": "ml_infra",
    "infrastructure": "ml_infra",
    "platform": "ml_infra",
    "ml platform": "ml_infra",
    "ml infrastructure": "ml_infra",
    # rlhf_rl
    "rl": "rlhf_rl",
    "reinforcement": "rlhf_rl",
    "rlhf": "rlhf_rl",
    "reinforcement learning": "rlhf_rl",
    # observability
    "observability": "observability",
    "monitoring": "observability",
    "logging": "observability",
    # gcp
    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    # kubernetes
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    # data_engineering
    "data pipeline": "data_engineering",
    "data engineering": "data_engineering",
    "etl": "data_engineering",
    # vector_db
    "vector store": "vector_db",
    "vector database": "vector_db",
    "qdrant": "vector_db",
    "faiss": "vector_db",
    "pinecone": "vector_db",
    "weaviate": "vector_db",
    # llm_agents
    "agents": "llm_agents",
    "agentic": "llm_agents",
    "tool use": "llm_agents",
    "agent framework": "llm_agents",
    # guardrails_safety
    "guardrails": "guardrails_safety",
    "safety": "guardrails_safety",
    "ai safety": "guardrails_safety",
}


def load_scored_jobs(files: List[Path]) -> List[Dict]:
    """
    Load and concatenate jobs from multiple JSON files.
    
    Args:
        files: List of paths to scored jobs JSON files
    
    Returns:
        List of job dictionaries
    """
    all_jobs = []
    
    for file_path in files:
        if not file_path.exists():
            print(f"Warning: File not found: {file_path}", file=sys.stderr)
            continue
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"Warning: Expected list in {file_path}, got {type(data)}", file=sys.stderr)
                continue
            
            all_jobs.extend(data)
            
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse JSON from {file_path}: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Warning: Error reading {file_path}: {e}", file=sys.stderr)
            continue
    
    return all_jobs


def filter_relevant_jobs(
    jobs: List[Dict],
    min_match_score: int = 8,
    categories: List[str] = ["A"]
) -> List[Dict]:
    """
    Filter jobs to only category A and match_score >= min_match_score.
    
    Args:
        jobs: List of job dictionaries
        min_match_score: Minimum match score threshold
        categories: List of categories to include (default: ["A"])
    
    Returns:
        Filtered list of job dictionaries
    """
    filtered = []
    
    for job in jobs:
        score = job.get("score", {})
        category = score.get("category", "")
        match_score = score.get("match_score", 0)
        
        if category in categories and isinstance(match_score, (int, float)) and match_score >= min_match_score:
            filtered.append(job)
    
    return filtered


def extract_skill_tokens(job: Dict) -> List[str]:
    """
    Extract and normalize skill tokens from a job posting.
    
    Extracts from fields like title, description, reasons, talk_track.
    Lowercases, splits on non-letters, strips short tokens (length < 3).
    Maps keywords to normalized skill names.
    
    Args:
        job: Job dictionary
    
    Returns:
        List of normalized skill names
    """
    # Collect text from various fields
    text_parts = []
    
    job_data = job.get("job", {})
    score_data = job.get("score", {})
    
    # Add title
    if "title" in job_data:
        text_parts.append(job_data["title"])
    
    # Add description (may be HTML encoded)
    if "description" in job_data:
        desc = job_data["description"]
        # Basic HTML entity decoding (simple cases)
        desc = desc.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        # Remove HTML tags (simple regex)
        desc = re.sub(r"<[^>]+>", " ", desc)
        text_parts.append(desc)
    
    # Add reasons and talk_track from score
    if "reasons" in score_data:
        text_parts.append(score_data["reasons"])
    if "talk_track" in score_data:
        text_parts.append(score_data["talk_track"])
    
    # Combine all text
    combined_text = " ".join(text_parts).lower()
    
    # Extract skills using keyword mapping
    found_skills = set()
    
    # Check for each keyword pattern
    for keyword, skill_name in KEYWORD_MAP.items():
        # Use word boundaries for better matching
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
        if re.search(pattern, combined_text, re.IGNORECASE):
            found_skills.add(skill_name)
    
    return list(found_skills)


def aggregate_skill_counts(jobs: List[Dict]) -> Dict[str, int]:
    """
    Aggregate skill counts across all jobs.
    
    Args:
        jobs: List of job dictionaries
    
    Returns:
        Dictionary mapping skill names to counts
    """
    all_skills = []
    
    for job in jobs:
        skills = extract_skill_tokens(job)
        all_skills.extend(skills)
    
    return dict(Counter(all_skills))


def compute_skill_view(
    skill_counts: Dict[str, int],
    current_skills: Dict[str, bool]
) -> Dict[str, List[Tuple[str, int]]]:
    """
    Compute the skill view comparing market demand vs current skills.
    
    Args:
        skill_counts: Dictionary mapping skill names to counts
        current_skills: Dictionary mapping skill names to boolean (True = have it)
    
    Returns:
        Dictionary with keys:
        - strong_and_in_demand: [(skill, count), ...]
        - gaps_high_priority: [(skill, count), ...]
        - nice_to_have: [(skill, count), ...]
    """
    strong_and_in_demand = []
    gaps_high_priority = []
    nice_to_have = []
    
    for skill, count in skill_counts.items():
        has_skill = current_skills.get(skill, False)
        
        if has_skill and count >= 2:
            strong_and_in_demand.append((skill, count))
        elif not has_skill and count >= 2:
            gaps_high_priority.append((skill, count))
        elif count == 1:
            nice_to_have.append((skill, count))
    
    # Sort by count descending
    strong_and_in_demand.sort(key=lambda x: x[1], reverse=True)
    gaps_high_priority.sort(key=lambda x: x[1], reverse=True)
    nice_to_have.sort(key=lambda x: x[1], reverse=True)
    
    return {
        "strong_and_in_demand": strong_and_in_demand,
        "gaps_high_priority": gaps_high_priority,
        "nice_to_have": nice_to_have,
    }


def generate_project_suggestions(gaps: List[Tuple[str, int]]) -> List[str]:
    """
    Generate project suggestions based on skill gaps.
    
    Args:
        gaps: List of (skill, count) tuples for high-priority gaps
    
    Returns:
        List of suggestion strings
    """
    suggestions = []
    gap_skills = [skill for skill, _ in gaps]
    
    if "ml_infra" in gap_skills:
        suggestions.append(
            "Consider a small project where you build an evaluation + logging pipeline "
            "around your ecommerce agent."
        )
    
    if "rlhf_rl" in gap_skills:
        suggestions.append(
            "Consider reading 1–2 RLHF papers and building a tiny offline preference "
            "dataset for your agent."
        )
    
    if "langchain" in gap_skills:
        suggestions.append(
            "Consider building a small project using LangChain to understand its patterns "
            "and how it compares to LangGraph."
        )
    
    if "kubernetes" in gap_skills:
        suggestions.append(
            "Consider deploying a small service to Kubernetes to get hands-on experience "
            "with container orchestration."
        )
    
    return suggestions


def generate_markdown_report(
    jobs: List[Dict],
    skill_view: Dict[str, List[Tuple[str, int]]],
    output_path: Path,
    input_files: List[Path],
    min_match_score: int,
) -> None:
    """
    Generate a Markdown skills gap report.
    
    Args:
        jobs: List of filtered job dictionaries
        skill_view: Dictionary with skill view data
        output_path: Path to save the report
        input_files: List of input file paths (for metadata)
        min_match_score: Minimum match score used for filtering
    """
    # Get top 10 skills by count
    all_skill_counts = {}
    for category in skill_view.values():
        for skill, count in category:
            all_skill_counts[skill] = all_skill_counts.get(skill, 0) + count
    
    top_skills = sorted(all_skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Generate report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    date_str = datetime.now().strftime("%Y%m%d")
    
    lines = []
    lines.append("# JobHunter Skills Gap Report")
    lines.append("")
    lines.append(f"_Generated at: {timestamp}_")
    lines.append("")
    lines.append(f"Analysing shortlisted jobs from: {', '.join(str(f.name) for f in input_files)}")
    lines.append(f"Filter: category=A, match_score >= {min_match_score}")
    lines.append(f"Total shortlisted jobs: {len(jobs)}")
    lines.append("")
    
    # Section 1: Top Demand Signals
    lines.append("## 1. Top Demand Signals (from shortlisted jobs)")
    lines.append("")
    lines.append("| Skill | Mentions in jobs |")
    lines.append("|-------|-----------------|")
    for skill, count in top_skills:
        lines.append(f"| {skill} | {count} |")
    lines.append("")
    
    # Section 2: Strong & In-Demand
    lines.append("## 2. Strong & In-Demand (我已经有的)")
    lines.append("")
    lines.append("These are skills you already have and the market strongly wants:")
    lines.append("")
    for skill, count in skill_view["strong_and_in_demand"]:
        lines.append(f"- **{skill}** — mentioned in {count} jobs")
    if not skill_view["strong_and_in_demand"]:
        lines.append("_No skills in this category._")
    lines.append("")
    
    # Section 3: High-Priority Gaps
    lines.append("## 3. High-Priority Gaps (值得补的)")
    lines.append("")
    lines.append("These are skills that show up repeatedly but are not yet your strengths:")
    lines.append("")
    for skill, count in skill_view["gaps_high_priority"]:
        lines.append(f"- **{skill}** — mentioned in {count} jobs")
    if not skill_view["gaps_high_priority"]:
        lines.append("_No high-priority gaps identified._")
    lines.append("")
    
    # Project suggestions
    suggestions = generate_project_suggestions(skill_view["gaps_high_priority"])
    if suggestions:
        lines.append("### Suggested Project Ideas")
        lines.append("")
        for suggestion in suggestions:
            lines.append(f"- {suggestion}")
        lines.append("")
    
    # Section 4: Nice-to-have
    lines.append("## 4. Nice-to-have (长尾技能)")
    lines.append("")
    lines.append("These appear only once but might be worth keeping an eye on:")
    lines.append("")
    for skill, count in skill_view["nice_to_have"]:
        lines.append(f"- **{skill}**")
    if not skill_view["nice_to_have"]:
        lines.append("_No skills in this category._")
    lines.append("")
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def find_latest_scored_files(data_dir: Path) -> List[Path]:
    """
    Auto-discover latest scored jobs JSON files.
    
    Args:
        data_dir: Directory to search in
    
    Returns:
        List of file paths
    """
    pattern = "jobs_scored_*.json"
    files = list(data_dir.glob(pattern))
    
    if not files:
        return []
    
    # Sort by modification time, newest first
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Return up to 2 most recent files
    return files[:2]


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate skills gap analysis from scored jobs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m experiments.jobhunter.skills_gap_report
  python -m experiments.jobhunter.skills_gap_report --scored-files data/jobhunter/scored/jobs_scored_llm_core_20251208.json
  python -m experiments.jobhunter.skills_gap_report --scored-files data/jobhunter/scored/jobs_scored_llm_core_20251208.json,data/jobhunter/scored/jobs_scored_data_ml_platform_20251208.json --min-match-score 8
        """,
    )
    
    parser.add_argument(
        "--scored-files",
        type=str,
        default=None,
        help="Comma-separated list of scored jobs JSON files. If omitted, auto-discovers latest files in data/jobhunter/scored/",
    )
    
    parser.add_argument(
        "--min-match-score",
        type=int,
        default=8,
        help="Minimum match score threshold (default: 8)",
    )
    
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Output file path. If omitted, defaults to reports/jobhunter/skills_gap_report_YYYYMMDD.md",
    )
    
    args = parser.parse_args()
    
    # Determine input files
    if args.scored_files:
        input_files = [project_root / f.strip() for f in args.scored_files.split(",")]
    else:
        # Auto-discover
        scored_dir = project_root / "data" / "jobhunter" / "scored"
        input_files = find_latest_scored_files(scored_dir)
        
        if not input_files:
            print("Error: No scored jobs files found. Please specify --scored-files.", file=sys.stderr)
            sys.exit(1)
    
    # Determine output file
    if args.output_file:
        output_path = project_root / args.output_file
    else:
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = project_root / "reports" / "jobhunter" / f"skills_gap_report_{date_str}.md"
    
    # Load jobs
    print(f"Loading jobs from {len(input_files)} file(s)...")
    all_jobs = load_scored_jobs(input_files)
    print(f"Loaded {len(all_jobs)} total jobs")
    
    # Filter to relevant jobs
    relevant_jobs = filter_relevant_jobs(all_jobs, min_match_score=args.min_match_score)
    print(f"Filtered to {len(relevant_jobs)} shortlisted jobs (category=A, match_score>={args.min_match_score})")
    
    if not relevant_jobs:
        print("Warning: No relevant jobs found. Report may be empty.", file=sys.stderr)
    
    # Aggregate skill counts
    skill_counts = aggregate_skill_counts(relevant_jobs)
    
    # Compute skill view
    skill_view = compute_skill_view(skill_counts, CURRENT_SKILLS)
    
    # Generate report
    generate_markdown_report(
        jobs=relevant_jobs,
        skill_view=skill_view,
        output_path=output_path,
        input_files=input_files,
        min_match_score=args.min_match_score,
    )
    
    print(f"Report saved to: {output_path}")
    print(f"  - Strong & in-demand skills: {len(skill_view['strong_and_in_demand'])}")
    print(f"  - High-priority gaps: {len(skill_view['gaps_high_priority'])}")
    print(f"  - Nice-to-have skills: {len(skill_view['nice_to_have'])}")


if __name__ == "__main__":
    main()
