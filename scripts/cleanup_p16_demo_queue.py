#!/usr/bin/env python3
"""One-shot P16 document-intake demo queue cleanup for Chen Kui pilot.

Keeps a small curated set of cases; hard-deletes the rest (mark workbench_test + DELETE).
Uses production Cloud Run API — requires UNIFIED_INTAKE_INTAKE_API_KEY in env.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = os.environ.get(
    "VITE_API_BASE_URL",
    "https://fiqa-api-1013093472160.us-west1.run.app",
).rstrip("/")
API_KEY = (os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()

# Curated demo queue — mix of READY / NEED_INFO / BROKER_REVIEW, Add Car + Policy Review
KEEP_CASE_IDS = {
    "case_05ea7789ecca",  # nanxin li · Policy Review · READY · Progressive premium
    "case_4a766cdda1ea",  # Li Hua · Add Car · READY · Toyota Camry
    "case_2443b8598545",  # Yong Kim · Add Car · READY
    "case_179318481bf5",  # nanxin li · Policy Review · NEED_INFO
    "case_965c2dd1a332",  # Li Hua · Policy Review · NEED_INFO
    "case_93fde2617ee6",  # Mei Lin Chen · Add Car · BROKER_REVIEW
}

JUNK_NAME_PATTERNS = (
    "qa test",
    "qa scenario",
    "qa ready",
    "regression",
    "conflict test",
    "test customer",
    "heic test",
    "need info test",
    "persistence test",
    "张三",
    "李四",
    "赵六",
    "钱七",
    "孙八",
    "周十",
    "吴十一",
    "陈九",
    "李华",
)


def _headers() -> dict[str, str]:
    if not API_KEY:
        print("ERROR: UNIFIED_INTAKE_INTAKE_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return {
        "Content-Type": "application/json",
        "X-Unified-Intake-Api-Key": API_KEY,
    }


def _req(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers=_headers(),
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        raise RuntimeError(f"{method} {path} -> {e.code}: {detail}") from e


def is_p16_case(c: dict) -> bool:
    lane = (c.get("service_lane") or "").strip()
    if lane in ("add_car", "policy_review"):
        return True
    src = (c.get("source_text") or "").lower()
    return "p16 add-car" in src or "p16 policy review" in src


def is_junk_name(name: str) -> bool:
    n = (name or "").strip().lower()
    if not n:
        return True
    return any(p in n for p in JUNK_NAME_PATTERNS)


def fetch_all_cases() -> list[dict]:
    cases: list[dict] = []
    offset = 0
    while True:
        data = _req("GET", f"/api/inbox/cases?limit=50&offset={offset}")
        batch = data.get("cases") or []
        if not batch:
            break
        cases.extend(batch)
        if len(batch) < 50:
            break
        offset += 50
    return cases


def delete_case(case_id: str) -> None:
    _req("PATCH", f"/api/inbox/cases/{case_id}/workbench", {"is_test": True})
    _req("DELETE", f"/api/inbox/cases/{case_id}")


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    all_cases = fetch_all_cases()
    p16 = [c for c in all_cases if is_p16_case(c)]
    to_delete: list[dict] = []
    kept: list[dict] = []

    for c in p16:
        cid = c.get("case_id") or ""
        if cid in KEEP_CASE_IDS:
            kept.append(c)
        else:
            to_delete.append(c)

    print(f"P16 cases total: {len(p16)}")
    print(f"Keeping: {len(kept)}")
    for c in kept:
        print(f"  KEEP {c.get('case_id')} | {c.get('customer_name')} | {c.get('service_lane')}")
    print(f"Deleting: {len(to_delete)}")

    if dry_run:
        print("(dry-run — no deletes)")
        return

    deleted = 0
    errors = 0
    for c in to_delete:
        cid = c.get("case_id") or ""
        if not cid:
            continue
        try:
            delete_case(cid)
            deleted += 1
            if deleted % 25 == 0:
                print(f"  ... deleted {deleted}")
        except Exception as e:
            errors += 1
            print(f"  FAIL {cid}: {e}", file=sys.stderr)

    print(f"Done. deleted={deleted} errors={errors} kept={len(kept)}")


if __name__ == "__main__":
    main()
