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


def _truthy_env(name: str) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def db_primary_reads_enabled() -> bool:
    """
    When True, HTTP/API case reads prefer Postgres (see case_truth_repository).

    Requires SERVICE_RECORD_DATABASE_URL or DATABASE_URL, and
    UNIFIED_INTAKE_DB_PRIMARY_READS=1|true|yes|on (default off).

    **Strict pilot alignment:** if UNIFIED_INTAKE_DB_PRIMARY_WRITES is on and
    UNIFIED_INTAKE_JSON_CASE_WRITES is off, reads are forced to Postgres so
    workbench/list/detail cannot read an empty or stale JSON file while writes
    go only to the database.
    """
    if not service_record_database_url():
        return False
    if _truthy_env("UNIFIED_INTAKE_DB_PRIMARY_READS"):
        return True
    if db_primary_writes_enabled() and not json_case_writes_enabled():
        return True
    return False


def json_read_fallback_allowed() -> bool:
    """
    When DB-primary reads are on, allow falling back to JSON if the PG row is missing
    or the DB read errors (transition / dual-track).

    Default: allowed. Set UNIFIED_INTAKE_JSON_READ_FALLBACK=0|false|no|off to disable
    (strict DB-only reads; missing row → None / 404).
    """
    raw = (os.getenv("UNIFIED_INTAKE_JSON_READ_FALLBACK") or "").strip().lower()
    if not raw:
        return True
    return raw not in ("0", "false", "no", "off")


def _falsy_env(name: str) -> bool:
    """True when env is explicitly 0/false/no/off (unset = not falsy)."""
    raw = (os.getenv(name) or "").strip().lower()
    return raw in ("0", "false", "no", "off")


def db_primary_writes_enabled() -> bool:
    """
    When True, case create/append and related mutations persist to Postgres first.

    Requires SERVICE_RECORD_DATABASE_URL or DATABASE_URL, and
    UNIFIED_INTAKE_DB_PRIMARY_WRITES=1|true|yes|on (default off).

    Rollback: unset DB_PRIMARY_WRITES; keep JSON writes on (default).
    """
    if not service_record_database_url():
        return False
    return _truthy_env("UNIFIED_INTAKE_DB_PRIMARY_WRITES")


def json_case_writes_enabled() -> bool:
    """
    When False, case_store skips writing unified_intake_cases.json for pilot DB-primary mode.

    Default: True (JSON writes on). Set UNIFIED_INTAKE_JSON_CASE_WRITES=0|false|no|off
    to disable JSON case writes (requires DB primary writes for online pilot).

    Rollback: UNIFIED_INTAKE_JSON_CASE_WRITES=1 or unset.
    """
    if _falsy_env("UNIFIED_INTAKE_JSON_CASE_WRITES"):
        return False
    return True
