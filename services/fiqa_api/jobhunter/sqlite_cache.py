"""
sqlite_cache.py - SQLite Cache Module for JobHunter JD Analysis

This module provides caching functionality for JD analysis results using SQLite.
It stores analysis results keyed by user_id, profile_id, and JD text hash to avoid
re-analyzing the same job descriptions.

Key features:
- Automatic database initialization
- JD text hashing for stable cache keys
- Thread-safe short-lived connections (no persistent connections)
- Graceful error handling (warnings, no exceptions thrown)
"""

import json
import logging
import sqlite3
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime

logger = logging.getLogger(__name__)

# Database file path (relative to this module's directory)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "jobhunter_cache.sqlite3"


def init_db() -> None:
    """
    Create SQLite DB and jd_analysis_cache table if not exists.
    
    This function is idempotent - safe to call multiple times.
    Creates the table and necessary indexes for efficient lookups.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jd_analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                profile_id TEXT NOT NULL,
                job_url TEXT,
                job_title TEXT,
                jd_hash TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                analysis_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create unique index on (user_id, profile_id, jd_hash)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_jd_cache_unique
                ON jd_analysis_cache (user_id, profile_id, jd_hash)
        """)
        
        # Create index on (user_id, profile_id, job_url) for URL-based lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jd_cache_url
                ON jd_analysis_cache (user_id, profile_id, job_url)
        """)
        
        conn.commit()
        conn.close()
        logger.debug(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.warning(f"Failed to initialize database: {e}")
        # Don't raise - let the calling code handle gracefully


def compute_jd_hash(text: str) -> str:
    """
    Normalize and hash JD text to get a stable identifier.
    
    Normalization steps:
    - Strip leading/trailing whitespace
    - Normalize internal whitespace (multiple spaces/newlines -> single newline)
    - Convert to UTF-8 for hashing
    
    Args:
        text: Raw JD text
        
    Returns:
        SHA256 hash hexdigest (64 characters)
    """
    if not text:
        return hashlib.sha256(b"").hexdigest()
    
    # Normalize: strip, then replace multiple whitespace with single newline
    normalized = " ".join(text.strip().split())
    # Convert multiple spaces/newlines to single newline
    normalized = "\n".join(line.strip() for line in normalized.splitlines() if line.strip())
    
    # Hash the normalized text
    hash_obj = hashlib.sha256(normalized.encode("utf-8"))
    return hash_obj.hexdigest()


def get_cached_analysis(
    user_id: str,
    profile_id: str,
    jd_hash: str,
) -> Optional[Dict[str, Any]]:
    """
    Return cached analysis_json as dict if found, else None.
    
    Args:
        user_id: User identifier (e.g., "local-user")
        profile_id: Profile identifier (e.g., "data_engineer_gcp")
        jd_hash: JD text hash (from compute_jd_hash)
        
    Returns:
        Cached analysis as dict if found, None otherwise.
        Returns None on any error (logged as warning).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query for cached analysis
        cursor.execute("""
            SELECT analysis_json, updated_at
            FROM jd_analysis_cache
            WHERE user_id = ? AND profile_id = ? AND jd_hash = ?
        """, (user_id, profile_id, jd_hash))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        # Deserialize JSON
        analysis_json_str = row["analysis_json"]
        analysis_dict = json.loads(analysis_json_str)
        logger.debug(f"Cache hit for user_id={user_id}, profile_id={profile_id}, jd_hash={jd_hash[:8]}...")
        return analysis_dict
        
    except Exception as e:
        logger.warning(f"Failed to get cached analysis: {e}")
        return None


def save_analysis(
    user_id: str,
    profile_id: str,
    job_url: Optional[str],
    job_title: Optional[str],
    jd_hash: str,
    raw_text: str,
    analysis: Dict[str, Any],
) -> None:
    """
    Upsert analysis result into jd_analysis_cache.
    
    If a record with the same (user_id, profile_id, jd_hash) exists, it will be updated.
    Otherwise, a new record will be inserted.
    
    Args:
        user_id: User identifier (e.g., "local-user")
        profile_id: Profile identifier (e.g., "data_engineer_gcp")
        job_url: Optional job posting URL
        job_title: Optional job title
        jd_hash: JD text hash (from compute_jd_hash)
        raw_text: Original JD text
        analysis: Analysis result as dict (will be serialized to JSON)
        
    Note:
        On error, logs a warning but does not raise exception (graceful degradation).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Serialize analysis to JSON
        analysis_json_str = json.dumps(analysis, ensure_ascii=False)
        
        # Get current UTC timestamp
        now_iso = datetime.utcnow().isoformat()
        
        # Try to use INSERT ... ON CONFLICT (SQLite 3.24+)
        # If that fails, fall back to UPDATE-then-INSERT pattern
        try:
            cursor.execute("""
                INSERT INTO jd_analysis_cache
                    (user_id, profile_id, job_url, job_title, jd_hash, raw_text, analysis_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, profile_id, jd_hash) DO UPDATE SET
                    job_url = excluded.job_url,
                    job_title = excluded.job_title,
                    raw_text = excluded.raw_text,
                    analysis_json = excluded.analysis_json,
                    updated_at = excluded.updated_at
            """, (user_id, profile_id, job_url, job_title, jd_hash, raw_text, analysis_json_str, now_iso, now_iso))
        except sqlite3.OperationalError as e:
            # Fallback for older SQLite versions that don't support ON CONFLICT
            if "ON CONFLICT" in str(e):
                logger.debug("ON CONFLICT not supported, using UPDATE-then-INSERT fallback")
                # Try UPDATE first
                cursor.execute("""
                    UPDATE jd_analysis_cache
                    SET job_url = ?,
                        job_title = ?,
                        raw_text = ?,
                        analysis_json = ?,
                        updated_at = ?
                    WHERE user_id = ? AND profile_id = ? AND jd_hash = ?
                """, (job_url, job_title, raw_text, analysis_json_str, now_iso, user_id, profile_id, jd_hash))
                
                # If no row was updated, INSERT
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO jd_analysis_cache
                            (user_id, profile_id, job_url, job_title, jd_hash, raw_text, analysis_json, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, profile_id, job_url, job_title, jd_hash, raw_text, analysis_json_str, now_iso, now_iso))
            else:
                raise
        
        conn.commit()
        conn.close()
        logger.debug(f"Cached analysis for user_id={user_id}, profile_id={profile_id}, jd_hash={jd_hash[:8]}...")
        
    except Exception as e:
        logger.warning(f"Failed to save analysis to cache: {e}")
        # Don't raise - graceful degradation


def list_cached_analyses(
    user_id: str,
    profile_id: Optional[str] = None,
    limit: int = 50,
    order: Literal["desc", "asc"] = "desc",
) -> List[Dict[str, Any]]:
    """
    List cached analysis results for a user, optionally filtered by profile_id.
    
    Note: This function returns the full analysis_json for each item (needed for match_score calculation).
    For better performance when only metadata is needed, consider using a separate lightweight query.
    
    Args:
        user_id: User identifier (e.g., "local_demo_user")
        profile_id: Optional profile identifier to filter by (e.g., "data_engineer_gcp")
        limit: Maximum number of results to return (default: 50)
        order: Sort order by updated_at timestamp ("desc" for newest first, "asc" for oldest first)
    
    Returns:
        List of dicts, each containing:
        - id: int (PRIMARY KEY, used for detail API lookup)
        - user_id: str
        - profile_id: str
        - job_url: Optional[str]
        - job_title: Optional[str]
        - jd_hash: str
        - raw_text: str
        - analysis: dict (deserialized from analysis_json, includes fit_summary/constraints for match_score)
        - created_at: str (ISO timestamp)
        - last_analyzed_at: str (ISO timestamp, same as updated_at)
    
    On error, logs warning and returns empty list (graceful degradation).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build SQL query with optional profile_id filter
        sql = """
            SELECT id, user_id, profile_id, job_url, job_title, jd_hash, raw_text,
                   analysis_json, created_at, updated_at
            FROM jd_analysis_cache
            WHERE user_id = ?
        """
        params: List[Any] = [user_id]
        
        if profile_id is not None:
            sql += " AND profile_id = ?"
            params.append(profile_id)
        
        # Add ORDER BY clause
        order_clause = "DESC" if order == "desc" else "ASC"
        sql += f" ORDER BY updated_at {order_clause}"
        
        # Add LIMIT clause
        sql += " LIMIT ?"
        params.append(limit)
        
        # Execute query
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to list of dicts
        results = []
        for row in rows:
            try:
                # Deserialize analysis_json
                analysis_dict = json.loads(row["analysis_json"])
                
                result_dict = {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "profile_id": row["profile_id"],
                    "job_url": row["job_url"],
                    "job_title": row["job_title"],
                    "jd_hash": row["jd_hash"],
                    "raw_text": row["raw_text"],
                    "analysis": analysis_dict,
                    "created_at": row["created_at"],
                    "last_analyzed_at": row["updated_at"],  # Use updated_at as last_analyzed_at
                }
                results.append(result_dict)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to deserialize analysis_json for id={row['id']}: {e}")
                continue
        
        logger.debug(f"Listed {len(results)} cached analyses for user_id={user_id}, profile_id={profile_id}")
        return results
        
    except Exception as e:
        logger.warning(f"Failed to list cached analyses: {e}")
        return []


def get_cached_analysis_by_id(cache_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single cached analysis by its primary key ID.
    
    This function is used by the detail API endpoint to fetch complete analysis results
    including full analysis_json with core_signals, lifecycle, spotlight_stories, etc.
    
    Args:
        cache_id: Primary key ID from jd_analysis_cache table
    
    Returns:
        Dict containing:
        - id: int
        - user_id: str
        - profile_id: str
        - job_url: Optional[str]
        - job_title: Optional[str]
        - jd_hash: str
        - raw_text: str
        - analysis_json: str (raw JSON string, caller should deserialize)
        - analysis: dict (deserialized from analysis_json)
        - created_at: str (ISO timestamp)
        - updated_at: str (ISO timestamp)
        
        Returns None if not found or on error (logged as warning).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query for cached analysis by ID
        cursor.execute("""
            SELECT id, user_id, profile_id, job_url, job_title, jd_hash, raw_text,
                   analysis_json, created_at, updated_at
            FROM jd_analysis_cache
            WHERE id = ?
        """, (cache_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            logger.debug(f"Cache item not found for id={cache_id}")
            return None
        
        # Deserialize analysis_json
        try:
            analysis_dict = json.loads(row["analysis_json"])
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to deserialize analysis_json for id={cache_id}: {e}")
            return None
        
        result_dict = {
            "id": row["id"],
            "user_id": row["user_id"],
            "profile_id": row["profile_id"],
            "job_url": row["job_url"],
            "job_title": row["job_title"],
            "jd_hash": row["jd_hash"],
            "raw_text": row["raw_text"],
            "analysis_json": row["analysis_json"],  # Keep raw JSON string for reference
            "analysis": analysis_dict,  # Deserialized dict
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        
        logger.debug(f"Retrieved cached analysis for id={cache_id}")
        return result_dict
        
    except Exception as e:
        logger.warning(f"Failed to get cached analysis by id={cache_id}: {e}")
        return None
