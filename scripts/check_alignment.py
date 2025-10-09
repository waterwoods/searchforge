import argparse, json, random, time
from typing import List, Dict, Set
from modules.search.search_pipeline import SearchPipeline
from modules.types import ScoredDocument
import os

def extract_doc_id(res: ScoredDocument) -> str:
    # 优先 payload.doc_id → 再退回 document.id
    md = getattr(res.document, "metadata", None) or {}
    if "doc_id" in md and md["doc_id"] is not None:
        return str(md["doc_id"])
    return str(getattr(res.document, "id", ""))

def load_beir_scifact() -> (Dict[str,str], Dict[str,Dict[str,int]]):
    # 使用 BEIR 官方加载（queries: dict[qid]=text, qrels: dict[qid]={docid:rel}}
    from beir import util, LoggingHandler
    from beir.datasets.data_loader import GenericDataLoader
    import logging
    logging.getLogger("beir").setLevel(logging.ERROR)
    data_path = util.download_and_unzip("https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip", "./data/")
    corpus, queries, qrels = GenericDataLoader(data_folder=data_path).load(split="test")
    # 返回 (queries, qrels)
    return queries, qrels

def load_beir_fiqa() -> (Dict[str,str], Dict[str,Dict[str,int]]):
    # 使用 BEIR 官方加载 FiQA（queries: dict[qid]=text, qrels: dict[qid]={docid:rel}}
    from beir import util, LoggingHandler
    from beir.datasets.data_loader import GenericDataLoader
    import logging
    logging.getLogger("beir").setLevel(logging.ERROR)
    data_path = util.download_and_unzip("https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/fiqa.zip", "./data/")
    corpus, queries, qrels = GenericDataLoader(data_folder=data_path).load(split="test")
    # 返回 (queries, qrels)
    return queries, qrels

def load_gold_jsonl(path: str):
    # 兼容本地 gold：每行 {"query": "...", "positive_ids": ["...","..."]}
    queries = {}
    qrels = {}
    with open(path, "r") as f:
        for i, line in enumerate(f):
            obj = json.loads(line)
            qid = str(i)
            queries[qid] = obj["query"]
            qrels[qid] = {str(x): 1 for x in obj.get("positive_ids", [])}
    return queries, qrels

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="pipeline yaml (vector/hybrid)")
    ap.add_argument("--collection", required=True, help="Qdrant collection name")
    ap.add_argument("--beir", choices=["scifact", "fiqa"], help="use BEIR built-in gold/qrels")
    ap.add_argument("--gold", help="optional local gold jsonl")
    ap.add_argument("--candidate_k", type=int, default=1000)
    ap.add_argument("--show_first", type=int, default=5)
    args = ap.parse_args()

    # 1) 构建 pipeline，强制关闭 reranker（只看候选覆盖）
    pipe = SearchPipeline.from_config(args.config)
    if hasattr(pipe, "reranker"):
        pipe.reranker = None

    # 2) 载入 gold
    if args.beir == "scifact":
        queries, qrels = load_beir_scifact()
    elif args.beir == "fiqa":
        queries, qrels = load_beir_fiqa()
    elif args.gold:
        queries, qrels = load_gold_jsonl(args.gold)
    else:
        raise SystemExit("Must provide --beir scifact or --gold gold.jsonl")

    # 3) Qdrant 抽样自检：payload.doc_id 存在性
    try:
        from qdrant_client import QdrantClient
        qc = QdrantClient(url=os.environ.get("QDRANT_URL","http://localhost:6333"))
        sample = qc.scroll(collection_name=args.collection, limit=20, with_payload=True)[0]
        missing = sum(1 for p in sample if not p.payload or ("doc_id" not in p.payload))
        print(f"[DOC-ID CHECK] sample=20, missing_payload.doc_id={missing}")
    except Exception as e:
        print(f"[DOC-ID CHECK] skipped ({type(e).__name__}: {e})")

    # 4) 覆盖率检测
    qids = list(queries.keys())
    shown = 0
    cover_hits_total, cover_total = 0, 0

    for qid in qids:
        qtext = queries[qid]
        gold_ids: Set[str] = set(qrels.get(qid, {}).keys())
        if not gold_ids:
            continue

        t0 = time.perf_counter()
        results: List[ScoredDocument] = pipe.search(qtext, collection_name=args.collection, candidate_k=args.candidate_k)
        dt_ms = (time.perf_counter() - t0) * 1000

        cand_ids = [extract_doc_id(r) for r in results]
        cand_set = set(cand_ids)
        inter = sorted(list(gold_ids & cand_set))[:10]

        cover_hits_total += len(gold_ids & cand_set)
        cover_total += len(gold_ids)

        if shown < args.show_first:
            print("──")
            print(f"Q[{qid}] {qtext[:80]} ...")
            print(f"  gold_ids({len(gold_ids)}): {sorted(list(gold_ids))[:10]}{' ...' if len(gold_ids)>10 else ''}")
            print(f"  cand@{args.candidate_k}({len(cand_ids)}): {cand_ids[:10]}{' ...' if len(cand_ids)>10 else ''}")
            print(f"  INTERSECTION({len(inter)}): {inter}")
            print(f"  COVER: {len(gold_ids & cand_set)}/{len(gold_ids)}  | latency={dt_ms:.1f}ms")
            shown += 1

    cover_rate = (cover_hits_total / cover_total) if cover_total else 0.0
    print("== SUMMARY ==")
    print(f"Candidate-K={args.candidate_k}, queries_with_gold={cover_total>0}")
    print(f"Macro COVER = {cover_rate:.3f}  ({cover_hits_total}/{cover_total})")
    print("If COVER ≪ expected, check payload.doc_id mapping or corpus/qrels split alignment.")

if __name__ == "__main__":
    main()
