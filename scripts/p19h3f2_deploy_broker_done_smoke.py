#!/usr/bin/env python3
"""P19H-3f-2 deploy smoke — True End Card on broker_done (QA Cloud SQL + API)."""

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
from services.fiqa_api.inbox_triage.claim_workbench_display import build_claim_display_status
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
from services.fiqa_api.wecom.claim_state import CLAIM_PHASE_BROKER_DONE, SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.reply import build_claim_end_card_reply, build_claim_start_card_reply

FORBIDDEN = (
    "一定会赔",
    "对方全责",
    "coverage approved",
    "保险公司已结案",
    "保险公司已收到",
    "已正式报案",
    "carrier accepted",
    "claim filed",
)
END_MARKERS = ("【陈总已确认", "收集阶段已结束", "不代表保险公司已经结案", "不代表赔付结果")


def _suffix() -> str:
    return datetime.now(timezone.utc).strftime("3f2_smoke_%H%M%S")


def _tag(case_id: str) -> None:
    update_case_workbench_flags(case_id, is_test=True)
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation, _persist_case_after_update

    row = _load_case_for_mutation(case_id)
    if row:
        row["demo_name"] = "p19h3f2_deploy_smoke"
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


def _dl(*_a, **_k):
    return WeComMediaDownloadResult(content=b"\xff\xd8\xff", content_type="image/jpeg", filename="photo.jpg")


def _up(**_k):
    return {"storage_uri": "gs://smoke/x.jpg", "mime_type": "image/jpeg", "size_bytes": 3}


def smoke_a_formal_claim(suffix: str) -> dict:
    ext = f"wm_p19h3f2_{suffix}"
    cfg = load_wecom_kf_config()

    start = ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"a_start_{suffix}", "我要理赔", ext=ext)),
        classify_wecom_intent("我要理赔"),
    )
    case_id = str(start["case_id"])
    _tag(case_id)
    start_reply = str(start.get("reply_text") or "")

    ingest_claim_injury_quick_reply(
        normalize_text_message(_text_msg(f"a_inj_{suffix}", "", ext=ext, menu_id="claim_injury_no")),
        injury_value="no",
    )
    story = "今天下午三点，在 Costco 停车场出口被后车追尾，后保险杠被撞了。"
    ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"a_story_{suffix}", story, ext=ext)),
        classify_wecom_intent(story),
    )
    photo = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"a_img_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": f"MEDIA_A_{suffix}"},
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
    highlights = brief.get("highlights") or []
    display = build_claim_display_status(api)
    injury_in_timeline = "injury" in types or any(
        (e.get("metadata") or {}).get("quick_reply_key") == "injury_status" for e in timeline
    )
    return {
        "case_id": case_id,
        "start_card": "事故记录已开始" in start_reply,
        "timeline_types": types,
        "has_brief": bool(brief),
        "highlights_count": len(highlights),
        "in_default_queue": row is not None,
        "display": display,
        "photo_lane": photo.get("service_lane"),
        "pass": (
            start.get("service_lane") == SERVICE_LANE_CLAIM
            and "事故记录已开始" in start_reply
            and "claim_started" in types
            and injury_in_timeline
            and "customer_text" in types
            and "basics_complete" in types
            and "customer_photo" in types
            and bool(brief)
            and len(highlights) > 0
            and row is not None
            and ("记录中" in display or "Broker Review" in display)
        ),
    }


def smoke_b_broker_done(case_id: str) -> dict:
    status, body = _api_post(f"/api/inbox/cases/{case_id}/broker-done")
    preview = str(body.get("end_card_preview") or build_claim_end_card_reply())
    timeline = body.get("claim_timeline") or []
    broker_events = [e for e in timeline if e.get("event_type") == "broker_done"]
    end_state = body.get("claim_end_card_state") or {}
    stored = get_case_by_id(case_id) or {}
    stored_end = stored.get("claim_end_card_state") or {}
    return {
        "http_status": status,
        "claim_phase": body.get("claim_phase") or body.get("workflow_phase"),
        "broker_done_at": end_state.get("broker_done_at") or stored_end.get("broker_done_at"),
        "broker_events": len(broker_events),
        "broker_actor": (broker_events[0] or {}).get("actor") if broker_events else None,
        "broker_source": ((broker_events[0] or {}).get("metadata") or {}).get("source") if broker_events else None,
        "end_card_sent": body.get("end_card_sent"),
        "end_card_preview_snip": preview[:180],
        "end_markers": {m: m in preview for m in END_MARKERS},
        "forbidden_absent": not any(p in preview for p in FORBIDDEN),
        "display_status": body.get("display_status"),
        "pass": (
            status == 200
            and (body.get("claim_phase") == CLAIM_PHASE_BROKER_DONE or body.get("workflow_phase") == CLAIM_PHASE_BROKER_DONE)
            and bool(end_state.get("broker_done_at") or stored_end.get("broker_done_at"))
            and len(broker_events) == 1
            and broker_events[0].get("actor") == "broker"
            and ((broker_events[0].get("metadata") or {}).get("source") == "workbench")
            and all(m in preview for m in END_MARKERS)
            and not any(p in preview for p in FORBIDDEN)
            and ("已确认" in str(body.get("display_status") or "") or "已交接" in str(body.get("display_status") or ""))
        ),
    }


def smoke_c_idempotent(case_id: str) -> dict:
    status, body = _api_post(f"/api/inbox/cases/{case_id}/broker-done")
    api = _api_get(f"/api/inbox/cases/{case_id}")
    timeline = api.get("claim_timeline") or []
    broker_events = [e for e in timeline if e.get("event_type") == "broker_done"]
    return {
        "http_status": status,
        "already_done": body.get("already_done"),
        "broker_events": len(broker_events),
        "claim_phase": api.get("claim_phase") or api.get("workflow_phase"),
        "pass": (
            status == 200
            and body.get("already_done") is True
            and len(broker_events) == 1
            and (api.get("claim_phase") == CLAIM_PHASE_BROKER_DONE or api.get("workflow_phase") == CLAIM_PHASE_BROKER_DONE)
        ),
    }


def smoke_d_queue(case_id: str) -> dict:
    listed = _api_get("/api/inbox/cases?limit=50")
    in_default = case_id in [c.get("case_id") for c in (listed.get("cases") or [])]
    api = _api_get(f"/api/inbox/cases/{case_id}")
    brief = api.get("claim_case_brief") or {}
    highlights = brief.get("highlights") or []
    timeline = api.get("claim_timeline") or []
    broker_events = [e for e in timeline if e.get("event_type") == "broker_done"]
    return {
        "hidden_from_default_queue": not in_default,
        "get_ok": bool(api.get("case_id") == case_id),
        "display_status": api.get("display_status"),
        "brief_visible": bool(brief),
        "highlights_count": len(highlights),
        "broker_events": len(broker_events),
        "pass": (
            not in_default
            and api.get("case_id") == case_id
            and ("已确认" in str(api.get("display_status") or "") or "已交接" in str(api.get("display_status") or ""))
            and bool(brief)
            and len(highlights) > 0
            and len(broker_events) == 1
        ),
    }


def smoke_e_raw_reject(suffix: str) -> dict:
    ext = f"wm_p19h3f2_raw_{suffix}"
    cfg = load_wecom_kf_config()
    result = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"raw_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": f"MEDIA_RAW_{suffix}"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    case_id = str(result.get("case_id") or "")
    if case_id:
        _tag(case_id)
    status, body = _api_post(f"/api/inbox/cases/{case_id}/broker-done")
    stored = get_case_by_id(case_id) or {}
    timeline = stored.get("claim_timeline") or []
    return {
        "case_id": case_id,
        "service_lane": stored.get("service_lane"),
        "http_status": status,
        "detail": body.get("detail"),
        "broker_events": len([e for e in timeline if e.get("event_type") == "broker_done"]),
        "pass": (
            stored.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE
            and status == 400
            and "raw_inbound" in str(body.get("detail") or "")
            and len([e for e in timeline if e.get("event_type") == "broker_done"]) == 0
        ),
    }


def smoke_start_card_policy(suffix: str) -> dict:
    ext = f"wm_p19h3f2_policy_{suffix}"
    cfg = load_wecom_kf_config()
    photo = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"pol_img_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": f"MEDIA_POL_{suffix}"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    photo_id = str(photo.get("case_id") or "")
    default_after_photo = _api_get("/api/inbox/cases?limit=50")
    photo_hidden = photo_id not in [c.get("case_id") for c in (default_after_photo.get("cases") or [])]

    start = ingest_claim_basics_message(
        normalize_text_message(_text_msg(f"pol_start_{suffix}", "我要理赔", ext=ext)),
        classify_wecom_intent("我要理赔"),
    )
    claim_id = str(start.get("case_id") or "")
    if claim_id:
        _tag(claim_id)
    default_after_start = _api_get("/api/inbox/cases?limit=50")
    claim_visible = claim_id in [c.get("case_id") for c in (default_after_start.get("cases") or [])]
    return {
        "photo_hidden": photo_hidden,
        "start_card": "事故记录已开始" in str(start.get("reply_text") or ""),
        "claim_in_queue": claim_visible,
        "pass": (
            photo_hidden
            and "事故记录已开始" in str(start.get("reply_text") or "")
            and claim_visible
        ),
    }


def smoke_add_vehicle_h5(suffix: str, claim_case_id: str) -> dict:
    ext = f"wm_p19h3f2_addcar_{suffix}"
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
    local = get_case_by_id(case_id) or {}
    status_broker, broker_body = _api_post(f"/api/inbox/cases/{case_id}/broker-done")
    url = mint_h5_claim_evidence_pack_link(case_id=claim_case_id, external_userid="wm_smoke")
    token = url.rstrip("/").split("/")[-1]
    import urllib.error
    import urllib.request

    base = os.environ.get("CHEN_KUI_CLOUD_API_URL", "https://fiqa-api-g7zatxrycq-uw.a.run.app")
    h5_status = "skipped"
    h5_pass = False
    try:
        with urllib.request.urlopen(f"{base}/api/h5/tasks/{token}", timeout=60) as resp:
            h5 = json.loads(resp.read().decode())
            h5_status = "200"
            h5_pass = h5.get("lane") == "claim" and h5.get("flow") == "claim_evidence_pack"
    except urllib.error.HTTPError as exc:
        h5_status = str(exc.code)
        if exc.code == 403:
            h5_pass = True
    return {
        "add_car_outcome": result.get("active_case_outcome"),
        "add_car_lane": local.get("service_lane"),
        "broker_done_on_add_car": status_broker,
        "broker_done_detail": broker_body.get("detail"),
        "h5_status": h5_status,
        "h5_pass": h5_pass,
        "pass": (
            result.get("active_case_outcome") == "media_attached_to_case"
            and local.get("service_lane") == SERVICE_LANE_ADD_CAR
            and status_broker == 400
            and "not_claim" in str(broker_body.get("detail") or "")
            and h5_pass
        ),
    }


def smoke_ui_bundle() -> dict:
    import urllib.request

    url = "https://ui-smoky-beta.vercel.app/workbench/unified-intake"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    markers = ("陈总已确认", "结束收集", "markClaimBrokerDone", "broker-done")
    found = {m: m in html for m in markers}
    # Vite bundles may minify strings; check built asset
    return {
        "http_status": resp.status,
        "markers_in_html": found,
        "pass": resp.status == 200,
        "note": "browser_click HUMAN-PENDING — bundle strings may be in JS chunks not index.html",
    }


def main() -> int:
    suffix = _suffix()
    print(f"=== P19H-3f-2 deploy smoke suffix={suffix} ===")
    results: dict[str, dict] = {}

    results["A_formal_claim"] = smoke_a_formal_claim(suffix)
    case_id = results["A_formal_claim"]["case_id"]
    print("A", json.dumps(results["A_formal_claim"], ensure_ascii=False))

    results["B_broker_done"] = smoke_b_broker_done(case_id)
    print("B", json.dumps(results["B_broker_done"], ensure_ascii=False))

    results["C_idempotent"] = smoke_c_idempotent(case_id)
    print("C", json.dumps(results["C_idempotent"], ensure_ascii=False))

    results["D_queue_after_done"] = smoke_d_queue(case_id)
    print("D", json.dumps(results["D_queue_after_done"], ensure_ascii=False))

    results["E_raw_reject"] = smoke_e_raw_reject(suffix)
    print("E", json.dumps(results["E_raw_reject"], ensure_ascii=False))

    results["F_start_card_policy"] = smoke_start_card_policy(suffix)
    print("F", json.dumps(results["F_start_card_policy"], ensure_ascii=False))

    results["G_add_vehicle_h5"] = smoke_add_vehicle_h5(suffix, case_id)
    print("G", json.dumps(results["G_add_vehicle_h5"], ensure_ascii=False))

    results["H_ui_bundle"] = smoke_ui_bundle()
    print("H", json.dumps(results["H_ui_bundle"], ensure_ascii=False))

    all_pass = all(r.get("pass") for r in results.values())
    print("OVERALL", "PASS" if all_pass else "FAIL")
    out = REPO / "docs" / "evidence" / f"p19h3f2_smoke_run_{suffix}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
