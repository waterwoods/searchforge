#!/usr/bin/env python3
"""
One-time script to index a local codebase into Qdrant vector database.

This script follows the "Read -> Split -> Embed -> Store" pattern:
1. Read: Load code files from the specified directory
2. Split: Break documents into manageable chunks
3. Embed: Generate vector embeddings for each chunk
4. Store: Upload embeddings to Qdrant collection

Usage:
    python scripts/index_codebase.py [--codebase-path /path/to/code]
"""

import os
import sys
import argparse
import uuid
import fnmatch
import ast
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


# ============================================================================
# CONFIGURATION - Modify these values or use command-line arguments
# ============================================================================

# Path to the codebase you want to index
# Default: parent directory (assumes script is in scripts/ folder)
# You can also pass this via --codebase-path argument
# DEFAULT_CODEBASE_PATH = "../"
DEFAULT_CODEBASE_PATH = "/Users/nanxinli/Documents/dev/searchforge"

# Qdrant connection settings
# If using a local Qdrant instance (e.g., via Docker):
#   docker run -p 6333:6333 qdrant/qdrant
# If using Qdrant Cloud, set QDRANT_URL and QDRANT_API_KEY in .env file
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)  # None if no auth required

# Qdrant collection name
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "searchforge_codebase")

# Embedding model configuration
# Popular choices:
# - "all-MiniLM-L6-v2" (384 dimensions, fast, good for most use cases)
# - "all-mpnet-base-v2" (768 dimensions, slower but more accurate)
# - "BAAI/bge-small-en" (384 dimensions, optimized for retrieval)
# - "BAAI/bge-base-en" (768 dimensions, better quality)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# Text splitting configuration
CHUNK_SIZE = 1000  # characters per chunk
CHUNK_OVERLAP = 100  # overlap between chunks for context continuity

# Batch size for embedding and uploading
BATCH_SIZE = 32

# File extensions to include (modify based on your codebase)
# Adjust this list to match your project's file types
INCLUDE_EXTENSIONS = [
    ".py",      # Python
    ".js",      # JavaScript
    ".jsx",     # React JSX
    ".ts",      # TypeScript
    ".tsx",     # React TypeScript
    ".md",      # Markdown
    ".txt",     # Text files
    ".json",    # JSON config files
    ".yaml",    # YAML config files
    ".yml",     # YAML config files
]

# Directory names to exclude from indexing (exact names or patterns)
# These are common directories that should be excluded to avoid noise
EXCLUDE_DIRS = [
    "node_modules",
    ".git",
    "dist",
    "build",
    "__pycache__",
    ".next",
    ".venv",
    "venv",
    "env",
    ".pytest_cache",
    "coverage",
    ".idea",
    ".vscode",
    "target",
]


# ============================================================================
# AST-BASED SYMBOL EXTRACTION
# ============================================================================

class PythonSymbolExtractor(ast.NodeVisitor):
    """
    AST visitor class to extract function and class definitions from Python code,
    along with their relationships (function calls and imports).
    
    This class walks through the Python AST and collects information about
    top-level and nested functions and classes, including their names, types,
    line number ranges, and relationships (edges) between symbols.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.symbols: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        # Stack to track the current scope (function/class/module)
        # Each entry is a tuple: (scope_kind, scope_name)
        self.scope_stack: List[Tuple[str, str]] = [('module', file_path)]

    def _get_current_scope_id(self) -> str:
        """
        Generate a stable ID for the current scope.
        Format: path::ClassName.method_name or path::function_name or path
        """
        if len(self.scope_stack) == 1:
            # Module-level scope
            return self.file_path
        
        # Build scope path from stack
        scope_parts = [name for kind, name in self.scope_stack[1:]]  # Skip module
        return f"{self.file_path}::{'.'.join(scope_parts)}"

    def _get_node_id(self, name: str, kind: str) -> str:
        """Generate a stable ID for a node (symbol)."""
        parent_scope = self._get_current_scope_id()
        if parent_scope == self.file_path:
            # Top-level symbol
            return f"{self.file_path}::{name}"
        else:
            # Nested symbol
            return f"{parent_scope}.{name}"

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit a function definition node."""
        end_lineno = getattr(node, 'end_lineno', node.lineno)
        node_id = self._get_node_id(node.name, 'function')
        
        self.symbols.append({
            'id': node_id,
            'name': node.name,
            'kind': 'function',
            'path': self.file_path,
            'start_line': node.lineno,
            'end_line': end_lineno
        })
        
        # Push function onto scope stack
        self.scope_stack.append(('function', node.name))
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit an async function definition node."""
        end_lineno = getattr(node, 'end_lineno', node.lineno)
        node_id = self._get_node_id(node.name, 'function')
        
        self.symbols.append({
            'id': node_id,
            'name': node.name,
            'kind': 'function',
            'path': self.file_path,
            'start_line': node.lineno,
            'end_line': end_lineno
        })
        
        # Push function onto scope stack
        self.scope_stack.append(('function', node.name))
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit a class definition node."""
        end_lineno = getattr(node, 'end_lineno', node.lineno)
        node_id = self._get_node_id(node.name, 'class')
        
        self.symbols.append({
            'id': node_id,
            'name': node.name,
            'kind': 'class',
            'path': self.file_path,
            'start_line': node.lineno,
            'end_line': end_lineno
        })
        
        # Push class onto scope stack
        self.scope_stack.append(('class', node.name))
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Call(self, node: ast.Call):
        """Visit a function call node to extract 'calls' relationships."""
        caller_id = self._get_current_scope_id()
        callee_name = None
        
        # Try to extract the name of the function being called
        if isinstance(node.func, ast.Name):
            # Simple function call: func()
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Method call or module.func call: obj.method() or module.func()
            # For now, just get the attribute name
            callee_name = self._get_full_attr_name(node.func)
        
        if callee_name and caller_id:
            self.edges.append({
                'src': caller_id,
                'dst': callee_name,
                'etype': 'calls',
                'loc': node.lineno
            })
        
        self.generic_visit(node)

    def _get_full_attr_name(self, node: ast.Attribute) -> str:
        """
        Recursively build the full attribute name for method/attribute calls.
        E.g., obj.method() -> 'obj.method', module.submodule.func() -> 'module.submodule.func'
        """
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            parts.append(current.id)
        
        return '.'.join(reversed(parts))

    def visit_Import(self, node: ast.Import):
        """Visit an import statement to extract 'imports' relationships."""
        importer_id = self._get_current_scope_id()
        
        for alias in node.names:
            imported_name = alias.name
            self.edges.append({
                'src': importer_id,
                'dst': imported_name,
                'etype': 'imports',
                'loc': node.lineno
            })
        
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit a 'from X import Y' statement to extract 'imports' relationships."""
        importer_id = self._get_current_scope_id()
        
        # Get the module being imported from
        module = node.module or ''
        
        for alias in node.names:
            imported_name = alias.name
            # Create a qualified name: module.name
            if module:
                full_name = f"{module}.{imported_name}"
            else:
                full_name = imported_name
            
            self.edges.append({
                'src': importer_id,
                'dst': full_name,
                'etype': 'imports',
                'loc': node.lineno
            })
        
        self.generic_visit(node)

    @classmethod
    def extract_symbols(cls, content: str, file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parse Python code and extract symbol information and relationships.
        
        Args:
            content: Python source code as a string
            file_path: Path to the Python file (for reference)
            
        Returns:
            Tuple of (symbols, edges) where:
            - symbols: List of symbol dictionaries containing id, name, kind, path, start_line, end_line
            - edges: List of edge dictionaries containing src, dst, etype, loc
        """
        try:
            tree = ast.parse(content)
            visitor = cls(file_path)
            visitor.visit(tree)
            return visitor.symbols, visitor.edges
        except SyntaxError:
            # Ignore files with syntax errors for now
            return [], []
        except Exception as e:
            print(f"Warning: AST parsing failed for {file_path}: {e}")
            return [], []


# ============================================================================
# MAIN INDEXING LOGIC
# ============================================================================

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Index a local codebase into Qdrant vector database"
    )
    parser.add_argument(
        "--codebase-path",
        type=str,
        default=DEFAULT_CODEBASE_PATH,
        help=f"Path to the codebase directory (default: {DEFAULT_CODEBASE_PATH})"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the collection if it already exists (deletes existing data)"
    )
    return parser.parse_args()


def initialize_clients(embedding_model_name: str):
    """
    Initialize Qdrant client and embedding model.
    
    Returns:
        tuple: (qdrant_client, embedding_model, embedding_size)
    """
    print(f"🔧 Initializing Qdrant client...")
    print(f"   URL: {QDRANT_URL}")
    
    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )
    
    print(f"🤖 Loading embedding model: {embedding_model_name}")
    print(f"   This may take a few moments on first run...")
    
    # Initialize embedding model
    embedding_model = SentenceTransformer(embedding_model_name)
    
    # Get embedding size by encoding a test string
    test_embedding = embedding_model.encode(["test"])
    embedding_size = len(test_embedding[0])
    
    print(f"   ✓ Model loaded (embedding size: {embedding_size})")
    
    return qdrant_client, embedding_model, embedding_size


def setup_collection(client: QdrantClient, collection_name: str, vector_size: int, recreate: bool = False):
    """
    Create or verify Qdrant collection.
    
    Args:
        client: Qdrant client instance
        collection_name: Name of the collection
        vector_size: Dimension of embedding vectors
        recreate: If True, delete and recreate the collection
    """
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    if collection_name in collection_names:
        if recreate:
            print(f"🗑️  Deleting existing collection: {collection_name}")
            client.delete_collection(collection_name)
        else:
            print(f"✓ Collection '{collection_name}' already exists")
            print(f"   Use --recreate flag to delete and recreate it")
            return
    
    print(f"📦 Creating collection: {collection_name}")
    print(f"   Vector size: {vector_size}")
    print(f"   Distance metric: Cosine")
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )
    
    print(f"   ✓ Collection created successfully")


def should_exclude_path(path: str, exclude_dirs: List[str]) -> bool:
    """
    Check if a path should be excluded based on exclude patterns.
    
    Args:
        path: File or directory path to check
        exclude_dirs: List of directory names to exclude
        
    Returns:
        True if path should be excluded, False otherwise
    """
    path_parts = Path(path).parts
    for exclude_dir in exclude_dirs:
        if exclude_dir in path_parts:
            return True
    return False


def find_code_files(codebase_path: str, extensions: List[str], exclude_dirs: List[str]) -> List[str]:
    """
    Find all code files in the codebase using os.walk.
    
    Args:
        codebase_path: Path to the codebase directory
        extensions: List of file extensions to include (e.g., ['.py', '.js'])
        exclude_dirs: List of directory names to exclude (e.g., ['node_modules', '.git'])
        
    Returns:
        List of file paths
    """
    print(f"\n📂 Finding code files in: {codebase_path}")
    print(f"   Including extensions: {', '.join(extensions)}")
    print(f"   Excluding directories: {', '.join(exclude_dirs)}")
    
    codebase_path = os.path.abspath(os.path.expanduser(codebase_path))
    
    # DEBUG: Confirm the absolute path being used
    print(f"   DEBUG: Absolute codebase_path after expansion: {codebase_path}")
    print(f"   DEBUG: Path exists: {os.path.exists(codebase_path)}")
    print(f"   DEBUG: Is directory: {os.path.isdir(codebase_path)}")
    
    if not os.path.exists(codebase_path):
        raise ValueError(f"Codebase path does not exist: {codebase_path}")
    
    file_paths = []
    
    # DEBUG: Show we're starting the walk
    print(f"   DEBUG: Starting os.walk from: {codebase_path}")
    
    # Walk through directory tree (followlinks=False to avoid following symlinks outside the directory)
    for root, dirs, files in os.walk(codebase_path, followlinks=False):
        # Remove excluded directories from dirs list to prevent os.walk from entering them
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Check if current path should be excluded
        if should_exclude_path(root, exclude_dirs):
            continue
        
        # Find matching files
        for file in files:
            # Check if file has one of the included extensions
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
    
    print(f"   ✓ Found {len(file_paths):,} files")
    
    # DEBUG: Show first 10 files found to verify they're from the correct directory
    if file_paths:
        print(f"   DEBUG: First 10 files found:")
        for i, fp in enumerate(file_paths[:10]):
            print(f"      {i+1}. {fp}")
        if len(file_paths) > 10:
            print(f"      ... and {len(file_paths) - 10} more files")
    
    return file_paths


def split_text(file_path: str, content: str, chunk_size: int = CHUNK_SIZE, 
               chunk_overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """
    Split file content into chunks with overlap.
    
    This function uses a simple line-based splitting approach:
    - Split content into lines
    - Group lines together until chunk_size is reached
    - Include chunk_overlap characters from the previous chunk
    
    Args:
        file_path: Path to the source file
        content: File content to split
        chunk_size: Target size for each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        List of dictionaries with 'text' and 'metadata' keys
    """
    if not content.strip():
        return []
    
    chunks = []
    lines = content.split('\n')
    
    current_chunk = []
    current_size = 0
    chunk_index = 0
    
    for line in lines:
        line_with_newline = line + '\n'
        line_size = len(line_with_newline)
        
        # If adding this line would exceed chunk_size, save current chunk
        if current_size + line_size > chunk_size and current_chunk:
            chunk_text = ''.join(current_chunk).rstrip('\n')
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'source': file_path,
                    'chunk_index': chunk_index
                }
            })
            chunk_index += 1
            
            # Calculate overlap: take last N characters from current chunk
            if chunk_overlap > 0 and chunk_text:
                overlap_text = chunk_text[-chunk_overlap:]
                # Find where to split at a line boundary for cleaner overlap
                newline_pos = overlap_text.find('\n')
                if newline_pos != -1:
                    overlap_text = overlap_text[newline_pos + 1:]
                
                current_chunk = [overlap_text + '\n'] if overlap_text else []
                current_size = len(overlap_text) + 1 if overlap_text else 0
            else:
                current_chunk = []
                current_size = 0
        
        # Add current line to chunk
        current_chunk.append(line_with_newline)
        current_size += line_size
    
    # Don't forget the last chunk
    if current_chunk:
        chunk_text = ''.join(current_chunk).rstrip('\n')
        chunks.append({
            'text': chunk_text,
            'metadata': {
                'source': file_path,
                'chunk_index': chunk_index
            }
        })
    
    return chunks


def associate_chunks_with_symbols(chunks: List[Dict[str, Any]], symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Associate text chunks with their corresponding symbols (functions/classes) based on line numbers.
    
    Args:
        chunks: List of chunk dictionaries from split_text
        symbols: List of symbol dictionaries from PythonSymbolExtractor
        
    Returns:
        Updated chunks with symbol metadata
    """
    # Calculate line numbers for each chunk
    for chunk in chunks:
        text = chunk['text']
        lines = text.split('\n')
        
        # Estimate the start and end line of this chunk
        # This is approximate since we don't track absolute line numbers in split_text
        # We'll use a heuristic: match chunk text to symbols
        
        # Find which symbol(s) this chunk might belong to
        chunk_symbols = []
        for symbol in symbols:
            # Check if the symbol name appears in the chunk
            if symbol['name'] in text:
                chunk_symbols.append(symbol)
        
        # If we found exactly one symbol, use it
        if len(chunk_symbols) == 1:
            symbol = chunk_symbols[0]
            chunk['metadata']['kind'] = symbol['kind']
            chunk['metadata']['name'] = symbol['name']
            chunk['metadata']['start_line'] = symbol['start_line']
            chunk['metadata']['end_line'] = symbol['end_line']
        elif len(chunk_symbols) > 1:
            # If multiple symbols, prefer the first one (usually the containing scope)
            symbol = chunk_symbols[0]
            chunk['metadata']['kind'] = symbol['kind']
            chunk['metadata']['name'] = symbol['name']
            chunk['metadata']['start_line'] = symbol['start_line']
            chunk['metadata']['end_line'] = symbol['end_line']
        else:
            # No specific symbol found, mark as file chunk
            chunk['metadata']['kind'] = 'file_chunk'
    
    return chunks


def load_and_split_files(file_paths: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load files and split them into chunks.
    For Python files, extract symbol information, relationships, and associate with chunks.
    
    Args:
        file_paths: List of file paths to process
        
    Returns:
        Tuple of (all_chunks, file_metadata_chunks) where:
        - all_chunks: List of regular chunk dictionaries with metadata
        - file_metadata_chunks: List of file-level metadata chunks containing edges
    """
    print(f"\n📖 Loading and splitting {len(file_paths):,} files...")
    print(f"   Chunk size: {CHUNK_SIZE} characters")
    print(f"   Chunk overlap: {CHUNK_OVERLAP} characters")
    
    all_chunks = []
    file_metadata_chunks = []
    files_processed = 0
    files_failed = 0
    python_files_with_symbols = 0
    python_files_with_edges = 0
    
    for file_path in tqdm(file_paths, desc="Processing files", unit="file"):
        try:
            # Try to read file with UTF-8 encoding, ignoring errors
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check if this is a Python file
            is_python = file_path.endswith('.py')
            
            if is_python:
                # Extract symbols and edges (relationships) from Python code
                symbols, edges = PythonSymbolExtractor.extract_symbols(content, file_path)
                
                # Split the content into chunks
                chunks = split_text(file_path, content)
                
                # Associate chunks with symbols
                if symbols:
                    chunks = associate_chunks_with_symbols(chunks, symbols)
                    python_files_with_symbols += 1
                else:
                    # No symbols found, mark all chunks as file_chunk
                    for chunk in chunks:
                        chunk['metadata']['kind'] = 'file_chunk'
                
                # Store edges as a special file-level metadata chunk
                if edges:
                    file_metadata_chunks.append({
                        'text': f"File: {file_path}",  # Small text for embedding
                        'metadata': {
                            'source': file_path,
                            'kind': 'file',
                            'name': file_path,
                            'edges_json': json.dumps(edges)  # Store edges as JSON
                        }
                    })
                    python_files_with_edges += 1
            else:
                # Non-Python file: use regular splitting
                chunks = split_text(file_path, content)
                # Mark all chunks as file_chunk
                for chunk in chunks:
                    chunk['metadata']['kind'] = 'file_chunk'
            
            all_chunks.extend(chunks)
            files_processed += 1
            
        except Exception as e:
            files_failed += 1
            # Silently skip files that can't be read
            continue
    
    print(f"   ✓ Processed {files_processed:,} files successfully")
    if python_files_with_symbols > 0:
        print(f"   ✓ Extracted symbols from {python_files_with_symbols:,} Python files")
    if python_files_with_edges > 0:
        print(f"   ✓ Extracted edges from {python_files_with_edges:,} Python files")
    if files_failed > 0:
        print(f"   ⚠️  Skipped {files_failed:,} files due to errors")
    print(f"   ✓ Created {len(all_chunks):,} regular chunks")
    print(f"   ✓ Created {len(file_metadata_chunks):,} file metadata chunks")
    if files_processed > 0:
        print(f"   Average chunks per file: {len(all_chunks) / files_processed:.1f}")
    
    return all_chunks, file_metadata_chunks


def embed_and_store(
    client: QdrantClient,
    collection_name: str,
    chunks: List[Dict[str, Any]],
    file_metadata_chunks: List[Dict[str, Any]],
    embedding_model: SentenceTransformer,
    batch_size: int = BATCH_SIZE
):
    """
    Generate embeddings for chunks and upload to Qdrant in batches.
    
    Args:
        client: Qdrant client instance
        collection_name: Name of the collection to upload to
        chunks: List of regular chunk dictionaries with 'text' and 'metadata' keys
        file_metadata_chunks: List of file metadata chunks containing edges
        embedding_model: SentenceTransformer model for generating embeddings
        batch_size: Number of chunks to process in each batch
    """
    # Combine all chunks (regular + file metadata) for processing
    all_chunks_to_process = chunks + file_metadata_chunks
    
    print(f"\n🚀 Embedding and storing {len(all_chunks_to_process):,} chunks...")
    print(f"   Regular chunks: {len(chunks):,}")
    print(f"   File metadata chunks (with edges): {len(file_metadata_chunks):,}")
    print(f"   Batch size: {batch_size}")
    print(f"   Collection: {collection_name}")
    
    total_batches = (len(all_chunks_to_process) + batch_size - 1) // batch_size
    
    with tqdm(total=len(all_chunks_to_process), desc="Processing chunks", unit="chunk") as pbar:
        for i in range(0, len(all_chunks_to_process), batch_size):
            batch = all_chunks_to_process[i:i + batch_size]
            
            try:
                # Extract text and metadata from chunk dictionaries
                texts = [chunk['text'] for chunk in batch]
                metadatas = [chunk['metadata'] for chunk in batch]
                
                # Generate embeddings for the batch
                embeddings = embedding_model.encode(
                    texts,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                
                # Prepare points for Qdrant
                points = []
                for j, (text, metadata, embedding) in enumerate(zip(texts, metadatas, embeddings)):
                    point_id = str(uuid.uuid4())
                    
                    # Prepare payload with text content and metadata
                    payload = {
                        "text": text,
                        "file_path": metadata.get("source", "unknown"),
                        "chunk_index": metadata.get("chunk_index", i + j),
                        "kind": metadata.get("kind", "file_chunk"),
                        "name": metadata.get("name", None),
                        "start_line": metadata.get("start_line", None),
                        "end_line": metadata.get("end_line", None),
                    }
                    
                    # Remove None values to keep Qdrant payloads clean
                    payload = {k: v for k, v in payload.items() if v is not None}
                    
                    # Add any additional metadata, including edges_json for file metadata chunks
                    for key, value in metadata.items():
                        if key not in ["source", "chunk_index", "kind", "name", "start_line", "end_line"] and isinstance(value, (str, int, float, bool)):
                            payload[key] = value
                    
                    points.append(
                        PointStruct(
                            id=point_id,
                            vector=embedding.tolist(),
                            payload=payload,
                        )
                    )
                
                # Upload batch to Qdrant
                client.upsert(
                    collection_name=collection_name,
                    points=points,
                )
                
                pbar.update(len(batch))
                
            except Exception as e:
                print(f"\n⚠️  Error processing batch {i//batch_size + 1}/{total_batches}: {e}")
                print(f"   Skipping batch and continuing...")
                pbar.update(len(batch))
                continue
    
    # Verify upload
    collection_info = client.get_collection(collection_name)
    print(f"\n✓ Upload complete!")
    print(f"   Total points in collection: {collection_info.points_count:,}")


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()
    
    # Parse command-line arguments
    args = parse_args()
    
    # DEBUG: Show the effective codebase path that will be used
    effective_codebase_path = os.path.abspath(os.path.expanduser(args.codebase_path))
    print("\n" + "=" * 70)
    print("🔍 CODEBASE INDEXING SCRIPT - DEBUG MODE")
    print("=" * 70)
    print(f"DEBUG: Raw codebase_path argument: {args.codebase_path}")
    print(f"DEBUG: Effective CODEBASE_PATH being used: {effective_codebase_path}")
    print(f"DEBUG: Current working directory: {os.getcwd()}")
    print(f"Collection name: {QDRANT_COLLECTION_NAME}")
    print(f"Embedding model: {EMBEDDING_MODEL_NAME}")
    print("=" * 70)
    
    try:
        # Step 1: Initialize clients
        qdrant_client, embedding_model, embedding_size = initialize_clients(EMBEDDING_MODEL_NAME)
        
        # Step 2: Setup collection
        setup_collection(qdrant_client, QDRANT_COLLECTION_NAME, embedding_size, args.recreate)
        
        # Step 3: Find code files
        file_paths = find_code_files(args.codebase_path, INCLUDE_EXTENSIONS, EXCLUDE_DIRS)
        
        if not file_paths:
            print("\n⚠️  No files found to index. Check your path and file extensions.")
            sys.exit(1)
        
        # Step 4: Load and split files into chunks
        chunks, file_metadata_chunks = load_and_split_files(file_paths)
        
        if not chunks and not file_metadata_chunks:
            print("\n⚠️  No chunks created. Files may be empty or unreadable.")
            sys.exit(1)
        
        # Step 5: Embed and store
        embed_and_store(qdrant_client, QDRANT_COLLECTION_NAME, chunks, file_metadata_chunks, embedding_model)
        
        print("\n" + "=" * 70)
        print("✅ INDEXING COMPLETE!")
        print("=" * 70)
        print(f"Collection '{QDRANT_COLLECTION_NAME}' is ready for queries.")
        print(f"You can now use this collection for code lookup and search.")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Indexing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during indexing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

