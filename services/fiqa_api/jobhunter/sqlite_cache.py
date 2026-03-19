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
# [health] inspected

import json
import logging
import os
import sqlite3
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime

logger = logging.getLogger(__name__)

# Database file path (relative to this module's directory)
# Priority: Use writable .runs directory, with fallback to old location for reading
BASE_DIR = Path(__file__).resolve().parent
OLD_DB_PATH = BASE_DIR / "jobhunter_cache.sqlite3"
RUNS_DIR = BASE_DIR.parent.parent.parent / ".runs"
NEW_DB_PATH = RUNS_DIR / "jobhunter_cache.sqlite3"

# Use .runs directory for writable database (always writable in Docker)
RUNS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = NEW_DB_PATH

# If new database doesn't exist but old one does, copy it
if not NEW_DB_PATH.exists() and OLD_DB_PATH.exists():
    try:
        import shutil
        shutil.copy2(OLD_DB_PATH, NEW_DB_PATH)
        logger.info(f"Migrated database from {OLD_DB_PATH} to {NEW_DB_PATH}")
    except Exception as e:
        logger.warning(f"Failed to migrate database: {e}. Will create new database.")

logger.info(f"Using database at {DB_PATH}")


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
        
        # Create user_profiles table for storing user resumes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                profile_id TEXT NOT NULL,
                resume_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, profile_id)
            )
        """)
        
        # Create unique index on (user_id, profile_id) for efficient UPSERT
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_profile_unique
                ON user_profiles (user_id, profile_id)
        """)
        
        # Create job_applications table for storing job application status
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                profile_id TEXT NOT NULL,
                cache_id INTEGER,
                job_url TEXT,
                job_title TEXT,
                company TEXT,
                status TEXT NOT NULL DEFAULT 'planned',
                first_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                applied_at TIMESTAMP,
                last_updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)
        
        # Create unique index on (user_id, profile_id, cache_id) to avoid duplicates
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_job_applications_unique
                ON job_applications (user_id, profile_id, cache_id)
        """)
        
        # Add deleted column if it doesn't exist (migration for existing databases)
        try:
            cursor.execute("PRAGMA table_info(job_applications)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'deleted' not in columns:
                cursor.execute("""
                    ALTER TABLE job_applications ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0
                """)
                logger.info("Added 'deleted' column to job_applications table")
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to check/add deleted column: {e}")
        
        # Add quick_view_json column if it doesn't exist (migration for existing databases)
        try:
            cursor.execute("PRAGMA table_info(jd_analysis_cache)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'quick_view_json' not in columns:
                cursor.execute("""
                    ALTER TABLE jd_analysis_cache ADD COLUMN quick_view_json TEXT
                """)
                logger.info("Added 'quick_view_json' column to jd_analysis_cache table")
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to check/add quick_view_json column: {e}")
        
        # Add quick_view_cn column if it doesn't exist (migration for existing databases)
        # Step 1: Add quick_view_cn column for Lv1 quick view text caching
        try:
            cursor.execute("PRAGMA table_info(jd_analysis_cache)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'quick_view_cn' not in columns:
                cursor.execute("""
                    ALTER TABLE jd_analysis_cache ADD COLUMN quick_view_cn TEXT
                """)
                logger.info("Added 'quick_view_cn' column to jd_analysis_cache table")
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to check/add quick_view_cn column: {e}")
        
        # Add auto_skip and auto_skip_reasons columns if they don't exist (migration for existing databases)
        try:
            cursor.execute("PRAGMA table_info(jd_analysis_cache)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'auto_skip' not in columns:
                cursor.execute("""
                    ALTER TABLE jd_analysis_cache ADD COLUMN auto_skip INTEGER NOT NULL DEFAULT 0
                """)
                logger.info("Added 'auto_skip' column to jd_analysis_cache table")
                conn.commit()
            if 'auto_skip_reasons' not in columns:
                cursor.execute("""
                    ALTER TABLE jd_analysis_cache ADD COLUMN auto_skip_reasons TEXT
                """)
                logger.info("Added 'auto_skip_reasons' column to jd_analysis_cache table")
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to check/add auto_skip columns: {e}")
        
        conn.commit()
        conn.close()
        logger.debug(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.warning(f"Failed to initialize database: {e}")
        # Don't raise - let the calling code handle gracefully


def ensure_migration() -> None:
    """
    Ensure database migration is applied (add deleted column if needed).
    
    This function should be called before any operation on job_applications table
    to ensure the schema is up to date.
    """
    try:
        if not DB_PATH.exists():
            init_db()
            return
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Check if deleted column exists
        cursor.execute("PRAGMA table_info(job_applications)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'deleted' not in columns:
            cursor.execute("""
                ALTER TABLE job_applications ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0
            """)
            conn.commit()
            logger.info("Migration: Added 'deleted' column to job_applications table")
        
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to ensure migration: {e}")
        # Don't raise - try to continue
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


def get_cache_id_by_hash(
    user_id: str,
    profile_id: str,
    jd_hash: str,
) -> Optional[int]:
    """
    Get cache_id (primary key) by user_id, profile_id, and jd_hash.
    
    Args:
        user_id: User identifier (e.g., "local-user")
        profile_id: Profile identifier (e.g., "data_engineer_gcp")
        jd_hash: JD text hash (from compute_jd_hash)
        
    Returns:
        Cache ID (primary key) if found, None otherwise.
        Returns None on any error (logged as warning).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Query for cache_id
        cursor.execute("""
            SELECT id
            FROM jd_analysis_cache
            WHERE user_id = ? AND profile_id = ? AND jd_hash = ?
        """, (user_id, profile_id, jd_hash))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        cache_id = row[0]
        logger.debug(f"Found cache_id={cache_id} for user_id={user_id}, profile_id={profile_id}, jd_hash={jd_hash[:8]}...")
        return cache_id
        
    except Exception as e:
        logger.warning(f"Failed to get cache_id by hash: {e}")
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
                   analysis_json, auto_skip, auto_skip_reasons, created_at, updated_at
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
                
                # Deserialize auto_skip_reasons from JSON string
                auto_skip_reasons = None
                auto_skip_reasons_str = row["auto_skip_reasons"] if "auto_skip_reasons" in row.keys() else None
                if auto_skip_reasons_str:
                    try:
                        auto_skip_reasons = json.loads(auto_skip_reasons_str)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to deserialize auto_skip_reasons for id={row['id']}")
                        auto_skip_reasons = None
                
                # Get auto_skip value (default to 0 if column doesn't exist for backward compatibility)
                auto_skip_value = 0
                if "auto_skip" in row.keys():
                    auto_skip_value = row["auto_skip"] or 0
                
                result_dict = {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "profile_id": row["profile_id"],
                    "job_url": row["job_url"],
                    "job_title": row["job_title"],
                    "jd_hash": row["jd_hash"],
                    "raw_text": row["raw_text"],
                    "analysis": analysis_dict,
                    "auto_skip": bool(auto_skip_value),
                    "auto_skip_reasons": auto_skip_reasons,
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
        
        # Query for cached analysis by ID (including quick_view_cn, auto_skip)
        cursor.execute("""
            SELECT id, user_id, profile_id, job_url, job_title, jd_hash, raw_text,
                   analysis_json, quick_view_cn, auto_skip, auto_skip_reasons, created_at, updated_at
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
        
        # Deserialize auto_skip_reasons from JSON string
        auto_skip_reasons = None
        auto_skip_reasons_str = row["auto_skip_reasons"] if "auto_skip_reasons" in row.keys() else None
        if auto_skip_reasons_str:
            try:
                auto_skip_reasons = json.loads(auto_skip_reasons_str)
            except json.JSONDecodeError:
                logger.warning(f"Failed to deserialize auto_skip_reasons for id={cache_id}")
                auto_skip_reasons = None
        
        # Get auto_skip value (default to 0 if column doesn't exist for backward compatibility)
        auto_skip_value = 0
        if "auto_skip" in row.keys():
            auto_skip_value = row["auto_skip"] or 0
        
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
            "quick_view_cn": row["quick_view_cn"],  # Lv1 quick view text
            "auto_skip": bool(auto_skip_value),
            "auto_skip_reasons": auto_skip_reasons,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        
        logger.debug(f"Retrieved cached analysis for id={cache_id}")
        return result_dict
        
    except Exception as e:
        logger.warning(f"Failed to get cached analysis by id={cache_id}: {e}")
        return None


def get_quick_view_for_cache_id(cache_id: int) -> Optional[Dict[str, Any]]:
    """
    Get quick_view_json for a cached JD analysis by cache_id.
    
    Args:
        cache_id: Primary key ID from jd_analysis_cache table
    
    Returns:
        Quick view dict if found, None otherwise.
        Returns None on any error (logged as warning).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query for quick_view_json by ID
        cursor.execute("""
            SELECT quick_view_json
            FROM jd_analysis_cache
            WHERE id = ?
        """, (cache_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            logger.debug(f"Cache item not found for id={cache_id}")
            return None
        
        quick_view_json_str = row["quick_view_json"]
        if quick_view_json_str is None:
            return None
        
        # Deserialize JSON
        try:
            quick_view_dict = json.loads(quick_view_json_str)
            logger.debug(f"Retrieved quick_view_json for id={cache_id}")
            return quick_view_dict
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to deserialize quick_view_json for id={cache_id}: {e}")
            return None
        
    except Exception as e:
        logger.warning(f"Failed to get quick_view_json by id={cache_id}: {e}")
        return None


def save_quick_view_for_cache_id(cache_id: int, quick_view: Dict[str, Any]) -> None:
    """
    Save quick_view_json for a cached JD analysis by cache_id.
    
    Args:
        cache_id: Primary key ID from jd_analysis_cache table
        quick_view: Quick view dict to save as JSON
    
    Note:
        On error, logs a warning but does not raise exception (graceful degradation).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Serialize quick_view to JSON
        quick_view_json_str = json.dumps(quick_view, ensure_ascii=False)
        
        # Get current UTC timestamp
        now_iso = datetime.utcnow().isoformat()
        
        # Update quick_view_json
        cursor.execute("""
            UPDATE jd_analysis_cache
            SET quick_view_json = ?,
                updated_at = ?
            WHERE id = ?
        """, (quick_view_json_str, now_iso, cache_id))
        
        if cursor.rowcount == 0:
            logger.warning(f"No row updated for cache_id={cache_id} when saving quick_view_json")
        else:
            logger.debug(f"Saved quick_view_json for cache_id={cache_id}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.warning(f"Failed to save quick_view_json for cache_id={cache_id}: {e}")
        # Don't raise - graceful degradation


def update_quick_view_cn(cache_id: int, quick_view_cn: str) -> None:
    """
    Update quick_view_cn (Lv1 quick view text) for a cached JD analysis by cache_id.
    
    Args:
        cache_id: Primary key ID from jd_analysis_cache table
        quick_view_cn: Quick view Chinese text to save
    
    Note:
        On error, logs a warning but does not raise exception (graceful degradation).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Get current UTC timestamp
        now_iso = datetime.utcnow().isoformat()
        
        # Update quick_view_cn
        cursor.execute("""
            UPDATE jd_analysis_cache
            SET quick_view_cn = ?,
                updated_at = ?
            WHERE id = ?
        """, (quick_view_cn, now_iso, cache_id))
        
        if cursor.rowcount == 0:
            logger.warning(f"No row updated for cache_id={cache_id} when saving quick_view_cn")
        else:
            logger.debug(f"Saved quick_view_cn for cache_id={cache_id}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.warning(f"Failed to save quick_view_cn for cache_id={cache_id}: {e}")
        # Don't raise - graceful degradation


def update_analysis_json(cache_id: int, analysis: Dict[str, Any]) -> None:
    """
    Update analysis_json for a cached JD analysis by cache_id.
    
    Args:
        cache_id: Primary key ID from jd_analysis_cache table
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
        
        # Update analysis_json
        cursor.execute("""
            UPDATE jd_analysis_cache
            SET analysis_json = ?,
                updated_at = ?
            WHERE id = ?
        """, (analysis_json_str, now_iso, cache_id))
        
        if cursor.rowcount == 0:
            logger.warning(f"No row updated for cache_id={cache_id} when updating analysis_json")
        else:
            logger.debug(f"Updated analysis_json for cache_id={cache_id}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.warning(f"Failed to update analysis_json for cache_id={cache_id}: {e}")
        # Don't raise - graceful degradation


def update_auto_skip_flags(cache_id: int, auto_skip: int, reasons: list[str] | None) -> None:
    """
    Update auto_skip and auto_skip_reasons for a cached JD analysis by cache_id.
    
    Args:
        cache_id: Primary key ID from jd_analysis_cache table
        auto_skip: Integer flag (0 = don't skip, 1 = auto skip)
        reasons: List of reason strings (will be serialized as JSON), or None for NULL
    
    Note:
        On error, logs a warning but does not raise exception (graceful degradation).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Get current UTC timestamp
        now_iso = datetime.utcnow().isoformat()
        
        # Serialize reasons to JSON string, or None
        reasons_json = None
        if reasons is not None:
            reasons_json = json.dumps(reasons, ensure_ascii=False)
        
        # Update auto_skip and auto_skip_reasons
        cursor.execute("""
            UPDATE jd_analysis_cache
            SET auto_skip = ?,
                auto_skip_reasons = ?,
                updated_at = ?
            WHERE id = ?
        """, (auto_skip, reasons_json, now_iso, cache_id))
        
        if cursor.rowcount == 0:
            logger.warning(f"No row updated for cache_id={cache_id} when saving auto_skip flags")
        else:
            logger.debug(f"Saved auto_skip flags for cache_id={cache_id}: auto_skip={auto_skip}, reasons={reasons}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.warning(f"Failed to save auto_skip flags for cache_id={cache_id}: {e}")
        # Don't raise - graceful degradation


def get_user_resume(user_id: str, profile_id: str) -> Optional[str]:
    """
    Get user resume text by user_id and profile_id.
    
    Args:
        user_id: User identifier (e.g., "andy_local")
        profile_id: Profile identifier (e.g., "data_engineer_gcp")
        
    Returns:
        Resume text as string if found, None otherwise.
        Returns None on any error (logged as warning).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Query for resume text
        cursor.execute("""
            SELECT resume_text
            FROM user_profiles
            WHERE user_id = ? AND profile_id = ?
        """, (user_id, profile_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            logger.debug(f"Resume not found for user_id={user_id}, profile_id={profile_id}")
            return None
        
        resume_text = row[0]
        logger.debug(f"Retrieved resume for user_id={user_id}, profile_id={profile_id}")
        return resume_text
        
    except Exception as e:
        logger.warning(f"Failed to get user resume: {e}")
        return None


def upsert_user_resume(user_id: str, profile_id: str, resume_text: str) -> None:
    """
    Upsert user resume text into user_profiles table.
    
    If a record with the same (user_id, profile_id) exists, it will be updated.
    Otherwise, a new record will be inserted.
    
    Args:
        user_id: User identifier (e.g., "andy_local")
        profile_id: Profile identifier (e.g., "data_engineer_gcp")
        resume_text: Resume text to save
        
    Note:
        On error, logs a warning but does not raise exception (graceful degradation).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Get current UTC timestamp
        now_iso = datetime.utcnow().isoformat()
        
        # Try to use INSERT ... ON CONFLICT (SQLite 3.24+)
        # If that fails, fall back to UPDATE-then-INSERT pattern
        try:
            cursor.execute("""
                INSERT INTO user_profiles (user_id, profile_id, resume_text, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, profile_id) DO UPDATE SET
                    resume_text = excluded.resume_text,
                    updated_at = excluded.updated_at
            """, (user_id, profile_id, resume_text, now_iso, now_iso))
        except sqlite3.OperationalError as e:
            # Fallback for older SQLite versions that don't support ON CONFLICT
            if "ON CONFLICT" in str(e):
                logger.debug("ON CONFLICT not supported, using UPDATE-then-INSERT fallback")
                # Try UPDATE first
                cursor.execute("""
                    UPDATE user_profiles
                    SET resume_text = ?,
                        updated_at = ?
                    WHERE user_id = ? AND profile_id = ?
                """, (resume_text, now_iso, user_id, profile_id))
                
                # If no row was updated, INSERT
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO user_profiles (user_id, profile_id, resume_text, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, profile_id, resume_text, now_iso, now_iso))
            else:
                raise
        
        conn.commit()
        conn.close()
        logger.debug(f"Upserted resume for user_id={user_id}, profile_id={profile_id}")
        
    except Exception as e:
        logger.warning(f"Failed to upsert user resume: {e}")
        # Don't raise - graceful degradation


def upsert_job_application(
    user_id: str,
    profile_id: str,
    cache_id: Optional[int],
    job_url: Optional[str],
    job_title: Optional[str],
    company: Optional[str],
    status: str,
    notes: Optional[str] = None,
    applied_at: Optional[str] = None,
) -> None:
    """
    Insert or update a job application record.
    
    If a record with the same (user_id, profile_id, cache_id) exists, it will be updated.
    Otherwise, a new record will be inserted.
    
    Note: Job application status is persisted in SQLite and survives backend/frontend restarts.
    
    Args:
        user_id: User identifier (e.g., "andy_local")
        profile_id: Profile identifier (e.g., "data_engineer_gcp")
        cache_id: JD analysis cache ID (can be None for non-batch JDs)
        job_url: Optional job posting URL
        job_title: Optional job title
        company: Optional company name
        status: Application status (planned, applied, interviewing, offer, rejected, skipped)
        notes: Optional notes
        applied_at: Optional ISO timestamp for when application was submitted
                   (if None and status is 'applied' or 'interviewing', will be set to current time)
    
    Note:
        On error, logs a warning but does not raise exception (graceful degradation).
    """
    try:
        # Ensure DB exists and migration is applied
        ensure_migration()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Get current UTC timestamp
        now_iso = datetime.utcnow().isoformat()
        
        # Determine applied_at: use provided value, or set to current time if status is applied/interviewing and not provided
        final_applied_at = applied_at
        if final_applied_at is None and status in ('applied', 'interviewing', 'offer'):
            final_applied_at = now_iso
        
        # Use UPDATE-then-INSERT pattern (more reliable than ON CONFLICT for this use case)
        # Try UPDATE first (including soft-deleted records to allow recovery)
        cursor.execute("""
            UPDATE job_applications
            SET job_url = COALESCE(?, job_url),
                job_title = COALESCE(?, job_title),
                company = COALESCE(?, company),
                status = ?,
                applied_at = ?,
                last_updated_at = ?,
                notes = ?,
                deleted = 0
            WHERE user_id = ? AND profile_id = ? AND cache_id = ?
        """, (job_url, job_title, company, status, final_applied_at, now_iso, notes,
              user_id, profile_id, cache_id))
        
        # If no row was updated, INSERT
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO job_applications
                    (user_id, profile_id, cache_id, job_url, job_title, company, status,
                     first_seen_at, applied_at, last_updated_at, notes, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (user_id, profile_id, cache_id, job_url, job_title, company, status,
                  now_iso, final_applied_at, now_iso, notes))
        
        conn.commit()
        conn.close()
        logger.debug(f"Upserted job application for user_id={user_id}, profile_id={profile_id}, cache_id={cache_id}")
        
    except Exception as e:
        logger.error(f"Failed to upsert job application: {e}")
        # Re-raise exception to allow caller to handle it
        raise


def get_job_application_by_cache_id(
    user_id: str,
    profile_id: str,
    cache_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Get a single job application record by user_id, profile_id, and cache_id.
    
    Args:
        user_id: User identifier (e.g., "andy_local")
        profile_id: Profile identifier (e.g., "data_engineer_gcp")
        cache_id: JD analysis cache ID (primary key from jd_analysis_cache table)
    
    Returns:
        Dict containing:
        - id: int
        - user_id: str
        - profile_id: str
        - cache_id: Optional[int]
        - job_url: Optional[str]
        - job_title: Optional[str]
        - company: Optional[str]
        - status: str
        - first_seen_at: str (ISO timestamp)
        - applied_at: Optional[str] (ISO timestamp)
        - last_updated_at: str (ISO timestamp)
        - notes: Optional[str]
        
        Returns None if not found or on error (logged as warning).
    """
    try:
        # Ensure DB exists and migration is applied
        ensure_migration()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query for job application (only non-deleted records)
        cursor.execute("""
            SELECT id, user_id, profile_id, cache_id, job_url, job_title, company,
                   status, first_seen_at, applied_at, last_updated_at, notes
            FROM job_applications
            WHERE user_id = ? AND profile_id = ? AND cache_id = ? AND deleted = 0
        """, (user_id, profile_id, cache_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            logger.debug(f"Job application not found for user_id={user_id}, profile_id={profile_id}, cache_id={cache_id}")
            return None
        
        result_dict = {
            "id": row["id"],
            "user_id": row["user_id"],
            "profile_id": row["profile_id"],
            "cache_id": row["cache_id"],
            "job_url": row["job_url"],
            "job_title": row["job_title"],
            "company": row["company"],
            "status": row["status"],
            "first_seen_at": row["first_seen_at"],
            "applied_at": row["applied_at"],
            "last_updated_at": row["last_updated_at"],
            "notes": row["notes"],
        }
        
        logger.debug(f"Retrieved job application for user_id={user_id}, profile_id={profile_id}, cache_id={cache_id}")
        return result_dict
        
    except Exception as e:
        logger.warning(f"Failed to get job application by cache_id: {e}")
        return None


def delete_job_application(
    user_id: str,
    profile_id: str,
    cache_id: int,
) -> bool:
    """
    Soft delete a job application record by user_id, profile_id, and cache_id.
    
    This function performs a soft delete by setting deleted = 1 instead of actually
    removing the record from the database. This allows for data recovery and audit trails.
    
    Args:
        user_id: User identifier (e.g., "andy_local")
        profile_id: Profile identifier (e.g., "data_engineer_gcp")
        cache_id: JD analysis cache ID (primary key from jd_analysis_cache table)
    
    Returns:
        True if record was soft deleted, False if not found or on error.
        On error, logs a warning but does not raise exception (graceful degradation).
    """
    try:
        # Ensure DB exists and migration is applied
        ensure_migration()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Soft delete: set deleted = 1 and update last_updated_at
        cursor.execute("""
            UPDATE job_applications
            SET deleted = 1,
                last_updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND profile_id = ? AND cache_id = ? AND deleted = 0
        """, (user_id, profile_id, cache_id))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if deleted:
            logger.debug(f"Soft deleted job application for user_id={user_id}, profile_id={profile_id}, cache_id={cache_id}")
        else:
            logger.debug(f"Job application not found for soft deletion: user_id={user_id}, profile_id={profile_id}, cache_id={cache_id}")
        
        return deleted
        
    except Exception as e:
        logger.error(f"Failed to soft delete job application: {e}")
        # Re-raise exception to allow caller to handle it
        raise


def list_job_applications(
    user_id: str,
    profile_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    List job application records for a user, optionally filtered by profile_id and status.
    
    Args:
        user_id: User identifier (e.g., "andy_local")
        profile_id: Optional profile identifier to filter by (e.g., "data_engineer_gcp")
        status: Optional status to filter by (planned, applied, interviewing, offer, rejected, skipped)
        limit: Maximum number of results to return (default: 100)
        offset: Number of results to skip (default: 0)
    
    Returns:
        List of dicts, each containing:
        - id: int
        - user_id: str
        - profile_id: str
        - cache_id: Optional[int]
        - job_url: Optional[str]
        - job_title: Optional[str]
        - company: Optional[str]
        - status: str
        - first_seen_at: str (ISO timestamp)
        - applied_at: Optional[str] (ISO timestamp)
        - last_updated_at: str (ISO timestamp)
        - notes: Optional[str]
    
    On error, logs warning and returns empty list (graceful degradation).
    """
    try:
        # Ensure DB exists and migration is applied
        ensure_migration()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build SQL query with optional filters (only non-deleted records)
        sql = """
            SELECT id, user_id, profile_id, cache_id, job_url, job_title, company,
                   status, first_seen_at, applied_at, last_updated_at, notes
            FROM job_applications
            WHERE user_id = ? AND deleted = 0
        """
        params: List[Any] = [user_id]
        
        if profile_id is not None:
            sql += " AND profile_id = ?"
            params.append(profile_id)
        
        if status is not None:
            sql += " AND status = ?"
            params.append(status)
        
        # Add ORDER BY clause (newest first)
        sql += " ORDER BY last_updated_at DESC"
        
        # Add LIMIT and OFFSET
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to list of dicts
        results = []
        for row in rows:
            result_dict = {
                "id": row["id"],
                "user_id": row["user_id"],
                "profile_id": row["profile_id"],
                "cache_id": row["cache_id"],
                "job_url": row["job_url"],
                "job_title": row["job_title"],
                "company": row["company"],
                "status": row["status"],
                "first_seen_at": row["first_seen_at"],
                "applied_at": row["applied_at"],
                "last_updated_at": row["last_updated_at"],
                "notes": row["notes"],
            }
            results.append(result_dict)
        
        logger.debug(f"Listed {len(results)} job applications for user_id={user_id}, profile_id={profile_id}, status={status}")
        return results
        
    except Exception as e:
        logger.warning(f"Failed to list job applications: {e}")
        return []
