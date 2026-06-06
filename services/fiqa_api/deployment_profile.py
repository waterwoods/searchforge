"""
Unified Intake deployment profiles — product-only vs full platform.

**Paid pilot / sellable product:** ``UNIFIED_INTAKE_PRODUCT_ONLY=1`` (required).

**platform_full** (flag off): legacy/dev mode — mounts lab/RAG/tuner routers.
Do not use on public broker URLs; startup warns in production-like mode.

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

# Operator-visible **contract generation label** (not a DB migration id).
# Bump when ``service_records`` / ``intake_sessions`` DDL, case document shape, or
# triage HTTP contract changes in a way that breaks read compatibility or replay.
# Surfaced on ``GET /health`` and ``GET /api/inbox/support/deployment-manifest``.
INTAKE_SCHEMA_EPOCH: Final[str] = "2026-05-11_minimal_signed_broker_token_v1"


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


def runtime_service_display_name() -> str:
    """Human-facing API name for logs, /version, and health JSON (keys unchanged)."""

    if is_unified_intake_product_only():
        return "Unified Intake API"
    return "SearchForge Main API (lab/dev — set UNIFIED_INTAKE_PRODUCT_ONLY=1 for paid pilot)"


def platform_inline_route_leak_count() -> int:
    """Count of documented ungated inline platform routes (for metrics / banners)."""

    return len(PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN)


def pilot_safe_default_profile_v1() -> dict[str, str]:
    """
    Documented minimum env tuple for a survivable paid pilot (not enforced at import).

    Values are placeholders — operators fill secrets in ``.env.cloudrun`` / Secret Manager.
    """

    return {
        "ENV": "prod",
        "UNIFIED_INTAKE_PRODUCT_ONLY": "1",
        "UNIFIED_INTAKE_DB_PRIMARY_READS": "1",
        "UNIFIED_INTAKE_DB_PRIMARY_WRITES": "1",
        "UNIFIED_INTAKE_JSON_CASE_WRITES": "0",
        "UNIFIED_INTAKE_JSON_READ_FALLBACK": "0",
        "UNIFIED_INTAKE_PG_DUAL_WRITE": "0",
        "SERVICE_RECORD_DATABASE_URL": "<required — Secret Manager recommended>",
        "UNIFIED_INTAKE_INTAKE_API_KEY": "<required — 24+ char random>",
        "UNIFIED_INTAKE_SUPPORT_API_KEY": "<required — 24+ char random>",
        "DEMO_MODE": "0",
    }


OPERATOR_WARNING_HUMAN: Final[dict[str, str]] = {
    "intake_api_key_equals_support_api_key_reduces_perimeter_separation_v1": (
        "Intake and support API keys are the same — use two different keys"
    ),
    "env_prod_with_demo_mode_truthy_v1": (
        "DEMO_MODE is on while ENV=prod — forbidden on paid pilot"
    ),
    "platform_full_api_surface_in_production_like_mode_v1": (
        "Lab/RAG API is exposed — set UNIFIED_INTAKE_PRODUCT_ONLY=1 for broker pilot"
    ),
    "production_like_missing_service_record_database_url_v1": (
        "Postgres URL missing — cases will not persist on paid pilot"
    ),
    "production_like_runtime_without_intake_api_key_v1": (
        "Intake API key missing — broker-facing endpoints are anonymous"
    ),
    "production_like_runtime_without_support_api_key_v1": (
        "Support API key missing — export/manifest endpoints are anonymous"
    ),
    "production_like_without_db_primary_writes_v1": (
        "Postgres primary writes off — cases may not land in Postgres"
    ),
    "json_case_writes_enabled_in_production_like_mode_v1": (
        "JSON case writes enabled — forbidden when ENV=prod or PG-primary"
    ),
    "dual_write_enabled_in_production_like_mode_v1": (
        "Dual-write (JSON + Postgres) enabled — use one write path only"
    ),
    "inmemory_sessions_flag_on_while_db_url_configured_v1": (
        "In-memory sessions with Postgres URL — unsafe for multi-instance Cloud Run"
    ),
    "inmemory_sessions_allowed_in_production_like_mode_v1": (
        "In-memory sessions allowed in prod-like mode — sessions will not survive restarts"
    ),
    "office_enforcement_on_without_service_record_database_url_multi_instance_unsafe_v1": (
        "Office enforcement on without Postgres — unsafe for multi-instance deploy"
    ),
    "broker_token_hmac_secret_shorter_than_recommended_v1": (
        "Broker token HMAC secret is shorter than 24 chars — use a longer random secret"
    ),
    "broker_token_hmac_configured_but_deploy_binding_unbound_production_like_v1": (
        "Broker token HMAC set but deploy binding unbound in prod-like mode"
    ),
}


def humanize_operator_warnings(codes: list[str] | None = None) -> list[str]:
    """Stable warning codes → short operator sentences (no secrets)."""

    raw = codes if codes is not None else deployment_operator_warnings()
    return [OPERATOR_WARNING_HUMAN.get(code, f"Review env: {code}") for code in raw]


def deployment_operator_warnings() -> list[str]:
    """
    Stable warning codes for operators (health + deployment-manifest). Not alarms — honesty.

    Rollback: fix env contradictions; these codes disappear when posture is consistent.
    """

    warnings: list[str] = []
    intake_k = (os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    support_k = (os.environ.get("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    if intake_k and support_k and intake_k == support_k:
        warnings.append("intake_api_key_equals_support_api_key_reduces_perimeter_separation_v1")

    demo_raw = (os.environ.get("DEMO_MODE") or "").strip().lower()
    env_raw = (os.environ.get("ENV") or "").strip().lower()
    demo_on = demo_raw in _DEMO_MODE_KEYS
    if env_raw == "prod" and demo_on:
        warnings.append("env_prod_with_demo_mode_truthy_v1")

    if not is_unified_intake_product_only():
        try:
            from services.fiqa_api.db.service_record_settings import is_production_mode

            if is_production_mode():
                warnings.append("platform_full_api_surface_in_production_like_mode_v1")
        except Exception:
            pass

    try:
        from services.fiqa_api.db.service_record_settings import (
            allow_inmemory_intake_sessions,
            db_primary_writes_enabled,
            is_production_mode,
            json_case_writes_enabled,
            service_record_database_url,
            service_record_dual_write_enabled,
        )
        from services.fiqa_api.security.case_office_access import case_office_enforcement_enabled

        has_db = service_record_database_url() is not None
        prod_like = is_production_mode()
        if prod_like and not has_db:
            warnings.append("production_like_missing_service_record_database_url_v1")
        if prod_like and not intake_k:
            warnings.append("production_like_runtime_without_intake_api_key_v1")
        if prod_like and not support_k:
            warnings.append("production_like_runtime_without_support_api_key_v1")
        if prod_like and has_db and not db_primary_writes_enabled():
            warnings.append("production_like_without_db_primary_writes_v1")
        if prod_like and json_case_writes_enabled():
            warnings.append("json_case_writes_enabled_in_production_like_mode_v1")
        if prod_like and service_record_dual_write_enabled():
            warnings.append("dual_write_enabled_in_production_like_mode_v1")
        if allow_inmemory_intake_sessions():
            if has_db:
                warnings.append("inmemory_sessions_flag_on_while_db_url_configured_v1")
            elif prod_like:
                warnings.append("inmemory_sessions_allowed_in_production_like_mode_v1")
        if case_office_enforcement_enabled() and prod_like and not has_db:
            warnings.append(
                "office_enforcement_on_without_service_record_database_url_multi_instance_unsafe_v1"
            )
    except Exception:
        logging.getLogger(__name__).debug(
            "deployment_operator_warnings: persistence posture checks skipped",
            exc_info=True,
        )

    try:
        from services.fiqa_api.security.token_scope_posture import token_scope_operator_warnings

        warnings.extend(token_scope_operator_warnings())
    except Exception:
        logging.getLogger(__name__).debug(
            "deployment_operator_warnings: token_scope_operator_warnings skipped",
            exc_info=True,
        )

    try:
        from services.fiqa_api.security.minimal_signed_broker_token import (
            broker_token_hmac_secret_configured,
            effective_deploy_binding,
        )
        from services.fiqa_api.db.service_record_settings import is_production_mode

        if broker_token_hmac_secret_configured():
            raw = (os.environ.get("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET") or "").strip()
            if raw and len(raw) < 24:
                warnings.append("broker_token_hmac_secret_shorter_than_recommended_v1")
            if is_production_mode() and effective_deploy_binding() == "unbound_v1":
                warnings.append(
                    "broker_token_hmac_configured_but_deploy_binding_unbound_production_like_v1"
                )
    except Exception:
        logging.getLogger(__name__).debug(
            "deployment_operator_warnings: broker token posture skipped",
            exc_info=True,
        )

    return warnings


def deployment_identity_truth() -> dict[str, Any]:
    """
    Best-effort labels for “which revision is answering?” in tickets.

    Not tamper-evident and not a substitute for release automation — only reduces
    “we thought we deployed X” disputes when platforms inject standard env vars.
    """

    rev = (os.environ.get("K_REVISION") or "").strip()
    svc = (os.environ.get("K_SERVICE") or "").strip()
    cfg = (os.environ.get("K_CONFIGURATION") or "").strip()
    sha_env: str | None = None
    for key in ("GIT_SHA", "COMMIT_SHA", "SOURCE_VERSION", "VERCEL_GIT_COMMIT_SHA"):
        raw = (os.environ.get(key) or "").strip()
        if raw:
            sha_env = raw[:64]
            break
    return {
        "semantics": "best_effort_deploy_labels_not_tamper_evident_v1",
        "k_service": svc or None,
        "k_revision": rev or None,
        "k_configuration": cfg or None,
        "commit_sha_from_env": sha_env,
    }


_INTAKE_CORE_READINESS_KEY: Final = "UNIFIED_INTAKE_INTAKE_CORE_READINESS"


def intake_core_readiness_enabled() -> bool:
    """
    Paid-pilot intake SaaS: /readyz may treat Qdrant/embedding as optional when set.

    Requires UNIFIED_INTAKE_PRODUCT_ONLY=1 so platform_full lab stacks stay strict.
    Not a substitute for DEMO_MODE on demo-cloud smoke deploys.
    """

    raw = (os.environ.get(_INTAKE_CORE_READINESS_KEY) or "").strip().lower()
    if raw not in _DEMO_MODE_KEYS:
        return False
    return is_unified_intake_product_only()


def intake_readiness_posture_dict() -> dict[str, Any]:
    """Operator summary: intake-core vs full-stack readiness (no secrets)."""

    demo_on = (os.environ.get("DEMO_MODE") or "").strip().lower() in _DEMO_MODE_KEYS
    intake_core = intake_core_readiness_enabled()
    vectors_optional = demo_on or intake_core
    if vectors_optional:
        mode = "intake_core"
    else:
        mode = "full_stack"
    return {
        "readiness_mode": mode,
        "demo_mode": demo_on,
        "intake_core_readiness": intake_core,
        "product_only": is_unified_intake_product_only(),
        "qdrant_blocks_readyz": not vectors_optional,
        "embedding_blocks_readyz": not vectors_optional,
        "intake_triage_needs_qdrant": False,
        "operator_note": (
            "Inbox triage is LLM/rule-based; Qdrant is for notice/knowledge wedge only."
            if vectors_optional
            else "/readyz requires Qdrant + embedding unless DEMO_MODE or intake_core_readiness."
        ),
    }


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

    warnings = deployment_operator_warnings()
    return {
        "demo_mode": demo_raw in _DEMO_MODE_KEYS,
        "env_label_raw": env_raw or "",
        "demo_mode_raw": demo_raw or "",
        "env_equals_prod": env_raw == "prod",
        "fast_startup": fast_raw in _DEMO_MODE_KEYS,
        "unified_intake_product_only": is_unified_intake_product_only(),
        "intake_core_readiness": intake_core_readiness_enabled(),
        "intake_readiness_posture": intake_readiness_posture_dict(),
        "unified_intake_allow_inmemory_sessions_for_tests": inmem_allowed,
        "operator_warnings": warnings,
        "operator_warnings_human": humanize_operator_warnings(warnings),
        "deployment_identity": deployment_identity_truth(),
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
            "deployment_profile=platform_full (OPTIONAL lab/RAG — set %s=1 for Unified Intake SaaS / paid pilot)",
            _ENV_KEY,
        )
