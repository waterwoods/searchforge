#!/usr/bin/env python3
"""
FiQA ID Sanity Check Script
检查 beir_fiqa_full_ta 集合中的文档ID是否与BEIR corpus对齐
"""

import json
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.search.vector_search import VectorSearch

def load_corpus_keys():
    """加载BEIR corpus中的所有文档ID"""
    corpus_keys = set()
    with open('data/fiqa/corpus.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                doc = json.loads(line)
                corpus_keys.add(doc['_id'])
    return corpus_keys

def check_collection_ids(collection_name, sample_size=10):
    """检查集合中的文档ID"""
    print(f"🔍 检查集合: {collection_name}")
    
    # 加载BEIR corpus keys
    corpus_keys = load_corpus_keys()
    print(f"📚 BEIR corpus包含 {len(corpus_keys)} 个文档")
    
    # 初始化向量搜索
    vs = VectorSearch()
    
    try:
        # 获取集合中的一些随机文档
        result = vs.client.scroll(
            collection_name=collection_name,
            limit=sample_size
        )
        
        if not result[0]:
            print(f"❌ 集合 {collection_name} 为空")
            return False
        
        print(f"\n📋 随机采样 {len(result[0])} 个文档:")
        print("=" * 80)
        
        all_valid = True
        for i, point in enumerate(result[0]):
            point_id = point.id
            payload = point.payload or {}
            doc_id = payload.get("doc_id")
            title = payload.get("title", "")
            
            print(f"{i+1:2d}. Point ID: {point_id}")
            print(f"    Payload doc_id: {doc_id}")
            print(f"    Title: {title[:50]}{'...' if len(title) > 50 else ''}")
            
            # 检查payload.doc_id是否存在
            if doc_id is None:
                print(f"    ❌ payload.doc_id 缺失")
                all_valid = False
            elif doc_id not in corpus_keys:
                print(f"    ❌ payload.doc_id '{doc_id}' 不在BEIR corpus中")
                all_valid = False
            else:
                print(f"    ✅ payload.doc_id '{doc_id}' 在BEIR corpus中")
            
            print()
        
        if all_valid:
            print("✅ 所有采样的文档都有有效的payload.doc_id且在BEIR corpus中")
            return True
        else:
            print("❌ 发现无效的文档ID，需要重新导入集合")
            return False
            
    except Exception as e:
        print(f"❌ 检查集合时出错: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="FiQA ID Sanity Check")
    parser.add_argument("--collection", default="beir_fiqa_full_ta", help="Collection name to check")
    parser.add_argument("--sample-size", type=int, default=10, help="Number of documents to sample")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔍 FiQA ID Sanity Check")
    print("=" * 80)
    
    is_valid = check_collection_ids(args.collection, args.sample_size)
    
    print("=" * 80)
    if is_valid:
        print("✅ 数据自检通过")
        exit(0)
    else:
        print("❌ 数据自检失败 - 需要重新导入集合")
        exit(1)

if __name__ == "__main__":
    main()
