#!/usr/bin/env python3
"""
P36 T2 — Cloud QA isolation verifier (fail-closed).

Proves Cloud QA cannot accidentally use Production mutable case data.
If isolation cannot be proven, exit non-zero. Never assume.

Canonical names: docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md

Never prints connection passwords or full secret values.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Frozen names (P36 T1 SSOT) — do not improvise
# ---------------------------------------------------------------------------
PROD_SERVICE_NAME = "fiqa-api"
QA_SERVICE_NAME = "fiqa-api-qa"
PROD_DATABASE_NAME = "caseiq"
QA_DATABASE_NAME = "caseiq-qa"
PROD_DB_SECRET = "fiqa-service-record-database-url-cloudsql-private"
QA_DB_SECRET = "fiqa-service-record-database-url-qa"
PROD_ENV_FILE_NAME = ".env.cloudrun"
QA_ENV_FILE_NAME = ".env.cloudrun.qa"
DEFAULT_PROJECT_ID = "optimal-disk-472305-e2"
CLOUD_SQL_INSTANCE = "caseiq-pilot-pg"

SecretAccessor = Callable[[str, str], str]


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class ResolvedTarget:
    host: str
    database: str
    source: str  # env-url | secret-manager
    secret_name: str | None

    def fingerprint(self) -> str:
        """Host + database only — never credentials."""
        return f"host={self.host or '?'} db={self.database or '?'}"


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


def _parse_db_url(url: str) -> tuple[str, str]:
    u = urlparse((url or "").strip())
    host = (u.hostname or "").strip()
    database = (u.path or "").lstrip("/").split("?")[0].strip()
    return host, database


def default_secret_accessor(secret_name: str, project_id: str) -> str:
    """Read latest Secret Manager payload via gcloud. Raises on failure."""
    proc = subprocess.run(
        [
            "gcloud",
            "secrets",
            "versions",
            "access",
            "latest",
            f"--secret={secret_name}",
            f"--project={project_id}",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip().splitlines()
        hint = err[-1] if err else f"exit {proc.returncode}"
        raise RuntimeError(f"cannot access secret {secret_name!r}: {hint}")
    value = (proc.stdout or "").strip()
    if not value:
        raise RuntimeError(f"secret {secret_name!r} is empty")
    return value


def resolve_db_target(
    env: dict[str, str],
    *,
    role: str,
    default_secret: str,
    project_id: str,
    secret_accessor: SecretAccessor | None,
    allow_secret_access: bool,
) -> ResolvedTarget:
    """
    Resolve host/database for role.

    Prefer plaintext URL in env file; else Secret Manager (when allowed).
    Fail closed via exceptions — callers convert to CheckResult.
    """
    url = (
        (env.get("SERVICE_RECORD_DATABASE_URL") or "").strip()
        or (env.get("DATABASE_URL") or "").strip()
        or (env.get("QA_SERVICE_RECORD_DATABASE_URL") or "").strip()
    )
    if url:
        host, database = _parse_db_url(url)
        if not database:
            raise RuntimeError(f"{role}: database URL has empty database name")
        return ResolvedTarget(host=host, database=database, source="env-url", secret_name=None)

    secret_name = (env.get("CLOUD_RUN_SECRET_SERVICE_RECORD_DB") or "").strip() or default_secret
    if role == "Cloud QA" and secret_name != QA_DB_SECRET:
        raise RuntimeError(
            f"{role}: refusing to resolve via non-QA secret {secret_name!r} "
            f"(expected {QA_DB_SECRET!r})"
        )
    if role == "Production" and secret_name == QA_DB_SECRET:
        raise RuntimeError(
            f"{role}: refusing to resolve via QA secret {secret_name!r} "
            f"(expected {PROD_DB_SECRET!r})"
        )
    if not allow_secret_access:
        raise RuntimeError(
            f"{role}: no SERVICE_RECORD_DATABASE_URL in env and secret access disabled "
            f"(would need secret {secret_name!r})"
        )
    if secret_accessor is None:
        raise RuntimeError(f"{role}: no secret accessor configured for {secret_name!r}")

    raw = secret_accessor(secret_name, project_id)
    host, database = _parse_db_url(raw)
    if not database:
        raise RuntimeError(f"{role}: secret {secret_name!r} URL has empty database name")
    return ResolvedTarget(
        host=host, database=database, source="secret-manager", secret_name=secret_name
    )


def verify_isolation(
    *,
    qa_env: dict[str, str],
    prod_env: dict[str, str],
    qa_env_path: Path | None,
    prod_env_path: Path | None,
    project_id: str,
    secret_accessor: SecretAccessor | None = None,
    allow_secret_access: bool = True,
) -> list[CheckResult]:
    """Run all isolation checks. Returns results; does not exit."""
    checks: list[CheckResult] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name=name, ok=ok, detail=detail))

    # --- Declared service names (QA must be explicit — no silent default PASS) ---
    qa_service = (qa_env.get("SERVICE_NAME") or "").strip()
    prod_service = (prod_env.get("SERVICE_NAME") or "").strip() or PROD_SERVICE_NAME

    add(
        "QA Cloud Run service name is declared",
        bool(qa_service),
        (
            f"SERVICE_NAME={qa_service!r}"
            if qa_service
            else "SERVICE_NAME missing in QA env — set SERVICE_NAME=fiqa-api-qa"
        ),
    )
    add(
        "QA Cloud Run service name matches frozen QA name",
        qa_service == QA_SERVICE_NAME,
        f"QA SERVICE_NAME={qa_service!r}; expected {QA_SERVICE_NAME!r}",
    )
    add(
        "QA Cloud Run service name != Production service name",
        bool(qa_service)
        and qa_service != prod_service
        and qa_service != PROD_SERVICE_NAME,
        f"QA={qa_service!r} Production={prod_service!r} (frozen Production={PROD_SERVICE_NAME!r})",
    )

    # --- Declared DB secret names (QA must be explicit) ---
    qa_secret = (qa_env.get("CLOUD_RUN_SECRET_SERVICE_RECORD_DB") or "").strip()
    prod_secret = (
        (prod_env.get("CLOUD_RUN_SECRET_SERVICE_RECORD_DB") or "").strip() or PROD_DB_SECRET
    )

    add(
        "QA DB secret name is declared",
        bool(qa_secret),
        (
            f"CLOUD_RUN_SECRET_SERVICE_RECORD_DB={qa_secret!r}"
            if qa_secret
            else (
                "CLOUD_RUN_SECRET_SERVICE_RECORD_DB missing — set "
                f"CLOUD_RUN_SECRET_SERVICE_RECORD_DB={QA_DB_SECRET}"
            )
        ),
    )
    add(
        "QA DB secret name matches frozen QA secret",
        qa_secret == QA_DB_SECRET,
        f"QA CLOUD_RUN_SECRET_SERVICE_RECORD_DB={qa_secret!r}; expected {QA_DB_SECRET!r}",
    )
    add(
        "QA DB secret name != Production DB secret name",
        bool(qa_secret) and qa_secret != prod_secret and qa_secret != PROD_DB_SECRET,
        f"QA={qa_secret!r} Production={prod_secret!r} (frozen Production={PROD_DB_SECRET!r})",
    )
    add(
        "QA does not use Production DB secret name",
        bool(qa_secret) and qa_secret != PROD_DB_SECRET,
        f"QA secret must not be {PROD_DB_SECRET!r}",
    )

    # --- Resolve connection targets ---
    qa_target: ResolvedTarget | None = None
    prod_target: ResolvedTarget | None = None

    try:
        qa_target = resolve_db_target(
            qa_env,
            role="Cloud QA",
            default_secret=QA_DB_SECRET,
            project_id=project_id,
            secret_accessor=secret_accessor,
            allow_secret_access=allow_secret_access,
        )
        add(
            "QA database connection target resolved",
            True,
            f"{qa_target.fingerprint()} source={qa_target.source}"
            + (f" secret={qa_target.secret_name}" if qa_target.secret_name else ""),
        )
    except Exception as exc:
        add(
            "QA database connection target resolved",
            False,
            f"FAIL CLOSED — cannot prove QA isolation: {exc}",
        )

    try:
        prod_target = resolve_db_target(
            prod_env,
            role="Production",
            default_secret=PROD_DB_SECRET,
            project_id=project_id,
            secret_accessor=secret_accessor,
            allow_secret_access=allow_secret_access,
        )
        add(
            "Production database connection target resolved",
            True,
            f"{prod_target.fingerprint()} source={prod_target.source}"
            + (f" secret={prod_target.secret_name}" if prod_target.secret_name else ""),
        )
    except Exception as exc:
        # Still fail closed: without Production target we cannot prove inequality.
        add(
            "Production database connection target resolved",
            False,
            f"FAIL CLOSED — cannot compare against Production: {exc}",
        )

    if qa_target is not None:
        add(
            "QA database name matches frozen QA database",
            qa_target.database == QA_DATABASE_NAME,
            f"resolved db={qa_target.database!r}; expected {QA_DATABASE_NAME!r}",
        )
        add(
            "QA database name is not Production database (caseiq)",
            qa_target.database != PROD_DATABASE_NAME,
            f"resolved db={qa_target.database!r}; Production db={PROD_DATABASE_NAME!r}",
        )
        add(
            "QA resolved target matches expected QA configuration",
            qa_target.database == QA_DATABASE_NAME,
            (
                f"expected database={QA_DATABASE_NAME!r} on instance {CLOUD_SQL_INSTANCE!r}; "
                f"got {qa_target.fingerprint()}"
            ),
        )

    if qa_target is not None and prod_target is not None:
        same_db = qa_target.database == prod_target.database
        same_host_and_db = (
            qa_target.host
            and prod_target.host
            and qa_target.host == prod_target.host
            and same_db
        )
        add(
            "QA database name != Production database name",
            qa_target.database != prod_target.database,
            f"QA db={qa_target.database!r} Production db={prod_target.database!r}",
        )
        add(
            "QA connection fingerprint != Production connection fingerprint",
            not same_host_and_db,
            f"QA[{qa_target.fingerprint()}] Production[{prod_target.fingerprint()}]",
        )

    # Env file hygiene (informational failures when paths supplied)
    if qa_env_path is not None and not qa_env_path.is_file():
        add(
            "QA env file exists",
            False,
            f"missing {qa_env_path} — copy configs/cloud_qa.env.example to {QA_ENV_FILE_NAME}",
        )
    elif qa_env_path is not None:
        add("QA env file exists", True, str(qa_env_path))

    if prod_env_path is not None and prod_env_path.is_file():
        add("Production env file present (optional)", True, str(prod_env_path))
    elif prod_env_path is not None:
        add(
            "Production env file present (optional)",
            True,
            f"{prod_env_path} absent — using frozen Production names / secret defaults",
        )

    return checks


def format_report(checks: list[CheckResult]) -> str:
    lines = [
        "=== P36 Cloud QA Isolation Verifier ===",
        "SSOT: docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md",
        "",
    ]
    for c in checks:
        mark = "PASS" if c.ok else "FAIL"
        lines.append(f"[{mark}] {c.name}")
        lines.append(f"       {c.detail}")
        if not c.ok:
            lines.append("       WHY: Cloud QA must never share Production mutable case data.")
    failed = [c for c in checks if not c.ok]
    lines.append("")
    if failed:
        lines.append(f"RESULT: FAIL ({len(failed)} check(s) failed) — exit 1")
        lines.append("Do not deploy Cloud QA until every check PASSes.")
    else:
        lines.append("RESULT: PASS — Cloud QA isolation proven for checked dimensions.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed verifier: Cloud QA must not use Production mutable data."
    )
    parser.add_argument(
        "--qa-env",
        type=Path,
        default=_REPO_ROOT / QA_ENV_FILE_NAME,
        help=f"Cloud QA env file (default: {_REPO_ROOT / QA_ENV_FILE_NAME})",
    )
    parser.add_argument(
        "--prod-env",
        type=Path,
        default=_REPO_ROOT / PROD_ENV_FILE_NAME,
        help=f"Production env file (default: {_REPO_ROOT / PROD_ENV_FILE_NAME})",
    )
    parser.add_argument(
        "--project",
        default=os.environ.get("PROJECT_ID") or DEFAULT_PROJECT_ID,
        help=f"GCP project for Secret Manager access (default: {DEFAULT_PROJECT_ID})",
    )
    parser.add_argument(
        "--no-secret-access",
        action="store_true",
        help="Do not call gcloud; require SERVICE_RECORD_DATABASE_URL in env files (still fail-closed).",
    )
    args = parser.parse_args(argv)

    qa_path: Path = args.qa_env
    prod_path: Path = args.prod_env

    if not qa_path.is_file():
        print("=== P36 Cloud QA Isolation Verifier ===", file=sys.stderr)
        print(f"[FAIL] QA env file missing: {qa_path}", file=sys.stderr)
        print(
            f"       Copy configs/cloud_qa.env.example → {QA_ENV_FILE_NAME}, "
            "fill values, then re-run.",
            file=sys.stderr,
        )
        print(
            "       WHY: Without a QA env file, isolation cannot be proven.",
            file=sys.stderr,
        )
        print("RESULT: FAIL — exit 1", file=sys.stderr)
        return 1

    qa_env = _load_dotenv(qa_path)
    prod_env = _load_dotenv(prod_path) if prod_path.is_file() else {}

    # Env file may override project
    project_id = (
        (qa_env.get("PROJECT_ID") or "").strip()
        or (prod_env.get("PROJECT_ID") or "").strip()
        or args.project
    )

    allow_secret = not args.no_secret_access
    accessor: SecretAccessor | None = default_secret_accessor if allow_secret else None

    checks = verify_isolation(
        qa_env=qa_env,
        prod_env=prod_env,
        qa_env_path=qa_path,
        prod_env_path=prod_path,
        project_id=project_id,
        secret_accessor=accessor,
        allow_secret_access=allow_secret,
    )
    report = format_report(checks)
    sys.stdout.write(report)
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
