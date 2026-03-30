"""
Environment wiring for Stage 1 service-record Postgres.

Dual-write is opt-in so local demo and Cloud Run without DB are unchanged.
"""

from __future__ import annotations

import os


def service_record_database_url() -> str | None:
    """Primary connection string for service-record tables."""
    for key in ("SERVICE_RECORD_DATABASE_URL", "DATABASE_URL"):
        raw = (os.getenv(key) or "").strip()
        if raw:
            return raw
    return None


def service_record_dual_write_enabled() -> bool:
    """
    When True and a database URL is set, new case writes also go to Postgres.

    Env: UNIFIED_INTAKE_PG_DUAL_WRITE=1|true|yes (default off).
    """
    if not service_record_database_url():
        return False
    flag = (os.getenv("UNIFIED_INTAKE_PG_DUAL_WRITE") or "").strip().lower()
    return flag in ("1", "true", "yes", "on")
