"""P19D-4B fix — Start Card convergence, completed flow, End Card follow-up."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from services.fiqa_api.inbox_triage.case_store import bind_case_channel_identity, get_case_by_id, save_case
from services.fiqa_api.inbox_triage.h5_task_upload import (
    h5_photo_flow_is_complete,
    wants_restart_add_car_photo_flow,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.reply import build_h5_vin_start_card_payload
from services.fiqa_api.wecom.slice import _build_add_car_h5_start_menu


@pytest.fixture(autouse=True)
def _json_store():
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


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


def _case_with_h5_photos(*, insurance_skipped: bool = False) -> dict:
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation, _persist_case_after_update

    mut = _load_case_for_mutation(saved["case_id"])
    assert mut is not None
    atts = [
        {"attachment_id": "a1", "source": "h5_task", "slot_assignment": "vin_photo"},
        {"attachment_id": "a2", "source": "h5_task", "slot_assignment": "registration_photo"},
    ]
    if not insurance_skipped:
        atts.append({"attachment_id": "a3", "source": "h5_task", "slot_assignment": "insurance_card_photo"})
    mut["case_attachments"] = atts
    if insurance_skipped:
        mut["h5_photo_flow_state"] = {"skipped_slots": ["insurance_card_photo"]}
    _persist_case_after_update(saved["case_id"], mut)
    return get_case_by_id(saved["case_id"]) or mut


def test_start_card_hides_long_url_in_msgmenu_tail():
    url = "https://example.test/task/upload/h5t1.verylongtokenpath"
    menu = build_h5_vin_start_card_payload(h5_url=url)
    tail = menu["tail_content"]
    assert "https://example.test" not in tail
    assert "请回复：链接" in tail
    assert menu["list"][0]["view"]["content"] == "开始上传照片"
    assert menu["list"][0]["view"]["url"] == url


def test_h5_photo_flow_is_complete_detects_uploads_and_skip():
    complete = _case_with_h5_photos()
    assert h5_photo_flow_is_complete(complete) is True
    skipped = _case_with_h5_photos(insurance_skipped=True)
    assert h5_photo_flow_is_complete(skipped) is True
    partial = save_case("partial", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    assert h5_photo_flow_is_complete(partial) is False


def test_wants_restart_add_car_photo_flow():
    assert wants_restart_add_car_photo_flow("我要重新加车") is True
    assert wants_restart_add_car_photo_flow("我要加车") is False


def test_completed_case_gets_followup_not_start_card():
    case = _case_with_h5_photos()
    bind_case_channel_identity(
        case["case_id"],
        wecom_external_userid="wm_followup_user",
        wecom_open_kf_id="wktest001",
    )
    normalized = {
        "external_userid": "wm_followup_user",
        "open_kf_id": "wktest001",
    }
    with patch(
        "services.fiqa_api.wecom.slice.try_send_h5_photo_flow_end_card",
        return_value={"sent": True},
    ) as mock_send:
        menu, text, masked = _build_add_car_h5_start_menu(
            normalized,
            case_id=case["case_id"],
        )
    assert menu is None
    assert masked is None
    assert text is not None
    assert "照片已收到" in text
    assert "提车日期" in text
    assert "不会自动修改您的保单" in text
    mock_send.assert_called_once_with(case["case_id"])


def test_incomplete_case_still_gets_start_card():
    saved = save_case("new add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    normalized = {"external_userid": "wm_new_user", "open_kf_id": "wktest001"}
    os.environ["H5_TASK_TOKEN_SECRET"] = "test-h5-secret"
    os.environ["H5_TASK_FRONTEND_BASE_URL"] = "https://example.test"
    menu, text, masked = _build_add_car_h5_start_menu(normalized, case_id=saved["case_id"])
    assert menu is not None
    assert text is None
    assert masked is not None
    assert menu["list"][0]["view"]["content"] == "开始上传照片"
    assert "https://example.test" not in menu["tail_content"]
