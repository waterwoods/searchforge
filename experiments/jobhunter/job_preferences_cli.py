#!/usr/bin/env python3
"""
job_preferences_cli.py - Interactive CLI for rating job preferences.

A minimal RLHF-style feedback loop: rate jobs (1-5) and optionally tag them,
then use these preferences to re-rank shortlists in job_hunter_report.py.

Test plan:
1) Run a JobHunter scoring pipeline to produce a scored jobs JSON.
2) Run the preference CLI to rate a few jobs.
3) Run the report generator with --use-preferences and confirm:
   - rated jobs show a "User rating" line,
   - the order changes when ratings are very high or very low.
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.jobhunter.schemas import JobPreferenceRecord
from services.fiqa_api.jobhunter.preferences_store import upsert_preference, get_default_preferences_path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def find_latest_scored_file() -> Optional[Path]:
    """
    Find the latest scored jobs file matching the pattern.
    
    Looks for files matching: data/jobhunter/scored/jobs_scored_*_latest.json
    If none found, tries: data/jobhunter/scored/jobs_scored_*.json
    
    Returns:
        Path to the latest file, or None if none found
    """
    scored_dir = project_root / "data" / "jobhunter" / "scored"
    
    if not scored_dir.exists():
        return None
    
    # First try *_latest.json files
    latest_files = sorted(scored_dir.glob("jobs_scored_*_latest.json"), reverse=True)
    if latest_files:
        return latest_files[0]
    
    # Fallback to any jobs_scored_*.json files
    all_files = sorted(scored_dir.glob("jobs_scored_*.json"), reverse=True)
    if all_files:
        return all_files[0]
    
    return None


def load_scored_jobs(path: Path) -> List[Dict[str, Any]]:
    """Load scored jobs from JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Scored jobs file not found: {path}")
    
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {path}, got {type(data)}")
    
    return data


def filter_and_sort_jobs(
    jobs: List[Dict[str, Any]],
    min_match_score: int,
    max_jobs: int,
) -> List[Dict[str, Any]]:
    """
    Filter jobs by category (A/B) and match_score, then sort and limit.
    
    Args:
        jobs: List of scored job dictionaries
        min_match_score: Minimum match_score to include
        max_jobs: Maximum number of jobs to return
    
    Returns:
        Filtered and sorted list of job dictionaries
    """
    filtered = []
    
    for item in jobs:
        score = item.get("score", {})
        category = score.get("category")
        match_score = score.get("match_score", 0)
        
        # Only keep A and B categories with sufficient match_score
        if category in ("A", "B") and isinstance(match_score, (int, float)) and match_score >= min_match_score:
            filtered.append(item)
    
    # Sort: A before B, then match_score desc, then seniority_score desc
    filtered.sort(
        key=lambda x: (
            x.get("score", {}).get("category", "Z"),  # A < B
            -x.get("score", {}).get("match_score", 0),  # Higher is better
            -x.get("score", {}).get("seniority_score", 0),  # Higher is better
        ),
    )
    
    # Limit to max_jobs
    return filtered[:max_jobs]


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length, adding ellipsis if needed."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def print_job_info(item: Dict[str, Any], index: int, total: int) -> None:
    """Print job information in a clear format."""
    job = item.get("job", {})
    score = item.get("score", {})
    
    job_id = job.get("job_id", "?")
    title = job.get("title", "Unknown Title")
    company = job.get("company", "Unknown Company")
    location = job.get("location") or "Location not specified"
    description = job.get("description", "")
    category = score.get("category", "?")
    match_score = score.get("match_score", "?")
    
    print("\n" + "=" * 70)
    print(f"[{index}/{total}] {title}")
    print("=" * 70)
    print(f"Job ID: {job_id}")
    print(f"Company: {company}")
    print(f"Location: {location}")
    print(f"Category: {category} | Match Score: {match_score}/10")
    print()
    
    # Show truncated description
    if description:
        # Strip HTML tags crudely (basic approach)
        desc_text = description.replace("<", " <").replace(">", "> ")
        words = desc_text.split()
        desc_clean = " ".join(words)[:400]
        print(f"Description preview: {desc_clean}...")
        print()


def collect_rating() -> Optional[int]:
    """
    Prompt user for a rating (1-5).
    
    Returns:
        Rating (1-5) if provided, None if skipped, -1 if quit
    """
    while True:
        user_input = input("Rating for this job (1-5, Enter to skip, q to quit): ").strip().lower()
        
        if not user_input:
            # Skip
            return None
        
        if user_input == "q":
            # Quit
            return -1
        
        try:
            rating = int(user_input)
            if 1 <= rating <= 5:
                return rating
            else:
                print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Please enter a number between 1 and 5, or press Enter to skip, or 'q' to quit.")


def collect_tags() -> Optional[List[str]]:
    """
    Prompt user for optional tags.
    
    Returns:
        List of tags (lowercased, stripped) if provided, None if skipped
    """
    user_input = input("Tags (comma separated, optional, Enter to skip): ").strip()
    
    if not user_input:
        return None
    
    # Split by comma, lowercase, strip whitespace
    tags = [tag.strip().lower() for tag in user_input.split(",") if tag.strip()]
    return tags if tags else None


def collect_notes() -> Optional[str]:
    """
    Prompt user for optional notes.
    
    Returns:
        Notes string if provided, None if skipped
    """
    user_input = input("Notes (optional, Enter to skip): ").strip()
    return user_input if user_input else None


def rate_jobs_interactive(
    jobs: List[Dict[str, Any]],
    min_match_score: int,
    max_jobs: int,
) -> tuple[int, int]:
    """
    Interactive rating loop.
    
    Args:
        jobs: List of all scored job dictionaries
        min_match_score: Minimum match_score to consider
        max_jobs: Maximum number of jobs to rate
    
    Returns:
        Tuple of (rated_count, skipped_count)
    """
    # Filter and sort
    filtered_jobs = filter_and_sort_jobs(jobs, min_match_score, max_jobs)
    
    if not filtered_jobs:
        print(f"No jobs found matching criteria (category A/B, match_score >= {min_match_score})")
        return 0, 0
    
    print(f"\nFound {len(filtered_jobs)} jobs to rate (showing up to {max_jobs})")
    print("You'll be asked to rate each job from 1 (dislike) to 5 (very like).")
    
    rated_count = 0
    skipped_count = 0
    
    for idx, item in enumerate(filtered_jobs, 1):
        job = item.get("job", {})
        score = item.get("score", {})
        
        # Print job info
        print_job_info(item, idx, len(filtered_jobs))
        
        # Collect rating
        rating = collect_rating()
        
        if rating == -1:
            # User quit
            print("\nRating session cancelled by user.")
            break
        
        if rating is None:
            # User skipped
            skipped_count += 1
            print("Skipped.")
            continue
        
        # Collect optional tags
        tags = collect_tags()
        
        # Collect optional notes
        notes = collect_notes()
        
        # Extract source from job or score
        source = job.get("source")
        
        # Create preference record
        try:
            record = JobPreferenceRecord(
                job_id=job.get("job_id", ""),
                company=job.get("company", ""),
                title=job.get("title", ""),
                source=source,
                user_rating=rating,
                tags=tags,
                notes=notes,
                rated_at=datetime.utcnow(),
            )
            
            # Save preference
            upsert_preference(record)
            rated_count += 1
            print(f"✓ Saved rating: {rating}/5")
            
        except Exception as e:
            logger.error(f"Failed to save preference for job {job.get('job_id')}: {e}")
            print(f"Error saving preference: {e}")
    
    return rated_count, skipped_count


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rate job preferences interactively (RLHF-style feedback)"
    )
    
    parser.add_argument(
        "--scored-file",
        type=str,
        default=None,
        help="Path to scored jobs JSON file (default: auto-detect latest)",
    )
    
    parser.add_argument(
        "--min-match-score",
        type=int,
        default=8,
        help="Minimum match_score to consider for rating (default: 8)",
    )
    
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=20,
        help="Maximum number of jobs to rate (default: 20)",
    )
    
    args = parser.parse_args()
    
    # Determine scored file path
    if args.scored_file:
        scored_path = Path(args.scored_file)
        if not scored_path.is_absolute():
            scored_path = project_root / scored_path
    else:
        scored_path = find_latest_scored_file()
        if not scored_path:
            print("Error: Could not find any scored jobs file.")
            print("Please provide --scored-file or run job_hunter_agent.py first.")
            sys.exit(1)
    
    print(f"Using scored jobs file: {scored_path}")
    
    # Load jobs
    try:
        jobs = load_scored_jobs(scored_path)
        print(f"Loaded {len(jobs)} scored jobs")
    except Exception as e:
        logger.error(f"Failed to load scored jobs: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    
    # Run interactive rating
    try:
        rated, skipped = rate_jobs_interactive(
            jobs,
            min_match_score=args.min_match_score,
            max_jobs=args.max_jobs,
        )
        
        prefs_path = get_default_preferences_path()
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Rated {rated} jobs, skipped {skipped} jobs.")
        print(f"Preferences saved to {prefs_path}")
        print("\nYou can now regenerate the report with re-ranking:")
        print(f"  python -m experiments.jobhunter.job_hunter_report --use-preferences --input-file {scored_path}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during rating: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
