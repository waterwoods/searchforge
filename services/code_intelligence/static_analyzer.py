from __future__ import annotations

from typing import Dict, List, Any, Iterable, Optional, Tuple


def _min_max_norm(values: List[float]) -> Dict[int, float]:
    """Min-max normalize a list of numeric values.

    Returns mapping of original index -> normalized value in [0, 1].
    If there is no variance (max == min), returns 0.0 for all indices.
    """
    if not values:
        return {}
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        return {i: 0.0 for i in range(len(values))}
    scale = vmax - vmin
    return {i: (values[i] - vmin) / scale for i in range(len(values))}


def _looks_like_test_or_tool(path: str) -> bool:
    p = path.lower()
    excluded_fragments = (
        "/tests/",
        "/test/",
        "test_",
        "_test.py",
        "/tools/",
        "/scripts/",
        "/script/",
        "/benchmark/",
        "/bench/",
        "/examples/",
        "/example/",
        "/migrations/",
        "/venv/",
        "/node_modules/",
    )
    return any(fragment in p for fragment in excluded_fragments)


def _detect_entrypoint_signals(node: Dict[str, Any]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    fq_name = str(node.get("fqName", ""))
    evidence = node.get("evidence", {}) or {}
    snippet = str(evidence.get("snippet", ""))

    signals = 0

    # Name based heuristics
    name_lower = fq_name.lower()
    name_patterns = (
        "main",
        "handler",
        "handle_",
        "endpoint",
        "route",
        "controller",
        "api.",
        "cli",
        "command",
    )
    if any(p in name_lower for p in name_patterns):
        signals += 1
        reasons.append("fqName suggests entrypoint")

    # Snippet / decorator based heuristics (common Python web/CLI frameworks)
    snippet_lower = snippet.lower()
    decorator_patterns = (
        "@app.get",
        "@app.post",
        "@app.put",
        "@app.delete",
        "@router.get",
        "@router.post",
        "@router.put",
        "@router.delete",
        "@bp.route",
        "flask",
        "fastapi",
        "falcon",
        "django",
        "@click.command",
        "@click.group",
        "typer.run",
        "if __name__ == \"__main__\":",
    )
    if any(p in snippet_lower for p in decorator_patterns):
        signals += 1
        reasons.append("decorator/snippet indicates entrypoint")

    # Treat strong signals as entrypoints
    is_entry = signals > 0
    if is_entry and not reasons:
        reasons.append("entrypoint-like")
    return is_entry, reasons


def _safe_get_number(container: Dict[str, Any], *path: str, default: float = 0.0) -> float:
    cur: Any = container
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    try:
        return float(cur)
    except (TypeError, ValueError):
        return default


def layer1_static_filter(all_nodes: List[Dict[str, Any]], top_k: int = 200) -> List[Dict[str, Any]]:
    """Layer-1 static rules filter for important nodes.

    Inputs
    - all_nodes: list of node dicts (from codegraph), each may include keys like:
        - id: str
        - fqName: str
        - kind: str
        - evidence: { file: str, snippet: str, ... }
        - metrics: { loc: int, complexity: int, ... }
        - hotness_score: number (optional)
        - data.risk_index: number (optional)

    Scoring signals (additive):
    - Entry decorators/heuristics (strong weight)
    - Higher cyclomatic complexity
    - Higher LOC
    - Higher in-degree (if present on node as one of: in_degree/inDegree/fanIn)
    - Light tie-breakers: hotness_score, risk_index

    Exclusions
    - Nodes from tests/tooling/scripts/bench/examples/etc are removed up-front.

    Returns top_k candidates as list of { nodeId, score, reasons }.
    """
    if not isinstance(all_nodes, list):
        return []

    working: List[Dict[str, Any]] = []
    for node in all_nodes:
        if not isinstance(node, dict):
            continue

        node_id = str(node.get("id", ""))
        if not node_id:
            continue

        evidence = node.get("evidence", {}) or {}
        file_path = str(evidence.get("file", ""))
        if _looks_like_test_or_tool(file_path):
            # Exclude tests/tools
            continue

        working.append(node)

    # Collect raw metrics for normalization
    loc_values: List[float] = []
    cpx_values: List[float] = []
    indeg_values: List[float] = []
    hot_values: List[float] = []
    risk_values: List[float] = []

    indeg_present_flags: List[bool] = []

    for node in working:
        metrics = node.get("metrics", {}) or {}
        loc_values.append(_safe_get_number({"m": metrics}, "m", "loc", default=0.0))
        cpx_values.append(_safe_get_number({"m": metrics}, "m", "complexity", default=0.0))

        # Try multiple common keys for inbound degree-like signals if present on nodes
        indeg = (
            _safe_get_number(node, "in_degree", default=float("nan"))
            if "in_degree" in node
            else _safe_get_number(node, "inDegree", default=float("nan"))
        )
        if indeg != indeg:  # NaN check
            indeg = _safe_get_number(metrics, "in_degree", default=float("nan"))
        if indeg != indeg:
            indeg = _safe_get_number(metrics, "fanIn", default=float("nan"))

        if indeg == indeg:  # not NaN
            indeg_values.append(indeg)
            indeg_present_flags.append(True)
        else:
            indeg_values.append(0.0)
            indeg_present_flags.append(False)

        hot_values.append(_safe_get_number(node, "hotness_score", default=0.0))
        risk_values.append(_safe_get_number(node, "data", "risk_index", default=0.0))

    # Normalize
    loc_norm = _min_max_norm(loc_values)
    cpx_norm = _min_max_norm(cpx_values)
    indeg_norm = _min_max_norm(indeg_values) if any(indeg_present_flags) else {}
    hot_norm = _min_max_norm(hot_values)
    risk_norm = _min_max_norm(risk_values)

    # Aggregate scores
    results: List[Dict[str, Any]] = []
    for idx, node in enumerate(working):
        node_id = str(node.get("id"))
        metrics = node.get("metrics", {}) or {}
        evidence = node.get("evidence", {}) or {}

        reasons: List[str] = []
        entrypoint, entry_reasons = _detect_entrypoint_signals(node)
        if entrypoint:
            reasons.extend(entry_reasons)

        # Core normalized metrics
        cpx_score = cpx_norm.get(idx, 0.0)
        loc_score = loc_norm.get(idx, 0.0)
        indegree_score = indeg_norm.get(idx, 0.0) if indeg_norm else 0.0
        hot_score = hot_norm.get(idx, 0.0)
        risk_score = risk_norm.get(idx, 0.0)

        if cpx_score > 0.8:
            reasons.append("high complexity")
        if loc_score > 0.8:
            reasons.append("large LOC")
        if indegree_score > 0.8:
            reasons.append("high fan-in")

        # Weighted sum
        score = (
            (3.0 if entrypoint else 0.0)
            + 1.5 * cpx_score
            + 1.2 * loc_score
            + 1.3 * indegree_score
            + 0.3 * hot_score
            + 0.2 * risk_score
        )

        if not reasons:
            # Provide at least one rationale
            top_signal = max(
                (
                    (cpx_score, "complexity"),
                    (loc_score, "loc"),
                    (indegree_score, "fan-in"),
                    (hot_score, "hotness"),
                    (risk_score, "risk"),
                ),
                key=lambda x: x[0],
            )
            if top_signal[0] > 0:
                reasons.append(f"notable {top_signal[1]}")

        results.append(
            {
                "nodeId": node_id,
                "score": float(score),
                "reasons": reasons,
            }
        )

    # Sort and take top_k
    results.sort(key=lambda r: r["score"], reverse=True)
    if top_k is not None and top_k > 0:
        results = results[:top_k]

    return results


__all__ = ["layer1_static_filter"]


