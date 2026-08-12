"""Pre-pilot guards: no secret material in logs, no identity simulate on Production.

Both are things a deploy gate cannot fully protect. Cloud Run env vars can be changed
by hand with ``gcloud run services update``, which never runs the gate, so the refusal
has to also hold at runtime. And logs are read by more people than the console is.
"""

from __future__ import annotations

import logging
import re

import pytest

from services.fiqa_api.inbox_triage.mp_customer_identity import mp_simulate_allowed

_FAKE_OPENAI_KEY = "sk-proj-AAAABBBBCCCCDDDDEEEEFFFF0000111122223333"


@pytest.fixture(autouse=True)
def _clean_deployment_labels(monkeypatch):
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("SERVICE_NAME", raising=False)
    monkeypatch.delenv("WECHAT_MP_ALLOW_SIMULATE", raising=False)
    monkeypatch.delenv("WECHAT_BINDING_ALLOW_SIMULATE", raising=False)


# --- Identity simulate is refused on Production, whatever the env says -----


@pytest.mark.parametrize(
    "flag", ["WECHAT_MP_ALLOW_SIMULATE", "WECHAT_BINDING_ALLOW_SIMULATE"]
)
@pytest.mark.parametrize(
    "prod_label", [{"ENV": "prod"}, {"SERVICE_NAME": "fiqa-api"}]
)
def test_simulate_refused_on_production(monkeypatch, flag, prod_label):
    for key, value in prod_label.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv(flag, "1")

    assert mp_simulate_allowed() is False


@pytest.mark.parametrize(
    "flag", ["WECHAT_MP_ALLOW_SIMULATE", "WECHAT_BINDING_ALLOW_SIMULATE"]
)
def test_simulate_still_available_on_cloud_qa(monkeypatch, flag):
    monkeypatch.setenv("SERVICE_NAME", "fiqa-api-qa")
    monkeypatch.setenv(flag, "1")

    assert mp_simulate_allowed() is True


def test_simulate_off_by_default_without_flag(monkeypatch):
    monkeypatch.setenv("SERVICE_NAME", "fiqa-api-qa")

    assert mp_simulate_allowed() is False


# --- No secret-derived material reaches the logs ---------------------------


def _assert_no_secret_material(text: str, secret: str) -> None:
    assert secret not in text
    # A prefix or a length is still an attacker hint and still a leak in a shared log.
    for width in (4, 6, 8, 12):
        assert secret[:width] not in text, f"leaked {width}-char prefix"
        assert secret[-width:] not in text, f"leaked {width}-char suffix"
    leaked_length = re.search(rf"(?i)\b(?:length|len)\b\s*[=:]?\s*{len(secret)}\b", text)
    assert leaked_length is None, f"leaked key length: {leaked_length.group(0)!r}"


def test_openai_client_logs_no_secret_material(monkeypatch, caplog, capsys):
    """``get_openai_client`` used to print and log the key prefix on every call."""
    from services.fiqa_api import clients

    monkeypatch.setenv("OPENAI_API_KEY", _FAKE_OPENAI_KEY)
    monkeypatch.setattr(clients, "OPENAI_API_KEY", _FAKE_OPENAI_KEY, raising=False)
    monkeypatch.setattr(clients, "_openai_client", None, raising=False)

    with caplog.at_level(logging.DEBUG):
        try:
            clients.get_openai_client()
        except Exception:
            # Client construction may fail without the SDK installed; the logging
            # under test happens before that, so the assertions below still apply.
            pass

    # Only our own records — third-party lines carry incidental digits.
    captured = capsys.readouterr()
    emitted = "\n".join(
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("services.fiqa_api")
    )
    emitted += captured.out + captured.err
    _assert_no_secret_material(emitted, _FAKE_OPENAI_KEY)


def test_startup_log_line_carries_no_secret_material():
    """The app_main startup line must state presence only."""
    from pathlib import Path

    source = Path("services/fiqa_api/app_main.py").read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in source.splitlines()
        if "OPENAI_API_KEY" in line
        and ("[:" in line or "len(" in line)
        and ("logger." in line or "print(" in line)
    ]
    assert offenders == [], f"secret-derived startup logging: {offenders}"
