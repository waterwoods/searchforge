#!/usr/bin/env python3
"""
Sanity Check for auto_insurance_v1 Collection
=============================================
随机抽样 30 条 points，检查 domain 分布和内容质量
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import ScrollRequest
except ImportError:
    print("❌ Error: qdrant-client not installed")
    print("   Install: pip install qdrant-client")
    sys.exit(1)

# Configuration
COLLECTION_NAME = "auto_insurance_v1"
SAMPLE_SIZE = 30

# Insurance/DMV/CDI related domains (whitelist)
INSURANCE_DOMAINS = {
    "insurance.ca.gov",  # California Department of Insurance
    "dmv.ca.gov",  # California DMV
    "geico.com",
    "statefarm.com",
    "progressive.com",
    "allstate.com",
    "farmers.com",
    "nationwide.com",
    "usaa.com",
    "aaa.com",
    "nerdwallet.com",
    "valuepenguin.com",
    "thezebra.com",
    "insurance.com",
    "bankrate.com",
    "dmv.org",  # DMV.org (unofficial but relevant)
}

def get_domain(url: str) -> str:
    """Extract domain from URL."""
    if not url:
        return "unknown"
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return "invalid"

def mask_sensitive_info(text: str) -> str:
    """Mask sensitive information in URLs and keys."""
    # Mask Qdrant URL
    if "qdrant" in text.lower():
        parts = text.split("/")
        for i, part in enumerate(parts):
            if "qdrant" in part.lower() or "cloud" in part.lower():
                if i + 1 < len(parts):
                    parts[i + 1] = "***"
        return "/".join(parts)
    return text

def main():
    # Get Qdrant connection info
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url:
        print("❌ Error: QDRANT_URL not set")
        sys.exit(1)
    
    if not qdrant_api_key:
        print("❌ Error: QDRANT_API_KEY not set")
        sys.exit(1)
    
    print("=" * 70)
    print("Auto Insurance Collection Sanity Check")
    print("=" * 70)
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Qdrant URL: {mask_sensitive_info(qdrant_url)}")
    print(f"Sample Size: {SAMPLE_SIZE}")
    print()
    
    # Connect to Qdrant
    try:
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
        )
        print("✅ Connected to Qdrant Cloud")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        sys.exit(1)
    
    # Check if collection exists
    try:
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        if COLLECTION_NAME not in collection_names:
            print(f"❌ Collection '{COLLECTION_NAME}' not found")
            print(f"   Available collections: {', '.join(collection_names)}")
            sys.exit(1)
        print(f"✅ Collection '{COLLECTION_NAME}' exists")
    except Exception as e:
        print(f"❌ Failed to list collections: {e}")
        sys.exit(1)
    
    # Get collection info
    try:
        info = client.get_collection(COLLECTION_NAME)
        total_points = info.points_count
        print(f"✅ Total points in collection: {total_points}")
    except Exception as e:
        print(f"❌ Failed to get collection info: {e}")
        sys.exit(1)
    
    if total_points == 0:
        print("❌ Collection is empty")
        sys.exit(1)
    
    # Scroll to get random sample
    print()
    print("📊 Sampling points...")
    try:
        # Use scroll with limit to get a sample
        # We'll scroll through and take points
        scroll_result = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=SAMPLE_SIZE,
            with_payload=True,
            with_vectors=False,
        )
        points = scroll_result[0]
        print(f"✅ Retrieved {len(points)} points")
    except Exception as e:
        print(f"❌ Failed to scroll collection: {e}")
        sys.exit(1)
    
    # Analyze points
    print()
    print("=" * 70)
    print("Sample Analysis")
    print("=" * 70)
    print()
    
    domains = []
    languages = []
    samples = []
    
    for i, point in enumerate(points, 1):
        payload = point.payload or {}
        title = payload.get("title", "") or ""
        text = payload.get("text", "") or ""
        source_url = payload.get("source_url", "") or payload.get("url", "") or ""
        language = payload.get("language", "unknown")
        
        domain = get_domain(source_url)
        domains.append(domain)
        languages.append(language)
        
        # Get preview text (first 80 chars)
        preview = (title + " " + text)[:80].replace("\n", " ").strip()
        
        samples.append({
            "index": i,
            "title": title[:80] if title else "(no title)",
            "preview": preview,
            "domain": domain,
            "source_url": source_url,
            "language": language,
        })
    
    # Print samples
    print("Sample Points:")
    print("-" * 70)
    for sample in samples:
        print(f"\n[{sample['index']}] Domain: {sample['domain']}")
        print(f"    Title: {sample['title']}")
        print(f"    Preview: {sample['preview']}...")
        print(f"    Language: {sample['language']}")
        print(f"    URL: {sample['source_url'][:80]}..." if len(sample['source_url']) > 80 else f"    URL: {sample['source_url']}")
    
    # Domain statistics
    print()
    print("=" * 70)
    print("Domain Statistics")
    print("=" * 70)
    domain_counter = Counter(domains)
    print(f"\nTop 10 Domains:")
    for domain, count in domain_counter.most_common(10):
        percentage = (count / len(domains)) * 100
        print(f"  {domain}: {count} ({percentage:.1f}%)")
    
    # Check insurance-related domains
    print()
    print("=" * 70)
    print("Quality Check")
    print("=" * 70)
    
    insurance_count = 0
    for domain in domains:
        # Check if domain matches insurance domains (exact or contains)
        is_insurance = False
        for insurance_domain in INSURANCE_DOMAINS:
            if insurance_domain in domain or domain in insurance_domain:
                is_insurance = True
                break
        if is_insurance:
            insurance_count += 1
    
    insurance_percentage = (insurance_count / len(domains)) * 100
    print(f"\nInsurance/DMV/CDI related domains: {insurance_count}/{len(domains)} ({insurance_percentage:.1f}%)")
    
    # Language distribution
    print()
    language_counter = Counter(languages)
    print("Language Distribution:")
    for lang, count in language_counter.most_common():
        percentage = (count / len(languages)) * 100
        print(f"  {lang}: {count} ({percentage:.1f}%)")
    
    # Final verdict
    print()
    print("=" * 70)
    print("Verdict")
    print("=" * 70)
    
    if insurance_percentage >= 80:
        print(f"✅ PASS: {insurance_percentage:.1f}% from insurance/DMV/CDI domains (>= 80%)")
        return 0
    else:
        print(f"❌ FAIL: Only {insurance_percentage:.1f}% from insurance/DMV/CDI domains (< 80%)")
        print(f"   Expected: >= 80%")
        print(f"   Actual: {insurance_percentage:.1f}%")
        return 1

if __name__ == "__main__":
    sys.exit(main())
