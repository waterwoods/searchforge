from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import OpenAI


class LLMDisabled(Exception):
    """Raised when LLM reflections are disabled or unavailable."""


def _render_prompt(summary: Dict[str, Any], suggestion: Dict[str, Any], baseline: Optional[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("Job metrics snapshot:")
    for key in ("p95_ms", "err_rate", "recall_at_10", "cost_tokens"):
        value = summary.get(key)
        lines.append(f"{key}: {value!r}")

    lines.append("")
    lines.append("Baseline metrics:")
    if baseline:
        for key in ("p95_ms", "err_rate", "recall_at_10"):
            lines.append(f"{key}: {baseline.get(key)!r}")
    else:
        lines.append("baseline: None")

    lines.append("")
    lines.append("Suggested changes:")
    changes = suggestion.get("changes", {}) if suggestion else {}
    if changes:
        for k, v in changes.items():
            lines.append(f"{k}: {v!r}")
    else:
        lines.append("changes: {}")

    lines.append("")
    lines.append(f"Expected effect: {suggestion.get('expected_effect')}")
    lines.append(f"Risk: {suggestion.get('risk')}")
    lines.append("")
    lines.append("Produce 2-6 operational bullets covering latency, quality, risk, and cost trends.")
    lines.append("Each bullet under 18 words; avoid redundant phrasing.")

    # limit prompt length for safety
    return "\n".join(lines[:24])


def _normalize_bullets(raw: str) -> List[str]:
    if not raw:
        return []
    raw_lines = [line.strip(" -•\t") for line in raw.splitlines()]
    bullets = [line for line in raw_lines if line]

    if len(bullets) < 2:
        combined = " ".join(bullets).split(". ")
        bullets = [part.strip().rstrip(".") for part in combined if part.strip()]

    bullets = [line[:200] for line in bullets]
    return bullets[:6]


def _estimate_cost(
    tokens_in: Optional[int],
    tokens_out: Optional[int],
    input_per_mtok: Optional[float],
    output_per_mtok: Optional[float],
) -> Optional[float]:
    if tokens_in is None and tokens_out is None:
        return None
    if input_per_mtok is None and output_per_mtok is None:
        return None

    total = 0.0
    if tokens_in is not None and input_per_mtok is not None:
        total += (tokens_in / 1_000_000.0) * input_per_mtok
    if tokens_out is not None and output_per_mtok is not None:
        total += (tokens_out / 1_000_000.0) * output_per_mtok

    return total if total > 0 else None


def reflect_with_llm(
    conf: Dict[str, Any],
    summary: Dict[str, Any],
    suggestion: Dict[str, Any],
    baseline: Optional[Dict[str, Any]],
    max_tokens: int = 256,
) -> Dict[str, Any]:
    api_key = conf.get("api_key")
    model = conf.get("model")
    if not api_key or not model:
        raise LLMDisabled("LLM disabled: missing API key or model")

    client = OpenAI(api_key=api_key)

    prompt = _render_prompt(summary, suggestion, baseline)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an SRE lead summarizing experiment telemetry for executives.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=max_tokens,
    )

    content = None
    if response.choices:
        content = response.choices[0].message.content

    tokens_in = getattr(getattr(response, "usage", None), "prompt_tokens", None)
    tokens_out = getattr(getattr(response, "usage", None), "completion_tokens", None)

    cost = _estimate_cost(tokens_in, tokens_out, conf.get("input_per_mtok"), conf.get("output_per_mtok"))

    points = _normalize_bullets(content or "")

    return {
        "points": points,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd_est": cost,
    }

