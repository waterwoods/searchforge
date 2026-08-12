"""Voice-First post-QA hardening — Chinese STT transcript extraction quality.

Driven by a real iPhone QA run whose Chirp transcript used ASCII commas and
dropped a character. That exposed three defects, each locked down here:

  1. clause windows ran across ASCII "," and swallowed the whole narrative
  2. an unbounded hedge regex discarded an explicit "我们都没有受伤"
  3. the model sentinel "unknown" was stored as if it were a real time value

Everything runs through the existing accident_story_assistant LangGraph.
"""

from __future__ import annotations

from services.fiqa_api.inbox_triage.accident_story_assistant.contract import (
    time_needs_refinement,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.extractors import (
    extract_injury_status,
    extract_location_text,
    extract_time_text,
    extract_vehicles,
    is_grounded_in_source,
    is_sentinel_text,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.graph import propose_from_story

# Verbatim Chirp output from the successful real-phone QA run.
REAL_PHONE_TRANSCRIPT = (
    "天在当趟圣安纳开车的时候,在十字路口被人追尾了,"
    "我感觉好像没问题,对方司机也没有受伤,我们都没有受伤。"
)


def _questions(proposal: dict) -> list[str]:
    return list(proposal.get("followup_questions") or [])


# ---------------------------------------------------------------------------
# Real-phone regression
# ---------------------------------------------------------------------------


def test_real_phone_transcript_location_is_not_the_whole_narrative():
    location, _conf = extract_location_text(REAL_PHONE_TRANSCRIPT)
    assert location == "圣安纳"
    assert "追尾" not in location
    assert "受伤" not in location
    assert len(location) < 20


def test_real_phone_transcript_explicit_no_injury_is_respected():
    injury, _conf, conflicts = extract_injury_status(REAL_PHONE_TRANSCRIPT)
    assert injury == "no"
    assert "injury_hedged_contradiction" not in conflicts


def test_real_phone_transcript_asks_time_not_injury():
    proposal = propose_from_story(raw_story=REAL_PHONE_TRANSCRIPT)
    missing = proposal["missing_required_facts"]
    assert "accident_datetime" in missing
    assert "injury_status" not in missing
    assert proposal["injury_status"] == "no"
    assert len(_questions(proposal)) <= 3


def test_ascii_comma_clauses_are_bounded():
    """Chinese STT emits ASCII "," — clause windows must stop there."""
    story = "今天在 Irvine 停车场撞了,对方说没事,我们都没有受伤。"
    location, _conf = extract_location_text(story)
    assert "对方" not in location
    assert "受伤" not in location


# ---------------------------------------------------------------------------
# Required Chinese voice matrix
# ---------------------------------------------------------------------------


def test_case_1_rear_end_san_jose_injury_still_missing():
    story = "昨天下午三点左右，我在 San Jose 被追尾了。"
    proposal = propose_from_story(raw_story=story)
    assert proposal["accident_time_text"] == "昨天下午三点左右"
    assert time_needs_refinement(proposal["accident_time_text"]) is False
    assert proposal["accident_location_text"] == "San Jose"
    assert proposal["injury_status"] == "unknown"
    assert proposal["missing_required_facts"] == ["injury_status"]
    assert len(_questions(proposal)) == 1
    assert "受伤" in _questions(proposal)[0]


def test_case_2_santa_ana_intersection_no_injury_question():
    story = "我昨天在 Santa Ana 开车，在一个十字路口被人追尾了，我们都没有受伤。"
    proposal = propose_from_story(raw_story=story)
    location = proposal["accident_location_text"]
    assert "Santa Ana" in location
    assert "追尾" not in location
    assert proposal["injury_status"] == "no"
    assert "injury_status" not in proposal["missing_required_facts"]
    assert len(_questions(proposal)) <= 3


def test_case_3_irvine_parking_lot_backing_collision():
    story = "今天早上在 Irvine 停车场倒车的时候撞到了另一辆车。"
    proposal = propose_from_story(raw_story=story)
    assert proposal["accident_time_text"] == "今天早上"
    assert proposal["accident_location_text"] == "Irvine 停车场"
    # Fault and injury were never stated — they must not be invented.
    assert proposal["injury_status"] == "unknown"
    assert "injury_status" in proposal["missing_required_facts"]


def test_case_4_bare_story_invents_nothing():
    proposal = propose_from_story(raw_story="刚才出事故了。")
    assert proposal["accident_location_text"] == ""
    assert proposal["involved_vehicles"] == []
    assert proposal["injury_status"] == "unknown"
    assert time_needs_refinement(proposal["accident_time_text"]) is True
    missing = proposal["missing_required_facts"]
    assert "accident_datetime" in missing
    assert "accident_location" in missing
    assert "injury_status" in missing
    assert len(_questions(proposal)) <= 3


def test_case_5_mixed_language_keeps_location_concise_and_vehicle_as_stated():
    story = "昨天下午在 Santa Ana 的 Wells Fargo parking lot 被一辆 pickup 撞了。"
    proposal = propose_from_story(raw_story=story)
    location = proposal["accident_location_text"]
    assert "Santa Ana" in location
    assert "Wells Fargo" in location
    assert "撞" not in location
    assert any("pickup" in v.lower() for v in proposal["involved_vehicles"])


# ---------------------------------------------------------------------------
# Model output may be cleaner, but never ungrounded
# ---------------------------------------------------------------------------


def test_model_sentinel_time_is_dropped_and_asked_instead():
    def llm(_text: str) -> dict:
        return {"accident_time_text": "unknown", "accident_location_text": "San Jose"}

    proposal = propose_from_story(raw_story="在 San Jose 被追尾了。", llm_caller=llm)
    assert proposal["accident_time_text"] == ""
    assert "accident_datetime" in proposal["missing_required_facts"]


def test_grounded_model_location_replaces_narrative_deterministic_value():
    story = "我昨天在 Santa Ana 开车，在一个十字路口被人追尾了。"

    def llm(_text: str) -> dict:
        return {"accident_location_text": "Santa Ana 的一个十字路口"}

    proposal = propose_from_story(raw_story=story, llm_caller=llm)
    assert proposal["accident_location_text"] == "Santa Ana 的一个十字路口"


def test_ungrounded_model_time_and_vehicle_are_rejected():
    def llm(_text: str) -> dict:
        return {
            "accident_time_text": "2026-08-01 15:00",
            "accident_location_text": "Oakland",
            "involved_vehicles": ["Tesla Model 3"],
        }

    proposal = propose_from_story(raw_story="刚才被追尾了。", llm_caller=llm)
    assert proposal["accident_time_text"] == ""
    assert proposal["accident_location_text"] == ""
    assert proposal["involved_vehicles"] == []


def test_hedged_contradiction_still_collapses_to_unknown():
    story = "好像有人受伤，也可能没有。"
    injury, _conf, conflicts = extract_injury_status(story)
    assert injury == "unknown"
    assert "injury_hedged_contradiction" in conflicts


# ---------------------------------------------------------------------------
# Helper units
# ---------------------------------------------------------------------------


def test_sentinel_detection():
    for value in ("unknown", "未知", "N/A", "不详", "待确认", "none"):
        assert is_sentinel_text(value) is True
    for value in ("昨天下午", "San Jose", "圣安纳"):
        assert is_sentinel_text(value) is False


def test_grounding_helper():
    source = "昨天下午在 Santa Ana 的十字路口被追尾"
    assert is_grounded_in_source("Santa Ana 的十字路口", source) is True
    assert is_grounded_in_source("Oakland", source) is False
    assert is_grounded_in_source("下午三点", source) is False


def test_vehicles_only_when_stated():
    assert extract_vehicles("被一辆 pickup 撞了") == ["pickup"]
    assert extract_vehicles("被人追尾了") == []


def test_time_extraction_handles_spoken_chinese_numerals():
    assert extract_time_text("昨天下午三点左右被追尾")[0] == "昨天下午三点左右"
    assert extract_time_text("今天早上八点半在停车场")[0] == "今天早上八点半"
