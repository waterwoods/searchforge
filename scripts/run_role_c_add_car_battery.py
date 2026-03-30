#!/usr/bin/env python3
"""
Role C + live Add-Car triage battery (HTTP).

Uses the same endpoints as the simulation tab:
  POST {BASE_URL}/api/inbox/simulation-role-c-customer
  POST {BASE_URL}/api/inbox/triage

Requires a running fiqa_api with OPENAI_API_KEY (Role C) and normal triage stack.

Examples:
  PYTHONPATH=. python3 scripts/run_role_c_add_car_battery.py --preset smoke
  PYTHONPATH=. python3 scripts/run_role_c_add_car_battery.py --preset handoff_loop --client-id chen_kui
  PYTHONPATH=. python3 scripts/run_role_c_add_car_battery.py --preset sprint_10_turn --client-id chen_kui
  PYTHONPATH=. python3 scripts/run_role_c_add_car_battery.py \\
    --persona fragmented --difficulty realistic --max-turns 10 --truth-chain --client-id chen_kui
  PYTHONPATH=. python3 scripts/run_role_c_add_car_battery.py --preset sprint_10_turn \\
    --include-labels C1-price-sensitive-tough-10,C3-family-vehicle-realistic-10,C4-materials-first-realistic-10 \\
    --report --client-id chen_kui
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import requests

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from role_c_battery_oracles import (  # noqa: E402
    aggregate_run_summary,
    warnings_for_turn,
    _norm_stem,
)

# Import knob validation from the same module the API uses
from services.fiqa_api.inbox_triage.role_c_simulation_service import (
    ROLE_C_MAX_TURNS_MAX,
    ROLE_C_MAX_TURNS_MIN,
    VALID_DIFFICULTIES,
    VALID_PERSONAS,
)

DEFAULT_BASE = os.environ.get("ROLE_C_BATTERY_BASE_URL", "http://127.0.0.1:8001")

# Small matrix for CI / founder smoke (4 turns each; cheap enough for spot checks)
BATTERY_PRESETS: dict[str, list[dict[str, Any]]] = {
    "smoke": [
        {
            "label": "smoke-fragmented-realistic",
            "persona_id": "fragmented",
            "difficulty": "realistic",
            "max_turns": 4,
            "optional_note": "",
        },
        {
            "label": "smoke-price-tough",
            "persona_id": "price_sensitive",
            "difficulty": "tough",
            "max_turns": 4,
            "optional_note": "",
        },
    ],
    # FORMAL_SUBMIT_ACTION_ROLE_C_SYSTEMATIC_BATTERY_SPRINT — multi-turn handoff / submit / follow-up stress
    "handoff_loop": [
        {
            "label": "C1-price-sensitive-realistic-6",
            "persona_id": "price_sensitive",
            "difficulty": "realistic",
            "max_turns": 6,
            "optional_note": "加车报价；关心保费与自付额；若系统说资料齐了，要追问是否算正式提交办公室、多久有消息。",
        },
        {
            "label": "C2-price-sensitive-tough-8",
            "persona_id": "price_sensitive",
            "difficulty": "tough",
            "max_turns": 8,
            "optional_note": "刁钻比价客户；对「办公室接手」「正式提交」措辞敏感；混合追问材料与时间线。",
        },
        {
            "label": "C3-elderly-tough-8",
            "persona_id": "elderly",
            "difficulty": "tough",
            "max_turns": 8,
            "optional_note": "年长客户口语；担心办公室有没有收到；反复确认算不算报上去了。",
        },
        {
            "label": "C4-family-vehicle-realistic-6",
            "persona_id": "family_vehicle",
            "difficulty": "realistic",
            "max_turns": 6,
            "optional_note": "家庭多车/主驾；资料齐后问承保细节与下一步谁负责。",
        },
        {
            "label": "C5-materials-first-realistic-6",
            "persona_id": "materials_first",
            "difficulty": "realistic",
            "max_turns": 6,
            "optional_note": "强调微信已发驾照dec；追问办公室收到没、要不要再点正式提交。",
        },
    ],
    # PRE_POST_SUBMIT_REGRESSION_CONTEXT_COVERAGE_ROLE_C_10_TURN_SPRINT — 10 turns + optional formal-submit inject
    "sprint_10_turn": [
        {
            "label": "C1-price-sensitive-tough-10",
            "persona_id": "price_sensitive",
            "difficulty": "tough",
            "max_turns": 10,
            "optional_note": "价格敏感；刁钻比价；追问正式提交与办公室是否收到；中后期继续抠条款与时间线。",
        },
        {
            "label": "C2-elderly-tough-10",
            "persona_id": "elderly",
            "difficulty": "tough",
            "max_turns": 10,
            "optional_note": "年长口语；反复确认报上去没有、办公室有没有收到；后期仍要简单复述要点。",
        },
        {
            "label": "C3-family-vehicle-realistic-10",
            "persona_id": "family_vehicle",
            "difficulty": "realistic",
            "max_turns": 10,
            "optional_note": "家庭多车/主驾；资料齐后问承保与下一步；后续追问补充材料。",
        },
        {
            "label": "C4-materials-first-realistic-10",
            "persona_id": "materials_first",
            "difficulty": "realistic",
            "max_turns": 10,
            "optional_note": "材料先发；问是否还要点正式提交；后期追问进度与核对。",
        },
        {
            "label": "C5-fragmented-tough-10",
            "persona_id": "fragmented",
            "difficulty": "tough",
            "max_turns": 10,
            "optional_note": "信息很碎；多轮补全；中后期挑战状态与是否已提交办公室。",
        },
    ],
}

# Broker-aligned line to persist Add-Car when triage is already handoff_ready (matches API tests).
_FORMAL_SUBMIT_INJECT_ZH = "【正式提交办公室】请按系统要点将本条加车记录交办公室处理。"


def _post_json(base: str, path: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    url = f"{base.rstrip('/')}{path}"
    r = requests.post(url, json=payload, timeout=timeout)
    if r.status_code >= 400:
        raise RuntimeError(f"{url} -> {r.status_code}: {r.text[:500]}")
    return r.json()


def _clip(s: str, n: int) -> str:
    t = (s or "").strip()
    if len(t) <= n:
        return t
    return t[: n - 1] + "…"


def _trace_row_from_triage(
    *,
    tri: dict[str, Any],
    turn_index: int | None,
    rc_model: str | None,
    customer: str,
    reply: str,
    case_id_session: str | None,
    post_submit_truth: bool,
    formal_submitted_at: str | None,
    updated_at: str | None,
    injected_formal_submit: bool,
    max_chars: int,
) -> dict[str, Any]:
    ac = tri.get("add_car_turn_intent")
    intent_payload: dict[str, Any] | None = None
    if isinstance(ac, dict):
        intent_payload = {
            "intent_family": ac.get("intent_family"),
            "handoff_base_key": ac.get("handoff_base_key"),
            "truth_notes": ac.get("truth_notes"),
        }
    return {
        "turn_index": turn_index,
        "role_c_model": rc_model,
        "customer": _clip(customer, max_chars),
        "reply": _clip(reply, max_chars),
        "issue_category": tri.get("issue_category"),
        "lifecycle_status": tri.get("lifecycle_status"),
        "handoff_ready": tri.get("handoff_ready"),
        "still_needed_fields": tri.get("still_needed_fields"),
        "quote_ready_status": tri.get("quote_ready_status"),
        "add_car_turn_intent": intent_payload,
        "case_persisted": tri.get("case_persisted"),
        "response_case_id": tri.get("case_id"),
        "session_case_id": case_id_session,
        "post_submit_truth": post_submit_truth,
        "formal_submitted_at": formal_submitted_at,
        "updated_at": updated_at,
        "injected_formal_submit": injected_formal_submit,
    }


def run_one_variant(
    base: str,
    *,
    persona_id: str,
    difficulty: str,
    max_turns: int,
    optional_note: str,
    client_id: str | None,
    timeout: float,
    label: str,
    truth_chain: bool = False,
    max_chars: int = 600,
) -> dict[str, Any]:
    session_id = str(uuid.uuid4())
    turns: list[dict[str, str]] = []
    trace: list[dict[str, Any]] = []
    per_turn_warnings: list[list[dict[str, Any]]] = []
    case_id: str | None = None
    formal_submitted_at_obs: str | None = None
    updated_at_obs: str | None = None
    reply_stems: list[str] = []
    prev_intent: str | None = None
    # Role C counts every customer line in the transcript; truth_chain injects one extra customer message.
    # Repo API allows le=12; some deployed builds cap at 8. Optional: ROLE_C_SIMULATION_MAX_TURNS=8
    # (10-turn truth-chain batteries need a server with le>=12 or reduce --preset turns).
    _extra = max_turns + (2 if truth_chain else 0)
    role_c_max_turns = min(ROLE_C_MAX_TURNS_MAX, _extra)
    _cap = os.environ.get("ROLE_C_SIMULATION_MAX_TURNS", "").strip()
    if _cap.isdigit():
        role_c_max_turns = min(int(_cap), role_c_max_turns)
    role_c_max_turns = max(ROLE_C_MAX_TURNS_MIN, role_c_max_turns)

    customer_turn_counter = 0
    for _ in range(max_turns):
        rc = _post_json(
            base,
            "/api/inbox/simulation-role-c-customer",
            {
                "persona_id": persona_id,
                "optional_note": optional_note,
                "difficulty": difficulty,
                "max_turns": role_c_max_turns,
                "conversation_turns": turns,
                "client_id": client_id,
            },
            timeout=timeout,
        )
        cust = (rc.get("customer_message") or "").strip()
        if not cust:
            raise RuntimeError(f"empty Role C message: {rc}")
        turns.append({"role": "customer", "text": cust})
        customer_turn_counter += 1

        post_submit = bool(case_id)
        tri = _post_json(
            base,
            "/api/inbox/triage",
            {
                "text": cust,
                "persist_case": False,
                "conversation_turns": turns[:-1],
                "soft_route": "add_car",
                "session_id": session_id,
                "client_id": client_id,
                **({"case_id": case_id} if case_id else {}),
            },
            timeout=timeout,
        )
        reply = (tri.get("client_reply_draft") or "").strip()
        turns.append({"role": "system", "text": reply or "(empty draft)"})

        ac = tri.get("add_car_turn_intent") if isinstance(tri.get("add_car_turn_intent"), dict) else {}
        intent_family = str(ac.get("intent_family") or "").strip() or None

        ws = warnings_for_turn(
            turn_number=customer_turn_counter,
            customer_text=cust,
            reply_text=reply,
            tri=tri,
            post_submit_truth=post_submit,
            injected_formal_submit=False,
            prev_intent_family=prev_intent,
            recent_reply_stems=reply_stems,
        )
        per_turn_warnings.append(ws)
        prev_intent = intent_family
        stem = _norm_stem(reply)
        if stem:
            reply_stems.append(stem)

        trace.append(
            {
                **_trace_row_from_triage(
                    tri=tri,
                    turn_index=rc.get("turn_index"),
                    rc_model=rc.get("model"),
                    customer=cust,
                    reply=reply,
                    case_id_session=case_id,
                    post_submit_truth=post_submit,
                    formal_submitted_at=formal_submitted_at_obs,
                    updated_at=updated_at_obs,
                    injected_formal_submit=False,
                    max_chars=max_chars,
                ),
                "warnings": ws,
            }
        )

        # Context coverage: once handoff_ready, inject one formal-submit persist so later turns carry case_id + truth.
        if truth_chain and not case_id and tri.get("handoff_ready"):
            tri_persist = _post_json(
                base,
                "/api/inbox/triage",
                {
                    "text": _FORMAL_SUBMIT_INJECT_ZH,
                    "persist_case": True,
                    "formal_submit": True,
                    "conversation_turns": [{"role": t["role"], "text": t["text"]} for t in turns],
                    "soft_route": "add_car",
                    "session_id": session_id,
                    "client_id": client_id,
                },
                timeout=timeout,
            )
            reply_p = (tri_persist.get("client_reply_draft") or "").strip()
            turns.append({"role": "customer", "text": _FORMAL_SUBMIT_INJECT_ZH})
            turns.append({"role": "system", "text": reply_p or "(empty draft)"})

            new_id = (tri_persist.get("case_id") or "").strip() or None
            formal_submitted_at_obs = (tri_persist.get("formal_submitted_at") or "").strip() or formal_submitted_at_obs
            updated_at_obs = (tri_persist.get("updated_at") or "").strip() or updated_at_obs

            inj_ws = warnings_for_turn(
                turn_number=customer_turn_counter,
                customer_text=_FORMAL_SUBMIT_INJECT_ZH,
                reply_text=reply_p,
                tri=tri_persist,
                post_submit_truth=False,
                injected_formal_submit=True,
                prev_intent_family=prev_intent,
                recent_reply_stems=reply_stems,
            )
            per_turn_warnings.append(inj_ws)

            trace.append(
                {
                    **_trace_row_from_triage(
                        tri=tri_persist,
                        turn_index=None,
                        rc_model=None,
                        customer=_FORMAL_SUBMIT_INJECT_ZH,
                        reply=reply_p,
                        case_id_session=new_id,
                        post_submit_truth=False,
                        formal_submitted_at=formal_submitted_at_obs,
                        updated_at=updated_at_obs,
                        injected_formal_submit=True,
                        max_chars=max_chars,
                    ),
                    "warnings": inj_ws,
                }
            )
            case_id = new_id
            prev_intent = (
                str((tri_persist.get("add_car_turn_intent") or {}).get("intent_family") or "").strip()
                or prev_intent
            )
            stem_p = _norm_stem(reply_p)
            if stem_p:
                reply_stems.append(stem_p)

        time.sleep(0.05)

    summary = aggregate_run_summary(per_turn_warnings, [label])
    return {
        "label": label,
        "persona_id": persona_id,
        "difficulty": difficulty,
        "truth_chain": truth_chain,
        "final_case_id": case_id,
        "formal_submitted_at_observed": formal_submitted_at_obs,
        "updated_at_observed": updated_at_obs,
        "trace": trace,
        "run_summary": summary,
        "warnings_flat": [w for row in per_turn_warnings for w in row],
    }


def _print_report(results: list[dict[str, Any]]) -> None:
    for r in results:
        print(f"\n=== {r['label']} ===")
        rs = r.get("run_summary") or {}
        print(
            "warning layers:",
            json.dumps(rs.get("warning_count_by_layer"), ensure_ascii=False),
        )
        print("turns_with_warnings:", rs.get("turns_with_warnings"))
        for row in rs.get("warning_codes_top") or []:
            print(f"  {row.get('code')}: {row.get('count')}")
        fc = r.get("final_case_id")
        fsa = r.get("formal_submitted_at_observed")
        print(f"final_case_id: {fc!r}  formal_submitted_at: {fsa!r}")


def main() -> int:
    p = argparse.ArgumentParser(description="Role C multi-turn battery against live triage API")
    p.add_argument("--base-url", default=DEFAULT_BASE, help="fiqa_api base URL")
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--preset", choices=sorted(BATTERY_PRESETS.keys()), default=None)
    p.add_argument("--persona", default="price_sensitive", choices=sorted(VALID_PERSONAS))
    p.add_argument("--difficulty", default="realistic", choices=sorted(VALID_DIFFICULTIES))
    p.add_argument(
        "--max-turns",
        type=int,
        default=6,
        choices=list(range(ROLE_C_MAX_TURNS_MIN, ROLE_C_MAX_TURNS_MAX + 1)),
    )
    p.add_argument("--optional-note", default="", help="Short operator note (optional 4th input)")
    p.add_argument("--client-id", default=None)
    p.add_argument(
        "--truth-chain",
        action="store_true",
        help=(
            "When triage returns handoff_ready, inject one formal-submit persist turn so subsequent "
            "requests pass case_id (reply_truth_context from case_store)."
        ),
    )
    p.add_argument("--jsonl", action="store_true", help="Print one JSON object per variant line")
    p.add_argument(
        "--report",
        action="store_true",
        help="Print human-readable per-variant summary (warning layers, turns, top codes)",
    )
    p.add_argument(
        "--include-labels",
        default="",
        help="Comma-separated substrings; when set, only preset variants whose label contains one of them run.",
    )
    p.add_argument(
        "--max-chars",
        type=int,
        default=600,
        help="Max characters per customer/reply in trace (default 600)",
    )
    args = p.parse_args()

    include: list[str] = [x.strip() for x in args.include_labels.split(",") if x.strip()]

    variants: list[dict[str, Any]]
    preset_truth_chain = args.preset == "sprint_10_turn"
    if args.preset:
        variants = []
        for row in BATTERY_PRESETS[args.preset]:
            lab = row["label"]
            if include and not any(sub in lab for sub in include):
                continue
            variants.append(
                {
                    "label": lab,
                    "persona_id": row["persona_id"],
                    "difficulty": row["difficulty"],
                    "max_turns": row["max_turns"],
                    "optional_note": row.get("optional_note", ""),
                    "truth_chain": preset_truth_chain or row.get("truth_chain", False),
                }
            )
        if not variants:
            print("ERROR: no variants matched --include-labels", file=sys.stderr)
            return 1
    else:
        if include:
            print("ERROR: --include-labels requires --preset", file=sys.stderr)
            return 1
        variants = [
            {
                "label": "single",
                "persona_id": args.persona,
                "difficulty": args.difficulty,
                "max_turns": args.max_turns,
                "optional_note": args.optional_note,
                "truth_chain": args.truth_chain,
            }
        ]

    results: list[dict[str, Any]] = []
    for v in variants:
        out = run_one_variant(
            args.base_url,
            persona_id=v["persona_id"],
            difficulty=v["difficulty"],
            max_turns=v["max_turns"],
            optional_note=v.get("optional_note", ""),
            client_id=args.client_id,
            timeout=args.timeout,
            label=v["label"],
            truth_chain=bool(v.get("truth_chain")),
            max_chars=args.max_chars,
        )
        results.append(out)
        if args.jsonl:
            print(json.dumps(out, ensure_ascii=False))
        else:
            nwarn = len(
                [
                    x
                    for x in (out.get("warnings_flat") or [])
                    if not str(x.get("code") or "").endswith("_INFO")
                ]
            )
            print(f"OK {out['label']}: trace_rows={len(out['trace'])} heuristic_warnings={nwarn}")

    if args.report and not args.jsonl and results:
        _print_report(results)

    if not args.jsonl and len(results) > 1:
        print(json.dumps({"variants": len(results), "ok": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
