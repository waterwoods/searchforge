"""Contact-gap tail policy: prior-thread counting + intent-aware short tails (outline §4.10)."""

from services.fiqa_api.inbox_triage.triage import _count_prior_system_contact_gap_tails_in_thread


def test_count_prior_contact_gap_zh_detects_long_and_short_markers():
    mt = (
        "[系统] 收到。若姓名或电话尚未在本对话中写清，办公室后续联系时可能会先确认联系方式。\n\n"
        "[系统] 好的。（若方便：请在本对话补一行姓名与电话，便于办公室联系。）\n\n"
        "[客户] 大概多久能出报价？"
    )
    assert _count_prior_system_contact_gap_tails_in_thread(mt, "zh") == 2


def test_count_prior_contact_gap_en():
    mt = (
        "[系统] Thanks. If your name or phone isn't clear on this record yet, the office may confirm.\n\n"
        "[客户] How long for a quote?"
    )
    assert _count_prior_system_contact_gap_tails_in_thread(mt, "en") == 1


def test_count_prior_contact_gap_no_system_segments():
    assert _count_prior_system_contact_gap_tails_in_thread("[客户] 你好", "zh") == 0
