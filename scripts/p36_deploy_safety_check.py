#!/usr/bin/env python3
"""
P36 T3 — Cloud QA / Production deploy safety check (fail-closed).

Rejects dangerous env/service/secret combinations before gcloud deploy.
Does not deploy, provision, or mutate infrastructure.

Canonical names: docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Frozen names (P36 T1 SSOT)
PROD_SERVICE_NAME = "fiqa-api"
QA_SERVICE_NAME = "fiqa-api-qa"
PROD_DATABASE_NAME = "caseiq"
QA_DATABASE_NAME = "caseiq-qa"
PROD_DB_SECRET = "fiqa-service-record-database-url-cloudsql-private"
QA_DB_SECRET = "fiqa-service-record-database-url-qa"
PROD_ENV_FILE_NAME = ".env.cloudrun"
QA_ENV_FILE_NAME = ".env.cloudrun.qa"

# QA Harness / fixture flags — opt-in only; never default ON; never on Production.
QA_HARNESS_FLAGS = (
    "ENABLE_P35_MP_QA_HARNESS",
    "ENABLE_P26H_FIXTURE_RUNNER",
    "UNIFIED_INTAKE_QA_FIXTURE_SURFACE",
    "P20_SLICE1_REQUEST_MORE",
)

DEPLOY_ENTRY_CLOUD_QA = "cloud_qa"
DEPLOY_ENTRY_PAID_PILOT = "paid_pilot"
DEPLOY_ENTRY_DEMO_SMOKE = "demo_smoke"


def _truthy(raw: str | None) -> bool:
    return (raw or "").strip().lower() in ("1", "true", "yes", "on")


def _load_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, _, val = s.partition("=")
        out[key.strip()] = val.strip().strip("'\"").strip()
    return out


def _db_name_from_url(url: str) -> str:
    u = urlparse((url or "").strip())
    return (u.path or "").lstrip("/").split("?")[0].strip()


def _is_cloud_qa_entry(deploy_entry: str) -> bool:
    return (deploy_entry or "").strip() == DEPLOY_ENTRY_CLOUD_QA


def _is_production_entry(deploy_entry: str) -> bool:
    return (deploy_entry or "").strip() in (
        DEPLOY_ENTRY_PAID_PILOT,
        DEPLOY_ENTRY_DEMO_SMOKE,
        "",
    )


def check_deploy_safety(
    *,
    deploy_entry: str,
    env_file: Path,
    env: dict[str, str] | None = None,
) -> list[str]:
    """
    Return a list of human-readable errors (empty => PASS).
    Fail closed: ambiguous or dangerous combinations produce errors.
    """
    errors: list[str] = []
    entry = (deploy_entry or "").strip()
    env_map = dict(env or {})
    basename = env_file.name if env_file else ""

    service = (env_map.get("SERVICE_NAME") or "").strip()
    # Match deploy_cloud_run_core.sh default when SERVICE_NAME unset on production path.
    if not service and not _is_cloud_qa_entry(entry):
        service = PROD_SERVICE_NAME
    db_secret = (env_map.get("CLOUD_RUN_SECRET_SERVICE_RECORD_DB") or "").strip()
    db_url = (env_map.get("SERVICE_RECORD_DATABASE_URL") or "").strip()
    db_name = _db_name_from_url(db_url) if db_url else ""

    # --- Env file ↔ entry alignment ---
    if _is_cloud_qa_entry(entry):
        if basename != QA_ENV_FILE_NAME:
            errors.append(
                f"Cloud QA deploy must load {QA_ENV_FILE_NAME}, got {basename or '(missing)'}"
            )
    elif entry == DEPLOY_ENTRY_PAID_PILOT:
        if basename != PROD_ENV_FILE_NAME:
            errors.append(
                f"Production paid-pilot deploy must load {PROD_ENV_FILE_NAME}, "
                f"got {basename or '(missing)'}"
            )
    elif entry == DEPLOY_ENTRY_DEMO_SMOKE:
        if basename == QA_ENV_FILE_NAME:
            errors.append(
                f"Demo smoke deploy must not load {QA_ENV_FILE_NAME} "
                f"(use {PROD_ENV_FILE_NAME} or a non-QA file)"
            )
    else:
        # Unknown / direct core invocation: still reject QA file unless entry is cloud_qa.
        if basename == QA_ENV_FILE_NAME:
            errors.append(
                f"{QA_ENV_FILE_NAME} requires DEPLOY_ENTRY={DEPLOY_ENTRY_CLOUD_QA} "
                f"(refusing to treat QA env as Production)"
            )

    # --- Cloud QA path ---
    if _is_cloud_qa_entry(entry) or basename == QA_ENV_FILE_NAME:
        if not service:
            errors.append(
                f"Cloud QA SERVICE_NAME missing — set SERVICE_NAME={QA_SERVICE_NAME}"
            )
        elif service == PROD_SERVICE_NAME:
            errors.append(
                f"QA env/deploy targeting Production service "
                f"SERVICE_NAME={PROD_SERVICE_NAME} is forbidden "
                f"(expected {QA_SERVICE_NAME})"
            )
        elif service != QA_SERVICE_NAME:
            errors.append(
                f"Cloud QA SERVICE_NAME={service!r}; expected {QA_SERVICE_NAME!r}"
            )

        use_sm = _truthy(env_map.get("CLOUD_RUN_USE_SECRET_MANAGER"))
        if use_sm and not db_secret:
            errors.append(
                f"Cloud QA with CLOUD_RUN_USE_SECRET_MANAGER=1 requires "
                f"CLOUD_RUN_SECRET_SERVICE_RECORD_DB={QA_DB_SECRET} "
                f"(refusing Production default)"
            )
        elif db_secret == PROD_DB_SECRET:
            errors.append(
                f"Cloud QA must not use Production DB secret {PROD_DB_SECRET} "
                f"(expected {QA_DB_SECRET})"
            )
        elif db_secret and db_secret != QA_DB_SECRET:
            errors.append(
                f"Cloud QA CLOUD_RUN_SECRET_SERVICE_RECORD_DB={db_secret!r}; "
                f"expected {QA_DB_SECRET!r}"
            )

        if db_name == PROD_DATABASE_NAME:
            errors.append(
                f"Cloud QA SERVICE_RECORD_DATABASE_URL targets Production database "
                f"{PROD_DATABASE_NAME!r} (expected {QA_DATABASE_NAME!r})"
            )
        elif db_name and db_name != QA_DATABASE_NAME:
            errors.append(
                f"Cloud QA database name={db_name!r}; expected {QA_DATABASE_NAME!r}"
            )

    # --- Production / paid-pilot / default production service ---
    targeting_prod_service = service == PROD_SERVICE_NAME
    production_like = (
        entry == DEPLOY_ENTRY_PAID_PILOT
        or (basename == PROD_ENV_FILE_NAME and not _is_cloud_qa_entry(entry))
        or (targeting_prod_service and not _is_cloud_qa_entry(entry))
    )

    if production_like:
        if service == QA_SERVICE_NAME:
            errors.append(
                f"Production deploy must not target Cloud QA service "
                f"SERVICE_NAME={QA_SERVICE_NAME}"
            )
        if db_secret == QA_DB_SECRET:
            errors.append(
                f"Production deploy must not use Cloud QA DB secret {QA_DB_SECRET}"
            )
        if db_name == QA_DATABASE_NAME:
            errors.append(
                f"Production deploy must not target Cloud QA database {QA_DATABASE_NAME!r}"
            )

        for flag in QA_HARNESS_FLAGS:
            if _truthy(env_map.get(flag)):
                errors.append(
                    f"QA Harness flag {flag}=ON is forbidden on Production "
                    f"(SERVICE_NAME={service or PROD_SERVICE_NAME}; "
                    f"move to {QA_ENV_FILE_NAME} / Cloud QA deploy)"
                )

    # --- Explicit: Production service + any harness ---
    if targeting_prod_service:
        for flag in QA_HARNESS_FLAGS:
            if _truthy(env_map.get(flag)):
                msg = (
                    f"Dangerous combination: SERVICE_NAME={PROD_SERVICE_NAME} "
                    f"with {flag}=ON"
                )
                if msg not in errors and not any(flag in e for e in errors):
                    errors.append(msg)

    return errors


def format_report(errors: list[str]) -> str:
    if not errors:
        return "RESULT: PASS — deploy safety checks ok"
    lines = [
        "RESULT: FAIL — refusing deploy (fail-closed)",
        "Fix these before any gcloud deploy:",
    ]
    for i, err in enumerate(errors, 1):
        lines.append(f"  {i}. {err}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P36 T3 fail-closed deploy safety check (no deploy)."
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        required=True,
        help="Env file the deploy script will load",
    )
    parser.add_argument(
        "--deploy-entry",
        default=os.environ.get("DEPLOY_ENTRY", ""),
        help="DEPLOY_ENTRY value (paid_pilot|cloud_qa|demo_smoke)",
    )
    args = parser.parse_args(argv)

    env_file = args.env_file
    if not env_file.is_file():
        print(
            f"=== P36 Deploy Safety Check ===\n"
            f"RESULT: FAIL — env file not found: {env_file}",
            file=sys.stderr,
        )
        return 1

    env_map = _load_dotenv(env_file)
    # Shell exports (entry posture) win over file for keys already set — match
    # deploy_cloud_run_core after source + _apply_deploy_entry_posture for flags
    # that operators might export. For harness flags, file OR environ truthy fails.
    for key in (
        "SERVICE_NAME",
        "CLOUD_RUN_SECRET_SERVICE_RECORD_DB",
        "SERVICE_RECORD_DATABASE_URL",
        *QA_HARNESS_FLAGS,
    ):
        if key in os.environ and os.environ.get(key) is not None:
            # Prefer process env when set (wrappers / operator exports).
            env_map[key] = os.environ[key]

    errors = check_deploy_safety(
        deploy_entry=args.deploy_entry,
        env_file=env_file,
        env=env_map,
    )
    print("=== P36 Deploy Safety Check ===")
    print(f"DEPLOY_ENTRY={args.deploy_entry or '(none)'}")
    print(f"ENV_FILE={env_file}")
    print(format_report(errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
