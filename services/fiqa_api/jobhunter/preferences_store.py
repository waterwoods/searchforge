"""
preferences_store.py - Storage module for job preference ratings.

This module handles loading and saving user preference ratings for jobs,
enabling RLHF-style feedback to refine job rankings.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from services.fiqa_api.jobhunter.schemas import JobPreferenceRecord

logger = logging.getLogger(__name__)


def get_default_preferences_path() -> Path:
    """
    Get the default preferences path relative to project root.
    
    Returns:
        Path to preferences.json in data/jobhunter/preferences/ directory.
    """
    # Try to find project root by looking for common markers
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / "poetry.lock").exists():
            return parent / "data" / "jobhunter" / "preferences" / "preferences.json"
    
    # Fallback: use relative path from current working directory
    return Path("data/jobhunter/preferences/preferences.json")


def load_preferences(path: Optional[Path] = None) -> Dict[str, JobPreferenceRecord]:
    """
    Load all preference records from disk.
    
    Args:
        path: Path to preferences JSON file. If None, uses get_default_preferences_path().
    
    Returns:
        Dictionary mapping job_id to JobPreferenceRecord.
        Returns empty dict if file doesn't exist or is corrupted.
    """
    if path is None:
        path = get_default_preferences_path()
    
    if not path.exists():
        logger.debug(f"Preferences file not found at {path}, returning empty dict")
        return {}
    
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.warning(f"Expected list in preferences file, got {type(data)}. Returning empty dict.")
            return {}
        
        # Convert list of dicts to dict of JobPreferenceRecord objects
        preferences: Dict[str, JobPreferenceRecord] = {}
        for item in data:
            try:
                # Handle datetime string conversion
                if "rated_at" in item and isinstance(item["rated_at"], str):
                    item["rated_at"] = datetime.fromisoformat(item["rated_at"])
                
                record = JobPreferenceRecord.model_validate(item)
                preferences[record.job_id] = record
            except Exception as e:
                logger.warning(f"Failed to parse preference record: {e}. Skipping.")
                continue
        
        logger.info(f"Loaded {len(preferences)} preference records from {path}")
        return preferences
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse preferences file {path}: {e}. Returning empty dict.")
        return {}
    except Exception as e:
        logger.warning(f"Error loading preferences from {path}: {e}. Returning empty dict.")
        return {}


def save_preferences(
    preferences: Dict[str, JobPreferenceRecord],
    path: Optional[Path] = None,
) -> None:
    """
    Save preference records to disk.
    
    The records are sorted by rated_at (most recent first) before writing.
    
    Args:
        preferences: Dictionary mapping job_id to JobPreferenceRecord
        path: Path to preferences JSON file. If None, uses get_default_preferences_path().
    """
    if path is None:
        path = get_default_preferences_path()
    
    # Convert to list and sort by rated_at (most recent first)
    records = list(preferences.values())
    records.sort(key=lambda r: r.rated_at, reverse=True)
    
    # Convert to JSON-serializable format
    data = [record.model_dump(mode="json") for record in records]
    
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write atomically (write to temp file, then rename)
    temp_path = path.with_suffix(".json.tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        temp_path.replace(path)
        logger.info(f"Saved {len(preferences)} preference records to {path}")
    except Exception as e:
        logger.error(f"Failed to save preferences to {path}: {e}")
        if temp_path.exists():
            temp_path.unlink()
        raise


def upsert_preference(
    record: JobPreferenceRecord,
    path: Optional[Path] = None,
) -> Dict[str, JobPreferenceRecord]:
    """
    Upsert a preference record (insert or update).
    
    This function loads existing preferences, updates/adds the given record,
    saves to disk, and returns the updated preferences dict.
    
    Args:
        record: JobPreferenceRecord to insert or update
        path: Path to preferences JSON file. If None, uses get_default_preferences_path().
    
    Returns:
        Updated dictionary of all preferences (mapping job_id to JobPreferenceRecord)
    """
    preferences = load_preferences(path)
    preferences[record.job_id] = record
    save_preferences(preferences, path)
    return preferences
