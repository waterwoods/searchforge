"""
Resolve QA Postgres URL for Chen Kui demo seed/reset/check scripts.

QA source of truth (P18.11): GCP Cloud SQL `caseiq` on instance `caseiq-pilot-pg`,
same secret as Cloud Run: fiqa-service-record-database-url-cloudsql-private.

Laptop seeding uses the instance PRIMARY public IP when the secret host is VPC-private
(authorized network must include operator IP — see gcloud sql instances describe).

Never log full connection strings.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse, urlunparse

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DB_URL_KEYS = frozenset({"SERVICE_RECORD_DATABASE_URL", "DATABASE_URL", "QA_SERVICE_RECORD_DATABASE_URL"})

QA_CLOUD_SQL_SECRET = "fiqa-service-record-database-url-cloudsql-private"
QA_CLOUD_SQL_INSTANCE = "caseiq-pilot-pg"
LEGACY_NEON_SECRET = "fiqa-service-record-database-url"  # DELETED — versions disabled; Neon project removed 2026-07-11
CLOUD_RUN_SERVICE = "fiqa-api"
CLOUD_RUN_REGION = "us-west1"

Target = Literal["local", "qa", "legacy-neon"]


def is_neon_database_url(url: str | None) -> bool:
    """True when URL hostname is legacy Neon (not Cloud SQL SSOT)."""
    if not url:
        return False
    host = (urlparse(url.strip()).hostname or "").lower()
    return "neon" in host


def strip_neon_database_urls_from_env() -> list[str]:
    """Remove legacy Neon DB URLs from process env; return stripped key names."""
    stripped: list[str] = []
    for key in _DB_URL_KEYS:
        raw = (os.environ.get(key) or "").strip()
        if raw and is_neon_database_url(raw):
            os.environ.pop(key, None)
            stripped.append(key)
    return stripped


@dataclass(frozen=True)
class DbIdentity:
    provider: str
    host: str
    database: str
    secret_name: str | None
    connection_mode: str

    def masked(self) -> str:
        return f"provider={self.provider} host={self.host} db={self.database} mode={self.connection_mode}"


def _gcloud_secret(secret: str) -> str:
    return subprocess.check_output(
        ["gcloud", "secrets", "versions", "access", "latest", f"--secret={secret}"],
        text=True,
    ).strip()


def _cloud_sql_public_ip() -> str:
    import json

    raw = subprocess.check_output(
        [
            "gcloud",
            "sql",
            "instances",
            "describe",
            QA_CLOUD_SQL_INSTANCE,
            "--format=json(ipAddresses)",
        ],
        text=True,
    )
    for item in json.loads(raw).get("ipAddresses", []):
        if item.get("type") == "PRIMARY":
            return str(item["ipAddress"])
    raise RuntimeError(f"no PRIMARY public IP on {QA_CLOUD_SQL_INSTANCE}")


def _rewrite_host(url: str, new_host: str) -> str:
    u = urlparse(url)
    if not u.netloc:
        return url
    if "@" in u.netloc:
        auth, _hostpart = u.netloc.rsplit("@", 1)
        port = ""
        if ":" in _hostpart and not _hostpart.startswith("/cloudsql"):
            _, port = _hostpart.split(":", 1)
            netloc = f"{auth}@{new_host}:{port}" if port else f"{auth}@{new_host}"
        else:
            netloc = f"{auth}@{new_host}"
    else:
        netloc = new_host
    return urlunparse((u.scheme, netloc, u.path, u.params, u.query, u.fragment))


def resolve_db_identity(target: Target, *, for_write: bool = True) -> DbIdentity:
    if target == "local":
        return DbIdentity("local-json", "n/a", "unified_intake_cases.json", None, "json-file")

    if target == "legacy-neon":
        raw = os.environ.get("SERVICE_RECORD_DATABASE_URL") or _gcloud_secret(LEGACY_NEON_SECRET)
        u = urlparse(raw)
        host = u.hostname or "unknown"
        db = (u.path or "").lstrip("/").split("?")[0] or "unknown"
        return DbIdentity("neon-legacy", host, db, LEGACY_NEON_SECRET, "direct")

    # QA = Cloud SQL (Cloud Run truth)
    raw = os.environ.get("QA_SERVICE_RECORD_DATABASE_URL") or _gcloud_secret(QA_CLOUD_SQL_SECRET)
    u = urlparse(raw)
    host = u.hostname or ""
    db = (u.path or "").lstrip("/").split("?")[0] or "caseiq"
    mode = "private-vpc"
    if host.startswith("10.") or host.startswith("172.") or host.startswith("192.168."):
        if for_write and os.environ.get("QA_SEED_SKIP_PUBLIC_IP") != "1":
            public = _cloud_sql_public_ip()
            raw = _rewrite_host(raw, public)
            host = public
            mode = "public-ip-authorized"
    return DbIdentity("gcp-cloud-sql", host, db, QA_CLOUD_SQL_SECRET, mode)


def apply_qa_postgres_env(*, for_write: bool = True) -> DbIdentity:
    """Set process env for Postgres-primary reads/writes against QA Cloud SQL."""
    # P25R — Cloud Run already has SERVICE_RECORD_DATABASE_URL (Unix socket / VPC).
    # Do not call gcloud inside the container (binary absent).
    existing = (os.environ.get("SERVICE_RECORD_DATABASE_URL") or "").strip()
    if existing and (
        (os.environ.get("K_SERVICE") or "").strip()
        or os.environ.get("QA_SEED_USE_EXISTING_DB_URL") == "1"
    ):
        u = urlparse(existing)
        host = u.hostname or "cloudsql"
        db = (u.path or "").lstrip("/").split("?")[0] or "caseiq"
        os.environ["UNIFIED_INTAKE_DB_PRIMARY_READS"] = "1"
        os.environ["UNIFIED_INTAKE_DB_PRIMARY_WRITES"] = "1"
        os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "0"
        os.environ.pop("UNIFIED_INTAKE_JSON_READ_FALLBACK", None)
        return DbIdentity("gcp-cloud-sql", host, db, None, "cloud-run-existing-url")

    ident = resolve_db_identity("qa", for_write=for_write)
    if ident.provider == "local-json":
        raise ValueError("apply_qa_postgres_env called with local target")
    raw = os.environ.get("QA_SERVICE_RECORD_DATABASE_URL") or _gcloud_secret(QA_CLOUD_SQL_SECRET)
    host = urlparse(raw).hostname or ""
    if host.startswith("10.") and for_write and os.environ.get("QA_SEED_SKIP_PUBLIC_IP") != "1":
        raw = _rewrite_host(raw, _cloud_sql_public_ip())
    os.environ["SERVICE_RECORD_DATABASE_URL"] = raw
    os.environ["UNIFIED_INTAKE_DB_PRIMARY_READS"] = "1"
    os.environ["UNIFIED_INTAKE_DB_PRIMARY_WRITES"] = "1"
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "0"
    os.environ.pop("UNIFIED_INTAKE_JSON_READ_FALLBACK", None)
    return ident


def ensure_h5_task_token_secret() -> bool:
    """Load H5_TASK_TOKEN_SECRET from Secret Manager when unset (matches Cloud Run)."""
    if (os.getenv("H5_TASK_TOKEN_SECRET") or "").strip():
        return True
    project = (os.getenv("PROJECT_ID") or "optimal-disk-472305-e2").strip()
    secret_name = (os.getenv("CLOUD_RUN_SECRET_H5_TASK_TOKEN") or "fiqa-h5-task-token-secret").strip()
    try:
        proc = subprocess.run(
            [
                "gcloud",
                "secrets",
                "versions",
                "access",
                "latest",
                f"--secret={secret_name}",
                f"--project={project}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            os.environ["H5_TASK_TOKEN_SECRET"] = proc.stdout.strip()
            return True
    except Exception:
        pass
    return False


def load_cloudrun_env_skip_db(*, override: bool = False) -> None:
    """Load .env.cloudrun API/runtime keys but never legacy Neon DATABASE_URL."""
    env_file = _REPO_ROOT / ".env.cloudrun"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, _, val = s.partition("=")
        key = key.strip()
        if key in _DB_URL_KEYS:
            continue
        val = val.strip().strip("'\"").strip()
        if override:
            os.environ[key] = val
        else:
            os.environ.setdefault(key, val)


def bootstrap_prototype_cloud_sql_env() -> DbIdentity:
    """Mini-program prototype QA: Cloud SQL SSOT + Cloud Run-aligned runtime flags."""
    load_cloudrun_env_skip_db(override=True)
    strip_neon_database_urls_from_env()
    ident = apply_qa_postgres_env(for_write=True)
    os.environ["ENV"] = "prod"
    ensure_h5_task_token_secret()
    return ident


def apply_legacy_neon_readonly_env() -> DbIdentity:
    """
    Break-glass read-only access to legacy Neon — never for QA/demo/production defaults.

    Requires explicit operator intent (CLI flag). Performs no writes.
    """
    import sys

    print(
        "[WARN] BREAK-GLASS: legacy Neon READ-ONLY — not QA/demo/production SSOT",
        file=sys.stderr,
    )
    os.environ.pop("QA_SERVICE_RECORD_DATABASE_URL", None)
    raw = os.environ.get("SERVICE_RECORD_DATABASE_URL") or _gcloud_secret(LEGACY_NEON_SECRET)
    if not is_neon_database_url(raw):
        raise RuntimeError("legacy-neon-readonly resolved to non-Neon host — aborting")
    os.environ["SERVICE_RECORD_DATABASE_URL"] = raw
    os.environ["LEGACY_NEON_READONLY"] = "1"
    os.environ["UNIFIED_INTAKE_DB_PRIMARY_READS"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "0"
    os.environ.pop("UNIFIED_INTAKE_JSON_READ_FALLBACK", None)
    return resolve_db_identity("legacy-neon", for_write=False)


def shell_export_qa_postgres_env(*, for_write: bool = True) -> tuple[DbIdentity, list[str]]:
    """Apply QA Postgres env; return bash export lines (values quoted, never logged)."""
    ident = apply_qa_postgres_env(for_write=for_write)
    keys = (
        "SERVICE_RECORD_DATABASE_URL",
        "UNIFIED_INTAKE_DB_PRIMARY_READS",
        "UNIFIED_INTAKE_DB_PRIMARY_WRITES",
        "UNIFIED_INTAKE_JSON_CASE_WRITES",
        "UNIFIED_INTAKE_JSON_READ_FALLBACK",
    )
    lines = [f"export {k}={shlex.quote(os.environ[k])}" for k in keys if os.environ.get(k)]
    return ident, lines


def cloud_run_revision() -> str:
    try:
        return subprocess.check_output(
            [
                "gcloud",
                "run",
                "services",
                "describe",
                CLOUD_RUN_SERVICE,
                f"--region={CLOUD_RUN_REGION}",
                "--format=value(status.latestReadyRevisionName)",
            ],
            text=True,
        ).strip()
    except Exception:
        return "unknown"
