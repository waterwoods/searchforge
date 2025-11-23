#!/usr/bin/env python3
"""
prepare_airbnb_la.py - Airbnb Los Angeles 数据清洗脚本

读取原始 CSV 文件，清洗并转换为 JSONL 格式，用于后续向量化。

用法:
    python scripts/prepare_airbnb_la.py [--input data/airbnb_la/raw/listings.csv] [--output data/airbnb_la/processed/listings_clean.jsonl] [--max-docs 5000]
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# ============================================================================
# 配置常量
# ============================================================================

# 默认路径
DEFAULT_INPUT_CSV = "data/airbnb_la/raw/listings.csv"
DEFAULT_OUTPUT_JSONL = "data/airbnb_la/processed/listings_clean.jsonl"
DEFAULT_MAX_DOCS = 5000  # Demo 用途，限制文档数

# 文本截断长度（字符）
MAX_TEXT_LENGTH = 2000


# ============================================================================
# 清洗函数
# ============================================================================

def clean_price(price_str: Optional[str]) -> float:
    """
    清洗价格字段。
    
    规则:
    - 去掉 $ 符号、逗号
    - 转为 float
    - 缺失值/无效值返回 0.0
    
    Args:
        price_str: 原始价格字符串，例如 "$250.00" 或 "1,500"
        
    Returns:
        float: 清洗后的价格，缺失时返回 0.0
    """
    if not price_str or not isinstance(price_str, str):
        return 0.0
    
    # 去掉 $ 符号和逗号
    cleaned = re.sub(r'[\$,]', '', price_str.strip())
    
    try:
        price = float(cleaned)
        # 确保价格非负
        return max(0.0, price)
    except (ValueError, TypeError):
        return 0.0


def clean_int(value: Optional[str], default: int = 0) -> int:
    """
    清洗整数字段。
    
    规则:
    - 转为 int
    - 缺失值/无效值返回 default
    
    Args:
        value: 原始值（字符串或数字）
        default: 缺失时的默认值（默认 0）
        
    Returns:
        int: 清洗后的整数值
    """
    if value is None:
        return default
    
    # 如果是字符串，尝试转换
    if isinstance(value, str):
        value = value.strip()
        if not value or value.lower() in ['', 'null', 'none', 'nan']:
            return default
    
    try:
        # 先转为 float，再转为 int（处理 "2.0" 这种情况）
        result = int(float(value))
        return max(0, result)  # 确保非负
    except (ValueError, TypeError):
        return default


def clean_text(text: Optional[str]) -> str:
    """
    清洗文本字段。
    
    规则:
    - 去除前后空白
    - 将多个空白字符替换为单个空格
    - 空值返回空字符串
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清洗后的文本
    """
    if not text or not isinstance(text, str):
        return ""
    
    # 去除前后空白，规范化空白字符
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned


def build_description_text(row: Dict[str, Any]) -> str:
    """
    构造房源描述文本。
    
    策略:
    1. 拼接字段：name + neighbourhood + room_type + summary/description
    2. 文本截断：最大 MAX_TEXT_LENGTH 字符
    3. 兜底生成：如果所有文本字段为空，生成结构化描述
    
    Args:
        row: CSV 行数据（字典）
        
    Returns:
        str: 构造的描述文本
    """
    parts = []
    
    # 1. 房源名称
    name = clean_text(row.get('name'))
    if name:
        parts.append(name)
    
    # 2. 社区信息
    neighbourhood = clean_text(row.get('neighbourhood_cleansed') or row.get('neighbourhood'))
    if neighbourhood:
        parts.append(f"in {neighbourhood}")
    
    # 3. 房间类型
    room_type = clean_text(row.get('room_type'))
    if room_type:
        parts.append(f"({room_type})")
    
    # 4. 房源摘要（优先）
    summary = clean_text(row.get('summary'))
    if summary:
        parts.append(summary)
    
    # 5. 房源描述（如果摘要不存在）
    description = clean_text(row.get('description'))
    if description and not summary:
        parts.append(description)
    
    # 6. 社区概览（补充信息）
    neighborhood_overview = clean_text(row.get('neighborhood_overview'))
    if neighborhood_overview:
        parts.append(neighborhood_overview)
    
    # 拼接所有部分
    combined = ". ".join(filter(None, parts))
    
    # 如果所有文本字段都为空，生成兜底描述
    if not combined.strip():
        price = clean_price(row.get('price'))
        bedrooms = clean_int(row.get('bedrooms'))
        room_type = clean_text(row.get('room_type')) or "room"
        neighbourhood = clean_text(row.get('neighbourhood_cleansed') or row.get('neighbourhood')) or "Los Angeles"
        
        combined = f"A {bedrooms}-bedroom {room_type} in {neighbourhood} priced at ${price:.0f} per night."
    
    # 截断到最大长度
    if len(combined) > MAX_TEXT_LENGTH:
        combined = combined[:MAX_TEXT_LENGTH].rsplit(' ', 1)[0] + "..."
    
    return combined


def process_row(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    处理单行 CSV 数据。
    
    Args:
        row: CSV 行数据（字典）
        
    Returns:
        dict: 处理后的文档字典，如果无效则返回 None
    """
    # 获取 ID（必须存在）
    listing_id = row.get('id')
    if not listing_id:
        return None
    
    # 转为字符串
    listing_id = str(listing_id).strip()
    if not listing_id:
        return None
    
    # 构造文档
    doc = {
        "id": listing_id,
        "text": build_description_text(row),  # 主文本字段（必须）
        "title": clean_text(row.get('name')) or f"Listing {listing_id}",
        "price": clean_price(row.get('price')),
        "bedrooms": clean_int(row.get('bedrooms')),
        "accommodates": clean_int(row.get('accommodates')),
        "neighbourhood": clean_text(row.get('neighbourhood_cleansed') or row.get('neighbourhood')),
        "room_type": clean_text(row.get('room_type')),
        "minimum_nights": clean_int(row.get('minimum_nights')),
        "availability_365": clean_int(row.get('availability_365')),
    }
    
    # 确保 text 字段不为空（兜底）
    if not doc["text"]:
        price = doc["price"]
        bedrooms = doc["bedrooms"]
        room_type = doc["room_type"] or "room"
        neighbourhood = doc["neighbourhood"] or "Los Angeles"
        doc["text"] = f"A {bedrooms}-bedroom {room_type} in {neighbourhood} priced at ${price:.0f} per night."
    
    return doc


# ============================================================================
# 主函数
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="清洗 Inside Airbnb Los Angeles CSV 数据并转换为 JSONL"
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_CSV,
        help=f"输入 CSV 文件路径（默认: {DEFAULT_INPUT_CSV}）"
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_JSONL,
        help=f"输出 JSONL 文件路径（默认: {DEFAULT_OUTPUT_JSONL}）"
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=DEFAULT_MAX_DOCS,
        help=f"最大文档数（默认: {DEFAULT_MAX_DOCS}，用于 demo）"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子（用于可复现性，默认: 42）"
    )
    
    args = parser.parse_args()
    
    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 错误: 输入文件不存在: {input_path}", file=sys.stderr)
        print(f"提示: 请从 https://insideairbnb.com/get-the-data/ 下载 listings.csv 到 {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # 创建输出目录
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取 CSV
    print(f"[读取] 从 {input_path} 读取 CSV 数据...")
    docs = []
    skipped = 0
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            # 使用 csv.DictReader 自动处理表头
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):  # 从第 2 行开始（第 1 行是表头）
                try:
                    doc = process_row(row)
                    if doc:
                        docs.append(doc)
                    else:
                        skipped += 1
                except Exception as e:
                    print(f"[警告] 第 {row_num} 行处理失败: {e}", file=sys.stderr)
                    skipped += 1
                    continue
                
                # 限制文档数
                if len(docs) >= args.max_docs:
                    print(f"[限制] 已达到最大文档数 {args.max_docs}，停止读取")
                    break
    
    except Exception as e:
        print(f"❌ 错误: 读取 CSV 文件失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"[统计] 读取完成: 成功 {len(docs)} 条，跳过 {skipped} 条")
    
    # 如果指定了随机种子，对文档进行固定排序（保证可复现）
    if args.seed is not None:
        import random
        random.seed(args.seed)
        # 按 ID 排序保证可复现
        docs.sort(key=lambda x: x["id"])
        print(f"[排序] 使用随机种子 {args.seed}，按 ID 排序")
    
    # 截断到最大文档数
    if len(docs) > args.max_docs:
        docs = docs[:args.max_docs]
        print(f"[截断] 截断到 {args.max_docs} 条文档")
    
    # 写入 JSONL
    print(f"[写入] 写入 JSONL 到 {output_path}...")
    written = 0
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for doc in docs:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
                written += 1
        
        print(f"[完成] 成功写入 {written} 条文档到 {output_path}")
        
    except Exception as e:
        print(f"❌ 错误: 写入 JSONL 文件失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 输出统计信息
    print("\n[统计] 数据清洗完成:")
    print(f"  - 总文档数: {written}")
    print(f"  - 包含价格的文档: {sum(1 for d in docs if d['price'] > 0)}")
    print(f"  - 包含卧室数的文档: {sum(1 for d in docs if d['bedrooms'] > 0)}")
    print(f"  - 平均价格: ${sum(d['price'] for d in docs) / len(docs) if docs else 0:.2f}")
    print(f"  - 平均卧室数: {sum(d['bedrooms'] for d in docs) / len(docs) if docs else 0:.2f}")
    print(f"\n✅ 清洗完成！输出文件: {output_path}")


if __name__ == '__main__':
    main()

