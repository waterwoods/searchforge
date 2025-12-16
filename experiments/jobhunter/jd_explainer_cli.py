#!/usr/bin/env python3
"""
jd_explainer_cli.py - CLI tool for manually testing the JD interpreter
========================================================================

This CLI allows you (and your dad / interviewers) to manually test the JD interpreter
without going through the whole JobHunter pipeline.

This is a candidate-specific JD explainer that can use a fixed candidate profile
(default: Andy's profile) to provide personalized job analysis.

Usage:
    # From a scored jobs file with default profile (Andy's profile):
    python -m experiments.jobhunter.jd_explainer_cli \
      --from-scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
      --job-id 4741102008 \
      --use-default-profile
    
    # From a text file with default profile:
    python -m experiments.jobhunter.jd_explainer_cli \
      --from-text-file path/to/jd.txt \
      --use-default-profile
    
    # With custom profile file:
    python -m experiments.jobhunter.jd_explainer_cli \
      --from-scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
      --job-id 4983501008 \
      --profile-file data/jobhunter/candidate_profile_andy.md
    
    # With inline candidate profile (legacy):
    python -m experiments.jobhunter.jd_explainer_cli \
      --from-scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
      --job-id 4983501008 \
      --candidate-profile "Senior backend/data/LLM engineer, strong in GCP, infra, observability, LangGraph agents."
    
    # Print JSON output:
    python -m experiments.jobhunter.jd_explainer_cli \
      --from-scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
      --job-id 4983501008 \
      --use-default-profile \
      --print-json

How to test:
    # Test with a high-scoring job from scored file:
    python3 -m experiments.jobhunter.jd_explainer_cli \
      --from-scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
      --job-id 4741102008 \
      --use-default-profile
    
    # Test with a JD text file:
    python3 -m experiments.jobhunter.jd_explainer_cli \
      --from-text-file /path/to/jd.txt \
      --use-default-profile
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.jobhunter.jd_interpreter import DEFAULT_MODEL
from services.fiqa_api.jobhunter.schemas import JobJDInput, JobJDSummary
from services.fiqa_api.jobhunter.profile_loader import load_candidate_profile as load_profile_from_file
from services.fiqa_api.jobhunter.job_fit_analyzer import JobFitSummary
from services.fiqa_api.jobhunter.graphs.jd_analysis_graph import run_jd_analysis
from services.fiqa_api.jobhunter.schemas import ConstraintCheckResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_candidate_profile_text(profile_input: str) -> str:
    """
    Load candidate profile from either a file path or literal text.
    
    This is a helper for the legacy --candidate-profile argument that accepts
    either a file path or inline text.
    
    Args:
        profile_input: Either a file path (relative to project root or absolute) or literal text
        
    Returns:
        Candidate profile text
    """
    # Try to resolve as file path first
    profile_path = project_root / profile_input if not Path(profile_input).is_absolute() else Path(profile_input)
    if profile_path.exists() and profile_path.is_file():
        return profile_path.read_text(encoding="utf-8").strip()
    else:
        # Treat as literal text
        return profile_input


def load_job_from_scored_file(scored_file: Path, job_id: str) -> JobJDInput:
    """
    Load a job from a scored jobs JSON file.
    
    Args:
        scored_file: Path to scored jobs JSON file
        job_id: Job ID to find
        
    Returns:
        JobJDInput
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If job_id not found
    """
    if not scored_file.exists():
        raise FileNotFoundError(f"Scored jobs file not found: {scored_file}")
    
    with open(scored_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of scored jobs, got {type(data)}")
    
    # Find the job with matching job_id
    for item in data:
        job = item.get("job", {})
        if job.get("job_id") == job_id:
            return JobJDInput(
                job_id=job.get("job_id"),
                company=job.get("company"),
                title=job.get("title"),
                location=job.get("location"),
                description=job.get("description", ""),
                candidate_profile=None,  # Will be set by caller if provided
            )
    
    raise ValueError(f"Job with job_id '{job_id}' not found in {scored_file}")


def load_job_from_text_file(text_file: Path, title: str = None, company: str = None, location: str = None) -> JobJDInput:
    """
    Load a job from a text file containing the JD.
    
    Args:
        text_file: Path to text file with JD
        title: Optional job title
        company: Optional company name
        location: Optional location
        
    Returns:
        JobJDInput
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not text_file.exists():
        raise FileNotFoundError(f"Text file not found: {text_file}")
    
    description = text_file.read_text(encoding="utf-8").strip()
    
    return JobJDInput(
        job_id=None,
        company=company,
        title=title,
        location=location,
        description=description,
        candidate_profile=None,  # Will be set by caller if provided
    )


def format_markdown_summary(
    summary: JobJDSummary,
    fit_summary: JobFitSummary = None,
    constraints = None,
) -> str:
    """
    Format a JobJDSummary as a clean Markdown summary.
    
    [Step 1 & 2 改动]
    - 在顶部显示 hard constraints 警告（如果 hard_block=True）
    - 在 spotlight stories 下方显示 evidence snippets
    
    Args:
        summary: JobJDSummary to format
        fit_summary: Optional JobFitSummary for personalized fit analysis
        constraints: Optional ConstraintCheckResult
        
    Returns:
        Markdown string
    """
    lines = []
    
    # Header
    title_str = summary.title or "Unknown Title"
    company_str = summary.company or "Unknown Company"
    lines.append(f"## JD Summary: {title_str} — {company_str}")
    lines.append("")
    
    # [Quick Filter] Quick filter warning at top (if skip_deep_analysis=True)
    if constraints and hasattr(constraints, "skip_deep_analysis") and constraints.skip_deep_analysis:
        lines.append("### ⚠️ **QUICK FILTER: JD does not look like a Data Engineer / LLM Engineer role**")
        lines.append("")
        lines.append("⚠️ Quick filter: JD appears to be a non-target role (e.g., financial sales). Skipping deep analysis.")
        lines.append("")
        if hasattr(constraints, "profile_mismatch_reasons") and constraints.profile_mismatch_reasons:
            lines.append("**Reasons:**")
            for reason in constraints.profile_mismatch_reasons:
                lines.append(f"- {reason}")
            lines.append("")
        lines.append("")
    
    # [Step 1] Hard constraints warning at top (if hard_block=True)
    if constraints and constraints.hard_block:
        lines.append("### ⚠️ **HARD CONSTRAINTS: This role may not be worth deep pursuit**")
        lines.append("")
        if constraints.hard_reasons:
            for reason in constraints.hard_reasons:
                lines.append(f"- ⚠️ {reason}")
            lines.append("")
    
    # Recommendation
    rec_emoji = {
        "APPLY": "✅",
        "MAYBE": "🤔",
        "SKIP": "❌",
    }.get(summary.recommendation, "🤔")
    
    lines.append(f"**Recommendation:** {rec_emoji} {summary.recommendation}")
    lines.append("")
    
    # Reasoning
    if summary.reasoning_summary:
        lines.append(f"**Why:** {summary.reasoning_summary}")
        lines.append("")
    
    # Gold points
    if summary.gold_points:
        lines.append("### 🥇 Gold (公司最想要什么)")
        lines.append("")
        for point in summary.gold_points:
            lines.append(f"- {point}")
        lines.append("")
    
    # Silver points
    if summary.silver_points:
        lines.append("### 🥈 Silver（关键技能/经验）")
        lines.append("")
        for point in summary.silver_points:
            lines.append(f"- {point}")
        lines.append("")
    
    # Bronze points
    if summary.bronze_points:
        lines.append("### 🥉 Bronze（加分项）")
        lines.append("")
        for point in summary.bronze_points:
            lines.append(f"- {point}")
        lines.append("")
    
    # Core skills
    if summary.core_skills:
        skills_str = ", ".join(summary.core_skills)
        lines.append("### 🔧 Core skills")
        lines.append("")
        lines.append(f"- {skills_str}")
        lines.append("")
    
    # Nice-to-have skills
    if summary.nice_to_have_skills:
        skills_str = ", ".join(summary.nice_to_have_skills)
        lines.append("### 💡 Nice-to-have skills")
        lines.append("")
        lines.append(f"- {skills_str}")
        lines.append("")
    
    # Risks / Red flags
    if summary.risks_or_red_flags:
        lines.append("### ⚠️ Risks / Red flags")
        lines.append("")
        for risk in summary.risks_or_red_flags:
            lines.append(f"- {risk}")
        lines.append("")
    else:
        lines.append("### ⚠️ Risks / Red flags")
        lines.append("")
        lines.append("_No significant risks identified._")
        lines.append("")
    
    # Evidence snippets
    if summary.evidence_snippets:
        lines.append("### 📝 Evidence snippets")
        lines.append("")
        for snippet in summary.evidence_snippets:
            lines.append(f"> {snippet}")
            lines.append("")
    
    # Core Signals section (before Reflection)
    if summary.core_signals:
        lines.append("---")
        lines.append("")
        lines.append("## 🔥 Core Signals（这个 JD 最在乎的 2–3 个主题）")
        lines.append("")
        if summary.core_narrative:
            lines.append(summary.core_narrative.strip())
            lines.append("")
        for idx, cs in enumerate(summary.core_signals, start=1):
            importance = f" (**{cs.importance}**)" if cs.importance else ""
            lines.append(f"{idx}. **{cs.theme}**{importance}")
            lines.append("")
            if cs.rationale:
                lines.append(f"   - {cs.rationale.strip()}")
                lines.append("")
            if cs.related_spotlights:
                joined = ", ".join(cs.related_spotlights)
                lines.append(f"   - Related spotlight: {joined}")
                lines.append("")
        lines.append("")
    
    # Reflection section
    has_reflection = (
        summary.reflection_problem_summary or
        summary.reflection_day_in_life or
        summary.reflection_pros_for_candidate or
        summary.reflection_risks_for_candidate or
        summary.lifecycle_summary or
        summary.top_story_points
    )
    if has_reflection:
        lines.append("---")
        lines.append("")
        lines.append("## Reflection / 深度反思（雇主故事 + 生命周期）")
        lines.append("")
        
        if summary.reflection_problem_summary:
            lines.append("### 🎯 Problem the team is trying to solve")
            lines.append("")
            lines.append(summary.reflection_problem_summary)
            lines.append("")
        
        if summary.lifecycle_summary:
            lines.append("### 🔄 Lifecycle Summary（工作生命周期概览）")
            lines.append("")
            lines.append(summary.lifecycle_summary)
            lines.append("")
        
        if summary.reflection_day_in_life:
            lines.append("### 📅 Ideal day-in-the-life")
            lines.append("")
            # Format as bullet points if it's a multi-line string
            day_lines = summary.reflection_day_in_life.strip().split('\n')
            for line in day_lines:
                line = line.strip()
                if line:
                    # Add bullet if not already present
                    if not line.startswith('-') and not line.startswith('•'):
                        lines.append(f"- {line}")
                    else:
                        lines.append(line)
            lines.append("")
        
        if summary.reflection_pros_for_candidate:
            lines.append("### ✅ Pros for Andy")
            lines.append("")
            # Format as bullet points
            pros_lines = summary.reflection_pros_for_candidate.strip().split('\n')
            for line in pros_lines:
                line = line.strip()
                if line:
                    if not line.startswith('-') and not line.startswith('•'):
                        lines.append(f"- {line}")
                    else:
                        lines.append(line)
            lines.append("")
        
        if summary.reflection_risks_for_candidate:
            lines.append("### ⚠️ Risks / possible pitfalls")
            lines.append("")
            # Format as bullet points
            risks_lines = summary.reflection_risks_for_candidate.strip().split('\n')
            for line in risks_lines:
                line = line.strip()
                if line:
                    if not line.startswith('-') and not line.startswith('•'):
                        lines.append(f"- {line}")
                    else:
                        lines.append(line)
            lines.append("")
    
    # Top Story Points section
    if summary.top_story_points:
        lines.append("### 🔑 Top Story Points（上联 / 下联故事）")
        lines.append("")
        for i, story in enumerate(summary.top_story_points, 1):
            lines.append(f"{i}. {story}")
        lines.append("")
    
    # Lifecycle & Spotlight Stories section
    has_lifecycle_stories = (
        summary.lifecycle or
        summary.spotlight_stories
    )
    if has_lifecycle_stories:
        lines.append("---")
        lines.append("")
        lines.append("## Lifecycle & Spotlight Stories（工作生命周期 + 深度故事）")
        lines.append("")
        
        # Lifecycle Summary
        if summary.lifecycle:
            if summary.lifecycle.summary:
                lines.append("### 🔄 Lifecycle Summary（完整工作流概览）")
                lines.append("")
                lines.append(summary.lifecycle.summary)
                lines.append("")
            
            if summary.lifecycle.stages:
                lines.append("### 📋 Lifecycle Stages（工作阶段）")
                lines.append("")
                for i, stage in enumerate(summary.lifecycle.stages, 1):
                    lines.append(f"{i}. {stage}")
                lines.append("")
        
        # Spotlight Stories
        if summary.spotlight_stories:
            lines.append("### 🎯 Spotlight Deep-Dive Stories（关键环节深度分析）")
            lines.append("")
            for i, story in enumerate(summary.spotlight_stories, 1):
                lines.append(f"#### Story {i}: {story.focus_area}")
                lines.append("")
                lines.append(f"**Why Important:** {story.why_important}")
                lines.append("")
                lines.append(f"**Upstream & Downstream:** {story.upstream_downstream}")
                lines.append("")
                lines.append(f"**Tools & Systems:** {story.tools_and_systems}")
                lines.append("")
                lines.append(f"**Constraints & Risks:** {story.constraints_and_risks}")
                lines.append("")
                lines.append(f"**Success Metrics:** {story.success_metrics}")
                lines.append("")
                # [Step 2] Evidence snippets from JD
                if story.evidence_snippets and len(story.evidence_snippets) > 0:
                    lines.append("**Evidence from JD:**")
                    lines.append("")
                    for snippet in story.evidence_snippets:
                        lines.append(f"- {snippet}")
                    lines.append("")
                if i < len(summary.spotlight_stories):
                    lines.append("---")
                    lines.append("")
    
    # Constraint flags (experimental)
    if constraints:
        lines.append("---")
        lines.append("")
        lines.append("### 🔍 Constraint flags (experimental)")
        lines.append("")
        # [Step 1] Show hard_block and hard_reasons if present
        if constraints.hard_block:
            lines.append("- **⚠️ Hard block:** True")
            if constraints.hard_reasons and len(constraints.hard_reasons) > 0:
                lines.append("  **Hard reasons:**")
                for reason in constraints.hard_reasons:
                    lines.append(f"    - {reason}")
        if constraints.soft_flags:
            lines.append(f"- **Soft flags:** {', '.join(constraints.soft_flags)}")
        if constraints.tags:
            lines.append(f"- **Tags:** {', '.join(constraints.tags)}")
        if constraints.reasons:
            lines.append("")
            lines.append("**Reasons:**")
            for reason in constraints.reasons:
                lines.append(f"  - {reason}")
        lines.append("")
    
    # Fit Summary (for candidate)
    if fit_summary:
        lines.append("---")
        lines.append("")
        lines.append("## Fit Summary / 适配小结（for Andy）")
        lines.append("")
        
        # Recommendation
        fit_rec_emoji = {
            "APPLY": "✅",
            "MAYBE": "🤔",
            "SKIP": "❌",
        }.get(fit_summary.recommendation_for_candidate, "🤔")
        
        lines.append(f"- **推荐：** {fit_rec_emoji} **{fit_summary.recommendation_for_candidate}**（for Andy）")
        lines.append("")
        
        # Strengths
        if fit_summary.strengths:
            lines.append("- **我的优势（✅ strengths）：**")
            lines.append("")
            for strength in fit_summary.strengths:
                lines.append(f"  - ✅ {strength}")
            lines.append("")
        else:
            lines.append("- **我的优势（✅ strengths）：**")
            lines.append("")
            lines.append("  - _未识别到明显优势匹配_")
            lines.append("")
        
        # Gaps
        if fit_summary.gaps:
            lines.append("- **关键缺口（⚠️ gaps）：**")
            lines.append("")
            for gap in fit_summary.gaps:
                lines.append(f"  - ⚠️ {gap}")
            lines.append("")
        else:
            lines.append("- **关键缺口（⚠️ gaps）：**")
            lines.append("")
            lines.append("  - _未识别到明显缺口_")
            lines.append("")
        
        # Action items
        if fit_summary.action_items:
            lines.append("- **下一步行动建议（Next actions）：**")
            lines.append("")
            for i, action in enumerate(fit_summary.action_items, 1):
                lines.append(f"  - {i}) {action}")
            lines.append("")
        else:
            lines.append("- **下一步行动建议（Next actions）：**")
            lines.append("")
            lines.append("  - _暂无具体行动建议_")
            lines.append("")
    else:
        lines.append("---")
        lines.append("")
        lines.append("## Fit Summary / 适配小结")
        lines.append("")
        lines.append("_未提供候选人画像，跳过 Fit Summary_")
        lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="JD Interpreter CLI - Test the JD interpreter on individual jobs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From scored jobs file with default profile:
  python -m experiments.jobhunter.jd_explainer_cli \\
    --from-scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \\
    --job-id 4741102008 \\
    --use-default-profile
  
  # From text file with default profile:
  python -m experiments.jobhunter.jd_explainer_cli \\
    --from-text-file path/to/jd.txt \\
    --use-default-profile
  
  # With custom profile file:
  python -m experiments.jobhunter.jd_explainer_cli \\
    --from-scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \\
    --job-id 4983501008 \\
    --profile-file data/jobhunter/candidate_profile_andy.md
  
  # With inline candidate profile (legacy):
  python -m experiments.jobhunter.jd_explainer_cli \\
    --from-scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \\
    --job-id 4983501008 \\
    --candidate-profile "Senior backend/data/LLM engineer, strong in GCP, infra, observability, LangGraph agents."
  
  # Print JSON output:
  python -m experiments.jobhunter.jd_explainer_cli \\
    --from-scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \\
    --job-id 4983501008 \\
    --use-default-profile \\
    --print-json
        """,
    )
    
    # Input modes (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--from-scored-file",
        type=str,
        help="Path to scored jobs JSON file",
    )
    input_group.add_argument(
        "--from-text-file",
        type=str,
        help="Path to text file containing JD",
    )
    
    # Job ID (required for scored file mode)
    parser.add_argument(
        "--job-id",
        type=str,
        help="Job ID to find in scored file (required with --from-scored-file)",
    )
    
    # Optional metadata for text file mode
    parser.add_argument(
        "--title",
        type=str,
        help="Job title (for --from-text-file mode)",
    )
    parser.add_argument(
        "--company",
        type=str,
        help="Company name (for --from-text-file mode)",
    )
    parser.add_argument(
        "--location",
        type=str,
        help="Job location (for --from-text-file mode)",
    )
    
    # Candidate profile options
    profile_group = parser.add_argument_group(
        "candidate profile",
        "Options for providing candidate profile for personalized analysis"
    )
    profile_group.add_argument(
        "--use-default-profile",
        action="store_true",
        default=False,
        help="Use the default candidate profile (Andy's profile) from data/jobhunter/candidate_profile_andy.md",
    )
    profile_group.add_argument(
        "--profile-file",
        type=str,
        default=None,
        help="Path to a custom candidate profile file (relative to project root or absolute path)",
    )
    profile_group.add_argument(
        "--candidate-profile",
        type=str,
        default=None,
        help="Candidate profile as inline text or path to .txt file (legacy option, overrides --use-default-profile and --profile-file)",
    )
    
    # Model
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use (default: {DEFAULT_MODEL})",
    )
    
    # Output options
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print raw JSON output instead of Markdown",
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.from_scored_file and not args.job_id:
        parser.error("--job-id is required when using --from-scored-file")
    
    # Load job
    try:
        if args.from_scored_file:
            scored_path = project_root / args.from_scored_file
            jd = load_job_from_scored_file(scored_path, args.job_id)
            logger.info(f"Loaded job {args.job_id} from {scored_path}")
        else:
            text_path = project_root / args.from_text_file
            jd = load_job_from_text_file(
                text_path,
                title=args.title,
                company=args.company,
                location=args.location,
            )
            logger.info(f"Loaded JD from {text_path}")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Error loading job: {e}")
        sys.exit(1)
    
    # Load candidate profile (priority: --candidate-profile > --profile-file > --use-default-profile)
    if args.candidate_profile:
        # Legacy: inline text or file path
        jd.candidate_profile = load_candidate_profile_text(args.candidate_profile)
        logger.info("Loaded candidate profile from --candidate-profile")
    elif args.profile_file:
        # Custom profile file
        profile_path = project_root / args.profile_file if not Path(args.profile_file).is_absolute() else Path(args.profile_file)
        jd.candidate_profile = load_profile_from_file(profile_path)
        logger.info(f"Loaded candidate profile from {profile_path}")
    elif args.use_default_profile:
        # Default profile (Andy's profile)
        jd.candidate_profile = load_profile_from_file()
        logger.info("Loaded default candidate profile (Andy's profile)")
    
    # Run JD analysis using Flow 1 (LangGraph)
    logger.info(f"Running JD analysis with Flow 1 (LangGraph) using model {args.model}...")
    try:
        # 使用 LangGraph Flow 1 进行 JD 解读和适配度分析
        result = run_jd_analysis(
            jd_input=jd,
            candidate_profile=jd.candidate_profile,
        )
        summary = result.get("jd_summary")
        fit_summary = result.get("fit_summary")
        constraints = result.get("constraints")
        
        if not summary:
            raise ValueError("JD analysis did not return jd_summary")
        
        logger.info("JD analysis complete (using LangGraph Flow 1)")
    except Exception as e:
        logger.error(f"Failed to run JD analysis: {e}", exc_info=True)
        sys.exit(1)
    
    # Output
    if args.print_json:
        # Print JSON
        output = summary.model_dump()
        if fit_summary:
            output["fit_summary"] = fit_summary.model_dump()
        if constraints:
            output["constraints"] = constraints.model_dump()
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        # Print Markdown
        markdown = format_markdown_summary(summary, fit_summary=fit_summary, constraints=constraints)
        print(markdown)


if __name__ == "__main__":
    main()
