"""
Graph Schema Definitions

This module defines Pydantic models for standardizing tool response formats.
The primary goal is to ensure consistent data structure at the tool's exit point,
preventing silent failures caused by format inconsistencies.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


# ============================================================================
# DETAILED CONTENT MODELS
# ============================================================================
# These models enforce strict validation on the individual nodes and edges,
# ensuring data integrity at the deepest level.


class Span(BaseModel):
    """Code span with line numbers."""
    start: int = Field(..., description="Starting line number")
    end: int = Field(..., description="Ending line number")


class NodeEvidence(BaseModel):
    """Evidence for a node's location in the codebase."""
    file: str = Field(..., description="File path of the evidence")
    span: Span = Field(..., description="Line span with start and end")
    snippet: str = Field(..., description="Code snippet of the evidence")


class Metrics(BaseModel):
    """Code metrics for a node."""
    loc: Optional[int] = Field(None, description="Lines of code")
    complexity: Optional[int] = Field(None, description="Cyclomatic complexity")


class Node(BaseModel):
    """
    A code graph node representing a code element (function, class, etc).
    
    This schema enforces strict validation on all node data, ensuring that
    any malformed nodes will cause immediate, loud failures rather than
    silent corruption.
    """
    id: str = Field(..., description="Unique ID of the node")
    fqName: str = Field(..., description="Fully qualified name of the code element")
    kind: str = Field(..., description="Type of the node (e.g., function, class)")
    language: str = Field(..., description="Programming language")
    evidence: NodeEvidence = Field(..., description="Location evidence in source code")
    signature: Optional[str] = Field(None, description="Function/method signature")
    doc: Optional[str] = Field(None, description="Documentation string")
    metrics: Optional[Metrics] = Field(None, description="Code metrics")
    hotness_score: Optional[int] = Field(None, description="Hotness/importance score")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EdgeEvidence(BaseModel):
    """Evidence for an edge's location in the codebase."""
    file: str = Field(..., description="File path where the relationship occurs")
    line: int = Field(..., description="Line number where the relationship occurs")
    context: Optional[str] = Field(None, description="Contextual description")
    signature: Optional[str] = Field(None, description="Call signature if applicable")


class Edge(BaseModel):
    """
    A code graph edge representing a relationship between nodes.
    
    Note: We use 'from_' with an alias to handle Python's 'from' keyword.
    """
    # Using alias to allow 'from' as a field name, which is a Python keyword
    from_: str = Field(..., alias="from", description="Source node ID")
    to: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Type of the edge (e.g., calls, inherits)")
    evidence: Optional[EdgeEvidence] = Field(None, description="Location evidence")
    
    class Config:
        # This allows Pydantic to accept 'from' as input and convert to 'from_'
        populate_by_name = True
        # Use alias for serialization to output 'from' instead of 'from_'
        by_alias = True


# ============================================================================
# TOOL RESPONSE CONTAINER
# ============================================================================


class ToolResponse(BaseModel):
    """Standardized tool response format with deep content validation.
    
    This class acts as a gateway to ensure all tool outputs are consistent
    at both the container level AND the content level.
    
    Key Features:
    - Container validation: Guarantees 'nodes' and 'edges' fields exist
    - Content validation: Each node/edge is validated against strict schemas
    - Fail-fast: Any malformed data causes immediate ValidationError
    
    This transforms silent failures into loud, debuggable crashes.
    """
    
    nodes: List[Node] = Field(default_factory=list, description="List of validated nodes")
    edges: List[Edge] = Field(default_factory=list, description="List of validated edges")
    
    @classmethod
    def from_graph_data(cls, graph_data: Dict[str, Any]) -> 'ToolResponse':
        """
        This is the smart adapter. It takes raw, potentially messy data
        and safely converts it into our standard ToolResponse format.
        It handles both direct and nested 'result' formats.
        
        Args:
            graph_data: Raw graph data that may be in various formats:
                - Direct format: {'nodes': [...], 'edges': [...]}
                - Nested format: {'result': {'nodes': [...], 'edges': [...]}}
        
        Returns:
            ToolResponse: A validated, standardized response object
        
        Examples:
            >>> # Direct format
            >>> raw = {'nodes': [{'id': '1'}], 'edges': []}
            >>> response = ToolResponse.from_graph_data(raw)
            
            >>> # Nested format
            >>> raw = {'result': {'nodes': [{'id': '1'}], 'edges': []}}
            >>> response = ToolResponse.from_graph_data(raw)
            
            >>> # Missing fields (gracefully handled)
            >>> raw = {}
            >>> response = ToolResponse.from_graph_data(raw)
            >>> # response.nodes == [], response.edges == []
        """
        data_to_parse = graph_data
        
        # Handle nested 'result' format
        if 'result' in data_to_parse and isinstance(data_to_parse['result'], dict):
            data_to_parse = data_to_parse['result']
        
        # Create standardized response with safe defaults
        return cls(
            nodes=data_to_parse.get('nodes', []),
            edges=data_to_parse.get('edges', [])
        )

