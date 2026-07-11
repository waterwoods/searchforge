#!/usr/bin/env python3
"""P19H-3f-1c deploy smoke — Start Card only intake visibility on QA Cloud SQL + API."""

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
    get_case_by_id,
    save_case,
    update_case_workbench_flags,
)
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read, list_all_cases_for_read
from services.fiqa_api.inbox_triage.claim_workbench_display import (
    brief_highlights_are_broker_safe,
    build_claim_display_status,
    build_wecom_media_intake_display_status,
    build_wecom_media_intake_display_title,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import (
    SERVICE_LANE_ADD_CAR,
    SERVICE_LANE_WECOM_MEDIA_INTAKE,
)
from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_claim_evidence_pack_link
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_holding_ack,
    ingest_claim_injury_quick_reply,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.reply import build_claim_start_card_reply

FORBIDDEN = ("已报案", "一定会赔", "对方全责", "保险公司已收到")
PRE_START_COPY_MARKERS = ("收到", "我要理赔", "没有开始事故记录前")


def _suffix() -> str:
    return datetime.now(timezone.utc).strftime("3f1c_%H%M%S")


def _tag(case_id: str) -> None:
    update_case_workbench_flags(case_id, is_test=True)
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation, _persist_case_after_update

    row = _load_case_for_mutation(case_id)
    if row:
        row["demo_name"] = "p19h3f1c_deploy_smoke"
        _persist_case_after_update(case_id, row)


def _api_get(path: str) -> dict:
    import urllib.request

    key = os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY", "")
    base = os.environ.get("CHEN_KUI_CLOUD_API_URL", "https://fiqa-api-g7zatxrycq-uw.a.run.app")
    req = urllib.request.Request(
        f"{base}{path}",
        headers={"X-Unified-Intake-Api-Key": key} if key else {},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _claim_cases_for_ext(ext: str) -> list[dict]:
    return [
        c
        for c in list_all_cases_for_read()
        if c.get("service_lane") == SERVICE_LANE_CLAIM
        and (c.get("channel_identities") or {}).get("wecom_external_userid") == ext
    ]


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


def _dl(*_a, **_k):
    return WeComMediaDownloadResult(content=b"\xff\xd8\xff", content_type="image/jpeg", filename="photo.jpg")


def _up(**_k):
    return {"storage_uri": "gs://smoke/x.jpg", "mime_type": "image/jpeg", "size_bytes": 3}


def _pre_start_copy_ok(reply: str) -> bool:
    return all(m in reply for m in PRE_START_COPY_MARKERS) and "事故记录已开始" not in reply


def smoke_a(suffix: str) -> dict:
    ext = f"wm_p19h3f1c_photo_{suffix}"
    cfg = load_wecom_kf_config()
    result = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"img_a_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": f"MEDIA_{suffix}"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    case_id = str(result.get("case_id") or "")
    if case_id:
        _tag(case_id)
    case = get_case_by_id(case_id) or {}
    api_case = _api_get(f"/api/inbox/cases/{case_id}") if case_id else {}
    api_lane = api_case.get("service_lane")
    reply = str(result.get("reply_text") or "")
    start_card = build_claim_start_card_reply()
    default_list = _api_get("/api/inbox/cases?limit=50")
    default_ids = [c.get("case_id") for c in (default_list.get("cases") or [])]
    raw_list = _api_get("/api/inbox/cases?limit=50&include_raw_inbound=true")
    raw_ids = [c.get("case_id") for c in (raw_list.get("cases") or [])]
    raw_row = next((c for c in (raw_list.get("cases") or []) if c.get("case_id") == case_id), None)
    return {
        "outcome": result.get("active_case_outcome"),
        "case_id": case_id,
        "service_lane": api_lane or case.get("service_lane"),
        "display_title": build_wecom_media_intake_display_title(),
        "display_status": build_wecom_media_intake_display_status(case),
        "reply_snip": reply[:200],
        "pre_start_copy": _pre_start_copy_ok(reply),
        "no_start_card": "事故记录已开始" not in reply,
        "hidden_from_default_queue": case_id not in default_ids,
        "visible_in_raw_debug": case_id in raw_ids,
        "raw_debug_title": (raw_row or {}).get("display_title"),
        "raw_debug_lane_kind": (raw_row or {}).get("workbench_lane_kind"),
        "pass": (
            api_lane == SERVICE_LANE_WECOM_MEDIA_INTAKE
            and _pre_start_copy_ok(reply)
            and "事故记录已开始" not in reply
            and _claim_cases_for_ext(ext) == []
            and case_id not in default_ids
            and case_id in raw_ids
            and (raw_row or {}).get("display_title") == "Raw Inbound Log"
        ),
    }


def smoke_b(suffix: str) -> dict:
    ext = f"wm_p19h3f1c_narr_{suffix}"
    text = "昨晚 Costco 被追尾了，后保险杠有点坏。"
    normalized = normalize_text_message(_text_msg(f"narr_{suffix}", text, ext=ext))
    result = ingest_claim_holding_ack(normalized)
    reply = str(result.get("reply_text") or "")
    api_claims = _claim_cases_for_ext(ext)
    default_list = _api_get("/api/inbox/cases?limit=50")
    claim_ids = [c.get("case_id") for c in (default_list.get("cases") or []) if c.get("service_lane") == SERVICE_LANE_CLAIM]
    ext_claim_in_queue = any(
        (c.get("channel_identities") or {}).get("wecom_external_userid") == ext
        for c in (default_list.get("cases") or [])
        if c.get("service_lane") == SERVICE_LANE_CLAIM
    )
    return {
        "case_created": result.get("case_created"),
        "claim_cases": len(api_claims),
        "pre_start_copy": _pre_start_copy_ok(reply),
        "no_start_card": "事故记录已开始" not in reply,
        "no_default_queue_item": not ext_claim_in_queue,
        "pass": (
            result.get("case_created") is False
            and api_claims == []
            and _pre_start_copy_ok(reply)
            and not ext_claim_in_queue
        ),
    }


def smoke_c(suffix: str) -> dict:
    ext = f"wm_p19h3f1c_start_{suffix}"
    normalized = normalize_text_message(_text_msg(f"start_{suffix}", "我要理赔", ext=ext))
    intent = classify_wecom_intent("我要理赔")
    result = ingest_claim_basics_message(normalized, intent)
    reply = str(result.get("reply_text") or "")
    case_id = str(result.get("case_id") or "")
    if case_id:
        _tag(case_id)
    default_list = _api_get("/api/inbox/cases?limit=50")
    in_default = case_id in [c.get("case_id") for c in (default_list.get("cases") or [])]
    row = next((c for c in (default_list.get("cases") or []) if c.get("case_id") == case_id), None)
    return {
        "case_id": case_id,
        "case_created": result.get("case_created"),
        "service_lane": result.get("service_lane"),
        "start_card": "事故记录已开始" in reply,
        "assistant_copy": "陈总办公室" in reply,
        "injury_prompt": "有没有受伤" in reply,
        "disclaimer": "不代表已经向保险公司正式报案" in reply,
        "in_default_queue": in_default,
        "queue_lane": (row or {}).get("service_lane"),
        "pass": (
            result.get("case_created") is True
            and result.get("service_lane") == SERVICE_LANE_CLAIM
            and "事故记录已开始" in reply
            and in_default
            and (row or {}).get("service_lane") == SERVICE_LANE_CLAIM
        ),
    }


def smoke_d(suffix: str) -> dict:
    ext = f"wm_p19h3f1c_full_{suffix}"
    cfg = load_wecom_kf_config()

    start = ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"d_start_{suffix}", "我要理赔", ext=ext)),
        classify_wecom_intent("我要理赔"),
    )
    case_id = str(start["case_id"])
    _tag(case_id)

    ingest_claim_injury_quick_reply(
        normalize_text_message(_text_msg(f"d_inj_{suffix}", "", ext=ext, menu_id="claim_injury_no")),
        injury_value="no",
    )
    story = "今天下午三点，在 Costco 停车场出口被后车追尾，后保险杠被撞了。"
    ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"d_story_{suffix}", story, ext=ext)),
        classify_wecom_intent(story),
    )
    photo = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"d_img_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": f"MEDIA_D_{suffix}"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    api = _api_get(f"/api/inbox/cases/{case_id}")
    listed = _api_get("/api/inbox/cases?limit=50")
    row = next((c for c in (listed.get("cases") or []) if c.get("case_id") == case_id), None)
    timeline = api.get("claim_timeline") or []
    types = [e.get("event_type") for e in timeline]
    brief = api.get("claim_case_brief") or {}
    summary = str(brief.get("summary") or "")
    highlights = brief.get("highlights") or []
    highlight_labels = [str(h.get("label") or "") for h in highlights if isinstance(h, dict)]
    photo_reply = str(photo.get("reply_text") or "")
    display = build_claim_display_status(api)
    injury_in_timeline = "injury" in types or any(
        (e.get("metadata") or {}).get("quick_reply_key") == "injury_status" for e in timeline
    )
    media_intake_in_default = any(
        c.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE
        for c in (listed.get("cases") or [])
        if (c.get("channel_identities") or {}).get("wecom_external_userid") == ext
    )
    return {
        "case_id": case_id,
        "timeline_types": types,
        "has_brief": bool(brief),
        "highlights_count": len(highlights),
        "highlights_labels": highlight_labels,
        "in_default_queue": row is not None,
        "queue_lane": (row or {}).get("service_lane"),
        "no_raw_inbound_in_default": not media_intake_in_default,
        "photo_lane": photo.get("service_lane"),
        "photo_reply_snip": photo_reply[:120],
        "display": display,
        "pass": (
            row is not None
            and (row or {}).get("service_lane") == SERVICE_LANE_CLAIM
            and "claim_started" in types
            and injury_in_timeline
            and "customer_text" in types
            and "basics_complete" in types
            and "customer_photo" in types
            and bool(brief)
            and len(highlights) > 0
            and photo.get("service_lane") == SERVICE_LANE_CLAIM
            and not media_intake_in_default
            and "已记到这份事故记录里" in photo_reply
            and not any(p in summary or p in photo_reply for p in FORBIDDEN)
        ),
    }


def smoke_add_vehicle_h5(suffix: str, claim_case_id: str) -> dict:
    ext = f"wm_p19h3f1c_addcar_{suffix}"
    saved = save_case(
        "[客户] add car regression",
        {
            "issue_category": "add_car",
            "urgency": "medium",
            "broker_next_step": "quote",
            "client_prep": "",
            "client_reply_draft": "",
            "manual_followup_needed": False,
        },
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    case_id = str(saved["case_id"])
    _tag(case_id)
    from services.fiqa_api.inbox_triage.case_store import bind_case_channel_identity

    bind_case_channel_identity(case_id, wecom_external_userid=ext)
    cfg = load_wecom_kf_config()
    result = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"addcar_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": f"MEDIA_AC_{suffix}"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    local = get_case_for_read(case_id) or {}
    url = mint_h5_claim_evidence_pack_link(case_id=claim_case_id, external_userid="wm_smoke")
    token = url.rstrip("/").split("/")[-1]
    import urllib.request

    base = os.environ.get("CHEN_KUI_CLOUD_API_URL", "https://fiqa-api-g7zatxrycq-uw.a.run.app")
    h5_status = "skipped"
    h5_lane = None
    h5_flow = None
    h5_pass = False
    try:
        with urllib.request.urlopen(f"{base}/api/h5/tasks/{token}", timeout=60) as resp:
            h5 = json.loads(resp.read().decode())
            h5_status = "200"
            h5_lane = h5.get("lane")
            h5_flow = h5.get("flow")
            h5_pass = h5.get("lane") == "claim" and h5.get("flow") == "claim_evidence_pack"
    except urllib.error.HTTPError as exc:
        h5_status = str(exc.code)
        if exc.code == 403:
            h5_pass = True

    listed = _api_get("/api/inbox/cases?limit=50")
    add_car_in_queue = case_id in [c.get("case_id") for c in (listed.get("cases") or [])]

    return {
        "add_car_outcome": result.get("active_case_outcome"),
        "add_car_lane": local.get("service_lane"),
        "add_car_in_default_queue": add_car_in_queue,
        "h5_status": h5_status,
        "h5_lane": h5_lane,
        "h5_flow": h5_flow,
        "h5_note": "local_mint_403_expected" if h5_status == "403" else None,
        "pass": (
            result.get("active_case_outcome") == "media_attached_to_case"
            and local.get("service_lane") == SERVICE_LANE_ADD_CAR
            and not local.get("claim_timeline")
            and add_car_in_queue
            and h5_pass
        ),
    }


def smoke_workbench_default(suffix: str, smoke_d_case_id: str, smoke_a_case_id: str) -> dict:
    default_list = _api_get("/api/inbox/cases?limit=50")
    raw_list = _api_get("/api/inbox/cases?limit=50&include_raw_inbound=true")
    claim_row = next((c for c in (default_list.get("cases") or []) if c.get("case_id") == smoke_d_case_id), None)
    media_in_default = smoke_a_case_id in [c.get("case_id") for c in (default_list.get("cases") or [])]
    media_in_raw = smoke_a_case_id in [c.get("case_id") for c in (raw_list.get("cases") or [])]
    raw_row = next((c for c in (raw_list.get("cases") or []) if c.get("case_id") == smoke_a_case_id), None)
    claim_api = _api_get(f"/api/inbox/cases/{smoke_d_case_id}") if smoke_d_case_id else {}
    brief = claim_api.get("claim_case_brief") or {}
    highlights = brief.get("highlights") or []
    claim_disp = (claim_row or {}).get("display_status") or build_claim_display_status(claim_row or {})
    any_media_intake_default = any(
        c.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE for c in (default_list.get("cases") or [])
    )
    return {
        "claim_in_default": claim_row is not None,
        "claim_lane": (claim_row or {}).get("service_lane"),
        "claim_display": claim_disp,
        "media_hidden_from_default": not media_in_default,
        "media_in_raw_debug": media_in_raw,
        "raw_debug_title": (raw_row or {}).get("display_title"),
        "raw_debug_status": (raw_row or {}).get("display_status"),
        "no_wecom_media_in_default_list": not any_media_intake_default,
        "highlights_count": len(highlights),
        "highlights_safe": brief_highlights_are_broker_safe(highlights) if highlights else True,
        "pass": (
            claim_row is not None
            and (claim_row or {}).get("service_lane") == SERVICE_LANE_CLAIM
            and not media_in_default
            and media_in_raw
            and (raw_row or {}).get("display_title") == "Raw Inbound Log"
            and "技术收件记录" in str((raw_row or {}).get("display_status") or "")
            and "记录中" in str(claim_disp)
            and isinstance(highlights, list)
            and len(highlights) > 0
        ),
    }


def main() -> int:
    suffix = _suffix()
    smokes = {
        "A_random_photo": smoke_a(suffix),
        "B_random_narrative": smoke_b(suffix),
        "C_explicit_start": smoke_c(suffix),
        "D_full_flow": smoke_d(suffix),
    }
    smokes["E_add_vehicle_h5"] = smoke_add_vehicle_h5(suffix, smokes["D_full_flow"]["case_id"])
    smokes["F_workbench_default_queue"] = smoke_workbench_default(
        suffix,
        smokes["D_full_flow"]["case_id"],
        smokes["A_random_photo"].get("case_id") or "",
    )

    out = {"suffix": suffix, "smokes": smokes}
    out["all_pass"] = all(s["pass"] for s in smokes.values())
    print(json.dumps(out, ensure_ascii=False, indent=2), flush=True)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
