"""
CodeGraph Tool for Agent's Tool Registry

This module provides a Python API to query the codegraph.v1.json data structure
in memory with fast, indexed lookups for nodes and their relationships.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict

from schemas.graph_schemas import ToolResponse


class CodeGraph:
    """
    A class to load and query the codegraph.v1.json data structure.
    
    Provides fast O(1) lookups for nodes by fully qualified name and efficient
    traversal of the graph to find neighbors within a specified number of hops.
    """
    
    def __init__(self, codegraph_path: str):
        """
        Initialize the CodeGraph by loading the JSON file.
        
        Args:
            codegraph_path: Path to the codegraph.v1.json file
        """
        self.codegraph_path = Path(codegraph_path)
        
        # Load the graph data
        self._load_graph_data()
        
        # Build edge indices for efficient neighbor traversal
        self._build_edge_indices()
    
    def _load_graph_data(self) -> None:
        """Load the JSON file and populate instance variables."""
        try:
            with open(self.codegraph_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            # Extract the main data structures
            self.nodes = graph_data.get('nodes', [])
            self.edges = graph_data.get('edges', [])
            self.indices = graph_data.get('indices', {})
            
            # Create a node lookup by ID for efficient access
            self._nodes_by_id = {node['id']: node for node in self.nodes}
            
            print(f"✅ Loaded codegraph: {len(self.nodes)} nodes, {len(self.edges)} edges")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"CodeGraph file not found: {self.codegraph_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in codegraph file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading codegraph: {e}")
    
    def _build_edge_indices(self) -> None:
        """
        Build edge indices for efficient neighbor traversal.
        
        Creates edgesFrom and edgesTo indices that map node IDs to lists of
        connected nodes for fast graph traversal.
        """
        self.edges_from = defaultdict(list)
        self.edges_to = defaultdict(list)
        
        for edge in self.edges:
            from_id = edge['from']
            to_id = edge['to']
            
            # Add to both directions for undirected traversal
            self.edges_from[from_id].append(to_id)
            self.edges_to[to_id].append(from_id)
        
        print(f"✅ Built edge indices: {len(self.edges_from)} source nodes, {len(self.edges_to)} target nodes")
    
    def get_node_by_fqname(self, fqname: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by its fully qualified name using O(1) lookup.
        
        Args:
            fqname: Fully qualified name of the function/node
            
        Returns:
            Node dictionary if found, None otherwise
        """
        # Use the byFqName index for fast lookup
        node_id = self.indices.get('byFqName', {}).get(fqname)
        
        if node_id is None:
            return None
        
        # Return the full node data
        return self._nodes_by_id.get(node_id)
    
    def get_neighbors(self, node_id: str, max_hops: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all neighbors within max_hops from the given node.
        
        Args:
            node_id: ID of the starting node
            max_hops: Maximum number of hops to traverse (default: 1)
            
        Returns:
            Dictionary containing 'nodes' and 'edges' lists representing the subgraph
        """
        if node_id not in self._nodes_by_id:
            return {'nodes': [], 'edges': []}
        
        # Track visited nodes and edges
        visited_nodes: Set[str] = set()
        visited_edges: Set[tuple] = set()
        current_level: Set[str] = {node_id}
        
        # Include the starting node
        visited_nodes.add(node_id)
        
        # BFS traversal for max_hops levels
        for hop in range(max_hops):
            next_level: Set[str] = set()
            
            for current_node in current_level:
                # Get all connected nodes (both incoming and outgoing)
                connected_nodes = set()
                
                # Outgoing edges
                for target in self.edges_from.get(current_node, []):
                    connected_nodes.add(target)
                    edge_key = (current_node, target)
                    if edge_key not in visited_edges:
                        visited_edges.add(edge_key)
                
                # Incoming edges
                for source in self.edges_to.get(current_node, []):
                    connected_nodes.add(source)
                    edge_key = (source, current_node)
                    if edge_key not in visited_edges:
                        visited_edges.add(edge_key)
                
                # Add unvisited nodes to next level
                for connected_node in connected_nodes:
                    if connected_node not in visited_nodes:
                        visited_nodes.add(connected_node)
                        next_level.add(connected_node)
            
            current_level = next_level
            
            # If no new nodes found, stop early
            if not current_level:
                break
        
        # Build the result
        result_nodes = [self._nodes_by_id[node_id] for node_id in visited_nodes 
                       if node_id in self._nodes_by_id]
        
        result_edges = []
        for edge in self.edges:
            edge_key = (edge['from'], edge['to'])
            if edge_key in visited_edges:
                result_edges.append(edge)
        
        return {
            'nodes': result_nodes,
            'edges': result_edges
        }
    
    def get_nodes_by_file(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all nodes from a specific file along with their internal connections.
        
        Args:
            file_path: Relative file path
            
        Returns:
            Dictionary containing 'nodes' and 'edges' lists representing the file's internal subgraph
        """
        # Step 1: Get all node IDs from the specified file
        node_ids = self.indices.get('byFilePath', {}).get(file_path, [])
        
        # Step 2: Create a set for O(1) lookup efficiency
        file_node_ids = set(node_ids)
        
        # Step 3: Get complete node data for all nodes in the file
        nodes_in_file = [self._nodes_by_id[node_id] for node_id in node_ids 
                        if node_id in self._nodes_by_id]
        
        # Step 4: Filter edges to find internal connections within the file
        internal_edges = []
        for edge in self.edges:
            source_id = edge.get('from')
            target_id = edge.get('to')
            
            # Check if both source and target nodes are in the same file
            if source_id in file_node_ids and target_id in file_node_ids:
                internal_edges.append(edge)
        
        # Step 5: Return the complete subgraph in the expected format
        # 🔍 DEBUG: Add logging to track file query results
        print(f"🔍 CodeGraph.get_nodes_by_file - File: {file_path}")
        print(f"🔍 CodeGraph.get_nodes_by_file - Found {len(nodes_in_file)} nodes, {len(internal_edges)} edges")
        if nodes_in_file:
            print(f"🔍 CodeGraph.get_nodes_by_file - First node: {nodes_in_file[0].get('id', 'no-id')}")
        
        raw_result = {
            'nodes': nodes_in_file,
            'edges': internal_edges
        }
        # Use the adapter to validate and standardize the output
        # Use by_alias=True to ensure 'from' is used instead of 'from_' in edge serialization
        return ToolResponse.from_graph_data(raw_result).dict(by_alias=True)
    
    def get_all_nodes_and_edges(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all nodes and edges from the graph.
        
        Returns:
            Dictionary containing 'nodes' and 'edges' lists with all graph data
        """
        raw_result = {
            'nodes': self.nodes,
            'edges': self.edges
        }
        # Use the adapter for this function as well
        # Use by_alias=True to ensure 'from' is used instead of 'from_' in edge serialization
        return ToolResponse.from_graph_data(raw_result).dict(by_alias=True)
    
    def get_neighborhood_by_node_id(self, node_id: str, depth: int = 2) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the neighborhood subgraph centered around a specific node.
        
        This method performs BFS traversal to find all nodes within the specified
        depth from the given node, returning a small, relevant subgraph.
        
        Args:
            node_id: ID of the central node
            depth: Maximum number of hops to traverse (default: 2)
            
        Returns:
            Dictionary containing 'nodes' and 'edges' lists representing the neighborhood subgraph,
            validated and standardized using the ToolResponse schema
        """
        # Use the existing get_neighbors method which implements BFS traversal
        raw_result = self.get_neighbors(node_id, max_hops=depth)
        
        # 🔍 DEBUG: Log neighborhood query results
        print(f"🔍 CodeGraph.get_neighborhood_by_node_id - Node: {node_id}, Depth: {depth}")
        print(f"🔍 CodeGraph.get_neighborhood_by_node_id - Found {len(raw_result.get('nodes', []))} nodes, {len(raw_result.get('edges', []))} edges")
        
        # Use the adapter to validate and standardize the output
        # Use by_alias=True to ensure 'from' is used instead of 'from_' in edge serialization
        return ToolResponse.from_graph_data(raw_result).dict(by_alias=True)
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get basic statistics about the loaded graph.
        
        Returns:
            Dictionary with graph statistics
        """
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'nodes_with_outgoing_edges': len(self.edges_from),
            'nodes_with_incoming_edges': len(self.edges_to),
            'unique_fqnames': len(self.indices.get('byFqName', {})),
            'unique_files': len(self.indices.get('byFilePath', {}))
        }
