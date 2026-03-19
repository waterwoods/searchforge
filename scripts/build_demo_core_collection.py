#!/usr/bin/env python3
"""
Build Demo Core Collection Script
=================================
从 RUN_REVIEW.md 或 passing.json 读取 Top 10-20 个 URL，
抓取 → 抽取正文 → embed → upsert 到 auto_insurance_demo_core collection

Supports:
  - --url-list /path/to/urls.txt (one URL per line)
  - --run-dir /path/to/run (auto-discover URLs from RUN_REVIEW.md or passing.json)
  - robots.txt check (skip blocked pages)
  - Ingest report: results/opencrawl_demo_ingest/
"""

import sys
import json
import re
import os
import argparse
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from datetime import datetime

import numpy as np
import requests
from bs4 import BeautifulSoup
from qdrant_client import QdrantClient

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
from qdrant_client.models import Distance, VectorParams, PointStruct

# Load env from .env / .env.cloudrun
try:
    from dotenv import load_dotenv
    load_dotenv()
    p = Path(".env.cloudrun")
    if p.exists():
        load_dotenv(p, override=True)
except ImportError:
    pass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths
REPO_ROOT = Path(__file__).parent.parent
RESULTS_DISCOVERY = REPO_ROOT / "results" / "auto_insurance_discovery"
RUNS_DIR = RESULTS_DISCOVERY / "runs"
INGEST_REPORT_DIR = REPO_ROOT / "results" / "opencrawl_demo_ingest"

# Collection name
COLLECTION_NAME = "auto_insurance_demo_core"

# Embedding model (384 dim - matches fiqa_api EXPECTED_QDRANT_DIM)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
FASTEMBED_MODEL = "BAAI/bge-small-en-v1.5"  # 384 dim, fastembed-compatible
EMBEDDING_DIM = 384


def get_embedding_model():
    """Get embedder: fastembed first (avoids sentence_transformers/huggingface_hub issues), else SentenceTransformer."""
    if FASTEMBED_AVAILABLE:
        try:
            model = TextEmbedding(model_name=FASTEMBED_MODEL)
            logger.info(f"Using fastembed: {FASTEMBED_MODEL}")
            return model, "fastembed"
        except Exception as e:
            logger.warning(f"fastembed failed: {e}")
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info(f"Using sentence_transformers: {EMBEDDING_MODEL_NAME}")
            return model, "sbert"
        except Exception as e:
            logger.warning(f"sentence_transformers failed: {e}")
    raise RuntimeError("No embedding backend. Install fastembed or sentence-transformers.")

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


class RobotsTxtChecker:
    """Check robots.txt compliance - skip blocked pages."""

    def __init__(self):
        self.parsers: Dict[str, RobotFileParser] = {}

    def can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        if base_url not in self.parsers:
            rp = RobotFileParser()
            robots_url = urljoin(base_url, "/robots.txt")
            try:
                rp.set_url(robots_url)
                rp.read()
                self.parsers[base_url] = rp
            except Exception as e:
                logger.debug(f"robots.txt not accessible for {base_url}: {e}")
                return True
        return self.parsers[base_url].can_fetch(USER_AGENT, url)


def _source_tier(domain: str) -> str:
    """Classify domain as gov, insurer, or other."""
    d = domain.lower()
    if ".gov" in d:
        return "gov"
    if any(x in d for x in ["insurance", "insurer", "geico", "statefarm", "allstate", "progressive"]):
        return "insurer"
    return "other"


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


def fetch_and_extract(
    url: str,
    timeout: int = 30,
    robots_checker: Optional[RobotsTxtChecker] = None,
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Fetch URL and extract content.
    Returns (doc, fail_reason). fail_reason is None on success.
    """
    if robots_checker and not robots_checker.can_fetch(url):
        return None, "robots_txt_blocked"
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type:
            return None, f"non_html:{content_type[:50]}"
        html = response.text
        title, text = extract_text(html, url)
        if len(text) < 100:
            return None, f"text_too_short:{len(text)}"
        return {
            "url": url,
            "title": title,
            "text": text,
            "text_length": len(text),
            "fetched_at": datetime.now().isoformat(),
        }, None
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.RequestException as e:
        return None, f"fetch_error:{str(e)[:80]}"
    except Exception as e:
        return None, f"error:{str(e)[:80]}"


def parse_run_review_md(file_path: Path) -> List[str]:
    """Parse RUN_REVIEW.md to extract Top 20 URLs from the table."""
    urls = []
    if not file_path.exists():
        logger.warning(f"RUN_REVIEW.md not found: {file_path}")
        return urls
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r'\|.*?\|.*?\|.*?https?://[^\s\|]+'
    matches = re.findall(pattern, content)
    for match in matches:
        url_match = re.search(r'https?://[^\s\|]+', match)
        if url_match:
            url = url_match.group(0).rstrip('|').strip()
            if url and url not in urls:
                urls.append(url)
    logger.info(f"Extracted {len(urls)} URLs from RUN_REVIEW.md")
    return urls


def get_urls_from_passing_json(file_path: Path, top_n: int = 20) -> List[str]:
    """Get top N URLs from passing.json sorted by score."""
    if not file_path.exists():
        logger.warning(f"passing.json not found: {file_path}")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        passing = json.load(f)
    sorted_passing = sorted(passing, key=lambda x: x.get('score', 0), reverse=True)
    urls = [item['url'] for item in sorted_passing[:top_n] if 'url' in item]
    logger.info(f"Extracted {len(urls)} URLs from passing.json (top {top_n} by score)")
    return urls


def get_urls_from_run_dir(run_dir: Path, top_n: int = 20) -> List[str]:
    """Get URLs from run folder: RUN_REVIEW.md first, else passing.json."""
    run_review = run_dir / "RUN_REVIEW.md"
    passing = run_dir / "passing.json"
    urls = parse_run_review_md(run_review)
    if not urls and passing.exists():
        urls = get_urls_from_passing_json(passing, top_n)
    if not urls and (RESULTS_DISCOVERY / "passing.json").exists():
        urls = get_urls_from_passing_json(RESULTS_DISCOVERY / "passing.json", top_n)
    return urls[:top_n]


def load_urls_from_file(path: Path, limit: int = 20) -> List[str]:
    """Load URLs from file (one per line)."""
    urls = []
    if not path.exists():
        logger.warning(f"URL list not found: {path}")
        return urls
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith("#"):
                urls.append(url)
    return urls[:limit]


def get_latest_run_dir() -> Optional[Path]:
    """Return latest run directory by timestamp."""
    if not RUNS_DIR.exists():
        return None
    dirs = sorted([d for d in RUNS_DIR.iterdir() if d.is_dir()], reverse=True)
    return dirs[0] if dirs else None


def initialize_qdrant_client() -> QdrantClient:
    """Initialize Qdrant client.
    When USE_LOCAL_QDRANT=1, force local host/port (ignore QDRANT_URL from .env.cloudrun).
    """
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_url = None if os.getenv("USE_LOCAL_QDRANT") == "1" else os.getenv("QDRANT_URL")
    qdrant_api_key = None if os.getenv("USE_LOCAL_QDRANT") == "1" else os.getenv("QDRANT_API_KEY")
    
    if qdrant_url and (qdrant_url.startswith("http://") or qdrant_url.startswith("https://")):
        logger.info(f"Connecting to Qdrant at {qdrant_url}")
        client_kwargs = {"url": qdrant_url}
        if qdrant_api_key:
            client_kwargs["api_key"] = qdrant_api_key
        client = QdrantClient(**client_kwargs)
    else:
        logger.info(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}")
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
    
    # Test connection
    try:
        collections = client.get_collections()
        logger.info(f"Connected to Qdrant. Available collections: {[c.name for c in collections.collections]}")
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Qdrant: {e}")
    
    return client


def create_collection(client: QdrantClient, collection_name: str, vector_size: int, recreate: bool = False):
    """Create or recreate Qdrant collection"""
    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_exists = any(c.name == collection_name for c in collections.collections)
        
        if collection_exists:
            if recreate:
                logger.info(f"Deleting existing collection: {collection_name}")
                client.delete_collection(collection_name)
            else:
                logger.info(f"Collection {collection_name} already exists, skipping creation")
                return
        
        # Create collection
        logger.info(f"Creating collection: {collection_name} (vector_size={vector_size})")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        logger.info(f"✅ Collection {collection_name} created successfully")
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise


def write_ingest_report(
    report_dir: Path,
    selected_run: Optional[str],
    url_count: int,
    ingested: List[Dict],
    failed: List[Dict],
    collection_name: str,
    points_count: int,
) -> None:
    """Write INGEST_REPORT.md, ingested.jsonl, failed.jsonl."""
    report_dir.mkdir(parents=True, exist_ok=True)
    ingested_path = report_dir / "ingested.jsonl"
    failed_path = report_dir / "failed.jsonl"
    with open(ingested_path, 'w', encoding='utf-8') as f:
        for doc in ingested:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    with open(failed_path, 'w', encoding='utf-8') as f:
        for item in failed:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    domains = {}
    for doc in ingested:
        d = urlparse(doc['url']).netloc
        domains[d] = domains.get(d, 0) + 1
    top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]
    fail_reasons = {}
    for item in failed:
        r = item.get("reason", "unknown")
        fail_reasons[r] = fail_reasons.get(r, 0) + 1
    report_path = report_dir / "INGEST_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Demo Ingest Report\n\n")
        f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")
        f.write(f"- **Selected run folder**: {selected_run or 'N/A'}\n")
        f.write(f"- **Selected URL count**: {url_count}\n")
        f.write(f"- **Ingested count**: {len(ingested)}\n")
        f.write(f"- **Failed count**: {len(failed)}\n")
        f.write(f"- **Collection**: `{collection_name}`\n")
        f.write(f"- **Points in collection**: {points_count}\n\n")
        f.write("## Failed (reasons)\n\n")
        for r, c in sorted(fail_reasons.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- {r}: {c}\n")
        f.write("\n## Top domains ingested\n\n")
        for d, c in top_domains:
            f.write(f"- {d}: {c}\n")
    logger.info(f"Report written to {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Build demo core collection")
    parser.add_argument("--url-list", type=Path, help="Path to URL list file (one per line)")
    parser.add_argument("--run-dir", type=Path, help="Run directory (uses RUN_REVIEW.md or passing.json)")
    parser.add_argument("--collection", type=str, default=COLLECTION_NAME, help="Qdrant collection name")
    parser.add_argument("--limit", type=int, default=20, help="Max URLs to process")
    parser.add_argument("--max-runtime-minutes", type=int, default=20, help="Max runtime in minutes")
    parser.add_argument("--top-n", type=int, default=20, help="(legacy) Same as --limit")
    parser.add_argument("--recreate", action="store_true", help="Recreate collection if exists")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't upsert to Qdrant)")
    parser.add_argument("--no-robots-check", action="store_true", help="Skip robots.txt check")
    parser.add_argument("--report-dir", type=Path, default=INGEST_REPORT_DIR, help="Ingest report output dir")
    parser.add_argument("--report-run-dir", type=str, default=None, help="Run dir for report (e.g. 2026-02-21_105716)")
    args = parser.parse_args()
    limit = args.limit or args.top_n

    # Resolve URLs
    urls = []
    selected_run = args.report_run_dir
    if args.url_list:
        urls = load_urls_from_file(args.url_list, limit)
    elif args.run_dir:
        selected_run = selected_run or str(args.run_dir)
        urls = get_urls_from_run_dir(args.run_dir, limit)
    else:
        run_dir = get_latest_run_dir()
        if run_dir:
            selected_run = selected_run or str(run_dir)
            urls = get_urls_from_run_dir(run_dir, limit)
        if not urls:
            urls = parse_run_review_md(RESULTS_DISCOVERY / "RUN_REVIEW.md")
            if not urls:
                urls = get_urls_from_passing_json(RESULTS_DISCOVERY / "passing.json", limit)

    if not urls:
        logger.error("No URLs found. Use --url-list, --run-dir, or ensure RUN_REVIEW.md/passing.json exist.")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Building Demo Core Collection")
    logger.info("=" * 60)
    logger.info(f"Collection: {args.collection}")
    logger.info(f"URLs: {len(urls)}")
    logger.info(f"Run folder: {selected_run or 'N/A'}")
    logger.info("")

    start_time = time.time()
    max_elapsed = args.max_runtime_minutes * 60
    robots_checker = None if args.no_robots_check else RobotsTxtChecker()

    # Fetch and extract
    documents = []
    failed = []
    for i, url in enumerate(urls, 1):
        if time.time() - start_time > max_elapsed:
            logger.warning("Max runtime reached, stopping fetch")
            break
        logger.info(f"[{i}/{len(urls)}] Fetching: {url[:70]}...")
        doc, reason = fetch_and_extract(url, robots_checker=robots_checker)
        if doc:
            documents.append(doc)
            logger.info(f"  ✅ {doc['text_length']} chars - {doc['title'][:50]}")
        else:
            failed.append({"url": url, "reason": reason or "unknown"})
            logger.warning(f"  ❌ {reason}")

    if not documents:
        logger.error("No documents extracted successfully")
        write_ingest_report(args.report_dir, selected_run, len(urls), [], failed, args.collection, 0)
        sys.exit(1)

    # Embed
    logger.info("")
    logger.info("Initializing embedding model...")
    model, backend = get_embedding_model()
    texts = [f"{doc['title']}\n{doc['text']}" for doc in documents]
    if backend == "fastembed":
        embeddings = np.array(list(model.embed(texts)))
    else:
        embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    if args.dry_run:
        logger.info("DRY RUN: Skipping Qdrant operations")
        write_ingest_report(args.report_dir, selected_run, len(urls), documents, failed, args.collection, 0)
        return

    client = initialize_qdrant_client()
    create_collection(client, args.collection, EMBEDDING_DIM, recreate=args.recreate)

    points = []
    for doc, embedding in zip(documents, embeddings):
        domain = urlparse(doc['url']).netloc
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, doc['url']))
        point = PointStruct(
            id=doc_id,
            vector=embedding.tolist(),
            payload={
                "doc_id": doc_id,
                "title": doc['title'],
                "text": doc['text'],
                "url": doc['url'],
                "domain": domain,
                "source_url": doc['url'],
                "fetched_at": doc['fetched_at'],
                "source_tier": _source_tier(domain),
            },
        )
        points.append(point)

    batch_size = 50
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=args.collection, points=batch)
        logger.info(f"  Upserted batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1} ({len(batch)} points)")

    collection_info = client.get_collection(args.collection)
    write_ingest_report(
        args.report_dir, selected_run, len(urls), documents, failed,
        args.collection, collection_info.points_count,
    )

    domains = {}
    for doc in documents:
        d = urlparse(doc['url']).netloc
        domains[d] = domains.get(d, 0) + 1
    logger.info("")
    logger.info("=" * 60)
    logger.info("Build Complete")
    logger.info("=" * 60)
    logger.info(f"Ingested: {len(documents)} | Failed: {len(failed)} | Points: {collection_info.points_count}")
    for dom, cnt in sorted(domains.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  - {dom}: {cnt}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
