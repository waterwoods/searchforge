"""P19M-1 — Mini Program prototype pure-logic unit tests (Node-free)."""

from __future__ import annotations

import re


def extract_token_from_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    without_query = raw.split("?")[0]
    segment = without_query.rstrip("/").split("/")[-1]
    if segment.startswith("h5t1."):
        return segment
    return ""


def story_complete(facts: dict) -> bool:
    return len(str(facts.get("accident_description") or "").strip()) >= 10


def basics_complete(facts: dict) -> bool:
    injury = str(facts.get("anyone_injured") or facts.get("injury_status") or "").strip().lower()
    has_injury = injury in ("yes", "no", "unknown")
    has_time = bool(str(facts.get("accident_datetime") or "").strip())
    has_location = bool(str(facts.get("accident_location") or "").strip())
    has_vehicle = len(str(facts.get("own_vehicle_info") or "").strip()) >= 2
    return has_injury and has_time and has_location and has_vehicle


def resolve_next_action_kind(task: dict) -> str:
    facts = task.get("key_facts") or {}
    submitted = bool(task.get("submitted")) or task.get("current_step") == "done"
    if submitted:
        return "receipt"
    if not story_complete(facts):
        return "story"
    if not basics_complete(facts):
        return "basics"
    photo_count = int(task.get("photo_count") or task.get("attachment_count") or 0)
    if photo_count < 2:
        return "photos"
    if task.get("current_step") == "review":
        return "review"
    return "review"


def test_extract_token_from_claim_intake_url():
    url = "https://example.test/task/claim/h5t1.abc.def"
    assert extract_token_from_url(url) == "h5t1.abc.def"


def test_extract_token_from_evidence_upload_url():
    url = "https://example.test/task/upload/h5t1.upload.token"
    assert extract_token_from_url(url) == "h5t1.upload.token"


def test_story_complete_threshold():
    assert story_complete({"accident_description": "短"}) is False
    assert story_complete({"accident_description": "我在等红灯时被追尾。"}) is True


def test_basics_complete_requires_all_fields():
    facts = {
        "anyone_injured": "no",
        "accident_datetime": "今天上午",
        "accident_location": "Irvine",
        "own_vehicle_info": "Toyota Camry",
    }
    assert basics_complete(facts) is True
    facts.pop("accident_location")
    assert basics_complete(facts) is False


def test_resolve_next_action_story_first():
    task = {
        "submitted": False,
        "current_step": "story",
        "key_facts": {},
        "photo_count": 0,
    }
    assert resolve_next_action_kind(task) == "story"


def test_resolve_next_action_photos_after_basics():
    task = {
        "submitted": False,
        "current_step": "evidence",
        "key_facts": {
            "anyone_injured": "no",
            "accident_datetime": "今天上午",
            "accident_location": "Irvine",
            "own_vehicle_info": "Toyota",
            "accident_description": "我在等红灯时被后车追尾。",
        },
        "photo_count": 1,
    }
    assert resolve_next_action_kind(task) == "photos"


def test_resolve_next_action_review_when_ready():
    task = {
        "submitted": False,
        "current_step": "review",
        "key_facts": {
            "anyone_injured": "no",
            "accident_datetime": "今天上午",
            "accident_location": "Irvine",
            "own_vehicle_info": "Toyota",
            "accident_description": "我在等红灯时被后车追尾。",
        },
        "photo_count": 2,
    }
    assert resolve_next_action_kind(task) == "review"


def test_submit_intent_id_format():
    intent = f"mp-12345-abc"
    assert re.match(r"^mp-\d+-[a-z0-9]+$", intent)
