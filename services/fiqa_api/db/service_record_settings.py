"""
Environment wiring for Stage 1 service-record Postgres.

Dual-write is opt-in so local demo and Cloud Run without DB are unchanged.

**Paid pilot:** Postgres is the only supported persistence truth (see
``docs/CURRENT_PRODUCT_SHAPE.md``). JSON case file paths below are
**legacy/dev compatibility** — not for ``ENV=prod`` or PG-primary pilots.

**Local dev:** JSON-only cases are OK when no ``SERVICE_RECORD_DATABASE_URL``.
"""

from __future__ import annotations

import os
from typing import Any


def service_record_database_url() -> str | None:
    """Primary connection string for service-record tables."""
    for key in ("SERVICE_RECORD_DATABASE_URL", "DATABASE_URL"):
        raw = (os.getenv(key) or "").strip()
        if raw:
            return raw
    return None


def allow_inmemory_intake_sessions() -> bool:
    """
    When no database URL is set, intake session persistence may use an in-process store
    only if this flag is explicitly enabled (tests and ad-hoc local scripts).

    Env: UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS=1|true|yes|on

    Normal / production-like runtime should leave this unset and configure
    SERVICE_RECORD_DATABASE_URL or DATABASE_URL so sessions are Postgres-backed.

    Rollback: unset this variable; configure a database URL for durable sessions.
    """
    raw = (os.getenv("UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


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


def is_production_mode() -> bool:
    """
    Production-like runtime: Postgres is the only durable case source of truth.

    True when ENV=prod (deployment) or UNIFIED_INTAKE_DB_PRIMARY_WRITES is on (PG-primary
    writes). Used to gate JSON case file reads/writes and read fallbacks — not a substitute
    for configuring SERVICE_RECORD_DATABASE_URL / DATABASE_URL.

    Note: Cloud QA (ENV=qa, fiqa-api-qa) also enables DB-primary writes, so this returns
    True there for persistence safety. Operator/console "Production" branding must use
    :func:`is_production_deployment` instead — never treat PG-primary alone as Production.
    """
    if (os.getenv("ENV") or "").strip().lower() == "prod":
        return True
    return _truthy_env("UNIFIED_INTAKE_DB_PRIMARY_WRITES")


def is_production_deployment() -> bool:
    """
    True when this process is an explicit Production *deployment* label.

    Used by Founder QA / operator status surfaces (``production_like``) so Cloud QA is
    never silently branded as Production. Distinct from :func:`is_production_mode`,
    which is also True when UNIFIED_INTAKE_DB_PRIMARY_WRITES is on (Cloud QA posture).

    Signals (no hostname guessing):
    - SERVICE_NAME=fiqa-api-qa or ENV=qa → False (Cloud QA)
    - ENV=prod or SERVICE_NAME=fiqa-api → True (Production)
    - Missing / ambiguous ENV+SERVICE_NAME → False (fail visible; do not claim Production)
    """
    env = (os.getenv("ENV") or "").strip().lower()
    service = (os.getenv("SERVICE_NAME") or "").strip().lower()

    if service == "fiqa-api-qa" or env == "qa":
        return False
    if env == "prod" or service == "fiqa-api":
        return True
    return False


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
    if is_production_mode():
        return True
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

    :func:`is_production_mode` is always False-return here: production must not use JSON
    as case truth.

    When not in that mode: default is to allow JSON fallback. Set
    UNIFIED_INTAKE_JSON_READ_FALLBACK=0|false|no|off to disable
    (strict DB-only reads; missing row → None / 404).
    """
    if is_production_mode():
        return False
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
    Legacy/dev compatibility: JSON case file writes (``unified_intake_cases.json``).

    When False, case_store skips writing the JSON file for pilot DB-primary mode.

    Default: True (JSON writes on). Set UNIFIED_INTAKE_JSON_CASE_WRITES=0|false|no|off
    to disable JSON case writes (requires DB primary writes for online pilot).

    Paid pilot: must be off — ``is_production_mode()`` forces False when ENV=prod.

    Rollback: UNIFIED_INTAKE_JSON_CASE_WRITES=1 or unset.
    """
    if is_production_mode():
        return False
    if _falsy_env("UNIFIED_INTAKE_JSON_CASE_WRITES"):
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


def unified_intake_case_persistence_report() -> dict[str, Any]:
    """
    Operator-facing snapshot: Postgres vs JSON case persistence posture (no deploy changes).

    ``unified_intake_case_persistence_mode`` is one of:
    STRICT_PG_ONLY, PG_FIRST_BUT_NOT_STRICT, MIXED_STATE, UNKNOWN
    """
    has_db = service_record_database_url() is not None
    prod = is_production_mode()
    db_w = db_primary_writes_enabled()
    db_r = db_primary_reads_enabled()
    jw = json_case_writes_enabled()
    dual = service_record_dual_write_enabled()
    pg_primary = postgres_case_persistence_primary()
    jfb = json_read_fallback_allowed()

    mode = "UNKNOWN"
    if not has_db:
        mode = "MIXED_STATE" if prod else "UNKNOWN"
    elif prod:
        mode = "STRICT_PG_ONLY" if db_w else "MIXED_STATE"
    elif pg_primary:
        mode = "STRICT_PG_ONLY"
    elif dual or (db_w and jw) or (db_r and jw):
        mode = "PG_FIRST_BUT_NOT_STRICT"
    elif db_w and not jw:
        mode = "STRICT_PG_ONLY"
    elif db_r and jw and not db_w:
        mode = "PG_FIRST_BUT_NOT_STRICT"
    else:
        mode = "UNKNOWN"

    return {
        "unified_intake_case_persistence_mode": mode,
        "has_service_record_database_url": has_db,
        "is_production_mode": prod,
        "db_primary_writes": db_w,
        "db_primary_reads": db_r,
        "json_case_writes": jw,
        "dual_write": dual,
        "postgres_case_persistence_primary": pg_primary,
        "json_read_fallback_allowed": jfb,
    }
