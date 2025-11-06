#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter
from typing import Dict, Any, List, Tuple

DATA_DIR = Path("data/fiqa_v1")
CORPUS = DATA_DIR / "corpus_10k_v1.jsonl"
QRELS = DATA_DIR / "fiqa_qrels_10k_v1.trec"
QUERIES = DATA_DIR / "fiqa_10k_v1" / "queries.jsonl"
REPORT = Path("reports/audit_fiqa_10k.md")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    docs = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))
    return docs


def read_qrels(path: Path) -> List[Tuple[str, str, int]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        qid, _, doc_id, rel = line.split()
        out.append((qid, doc_id, int(rel)))
    return out


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    corpus = read_jsonl(CORPUS)
    queries = read_jsonl(QUERIES)
    qrels = read_qrels(QRELS)

    # 1) 文档字段缺失统计
    total_docs = len(corpus)
    missing_title = 0
    missing_abstract = 0
    for d in corpus:
        title = d.get("title")
        abstract = d.get("abstract")
        if not title or not str(title).strip():
            missing_title += 1
        if not abstract or not str(abstract).strip():
            missing_abstract += 1

    # 2) qrels 覆盖率（有标注的 query 数 / queries 总数）
    qrels_qids = {qid for (qid, _doc, _rel) in qrels}
    queries_qids = set()
    # queries schema can be id or qid; support both
    for q in queries:
        qid = q.get("qid") or q.get("id")
        if qid is not None:
            queries_qids.add(str(qid))
    qrels_query_covered = len(qrels_qids & queries_qids)
    qrels_query_total = len(qrels_qids)
    query_total = len(queries_qids)

    # 3) qrels doc_id ⊆ corpus doc_id 检查
    corpus_ids = {str(d.get("doc_id")) for d in corpus if d.get("doc_id") is not None}
    qrels_doc_ids = {doc_id for (_qid, doc_id, _rel) in qrels}
    missing_doc_ids = sorted(list(qrels_doc_ids - corpus_ids))[:20]
    subset_ok = len(missing_doc_ids) == 0

    # 额外：qrels 中的正例计数
    rel_counter = Counter(rel for (_qid, _doc, rel) in qrels)

    # 写报告
    REPORT.write_text(
        "\n".join([
            "# FIQA 10k v1 审计报告",
            f"数据源: {CORPUS}",
            "",
            "## 文档字段健康",
            f"- 总文档数: {total_docs}",
            f"- 缺失 title 比例: {missing_title}/{total_docs} = {missing_title/ max(1,total_docs):.2%}",
            f"- 缺失 abstract 比例: {missing_abstract}/{total_docs} = {missing_abstract/ max(1,total_docs):.2%}",
            "",
            "## qrels 覆盖率",
            f"- 有标注的 query 数: {qrels_query_total}",
            f"- queries.jsonl 中的 query 数: {query_total}",
            f"- 交集: {qrels_query_covered}",
            f"- 覆盖率: {qrels_query_covered}/ {qrels_query_total} = "
            f"{(qrels_query_covered / max(1, qrels_query_total)):.2%}",
            "",
            "## qrels doc_id ⊆ corpus doc_id",
            f"- 是否子集: {subset_ok}",
            ("- 缺失样例 (最多20个): " + ", ".join(missing_doc_ids)) if not subset_ok else "",
            "",
            "## 其他统计",
            f"- qrels 相关性分布: {dict(rel_counter)}",
            "",
            "(本报告由 scripts/v12_audit_fiqa_v1.py 生成)",
        ]),
        encoding="utf-8"
    )

    print(f"[AUDIT] Report written to {REPORT}")


if __name__ == "__main__":
    main()
