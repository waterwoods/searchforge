#!/usr/bin/env python3
"""
Prepare a clean local Unified Intake founder-demo queue.

This keeps the founder demo repeatable without pretending the queue is live inbox data.
It resets the local case store, seeds a narrow demo-safe case mix, and prints a short summary.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final

from services.fiqa_api.inbox_triage.case_store import (
    add_case_note,
    save_case,
    update_case_follow_up,
    update_case_status,
)
from services.fiqa_api.inbox_triage.triage import triage_message


REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
DEFAULT_STORE_PATH: Final[Path] = REPO_ROOT / "data" / "unified_intake_cases.json"


@dataclass(frozen=True)
class DemoSeed:
    label: str
    text: str
    status: str
    waiting_on: str
    next_contact_by_offset_days: int
    note: str


DEMO_SEEDS: Final[list[DemoSeed]] = [
    DemoSeed(
        label="Cancellation risk",
        text="Carrier notice: Your policy will be cancelled due to non-payment. 客户说这个是不是今天一定要处理？",
        status="reviewing",
        waiting_on="broker",
        next_contact_by_offset_days=0,
        note="Client is worried coverage may stop today; call after confirming balance due.",
    ),
    DemoSeed(
        label="Missing document follow-up",
        text="UW follow up - need dec page + garaging proof. 客户说上周发过了",
        status="waiting_client",
        waiting_on="client",
        next_contact_by_offset_days=1,
        note="Client said they can resend declaration page and garaging proof tomorrow morning.",
    ),
    DemoSeed(
        label="Add-car quote request",
        text="客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价",
        status="reviewing",
        waiting_on="broker",
        next_contact_by_offset_days=0,
        note="Same-day quote if VIN and driver details come back before end of day.",
    ),
    DemoSeed(
        label="Premium review",
        text="客户说这个月保费太高了，能不能看看怎么降一点",
        status="waiting_client",
        waiting_on="client",
        next_contact_by_offset_days=2,
        note="Waiting on latest bill and declaration page before reviewing adjustment options.",
    ),
    DemoSeed(
        label="DMV / SR-22 help",
        text="DMV信说要 SR-22 proof 才能 clear suspension，这个要带什么？",
        status="reviewing",
        waiting_on="broker",
        next_contact_by_offset_days=1,
        note="Confirm whether DMV wants SR-22 filing proof before telling client what to bring.",
    ),
    DemoSeed(
        label="Payment failed / lapse risk",
        text="AutoPay failed again, please update card to avoid interruption in coverage",
        status="reviewing",
        waiting_on="broker",
        next_contact_by_offset_days=0,
        note="Same-day payment fix; client may not have seen carrier notice yet.",
    ),
    DemoSeed(
        label="Remove car",
        text="客户卖掉旧车了，想把2014 Honda Accord从保单拿掉",
        status="reviewing",
        waiting_on="broker",
        next_contact_by_offset_days=0,
        note="Confirm sale date and remove vehicle; check if replacement car needs adding.",
    ),
    DemoSeed(
        label="English notice + Chinese confusion",
        text="客户问：这个英文 notice 说 payment failed，我现在怎么办？",
        status="reviewing",
        waiting_on="broker",
        next_contact_by_offset_days=0,
        note="Client confused by English carrier notice; draft reply in Chinese.",
    ),
    DemoSeed(
        label="Declaration page missing",
        text="客户发来carrier email，说 declaration page missing，他问这个什么意思",
        status="waiting_client",
        waiting_on="client",
        next_contact_by_offset_days=1,
        note="Explain declaration page = 保单首页; client will resend.",
    ),
    DemoSeed(
        label="Chinese cancellation summary",
        text="保险公司说我的保单7天后要cancel",
        status="reviewing",
        waiting_on="broker",
        next_contact_by_offset_days=0,
        note="Client pasted carrier summary; confirm exact deadline and balance due.",
    ),
    DemoSeed(
        label="Claim intake / accident first response",
        text="刚出事故了，要收集什么？",
        status="reviewing",
        waiting_on="broker",
        next_contact_by_offset_days=0,
        note="First-step guidance given; confirm accident details, photos, other driver info.",
    ),
    DemoSeed(
        label="Messy-user: hit-and-run panic",
        text="刚撞了，对方跑了，我现在先干嘛",
        status="reviewing",
        waiting_on="broker",
        next_contact_by_offset_days=0,
        note="Adversarial C1: ultra-short, panic; system routes to claim_intake.",
    ),
    DemoSeed(
        label="Mixed-intent: claim + payment notice",
        text="出事了要拍什么，还有这个payment failed通知什么意思",
        status="reviewing",
        waiting_on="broker",
        next_contact_by_offset_days=0,
        note="MI-CL2: claim prioritized; accident first-step + payment context.",
    ),
]


def store_path() -> Path:
    raw_path = (os.getenv("UNIFIED_INTAKE_CASES_PATH") or "").strip()
    if not raw_path:
        return DEFAULT_STORE_PATH
    path = Path(raw_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def iso_date(days_from_today: int) -> str:
    today = datetime.now(timezone.utc).date()
    return (today + timedelta(days=days_from_today)).isoformat()


def reset_case_store(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cases": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    path = store_path()
    reset_case_store(path)

    created_cases: list[dict] = []
    for seed in DEMO_SEEDS:
        created = save_case(seed.text, triage_message(seed.text))
        updated = update_case_status(created["case_id"], seed.status) or created
        updated = update_case_follow_up(
            updated["case_id"],
            seed.waiting_on,
            iso_date(seed.next_contact_by_offset_days),
        ) or updated
        updated = add_case_note(updated["case_id"], seed.note) or updated
        created_cases.append(updated)

    attention_now = sum(1 for case in created_cases if case["urgency"] in {"critical", "high"} or case["waiting_on"] == "broker")
    waiting_client = sum(1 for case in created_cases if case["waiting_on"] == "client")
    print(f"Founder demo queue prepared at {path}")
    print(f"Seeded cases: {len(created_cases)}")
    print(f"Needs attention now: {attention_now}")
    print(f"Waiting on client: {waiting_client}")
    print("Strongest route: cancellation risk -> reopen missing document -> add-car or premium review")
    print("Queue now includes: cancellation, missing doc, add car, premium review, DMV/SR-22, payment failed, remove car, English+Chinese confusion, dec page, Chinese cancellation, claim intake, messy-user (C1), mixed-intent (MI-CL2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
