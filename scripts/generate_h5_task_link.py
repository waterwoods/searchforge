#!/usr/bin/env python3
"""Generate H5 guided task upload link for an Add Vehicle case (P19D-2).

Usage:
  PYTHONPATH=. python3 scripts/generate_h5_task_link.py --case-id <case_id> --slot vin_photo

  PYTHONPATH=. python3 scripts/generate_h5_task_link.py --case-id case_abc --slot vin_photo --base-url http://127.0.0.1:5173
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parents[1]
    for name in (".env.cloudrun", ".env"):
        p = root / name
        if p.exists():
            load_dotenv(p, override=False)


def main() -> int:
    _load_dotenv()
    if str(os.getcwd()) not in sys.path:
        sys.path.insert(0, os.getcwd())

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case-id", required=True, help="Add Vehicle case_id")
    p.add_argument("--slot", default="vin_photo", help="Task slot for v1 link (default: vin_photo)")
    p.add_argument(
        "--flow",
        action="store_true",
        help="Mint v2 Add Vehicle photo flow link (VIN + registration + insurance)",
    )
    p.add_argument("--lane", default="add_car", help="Service lane (default: add_car)")
    p.add_argument("--ttl-seconds", type=int, default=86400, help="Token TTL (default 24h)")
    p.add_argument(
        "--base-url",
        default="",
        help="Frontend base URL (default: UNIFIED_INTAKE_FRONTEND_ORIGIN or local dev)",
    )
    args = p.parse_args()

    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
    from services.fiqa_api.inbox_triage.h5_task_link import (
        h5_task_frontend_base,
        mint_h5_add_vehicle_photo_flow_link,
        mint_h5_task_link,
    )

    case_id = args.case_id.strip()
    case = get_case_for_read(case_id)
    if case is None:
        print(f"case not found: {case_id}", file=sys.stderr)
        return 1

    ext_uid = str(case.get("wecom_external_userid") or "").strip() or None
    try:
        base = (args.base_url or h5_task_frontend_base()).rstrip("/")
        if args.flow:
            url = mint_h5_add_vehicle_photo_flow_link(
                case_id=case_id,
                lane=args.lane,
                external_userid=ext_uid,
                base_url=base,
                ttl_seconds=max(60, int(args.ttl_seconds)),
            )
        else:
            url = mint_h5_task_link(
                case_id=case_id,
                lane=args.lane,
                slot=args.slot,
                external_userid=ext_uid,
                base_url=base,
                ttl_seconds=max(60, int(args.ttl_seconds)),
            )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
