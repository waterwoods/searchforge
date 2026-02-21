#!/usr/bin/env python3
"""
Step 5B MVP: Verify discovered sources by crawling a small sample
Fetches pages from passing sources and writes JSONL.
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "results" / "auto_insurance_discovery"


def extract_text(html: str, url: str) -> Tuple[str, str]:
    """Extract title and text content from HTML"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get title
        title = soup.title.string if soup.title else "No title"
        if title:
            title = title.strip()
        
        # Remove script, style, nav, header, footer
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # Extract main content
        main_content = None
        for selector in ["main", "article", "[role='main']", "body"]:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.body if soup.body else soup
        
        # Get text
        text = main_content.get_text(separator=" ", strip=True)
        # Clean up excessive whitespace
        text = " ".join(text.split())
        
        return title, text
    except Exception as e:
        logger.warning(f"Failed to extract text from {url}: {e}")
        return "No title", ""


def fetch_and_extract(url: str, timeout: int = 10) -> Optional[Dict]:
    """Fetch URL and extract content"""
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type:
            logger.warning(f"Skipping non-HTML: {url} ({content_type})")
            return None
        
        html = response.text
        title, text = extract_text(html, url)
        
        return {
            "url": url,
            "title": title,
            "text": text,
            "text_length": len(text),
            "fetched_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def generate_verify_report(documents: List[Dict], output_dir: Path):
    """Generate verification report"""
    report = []
    report.append("# Verification Report")
    report.append("")
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("")
    
    report.append("## Summary")
    report.append("")
    report.append(f"- Pages fetched: {len(documents)}")
    report.append(f"- Documents kept: {len(documents)}")
    
    if documents:
        total_chars = sum(d['text_length'] for d in documents)
        avg_chars = total_chars / len(documents)
        report.append(f"- Total characters: {total_chars:,}")
        report.append(f"- Average characters: {avg_chars:.0f}")
        report.append("")
        
        # Domain breakdown
        domain_counts = defaultdict(int)
        domain_chars = defaultdict(int)
        for doc in documents:
            domain = urlparse(doc['url']).netloc
            domain_counts[domain] += 1
            domain_chars[domain] += doc['text_length']
        
        report.append("## By Domain")
        report.append("")
        for domain in sorted(domain_counts.keys()):
            count = domain_counts[domain]
            chars = domain_chars[domain]
            avg = chars / count if count > 0 else 0
            report.append(f"- **{domain}**: {count} pages, {chars:,} chars (avg {avg:.0f})")
        report.append("")
        
        # Top documents
        report.append("## Documents")
        report.append("")
        for i, doc in enumerate(documents, 1):
            report.append(f"{i}. **{doc['title'][:60]}**")
            report.append(f"   - URL: {doc['url']}")
            report.append(f"   - Length: {doc['text_length']:,} chars")
            report.append("")
    
    report_file = output_dir / "VERIFY_REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    logger.info(f"Wrote verification report to {report_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Verify discovered sources")
    parser.add_argument("--input-passing-json", type=str, default=None,
                       help="Path to passing.json (default: <output-dir>/passing.json)")
    parser.add_argument("--top-k", type=int, default=5,
                       help="Top K candidates to verify (default: 5)")
    parser.add_argument("--pages-per-domain", type=int, default=3,
                       help="Pages per domain (default: 3)")
    parser.add_argument("--output-dir", type=str, default=None,
                       help="Output directory (default: results/auto_insurance_discovery)")
    
    args = parser.parse_args()
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine passing file
    if args.input_passing_json:
        passing_file = Path(args.input_passing_json)
    else:
        passing_file = output_dir / "passing.json"
    
    # Load passing candidates
    if not passing_file.exists():
        logger.error(f"Passing file not found: {passing_file}")
        logger.error("Run discovery first: python scripts/discover_auto_insurance_sources.py")
        sys.exit(1)
    
    with open(passing_file, 'r', encoding='utf-8') as f:
        passing = json.load(f)
    
    if not passing:
        logger.error("No passing candidates found")
        sys.exit(1)
    
    logger.info(f"Loaded {len(passing)} passing candidates")
    
    # Group by domain
    domains = defaultdict(list)
    for candidate in passing:
        domain = candidate['domain']
        domains[domain].append(candidate)
    
    # Select top domains (by candidate count)
    sorted_domains = sorted(domains.items(), key=lambda x: len(x[1]), reverse=True)
    selected_domains = [d[0] for d in sorted_domains[:2]]
    logger.info(f"Selected domains: {selected_domains}")
    
    # Select URLs (top K total, respecting pages-per-domain)
    urls_to_fetch = []
    for domain in selected_domains:
        domain_candidates = domains[domain]
        # Sort by score and take top pages_per_domain
        domain_candidates_sorted = sorted(domain_candidates, key=lambda x: x['score'], reverse=True)
        urls_to_fetch.extend([c['url'] for c in domain_candidates_sorted[:args.pages_per_domain]])
        if len(urls_to_fetch) >= args.top_k:
            break
    
    urls_to_fetch = urls_to_fetch[:args.top_k]
    logger.info(f"Fetching {len(urls_to_fetch)} URLs")
    
    # Fetch and extract
    documents = []
    for url in urls_to_fetch:
        logger.info(f"Fetching: {url}")
        doc = fetch_and_extract(url)
        if doc:
            documents.append(doc)
            logger.info(f"  Extracted: {doc['text_length']} chars")
    
    # Write JSONL
    verify_output = output_dir / "verify_corpus.jsonl"
    with open(verify_output, 'w', encoding='utf-8') as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')
    logger.info(f"Wrote {len(documents)} documents to {verify_output}")
    
    # Generate report
    generate_verify_report(documents, output_dir)
    
    # Print summary
    total_chars = sum(d['text_length'] for d in documents)
    avg_chars = total_chars / len(documents) if documents else 0
    domains_fetched = set(urlparse(d['url']).netloc for d in documents)
    
    print("\n" + "="*60)
    print("Verification Complete")
    print("="*60)
    print(f"Pages fetched: {len(documents)}")
    print(f"Documents kept: {len(documents)}")
    print(f"Domains: {len(domains_fetched)} ({', '.join(domains_fetched)})")
    print(f"Average chars: {avg_chars:.0f}")
    print(f"\nOutputs:")
    print(f"  - {verify_output}")
    print(f"  - {output_dir / 'VERIFY_REPORT.md'}")
    print("="*60)


if __name__ == "__main__":
    main()
