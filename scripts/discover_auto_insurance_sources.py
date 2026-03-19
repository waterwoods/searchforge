#!/usr/bin/env python3
"""
Step 5B MVP: Auto-discover new insurance information sources
Discovers candidate URLs from seed pages, scores them, and filters to passing candidates.
Supports long-running jobs with checkpointing and crash-resume safety.
"""

import sys
import json
import time
import argparse
import signal
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from collections import defaultdict
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM gracefully"""
    global shutdown_requested
    logger.info("Shutdown signal received, will finish current operation and exit gracefully")
    shutdown_requested = True

# Seed URLs - known-good starting points
# Note: Using specific /auto/ or /car-insurance/ pages, not homepages, for better discovery
# T0 = CA government (authoritative). T1 = commercial insurers (allowed, lower than .gov).
# State Farm removed: blocked by robots.txt per prior run review.
SEED_URLS = [
    # T0: Official CA government sources (authoritative)
    "https://www.dmv.ca.gov/portal/vehicle-registration/insurance-requirements/",
    "https://www.insurance.ca.gov/01-consumers/help/auto/",
    # T1: Major insurers - auto insurance entry/info pages
    "https://www.geico.com/information/aboutinsurance/auto/",
    "https://www.progressive.com/auto/",
    "https://www.allstate.com/auto-insurance",
    "https://www.farmers.com/insurance/auto",
    "https://www.nationwide.com/personal/insurance/auto/",
    "https://www.libertymutual.com/auto-insurance",
    "https://www.travelers.com/car-insurance",
    "https://ace.aaa.com/insurance/auto-insurance.html",
    "https://www.usaa.com/insurance/vehicles/auto",
]

# Domain trust tiers (see docs/STEP5B_SEEDS_TIERS_UPDATE.md)
# T0: CA government domains - highest trust, authoritative for CA regulations
# T1: Commercial insurers - major companies, allowed but lower than .gov
# T2: Reputable third-party (NAIC, III, comparison sites)
DOMAIN_TRUST_TIERS = {
    "T0": {  # Official CA gov domains - highest trust
        "dmv.ca.gov", "insurance.ca.gov", "ca.gov"
    },
    "T1": {  # Top insurers - major insurance companies (commercial tier)
        "geico.com", "progressive.com", "allstate.com", "farmers.com", "nationwide.com",
        "libertymutual.com", "travelers.com", "aaa.com", "ace.aaa.com", "usaa.com"
    },
    "T2": {  # Other reputable sources
        "naic.org",  # National Association of Insurance Commissioners
        "iii.org",  # Insurance Information Institute
        "consumerreports.org",
        "nerdwallet.com",
        "valuepenguin.com",
        "thezebra.com",
    }
}

# Insurance-related keywords for scoring
INSURANCE_KEYWORDS = [
    "insurance", "auto", "car", "vehicle", "liability", "coverage", "claim",
    "sr-22", "premium", "deductible", "uninsured", "collision", "comprehensive",
    "policy", "motorist", "medical", "payment", "bodily", "property", "damage"
]

# Binary extensions to exclude
BINARY_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".jpg", ".jpeg", ".png", ".gif", ".svg"}

# URL patterns to exclude
EXCLUDE_PATTERNS = [
    "/login", "/account", "/careers", "/pressroom", "/privacy", "/terms",
    "/contact", "/signup", "/register", "/checkout", "/cart", "/payment"
]


class RobotsTxtChecker:
    """Check robots.txt compliance. Uses timeout to avoid hanging on slow domains."""
    
    def __init__(self, timeout: int = 10):
        self.parsers: Dict[str, RobotFileParser] = {}
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        self.timeout = timeout
    
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        if base_url not in self.parsers:
            rp = RobotFileParser()
            robots_url = urljoin(base_url, "/robots.txt")
            try:
                # Fetch with timeout to avoid hanging (RobotFileParser.read() has no timeout)
                resp = requests.get(robots_url, timeout=self.timeout)
                resp.raise_for_status()
                rp.parse(resp.text.splitlines())
                self.parsers[base_url] = rp
                logger.debug(f"Loaded robots.txt from {robots_url}")
            except Exception as e:
                logger.warning(f"Failed to read robots.txt from {robots_url}: {e}")
                # Default to allowing if robots.txt is not accessible
                return True
        
        return self.parsers[base_url].can_fetch(self.user_agent, url)


class SourceDiscoverer:
    """Discover and score candidate URLs"""
    
    def __init__(self, per_domain_delay: float = 1.0, global_delay: float = 0.5):
        self.robots_checker = RobotsTxtChecker()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        self.visited_urls: Set[str] = set()
        self.candidates: List[Dict] = []
        self.per_domain_delay = per_domain_delay
        self.global_delay = global_delay
        self.start_time = time.time()
        self.last_checkpoint_time = time.time()
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        parsed = urlparse(url)
        # Remove query params and fragments
        parsed = parsed._replace(query="", fragment="")
        # Remove trailing slash
        path = parsed.path.rstrip("/")
        parsed = parsed._replace(path=path)
        # Lowercase domain
        parsed = parsed._replace(netloc=parsed.netloc.lower())
        return urlunparse(parsed)
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        # Remove www. prefix
        domain = domain.replace('www.', '')
        return domain
    
    def get_domain_tier(self, domain: str) -> Optional[str]:
        """Get trust tier for domain"""
        for tier, domains in DOMAIN_TRUST_TIERS.items():
            if domain in domains:
                return tier
        return None
    
    def is_binary_url(self, url: str) -> bool:
        """Check if URL points to binary file"""
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        return any(path_lower.endswith(ext) for ext in BINARY_EXTENSIONS)
    
    def should_exclude_url(self, url: str) -> bool:
        """Check if URL should be excluded based on patterns"""
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in EXCLUDE_PATTERNS)
    
    def has_long_query(self, url: str) -> bool:
        """Check if URL has suspiciously long query string"""
        parsed = urlparse(url)
        return len(parsed.query) > 100
    
    def extract_text(self, html: str) -> Tuple[str, str]:
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
            logger.warning(f"Failed to extract text: {e}")
            return "No title", ""
    
    def score_url(self, url: str, domain: str, title: str, text: str) -> Tuple[float, List[str]]:
        """Score a candidate URL"""
        score = 0.0
        reasons = []
        
        # Domain trust tier
        tier = self.get_domain_tier(domain)
        if tier == "T0":
            score += 30.0
            reasons.append("T0_official_gov")
        elif tier == "T1":
            score += 20.0
            reasons.append("T1_top_insurer")
        elif tier == "T2":
            score += 10.0
            reasons.append("T2_reputable")
        else:
            score += 2.0
            reasons.append("T3_unknown_domain")
        
        # Keyword matching in URL
        url_lower = url.lower()
        keyword_matches = sum(1 for kw in INSURANCE_KEYWORDS if kw in url_lower)
        score += keyword_matches * 2.0
        if keyword_matches > 0:
            reasons.append(f"url_keywords_{keyword_matches}")
        
        # Keyword matching in title
        title_lower = title.lower()
        title_keyword_matches = sum(1 for kw in INSURANCE_KEYWORDS if kw in title_lower)
        score += title_keyword_matches * 1.5
        if title_keyword_matches > 0:
            reasons.append(f"title_keywords_{title_keyword_matches}")
        
        # Content length (contentfulness)
        text_length = len(text)
        if text_length >= 1200:
            score += 15.0
            reasons.append("contentful_1200+")
        elif text_length >= 500:
            score += 8.0
            reasons.append("contentful_500+")
        elif text_length >= 200:
            score += 3.0
            reasons.append("contentful_200+")
        else:
            reasons.append("low_content")
        
        # Penalties
        if self.has_long_query(url):
            score -= 5.0
            reasons.append("penalty_long_query")
        
        return score, reasons
    
    def fetch_url(self, url: str, timeout: int = 10) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Fetch URL and return (html, title, text) or (None, None, None) on failure"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                logger.debug(f"Skipping non-HTML: {url} ({content_type})")
                return None, None, None
            
            html = response.text
            title, text = self.extract_text(html)
            return html, title, text
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")
            return None, None, None
    
    def extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract links from HTML"""
        links = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                # Remove fragment
                parsed = urlparse(absolute_url)
                absolute_url = urlunparse(parsed._replace(fragment=''))
                
                # Only http/https
                if not absolute_url.startswith(('http://', 'https://')):
                    continue
                
                links.append(absolute_url)
        except Exception as e:
            logger.warning(f"Failed to extract links from {base_url}: {e}")
        return links
    
    def discover_from_seed(self, seed_url: str, max_links_per_seed: int = 50) -> List[str]:
        """Discover candidate URLs from a seed page"""
        global shutdown_requested
        discovered = []
        
        normalized = self.normalize_url(seed_url)
        if normalized in self.visited_urls:
            return discovered
        
        self.visited_urls.add(normalized)
        
        logger.info(f"Discovering from seed: {seed_url}")
        
        # Check robots.txt - log and skip blocked domains
        if not self.robots_checker.can_fetch(seed_url):
            logger.info(f"Blocked by robots.txt (skipping): {seed_url}")
            return discovered
        
        # Fetch seed page
        html, title, text = self.fetch_url(seed_url)
        if not html:
            logger.warning(f"Failed to fetch seed: {seed_url}")
            return discovered
        
        # Extract links
        links = self.extract_links(html, seed_url)
        logger.info(f"Found {len(links)} links from {seed_url}")
        
        # Process links
        for link in links[:max_links_per_seed]:
            if shutdown_requested:
                logger.info("Shutdown requested, stopping discovery")
                break
            
            normalized_link = self.normalize_url(link)
            if normalized_link in self.visited_urls:
                continue
            
            # Basic filters
            if self.is_binary_url(link):
                continue
            if self.should_exclude_url(link):
                continue
            if self.has_long_query(link):
                continue
            
            discovered.append(link)
            self.visited_urls.add(normalized_link)
        
        # Per-domain delay
        if self.per_domain_delay > 0:
            time.sleep(self.per_domain_delay)
        
        return discovered
    
    def process_candidate(self, url: str) -> Optional[Dict]:
        """Process a candidate URL and return candidate dict or None"""
        domain = self.get_domain(url)
        
        # Check robots.txt
        blocked = not self.robots_checker.can_fetch(url)
        if blocked:
            logger.info(f"Blocked by robots.txt (skipping): {url}")
            return {
                "url": url,
                "domain": domain,
                "score": 0.0,
                "reasons": ["blocked_robots_txt"],
                "blocked_by_robots": True,
                "content_length": 0,
                "title": "Blocked"
            }
        
        # Fetch and extract
        html, title, text = self.fetch_url(url)
        if not html:
            return {
                "url": url,
                "domain": domain,
                "score": 0.0,
                "reasons": ["fetch_failed"],
                "blocked_by_robots": False,
                "content_length": 0,
                "title": "Fetch failed"
            }
        
        content_length = len(text)
        
        # Score
        score, reasons = self.score_url(url, domain, title, text)
        
        return {
            "url": url,
            "domain": domain,
            "score": round(score, 2),
            "reasons": reasons,
            "blocked_by_robots": False,
            "content_length": content_length,
            "title": title
        }
    
    def run_discovery(self, max_candidates: int = 30, max_runtime_minutes: Optional[int] = None, 
                     checkpoint_every_sec: int = 600, output_dir: Optional[Path] = None) -> List[Dict]:
        """Run discovery process with checkpointing support"""
        global shutdown_requested
        logger.info("Starting discovery process...")
        if max_runtime_minutes:
            logger.info(f"Max runtime: {max_runtime_minutes} minutes")
        if checkpoint_every_sec:
            logger.info(f"Checkpointing every {checkpoint_every_sec} seconds")
        
        max_runtime_seconds = max_runtime_minutes * 60 if max_runtime_minutes else None
        
        # Discover from seeds
        all_discovered = []
        for seed_url in SEED_URLS:
            if shutdown_requested:
                logger.info("Shutdown requested, stopping seed discovery")
                break
            
            if max_runtime_seconds and (time.time() - self.start_time) >= max_runtime_seconds:
                logger.info(f"Max runtime ({max_runtime_minutes} minutes) reached, stopping seed discovery")
                break
            
            discovered = self.discover_from_seed(seed_url)
            all_discovered.extend(discovered)
            
            if self.global_delay > 0:
                time.sleep(self.global_delay)
        
        logger.info(f"Discovered {len(all_discovered)} candidate URLs")
        
        # Process candidates
        logger.info("Processing candidates...")
        processed_count = 0
        for i, url in enumerate(all_discovered[:max_candidates * 2], 1):
            if shutdown_requested:
                logger.info("Shutdown requested, stopping candidate processing")
                break
            
            if max_runtime_seconds and (time.time() - self.start_time) >= max_runtime_seconds:
                logger.info(f"Max runtime ({max_runtime_minutes} minutes) reached, stopping candidate processing")
                break
            
            candidate = self.process_candidate(url)
            if candidate:
                self.candidates.append(candidate)
                processed_count += 1
            
            if i % 5 == 0:
                elapsed = time.time() - self.start_time
                logger.info(f"Processed {i}/{min(len(all_discovered), max_candidates * 2)} candidates "
                          f"({processed_count} valid, {elapsed/60:.1f} min elapsed)")
            
            # Checkpoint check
            if checkpoint_every_sec and (time.time() - self.last_checkpoint_time) >= checkpoint_every_sec:
                self._write_checkpoint(output_dir)
                self.last_checkpoint_time = time.time()
            
            if self.global_delay > 0:
                time.sleep(self.global_delay)
        
        # Sort by score
        self.candidates.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"Processed {len(self.candidates)} candidates")
        return self.candidates
    
    def _write_checkpoint(self, output_dir: Optional[Path]):
        """Write checkpoint files"""
        if not output_dir:
            return
        
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Write partial candidates
            candidates_file = output_dir / "candidates.json"
            with open(candidates_file, 'w', encoding='utf-8') as f:
                json.dump(self.candidates, f, indent=2, ensure_ascii=False)
            
            # Write checkpoint metadata
            checkpoint_file = output_dir / "checkpoint.json"
            checkpoint_data = {
                "timestamp": datetime.now().isoformat(),
                "candidates_count": len(self.candidates),
                "visited_urls_count": len(self.visited_urls),
                "elapsed_seconds": time.time() - self.start_time
            }
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Checkpoint written: {len(self.candidates)} candidates")
        except Exception as e:
            logger.warning(f"Failed to write checkpoint: {e}")


def generate_report(candidates: List[Dict], passing: List[Dict]) -> str:
    """Generate human-readable report"""
    report = []
    report.append("# Auto Insurance Source Discovery Report")
    report.append("")
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("")
    
    report.append("## Summary")
    report.append("")
    report.append(f"- Total candidates discovered: {len(candidates)}")
    report.append(f"- Passing candidates: {len(passing)}")
    report.append("")
    
    # Domain breakdown
    domain_counts = defaultdict(int)
    for c in candidates:
        domain_counts[c['domain']] += 1
    report.append("## Candidates by Domain")
    report.append("")
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
        report.append(f"- {domain}: {count} candidates")
    report.append("")
    
    # Top candidates
    report.append("## Top 10 Candidates")
    report.append("")
    for i, c in enumerate(candidates[:10], 1):
        report.append(f"{i}. **{c['title'][:60]}**")
        report.append(f"   - URL: {c['url']}")
        report.append(f"   - Score: {c['score']}")
        report.append(f"   - Domain: {c['domain']}")
        report.append(f"   - Content: {c['content_length']} chars")
        report.append(f"   - Reasons: {', '.join(c['reasons'])}")
        report.append("")
    
    # Passing candidates
    report.append("## Passing Candidates")
    report.append("")
    for i, c in enumerate(passing, 1):
        report.append(f"{i}. **{c['title'][:60]}**")
        report.append(f"   - URL: {c['url']}")
        report.append(f"   - Score: {c['score']}")
        report.append("")
    
    return "\n".join(report)


def filter_passing(candidates: List[Dict], min_score: float = 15.0, max_per_domain: int = 5) -> List[Dict]:
    """Filter candidates to passing list"""
    passing = []
    domain_counts = defaultdict(int)
    
    for candidate in candidates:
        if candidate['blocked_by_robots']:
            continue
        if candidate['score'] < min_score:
            continue
        
        domain = candidate['domain']
        if domain_counts[domain] >= max_per_domain:
            continue
        
        passing.append(candidate)
        domain_counts[domain] += 1
    
    return passing


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Discover auto insurance sources")
    parser.add_argument("--max-runtime-minutes", type=int, default=None,
                       help="Maximum runtime in minutes")
    parser.add_argument("--max-candidates", type=int, default=30,
                       help="Maximum number of candidates to process")
    parser.add_argument("--per-domain-delay", type=float, default=1.0,
                       help="Delay in seconds between seed domains")
    parser.add_argument("--global-delay", type=float, default=0.5,
                       help="Delay in seconds between candidate processing")
    parser.add_argument("--checkpoint-every-sec", type=int, default=600,
                       help="Checkpoint interval in seconds (default: 600 = 10 min)")
    parser.add_argument("--output-dir", type=str, default=None,
                       help="Output directory (default: results/auto_insurance_discovery)")
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(__file__).parent.parent / "results" / "auto_insurance_discovery"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    discoverer = SourceDiscoverer(
        per_domain_delay=args.per_domain_delay,
        global_delay=args.global_delay
    )
    
    candidates = discoverer.run_discovery(
        max_candidates=args.max_candidates,
        max_runtime_minutes=args.max_runtime_minutes,
        checkpoint_every_sec=args.checkpoint_every_sec,
        output_dir=output_dir
    )
    
    # Filter to passing
    passing = filter_passing(candidates, min_score=15.0, max_per_domain=5)
    
    # Write outputs
    candidates_file = output_dir / "candidates.json"
    with open(candidates_file, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote {len(candidates)} candidates to {candidates_file}")
    
    passing_file = output_dir / "passing.json"
    with open(passing_file, 'w', encoding='utf-8') as f:
        json.dump(passing, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote {len(passing)} passing candidates to {passing_file}")
    
    # Generate report
    report = generate_report(candidates, passing)
    report_file = output_dir / "REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"Wrote report to {report_file}")
    
    print("\n" + "="*60)
    print("Discovery Complete")
    print("="*60)
    print(f"Candidates: {len(candidates)}")
    print(f"Passing: {len(passing)}")
    print(f"\nOutputs:")
    print(f"  - {candidates_file}")
    print(f"  - {passing_file}")
    print(f"  - {report_file}")
    print("="*60)


if __name__ == "__main__":
    main()
