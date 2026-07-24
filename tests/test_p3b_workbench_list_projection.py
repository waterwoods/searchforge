"""P3-B Slice 1 — Workbench list projection, search, TEST identity."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.case_ref import reset_json_case_ref_counter_for_tests
from services.fiqa_api.inbox_triage.workbench_list_projection import (
    attach_workbench_list_projection,
    build_workbench_list_projection,
    case_matches_workbench_search,
    resolve_customer_display_name,
)


def setup_function():
    reset_json_case_ref_counter_for_tests(1000)


def test_list_projection_fields_and_human_labels():
    case = {
        "case_id": "case_deadbeef0012",
        "case_ref": "CLM-1028",
        "customer_name": "陈明",
        "customer_phone": "6265552345",
        "policy_number": "POL-998877",
        "primary_vehicle_summary": "2021 Toyota Camry",
        "known_facts": {"qa_label": "Founder-iPhone", "accident_description": "倒车碰撞"},
        "workbench_test": False,
        "updated_at": "2026-07-23T12:00:00Z",
        "constitution_projection": {
            "current_stage": "waiting_broker",
            "customer": {"today": "先不用操作"},
            "broker": {
                "next_action": {"label": "等待办公室审核", "enabled": True},
                "queue_summary": {"label": "客户已完成，等你审核"},
            },
        },
    }
    proj = build_workbench_list_projection(case)
    assert proj["case_ref"] == "CLM-1028"
    assert proj["customer_display_name"] == "陈明"
    assert proj["phone_last_four"] == "2345"
    assert proj["policy_suffix"] == "8877"
    assert proj["vehicle_summary"] == "2021 Toyota Camry"
    assert proj["qa_label"] == "Founder-iPhone"
    assert proj["is_test"] is False
    assert proj["customer_current_action_label"] == "先不用操作"
    assert proj["broker_next_action_label"] == "等待办公室审核"
    assert "倒车" in proj["latest_meaningful_summary"]
    assert proj["filter_bucket"] == "waiting_broker"
    # Never expose raw workflow code as primary.
    assert "BROKER_REVIEW" not in proj["customer_current_action_label"]
    assert "BROKER_REVIEW" not in proj["broker_next_action_label"]


def test_test_case_identity_uses_wechat_suffix_not_qa_customer():
    case = {
        "case_id": "case_ab12cd34ef56",
        "customer_name": "QA Customer",
        "person_link_key": "opaque_link_key_zzab12",
        "workbench_test": True,
        "known_facts": {"qa_label": "Founder-iPhone"},
    }
    name = resolve_customer_display_name(case)
    assert name == "微信客户 · ab12"
    assert "QA Customer" not in name
    proj = build_workbench_list_projection(case)
    assert proj["customer_display_name"] == "微信客户 · ab12"
    assert proj["qa_label"] == "Founder-iPhone"
    assert proj["is_test"] is True


def test_display_name_priority_remark_then_real_name_then_nickname():
    # 1) office/broker remark wins when present
    with_remark = {
        "case_id": "case_r1",
        "customer_name": "真实姓名",
        "extra": {
            "customer_identity": {
                "wecom_remark": "办公室备注·陈总熟人",
                "wecom_nickname": "微信昵称甲",
            }
        },
    }
    assert resolve_customer_display_name(with_remark) == "办公室备注·陈总熟人"

    # 2) real customer_name before nickname
    with_name = {
        "case_id": "case_r2",
        "customer_name": "陈明",
        "extra": {"customer_identity": {"wecom_nickname": "微信昵称乙"}},
    }
    assert resolve_customer_display_name(with_name) == "陈明"

    # 3) nickname when no real name
    with_nick = {
        "case_id": "case_r3",
        "customer_name": "QA Customer",
        "extra": {"customer_identity": {"wecom_nickname": "小明爸"}},
    }
    assert resolve_customer_display_name(with_nick) == "小明爸"


def test_never_shows_wx_or_openid_as_primary_name():
    case = {
        "case_id": "case_leak001",
        "customer_name": "wx_abcdef1234567890",
        "person_link_key": "wx_zz99ab12",
        "customer_phone": "6265558888",
    }
    name = resolve_customer_display_name(case)
    assert not name.startswith("wx_")
    assert "openid" not in name.lower()
    assert name == "微信客户 · ab12"
    proj = build_workbench_list_projection(case)
    assert "wx_" not in proj["customer_display_name"]
    assert proj["customer_display_name"] == "微信客户 · ab12"


def test_search_matches_case_ref_phone_vehicle_qa_label():
    case = {
        "case_id": "case_92da6e0bcfce",
        "case_ref": "CLM-1031",
        "customer_name": "",
        "customer_phone": "6265559999",
        "person_link_key": "key_suffix_ab12",
        "primary_vehicle_summary": "2021 Toyota Camry",
        "known_facts": {"qa_label": "Founder-iPhone"},
        "workbench_test": True,
    }
    attach_workbench_list_projection(case)
    assert case_matches_workbench_search(case, "CLM-1031")
    assert case_matches_workbench_search(case, "founder-iphone")
    assert case_matches_workbench_search(case, "9999")
    assert case_matches_workbench_search(case, "camry")
    assert case_matches_workbench_search(case, "92da6e0b")
    assert case_matches_workbench_search(case, "case_92da6e0bcfce")
    assert not case_matches_workbench_search(case, "missing-token")


def test_idle_broker_label_falls_back_to_open_case():
    case = {
        "case_id": "case_idle1",
        "case_ref": "CLM-3001",
        "constitution_projection": {
            "broker": {"next_action": {"label": "暂无动作", "enabled": False}},
        },
    }
    proj = build_workbench_list_projection(case)
    assert proj["broker_next_action_label"] == "打开案件核对"
    assert "暂无动作" not in proj["broker_next_action_label"]


def test_internal_broker_step_codes_are_humanized():
    case = {
        "case_id": "case_code1",
        "case_ref": "CLM-3002",
        "broker_next_step": "review_ready",
    }
    proj = build_workbench_list_projection(case)
    assert proj["broker_next_action_label"] == "客户已完成，请审核"
    assert "review_ready" not in proj["broker_next_action_label"]

    eng = {
        "case_id": "case_code2",
        "case_ref": "CLM-3003",
        "broker_next_step": "Customer is completing default intake; review when ready.",
    }
    assert build_workbench_list_projection(eng)["broker_next_action_label"] == "客户填写中"


def test_test_filter_bucket_via_is_test_flag():
    test_case = {
        "case_id": "case_t1",
        "case_ref": "CLM-2001",
        "workbench_test": True,
        "waiting_on": "client",
    }
    real_case = {
        "case_id": "case_r1",
        "case_ref": "CLM-2002",
        "workbench_test": False,
        "waiting_on": "broker",
    }
    tp = build_workbench_list_projection(test_case)
    rp = build_workbench_list_projection(real_case)
    assert tp["is_test"] is True
    assert rp["is_test"] is False
    assert tp["filter_bucket"] == "waiting_customer"
    assert rp["filter_bucket"] == "waiting_broker"
