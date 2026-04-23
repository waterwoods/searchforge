"""
Append / continuation boundary customer-visible copy: engine defaults + client stitched merge.

Classification (`_classify_append_case_boundary`) stays in triage; this module only holds
defaults and the merge of `stitched.append_boundary` over them (per docs: no cross-client fallback).
"""

from __future__ import annotations

from typing import Any

# Engine defaults; merged with stitched.append_boundary per client (no cross-client fallback).
APPEND_BOUNDARY_DEFAULTS: dict[str, Any] = {
    "continuity_zh": {
        "add_car": "本条加车记录办公室在跟进中；",
        "claim": "理赔这边办公室会继续跟进。",
        "remove_car": "车辆变更这边办公室会继续跟进。",
        "payment": "付款/通知相关办公室会继续跟进。",
        "missing_doc": "材料补件这边办公室会继续跟进。",
        "premium": "续保/保费这边办公室会继续跟进。",
        "generic": "前一件事办公室会继续跟进。",
    },
    "new_issue_tail_zh": {
        "claim": "您这条理赔我先转给办公室，请他们尽快联系您。",
        "billing": "账单问题我也一起转给办公室核实。",
        "remove_car": "删车/卖车我也转给办公室一并处理。",
        "premium": "续保/保费相关我也转给办公室一并跟进。",
        "add_car": "加车报价需求我也转给办公室一并处理。",
        "default": "您这条新问题我也转给办公室一并处理。",
    },
    "continuity_en_add_car": "We'll keep your add-car quote with the office. ",
    "continuity_en_other": "We'll keep your prior request with the office. ",
    "new_issue_tail_en": {
        "claim": "I've flagged this claim item for them to follow up.",
        "billing": "I've asked them to review the billing question too.",
        "remove_car": "I've included the vehicle-removal request as well.",
        "premium": "I've also flagged the renewal/premium question for the office.",
        "add_car": "I've passed along the new vehicle quote request as well.",
        "default": "I've shared this new item with them to handle.",
    },
    "add_car_split_hint_zh": (
        " 如属完全不同的事项，建议您用「提交新问题」另开服务记录，不要和本条加车混在同一对话里。"
    ),
    "add_car_split_hint_en": (
        " If this is a separate topic, please start a new request next time so the office can track it cleanly."
    ),
    "borderline_zh": "收到。我先按您这条整理给办公室；如果和前面不是同一件事，也请简单说明一下，方便分开跟进。",
    "borderline_en": (
        "Got it—I'm forwarding this to the office. "
        "If this is separate from what we discussed before, a quick note helps us track it cleanly."
    ),
}


def merge_append_boundary_str_subdict(base: dict[str, str], override: Any) -> dict[str, str]:
    out = dict(base)
    if not isinstance(override, dict):
        return out
    for k, v in override.items():
        if isinstance(v, str) and v.strip():
            out[str(k)] = v.strip()
    return out


def merged_append_boundary_copy(
    client_id: str | None,
    stitched_phrases: dict[str, Any],
) -> dict[str, Any]:
    """
    Merge client `stitched.append_boundary` over engine defaults.
    `stitched_phrases` is the full stitched map from the same source as triage (cached getter).
    """
    d = APPEND_BOUNDARY_DEFAULTS
    raw_any = stitched_phrases.get("append_boundary")
    raw = raw_any if isinstance(raw_any, dict) else {}
    continuity_zh = merge_append_boundary_str_subdict(d["continuity_zh"], raw.get("continuity_zh"))
    new_issue_tail_zh = merge_append_boundary_str_subdict(d["new_issue_tail_zh"], raw.get("new_issue_tail_zh"))
    new_issue_tail_en = merge_append_boundary_str_subdict(d["new_issue_tail_en"], raw.get("new_issue_tail_en"))

    def _str_override(key: str) -> str:
        v = raw.get(key)
        if isinstance(v, str) and v.strip():
            return v.rstrip("\r\n")
        return d[key]

    return {
        "continuity_zh": continuity_zh,
        "new_issue_tail_zh": new_issue_tail_zh,
        "new_issue_tail_en": new_issue_tail_en,
        "continuity_en_add_car": _str_override("continuity_en_add_car"),
        "continuity_en_other": _str_override("continuity_en_other"),
        "add_car_split_hint_zh": _str_override("add_car_split_hint_zh"),
        "add_car_split_hint_en": _str_override("add_car_split_hint_en"),
        "borderline_zh": _str_override("borderline_zh"),
        "borderline_en": _str_override("borderline_en"),
    }
