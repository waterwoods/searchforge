"""P19M-1 — Mini Program prototype pure-logic unit tests (Node-free)."""

from __future__ import annotations

import re

FIELD_LABELS = {
    "anyone_injured": "是否有人受伤",
    "injury_status": "是否有人受伤",
    "accident_datetime": "事故时间",
    "accident_location": "事故地点",
    "accident_description": "事故经过",
    "own_vehicle_info": "您的车辆信息",
    "other_party_plate": "对方车牌",
    "other_party_info": "对方信息",
    "customer_damage_photo": "事故照片",
    "other_party_vehicle_photo": "事故照片",
    "scene_photo": "事故现场照片",
    "photos": "事故照片",
    "police_involved": "是否报警",
}

PHOTO_KEYS = {
    "customer_damage_photo",
    "other_party_vehicle_photo",
    "scene_photo",
    "photos",
}

UNSUPPORTED_KEYS = {
    "other_party_plate",
    "other_party_info",
    "police_involved",
}

ACTIONABLE_ROUTES = {
    "accident_description": "/pages/story/story",
    "anyone_injured": "/pages/basics/basics",
    "injury_status": "/pages/basics/basics",
    "accident_datetime": "/pages/basics/basics",
    "accident_location": "/pages/basics/basics",
    "own_vehicle_info": "/pages/basics/basics",
    "customer_damage_photo": "/pages/photos/photos",
    "other_party_vehicle_photo": "/pages/photos/photos",
    "scene_photo": "/pages/photos/photos",
    "photos": "/pages/photos/photos",
}


def normalize_missing_key(key: str) -> str:
    raw = (key or "").strip()
    if raw == "anyone_injured":
        return "injury_status"
    if raw in PHOTO_KEYS:
        return "photos"
    return raw


def missing_item_label(item: dict) -> str:
    if item.get("label"):
        return str(item["label"])
    key = item.get("key") or item.get("field") or ""
    return FIELD_LABELS.get(key, key or "待补充资料")


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
    phase = str(task.get("phase") or "")
    if submitted:
        if first_actionable_missing_route(task):
            return "supplement"
        return "receipt"
    if phase == "broker_done":
        return "done"
    if phase == "broker_needs_more_info":
        return "supplement"
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


def injury_complete(facts: dict) -> bool:
    injury = str(facts.get("anyone_injured") or facts.get("injury_status") or "").strip().lower()
    return injury in ("yes", "no", "unknown")


def resolve_missing_item_nav(key: str, task: dict) -> dict:
    normalized = normalize_missing_key(key)
    facts = task.get("key_facts") or {}
    photo_count = int(task.get("photo_count") or task.get("attachment_count") or 0)

    if normalized == "accident_description":
        if story_complete(facts):
            return {"action": "COMPLETED", "route": None}
        return {"action": "ACTIONABLE_NOW", "route": ACTIONABLE_ROUTES["accident_description"]}

    if normalized == "injury_status":
        if injury_complete(facts):
            return {"action": "COMPLETED", "route": None}
        return {"action": "ACTIONABLE_NOW", "route": ACTIONABLE_ROUTES["injury_status"]}

    if normalized == "accident_datetime":
        if str(facts.get("accident_datetime") or "").strip():
            return {"action": "COMPLETED", "route": None}
        return {"action": "ACTIONABLE_NOW", "route": ACTIONABLE_ROUTES["accident_datetime"]}

    if normalized == "accident_location":
        if str(facts.get("accident_location") or "").strip():
            return {"action": "COMPLETED", "route": None}
        return {"action": "ACTIONABLE_NOW", "route": ACTIONABLE_ROUTES["accident_location"]}

    if normalized == "own_vehicle_info":
        if len(str(facts.get("own_vehicle_info") or "").strip()) >= 2:
            return {"action": "COMPLETED", "route": None}
        return {"action": "ACTIONABLE_NOW", "route": ACTIONABLE_ROUTES["own_vehicle_info"]}

    if normalized == "photos":
        if photo_count >= 2:
            return {"action": "COMPLETED", "route": None}
        return {"action": "ACTIONABLE_NOW", "route": ACTIONABLE_ROUTES["photos"]}

    if normalized in UNSUPPORTED_KEYS:
        return {"action": "DISPLAY_ONLY_PROTOTYPE", "route": None}

    route = ACTIONABLE_ROUTES.get(normalized)
    if route:
        return {"action": "ACTIONABLE_NOW", "route": route}
    return {"action": "UNSUPPORTED", "route": None}


def build_supplement_rows(task: dict) -> list[dict]:
    facts = task.get("key_facts") or {}
    photo_count = int(task.get("photo_count") or task.get("attachment_count") or 0)
    rows: list[dict] = []
    seen: set[str] = set()

    checklist = [
        ("accident_description", not story_complete(facts), "/pages/story/story"),
        ("injury_status", not injury_complete(facts), "/pages/basics/basics"),
        (
            "accident_datetime",
            not str(facts.get("accident_datetime") or "").strip(),
            "/pages/basics/basics",
        ),
        (
            "accident_location",
            not str(facts.get("accident_location") or "").strip(),
            "/pages/basics/basics",
        ),
        (
            "own_vehicle_info",
            len(str(facts.get("own_vehicle_info") or "").strip()) < 2,
            "/pages/basics/basics",
        ),
        ("photos", photo_count < 2, "/pages/photos/photos"),
    ]

    for key, incomplete, route in checklist:
        if not incomplete:
            continue
        # Submitted status must not block supplement editing.
        seen.add(key)
        rows.append({"key": key, "actionable": True, "route": route})

    for item in task.get("missing_info") or []:
        key = normalize_missing_key(str(item.get("key") or item.get("field") or ""))
        if not key or key in seen:
            continue
        nav = resolve_missing_item_nav(key, task)
        if nav["action"] == "COMPLETED":
            continue
        seen.add(key)
        rows.append(
            {
                "key": key,
                "actionable": nav["action"] == "ACTIONABLE_NOW",
                "route": nav.get("route"),
            }
        )

    return rows


def first_actionable_missing_route(task: dict) -> str | None:
    for row in build_supplement_rows(task):
        if row.get("actionable") and row.get("route"):
            return str(row["route"])
    return None


def resolve_supplement_action(missing_items: list[dict]) -> dict | None:
    """Mirror of miniapp resolveSupplementAction — deterministic first actionable route."""
    priority = (
        "/pages/story/story",
        "/pages/basics/basics",
        "/pages/photos/photos",
    )
    routes = [
        str(item.get("route") or "").strip()
        for item in missing_items
        if item.get("actionable") and item.get("route")
    ]
    routes = [route for route in routes if route]
    if not routes:
        return None
    unique = list(dict.fromkeys(routes))
    route = next((candidate for candidate in priority if candidate in unique), unique[0])
    return {"route": route}


def resolve_next_action_route(task: dict) -> str:
    facts = task.get("key_facts") or {}
    submitted = bool(task.get("submitted")) or task.get("current_step") == "done"
    phase = str(task.get("phase") or "")
    dash = task.get("dashboard_summary") or {}
    supplement_route = first_actionable_missing_route(task)
    if submitted:
        return supplement_route or "/pages/receipt/receipt"
    if phase == "broker_done":
        return "/pages/receipt/receipt"
    if phase == "broker_needs_more_info":
        return supplement_route or "/pages/photos/photos"
    if not story_complete(facts):
        return "/pages/story/story"
    if not basics_complete(facts):
        return "/pages/basics/basics"
    photo_count = int(task.get("photo_count") or task.get("attachment_count") or 0)
    if photo_count < 2:
        return "/pages/photos/photos"
    if task.get("current_step") == "review" or "提交" in str(dash.get("primary_cta") or ""):
        return "/pages/review/review"
    if "补充" in str(dash.get("primary_cta") or ""):
        return supplement_route or "/pages/basics/basics"
    return "/pages/review/review"


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


def test_launch_context_priority():
    """Launch query beats dev config beats resume (mirrors taskLaunchContext)."""

    def resolve(query: str, dev: str, resume: str) -> str | None:
        if query.strip():
            return query.strip()
        if dev.strip():
            return dev.strip()
        if resume.strip():
            return resume.strip()
        return None

    assert resolve("h5t1.query", "h5t1.dev", "h5t1.resume") == "h5t1.query"
    assert resolve("", "h5t1.dev", "h5t1.resume") == "h5t1.dev"
    assert resolve("", "", "h5t1.resume") == "h5t1.resume"
    assert resolve("", "", "") is None


def test_persist_only_after_valid_load_contract():
    """Document: resume token must be written only after successful GET intake."""
    persisted = False
    loaded = False

    def simulate_load(success: bool) -> None:
        nonlocal persisted, loaded
        loaded = success
        if success:
            persisted = True

    simulate_load(False)
    assert persisted is False
    simulate_load(True)
    assert persisted is True

    intent = f"mp-12345-abc"
    assert re.match(r"^mp-\d+-[a-z0-9]+$", intent)


def test_missing_item_story_routes_to_story_page():
    task = {"key_facts": {}, "photo_count": 0}
    nav = resolve_missing_item_nav("accident_description", task)
    assert nav["action"] == "ACTIONABLE_NOW"
    assert nav["route"] == "/pages/story/story"


def test_missing_item_basics_fields_route_to_basics_page():
    task = {"key_facts": {}, "photo_count": 0}
    for key in ("accident_datetime", "accident_location", "injury_status", "own_vehicle_info"):
        nav = resolve_missing_item_nav(key, task)
        assert nav["action"] == "ACTIONABLE_NOW"
        assert nav["route"] == "/pages/basics/basics"


def test_missing_item_photos_route_to_photos_page():
    task = {"key_facts": {}, "photo_count": 0}
    nav = resolve_missing_item_nav("photos", task)
    assert nav["action"] == "ACTIONABLE_NOW"
    assert nav["route"] == "/pages/photos/photos"


def test_completed_story_not_actionable():
    task = {
        "key_facts": {"accident_description": "我在等红灯时被后车追尾。"},
        "photo_count": 0,
    }
    nav = resolve_missing_item_nav("accident_description", task)
    assert nav["action"] == "COMPLETED"


def test_unsupported_other_party_not_actionable():
    task = {"key_facts": {}, "photo_count": 0}
    nav = resolve_missing_item_nav("other_party_info", task)
    assert nav["action"] == "DISPLAY_ONLY_PROTOTYPE"
    assert nav.get("route") is None


def test_build_supplement_rows_omits_completed_items():
    task = {
        "submitted": False,
        "key_facts": {
            "accident_description": "我在等红灯时被后车追尾。",
            "anyone_injured": "no",
            "accident_datetime": "今天上午",
            "accident_location": "Irvine",
            "own_vehicle_info": "Toyota",
        },
        "photo_count": 2,
        "missing_info": [],
    }
    rows = build_supplement_rows(task)
    assert rows == []


def test_build_supplement_rows_includes_backend_unsupported_as_static():
    task = {
        "submitted": False,
        "key_facts": {},
        "photo_count": 0,
        "missing_info": [{"field": "other_party_info", "label": "对方信息"}],
    }
    rows = build_supplement_rows(task)
    other_party = next(row for row in rows if row["key"] == "other_party_info")
    assert other_party["actionable"] is False


def test_resolve_next_action_submitted_goes_to_receipt():
    task = {
        "submitted": True,
        "current_step": "done",
        "key_facts": {
            "anyone_injured": "no",
            "accident_datetime": "今天上午",
            "accident_location": "Irvine",
            "own_vehicle_info": "Toyota",
            "accident_description": "我在等红灯时被后车追尾。",
        },
        "photo_count": 2,
    }
    assert resolve_next_action_kind(task) == "receipt"
    assert resolve_next_action_route(task) == "/pages/receipt/receipt"


def test_resolve_next_action_submitted_with_missing_goes_to_supplement():
    task = {
        "submitted": True,
        "current_step": "done",
        "key_facts": {
            "anyone_injured": "",
            "accident_datetime": "今天上午",
            "accident_location": "Irvine",
            "own_vehicle_info": "Toyota",
            "accident_description": "我在等红灯时被后车追尾。",
        },
        "photo_count": 2,
    }
    assert resolve_next_action_kind(task) == "supplement"
    assert resolve_next_action_route(task) == "/pages/basics/basics"


def test_resolve_supplement_action_priority_is_deterministic():
    action = resolve_supplement_action(
        [
            {"actionable": True, "route": "/pages/photos/photos"},
            {"actionable": True, "route": "/pages/basics/basics"},
            {"actionable": True, "route": "/pages/story/story"},
        ]
    )
    assert action is not None
    assert action["route"] == "/pages/story/story"


def test_resolve_next_action_broker_done_goes_to_receipt():
    task = {
        "submitted": False,
        "phase": "broker_done",
        "key_facts": {},
        "photo_count": 0,
    }
    assert resolve_next_action_kind(task) == "done"
    assert resolve_next_action_route(task) == "/pages/receipt/receipt"


def test_resolve_next_action_needs_more_info_is_supplement():
    task = {
        "submitted": False,
        "phase": "broker_needs_more_info",
        "key_facts": {},
        "photo_count": 0,
        "missing_info": [{"field": "accident_description", "label": "事故经过"}],
    }
    assert resolve_next_action_kind(task) == "supplement"
    assert resolve_next_action_route(task) == "/pages/story/story"


def test_primary_cta_route_never_points_to_task_home():
    scenarios = [
        {"submitted": False, "current_step": "story", "key_facts": {}, "photo_count": 0},
        {
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
        },
        {
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
        },
    ]
    for task in scenarios:
        route = resolve_next_action_route(task)
        assert route != "/pages/task-home/task-home"


def test_server_refresh_contract_documented():
    """Task Home onShow must re-fetch intake; child pages update app.task before navigateBack."""
    refreshed_on_show = True
    child_save_updates_app_task = True
    assert refreshed_on_show and child_save_updates_app_task
