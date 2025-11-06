#!/usr/bin/env python3

import argparse
import json
import os
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


def load_corpus(path: str) -> List[Dict[str, Any]]:
    docs = []
    with open(path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            doc_id = str(obj.get('doc_id'))
            title = obj.get('title', '') or ''
            text = obj.get('abstract') or obj.get('text') or ''
            docs.append({'doc_id': doc_id, 'title': title, 'text': text})
    return docs


def ensure_collection(client: QdrantClient, name: str, dim: int, recreate: bool) -> None:
    if recreate:
        try:
            client.delete_collection(name)
        except Exception:
            pass
    client.recreate_collection(collection_name=name, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))


def embed_documents(model: SentenceTransformer, docs: List[Dict[str, Any]], fields: str) -> List[List[float]]:
    contents = []
    for d in docs:
        if fields == 'title+text':
            contents.append((d['title'] + ' ' + d['text']).strip())
        elif fields == 'text':
            contents.append(d['text'])
        elif fields == 'title':
            contents.append(d['title'])
        else:
            contents.append((d['title'] + ' ' + d['text']).strip())
    return model.encode(contents, show_progress_bar=True, batch_size=512, normalize_embeddings=False).tolist()


def upsert(client: QdrantClient, name: str, docs: List[Dict[str, Any]], vectors: List[List[float]], batch_size: int = 512) -> None:
    points: List[PointStruct] = []
    for i, (d, v) in enumerate(zip(docs, vectors)):
        pid = i + 1
        points.append(PointStruct(id=pid, vector=v, payload={'doc_id': d['doc_id'], 'title': d['title'], 'text': d['text']}))
    for i in tqdm(range(0, len(points), batch_size), desc='Upserting'):
        client.upsert(collection_name=name, points=points[i:i+batch_size], wait=True)


def sample_ids(client: QdrantClient, name: str, k: int = 10) -> List[str]:
    res = client.scroll(collection_name=name, limit=k, with_payload=True)
    pts = res[0]
    return [str(p.payload.get('doc_id')) for p in pts]


def collection_doc_ids(client: QdrantClient, name: str) -> set:
    ids = set()
    offset = None
    while True:
        points, offset = client.scroll(collection_name=name, limit=1000, offset=offset, with_payload=True)
        for p in points:
            d = p.payload.get('doc_id')
            if d is not None:
                ids.add(int(str(d)))
        if offset is None or not points:
            break
    return ids


def load_qrels_ids(path: str) -> set:
    Q = set()
    with open(path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            for d in obj.get('relevant_doc_ids', []):
                s = str(d)
                if s.isdigit():
                    Q.add(int(s))
    return Q


def main():
    ap = argparse.ArgumentParser(description='Recreate Qdrant collection from JSONL corpus')
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--collection', default='fiqa_10k_v1')
    ap.add_argument('--qrels', default=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'fiqa_v1', 'fiqa_qrels_10k_v1.jsonl')))
    ap.add_argument('--fields', default='title+text', choices=['title','text','title+text'])
    ap.add_argument('--recreate', action='store_true')
    ap.add_argument('--qdrant-url', default='http://localhost:6333')
    ap.add_argument('--min_coverage', type=float, default=0.995)
    args = ap.parse_args()

    docs = load_corpus(args.corpus)
    print(f'Loaded {len(docs)} docs from {args.corpus}')

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    dim = model.get_sentence_embedding_dimension()

    client = QdrantClient(host='localhost', port=6333) if args.qdrant_url.startswith('http') else QdrantClient(url=args.qdrant_url)

    ensure_collection(client, args.collection, dim, args.recreate)

    vectors = embed_documents(model, docs, args.fields)
    upsert(client, args.collection, docs, vectors)

    sample = sample_ids(client, args.collection, k=10)
    print('Sample doc_ids:', sample)

    Q = load_qrels_ids(args.qrels)
    C = collection_doc_ids(client, args.collection)
    cover = (len(Q & C) / len(Q)) if Q else 0.0
    print(f'Coverage: {len(Q & C)}/{len(Q)} = {cover:.4%}')

    if cover < args.min_coverage:
        print(f'Coverage below threshold {args.min_coverage:.3%}', flush=True)
        raise SystemExit(2)

    print('✅ Rebuild complete and coverage threshold met.')


if __name__ == '__main__':
    main()



