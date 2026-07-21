"""P36 T3 — deploy safety check fail-closed unit tests."""

from __future__ import annotations

from pathlib import Path

from scripts.p36_deploy_safety_check import (
    PROD_DB_SECRET,
    PROD_SERVICE_NAME,
    QA_DB_SECRET,
    QA_HARNESS_FLAGS,
    QA_SERVICE_NAME,
    check_deploy_safety,
    format_report,
    main,
)


def _qa_env(**overrides: str) -> dict[str, str]:
    base = {
        "SERVICE_NAME": QA_SERVICE_NAME,
        "CLOUD_RUN_USE_SECRET_MANAGER": "1",
        "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": QA_DB_SECRET,
    }
    base.update(overrides)
    return base


def _prod_env(**overrides: str) -> dict[str, str]:
    base = {
        "SERVICE_NAME": PROD_SERVICE_NAME,
        "CLOUD_RUN_USE_SECRET_MANAGER": "1",
        "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": PROD_DB_SECRET,
    }
    base.update(overrides)
    return base


def test_production_clean_passes():
    errs = check_deploy_safety(
        deploy_entry="paid_pilot",
        env_file=Path(".env.cloudrun"),
        env=_prod_env(),
    )
    assert errs == []


def test_cloud_qa_clean_passes():
    errs = check_deploy_safety(
        deploy_entry="cloud_qa",
        env_file=Path(".env.cloudrun.qa"),
        env=_qa_env(),
    )
    assert errs == []


def test_production_rejects_qa_harness_flags():
    for flag in QA_HARNESS_FLAGS:
        errs = check_deploy_safety(
            deploy_entry="paid_pilot",
            env_file=Path(".env.cloudrun"),
            env=_prod_env(**{flag: "1"}),
        )
        assert errs, f"expected fail for {flag}"
        assert any(flag in e for e in errs)


def test_fiqa_api_with_harness_impossible():
    errs = check_deploy_safety(
        deploy_entry="paid_pilot",
        env_file=Path(".env.cloudrun"),
        env=_prod_env(ENABLE_P35_MP_QA_HARNESS="1"),
    )
    assert any("fiqa-api" in e and "ENABLE_P35_MP_QA_HARNESS" in e for e in errs)


def test_qa_env_targeting_production_service_rejected():
    errs = check_deploy_safety(
        deploy_entry="cloud_qa",
        env_file=Path(".env.cloudrun.qa"),
        env=_qa_env(SERVICE_NAME=PROD_SERVICE_NAME),
    )
    assert any("Production service" in e or PROD_SERVICE_NAME in e for e in errs)


def test_qa_with_production_db_secret_rejected():
    errs = check_deploy_safety(
        deploy_entry="cloud_qa",
        env_file=Path(".env.cloudrun.qa"),
        env=_qa_env(CLOUD_RUN_SECRET_SERVICE_RECORD_DB=PROD_DB_SECRET),
    )
    assert any(PROD_DB_SECRET in e for e in errs)


def test_qa_secret_manager_without_db_secret_name_rejected():
    errs = check_deploy_safety(
        deploy_entry="cloud_qa",
        env_file=Path(".env.cloudrun.qa"),
        env=_qa_env(CLOUD_RUN_SECRET_SERVICE_RECORD_DB=""),
    )
    # empty override leaves key as "" — require explicit QA secret
    env = _qa_env()
    del env["CLOUD_RUN_SECRET_SERVICE_RECORD_DB"]
    errs = check_deploy_safety(
        deploy_entry="cloud_qa",
        env_file=Path(".env.cloudrun.qa"),
        env=env,
    )
    assert any("CLOUD_RUN_SECRET_SERVICE_RECORD_DB" in e for e in errs)


def test_production_with_qa_db_secret_rejected():
    errs = check_deploy_safety(
        deploy_entry="paid_pilot",
        env_file=Path(".env.cloudrun"),
        env=_prod_env(CLOUD_RUN_SECRET_SERVICE_RECORD_DB=QA_DB_SECRET),
    )
    assert any(QA_DB_SECRET in e for e in errs)


def test_paid_pilot_loading_qa_env_file_rejected():
    errs = check_deploy_safety(
        deploy_entry="paid_pilot",
        env_file=Path("/tmp/.env.cloudrun.qa"),
        env=_prod_env(),
    )
    assert any(".env.cloudrun.qa" in e or "paid-pilot" in e.lower() for e in errs)


def test_cloud_qa_loading_prod_env_file_rejected():
    errs = check_deploy_safety(
        deploy_entry="cloud_qa",
        env_file=Path("/tmp/.env.cloudrun"),
        env=_qa_env(),
    )
    assert any(".env.cloudrun.qa" in e for e in errs)


def test_qa_harness_opt_in_allowed_on_cloud_qa():
    errs = check_deploy_safety(
        deploy_entry="cloud_qa",
        env_file=Path(".env.cloudrun.qa"),
        env=_qa_env(
            ENABLE_P35_MP_QA_HARNESS="1",
            UNIFIED_INTAKE_QA_FIXTURE_SURFACE="1",
            ENABLE_P26H_FIXTURE_RUNNER="1",
        ),
    )
    assert errs == []


def test_harness_flags_do_not_default_on_in_module():
    # Module must not define truthy defaults for harness flags.
    import scripts.p36_deploy_safety_check as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    for flag in QA_HARNESS_FLAGS:
        assert f"{flag}=1" not in src
        assert f'{flag}": "1"' not in src


def test_cli_fails_closed_on_dangerous_combo(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env.cloudrun"
    env_path.write_text(
        "\n".join(
            [
                f"SERVICE_NAME={PROD_SERVICE_NAME}",
                "ENABLE_P26H_FIXTURE_RUNNER=1",
                "UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("ENABLE_P26H_FIXTURE_RUNNER", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_QA_FIXTURE_SURFACE", raising=False)
    rc = main(["--env-file", str(env_path), "--deploy-entry", "paid_pilot"])
    assert rc == 1


def test_cli_pass_clean_prod(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env.cloudrun"
    env_path.write_text(
        "\n".join(
            [
                f"SERVICE_NAME={PROD_SERVICE_NAME}",
                f"CLOUD_RUN_SECRET_SERVICE_RECORD_DB={PROD_DB_SECRET}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    for flag in QA_HARNESS_FLAGS:
        monkeypatch.delenv(flag, raising=False)
    rc = main(["--env-file", str(env_path), "--deploy-entry", "paid_pilot"])
    assert rc == 0


def test_format_report_fail_closed_message():
    text = format_report(["bad combo"])
    assert "FAIL" in text
    assert "bad combo" in text
