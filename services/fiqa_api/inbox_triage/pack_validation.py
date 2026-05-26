"""Lightweight client-pack filesystem checks (fail-fast onboarding)."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]


def validate_client_pack_layout(client_id: str) -> list[str]:
    """Return issue strings; empty list means the pack layout is valid for onboarding."""
    cid = (client_id or "").strip()
    if not cid:
        return ["client_id is empty"]
    base = _REPO_ROOT / "configs" / "clients" / cid
    if not base.is_dir():
        return [f"missing configs/clients/{cid}"]
    issues: list[str] = []
    for name in ("ui_copy.json", "handoff_phrases.json"):
        if not (base / name).is_file():
            issues.append(f"missing configs/clients/{cid}/{name}")
    return issues
