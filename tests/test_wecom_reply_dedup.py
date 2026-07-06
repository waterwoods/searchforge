"""Unit tests for the WeCom outbound reply idempotency guard."""

from __future__ import annotations

import pytest

from services.fiqa_api.wecom import reply_dedup


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reply_dedup.reset_reply_dedup_memory_for_tests()
    yield
    reply_dedup.reset_reply_dedup_memory_for_tests()


def test_claim_true_once_then_false_in_memory() -> None:
    assert reply_dedup.claim_reply_send("m1") is True
    assert reply_dedup.claim_reply_send("m1") is False
    assert reply_dedup.claim_reply_send("m1") is False


def test_different_msg_ids_each_claim_independently() -> None:
    assert reply_dedup.claim_reply_send("m1") is True
    assert reply_dedup.claim_reply_send("m2") is True
    assert reply_dedup.claim_reply_send("m1") is False
    assert reply_dedup.claim_reply_send("m2") is False


def test_release_allows_a_subsequent_claim() -> None:
    assert reply_dedup.claim_reply_send("m1") is True
    reply_dedup.release_reply_claim("m1")
    assert reply_dedup.claim_reply_send("m1") is True


def test_empty_msg_id_never_blocks_send() -> None:
    """No msg_id to key on: never suppress a reply just because we can't dedup it."""
    assert reply_dedup.claim_reply_send("") is True
    assert reply_dedup.claim_reply_send("") is True
    assert reply_dedup.claim_reply_send(None) is True  # type: ignore[arg-type]


def test_release_of_unclaimed_msg_id_is_a_no_op() -> None:
    reply_dedup.release_reply_claim("never_claimed")
    assert reply_dedup.claim_reply_send("never_claimed") is True


class _FakeCursor:
    def __init__(self, store: dict[str, bool]):
        self._store = store
        self.rowcount = 0

    def execute(self, sql: str, params: dict | tuple | None = None) -> None:
        normalized = " ".join(sql.split())
        if normalized.startswith("CREATE TABLE"):
            return
        if normalized.startswith("INSERT INTO wecom_reply_dedup"):
            mid = params["mid"]
            if mid in self._store:
                self.rowcount = 0
            else:
                self._store[mid] = True
                self.rowcount = 1
        elif normalized.startswith("DELETE FROM wecom_reply_dedup"):
            mid = params["mid"]
            existed = self._store.pop(mid, None) is not None
            self.rowcount = 1 if existed else 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConnection:
    def __init__(self, store: dict[str, bool]):
        self._store = store

    def transaction(self):
        return _FakeTransaction()

    def cursor(self):
        return _FakeCursor(self._store)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_claim_uses_atomic_postgres_insert_when_db_configured(monkeypatch) -> None:
    """When a database URL is configured, the claim must go through the
    atomic INSERT ... ON CONFLICT DO NOTHING path (this is what makes the
    guarantee hold across multiple Cloud Run instances), not just the
    in-process set."""
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://fake/db")
    fake_store: dict[str, bool] = {}

    import contextlib

    @contextlib.contextmanager
    def fake_connection():
        yield _FakeConnection(fake_store)

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.service_record_connection",
        fake_connection,
    )

    assert reply_dedup.claim_reply_send("pg_m1") is True
    assert fake_store == {"pg_m1": True}
    assert reply_dedup.claim_reply_send("pg_m1") is False

    reply_dedup.release_reply_claim("pg_m1")
    assert fake_store == {}
    assert reply_dedup.claim_reply_send("pg_m1") is True


def test_db_error_degrades_to_in_memory_guard_without_raising(monkeypatch) -> None:
    """Dedup must never raise or block a reply just because the DB is
    briefly unavailable — it degrades to the in-process guard."""
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://fake/db")

    def boom():
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.service_record_connection",
        boom,
    )

    assert reply_dedup.claim_reply_send("m_degraded") is True
    assert reply_dedup.claim_reply_send("m_degraded") is False
