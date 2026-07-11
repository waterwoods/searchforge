"""DB resolution guardrails — Cloud SQL SSOT, legacy Neon isolation."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from scripts.demo_db_resolve import (
    apply_legacy_neon_readonly_env,
    bootstrap_prototype_cloud_sql_env,
    is_neon_database_url,
    load_cloudrun_env_skip_db,
    strip_neon_database_urls_from_env,
)


NEON_URL = "postgresql://user:pass@ep-test.c-3.us-west-2.aws.neon.tech/neondb"
CLOUD_URL = "postgresql://user:pass@10.1.2.3/caseiq"


def test_is_neon_database_url():
    assert is_neon_database_url(NEON_URL) is True
    assert is_neon_database_url(CLOUD_URL) is False
    assert is_neon_database_url("") is False


def test_strip_neon_database_urls_from_env(monkeypatch):
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", NEON_URL)
    monkeypatch.setenv("DATABASE_URL", CLOUD_URL)
    stripped = strip_neon_database_urls_from_env()
    assert stripped == ["SERVICE_RECORD_DATABASE_URL"]
    assert os.environ.get("SERVICE_RECORD_DATABASE_URL") is None
    assert os.environ.get("DATABASE_URL") == CLOUD_URL


def test_load_cloudrun_env_skip_db_skips_db_keys(tmp_path, monkeypatch):
    env_file = tmp_path / ".env.cloudrun"
    env_file.write_text(
        "TRANSLATION_ENABLED=1\nSERVICE_RECORD_DATABASE_URL=" + NEON_URL + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("TRANSLATION_ENABLED", raising=False)
    load_cloudrun_env_skip_db(override=True)
    assert os.environ.get("TRANSLATION_ENABLED") == "1"
    assert os.environ.get("SERVICE_RECORD_DATABASE_URL") is None


def test_bootstrap_prototype_cloud_sql_env_uses_cloud_sql(tmp_path, monkeypatch):
    env_file = tmp_path / ".env.cloudrun"
    env_file.write_text("SERVICE_RECORD_DATABASE_URL=" + NEON_URL + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)

    with patch("scripts.demo_db_resolve.apply_qa_postgres_env") as mock_apply:
        mock_apply.return_value = type(
            "Ident",
            (),
            {"masked": lambda self: "provider=gcp-cloud-sql host=10.0.0.1 db=caseiq mode=public-ip-authorized"},
        )()
        ident = bootstrap_prototype_cloud_sql_env()
        mock_apply.assert_called_once_with(for_write=True)
        assert "gcp-cloud-sql" in ident.masked()


def test_apply_legacy_neon_readonly_env_sets_flag(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    with patch("scripts.demo_db_resolve._gcloud_secret", return_value=NEON_URL):
        ident = apply_legacy_neon_readonly_env()
    assert os.environ.get("LEGACY_NEON_READONLY") == "1"
    assert os.environ.get("UNIFIED_INTAKE_DB_PRIMARY_WRITES") is None
    assert os.environ.get("SERVICE_RECORD_DATABASE_URL") == NEON_URL
    assert ident.provider == "neon-legacy"


def test_apply_legacy_neon_readonly_rejects_non_neon(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    with patch("scripts.demo_db_resolve._gcloud_secret", return_value=CLOUD_URL):
        with pytest.raises(RuntimeError, match="non-Neon"):
            apply_legacy_neon_readonly_env()


def test_seed_legacy_neon_target_disabled():
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "scripts/seed_chen_kui_demo.py", "--target", "legacy-neon", "--dry-run"],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        env={**os.environ, "PYTHONPATH": "."},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "legacy-neon writes are disabled" in proc.stderr
