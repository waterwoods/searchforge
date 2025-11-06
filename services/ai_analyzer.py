from __future__ import annotations

import os
import json
import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    # Prefer async client for true parallelism
    from openai import AsyncOpenAI  # type: ignore
except Exception:  # pragma: no cover - library may not be installed in some environments
    AsyncOpenAI = None  # type: ignore


# In-memory cache simulating a `node_intelligence` store
NODE_INTELLIGENCE_STORE: Dict[str, Dict[str, Any]] = {}

# Allowed tags for classification
ALLOWED_TAGS = {"Entry", "Core", "Bottleneck", "TechDebt"}


def _get_node_id(node: Any) -> Optional[str]:
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return None
    return (
        node.get("id")
        or node.get("node_id")
        or node.get("fid")
        or node.get("uid")
        or node.get("name")
    )


def _extract_context_fields(node: Dict[str, Any]) -> Tuple[str, str, str]:
    fq_name = (
        node.get("fqName")
        or node.get("fqname")
        or node.get("qualified_name")
        or node.get("name")
        or node.get("id")
        or "unknown"
    )
    kind = node.get("kind") or node.get("type") or node.get("node_type") or "unknown"

    evidence = node.get("evidence") if isinstance(node.get("evidence"), dict) else {}
    snippet = (
        node.get("snippet")
        or node.get("code")
        or node.get("codeSnippet")
        or node.get("code_snippet")
        or node.get("text")
        or (evidence.get("snippet") if isinstance(evidence, dict) else None)
        or ""
    )
    return str(fq_name), str(kind), str(snippet)


async def _call_llm(client: Any, model: str, prompt: str) -> Dict[str, Any]:
    """Call OpenAI chat.completions with JSON response enforcement."""
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert Staff Software Engineer. "
                        "Return concise JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception:
        # Best-effort fallback: try to extract a JSON object substring
        try:
            text = locals().get("content", "")
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start : end + 1])
        except Exception:
            pass
        return {}


async def layer3_ai_analysis(top_nodes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Layer-3 deep paid analysis using gpt-4o-mini in parallel.

    Inputs:
        top_nodes: Layer-2 output list of top-80 node dicts (or ids). We will analyze the top-50.

    Behavior:
        - Build prompts per node requesting JSON with fields:
          aiSummary, aiImportance (0-10), aiTags ["Entry","Core","Bottleneck","TechDebt"].
        - Execute OpenAI calls in parallel using AsyncOpenAI and asyncio.gather.
        - Persist results into NODE_INTELLIGENCE_STORE.

    Returns:
        Mapping of node_id -> stored intelligence payload.
    """
    if not isinstance(top_nodes, list) or not top_nodes:
        return {}

    # Take top-50 only
    candidates = top_nodes[:50]

    # Initialize async OpenAI client lazily
    if AsyncOpenAI is None:  # pragma: no cover
        raise RuntimeError("openai package with AsyncOpenAI client is required for layer3 analysis")

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model_name = "gpt-4o-mini"

    # Limit concurrent LLM calls to avoid local resource exhaustion
    concurrency = int(os.getenv("AI_ANALYZER_CONCURRENCY", "8"))
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def analyze_one(node_like: Any) -> Optional[Tuple[str, Dict[str, Any]]]:
        node_id = _get_node_id(node_like)
        if not node_id:
            return None

        node_dict: Dict[str, Any] = node_like if isinstance(node_like, dict) else {"id": node_id}
        fq_name, kind, snippet = _extract_context_fields(node_dict)

        prompt = (
            "Analyze this repository node and return strictly a compact JSON object with keys: "
            "aiSummary (string <= 80 words), aiImportance (integer 0-10), aiTags (array subset of: "
            "['Entry','Core','Bottleneck','TechDebt']). Do not include any extra fields.\n\n"
            f"Node: {fq_name}\nKind: {kind}\n\n"
            "Relevant Code Snippet (may be empty):\n" + snippet[:1200]
        )

        async with semaphore:
            payload = await _call_llm(client, model_name, prompt)

        # Normalize fields
        ai_summary = str(payload.get("aiSummary", "")).strip()
        try:
            ai_importance = int(payload.get("aiImportance", 0))
        except Exception:
            ai_importance = 0
        raw_tags = payload.get("aiTags", [])
        if isinstance(raw_tags, str):
            # allow comma-separated fallback
            raw_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        ai_tags = [t for t in raw_tags if isinstance(t, str) and t in ALLOWED_TAGS]

        record = {
            "nodeId": node_id,
            "aiSummary": ai_summary,
            "aiImportance": max(0, min(10, ai_importance)),
            "aiTags": ai_tags,
            "model": model_name,
            "ts": int(time.time()),
        }

        NODE_INTELLIGENCE_STORE[node_id] = record
        return node_id, record

    results = await asyncio.gather(*(analyze_one(n) for n in candidates), return_exceptions=False)

    out: Dict[str, Dict[str, Any]] = {}
    for item in results:
        if not item:
            continue
        nid, rec = item
        out[nid] = rec
    return out


def get_node_intelligence(node_id: str) -> Optional[Dict[str, Any]]:
    """Fetch stored intelligence for a node from the in-memory store."""
    if not node_id:
        return None
    return NODE_INTELLIGENCE_STORE.get(node_id)


__all__ = [
    "layer3_ai_analysis",
    "get_node_intelligence",
    "NODE_INTELLIGENCE_STORE",
]











