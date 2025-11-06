"""Golden Path extraction module.

This module provides the core algorithm to compute a concise, guided path
through the code graph starting from a given entry node. The algorithm:

- Prefers AI-labeled "Core" nodes (Layer 3) if available.
- Otherwise falls back to the path from the entry node to the PageRank top-1
  node in the graph.
- Ensures the returned path has a length between 5 and 9 nodes by trimming or
  expanding along outgoing edges when possible.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

import networkx as nx


def _normalize_ai_label(value: object) -> Optional[str]:
    """Best-effort normalization for AI label values.

    Accepts a variety of shapes that might appear in a simulated Layer 3 store
    or node attributes and attempts to resolve them to a single string label.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # Common possibilities: {"label": "Core"} or nested fields
        for key in ("label", "ai_label", "value", "tag"):
            if key in value and isinstance(value[key], str):
                return value[key]
        return None
    if isinstance(value, (list, tuple)):
        # If a list of tags, prefer literal "Core" when present
        for item in value:
            lab = _normalize_ai_label(item)
            if lab == "Core":
                return lab
        # Fallback to first string-like label
        for item in value:
            if isinstance(item, str):
                return item
        return None
    return None


def _discover_core_candidates(
    graph: nx.DiGraph,
    ai_labels: Optional[Dict[str, object]]
) -> Set[str]:
    """Return the set of node ids labeled as Core by AI.

    This consults both the provided ai_labels mapping and per-node attributes
    on the graph to maximize compatibility with different simulated storages.
    """
    core_nodes: Set[str] = set()

    # 1) Provided mapping takes precedence when available
    if ai_labels:
        for node_id, raw in ai_labels.items():
            label = _normalize_ai_label(raw)
            if label == "Core":
                core_nodes.add(str(node_id))

    # 2) Augment by scanning node attributes (defensive)
    for node_id, attrs in graph.nodes(data=True):
        # Try a few conventional attribute names
        attr_candidates: Tuple[object, ...] = (
            attrs.get("ai_label"),
            attrs.get("layer3_label"),
            attrs.get("ai_tags"),
            attrs.get("tags"),
        )
        for raw in attr_candidates:
            if _normalize_ai_label(raw) == "Core":
                core_nodes.add(str(node_id))
                break

    return core_nodes


def _bfs_nearest_target_path(
    graph: nx.DiGraph,
    source: str,
    targets: Set[str]
) -> Optional[List[str]]:
    """Return the path from source to the first discovered target via BFS.

    This yields the shortest path in terms of edge count and aligns with the
    "first discovered" semantics for Core nodes.
    """
    if source not in graph:
        return None
    try:
        all_paths: Dict[str, List[str]] = nx.single_source_shortest_path(graph, source)
    except Exception:
        return None

    # Iteration order of single_source_shortest_path values is by nondecreasing path length
    for node_id, path in all_paths.items():
        if node_id in targets:
            return [str(n) for n in path]
    return None


def _fallback_pagerank_path(graph: nx.DiGraph, entry_node_id: str) -> List[str]:
    """Fallback: path from entry to PageRank top-1 node.

    If unreachable, try next most central nodes until a reachable target is
    found. If none are reachable, return the entry node alone when valid.
    """
    if entry_node_id not in graph:
        return []

    pr: Dict[str, float] = nx.pagerank(graph, alpha=0.85)
    ranked: List[str] = [n for n, _ in sorted(pr.items(), key=lambda kv: kv[1], reverse=True)]
    if not ranked:
        return [entry_node_id]

    for target in ranked:
        try:
            path = nx.shortest_path(graph, source=entry_node_id, target=target)
            return [str(n) for n in path]
        except Exception:
            continue

    # As a last resort, return the entry if present
    return [entry_node_id]


def _extend_path_to_min_length(
    graph: nx.DiGraph, path: List[str], min_len: int = 5, max_len: int = 9
) -> List[str]:
    """Ensure path length is within [min_len, max_len].

    - Trim to max_len if longer.
    - If shorter than min_len, extend by walking successors greedily without
      revisiting nodes. Stops when no further unique successors are available.
    """
    if not path:
        return []

    if len(path) > max_len:
        return path[:max_len]

    if len(path) >= min_len:
        return path

    seen: Set[str] = set(path)
    extended: List[str] = list(path)
    cursor: str = extended[-1]

    while len(extended) < min_len:
        succs: List[str] = [str(n) for n in graph.successors(cursor)] if cursor in graph else []
        # Choose the first unseen successor deterministically by id order
        next_candidates = [n for n in sorted(succs) if n not in seen]
        if not next_candidates:
            break
        nxt = next_candidates[0]
        extended.append(nxt)
        seen.add(nxt)
        cursor = nxt

    return extended


def extract_golden_path(
    entry_node_id: str,
    graph: nx.DiGraph,
    ai_labels: Optional[Dict[str, object]] = None,
    *,
    min_nodes: int = 5,
    max_nodes: int = 9,
) -> List[str]:
    """Compute the Golden Path from an entry node.

    Args:
        entry_node_id: Starting node id.
        graph: Directed NetworkX graph instance.
        ai_labels: Optional mapping of node_id -> AI label info (Layer 3). The
            values may be strings (e.g., "Core"), dicts, or lists; they will be
            normalized.
        min_nodes: Minimum number of nodes to return (default 5).
        max_nodes: Maximum number of nodes to return (default 9).

    Returns:
        A list of node ids representing the path. Length is bounded within
        [min_nodes, max_nodes] when possible.
    """
    # 1) Prefer AI-labeled Core targets
    core_candidates = _discover_core_candidates(graph, ai_labels)

    path: List[str] = []
    if core_candidates:
        bfs_path = _bfs_nearest_target_path(graph, entry_node_id, core_candidates)
        if bfs_path:
            path = bfs_path

    # 2) Fallback to PageRank Top-1 reachable path
    if not path:
        path = _fallback_pagerank_path(graph, entry_node_id)

    # 3) Enforce length constraints
    path = _extend_path_to_min_length(graph, path, min_len=min_nodes, max_len=max_nodes)

    return path


