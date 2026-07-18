"""P26H QA fixture client — HTTP or in-process transport.

Environment:
  P26H_QA_BASE_URL          Deployed API origin (e.g. https://qa.example.com)
  P26H_QA_TRANSPORT         http | inprocess (default: http if BASE_URL set, else unset)
  UNIFIED_INTAKE_SUPPORT_API_KEY  Support key for authorized fixture routes
  ENABLE_P26H_FIXTURE_RUNNER=1
  UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1   (required on server; inprocess also needs locally)
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


class FixtureClientError(RuntimeError):
    def __init__(self, message: str, *, layer: str = "Fixture Runner", detail: str = ""):
        super().__init__(message)
        self.layer = layer
        self.detail = detail


@dataclass(frozen=True)
class FixtureTransportInfo:
    transport: str
    base_url: str
    notes: str


def resolve_transport() -> FixtureTransportInfo:
    explicit = (os.getenv("P26H_QA_TRANSPORT") or "").strip().lower()
    base = (os.getenv("P26H_QA_BASE_URL") or os.getenv("UNIFIED_INTAKE_QA_BASE_URL") or "").strip().rstrip("/")
    if explicit == "inprocess" or base.lower() in {"inprocess", "local-inprocess"}:
        return FixtureTransportInfo(
            transport="inprocess",
            base_url="inprocess",
            notes="In-process fixture runner (local verification of QA path).",
        )
    if explicit == "http" or base.startswith("http://") or base.startswith("https://"):
        if not base.startswith("http"):
            raise FixtureClientError(
                "P26H_QA_BASE_URL must be an http(s) origin when transport=http",
                detail="Set P26H_QA_BASE_URL=https://<qa-host>",
            )
        return FixtureTransportInfo(transport="http", base_url=base, notes="Deployed QA HTTP fixture API.")
    raise FixtureClientError(
        "QA fixture transport not configured",
        detail=(
            "Set P26H_QA_BASE_URL=https://<qa-host> and UNIFIED_INTAKE_SUPPORT_API_KEY=<key>, "
            "or P26H_QA_TRANSPORT=inprocess with ENABLE_P26H_FIXTURE_RUNNER=1 and "
            "UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1 for local QA-path verification."
        ),
    )


class FixtureClient(Protocol):
    def status(self) -> dict[str, Any]: ...
    def create_run(self) -> dict[str, Any]: ...
    def create_case(self, harness_run_id: str, **kwargs: Any) -> dict[str, Any]: ...
    def register_evidence(self, harness_run_id: str, case_id: str, slot: str) -> dict[str, Any]: ...
    def patch_vehicle(self, harness_run_id: str, case_id: str) -> dict[str, Any]: ...
    def broker_followup(self, harness_run_id: str, case_id: str) -> dict[str, Any]: ...
    def inspect(self, harness_run_id: str, case_id: str) -> dict[str, Any]: ...
    def expired_token(self, harness_run_id: str, case_id: str) -> dict[str, Any]: ...
    def cleanup(self, harness_run_id: str) -> dict[str, Any]: ...


class InProcessFixtureClient:
    def __init__(self) -> None:
        from services.fiqa_api.inbox_triage import p26h_qa_fixture_runner as fx

        self._fx = fx
        try:
            fx.assert_fixture_runner_allowed(require_support_key_in_prod=False)
        except ValueError as exc:
            raise FixtureClientError(
                str(exc),
                detail="Enable ENABLE_P26H_FIXTURE_RUNNER=1 and UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1",
            ) from exc

    def status(self) -> dict[str, Any]:
        return self._fx.fixture_runner_status()

    def create_run(self) -> dict[str, Any]:
        return self._fx.create_run()

    def create_case(self, harness_run_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._fx.create_fresh_claim(harness_run_id=harness_run_id, **kwargs)

    def register_evidence(self, harness_run_id: str, case_id: str, slot: str) -> dict[str, Any]:
        return self._fx.register_test_evidence(
            harness_run_id=harness_run_id, case_id=case_id, slot=slot
        )

    def patch_vehicle(self, harness_run_id: str, case_id: str) -> dict[str, Any]:
        return self._fx.patch_vehicle_facts(harness_run_id=harness_run_id, case_id=case_id)

    def broker_followup(self, harness_run_id: str, case_id: str) -> dict[str, Any]:
        return self._fx.create_broker_followup(harness_run_id=harness_run_id, case_id=case_id)

    def inspect(self, harness_run_id: str, case_id: str) -> dict[str, Any]:
        return self._fx.inspect_case(harness_run_id=harness_run_id, case_id=case_id)

    def expired_token(self, harness_run_id: str, case_id: str) -> dict[str, Any]:
        return self._fx.issue_expired_token(harness_run_id=harness_run_id, case_id=case_id)

    def cleanup(self, harness_run_id: str) -> dict[str, Any]:
        return self._fx.cleanup_run(harness_run_id)


class HttpFixtureClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.support_key = (os.getenv("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.support_key:
            headers["X-Unified-Intake-Support-Key"] = self.support_key
        return headers

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            if exc.code in (401, 403):
                raise FixtureClientError(
                    f"fixture_auth_refused:{exc.code}",
                    detail=detail or "missing/invalid support key or fixture surface disabled",
                ) from exc
            raise FixtureClientError(
                f"fixture_http_{exc.code}",
                detail=detail,
            ) from exc
        except urllib.error.URLError as exc:
            raise FixtureClientError(
                "fixture_unreachable",
                detail=str(exc.reason if hasattr(exc, "reason") else exc),
            ) from exc

    def status(self) -> dict[str, Any]:
        return self._request("GET", "/api/inbox/support/p26h-fixture/status")

    def create_run(self) -> dict[str, Any]:
        return self._request("POST", "/api/inbox/support/p26h-fixture/runs")

    def create_case(self, harness_run_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/inbox/support/p26h-fixture/runs/{harness_run_id}/cases",
            {
                "suffix": kwargs.get("suffix", "fresh"),
                "session_id": kwargs.get("session_id"),
                "idempotency_key": kwargs.get("idempotency_key"),
                "accident_description": kwargs.get(
                    "accident_description", "停车场倒车碰撞，前保险杠受损"
                ),
            },
        )

    def register_evidence(self, harness_run_id: str, case_id: str, slot: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/inbox/support/p26h-fixture/runs/{harness_run_id}/cases/{case_id}/evidence",
            {"slot": slot},
        )

    def patch_vehicle(self, harness_run_id: str, case_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/inbox/support/p26h-fixture/runs/{harness_run_id}/cases/{case_id}/vehicle",
            {},
        )

    def broker_followup(self, harness_run_id: str, case_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/inbox/support/p26h-fixture/runs/{harness_run_id}/cases/{case_id}/broker-followup",
            {},
        )

    def inspect(self, harness_run_id: str, case_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/api/inbox/support/p26h-fixture/runs/{harness_run_id}/cases/{case_id}/inspect",
        )

    def expired_token(self, harness_run_id: str, case_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/inbox/support/p26h-fixture/runs/{harness_run_id}/cases/{case_id}/expired-token",
            {},
        )

    def cleanup(self, harness_run_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/api/inbox/support/p26h-fixture/runs/{harness_run_id}")


def open_fixture_client() -> tuple[FixtureClient, FixtureTransportInfo]:
    info = resolve_transport()
    if info.transport == "inprocess":
        return InProcessFixtureClient(), info
    return HttpFixtureClient(info.base_url), info
