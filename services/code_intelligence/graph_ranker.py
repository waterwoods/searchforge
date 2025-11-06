"""
Layer 2 Graph Ranking Module

This module implements the second layer of the AI funnel: graph-based ranking
over a set of candidate nodes using PageRank and Betweenness Centrality. The
final composite score is computed as:

    Final_Score = (PageRank * 60) + (Betweenness_Centrality * 40)

The primary entrypoint is `layer2_graph_ranking`, which accepts a list of
candidate node IDs and a NetworkX directed graph, and returns the top 80
ranked candidates along with their component scores.
"""

from typing import List, Dict, Any

import networkx as nx


def layer2_graph_ranking(
    candidate_node_ids: List[str],
    graph: nx.DiGraph,
) -> List[Dict[str, Any]]:
    """
    Rank candidate nodes using a composite of PageRank and Betweenness Centrality.

    Args:
        candidate_node_ids: Top-200 candidate node IDs from Layer 1.
        graph: A NetworkX directed graph instance (nx.DiGraph).

    Returns:
        List of top-80 candidates sorted by the composite score, each item is:
        {
          "id": <node_id>,
          "final_score": <float>,
          "pagerank": <float>,
          "betweenness": <float>
        }
    """
    if graph is None:
        return []

    # Filter out candidates that are not present in the graph
    candidates_in_graph = [nid for nid in candidate_node_ids if graph.has_node(nid)]
    if not candidates_in_graph:
        return []

    # Compute global metrics over the graph
    # Note: For large graphs, betweenness can be expensive. If performance
    # becomes a concern, consider approximations (e.g., k-samples) or reusing
    # cached/precomputed metrics.
    pagerank_scores: Dict[str, float] = nx.pagerank(graph)
    betweenness_scores: Dict[str, float] = nx.betweenness_centrality(graph, normalized=True)

    ranked: List[Dict[str, Any]] = []
    for node_id in candidates_in_graph:
        pr = float(pagerank_scores.get(node_id, 0.0))
        bc = float(betweenness_scores.get(node_id, 0.0))
        final_score = (pr * 60.0) + (bc * 40.0)
        ranked.append(
            {
                "id": node_id,
                "final_score": float(final_score),
                "pagerank": pr,
                "betweenness": bc,
            }
        )

    ranked.sort(key=lambda x: x["final_score"], reverse=True)

    # Return Top-80
    return ranked[:80]











