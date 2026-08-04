"""Offline / LangSmith-compatible evaluators for accident-story golden dataset."""

from __future__ import annotations

from typing import Any, Callable

from services.fiqa_api.inbox_triage.accident_story_assistant.tracing import META_ALLOWLIST

EvaluatorFn = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


def _pass(name: str, detail: str = "") -> dict[str, Any]:
    return {"evaluator": name, "ok": True, "detail": detail}


def _fail(name: str, detail: str) -> dict[str, Any]:
    return {"evaluator": name, "ok": False, "detail": detail}


def eval_max_questions_le_3(proposal: dict[str, Any], expect: dict[str, Any]) -> dict[str, Any]:
    qs = list(proposal.get("followup_questions") or [])
    cap = int(expect.get("max_followup_questions") or 3)
    if len(qs) > 3:
        return _fail("max_questions_le_3", f"got {len(qs)} > 3")
    if len(qs) > cap:
        return _fail("max_questions_le_3", f"got {len(qs)} > expect cap {cap}")
    return _pass("max_questions_le_3", f"n={len(qs)} cap={cap}")


def eval_missing_matches_expect(proposal: dict[str, Any], expect: dict[str, Any]) -> dict[str, Any]:
    missing = set(str(x) for x in (proposal.get("missing_required_facts") or []))
    contains = [str(x) for x in (expect.get("missing_contains") or [])]
    excludes = [str(x) for x in (expect.get("missing_excludes") or [])]
    for key in contains:
        if key not in missing:
            return _fail("missing_matches_expect", f"missing lacks {key}; got={sorted(missing)}")
    for key in excludes:
        if key in missing:
            return _fail("missing_matches_expect", f"missing unexpectedly has {key}")
    return _pass("missing_matches_expect", f"missing={sorted(missing)}")


def eval_extracted_fact_correctness(proposal: dict[str, Any], expect: dict[str, Any]) -> dict[str, Any]:
    extracted = expect.get("extracted") if isinstance(expect.get("extracted"), dict) else {}
    for key, want in extracted.items():
        if key == "accident_type":
            guided = proposal.get("guided_view") if isinstance(proposal.get("guided_view"), dict) else {}
            rows = guided.get("fact_rows") if isinstance(guided.get("fact_rows"), list) else []
            got = ""
            for row in rows:
                if isinstance(row, dict) and row.get("key") == "accident_type":
                    got = str(row.get("value_zh") or "")
                    break
            if want and want not in got:
                return _fail("extracted_fact_correctness", f"accident_type want={want} got={got}")
            continue
        got = proposal.get(key)
        if str(got) != str(want):
            return _fail("extracted_fact_correctness", f"{key} want={want} got={got}")
    return _pass("extracted_fact_correctness", "ok")


def eval_no_unnecessary_questions(proposal: dict[str, Any], expect: dict[str, Any]) -> dict[str, Any]:
    """Questions must only cover missing keys (no extras beyond missing set)."""
    missing = [str(x) for x in (proposal.get("missing_required_facts") or [])]
    guided = proposal.get("guided_view") if isinstance(proposal.get("guided_view"), dict) else {}
    fields = guided.get("followup_fields") if isinstance(guided.get("followup_fields"), list) else []
    asked = [str(f.get("field_key") or "") for f in fields if isinstance(f, dict)]
    for key in asked:
        if key and key not in missing:
            return _fail("no_unnecessary_questions", f"asked {key} not in missing={missing}")
    # Also: question count should equal guided followup_fields and <= missing
    qs = list(proposal.get("followup_questions") or [])
    if len(qs) != len(asked) and asked:
        return _fail("no_unnecessary_questions", f"questions={len(qs)} fields={len(asked)}")
    return _pass("no_unnecessary_questions", f"asked={asked}")


def eval_no_silent_injury_no(proposal: dict[str, Any], expect: dict[str, Any]) -> dict[str, Any]:
    if expect.get("never_coerce_injury_to_no") or str(
        (expect.get("extracted") or {}).get("injury_status") or ""
    ) == "unknown":
        if proposal.get("injury_status") == "no" and "unknown" in str(
            (expect.get("extracted") or {}).get("injury_status") or "unknown"
        ):
            # only fail when expect says unknown
            if str((expect.get("extracted") or {}).get("injury_status")) == "unknown":
                return _fail("no_silent_injury_no", "unknown coerced to no")
    if str((expect.get("extracted") or {}).get("injury_status")) == "unknown":
        if proposal.get("injury_status") != "unknown":
            return _fail(
                "no_silent_injury_no",
                f"expected unknown got {proposal.get('injury_status')}",
            )
    return _pass("no_silent_injury_no", str(proposal.get("injury_status")))


def eval_conflict_not_resolved(proposal: dict[str, Any], expect: dict[str, Any]) -> dict[str, Any]:
    want = list(expect.get("conflicts") or [])
    if not want:
        return _pass("conflict_not_resolved", "n/a")
    got = list(proposal.get("conflicts") or [])
    for c in want:
        if c not in got:
            return _fail("conflict_not_resolved", f"missing conflict {c}; got={got}")
    if proposal.get("injury_status") != "unknown":
        return _fail("conflict_not_resolved", f"injury should stay unknown, got={proposal.get('injury_status')}")
    guided = proposal.get("guided_view") if isinstance(proposal.get("guided_view"), dict) else {}
    if not guided.get("conflicts"):
        return _fail("conflict_not_resolved", "guided_view.conflicts empty")
    return _pass("conflict_not_resolved", f"conflicts={got}")


def eval_fallback_on_bad_llm(proposal: dict[str, Any], expect: dict[str, Any]) -> dict[str, Any]:
    want = bool(expect.get("fallback"))
    got = bool(proposal.get("used_fallback"))
    if want and not got:
        return _fail("fallback_on_bad_llm", "expected used_fallback=true")
    if want and not str(proposal.get("fallback_reason") or "").strip():
        return _fail("fallback_on_bad_llm", "missing fallback_reason")
    # Proposal must still be usable
    if "injury_status" not in proposal:
        return _fail("fallback_on_bad_llm", "proposal unusable")
    if want:
        return _pass("fallback_on_bad_llm", str(proposal.get("fallback_reason"))[:120])
    return _pass("fallback_on_bad_llm", f"fallback={got}")


def eval_guided_view_present(proposal: dict[str, Any], expect: dict[str, Any]) -> dict[str, Any]:
    guided = proposal.get("guided_view")
    if not isinstance(guided, dict):
        return _fail("guided_view_present", "missing guided_view")
    qs = list(proposal.get("followup_questions") or [])
    fields = guided.get("followup_fields") if isinstance(guided.get("followup_fields"), list) else []
    if len(fields) != len(qs):
        return _fail("guided_view_present", f"fields={len(fields)} questions={len(qs)}")
    if guided.get("title_zh") != "AI已帮您整理":
        return _fail("guided_view_present", f"title={guided.get('title_zh')}")
    return _pass("guided_view_present", f"fields={len(fields)}")


def eval_no_pii_in_trace_meta(proposal: dict[str, Any], expect: dict[str, Any]) -> dict[str, Any]:
    meta = proposal.get("_trace_metadata")
    if not isinstance(meta, dict):
        return _fail("no_pii_in_trace_meta", "missing _trace_metadata")
    banned = ("raw_story", "accident_description", "normalized_story", "incident_summary", "phone", "openid", "token")
    for k, v in meta.items():
        if k not in META_ALLOWLIST:
            return _fail("no_pii_in_trace_meta", f"key not allowlisted: {k}")
        for b in banned:
            if b in str(k).lower():
                return _fail("no_pii_in_trace_meta", f"banned key {k}")
            if isinstance(v, str) and b in v.lower() and k not in ("fallback_reason_category", "model_name", "model_provider"):
                # values should not contain story-like long chinese blobs; length already capped
                if len(v) > 80 and any("\u4e00" <= ch <= "\u9fff" for ch in v):
                    return _fail("no_pii_in_trace_meta", f"suspicious text in {k}")
    if "story_char_len" not in meta:
        return _fail("no_pii_in_trace_meta", "missing story_char_len")
    return _pass("no_pii_in_trace_meta", f"keys={sorted(meta.keys())}")


DEFAULT_EVALUATORS: list[EvaluatorFn] = [
    eval_extracted_fact_correctness,
    eval_missing_matches_expect,
    eval_max_questions_le_3,
    eval_no_unnecessary_questions,
    eval_no_silent_injury_no,
    eval_conflict_not_resolved,
    eval_fallback_on_bad_llm,
    eval_guided_view_present,
    eval_no_pii_in_trace_meta,
]


def run_evaluators(proposal: dict[str, Any], expect: dict[str, Any]) -> list[dict[str, Any]]:
    return [fn(proposal, expect) for fn in DEFAULT_EVALUATORS]
