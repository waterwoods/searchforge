#!/usr/bin/env python3
"""Verify miniapp/app.json page declarations resolve to required source files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "miniapp"


def main() -> int:
    app_json_path = ROOT / "app.json"
    project_config_path = ROOT / "project.config.json"

    if not app_json_path.is_file():
        print(f"ERROR: missing {app_json_path}")
        return 1

    app_json = json.loads(app_json_path.read_text(encoding="utf-8"))
    pages = app_json.get("pages", [])
    if not pages:
        print("ERROR: app.json has no pages")
        return 1

    project_config = json.loads(project_config_path.read_text(encoding="utf-8"))
    plugins = project_config.get("setting", {}).get("useCompilerPlugins")
    ts_enabled = plugins == ["typescript"] or (
        isinstance(plugins, list) and "typescript" in plugins
    )

    errors: list[str] = []
    for index, page in enumerate(pages):
        base = ROOT / page
        ts_path = base.with_suffix(".ts")
        js_path = base.with_suffix(".js")
        wxml_path = Path(f"{base}.wxml")
        json_path = Path(f"{base}.json")

        if not wxml_path.is_file():
            errors.append(f"pages[{index}] {page}: missing {page}.wxml")
        if not json_path.is_file():
            errors.append(f"pages[{index}] {page}: missing {page}.json")
        if ts_path.is_file() and not js_path.is_file() and not ts_enabled:
            errors.append(
                f"pages[{index}] {page}: has .ts but no .js and typescript plugin disabled"
            )
        if not ts_path.is_file() and not js_path.is_file():
            errors.append(f"pages[{index}] {page}: missing .ts and .js")

    app_ts = ROOT / "app.ts"
    app_js = ROOT / "app.js"
    if app_ts.is_file() and not app_js.is_file() and not ts_enabled:
        errors.append("app.ts exists but app.js missing and typescript plugin disabled")

    print(f"Checked {len(pages)} pages in {app_json_path}")
    print(f"TypeScript compiler plugin enabled: {ts_enabled}")
    if errors:
        print("FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("OK: all declared pages resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
