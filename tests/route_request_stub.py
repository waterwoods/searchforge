"""Minimal Starlette Request for calling FastAPI route handlers directly in tests."""

from __future__ import annotations

from starlette.requests import Request


def minimal_route_request(*, client_asserted_org_id: str | None = None) -> Request:
    scope: dict = {
        "type": "http",
        "asgi": {"spec_version": "2.3", "version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "root_path": "",
        "headers": [],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
    }
    req = Request(scope)
    if client_asserted_org_id is not None:
        req.state.client_asserted_org_id = client_asserted_org_id
    return req
