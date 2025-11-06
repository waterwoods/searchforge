#!/usr/bin/env python3
"""
数据准备脚本 - prepare_data.py (V3)

此脚本用于从 beir/fiqa 数据集中创建一个固定大小的子集，并预先计算所有相关文档的嵌入向量。
将耗时的"数据嵌入 (Embedding)"计算与后续的"检索性能 (Retrieval)"测试完全分离，
确保后续所有实验的科学性和快速迭代能力。

V3新特性：
- 所有输出文件保存到项目仓库内部
- 根据实际数据量动态命名输出目录
- 生成数据校验文件 (checksums.json) 和统计快照 (stats.json)
- 预先构建BM25稀疏索引

输出：
- processed_corpus.jsonl: 包含文档ID、文本和元数据
- embeddings_primary.npy: 主要模型的文档嵌入向量
- embeddings_secondary.npy: 次要模型的文档嵌入向量
- queries_subset_N.jsonl: 查询子集
- qrels_subset_N.tsv: 查询子集的相关性标注
- queries_dev.jsonl, qrels_dev.tsv: 开发集查询和标注
- queries_test.jsonl, qrels_test.tsv: 测试集查询和标注
- query_embeddings_primary.npy: 主要模型的查询嵌入向量
- query_embeddings_secondary.npy: 次要模型的查询嵌入向量
- stats.json: 数据统计信息
- checksums.json: 文件校验和
- bm25_index/: BM25索引目录
- manifest.json: 实验元数据记录（包含环境信息）
"""

import hashlib
import json
import logging
import pathlib
import platform
import random
import statistics
import subprocess
import sys
from typing import Dict, List, Set, Tuple

import numpy as np
from beir import util
from beir.datasets.data_loader import GenericDataLoader
from sentence_transformers import SentenceTransformer

# ============================================================================
# Configuration Constants
# ============================================================================

DATASET_NAME = "beir/fiqa"
SUBSET_QUERIES_COUNT = 5000
PRIMARY_MODEL = "all-MiniLM-L6-v2"
SECONDARY_MODEL = "BAAI/bge-small-en-v1.5"
# 输出目录：相对于脚本文件所在位置，指向项目内部的reports目录
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
OUTPUT_BASE_DIR = SCRIPT_DIR.parent / "reports" / "dataset_prepared"
RANDOM_SEED = 2025
DEV_TEST_SPLIT_RATIO = 0.8  # 80% for dev, 20% for test

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 尝试导入psutil，如果不可用则使用fallback
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, some environment specs will be missing")

# 尝试导入pyserini，如果不可用则记录警告
try:
    from pyserini.index import IndexWriter
    from pyserini.index.lucene import LuceneIndexWriter
    PYSERINI_AVAILABLE = True
except ImportError:
    PYSERINI_AVAILABLE = False
    logger.warning("pyserini not available, BM25 index will not be built")

# 禁用 BEIR 的详细日志
logging.getLogger("beir").setLevel(logging.ERROR)


def load_full_dataset():
    """
    加载完整的 beir/fiqa 数据集。
    
    Returns:
        tuple: (corpus, queries, qrels)
            - corpus: Dict[str, Dict] - 文档字典，key为文档ID
            - queries: Dict[str, str] - 查询字典，key为查询ID
            - qrels: Dict[str, Dict[str, int]] - 相关性标注，key为查询ID，value为{文档ID: 相关性分数}
    """
    logger.info(f"Loading dataset: {DATASET_NAME}")
    
    # 下载并解压数据集
    data_path = util.download_and_unzip(
        "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/fiqa.zip",
        "./data/"
    )
    
    # 加载数据
    data_loader = GenericDataLoader(data_folder=data_path)
    corpus, queries, qrels = data_loader.load(split="test")
    
    logger.info(f"Loaded dataset: {len(corpus)} documents, {len(queries)} queries, {len(qrels)} query-document pairs")
    
    return corpus, queries, qrels


def create_deterministic_subset(corpus: Dict[str, Dict], queries: Dict[str, str], qrels: Dict[str, Dict[str, int]]):
    """
    创建一个确定性的文档子集。
    
    步骤：
    1. 从 queries 中随机选择 SUBSET_QUERIES_COUNT 条查询（使用固定随机种子）
    2. 遍历这些查询的 qrels，收集所有相关的、不重复的文档ID
    3. 根据这些文档ID，从完整的 corpus 中筛选出文档子集
    
    Args:
        corpus: 完整的文档字典
        queries: 完整的查询字典
        qrels: 完整的相关性标注字典
    
    Returns:
        tuple: (subset_corpus, subset_query_ids, subset_queries, subset_qrels)
            - subset_corpus: Dict[str, Dict] - 文档子集
            - subset_query_ids: List[str] - 选中的查询ID列表
            - subset_queries: Dict[str, str] - 查询子集
            - subset_qrels: Dict[str, Dict[str, int]] - 查询子集的相关性标注
    """
    logger.info(f"Creating deterministic subset with {SUBSET_QUERIES_COUNT} queries (seed={RANDOM_SEED})")
    
    # 设置随机种子以确保可复现性
    random.seed(RANDOM_SEED)
    
    # 从所有查询中随机选择指定数量的查询
    all_query_ids = list(queries.keys())
    if len(all_query_ids) < SUBSET_QUERIES_COUNT:
        logger.warning(
            f"Available queries ({len(all_query_ids)}) < requested ({SUBSET_QUERIES_COUNT}). "
            f"Using all available queries."
        )
        subset_query_ids = all_query_ids
    else:
        subset_query_ids = random.sample(all_query_ids, SUBSET_QUERIES_COUNT)
    
    logger.info(f"Selected {len(subset_query_ids)} queries")
    
    # 创建查询子集和qrels子集
    subset_queries = {qid: queries[qid] for qid in subset_query_ids}
    subset_qrels = {qid: qrels[qid] for qid in subset_query_ids if qid in qrels}
    
    # 收集所有相关的文档ID
    relevant_doc_ids: Set[str] = set()
    for query_id in subset_query_ids:
        if query_id in qrels:
            # qrels[query_id] 是一个字典，key是文档ID，value是相关性分数
            # 只收集相关性分数大于0的文档
            for doc_id, relevance in qrels[query_id].items():
                if relevance > 0:
                    relevant_doc_ids.add(doc_id)
    
    logger.info(f"Found {len(relevant_doc_ids)} unique relevant documents")
    
    # 从完整的 corpus 中筛选出文档子集
    subset_corpus = {doc_id: corpus[doc_id] for doc_id in relevant_doc_ids if doc_id in corpus}
    
    logger.info(f"Created subset corpus with {len(subset_corpus)} documents")
    
    return subset_corpus, subset_query_ids, subset_queries, subset_qrels


def compute_text_statistics(processed_data: List[Dict]) -> Dict:
    """
    计算文档文本长度的统计信息。
    
    Args:
        processed_data: 处理后的数据列表
    
    Returns:
        Dict: 包含min, max, mean, std等统计信息的字典
    """
    text_lengths = [len(item.get("text", "")) for item in processed_data]
    
    if not text_lengths:
        return {
            "min": 0,
            "max": 0,
            "mean": 0,
            "std": 0,
            "count": 0
        }
    
    return {
        "min": min(text_lengths),
        "max": max(text_lengths),
        "mean": round(statistics.mean(text_lengths), 2),
        "std": round(statistics.stdev(text_lengths) if len(text_lengths) > 1 else 0, 2),
        "median": statistics.median(text_lengths),
        "count": len(text_lengths)
    }


def save_subset_queries_and_qrels(
    subset_queries: Dict[str, str],
    subset_qrels: Dict[str, Dict[str, int]],
    actual_query_count: int,
    output_dir: pathlib.Path
):
    """
    保存查询子集和qrels到磁盘。
    
    Args:
        subset_queries: 查询子集字典
        subset_qrels: qrels子集字典
        actual_query_count: 实际查询数量（用于动态命名）
        output_dir: 输出目录
    """
    logger.info("Saving subset queries and qrels...")
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存查询子集（JSONL格式，使用动态命名）
    queries_path = output_dir / f"queries_subset_{actual_query_count}.jsonl"
    logger.info(f"Saving queries to {queries_path}")
    with open(queries_path, 'w', encoding='utf-8') as f:
        for qid, query_text in subset_queries.items():
            f.write(json.dumps({"query_id": qid, "text": query_text}, ensure_ascii=False) + '\n')
    
    # 保存qrels子集（TSV格式，符合BEIR标准，使用动态命名）
    qrels_path = output_dir / f"qrels_subset_{actual_query_count}.tsv"
    logger.info(f"Saving qrels to {qrels_path}")
    with open(qrels_path, 'w', encoding='utf-8') as f:
        # 写入TSV头部
        f.write("query-id\tcorpus-id\tscore\n")
        # 写入数据
        for qid, doc_relevance in subset_qrels.items():
            for doc_id, relevance in doc_relevance.items():
                if relevance > 0:  # 只保存相关性分数大于0的
                    f.write(f"{qid}\t{doc_id}\t{relevance}\n")
    
    logger.info("Subset queries and qrels saved successfully")


def split_dev_test(subset_query_ids: List[str]) -> Tuple[List[str], List[str]]:
    """
    将查询ID列表划分为开发集和测试集。
    
    Args:
        subset_query_ids: 查询ID列表
    
    Returns:
        tuple: (dev_query_ids, test_query_ids)
    """
    logger.info(f"Splitting queries into dev/test sets ({DEV_TEST_SPLIT_RATIO:.0%}/{1-DEV_TEST_SPLIT_RATIO:.0%})")
    
    # 使用固定随机种子（RANDOM_SEED + 1）进行划分
    random.seed(RANDOM_SEED + 1)
    
    # 打乱查询ID列表
    shuffled_query_ids = subset_query_ids.copy()
    random.shuffle(shuffled_query_ids)
    
    # 计算划分点
    split_point = int(len(shuffled_query_ids) * DEV_TEST_SPLIT_RATIO)
    
    dev_query_ids = shuffled_query_ids[:split_point]
    test_query_ids = shuffled_query_ids[split_point:]
    
    logger.info(f"Dev set: {len(dev_query_ids)} queries, Test set: {len(test_query_ids)} queries")
    
    return dev_query_ids, test_query_ids


def save_dev_test_splits(
    dev_query_ids: List[str],
    test_query_ids: List[str],
    queries: Dict[str, str],
    qrels: Dict[str, Dict[str, int]],
    output_dir: pathlib.Path
):
    """
    保存开发集和测试集的查询和qrels文件。
    
    Args:
        dev_query_ids: 开发集查询ID列表
        test_query_ids: 测试集查询ID列表
        queries: 完整的查询字典
        qrels: 完整的qrels字典
        output_dir: 输出目录
    """
    logger.info("Saving dev/test splits...")
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存开发集查询
    dev_queries_path = output_dir / "queries_dev.jsonl"
    logger.info(f"Saving dev queries to {dev_queries_path}")
    with open(dev_queries_path, 'w', encoding='utf-8') as f:
        for qid in dev_query_ids:
            if qid in queries:
                f.write(json.dumps({"query_id": qid, "text": queries[qid]}, ensure_ascii=False) + '\n')
    
    # 保存开发集qrels
    dev_qrels_path = output_dir / "qrels_dev.tsv"
    logger.info(f"Saving dev qrels to {dev_qrels_path}")
    with open(dev_qrels_path, 'w', encoding='utf-8') as f:
        f.write("query-id\tcorpus-id\tscore\n")
        for qid in dev_query_ids:
            if qid in qrels:
                for doc_id, relevance in qrels[qid].items():
                    if relevance > 0:
                        f.write(f"{qid}\t{doc_id}\t{relevance}\n")
    
    # 保存测试集查询
    test_queries_path = output_dir / "queries_test.jsonl"
    logger.info(f"Saving test queries to {test_queries_path}")
    with open(test_queries_path, 'w', encoding='utf-8') as f:
        for qid in test_query_ids:
            if qid in queries:
                f.write(json.dumps({"query_id": qid, "text": queries[qid]}, ensure_ascii=False) + '\n')
    
    # 保存测试集qrels
    test_qrels_path = output_dir / "qrels_test.tsv"
    logger.info(f"Saving test qrels to {test_qrels_path}")
    with open(test_qrels_path, 'w', encoding='utf-8') as f:
        f.write("query-id\tcorpus-id\tscore\n")
        for qid in test_query_ids:
            if qid in qrels:
                for doc_id, relevance in qrels[qid].items():
                    if relevance > 0:
                        f.write(f"{qid}\t{doc_id}\t{relevance}\n")
    
    logger.info("Dev/test splits saved successfully")


def initialize_embedding_models():
    """
    初始化两个嵌入模型。
    
    Returns:
        tuple: (primary_model, secondary_model, primary_dim, secondary_dim)
    """
    logger.info(f"Loading primary model: {PRIMARY_MODEL}")
    primary_model = SentenceTransformer(PRIMARY_MODEL)
    
    logger.info(f"Loading secondary model: {SECONDARY_MODEL}")
    secondary_model = SentenceTransformer(SECONDARY_MODEL)
    
    # 获取模型维度
    primary_dim = primary_model.get_sentence_embedding_dimension()
    secondary_dim = secondary_model.get_sentence_embedding_dimension()
    
    logger.info(f"Primary model dimension: {primary_dim}")
    logger.info(f"Secondary model dimension: {secondary_dim}")
    
    return primary_model, secondary_model, primary_dim, secondary_dim


def precompute_document_embeddings(
    subset_corpus: Dict[str, Dict],
    primary_model: SentenceTransformer,
    secondary_model: SentenceTransformer,
    output_dir: pathlib.Path
):
    """
    预计算文档的嵌入向量并准备数据。
    
    Args:
        subset_corpus: 文档子集
        primary_model: 主要嵌入模型
        secondary_model: 次要嵌入模型
        output_dir: 输出目录
    
    Returns:
        tuple: (processed_data, primary_embeddings, secondary_embeddings)
            - processed_data: List[Dict] - 处理后的数据列表
            - primary_embeddings: np.ndarray - 主要模型的嵌入向量数组
            - secondary_embeddings: np.ndarray - 次要模型的嵌入向量数组
    """
    logger.info("Pre-computing document embeddings...")
    
    # 准备文本列表（保持顺序一致）
    doc_ids = list(subset_corpus.keys())
    texts = []
    processed_data = []
    
    for doc_id in doc_ids:
        doc = subset_corpus[doc_id]
        # 合并 title 和 text
        title = doc.get("title", "").strip()
        text_content = doc.get("text", "").strip()
        combined_text = f"{title} {text_content}".strip()
        
        texts.append(combined_text)
        
        # 存储元数据
        processed_data.append({
            "doc_id": doc_id,
            "text": combined_text,
            "title": title,
            "original_text": text_content
        })
    
    # 批量计算嵌入向量
    logger.info(f"Computing primary document embeddings ({PRIMARY_MODEL})...")
    primary_embeddings = primary_model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    logger.info(f"Computing secondary document embeddings ({SECONDARY_MODEL})...")
    secondary_embeddings = secondary_model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    # 将嵌入向量添加到处理后的数据中（仅作为元数据，实际向量保存在 .npy 文件中）
    for i, data_item in enumerate(processed_data):
        data_item["embedding_primary_shape"] = primary_embeddings[i].shape
        data_item["embedding_secondary_shape"] = secondary_embeddings[i].shape
    
    logger.info(f"Computed embeddings for {len(processed_data)} documents")
    
    return processed_data, primary_embeddings, secondary_embeddings


def precompute_query_embeddings(
    subset_queries: Dict[str, str],
    primary_model: SentenceTransformer,
    secondary_model: SentenceTransformer,
    output_dir: pathlib.Path
):
    """
    预计算查询的嵌入向量。
    
    Args:
        subset_queries: 查询子集字典
        primary_model: 主要嵌入模型
        secondary_model: 次要嵌入模型
        output_dir: 输出目录
    
    Returns:
        tuple: (primary_query_embeddings, secondary_query_embeddings)
            - primary_query_embeddings: np.ndarray - 主要模型的查询嵌入向量数组
            - secondary_query_embeddings: np.ndarray - 次要模型的查询嵌入向量数组
    """
    logger.info("Pre-computing query embeddings...")
    
    # 按照查询ID的顺序准备查询文本列表
    query_ids = list(subset_queries.keys())
    query_texts = [subset_queries[qid] for qid in query_ids]
    
    # 批量计算嵌入向量
    logger.info(f"Computing primary query embeddings ({PRIMARY_MODEL})...")
    primary_query_embeddings = primary_model.encode(
        query_texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    logger.info(f"Computing secondary query embeddings ({SECONDARY_MODEL})...")
    secondary_query_embeddings = secondary_model.encode(
        query_texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    logger.info(f"Computed embeddings for {len(query_texts)} queries")
    
    # 保存查询嵌入向量
    output_dir.mkdir(parents=True, exist_ok=True)
    
    primary_query_emb_path = output_dir / "query_embeddings_primary.npy"
    logger.info(f"Saving primary query embeddings to {primary_query_emb_path}")
    np.save(primary_query_emb_path, primary_query_embeddings)
    
    secondary_query_emb_path = output_dir / "query_embeddings_secondary.npy"
    logger.info(f"Saving secondary query embeddings to {secondary_query_emb_path}")
    np.save(secondary_query_emb_path, secondary_query_embeddings)
    
    logger.info("Query embeddings saved successfully")
    
    return primary_query_embeddings, secondary_query_embeddings


def save_processed_data(
    processed_data: List[Dict],
    primary_embeddings: np.ndarray,
    secondary_embeddings: np.ndarray,
    output_dir: pathlib.Path
):
    """
    保存处理后的数据到磁盘。
    
    Args:
        processed_data: 处理后的数据列表
        primary_embeddings: 主要模型的嵌入向量数组
        secondary_embeddings: 次要模型的嵌入向量数组
        output_dir: 输出目录
    """
    logger.info(f"Saving processed data to {output_dir}")
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存 corpus 元数据（JSONL 格式）
    corpus_metadata_path = output_dir / "processed_corpus.jsonl"
    logger.info(f"Saving corpus metadata to {corpus_metadata_path}")
    with open(corpus_metadata_path, 'w', encoding='utf-8') as f:
        for item in processed_data:
            # 移除 embedding shapes，因为它们只是元数据
            item_to_save = {k: v for k, v in item.items() if not k.endswith('_shape')}
            f.write(json.dumps(item_to_save, ensure_ascii=False) + '\n')
    
    # 保存嵌入向量（.npy 格式）
    primary_embeddings_path = output_dir / "embeddings_primary.npy"
    logger.info(f"Saving primary embeddings to {primary_embeddings_path}")
    np.save(primary_embeddings_path, primary_embeddings)
    
    secondary_embeddings_path = output_dir / "embeddings_secondary.npy"
    logger.info(f"Saving secondary embeddings to {secondary_embeddings_path}")
    np.save(secondary_embeddings_path, secondary_embeddings)
    
    logger.info("Data saved successfully")


def build_bm25_index(corpus_jsonl_path: pathlib.Path, output_dir: pathlib.Path) -> bool:
    """
    使用Pyserini构建BM25索引。
    
    Args:
        corpus_jsonl_path: processed_corpus.jsonl文件路径
        output_dir: 输出目录
    
    Returns:
        bool: 是否成功构建索引
    """
    if not PYSERINI_AVAILABLE:
        logger.warning("Pyserini not available, skipping BM25 index construction")
        return False
    
    logger.info("Building BM25 index with Pyserini...")
    
    try:
        # BM25索引输出目录
        bm25_index_dir = output_dir / "bm25_index"
        
        # 如果索引已存在，先删除
        if bm25_index_dir.exists():
            import shutil
            shutil.rmtree(bm25_index_dir)
        
        bm25_index_dir.mkdir(parents=True, exist_ok=True)
        
        # 准备临时目录用于索引构建
        temp_input_dir = output_dir / "temp_index_input"
        temp_input_dir.mkdir(parents=True, exist_ok=True)
        
        # 转换格式：将doc_id映射为id，text映射为contents
        temp_jsonl = temp_input_dir / "corpus.jsonl"
        logger.info(f"Converting corpus format for indexing...")
        doc_count = 0
        with open(corpus_jsonl_path, 'r', encoding='utf-8') as f_in, \
             open(temp_jsonl, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                doc = json.loads(line)
                pyserini_doc = {
                    "id": doc["doc_id"],
                    "contents": doc["text"]
                }
                f_out.write(json.dumps(pyserini_doc) + '\n')
                doc_count += 1
        
        logger.info(f"Converted {doc_count} documents for indexing")
        
        # 尝试使用Pyserini的Python API构建索引
        try:
            # 导入Pyserini的索引构建API
            from pyserini.index.lucene import LuceneIndexWriter, IndexWriter
            
            logger.info(f"Building index at {bm25_index_dir}...")
            writer = IndexWriter(str(bm25_index_dir))
            
            with open(temp_jsonl, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    doc = json.loads(line)
                    writer.add_document(doc)
                    if line_num % 100 == 0:
                        logger.info(f"Indexed {line_num} documents...")
            
            writer.close()
            logger.info(f"BM25 index built successfully with {doc_count} documents")
            
        except ImportError:
            # 如果Python API不可用，尝试使用命令行工具
            logger.info("Python API not available, trying command-line tool...")
            result = subprocess.run(
                [
                    "python", "-m", "pyserini.index",
                    "-collection", "JsonCollection",
                    "-generator", "DefaultLuceneDocumentGenerator",
                    "-threads", "1",
                    "-input", str(temp_input_dir),
                    "-index", str(bm25_index_dir),
                    "-storePositions", "-storeDocvectors", "-storeRaw"
                ],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to build BM25 index: {result.stderr}")
                logger.warning("BM25 index construction failed, but continuing...")
                # 清理临时目录
                import shutil
                shutil.rmtree(temp_input_dir, ignore_errors=True)
                return False
            else:
                logger.info("BM25 index built successfully using command-line tool")
        
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_input_dir, ignore_errors=True)
        
        return True
        
    except Exception as e:
        logger.error(f"Error building BM25 index: {e}", exc_info=True)
        logger.warning("BM25 index construction failed, but continuing...")
        # 清理可能的临时文件
        temp_input_dir = output_dir / "temp_index_input"
        if temp_input_dir.exists():
            import shutil
            shutil.rmtree(temp_input_dir, ignore_errors=True)
        return False


def compute_file_checksums(output_dir: pathlib.Path) -> Dict[str, str]:
    """
    计算输出目录中所有数据文件的SHA256校验和。
    
    Args:
        output_dir: 输出目录
    
    Returns:
        Dict[str, str]: 文件名到校验和的映射
    """
    logger.info("Computing file checksums...")
    
    checksums = {}
    
    # 需要计算校验和的文件扩展名
    extensions = ['.jsonl', '.tsv', '.npy', '.json']
    
    # 排除的目录和文件
    excluded_names = {'bm25_index', 'temp_index_input'}
    
    for file_path in output_dir.iterdir():
        # 只处理文件，跳过目录和临时文件
        if file_path.is_file() and file_path.suffix in extensions:
            if file_path.name not in excluded_names and not file_path.name.startswith('temp_'):
                sha256_hash = hashlib.sha256()
                try:
                    with open(file_path, 'rb') as f:
                        # 分块读取大文件
                        for chunk in iter(lambda: f.read(4096), b""):
                            sha256_hash.update(chunk)
                    checksums[file_path.name] = sha256_hash.hexdigest()
                    logger.debug(f"Computed checksum for {file_path.name}")
                except Exception as e:
                    logger.warning(f"Failed to compute checksum for {file_path.name}: {e}")
    
    logger.info(f"Computed checksums for {len(checksums)} files")
    return checksums


def save_stats_and_checksums(
    text_stats: Dict,
    corpus_count: int,
    query_count: int,
    checksums: Dict[str, str],
    output_dir: pathlib.Path
):
    """
    保存统计信息和校验和到文件。
    
    Args:
        text_stats: 文本统计信息
        corpus_count: 文档数量
        query_count: 查询数量
        checksums: 文件校验和字典
        output_dir: 输出目录
    """
    logger.info("Saving stats and checksums...")
    
    # 保存统计信息
    stats = {
        "corpus": {
            "document_count": corpus_count,
            "text_length_statistics": text_stats
        },
        "queries": {
            "query_count": query_count
        }
    }
    
    stats_path = output_dir / "stats.json"
    logger.info(f"Saving statistics to {stats_path}")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    # 保存校验和
    checksums_path = output_dir / "checksums.json"
    logger.info(f"Saving checksums to {checksums_path}")
    with open(checksums_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2, ensure_ascii=False)
    
    logger.info("Stats and checksums saved successfully")


def get_environment_specs() -> Dict:
    """
    获取环境规格信息（CPU、RAM、库版本等）。
    
    Returns:
        Dict: 包含环境信息的字典
    """
    try:
        # 获取CPU信息
        cpu_info = platform.processor()
        if not cpu_info or cpu_info == "":
            # 对于macOS，尝试获取更详细的CPU信息
            if platform.system() == "Darwin":
                try:
                    import subprocess
                    cpu_info = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
                except:
                    cpu_info = platform.machine()
            else:
                cpu_info = platform.machine()
        
        # 获取CPU核心数
        if PSUTIL_AVAILABLE:
            cpu_count = psutil.cpu_count(logical=True)
        else:
            try:
                import os
                cpu_count = os.cpu_count() or "unknown"
            except:
                cpu_count = "unknown"
        
        # 获取RAM信息（GB）
        if PSUTIL_AVAILABLE:
            ram_total_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        else:
            ram_total_gb = "unknown"
        
        # 获取库版本信息
        libraries = {}
        try:
            import beir
            libraries["beir"] = beir.__version__
        except:
            libraries["beir"] = "unknown"
        
        try:
            import sentence_transformers
            libraries["sentence_transformers"] = sentence_transformers.__version__
        except:
            libraries["sentence_transformers"] = "unknown"
        
        libraries["numpy"] = np.__version__
        libraries["python"] = sys.version.split()[0]
        
        # 获取pyserini版本
        if PYSERINI_AVAILABLE:
            try:
                import pyserini
                libraries["pyserini"] = getattr(pyserini, "__version__", "unknown")
            except:
                libraries["pyserini"] = "unknown"
        else:
            libraries["pyserini"] = "not_available"
        
        return {
            "cpu_info": cpu_info,
            "cpu_count": cpu_count,
            "ram_total_gb": ram_total_gb,
            "platform": platform.system(),
            "platform_version": platform.version(),
            "libraries": libraries
        }
    except Exception as e:
        logger.warning(f"Failed to get some environment specs: {e}")
        return {
            "cpu_info": "unknown",
            "cpu_count": "unknown",
            "ram_total_gb": "unknown",
            "platform": platform.system(),
            "platform_version": platform.version(),
            "libraries": {
                "numpy": np.__version__,
                "python": sys.version.split()[0]
            }
        }


def generate_manifest(
    subset_corpus: Dict[str, Dict],
    dev_query_ids: List[str],
    test_query_ids: List[str],
    primary_dim: int,
    secondary_dim: int,
    actual_query_count: int,
    output_dir: pathlib.Path,
    bm25_index_built: bool
):
    """
    生成 manifest.json 文件，记录实验元数据。
    
    Args:
        subset_corpus: 文档子集
        dev_query_ids: 开发集查询ID列表
        test_query_ids: 测试集查询ID列表
        primary_dim: 主要模型的嵌入维度
        secondary_dim: 次要模型的嵌入维度
        actual_query_count: 实际查询数量
        output_dir: 输出目录
        bm25_index_built: BM25索引是否已构建
    """
    logger.info("Generating manifest.json...")
    
    # 构建相对路径（相对于输出目录）
    def rel_path(filename):
        return str(pathlib.Path(filename).name)
    
    # 获取环境信息
    env_specs = get_environment_specs()
    
    # 获取pyserini版本
    pyserini_version = "unknown"
    if PYSERINI_AVAILABLE:
        try:
            import pyserini
            pyserini_version = getattr(pyserini, "__version__", "unknown")
        except:
            pass
    
    manifest = {
        "source_dataset": DATASET_NAME,
        "subset_queries_count": actual_query_count,
        "subset_corpus_count": len(subset_corpus),
        "random_seed": RANDOM_SEED,
        "data_split": {
            "dev_queries_count": len(dev_query_ids),
            "test_queries_count": len(test_query_ids),
            "split_ratio": DEV_TEST_SPLIT_RATIO
        },
        "models": {
            "primary": {
                "name": PRIMARY_MODEL,
                "dimension": primary_dim
            },
            "secondary": {
                "name": SECONDARY_MODEL,
                "dimension": secondary_dim
            }
        },
        "environment_specs": env_specs,
        "data_hygiene": {
            "stats_file": rel_path("stats.json"),
            "checksums_file": rel_path("checksums.json")
        },
        "prebuilt_indexes": {
            "bm25": {
                "path": rel_path("bm25_index/") if bm25_index_built else None,
                "tool": "pyserini" if bm25_index_built else None,
                "version": pyserini_version if bm25_index_built else None,
                "available": bm25_index_built
            }
        },
        "output_files": {
            "corpus_metadata": rel_path("processed_corpus.jsonl"),
            "primary_embeddings": rel_path("embeddings_primary.npy"),
            "secondary_embeddings": rel_path("embeddings_secondary.npy"),
            "queries_subset": rel_path(f"queries_subset_{actual_query_count}.jsonl"),
            "qrels_subset": rel_path(f"qrels_subset_{actual_query_count}.tsv"),
            "queries_dev": rel_path("queries_dev.jsonl"),
            "qrels_dev": rel_path("qrels_dev.tsv"),
            "queries_test": rel_path("queries_test.jsonl"),
            "qrels_test": rel_path("qrels_test.tsv"),
            "primary_query_embeddings": rel_path("query_embeddings_primary.npy"),
            "secondary_query_embeddings": rel_path("query_embeddings_secondary.npy")
        }
    }
    
    manifest_path = output_dir / "manifest.json"
    logger.info(f"Saving manifest to {manifest_path}")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    logger.info("Manifest generated successfully")


def main():
    """
    主函数：执行完整的数据准备流程。
    """
    logger.info("=" * 80)
    logger.info("Data Preparation Script Started (V3)")
    logger.info("=" * 80)
    
    try:
        # 1. 加载完整数据集
        corpus, queries, qrels = load_full_dataset()
        
        # 2. 创建确定性子集（返回查询和qrels子集）
        subset_corpus, subset_query_ids, subset_queries, subset_qrels = create_deterministic_subset(
            corpus, queries, qrels
        )
        
        # 3. 根据实际查询数量动态创建输出目录
        actual_query_count = len(subset_query_ids)
        final_output_dir = OUTPUT_BASE_DIR / f"fiqa_{actual_query_count}"
        logger.info(f"Output directory: {final_output_dir}")
        
        # 4. 保存查询子集和qrels（使用动态命名）
        save_subset_queries_and_qrels(subset_queries, subset_qrels, actual_query_count, final_output_dir)
        
        # 5. 划分dev/test集
        dev_query_ids, test_query_ids = split_dev_test(subset_query_ids)
        
        # 6. 保存dev/test划分
        save_dev_test_splits(dev_query_ids, test_query_ids, subset_queries, subset_qrels, final_output_dir)
        
        # 7. 初始化嵌入模型
        primary_model, secondary_model, primary_dim, secondary_dim = initialize_embedding_models()
        
        # 8. 预计算文档嵌入向量并准备数据
        processed_data, primary_embeddings, secondary_embeddings = precompute_document_embeddings(
            subset_corpus,
            primary_model,
            secondary_model,
            final_output_dir
        )
        
        # 9. 计算文本统计信息
        text_stats = compute_text_statistics(processed_data)
        
        # 10. 保存处理后的文档数据
        save_processed_data(
            processed_data,
            primary_embeddings,
            secondary_embeddings,
            final_output_dir
        )
        
        # 11. 构建BM25索引
        corpus_jsonl_path = final_output_dir / "processed_corpus.jsonl"
        bm25_index_built = build_bm25_index(corpus_jsonl_path, final_output_dir)
        
        # 12. 预计算查询嵌入向量
        precompute_query_embeddings(
            subset_queries,
            primary_model,
            secondary_model,
            final_output_dir
        )
        
        # 13. 计算文件校验和
        checksums = compute_file_checksums(final_output_dir)
        
        # 14. 保存统计信息和校验和
        save_stats_and_checksums(
            text_stats,
            len(subset_corpus),
            actual_query_count,
            checksums,
            final_output_dir
        )
        
        # 15. 生成 manifest.json
        generate_manifest(
            subset_corpus,
            dev_query_ids,
            test_query_ids,
            primary_dim,
            secondary_dim,
            actual_query_count,
            final_output_dir,
            bm25_index_built
        )
        
        logger.info("=" * 80)
        logger.info("Data Preparation Completed Successfully!")
        logger.info(f"Output directory: {final_output_dir.absolute()}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during data preparation: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
