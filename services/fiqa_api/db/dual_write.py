"""
Opt-in dual-write from JSON case_store to Postgres.

Pilot behavior: JSON remains authoritative; Postgres errors are logged only.
"""

from __future__ import annotations

import logging
from typing import Any

from services.fiqa_api.db.service_record_settings import service_record_dual_write_enabled

logger = logging.getLogger(__name__)


def maybe_dual_write_new_case(case: dict[str, Any]) -> None:
    if not service_record_dual_write_enabled():
        return
    try:
        from services.fiqa_api.db.service_record_repository import persist_new_case

        persist_new_case(case)
    except Exception:
        logger.exception("Postgres dual-write failed for new case (JSON store is source of truth)")


def maybe_dual_write_case_append(case: dict[str, Any]) -> None:
    if not service_record_dual_write_enabled():
        return
    try:
        from services.fiqa_api.db.service_record_repository import persist_case_append

        persist_case_append(case)
    except Exception:
        logger.exception("Postgres dual-write failed for case append (JSON store is source of truth)")
