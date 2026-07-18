#!/usr/bin/env python3
"""
P25 — Golden QA DevTools Preview prep / clear (session-only).

Writes token into gitignored miniapp/project.private.config.json compile condition.
Never commits tokens. Build Gate must clear before packaging.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_CONFIG = ROOT / "miniapp" / "project.private.config.json"
ENTRY_PATH = "pages/entry/entry"
GOLDEN_ENTRY_NAME = "pages/entry/entry (Golden QA session)"
_TOKEN_QUERY_RE = re.compile(r"(?:^|[?&])token=")


def _load_private_config() -> dict[str, Any]:
    if not PRIVATE_CONFIG.exists():
        return {
            "libVersion": "3.16.2",
            "projectname": "miniapp",
            "condition": {"miniprogram": {"list": []}},
            "setting": {},
        }
    return json.loads(PRIVATE_CONFIG.read_text(encoding="utf-8"))


def _save_private_config(cfg: dict[str, Any]) -> None:
    PRIVATE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE_CONFIG.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _miniprogram_list(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    condition = cfg.setdefault("condition", {})
    if not isinstance(condition, dict):
        condition = {}
        cfg["condition"] = condition
    mp = condition.setdefault("miniprogram", {})
    if not isinstance(mp, dict):
        mp = {}
        condition["miniprogram"] = mp
    lst = mp.setdefault("list", [])
    if not isinstance(lst, list):
        lst = []
        mp["list"] = lst
    return lst


def _private_config_label() -> str:
    try:
        return str(PRIVATE_CONFIG.relative_to(ROOT))
    except ValueError:
        return str(PRIVATE_CONFIG)


def prepare_devtools_preview(token: str) -> dict[str, Any]:
    """Inject session compile query for pages/entry/entry. Returns status dict."""
    raw = (token or "").strip()
    if not raw.startswith("h5t1."):
        raise ValueError("invalid_golden_token")
    query = f"token={raw}"
    cfg = _load_private_config()
    lst = _miniprogram_list(cfg)
    updated = False
    for entry in lst:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("pathName") or "") == ENTRY_PATH:
            entry["query"] = query
            entry["name"] = GOLDEN_ENTRY_NAME
            entry.setdefault("launchMode", "default")
            entry.setdefault("scene", None)
            updated = True
            break
    if not updated:
        lst.append(
            {
                "name": GOLDEN_ENTRY_NAME,
                "pathName": ENTRY_PATH,
                "query": query,
                "launchMode": "default",
                "scene": None,
            }
        )
    _save_private_config(cfg)
    compile_line = f"{ENTRY_PATH}?{query}"
    line_path = ROOT / "docs" / "evidence" / "golden_qa" / "last_reset" / "devtools_compile_line.txt"
    line_path.parent.mkdir(parents=True, exist_ok=True)
    line_path.write_text(compile_line + "\n", encoding="utf-8")
    return {
        "ok": True,
        "preview_prepared": True,
        "pathName": ENTRY_PATH,
        "compile_name": GOLDEN_ENTRY_NAME,
        "private_config": _private_config_label(),
        "devtools_hint": f"DevTools → compile mode 「{GOLDEN_ENTRY_NAME}」 → 清缓存 → Preview → scan once",
    }


def clear_devtools_preview_tokens() -> dict[str, Any]:
    """
    Remove token= from all compile-condition queries.
    Fail closed: raises RuntimeError if file exists but cannot be cleaned/verified.
    """
    if not PRIVATE_CONFIG.exists():
        return {"ok": True, "cleared": 0, "reason": "private_config_absent"}

    try:
        cfg = _load_private_config()
    except Exception as exc:
        raise RuntimeError(f"golden_preview_clear_failed:load:{exc}") from exc

    lst = _miniprogram_list(cfg)
    cleared = 0
    for entry in lst:
        if not isinstance(entry, dict):
            continue
        query = str(entry.get("query") or "")
        if _TOKEN_QUERY_RE.search(query):
            entry["query"] = ""
            if str(entry.get("pathName") or "") == ENTRY_PATH:
                entry["name"] = "pages/entry/entry (token via query only)"
            cleared += 1

    try:
        _save_private_config(cfg)
    except Exception as exc:
        raise RuntimeError(f"golden_preview_clear_failed:write:{exc}") from exc

    # Verify no token remains
    try:
        verify = _load_private_config()
    except Exception as exc:
        raise RuntimeError(f"golden_preview_clear_failed:reread:{exc}") from exc
    for entry in _miniprogram_list(verify):
        if not isinstance(entry, dict):
            continue
        if _TOKEN_QUERY_RE.search(str(entry.get("query") or "")):
            raise RuntimeError("golden_preview_clear_failed:token_still_present")

    return {"ok": True, "cleared": cleared, "private_config": _private_config_label()}


def preview_has_session_token() -> bool:
    if not PRIVATE_CONFIG.exists():
        return False
    cfg = _load_private_config()
    for entry in _miniprogram_list(cfg):
        if isinstance(entry, dict) and _TOKEN_QUERY_RE.search(str(entry.get("query") or "")):
            return True
    return False
