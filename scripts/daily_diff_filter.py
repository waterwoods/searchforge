#!/usr/bin/env python3
"""
Daily Diff Filter
=================
Filters out documents that haven't changed since yesterday's crawl.
Compares source_url + content_hash to detect duplicates.
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Set, Dict, List
from datetime import datetime, timedelta

def hash_content(title: str, text: str) -> str:
    """Generate content hash from title and text"""
    content = f"{title}{text[:500]}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def load_yesterday_hashes(yesterday_path: Path) -> Set[str]:
    """Load source_url:content_hash pairs from yesterday's corpus"""
    hashes = set()
    if not yesterday_path.exists():
        return hashes
    
    try:
        with open(yesterday_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                    source_url = doc.get("source_url", "")
                    title = doc.get("title", "")
                    text = doc.get("text", "")
                    content_hash = hash_content(title, text)
                    hash_key = f"{source_url}:{content_hash}"
                    hashes.add(hash_key)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"WARNING: Failed to load yesterday's corpus: {e}", file=sys.stderr)
    
    return hashes

def filter_corpus(today_path: Path, yesterday_path: Path, output_path: Path) -> Dict:
    """Filter today's corpus, removing unchanged documents"""
    yesterday_hashes = load_yesterday_hashes(yesterday_path)
    
    total_docs = 0
    filtered_docs = 0
    unchanged_docs = 0
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(today_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            line = line.strip()
            if not line:
                continue
            
            try:
                doc = json.loads(line)
                total_docs += 1
                
                source_url = doc.get("source_url", "")
                title = doc.get("title", "")
                text = doc.get("text", "")
                content_hash = hash_content(title, text)
                hash_key = f"{source_url}:{content_hash}"
                
                if hash_key in yesterday_hashes:
                    unchanged_docs += 1
                    continue
                
                # New or changed document
                outfile.write(line + '\n')
                filtered_docs += 1
                
            except json.JSONDecodeError as e:
                print(f"WARNING: Skipping invalid JSON: {e}", file=sys.stderr)
                continue
    
    return {
        "total_documents": total_docs,
        "unchanged_documents": unchanged_docs,
        "filtered_documents": filtered_docs,
        "filter_rate": unchanged_docs / total_docs if total_docs > 0 else 0.0
    }

def main():
    if len(sys.argv) < 3:
        print("Usage: daily_diff_filter.py <today_corpus.jsonl> <yesterday_corpus.jsonl> <output.jsonl>", file=sys.stderr)
        sys.exit(1)
    
    today_path = Path(sys.argv[1])
    yesterday_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    
    if not today_path.exists():
        print(f"ERROR: Today's corpus not found: {today_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Filtering corpus:")
    print(f"  Today: {today_path}")
    print(f"  Yesterday: {yesterday_path}")
    print(f"  Output: {output_path}")
    
    stats = filter_corpus(today_path, yesterday_path, output_path)
    
    print(f"\nFilter statistics:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Unchanged (filtered out): {stats['unchanged_documents']}")
    print(f"  New/changed (kept): {stats['filtered_documents']}")
    print(f"  Filter rate: {stats['filter_rate']:.1%}")
    
    if stats['total_documents'] == 0:
        print("WARNING: No documents processed", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
