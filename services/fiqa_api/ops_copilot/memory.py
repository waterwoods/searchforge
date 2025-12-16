"""
memory.py - Lightweight File-Based Memory Layer for Ops Copilot
================================================================
Simple memory loader that reads markdown knowledge base files and returns
relevant snippets based on service/env/region matching.

This is a minimal implementation for interview demo purposes. In production,
this would be replaced with a vector DB or proper knowledge base system.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("ops_copilot.memory")

# Module-level cache for knowledge base files (loaded once at module import)
_KNOWLEDGE_BASE: Dict[str, str] = {}
_KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent.parent.parent / "knowledge_base"


def _load_knowledge_base() -> None:
    """
    Load all knowledge base markdown files into memory at module initialization.
    
    This runs once when the module is imported, not on every query.
    """
    global _KNOWLEDGE_BASE
    
    if _KNOWLEDGE_BASE:
        # Already loaded
        return
    
    try:
        kb_dir = _KNOWLEDGE_BASE_DIR
        if not kb_dir.exists():
            logger.warning(f"[MEMORY] Knowledge base directory not found: {kb_dir}")
            return
        
        # Load all markdown files
        for md_file in ["incidents.md", "runbooks.md", "configs.md", "lessons_learned.md"]:
            file_path = kb_dir / md_file
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                category = md_file.replace(".md", "")
                _KNOWLEDGE_BASE[category] = content
                logger.info(f"[MEMORY] Loaded {len(content)} chars from {md_file}")
            else:
                logger.warning(f"[MEMORY] Knowledge base file not found: {md_file}")
        
        logger.info(f"[MEMORY] Knowledge base loaded: {len(_KNOWLEDGE_BASE)} categories")
    except Exception as e:
        logger.warning(f"[MEMORY] Failed to load knowledge base: {e}")


# Load knowledge base at module import time
_load_knowledge_base()


def _extract_snippets(
    content: str,
    service_name: str,
    env: Optional[str] = None,
    region: Optional[str] = None,
    max_snippets: int = 3,
    max_snippet_length: int = 400,
) -> List[str]:
    """
    Extract relevant snippets from content based on simple text matching.
    
    Args:
        content: Full text content to search
        service_name: Service name to match (e.g., "payment-service")
        env: Optional environment (e.g., "prod", "staging")
        region: Optional region (e.g., "us-east-1")
        max_snippets: Maximum number of snippets to return
        max_snippet_length: Maximum length of each snippet in characters
    
    Returns:
        List of relevant snippets (max max_snippets items)
    """
    snippets = []
    
    # Split content by markdown headers (## sections)
    sections = content.split("\n## ")
    
    for section in sections:
        if not section.strip():
            continue
        
        # Simple text matching: check if section contains service name
        # Use case-insensitive matching
        section_lower = section.lower()
        service_lower = service_name.lower()
        
        # Check for exact service name match first
        if f"[{service_lower}]" in section_lower or service_lower in section_lower:
            # Optional: check env and region for more specific matching
            env_match = True
            region_match = True
            
            if env:
                env_lower = env.lower()
                # Check if section mentions environment
                if f"[{env_lower}]" in section_lower:
                    env_match = True
                elif "prod" in section_lower or "staging" in section_lower or "dev" in section_lower:
                    # Section mentions some environment but not ours - deprioritize
                    env_match = False
                else:
                    # Section doesn't mention environment - neutral match
                    env_match = True
            
            if region:
                region_lower = region.lower()
                # Check if section mentions region
                if region_lower in section_lower:
                    region_match = True
                elif "us-east" in section_lower or "us-west" in section_lower or "eu-west" in section_lower:
                    # Section mentions some region but not ours - deprioritize
                    region_match = False
                else:
                    # Section doesn't mention region - neutral match
                    region_match = True
            
            # Priority: exact match (service + env + region) > partial match
            if env_match and region_match:
                # Extract first few lines or first paragraph
                lines = section.split("\n")
                snippet_lines = []
                char_count = 0
                
                for line in lines[:20]:  # Look at first 20 lines
                    if char_count + len(line) > max_snippet_length:
                        break
                    snippet_lines.append(line)
                    char_count += len(line) + 1  # +1 for newline
                
                snippet = "\n".join(snippet_lines).strip()
                if snippet and len(snippet) > 50:  # Minimum snippet length
                    # Truncate if too long
                    if len(snippet) > max_snippet_length:
                        snippet = snippet[:max_snippet_length] + "..."
                    snippets.append(snippet)
                
                if len(snippets) >= max_snippets:
                    break
    
    return snippets


def load_system_memory(
    service_name: str,
    env: Optional[str] = None,
    region: Optional[str] = None,
    max_snippets_per_category: int = 2,
    max_snippet_length: int = 400,
) -> Dict[str, List[str]]:
    """
    Load relevant memory snippets for a given service/env/region.
    
    This function searches the knowledge base (incidents, runbooks, configs, lessons)
    and returns snippets that match the service name, optionally filtered by env/region.
    
    Args:
        service_name: Service name (e.g., "payment-service", "api-gateway")
        env: Optional environment filter (e.g., "prod", "staging", "dev")
        region: Optional region filter (e.g., "us-east-1", "us-west-2")
        max_snippets_per_category: Maximum snippets per category (default: 2)
        max_snippet_length: Maximum length of each snippet in characters (default: 400)
    
    Returns:
        Dictionary with keys: "incidents", "runbooks", "configs", "lessons"
        Each value is a list of relevant snippet strings (may be empty if no matches)
    
    Example:
        >>> memory = load_system_memory("payment-service", env="prod", region="us-east-1")
        >>> print(f"Found {len(memory['incidents'])} incident snippets")
        >>> for snippet in memory['incidents']:
        >>>     print(snippet[:100])
    """
    if not _KNOWLEDGE_BASE:
        logger.warning(
            f"[MEMORY] Knowledge base not loaded, returning empty memory for {service_name}"
        )
        return {
            "incidents": [],
            "runbooks": [],
            "configs": [],
            "lessons": [],
        }
    
    logger.debug(
        f"[MEMORY] Loading memory for service={service_name} env={env} region={region}"
    )
    
    result = {
        "incidents": [],
        "runbooks": [],
        "configs": [],
        "lessons": [],
    }
    
    # Extract snippets from each category
    for category in ["incidents", "runbooks", "configs", "lessons_learned"]:
        content = _KNOWLEDGE_BASE.get(category, "")
        if not content:
            continue
        
        snippets = _extract_snippets(
            content=content,
            service_name=service_name,
            env=env,
            region=region,
            max_snippets=max_snippets_per_category,
            max_snippet_length=max_snippet_length,
        )
        
        # Map "lessons_learned" to "lessons" for output
        output_key = "lessons" if category == "lessons_learned" else category
        result[output_key] = snippets
        
        logger.debug(
            f"[MEMORY] Found {len(snippets)} snippets for {service_name} in {category}"
        )
    
    # Log summary
    total_snippets = sum(len(snippets) for snippets in result.values())
    logger.info(
        f"[MEMORY] Loaded {total_snippets} total snippets for {service_name} "
        f"(incidents={len(result['incidents'])}, runbooks={len(result['runbooks'])}, "
        f"configs={len(result['configs'])}, lessons={len(result['lessons'])})"
    )
    
    return result


__all__ = ["load_system_memory"]

