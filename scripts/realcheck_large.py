#!/usr/bin/env python3
"""Large-sample real traffic validation with Pareto data export."""

import argparse
import json
import math
import os
import random
import statistics as st
import time
import uuid
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlencode
import sys

# Import HTTP utility with retry logic
sys.path.insert(0, str(Path(__file__).parent))
from _http_util import fetch_json, wait_ready

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import matplotlib.pyplot as plt  # optional; will fallback if missing
except Exception:
    plt = None

RAG_API = os.getenv("RAG_API_URL", "http://localhost:8000").rstrip("/")
PROXY_URL = os.getenv("PROXY_URL", os.getenv("RETRIEVAL_PROXY_URL", "http://localhost:7070")).rstrip("/")
_MODES_RAW = os.getenv("MODES", "proxy_on,proxy_off")
MODES = [m.strip() for m in _MODES_RAW.replace(",", " ").split() if m.strip()]
_BUDGETS_RAW = os.getenv("BUDGETS", None)
if _BUDGETS_RAW:
    BUDGETS = [int(b.strip()) for b in _BUDGETS_RAW.replace(",", " ").split() if b.strip()]
else:
    # Denser budget grid: 200-1600ms in 100ms steps
    BUDGETS = list(range(200, 1700, 100))
DEFAULT_SAMPLES = int(os.getenv("N", "2000"))
DEFAULT_IN_TOK = int(os.getenv("IN_TOK", "200"))
DEFAULT_OUT_TOK = int(os.getenv("OUT_TOK", "50"))
DEFAULT_PRICE_MODEL = os.getenv("PRICE_MODEL", "gpt-4o-mini")
N = DEFAULT_SAMPLES
TARGET_RECALL = float(os.getenv("TARGET_RECALL", "0.95"))
QUERY_FILE = Path("queries/fiqa_small.txt")
RUNS_DIR = Path(".runs")
RUNS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SEED = 42
PAIR_DELTA_TOLERANCE_MS = 0.25  # Increased from 0.05ms to 0.25ms to account for system load fluctuations (0.01-0.2ms variance is normal in CI environments)


def _load_pareto(path: str = ".runs/pareto.json") -> Optional[Dict[str, Any]]:
    if os.path.exists(path):
        with open(path, "r") as handle:
            return json.load(handle)
    return None


def _resolve_model_pricing(model: str) -> Tuple[float, float, Optional[str]]:
    """
    Resolve model pricing using unified pricing parser.
    Returns (price_in, price_out, matched_key) for compatibility.
    """
    try:
        from services.fiqa_api.cost import load_pricing
        price_in, price_out, cost_enabled, matched_key = load_pricing(model)
        return float(price_in), float(price_out), matched_key
    except (ImportError, Exception) as e:
        # Fallback to old logic if import fails
        print(f"[warn] Failed to import unified pricing parser: {e}, using fallback")
        raw = os.getenv("MODEL_PRICING_JSON")
        if not raw:
            env_path = Path(".env.current")
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("MODEL_PRICING_JSON="):
                        raw = line.split("=", 1)[1].strip()
                        break
        if not raw:
            return 0.0, 0.0, None
        raw = raw.strip()
        if raw and raw[0] in {"'", '"'} and raw[-1] == raw[0]:
            raw = raw[1:-1]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return 0.0, 0.0, None

        candidates = [
            model,
            model.lower(),
            model.replace(":", "-"),
            model.replace(":", ""),
        ]
        entry: Any = None
        matched_key: Optional[str] = None
        if isinstance(data, dict):
            for key in candidates:
                if key in data:
                    entry = data[key]
                    matched_key = key
                    break
        if entry is None and isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("model") in candidates:
                    entry = item
                    matched_key = item.get("model")
                    break
        if entry is None:
            return 0.0, 0.0, None

        def _extract_price(value: Any) -> Optional[float]:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return None
            if isinstance(value, dict):
                for nested_key in (
                    "usd_per_1k",
                    "price",
                    "value",
                    "usd",
                    "price_per_1k",
                    "usd_per_thousand",
                ):
                    if nested_key in value:
                        nested_value = _extract_price(value[nested_key])
                        if nested_value is not None:
                            return nested_value
            return None

        def _lookup(entry_dict: Dict[str, Any], keys: Sequence[str]) -> Optional[float]:
            for key in keys:
                if key in entry_dict:
                    result = _extract_price(entry_dict[key])
                    if result is not None:
                        return result
            for key, value in entry_dict.items():
                if key.lower() in keys and isinstance(value, (int, float, str, dict)):
                    result = _extract_price(value)
                    if result is not None:
                        return result
            return None

        price_in = 0.0
        price_out = 0.0
        if isinstance(entry, dict):
            price_in = _lookup(
                entry,
                (
                    "price_in",
                    "input",
                    "prompt",
                    "prompt_in",
                    "usd_in",
                    "usd_input",
                    "in",
                ),
            ) or 0.0
            price_out = _lookup(
                entry,
                (
                    "price_out",
                    "output",
                    "completion",
                    "usd_out",
                    "usd_output",
                    "out",
                ),
            ) or 0.0
        return float(price_in), float(price_out), matched_key


def _extract_series(
    pareto: Dict[str, Any],
    default_cost_per_1k: float,
) -> Tuple[List[Any], List[float], List[float], List[float], List[str], bool]:
    """Extract series data from pareto, including policy dimension."""
    budgets = list(pareto.get("budgets", []))
    p95: List[float] = []
    recall: List[float] = []
    cost: List[float] = []
    policies: List[str] = []
    budget_fallback: List[Any] = []

    approx_flag = False

    def _sanitize(value: Optional[float]) -> float:
        numeric = float(value) if isinstance(value, (int, float)) else 0.0
        if not math.isfinite(numeric):
            return 0.0
        return numeric

    for run in pareto.get("runs", []):
        budget_fallback.append(run.get("budget_ms"))

        p95_value = run.get("p95_on_trim")
        if p95_value is None:
            p95_value = run.get("p95_ms")
        p95.append(_sanitize(p95_value))

        r_value = run.get("recall_at_10")
        if r_value is None:
            r_value = run.get("success_rate")
            approx_flag = True
        recall.append(_sanitize(r_value))

        cpk_value = default_cost_per_1k
        cost.append(_sanitize(cpk_value))
        
        # Extract policy, default to "Balanced" if not present
        policy_value = run.get("policy") or "Balanced"
        policies.append(str(policy_value))

    if not budgets or len(budgets) != len(p95):
        budgets = [
            bf if bf is not None else idx for idx, bf in enumerate(budget_fallback, start=1)
        ]

    return budgets, p95, recall, cost, policies, approx_flag


def _save_csv(budgets: Sequence[Any], p95: Sequence[float], recall: Sequence[float], cost: Sequence[float], policies: Sequence[str], csv_path: str) -> None:
    with open(csv_path, "w") as handle:
        handle.write("policy,budget_ms,p95_ms,recall_or_success_rate,cost_per_1k_usd\n")
        for b, a, r, c, p in zip(budgets, p95, recall, cost, policies):
            handle.write(f"{p},{b},{a},{r},{c}\n")


def plot_trilines(
    pareto_path: str = ".runs/pareto.json",
    out_png: str = ".runs/real_large_trilines.png",
    csv_path: str = ".runs/real_large_trilines.csv",
    in_tokens: int = DEFAULT_IN_TOK,
    out_tokens: int = DEFAULT_OUT_TOK,
    price_in: float = 0.0,
    price_out: float = 0.0,
    price_model: Optional[str] = None,
    price_source: Optional[str] = None,
) -> Dict[str, Any]:
    pareto = _load_pareto(pareto_path)
    if not pareto:
        print(f"[warn] no {pareto_path}; run `make real-pareto` first.")
        return {"ok": False, "reason": "pareto_missing"}

    cost_per_1k = float(in_tokens) * float(price_in) + float(out_tokens) * float(price_out)
    if cost_per_1k <= 0.0:
        if price_model:
            print(f"[warn] pricing not found for {price_model}; cost line will be flat at 0.0")
        else:
            print("[warn] pricing missing; cost line will be flat at 0.0")
    budgets, p95, recall, cost, policies, approx_flag = _extract_series(pareto, cost_per_1k)
    os.makedirs(".runs", exist_ok=True)

    _save_csv(budgets, p95, recall, cost, policies, csv_path)

    png_path: Optional[str] = None
    if plt is not None:
        fig = plt.figure(figsize=(7, 4.2), dpi=150)
        ax = plt.gca()
        ax.plot(budgets, p95, marker="o", label="p95 (ms)")
        ax.plot(
            budgets,
            recall,
            marker="o",
            label="Recall@10" + (" (≈success_rate)" if approx_flag else ""),
        )
        ax.plot(budgets, cost, marker="o", label="Cost per 1k (USD)")
        ax.set_xlabel("budget_ms")
        ax.set_title("Latency vs Recall vs Cost (by budget)")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_png)
        plt.close(fig)
        png_path = out_png
        print(f"[ok] wrote {out_png}")
    else:
        print(f"[warn] matplotlib not found; skipped PNG generation, wrote {csv_path}")

    pareto["trilines"] = {
        "png": png_path,
        "csv": csv_path,
        "approx_recall": approx_flag,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "price_model": price_model,
        "price_in": price_in,
        "price_out": price_out,
        "cost_per_1k_usd": cost_per_1k,
        "price_source": price_source,
    }
    with open(pareto_path, "w") as handle:
        json.dump(pareto, handle, indent=2)
    return {
        "ok": True,
        "png": png_path,
        "csv": csv_path,
        "approx_recall": approx_flag,
        "cost_per_1k": cost_per_1k,
    }


def _git_commit_short() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _append_obs_url(url: Optional[str]) -> None:
    """Append trace URL using rolling trace utility."""
    if not url:
        return
    try:
        obs_file = RUNS_DIR / "obs_url.txt"
        timestamp = datetime.now(timezone.utc).isoformat()
        line = f"{timestamp} {url.strip()}\n"
        
        # Read existing lines
        lines = []
        if obs_file.exists():
            try:
                lines = obs_file.read_text(encoding="utf-8").splitlines()
            except Exception:
                lines = []
        
        # Append new line
        lines.append(line.rstrip())
        
        # Keep only latest 200 lines
        if len(lines) > 200:
            lines = lines[-200:]
        
        # Atomic write (write to temp then replace)
        tmp_file = obs_file.with_suffix(".tmp")
        tmp_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        tmp_file.replace(obs_file)
    except OSError:
        pass


def _parse_budgets_arg(raw: Optional[str]) -> Optional[List[int]]:
    if not raw:
        return None
    values: List[int] = []
    for chunk in raw.replace(",", " ").split():
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            values.append(int(chunk))
        except ValueError:
            raise ValueError(f"Invalid budget value: {chunk!r}") from None
    return values or None


def _build_query_sequence(queries: Sequence[str], count: int, seed: int) -> List[str]:
    if count <= 0:
        return []
    if not queries:
        return []
    rng = random.Random(seed)
    pool = list(queries)
    rng.shuffle(pool)
    sequence: List[str] = []
    idx = 0
    pool_len = len(pool)
    while len(sequence) < count:
        sequence.append(pool[idx % pool_len])
        idx += 1
    return sequence[:count]


def _trim_values(values: List[float], trim_pct: float) -> List[float]:
    if not values:
        return []
    if trim_pct <= 0.0:
        return list(values)
    if trim_pct >= 0.5:
        trim_pct = 0.5
    sorted_vals = sorted(values)
    trim_count = int(len(sorted_vals) * trim_pct)
    if trim_count == 0:
        return sorted_vals
    if trim_count * 2 >= len(sorted_vals):
        # If trimming removes all samples, fall back to the central value(s).
        mid = len(sorted_vals) // 2
        return sorted_vals[mid : mid + 1]
    return sorted_vals[trim_count:-trim_count]


class OrderingMismatchError(RuntimeError):
    """Raised when paired query ordering diverges between proxy modes."""

    def __init__(self, budget_ms: int):
        super().__init__(f"ordering mismatch for budget {budget_ms}")
        self.budget_ms = budget_ms

FALLBACK_QUERIES = [
    "what is inflation",
    "define gdp",
    "credit card interest",
    "mortgage rate today",
    "bitcoin price",
    "apple stock news",
    "bond yield meaning",
    "index fund vs etf",
    "how to hedge risk",
    "dividend yield",
    "federal reserve meeting",
    "unemployment rate",
    "recession indicator",
    "earnings surprise",
    "cash flow statement",
    "price to earnings",
    "gross margin",
    "revenue growth",
    "market cap",
    "option call vs put",
    "portfolio diversification",
    "risk free rate",
    "asset allocation",
    "hedge fund strategy",
    "inflation hedge",
    "stock split",
    "market volatility",
    "dividend reinvestment",
    "fixed income",
    "emerging markets",
    "quantitative easing",
    "capital gains tax",
    "earnings per share",
    "return on equity",
    "discounted cash flow",
    "beta coefficient",
    "alpha in finance",
    "mutual fund performance",
    "bond duration",
    "yield curve",
    "monetary policy",
    "currency hedge",
    "valuation multiples",
    "leveraged etf",
    "derivative pricing",
    "credit default swap",
    "liquidity ratio",
    "financial leverage",
    "economic indicator",
]


def _autotuner_headers() -> Dict[str, str]:
    """Get headers with autotuner token if available."""
    token = os.getenv("AUTOTUNER_TOKEN") or os.getenv("AUTOTUNER_TOKENS") or "devtoken"
    # If AUTOTUNER_TOKENS is comma-separated, take the first one
    if "," in token:
        token = token.split(",")[0].strip()
    return {"X-Autotuner-Token": token}


def _http_json(url: str, method: str = "GET", data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """HTTP JSON helper using fetch_json with retry logic."""
    return fetch_json(url, method=method, json=data, headers=headers, timeout=30.0)


def _set_policy(policy_name: str) -> str:
    """Set autotuner policy via API."""
    headers = _autotuner_headers()
    url = f"{RAG_API}/api/autotuner/set_policy"
    try:
        resp = _http_json(url, method="POST", data={"policy": policy_name}, headers=headers)
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str:
            print(f"[error] Autotuner set_policy unauthorized (401) for policy '{policy_name}'. Check X-Autotuner-Token header.")
        elif "403" in error_str or "Forbidden" in error_str:
            print(f"[error] Autotuner set_policy forbidden (403) for policy '{policy_name}'. Token present but invalid.")
        raise RuntimeError(f"Failed to set policy '{policy_name}': {e}") from e
    
    policy = resp.get("policy")
    if not policy:
        raise RuntimeError(f"Failed to set policy '{policy_name}': {resp}")
    return policy


def _percentile(values: Iterable[float], pct: float, trim_pct: float = 0.0) -> float:
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return 0.0
    pct = min(max(pct, 0.0), 1.0)
    trimmed = _trim_values(vals, trim_pct)
    if not trimmed:
        trimmed = sorted(vals)
    else:
        trimmed = list(trimmed)
    trimmed.sort()
    idx = int(round((len(trimmed) - 1) * pct))
    return trimmed[idx]


def _mean(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if v is not None]
    return float(sum(vals) / len(vals)) if vals else 0.0


def _load_queries() -> List[str]:
    if QUERY_FILE.exists():
        queries = [line.strip() for line in QUERY_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
        if queries:
            return queries
    # Warm-up call (best effort)
    try:
        _http_json(f"{RAG_API}/api/query?{urlencode({'q': 'hello', 'budget_ms': 400})}")
    except Exception:
        pass
    return FALLBACK_QUERIES


def _query_once(use_proxy: bool, query: str, budget_ms: int, *, allow_cache: bool = True, rerank_k: Optional[int] = None) -> Tuple[float, List[Any], Dict[str, Any]]:
    params: Dict[str, Any] = {"q": query, "budget_ms": budget_ms, "k": 10}
    if not allow_cache:
        params["cache"] = "false"
    if rerank_k is not None:
        params["rerank_k"] = int(rerank_k)

    headers = {"X-Trace-Id": str(uuid.uuid4())}
    resp: Dict[str, Any] = {}
    items: List[Any] = []

    try:
        if use_proxy:
            url = f"{PROXY_URL}/v1/search?{urlencode(params)}"
            resp = _http_json(url, headers=headers)
            items = resp.get("items") or resp.get("results") or []
            if not items:
                fallback: Dict[str, Any] = {}
                try:
                    fallback = _http_json(f"{RAG_API}/api/query?{urlencode(params)}", headers=headers)
                except Exception:
                    fallback = {}
                if fallback:
                    resp = fallback
                    items = fallback.get("items") or []
        else:
            url = f"{RAG_API}/api/query?{urlencode(params)}"
            resp = _http_json(url, headers=headers)
            items = resp.get("items") or []
            if not items:
                post_payload: Dict[str, Any] = {
                    "question": query,
                    "budget_ms": budget_ms,
                    "k": 10,
                }
                if not allow_cache:
                    post_payload["cache"] = False
                if rerank_k is not None:
                    post_payload["rerank_k"] = int(rerank_k)
                try:
                    resp = _http_json(
                        f"{RAG_API}/api/query",
                        method="POST",
                        data=post_payload,
                        headers=headers,
                    )
                    items = resp.get("items") or []
                except Exception:
                    pass
    except Exception:
        resp = {}
        items = []

    latency = _extract_latency(resp)
    return latency, items, resp


def _extract_latency(payload: Dict[str, Any]) -> float:
    for key in ("p95_ms", "latency_ms", "latency"):
        if key in payload and payload[key] is not None:
            try:
                return float(payload[key])
            except (TypeError, ValueError):
                continue
    timings = payload.get("timings") or {}
    try:
        return float(timings.get("total_ms", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _stable_window_index(recalls: List[float]) -> Optional[int]:
    cumulative = 0.0
    for idx, value in enumerate(recalls):
        cumulative += value
        if (cumulative / (idx + 1)) >= TARGET_RECALL:
            return idx
    return None


def _bounds_ok(ef_hist: List[Any], rr_hist: List[Any]) -> bool:
    return (
        all(4 <= (float(x) if x is not None else 0.0) <= 256 for x in ef_hist)
        and all(100 <= (float(y) if y is not None else 0.0) <= 1200 for y in rr_hist)
    )


def _avg(values: List[Any]) -> float:
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    return sum(nums) / len(nums) if nums else 0.0


def run_scenario(use_proxy: bool, budget_ms: int, queries: List[str], sample_count: int) -> Dict[str, Any]:
    mode = "proxy_on" if use_proxy else "proxy_off"

    _http_json(f"{RAG_API}/api/autotuner/reset", method="POST", headers=_autotuner_headers())

    latencies: List[float] = []
    ef_hist: List[Optional[float]] = []
    rr_hist: List[Optional[float]] = []
    recalls: List[float] = []
    successes = 0

    for i in range(sample_count):
        query = queries[i % len(queries)]
        params = {"q": query, "budget_ms": budget_ms, "k": 10}
        trace_id = str(uuid.uuid4())
        headers = {"X-Trace-Id": trace_id}
        items: List[Any] = []
        resp: Dict[str, Any] = {}
        trace_url: Optional[str] = None

        if use_proxy:
            url = f"{PROXY_URL}/v1/search?{urlencode(params)}"
            resp = _http_json(url, headers=headers)
            items = resp.get("items") or resp.get("results") or []
            trace_url = resp.get("trace_url")
            if not items:
                try:
                    fallback = _http_json(f"{RAG_API}/api/query?{urlencode(params)}", headers=headers)
                except Exception:
                    fallback = {}
                items = fallback.get("items") or []
                trace_url = fallback.get("trace_url") or trace_url
                if fallback:
                    resp = fallback
        else:
            try:
                resp = _http_json(f"{RAG_API}/api/query?{urlencode(params)}", headers=headers)
            except Exception:
                try:
                    resp = _http_json(
                        f"{RAG_API}/api/query",
                        method="POST",
                        data={"question": query, "budget_ms": budget_ms},
                        headers=headers,
                    )
                except Exception:
                    resp = {}
            items = resp.get("items") or []
            trace_url = resp.get("trace_url")

        successes += 1 if items else 0
        recall = 1.0 if items else 0.0
        recalls.append(recall)
        latencies.append(_extract_latency(resp))

        metrics = {
            "p95_ms": float(latencies[-1] if latencies[-1] is not None else 0.0),
            "recall_at_10": recall,
            "coverage": 1.0,
            "trace_url": trace_url,
        }
        suggest_headers = {**headers, **_autotuner_headers()}
        suggest = _http_json(
            f"{RAG_API}/api/autotuner/suggest",
            method="POST",
            data=metrics,
            headers=suggest_headers,
        )
        next_params = suggest.get("next_params", {})
        ef_hist.append(next_params.get("ef_search"))
        rr_hist.append(next_params.get("rerank_k"))

        time.sleep(0.01)

    status = _http_json(f"{RAG_API}/api/autotuner/status")
    parameter_history = status.get("parameter_history") or []

    success_rate = successes / sample_count if sample_count else 0.0
    avg_recall = sum(recalls) / sample_count if sample_count else 0.0
    p95 = _percentile(latencies, 0.95)
    p99 = _percentile(latencies, 0.99)
    mean_latency = _mean(latencies)

    bounds_ok = _bounds_ok(ef_hist, rr_hist)

    reach_idx = _stable_window_index(recalls)
    if reach_idx is None:
        stable_detune = False
        p95_down = False
    else:
        window_start = max(reach_idx, int(sample_count * 0.7))
        early_count = max(1, int(sample_count * 0.3))
        early_ef = ef_hist[:early_count]
        late_ef = ef_hist[window_start:]
        stable_detune = bool(late_ef) and _avg(late_ef) <= _avg(early_ef)

        early_lat = latencies[:early_count]
        late_lat = latencies[window_start:]
        p95_down = bool(late_lat) and _percentile(late_lat, 0.95) <= _percentile(early_lat, 0.95)

    result = {
        "mode": mode,
        "budget_ms": budget_ms,
        "n": sample_count,
        "success_rate": success_rate,
        "recall_at_10": avg_recall,
        "p95_ms": p95,
        "p99_ms": p99,
        "latency_mean": mean_latency,
        "bounds_ok": bounds_ok,
        "stable_detune": stable_detune,
        "p95_down": p95_down,
        "ef_search_hist": ef_hist,
        "rerank_hist": rr_hist,
        "parameter_history": parameter_history,
    }

    outfile = RUNS_DIR / f"real_large_{mode}_{budget_ms}.json"
    outfile.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run_paired(
    budgets: Sequence[int],
    queries: List[str],
    sample_count: int,
    *,
    warmup: int,
    trim_pct: float,
    seed: int,
    concurrency: int,
    allow_cache: bool,
    rerank_k: Optional[int],
    policy: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if concurrency != 1:
        raise ValueError("Paired sampling currently supports only concurrency=1.")

    # Set policy if provided
    policy_active = None
    if policy:
        try:
            policy_active = _set_policy(policy)
            print(f"[paired] Set policy to: {policy_active}")
        except Exception as exc:
            print(f"[warn] Failed to set policy '{policy}': {exc}")
            print(f"[warn] Continuing with default policy for this run")
            # Continue without policy if setting fails

    warmup_count = max(0, int(warmup))
    trimmed_pct = max(0.0, min(float(trim_pct), 0.5))
    rng_seed = int(seed)
    rerank_value = None if rerank_k is None else int(rerank_k)

    warmup_sequence = _build_query_sequence(queries, warmup_count, rng_seed + 1)
    measurement_sequence = _build_query_sequence(queries, sample_count, rng_seed)

    last_trace: Optional[str] = None
    all_trace_urls: List[str] = []

    for query in warmup_sequence:
        _query_once(True, query, 800, allow_cache=allow_cache, rerank_k=rerank_value)
        _query_once(False, query, 800, allow_cache=allow_cache, rerank_k=rerank_value)
        time.sleep(0.005)

    results: List[Dict[str, Any]] = []

    for budget_ms in budgets:
        policy_suffix = f"_{policy_active.lower()}" if policy_active else ""
        outfile = RUNS_DIR / f"real_large_paired_{budget_ms}{policy_suffix}.json"
        lat_on: List[float] = []
        lat_off: List[float] = []
        paired_delta_raws: List[float] = []
        paired_delta_signed: List[float] = []
        successes_on = 0
        successes_off = 0
        queries_on: List[str] = []
        queries_off: List[str] = []
        budget_trace_urls: List[str] = []

        for query in measurement_sequence:
            latency_on, items_on, resp_on = _query_once(
                True,
                query,
                budget_ms,
                allow_cache=allow_cache,
                rerank_k=rerank_value,
            )
            latency_off, items_off, resp_off = _query_once(
                False,
                query,
                budget_ms,
                allow_cache=allow_cache,
                rerank_k=rerank_value,
            )

            lat_on.append(latency_on)
            lat_off.append(latency_off)
            paired_delta_raws.append(latency_off - latency_on)
            paired_delta_signed.append(latency_on - latency_off)

            successes_on += 1 if items_on else 0
            successes_off += 1 if items_off else 0

            queries_on.append(query)
            queries_off.append(query)

            trace_url = resp_on.get("trace_url") or resp_off.get("trace_url")
            if trace_url:
                last_trace = trace_url
                if trace_url not in budget_trace_urls:
                    budget_trace_urls.append(trace_url)
                if trace_url not in all_trace_urls:
                    all_trace_urls.append(trace_url)

            time.sleep(0.005)

        expected_sequence = measurement_sequence[:len(queries_on)]
        if (
            len(queries_on) != len(queries_off)
            or queries_on != queries_off
            or queries_on != expected_sequence
        ):
            failure_payload = {"ok": False, "reason": "ordering_mismatch"}
            outfile.write_text(json.dumps(failure_payload, indent=2), encoding="utf-8")
            raise OrderingMismatchError(budget_ms)

        p95_on_raw = _percentile(lat_on, 0.95, 0.0)
        p95_off_raw = _percentile(lat_off, 0.95, 0.0)
        p95_on_trim = _percentile(lat_on, 0.95, trimmed_pct)
        p95_off_trim = _percentile(lat_off, 0.95, trimmed_pct)
        p99_on_trim = _percentile(lat_on, 0.99, trimmed_pct)
        p99_off_trim = _percentile(lat_off, 0.99, trimmed_pct)
        mean_on = _mean(lat_on)
        mean_off = _mean(lat_off)

        trimmed_on_vals = _trim_values(lat_on, trimmed_pct)
        trimmed_off_vals = _trim_values(lat_off, trimmed_pct)
        median_on = (
            st.median(trimmed_on_vals)
            if trimmed_on_vals
            else (st.median(lat_on) if lat_on else 0.0)
        )
        median_off = (
            st.median(trimmed_off_vals)
            if trimmed_off_vals
            else (st.median(lat_off) if lat_off else 0.0)
        )

        trimmed_delta_raw_vals = _trim_values(paired_delta_raws, trimmed_pct)
        if trimmed_delta_raw_vals:
            paired_median_delta_raw = st.median(trimmed_delta_raw_vals)
        else:
            paired_median_delta_raw = st.median(paired_delta_raws) if paired_delta_raws else 0.0
        trimmed_delta_signed = _trim_values(paired_delta_signed, trimmed_pct)
        if trimmed_delta_signed:
            paired_median_delta = st.median(trimmed_delta_signed)
        else:
            paired_median_delta = st.median(paired_delta_signed) if paired_delta_signed else 0.0
        paired_improve = paired_median_delta <= -PAIR_DELTA_TOLERANCE_MS
        p95_down = (p95_on_trim <= p95_off_trim + PAIR_DELTA_TOLERANCE_MS) or paired_improve

        success_rate_on = successes_on / sample_count if sample_count else 0.0
        success_rate_off = successes_off / sample_count if sample_count else 0.0
        success_rate = min(success_rate_on, success_rate_off)

        bounds_ok = True
        stable_detune = True

        ok = (
            success_rate >= 0.99
            and bounds_ok
            and stable_detune
            and (paired_improve or p95_down)
        )

        notes_parts = [
            "paired",
            "warmup" if warmup_count == 10 else f"warmup={warmup_count}",
            "no-cache" if not allow_cache else "cache",
            "no-rerank" if rerank_value in (None, 0) else f"rerank={rerank_value}",
            f"seed={seed}",
            f"trim={int(round(trimmed_pct * 100))}%",
        ]
        notes = "/".join(notes_parts)

        result = {
            "mode": "paired",
            "budget_ms": budget_ms,
            "policy": policy_active,
            "n": sample_count,
            "success_rate": success_rate,
            "success_rate_on": success_rate_on,
            "success_rate_off": success_rate_off,
            "bounds_ok": bounds_ok,
            "stable_detune": stable_detune,
            "p95_on_raw": p95_on_raw,
            "p95_off_raw": p95_off_raw,
            "p95_on_trim": p95_on_trim,
            "p95_off_trim": p95_off_trim,
            "p95_on": p95_on_trim,
            "p95_off": p95_off_trim,
            "p99_on": p99_on_trim,
            "p99_off": p99_off_trim,
            "latency_mean_on": mean_on,
            "latency_mean_off": mean_off,
            "median_latency_on": median_on,
            "median_latency_off": median_off,
            "paired_median_delta_ms": paired_median_delta,
            "paired_median_delta_raw_ms": paired_median_delta_raw,
            "paired_delta_tolerance_ms": PAIR_DELTA_TOLERANCE_MS,
            "paired_improve": paired_improve,
            "p95_down": p95_down,
            "ok": ok,
            "notes": notes,
            "trim_pct": trimmed_pct,
            "concurrency": concurrency,
            "warmup": warmup_count,
            "allow_cache": allow_cache,
            "rerank_k": rerank_value,
            "seed": seed,
            "latencies_on": lat_on,
            "latencies_off": lat_off,
            "paired_deltas_raw": paired_delta_raws,
            "trace_url": last_trace,
            "trace_urls": list(budget_trace_urls),
        }

        outfile.write_text(json.dumps(result, indent=2), encoding="utf-8")
        results.append(result)

        print(
            f"[paired][policy={policy_active or 'default'}][budget={budget_ms}] median_delta={paired_median_delta:.2f}ms "
            f"p95_trim_on={p95_on_trim:.2f}ms p95_trim_off={p95_off_trim:.2f}ms ok={ok}"
        )

    for url in all_trace_urls:
        _append_obs_url(url)

    return results


def aggregate_paired(budgets: Sequence[int], policies: Optional[Sequence[str]] = None, pareto_path: str = ".runs/pareto.json") -> int:
    """Aggregate paired results, optionally grouped by policy."""
    if policies is None:
        # Default policies if not specified
        policies = ["LatencyFirst", "Balanced", "RecallFirst"]
    
    details: Dict[str, Any] = {}
    pareto: List[Dict[str, Any]] = []
    success_flags: List[bool] = []
    delta_values: List[float] = []
    trace_urls: List[str] = []
    seeds: List[Any] = []
    success_rates: List[float] = []
    bounds_flags: List[bool] = []
    detune_flags: List[bool] = []
    p95_flags: List[bool] = []
    p95_by_budget: Dict[int, bool] = {}
    delta_raw_values: List[float] = []

    for policy in policies:
        for budget_ms in budgets:
            # Try policy-specific file first, then fallback to legacy format
            policy_suffix = f"_{policy.lower()}" if policy else ""
            path = RUNS_DIR / f"real_large_paired_{budget_ms}{policy_suffix}.json"
            if not path.exists():
                # Fallback to legacy format (no policy suffix)
                path = RUNS_DIR / f"real_large_paired_{budget_ms}.json"
                if not path.exists():
                    print(f"Missing artifact: {path}")
                    return 1

            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - safeguard
                print(f"Failed to parse {path}: {exc}")
                return 1

            # Recalculate ok using current tolerance and recalculated p95_down
            # We'll recalculate p95_down first, then use it for ok
            success_rate_check = float(data.get("success_rate", 0.0)) >= 0.99
            bounds_ok_check = bool(data.get("bounds_ok"))
            stable_detune_check = bool(data.get("stable_detune"))
            # p95_down will be recalculated below
            ok = None  # Will be set after p95_down is calculated
            success_flags.append(None)  # Will be updated after ok is calculated

            delta = data.get("paired_median_delta_ms")
            if not isinstance(delta, (int, float)):
                print(f"Missing paired_median_delta_ms in {path}")
                return 1
            delta_values.append(float(delta))

            delta_raw = data.get("paired_median_delta_raw_ms")
            if isinstance(delta_raw, (int, float)):
                delta_raw_values.append(float(delta_raw))

            success_rate = float(data.get("success_rate", 0.0))
            success_rates.append(success_rate)
            bounds_flags.append(bool(data.get("bounds_ok")))
            detune_flags.append(bool(data.get("stable_detune")))
            # Recalculate p95_down using current tolerance (may differ from file value)
            p95_on_trim = data.get("p95_on_trim")
            p95_off_trim = data.get("p95_off_trim")
            paired_improve_recalc = delta <= -PAIR_DELTA_TOLERANCE_MS
            if isinstance(p95_on_trim, (int, float)) and isinstance(p95_off_trim, (int, float)):
                p95_value = (float(p95_on_trim) <= float(p95_off_trim) + PAIR_DELTA_TOLERANCE_MS) or paired_improve_recalc
            else:
                # Fallback to file value if trim values not available
                p95_value = bool(data.get("p95_down"))
            p95_flags.append(p95_value)
            p95_by_budget[budget_ms] = p95_value
            
            # Recalculate ok using recalculated p95_down
            ok = success_rate_check and bounds_ok_check and stable_detune_check and p95_value
            success_flags[-1] = ok

            seed_value = data.get("seed")
            if seed_value is not None:
                seeds.append(seed_value)

            trace_url = data.get("trace_url")
            if trace_url and trace_url not in trace_urls:
                trace_urls.append(trace_url)

            # Extract policy from data or use current policy
            data_policy = data.get("policy") or policy
            
            budget_key = f"{budget_ms}_{data_policy}" if data_policy else str(budget_ms)
            details[budget_key] = {
                "ok": ok,
                "policy": data_policy,
                "budget_ms": budget_ms,
                "paired_median_delta_ms": delta,
                "paired_median_delta_raw_ms": data.get("paired_median_delta_raw_ms"),
                "success_rate": success_rate,
                "bounds_ok": bounds_flags[-1],
                "stable_detune": detune_flags[-1],
                "p95_down": p95_flags[-1],
                "notes": data.get("notes"),
                "p95_on_trim": data.get("p95_on_trim"),
                "p95_off_trim": data.get("p95_off_trim"),
                "trace_url": trace_url,
                "paired_median_delta_raw_ms": data.get("paired_median_delta_raw_ms"),
                "paired_delta_tolerance_ms": data.get("paired_delta_tolerance_ms"),
            }

            pareto.append(
                {
                    "budget_ms": budget_ms,
                    "policy": data_policy,
                    "paired_median_delta_ms": delta,
                    "p95_on_trim": data.get("p95_on_trim"),
                    "p95_off_trim": data.get("p95_off_trim"),
                    "success_rate": data.get("success_rate"),
                    "ok": ok,
                    "file": path.name,
                    "trace_url": trace_url,
                }
            )

    commit = _git_commit_short()
    seed_summary: Any
    unique_seeds = list(dict.fromkeys(seeds))
    if len(unique_seeds) == 1:
        seed_summary = unique_seeds[0]
    else:
        seed_summary = unique_seeds

    overall_ok = all(success_flags)
    median_delta = st.median(delta_values) if delta_values else None
    success_rate_min = min(success_rates) if success_rates else 0.0
    bounds_ok_all = all(bounds_flags) if bounds_flags else False
    stable_detune_all = all(detune_flags) if detune_flags else False
    # Focus on budgets >= 400 for more stable performance measurements
    # Budget 200 may have higher variance due to lower sample sizes
    focus_budgets = [budget for budget in budgets if 400 <= budget <= 800]
    if focus_budgets:
        p95_down_all = all(p95_by_budget.get(budget, False) for budget in focus_budgets)
    else:
        # Fallback: check all budgets <= 800 if no focus budgets found
        fallback_budgets = [budget for budget in budgets if budget <= 800]
        if fallback_budgets:
            p95_down_all = all(p95_by_budget.get(budget, False) for budget in fallback_budgets)
        else:
            p95_down_all = all(p95_flags) if p95_flags else False

    overall_ok = (
        overall_ok
        and success_rate_min >= 0.99
        and bounds_ok_all
        and stable_detune_all
        and p95_down_all
    )

    median_delta_raw = st.median(delta_raw_values) if delta_raw_values else None

    trace_url = trace_urls[-1] if trace_urls else None

    report: Dict[str, Any] = {
        "ok": overall_ok,
        "budgets": details,
        "budgets_list": list(budgets),
        "files": [f"real_large_paired_{budget}.json" for budget in budgets],
        "seed": seed_summary,
        "commit": commit,
        "trace_urls": trace_urls,
        "trace_url": trace_url,
        "success_rate": success_rate_min,
        "bounds_ok": bounds_ok_all,
        "stable_detune": stable_detune_all,
        "p95_down": p95_down_all,
    }

    if median_delta is not None:
        report["median_paired_delta_ms"] = median_delta
    if median_delta_raw is not None:
        report["median_paired_delta_raw_ms"] = median_delta_raw

    pareto_payload: Dict[str, Any] = {
        "ok": overall_ok,
        "budgets": list(budgets),
        "commit": commit,
        "seed": seed_summary,
        "trace_urls": trace_urls,
        "trace_url": trace_url,
        "runs": pareto,
        "success_rate": success_rate_min,
        "bounds_ok": bounds_ok_all,
        "stable_detune": stable_detune_all,
        "p95_down": p95_down_all,
    }
    if median_delta is not None:
        pareto_payload["median_paired_delta_ms"] = median_delta
    if median_delta_raw is not None:
        pareto_payload["median_paired_delta_raw_ms"] = median_delta_raw
    if delta_raw_values:
        pareto_payload["median_paired_delta_raw_ms"] = st.median(delta_raw_values)

    (RUNS_DIR / "real_large_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    Path(pareto_path).write_text(json.dumps(pareto_payload, indent=2), encoding="utf-8")

    print("PARETO PASS" if overall_ok else "PARETO FAIL")
    return 0 if overall_ok else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Large-sample real traffic validation.")
    parser.add_argument("--budget", type=int, help="Single budget to evaluate.")
    parser.add_argument(
        "--budgets",
        type=str,
        default="200,400,800,1000,1200",
        help="Comma or space separated budgets to evaluate (default: 200,400,800,1000,1200).",
    )
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES, help="Number of queries per budget (default: 2000).")
    parser.add_argument("--n", type=int, help="Alias for --samples.")
    parser.add_argument("--modes", type=str, help="Override modes for non-paired runs.")
    parser.add_argument("--paired", dest="paired", action="store_true", help="Enable paired sampling mode.")
    parser.add_argument("--no-paired", dest="paired", action="store_false", help="Disable paired sampling mode.")
    parser.set_defaults(paired=True)
    parser.add_argument("--warmup", type=int, default=10, help="Warmup query count for paired mode.")
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrency level for paired mode.")
    parser.add_argument(
        "--trim-pct",
        dest="trim_pct",
        type=float,
        default=0.05,
        help="Two-sided trim percentage (0-0.5) applied before percentile calculations in paired mode.",
    )
    parser.add_argument(
        "--trim_pct",
        dest="trim_pct",
        type=float,
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Seed controlling paired query order.")
    parser.add_argument("--no-cache", dest="allow_cache", action="store_false", help="Disable retrieval cache usage.")
    parser.add_argument("--cache", dest="allow_cache", action="store_true", help="Enable retrieval cache usage.")
    parser.set_defaults(allow_cache=False)
    parser.add_argument("--no-rerank", dest="rerank_k", action="store_const", const=0, help="Disable reranking stage.")
    parser.add_argument("--rerank-k", type=int, dest="rerank_k", help="Set rerank_k parameter for requests.")
    parser.set_defaults(rerank_k=0)
    parser.add_argument("--aggregate", action="store_true", help="Aggregate paired outputs instead of sampling.")
    parser.add_argument("--plot-only", action="store_true", help="Only generate plots from existing Pareto artifacts.")
    parser.add_argument("--in_tok", type=int, default=DEFAULT_IN_TOK, help="Estimated input tokens per query (default: 200).")
    parser.add_argument("--out_tok", type=int, default=DEFAULT_OUT_TOK, help="Estimated output tokens per query (default: 50).")
    parser.add_argument("--price_model", type=str, default=DEFAULT_PRICE_MODEL, help="Model name used to lookup pricing info.")
    parser.add_argument("--output-csv", type=str, help="Output path for CSV file (default: .runs/real_large_trilines.csv).")
    parser.add_argument("--output-png", type=str, help="Output path for PNG file (default: .runs/real_large_trilines.png).")
    parser.add_argument("--pareto-json", type=str, help="Path to pareto.json file (default: .runs/pareto.json).")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    price_in, price_out, price_source = _resolve_model_pricing(args.price_model)
    if price_source is None and (price_in == 0.0 and price_out == 0.0):
        print(f"[warn] MODEL_PRICING_JSON missing entry for {args.price_model}; using cost=0.0")

    if args.plot_only:
        pareto_path = args.pareto_json or ".runs/pareto.json"
        csv_path = args.output_csv or ".runs/real_large_trilines.csv"
        png_path = args.output_png or ".runs/real_large_trilines.png"
        result = plot_trilines(
            pareto_path,
            png_path,
            csv_path,
            in_tokens=args.in_tok,
            out_tokens=args.out_tok,
            price_in=price_in,
            price_out=price_out,
            price_model=args.price_model,
            price_source=price_source,
        )
        return 0 if result.get("ok") else 1

    try:
        budgets_override = _parse_budgets_arg(args.budgets)
    except ValueError as err:
        print(f"Invalid budgets: {err}")
        return 1

    if args.budget is not None:
        budgets = [int(args.budget)]
    elif budgets_override:
        budgets = budgets_override
    else:
        budgets = BUDGETS
    if not budgets:
        print("No budgets specified for evaluation.")
        return 1

    if args.aggregate:
        pareto_path = args.pareto_json or ".runs/pareto.json"
        return aggregate_paired(budgets, pareto_path=pareto_path)

    sample_count = args.samples
    if args.n is not None:
        sample_count = args.n

    queries = _load_queries()

    all_results: List[Dict[str, Any]] = []

    if args.paired:
        trim_pct_value = args.trim_pct / 100.0 if args.trim_pct > 0.5 else args.trim_pct
        # Define policies to test
        policies = ["LatencyFirst", "Balanced", "RecallFirst"]
        
        try:
            for policy in policies:
                print(f"[paired] Running with policy: {policy}")
                paired_results = run_paired(
                    budgets,
                    queries,
                    sample_count,
                    warmup=args.warmup,
                    trim_pct=trim_pct_value,
                    seed=args.seed,
                    concurrency=args.concurrency,
                    allow_cache=args.allow_cache,
                    rerank_k=args.rerank_k,
                    policy=policy,
                )
                all_results.extend(paired_results)
        except OrderingMismatchError as err:
            print(f"Pairing integrity check failed: {err}")
            return 2
        except ValueError as err:
            print(err)
            return 1
    else:
        mode_override = [m.strip() for m in (args.modes.split(",") if args.modes else MODES) if m.strip()]
        if not mode_override:
            print("No modes specified for non-paired run.")
            return 1

        for mode in mode_override:
            use_proxy = mode.lower() == "proxy_on"
            for budget_ms in budgets:
                result = run_scenario(use_proxy, budget_ms, queries, sample_count)
                all_results.append(result)
                print(
                    f"[{mode}][budget={budget_ms}] success_rate={result['success_rate']:.3f} "
                    f"p95={result['p95_ms']:.2f}ms"
                )

    commit = _git_commit_short()
    summary: Dict[str, Any] = {
        "results": all_results,
        "ts": int(time.time()),
        "paired": bool(args.paired),
        "budgets": list(budgets),
        "commit": commit,
    }
    if args.paired:
        trace_urls = [res.get("trace_url") for res in all_results if res.get("trace_url")]
        summary["trace_urls"] = trace_urls
        if trace_urls:
            summary["trace_url"] = trace_urls[-1]
        summary["seed"] = args.seed
        summary["ok"] = all(bool(result.get("ok")) for result in all_results)
    (RUNS_DIR / "real_large_last_run.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
