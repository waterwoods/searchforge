#!/usr/bin/env python3
"""
Step 5B MVP: Optionally append passing discovered sources to data_sources.json
Creates a new ds_auto_discovered_001 entry without modifying existing ds_001..ds_005.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
REPO_DIR = Path(__file__).parent.parent
PASSING_FILE = REPO_DIR / "results" / "auto_insurance_discovery" / "passing.json"
DATA_SOURCES_FILE = REPO_DIR / "docs" / "prompt2_input" / "data_sources.json"


def group_by_domain(passing: List[Dict]) -> Dict[str, List[Dict]]:
    """Group passing candidates by domain"""
    domains = defaultdict(list)
    for candidate in passing:
        domain = candidate['domain']
        domains[domain].append(candidate)
    return dict(domains)


def create_data_source_entry(domain: str, urls: List[str], base_url: str) -> Dict:
    """Create a data source entry for a domain"""
    # Determine priority based on domain
    if any(gov in domain for gov in ['dmv.ca.gov', 'insurance.ca.gov', 'ca.gov']):
        priority = "P0"
    elif domain in ['geico.com', 'progressive.com', 'statefarm.com', 'allstate.com', 'farmers.com', 'nationwide.com']:
        priority = "P1"
    else:
        priority = "P2"
    
    return {
        "id": "ds_auto_discovered_001",
        "name": f"Auto-Discovered: {domain}",
        "base_url": base_url,
        "priority": priority,
        "content_types": ["auto_discovered", "coverage", "faq"],
        "expected_value": f"Auto-discovered content from {domain}",
        "crawl_difficulty": "medium",
        "legal_note": "Auto-discovered source. Review robots.txt before crawling.",
        "target_urls": urls[:15],  # Limit to 15 URLs
        "estimated_documents": len(urls) * 10,  # Rough estimate
        "language": "en"
    }


def main():
    """Main entry point"""
    # Load passing candidates
    if not PASSING_FILE.exists():
        logger.error(f"Passing file not found: {PASSING_FILE}")
        logger.error("Run discovery first: bash scripts/run_step5b_discovery_mvp.sh")
        sys.exit(1)
    
    with open(PASSING_FILE, 'r', encoding='utf-8') as f:
        passing = json.load(f)
    
    if not passing:
        logger.error("No passing candidates found")
        sys.exit(1)
    
    logger.info(f"Loaded {len(passing)} passing candidates")
    
    # Group by domain
    domains = group_by_domain(passing)
    logger.info(f"Found {len(domains)} domains")
    
    # Select top domain (most URLs)
    if not domains:
        logger.error("No domains found")
        sys.exit(1)
    
    top_domain = max(domains.items(), key=lambda x: len(x[1]))[0]
    domain_candidates = domains[top_domain]
    
    logger.info(f"Selected domain: {top_domain} ({len(domain_candidates)} URLs)")
    
    # Extract URLs and base_url
    urls = [c['url'] for c in domain_candidates]
    # Get base_url from first URL
    from urllib.parse import urlparse
    first_url = urls[0]
    parsed = urlparse(first_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    # Create data source entry
    new_entry = create_data_source_entry(top_domain, urls, base_url)
    
    # Load existing data_sources.json
    if not DATA_SOURCES_FILE.exists():
        logger.error(f"Data sources file not found: {DATA_SOURCES_FILE}")
        sys.exit(1)
    
    with open(DATA_SOURCES_FILE, 'r', encoding='utf-8') as f:
        data_sources = json.load(f)
    
    # Check if ds_auto_discovered_001 already exists
    existing_ids = {ds['id'] for ds in data_sources.get('data_sources', [])}
    if 'ds_auto_discovered_001' in existing_ids:
        logger.warning("ds_auto_discovered_001 already exists. Skipping append.")
        logger.info("To update, manually remove the existing entry first.")
        sys.exit(0)
    
    # Append new entry
    if 'data_sources' not in data_sources:
        data_sources['data_sources'] = []
    
    data_sources['data_sources'].append(new_entry)
    data_sources['total_sources'] = len(data_sources['data_sources'])
    
    # Backup original file
    backup_file = DATA_SOURCES_FILE.with_suffix('.json.bak')
    import shutil
    shutil.copy2(DATA_SOURCES_FILE, backup_file)
    logger.info(f"Backed up original to: {backup_file}")
    
    # Write updated file
    with open(DATA_SOURCES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_sources, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Appended ds_auto_discovered_001 to {DATA_SOURCES_FILE}")
    
    print("\n" + "="*60)
    print("Append Complete")
    print("="*60)
    print(f"Added entry: ds_auto_discovered_001")
    print(f"Domain: {top_domain}")
    print(f"URLs: {len(urls)}")
    print(f"Base URL: {base_url}")
    print(f"\nBackup: {backup_file}")
    print(f"Updated: {DATA_SOURCES_FILE}")
    print("="*60)
    print("\n⚠️  WARNING: Review the new entry before using in production!")
    print("   - Verify URLs are accessible")
    print("   - Check robots.txt compliance")
    print("   - Confirm content is relevant")


if __name__ == "__main__":
    main()
