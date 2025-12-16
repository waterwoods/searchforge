"""
applications_tracker.py - Local JSON-backed tracker for job application statuses.

Stores data in data/jobhunter/applications_log.json (list of JobApplicationRecord).
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

from services.fiqa_api.jobhunter.schemas import (
    JobPosting,
    JobApplicationStatus,
    JobApplicationRecord,
)

logger = logging.getLogger(__name__)

# Note: Use get_default_applications_log_path() for actual path resolution
# This is kept for backward compatibility but should be resolved relative to project root
DEFAULT_APPLICATIONS_LOG_PATH = Path("data/jobhunter/applications_log.json")


def get_default_applications_log_path() -> Path:
    """
    Get the default applications log path relative to project root.
    
    Returns:
        Path to applications_log.json in data/jobhunter/ directory.
    """
    # Try to find project root by looking for common markers
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / "poetry.lock").exists():
            return parent / "data" / "jobhunter" / "applications_log.json"
    
    # Fallback: use relative path from current working directory
    return Path("data/jobhunter/applications_log.json")


def load_applications(path: Optional[Path] = None) -> Dict[str, JobApplicationRecord]:
    """
    Load application records from JSON file.
    
    Returns a dict mapping job_id -> JobApplicationRecord.
    If file does not exist, return {}.
    
    Args:
        path: Path to the applications log JSON file. If None, uses get_default_applications_log_path().
    
    Returns:
        Dictionary mapping job_id to JobApplicationRecord.
    """
    if path is None:
        path = get_default_applications_log_path()
    
    if not path.exists():
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.warning(f"Expected list in {path}, got {type(data)}. Starting from empty.")
            return {}
        
        records = {}
        for item in data:
            try:
                # Parse datetime string to datetime object
                if isinstance(item.get("last_updated"), str):
                    item["last_updated"] = datetime.fromisoformat(item["last_updated"])
                
                record = JobApplicationRecord(**item)
                records[record.job_id] = record
            except Exception as e:
                logger.warning(f"Failed to parse record: {item}. Error: {e}. Skipping.")
                continue
        
        return records
    
    except json.JSONDecodeError as e:
        logger.warning(f"Corrupted JSON in {path}: {e}. Starting from empty.")
        return {}
    except Exception as e:
        logger.warning(f"Error loading applications from {path}: {e}. Starting from empty.")
        return {}


def save_applications(
    records: Dict[str, JobApplicationRecord],
    path: Optional[Path] = None,
) -> None:
    """
    Save application records to JSON file.
    
    Uses UTF-8, indent=2, ensure_ascii=False.
    
    Args:
        records: Dictionary mapping job_id to JobApplicationRecord.
        path: Path to the applications log JSON file. If None, uses get_default_applications_log_path().
    """
    if path is None:
        path = get_default_applications_log_path()
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert records to list of dicts
    records_list = []
    for record in records.values():
        record_dict = record.model_dump()
        # Convert datetime to ISO string for JSON serialization
        if isinstance(record_dict.get("last_updated"), datetime):
            record_dict["last_updated"] = record_dict["last_updated"].isoformat()
        records_list.append(record_dict)
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving applications to {path}: {e}")
        raise


def update_application(
    job: JobPosting,
    status: JobApplicationStatus,
    notes: Optional[str] = None,
    path: Optional[Path] = None,
) -> JobApplicationRecord:
    """
    Upsert a JobApplicationRecord for the given job_id.
    
    Update status, notes, last_updated.
    
    Args:
        job: JobPosting instance to create/update record for.
        status: New application status.
        notes: Optional notes about the application.
        path: Path to the applications log JSON file. If None, uses get_default_applications_log_path().
    
    Returns:
        The created or updated JobApplicationRecord.
    """
    if path is None:
        path = get_default_applications_log_path()
    records = load_applications(path)
    
    # Create or update record
    now = datetime.now(timezone.utc)
    
    if job.job_id in records:
        # Update existing record
        record = records[job.job_id]
        record.status = status
        record.notes = notes
        record.last_updated = now
        # Update other fields in case job info changed
        record.company = job.company
        record.title = job.title
        record.source = job.source
        record.url = job.url
        record.location = job.location
    else:
        # Create new record
        record = JobApplicationRecord(
            job_id=job.job_id,
            company=job.company,
            title=job.title,
            source=job.source,
            url=job.url,
            status=status,
            notes=notes,
            last_updated=now,
            location=job.location,
        )
        records[job.job_id] = record
    
    save_applications(records, path)
    return record


def list_by_status(
    records: Dict[str, JobApplicationRecord],
    status: JobApplicationStatus,
) -> List[JobApplicationRecord]:
    """
    Return all records with the given status.
    
    Args:
        records: Dictionary mapping job_id to JobApplicationRecord.
        status: Status to filter by.
    
    Returns:
        List of JobApplicationRecord instances with the given status.
    """
    return [record for record in records.values() if record.status == status]
