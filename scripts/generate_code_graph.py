#!/usr/bin/env python3
"""
Code Graph Generator Script
===========================

This script scans the Python codebase, uses AST to extract a graph of nodes (files, functions) 
and edges (calls, imports), and stores this graph in a dedicated Qdrant collection named `code_graph`.

The graph structure:
- Nodes: Files and functions with metadata
- Edges: Function calls and imports between nodes
"""

import os
import ast
import json
import sys
from typing import List, Dict, Any, Set, Tuple
from pathlib import Path

# Add project root to path to import our existing clients
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.fiqa_api.clients import get_qdrant_client
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Configuration
COLLECTION_NAME = "code_graph"
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))  # Go up from scripts/ to project root

# Directories to skip during scanning
SKIP_DIRS = {'.venv', '__pycache__', 'node_modules', '.git', '.pytest_cache', 'venv', 'env'}

# File extensions to scan
PYTHON_EXTENSIONS = {'.py'}


class CodeGraphExtractor(ast.NodeVisitor):
    """
    AST visitor that extracts nodes (files, functions) and edges (calls, imports) 
    from Python code to build a code graph.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.nodes = []
        self.edges = []
        self.current_function = None
        self.imports = {}  # Store imports for edge creation
        
    def visit_FunctionDef(self, node):
        """Extract function definitions as nodes."""
        function_id = f"{self.file_path}::{node.name}"
        
        # Get function source code (first 200 chars for snippet)
        try:
            source_lines = ast.get_source_segment(self.file_path, node) or ""
            code_snippet = source_lines[:200] + "..." if len(source_lines) > 200 else source_lines
        except:
            code_snippet = f"def {node.name}(...)"
        
        function_node = {
            "id": function_id,
            "type": "function",
            "file_path": self.file_path,
            "name": node.name,
            "code_snippet": code_snippet,
            "line_number": node.lineno
        }
        
        self.nodes.append(function_node)
        
        # Track current function for call edges
        old_function = self.current_function
        self.current_function = function_id
        
        # Visit child nodes
        self.generic_visit(node)
        
        # Restore previous function context
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node):
        """Extract async function definitions as nodes."""
        # Treat async functions the same as regular functions
        self.visit_FunctionDef(node)
    
    def visit_Call(self, node):
        """Extract function calls as edges."""
        if self.current_function is None:
            return  # Skip calls outside of functions
        
        # Extract the function name being called
        if isinstance(node.func, ast.Name):
            # Direct function call: function_name()
            target_function = node.func.id
            target_id = f"{self.file_path}::{target_function}"
            
            edge = {
                "source": self.current_function,
                "target": target_id,
                "type": "calls",
                "line_number": node.lineno
            }
            self.edges.append(edge)
            
        elif isinstance(node.func, ast.Attribute):
            # Method call: object.method()
            if isinstance(node.func.value, ast.Name):
                # local_object.method()
                target_function = f"{node.func.value.id}.{node.func.attr}"
                target_id = f"{self.file_path}::{target_function}"
                
                edge = {
                    "source": self.current_function,
                    "target": target_id,
                    "type": "calls",
                    "line_number": node.lineno
                }
                self.edges.append(edge)
        
        # Visit child nodes
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Extract import statements as edges."""
        for alias in node.names:
            module_name = alias.name
            import_name = alias.asname or alias.name
            
            # Create edge from current context to imported module
            if self.current_function:
                edge = {
                    "source": self.current_function,
                    "target": f"module::{module_name}",
                    "type": "imports",
                    "line_number": node.lineno
                }
            else:
                # Module-level import
                edge = {
                    "source": f"file::{self.file_path}",
                    "target": f"module::{module_name}",
                    "type": "imports",
                    "line_number": node.lineno
                }
            
            self.edges.append(edge)
            self.imports[import_name] = module_name
    
    def visit_ImportFrom(self, node):
        """Extract from-import statements as edges."""
        module_name = node.module or ""
        
        for alias in node.names:
            item_name = alias.name
            import_name = alias.asname or alias.name
            
            # Create edge from current context to imported item
            if self.current_function:
                edge = {
                    "source": self.current_function,
                    "target": f"module::{module_name}.{item_name}",
                    "type": "imports",
                    "line_number": node.lineno
                }
            else:
                # Module-level import
                edge = {
                    "source": f"file::{self.file_path}",
                    "target": f"module::{module_name}.{item_name}",
                    "type": "imports",
                    "line_number": node.lineno
                }
            
            self.edges.append(edge)
            self.imports[import_name] = f"{module_name}.{item_name}"


def setup_qdrant_collection(client):
    """
    Set up the Qdrant collection for code graph storage.
    Deletes existing collection if it exists, then creates a new one.
    """
    print(f"🔧 Setting up Qdrant collection '{COLLECTION_NAME}'...")
    
    # Check if collection exists and delete it
    try:
        collections = client.get_collections()
        existing_collections = [c.name for c in collections.collections]
        
        if COLLECTION_NAME in existing_collections:
            print(f"🗑️  Deleting existing collection '{COLLECTION_NAME}'...")
            client.delete_collection(collection_name=COLLECTION_NAME)
            print(f"✅ Collection '{COLLECTION_NAME}' deleted")
    except Exception as e:
        print(f"⚠️  Error checking/deleting collection: {e}")
    
    # Create new collection
    try:
        print(f"📋 Creating new collection '{COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,  # Standard embedding size
                distance=Distance.COSINE
            )
        )
        print(f"✅ Collection '{COLLECTION_NAME}' created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        return False


def scan_python_files(root_dir: str) -> List[str]:
    """
    Scan the project directory for Python files, skipping specified directories.
    
    Args:
        root_dir: Root directory to scan
        
    Returns:
        List of Python file paths
    """
    python_files = []
    
    print(f"🔍 Scanning directory: {root_dir}")
    
    for root, dirs, files in os.walk(root_dir):
        # Remove directories we want to skip
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            if any(file.endswith(ext) for ext in PYTHON_EXTENSIONS):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    
    print(f"📁 Found {len(python_files)} Python files")
    return python_files


def extract_code_graph(file_path: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Extract code graph from a single Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Tuple of (nodes, edges) extracted from the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content, filename=file_path)
        
        # Create extractor and visit the AST
        extractor = CodeGraphExtractor(file_path)
        extractor.visit(tree)
        
        # Add file as a node
        file_node = {
            "id": f"file::{file_path}",
            "type": "file",
            "file_path": file_path,
            "name": os.path.basename(file_path),
            "code_snippet": content[:500] + "..." if len(content) > 500 else content,
            "line_count": len(content.splitlines())
        }
        extractor.nodes.append(file_node)
        
        return extractor.nodes, extractor.edges
        
    except Exception as e:
        print(f"⚠️  Error processing {file_path}: {e}")
        return [], []


def save_to_qdrant(client, all_nodes: List[Dict], all_edges: List[Dict]):
    """
    Save the extracted code graph to Qdrant.
    Each node becomes a point with its connected edges stored in the payload.
    
    Args:
        client: Qdrant client
        all_nodes: List of all nodes
        all_edges: List of all edges
    """
    print(f"💾 Saving {len(all_nodes)} nodes and {len(all_edges)} edges to Qdrant...")
    
    # Group edges by source node
    edges_by_node = {}
    for edge in all_edges:
        source = edge["source"]
        if source not in edges_by_node:
            edges_by_node[source] = []
        edges_by_node[source].append(edge)
    
    # Create points for each node
    points = []
    for i, node in enumerate(all_nodes):
        node_id = node["id"]
        connected_edges = edges_by_node.get(node_id, [])
        
        # Create point payload
        payload = {
            "id": node_id,  # Store canonical ID in payload
            "type": node["type"],
            "file_path": node["file_path"],
            "name": node.get("name", ""),
            "code_snippet": node.get("code_snippet", ""),
            "line_number": node.get("line_number", 0),
            "line_count": node.get("line_count", 0),
            "edges_json": json.dumps(connected_edges),
            "edge_count": len(connected_edges)
        }
        
        # Create point using numeric ID as Qdrant point ID, but store canonical ID in payload
        point = PointStruct(
            id=i,  # Use numeric ID for Qdrant compatibility
            vector=[0.0] * 384,  # Dummy vector for now
            payload=payload
        )
        points.append(point)
    
    # Batch insert points
    try:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"✅ Successfully saved {len(points)} points to Qdrant!")
        return True
    except Exception as e:
        print(f"❌ Error saving to Qdrant: {e}")
        return False


def main():
    """Main function that orchestrates the code graph generation process."""
    print("🚀 Starting Code Graph Generation...")
    print(f"📂 Project root: {PROJECT_ROOT}")
    
    # Initialize Qdrant client
    try:
        print("🔗 Connecting to Qdrant...")
        client = get_qdrant_client()
        print("✅ Qdrant client connected successfully!")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return False
    
    # Setup collection
    if not setup_qdrant_collection(client):
        return False
    
    # Scan Python files
    python_files = scan_python_files(PROJECT_ROOT)
    if not python_files:
        print("⚠️  No Python files found to process")
        return False
    
    # Process each file
    all_nodes = []
    all_edges = []
    
    print(f"🔍 Processing {len(python_files)} Python files...")
    
    for i, file_path in enumerate(python_files, 1):
        print(f"📄 [{i}/{len(python_files)}] Scanning {file_path}...")
        
        nodes, edges = extract_code_graph(file_path)
        all_nodes.extend(nodes)
        all_edges.extend(edges)
        
        print(f"   Found {len(nodes)} nodes, {len(edges)} edges")
    
    print(f"📊 Total extracted: {len(all_nodes)} nodes, {len(all_edges)} edges")
    
    # Save to Qdrant
    if save_to_qdrant(client, all_nodes, all_edges):
        print("🎉 Code graph generation completed successfully!")
        return True
    else:
        print("❌ Failed to save code graph to Qdrant")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
