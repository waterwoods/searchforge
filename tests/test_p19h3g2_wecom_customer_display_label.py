"""P19H-3g-2 Phase 1 — WeCom customer display label at channel bind."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_attachment_api import sanitize_case_for_workbench_api
from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
)
from services.fiqa_api.wecom.active_case_bridge import create_or_attach_draft_case_for_start_click
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message
from services.fiqa_api.wecom.identity import (
    is_generic_wecom_customer_name,
    wecom_customer_display_label,
    wecom_customer_facing_display_name,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply import build_claim_status_card_reply


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


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


def _add_car_stub() -> dict:
    return {
        "issue_category": "add_car",
        "urgency": "medium",
        "manual_followup_needed": False,
        "broker_next_step": "Collect vehicle documents.",
        "client_prep": "",
        "client_reply_draft": "",
    }


def _claim_start_normalized(ext: str = "wm_claim_p19h3g2") -> dict:
    return normalize_text_message(
        {
            "msgid": "msg_claim_g2",
            "open_kfid": "wk001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "send_time": 1719750000,
            "text": {"content": "我要理赔"},
        }
    )


def test_is_generic_wecom_customer_name() -> None:
    assert is_generic_wecom_customer_name(None)
    assert is_generic_wecom_customer_name("")
    assert is_generic_wecom_customer_name("企业微信客户")
    assert is_generic_wecom_customer_name("微信客户 · abc123")
    assert is_generic_wecom_customer_name("企业微信客户（尾号 mxcw）")
    assert not is_generic_wecom_customer_name("张先生")
    assert not is_generic_wecom_customer_name("Chen Kui")


def test_bind_sets_customer_name_when_empty() -> None:
    saved = save_case("[客户] test", _add_car_stub(), service_lane="add_car")
    cid = str(saved["case_id"])
    ext = "wm_bind_empty_g2"

    bind_case_channel_identity(cid, wecom_external_userid=ext, wecom_open_kf_id="wk001")

    case = get_case_by_id(cid)
    assert case is not None
    assert case["wecom_external_userid"] == ext
    assert case["customer_name"] == wecom_customer_display_label(ext)


def test_bind_does_not_overwrite_meaningful_customer_name() -> None:
    from services.fiqa_api.inbox_triage.case_store import update_case_customer

    saved = save_case("[客户] test", _add_car_stub(), service_lane="add_car")
    cid = str(saved["case_id"])
    update_case_customer(cid, customer_name="李女士")
    ext = "wm_bind_preserve_g2"

    bind_case_channel_identity(cid, wecom_external_userid=ext)

    case = get_case_by_id(cid)
    assert case is not None
    assert case["customer_name"] == "李女士"


def test_bind_backfills_generic_placeholder() -> None:
    from services.fiqa_api.inbox_triage.case_store import update_case_customer

    saved = save_case("[客户] test", _add_car_stub(), service_lane="add_car")
    cid = str(saved["case_id"])
    update_case_customer(cid, customer_name="企业微信客户")
    ext = "wm_backfill_g2abcdef"
    bind_case_channel_identity(cid, wecom_external_userid=ext)

    case = get_case_by_id(cid)
    assert case is not None
    assert case["customer_name"] == "微信客户 · abcdef"


def test_claim_create_sets_non_generic_customer_name() -> None:
    ext = "wm_claim_create_g2abcdef"
    norm = _claim_start_normalized(ext)
    ingest_claim_basics_message(norm, classify_wecom_intent(norm["text"]))

    from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read

    cases = [c for c in list_all_cases_for_read() if c.get("wecom_external_userid") == ext]
    assert len(cases) == 1
    assert cases[0]["customer_name"] == "微信客户 · abcdef"


def test_add_car_start_sets_non_generic_customer_name() -> None:
    ext = "wm_add_car_g2abcdef"
    normalized = normalize_text_message(
        {
            "msgid": "msg_start_g2",
            "open_kfid": "wk001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "send_time": 1719750000,
            "text": {"content": "开始"},
        }
    )
    create_or_attach_draft_case_for_start_click(normalized)

    from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read

    cases = [c for c in list_all_cases_for_read() if c.get("wecom_external_userid") == ext]
    assert len(cases) == 1
    assert cases[0]["customer_name"] == "微信客户 · abcdef"


def test_workbench_api_masks_full_external_userid() -> None:
    saved = save_case("[客户] test", _add_car_stub(), service_lane="add_car")
    cid = str(saved["case_id"])
    ext = "wm_mask_test_g2abcdef"
    bind_case_channel_identity(cid, wecom_external_userid=ext)

    case = get_case_by_id(cid)
    assert case is not None
    safe = sanitize_case_for_workbench_api(case)
    assert safe.get("wecom_external_userid") is None
    assert safe.get("customer_name") == "微信客户 · abcdef"


def test_status_card_uses_wechat_customer_not_suffix() -> None:
    case = {
        "case_id": "case_status_g2",
        "customer_name": "微信客户 · abc123",
        "service_lane": "claim",
        "claim_phase": "claim_started",
    }
    reply = build_claim_status_card_reply(case)
    assert "abc123" not in reply
    assert "客户：微信客户" in reply
    assert "wm_" not in reply


def test_customer_facing_name_preserves_broker_meaningful_name() -> None:
    assert wecom_customer_facing_display_name("张先生") == "张先生"
    assert wecom_customer_facing_display_name("微信客户 · xyz") == "微信客户"
