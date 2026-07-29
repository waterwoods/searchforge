"""QA / Founder harness scenario keys for C01.

Capability-facing helpers so Workflow / Cap 03 wiring never import adapter
fixture modules directly.
"""

from __future__ import annotations

from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import SCENARIO_KEYS

# Founder QA / DevTools aliases (honored only when mock flag is on).
_SCENARIO_ALIASES: dict[str, str] = {
    "S1": "S1_existing_active",
    "S2": "S2_multi_vehicle",
    "S3": "S3_no_active",
    "S4": "S4_stale_policy",
    "S5": "S5_no_mapping",
    "S6": "S6_unavailable",
    "AMBIGUOUS": "AMBIGUOUS",
}


def list_qa_scenario_keys() -> dict[str, str]:
    return dict(SCENARIO_KEYS)


def person_link_for_mock_scenario(mock_scenario: str | None) -> str | None:
    """Map S1…S6 / long ids → mock person_link_key. None if unknown."""
    raw = str(mock_scenario or "").strip()
    if not raw:
        return None
    upper = raw.upper()
    scenario_id = _SCENARIO_ALIASES.get(upper) or raw
    if scenario_id in SCENARIO_KEYS:
        return SCENARIO_KEYS[scenario_id]
    if raw.startswith("wx_mock_cap01_"):
        return raw
    return None
