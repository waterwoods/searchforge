"""
health_db.py - SQLite Database Module for Health Monitoring

This module provides database functionality for storing health readings (heart rate, SpO2)
from ESP32 devices using SQLite.

Key features:
- Automatic database initialization
- Thread-safe short-lived connections (no persistent connections)
- Graceful error handling (warnings, no exceptions thrown)
"""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Database file path (following jobhunter pattern)
# Use .runs directory for writable database (always writable in Docker)
BASE_DIR = Path(__file__).resolve().parent
RUNS_DIR = BASE_DIR.parent.parent.parent / ".runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = RUNS_DIR / "health_readings.sqlite3"

logger.info(f"Using health database at {DB_PATH}")


def init_health_db() -> None:
    """
    Create SQLite DB and health_readings table if not exists.
    
    This function is idempotent - safe to call multiple times.
    Creates the table with necessary indexes for efficient lookups.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL DEFAULT 'esp32-default',
                hr REAL NOT NULL,
                spo2 REAL NOT NULL,
                time_ms INTEGER,
                time_str TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Create index on created_at for efficient time-based queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_readings_created_at
                ON health_readings (created_at DESC)
        """)
        
        # Create index on source for filtering by device
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_readings_source
                ON health_readings (source)
        """)
        
        conn.commit()
        conn.close()
        logger.debug(f"Health database initialized at {DB_PATH}")
    except Exception as e:
        logger.warning(f"Failed to initialize health database: {e}")
        # Don't raise - let the calling code handle gracefully


def insert_health_reading(
    hr: float,
    spo2: float,
    time_ms: Optional[int] = None,
    time_str: Optional[str] = None,
    source: str = "esp32-default",
) -> None:
    """
    Insert a health reading into the database.
    
    Args:
        hr: Heart rate (beats per minute)
        spo2: Blood oxygen saturation (percentage)
        time_ms: Optional timestamp in milliseconds from ESP32
        time_str: Optional timestamp string from ESP32 (YYYY-MM-DD HH:MM:SS)
        source: Device identifier (default: 'esp32-default')
        
    Note:
        On error, logs a warning but does not raise exception (graceful degradation).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_health_db()
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        # Get current UTC timestamp (ISO8601 format)
        now_iso = datetime.utcnow().isoformat()
        
        # Insert reading
        cursor.execute("""
            INSERT INTO health_readings
                (source, hr, spo2, time_ms, time_str, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (source, hr, spo2, time_ms, time_str, now_iso))
        
        conn.commit()
        conn.close()
        logger.debug(f"Inserted health reading: hr={hr}, spo2={spo2}, source={source}")
        
    except Exception as e:
        logger.warning(f"Failed to insert health reading: {e}")
        # Don't raise - graceful degradation


def get_latest_health_readings(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get the latest health readings from the database.
    
    Args:
        limit: Maximum number of results to return (default: 50)
    
    Returns:
        List of dicts, each containing:
        - id: int
        - source: str
        - hr: float
        - spo2: float
        - time_ms: Optional[int]
        - time_str: Optional[str]
        - created_at: str (ISO timestamp)
    
    On error, logs warning and returns empty list (graceful degradation).
    """
    try:
        # Ensure DB exists
        if not DB_PATH.exists():
            init_health_db()
            return []
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query latest readings ordered by created_at DESC
        cursor.execute("""
            SELECT id, source, hr, spo2, time_ms, time_str, created_at
            FROM health_readings
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to list of dicts
        results = []
        for row in rows:
            result_dict = {
                "id": row["id"],
                "source": row["source"],
                "hr": row["hr"],
                "spo2": row["spo2"],
                "time_ms": row["time_ms"],
                "time_str": row["time_str"],
                "created_at": row["created_at"],
            }
            results.append(result_dict)
        
        logger.debug(f"Retrieved {len(results)} health readings")
        return results
        
    except Exception as e:
        logger.warning(f"Failed to get latest health readings: {e}")
        return []
