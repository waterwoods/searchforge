"""Bounded LangGraph for accident-story AI subworkflow only.

Never submits/closes claims, never mutates lifecycle, never decides coverage.
Final persistence happens outside this graph after customer confirmation.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable

from services.fiqa_api.inbox_triage.accident_story_assistant.contract import (
    AccidentStoryState,
    ProposedFact,
    empty_state,
    public_proposal,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.extractors import (
    build_incident_summary,
    extract_injury_status,
    extract_location_text,
    extract_time_text,
    extract_vehicles,
    normalize_story,
    validate_model_proposals,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.guardrails import (
    apply_safety_guardrails,
    build_confirmation_proposal,
    derive_missing_facts,
    draft_followup_questions,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.tracing import (
    LatencyTimer,
    build_root_trace_metadata,
    process_traced_inputs,
    process_traced_outputs,
)
from services.fiqa_api.observability.langsmith_tracing import maybe_traceable

logger = logging.getLogger(__name__)


def _llm_enabled() -> bool:
    from services.fiqa_api.inbox_triage.accident_story_assistant.flags import (
        llm_extraction_enabled,
    )

    return llm_extraction_enabled()


@maybe_traceable(
    name="accident_story.normalize_story",
    process_inputs=process_traced_inputs,
    process_outputs=process_traced_outputs,
    metadata={"node": "normalize_story"},
)
def node_normalize_story(state: AccidentStoryState) -> AccidentStoryState:
    out = dict(state)
    out["normalized_story"] = normalize_story(str(state.get("raw_story") or ""))
    out.setdefault("schema_version", 1)
    return out  # type: ignore[return-value]


_LLM_HOOK: Callable[[str], dict[str, Any]] | None = None


@maybe_traceable(
    name="accident_story.extract_fact_proposals",
    process_inputs=process_traced_inputs,
    process_outputs=process_traced_outputs,
    metadata={"node": "extract_fact_proposals"},
)
def node_extract_fact_proposals(state: AccidentStoryState) -> AccidentStoryState:
    """Deterministic extraction; optional LLM merge when ACCIDENT_STORY_LLM=1 or test hook."""
    out = dict(state)
    text = str(out.get("normalized_story") or out.get("raw_story") or "")
    injury, inj_conf, conflicts = extract_injury_status(text)
    time_text, time_conf = extract_time_text(text)
    loc_text, loc_conf = extract_location_text(text)
    vehicles = extract_vehicles(text)

    out["injury_status"] = injury
    out["accident_time_text"] = time_text
    out["accident_location_text"] = loc_text
    out["involved_vehicles"] = vehicles
    out["involved_parties"] = list(out.get("involved_parties") or [])
    out["conflicts"] = list(dict.fromkeys([*(out.get("conflicts") or []), *conflicts]))
    out["confidence_by_field"] = {
        "injury_status": inj_conf,
        "accident_datetime": time_conf,
        "accident_location": loc_conf,
        "accident_description": 0.9 if text else 0.0,
    }
    out["model_provider"] = "deterministic"
    out["model_name"] = "rules_v1"

    llm_caller = _LLM_HOOK
    if _llm_enabled() or callable(llm_caller):
        try:
            if callable(llm_caller):
                llm_out = llm_caller(text)
            else:
                llm_out = _call_optional_llm(text)
            if not isinstance(llm_out, dict):
                raise ValueError("invalid_model_json")
            provider = str(llm_out.pop("_provider", "") or "openai")
            model_name = str(llm_out.pop("_model", "") or "accident_story_llm")
            merged = validate_model_proposals(llm_out)
            # HARD: re-check source evidence before accepting model injury.
            from services.fiqa_api.inbox_triage.accident_story_assistant.guardrails import (
                enforce_injury_evidence_guardrail,
            )

            if merged.get("injury_status"):
                safe_injury, inj_conflicts, inj_warns = enforce_injury_evidence_guardrail(
                    source_text=text,
                    proposed_injury=str(merged.get("injury_status")),
                    prior_conflicts=list(out.get("conflicts") or []),
                )
                out["injury_status"] = safe_injury
                out["conflicts"] = inj_conflicts
                if inj_warns:
                    out["warnings"] = list(
                        dict.fromkeys([*(out.get("warnings") or []), *inj_warns])
                    )
            for key in ("accident_time_text", "accident_location_text", "incident_summary"):
                if merged.get(key) and not str(out.get(key) or "").strip():
                    out[key] = merged[key]
            if merged.get("involved_vehicles"):
                out["involved_vehicles"] = list(
                    dict.fromkeys([*(out.get("involved_vehicles") or []), *merged["involved_vehicles"]])
                )[:5]
            if merged.get("confidence_by_field"):
                conf = dict(out.get("confidence_by_field") or {})
                conf.update(merged["confidence_by_field"])
                # Cap injury confidence when evidence forced unknown.
                if out.get("injury_status") == "unknown" and any(
                    w == "injury_llm_unsupported_forced_unknown"
                    for w in (out.get("warnings") or [])
                ):
                    conf["injury_status"] = min(float(conf.get("injury_status") or 0.3), 0.3)
                out["confidence_by_field"] = conf
            out["model_provider"] = provider or "openai"
            out["model_name"] = model_name or "accident_story_llm"
        except Exception as exc:
            out["used_fallback"] = True
            out["fallback_reason"] = f"llm_failed:{exc}"
            warns = list(out.get("warnings") or [])
            warns.append("llm_unavailable_or_invalid_using_deterministic")
            out["warnings"] = warns

    out["incident_summary"] = str(out.get("incident_summary") or "") or build_incident_summary(
        normalized=text,
        injury=out["injury_status"],  # type: ignore[arg-type]
        time_text=str(out.get("accident_time_text") or ""),
        location_text=str(out.get("accident_location_text") or ""),
    )
    return out  # type: ignore[return-value]


def _call_optional_llm(text: str) -> dict[str, Any]:
    """Optional LLM path — disabled by default; raises on timeout/invalid/missing creds."""
    import concurrent.futures
    import json
    import re

    from services.fiqa_api.inbox_triage.accident_story_assistant.flags import (
        llm_max_retries,
        llm_timeout_seconds,
    )

    api_key = (os.getenv("OPENAI_API_KEY") or os.getenv("ACCIDENT_STORY_LLM_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("missing_credentials:accident_story_llm")

    model = (os.getenv("ACCIDENT_STORY_LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    story = str(text or "")[:2000]

    def _invoke() -> dict[str, Any]:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        system = (
            "Extract California auto accident intake facts from the customer story. "
            "Return ONLY a JSON object with keys from this allow-list: "
            "injury_status (yes|no|unknown), accident_time_text, accident_location_text, "
            "incident_summary, involved_vehicles (string array), confidence_by_field (object). "
            "Rules: never invent facts; if injury is unclear use unknown; "
            "never decide coverage/liability; never add other keys."
        )
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            max_tokens=400,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": story},
            ],
        )
        content = ""
        try:
            content = str(resp.choices[0].message.content or "")
        except Exception as exc:  # noqa: BLE001
            raise ValueError("invalid_model_json") from exc
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        try:
            parsed = json.loads(content)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("invalid_model_json") from exc
        if not isinstance(parsed, dict):
            raise ValueError("invalid_model_json")
        parsed["_provider"] = "openai"
        parsed["_model"] = model
        return parsed

    last_exc: Exception | None = None
    attempts = 1 + int(llm_max_retries())
    for _ in range(max(1, attempts)):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(_invoke)
                return fut.result(timeout=float(llm_timeout_seconds()))
        except concurrent.futures.TimeoutError:
            last_exc = TimeoutError("provider_timeout")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            # Do not retry auth/credential failures.
            if "missing_credentials" in str(exc).lower() or "auth" in str(exc).lower():
                break
    assert last_exc is not None
    raise last_exc


@maybe_traceable(
    name="accident_story.validate_proposals",
    process_inputs=process_traced_inputs,
    process_outputs=process_traced_outputs,
    metadata={"node": "validate_proposals"},
)
def node_validate_proposals(state: AccidentStoryState) -> AccidentStoryState:
    out = dict(state)
    if str(out.get("injury_status") or "") not in ("yes", "no", "unknown"):
        out["used_fallback"] = True
        out["fallback_reason"] = out.get("fallback_reason") or "invalid_injury_status"
        out["injury_status"] = "unknown"
        warns = list(out.get("warnings") or [])
        warns.append("proposal_validation_coerced_injury_unknown")
        out["warnings"] = warns
    facts: list[ProposedFact] = []
    story = str(out.get("normalized_story") or out.get("raw_story") or "").strip()
    if story:
        facts.append(
            {
                "field_key": "accident_description",
                "value": story,
                "authority": "ai_proposed",
                "confidence": float((out.get("confidence_by_field") or {}).get("accident_description") or 0.9),
                "source": "customer_text",
            }
        )
    if str(out.get("accident_time_text") or "").strip():
        facts.append(
            {
                "field_key": "accident_datetime",
                "value": str(out["accident_time_text"]),
                "authority": "ai_proposed",
                "confidence": float((out.get("confidence_by_field") or {}).get("accident_datetime") or 0.5),
                "source": "extractor",
            }
        )
    if str(out.get("accident_location_text") or "").strip():
        facts.append(
            {
                "field_key": "accident_location",
                "value": str(out["accident_location_text"]),
                "authority": "ai_proposed",
                "confidence": float((out.get("confidence_by_field") or {}).get("accident_location") or 0.5),
                "source": "extractor",
            }
        )
    facts.append(
        {
            "field_key": "injury_status",
            "value": str(out.get("injury_status") or "unknown"),
            "authority": "ai_proposed",
            "confidence": float((out.get("confidence_by_field") or {}).get("injury_status") or 0.2),
            "source": "extractor",
        }
    )
    out["proposed_facts"] = facts
    return out  # type: ignore[return-value]


@maybe_traceable(
    name="accident_story.derive_missing_facts",
    process_inputs=process_traced_inputs,
    process_outputs=process_traced_outputs,
    metadata={"node": "derive_missing_facts"},
)
def node_derive_missing_facts(state: AccidentStoryState) -> AccidentStoryState:
    out = dict(state)
    out["missing_required_facts"] = derive_missing_facts(out)  # type: ignore[arg-type]
    return out  # type: ignore[return-value]


@maybe_traceable(
    name="accident_story.draft_followup_questions",
    process_inputs=process_traced_inputs,
    process_outputs=process_traced_outputs,
    metadata={"node": "draft_followup_questions"},
)
def node_draft_followup_questions(state: AccidentStoryState) -> AccidentStoryState:
    out = dict(state)
    missing = list(out.get("missing_required_facts") or [])
    from services.fiqa_api.inbox_triage.accident_story_assistant.flags import (
        max_followup_questions,
    )

    out["followup_questions"] = draft_followup_questions(
        missing, max_questions=max_followup_questions()
    )
    return out  # type: ignore[return-value]


@maybe_traceable(
    name="accident_story.apply_safety_guardrails",
    process_inputs=process_traced_inputs,
    process_outputs=process_traced_outputs,
    metadata={"node": "apply_safety_guardrails"},
)
def node_apply_safety_guardrails(state: AccidentStoryState) -> AccidentStoryState:
    return apply_safety_guardrails(state)


@maybe_traceable(
    name="accident_story.build_confirmation_proposal",
    process_inputs=process_traced_inputs,
    process_outputs=process_traced_outputs,
    metadata={"node": "build_customer_confirmation_proposal"},
)
def node_build_customer_confirmation_proposal(state: AccidentStoryState) -> AccidentStoryState:
    return build_confirmation_proposal(state)


_NODE_SEQUENCE: tuple[Callable[[AccidentStoryState], AccidentStoryState], ...] = (
    node_normalize_story,
    node_extract_fact_proposals,
    node_validate_proposals,
    node_derive_missing_facts,
    node_draft_followup_questions,
    node_apply_safety_guardrails,
    node_build_customer_confirmation_proposal,
)


@maybe_traceable(
    name="accident_story.run_graph",
    process_inputs=process_traced_inputs,
    process_outputs=process_traced_outputs,
    metadata={"assistant": "accident_story_langgraph_v1"},
)
def run_accident_story_graph(
    *,
    raw_story: str,
    command_id: str = "",
    idempotency_key: str = "",
    llm_caller: Callable[[str], dict[str, Any]] | None = None,
    scenario: str = "",
) -> AccidentStoryState:
    """Execute the bounded graph. Persistence stays outside."""
    global _LLM_HOOK
    timer = LatencyTimer()
    initial: AccidentStoryState = empty_state(
        raw_story=raw_story,
        command_id=command_id,
        idempotency_key=idempotency_key,
    )
    prev_hook = _LLM_HOOK
    _LLM_HOOK = llm_caller
    try:
        from langgraph.graph import END, StateGraph

        graph: Any = StateGraph(AccidentStoryState)
        graph.add_node("normalize_story", node_normalize_story)
        graph.add_node("extract_fact_proposals", node_extract_fact_proposals)
        graph.add_node("validate_proposals", node_validate_proposals)
        graph.add_node("derive_missing_facts", node_derive_missing_facts)
        graph.add_node("draft_followup_questions", node_draft_followup_questions)
        graph.add_node("apply_safety_guardrails", node_apply_safety_guardrails)
        graph.add_node(
            "build_customer_confirmation_proposal",
            node_build_customer_confirmation_proposal,
        )
        graph.set_entry_point("normalize_story")
        graph.add_edge("normalize_story", "extract_fact_proposals")
        graph.add_edge("extract_fact_proposals", "validate_proposals")
        graph.add_edge("validate_proposals", "derive_missing_facts")
        graph.add_edge("derive_missing_facts", "draft_followup_questions")
        graph.add_edge("draft_followup_questions", "apply_safety_guardrails")
        graph.add_edge("apply_safety_guardrails", "build_customer_confirmation_proposal")
        graph.add_edge("build_customer_confirmation_proposal", END)
        app = graph.compile()
        # LangGraph auto-instrumentation dumps full AccidentStoryState (raw_story)
        # into LangSmith when LANGCHAIN_TRACING_V2 is on. Suppress nested auto-traces;
        # our @maybe_traceable hooks apply process_inputs/outputs redaction instead.
        try:
            from langsmith.run_helpers import tracing_context as _ls_tracing_context
        except Exception:  # pragma: no cover
            _ls_tracing_context = None  # type: ignore[assignment]
        if _ls_tracing_context is not None:
            with _ls_tracing_context(enabled=False):
                result = app.invoke(dict(initial))
        else:
            result = app.invoke(dict(initial))
        state = result  # type: ignore[assignment]
    except Exception as exc:
        logger.warning("langgraph_unavailable_sequential_fallback: %s", exc)
        state = dict(initial)  # type: ignore[assignment]
        for fn in _NODE_SEQUENCE:
            state = fn(state)  # type: ignore[assignment]
        state = dict(state)
        state["used_fallback"] = True
        state["fallback_reason"] = state.get("fallback_reason") or f"graph_runtime:{exc}"
    finally:
        _LLM_HOOK = prev_hook

    meta = build_root_trace_metadata(
        state=dict(state),  # type: ignore[arg-type]
        scenario=scenario,
        latency_ms=timer.ms(),
    )
    out = dict(state)
    out["_trace_metadata"] = meta  # type: ignore[typeddict-unknown-key]
    return out  # type: ignore[return-value]


def propose_from_story(
    *,
    raw_story: str,
    command_id: str = "",
    idempotency_key: str = "",
    llm_caller: Callable[[str], dict[str, Any]] | None = None,
    scenario: str = "",
) -> dict[str, Any]:
    state = run_accident_story_graph(
        raw_story=raw_story,
        command_id=command_id,
        idempotency_key=idempotency_key,
        llm_caller=llm_caller,
        scenario=scenario,
    )
    proposal = public_proposal(state)
    if isinstance(state.get("_trace_metadata"), dict):
        proposal["_trace_metadata"] = dict(state["_trace_metadata"])  # type: ignore[index]
    return proposal
