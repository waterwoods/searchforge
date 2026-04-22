"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage import session_repository as intake_repo

_SESSION_FILE_MODULES = (
    "test_intake_session_persistence",
    "test_wechat_binding",
    "test_case_binding",
    "test_real_user_simulation",
)


@pytest.fixture(autouse=True)
def _reset_intake_session_store(request, monkeypatch):
    """
    Explicit in-memory intake sessions during pytest when no DB URL is set; isolation
    via reset. When DATABASE_URL is set on the host, intake tests that need memory
    still strip DB env (see _SESSION_FILE_MODULES).
    """
    monkeypatch.setenv("UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS", "1")
    fspath = str(request.fspath) if request.fspath else ""
    if any(m in fspath for m in _SESSION_FILE_MODULES):
        monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
    intake_repo.reset_intake_session_memory_for_tests()
    yield
    intake_repo.reset_intake_session_memory_for_tests()
