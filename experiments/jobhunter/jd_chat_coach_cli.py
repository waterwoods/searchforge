#!/usr/bin/env python3
"""
jd_chat_coach_cli.py - Multi-turn Chat Coach for JD Analysis
============================================================

A multi-turn conversational CLI that:
1. Loads a JD (from scored file or text file)
2. Runs initial "health check" (JD interpretation + job fit analysis)
3. Enters interactive chat mode for follow-up questions

Usage:
    # From scored file with job-id:
    python -m experiments.jobhunter.jd_chat_coach_cli \
      --scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
      --job-id 4741102008 \
      --use-default-profile
    
    # From text file:
    python -m experiments.jobhunter.jd_chat_coach_cli \
      --jd-file path/to/jd.txt \
      --use-default-profile
    
    # Find latest scored file automatically:
    python -m experiments.jobhunter.jd_chat_coach_cli \
      --job-id 4741102008 \
      --use-default-profile
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.jobhunter.jd_interpreter import DEFAULT_MODEL
from services.fiqa_api.jobhunter.schemas import JobJDInput, JobJDSummary
from services.fiqa_api.jobhunter.profile_loader import load_candidate_profile
from services.fiqa_api.clients import get_openai_client
from services.fiqa_api.jobhunter.graphs.jd_analysis_graph import run_jd_analysis
from services.fiqa_api.jobhunter.graphs.jd_chat_graph import build_jd_chat_graph
from services.fiqa_api.telemetry.langsmith_config import (
    is_langsmith_enabled,
    default_langsmith_run_config,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def find_latest_scored_file(scored_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Find the latest scored jobs file matching the pattern.
    
    Looks for files matching: data/jobhunter/scored/jobs_scored_*_latest.json
    If none found, tries: data/jobhunter/scored/jobs_scored_*.json
    
    Args:
        scored_dir: Directory to search (default: data/jobhunter/scored)
        
    Returns:
        Path to latest scored file, or None if not found
    """
    if scored_dir is None:
        scored_dir = project_root / "data" / "jobhunter" / "scored"
    
    if not scored_dir.exists():
        return None
    
    # First try *_latest.json files
    latest_files = sorted(scored_dir.glob("jobs_scored_*_latest.json"), reverse=True)
    if latest_files:
        return latest_files[0]
    
    # Fallback to any jobs_scored_*.json files (sorted by modification time)
    all_files = list(scored_dir.glob("jobs_scored_*.json"))
    if all_files:
        all_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return all_files[0]
    
    return None


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


def load_job_from_text_file(
    text_file: Path,
    title: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
) -> JobJDInput:
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


def print_initial_summary(
    jd_summary: JobJDSummary,
    fit_summary: Optional[any] = None,
) -> None:
    """
    Print a concise initial summary for the user.
    
    Args:
        jd_summary: Job JD summary
        fit_summary: Optional job fit summary
    """
    print("\n" + "=" * 60)
    print("📋 JD 初步分析完成")
    print("=" * 60)
    
    # Job info
    title_str = jd_summary.title or "Unknown Title"
    company_str = jd_summary.company or "Unknown Company"
    location_str = jd_summary.location or "Unknown Location"
    print(f"\n职位: {title_str} @ {company_str}")
    print(f"地点: {location_str}")
    
    # Recommendation
    rec_emoji = {
        "APPLY": "✅",
        "MAYBE": "🤔",
        "SKIP": "❌",
    }.get(jd_summary.recommendation, "🤔")
    
    print(f"\n推荐: {rec_emoji} {jd_summary.recommendation}")
    if jd_summary.reasoning_summary:
        print(f"理由: {jd_summary.reasoning_summary}")
    
    # Top 3 gold points
    if jd_summary.gold_points:
        print("\n🥇 核心要点 (Top 3):")
        for i, point in enumerate(jd_summary.gold_points[:3], 1):
            print(f"  {i}. {point}")
    
    # Fit summary if available
    if fit_summary:
        print("\n" + "-" * 60)
        print("📊 适配分析 (for you):")
        
        fit_rec_emoji = {
            "APPLY": "✅",
            "MAYBE": "🤔",
            "SKIP": "❌",
        }.get(fit_summary.recommendation_for_candidate, "🤔")
        
        print(f"推荐: {fit_rec_emoji} {fit_summary.recommendation_for_candidate}")
        
        if fit_summary.strengths:
            print("\n✅ 你的优势:")
            for strength in fit_summary.strengths[:3]:
                print(f"  • {strength}")
        
        if fit_summary.gaps:
            print("\n⚠️  关键缺口:")
            for gap in fit_summary.gaps[:2]:
                print(f"  • {gap}")
    
    print("\n" + "=" * 60)
    print("💬 现在可以开始提问了！")
    print("   - 输入问题继续对话")
    print("   - 输入 /summary 查看完整摘要")
    print("   - 输入 /exit 或 /quit 退出")
    print("=" * 60 + "\n")


def format_full_summary(
    jd_summary: JobJDSummary,
    fit_summary: Optional[any] = None,
) -> str:
    """
    Format a full summary for /summary command.
    
    Args:
        jd_summary: Job JD summary
        fit_summary: Optional job fit summary
        
    Returns:
        Formatted summary string
    """
    lines = []
    
    # Header
    title_str = jd_summary.title or "Unknown Title"
    company_str = jd_summary.company or "Unknown Company"
    lines.append(f"## JD Summary: {title_str} — {company_str}")
    lines.append("")
    
    # Recommendation
    rec_emoji = {
        "APPLY": "✅",
        "MAYBE": "🤔",
        "SKIP": "❌",
    }.get(jd_summary.recommendation, "🤔")
    
    lines.append(f"**Recommendation:** {rec_emoji} {jd_summary.recommendation}")
    lines.append("")
    
    # Reasoning
    if jd_summary.reasoning_summary:
        lines.append(f"**Why:** {jd_summary.reasoning_summary}")
        lines.append("")
    
    # Gold points
    if jd_summary.gold_points:
        lines.append("### 🥇 Gold (公司最想要什么)")
        lines.append("")
        for point in jd_summary.gold_points:
            lines.append(f"- {point}")
        lines.append("")
    
    # Silver points
    if jd_summary.silver_points:
        lines.append("### 🥈 Silver（关键技能/经验）")
        lines.append("")
        for point in jd_summary.silver_points:
            lines.append(f"- {point}")
        lines.append("")
    
    # Core skills
    if jd_summary.core_skills:
        skills_str = ", ".join(jd_summary.core_skills)
        lines.append("### 🔧 Core skills")
        lines.append("")
        lines.append(f"- {skills_str}")
        lines.append("")
    
    # Risks / Red flags
    if jd_summary.risks_or_red_flags:
        lines.append("### ⚠️ Risks / Red flags")
        lines.append("")
        for risk in jd_summary.risks_or_red_flags:
            lines.append(f"- {risk}")
        lines.append("")
    
    # Fit Summary (for candidate)
    if fit_summary:
        lines.append("---")
        lines.append("")
        lines.append("## Fit Summary / 适配小结（for you）")
        lines.append("")
        
        fit_rec_emoji = {
            "APPLY": "✅",
            "MAYBE": "🤔",
            "SKIP": "❌",
        }.get(fit_summary.recommendation_for_candidate, "🤔")
        
        lines.append(f"- **推荐：** {fit_rec_emoji} **{fit_summary.recommendation_for_candidate}**")
        lines.append("")
        
        # Strengths
        if fit_summary.strengths:
            lines.append("- **我的优势（✅ strengths）：**")
            lines.append("")
            for strength in fit_summary.strengths:
                lines.append(f"  - ✅ {strength}")
            lines.append("")
        
        # Gaps
        if fit_summary.gaps:
            lines.append("- **关键缺口（⚠️ gaps）：**")
            lines.append("")
            for gap in fit_summary.gaps:
                lines.append(f"  - ⚠️ {gap}")
            lines.append("")
        
        # Action items
        if fit_summary.action_items:
            lines.append("- **下一步行动建议（Next actions）：**")
            lines.append("")
            for i, action in enumerate(fit_summary.action_items, 1):
                lines.append(f"  - {i}) {action}")
            lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="JD Chat Coach - Multi-turn conversational JD analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From scored file with job-id:
  python -m experiments.jobhunter.jd_chat_coach_cli \\
    --scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \\
    --job-id 4741102008 \\
    --use-default-profile
  
  # From text file:
  python -m experiments.jobhunter.jd_chat_coach_cli \\
    --jd-file path/to/jd.txt \\
    --use-default-profile
  
  # Find latest scored file automatically:
  python -m experiments.jobhunter.jd_chat_coach_cli \\
    --job-id 4741102008 \\
    --use-default-profile
        """,
    )
    
    # Input options
    parser.add_argument(
        "--scored-file",
        type=str,
        default=None,
        help="Path to scored jobs JSON file (if not provided, will try to find latest)",
    )
    parser.add_argument(
        "--job-id",
        type=str,
        default=None,
        help="Job ID to find in scored file (required with --scored-file or when auto-finding)",
    )
    parser.add_argument(
        "--jd-file",
        type=str,
        default=None,
        help="Path to text file containing JD",
    )
    
    # Optional metadata for text file mode
    parser.add_argument(
        "--title",
        type=str,
        help="Job title (for --jd-file mode)",
    )
    parser.add_argument(
        "--company",
        type=str,
        help="Company name (for --jd-file mode)",
    )
    parser.add_argument(
        "--location",
        type=str,
        help="Job location (for --jd-file mode)",
    )
    
    # Candidate profile
    parser.add_argument(
        "--use-default-profile",
        action="store_true",
        default=True,
        help="Use the default candidate profile (Andy's profile) from data/jobhunter/candidate_profile_andy.md (default: True)",
    )
    parser.add_argument(
        "--no-profile",
        action="store_true",
        help="Don't use any candidate profile",
    )
    
    # Model
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use (default: {DEFAULT_MODEL})",
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.jd_file and not args.job_id:
        parser.error("Must provide either --jd-file or --job-id")
    
    if args.jd_file and args.job_id:
        parser.error("Cannot use both --jd-file and --job-id")
    
    if args.job_id and not args.scored_file:
        # Try to find latest scored file
        latest_file = find_latest_scored_file()
        if latest_file:
            args.scored_file = str(latest_file)
            logger.info(f"Auto-found latest scored file: {args.scored_file}")
        else:
            parser.error("--job-id requires --scored-file or a scored file in data/jobhunter/scored/")
    
    # Load job
    try:
        if args.job_id:
            scored_path = project_root / args.scored_file
            jd = load_job_from_scored_file(scored_path, args.job_id)
            logger.info(f"Loaded job {args.job_id} from {scored_path}")
        else:
            text_path = project_root / args.jd_file if not Path(args.jd_file).is_absolute() else Path(args.jd_file)
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
    
    # Load candidate profile
    candidate_profile = None
    if not args.no_profile and args.use_default_profile:
        try:
            candidate_profile = load_candidate_profile()
            jd.candidate_profile = candidate_profile
            logger.info("Loaded default candidate profile (Andy's profile)")
        except Exception as e:
            logger.warning(f"Failed to load default profile: {e}")
    
    # Run initial analysis using Flow 1 (LangGraph)
    print("\n🔍 正在分析 JD（使用 LangGraph Flow 1）...")
    try:
        result = run_jd_analysis(
            jd_input=jd,
            candidate_profile=candidate_profile,
        )
        jd_summary = result.get("jd_summary")
        fit_summary = result.get("fit_summary")
        
        if not jd_summary:
            raise ValueError("JD analysis did not return jd_summary")
        
        logger.info("JD analysis complete (using LangGraph Flow 1)")
    except Exception as e:
        logger.error(f"Failed to run JD analysis: {e}", exc_info=True)
        sys.exit(1)
    
    # Print initial summary
    print_initial_summary(jd_summary, fit_summary)
    
    # Build chat graph using Flow 2 (LangGraph)
    print("💬 初始化对话系统（使用 LangGraph Flow 2）...")
    chat_graph = build_jd_chat_graph().compile()
    
    # Initialize chat state
    from services.fiqa_api.jobhunter.schemas import JDChatState
    
    chat_state: JDChatState = {
        "jd_input": jd,
        "jd_summary": jd_summary,
        "fit_summary": fit_summary,
        "candidate_profile": candidate_profile,
        "history": [],
        "last_user_message": None,
        "last_response": None,
    }
    
    # Enter chat loop
    print("💬 对话开始（输入 /exit 或 /quit 退出）\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in {"/exit", "/quit"}:
                print("\n👋 再见！祝求职顺利！\n")
                break
            
            if user_input.lower() == "/summary":
                print("\n" + "=" * 60)
                print("📋 完整摘要")
                print("=" * 60)
                print(format_full_summary(jd_summary, fit_summary))
                print("=" * 60 + "\n")
                continue
            
            # Update chat state with user message
            chat_state["last_user_message"] = user_input
            
            # Generate response using Flow 2 (LangGraph)
            print("\n🤖 Coach: ", end="", flush=True)
            if is_langsmith_enabled():
                config = default_langsmith_run_config("jobhunter_jd_chat")
                result_state = chat_graph.invoke(chat_state, config=config)
            else:
                result_state = chat_graph.invoke(chat_state)
            
            # Update chat state with response
            chat_state["last_response"] = result_state.get("last_response")
            chat_state["history"] = result_state.get("history", chat_state["history"])
            
            response = result_state.get("last_response", "抱歉，无法生成回答。")
            print(response)
            print()  # Empty line for readability
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！祝求职顺利！\n")
            break
        except EOFError:
            print("\n\n👋 再见！祝求职顺利！\n")
            break
        except Exception as e:
            logger.error(f"Error in chat loop: {e}", exc_info=True)
            print(f"\n❌ 发生错误: {e}\n")


if __name__ == "__main__":
    main()
