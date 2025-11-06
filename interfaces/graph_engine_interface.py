"""Graph engine interface definitions.

Defines an abstract interface for pluggable graph engines. Concrete engines
must implement all methods to provide neighborhood queries and graph analytics.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class GraphEngineInterface(ABC):
    """Abstract base class for graph engines.

    Implementations should be backed by a graph library or database and expose
    a consistent set of operations for querying neighborhoods and computing
    common centrality metrics.
    """

    @abstractmethod
    def get_neighborhood(self, node_id: str, depth: int = 2) -> Dict[str, object]:
        """Return a neighborhood subgraph around a node up to a given depth.

        Args:
            node_id: The starting node identifier.
            depth: BFS depth (number of hops) to include in the neighborhood.

        Returns:
            A dictionary with keys:
              - "nodes": Dict[node_id, Dict[str, object]] of node attributes
              - "edges": List[Dict[str, str]] of directed edges with keys "from" and "to"
        """

    @abstractmethod
    def get_shortest_path(self, start_node_id: str, end_node_id: str) -> List[str]:
        """Compute the shortest path between two nodes.

        Args:
            start_node_id: The source node identifier.
            end_node_id: The target node identifier.

        Returns:
            The sequence of node identifiers forming the shortest path.
        """

    @abstractmethod
    def calculate_pagerank(self) -> Dict[str, float]:
        """Compute PageRank scores for all nodes.

        Returns:
            Mapping of node identifier to PageRank score.
        """

    @abstractmethod
    def calculate_betweenness_centrality(self) -> Dict[str, float]:
        """Compute betweenness centrality for all nodes.

        Returns:
            Mapping of node identifier to betweenness centrality score.
        """


