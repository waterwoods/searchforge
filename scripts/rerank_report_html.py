#!/usr/bin/env python3
"""
HTML Report Generator for Rerank Comparison

Generates an HTML report comparing Top-5 results with and without reranking.
Shows rank changes, scores, deltas, and highlighted matched tokens.
"""

import argparse
import base64
import csv
import html
import math
import os
import re
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.search.search_pipeline import SearchPipeline
from modules.rerankers.simple_ce import CrossEncoderReranker
from modules.types import Document, ScoredDocument


def _fmt_ce(score, use_norm: bool):
    """Return display string for CE score; sigmoid when normalized."""
    if score is None:
        return "-"
    if use_norm:
        try:
            val = 1.0 / (1.0 + math.exp(-float(score)))
            return f"{val:.3f} (σ)"
        except Exception:
            return f"{score:.3f}"
    return f"{float(score):.3f}"


def normalize_query_tokens(query: str) -> List[str]:
    """Normalize query tokens: lowercase, split by non-alnum, remove short tokens."""
    tokens = re.findall(r'\b\w+\b', query.lower())
    return [token for token in tokens if len(token) >= 2]


def highlight_tokens(text: str, query_tokens: List[str]) -> str:
    """Highlight matched tokens in text with <mark> tags."""
    if not query_tokens:
        return text
    
    # Create a regex pattern that matches any of the query tokens
    pattern = '|'.join(re.escape(token) for token in query_tokens)
    regex = re.compile(f'\\b({pattern})\\b', re.IGNORECASE)
    
    def replace_func(match):
        return f'<mark>{match.group(0)}</mark>'
    
    return regex.sub(replace_func, text)


def create_snippet(text: str, max_length: int = 160) -> str:
    """Create a snippet from document text, truncating if necessary."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def convert_to_dict(scored_doc: ScoredDocument) -> Dict[str, Any]:
    """Convert ScoredDocument to dictionary format."""
    # Handle different Document types (langchain vs our custom)
    if hasattr(scored_doc.document, 'text'):
        text = scored_doc.document.text
    elif hasattr(scored_doc.document, 'page_content'):
        text = scored_doc.document.page_content
    else:
        text = str(scored_doc.document)
    
    # Extract ID from metadata or use document ID
    doc_id = scored_doc.document.id if hasattr(scored_doc.document, 'id') else scored_doc.document.metadata.get('id', 'unknown')
    
    return {
        'id': doc_id,
        'text': text,
        'score': scored_doc.score,
        'metadata': scored_doc.document.metadata or {}
    }


def search_without_rerank(pipeline: SearchPipeline, query: str, collection_name: str, candidate_k: int) -> List[ScoredDocument]:
    """Search with reranker disabled to get base similarity scores."""
    # Temporarily disable reranker
    original_reranker = pipeline.reranker
    pipeline.reranker = None
    
    # Update retriever config to get more candidates
    original_top_k = pipeline.config.get("retriever", {}).get("top_k", 20)
    pipeline.config["retriever"]["top_k"] = candidate_k
    
    try:
        results = pipeline.search(query, collection_name)
        return results
    finally:
        # Restore original settings
        pipeline.reranker = original_reranker
        pipeline.config["retriever"]["top_k"] = original_top_k


def search_with_rerank(pipeline: SearchPipeline, query: str, collection_name: str, candidate_k: int, rerank_k: int) -> List[ScoredDocument]:
    """Search with reranker enabled."""
    # Get candidates without reranking first
    base_results = search_without_rerank(pipeline, query, collection_name, candidate_k)
    
    if not base_results:
        return []
    
    # Convert to our Document format for reranking
    from modules.types import Document
    docs = []
    for result in base_results:
        # Extract text from different document types
        if hasattr(result.document, 'text'):
            text = result.document.text
        elif hasattr(result.document, 'page_content'):
            text = result.document.page_content
        else:
            text = str(result.document)
        
        # Extract ID
        doc_id = result.document.id if hasattr(result.document, 'id') else result.document.metadata.get('id', 'unknown')
        
        # Create our Document format
        doc = Document(
            id=doc_id,
            text=text,
            metadata=result.document.metadata or {}
        )
        docs.append(doc)
    
    # Apply CrossEncoder reranker
    reranker = CrossEncoderReranker()
    reranked_results = reranker.rerank(query, docs, top_k=rerank_k)
    
    return reranked_results




def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text.lower())


def run_compare_once(query: str, cfg: Dict[str, Any]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Run comparison for a single query and return base, rerank, and diffs."""
    collection_name = cfg.get('collection_name', 'documents')
    candidate_k = cfg.get('candidate_k', 50)
    rerank_k = cfg.get('rerank_k', 50)
    
    # Create pipeline
    pipeline = SearchPipeline(cfg)
    
    # Get results without reranking
    base_results = search_without_rerank(pipeline, query, collection_name, candidate_k)
    base_dict = [convert_to_dict(result) for result in base_results]
    
    # Get results with reranking
    rerank_results = search_with_rerank(pipeline, query, collection_name, candidate_k, rerank_k)
    rerank_dict = [convert_to_dict(result) for result in rerank_results]
    
    # Calculate diffs
    base_rank_map = {result['id']: i + 1 for i, result in enumerate(base_dict)}
    diffs = []
    for i, rerank_result in enumerate(rerank_dict[:5]):
        doc_id = rerank_result['id']
        base_rank = base_rank_map.get(doc_id, "N/A")
        current_rank = i + 1
        base_score = next((r['score'] for r in base_dict if r['id'] == doc_id), 0.0)
        rerank_score = rerank_result['score']
        delta = rerank_score - base_score
        
        diffs.append({
            'id': doc_id,
            'base_rank': base_rank,
            'rerank_rank': current_rank,
            'base_score': base_score,
            'rerank_score': rerank_score,
            'delta': delta,
            'text': rerank_result['text']
        })
    
    return base_dict, rerank_dict, diffs


def run_hybrid_compare_once(query: str, cfg: Dict[str, Any]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Run hybrid vs vector comparison for a single query."""
    collection_name = cfg.get('collection_name', 'documents')
    candidate_k = cfg.get('candidate_k', 50)
    
    # Create vector-only config
    vector_cfg = cfg.copy()
    vector_cfg["retriever"] = {"type": "vector", "top_k": candidate_k}
    vector_pipeline = SearchPipeline(vector_cfg)
    
    # Create hybrid config
    hybrid_cfg = cfg.copy()
    if "retriever" not in hybrid_cfg:
        hybrid_cfg["retriever"] = {}
    hybrid_cfg["retriever"].update({
        "type": "hybrid",
        "alpha": 0.6,
        "vector_top_k": 200,
        "bm25_top_k": 200,
        "top_k": candidate_k
    })
    hybrid_pipeline = SearchPipeline(hybrid_cfg)
    
    # Get vector results
    vector_results = vector_pipeline.search(query, collection_name)
    vector_dict = [convert_to_dict(result) for result in vector_results]
    
    # Get hybrid results
    hybrid_results = hybrid_pipeline.search(query, collection_name)
    hybrid_dict = [convert_to_dict(result) for result in hybrid_results]
    
    # Calculate diffs
    vector_rank_map = {result['id']: i + 1 for i, result in enumerate(vector_dict)}
    diffs = []
    for i, hybrid_result in enumerate(hybrid_dict[:5]):
        doc_id = hybrid_result['id']
        vector_rank = vector_rank_map.get(doc_id, "N/A")
        current_rank = i + 1
        vector_score = next((r['score'] for r in vector_dict if r['id'] == doc_id), 0.0)
        hybrid_score = hybrid_result['score']
        delta = hybrid_score - vector_score
        
        diffs.append({
            'id': doc_id,
            'base_rank': vector_rank,
            'rerank_rank': current_rank,
            'base_score': vector_score,
            'rerank_score': hybrid_score,
            'delta': delta,
            'text': hybrid_result['text']
        })
    
    return vector_dict, hybrid_dict, diffs


def render_query_section(query: str, cfg: Dict[str, Any], prece_mode: bool = False, normalize_ce: bool = False) -> str:
    """Render HTML section for a single query."""
    try:
        print(f"Processing query: {query!r}")
        if prece_mode:
            # In pre-CE mode, only do hybrid vs vector comparison
            vector_top, hybrid_top, diffs = run_hybrid_compare_once(query, cfg)
            base_top = vector_top
            rerank_top = hybrid_top
        else:
            base_top, rerank_top, diffs = run_compare_once(query, cfg)
        
        # Normalize query tokens for highlighting
        query_tokens = normalize_query_tokens(query)
        
        # Check if top-1 changed
        top1_changed = "YES" if (base_top and rerank_top and 
                                base_top[0]['id'] != rerank_top[0]['id']) else "NO"
        
        if prece_mode:
            # Pre-CE mode: Vector vs Hybrid comparison
            html_parts = [
                f'<section id="{slugify(query)}">',
                f'<h2>Query: {html.escape(query)} (pre-CE)',
                f'<span class="summary-badge summary-{"yes" if top1_changed == "YES" else "no"}">',
                f'Vector vs Hybrid: {top1_changed}</span></h2>',
                '<table>',
                '<thead><tr>',
                '<th>Rank(Vector→Hybrid)</th>',
                '<th>Doc ID</th>',
                '<th>Snippet</th>',
                '<th>Vector Score</th>',
                '<th>Hybrid Score</th>',
                '<th>ΔScore</th>',
                '</tr></thead>',
                '<tbody>'
            ]
        else:
            # Normal mode: Base vs Rerank comparison
            html_parts = [
                f'<section id="{slugify(query)}">',
                f'<h2>Query: {html.escape(query)}',
                f'<span class="summary-badge summary-{"yes" if top1_changed == "YES" else "no"}">',
                f'Top-1 changed: {top1_changed}</span></h2>',
                '<table>',
                '<thead><tr>',
                '<th>Rank(before→after)</th>',
                '<th>Doc ID</th>',
                '<th>Snippet</th>',
                '<th>Pre-CE Score</th>',
                '<th>CE Score</th>',
                '<th>ΔScore</th>',
                '</tr></thead>',
                '<tbody>'
            ]
        
        for diff in diffs[:5]:  # Top-5 only
            # Format rank change
            if diff['base_rank'] != "N/A":
                rank_change = f"{diff['base_rank']} → {diff['rerank_rank']}"
            else:
                rank_change = f"N/A → {diff['rerank_rank']}"
            
            # Create snippet with highlighting
            snippet = create_snippet(diff['text'])
            highlighted_snippet = highlight_tokens(snippet, query_tokens)
            
            # Format delta
            delta_class = "delta-positive" if diff['delta'] > 0 else "delta-negative" if diff['delta'] < 0 else ""
            delta_str = f"{diff['delta']:+.3f}" if diff['delta'] != 0 else "0.000"
            
            html_parts.extend([
                '<tr>',
                f'<td class="rank-change">{rank_change}</td>',
                f'<td class="doc-id">{diff["id"]}</td>',
                f'<td class="snippet">{highlighted_snippet}</td>',
                f'<td class="score">{_fmt_ce(diff["base_score"], False)}</td>',
                f'<td class="score">{_fmt_ce(diff["rerank_score"], normalize_ce)}</td>',
                f'<td class="score {delta_class}">{delta_str}</td>',
                '</tr>'
            ])
        
        html_parts.extend(['</tbody>', '</table>'])
        
        # Add hybrid vs vector comparison only in normal mode (not pre-CE)
        if not prece_mode:
            try:
                vector_top, hybrid_top, hybrid_diffs = run_hybrid_compare_once(query, cfg)
                
                # Check if top-1 changed in hybrid
                hybrid_top1_changed = "YES" if (vector_top and hybrid_top and 
                                               vector_top[0]['id'] != hybrid_top[0]['id']) else "NO"
                
                html_parts.extend([
                    f'<h3>Hybrid vs Vector Comparison',
                    f'<span class="summary-badge summary-{"yes" if hybrid_top1_changed == "YES" else "no"}">',
                    f'Hybrid ON/OFF: {hybrid_top1_changed}</span></h3>',
                    '<table>',
                    '<thead><tr>',
                    '<th>Rank(Vector→Hybrid)</th>',
                    '<th>Doc ID</th>',
                    '<th>Snippet</th>',
                    '<th>Vector Score</th>',
                    '<th>Hybrid Score</th>',
                    '<th>ΔScore</th>',
                    '</tr></thead>',
                    '<tbody>'
                ])
                
                for diff in hybrid_diffs[:5]:  # Top-5 only
                    # Format rank change
                    if diff['base_rank'] != "N/A":
                        rank_change = f"{diff['base_rank']} → {diff['rerank_rank']}"
                    else:
                        rank_change = f"N/A → {diff['rerank_rank']}"
                    
                    # Create snippet with highlighting
                    snippet = create_snippet(diff['text'])
                    highlighted_snippet = highlight_tokens(snippet, query_tokens)
                    
                    # Format delta
                    delta_class = "delta-positive" if diff['delta'] > 0 else "delta-negative" if diff['delta'] < 0 else ""
                    delta_str = f"{diff['delta']:+.3f}" if diff['delta'] != 0 else "0.000"
                    
                    html_parts.extend([
                        '<tr>',
                        f'<td class="rank-change">{rank_change}</td>',
                        f'<td class="doc-id">{diff["id"]}</td>',
                        f'<td class="snippet">{highlighted_snippet}</td>',
                        f'<td class="score">{diff["base_score"]:.3f}</td>',
                        f'<td class="score">{diff["rerank_score"]:.3f}</td>',
                        f'<td class="score {delta_class}">{delta_str}</td>',
                        '</tr>'
                    ])
                
                html_parts.extend(['</tbody>', '</table>'])
                
            except Exception as e:
                html_parts.append(f'<p class="error">Hybrid comparison error: {html.escape(str(e))}</p>')
        
        html_parts.append('</section>')
        
        print(f"  Base results: {len(base_top)}, Rerank results: {len(rerank_top)}")
        return '\n'.join(html_parts)
        
    except Exception as e:
        print(f"  Error processing query '{query}': {e}")
        return f'<section id="{slugify(query)}"><h2>Query: {html.escape(query)}</h2><p class="error">Error: {html.escape(str(e))}</p></section>'


def render_sweep_section(sweep_dir: Path) -> str:
    """Render sweep analysis section if data exists."""
    if not sweep_dir.exists():
        return ""
    
    # Check for combined chart
    combined_chart = sweep_dir / "sweep_combined.png"
    if not combined_chart.exists():
        return ""
    
    # Encode chart as base64
    with open(combined_chart, 'rb') as f:
        chart_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Check for CSV metrics
    csv_path = sweep_dir / "sweep_metrics.csv"
    metrics_table = ""
    if csv_path.exists():
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if rows:
                # Check if we have the new format with p50/p95/p99 columns
                has_new_format = 'p50_ms' in reader.fieldnames and 'p99_ms' in reader.fieldnames
                
                metrics_table = "<h3>Parameter Sweep Metrics</h3><table><thead><tr>"
                metrics_table += "<th>Candidate K</th><th>Rerank K</th>"
                
                if has_new_format:
                    metrics_table += "<th>P50 (ms)</th><th>P95 (ms)</th><th>P99 (ms)</th>"
                    metrics_table += "<th>Top-1 Rate</th><th>Recall@10 (%)</th>"
                else:
                    # Fallback to old format
                    metrics_table += "<th>P95 (ms)</th><th>Top-1 Changed (%)</th><th>Recall@10 (%)</th>"
                
                metrics_table += "</tr></thead><tbody>"
                
                for row in rows:
                    metrics_table += f"<tr><td>{row['candidate_k']}</td><td>{row['rerank_k']}</td>"
                    
                    if has_new_format:
                        # New format with error bars
                        p50 = f"{float(row['p50_ms']):.1f}" if row['p50_ms'] != 'nan' else "N/A"
                        p95 = f"{float(row['p95_ms']):.1f}" if row['p95_ms'] != 'nan' else "N/A"
                        p99 = f"{float(row['p99_ms']):.1f}" if row['p99_ms'] != 'nan' else "N/A"
                        top1 = f"{float(row['top1_rate']) * 100:.1f}" if row['top1_rate'] != 'nan' else "N/A"
                        recall = f"{float(row['recall_at10']) * 100:.1f}" if row['recall_at10'] != 'nan' else "N/A"
                        
                        metrics_table += f"<td>{p50}</td><td>{p95}</td><td>{p99}</td>"
                        metrics_table += f"<td>{top1}</td><td>{recall}</td>"
                    else:
                        # Old format fallback
                        p95 = f"{float(row['p95_ms']):.1f}" if row['p95_ms'] != 'nan' else "N/A"
                        top1 = f"{float(row['top1_change_rate']) * 100:.1f}" if row['top1_change_rate'] != 'nan' else "N/A"
                        recall = f"{float(row['recall_at10']) * 100:.1f}" if row['recall_at10'] != 'nan' else "N/A"
                        
                        metrics_table += f"<td>{p95}</td><td>{top1}</td><td>{recall}</td>"
                    
                    metrics_table += "</tr>"
                
                metrics_table += "</tbody></table>"
        except Exception as e:
            print(f"Warning: Could not read sweep metrics CSV: {e}")
    
    return f"""
    <section id="sweep_analysis">
        <h2>Effect vs Performance Analysis</h2>
        <p>Parameter sweep analysis showing the trade-offs between latency, effectiveness, and quality across different candidate and rerank settings. Charts show P95 latency with P50-P99 error bands.</p>
        <div style="text-align: center; margin: 20px 0;">
            <img src="data:image/png;base64,{chart_data}" alt="Parameter Sweep Analysis (P95 with P50-P99 band)" style="max-width: 100%; height: auto;">
        </div>
        {metrics_table}
    </section>
    """


def main():
    parser = argparse.ArgumentParser(description='Generate HTML report comparing rerank results')
    parser.add_argument('--config', help='Path to YAML config file')
    parser.add_argument('--collection', help='Collection name to search')
    parser.add_argument('--candidate_k', type=int, help='Number of candidates to fetch')
    parser.add_argument('--rerank_k', type=int, help='Number of candidates to rerank')
    parser.add_argument('--output', default='reports/rerank_html', help='Output directory for HTML report')
    parser.add_argument('--queries', nargs='+', required=True, help='one or more queries')
    parser.add_argument('--sweep-dir', default='reports/rerank_html/sweep', help='Directory containing sweep analysis results')
    parser.add_argument('--prece', action='store_true', help='Skip cross-encoder rerank; compare Vector vs Hybrid candidates only')
    parser.add_argument('--normalize-ce', action='store_true',
                        help='Display CE scores with sigmoid for readability (does not change ranking)')
    
    args = parser.parse_args()
    
    # Load and override config
    cfg = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                cfg = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    # Apply CLI overrides
    if args.collection:
        cfg["collection_name"] = args.collection
    if args.candidate_k:
        cfg["candidate_k"] = args.candidate_k
    if args.rerank_k:
        cfg["rerank_k"] = args.rerank_k
    
    # Create output directory
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp and output path
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out_path = out_dir / f"report_{ts}.html"
    
    # Process queries and build sections
    sections = []
    toc = []
    
    for q in args.queries:
        sections.append(render_query_section(q, cfg, args.prece, args.normalize_ce))
        toc.append(f'<li><a href="#{slugify(q)}">{html.escape(q)}</a></li>')
    
    # Add sweep analysis section if available
    sweep_dir = Path(args.sweep_dir)
    sweep_section = render_sweep_section(sweep_dir)
    if sweep_section:
        sections.append(sweep_section)
        toc.append('<li><a href="#sweep_analysis">Effect vs Performance Analysis</a></li>')
    
    # Inline CSS
    INLINE_CSS = """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }
        h2 { color: #007acc; margin-top: 30px; }
        h3 { color: #0056b3; margin-top: 20px; }
        .summary-badge { display: inline-block; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; margin-left: 10px; }
        .summary-yes { background: #d4edda; color: #155724; }
        .summary-no { background: #f8d7da; color: #721c24; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: bold; color: #333; }
        .rank-change { font-weight: bold; color: #007acc; }
        .score { font-family: monospace; font-size: 13px; }
        .delta-positive { color: #28a745; font-weight: bold; }
        .delta-negative { color: #dc3545; font-weight: bold; }
        .snippet { max-width: 400px; line-height: 1.4; }
        mark { background: #ffeb3b; padding: 1px 2px; border-radius: 2px; }
        .doc-id { font-family: monospace; font-size: 12px; color: #666; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 5px; }
        ol { margin: 20px 0; }
        li { margin: 5px 0; }
        a { color: #007acc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    """
    
    # Assemble final HTML
    title_suffix = " (pre-CE)" if args.prece else ""
    html_content = f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rerank Report ({ts}){title_suffix}</title>
    <style>{INLINE_CSS}</style>
</head>
<body>
    <div class="container">
        <h1>Rerank Comparison Report{title_suffix}</h1>
        <p><b>Collection:</b> {html.escape(cfg.get('collection_name',''))} ·
           <b>candidate_k:</b> {cfg.get('candidate_k')} ·
           <b>rerank_k:</b> {cfg.get('rerank_k')}</p>
        <h2>Queries</h2>
        <ol>{"".join(toc)}</ol>
        {"".join(sections)}
    </div>
</body>
</html>"""
    
    # Write the file
    out_path.write_text(html_content, encoding="utf-8")
    print(f"HTML report generated: {out_path}")


if __name__ == "__main__":
    main()
