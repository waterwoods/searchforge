#!/usr/bin/env python3
"""
Aggregate triage latency breakdown from ASGI chaos runs (requires TRIAGE_RETURN_PERF_METRICS=1).

  TRIAGE_RETURN_PERF_METRICS=1 LLM_GENERATION_ENABLED=1 PYTHONPATH=. python3 scripts/profile_live_latency.py \\
    --sessions 50 --out results/LATENCY_BASELINE.json
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
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


def _pick_sessions(library: Path, n: int, include_proc: bool) -> list[dict[str, Any]]:
    all_s = _load_scenarios(library)
    mult = [s for s in all_s if len(_turns_from_scenario(s)) >= 1]
    if not include_proc:
        mult = [s for s in mult if not str(s.get("id") or "").startswith("proc_")]
    return mult[: max(1, min(n, len(mult)))]


def _pct(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    n = len(sorted_vals)
    i = min(n - 1, max(0, int(round(p * (n - 1)))))
    return round(sorted_vals[i], 2)


def _max_ms(sorted_vals: list[float]) -> float:
    if not sorted_vals:
        return 0.0
    return round(max(sorted_vals), 2)


def _slowest_step(turns: list[dict[str, Any]]) -> dict[str, Any]:
    worst: dict[str, Any] = {"component": "", "ms": 0.0, "text_preview": ""}
    for t in turns:
        m = t.get("triage_turn_metrics") if isinstance(t, dict) else None
        if not isinstance(m, dict):
            continue
        pairs = [
            ("total", float(m.get("latency_ms") or 0)),
            ("llm_total", float(m.get("llm_total_ms") or 0)),
            ("db", float(m.get("db_ms") or 0)),
            ("resolver", float(m.get("resolver_ms") or 0)),
        ]
        for name, ms in pairs:
            if ms > float(worst.get("ms") or 0):
                worst = {
                    "component": name,
                    "ms": round(ms, 2),
                    "text_preview": str(t.get("text_preview") or "")[:80],
                }
    return worst


async def _run(pack: list[dict[str, Any]]) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location(
        "llm_chaos_live_triage_check",
        ROOT / "scripts" / "llm_chaos_live_triage_check.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("llm_chaos_live_triage_check")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "_triage_asgi_chaos_pack")
    return await fn(pack, attach_turn_perf=True)


def _collect_route_metric(turns: list[dict[str, Any]], key: str) -> list[float]:
    out: list[float] = []
    for t in turns:
        rp = t.get("route_perf") if isinstance(t, dict) else None
        if isinstance(rp, dict) and key in rp:
            out.append(float(rp[key] or 0))
    return out


def main() -> int:
    os.environ["TRIAGE_RETURN_PERF_METRICS"] = "1"
    p = argparse.ArgumentParser()
    p.add_argument("--sessions", type=int, default=40)
    p.add_argument(
        "--library",
        type=str,
        default="tests/scenario_libraries/add_car_entity_integration_scenarios.py",
    )
    p.add_argument("--include-proc", action="store_true")
    p.add_argument("--out", type=str, default="results/LATENCY_PROFILE.json")
    args = p.parse_args()

    libp = (ROOT / args.library).resolve()
    pack = _pick_sessions(libp, args.sessions, include_proc=args.include_proc)
    raw = asyncio.run(_run(pack))

    http_totals: list[float] = []
    triage_core: list[float] = []
    llms: list[float] = []
    dbs: list[float] = []
    resolvers: list[float] = []
    route_overheads: list[float] = []
    route_prep: list[float] = []
    slow_global: dict[str, Any] = {"component": "", "ms": 0.0, "session": ""}

    for sess in raw.get("sessions") or []:
        if not isinstance(sess, dict):
            continue
        sid = sess.get("id")
        for t in sess.get("turns") or []:
            if not isinstance(t, dict):
                continue
            http_ms = float(t.get("latency_ms") or 0)
            http_totals.append(http_ms)
            m = t.get("triage_turn_metrics") if isinstance(t.get("triage_turn_metrics"), dict) else None
            rp = t.get("route_perf") if isinstance(t.get("route_perf"), dict) else None
            if m is None and isinstance(rp, dict) and float(rp.get("triage_ms") or 0) > 0:
                m = {"latency_ms": rp.get("triage_ms"), "llm_total_ms": 0.0, "db_ms": 0.0, "resolver_ms": 0.0}
            if isinstance(rp, dict):
                ro = float(rp.get("route_overhead_ms") or 0)
                if ro > 0:
                    route_overheads.append(ro)
                # session+case prep outside triage wall (approx)
                prep = float(rp.get("session_ms") or 0) + float(rp.get("case_ms") or 0)
                if prep > 0:
                    route_prep.append(prep)
            if isinstance(m, dict):
                core = float(m.get("latency_ms") or 0)
                triage_core.append(core)
                llms.append(float(m.get("llm_total_ms") or 0))
                dbs.append(float(m.get("db_ms") or 0))
                resolvers.append(float(m.get("resolver_ms") or 0))
                overhead_est = max(0.0, http_ms - core)
                for name, val in (
                    ("http_total", http_ms),
                    ("triage_core", core),
                    ("llm", float(m.get("llm_total_ms") or 0)),
                    ("db", float(m.get("db_ms") or 0)),
                    ("resolver", float(m.get("resolver_ms") or 0)),
                    ("route_overhead_est", overhead_est),
                ):
                    if val > float(slow_global.get("ms") or 0):
                        slow_global = {"component": name, "ms": round(val, 2), "session": sid}
            else:
                triage_core.append(0.0)
                llms.append(0.0)
                dbs.append(0.0)
                resolvers.append(0.0)
                if http_ms > float(slow_global.get("ms") or 0):
                    slow_global = {"component": "http_total", "ms": round(http_ms, 2), "session": sid}

    http_totals.sort()
    triage_core.sort()
    llms.sort()
    dbs.sort()
    resolvers.sort()
    route_overheads.sort()
    route_prep.sort()

    route_perf_breakdown: dict[str, Any] | None = None
    all_turns: list[dict[str, Any]] = []
    for sess in raw.get("sessions") or []:
        if isinstance(sess, dict):
            for t in sess.get("turns") or []:
                if isinstance(t, dict):
                    all_turns.append(t)
    if all_turns:
        keys = (
            "route_total_ms",
            "route_overhead_ms",
            "triage_ms",
            "session_ms",
            "case_ms",
            "assist_ms",
            "conversion_ms",
            "postprocess_ms",
        )
        route_perf_breakdown = {}
        for k in keys:
            vals = sorted(_collect_route_metric(all_turns, k))
            if vals:
                route_perf_breakdown[k] = {"p50": _pct(vals, 0.5), "p95": _pct(vals, 0.95), "max": _max_ms(vals)}

    breakdown = {
        "note": "total = HTTP round-trip per chaos client; triage_core = triage_conversation wall from metrics",
        "total_http_request": {
            "p50": _pct(http_totals, 0.5),
            "p95": _pct(http_totals, 0.95),
            "max": _max_ms(http_totals),
        },
        "triage_core": {
            "p50": _pct(triage_core, 0.5),
            "p95": _pct(triage_core, 0.95),
            "max": _max_ms(triage_core),
        },
        "llm": {
            "p50": _pct(llms, 0.5),
            "p95": _pct(llms, 0.95),
            "max": _max_ms(llms),
        },
        "db": {
            "p50": _pct(dbs, 0.5),
            "p95": _pct(dbs, 0.95),
            "max": _max_ms(dbs),
        },
        "resolver": {
            "p50": _pct(resolvers, 0.5),
            "p95": _pct(resolvers, 0.95),
            "max": _max_ms(resolvers),
        },
        "route_overhead": {
            "p50": _pct(route_overheads, 0.5) if route_overheads else round(
                max(0.0, _pct(http_totals, 0.5) - _pct(triage_core, 0.5)), 2
            ),
            "p95": _pct(route_overheads, 0.95) if route_overheads else round(
                max(0.0, _pct(http_totals, 0.95) - _pct(triage_core, 0.95)), 2
            ),
            "note": "prefer route_perf.route_overhead_ms when TRIAGE_RETURN_PERF_METRICS=1; else HTTP - triage_core",
        },
        "route_fanout_ms": route_perf_breakdown,
        "slowest_step_global": slow_global,
    }

    out: dict[str, Any] = {
        "library": str(args.library),
        "session_target": args.sessions,
        "session_count": raw.get("session_count"),
        "turn_count": len(http_totals),
        "LATENCY_BREAKDOWN": breakdown,
        "raw_summary": {k: raw.get(k) for k in ("passed", "failed", "llm_generation_enabled", "pg_env") if k in raw},
        "sessions": raw.get("sessions"),
    }
    outp = ROOT / args.out
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(breakdown, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
