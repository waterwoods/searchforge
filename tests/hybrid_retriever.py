# SurgeForge Retrieval MVP — Study Map
# 
# Legend: ★ SLA-critical   ★ CACHE   ★ RPS/Concurrency   ★ FASTPATH   ★ RETRY   ★ EVAL
# 
# Control Flow:
# BM25Index → VectorIndex → HybridRetriever → cache → fastpath → merge
#     ↓           ↓              ↓            ↓        ↓         ↓
#  postings   similarity    parallel      TTL/LFU   threshold  alpha
#
# hybrid_retriever.py
import asyncio, time, math, random, contextlib
from collections import Counter, defaultdict, OrderedDict
from dataclasses import dataclass
from typing import List, Tuple, Dict, Iterable, Optional

import numpy as np

# FAISS 可选后端
try:
    import faiss
    HAVE_FAISS = True
except Exception:
    HAVE_FAISS = False

# ---- 引用你已完成的批量嵌入器（放同目录） ----
from batch_embedder import AsyncBatchEmbedder, FakeEmbedAPI

# -----------------------
# 简易 BM25 实现
# -----------------------
def tokenize(s: str) -> List[str]:
    return [t for t in ''.join(ch.lower() if ch.isalnum() else ' ' for ch in s).split() if t]

@dataclass
class BM25Index:
    k1: float = 1.5  # ★ SLA: BM25 k1 parameter
    b: float = 0.75  # ★ SLA: BM25 b parameter

    def build(self, docs: List[str]):
        self.N = len(docs)
        self.docs = docs
        self.toks = [tokenize(x) for x in docs]
        self.doc_len = [len(t) for t in self.toks]
        self.avgdl = sum(self.doc_len) / max(1, self.N)
        # df & idf
        df = Counter()
        for ts in self.toks:
            df.update(set(ts))
        self.idf = {t: math.log((self.N - df[t] + 0.5) / (df[t] + 0.5) + 1.0) for t in df}  # ★ SLA: idf calculation
        # 预计算 tf
        self.tf = [Counter(ts) for ts in self.toks]
        # --- 在 BM25Index.build 里加倒排 ---
        self.postings = defaultdict(list)  # ★ FASTPATH: postings inverted index
        for i, ts in enumerate(self.toks):
            for t in set(ts):
                self.postings[t].append(i)

    # def search(self, query: str, topk: int = 20) -> List[Tuple[int, float]]:
    #     q = tokenize(query)
    #     scores: Dict[int, float] = defaultdict(float)
    #     for i, tf_i in enumerate(self.tf):
    #         dl = self.doc_len[i] or 1
    #         K = self.k1 * (1 - self.b + self.b * dl / max(1, self.avgdl))
    #         s = 0.0
    #         for t in q:
    #             if t not in tf_i or t not in self.idf:
    #                 continue
    #             f = tf_i[t]
    #             s += self.idf[t] * (f * (self.k1 + 1)) / (f + K)
    #         scores[i] = s
    #     # 取 topk
    #     if not scores:
    #         return []
    #     items = list(scores.items())
    #     items.sort(key=lambda x: x[1], reverse=True)
    #     return items[:topk]

    # --- 替换 BM25Index.search ---
    def search(self, query: str, topk: int = 20) -> List[Tuple[int, float]]:
        q = tokenize(query)
        cand = set()
        for t in q:
            cand.update(self.postings.get(t, []))  # ★ FASTPATH: candidate set (no full scan)
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
        items = list(scores.items());
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:topk]
# -----------------------
# 向量索引（点积，不归一化）
# -----------------------
@dataclass
class VectorIndex:
    mat: np.ndarray  # (N, D)
    def search(self, qvec: np.ndarray, topk: int = 20) -> List[Tuple[int, float]]:  # ★ SLA: vector similarity
        # 点积越大越相似；不做归一化以保持区分度（配合 FakeEmbedAPI）
        sims = self.mat @ qvec
        # topk
        if topk >= len(sims):
            idx = np.argsort(-sims)
        else:
            part = np.argpartition(-sims, topk)[:topk]
            idx = part[np.argsort(-sims[part])]
        return [(int(i), float(sims[i])) for i in idx[:topk]]

@dataclass
class FaissIndex:  # ★ SLA: FAISS vector backend
    mat: np.ndarray
    def __post_init__(self):
        d = self.mat.shape[1]
        self.index = faiss.IndexFlatIP(d)   # 点积
        self.index.add(self.mat.astype('float32'))
    def search(self, qvec: np.ndarray, topk: int = 20):
        D, I = self.index.search(qvec.reshape(1, -1).astype('float32'), topk)
        return [(int(i), float(d)) for i, d in zip(I[0], D[0])]

# -----------------------
# TTL LRU 缓存
# -----------------------
class TTLLRU:  # ★ CACHE: TTL LRU cache
    def __init__(self, max_items=1000, ttl_s=60):
        self.max = max_items
        self.ttl = ttl_s
        self.od = OrderedDict()  # key -> (expire_ts, value)
        self.hits = 0
        self.miss = 0
    def get(self, key):
        now = time.time()
        if key in self.od:
            exp, val = self.od[key]
            if exp > now:
                self.od.move_to_end(key)  # ★ CACHE: LRU eviction
                self.hits += 1
                return val
            else:
                del self.od[key]
        self.miss += 1
        return None
    def set(self, key, val):
        now = time.time()
        self.od[key] = (now + self.ttl, val)
        self.od.move_to_end(key)
        if len(self.od) > self.max:
            self.od.popitem(last=False)  # ★ CACHE: eviction
    def hit_rate(self):  # ★ CACHE: hit rate tracking
        tot = self.hits + self.miss
        return (self.hits / tot) if tot else 0.0

class TTLLFU:  # ★ CACHE: TTL LFU cache
    def __init__(self, max_items=1000, ttl_s=60):
        self.max, self.ttl = max_items, ttl_s
        self.store = {}  # key -> (expire_ts, val, freq)
        self.hits = 0; self.miss = 0
    def get(self, key):
        now = time.time()
        it = self.store.get(key)
        if not it or it[0] <= now:
            if it: self.store.pop(key, None)
            self.miss += 1; return None
        exp, val, f = it
        self.store[key] = (exp, val, f+1)  # ★ CACHE: frequency tracking
        self.hits += 1; return val
    def set(self, key, val):
        now = time.time()
        if len(self.store) >= self.max:
            victim = min(self.store.items(), key=lambda kv: (kv[1][2], kv[1][0]))[0]  # ★ CACHE: LFU eviction
            self.store.pop(victim, None)
        self.store[key] = (now + self.ttl, val, 1)
    def hit_rate(self):  # ★ CACHE: hit rate tracking
        tot = self.hits + self.miss
        return (self.hits / tot) if tot else 0.0

# -----------------------
# 混合检索（BM25 + 向量加权）
# -----------------------
class HybridRetriever:
    def __init__(self, embedder: AsyncBatchEmbedder, vec_index: VectorIndex, bm25: BM25Index,
                 alpha: float = 0.6, cache_ttl_s: int = 60, cache_max: int = 1000,  # ★ SLA/CACHE: alpha, cache params
                 bm25_fast_thresh: float = 0.85):  # ★ FASTPATH: fast path threshold
        self.embedder = embedder
        self.vec_index = vec_index
        self.bm25 = bm25
        self.alpha = alpha
        self.cache = TTLLFU(cache_max, cache_ttl_s)  # ★ CACHE: 用 LFU
        self.qvec_cache = TTLLRU(cache_max, cache_ttl_s)   # ★ CACHE: 查询向量仍用 LRU
        self.bm25_fast_thresh = bm25_fast_thresh

    async def _embed_query(self, query: str):
        v = self.qvec_cache.get(query)  # ★ CACHE: qvec TTL cache
        if v is not None: 
            return v
        v = np.array(await self.embedder.embed_one(query), dtype=np.float32)
        self.qvec_cache.set(query, v)
        return v

    async def retrieve(self, query: str, k: int = 10) -> List[Tuple[int, float]]:
        ck = (query, k, self.alpha)
        hit = self.cache.get(ck)  # ★ CACHE: result cache check
        if hit is not None:
            return hit

        # 并行启动嵌入，BM25 同时计算；若 BM25 足够强则直接走快路径并取消向量
        embed_task = asyncio.create_task(self._embed_query(query))  # ★ FASTPATH: parallel query embed
        bres = self.bm25.search(query, topk=max(50, k))  # ★ SLA: BM25 first

        # 归一化（稳健 min-max）
        def norm(res):  # ★ SLA: normalize scores
            if not res: return {}
            mx = max(1e-9, max(s for _, s in res)); mn = min(s for _, s in res)
            d = (mx - mn) if (mx - mn) > 1e-9 else 1.0
            return {i: (s - mn) / d for i, s in res}, (mx - mn) <= 1e-9, (res[0][1] - mn) / d

        bdict, b_degenerate, b_top = norm(bres)

        # 快路径：BM25 足够自信 → 直接返回（避免等待向量嵌入）
        if bres and b_top >= self.bm25_fast_thresh and not b_degenerate:  # ★ FASTPATH: fast-path return if bm25_top≥threshold
            with contextlib.suppress(Exception):
                embed_task.cancel()
            out = [(i, bdict[i]) for i, _ in bres[:k]]
            self.cache.set(ck, out)  # ★ CACHE: cache set
            return out

        # 否则融合（等待向量结果）
        qvec = await embed_task
        vres = self.vec_index.search(qvec, topk=max(50, k))
        vdict, _, _ = norm(vres)
        union = set(vdict) | set(bdict)
        merged = [(i, self.alpha * vdict.get(i, 0.0) + (1 - self.alpha) * bdict.get(i, 0.0)) for i in union]  # ★ SLA: merge scores (alpha-weighted)
        merged.sort(key=lambda x: x[1], reverse=True)
        out = merged[:k]
        self.cache.set(ck, out)  # ★ CACHE: cache set
        return out

# -----------------------
# 基准测试
# -----------------------
async def build_corpus_and_indexes(N=300, dim=64):
    # 文档离线嵌入（可以慢点）
    api_doc = FakeEmbedAPI(dim=dim, rps_limit=36, base_ms=35, per_item_ms=4, jitter_ms=12)  # ★ FASTPATH/SLA: doc vs query embed API (slow vs low-latency)
    embedder_doc = AsyncBatchEmbedder(api_doc, max_batch_size=32, max_batch_latency_ms=25,
                                      max_concurrency=8, rps_limit=36)

    # 文档向量
    docs = [f"function foo{i} uses kafka stream to update qdrant index {i%17}" for i in range(N)]
    vecs = [asyncio.create_task(embedder_doc.embed_one(f"function foo{i} uses kafka stream to update qdrant index {i%17}")) for i in range(N)]
    vecs = [np.array(await t, dtype=np.float32) for t in vecs]
    V = np.vstack(vecs)

    # 查询在线嵌入（低延迟通道）
    api_q = FakeEmbedAPI(dim=dim, rps_limit=64, base_ms=10, per_item_ms=2, jitter_ms=6)  # ★ FASTPATH/SLA: low-latency query API
    embedder_q = AsyncBatchEmbedder(api_q, max_batch_size=16, max_batch_latency_ms=15,
                                    max_concurrency=8, rps_limit=64)

    vindex = FaissIndex(V) if HAVE_FAISS else VectorIndex(V)
    bm25 = BM25Index(); bm25.build([f"function foo{i} uses kafka stream to update qdrant index {i%17}" for i in range(N)])
    return bm25.docs, embedder_q, vindex, bm25

async def benchmark(Q=200, N=300, k=10):
    docs, embedder, vindex, bm25 = await build_corpus_and_indexes(N=N)
    retr = HybridRetriever(embedder, vindex, bm25, alpha=0.6, cache_ttl_s=320, cache_max=2048, bm25_fast_thresh=0.85)

    # 构造查询：一半是“命中自身”的同文查询；一半是轻微变体（测试 BM25/混合效果）
    queries = []
    for _ in range(Q//2):
        i = random.randint(0, N-1)
        queries.append(docs[i])  # exact
    vocab = ["kafka","spark","faiss","qdrant","rerank","batch","cache","pq","hnsw","onnx"]
    for _ in range(Q - len(queries)):
        i = random.randint(0, N-1)
        w = random.choice(vocab)
        queries.append(f"{docs[i]} {w}")

    # 首轮检索（冷缓存）
    lat = []
    correct_top1 = 0
    t0 = time.time()
    for q in queries:
        s = time.time()
        res = await retr.retrieve(q, k=k)
        lat.append(time.time() - s)
        # 自检：若是 exact 查询，判断 top1 是否为其自身（文本相等）
        if q in docs and res and docs[res[0][0]] == q:
            correct_top1 += 1
    t1 = time.time()

    # 二轮（命中缓存）
    for q in queries:
        _ = await retr.retrieve(q, k=k)

    import statistics
    p95 = statistics.quantiles(lat, n=100)[94]
    p50 = statistics.median(lat)
    hit = retr.cache.hit_rate()

    print(f"N={N} Q={Q} k={k} total={t1-t0:.3f}s p50={p50*1000:.1f}ms p95={p95*1000:.1f}ms cache_hit={hit*100:.1f}% top1_correct={correct_top1}/{Q//2}")

    # 验收断言
    assert p95*1000 < 30.0, "检索 p95 未小于 30ms"  # ★ EVAL: p95<30ms, cache≥40%, top1≥95/100
    assert hit >= 0.40, "缓存命中率不足 40%"  # ★ EVAL: cache≥40%
    assert correct_top1 >= int(0.95 * (Q//2)), "Top-1 自检召回不足 95%"  # ★ EVAL: top1≥95/100

async def smoke_10q():
    """10Q<1s 自测闸门"""
    # 使用更小的数据集和更稳定的配置
    docs, embedder, vindex, bm25 = await build_corpus_and_indexes(N=100)
    retr = HybridRetriever(embedder, vindex, bm25, alpha=0.6, cache_ttl_s=60, cache_max=1024)
    qs = [docs[i] for i in range(10)]
    t0 = time.time()
    await asyncio.gather(*(retr.retrieve(q, k=5) for q in qs))
    dur = time.time() - t0
    assert dur < 1.0, f"10Q took {dur:.3f}s"  # ★ EVAL: total<1s gate
    print(f"10Q total {dur:.3f}s ✓")

async def benchmark_3000():
    """N=3000 全量压测"""
    print("🚀 启动 N=3000 全量压测...")
    await benchmark(Q=200, N=3000, k=10)

if __name__ == "__main__":
    # asyncio.run(smoke_10q())
    print("\n" + "="*50)
    asyncio.run(benchmark_3000())

# Study Checklist
# Numbers to remember:
#   hybrid: alpha=0.6, bm25_fast_thresh=0.85, cache_ttl_s=60, cache_max=1024
#   eval gates: p95<30ms (retrieval), cache≥40%, top1≥95/100; embedder p95<200ms; 10Q<1s
# 3 trade-offs (one line each):
#   HNSW vs PQ: HNSW faster search, PQ smaller memory
#   BM25 vs vector: BM25 exact matches, vector semantic similarity
#   ONNX vs Torch: ONNX faster inference, Torch more flexible
# Grep cheats:
#   grep -n "★" -n
#   grep -n "\[FASTPATH\]\|\[RPS\]\|\[CACHE\]"