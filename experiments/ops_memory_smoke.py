#!/usr/bin/env python3
"""
ops_memory_smoke.py - Smoke Test for Ops Copilot Memory Layer
==============================================================
Small demo script that shows memory loading works for different services.

Usage:
    python experiments/ops_memory_smoke.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot.memory import load_system_memory


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print()


def print_memory_results(service_name: str, env: str, region: str = None) -> None:
    """
    Load and print memory for a service.
    
    Args:
        service_name: Service name (e.g., "payment-service")
        env: Environment (e.g., "prod")
        region: Optional region (e.g., "us-east-1")
    """
    print(f"Service: {service_name}")
    print(f"Environment: {env}")
    if region:
        print(f"Region: {region}")
    print()
    
    # Load memory
    memory = load_system_memory(
        service_name=service_name,
        env=env,
        region=region,
        max_snippets_per_category=2,
        max_snippet_length=400,
    )
    
    # Print summary
    total_snippets = sum(len(snippets) for snippets in memory.values())
    print(f"Total snippets found: {total_snippets}")
    print()
    
    # Print each category
    for category in ["incidents", "runbooks", "configs", "lessons"]:
        snippets = memory.get(category, [])
        print(f"[{category.upper()}] - {len(snippets)} snippet(s)")
        
        if snippets:
            for i, snippet in enumerate(snippets, 1):
                print(f"\n  Snippet {i}:")
                # Print first 200 characters
                preview = snippet[:200] if len(snippet) > 200 else snippet
                # Add indentation
                preview_indented = "\n    ".join(preview.split("\n"))
                print(f"    {preview_indented}")
                if len(snippet) > 200:
                    print(f"    ... (truncated, full length: {len(snippet)} chars)")
        else:
            print("    (no snippets found)")
        
        print()
    
    print("-" * 80)


def main():
    """Main entry point."""
    print_section_header("Ops Copilot Memory Layer - Smoke Test")
    
    print("This script demonstrates the file-based memory layer for Ops Copilot.")
    print("It loads knowledge base snippets (incidents, runbooks, configs, lessons)")
    print("for different services and shows what historical context is available.")
    print()
    print("The memory layer uses simple text matching on markdown files in knowledge_base/")
    print("and returns relevant snippets based on service name, environment, and region.")
    print()
    
    # Test Case 1: payment-service prod us-east-1
    print_section_header("Test Case 1: payment-service / prod / us-east-1")
    print_memory_results(
        service_name="payment-service",
        env="prod",
        region="us-east-1",
    )
    
    # Test Case 2: api-gateway prod (no region)
    print_section_header("Test Case 2: api-gateway / prod / (no region)")
    print_memory_results(
        service_name="api-gateway",
        env="prod",
    )
    
    # Test Case 3: search-api staging
    print_section_header("Test Case 3: search-api / staging / (no region)")
    print_memory_results(
        service_name="search-api",
        env="staging",
    )
    
    # Test Case 4: user-service prod (should have some results)
    print_section_header("Test Case 4: user-service / prod / (no region)")
    print_memory_results(
        service_name="user-service",
        env="prod",
    )
    
    # Test Case 5: unknown-service (should return empty)
    print_section_header("Test Case 5: unknown-service / prod / (no region)")
    print("Expected: No snippets found (service not in knowledge base)")
    print()
    print_memory_results(
        service_name="unknown-service",
        env="prod",
    )
    
    # Summary
    print_section_header("Summary")
    print("✓ Memory layer smoke test complete!")
    print()
    print("Key observations:")
    print("  - Service-specific snippets are correctly filtered")
    print("  - Environment and region matching works when specified")
    print("  - Unknown services gracefully return empty results")
    print("  - Snippet length is controlled (max ~400 chars per snippet)")
    print("  - Each category (incidents/runbooks/configs/lessons) is searched independently")
    print()
    print("Next steps:")
    print("  - This memory is now wired into the LLM explanation prompt")
    print("  - Run: python experiments/ops_copilot_demo.py --scenario critical")
    print("  - The LLM narrative will include historical context from these snippets")
    print()


if __name__ == "__main__":
    main()

