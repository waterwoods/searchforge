"""P19H-3f-1c — Start Card only intake: raw inbound hidden from broker workbench queue."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import (
    SERVICE_LANE_ADD_CAR,
    SERVICE_LANE_WECOM_MEDIA_INTAKE,
)
from services.fiqa_api.inbox_triage.workbench_enrichment import (
    filter_broker_workbench_cases,
    is_raw_inbound_case,
)
from services.fiqa_api.routes.inbox_triage import router as inbox_router
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message, ingest_claim_holding_ack
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


@pytest.fixture(autouse=True)
def _json_store(monkeypatch):
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


@pytest.fixture
def cfg(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "sec")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    return load_wecom_kf_config()


def _api_client() -> TestClient:
    app = FastAPI()
    app.include_router(inbox_router)
    return TestClient(app)


def _triage_stub() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": False,
        "broker_next_step": "Review",
        "client_prep": "",
        "client_reply_draft": "",
        "primary_vehicle_summary": "2024 Tesla Model 3",
    }


def _msg(msg_id: str, content: str, *, ext: str = "wm_p19h3f1c") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": content},
    }


def _normalized(text: str, *, ext: str = "wm_p19h3f1c", msg_id: str = "m1") -> dict:
    return normalize_text_message(_msg(msg_id, text, ext=ext))


def _image_msg(msg_id: str, *, ext: str = "wm_p19h3f1c_photo") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "image",
        "image": {"media_id": f"media_{msg_id}"},
    }


def _fake_download(_cfg, *, media_id: str, msgtype: str) -> WeComMediaDownloadResult:
    return WeComMediaDownloadResult(
        content=b"\xff\xd8\xff",
        content_type="image/jpeg",
        filename="photo.jpg",
    )


def _fake_upload(**_kwargs) -> dict:
    return {
        "storage_uri": "gs://test-bucket/wecom/photo.jpg",
        "mime_type": "image/jpeg",
        "size_bytes": 3,
    }


def _seed_wecom_media_intake(cfg) -> str:
    norm = normalize_media_message(_image_msg("img_raw", ext="wm_raw_only"))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["active_case_outcome"] == "media_unassigned"
    case_id = str(result["case_id"])
    case = get_case_by_id(case_id) or {}
    assert case.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE
    return case_id


def _seed_claim() -> str:
    result = ingest_claim_basics_message(
        _normalized("我要理赔", ext="wm_claim_wb", msg_id="m_start"),
        classify_wecom_intent("我要理赔"),
    )
    return str(result["case_id"])


def test_default_workbench_list_excludes_wecom_media_intake(cfg):
    media_id = _seed_wecom_media_intake(cfg)
    claim_id = _seed_claim()
    add_car = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)

    resp = _api_client().get("/api/inbox/cases", params={"limit": 50})
    assert resp.status_code == 200
    ids = [c["case_id"] for c in resp.json().get("cases") or []]
    assert media_id not in ids
    assert claim_id in ids
    assert add_car["case_id"] in ids


def test_include_raw_inbound_debug_param_shows_wecom_media_intake(cfg):
    media_id = _seed_wecom_media_intake(cfg)
    resp = _api_client().get(
        "/api/inbox/cases",
        params={"limit": 50, "include_raw_inbound": "true"},
    )
    assert resp.status_code == 200
    ids = [c["case_id"] for c in resp.json().get("cases") or []]
    assert media_id in ids


def test_formal_case_detail_still_works(cfg):
    claim_id = _seed_claim()
    _seed_wecom_media_intake(cfg)
    resp = _api_client().get(f"/api/inbox/cases/{claim_id}")
    assert resp.status_code == 200
    assert resp.json().get("service_lane") == SERVICE_LANE_CLAIM


def test_wecom_media_intake_data_not_deleted(cfg):
    media_id = _seed_wecom_media_intake(cfg)
    assert get_case_by_id(media_id) is not None
    all_cases = list_all_cases_for_read()
    assert any(c.get("case_id") == media_id for c in all_cases)


def test_random_photo_no_broker_queue_item(cfg):
    _seed_wecom_media_intake(cfg)
    visible = filter_broker_workbench_cases(list_all_cases_for_read())
    assert not any(c.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE for c in visible)


def test_random_narrative_no_broker_queue_item():
    text = "昨晚 Costco 被追尾了，后保险杠有点坏。"
    normalized = _normalized(text, msg_id="m_narr")
    intent = classify_wecom_intent(text)
    result = ingest_claim_holding_ack(normalized)
    assert result["case_created"] is False
    visible = filter_broker_workbench_cases(list_all_cases_for_read())
    assert not any(c.get("service_lane") == SERVICE_LANE_CLAIM for c in visible)


def test_explicit_start_appears_in_broker_queue():
    claim_id = _seed_claim()
    visible = filter_broker_workbench_cases(list_all_cases_for_read())
    assert any(c.get("case_id") == claim_id for c in visible)


def test_active_claim_photo_not_raw_queue(cfg):
    ext = "wm_photo_bind"
    ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="m_s"),
        classify_wecom_intent("我要理赔"),
    )
    norm = normalize_media_message(_image_msg("img_bind", ext=ext))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["service_lane"] == SERVICE_LANE_CLAIM
    visible = filter_broker_workbench_cases(list_all_cases_for_read())
    assert any(c.get("case_id") == result["case_id"] for c in visible)
    assert not any(c.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE for c in visible)


def test_is_raw_inbound_case_helper():
    assert is_raw_inbound_case({"service_lane": SERVICE_LANE_WECOM_MEDIA_INTAKE}) is True
    assert is_raw_inbound_case({"service_lane": SERVICE_LANE_CLAIM}) is False
    assert is_raw_inbound_case({"service_lane": SERVICE_LANE_ADD_CAR}) is False
