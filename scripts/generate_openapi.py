#!/usr/bin/env python3
"""Generate OpenAPI snapshot from FastAPI app"""
import sys
import json
from pathlib import Path

# Add services/fiqa_api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "fiqa_api"))

from app import app

def main():
    output_path = Path(__file__).parent.parent / "docs" / "openapi_snapshot.json"
    output_path.parent.mkdir(exist_ok=True)
    
    # Get OpenAPI schema from FastAPI
    openapi_schema = app.openapi()
    
    # Write to file with pretty formatting
    with open(output_path, 'w') as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"✓ Generated OpenAPI snapshot: {output_path}")
    print(f"  Endpoints: {len(openapi_schema.get('paths', {}))} paths")
    print(f"  Version: {openapi_schema.get('info', {}).get('version', 'unknown')}")
    
    # Verify /search response schema contains required keys
    search_schema = openapi_schema.get('paths', {}).get('/search', {})
    search_response = search_schema.get('post', {}).get('responses', {}).get('200', {})
    print(f"  /search response schema: present={bool(search_response)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

