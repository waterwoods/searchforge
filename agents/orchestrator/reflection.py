"""
Reflection module for post-phase analysis.

The orchestrator uses the reflection decision to determine whether to continue
searching, shrink the parameter space, or stop early.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import statistics
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from observe.logging import EventLogger


@dataclass
class ReflectionDecision:
    action: str
    reason: str

    def to_dict(self) -> Dict[str, str]:
        return {"action": self.action, "reason": self.reason}


def _compute_failure_rate(results: Iterable[Dict[str, Any]]) -> float:
    results = list(results)
    if not results:
        return 0.0
    failures = sum(1 for item in results if item.get("status") != "ok")
    return failures / len(results)


def _compute_recall_variance(results: Iterable[Dict[str, Any]]) -> float:
    recalls: List[float] = []
    for item in results:
        metrics = item.get("metrics") or {}
        recall = metrics.get("recall_at_10")
        if recall is not None:
            recalls.append(float(recall))
    if len(recalls) < 2:
        return 0.0
    return statistics.pvariance(recalls)


def post_phase_reflect(
    stats: Dict[str, Any],
    *,
    logger: Optional[EventLogger] = None,
) -> Dict[str, str]:
    """
    Analyze stage statistics and return a reflection decision.

    Expected stats keys:
        - run_id: str
        - stage: str
        - results: Iterable[dict] with `status` and `metrics`
        - thresholds.failure_rate: float (default 0.3)
        - thresholds.recall_variance: float (default 0.02)
    """

    run_id = stats.get("run_id")
    stage = stats.get("stage", "UNKNOWN").upper()
    results = stats.get("results") or []

    thresholds = stats.get("thresholds") or {}
    failure_threshold = float(thresholds.get("failure_rate", 0.3))
    variance_threshold = float(thresholds.get("recall_variance", 0.02))

    failure_rate = float(stats.get("failure_rate") or _compute_failure_rate(results))
    recall_variance = float(
        stats.get("recall_variance") or _compute_recall_variance(results)
    )

    if failure_rate >= failure_threshold:
        decision = ReflectionDecision(
            action="early_stop",
            reason=f"failure_rate {failure_rate:.2%} exceeds threshold {failure_threshold:.0%}",
        )
    elif recall_variance >= variance_threshold:
        decision = ReflectionDecision(
            action="shrink",
            reason=f"recall variance {recall_variance:.4f} exceeds threshold {variance_threshold:.4f}",
        )
    else:
        decision = ReflectionDecision(action="keep", reason="metrics stable")

    if logger is not None and run_id:
        logger.log_event(
            run_id,
            "REFLECTION_DECISION",
            {
                "stage": stage,
                "action": decision.action,
                "reason": decision.reason,
                "failure_rate": failure_rate,
                "recall_variance": recall_variance,
            },
        )

    return decision.to_dict()


def sanitize_and_shorten(text: str, max_chars: int = 1200) -> str:
    """
    Sanitize text by masking sensitive patterns (paths, URLs, keys) and truncate.
    
    Args:
        text: Input text to sanitize
        max_chars: Maximum characters to keep
    
    Returns:
        Sanitized and truncated text
    """
    if not text:
        return ""
    
    # Patterns to mask
    patterns = [
        (r'/[^\s]+', '[PATH]'),  # File paths
        (r'https?://[^\s]+', '[URL]'),  # URLs
        (r'sk-[a-zA-Z0-9]{32,}', '[API_KEY]'),  # OpenAI API keys
        (r'[a-zA-Z0-9]{32,}', '[HASH]'),  # Long hashes
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),  # IP addresses
    ]
    
    sanitized = text
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized)
    
    # Truncate if needed
    if len(sanitized) > max_chars:
        sanitized = sanitized[:max_chars] + "..."
    
    return sanitized


class ReflectionCache:
    """Cache for LLM reflection results based on prompt hash."""
    
    def __init__(self, storage_path: str = "reports/reflection_cache.jsonl") -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache from disk."""
        if not self.storage_path.exists():
            return
        
        try:
            with self.storage_path.open("r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        prompt_hash = entry.get("prompt_hash")
                        if prompt_hash:
                            self._cache[prompt_hash] = entry.get("payload", {})
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception:
            pass
    
    def get(self, prompt_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached result by prompt hash."""
        with self._lock:
            return self._cache.get(prompt_hash)
    
    def set(self, prompt_hash: str, payload: Dict[str, Any]) -> None:
        """Store result in cache."""
        with self._lock:
            self._cache[prompt_hash] = payload
            # Append to JSONL file
            try:
                entry = {
                    "prompt_hash": prompt_hash,
                    "payload": payload,
                    "timestamp": time.time(),
                }
                with self.storage_path.open("a", encoding="utf-8") as fp:
                    fp.write(json.dumps(entry) + "\n")
            except Exception:
                pass


# Global cache instance
_reflection_cache: Optional[ReflectionCache] = None


def _get_cache() -> ReflectionCache:
    """Get or create global cache instance."""
    global _reflection_cache
    if _reflection_cache is None:
        _reflection_cache = ReflectionCache()
    return _reflection_cache


def summarize(
    stage: str,
    kpis: Dict[str, Any],
    sla: Dict[str, Any],
    llm_cfg: Dict[str, Any],
    *,
    prompt_hash: Optional[str] = None,
    spent_cost: float = 0.0,
) -> Dict[str, Any]:
    """
    Generate a reflection summary for a completed stage.
    
    Args:
        stage: Stage name (e.g., "SMOKE", "GRID")
        kpis: Key performance indicators (metrics, duration, etc.)
        sla: SLA verification results
        llm_cfg: LLM configuration dict with keys:
            - enable: bool
            - provider: str (e.g., "openai")
            - model: str
            - max_tokens: int
            - temperature: float
            - cost_cap_usd: float
        prompt_hash: Optional pre-computed prompt hash for caching
        spent_cost: Cumulative cost spent so far in this run
    
    Returns:
        Dict with keys:
            - stage: str
            - model: str
            - tokens: int
            - cost_usd: float
            - confidence: float (0.0-1.0)
            - cache_hit: bool
            - blocked: bool
            - elapsed_ms: int
            - prompt_hash: str
            - rationale_md: str (markdown summary, full)
            - rationale_md_lite: str (sanitized and shortened)
            - next_actions: List[Dict] with {id, label, eta_min}
            - detail_level: str ("full")
    """
    start_time = time.monotonic()
    stage_upper = stage.upper()
    
    # Default response structure
    result = {
        "stage": stage_upper,
        "model": "rule-engine",
        "tokens": 0,
        "cost_usd": 0.0,
        "confidence": 0.5,
        "cache_hit": False,
        "blocked": False,
        "elapsed_ms": 0,
        "prompt_hash": "",
        "rationale_md": "",
        "rationale_md_lite": "",
        "next_actions": [],
        "detail_level": "full",
    }
    
    # Check if LLM is enabled and cost cap allows
    llm_enabled = llm_cfg.get("enable", False)
    cost_cap = float(llm_cfg.get("cost_cap_usd", 0.50))
    
    if not llm_enabled or cost_cap <= spent_cost:
        # Rule-based fallback (blocked or disabled)
        result["blocked"] = True
        result["rationale_md"] = _rule_based_summary(stage_upper, kpis, sla)
        result["rationale_md_lite"] = sanitize_and_shorten(result["rationale_md"])
        result["next_actions"] = _rule_based_next_actions(stage_upper, kpis, sla)
        result["elapsed_ms"] = int((time.monotonic() - start_time) * 1000)
        return result
    
    # Compute prompt hash if not provided
    if prompt_hash is None:
        prompt_data = {
            "stage": stage_upper,
            "metrics": kpis.get("metrics", {}),
            "sla_verdict": sla.get("verdict", "unknown"),
        }
        prompt_hash = hashlib.sha256(
            json.dumps(prompt_data, sort_keys=True).encode()
        ).hexdigest()[:16]
    
    result["prompt_hash"] = prompt_hash
    
    # Check cache first
    cache = _get_cache()
    cached_result = cache.get(prompt_hash)
    if cached_result:
        result.update(cached_result)
        result["cache_hit"] = True
        result["cost_usd"] = 0.0  # Cached results have no cost
        result["tokens"] = 0
        result["rationale_md_lite"] = sanitize_and_shorten(result.get("rationale_md", ""))
        result["elapsed_ms"] = int((time.monotonic() - start_time) * 1000)
        return result
    
    # Try LLM-based summarization
    try:
        llm_result = _llm_summarize(stage_upper, kpis, sla, llm_cfg, prompt_hash, spent_cost)
        
        # Check if cost would exceed cap
        estimated_cost = llm_result.get("cost_usd", 0.0)
        if spent_cost + estimated_cost > cost_cap:
            # Blocked by cost cap
            result["blocked"] = True
            result["rationale_md"] = _rule_based_summary(stage_upper, kpis, sla)
            result["rationale_md_lite"] = sanitize_and_shorten(result["rationale_md"])
            result["next_actions"] = _rule_based_next_actions(stage_upper, kpis, sla)
        else:
            result.update(llm_result)
            result["rationale_md_lite"] = sanitize_and_shorten(result.get("rationale_md", ""))
            # Cache the result
            cache.set(prompt_hash, {
                "model": result["model"],
                "tokens": result["tokens"],
                "cost_usd": result["cost_usd"],
                "confidence": result["confidence"],
                "rationale_md": result["rationale_md"],
                "next_actions": result["next_actions"],
            })
    except Exception as e:
        # Fallback to rule-based on error
        result["rationale_md"] = _rule_based_summary(stage_upper, kpis, sla)
        result["rationale_md_lite"] = sanitize_and_shorten(result["rationale_md"])
        result["next_actions"] = _rule_based_next_actions(stage_upper, kpis, sla)
        result["model"] = "rule-engine"  # Indicate fallback
    
    result["elapsed_ms"] = int((time.monotonic() - start_time) * 1000)
    return result


def _rule_based_summary(stage: str, kpis: Dict[str, Any], sla: Dict[str, Any]) -> str:
    """Generate a rule-based markdown summary."""
    lines = [f"# Stage: {stage}", ""]
    
    # Add metrics summary
    metrics = kpis.get("metrics", {})
    if metrics:
        lines.append("## Metrics")
        if "recall_at_10" in metrics:
            lines.append(f"- Recall@10: {metrics['recall_at_10']:.4f}")
        if "p95_ms" in metrics:
            lines.append(f"- P95 Latency: {metrics['p95_ms']:.2f} ms")
        if "cost" in metrics:
            lines.append(f"- Cost: {metrics['cost']:.4f}")
        lines.append("")
    
    # Add SLA status
    sla_verdict = sla.get("verdict", "unknown")
    lines.append(f"## SLA Status: {sla_verdict.upper()}")
    sla_checks = sla.get("checks", [])
    if sla_checks:
        for check in sla_checks:
            status = "✓" if check.get("passed", False) else "✗"
            lines.append(f"- {status} {check.get('name', 'Unknown')}: {check.get('message', '')}")
    lines.append("")
    
    # Add stage-specific notes
    duration_ms = kpis.get("duration_ms", 0)
    if duration_ms:
        lines.append(f"## Duration: {duration_ms} ms")
    
    return "\n".join(lines)


def _rule_based_next_actions(stage: str, kpis: Dict[str, Any], sla: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate rule-based next actions."""
    actions = []
    
    # Determine next stage
    stage_order = ["SMOKE", "GRID", "AB", "SELECT", "PUBLISH"]
    try:
        current_idx = stage_order.index(stage)
        if current_idx < len(stage_order) - 1:
            next_stage = stage_order[current_idx + 1]
            actions.append({
                "id": f"proceed_to_{next_stage.lower()}",
                "label": f"Proceed to {next_stage}",
                "eta_min": _estimate_eta_min(next_stage),
            })
    except ValueError:
        pass
    
    # Add action based on SLA
    sla_verdict = sla.get("verdict", "unknown")
    if sla_verdict == "fail":
        actions.append({
            "id": "review_sla_violations",
            "label": "Review SLA violations",
            "eta_min": 5,
        })
    
    return actions


def _estimate_eta_min(stage: str) -> int:
    """Estimate ETA in minutes for a stage."""
    estimates = {
        "SMOKE": 2,
        "GRID": 10,
        "AB": 5,
        "SELECT": 1,
        "PUBLISH": 2,
    }
    return estimates.get(stage, 5)


def _llm_summarize(
    stage: str,
    kpis: Dict[str, Any],
    sla: Dict[str, Any],
    llm_cfg: Dict[str, Any],
    prompt_hash: str,
    spent_cost: float,
) -> Dict[str, Any]:
    """Call LLM to generate reflection summary."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("OpenAI package not available")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    provider = llm_cfg.get("provider", "openai")
    if provider != "openai":
        raise ValueError(f"Unsupported provider: {provider}")
    
    model = llm_cfg.get("model", "gpt-4o-mini")
    max_tokens = llm_cfg.get("max_tokens", 512)
    temperature = llm_cfg.get("temperature", 0.2)
    cost_cap = llm_cfg.get("cost_cap_usd", 0.50)
    
    client = OpenAI(api_key=api_key)
    
    # Build prompt
    prompt_data = {
        "stage": stage,
        "metrics": kpis.get("metrics", {}),
        "duration_ms": kpis.get("duration_ms", 0),
        "sla_verdict": sla.get("verdict", "unknown"),
        "sla_checks": sla.get("checks", []),
    }
    
    system_prompt = (
        "You are an expert ML engineer analyzing experiment stage results. "
        "Return a JSON object with 'rationale_md' (markdown summary) and 'next_actions' (array of {id, label, eta_min}). "
        "Be concise and actionable."
    )
    
    user_prompt = (
        f"Analyze the {stage} stage results:\n\n"
        f"Metrics: {json.dumps(prompt_data['metrics'], indent=2)}\n"
        f"Duration: {prompt_data['duration_ms']} ms\n"
        f"SLA Verdict: {prompt_data['sla_verdict']}\n"
        f"SLA Checks: {json.dumps(prompt_data['sla_checks'], indent=2)}\n\n"
        "Provide a brief markdown summary and suggest next actions."
    )
    
    # Call LLM
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content or "{}"
        llm_data = json.loads(content)
        
        # Extract usage
        usage = response.usage
        tokens_used = usage.total_tokens if usage else 0
        
        # Estimate cost (rough pricing for gpt-4o-mini: $0.15/$0.60 per 1M tokens)
        cost_per_1m_input = 0.15
        cost_per_1m_output = 0.60
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        cost_usd = (input_tokens * cost_per_1m_input + output_tokens * cost_per_1m_output) / 1_000_000
        
        # Check cost cap (should have been checked before, but double-check)
        if spent_cost + cost_usd > cost_cap:
            raise ValueError(f"Cost ${spent_cost + cost_usd:.4f} would exceed cap ${cost_cap:.4f}")
        
        # Extract results
        rationale_md = llm_data.get("rationale_md", "")
        next_actions = llm_data.get("next_actions", [])
        
        # Validate next_actions format
        validated_actions = []
        for action in next_actions:
            if isinstance(action, dict) and "id" in action and "label" in action:
                validated_actions.append({
                    "id": str(action["id"]),
                    "label": str(action["label"]),
                    "eta_min": int(action.get("eta_min", 5)),
                })
        
        return {
            "model": model,
            "tokens": tokens_used,
            "cost_usd": round(cost_usd, 6),
            "confidence": 0.8,  # LLM-based summaries have higher confidence
            "cache_hit": False,
            "blocked": False,
            "rationale_md": rationale_md,
            "next_actions": validated_actions,
            "prompt_hash": prompt_hash,
        }
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}") from e

