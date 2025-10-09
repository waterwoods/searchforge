#!/usr/bin/env python3
import os, argparse, re, sys
from typing import List, Tuple

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.rerankers.factory import create_reranker
from modules.types import ScoredDocument, Document, QueryResult
from modules.search.search_pipeline import SearchPipeline
from modules.search.vector_search import VectorSearch

DEFAULT_QUERIES = [
    "fast usb c cable charging",
    "wireless charger pad",
    "usb c hub adapter"
]

def highlight_matches(text: str, query: str) -> str:
    tokens = [t for t in re.split(r"[^a-z0-9]+", query.lower()) if t]
    out = text
    for t in set(tokens):
        out = re.sub(fr"(?i)\b({re.escape(t)})\b", r"[\1]", out)
    return out

def topN(docs: List[ScoredDocument], n:int=5) -> List[ScoredDocument]:
    return sorted(docs, key=lambda x: x.score, reverse=True)[:n]

def as_rows(tag: str, items: List[ScoredDocument], query: str) -> List[Tuple[int,float,str]]:
    rows = []
    for idx, sd in enumerate(items, 1):
        txt = sd.document.text if isinstance(sd.document, Document) else str(sd.document)
        rows.append((idx, sd.score, highlight_matches(txt[:140], query)))
    return rows

def print_table(title: str, rows, extra=None):
    print(f"\n== {title} ==")
    if extra: print(extra)
    print(f"{'#':>2} | {'score':>9} | text")
    print("-"*80)
    for r in rows:
        print(f"{r[0]:>2} | {r[1]:>9.3f} | {r[2]}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/demo_rerank.yaml")
    p.add_argument("--collection", default=None, help="override retriever.collection_name")
    p.add_argument("--candidate_k", type=int, default=50, help="retriever top_k candidates")
    p.add_argument("--rerank_k", type=int, default=50, help="reranker top_k")
    p.add_argument("--model", default="cross-encoder/ms-marco-MiniLM-L-6-v2")
    p.add_argument("--queries", nargs="*", default=DEFAULT_QUERIES)
    args = p.parse_args()

    # Cache dirs (no network surprises if you have a local cache)
    os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", os.path.expanduser("~/.cache/huggingface"))
    os.environ.setdefault("TRANSFORMERS_CACHE", os.path.expanduser("~/.cache/huggingface"))

    pipe = SearchPipeline.from_config(args.config)
    # runtime overrides
    if args.collection and hasattr(pipe, "retriever") and hasattr(pipe.retriever, "config"):
        pipe.retriever.config["collection_name"] = args.collection
    if hasattr(pipe, "retriever") and hasattr(pipe.retriever, "config"):
        pipe.retriever.config["top_k"] = args.candidate_k

    # Build rerankers
    fake_cfg = {"type": "fake", "top_k": args.rerank_k}
    real_cfg = {"type": "cross_encoder", "model": args.model, "top_k": args.rerank_k}
    fake = create_reranker(fake_cfg)
    real = create_reranker(real_cfg)

    for q in args.queries:
        print("\n" + "="*100)
        print(f"Query: {q}")

        # Step 1: get base candidates (NO rerank). We use pipeline internal retrieval.
        # We need to access the vector search directly to get base candidates
        retriever_cfg = pipe.config.get("retriever", {})
        collection_name = args.collection or retriever_cfg.get("collection_name", "documents")
        
        # Use vector search directly to get base candidates without reranking
        vector_search = VectorSearch()
        base_results = vector_search.vector_search(
            query=q,
            collection_name=collection_name,
            top_n=args.candidate_k
        )
        
        # Convert to ScoredDocument format if needed
        base_scored = []
        for i, result in enumerate(base_results):
            if hasattr(result, 'document') and hasattr(result, 'score'):
                # Check if it's our custom Document or LangChain Document
                doc = result.document
                if hasattr(doc, 'text'):
                    # Our custom Document
                    base_scored.append(result)
                elif hasattr(doc, 'page_content'):
                    # LangChain Document - convert to our format
                    custom_doc = Document(
                        id=str(getattr(doc, 'id', f'base_{i}')),
                        text=doc.page_content,
                        metadata=getattr(doc, 'metadata', {})
                    )
                    base_scored.append(ScoredDocument(
                        document=custom_doc,
                        score=result.score,
                        explanation=result.explanation or f"Vector search result #{i+1}"
                    ))
                else:
                    # Fallback
                    base_scored.append(result)
            elif hasattr(result, 'content') and hasattr(result, 'score'):
                content = result.content
                if hasattr(content, 'page_content'):
                    content_text = content.page_content
                else:
                    content_text = str(content)
                
                doc = Document(
                    id=str(getattr(result, 'id', f'base_{i}')),
                    text=content_text,
                    metadata=getattr(result, 'metadata', {})
                )
                base_scored.append(ScoredDocument(
                    document=doc,
                    score=result.score,
                    explanation=f"Vector search result #{i+1}"
                ))
        
        base_top = topN(base_scored, 5)
        print_table("Base (vector-only)", as_rows("base", base_top, q),
                    extra=f"collection={collection_name}  candidates_k={args.candidate_k}")

        # Prepare documents list for rerankers
        docs_for_rerank = [sd.document for sd in base_scored]

        # Step 2: Fake rerank
        fake_ranked = fake.rerank(q, docs_for_rerank)
        fake_top = topN(fake_ranked, 5)
        print_table("FakeReranker Top-5", as_rows("fake", fake_top, q))

        # Step 3: Real cross-encoder rerank
        real_ranked = real.rerank(q, docs_for_rerank, top_k=args.rerank_k)
        real_top = topN(real_ranked, 5)
        print_table("CrossEncoder Top-5", as_rows("real", real_top, q))

        # Diff summary
        def ids(xs): return [getattr(d.document, "id", str(i)) for i, d in enumerate(xs)]
        print("\nDiff (top-5 ids):")
        print(" base :", ids(base_top))
        print(" fake :", ids(fake_top))
        print(" real :", ids(real_top))

if __name__ == "__main__":
    main()
