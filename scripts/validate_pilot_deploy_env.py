#!/usr/bin/env python3
"""
Validate .env.cloudrun (or current env) against survivable pilot defaults.

Exit 0 when posture matches minimum paid-pilot tuple; exit 1 with actionable errors.
Does not print secret values.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.fiqa_api.deployment_profile import pilot_safe_default_profile_v1  # noqa: E402


def _truthy(raw: str | None) -> bool:
    return (raw or "").strip().lower() in ("1", "true", "yes", "on")


def _falsy(raw: str | None) -> bool:
    return (raw or "").strip().lower() in ("0", "false", "no", "off")


def _load_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        key, _, val = s.partition("=")
        out[key.strip()] = val.strip()
    return out


def _env_snapshot(source: dict[str, str]) -> dict[str, str]:
    """Merge file/env into os.environ-like dict for checks (file wins)."""
    merged = dict(os.environ)
    merged.update(source)
    return merged


def validate_pilot_env(env: dict[str, str]) -> list[str]:
    errors: list[str] = []

    def get(key: str) -> str:
        return (env.get(key) or "").strip()

    if not _truthy(get("UNIFIED_INTAKE_PRODUCT_ONLY")):
        errors.append("UNIFIED_INTAKE_PRODUCT_ONLY must be 1 (product-only API surface)")

    has_db = bool(get("SERVICE_RECORD_DATABASE_URL") or get("DATABASE_URL"))
    if not has_db and not _truthy(get("CLOUD_RUN_USE_SECRET_MANAGER")):
        errors.append(
            "SERVICE_RECORD_DATABASE_URL or DATABASE_URL required "
            "(or CLOUD_RUN_USE_SECRET_MANAGER=1 with fiqa-service-record-database-url secret)"
        )

    if not _truthy(get("UNIFIED_INTAKE_DB_PRIMARY_WRITES")):
        errors.append("UNIFIED_INTAKE_DB_PRIMARY_WRITES must be 1")

    if not _truthy(get("UNIFIED_INTAKE_DB_PRIMARY_READS")):
        errors.append("UNIFIED_INTAKE_DB_PRIMARY_READS must be 1")

    if not _falsy(get("UNIFIED_INTAKE_JSON_CASE_WRITES")):
        errors.append("UNIFIED_INTAKE_JSON_CASE_WRITES must be 0 (JSON case path is dev-only)")

    if not _falsy(get("UNIFIED_INTAKE_JSON_READ_FALLBACK")):
        errors.append("UNIFIED_INTAKE_JSON_READ_FALLBACK must be 0 (no silent JSON authority in prod-like pilot)")

    if not _falsy(get("UNIFIED_INTAKE_PG_DUAL_WRITE")):
        errors.append("UNIFIED_INTAKE_PG_DUAL_WRITE must be 0 (single write path required)")

    if has_db and _truthy(get("UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS")):
        errors.append(
            "UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS must be off when SERVICE_RECORD_DATABASE_URL is set"
        )

    if not get("UNIFIED_INTAKE_INTAKE_API_KEY"):
        errors.append("UNIFIED_INTAKE_INTAKE_API_KEY must be set (24+ char random)")

    if not get("UNIFIED_INTAKE_SUPPORT_API_KEY"):
        errors.append("UNIFIED_INTAKE_SUPPORT_API_KEY must be set (24+ char random)")

    # Optional but recommended
    if get("UNIFIED_INTAKE_INTAKE_API_KEY") and get("UNIFIED_INTAKE_SUPPORT_API_KEY"):
        if get("UNIFIED_INTAKE_INTAKE_API_KEY") == get("UNIFIED_INTAKE_SUPPORT_API_KEY"):
            errors.append("UNIFIED_INTAKE_INTAKE_API_KEY must differ from UNIFIED_INTAKE_SUPPORT_API_KEY")

    env_label = get("ENV").lower()
    paid_pilot_signals = (
        env_label == "prod"
        or _truthy(get("UNIFIED_INTAKE_PRODUCT_ONLY"))
        or _truthy(get("UNIFIED_INTAKE_DB_PRIMARY_WRITES"))
        or _truthy(get("PILOT_DEPLOY_STRICT"))
    )
    if paid_pilot_signals and _truthy(get("DEMO_MODE")):
        errors.append(
            "DEMO_MODE must be off or unset for paid-pilot deploy (contradicts prod-like posture)"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pilot deploy env posture")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=_REPO_ROOT / ".env.cloudrun",
        help="Dotenv file to validate (default: .env.cloudrun)",
    )
    parser.add_argument(
        "--skip-missing-file",
        action="store_true",
        help="Exit 0 when env file does not exist (local trial readiness)",
    )
    parser.add_argument(
        "--show-profile",
        action="store_true",
        help="Print pilot_safe_default_profile_v1 and exit",
    )
    args = parser.parse_args()

    if args.show_profile:
        for k, v in pilot_safe_default_profile_v1().items():
            print(f"{k}={v}")
        return 0

    if args.env_file.exists():
        file_env = _load_dotenv(args.env_file)
        env = _env_snapshot(file_env)
        label = str(args.env_file)
    elif args.skip_missing_file:
        print(f"SKIP pilot deploy env validation ({args.env_file} not found)")
        return 0
    else:
        env = _env_snapshot({})
        label = "process environment"

    errors = validate_pilot_env(env)
    if errors:
        print(f"FAIL pilot deploy env ({label}):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Reference tuple (--show-profile):", file=sys.stderr)
        for k, v in pilot_safe_default_profile_v1().items():
            print(f"  {k}={v}", file=sys.stderr)
        return 1

    print(f"OK pilot deploy env ({label})")
    if _truthy(env.get("UNIFIED_INTAKE_PRODUCT_ONLY")):
        print("  product_only=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
