#!/usr/bin/env python3
"""
Local smoke test for vehicle entity repository (Postgres + JSONB).

Requires: SERVICE_RECORD_DATABASE_URL or DATABASE_URL, and intake_entities table
(see services/fiqa_api/db/schema/intake_entities.sql).

Usage: PYTHONPATH=. python3 scripts/test_vehicle_entity_repo.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.db.service_record_settings import service_record_database_url
from services.fiqa_api.inbox_triage.entity_repository import (
    get_active_vehicle,
    save_vehicle_entity,
    update_vehicle_entity,
)


def main() -> int:
    if not service_record_database_url():
        print("SKIP: SERVICE_RECORD_DATABASE_URL / DATABASE_URL not set")
        return 0

    sid = f"test_vehmvp_{uuid.uuid4().hex[:16]}"
    base = {
        "year": "2020",
        "make": "Toyota",
        "model": "Camry",
        "vin": "",
        "zip": "92618",
        "driver": "",
        "source_turns": [],
        "confidence": {},
    }
    # 1) create
    save_vehicle_entity(sid, base, case_id="case_test_vehmvp")
    row = get_active_vehicle(sid)
    assert row is not None, "expected row after save"
    p = row.get("payload") or {}
    assert p.get("year") == "2020"
    assert p.get("model") == "Camry"

    # 2) update year
    update_vehicle_entity(sid, {"year": "2021"})
    row2 = get_active_vehicle(sid)
    assert row2 is not None
    p2 = row2.get("payload") or {}
    assert p2.get("year") == "2021", p2
    assert p2.get("model") == "Camry", "merge should keep model"

    # 3) update vin
    vin = "1HGBH41JXMN109186"
    update_vehicle_entity(sid, {"vin": vin})
    row3 = get_active_vehicle(sid)
    assert row3 is not None
    p3 = row3.get("payload") or {}
    assert p3.get("vin") == vin, p3
    assert p3.get("year") == "2021"
    assert p3.get("zip") == "92618"

    print("OK: vehicle entity repo create / merge / read")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print("FAIL:", e)
        raise
