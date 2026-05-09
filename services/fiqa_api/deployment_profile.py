"""
Unified Intake deployment profiles — product-only vs full platform.

``UNIFIED_INTAKE_PRODUCT_ONLY=1`` reduces FastAPI *included routers* to the
Unified Intake sellable surface + health/Qdrant probes + founder analytics.

**Wire honesty:** platform/lab/graph/tuner/demo routes that were previously
registered as unguarded ``@app.*`` handlers are defined in
``platform_inline_routes.register_platform_inline_routes`` and are invoked only
when **not** in product-only mode. The historical leak list is kept empty and
documented for auditors; see ``docs/sprints/STRICT_PRODUCT_ONLY_WIRE_CLOSURE_SUPPORT_EXPORT_SPRINT.md``.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Final

_ENV_KEY: Final = "UNIFIED_INTAKE_PRODUCT_ONLY"
_DEMO_MODE_KEYS: Final[tuple[str, ...]] = ("1", "true", "yes", "on")

# Bump when ``service_records`` / ``intake_sessions`` DDL, case document shape, or
# triage HTTP contract changes in a way that breaks read compatibility or replay.
# Surfaced on ``GET /health`` and ``GET /api/inbox/support/deployment-manifest``.
INTAKE_SCHEMA_EPOCH: Final[str] = "2026-05-09_org_continuity_office_owner_column_v1"


def intake_schema_epoch() -> str:
    """Operator-visible schema / contract generation label (not a DB migration id)."""

    return INTAKE_SCHEMA_EPOCH

# Historically: FastAPI paths registered inline on ``app`` in ``app_main.py`` that
# stayed mounted even in product-only mode. Those handlers now live in
# ``platformInlineRoutes`` and are not registered when product-only is on.
PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN: Final[tuple[str, ...]] = ()


def is_unified_intake_product_only() -> bool:
    raw = (os.environ.get(_ENV_KEY) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def platform_inline_route_leak_count() -> int:
    """Count of documented ungated inline platform routes (for metrics / banners)."""

    return len(PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN)


def deployment_operator_warnings() -> list[str]:
    """
    Stable warning codes for operators (health + deployment-manifest). Not alarms — honesty.

    Rollback: fix env contradictions; these codes disappear when posture is consistent.
    """

    warnings: list[str] = []
    demo_raw = (os.environ.get("DEMO_MODE") or "").strip().lower()
    env_raw = (os.environ.get("ENV") or "").strip().lower()
    demo_on = demo_raw in _DEMO_MODE_KEYS
    if env_raw == "prod" and demo_on:
        warnings.append("env_prod_with_demo_mode_truthy_v1")

    try:
        from services.fiqa_api.db.service_record_settings import (
            allow_inmemory_intake_sessions,
            is_production_mode,
            service_record_database_url,
        )

        has_db = service_record_database_url() is not None
        if is_production_mode() and not has_db:
            warnings.append("production_like_missing_service_record_database_url_v1")
        if allow_inmemory_intake_sessions():
            if has_db:
                warnings.append("inmemory_sessions_flag_on_while_db_url_configured_v1")
            elif is_production_mode():
                warnings.append("inmemory_sessions_allowed_in_production_like_mode_v1")
    except Exception:
        logging.getLogger(__name__).debug(
            "deployment_operator_warnings: persistence posture checks skipped",
            exc_info=True,
        )

    return warnings


def operator_runtime_hints() -> dict[str, Any]:
    """Non-secret env flags for deployment-manifest / health (drift detection, not security).

    Values are booleans or short strings only — never secrets or connection strings.
    """

    demo_raw = (os.environ.get("DEMO_MODE") or "").strip().lower()
    env_raw = (os.environ.get("ENV") or "").strip().lower()
    fast_raw = (os.environ.get("FAST_STARTUP") or "1").strip().lower()

    try:
        from services.fiqa_api.db.service_record_settings import allow_inmemory_intake_sessions

        inmem_allowed = allow_inmemory_intake_sessions()
    except Exception:
        logging.getLogger(__name__).debug(
            "operator_runtime_hints: allow_inmemory_intake_sessions unreadable",
            exc_info=True,
        )
        inmem_allowed = False

    return {
        "demo_mode": demo_raw in _DEMO_MODE_KEYS,
        "env_label_raw": env_raw or "",
        "demo_mode_raw": demo_raw or "",
        "env_equals_prod": env_raw == "prod",
        "fast_startup": fast_raw in _DEMO_MODE_KEYS,
        "unified_intake_product_only": is_unified_intake_product_only(),
        "unified_intake_allow_inmemory_sessions_for_tests": inmem_allowed,
        "operator_warnings": deployment_operator_warnings(),
    }


def log_deployment_profile_banner(log: logging.Logger) -> None:
    if is_unified_intake_product_only():
        n = platform_inline_route_leak_count()
        if n:
            log.warning(
                "deployment_profile=unified_intake_product_only (%s): gated routers omitted; "
                "%d additional platform/lab routes remain registered inline on app "
                "(see deployment_profile.PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN).",
                _ENV_KEY,
                n,
            )
        else:
            log.info(
                "deployment_profile=unified_intake_product_only (%s): product wire surface; "
                "platform inline routes deferred to register_platform_inline_routes() "
                "(not called in this profile). SSOT: "
                "docs/sprints/STRICT_PRODUCT_ONLY_WIRE_CLOSURE_SUPPORT_EXPORT_SPRINT.md.",
                _ENV_KEY,
            )
    else:
        log.info(
            "deployment_profile=platform_full (set %s=1 for reduced Unified Intake API surface)",
            _ENV_KEY,
        )
