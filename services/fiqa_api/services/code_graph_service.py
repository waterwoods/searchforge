"""
code_graph_service.py - Code Graph Service Logic
===============================================
Pure business logic for fetching and processing code graph data from Qdrant.
No client creation - uses clients.py singletons.

Features:
- Fetch all points from code_graph collection
- Reconstruct full graph with nodes and edges
- Process edges_json from payloads
"""

import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# ========================================
# Constants
# ========================================

CODE_GRAPH_COLLECTION = "code_graph"


# ========================================
# Core Code Graph Logic
# ========================================

async def get_full_graph() -> Dict[str, Any]:
    """
    Fetch the complete code graph from Qdrant and reconstruct it.
    
    Returns:
        Dict containing 'nodes' and 'edges' lists with the full graph data
        
    Raises:
        RuntimeError: If Qdrant client is not available
        Exception: On critical errors
    """
    from services.fiqa_api.clients import (
        get_qdrant_client,
        ensure_qdrant_connection
    )
    
    # Ensure Qdrant connection is healthy before proceeding
    if not ensure_qdrant_connection():
        logger.warning("[CODE_GRAPH] Qdrant connection unhealthy, graph fetch may fail")
    
    # Get Qdrant client
    qdrant_client = get_qdrant_client()
    
    try:
        logger.info(f"[CODE_GRAPH] Fetching all points from collection: {CODE_GRAPH_COLLECTION}")
        
        # Use scroll to fetch all points from the code_graph collection
        points, _ = qdrant_client.scroll(
            collection_name=CODE_GRAPH_COLLECTION,
            limit=10000,  # Large limit to get all points
            with_payload=True,
            with_vectors=False  # We don't need vectors for graph data
        )
        
        if not points:
            logger.warning(f"[CODE_GRAPH] No points found in collection: {CODE_GRAPH_COLLECTION}")
            return {
                "nodes": [],
                "edges": []
            }
        
        logger.info(f"[CODE_GRAPH] Retrieved {len(points)} points from collection")
        
        # Process points to reconstruct the graph
        nodes = []
        edges = []
        
        for point in points:
            payload = point.payload or {}
            
            
            # Add the main node data
            node_data = {
                "id": payload.get("id", str(point.id)),  # Use canonical ID from payload
                "file_path": payload.get("file_path", ""),
                "name": payload.get("name", ""),
                "kind": payload.get("type", ""),  # Use 'type' from payload
                "start_line": payload.get("line_number", 0),  # Use 'line_number' from payload
                "end_line": payload.get("line_count", 0),  # Use 'line_count' from payload
                "text": payload.get("code_snippet", ""),  # Use 'code_snippet' from payload
                "language": payload.get("language", "python")
            }
            nodes.append(node_data)
            
            # Parse and add edges from edges_json
            edges_json_str = payload.get("edges_json")
            if edges_json_str:
                try:
                    edges_data = json.loads(edges_json_str)
                    if isinstance(edges_data, list):
                        for edge in edges_data:
                            if isinstance(edge, dict) and ("src" in edge or "source" in edge) and ("dst" in edge or "target" in edge):
                                edge_data = {
                                    "src": edge.get("src", edge.get("source", "")),
                                    "dst": edge.get("dst", edge.get("target", "")),
                                    "type": edge.get("type", edge.get("etype", "unknown")),
                                    "file_path": payload.get("file_path", "")
                                }
                                edges.append(edge_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"[CODE_GRAPH] Failed to parse edges_json for point {point.id}: {e}")
                    continue
        
        logger.info(f"[CODE_GRAPH] Reconstructed graph with {len(nodes)} nodes and {len(edges)} edges")
        
        return {
            "nodes": nodes,
            "edges": edges
        }
        
    except Exception as e:
        logger.error(f"[CODE_GRAPH] Failed to fetch code graph: {e}")
        raise RuntimeError(f"Failed to fetch code graph: {str(e)}")


def get_graph_stats() -> Dict[str, Any]:
    """
    Get statistics about the code graph collection.
    
    Returns:
        Dict with collection statistics
    """
    from services.fiqa_api.clients import (
        get_qdrant_client,
        ensure_qdrant_connection
    )
    
    # Ensure Qdrant connection is healthy
    if not ensure_qdrant_connection():
        logger.warning("[CODE_GRAPH] Qdrant connection unhealthy, stats may fail")
        return {
            "ok": False,
            "error": "Qdrant connection unhealthy"
        }
    
    try:
        qdrant_client = get_qdrant_client()
        
        # Get collection info
        collection_info = qdrant_client.get_collection(CODE_GRAPH_COLLECTION)
        
        return {
            "ok": True,
            "collection_name": CODE_GRAPH_COLLECTION,
            "points_count": collection_info.points_count,
            "vector_size": collection_info.config.params.vectors.size if collection_info.config.params.vectors else 0,
            "status": "ready"
        }
        
    except Exception as e:
        logger.error(f"[CODE_GRAPH] Failed to get graph stats: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


async def get_summary_graph() -> Dict[str, Any]:
    """
    Fetch a summary view of the code graph with only entry points and their direct neighbors.
    
    This function creates a smaller, digestible graph by:
    1. Identifying entry points (High-Level nodes like routes, APIs)
    2. Finding their direct neighbors (1-hop connections)
    3. Building a focused graph with only these critical nodes
    
    Returns:
        Dict containing 'nodes' and 'edges' lists with the summary graph data
        
    Raises:
        RuntimeError: If Qdrant client is not available
        Exception: On critical errors
    """
    from services.fiqa_api.clients import (
        get_qdrant_client,
        ensure_qdrant_connection
    )
    
    # Ensure Qdrant connection is healthy before proceeding
    if not ensure_qdrant_connection():
        logger.warning("[CODE_GRAPH] Qdrant connection unhealthy, summary graph fetch may fail")
    
    # Get Qdrant client
    qdrant_client = get_qdrant_client()
    
    try:
        logger.info(f"[CODE_GRAPH] Fetching summary graph from collection: {CODE_GRAPH_COLLECTION}")
        
        # Use scroll to fetch all points from the code_graph collection
        points, _ = qdrant_client.scroll(
            collection_name=CODE_GRAPH_COLLECTION,
            limit=10000,  # Large limit to get all points
            with_payload=True,
            with_vectors=False  # We don't need vectors for graph data
        )
        
        if not points:
            logger.warning(f"[CODE_GRAPH] No points found in collection: {CODE_GRAPH_COLLECTION}")
            return {
                "nodes": [],
                "edges": []
            }
        
        logger.info(f"[CODE_GRAPH] Retrieved {len(points)} points from collection")
        
        # First, get the full graph data, as we need it all to find neighbors
        all_nodes = []
        nodes_by_id = {}
        
        # Process all points to create node lookup
        for point in points:
            payload = point.payload or {}
            
            # Create node data
            node_data = {
                "id": payload.get("id", str(point.id)),  # Use canonical ID from payload
                "file_path": payload.get("file_path", ""),
                "name": payload.get("name", ""),
                "kind": payload.get("type", ""),
                "start_line": payload.get("line_number", 0),
                "end_line": payload.get("line_count", 0),
                "text": payload.get("code_snippet", ""),
                "language": payload.get("language", "python"),
                "edges_json": payload.get("edges_json", "")  # Store edges_json for processing
            }
            all_nodes.append(node_data)
            nodes_by_id[node_data["id"]] = node_data  # Use canonical ID as key
        
        # Identify entry points
        entry_points = [
            node for node in all_nodes
            if ("routes" in node.get("file_path", "").lower() or 
                "api" in node.get("file_path", "").lower() or
                "route" in node.get("kind", "").lower() or 
                "endpoint" in node.get("kind", "").lower() or
                "controller" in node.get("kind", "").lower() or 
                "handler" in node.get("kind", "").lower())
        ]
        
        logger.info(f"[CODE_GRAPH] Found {len(entry_points)} entry points")
        
        # Build summary graph with entry points and their neighbors
        summary_nodes = {}  # Use dict to automatically handle duplicates
        summary_edges = []
        
        # Loop through only the entry points to find their connections
        for entry_point in entry_points:
            entry_point_id = entry_point['id']
            summary_nodes[entry_point_id] = entry_point
            logger.debug(f"[CODE_GRAPH] Processing entry point: {entry_point['name']} ({entry_point['file_path']})")
            
            # Parse the edges connected to this entry point
            edges_json_str = entry_point.get("edges_json", "")
            if edges_json_str:
                try:
                    edge_list = json.loads(edges_json_str)
                    if isinstance(edge_list, list):
                        for edge in edge_list:
                            if isinstance(edge, dict):
                                # Add the edge to our summary list
                                edge_data = {
                                    "src": edge.get("src", edge.get("source", "")),
                                    "dst": edge.get("dst", edge.get("target", "")),
                                    "type": edge.get("type", edge.get("etype", "unknown")),
                                    "file_path": entry_point.get("file_path", "")
                                }
                                summary_edges.append(edge_data)
                                
                                # Find the neighbor node
                                target_id = edge.get("target") or edge.get("dst")
                                if target_id and target_id in nodes_by_id:
                                    # Add the neighbor node to our summary list
                                    summary_nodes[target_id] = nodes_by_id[target_id]
                                    logger.debug(f"[CODE_GRAPH] Found neighbor: {nodes_by_id[target_id]['name']} for entry point {entry_point['name']}")
                except json.JSONDecodeError as e:
                    logger.warning(f"[CODE_GRAPH] Failed to parse edges_json for entry point {entry_point_id}: {e}")
                    continue
        
        # Convert the dictionary of nodes back to a list
        final_nodes = list(summary_nodes.values())
        
        logger.info(f"[CODE_GRAPH] Summary graph: {len(final_nodes)} nodes ({len(entry_points)} entry points, {len(final_nodes) - len(entry_points)} neighbors), {len(summary_edges)} edges")
        
        return {
            "nodes": final_nodes,
            "edges": summary_edges
        }
        
    except Exception as e:
        logger.error(f"[CODE_GRAPH] Failed to fetch summary graph: {e}")
        raise RuntimeError(f"Failed to fetch summary graph: {str(e)}")


async def get_local_graph(search_term: str) -> Dict[str, Any]:
    """
    Fetch a localized graph centered around a specific node found by flexible search.
    
    This function creates a focused, small graph by:
    1. Finding the center node based on flexible search (ID or name matching)
    2. Finding all 1-hop neighbors of the center node
    3. Building a small graph with only the center node and its direct neighbors
    4. Including only the edges that connect these nodes
    
    Args:
        search_term: The search term to find the center node (matches against ID or name)
        
    Returns:
        Dict containing 'nodes' and 'edges' lists with the local graph data
        
    Raises:
        RuntimeError: If Qdrant client is not available
        Exception: On critical errors
    """
    from services.fiqa_api.clients import (
        get_qdrant_client,
        ensure_qdrant_connection
    )
    
    # Ensure Qdrant connection is healthy before proceeding
    if not ensure_qdrant_connection():
        logger.warning("[CODE_GRAPH] Qdrant connection unhealthy, local graph fetch may fail")
    
    # Get Qdrant client
    qdrant_client = get_qdrant_client()
    
    try:
        logger.info(f"[CODE_GRAPH] Fetching local graph for search term: {search_term}")
        
        # Get the full graph data first
        full_graph = await get_full_graph()
        all_nodes = full_graph.get("nodes", [])
        all_edges = full_graph.get("edges", [])
        
        if not all_nodes:
            logger.warning(f"[CODE_GRAPH] No nodes found in graph")
            return {
                "nodes": [],
                "edges": []
            }
        
        logger.info(f"[CODE_GRAPH] Retrieved graph with {len(all_nodes)} nodes and {len(all_edges)} edges")
        
        # Find the center node using flexible search
        center_node = None
        nodes_by_id = {node['id']: node for node in all_nodes}
        
        # --- THIS IS THE FIX ---
        # Find the first node that contains the search term in its ID or name
        for node in all_nodes:
            # Flexible search condition
            if search_term in node.get('id', '') or search_term in node.get('name', ''):
                center_node = node
                break  # We found our target, stop searching
        
        # If no node was found after searching, return empty
        if not center_node:
            logger.warning(f"[CODE_GRAPH] No node found matching search term: {search_term}")
            return {"nodes": [], "edges": []}
        
        logger.info(f"[CODE_GRAPH] Found center node: {center_node['name']} ({center_node['file_path']})")
        
        # --- THIS IS THE NEW CORE LOGIC ---
        nodes_to_find_connections_for = set()
        
        # Check if the found node is a file
        if center_node.get('kind') == 'file':
            # It's a file, so its "family" includes itself and all its functions
            file_path = center_node.get('file_path')
            nodes_to_find_connections_for.add(center_node['id'])
            
            # Find all functions that belong to this file
            functions_found = 0
            for node in all_nodes:
                if node.get('file_path') == file_path and node.get('kind') == 'function':
                    nodes_to_find_connections_for.add(node['id'])
                    functions_found += 1
                    logger.debug(f"[CODE_GRAPH] Found function in file: {node['name']} (ID: {node['id']})")
                    
            logger.info(f"[CODE_GRAPH] Found file node, including {len(nodes_to_find_connections_for)} total nodes (1 file + {functions_found} functions)")
            
            # If no functions found, let's check what nodes exist for this file
            if functions_found == 0:
                logger.info(f"[CODE_GRAPH] No functions found for file: {file_path}")
                # Let's see what other nodes exist for this file
                other_nodes_in_file = []
                for node in all_nodes:
                    if node.get('file_path') == file_path and node['id'] != center_node['id']:
                        other_nodes_in_file.append(f"{node['name']} (kind: {node.get('kind')})")
                if other_nodes_in_file:
                    logger.info(f"[CODE_GRAPH] Other nodes in file: {', '.join(other_nodes_in_file)}")
                else:
                    logger.info(f"[CODE_GRAPH] No other nodes found in file: {file_path}")
        else:
            # It's just a single function
            nodes_to_find_connections_for.add(center_node['id'])
            logger.info(f"[CODE_GRAPH] Found function node, including 1 node")
        
        # --- The rest of the logic now uses this "family" set ---
        summary_nodes = {}
        summary_edges = []
        
        # Find all edges connected to ANY node in our target family
        edges_checked = 0
        edges_found = 0
        
        for edge in all_edges:
            source_id = edge.get("src") or edge.get("source")
            target_id = edge.get("dst") or edge.get("target")
            edges_checked += 1
            
            is_related = (source_id in nodes_to_find_connections_for) or \
                         (target_id in nodes_to_find_connections_for)
            
            if is_related:
                summary_edges.append(edge)
                edges_found += 1
                logger.debug(f"[CODE_GRAPH] Found related edge: {source_id} -> {target_id}")
                # Add both source and target nodes to the graph to ensure the edge is complete
                if source_id in nodes_by_id:
                    summary_nodes[source_id] = nodes_by_id[source_id]
                if target_id in nodes_by_id:
                    summary_nodes[target_id] = nodes_by_id[target_id]
                    
        logger.info(f"[CODE_GRAPH] Edge search: checked {edges_checked} edges, found {edges_found} related edges")
        
        final_nodes = list(summary_nodes.values())
        
        logger.info(f"[CODE_GRAPH] Local graph: {len(final_nodes)} nodes, {len(summary_edges)} edges")
        
        return {
            "nodes": final_nodes,
            "edges": summary_edges
        }
        
    except Exception as e:
        logger.error(f"[CODE_GRAPH] Failed to fetch local graph: {e}")
        raise RuntimeError(f"Failed to fetch local graph: {str(e)}")
