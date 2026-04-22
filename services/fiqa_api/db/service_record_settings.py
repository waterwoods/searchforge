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


def _falsy_env(name: str) -> bool:
    """True when env is explicitly 0/false/no/off (unset = not falsy)."""
    raw = (os.getenv(name) or "").strip().lower()
    return raw in ("0", "false", "no", "off")


def db_primary_reads_enabled() -> bool:
    """
    When True, HTTP/API case reads (and case_store mutations via the same facade)
    prefer Postgres (see case_truth_repository).

    Requires SERVICE_RECORD_DATABASE_URL or DATABASE_URL.

    Enabled when any of:
    - UNIFIED_INTAKE_DB_PRIMARY_READS=1|true|yes|on
    - UNIFIED_INTAKE_DB_PRIMARY_WRITES=1 with UNIFIED_INTAKE_JSON_CASE_WRITES off
      (strict pilot: writes are DB-only, reads must not be JSON-first).
    - UNIFIED_INTAKE_PG_DUAL_WRITE=1 (Postgres mirror receives the same creates/appends
      as JSON; JSON-first reads break read-your-writes across instances).

    **Rollback / debug:** set UNIFIED_INTAKE_DB_PRIMARY_READS=0|false|no|off to force
    JSON-first reads even when dual-write or strict pilot writes would otherwise
    prefer Postgres (use only when re-enabling JSON authority locally).
    """
    if not service_record_database_url():
        return False
    if _falsy_env("UNIFIED_INTAKE_DB_PRIMARY_READS"):
        return False
    if _truthy_env("UNIFIED_INTAKE_DB_PRIMARY_READS"):
        return True
    if db_primary_writes_enabled() and not json_case_writes_enabled():
        return True
    if service_record_dual_write_enabled():
        return True
    return False


def json_read_fallback_allowed() -> bool:
    """
    When DB-primary reads are on, allow falling back to JSON if the PG row is missing
    or the DB read errors (transition / dual-track).

    When :func:`postgres_case_persistence_primary` is True (Postgres is the only durable
    case store — DB primary writes on, JSON case file writes off), this always returns
    False. No silent JSON case reads in that mode, even if
    ``UNIFIED_INTAKE_JSON_READ_FALLBACK`` is set to a truthy value (avoids
    misconfiguration during pilot).

    When not in that mode: default is to allow JSON fallback. Set
    UNIFIED_INTAKE_JSON_READ_FALLBACK=0|false|no|off to disable
    (strict DB-only reads; missing row → None / 404).
    """
    if postgres_case_persistence_primary():
        return False
    raw = (os.getenv("UNIFIED_INTAKE_JSON_READ_FALLBACK") or "").strip().lower()
    if not raw:
        return True
    return raw not in ("0", "false", "no", "off")


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


def json_session_writes_enabled() -> bool:
    """
    When False, session_store skips writing unified_intake_sessions.json (no server-side
    in-progress restore after refresh). Use for strict production deployments that must
    not create or update session JSON on disk.

    Default: True (session JSON writes on). Set UNIFIED_INTAKE_JSON_SESSION_WRITES=0|false|no|off
    to disable.

    Rollback: unset UNIFIED_INTAKE_JSON_SESSION_WRITES or set to 1|true|yes|on.
    """
    if _falsy_env("UNIFIED_INTAKE_JSON_SESSION_WRITES"):
        return False
    return True


def postgres_case_persistence_primary() -> bool:
    """
    True when DB URL is set, Postgres primary writes are on, and JSON case file writes are off.

    In this configuration the durable case record is Postgres; JSON case files must not be
    treated as authoritative (see case_truth_repository + UNIFIED_INTAKE_JSON_READ_FALLBACK).
    """
    return bool(
        service_record_database_url()
        and db_primary_writes_enabled()
        and not json_case_writes_enabled()
    )
