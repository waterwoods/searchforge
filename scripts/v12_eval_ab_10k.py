#!/usr/bin/env python3

import argparse
import json
import time
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchText
from sentence_transformers import SentenceTransformer
import numpy as np


def tokenize(s: str) -> List[str]:
    return [t for t in ''.join(ch.lower() if ch.isalnum() else ' ' for ch in s).split() if t]

class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
    def build(self, docs: List[str]):
        self.N = len(docs)
        self.docs = docs
        self.toks = [tokenize(x) for x in docs]
        self.doc_len = [len(t) for t in self.toks]
        self.avgdl = sum(self.doc_len) / max(1, self.N)
        df = Counter()
        for ts in self.toks:
            df.update(set(ts))
        self.idf = {t: np.log((self.N - df[t] + 0.5) / (df[t] + 0.5) + 1.0) for t in df}
        self.tf = [Counter(ts) for ts in self.toks]
        self.postings = defaultdict(list)
        for i, ts in enumerate(self.toks):
            for t in set(ts):
                self.postings[t].append(i)
    def search(self, query: str, topk: int = 40) -> List[Tuple[int, float]]:
        q = tokenize(query)
        cand = set()
        for t in q:
            cand.update(self.postings.get(t, []))
        if not cand:
            return []
        scores = {}
        for i in cand:
            dl = self.doc_len[i] or 1
            K = self.k1 * (1 - self.b + self.b * dl / max(1, self.avgdl))
            s = 0.0
            tf_i = self.tf[i]
            for t in q:
                if t in tf_i and t in self.idf:
                    f = tf_i[t]
                    s += self.idf[t] * (f * (self.k1 + 1)) / (f + K)
            scores[i] = s
        items = list(scores.items())
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:topk]


def rrf_fuse(a: List[Tuple[int, float]], b: List[Tuple[int, float]], k: int = 40) -> List[Tuple[int, float]]:
    rank_a = {doc: i for i, (doc, _) in enumerate(a)}
    rank_b = {doc: i for i, (doc, _) in enumerate(b)}
    docs = set(rank_a) | set(rank_b)
    fused = []
    for d in docs:
        ra = rank_a.get(d, 10**9)
        rb = rank_b.get(d, 10**9)
        score = 1.0 / (k + ra) + 1.0 / (k + rb)
        fused.append((d, score))
    fused.sort(key=lambda x: x[1], reverse=True)
    return fused


def recall_at_10(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
    if not relevant_ids:
        return 0.0
    R = set(str(x) for x in relevant_ids)
    H = set(str(x) for x in retrieved_ids[:10])
    return len(R & H) / min(10, len(R))


def load_corpus(path: str) -> Tuple[List[str], List[str]]:
    texts, ids = [], []
    with open(path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            ids.append(str(obj.get('doc_id')))
            texts.append(((obj.get('title') or '') + ' ' + (obj.get('abstract') or obj.get('text') or '')).strip())
    return texts, ids


def load_queries(path: str) -> List[Dict[str,str]]:
    qs = []
    with open(path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            qs.append({'id': str(obj.get('id')), 'text': obj.get('text', '')})
    return qs


def load_qrels(path: str) -> Dict[str, List[str]]:
    M = {}
    with open(path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            M[str(obj.get('query_id'))] = [str(x) for x in obj.get('relevant_doc_ids', [])]
    return M


def vector_search(client: QdrantClient, collection: str, vec: List[float], top_k: int) -> List[str]:
    res = client.search(collection_name=collection, query_vector=vec, limit=top_k, with_payload=True)
    return [str(p.payload.get('doc_id')) for p in res]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--collection', default='fiqa_10k_v1')
    ap.add_argument('--corpus', default='data/fiqa_v1/corpus_10k_v1.fixed.jsonl')
    ap.add_argument('--queries', default='data/fiqa_v1/fiqa_10k_v1/queries.jsonl')
    ap.add_argument('--qrels', default='data/fiqa_v1/fiqa_qrels_10k_v1.jsonl')
    ap.add_argument('--sample', type=int, default=500)
    ap.add_argument('--rrf_k', type=int, default=40)
    ap.add_argument('--top_k', type=int, default=10)
    args = ap.parse_args()

    texts, ids = load_corpus(args.corpus)
    bm25 = BM25Index(); bm25.build(texts)

    qs = load_queries(args.queries)
    qrels = load_qrels(args.qrels)
    if args.sample and len(qs) > args.sample:
        qs = qs[:args.sample]

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    client = QdrantClient(host='localhost', port=6333)

    lat_v = []
    lat_h = []
    rec_v = []
    rec_h = []

    for q in qs:
        rel = qrels.get(q['id'], [])
        t0 = time.perf_counter()
        v = model.encode(q['text']).tolist()
        vec_ids = vector_search(client, args.collection, v, top_k=max(args.top_k, 40))
        t1 = time.perf_counter()
        lat_v.append((t1 - t0) * 1000)
        rec_v.append(recall_at_10(vec_ids, rel))

        # Hybrid: BM25 + vector via RRF
        bres = bm25.search(q['text'], topk=40)
        # Map BM25 indices to doc_ids
        bm25_ids = [ids[i] for i, _ in bres]
        # Build position lists
        a = [(i, 1.0) for i, _ in enumerate(vec_ids)]
        b = [(ids.index(did), 1.0) for did in bm25_ids]  # ids.index O(N), but small 10k
        fused = rrf_fuse(a, b, k=args.rrf_k)
        fused_sorted = sorted(fused, key=lambda x: x[1], reverse=True)
        top_ids = [ids[i] for i, _ in fused_sorted[:args.top_k]]
        t2 = time.perf_counter()
        lat_h.append((t2 - t0) * 1000)
        rec_h.append(recall_at_10(top_ids, rel))

    import statistics
    def p95(xs):
        ys = sorted(xs)
        return ys[int(0.95 * (len(ys)-1))] if ys else 0.0

    print('\nA/B (sample={}):'.format(len(qs)))
    print('Baseline vector-only: Recall@10={:.4f}, p95(ms)={:.1f}'.format(sum(rec_v)/len(rec_v), p95(lat_v)))
    print('+RRF hybrid:         Recall@10={:.4f}, p95(ms)={:.1f}'.format(sum(rec_h)/len(rec_h), p95(lat_h)))

if __name__ == '__main__':
    main()



