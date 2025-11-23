#!/usr/bin/env python3
"""
import_airbnb_la_to_qdrant.py - 将清洗后的 Airbnb LA 数据向量化并导入 Qdrant

读取清洗后的 JSONL 文件，使用与现有 RAG pipeline 一致的 embedding 模型进行向量化，
然后批量写入 Qdrant collection `airbnb_la_demo`。

用法:
    python scripts/import_airbnb_la_to_qdrant.py [--input data/airbnb_la/processed/listings_clean.jsonl] [--collection airbnb_la_demo] [--recreate]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    HnswConfigDiff,
    PayloadSchemaType,
)
from tqdm import tqdm

# ============================================================================
# 配置常量
# ============================================================================

# 默认路径
DEFAULT_INPUT_JSONL = "data/airbnb_la/processed/listings_clean.jsonl"
DEFAULT_COLLECTION = "airbnb_la_demo"

# Embedding 配置（必须与现有 RAG pipeline 一致）
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 的维度

# 批量处理配置
BATCH_SIZE = 64  # Embedding batch size
UPSERT_BATCH_SIZE = 128  # Qdrant upsert batch size

# Qdrant 连接配置（从环境变量读取，否则使用默认值）
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_URL = os.getenv("QDRANT_URL", f"http://{QDRANT_HOST}:{QDRANT_PORT}")

# HNSW 索引参数（可选，使用默认值）
HNSW_M = 16  # 默认值
HNSW_EF_CONSTRUCT = 200  # 默认值


# ============================================================================
# 加载和初始化
# ============================================================================

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """
    加载 JSONL 文件。
    
    Args:
        path: JSONL 文件路径
        
    Returns:
        List[Dict]: 文档列表
    """
    docs = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
                docs.append(doc)
            except json.JSONDecodeError as e:
                print(f"[警告] 第 {line_num} 行 JSON 解析失败: {e}", file=sys.stderr)
                continue
    return docs


def get_embedder():
    """
    获取 embedding 模型（复用现有 RAG pipeline 的配置）。
    
    优先使用 services/fiqa_api/clients.py 的 get_embedder()，
    如果不可用则直接加载 SentenceTransformer。
    
    Returns:
        SentenceTransformer 或 FastEmbedder 实例
    """
    # 尝试使用现有的 clients 模块（如果可用）
    try:
        import sys
        from pathlib import Path
        
        # 添加项目根目录到 sys.path
        project_root = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(project_root))
        
        from services.fiqa_api.clients import get_embedder as _get_embedder
        embedder = _get_embedder()
        if embedder is not None:
            print(f"[EMBEDDER] 使用现有的 embedder (backend: {os.getenv('EMBEDDING_BACKEND', 'FASTEMBED')})")
            return embedder
    except (ImportError, Exception) as e:
        print(f"[EMBEDDER] 无法使用现有 embedder，回退到 SentenceTransformer: {e}")
    
    # 回退：直接使用 SentenceTransformer
    from sentence_transformers import SentenceTransformer
    print(f"[EMBEDDER] 加载 SentenceTransformer 模型: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"[EMBEDDER] 模型维度: {model.get_sentence_embedding_dimension()}")
    return model


def encode_batch(embedder, texts: List[str], batch_size: int = BATCH_SIZE) -> List[List[float]]:
    """
    批量编码文本为向量。
    
    Args:
        embedder: Embedding 模型（SentenceTransformer 或 FastEmbedder）
        texts: 文本列表
        batch_size: 批量大小
        
    Returns:
        List[List[float]]: 向量列表
    """
    vectors = []
    
    # 检查 embedder 类型
    if hasattr(embedder, 'encode') and callable(embedder.encode):
        # SentenceTransformer 或 FastEmbedder
        try:
            # FastEmbedder: encode(list[str]) -> np.ndarray
            if hasattr(embedder, '__class__') and 'FastEmbedder' in str(embedder.__class__):
                for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
                    batch = texts[i:i + batch_size]
                    batch_vectors = embedder.encode(batch)
                    # FastEmbedder 返回 numpy array
                    if hasattr(batch_vectors, 'tolist'):
                        vectors.extend(batch_vectors.tolist())
                    else:
                        vectors.extend(batch_vectors)
            else:
                # SentenceTransformer: encode(list[str]) -> np.ndarray
                for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
                    batch = texts[i:i + batch_size]
                    batch_vectors = embedder.encode(batch, show_progress_bar=False, normalize_embeddings=False)
                    if hasattr(batch_vectors, 'tolist'):
                        vectors.extend(batch_vectors.tolist())
                    else:
                        vectors.extend(batch_vectors)
        except Exception as e:
            print(f"[错误] Embedding 失败: {e}", file=sys.stderr)
            raise
    else:
        raise ValueError(f"不支持的 embedder 类型: {type(embedder)}")
    
    return vectors


# ============================================================================
# Qdrant Collection 管理
# ============================================================================

def create_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
    recreate: bool = False,
) -> None:
    """
    创建 Qdrant collection。
    
    Args:
        client: Qdrant 客户端
        collection_name: Collection 名称
        vector_size: 向量维度
        distance: 距离度量（默认 COSINE）
        recreate: 如果 collection 已存在，是否删除重建
    """
    # 如果 recreate=True，先删除现有 collection
    if recreate:
        try:
            print(f"[COLLECTION] 删除现有 collection '{collection_name}'...")
            client.delete_collection(collection_name)
            time.sleep(0.5)  # 等待删除完成
            print(f"[COLLECTION] 已删除 '{collection_name}'")
        except Exception as e:
            if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                print(f"[COLLECTION] Collection '{collection_name}' 不存在（将创建新的）")
            else:
                print(f"[警告] 删除 collection 时出错: {e}")
    
    # 检查 collection 是否存在
    if not recreate:
        try:
            info = client.get_collection(collection_name)
            points_count = getattr(info, 'points_count', 0)
            raise ValueError(
                f"Collection '{collection_name}' 已存在，包含 {points_count} 个点。"
                f"使用 --recreate 重建它。"
            )
        except ValueError:
            raise
        except Exception:
            # Collection 不存在，可以继续创建
            pass
    
    # 创建 collection
    print(f"[COLLECTION] 创建 '{collection_name}' (vector_size={vector_size}, distance={distance.value})...")
    
    # 构建向量配置（可选 HNSW 参数）
    vectors_config = VectorParams(
        size=vector_size,
        distance=distance,
        # 可选：自定义 HNSW 参数
        # hnsw_config=HnswConfigDiff(
        #     m=HNSW_M,
        #     ef_construct=HNSW_EF_CONSTRUCT,
        # ),
    )
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=vectors_config,
    )
    
    print(f"[COLLECTION] 已创建 '{collection_name}'")


def create_payload_indexes(
    client: QdrantClient,
    collection_name: str,
) -> None:
    """
    为 payload 字段创建索引（用于过滤）。
    
    Args:
        client: Qdrant 客户端
        collection_name: Collection 名称
    """
    print(f"[INDEX] 为 '{collection_name}' 创建 payload 索引...")
    
    indexes = [
        ("price", PayloadSchemaType.FLOAT),
        ("bedrooms", PayloadSchemaType.INTEGER),
        ("neighbourhood", PayloadSchemaType.KEYWORD),
        ("room_type", PayloadSchemaType.KEYWORD),
    ]
    
    for field_name, schema_type in indexes:
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema_type,
            )
            print(f"[INDEX] ✓ 已创建索引: {field_name} ({schema_type.value})")
        except Exception as e:
            # 如果索引已存在或其他错误，继续
            if "already exists" in str(e).lower():
                print(f"[INDEX] - 索引已存在: {field_name}")
            else:
                print(f"[警告] 创建索引 {field_name} 失败: {e}")


def upsert_documents(
    client: QdrantClient,
    collection_name: str,
    docs: List[Dict[str, Any]],
    vectors: List[List[float]],
    batch_size: int = UPSERT_BATCH_SIZE,
) -> None:
    """
    批量写入文档到 Qdrant。
    
    Args:
        client: Qdrant 客户端
        collection_name: Collection 名称
        docs: 文档列表（包含 id, text, title 等字段）
        vectors: 向量列表（与 docs 一一对应）
        batch_size: 批量大小
    """
    if len(docs) != len(vectors):
        raise ValueError(f"文档数 ({len(docs)}) 与向量数 ({len(vectors)}) 不匹配")
    
    print(f"[UPSERT] 准备写入 {len(docs)} 个文档到 '{collection_name}'...")
    
    points = []
    for doc, vector in zip(docs, vectors):
        # 将字符串 ID 转换为整数或 UUID（Qdrant 要求）
        # 优先尝试直接转换为整数，否则使用哈希值
        doc_id_str = str(doc["id"])
        try:
            # 尝试直接转换为整数
            point_id = int(doc_id_str)
            # 确保是正数且不超过 2^63-1（Qdrant 的限制）
            if point_id < 0 or point_id > 9223372036854775807:
                raise ValueError("ID out of range")
        except (ValueError, OverflowError):
            # 如果无法转换为整数，使用字符串的哈希值
            # 使用绝对值确保是正数，然后取模确保在合理范围内
            point_id = abs(hash(doc_id_str)) % 9223372036854775807
        
        # 构造 payload（包含所有字段）
        payload = {
            "doc_id": doc_id_str,  # 作为 doc_id（字符串，保持原始 listing ID）
            "text": doc["text"],  # 主文本字段（必须）
            "title": doc.get("title", ""),  # 标题
            "price": doc.get("price", 0.0),  # 价格（float）
            "bedrooms": doc.get("bedrooms", 0),  # 卧室数（int）
            "accommodates": doc.get("accommodates", 0),  # 可容纳人数（int）
            "neighbourhood": doc.get("neighbourhood", ""),  # 社区（string）
            "room_type": doc.get("room_type", ""),  # 房间类型（string）
            "minimum_nights": doc.get("minimum_nights", 0),  # 最少入住天数（int）
            "availability_365": doc.get("availability_365", 0),  # 全年可用天数（int）
        }
        
        point = PointStruct(
            id=point_id,  # 使用原始 listing ID
            vector=vector,
            payload=payload,
        )
        points.append(point)
    
    # 批量 upsert（带重试）
    total_batches = (len(points) + batch_size - 1) // batch_size
    for i in tqdm(range(0, len(points), batch_size), desc="Upserting"):
        batch = points[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        # 重试机制
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                client.upsert(
                    collection_name=collection_name,
                    points=batch,
                    wait=True,
                )
                break  # 成功，退出重试循环
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"[警告] Batch {batch_num}/{total_batches} 失败，{retry_delay:.1f}s 后重试: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    print(f"[错误] Batch {batch_num}/{total_batches} 重试 {max_retries} 次后仍失败: {e}", file=sys.stderr)
                    raise
    
    # 验证
    try:
        info = client.get_collection(collection_name)
        points_count = getattr(info, 'points_count', len(points))
        print(f"[UPSERT] 验证: '{collection_name}' 包含 {points_count} 个点")
    except Exception as e:
        print(f"[警告] 验证失败: {e}")


# ============================================================================
# 主函数
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="将清洗后的 Airbnb LA 数据向量化并导入 Qdrant"
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_JSONL,
        help=f"输入 JSONL 文件路径（默认: {DEFAULT_INPUT_JSONL}）"
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help=f"Qdrant collection 名称（默认: {DEFAULT_COLLECTION}）"
    )
    parser.add_argument(
        "--qdrant-url",
        default=QDRANT_URL,
        help=f"Qdrant URL（默认: {QDRANT_URL}）"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="如果 collection 已存在，删除重建"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Embedding 批量大小（默认: {BATCH_SIZE}）"
    )
    parser.add_argument(
        "--upsert-batch-size",
        type=int,
        default=UPSERT_BATCH_SIZE,
        help=f"Qdrant upsert 批量大小（默认: {UPSERT_BATCH_SIZE}）"
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=None,
        help="最大文档数（用于测试，默认: 无限制）"
    )
    
    args = parser.parse_args()
    
    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 错误: 输入文件不存在: {input_path}", file=sys.stderr)
        print(f"提示: 先运行 python scripts/prepare_airbnb_la.py 清洗数据", file=sys.stderr)
        sys.exit(1)
    
    # 加载文档
    print(f"[读取] 从 {input_path} 读取 JSONL 数据...")
    docs = load_jsonl(str(input_path))
    
    if not docs:
        print("❌ 错误: 没有读取到任何文档", file=sys.stderr)
        sys.exit(1)
    
    # 限制文档数（用于测试）
    if args.max_docs and len(docs) > args.max_docs:
        docs = docs[:args.max_docs]
        print(f"[限制] 限制到 {args.max_docs} 个文档")
    
    print(f"[统计] 读取完成: {len(docs)} 个文档")
    
    # 初始化 Qdrant 客户端
    print(f"[QDRANT] 连接到 {args.qdrant_url}...")
    try:
        if args.qdrant_url.startswith("http"):
            client = QdrantClient(url=args.qdrant_url)
        else:
            # 格式: localhost:6333
            host, port = args.qdrant_url.split(":") if ":" in args.qdrant_url else (args.qdrant_url, "6333")
            client = QdrantClient(host=host, port=int(port))
        
        # 测试连接
        client.get_collections()
        print(f"[QDRANT] 连接成功")
    except Exception as e:
        print(f"❌ 错误: 连接 Qdrant 失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 初始化 Embedding 模型
    print(f"[EMBEDDER] 初始化 embedding 模型...")
    embedder = get_embedder()
    
    # 验证维度
    if hasattr(embedder, 'get_sentence_embedding_dimension'):
        actual_dim = embedder.get_sentence_embedding_dimension()
    elif hasattr(embedder, 'dim'):
        actual_dim = embedder.dim
    else:
        # 测试编码一个示例文本以获取维度
        test_vector = embedder.encode(["test"])
        if hasattr(test_vector, 'shape'):
            actual_dim = test_vector.shape[-1] if len(test_vector.shape) > 1 else len(test_vector[0])
        else:
            actual_dim = len(test_vector[0]) if isinstance(test_vector, list) else len(test_vector)
    
    if actual_dim != EMBEDDING_DIM:
        print(f"⚠️  警告: Embedding 维度 ({actual_dim}) 与预期 ({EMBEDDING_DIM}) 不匹配", file=sys.stderr)
        print(f"   将继续使用实际维度 {actual_dim}")
        vector_size = actual_dim
    else:
        vector_size = EMBEDDING_DIM
    
    # 创建或获取 collection
    try:
        create_collection(
            client=client,
            collection_name=args.collection,
            vector_size=vector_size,
            distance=Distance.COSINE,
            recreate=args.recreate,
        )
    except ValueError as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 创建 payload 索引
    create_payload_indexes(client, args.collection)
    
    # 提取文本并编码
    print(f"[EMBEDDING] 编码 {len(docs)} 个文档...")
    texts = [doc["text"] for doc in docs]
    vectors = encode_batch(embedder, texts, batch_size=args.batch_size)
    
    if len(vectors) != len(docs):
        print(f"❌ 错误: 向量数 ({len(vectors)}) 与文档数 ({len(docs)}) 不匹配", file=sys.stderr)
        sys.exit(1)
    
    # 写入 Qdrant
    upsert_documents(
        client=client,
        collection_name=args.collection,
        docs=docs,
        vectors=vectors,
        batch_size=args.upsert_batch_size,
    )
    
    print("\n[完成] ✅ 导入完成!")
    print(f"  - Collection: {args.collection}")
    print(f"  - 文档数: {len(docs)}")
    print(f"  - 向量维度: {vector_size}")
    print(f"  - 距离度量: COSINE")


if __name__ == '__main__':
    main()

