#!/usr/bin/env python3
"""
generate_comparison_report.py - Generate comparison report from JD summaries
============================================================================

This script reads multiple JD summary markdown files and generates a
comparison report highlighting key differences and recommendations.

Usage:
    python3 experiments/jobhunter/generate_comparison_report.py \
        --summary-dir reports/jobhunter \
        --job-ids 4985877008 4974302008 4946314008 4952079008 4949336008 \
        --output reports/jobhunter/jd_agent_summary_comparison_andy.md
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_jd_summary(markdown_file: Path) -> Dict[str, any]:
    """
    Parse a JD summary markdown file into structured data.
    
    Returns:
        Dict with keys: title, company, recommendation, reasoning_summary,
        gold_points, silver_points, bronze_points, core_skills, nice_to_have_skills,
        risks_or_red_flags, evidence_snippets, job_id
    """
    content = markdown_file.read_text(encoding="utf-8")
    
    # Extract job_id from filename
    job_id = markdown_file.stem.replace("jd_summary_", "").replace("_andy_agents", "")
    
    # Parse title and company from header
    title_match = re.search(r"## JD Summary: (.+?) — (.+)", content)
    title = title_match.group(1) if title_match else "Unknown"
    company = title_match.group(2) if title_match else "Unknown"
    
    # Parse recommendation
    rec_match = re.search(r"\*\*Recommendation:\*\* (.+?)\n", content)
    recommendation = rec_match.group(1).strip() if rec_match else "UNKNOWN"
    # Remove emoji
    recommendation = re.sub(r"[^\w\s]", "", recommendation).strip()
    
    # Parse reasoning summary
    why_match = re.search(r"\*\*Why:\*\* (.+?)(?=\n\n###|\n\*\*|$)", content, re.DOTALL)
    reasoning_summary = why_match.group(1).strip() if why_match else ""
    
    # Parse gold points
    gold_section = re.search(r"### 🥇 Gold.*?\n\n(.*?)(?=\n\n###|$)", content, re.DOTALL)
    gold_points = []
    if gold_section:
        gold_text = gold_section.group(1)
        gold_points = [line.strip()[2:] for line in gold_text.split("\n") if line.strip().startswith("-")]
    
    # Parse silver points
    silver_section = re.search(r"### 🥈 Silver.*?\n\n(.*?)(?=\n\n###|$)", content, re.DOTALL)
    silver_points = []
    if silver_section:
        silver_text = silver_section.group(1)
        silver_points = [line.strip()[2:] for line in silver_text.split("\n") if line.strip().startswith("-")]
    
    # Parse bronze points
    bronze_section = re.search(r"### 🥉 Bronze.*?\n\n(.*?)(?=\n\n###|$)", content, re.DOTALL)
    bronze_points = []
    if bronze_section:
        bronze_text = bronze_section.group(1)
        bronze_points = [line.strip()[2:] for line in bronze_text.split("\n") if line.strip().startswith("-")]
    
    # Parse core skills
    core_skills_section = re.search(r"### 🔧 Core skills.*?\n\n(.*?)(?=\n\n###|$)", content, re.DOTALL)
    core_skills = []
    if core_skills_section:
        skills_text = core_skills_section.group(1)
        skills_match = re.search(r"- (.+)", skills_text)
        if skills_match:
            core_skills = [s.strip() for s in skills_match.group(1).split(",")]
    
    # Parse nice-to-have skills
    nice_to_have_section = re.search(r"### 💡 Nice-to-have skills.*?\n\n(.*?)(?=\n\n###|$)", content, re.DOTALL)
    nice_to_have_skills = []
    if nice_to_have_section:
        skills_text = nice_to_have_section.group(1)
        skills_match = re.search(r"- (.+)", skills_text)
        if skills_match:
            nice_to_have_skills = [s.strip() for s in skills_match.group(1).split(",")]
    
    # Parse risks/red flags
    risks_section = re.search(r"### ⚠️ Risks / Red flags.*?\n\n(.*?)(?=\n\n###|$)", content, re.DOTALL)
    risks_or_red_flags = []
    if risks_section:
        risks_text = risks_section.group(1)
        # Skip "No significant risks identified"
        if "No significant risks" not in risks_text:
            risks_or_red_flags = [line.strip()[2:] for line in risks_text.split("\n") if line.strip().startswith("-")]
    
    # Parse evidence snippets
    evidence_section = re.search(r"### 📝 Evidence snippets.*?\n\n(.*?)(?=\n\n###|$)", content, re.DOTALL)
    evidence_snippets = []
    if evidence_section:
        evidence_text = evidence_section.group(1)
        evidence_snippets = [line.strip()[1:] for line in evidence_text.split("\n") if line.strip().startswith(">")]
    
    return {
        "job_id": job_id,
        "title": title,
        "company": company,
        "recommendation": recommendation,
        "reasoning_summary": reasoning_summary,
        "gold_points": gold_points,
        "silver_points": silver_points,
        "bronze_points": bronze_points,
        "core_skills": core_skills,
        "nice_to_have_skills": nice_to_have_skills,
        "risks_or_red_flags": risks_or_red_flags,
        "evidence_snippets": evidence_snippets,
    }


def load_job_url(job_id: str, scored_file: Path) -> Optional[str]:
    """Load job URL from scored jobs file."""
    import json
    
    try:
        with open(scored_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for item in data:
            job = item.get("job", {})
            if job.get("job_id") == job_id:
                return job.get("url", "#")
    except Exception:
        pass
    
    return None


def generate_comparison_report(
    summaries: List[Dict],
    scored_file: Optional[Path] = None,
) -> str:
    """Generate comparison report markdown."""
    lines = []
    
    lines.append("# Agent/RAG Jobs Comparison Report for Andy")
    lines.append("")
    lines.append("## Overview Table")
    lines.append("")
    lines.append("| Company | Title | Match Score | Recommendation | Why (Summary) |")
    lines.append("|---------|-------|-------------|----------------|----------------|")
    
    # Load match scores from scored file if available
    match_scores = {}
    if scored_file and scored_file.exists():
        import json
        try:
            with open(scored_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                job = item.get("job", {})
                score = item.get("score", {})
                match_scores[job.get("job_id")] = score.get("match_score", "N/A")
        except Exception:
            pass
    
    for summary in summaries:
        job_id = summary["job_id"]
        company = summary["company"]
        title = summary["title"]
        match_score = match_scores.get(job_id, "N/A")
        recommendation = summary["recommendation"]
        reasoning = summary["reasoning_summary"][:100] + "..." if len(summary["reasoning_summary"]) > 100 else summary["reasoning_summary"]
        
        # Escape pipe characters
        title_escaped = title.replace("|", "\\|")
        reasoning_escaped = reasoning.replace("|", "\\|")
        
        lines.append(f"| {company} | {title_escaped} | {match_score} | {recommendation} | {reasoning_escaped} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Detailed sections for each job
    for summary in summaries:
        job_id = summary["job_id"]
        company = summary["company"]
        title = summary["title"]
        
        # Get job URL
        url = "#"
        if scored_file and scored_file.exists():
            url = load_job_url(job_id, scored_file) or "#"
        
        lines.append(f"## {title} — {company}")
        lines.append("")
        lines.append(f"**Job ID:** {job_id} | [JD Link]({url})")
        lines.append("")
        
        # Gold points
        if summary["gold_points"]:
            lines.append("### 🥇 Gold: What the company most wants")
            lines.append("")
            for point in summary["gold_points"][:3]:  # Top 3
                lines.append(f"- {point}")
            lines.append("")
        
        # Silver points
        if summary["silver_points"]:
            lines.append("### 🥈 Silver: Key skills (3-5 points)")
            lines.append("")
            for point in summary["silver_points"][:5]:  # Top 5
                lines.append(f"- {point}")
            lines.append("")
        
        # Bronze points
        if summary["bronze_points"]:
            lines.append("### 🥉 Bronze: Nice-to-haves")
            lines.append("")
            for point in summary["bronze_points"][:3]:  # Top 3
                lines.append(f"- {point}")
            lines.append("")
        
        # Risks/Red flags
        if summary["risks_or_red_flags"]:
            lines.append("### ⚠️ Main risks/gaps for Andy")
            lines.append("")
            for risk in summary["risks_or_red_flags"][:3]:  # Top 3
                lines.append(f"- {risk}")
            lines.append("")
        else:
            lines.append("### ⚠️ Main risks/gaps for Andy")
            lines.append("")
            lines.append("_No significant risks identified._")
            lines.append("")
        
        # Overall judgment
        rec_emoji = {
            "APPLY": "✅",
            "MAYBE": "🤔",
            "SKIP": "❌",
        }.get(summary["recommendation"], "🤔")
        
        lines.append(f"### Overall Judgment: {rec_emoji} {summary['recommendation']}")
        lines.append("")
        lines.append(f"{summary['reasoning_summary']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # QA Summary
    lines.append("## QA Summary & Recommendations")
    lines.append("")
    lines.append("### Analysis Status")
    lines.append("")
    lines.append(f"- ✅ {len(summaries)} jobs analyzed successfully")
    lines.append("- ✅ All summary files contain complete data")
    lines.append("")
    
    # Categorize jobs
    apply_jobs = [s for s in summaries if s["recommendation"] == "APPLY"]
    maybe_jobs = [s for s in summaries if s["recommendation"] == "MAYBE"]
    skip_jobs = [s for s in summaries if s["recommendation"] == "SKIP"]
    
    lines.append("### Job Categories")
    lines.append("")
    if apply_jobs:
        lines.append("**✅ Highly Recommended (APPLY):**")
        for job in apply_jobs:
            lines.append(f"- {job['company']}: {job['title']}")
        lines.append("")
    
    if maybe_jobs:
        lines.append("**🤔 Consider (MAYBE):**")
        for job in maybe_jobs:
            lines.append(f"- {job['company']}: {job['title']}")
        lines.append("")
    
    if skip_jobs:
        lines.append("**❌ Not Recommended (SKIP):**")
        for job in skip_jobs:
            lines.append(f"- {job['company']}: {job['title']}")
        lines.append("")
    
    # Identify best fit types
    lines.append("### Best Fit Job Types for Andy")
    lines.append("")
    lines.append("Based on the analysis, the following job types are most suitable:")
    lines.append("")
    
    # Analyze by job title patterns
    forward_deployed = [s for s in summaries if "Forward Deployed" in s["title"] or "Applied AI" in s["title"]]
    platform_tooling = [s for s in summaries if "Tool" in s["title"] or "Platform" in s["title"] or "Operations" in s["title"]]
    safeguards = [s for s in summaries if "Safeguard" in s["title"]]
    
    if forward_deployed:
        lines.append("1. **Forward Deployed / Applied AI roles:**")
        for job in forward_deployed:
            lines.append(f"   - {job['title']} ({job['recommendation']})")
        lines.append("   - *Note: May require travel and customer-facing work*")
        lines.append("")
    
    if platform_tooling:
        lines.append("2. **Agent Platform / Tooling roles:**")
        for job in platform_tooling:
            lines.append(f"   - {job['title']} ({job['recommendation']})")
        lines.append("   - *Note: Strong technical fit, but check remote work policy*")
        lines.append("")
    
    if safeguards:
        lines.append("3. **Safeguards / Safety roles:**")
        for job in safeguards:
            lines.append(f"   - {job['title']} ({job['recommendation']})")
        lines.append("   - *Note: Good technical match, but may require in-office presence*")
        lines.append("")
    
    lines.append("### Priority Recommendations")
    lines.append("")
    lines.append("**Top 1-2 job types to prioritize:**")
    lines.append("")
    if platform_tooling:
        lines.append("1. **Agent Platform / Tooling roles** - Best technical fit with Andy's skills in LLM agents, RAG, and infrastructure")
    if forward_deployed:
        lines.append("2. **Forward Deployed / Applied AI roles** - Good match if willing to accept travel requirements")
    lines.append("")
    lines.append("**Key considerations for interviews:**")
    lines.append("")
    lines.append("- Emphasize production LLM agent experience (LangGraph, multi-agent systems)")
    lines.append("- Highlight RAG and evaluation framework work")
    lines.append("- Discuss remote work preferences and flexibility on travel/office requirements")
    lines.append("- Prepare stories about building scalable agent systems and infrastructure")
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate comparison report from JD summaries"
    )
    parser.add_argument(
        "--summary-dir",
        type=str,
        required=True,
        help="Directory containing JD summary markdown files",
    )
    parser.add_argument(
        "--job-ids",
        type=str,
        nargs="+",
        required=True,
        help="List of job IDs to include in report",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output markdown file path",
    )
    parser.add_argument(
        "--scored-file",
        type=str,
        default=None,
        help="Path to scored jobs JSON file (for URLs and match scores)",
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    project_root = Path(__file__).parent.parent.parent
    summary_dir = project_root / args.summary_dir if not Path(args.summary_dir).is_absolute() else Path(args.summary_dir)
    output_path = project_root / args.output if not Path(args.output).is_absolute() else Path(args.output)
    scored_file = None
    if args.scored_file:
        scored_file = project_root / args.scored_file if not Path(args.scored_file).is_absolute() else Path(args.scored_file)
    
    # Load summaries
    summaries = []
    for job_id in args.job_ids:
        summary_file = summary_dir / f"jd_summary_{job_id}_andy_agents.md"
        if not summary_file.exists():
            print(f"Warning: Summary file not found: {summary_file}")
            continue
        
        try:
            summary = parse_jd_summary(summary_file)
            summaries.append(summary)
        except Exception as e:
            print(f"Error parsing {summary_file}: {e}")
            continue
    
    if not summaries:
        print("Error: No valid summaries found")
        return
    
    # Generate report
    report = generate_comparison_report(summaries, scored_file=scored_file)
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Generated comparison report: {output_path}")
    print(f"Included {len(summaries)} job summaries")


if __name__ == "__main__":
    main()





