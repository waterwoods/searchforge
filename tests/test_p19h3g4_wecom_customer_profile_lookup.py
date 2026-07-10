"""P19H-3g-4 — WeCom KF customer profile lookup (nickname / avatar / unionid)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from services.fiqa_api.inbox_triage.case_attachment_api import sanitize_case_for_workbench_api
from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
    update_case_customer,
)
from services.fiqa_api.wecom.active_case_bridge import create_or_attach_draft_case_for_start_click
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message
from services.fiqa_api.wecom.config import WeComKfConfig, load_wecom_kf_config
from services.fiqa_api.wecom.customer_profile import (
    fetch_kf_customer_profile,
    merge_customer_identity,
    should_fetch_kf_customer_profile,
)
from services.fiqa_api.wecom.identity import (
    is_generic_wecom_customer_name,
    resolve_wecom_workbench_display_name,
    wecom_customer_display_label,
    wecom_customer_facing_display_name,
)
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


def _mock_batchget_response(
    *,
    nickname: str = "",
    avatar: str = "",
    unionid: str = "",
    invalid: bool = False,
) -> dict[str, Any]:
    if invalid:
        return {"errcode": 0, "customer_list": [], "invalid_external_userid": ["wm_test_g4"]}
    return {
        "errcode": 0,
        "customer_list": [
            {
                "external_userid": "wm_test_g4abcdef",
                "nickname": nickname,
                "avatar": avatar,
                "unionid": unionid,
                "gender": 1,
            }
        ],
        "invalid_external_userid": [],
    }


def _test_cfg() -> WeComKfConfig:
    return WeComKfConfig(
        token="t",
        encoding_aes_key="k",
        corp_id="corp",
        kf_secret="secret",
    )


def test_kf_profile_success_normalizes_fields() -> None:
    mock_resp = type("R", (), {"raise_for_status": lambda self: None, "json": lambda self: _mock_batchget_response(nickname="张三", avatar="https://avatar.example/a.jpg", unionid="oUnion123")})()

    with patch("services.fiqa_api.wecom.customer_profile.get_access_token", return_value="tok"), patch(
        "services.fiqa_api.wecom.customer_profile.httpx.post", return_value=mock_resp
    ):
        profile = fetch_kf_customer_profile("wm_test_g4abcdef", cfg=_test_cfg())

    assert profile is not None
    assert profile["wecom_nickname"] == "张三"
    assert profile["wecom_avatar"] == "https://avatar.example/a.jpg"
    assert profile["wecom_unionid"] == "oUnion123"
    assert profile["profile_source"] == "kf_customer_batchget"
    assert profile["real_wechat_id_available"] is False
    assert "nickname" in profile["raw_available_fields"]


def test_kf_profile_api_failure_returns_none() -> None:
    with patch("services.fiqa_api.wecom.customer_profile.get_access_token", return_value="tok"), patch(
        "services.fiqa_api.wecom.customer_profile.httpx.post", side_effect=TimeoutError("timeout")
    ):
        profile = fetch_kf_customer_profile("wm_test_g4abcdef", cfg=_test_cfg())
    assert profile is None


def test_bind_with_nickname_sets_customer_name() -> None:
    saved = save_case("[客户] test", _add_car_stub(), service_lane="add_car")
    cid = str(saved["case_id"])
    ext = "wm_nick_g4abcdef"

    mock_profile = {
        "wecom_nickname": "李四",
        "wecom_avatar": "https://avatar.example/b.jpg",
        "profile_source": "kf_customer_batchget",
        "profile_fetched_at": "2026-07-10T12:00:00Z",
        "raw_available_fields": ["nickname", "avatar"],
        "real_wechat_id_available": False,
        "wecom_external_userid_suffix": "abcdef",
    }

    with patch(
        "services.fiqa_api.wecom.customer_profile.fetch_kf_customer_profile",
        return_value=mock_profile,
    ):
        bind_case_channel_identity(cid, wecom_external_userid=ext)

    case = get_case_by_id(cid)
    assert case is not None
    assert case["customer_name"] == "李四"
    identity = (case.get("extra") or {}).get("customer_identity") or {}
    assert identity.get("wecom_nickname") == "李四"
    assert identity.get("wecom_avatar") == "https://avatar.example/b.jpg"


def test_bind_with_nickname_does_not_overwrite_meaningful_name() -> None:
    saved = save_case("[客户] test", _add_car_stub(), service_lane="add_car")
    cid = str(saved["case_id"])
    update_case_customer(cid, customer_name="王五")
    ext = "wm_preserve_g4abcdef"

    mock_profile = {
        "wecom_nickname": "李四",
        "profile_source": "kf_customer_batchget",
        "profile_fetched_at": "2026-07-10T12:00:00Z",
        "wecom_external_userid_suffix": "abcdef",
    }

    with patch(
        "services.fiqa_api.wecom.customer_profile.fetch_kf_customer_profile",
        return_value=mock_profile,
    ):
        bind_case_channel_identity(cid, wecom_external_userid=ext)

    case = get_case_by_id(cid)
    assert case is not None
    assert case["customer_name"] == "王五"


def test_bind_with_no_nickname_keeps_suffix_label() -> None:
    saved = save_case("[客户] test", _add_car_stub(), service_lane="add_car")
    cid = str(saved["case_id"])
    ext = "wm_no_nick_g4abcdef"

    with patch(
        "services.fiqa_api.wecom.customer_profile.fetch_kf_customer_profile",
        return_value=None,
    ):
        bind_case_channel_identity(cid, wecom_external_userid=ext)

    case = get_case_by_id(cid)
    assert case is not None
    assert case["customer_name"] == wecom_customer_display_label(ext)
    identity = (case.get("extra") or {}).get("customer_identity") or {}
    assert identity.get("wecom_external_userid_suffix") == "abcdef"
    assert not identity.get("wecom_nickname")


def test_customer_identity_stored_in_extra_bag() -> None:
    saved = save_case("[客户] test", _add_car_stub(), service_lane="add_car")
    cid = str(saved["case_id"])
    ext = "wm_extra_g4abcdef"

    mock_profile = {
        "wecom_nickname": "赵六",
        "wecom_unionid": "oUnion456",
        "profile_source": "kf_customer_batchget",
        "profile_fetched_at": "2026-07-10T12:00:00Z",
        "raw_available_fields": ["nickname", "unionid"],
        "real_wechat_id_available": False,
        "wecom_external_userid_suffix": "abcdef",
    }

    with patch(
        "services.fiqa_api.wecom.customer_profile.fetch_kf_customer_profile",
        return_value=mock_profile,
    ):
        bind_case_channel_identity(cid, wecom_external_userid=ext)

    case = get_case_by_id(cid)
    assert case is not None
    identity = (case.get("extra") or {}).get("customer_identity") or {}
    assert identity["wecom_nickname"] == "赵六"
    assert identity["wecom_unionid"] == "oUnion456"
    assert identity["profile_source"] == "kf_customer_batchget"


def test_workbench_api_masks_full_external_userid() -> None:
    saved = save_case("[客户] test", _add_car_stub(), service_lane="add_car")
    cid = str(saved["case_id"])
    ext = "wm_mask_g4abcdef"

    mock_profile = {
        "wecom_nickname": "陈七",
        "profile_source": "kf_customer_batchget",
        "profile_fetched_at": "2026-07-10T12:00:00Z",
        "wecom_external_userid_suffix": "abcdef",
    }

    with patch(
        "services.fiqa_api.wecom.customer_profile.fetch_kf_customer_profile",
        return_value=mock_profile,
    ):
        bind_case_channel_identity(cid, wecom_external_userid=ext)

    case = get_case_by_id(cid)
    assert case is not None
    safe = sanitize_case_for_workbench_api(case)
    assert safe.get("wecom_external_userid") is None
    assert safe.get("customer_name") == "陈七"
    identity = (safe.get("extra") or {}).get("customer_identity") or {}
    assert identity.get("wecom_external_userid") is None
    assert identity.get("wecom_nickname") == "陈七"


def test_workbench_display_prefers_nickname_over_suffix() -> None:
    case = {
        "customer_name": "微信客户 · abcdef",
        "extra": {
            "customer_identity": {
                "wecom_nickname": "周八",
            }
        },
        "wecom_external_userid": "wm_display_g4abcdef",
    }
    assert resolve_wecom_workbench_display_name(case) == "周八"


def test_status_card_does_not_expose_full_external_userid() -> None:
    case = {
        "case_id": "case_status_g4",
        "customer_name": "张三",
        "service_lane": "claim",
        "claim_phase": "claim_started",
        "wecom_external_userid": "wm_secret_g4abcdef",
    }
    reply = build_claim_status_card_reply(case)
    assert "wm_secret" not in reply
    assert "abcdef" not in reply or "客户：张三" in reply
    assert "客户：张三" in reply


def test_profile_lookup_not_called_when_nickname_cached() -> None:
    saved = save_case("[客户] test", _add_car_stub(), service_lane="add_car")
    cid = str(saved["case_id"])
    ext = "wm_cached_g4abcdef"

    mock_profile = {
        "wecom_nickname": "已缓存",
        "profile_source": "kf_customer_batchget",
        "profile_fetched_at": "2026-07-10T12:00:00Z",
        "wecom_external_userid_suffix": "abcdef",
    }

    with patch(
        "services.fiqa_api.wecom.customer_profile.fetch_kf_customer_profile",
        return_value=mock_profile,
    ) as mock_fetch:
        bind_case_channel_identity(cid, wecom_external_userid=ext)
        assert mock_fetch.call_count == 1
        bind_case_channel_identity(cid, wecom_external_userid=ext)
        assert mock_fetch.call_count == 1

    assert should_fetch_kf_customer_profile({"wecom_nickname": "已缓存"}) is False


def test_claim_start_flow_still_works() -> None:
    ext = "wm_claim_g4abcdef"
    norm = normalize_text_message(
        {
            "msgid": "msg_claim_g4",
            "open_kfid": "wk001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "send_time": 1719750000,
            "text": {"content": "我要理赔"},
        }
    )

    with patch(
        "services.fiqa_api.wecom.customer_profile.fetch_kf_customer_profile",
        return_value=None,
    ):
        ingest_claim_basics_message(norm, classify_wecom_intent(norm["text"]))

    from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read

    cases = [c for c in list_all_cases_for_read() if c.get("wecom_external_userid") == ext]
    assert len(cases) == 1
    assert cases[0]["customer_name"] == "微信客户 · abcdef"


def test_add_car_start_flow_still_works() -> None:
    ext = "wm_addcar_g4abcdef"
    normalized = normalize_text_message(
        {
            "msgid": "msg_addcar_g4",
            "open_kfid": "wk001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "send_time": 1719750000,
            "text": {"content": "开始"},
        }
    )

    with patch(
        "services.fiqa_api.wecom.customer_profile.fetch_kf_customer_profile",
        return_value=None,
    ):
        create_or_attach_draft_case_for_start_click(normalized)

    from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read

    cases = [c for c in list_all_cases_for_read() if c.get("wecom_external_userid") == ext]
    assert len(cases) == 1
    assert cases[0]["customer_name"] == "微信客户 · abcdef"


def test_customer_facing_name_hides_suffix_but_shows_nickname() -> None:
    assert wecom_customer_facing_display_name("微信客户 · abc123") == "微信客户"
    assert wecom_customer_facing_display_name("真实昵称") == "真实昵称"


def test_merge_customer_identity_preserves_existing() -> None:
    existing = {"wecom_nickname": "旧名", "profile_fetched_at": "2026-07-01T00:00:00Z"}
    profile = {
        "wecom_nickname": "新名",
        "profile_fetched_at": "2026-07-10T12:00:00Z",
        "profile_source": "kf_customer_batchget",
    }
    merged = merge_customer_identity(existing, profile, external_userid="wm_merge_g4abcdef")
    assert merged["wecom_nickname"] == "新名"
    assert merged["wecom_external_userid_suffix"] == "abcdef"


def test_is_generic_treats_suffix_as_generic() -> None:
    assert is_generic_wecom_customer_name("微信客户 · abcdef")
    assert not is_generic_wecom_customer_name("张三")
