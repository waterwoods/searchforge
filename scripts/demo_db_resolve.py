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
import re
import subprocess
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse, urlunparse

QA_CLOUD_SQL_SECRET = "fiqa-service-record-database-url-cloudsql-private"
QA_CLOUD_SQL_INSTANCE = "caseiq-pilot-pg"
LEGACY_NEON_SECRET = "fiqa-service-record-database-url"
CLOUD_RUN_SERVICE = "fiqa-api"
CLOUD_RUN_REGION = "us-west1"

Target = Literal["local", "qa", "legacy-neon"]


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
