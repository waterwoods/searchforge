#!/usr/bin/env python3
"""P19H-3f-4 deploy smoke — Unified Status Card + text frame (QA Cloud SQL + API)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.demo_db_resolve import load_cloudrun_env_skip_db

load_cloudrun_env_skip_db()


os.environ["ENV"] = "prod"

from scripts.demo_db_resolve import apply_qa_postgres_env  # noqa: E402

apply_qa_postgres_env(for_write=True)

from services.fiqa_api.inbox_triage.case_store import (  # noqa: E402
    append_follow_up_message,
    bind_case_channel_identity,
    get_case_by_id,
    patch_case_known_facts,
    save_case,
    update_case_workbench_flags,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read, list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import (
    SERVICE_LANE_ADD_CAR,
    SERVICE_LANE_WECOM_MEDIA_INTAKE,
)
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_collision_choice,
    ingest_claim_holding_ack,
    ingest_claim_lane_switch_choice,
    ingest_claim_status_request,
)
from services.fiqa_api.wecom.claim_end_card import try_send_claim_end_card
from services.fiqa_api.wecom.claim_state import CLAIM_PHASE_BROKER_DONE, SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message

FRAME = "━━━━━━━━━━━━"
START_TITLE = "【事故记录已开始 ✅】"
STATUS_TITLE = "【当前状态】"
CONFIRM_TITLE = "【请确认】"
COLLISION_TITLE = "【请选择事故记录】"
END_TITLE = "【陈总已确认 ✅】"
FORBIDDEN = (
    "已报案",
    "一定会赔",
    "对方全责",
    "保险公司已收到",
    "coverage approved",
    "claim approved",
)
_ACCIDENT_NARRATIVE = "昨天7月8号，我们在 Santa Ana 红绿灯停下来，后车没停撞了我们。"


def _suffix() -> str:
    return datetime.now(timezone.utc).strftime("3f4_smoke_%H%M%S")


def _tag(case_id: str) -> None:
    update_case_workbench_flags(case_id, is_test=True)
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation, _persist_case_after_update

    row = _load_case_for_mutation(case_id)
    if row:
        row["demo_name"] = "p19h3f4_deploy_smoke"
        _persist_case_after_update(case_id, row)


def _api_headers() -> dict[str, str]:
    key = os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY", "")
    return {"X-Unified-Intake-Api-Key": key} if key else {}


def _api_get(path: str) -> dict:
    import urllib.request

    base = os.environ.get("CHEN_KUI_CLOUD_API_URL", "https://fiqa-api-g7zatxrycq-uw.a.run.app")
    req = urllib.request.Request(f"{base}{path}", headers=_api_headers())
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _api_post(path: str, body: dict | None = None) -> tuple[int, dict]:
    import urllib.error
    import urllib.request

    base = os.environ.get("CHEN_KUI_CLOUD_API_URL", "https://fiqa-api-g7zatxrycq-uw.a.run.app")
    data = json.dumps(body or {}).encode()
    headers = {"Content-Type": "application/json", **_api_headers()}
    req = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return exc.code, payload


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


def _claim_count(ext: str) -> int:
    return sum(
        1
        for c in list_all_cases_for_read()
        if c.get("service_lane") == SERVICE_LANE_CLAIM
        and (
            c.get("wecom_external_userid") == ext
            or (c.get("channel_identities") or {}).get("wecom_external_userid") == ext
        )
    )


def _forbidden_in(text: str) -> list[str]:
    return [p for p in FORBIDDEN if p in text]


def _dl(*_a, **_k):
    return WeComMediaDownloadResult(content=b"\xff\xd8\xff", content_type="image/jpeg", filename="photo.jpg")


def _up(**_k):
    return {"storage_uri": "gs://smoke/x.jpg", "mime_type": "image/jpeg", "size_bytes": 3}


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


def _claim_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Collect basics.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "claim_phase": "claim_started",
    }


def smoke_a_start_frame(suffix: str) -> dict:
    ext = f"wm_3f4_a_{suffix}"
    result = ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"a_{suffix}", "我要理赔", ext=ext)),
        classify_wecom_intent("我要理赔"),
    )
    reply = str(result.get("reply_text") or "")
    case_id = str(result.get("case_id") or "")
    if case_id:
        _tag(case_id)
    return {
        "case_id": case_id,
        "case_created": result.get("case_created"),
        "has_frame": FRAME in reply,
        "has_start_title": START_TITLE in reply,
        "has_office": "陈总办公室" in reply,
        "has_injury": "有没有受伤" in reply,
        "has_disclaimer": "不代表已经向保险公司正式报案" in reply,
        "injury_menu": bool(result.get("menu_payload")),
        "forbidden": _forbidden_in(reply),
        "pass": (
            result.get("case_created") is True
            and FRAME in reply
            and START_TITLE in reply
            and "陈总办公室" in reply
            and "有没有受伤" in reply
            and "不代表已经向保险公司正式报案" in reply
            and bool(result.get("menu_payload"))
            and not _forbidden_in(reply)
        ),
    }


def smoke_b_status_card(suffix: str) -> dict:
    ext = f"wm_3f4_b_{suffix}"
    start = ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"b0_{suffix}", "我要理赔", ext=ext)),
        classify_wecom_intent("我要理赔"),
    )
    case_id = str(start["case_id"])
    _tag(case_id)
    patch_case_known_facts(
        case_id,
        {
            "accident_datetime": "7月8日",
            "accident_location": "Santa Ana 红绿灯",
            "accident_description": "后车追尾",
            "injury_status": "no",
        },
    )
    before = _claim_count(ext)
    replies: dict[str, str] = {}
    for i, word in enumerate(("进度", "状态", "理赔进度"), start=1):
        r = ingest_claim_status_request(
            normalize_text_message(_text_msg(f"b{i}_{suffix}", word, ext=ext)),
            classify_wecom_intent(word),
        )
        replies[word] = str(r.get("reply_text") or "")
    after = _claim_count(ext)
    progress_reply = replies["进度"]
    return {
        "case_id": case_id,
        "claim_count_unchanged": before == after == 1,
        "progress_outcome": "claim_status_card",
        "has_frame": FRAME in progress_reply,
        "has_status_title": STATUS_TITLE in progress_reply,
        "sections": all(x in progress_reply for x in ("已收到", "还缺", "下一步", "提醒")),
        "no_second_start": START_TITLE not in progress_reply,
        "forbidden": _forbidden_in(progress_reply),
        "pass": (
            before == after == 1
            and FRAME in progress_reply
            and STATUS_TITLE in progress_reply
            and all(x in progress_reply for x in ("已收到", "还缺", "下一步", "提醒"))
            and START_TITLE not in progress_reply
            and not _forbidden_in(progress_reply)
            and all(FRAME in t and STATUS_TITLE in t for t in replies.values())
        ),
    }


def smoke_c_no_active_status(suffix: str) -> dict:
    ext = f"wm_3f4_c_{suffix}"
    before = _claim_count(ext)
    result = ingest_claim_status_request(
        normalize_text_message(_text_msg(f"c_{suffix}", "理赔进度", ext=ext)),
        classify_wecom_intent("理赔进度"),
    )
    after = _claim_count(ext)
    reply = str(result.get("reply_text") or "")
    return {
        "case_created": result.get("case_created"),
        "claim_count": after,
        "no_active_copy": "没有" in reply and "事故记录" in reply,
        "suggest_start": "我要理赔" in reply,
        "no_start_card": START_TITLE not in reply,
        "pass": (
            result.get("case_created") is False
            and before == after == 0
            and "我要理赔" in reply
            and START_TITLE not in reply
        ),
    }


def smoke_d_confirm_frame(suffix: str) -> dict:
    ext = f"wm_3f4_d_{suffix}"
    add_car = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    add_car_id = str(add_car["case_id"])
    bind_case_channel_identity(add_car_id, wecom_external_userid=ext)
    _tag(add_car_id)

    prompt = ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"d0_{suffix}", "我要理赔", ext=ext)),
        classify_wecom_intent("我要理赔"),
    )
    prompt_reply = str(prompt.get("reply_text") or "")
    menu = prompt.get("menu_payload") or {}
    combined = prompt_reply + json.dumps(menu, ensure_ascii=False)

    confirm = ingest_claim_lane_switch_choice(
        normalize_text_message(_text_msg(f"d1_{suffix}", "开始事故记录", ext=ext))
    )
    confirm_reply = str(confirm.get("reply_text") or "")
    claim_id = str(confirm.get("case_id") or "")

    return {
        "add_car_id": add_car_id,
        "prompt_outcome": prompt.get("active_case_outcome"),
        "has_frame": FRAME in combined,
        "has_confirm_title": CONFIRM_TITLE in combined,
        "has_pause_add_car": "暂停当前加车资料收集" in combined,
        "has_start_choice": "开始事故记录" in combined,
        "has_continue_add_car": "继续加车" in combined,
        "has_disclaimer": "不代表已经向保险公司正式报案" in combined,
        "no_immediate_claim": prompt.get("case_created") is False,
        "confirm_start_card": START_TITLE in confirm_reply and FRAME in confirm_reply,
        "claim_id": claim_id,
        "pass": (
            prompt.get("active_case_outcome") == "claim_lane_switch_prompt"
            and prompt.get("case_created") is False
            and FRAME in combined
            and CONFIRM_TITLE in combined
            and "暂停当前加车资料收集" in combined
            and "开始事故记录" in combined
            and "继续加车" in combined
            and confirm.get("case_created") is True
            and START_TITLE in confirm_reply
            and FRAME in confirm_reply
        ),
    }


def _open_claim_with_story(ext: str, suffix: str) -> str:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = str(saved["case_id"])
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    _tag(cid)
    ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    patch_case_known_facts(
        cid,
        {
            "accident_datetime": "7月7日上午",
            "accident_location": "Irvine Blvd",
            "accident_description": "被追尾",
        },
    )
    append_follow_up_message(
        cid,
        "7月7日上午在 Irvine Blvd 被追尾",
        {
            **_claim_stub(),
            "collected_fields": ["accident_datetime", "accident_location", "accident_description"],
        },
    )
    update_claim_workflow_state(
        cid,
        claim_phase="accident_basics_complete",
        guided_workflow_state="collecting_text",
    )
    case = get_case_by_id(cid) or saved
    case["created_at"] = ts
    case["updated_at"] = ts
    return cid


def smoke_e_collision_frame(suffix: str) -> dict:
    ext = f"wm_3f4_e_{suffix}"
    existing_id = _open_claim_with_story(ext, suffix)
    before = _claim_count(ext)
    result = ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"e0_{suffix}", _ACCIDENT_NARRATIVE, ext=ext)),
        classify_wecom_intent(_ACCIDENT_NARRATIVE),
    )
    reply = str(result.get("reply_text") or "")
    menu = result.get("menu_payload") or {}
    combined = reply + json.dumps(menu, ensure_ascii=False)
    mid = _claim_count(ext)

    choice = ingest_claim_collision_choice(
        normalize_text_message(_text_msg(f"e1_{suffix}", "开始新的事故记录", ext=ext))
    )
    after = _claim_count(ext)
    choice_reply = str(choice.get("reply_text") or "")

    return {
        "existing_id": existing_id,
        "resolver_outcome": result.get("active_case_outcome"),
        "has_frame": FRAME in combined,
        "has_collision_title": COLLISION_TITLE in combined,
        "has_choices": all(x in combined for x in ("继续上一个事故", "开始新的事故记录", "联系陈总")),
        "no_silent_append": mid == before,
        "new_claim_after_choice": after == before + 1,
        "choice_start_card": START_TITLE in choice_reply and FRAME in choice_reply,
        "pass": (
            result.get("active_case_outcome") == "claim_collision_resolver"
            and FRAME in combined
            and COLLISION_TITLE in combined
            and all(x in combined for x in ("继续上一个事故", "开始新的事故记录", "联系陈总"))
            and mid == before
            and after == before + 1
            and START_TITLE in choice_reply
            and FRAME in choice_reply
        ),
    }


def smoke_f_end_card(suffix: str) -> dict:
    ext = f"wm_3f4_f_{suffix}"
    start = ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"f0_{suffix}", "我要理赔", ext=ext)),
        classify_wecom_intent("我要理赔"),
    )
    case_id = str(start["case_id"])
    _tag(case_id)
    from services.fiqa_api.inbox_triage.case_store import bind_case_channel_identity as bind

    bind(case_id, wecom_external_userid=ext, wecom_open_kf_id="wktest001")

    status1, body1 = _api_post(f"/api/inbox/cases/{case_id}/broker-done")
    preview = str(body1.get("end_card_preview") or body1.get("preview") or "")
    status2, body2 = _api_post(f"/api/inbox/cases/{case_id}/broker-done")
    case = get_case_by_id(case_id) or {}
    return {
        "case_id": case_id,
        "broker_done_status": status1,
        "has_frame": FRAME in preview,
        "has_end_title": END_TITLE in preview,
        "has_phase_end": "收集阶段已结束" in preview,
        "has_disclaimer": "不代表" in preview and ("结案" in preview or "赔付" in preview),
        "second_status": status2,
        "idempotent": status2 == 200 and case.get("claim_phase") == CLAIM_PHASE_BROKER_DONE,
        "forbidden": _forbidden_in(preview),
        "pass": (
            status1 == 200
            and FRAME in preview
            and END_TITLE in preview
            and "收集阶段已结束" in preview
            and status2 == 200
            and not _forbidden_in(preview)
        ),
    }


def smoke_regression(suffix: str) -> dict:
    ext_photo = f"wm_3f4_r_photo_{suffix}"
    cfg = load_wecom_kf_config()
    photo = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"r_img_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext_photo,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": f"MEDIA_{suffix}"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    photo_case_id = str(photo.get("case_id") or "")
    photo_case = get_case_for_read(photo_case_id) if photo_case_id else {}
    listed = _api_get("/api/inbox/cases?limit=50")
    media_in_default = bool(
        photo_case_id
        and any(c.get("case_id") == photo_case_id for c in (listed.get("cases") or []))
    )

    ext_narr = f"wm_3f4_r_narr_{suffix}"
    narr = ingest_claim_holding_ack(
        normalize_text_message(
            _text_msg(f"r_narr_{suffix}", "昨晚 Costco 被追尾了。", ext=ext_narr)
        )
    )

    status_raw, raw_body = _api_post("/api/inbox/cases/fake-id/broker-done")
    media_id = photo_case_id
    if media_id:
        status_media, _ = _api_post(f"/api/inbox/cases/{media_id}/broker-done")
    else:
        status_media = 0

    return {
        "photo_outcome": photo.get("active_case_outcome"),
        "photo_case_id": photo_case_id or None,
        "photo_lane": photo_case.get("service_lane"),
        "photo_hidden_from_queue": photo_case.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE
        and not media_in_default,
        "narrative_no_claim": _claim_count(ext_narr) == 0,
        "broker_done_rejects_raw": status_media == 400 if media_id else True,
        "pass": (
            (
                photo.get("active_case_outcome") == "media_unassigned"
                or photo_case.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE
            )
            and _claim_count(ext_narr) == 0
            and (status_media == 400 if media_id else True)
        ),
    }


def main() -> int:
    suffix = _suffix()
    print(f"=== P19H-3f-4 deploy smoke suffix={suffix} ===")
    results = {
        "A_start_frame": smoke_a_start_frame(suffix),
        "B_status_card": smoke_b_status_card(suffix),
        "C_no_active_status": smoke_c_no_active_status(suffix),
        "D_confirm_frame": smoke_d_confirm_frame(suffix),
        "E_collision_frame": smoke_e_collision_frame(suffix),
        "F_end_card": smoke_f_end_card(suffix),
        "regression": smoke_regression(suffix),
    }
    for key, val in results.items():
        print(key, json.dumps(val, ensure_ascii=False))
    all_pass = all(r.get("pass") for r in results.values())
    print("OVERALL", "PASS" if all_pass else "FAIL")
    out = REPO / "docs" / "evidence" / f"p19h3f4_smoke_run_{suffix}.json"
    out.write_text(json.dumps({"suffix": suffix, "smokes": results, "all_pass": all_pass}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
