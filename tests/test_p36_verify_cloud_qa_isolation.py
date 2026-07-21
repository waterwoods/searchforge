"""P36 T2 — Cloud QA isolation verifier fail-closed unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.p36_verify_cloud_qa_isolation import (
    PROD_DATABASE_NAME,
    PROD_DB_SECRET,
    PROD_SERVICE_NAME,
    QA_DATABASE_NAME,
    QA_DB_SECRET,
    QA_SERVICE_NAME,
    format_report,
    main,
    verify_isolation,
)

QA_URL = "postgresql://u:p@10.73.0.3:5432/caseiq-qa"
PROD_URL = "postgresql://u:p@10.73.0.3:5432/caseiq"
WRONG_QA_URL_CASEIQ = "postgresql://u:p@10.73.0.3:5432/caseiq"


def _secret_map(mapping: dict[str, str]):
    def _access(secret_name: str, project_id: str) -> str:
        if secret_name not in mapping:
            raise RuntimeError(f"secret missing: {secret_name}")
        return mapping[secret_name]

    return _access


def test_pass_when_qa_and_prod_isolated():
    qa_env = {
        "SERVICE_NAME": QA_SERVICE_NAME,
        "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": QA_DB_SECRET,
        "SERVICE_RECORD_DATABASE_URL": QA_URL,
    }
    prod_env = {
        "SERVICE_NAME": PROD_SERVICE_NAME,
        "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": PROD_DB_SECRET,
        "SERVICE_RECORD_DATABASE_URL": PROD_URL,
    }
    checks = verify_isolation(
        qa_env=qa_env,
        prod_env=prod_env,
        qa_env_path=None,
        prod_env_path=None,
        project_id="optimal-disk-472305-e2",
        allow_secret_access=False,
    )
    assert all(c.ok for c in checks), format_report(checks)
    assert "RESULT: PASS" in format_report(checks)


def test_fail_when_qa_service_is_production():
    checks = verify_isolation(
        qa_env={
            "SERVICE_NAME": PROD_SERVICE_NAME,
            "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": QA_DB_SECRET,
            "SERVICE_RECORD_DATABASE_URL": QA_URL,
        },
        prod_env={"SERVICE_RECORD_DATABASE_URL": PROD_URL},
        qa_env_path=None,
        prod_env_path=None,
        project_id="p",
        allow_secret_access=False,
    )
    failed = {c.name for c in checks if not c.ok}
    assert any("service name" in n for n in failed)
    assert "RESULT: FAIL" in format_report(checks)


def test_fail_when_qa_secret_is_production_secret():
    checks = verify_isolation(
        qa_env={
            "SERVICE_NAME": QA_SERVICE_NAME,
            "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": PROD_DB_SECRET,
            "SERVICE_RECORD_DATABASE_URL": QA_URL,
        },
        prod_env={"SERVICE_RECORD_DATABASE_URL": PROD_URL},
        qa_env_path=None,
        prod_env_path=None,
        project_id="p",
        allow_secret_access=False,
    )
    failed_details = " ".join(c.detail for c in checks if not c.ok)
    assert PROD_DB_SECRET in failed_details


def test_fail_when_qa_resolves_to_caseiq():
    checks = verify_isolation(
        qa_env={
            "SERVICE_NAME": QA_SERVICE_NAME,
            "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": QA_DB_SECRET,
            "SERVICE_RECORD_DATABASE_URL": WRONG_QA_URL_CASEIQ,
        },
        prod_env={"SERVICE_RECORD_DATABASE_URL": PROD_URL},
        qa_env_path=None,
        prod_env_path=None,
        project_id="p",
        allow_secret_access=False,
    )
    assert any(not c.ok and PROD_DATABASE_NAME in c.detail for c in checks)
    assert any(not c.ok and "caseiq" in c.detail for c in checks)


def test_fail_when_qa_url_missing_and_no_secret_access():
    checks = verify_isolation(
        qa_env={
            "SERVICE_NAME": QA_SERVICE_NAME,
            "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": QA_DB_SECRET,
        },
        prod_env={"SERVICE_RECORD_DATABASE_URL": PROD_URL},
        qa_env_path=None,
        prod_env_path=None,
        project_id="p",
        allow_secret_access=False,
    )
    assert any(not c.ok and "cannot prove QA isolation" in c.detail for c in checks)


def test_fail_when_same_host_and_database():
    shared = "postgresql://u:p@10.1.2.3:5432/caseiq-qa"
    # Both point at caseiq-qa — same fingerprint (misconfigured prod URL for test)
    checks = verify_isolation(
        qa_env={
            "SERVICE_NAME": QA_SERVICE_NAME,
            "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": QA_DB_SECRET,
            "SERVICE_RECORD_DATABASE_URL": shared,
        },
        prod_env={
            "SERVICE_NAME": PROD_SERVICE_NAME,
            "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": PROD_DB_SECRET,
            "SERVICE_RECORD_DATABASE_URL": shared,
        },
        qa_env_path=None,
        prod_env_path=None,
        project_id="p",
        allow_secret_access=False,
    )
    assert any(
        not c.ok and "fingerprint" in c.name for c in checks
    ), format_report(checks)


def test_secret_accessor_resolves_qa_and_prod():
    accessor = _secret_map({QA_DB_SECRET: QA_URL, PROD_DB_SECRET: PROD_URL})
    checks = verify_isolation(
        qa_env={
            "SERVICE_NAME": QA_SERVICE_NAME,
            "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": QA_DB_SECRET,
        },
        prod_env={
            "SERVICE_NAME": PROD_SERVICE_NAME,
            "CLOUD_RUN_SECRET_SERVICE_RECORD_DB": PROD_DB_SECRET,
        },
        qa_env_path=None,
        prod_env_path=None,
        project_id="p",
        secret_accessor=accessor,
        allow_secret_access=True,
    )
    assert all(c.ok for c in checks), format_report(checks)
    assert any(c.ok and c.name.startswith("QA database connection") for c in checks)


def test_cli_missing_qa_env_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["--qa-env", str(tmp_path / "missing.env"), "--no-secret-access"])
    assert rc == 1


def test_cli_pass_with_env_urls(tmp_path: Path):
    qa = tmp_path / ".env.cloudrun.qa"
    prod = tmp_path / ".env.cloudrun"
    qa.write_text(
        "\n".join(
            [
                f"SERVICE_NAME={QA_SERVICE_NAME}",
                f"CLOUD_RUN_SECRET_SERVICE_RECORD_DB={QA_DB_SECRET}",
                f"SERVICE_RECORD_DATABASE_URL={QA_URL}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    prod.write_text(
        "\n".join(
            [
                f"SERVICE_NAME={PROD_SERVICE_NAME}",
                f"CLOUD_RUN_SECRET_SERVICE_RECORD_DB={PROD_DB_SECRET}",
                f"SERVICE_RECORD_DATABASE_URL={PROD_URL}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rc = main(
        [
            "--qa-env",
            str(qa),
            "--prod-env",
            str(prod),
            "--no-secret-access",
        ]
    )
    assert rc == 0


def test_cli_fail_when_qa_points_at_caseiq(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    qa = tmp_path / ".env.cloudrun.qa"
    prod = tmp_path / ".env.cloudrun"
    qa.write_text(
        "\n".join(
            [
                f"SERVICE_NAME={QA_SERVICE_NAME}",
                f"CLOUD_RUN_SECRET_SERVICE_RECORD_DB={QA_DB_SECRET}",
                f"SERVICE_RECORD_DATABASE_URL={WRONG_QA_URL_CASEIQ}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    prod.write_text(f"SERVICE_RECORD_DATABASE_URL={PROD_URL}\n", encoding="utf-8")
    rc = main(["--qa-env", str(qa), "--prod-env", str(prod), "--no-secret-access"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "RESULT: FAIL" in captured.out
    assert QA_DATABASE_NAME in captured.out or "caseiq" in captured.out
