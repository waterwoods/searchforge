"""
[CORE] Input/Output Contracts and JSON Schema Validation

Pure data contracts with no I/O dependencies.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import jsonschema


@dataclass
class RewriteInput:
    """Input contract for query rewriting."""
    query: str
    locale: Optional[str] = None
    time_range: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RewriteOutput:
    """Output contract for rewritten query with structured metadata."""
    topic: str
    entities: List[str]
    time_range: Optional[str]
    query_rewrite: str
    filters: Dict[str, Optional[str]]  # date_from, date_to

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# [CORE: jsonschema] - Strict schema for validation
REWRITE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
        "entities": {
            "type": "array",
            "items": {"type": "string"}
        },
        "time_range": {"type": ["string", "null"]},
        "query_rewrite": {"type": "string"},
        "filters": {
            "type": "object",
            "properties": {
                "date_from": {"type": ["string", "null"]},
                "date_to": {"type": ["string", "null"]}
            },
            "required": ["date_from", "date_to"],
            "additionalProperties": False
        }
    },
    "required": ["topic", "entities", "time_range", "query_rewrite", "filters"],
    "additionalProperties": False
}


def validate(data: Dict[str, Any]) -> bool:
    """
    [CORE: schema-validate] - Validate data against REWRITE_OUTPUT_SCHEMA.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        True if valid
        
    Raises:
        jsonschema.ValidationError: If validation fails
    """
    jsonschema.validate(instance=data, schema=REWRITE_OUTPUT_SCHEMA)
    return True


def from_dict(data: Dict[str, Any]) -> RewriteOutput:
    """
    Create RewriteOutput from validated dict.
    
    Args:
        data: Dictionary matching REWRITE_OUTPUT_SCHEMA
        
    Returns:
        RewriteOutput instance
    """
    validate(data)  # Ensure valid before creating
    return RewriteOutput(
        topic=data["topic"],
        entities=data["entities"],
        time_range=data["time_range"],
        query_rewrite=data["query_rewrite"],
        filters=data["filters"]
    )
