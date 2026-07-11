#!/usr/bin/env python3
"""P19H-3f-2 deploy smoke — Add Car → Claim lane switch confirm card (QA Cloud SQL + API)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.demo_db_resolve import load_cloudrun_env_skip_db

load_cloudrun_env_skip_db()


os.environ["ENV"] = "prod"

from scripts.demo_db_resolve import apply_qa_postgres_env  # noqa: E402

apply_qa_postgres_env(for_write=True)

from services.fiqa_api.inbox_triage.case_store import (  # noqa: E402
    bind_case_channel_identity,
    save_case,
    update_case_workbench_flags,
)
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read  # noqa: E402
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_holding_ack,
    ingest_claim_lane_switch_choice,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message

START_MARKER = "【事故记录已开始 ✅】"
DEFER_MARKERS = ("先完成当前请求", "Let's finish your current request first")


def _suffix() -> str:
    return datetime.now(timezone.utc).strftime("3f2_ls_%H%M%S")


def _tag(case_id: str) -> None:
    update_case_workbench_flags(case_id, is_test=True)
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation, _persist_case_after_update

    row = _load_case_for_mutation(case_id)
    if row:
        row["demo_name"] = "p19h3f2_lane_switch_smoke"
        _persist_case_after_update(case_id, row)


def _api_headers() -> dict[str, str]:
    key = os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY", "")
    return {"X-Unified-Intake-Api-Key": key} if key else {}


def _api_get(path: str) -> tuple[int, dict | str]:
    import urllib.error
    import urllib.request

    base = os.environ.get("CHEN_KUI_CLOUD_API_URL", "https://fiqa-api-g7zatxrycq-uw.a.run.app")
    req = urllib.request.Request(f"{base}{path}", headers=_api_headers())
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def _text_msg(msg_id: str, content: str, *, ext: str, menu_id: str | None = None) -> dict:
    msg = {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": content},
    }
    if menu_id:
        msg["menu_id"] = menu_id
    return msg


def _triage_stub() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "Review.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def _save_add_car(ext: str) -> str:
    saved = save_case("add car smoke", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = str(saved["case_id"])
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    _tag(cid)
    return cid


def smoke_a_explicit_intent(suffix: str) -> dict:
    ext = f"wm_ls_a_{suffix}"
    add_car_id = _save_add_car(ext)
    result = ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"a1_{suffix}", "我现在要进行理赔", ext=ext)),
        classify_wecom_intent("我现在要进行理赔"),
    )
    reply = str(result.get("reply_text") or "")
    menu = result.get("menu_payload") or {}
    combined = reply + json.dumps(menu, ensure_ascii=False)
    return {
        "add_car_id": add_car_id,
        "outcome": result.get("active_case_outcome"),
        "case_created": result.get("case_created"),
        "has_confirm_copy": all(x in combined for x in ("事故/理赔记录", "暂停当前加车资料收集", "开始事故记录", "继续加车")),
        "no_start_card": START_MARKER not in combined,
        "no_deferral": not any(m in combined for m in DEFER_MARKERS),
        "pass": (
            result.get("active_case_outcome") == "claim_lane_switch_prompt"
            and result.get("case_created") is False
            and START_MARKER not in combined
            and not any(m in combined for m in DEFER_MARKERS)
        ),
    }


def smoke_b_confirm(suffix: str) -> dict:
    ext = f"wm_ls_b_{suffix}"
    add_car_id = _save_add_car(ext)
    ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"b0_{suffix}", "我要理赔", ext=ext)),
        classify_wecom_intent("我要理赔"),
    )
    confirm = ingest_claim_lane_switch_choice(
        normalize_text_message(_text_msg(f"b1_{suffix}", "开始事故记录", ext=ext))
    )
    claim_id = str(confirm.get("case_id") or "")
    claim = get_case_for_read(claim_id) or {}
    add_car = get_case_for_read(add_car_id) or {}
    reply = str(confirm.get("reply_text") or "")
    listed_status, listed = _api_get("/api/inbox/cases?limit=80")
    api_status, api_case = _api_get(f"/api/inbox/cases/{claim_id}")
    row = next((c for c in (listed.get("cases") or []) if c.get("case_id") == claim_id), None) if isinstance(listed, dict) else None
    in_queue = (
        isinstance(api_case, dict)
        and api_case.get("case_id") == claim_id
        and api_case.get("service_lane") == SERVICE_LANE_CLAIM
    )
    return {
        "add_car_id": add_car_id,
        "claim_id": claim_id,
        "add_car_preserved": bool(add_car),
        "claim_lane": claim.get("service_lane"),
        "start_card": START_MARKER in reply,
        "injury_menu": bool(confirm.get("menu_payload")),
        "in_default_queue": in_queue or row is not None,
        "pass": (
            confirm.get("case_created") is True
            and confirm.get("active_case_outcome") == "claim_start_card_sent"
            and START_MARKER in reply
            and bool(confirm.get("menu_payload"))
            and bool(add_car)
            and claim.get("service_lane") == SERVICE_LANE_CLAIM
            and (in_queue or row is not None)
        ),
    }


def smoke_c_cancel(suffix: str) -> dict:
    ext = f"wm_ls_c_{suffix}"
    add_car_id = _save_add_car(ext)
    ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"c0_{suffix}", "我要理赔", ext=ext)),
        classify_wecom_intent("我要理赔"),
    )
    cancel = ingest_claim_lane_switch_choice(
        normalize_text_message(_text_msg(f"c1_{suffix}", "继续加车", ext=ext))
    )
    reply = str(cancel.get("reply_text") or "")
    return {
        "add_car_id": add_car_id,
        "case_created": cancel.get("case_created"),
        "continue_copy": "继续完成加车资料" in reply,
        "no_start_card": START_MARKER not in reply,
        "pass": (
            cancel.get("case_created") is False
            and "继续完成加车资料" in reply
            and START_MARKER not in reply
        ),
    }


def smoke_d_ambiguous(suffix: str) -> dict:
    ext = f"wm_ls_d_{suffix}"
    _save_add_car(ext)
    text = "昨晚 Costco 被追尾了，后保险杠有点坏"
    result = ingest_claim_holding_ack(
        normalize_text_message(_text_msg(f"d1_{suffix}", text, ext=ext))
    )
    reply = str(result.get("reply_text") or "")
    return {
        "outcome": result.get("active_case_outcome"),
        "case_created": result.get("case_created"),
        "no_start_card": START_MARKER not in reply,
        "pass": (
            result.get("case_created") is False
            and result.get("active_case_outcome") == "claim_holding_ack"
            and START_MARKER not in reply
        ),
    }


def smoke_e_regression(suffix: str) -> dict:
    ext = f"wm_ls_e_{suffix}"
    solo = ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"e1_{suffix}", "我要理赔", ext=ext)),
        classify_wecom_intent("我要理赔"),
    )
    cfg = load_wecom_kf_config()

    def _dl(*_a, **_k):
        return WeComMediaDownloadResult(content=b"\xff\xd8\xff", content_type="image/jpeg", filename="photo.jpg")

    def _up(**_k):
        return {"storage_uri": "gs://smoke/x.jpg", "mime_type": "image/jpeg", "size_bytes": 3}

    photo = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"e_img_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": f"wm_ls_photo_{suffix}",
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": f"MEDIA_E_{suffix}"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    listed_status, listed = _api_get("/api/inbox/cases?limit=80")
    photo_rows = [
        c
        for c in (listed.get("cases") or [])
        if c.get("service_lane") == "wecom_media_intake"
    ] if isinstance(listed, dict) else []
    default_has_photo = any(
        c.get("service_lane") == "wecom_media_intake" for c in (listed.get("cases") or [])
    ) if isinstance(listed, dict) else False
    solo_reply = str(solo.get("reply_text") or "") + json.dumps(solo.get("menu_payload") or {}, ensure_ascii=False)
    return {
        "solo_start_card": START_MARKER in solo_reply,
        "solo_case_created": solo.get("case_created"),
        "photo_lane": photo.get("service_lane"),
        "photo_in_default_queue": default_has_photo,
        "pass": (
            solo.get("case_created") is True
            and START_MARKER in solo_reply
            and photo.get("service_lane") == "wecom_media_intake"
        ),
    }


def main() -> int:
    suffix = _suffix()
    health_status, health = _api_get("/health/live")
    ready_status, ready = _api_get("/readyz")
    version_status, version = _api_get("/version")

    results = {
        "suffix": suffix,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api": {
            "health_live": health_status,
            "readyz": ready_status,
            "version": version if isinstance(version, dict) else str(version)[:200],
        },
        "smoke_a_explicit_intent": smoke_a_explicit_intent(suffix),
        "smoke_b_confirm": smoke_b_confirm(suffix),
        "smoke_c_cancel": smoke_c_cancel(suffix),
        "smoke_d_ambiguous": smoke_d_ambiguous(suffix),
        "smoke_e_regression": smoke_e_regression(suffix),
    }
    results["all_pass"] = all(
        results[k].get("pass") for k in results if k.startswith("smoke_")
    ) and health_status == 200 and ready_status == 200

    out_dir = REPO / "docs" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"p19h3f2_smoke_run_{suffix}.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nWrote {out_path}")
    return 0 if results["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
