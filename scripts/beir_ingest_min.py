import argparse, json, re, time
from beir import util
from beir.datasets.data_loader import GenericDataLoader
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

def norm(txt): 
    return re.sub(r"\s+", " ", (txt or "")).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)   # fiqa / scifact
    ap.add_argument("--collection", required=True)
    ap.add_argument("--host", default="localhost"); ap.add_argument("--port", type=int, default=6333)
    ap.add_argument("--limit", type=int, default=None)   # 小集/抽样上限
    ap.add_argument("--batch", type=int, default=128)   # batch size for upsert
    ap.add_argument("--recreate", action='store_true')   # recreate collection if exists
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = ap.parse_args()

    url = util.download_and_unzip("https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{}.zip".format(args.dataset), "./data/")
    corpus, _, _ = GenericDataLoader(data_folder=url).load(split="test")

    # 1) 准备向量
    docs = list(corpus.items())
    if args.limit:
        docs = docs[:args.limit]
    ids = [did for did,_ in docs]
    
    # 统一使用 title + abstract 作为文本
    texts = []
    payloads = []
    for doc_id, doc in docs:
        title = (doc.get("title") or "").strip()
        abstract = (doc.get("abstract") or doc.get("text") or "").strip()
        text = (title + "\n\n" + abstract).strip()
        texts.append(text)
        payloads.append({"doc_id": str(doc_id), "title": title, "abstract": abstract})
    
    emb = SentenceTransformer(args.model).encode(texts, batch_size=64, show_progress_bar=True)

    # 2) 建 collection（若不存在）
    cli = QdrantClient(host=args.host, port=args.port)
    if args.recreate and args.collection in [c.name for c in cli.get_collections().collections]:
        print(f"Dropping existing collection: {args.collection}")
        cli.delete_collection(args.collection)
    if args.collection not in [c.name for c in cli.get_collections().collections]:
        print(f"Creating collection: {args.collection}")
        cli.recreate_collection(args.collection, vectors_config=VectorParams(size=len(emb[0]), distance=Distance.COSINE))

    # 3) 写入（payload 带 doc_id 与 text，方便评测）
    points = [PointStruct(id=i, vector=emb[i], payload={"doc_id": str(ids[i]), "text": texts[i], **payloads[i]}) for i in range(len(ids))]
    
    # Batch upsert with retry
    batch_size = args.batch
    total_batches = (len(points) + batch_size - 1) // batch_size
    print(f"Upserting {len(points)} points in {total_batches} batches of {batch_size}")
    
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        for attempt in range(3):  # 3 retries
            try:
                cli.upsert(collection_name=args.collection, points=batch)
                print(f"Batch {batch_num}/{total_batches} OK ({len(batch)} points)")
                break
            except Exception as e:
                if attempt < 2:
                    print(f"Batch {batch_num} failed (attempt {attempt + 1}/3): {e}, retrying...")
                    time.sleep(0.5)
                else:
                    print(f"Batch {batch_num} failed after 3 attempts: {e}")
                    raise
    
    print(f"INGEST OK: {args.collection}, docs={len(points)}")

if __name__ == "__main__":
    main()
