"""Env helpers for DB-primary writes + JSON case write gating."""

from __future__ import annotations

import pytest

from services.fiqa_api.db import service_record_settings as s


def test_db_primary_writes_requires_url(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    assert s.db_primary_writes_enabled() is False


def test_db_primary_writes_truthy(monkeypatch):
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    assert s.db_primary_writes_enabled() is True


def test_db_primary_reads_auto_on_when_json_case_writes_off(monkeypatch):
    """Strict pilot: reads must follow Postgres when JSON file is not written."""
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "0")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)
    assert s.db_primary_reads_enabled() is True


def test_db_primary_reads_not_auto_when_json_still_written(monkeypatch):
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_JSON_CASE_WRITES", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_PG_DUAL_WRITE", raising=False)
    assert s.db_primary_reads_enabled() is False


def test_db_primary_reads_auto_on_when_pg_dual_write(monkeypatch):
    """Neon mirror path: same creates/appends hit PG — reads must follow for multi-instance."""
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("UNIFIED_INTAKE_PG_DUAL_WRITE", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    assert s.db_primary_reads_enabled() is True


def test_db_primary_reads_explicit_off_disables_even_with_dual_write(monkeypatch):
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("UNIFIED_INTAKE_PG_DUAL_WRITE", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_READS", "0")
    assert s.db_primary_reads_enabled() is False


def test_json_case_writes_default_on(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_JSON_CASE_WRITES", raising=False)
    assert s.json_case_writes_enabled() is True


def test_json_case_writes_explicit_off(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "0")
    assert s.json_case_writes_enabled() is False


@pytest.mark.parametrize("val", ("false", "no", "off"))
def test_json_case_writes_falsy(val, monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", val)
    assert s.json_case_writes_enabled() is False


def test_json_session_writes_default_on(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_JSON_SESSION_WRITES", raising=False)
    assert s.json_session_writes_enabled() is True


def test_json_session_writes_explicit_off(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_SESSION_WRITES", "0")
    assert s.json_session_writes_enabled() is False


def test_postgres_case_persistence_primary(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "0")
    assert s.postgres_case_persistence_primary() is False

    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "0")
    assert s.postgres_case_persistence_primary() is True
