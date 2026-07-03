#!/usr/bin/env python3
"""
WeCom Track A readiness — single deterministic operational report.

Orchestrates existing diagnostics only (no duplicated API logic).

Usage:
  PYTHONPATH=. python3 scripts/wecom_readiness.py
  PYTHONPATH=. python3 scripts/wecom_readiness.py --env-file .env.cloudrun
  PYTHONPATH=. python3 scripts/wecom_readiness.py --base-url https://your-service.run.app
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.wecom.diagnostics import (  # noqa: E402
    map_sync_msg_errcode,
    sync_msg_blocker_summary,
    sync_msg_errcode_causes,
    sync_msg_errcode_meaning,
    track_a_green_ready,
    track_a_ready,
)
from services.fiqa_api.wecom.intent import classify_wecom_intent  # noqa: E402
from services.fiqa_api.wecom.normalize import normalize_text_message  # noqa: E402
from services.fiqa_api.wecom.synthetic_fixtures import SYNTHETIC_ADD_CAR_WITH_PHONE  # noqa: E402
from services.fiqa_api.wecom.diagnostics import resolve_secret  # noqa: E402
from scripts.validate_wecom_gettoken import (  # noqa: E402
    CallbackProbeResult,
    CredentialReadiness,
    GettokenResult,
    check_credentials,
    fetch_gettoken,
    load_dotenv,
    probe_wecom_callback,
)
from scripts.validate_wecom_sync_msg import SyncMsgCheckResult, run_sync_msg_check  # noqa: E402

Status = Literal["PASS", "WARNING", "FAIL", "SKIP"]
ScoreItem = tuple[str, Status, float]


@dataclass(frozen=True)
class TrackAEngineering:
    callback: str
    normalize: str
    bridge: str
    active_case: str
    sync_msg: str


@dataclass(frozen=True)
class ReadinessReport:
    credentials: CredentialReadiness
    callback: CallbackProbeResult | None
    gettoken: GettokenResult | None
    sync_msg: SyncMsgCheckResult | None
    track_a: TrackAEngineering
    score_pct: int
    track_a_ready: bool
    track_a_green: bool
    stopped_early: str | None


def _score_weight(status: Status) -> float:
    if status == "PASS":
        return 1.0
    if status == "WARNING":
        return 0.5
    if status == "SKIP":
        return 0.0
    return 0.0


def _compute_score(items: list[ScoreItem]) -> int:
    if not items:
        return 0
    total = sum(weight for _, _, weight in items)
    earned = sum(_score_weight(status) * weight for _, status, weight in items)
    return round(100 * earned / total)


def _resolve_base_url(explicit: str | None) -> str:
    import os

    if explicit and explicit.strip():
        return explicit.strip().rstrip("/")
    for key in ("CLOUD_RUN_URL", "WECOM_CALLBACK_BASE_URL", "WECOM_BASE_URL"):
        val = (os.getenv(key) or "").strip()
        if val:
            return val.rstrip("/")
    return "http://localhost:8001"


def _check_normalize() -> Status:
    try:
        event = normalize_text_message(SYNTHETIC_ADD_CAR_WITH_PHONE)
        required = ("channel", "msg_id", "text", "event_type")
        if all(event.get(k) for k in required):
            return "PASS"
    except Exception:
        return "FAIL"
    return "FAIL"


def _check_bridge() -> Status:
    try:
        from services.fiqa_api.wecom.active_case_bridge import ingest_wecom_text_to_active_case  # noqa: F401

        intent = classify_wecom_intent(SYNTHETIC_ADD_CAR_WITH_PHONE["text"]["content"])
        if intent.intent:
            return "PASS"
    except Exception:
        return "FAIL"
    return "FAIL"


def _check_active_case_engineering() -> Status:
    try:
        from services.fiqa_api.inbox_triage.active_case_resolver import resolve_active_case_for_evidence  # noqa: F401

        return "PASS"
    except Exception:
        return "FAIL"


def _callback_overall(probe: CallbackProbeResult) -> Status:
    if probe.route_status != "PASS":
        return "FAIL"
    if probe.verify_status == "PASS" and probe.decrypt_status == "PASS":
        return "PASS"
    if probe.verify_status == "FAIL" or probe.decrypt_status == "FAIL":
        return "FAIL"
    return "WARNING"


def build_report(*, base_url: str, env_file: Path) -> ReadinessReport:
    import os

    credentials = check_credentials(env_file=env_file)
    callback_probe = probe_wecom_callback(base_url)

    gettoken_result: GettokenResult | None = None
    sync_msg_result: SyncMsgCheckResult | None = None
    stopped_early: str | None = None

    if callback_probe.route_status != "PASS":
        stopped_early = "callback route unreachable"
    else:
        corp_id = (os.getenv("WECOM_CORP_ID") or "").strip()
        secret_key, secret = resolve_secret()
        if corp_id and secret:
            gettoken_result = fetch_gettoken(
                corp_id=corp_id,
                secret=secret,
                secret_key=secret_key,
            )
            if gettoken_result.status == "PASS":
                sync_msg_result = run_sync_msg_check()

    cb_status = _callback_overall(callback_probe)
    norm_status = _check_normalize()
    bridge_status = _check_bridge()
    active_case_status = _check_active_case_engineering()
    sync_status: Status = (
        sync_msg_result.status
        if sync_msg_result is not None
        else ("SKIP" if stopped_early or gettoken_result is None or gettoken_result.status != "PASS" else "FAIL")
    )

    track_a = TrackAEngineering(
        callback=cb_status,
        normalize=norm_status,
        bridge=bridge_status,
        active_case=active_case_status,
        sync_msg=sync_status,
    )

    score_items: list[ScoreItem] = [
        ("cloudrun_env", credentials.cloudrun_env, 1),
        ("corp_id", credentials.callback_keys[0].status, 1),
        ("callback_token", credentials.callback_keys[1].status, 1),
        ("encoding_aes_key", credentials.callback_keys[2].status, 1),
        ("secret_class", credentials.secret_class_status, 1),
        ("callback_route", callback_probe.route_status, 2),
        ("callback_verify", callback_probe.verify_status, 2),
        ("callback_decrypt", callback_probe.decrypt_status, 2),
        ("gettoken", gettoken_result.status if gettoken_result else "SKIP", 3),
        ("sync_msg", sync_status, 4),
        ("track_normalize", norm_status, 1),
        ("track_bridge", bridge_status, 1),
        ("track_active_case", active_case_status, 1),
    ]
    score_pct = _compute_score(score_items)

    sm_code = sync_msg_result.errcode if sync_msg_result else None
    sm_count = sync_msg_result.message_count if sync_msg_result else 0
    ready = track_a_ready(sm_code) if sync_msg_result and sync_msg_result.status == "PASS" else False
    green = track_a_green_ready(sm_code, message_count=sm_count) if ready else False

    return ReadinessReport(
        credentials=credentials,
        callback=callback_probe,
        gettoken=gettoken_result,
        sync_msg=sync_msg_result,
        track_a=track_a,
        score_pct=score_pct,
        track_a_ready=ready,
        track_a_green=green,
        stopped_early=stopped_early,
    )


def _line(label: str, status: Status) -> None:
    print(f"{label}:")
    print(f"{status}")
    print()


def _print_section(title: str) -> None:
    print(title)
    print("-" * 32)
    print()


def _print_next_action_steps(errcode: int | None) -> None:
    code = int(errcode if errcode is not None else -1)
    if code == 48002:
        print("Go to:")
        print()
        print("企业微信")
        print()
        print("↓")
        print()
        print("微信客服")
        print()
        print("↓")
        print()
        print("API")
        print()
        print("↓")
        print()
        print("可调用接口的应用")
        print()
        print("Confirm:")
        print()
        print("CaseIQ AI Adapter")
        print()
        print("Then")
        print()
        print("↓")
        print()
        print("通过API管理微信客服账号")
        print()
        print("Confirm:")
        print()
        print("correct wk account")
        print()
        print("Then")
        print()
        print("↓")
        print()
        print("Copy")
        print()
        print("WECOM_KF_SECRET")
        print()
        print("Deploy")
        print()
        print("Run:")
        print()
        print("python scripts/validate_wecom_sync_msg.py")
        return

    diag = map_sync_msg_errcode(code if code >= 0 else None)
    print(diag.next_action)


def print_report(report: ReadinessReport, *, base_url: str) -> None:
    creds = report.credentials
    cb = report.callback
    gt = report.gettoken
    sm = report.sync_msg

    print("=" * 50)
    print("WeCom Readiness Report")
    print("=" * 50)
    print()

    _print_section("Environment")
    _line("CloudRun Env", creds.cloudrun_env)
    _line("Corp ID", creds.callback_keys[0].status)
    _line("Callback Token", creds.callback_keys[1].status)
    _line("EncodingAESKey", creds.callback_keys[2].status)
    _line("Secret Class", creds.secret_class_status)
    print("Using:")
    print(creds.resolved_secret_key or "(none)")
    print()
    kf_item = next((i for i in creds.secret_keys if i.key == "WECOM_KF_SECRET"), None)
    if kf_item:
        print("WECOM_KF_SECRET:")
        print(kf_item.detail)
        print()
    if creds.secret_class_status == "WARNING":
        print("Recommendation:")
        print("Use WECOM_KF_SECRET if available.")
        print()
    print("-" * 32)
    print()

    if cb is None:
        _print_section("Callback")
        print("Route:")
        print("SKIP")
        print()
    else:
        _print_section("Callback")
        _line("Route", cb.route_status)
        if cb.route_detail and cb.route_status != "PASS":
            print(f"Detail: {cb.route_detail}")
            print()
        _line("Verify", cb.verify_status)
        if cb.verify_detail and cb.verify_status != "PASS":
            print(f"Detail: {cb.verify_detail}")
            print()
        _line("Decrypt", cb.decrypt_status)
        if cb.decrypt_detail and cb.decrypt_status != "PASS":
            print(f"Detail: {cb.decrypt_detail}")
            print()
        print("-" * 32)
        print()

    if report.stopped_early:
        print("=" * 50)
        print("Overall Verdict")
        print("=" * 50)
        print()
        print("Track A")
        print()
        print("NOT READY")
        print()
        print("Reason:")
        print()
        print(report.stopped_early)
        print()
        print(f"Service base URL: {base_url}")
        print()
        blocker = sync_msg_blocker_summary(None)
        print("=" * 50)
        print("Today's Biggest Blocker")
        print("=" * 50)
        print()
        print("Callback route unreachable")
        print()
        print(blocker.category)
        print()
        print("Estimated remaining work")
        print()
        print(f"Admin: {blocker.admin_minutes}")
        print(f"Engineering: 0–1 days")
        print(f"Business risk: {blocker.business_risk}")
        print()
        return

    _print_section("Access Token")
    if gt is None:
        _line("gettoken", "SKIP")
    else:
        _line("gettoken", gt.status)
        if gt.status == "PASS":
            print("Token fingerprint:")
            print(f"{gt.secret_fingerprint}")
            print()
        elif gt.errcode is not None:
            print(f"errcode: {gt.errcode}")
            print(f"errmsg: {gt.errmsg}")
            print()
    print("-" * 32)
    print()

    if gt is not None and gt.status != "PASS":
        print("=" * 50)
        print("Overall Verdict")
        print("=" * 50)
        print()
        print("Track A")
        print()
        print("NOT READY")
        print()
        print("Reason:")
        print()
        print(f"gettoken {gt.status}")
        if gt.errcode == 40001:
            diag = map_sync_msg_errcode(40001)
            print()
            print(diag.next_action)
        blocker = sync_msg_blocker_summary(gt.errcode)
        print()
        print("=" * 50)
        print("Today's Biggest Blocker")
        print("=" * 50)
        print()
        print(str(gt.errcode or "gettoken failure"))
        print()
        print(blocker.category)
        print()
        print("Estimated remaining work")
        print()
        print(f"Admin: {blocker.admin_minutes}")
        print(f"Engineering: {blocker.engineering_days}")
        print(f"Business risk: {blocker.business_risk}")
        print()
        return

    _print_section("sync_msg")
    if sm is None:
        _line("Result", "SKIP")
    else:
        _line("Result", sm.status)
        if sm.errcode is not None:
            print(f"errcode:")
            print(sm.errcode)
            print()
        if sm.errmsg:
            print(f"errmsg: {sm.errmsg}")
            print()
        print("Meaning:")
        print()
        print(sync_msg_errcode_meaning(sm.errcode))
        print()
        if sm.status == "FAIL" and sm.errcode is not None:
            causes = sync_msg_errcode_causes(sm.errcode)
            if causes:
                print("Most likely causes:")
                print()
                for idx, cause in enumerate(causes, start=1):
                    print(f"[{idx}]")
                    print(cause.label)
                    print()
                print("Probability:")
                print()
                for cause in causes:
                    print(f"{cause.label}:")
                    print(f"{cause.probability_pct}%")
                    print()
        if sm.status == "PASS":
            print(f"message_count: {sm.message_count}")
            print()
    print("-" * 32)
    print()

    _print_section("Current Track A")
    _line("Callback", report.track_a.callback)
    _line("Normalize", report.track_a.normalize)
    _line("Bridge", report.track_a.bridge)
    _line("Active Case", report.track_a.active_case)
    _line("sync_msg", report.track_a.sync_msg)
    print("Overall:")
    print()
    print(f"{report.score_pct}%")
    print()
    print("Track A:")
    print("READY" if report.track_a_ready else "NOT READY")
    print()
    print("-" * 32)
    print()

    if sm is not None and sm.status == "FAIL":
        print("Next Action")
        print()
        _print_next_action_steps(sm.errcode)
        print()

    print("=" * 50)
    print("Overall Verdict")
    print("=" * 50)
    print()
    print("Track A")
    print()
    if report.track_a_green:
        print("GREEN — Track A Ready")
        print()
        print(f"sync_msg PASS with {sm.message_count if sm else 0} message(s) pulled.")
    elif report.track_a_ready:
        print("READY")
        print()
        print("Congratulations.")
        print("Track A is operational.")
        print("You can begin")
        print("WeCom → Active Case integration.")
    else:
        print("NOT READY")
        print()
        print("Reason:")
        print()
        if sm and sm.errcode is not None:
            print(sm.errcode)
            print()
            admin_codes = {48002, 48007, 60020, 95011, 95012}
            if sm.errcode in admin_codes:
                print("No engineering blocker detected.")
                print()
                print("Most likely admin configuration.")
        elif sm:
            print(sm.errmsg or "sync_msg check failed")
        else:
            print("sync_msg not run")
    print()

    blocker = sync_msg_blocker_summary(sm.errcode if sm else None)
    print("=" * 50)
    print("Today's Biggest Blocker")
    print("=" * 50)
    print()
    if report.track_a_ready:
        print("None — sync_msg permission works")
        print()
        print(blocker.category)
    elif sm and sm.errcode is not None:
        print(str(sm.errcode))
        print()
        print(blocker.category)
    elif report.stopped_early:
        print("Callback route unreachable")
        print()
        print("Infrastructure")
    else:
        print("Pending checks")
        print()
        print(blocker.category)
    print()
    print("Estimated remaining work")
    print()
    print(f"Admin: {blocker.admin_minutes}")
    print(f"Engineering: {blocker.engineering_days}")
    print(f"Business risk: {blocker.business_risk}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="WeCom Track A readiness report")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=REPO / ".env.cloudrun",
        help="Dotenv file to load (default: .env.cloudrun)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="API base URL for callback probe (default: CLOUD_RUN_URL or localhost:8001)",
    )
    args = parser.parse_args()

    load_dotenv(args.env_file)
    base_url = _resolve_base_url(args.base_url)
    report = build_report(base_url=base_url, env_file=args.env_file)
    print_report(report, base_url=base_url)

    if report.stopped_early:
        return 2
    if report.gettoken and report.gettoken.status != "PASS":
        return 1
    if report.sync_msg and report.sync_msg.status == "FAIL":
        return 1
    if report.sync_msg and report.sync_msg.status == "PASS":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
