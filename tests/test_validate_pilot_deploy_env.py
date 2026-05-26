"""Pilot deploy env validation script."""

from pathlib import Path

from scripts.validate_pilot_deploy_env import validate_pilot_env, _load_dotenv, _truthy, _falsy


def _minimal_pilot_env(**overrides):
    base = {
        "UNIFIED_INTAKE_PRODUCT_ONLY": "1",
        "SERVICE_RECORD_DATABASE_URL": "postgresql://u:p@h/db",
        "UNIFIED_INTAKE_DB_PRIMARY_WRITES": "1",
        "UNIFIED_INTAKE_DB_PRIMARY_READS": "1",
        "UNIFIED_INTAKE_JSON_CASE_WRITES": "0",
        "UNIFIED_INTAKE_JSON_READ_FALLBACK": "0",
        "UNIFIED_INTAKE_PG_DUAL_WRITE": "0",
        "UNIFIED_INTAKE_INTAKE_API_KEY": "intake-secret-minimum-length-ok-12345",
        "UNIFIED_INTAKE_SUPPORT_API_KEY": "support-secret-minimum-length-ok-1234",
    }
    base.update(overrides)
    return base


def test_validate_pilot_env_passes_minimal_tuple():
    assert validate_pilot_env(_minimal_pilot_env()) == []


def test_validate_pilot_env_fails_json_read_fallback_enabled():
    errs = validate_pilot_env(_minimal_pilot_env(UNIFIED_INTAKE_JSON_READ_FALLBACK="1"))
    assert any("UNIFIED_INTAKE_JSON_READ_FALLBACK" in e for e in errs)


def test_validate_pilot_env_fails_missing_db_primary_reads():
    errs = validate_pilot_env(_minimal_pilot_env(UNIFIED_INTAKE_DB_PRIMARY_READS="0"))
    assert any("UNIFIED_INTAKE_DB_PRIMARY_READS" in e for e in errs)


def test_validate_pilot_env_fails_missing_product_only():
    env = _minimal_pilot_env(UNIFIED_INTAKE_PRODUCT_ONLY="0")
    del env["UNIFIED_INTAKE_PRODUCT_ONLY"]
    errs = validate_pilot_env(env)
    assert any("UNIFIED_INTAKE_PRODUCT_ONLY" in e for e in errs)


def test_validate_pilot_env_fails_prod_demo_mode():
    errs = validate_pilot_env(_minimal_pilot_env(ENV="prod", DEMO_MODE="true"))
    assert any("DEMO_MODE" in e for e in errs)


def test_validate_pilot_env_fails_json_writes_enabled():
    errs = validate_pilot_env(_minimal_pilot_env(UNIFIED_INTAKE_JSON_CASE_WRITES="1"))
    assert any("UNIFIED_INTAKE_JSON_CASE_WRITES" in e for e in errs)


def test_validate_pilot_env_fails_missing_db():
    env = _minimal_pilot_env()
    del env["SERVICE_RECORD_DATABASE_URL"]
    errs = validate_pilot_env(env)
    assert any("SERVICE_RECORD_DATABASE_URL" in e for e in errs)


def test_validate_pilot_env_fails_demo_mode_with_product_only():
    errs = validate_pilot_env(_minimal_pilot_env(DEMO_MODE="1"))
    assert any("DEMO_MODE" in e for e in errs)


def test_validate_pilot_env_accepts_secret_manager_for_db():
    env = _minimal_pilot_env()
    del env["SERVICE_RECORD_DATABASE_URL"]
    env["CLOUD_RUN_USE_SECRET_MANAGER"] = "1"
    assert validate_pilot_env(env) == []


def test_validate_pilot_env_fails_dual_write_enabled():
    errs = validate_pilot_env(_minimal_pilot_env(UNIFIED_INTAKE_PG_DUAL_WRITE="1"))
    assert any("UNIFIED_INTAKE_PG_DUAL_WRITE" in e for e in errs)


def test_validate_pilot_env_fails_inmemory_sessions_with_db():
    errs = validate_pilot_env(
        _minimal_pilot_env(UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS="1")
    )
    assert any("UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS" in e for e in errs)


def test_validate_pilot_env_fails_matching_intake_support_keys():
    key = "same-secret-minimum-length-ok-123456789"
    errs = validate_pilot_env(
        _minimal_pilot_env(
            UNIFIED_INTAKE_INTAKE_API_KEY=key,
            UNIFIED_INTAKE_SUPPORT_API_KEY=key,
        )
    )
    assert any("must differ" in e for e in errs)


def test_validate_pilot_env_fails_unset_json_case_writes():
    env = _minimal_pilot_env()
    del env["UNIFIED_INTAKE_JSON_CASE_WRITES"]
    errs = validate_pilot_env(env)
    assert any("UNIFIED_INTAKE_JSON_CASE_WRITES" in e for e in errs)


def test_load_dotenv_skips_comments(tmp_path: Path):
    p = tmp_path / "x.env"
    p.write_text(
        "# comment\nUNIFIED_INTAKE_PRODUCT_ONLY=1\n\nFOO=bar\n",
        encoding="utf-8",
    )
    d = _load_dotenv(p)
    assert d["UNIFIED_INTAKE_PRODUCT_ONLY"] == "1"
    assert d["FOO"] == "bar"
