#!/usr/bin/env python3
# scripts/compare_top5.py
import copy, re, sys, json, time
from pathlib import Path

# --- 1) 轻量 YAML 读取（不引入额外依赖） ---
def load_yaml(path: Path):
    try:
        import yaml  # 若你环境已有 PyYAML，会用它（更稳）
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        # 极简 JSON 备选：若你的配置是 YAML 超集且结构简单，这也能工作
        # 否则请 `pip install pyyaml` 后重跑
        with open(path, "r", encoding="utf-8") as f:
            return json.loads(f.read())

# --- 2) 命中词提示：简单 token overlap ---
def hit_hints(query: str, text: str, topn: int = 5):
    q_tokens = {t.lower() for t in re.findall(r"\w+", query)}
    t_tokens = [t.lower() for t in re.findall(r"\w+", text)]
    hits = [t for t in t_tokens if t in q_tokens]
    # 返回去重后出现频次高的前若干个
    freq = {}
    for h in hits:
        freq[h] = freq.get(h, 0) + 1
    return ", ".join(sorted(freq, key=freq.get, reverse=True)[:topn]) or "-"

# --- 3) 运行一次：开/关 reranker ---
def run_once(cfg_path: Path, enable_reranker: bool, query: str, top_k: int = 5):
    from modules.search.search_pipeline import SearchPipeline  # 你项目里的 Pipeline
    cfg = load_yaml(cfg_path)
    
    # 根据enable_reranker参数修改配置
    if enable_reranker:
        # 开启reranker：确保有reranker配置
        if "reranker" not in cfg:
            cfg["reranker"] = {"type": "fake", "top_k": 10, "params": {"weight": 1.0}}
    else:
        # 关闭reranker：移除reranker配置或设置为none
        if "reranker" in cfg:
            cfg["reranker"] = {"type": "none"}

    # 直接使用配置字典创建pipeline
    pipe = SearchPipeline(cfg)
    res = pipe.search(query=query, collection_name="test_collection")  # 期望返回 List[ScoredDocument]
    return res[:top_k]  # 只返回前top_k个结果

# --- 4) 格式化打印前5对比 ---
def print_top5_compare(query: str, base, rerank):
    print(f"\n=== Query: {query} ===")
    print(f"{'Rank':<4} {'BASE(score)':<16} {'→':^3} {'RERANK(score)':<16}  HitHints")
    print("-" * 64)

    # 对齐前5（按各自排序）
    for i in range(5):
        b = base[i] if i < len(base) else None
        r = rerank[i] if i < len(rerank) else None
        if not b and not r: break

        b_text = b.document.text if b else ""
        r_text = r.document.text if r else ""

        # 分数
        b_sc = f"{b.score:.3f}" if b else "-"
        r_sc = f"{r.score:.3f}" if r else "-"

        # 命中词（对 rerank 结果做提示，更直观）
        hints = hit_hints(query, r_text or b_text)

        print(f"{i+1:<4} {b_sc:<16} {'→':^3} {r_sc:<16}  {hints}")

    # 简单的“排序变化”提示：看 base top1 文档是否被顶替
    if base and rerank:
        changed = (base[0].document.id != rerank[0].document.id)
        print(f"Top-1 changed: {'YES' if changed else 'NO'}")

def main():
    # 传参：configs/demo_rerank.yaml "usb c fast charging cable"
    cfg_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("configs/demo_rerank.yaml")
    queries = sys.argv[2:] or [
        "fast usb c cable charging",
        "wireless charger for iphone",
        "bluetooth headphones noise cancelling",
    ]

    print(f"Using config: {cfg_path}")
    for q in queries:
        # 先跑 baseline（关 reranker）
        base = run_once(cfg_path, enable_reranker=False, query=q, top_k=5)
        # 再跑 rerank（开 reranker）
        rerank = run_once(cfg_path, enable_reranker=True, query=q, top_k=5)
        print_top5_compare(q, base, rerank)

if __name__ == "__main__":
    main()