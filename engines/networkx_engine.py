"""NetworkX-based implementation of the pluggable graph engine.

Loads the single source of truth produced by scripts/build_graphs.py
(codegraph.v1.json) and exposes neighborhood queries and centrality metrics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Iterable

import networkx as nx

from interfaces.graph_engine_interface import GraphEngineInterface


class NetworkXEngine(GraphEngineInterface):
    """NetworkX-backed engine that reads graph data from codegraph.v1.json."""

    def __init__(self, graph_path: str | Path | None = None) -> None:
        """Initialize the engine and load the graph into a directed NetworkX graph.

        Args:
            graph_path: Optional path to a codegraph.v1.json file. If not provided,
                defaults to a file named "codegraph.v1.json" at the repository root.
        """
        self.graph: nx.DiGraph = nx.DiGraph()

        resolved_path = self._resolve_graph_path(graph_path)
        self._load_from_json(resolved_path)

    def _resolve_graph_path(self, graph_path: str | Path | None) -> Path:
        if graph_path is not None:
            return Path(graph_path).resolve()

        # Default to repo-root codegraph.v1.json
        candidate = Path.cwd() / "codegraph.v1.json"
        if candidate.exists():
            return candidate.resolve()

        # Fallback: also try frontend public artifact if present
        alt = Path.cwd() / "code-lookup-frontend" / "public" / "codegraph.v1.json"
        if alt.exists():
            return alt.resolve()

        raise FileNotFoundError(
            "codegraph.v1.json not found. Provide graph_path or run scripts/build_graphs.py"
        )

    def _load_from_json(self, path: Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        # Add nodes with attributes; ensure stable string ids
        for node in nodes:
            node_id = str(node.get("id"))
            # Copy all attributes except id so it remains the key
            attrs = {k: v for k, v in node.items() if k != "id"}
            self.graph.add_node(node_id, **attrs)

        # Add directed edges
        for edge in edges:
            src = str(edge.get("from"))
            dst = str(edge.get("to"))
            attrs = {k: v for k, v in edge.items() if k not in {"from", "to"}}
            self.graph.add_edge(src, dst, **attrs)

    # Interface implementations -------------------------------------------------
    def get_neighborhood(self, node_id: str, depth: int = 2) -> Dict[str, object]:
        if node_id not in self.graph:
            return {"nodes": {}, "edges": []}

        # BFS outward neighborhood up to depth
        reachable = nx.single_source_shortest_path_length(self.graph, node_id, cutoff=depth)
        node_ids: Iterable[str] = reachable.keys()

        # Induce subgraph and serialize
        subg = self.graph.subgraph(node_ids).copy()

        nodes_out: Dict[str, Dict[str, object]] = {
            str(n): dict(subg.nodes[n]) for n in subg.nodes
        }
        edges_out: List[Dict[str, str]] = [
            {"from": str(u), "to": str(v)} for u, v in subg.edges
        ]

        return {"nodes": nodes_out, "edges": edges_out}

    def get_shortest_path(self, start_node_id: str, end_node_id: str) -> List[str]:
        path = nx.shortest_path(self.graph, source=start_node_id, target=end_node_id)
        return [str(n) for n in path]

    def calculate_pagerank(self) -> Dict[str, float]:
        scores = nx.pagerank(self.graph, alpha=0.85)
        return {str(n): float(s) for n, s in scores.items()}

    def calculate_betweenness_centrality(self) -> Dict[str, float]:
        scores = nx.betweenness_centrality(self.graph, normalized=True)
        return {str(n): float(s) for n, s in scores.items()}


if __name__ == "__main__":
    # Quick smoke test: load graph and print a small neighborhood
    engine = NetworkXEngine()
    print(f"Loaded graph: {engine.graph.number_of_nodes()} nodes, {engine.graph.number_of_edges()} edges")

    # Try neighborhood of an arbitrary node (first one if available)
    first_node = next(iter(engine.graph.nodes), None)
    if first_node is not None:
        hood = engine.get_neighborhood(first_node, depth=2)
        print(
            f"Neighborhood around {first_node}: {len(hood['nodes'])} nodes, {len(hood['edges'])} edges"
        )
    else:
        print("Graph is empty; no neighborhood to display.")


