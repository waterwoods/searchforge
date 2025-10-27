#!/usr/bin/env python3
"""
P0 Code Lookup Agent - Core Offline Builder Script

This script is the foundation of the P0 Code Lookup Agent system. It parses Python 
source code directories and generates the single source of truth: codegraph.v1.json.

The script extracts function nodes, builds indices, and analyzes function call 
relationships to create edges between functions.
"""

import ast
import json
import argparse
import subprocess
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict


class CodeGraphBuilder:
    """
    Core builder for the P0 Code Lookup Agent's code graph.
    
    This class orchestrates the parsing of Python source code and generation
    of the codegraph.v1.json file that serves as the system's single source of truth.
    """
    
    def __init__(self, source_dir: str, output_path: str, incremental: bool = False):
        """
        Initialize the CodeGraphBuilder.
        
        Args:
            source_dir: Path to the source code directory to analyze
            output_path: Path where codegraph.v1.json will be written
            incremental: Whether to perform incremental updates
        """
        self.source_dir = Path(source_dir).resolve()
        self.output_path = Path(output_path)
        self.incremental = incremental
        self.nodes = []
        self.edges = []  # Will be populated with function call edges
        self.node_counter = 1  # For generating F1, F2, etc. IDs
        
        # Indices for fast lookup
        self.by_fq_name = {}
        self.by_file_path = defaultdict(list)
        
        # Store function ASTs for second pass analysis
        self.function_asts = {}  # Maps node_id to (func_node, file_path, relative_path)
        
        # Incremental update tracking
        self.file_hashes = {}  # Track file modification times/hashes
        self.last_build_time = None
        
    def build_graph(self) -> Dict[str, Any]:
        """
        Main orchestration method that builds the complete code graph.
        
        Returns:
            Complete graph dictionary ready for JSON serialization
        """
        print("🏗️  Starting P0 Code Lookup Agent Graph Builder...")
        
        # Load existing graph if incremental mode
        if self.incremental:
            self._load_existing_graph()
        
        # Find all Python files
        python_files = self._find_python_files()
        print(f"📁 Found {len(python_files)} Python files to analyze")
        
        # Filter files that need rebuilding (incremental mode)
        if self.incremental:
            files_to_process = [f for f in python_files if self._should_rebuild_file(f)]
            if files_to_process:
                print(f"🔄 Incremental mode: {len(files_to_process)} files need rebuilding")
                # Remove existing nodes from changed files
                for file_path in files_to_process:
                    self._remove_nodes_from_file(file_path)
            else:
                print("✅ Incremental mode: No files need rebuilding")
        else:
            files_to_process = python_files
        
        # Parse each file and extract functions
        for file_path in files_to_process:
            self._parse_file(file_path)
            if self.incremental:
                self._update_file_hash(file_path)
        
        print(f"🔍 Extracted {len(self.nodes)} function nodes")
        
        # Second pass: Extract function call edges
        print("🔗 Extracting function call edges...")
        self._extract_function_calls()
        print(f"🔗 Extracted {len(self.edges)} function call edges")
        
        # Generate final graph structure
        graph_data = self._generate_final_graph()
        
        print("✅ Graph generation complete!")
        return graph_data
    
    def _find_python_files(self) -> List[Path]:
        """
        Recursively find all Python files in the source directory.
        
        Returns:
            List of Python file paths
        """
        python_files = []
        
        # Directories to exclude
        exclude_dirs = {
            '__pycache__', '.git', '.pytest_cache', '.mypy_cache', 
            '.tox', 'build', 'dist', 'venv', '.venv', 'node_modules',
            'tests', 'test', 'tests_', 'test_', 'spec', 'specs'
        }
        
        # Files to exclude
        exclude_files = {
            '__init__.py', '__main__.py', 'setup.py', 'conftest.py'
        }
        
        for py_file in self.source_dir.rglob("*.py"):
            # Skip if in excluded directory
            if any(part in exclude_dirs for part in py_file.parts):
                continue
                
            # Skip excluded files
            if py_file.name in exclude_files:
                continue
                
            # Skip if file is too small (likely empty or just comments)
            if py_file.stat().st_size < 50:
                continue
                
            python_files.append(py_file)
        
        return sorted(python_files)
    
    def _parse_file(self, file_path: Path) -> None:
        """
        Parse a single Python file and extract function information.
        
        Args:
            file_path: Path to the Python file to parse
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Parse the AST
            tree = ast.parse(source_code, filename=str(file_path))
            
            # Calculate relative path for module naming
            relative_path = file_path.relative_to(self.source_dir)
            
            # Determine module name
            module_parts = list(relative_path.parts[:-1])  # All parts except filename
            if not module_parts:
                module_name = "root"
            else:
                module_name = ".".join(module_parts)
            
            # Extract functions from the AST
            self._extract_functions(tree, file_path, relative_path, module_name, source_code)
            
        except Exception as e:
            print(f"⚠️  Error parsing {file_path}: {e}")
    
    def _extract_functions(self, tree: ast.AST, file_path: Path, 
                          relative_path: Path, module_name: str, source_code: str) -> None:
        """
        Extract function definitions from the AST.
        
        Args:
            tree: Parsed AST
            file_path: Path to the source file
            relative_path: Relative path from source directory
            module_name: Module name for FQN construction
            source_code: Raw source code for snippet extraction
        """
        lines = source_code.splitlines()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._create_function_node(
                    node, file_path, relative_path, module_name, 
                    source_code, lines, parent_class=None
                )
            elif isinstance(node, ast.AsyncFunctionDef):
                self._create_function_node(
                    node, file_path, relative_path, module_name, 
                    source_code, lines, parent_class=None
                )
            elif isinstance(node, ast.ClassDef):
                # Process methods within classes
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self._create_function_node(
                            child, file_path, relative_path, module_name, 
                            source_code, lines, parent_class=node.name
                        )
    
    def _create_function_node(self, func_node: ast.FunctionDef, file_path: Path,
                             relative_path: Path, module_name: str, source_code: str,
                             lines: List[str], parent_class: Optional[str] = None) -> None:
        """
        Create a function node from an AST function definition.
        
        Args:
            func_node: AST function definition node
            file_path: Path to the source file
            relative_path: Relative path from source directory
            module_name: Module name for FQN construction
            source_code: Raw source code
            lines: Source code split into lines
            parent_class: Name of parent class if this is a method
        """
        func_name = func_node.name
        
        # Generate FQN (Fully Qualified Name)
        if parent_class:
            fq_name = f"{module_name}.{parent_class}.{func_name}"
        else:
            fq_name = f"{module_name}.{func_name}"
        
        # Generate unique ID
        node_id = f"F{self.node_counter}"
        self.node_counter += 1
        
        # Extract signature
        signature = self._extract_signature(func_node)
        
        # Extract docstring
        doc = self._extract_docstring(func_node)
        
        # Calculate span (line numbers)
        start_line = func_node.lineno
        end_line = func_node.end_lineno or start_line
        
        # Extract code snippet
        snippet_lines = lines[start_line-1:end_line]
        snippet = "\n".join(snippet_lines)
        
        # Calculate metrics
        loc = end_line - start_line + 1
        complexity = self._calculate_complexity(func_node)
        
        # Create the function node
        function_node = {
            "id": node_id,
            "fqName": fq_name,
            "kind": "function",
            "language": "py",
            "signature": signature,
            "doc": doc,
            "evidence": {
                "file": str(relative_path),
                "span": {"start": start_line, "end": end_line},
                "snippet": snippet
            },
            "metrics": {
                "loc": loc,
                "complexity": complexity
            }
        }
        
        # Add to nodes list
        self.nodes.append(function_node)
        
        # Update indices
        self.by_fq_name[fq_name] = node_id
        self.by_file_path[str(relative_path)].append(node_id)
        
        # Store AST for second pass analysis
        self.function_asts[node_id] = (func_node, file_path, relative_path)
    
    def _extract_signature(self, func_node: ast.FunctionDef) -> str:
        """
        Extract function signature from AST node.
        
        Args:
            func_node: AST function definition node
            
        Returns:
            Function signature string
        """
        args = []
        
        # Handle positional arguments
        for arg in func_node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        # Handle vararg (*args)
        if func_node.args.vararg:
            args.append(f"*{func_node.args.vararg.arg}")
        
        # Handle keyword-only arguments
        if func_node.args.kwonlyargs:
            for arg in func_node.args.kwonlyargs:
                arg_str = arg.arg
                if arg.annotation:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                args.append(arg_str)
        
        # Handle kwarg (**kwargs)
        if func_node.args.kwarg:
            args.append(f"**{func_node.args.kwarg.arg}")
        
        # Build signature
        signature = f"({', '.join(args)})"
        
        # Add return type annotation
        if func_node.returns:
            signature += f" -> {ast.unparse(func_node.returns)}"
        
        return signature
    
    def _extract_docstring(self, func_node: ast.FunctionDef) -> str:
        """
        Extract docstring from function node.
        
        Args:
            func_node: AST function definition node
            
        Returns:
            Docstring text or empty string
        """
        if (func_node.body and 
            isinstance(func_node.body[0], ast.Expr) and 
            isinstance(func_node.body[0].value, ast.Constant) and
            isinstance(func_node.body[0].value.value, str)):
            return func_node.body[0].value.value.strip()
        return ""
    
    def _calculate_complexity(self, func_node: ast.FunctionDef) -> int:
        """
        Calculate cyclomatic complexity of a function.
        
        Args:
            func_node: AST function definition node
            
        Returns:
            Complexity score
        """
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _extract_function_calls(self) -> None:
        """
        Second pass: Extract function call edges by analyzing each function's AST.
        """
        for node_id, (func_node, file_path, relative_path) in self.function_asts.items():
            self._analyze_function_calls(func_node, node_id, file_path, relative_path)
    
    def _analyze_function_calls(self, func_node: ast.FunctionDef, caller_id: str, 
                              file_path: Path, relative_path: Path) -> None:
        """
        Analyze a function's AST to find calls to other functions.
        
        Args:
            func_node: AST function definition node
            caller_id: ID of the calling function
            file_path: Path to the source file
            relative_path: Relative path from source directory
        """
        # Walk through all nodes in the function body
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                self._process_call_node(node, caller_id, file_path, relative_path)
    
    def _process_call_node(self, call_node: ast.Call, caller_id: str, 
                          file_path: Path, relative_path: Path) -> None:
        """
        Process a single call node to create an edge if the target function exists.
        
        Args:
            call_node: AST call node
            caller_id: ID of the calling function
            file_path: Path to the source file
            relative_path: Relative path from source directory
        """
        # Extract the function name being called
        func_name = self._resolve_call_name(call_node)
        if not func_name:
            return
        
        # Try to find the target function in our index
        target_id = self._find_target_function(func_name)
        if not target_id:
            return
        
        # Create the edge with enhanced evidence
        edge = {
            "from": caller_id,
            "to": target_id,
            "type": "calls",
            "evidence": {
                "file": str(relative_path),
                "line": call_node.lineno,
                "context": self._extract_call_context(call_node),
                "signature": self._extract_call_signature(call_node)
            }
        }
        
        # Add to edges list (avoid duplicates)
        if edge not in self.edges:
            self.edges.append(edge)
    
    def _resolve_call_name(self, call_node: ast.Call) -> Optional[str]:
        """
        Resolve the name of the function being called.
        
        Args:
            call_node: AST call node
            
        Returns:
            Function name or None if cannot be resolved
        """
        func = call_node.func
        
        # Direct function call: func()
        if isinstance(func, ast.Name):
            return func.id
        
        # Method call: obj.method()
        elif isinstance(func, ast.Attribute):
            # For now, we'll try to resolve method calls by checking if
            # the method name exists as a standalone function
            return func.attr
        
        # Other complex cases (subscripts, etc.) - skip for now
        return None
    
    def _find_target_function(self, func_name: str) -> Optional[str]:
        """
        Find the target function ID by name using various strategies.
        
        Args:
            func_name: Name of the function to find
            
        Returns:
            Node ID of the target function or None if not found
        """
        # Strategy 1: Direct lookup by FQN (exact match)
        for fq_name, node_id in self.by_fq_name.items():
            if fq_name.endswith(f".{func_name}") or fq_name == func_name:
                return node_id
        
        # Strategy 2: Look for function with matching name (best effort)
        # This handles cases where we can't determine the full module path
        for fq_name, node_id in self.by_fq_name.items():
            if fq_name.split('.')[-1] == func_name:
                return node_id
        
        return None
    
    def _extract_call_context(self, call_node: ast.Call) -> str:
        """
        Extract context around the function call for better evidence.
        
        Args:
            call_node: AST call node
            
        Returns:
            Context string around the call
        """
        try:
            # Get the source line where the call occurs
            if hasattr(call_node, 'lineno') and call_node.lineno:
                # This would need access to source lines, simplified for now
                return f"Call to {self._resolve_call_name(call_node)}"
        except:
            pass
        return ""
    
    def _extract_call_signature(self, call_node: ast.Call) -> str:
        """
        Extract the signature of the function call.
        
        Args:
            call_node: AST call node
            
        Returns:
            Call signature string
        """
        try:
            func_name = self._resolve_call_name(call_node)
            if not func_name:
                return ""
            
            # Count arguments
            arg_count = len(call_node.args) + len(call_node.keywords)
            return f"{func_name}({arg_count} args)"
        except:
            return ""
    
    def _should_rebuild_file(self, file_path: Path) -> bool:
        """
        Check if a file needs to be rebuilt based on modification time.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file needs rebuilding
        """
        if not self.incremental:
            return True
            
        try:
            current_mtime = file_path.stat().st_mtime
            file_key = str(file_path.relative_to(self.source_dir))
            
            if file_key not in self.file_hashes:
                return True
                
            return current_mtime > self.file_hashes[file_key]
        except:
            return True
    
    def _update_file_hash(self, file_path: Path) -> None:
        """Update the hash for a file after processing."""
        try:
            current_mtime = file_path.stat().st_mtime
            file_key = str(file_path.relative_to(self.source_dir))
            self.file_hashes[file_key] = current_mtime
        except:
            pass
    
    def _load_existing_graph(self) -> Optional[Dict[str, Any]]:
        """Load existing graph for incremental updates."""
        if not self.incremental or not self.output_path.exists():
            return None
            
        try:
            with open(self.output_path, 'r', encoding='utf-8') as f:
                existing_graph = json.load(f)
            
            # Extract existing data
            self.nodes = existing_graph.get('nodes', [])
            self.edges = existing_graph.get('edges', [])
            
            # Rebuild indices
            self.by_fq_name = existing_graph.get('indices', {}).get('byFqName', {})
            self.by_file_path = defaultdict(list, existing_graph.get('indices', {}).get('byFilePath', {}))
            
            # Find highest node counter
            max_id = 0
            for node in self.nodes:
                if node.get('id', '').startswith('F'):
                    try:
                        node_num = int(node['id'][1:])
                        max_id = max(max_id, node_num)
                    except:
                        pass
            self.node_counter = max_id + 1
            
            print(f"📂 Loaded existing graph: {len(self.nodes)} nodes, {len(self.edges)} edges")
            return existing_graph
            
        except Exception as e:
            print(f"⚠️  Error loading existing graph: {e}")
            return None
    
    def _remove_nodes_from_file(self, file_path: Path) -> None:
        """Remove all nodes and edges associated with a specific file."""
        relative_path = str(file_path.relative_to(self.source_dir))
        
        # Find nodes to remove
        nodes_to_remove = []
        for node in self.nodes:
            if node.get('evidence', {}).get('file') == relative_path:
                nodes_to_remove.append(node['id'])
        
        # Remove nodes
        self.nodes = [node for node in self.nodes if node['id'] not in nodes_to_remove]
        
        # Remove edges involving these nodes
        self.edges = [edge for edge in self.edges 
                     if edge['from'] not in nodes_to_remove and edge['to'] not in nodes_to_remove]
        
        # Update indices
        self.by_fq_name = {fq_name: node_id for fq_name, node_id in self.by_fq_name.items()
                          if node_id not in nodes_to_remove}
        
        if relative_path in self.by_file_path:
            del self.by_file_path[relative_path]
        
        print(f"🗑️  Removed {len(nodes_to_remove)} nodes from {relative_path}")
    
    def _generate_final_graph(self) -> Dict[str, Any]:
        """
        Generate the final graph structure according to the schema template.
        
        Returns:
            Complete graph dictionary
        """
        # Get repository name and commit hash
        repo_name = self.source_dir.name
        try:
            commit_hash = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], 
                cwd=self.source_dir,
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
        except:
            commit_hash = "unknown"
        
        # Create meta information
        meta = {
            "repo": repo_name,
            "commit": commit_hash
        }
        
        # Assemble final graph according to schema
        graph_data = {
            "meta": meta,
            "nodes": self.nodes,
            "edges": self.edges,  # Now populated with function call edges
            "indices": {
                "byFqName": self.by_fq_name,
                "byFilePath": dict(self.by_file_path)
            }
        }
        
        return graph_data
    
    def save_graph(self) -> None:
        """
        Build the graph and save it to the specified output path.
        """
        graph_data = self.build_graph()
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Graph saved to {self.output_path}")
        print(f"📊 Final stats: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")


def main():
    """
    Main entry point with command-line interface.
    """
    parser = argparse.ArgumentParser(
        description="P0 Code Lookup Agent - Core Offline Builder Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/build_graphs.py ./src ./codegraph.v1.json
  python scripts/build_graphs.py /path/to/project /path/to/output.json
        """
    )
    
    parser.add_argument(
        'source_dir',
        help='Path to the source code directory to analyze'
    )
    
    parser.add_argument(
        'output_path',
        help='Path where codegraph.v1.json will be written'
    )
    
    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Enable incremental updates (only rebuild changed files)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    source_path = Path(args.source_dir)
    if not source_path.exists():
        print(f"❌ Error: Source directory '{args.source_dir}' does not exist")
        return 1
    
    if not source_path.is_dir():
        print(f"❌ Error: '{args.source_dir}' is not a directory")
        return 1
    
    print(f"🚀 Building P0 Code Lookup Agent graph...")
    print(f"📂 Source directory: {args.source_dir}")
    print(f"📄 Output file: {args.output_path}")
    
    # Create and run the builder
    builder = CodeGraphBuilder(args.source_dir, args.output_path, args.incremental)
    builder.save_graph()
    
    print("🎉 P0 Code Lookup Agent graph building complete!")
    return 0


if __name__ == "__main__":
    exit(main())
