"""
Opt-in dual-write from JSON case_store to Postgres.

When UNIFIED_INTAKE_PG_DUAL_WRITE is on (and a DB URL is set), creates/appends are
mirrored to Postgres; failures are logged only (JSON still receives the write).

Reads: with dual-write enabled, `db_primary_reads_enabled()` is true so HTTP and
mutations prefer Postgres first (JSON fallback when allowed) — see case_truth_repository.

When UNIFIED_INTAKE_DB_PRIMARY_WRITES is on, Postgres is written from case_store
directly; these helpers become no-ops to avoid duplicate inserts/appends.
"""

from __future__ import annotations

import logging
from typing import Any

from services.fiqa_api.db.service_record_settings import (
    db_primary_writes_enabled,
    service_record_dual_write_enabled,
)

logger = logging.getLogger(__name__)


def maybe_dual_write_new_case(case: dict[str, Any]) -> None:
    if db_primary_writes_enabled():
        return
    if not service_record_dual_write_enabled():
        return
    try:
        from services.fiqa_api.db.service_record_repository import persist_new_case

        persist_new_case(case)
    except Exception:
        logger.exception(
            "UNIFIED_INTAKE_DB_OBS signal=PG_DUAL_WRITE_NEW_CASE_FAIL (JSON store is source of truth)"
        )


def maybe_dual_write_case_append(case: dict[str, Any]) -> None:
    if db_primary_writes_enabled():
        return
    if not service_record_dual_write_enabled():
        return
    try:
        from services.fiqa_api.db.service_record_repository import persist_case_append

        persist_case_append(case)
    except Exception:
        logger.exception(
            "UNIFIED_INTAKE_DB_OBS signal=PG_DUAL_WRITE_APPEND_FAIL (JSON store is source of truth)"
        )
