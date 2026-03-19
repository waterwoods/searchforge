#!/usr/bin/env python3
"""
Fetch and extract readable text from a single webpage.
Outputs: raw.html and extracted.txt
"""

import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

# Configuration
OUTPUT_DIR = Path.home() / "searchforge" / "results" / "openclaw_demo"
TARGET_CONFIG = OUTPUT_DIR / "target.json"

def main():
    # Load target URL
    if not TARGET_CONFIG.exists():
        print(f"ERROR: Target config not found: {TARGET_CONFIG}", file=sys.stderr)
        sys.exit(1)
    
    with open(TARGET_CONFIG) as f:
        config = json.load(f)
    target_url = config["target_url"]
    
    print(f"Fetching: {target_url}")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Fetch with proper User-Agent
    req = urllib.request.Request(
        target_url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                print(f"ERROR: Expected text/html, got: {content_type}", file=sys.stderr)
                sys.exit(1)
            
            html_content = response.read()
            final_url = response.url
            
    except Exception as e:
        print(f"ERROR: Failed to fetch: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Save raw HTML
    raw_html_path = OUTPUT_DIR / "raw.html"
    with open(raw_html_path, "wb") as f:
        f.write(html_content)
    print(f"Saved raw HTML: {raw_html_path}")
    
    # Extract readable text
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remove script, style, nav, header, footer elements
    for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
        element.decompose()
    
    # Get title
    title = soup.title.string if soup.title else "No title"
    
    # Extract main content (prefer main, article, or body)
    main_content = None
    for selector in ["main", "article", "[role='main']", "body"]:
        main_content = soup.select_one(selector)
        if main_content:
            break
    
    if not main_content:
        main_content = soup.body if soup.body else soup
    
    # Get text
    text = main_content.get_text(separator="\n", strip=True)
    
    # Clean up excessive whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    cleaned_text = "\n".join(lines)
    
    # Save extracted text
    extracted_path = OUTPUT_DIR / "extracted.txt"
    with open(extracted_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    
    # Print stats
    char_count = len(cleaned_text)
    print(f"Extracted: {char_count:,} characters")
    print(f"Title: {title}")
    print(f"Final URL: {final_url}")
    print(f"Saved extracted text: {extracted_path}")
    
    if char_count < 100:
        print("WARNING: Extracted text is very short", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
