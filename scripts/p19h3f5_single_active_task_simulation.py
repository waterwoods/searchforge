#!/usr/bin/env python3
"""P19H-3f-5 local simulation — Single Active Task per Lane scenarios."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    mark_claim_broker_done,
    patch_case_known_facts,
    save_case,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_collision_choice,
    ingest_claim_holding_ack,
    ingest_claim_status_request,
)
from services.fiqa_api.wecom.claim_end_card import try_send_claim_end_card
from services.fiqa_api.wecom.claim_state import CLAIM_PHASE_BROKER_REVIEW, SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message

START_TITLE = "【事故记录已开始 ✅】"
CONFIRM_TITLE = "【请确认】"
STATUS_TITLE = "【当前状态】"
END_TITLE = "【陈总已确认 ✅】"


def _setup_store() -> Path:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    os.environ["WECOM_KF_TOKEN"] = "tok"
    os.environ["WECOM_KF_ENCODING_AES_KEY"] = "a" * 43
    os.environ["WECOM_CORP_ID"] = "wwtest"
    os.environ["WECOM_KF_SECRET"] = "secret"
    load_wecom_kf_config.cache_clear()
    return path


def _text(content: str, *, ext: str, msg_id: str) -> dict:
    return normalize_text_message(
        {
            "msgid": msg_id,
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "text": {"content": content},
        }
    )


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


def _open_claim(ext: str, *, complete: bool = False) -> str:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = str(saved["case_id"])
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    if complete:
        patch_case_known_facts(
            cid,
            {
                "accident_datetime": "7月8日",
                "accident_location": "Santa Ana",
                "accident_description": "追尾",
            },
        )
        update_claim_workflow_state(cid, claim_phase="accident_basics_complete")
    return cid


def _claim_count(ext: str) -> int:
    return sum(
        1
        for c in list_all_cases_for_read()
        if c.get("wecom_external_userid") == ext and c.get("service_lane") == SERVICE_LANE_CLAIM
    )


def _dl(cfg, **kwargs):
    return WeComMediaDownloadResult(content=b"\xff\xd8\xff", content_type="image/jpeg", filename="p.jpg")


def _up(**kwargs):
    return {"storage_uri": "gs://sim/x.jpg", "mime_type": "image/jpeg", "size_bytes": 3}


def run_simulation() -> dict:
    _setup_store()
    suffix = datetime.now(timezone.utc).strftime("%H%M%S")
    scenarios: dict[str, dict] = {}

    ext_a = f"wm_3f5_a_{suffix}"
    r_a = ingest_claim_holding_ack(_text("刚才追尾了", ext=ext_a, msg_id="a1"))
    scenarios["A_no_open_passive_holding"] = {
        "outcome": r_a.get("active_case_outcome"),
        "claim_count": _claim_count(ext_a),
        "pass": r_a.get("active_case_outcome") == "claim_holding_ack" and _claim_count(ext_a) == 0,
    }

    ext_b = f"wm_3f5_b_{suffix}"
    r_b = ingest_claim_basics_message(_text("我要理赔", ext=ext_b, msg_id="b1"), classify_wecom_intent("我要理赔"))
    scenarios["B_start_claim_start_card"] = {
        "outcome": r_b.get("active_case_outcome"),
        "has_start": START_TITLE in str(r_b.get("reply_text") or ""),
        "pass": r_b.get("active_case_outcome") == "claim_start_card_sent" and START_TITLE in str(r_b.get("reply_text") or ""),
    }

    ext_c = f"wm_3f5_c_{suffix}"
    cid_c = _open_claim(ext_c, complete=True)
    r_c = ingest_claim_basics_message(
        _text("对方保险是 State Farm", ext=ext_c, msg_id="c1"),
        classify_wecom_intent("对方保险是 State Farm"),
    )
    scenarios["C_claim_supplement_append"] = {
        "case_id": r_c.get("case_id"),
        "outcome": r_c.get("active_case_outcome"),
        "pass": r_c.get("case_id") == cid_c and r_c.get("active_case_outcome") != "claim_collision_resolver",
    }

    ext_d = f"wm_3f5_d_{suffix}"
    cid_d = _open_claim(ext_d, complete=True)
    r_d = ingest_claim_status_request(_text("进度", ext=ext_d, msg_id="d1"), classify_wecom_intent("进度"))
    scenarios["D_claim_status_card"] = {
        "case_id": r_d.get("case_id"),
        "has_status": STATUS_TITLE in str(r_d.get("reply_text") or ""),
        "pass": r_d.get("case_id") == cid_d and STATUS_TITLE in str(r_d.get("reply_text") or ""),
    }

    ext_e = f"wm_3f5_e_{suffix}"
    _open_claim(ext_e, complete=True)
    newest_e = _open_claim(ext_e, complete=True)
    r_e = ingest_claim_basics_message(
        _text("补充一下对方电话", ext=ext_e, msg_id="e1"),
        classify_wecom_intent("补充一下对方电话"),
    )
    case_e = get_case_by_id(newest_e) or {}
    scenarios["E_multi_open_ordinary_append_flag"] = {
        "case_id": r_e.get("case_id"),
        "risk_flag": "possible_multi_claim_context" in (case_e.get("risk_flags") or []),
        "pass": r_e.get("case_id") == newest_e and "possible_multi_claim_context" in (case_e.get("risk_flags") or []),
    }

    ext_f = f"wm_3f5_f_{suffix}"
    _open_claim(ext_f, complete=True)
    newest_f = _open_claim(ext_f, complete=True)
    cfg = load_wecom_kf_config()
    r_f = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"f_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext_f,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": "mid"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    case_f = get_case_by_id(newest_f) or {}
    scenarios["F_multi_open_photo_bind_flag"] = {
        "case_id": r_f.get("case_id"),
        "outcome": r_f.get("active_case_outcome"),
        "risk_flag": "possible_multi_claim_context" in (case_f.get("risk_flags") or []),
        "pass": r_f.get("case_id") == newest_f and "possible_multi_claim_context" in (case_f.get("risk_flags") or []),
    }

    ext_g = f"wm_3f5_g_{suffix}"
    _open_claim(ext_g, complete=True)
    _open_claim(ext_g, complete=True)
    r_g = ingest_claim_basics_message(_text("新的事故", ext=ext_g, msg_id="g1"), classify_wecom_intent("新的事故"))
    scenarios["G_multi_open_new_accident_confirm"] = {
        "outcome": r_g.get("active_case_outcome"),
        "has_confirm": CONFIRM_TITLE in str(r_g.get("reply_text") or ""),
        "pass": r_g.get("active_case_outcome") == "claim_collision_resolver" and CONFIRM_TITLE in str(r_g.get("reply_text") or ""),
    }

    ext_h = f"wm_3f5_h_{suffix}"
    _open_claim(ext_h, complete=True)
    ingest_claim_basics_message(
        _text("新的事故", ext=ext_h, msg_id="h0"),
        classify_wecom_intent("新的事故"),
    )
    before_h = _claim_count(ext_h)
    r_h = ingest_claim_collision_choice(_text("2", ext=ext_h, msg_id="h1"))
    scenarios["H_confirm_2_new_claim_start"] = {
        "outcome": r_h.get("active_case_outcome"),
        "claim_count_delta": _claim_count(ext_h) - before_h,
        "has_start": START_TITLE in str(r_h.get("reply_text") or ""),
        "pass": r_h.get("active_case_outcome") == "claim_start_card_sent" and _claim_count(ext_h) == before_h + 1,
    }

    ext_i = f"wm_3f5_i_{suffix}"
    add_car = save_case("add car", {"issue_category": "add_car_quote", "urgency": "medium", "manual_followup_needed": True, "broker_next_step": "x", "client_prep": "", "client_reply_draft": "", "handoff_ready": False}, service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(str(add_car["case_id"]), wecom_external_userid=ext_i)
    r_i = ingest_claim_basics_message(_text("我要理赔", ext=ext_i, msg_id="i1"), classify_wecom_intent("我要理赔"))
    scenarios["I_add_car_claim_lane_switch"] = {
        "outcome": r_i.get("active_case_outcome"),
        "pass": r_i.get("active_case_outcome") == "claim_lane_switch_prompt",
    }

    ext_j = f"wm_3f5_j_{suffix}"
    cid_j = _open_claim(ext_j, complete=False)
    update_claim_workflow_state(cid_j, claim_phase=CLAIM_PHASE_BROKER_REVIEW)
    done = mark_claim_broker_done(cid_j)
    end = try_send_claim_end_card(cid_j)
    end_text = str(end.get("end_card_preview") or end.get("reply_text") or "")
    scenarios["J_broker_done_end_card"] = {
        "broker_done": done.get("already_done") is False or done.get("end_card_sent") is not False,
        "end_card": END_TITLE in end_text,
        "pass": END_TITLE in end_text,
    }

    all_pass = all(s.get("pass") for s in scenarios.values())
    return {
        "sprint": "P19H-3f-5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS" if all_pass else "FAIL",
        "scenarios": scenarios,
    }


def main() -> int:
    result = run_simulation()
    out = REPO / "docs" / "evidence" / "p19h3f5_single_active_task_simulation_2026_07_10.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nWrote {out}")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
