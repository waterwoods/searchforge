#!/usr/bin/env python3
"""
fetch_greenhouse_jobs.py - Fetch job postings from Greenhouse Job Board APIs
=============================================================================

This script fetches job postings from Greenhouse Job Board APIs for a set of
target companies, normalizes them into a unified JobPosting schema, and saves
both raw and normalized data.

Usage:
    python -m experiments.jobhunter.fetch_greenhouse_jobs
    python -m experiments.jobhunter.fetch_greenhouse_jobs --companies anthropic,databricks,openai,perplexityai,scaleai,runwayml
    python -m experiments.jobhunter.fetch_greenhouse_jobs --output-dir-raw data/jobhunter/raw

Output:
    - Raw JSON per company: data/jobhunter/raw/{company_slug}_jobs_YYYYMMDD.json
    - Normalized combined: data/jobhunter/normalized/jobs_YYYYMMDD.json
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.jobhunter.schemas import JobPosting

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Default target companies
DEFAULT_GREENHOUSE_COMPANIES = [
    "anthropic",
    "databricks",
    "openai",
    "perplexityai",
    "scaleai",
    "runwayml",
]

# Greenhouse API base URL
GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"


def fetch_greenhouse_jobs_for_company(company_slug: str, timeout: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch job postings from Greenhouse API for a specific company.
    
    Args:
        company_slug: Company slug (e.g., "anthropic")
        timeout: HTTP request timeout in seconds
    
    Returns:
        List of job dictionaries from Greenhouse API, or None on error
    """
    url = f"{GREENHOUSE_API_BASE}/{company_slug}/jobs?content=true"
    
    try:
        logger.info(f"Fetching jobs from Greenhouse for company: {company_slug}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        jobs = response.json().get("jobs", [])
        logger.info(f"Fetched {len(jobs)} jobs for {company_slug}")
        return jobs
    
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch jobs for {company_slug}: {e}")
        return None


def normalize_greenhouse_job(job: Dict[str, Any], company_slug: str) -> JobPosting:
    """
    Normalize a Greenhouse job posting into a JobPosting model.
    
    Args:
        job: Raw job dictionary from Greenhouse API
        company_slug: Company slug for source identification
    
    Returns:
        JobPosting instance
    """
    # Extract location
    location = None
    if "location" in job and job["location"]:
        location = job["location"].get("name")
    
    # Determine if remote (case-insensitive check)
    is_remote = None
    if location:
        location_lower = location.lower()
        is_remote = "remote" in location_lower
    
    # Extract employment type (Greenhouse doesn't always provide this directly)
    employment_type = None
    if "metadata" in job:
        # Check various metadata fields that might contain employment type
        metadata = job["metadata"]
        if isinstance(metadata, list):
            for item in metadata:
                if isinstance(item, dict) and item.get("name") == "Employment Type":
                    employment_type = item.get("value")
                    break
    
    # Extract department
    department = None
    if "departments" in job and job["departments"]:
        if isinstance(job["departments"], list) and len(job["departments"]) > 0:
            department = job["departments"][0].get("name")
    
    # Extract description (content field)
    description = job.get("content", "")
    
    # Extract URL
    url = job.get("absolute_url", "")
    
    # Extract timestamps
    created_at = job.get("created_at")
    updated_at = job.get("updated_at")
    
    return JobPosting(
        job_id=str(job["id"]),
        title=job.get("title", ""),
        company=company_slug,
        location=location,
        is_remote=is_remote,
        employment_type=employment_type,
        department=department,
        source=f"greenhouse:{company_slug}",
        url=url,
        description=description,
        created_at=created_at,
        updated_at=updated_at,
        tags=[],  # Empty for now, can be populated later
        raw=job,  # Store entire raw payload
    )


def normalize_greenhouse_jobs(jobs: List[Dict[str, Any]], company_slug: str) -> List[JobPosting]:
    """
    Normalize a list of Greenhouse job postings.
    
    Args:
        jobs: List of raw job dictionaries from Greenhouse API
        company_slug: Company slug for source identification
    
    Returns:
        List of JobPosting instances
    """
    normalized = []
    for job in jobs:
        try:
            posting = normalize_greenhouse_job(job, company_slug)
            normalized.append(posting)
        except Exception as e:
            logger.warning(f"Failed to normalize job {job.get('id', 'unknown')} for {company_slug}: {e}")
            continue
    
    return normalized


def save_raw_jobs(jobs: List[Dict[str, Any]], company_slug: str, output_dir: Path, date_str: str) -> Path:
    """
    Save raw job postings to a JSON file.
    
    Args:
        jobs: List of raw job dictionaries
        company_slug: Company slug for filename
        output_dir: Output directory path
        date_str: Date string in YYYYMMDD format
    
    Returns:
        Path to the saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{company_slug}_jobs_{date_str}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved raw jobs to {output_file}")
    return output_file


def save_normalized_jobs(postings: List[JobPosting], output_dir: Path, date_str: str) -> Path:
    """
    Save normalized job postings to a JSON file.
    
    Args:
        postings: List of JobPosting instances
        output_dir: Output directory path
        date_str: Date string in YYYYMMDD format
    
    Returns:
        Path to the saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"jobs_{date_str}.json"
    
    # Convert to dicts using Pydantic v2 model_dump()
    normalized_dicts = [posting.model_dump() for posting in postings]
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(normalized_dicts, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(postings)} normalized jobs to {output_file}")
    return output_file


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Fetch job postings from Greenhouse Job Board APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m experiments.jobhunter.fetch_greenhouse_jobs
  python -m experiments.jobhunter.fetch_greenhouse_jobs --companies anthropic,databricks,openai,perplexityai,scaleai,runwayml
  python -m experiments.jobhunter.fetch_greenhouse_jobs --output-dir-raw custom/raw
        """,
    )
    
    parser.add_argument(
        "--companies",
        type=str,
        default=",".join(DEFAULT_GREENHOUSE_COMPANIES),
        help=f"Comma-separated list of company slugs (default: {','.join(DEFAULT_GREENHOUSE_COMPANIES)})",
    )
    
    parser.add_argument(
        "--output-dir-raw",
        type=str,
        default="data/jobhunter/raw",
        help="Output directory for raw JSON files (default: data/jobhunter/raw)",
    )
    
    parser.add_argument(
        "--output-dir-normalized",
        type=str,
        default="data/jobhunter/normalized",
        help="Output directory for normalized JSON files (default: data/jobhunter/normalized)",
    )
    
    args = parser.parse_args()
    
    # Parse company list
    company_slugs = [slug.strip() for slug in args.companies.split(",") if slug.strip()]
    if not company_slugs:
        logger.error("No companies specified")
        sys.exit(1)
    
    # Setup output directories
    output_dir_raw = project_root / args.output_dir_raw
    output_dir_normalized = project_root / args.output_dir_normalized
    
    # Get current date string
    date_str = datetime.now().strftime("%Y%m%d")
    
    logger.info(f"Fetching jobs for companies: {', '.join(company_slugs)}")
    logger.info(f"Raw output directory: {output_dir_raw}")
    logger.info(f"Normalized output directory: {output_dir_normalized}")
    
    # Fetch and process jobs for each company
    all_normalized_postings = []
    
    for company_slug in company_slugs:
        # Fetch raw jobs
        raw_jobs = fetch_greenhouse_jobs_for_company(company_slug)
        
        if raw_jobs is None:
            logger.warning(f"Skipping {company_slug} due to fetch error")
            continue
        
        if not raw_jobs:
            logger.info(f"No jobs found for {company_slug}")
            continue
        
        # Save raw jobs
        save_raw_jobs(raw_jobs, company_slug, output_dir_raw, date_str)
        
        # Normalize jobs
        normalized_postings = normalize_greenhouse_jobs(raw_jobs, company_slug)
        all_normalized_postings.extend(normalized_postings)
        
        logger.info(f"Normalized {len(normalized_postings)} jobs for {company_slug}")
    
    # Save combined normalized jobs
    if all_normalized_postings:
        save_normalized_jobs(all_normalized_postings, output_dir_normalized, date_str)
        logger.info(f"Total normalized jobs: {len(all_normalized_postings)}")
    else:
        logger.warning("No jobs were successfully fetched and normalized")
    
    logger.info("Done")


if __name__ == "__main__":
    main()
