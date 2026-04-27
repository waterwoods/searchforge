#!/usr/bin/env python3
"""
Chaos / multi-turn triage against ASGI (in-process).

  PYTHONPATH=. python3 scripts/llm_chaos_live_triage_check.py --asgi --out results/PG_LIVE.json
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _turns_from_scenario(s: dict[str, Any]) -> list[Any]:
    t = s.get("turns")
    if isinstance(t, list) and t:
        return t
    ut = s.get("user_turns")
    if isinstance(ut, list) and ut:
        return ut
    return []


def _load_scenarios(library: Path) -> list[dict[str, Any]]:
    spec = importlib.util.spec_from_file_location("scen_lib", library)
    if spec is None or spec.loader is None:
        raise RuntimeError(str(library))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in ("ALL_SCENARIOS", "SCENARIOS"):
        if hasattr(mod, name):
            return list(getattr(mod, name))
    return []


def _pick_live_sessions(
    max_sessions: int = 30,
    *,
    library: Path | None = None,
    include_proc: bool = True,
) -> list[dict[str, Any]]:
    p = library or (ROOT / "tests/scenario_libraries/add_car_entity_integration_scenarios.py")
    all_s = _load_scenarios(p)
    mult = [s for s in all_s if len(_turns_from_scenario(s)) >= 2]
    if not include_proc:
        mult = [s for s in mult if not str(s.get("id") or "").startswith("proc_")]
    return mult[: min(len(mult), max(1, max_sessions))]


def _inactive_leak_tokens(rows: list[dict[str, Any]], active_eid: str) -> list[str]:
    toks: list[str] = []
    for r in rows or []:
        if bool(r.get("is_active")):
            continue
        if str(r.get("entity_id") or "") == (active_eid or ""):
            continue
        pl = r.get("payload")
        if not isinstance(pl, dict):
            continue
        for k in ("model", "make"):
            v = str(pl.get(k) or "").strip().lower()
            v = v.replace("_", " ")
            if len(v) >= 3 and v not in ("toyota", "honda", "ford", "nissan", "lexus"):
                toks.append(v)
            elif len(v) >= 4:
                toks.append(v)
    return list(dict.fromkeys(toks))


def _text_has_token(hay: str, tok: str) -> bool:
    if not tok or not hay:
        return False
    return tok in hay.lower()


async def _triage_asgi_chaos_pack(
    sessions: list[dict[str, Any]],
    *,
    attach_turn_perf: bool = False,
) -> dict[str, Any]:
    import time as time_mod

    import httpx
    from httpx import ASGITransport

    from services.fiqa_api.app_main import app
    from services.fiqa_api.db.service_record_settings import service_record_database_url
    from services.fiqa_api.inbox_triage.entity_repository import get_active_vehicle, get_all_vehicles
    from services.fiqa_api.inbox_triage.triage import (
        _entity_payload_has_vehicle_identity,
        _primary_vehicle_summary_from_entity_payload,
        _vehicle_key_from_entity_payload,
    )

    has_db = bool(service_record_database_url())
    session_results: list[dict[str, Any]] = []
    clarify_turns = 0
    failed = 0
    passed = 0

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=180.0) as client:
        for sc in sessions:
            sid = f"live_{sc.get('id')}_{uuid.uuid4().hex[:10]}"
            conv: list[dict[str, str]] = []
            turns = _turns_from_scenario(sc)
            turn_trace: list[dict[str, Any]] = []
            sess_failed = False
            for t in turns:
                if isinstance(t, str):
                    text = t
                else:
                    text = str((t or {}).get("text") or "")
                if not (text or "").strip():
                    continue
                payload = {
                    "text": text,
                    "client_id": "chen_kui",
                    "session_id": sid,
                    "conversation_turns": conv,
                }
                sr = (sc.get("soft_route") or "").strip()
                if sr:
                    payload["soft_route"] = sr
                t_req = time_mod.perf_counter()
                r = await client.post("/api/inbox/triage", json=payload)
                lat_ms = (time_mod.perf_counter() - t_req) * 1000.0
                try:
                    body = r.json() if r.content else {}
                except Exception:
                    body = {"_parse_err": (r.text or "")[:400]}
                bd = body if isinstance(body, dict) else {}
                if r.status_code != 200:
                    sess_failed = True
                if bd.get("active_vehicle_clarify_prompt"):
                    clarify_turns += 1
                av_turn = get_active_vehicle(sid) if has_db else None
                all_turn = get_all_vehicles(sid) if has_db else []
                n_active_turn = sum(1 for x in all_turn if x.get("is_active")) if has_db else 0
                if has_db and n_active_turn > 1:
                    sess_failed = True
                ve = None
                if has_db and av_turn:
                    pl = (av_turn or {}).get("payload")
                    ve = {
                        "entity_id": (av_turn or {}).get("entity_id"),
                        "is_active": (av_turn or {}).get("is_active"),
                        "payload": pl if isinstance(pl, dict) else pl,
                    }
                conv.append({"role": "customer", "text": text})
                row: dict[str, Any] = {
                    "text_preview": text[:100],
                    "status": r.status_code,
                    "had_clarify_prompt": bool(bd.get("active_vehicle_clarify_prompt")),
                    "primary_vehicle_summary": bd.get("primary_vehicle_summary"),
                    "vehicle_key": bd.get("vehicle_key"),
                    "rows_in_db": len(all_turn),
                    "active_rows_in_db": n_active_turn,
                    "latency_ms": round(lat_ms, 2),
                    "triage_path": bd.get("triage_path"),
                }
                if attach_turn_perf and isinstance(bd.get("triage_turn_metrics"), dict):
                    row["triage_turn_metrics"] = bd.get("triage_turn_metrics")
                if attach_turn_perf and isinstance(bd.get("route_perf"), dict):
                    row["route_perf"] = bd.get("route_perf")
                if has_db and av_turn:
                    pl_turn = (av_turn or {}).get("payload")
                    pld_turn = pl_turn if isinstance(pl_turn, dict) else {}
                    exp_sum_t = (_primary_vehicle_summary_from_entity_payload(pld_turn) or "").strip()
                    exp_vk_t = (_vehicle_key_from_entity_payload(pld_turn) or "").strip()
                    act_sum_t = str(bd.get("primary_vehicle_summary") or "").strip()
                    act_vk_t = str(bd.get("vehicle_key") or "").strip()
                    if _entity_payload_has_vehicle_identity(pld_turn):
                        vk_ok = exp_vk_t == act_vk_t
                        sum_ok = exp_sum_t.lower() == act_sum_t.lower()
                        row["pg_truth_match"] = vk_ok
                        if not vk_ok:
                            row["pg_truth_err"] = (
                                f"exp_sum={exp_sum_t!r} act_sum={act_sum_t!r} exp_vk={exp_vk_t!r} act_vk={act_vk_t!r}"
                            )
                            sess_failed = True
                        elif not sum_ok:
                            row["pg_truth_summary_drift"] = True
                    inactive_leak = _inactive_leak_tokens(all_turn, str((av_turn or {}).get("entity_id") or ""))
                    draft = str(bd.get("client_reply_draft") or "")
                    for tok in inactive_leak:
                        if _text_has_token(draft, tok):
                            row["inactive_vehicle_leak"] = tok
                            sess_failed = True
                            break
                turn_trace.append(row)
            if sess_failed:
                failed += 1
            else:
                passed += 1
            session_results.append({"id": sc.get("id"), "turns": turn_trace})

    return {
        "sessions": session_results,
        "session_count": len(session_results),
        "passed": passed,
        "failed": failed,
        "clarify_turns": clarify_turns,
        "llm_generation_enabled": (os.environ.get("LLM_GENERATION_ENABLED") or "")
        .strip()
        .lower()
        in ("1", "true", "yes", "on"),
        "pg_env": has_db,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--asgi", action="store_true")
    p.add_argument("--smoke", action="store_true")
    p.add_argument(
        "--library",
        type=str,
        default="tests/scenario_libraries/add_car_entity_integration_scenarios.py",
    )
    p.add_argument("--include-proc", action="store_true")
    p.add_argument("--max-sessions", "--sessions", type=int, default=30, dest="max_sessions")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    t0 = __import__("time").time()
    if args.asgi:
        libp = (ROOT / args.library).resolve()
        pack = _pick_live_sessions(
            max_sessions=max(20, min(args.max_sessions, 50)),
            library=libp,
            include_proc=args.include_proc,
        )
        attach_perf = (os.environ.get("TRIAGE_RETURN_PERF_METRICS") or "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        chaos = asyncio.run(_triage_asgi_chaos_pack(pack, attach_turn_perf=attach_perf))
        chaos["library"] = str(args.library)
        chaos["mode"] = "asgi_chaos_pack"
        chaos["duration_sec"] = round(__import__("time").time() - t0, 3)
        chaos["ok"] = chaos["failed"] == 0
        out = chaos
    else:
        out = {"ok": False, "error": "use --asgi"}

    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if args.asgi:
        return 0 if out.get("ok") else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
