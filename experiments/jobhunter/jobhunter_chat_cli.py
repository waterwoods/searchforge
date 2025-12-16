#!/usr/bin/env python3
"""
jobhunter_chat_cli.py - Interactive chat-style CLI for JobHunter
================================================================

A minimal interactive CLI that asks the user a few questions, then runs
the existing JobHunter scoring and reporting pipeline.

Usage:
    python -m experiments.jobhunter.jobhunter_chat_cli

    How to test:
    1) Run the chat CLI:
       python -m experiments.jobhunter.jobhunter_chat_cli
    
    2) Use defaults (anthropic/databricks/openai/perplexityai/scaleai/runwayml, preset llm_core, US-only, etc.)
    
    3) After preview, mark 1–2 jobs as APPLIED and 1 job as SNOOZED:
       - Enter 'a' to mark as applied
       - Enter job number (1-5) or job_id
       - Enter status (a/s/r)
       - Optionally add notes
    
    4) Run again and use [l] to see applications summary:
       - After preview, enter 'l' to list summary
       - Should show correct counts for applied/snoozed/rejected
    
    Expected results:
    - data/jobhunter/applications_log.json is created after marking a job
    - Re-running the CLI and choosing [l] shows correct counts
    - Existing CLIs (job_hunter_agent.py, job_hunter_report.py) still work without modification
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from experiments.jobhunter.job_hunter_agent import run_job_hunter
from experiments.jobhunter.job_hunter_report import run_job_hunter_report
from services.fiqa_api.jobhunter.applications_tracker import (
    load_applications,
    update_application,
    list_by_status,
    get_default_applications_log_path,
)
from services.fiqa_api.jobhunter.schemas import (
    JobPosting,
    JobApplicationStatus,
)


def get_today_date_str() -> str:
    """Get today's date string in YYYYMMDD format."""
    return datetime.now().strftime("%Y%m%d")


def ask_user_preferences() -> Dict[str, Any]:
    """
    Ask user for their job search preferences.
    
    Returns:
        Dictionary with keys: companies, role_presets, location_filters, max_age_days, limit, enable_auto_tune
    """
    print("\n" + "=" * 60)
    print("JobHunter Assistant - Let's find your next role!")
    print("=" * 60)
    print("\nI'll ask you a few questions, then run the scoring pipeline.")
    print("You can press Enter to use the default values.\n")
    
    # Auto-tuning question
    auto_tune_input = input("Enable auto-tuning of filters if the shortlist is too small/too large? (y/n, default=y): ").strip().lower()
    enable_auto_tune = auto_tune_input != "n"
    
    # Company filter
    companies_input = input("Which companies do you want to include? (default: anthropic,databricks,openai,perplexityai,scaleai,runwayml): ").strip()
    if not companies_input:
        companies = ["anthropic", "databricks", "openai", "perplexityai", "scaleai", "runwayml"]
    else:
        companies = [c.strip().lower() for c in companies_input.split(",") if c.strip()]
    
    # Role preset
    role_input = input("Which role type? (1=llm_core, 2=data_ml_platform, 3=both, default=1): ").strip()
    if not role_input or role_input == "1":
        role_presets = ["llm_core"]
    elif role_input == "2":
        role_presets = ["data_ml_platform"]
    elif role_input == "3":
        role_presets = ["llm_core", "data_ml_platform"]
    else:
        print(f"Invalid choice '{role_input}', defaulting to llm_core")
        role_presets = ["llm_core"]
    
    # Location filter
    location_input = input("Only US-based roles? (y/n, default=y): ").strip().lower()
    if not location_input or location_input == "y":
        location_filters = ["San Francisco", "New York", "Seattle", "United States", "Remote (US)"]
    else:
        location_filters = []
    
    # Max age
    max_age_input = input("Max job age in days? (default: 45): ").strip()
    try:
        max_age_days = int(max_age_input) if max_age_input else 45
    except ValueError:
        print(f"Invalid number '{max_age_input}', using default 45")
        max_age_days = 45
    
    # Limit
    limit_input = input("Max number of jobs to score? (default: 50): ").strip()
    try:
        limit = int(limit_input) if limit_input else 50
    except ValueError:
        print(f"Invalid number '{limit_input}', using default 50")
        limit = 50
    
    return {
        "companies": companies,
        "role_presets": role_presets,
        "location_filters": location_filters,
        "max_age_days": max_age_days,
        "limit": limit,
        "enable_auto_tune": enable_auto_tune,
    }


def count_shortlisted_jobs(scored_file: Path, min_match_score: int = 8) -> int:
    """
    Count the number of shortlisted jobs in the scored JSON file.
    
    Applies the same filtering logic as the report:
    - Only counts jobs with category A or B
    - Only counts jobs with match_score >= min_match_score
    
    Args:
        scored_file: Path to the scored jobs JSON file
        min_match_score: Minimum match score threshold (default: 8)
    
    Returns:
        Number of shortlisted jobs
    """
    try:
        with open(scored_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return 0
        
        count = 0
        for item in data:
            score = item.get("score", {})
            category = score.get("category")
            match_score = score.get("match_score", 0)
            
            # Only count A and B categories with sufficient match_score
            if category in ("A", "B") and isinstance(match_score, (int, float)) and match_score >= min_match_score:
                count += 1
        
        return count
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        return 0


def auto_tune_and_rerun_if_needed(
    preset_name: str,
    params: Dict[str, Any],
    scored_file: Path,
    report_file: Path,
    companies: List[str],
    location_filters: List[str],
    date_str: str,
) -> Tuple[int, Dict[str, Any]]:
    """
    Auto-tune parameters and rerun if the shortlist size is outside the target range.
    
    Target range: 5-25 jobs
    
    Adjustment policy:
    - If shortlist_count == 0:
      - If max_age_days < 90: set max_age_days = min(90, max_age_days * 2) and rerun
      - Else: lower min_match_score by 1 (down to minimum 7) and rerun
    - If 0 < shortlist_count < 5:
      - If min_match_score > 8: lower by 1 and rerun
      - Else if max_age_days < 60: set max_age_days = min(60, max_age_days + 15) and rerun
      - Else: increase limit moderately (limit = min(100, limit + 25)) and rerun
    - If shortlist_count > 25:
      - Increase min_match_score by 1 (up to 9) and rerun
    - Otherwise: no auto-tuning
    
    Args:
        preset_name: Keyword preset name
        params: Dictionary with max_age_days, limit, min_match_score
        scored_file: Path to scored JSON file
        report_file: Path to report MD file
        companies: List of company filters
        location_filters: List of location filters
        date_str: Date string in YYYYMMDD format
    
    Returns:
        Tuple of (final_shortlist_count, updated_params)
    """
    TARGET_MIN = 5
    TARGET_MAX = 25
    
    max_age_days = params.get("max_age_days", 45)
    limit = params.get("limit", 50)
    min_match_score = params.get("min_match_score", 8)
    
    # Count initial shortlist
    shortlist_count = count_shortlisted_jobs(scored_file, min_match_score)
    
    print(f"\nInitial shortlist: {shortlist_count} jobs")
    
    # Check if auto-tuning is needed
    if TARGET_MIN <= shortlist_count <= TARGET_MAX:
        print("Shortlist size is within target range (5-25). No auto-tuning needed.")
        return shortlist_count, params
    
    # Determine adjustments
    adjustments = []
    new_max_age_days = max_age_days
    new_limit = limit
    new_min_match_score = min_match_score
    
    if shortlist_count == 0:
        if max_age_days < 90:
            new_max_age_days = min(90, max_age_days * 2)
            adjustments.append(f"increased max_age_days from {max_age_days} to {new_max_age_days}")
        else:
            new_min_match_score = max(7, min_match_score - 1)
            adjustments.append(f"lowered min_match_score from {min_match_score} to {new_min_match_score}")
    
    elif 0 < shortlist_count < TARGET_MIN:
        if min_match_score > 8:
            new_min_match_score = min_match_score - 1
            adjustments.append(f"lowered min_match_score from {min_match_score} to {new_min_match_score}")
        elif max_age_days < 60:
            new_max_age_days = min(60, max_age_days + 15)
            adjustments.append(f"increased max_age_days from {max_age_days} to {new_max_age_days}")
        else:
            new_limit = min(100, limit + 25)
            adjustments.append(f"increased limit from {limit} to {new_limit}")
    
    elif shortlist_count > TARGET_MAX:
        new_min_match_score = min(9, min_match_score + 1)
        adjustments.append(f"increased min_match_score from {min_match_score} to {new_min_match_score}")
    
    # If no adjustments needed, return as-is
    if not adjustments:
        return shortlist_count, params
    
    # Print auto-tuning message
    print(f"Shortlist too {'small' if shortlist_count < TARGET_MIN else 'large'} ({shortlist_count} jobs).")
    print(f"Auto-tuning: {', '.join(adjustments)}")
    
    # Rerun with adjusted parameters
    try:
        # Rerun scoring with updated max_age_days and limit
        run_job_hunter(
            company_filters=companies,
            keyword_preset=preset_name,
            keyword_filters=[],
            location_filters=location_filters,
            max_age_days=new_max_age_days,
            limit=new_limit,
            output_file=scored_file,
            input_file=None,
            model="gpt-4o-mini",
        )
        
        # Rerun reporting with updated min_match_score
        run_job_hunter_report(
            input_file=scored_file,
            output_file=report_file,
            min_match_score=new_min_match_score,
            include_b=True,
        )
        
        # Recompute shortlist count
        final_shortlist_count = count_shortlisted_jobs(scored_file, new_min_match_score)
        print(f"Final shortlist: {final_shortlist_count} jobs")
        
        # Return updated params
        updated_params = {
            "max_age_days": new_max_age_days,
            "limit": new_limit,
            "min_match_score": new_min_match_score,
        }
        
        return final_shortlist_count, updated_params
        
    except Exception as e:
        print(f"Error during auto-tuning rerun: {e}")
        # Return original results if rerun fails
        return shortlist_count, params


def run_pipeline_for_preset(
    preset: str,
    companies: List[str],
    location_filters: List[str],
    max_age_days: int,
    limit: int,
    date_str: str,
    enable_auto_tune: bool = False,
) -> Tuple[Path, Path, int, int]:
    """
    Run the scoring and reporting pipeline for a single keyword preset.
    
    Args:
        preset: Keyword preset name ('llm_core' or 'data_ml_platform')
        companies: List of company filters
        location_filters: List of location filters
        max_age_days: Maximum job age in days
        limit: Maximum number of jobs to score
        date_str: Date string in YYYYMMDD format
        enable_auto_tune: Whether to enable auto-tuning (default: False)
    
    Returns:
        Tuple of (scored_json_path, report_md_path, shortlist_count, final_min_match_score)
    """
    print(f"\n{'=' * 60}")
    print(f"Running pipeline for preset: {preset}")
    print(f"{'=' * 60}\n")
    
    # Build output paths
    scored_json_path = project_root / "data" / "jobhunter" / "scored" / f"jobs_scored_{preset}_{date_str}.json"
    report_md_path = project_root / "reports" / "jobhunter" / f"job_shortlist_{preset}_{date_str}.md"
    
    # Initial parameters
    min_match_score = 8
    current_params = {
        "max_age_days": max_age_days,
        "limit": limit,
        "min_match_score": min_match_score,
    }
    
    # Run scoring
    try:
        run_job_hunter(
            company_filters=companies,
            keyword_preset=preset,
            keyword_filters=[],
            location_filters=location_filters,
            max_age_days=max_age_days,
            limit=limit,
            output_file=scored_json_path,
            input_file=None,  # Use default (today's normalized file)
            model="gpt-4o-mini",
        )
    except Exception as e:
        print(f"\nError during scoring: {e}")
        raise
    
    # Run reporting
    try:
        run_job_hunter_report(
            input_file=scored_json_path,
            output_file=report_md_path,
            min_match_score=min_match_score,
            include_b=True,
        )
    except Exception as e:
        print(f"\nError during report generation: {e}")
        raise
    
    # Auto-tuning if enabled
    shortlist_count = count_shortlisted_jobs(scored_json_path, min_match_score)
    
    if enable_auto_tune:
        shortlist_count, current_params = auto_tune_and_rerun_if_needed(
            preset_name=preset,
            params=current_params,
            scored_file=scored_json_path,
            report_file=report_md_path,
            companies=companies,
            location_filters=location_filters,
            date_str=date_str,
        )
        # Update min_match_score from tuned params
        min_match_score = current_params.get("min_match_score", min_match_score)
    
    return scored_json_path, report_md_path, shortlist_count, min_match_score


def print_shortlist_preview(scored_json_path: Path, preset: str, min_match_score: int = 8) -> List[Dict[str, Any]]:
    """
    Print a preview of the top 5 shortlisted jobs from the scored JSON file.
    
    Args:
        scored_json_path: Path to the scored jobs JSON file
        preset: Keyword preset name for display
        min_match_score: Minimum match score threshold (default: 8)
    
    Returns:
        List of top 5 shortlisted job dictionaries (for use in interactive updates)
    """
    try:
        with open(scored_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"Warning: Expected list in {scored_json_path}, got {type(data)}")
            return
        
        if not data:
            print(f"No jobs found in {scored_json_path}")
            return
        
        # Sort: A before B, then match_score desc, then seniority_score desc
        sorted_data = sorted(
            data,
            key=lambda x: (
                x.get("score", {}).get("category", "Z"),  # A < B < C
                -x.get("score", {}).get("match_score", 0),  # Higher is better
                -x.get("score", {}).get("seniority_score", 0),  # Higher is better
            ),
        )
        
        # Filter to only A and B categories with sufficient match_score
        filtered = [
            item for item in sorted_data
            if item.get("score", {}).get("category") in ("A", "B")
            and item.get("score", {}).get("match_score", 0) >= min_match_score
        ]
        
        print(f"\n{'=' * 60}")
        print(f"Top 5 Shortlisted Jobs ({preset})")
        print(f"{'=' * 60}\n")
        
        top_5 = filtered[:5]
        if not top_5:
            print(f"No jobs matched the criteria (category A/B with match_score >= {min_match_score})")
            return []
        
        for idx, item in enumerate(top_5, 1):
            job = item.get("job", {})
            score = item.get("score", {})
            
            title = job.get("title", "Unknown Title")
            company = job.get("company", "Unknown Company")
            location = job.get("location") or "Location not specified"
            category = score.get("category", "?")
            match_score = score.get("match_score", "?")
            
            print(f"{idx}. {title}")
            print(f"   Company: {company}")
            print(f"   Location: {location}")
            print(f"   Category: {category} | Match Score: {match_score}/10")
            print()
        
        return top_5
        
    except FileNotFoundError:
        print(f"Warning: Could not read {scored_json_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse JSON from {scored_json_path}: {e}")
        return []
    except Exception as e:
        print(f"Warning: Error reading shortlist preview: {e}")
        return []


def interactive_update_applications(
    scored_jobs: List[Dict[str, Any]],
    preset_name: str,
) -> None:
    """
    Allow user to mark a few jobs as applied/snoozed/rejected.
    
    Uses applications_tracker module under the hood.
    
    Args:
        scored_jobs: List of scored job dictionaries from the shortlist preview.
        preset_name: Preset name for display purposes.
    """
    if not scored_jobs:
        return
    
    print("\n" + "=" * 60)
    print("Application Status Tracker")
    print("=" * 60)
    print("\nYou can now mark applications:")
    print("  [a] Mark job as APPLIED")
    print("  [s] Mark job as SNOOZED (decide later)")
    print("  [r] Mark job as REJECTED")
    print("  [l] List existing applications summary")
    print("  [enter] Skip and continue")
    
    user_input = input("\nEnter your choice: ").strip().lower()
    
    if not user_input:
        # User pressed Enter, skip
        return
    
    if user_input == "l":
        # List summary
        log_path = get_default_applications_log_path()
        records = load_applications(log_path)
        applied_count = len(list_by_status(records, JobApplicationStatus.APPLIED))
        snoozed_count = len(list_by_status(records, JobApplicationStatus.SNOOZED))
        rejected_count = len(list_by_status(records, JobApplicationStatus.REJECTED))
        
        print("\nApplications summary:")
        print(f"  applied: {applied_count}")
        print(f"  snoozed: {snoozed_count}")
        print(f"  rejected: {rejected_count}")
        return
    
    # Parse job identifier (index or job_id)
    job_identifier = input("Enter job number (1-5) or job_id: ").strip()
    if not job_identifier:
        print("No job identifier provided. Skipping.")
        return
    
    # Try to find the job
    job_dict = None
    
    # First, try as index (1-based)
    try:
        idx = int(job_identifier) - 1
        if 0 <= idx < len(scored_jobs):
            job_dict = scored_jobs[idx]
    except ValueError:
        # Not a number, try as job_id
        for item in scored_jobs:
            if item.get("job", {}).get("job_id") == job_identifier:
                job_dict = item
                break
    
    if not job_dict:
        print(f"Job not found: {job_identifier}")
        return
    
    # Get status choice
    status_input = input("Status (a=applied, s=snoozed, r=rejected): ").strip().lower()
    status_map = {
        "a": JobApplicationStatus.APPLIED,
        "s": JobApplicationStatus.SNOOZED,
        "r": JobApplicationStatus.REJECTED,
    }
    
    if status_input not in status_map:
        print(f"Invalid status '{status_input}'. Skipping.")
        return
    
    status = status_map[status_input]
    
    # Get optional notes
    notes = input("Optional notes (press Enter to skip): ").strip()
    if not notes:
        notes = None
    
    # Create JobPosting from job_dict
    job_data = job_dict.get("job", {})
    try:
        job = JobPosting(**job_data)
    except Exception as e:
        print(f"Error creating JobPosting: {e}")
        return
    
    # Update application
    try:
        log_path = get_default_applications_log_path()
        record = update_application(job, status, notes, log_path)
        print(f"\n✓ Updated: {job.title} at {job.company} -> {status.value}")
        if notes:
            print(f"  Notes: {notes}")
    except Exception as e:
        print(f"Error updating application: {e}")


def main() -> None:
    """Main entry point for the interactive CLI."""
    try:
        while True:
            # Get user preferences
            prefs = ask_user_preferences()
            
            date_str = get_today_date_str()
            
            # Run pipeline for each selected preset
            results = []
            for preset in prefs["role_presets"]:
                try:
                    scored_path, report_path, shortlist_count, final_min_match_score = run_pipeline_for_preset(
                        preset=preset,
                        companies=prefs["companies"],
                        location_filters=prefs["location_filters"],
                        max_age_days=prefs["max_age_days"],
                        limit=prefs["limit"],
                        date_str=date_str,
                        enable_auto_tune=prefs.get("enable_auto_tune", False),
                    )
                    
                    results.append({
                        "preset": preset,
                        "scored_json": scored_path,
                        "report_md": report_path,
                        "shortlist_count": shortlist_count,
                    })
                    
                    # Print shortlist preview
                    top_jobs = print_shortlist_preview(scored_path, preset, final_min_match_score)
                    
                    # Interactive application status updates
                    if top_jobs:
                        interactive_update_applications(top_jobs, preset)
                    
                except Exception as e:
                    print(f"\nError processing preset '{preset}': {e}")
                    continue
            
            # Print summary
            print(f"\n{'=' * 60}")
            print("Summary")
            print(f"{'=' * 60}\n")
            
            for result in results:
                print(f"Preset: {result['preset']}")
                print(f"  Shortlisted jobs: {result.get('shortlist_count', 'N/A')}")
                print(f"  Scored JSON: {result['scored_json']}")
                print(f"  Report: {result['report_md']}")
                print()
            
            if results:
                print("You can open the full reports in:")
                for result in results:
                    print(f"  - {result['report_md']}")
                
                print()
                print("You can now refine this shortlist with your personal preferences:")
                print()
                print("1) Rate jobs (1-5) via:")
                for result in results:
                    print(f"   python -m experiments.jobhunter.job_preferences_cli --scored-file {result['scored_json']}")
                print()
                print("2) Regenerate report with re-ranking:")
                for result in results:
                    print(f"   python -m experiments.jobhunter.job_hunter_report --use-preferences --input-file {result['scored_json']}")
                print()
            
            # Ask if user wants to run another search
            print()
            again = input("Run another search? (y/n, default=n): ").strip().lower()
            if again != "y":
                break
            
            print()
        
        print("\nThank you for using JobHunter Assistant! Good luck with your job search!\n")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
