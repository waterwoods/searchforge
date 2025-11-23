#!/usr/bin/env bash
# Verify doc_id coverage in qrels after restoration

set -euo pipefail

# paths
QRELS=experiments/data/fiqa/fiqa_qrels_hard_50k_v1.tsv
COLL=fiqa_para_50k
BASE=${BASE:-http://localhost:6333}

echo "1) 抓 20 个随机 doc_id + 指定 000455"

python3 <<PY | tee .runs/check_ids.txt
import random
from qdrant_client import QdrantClient

COLL = "$COLL"
BASE = "$BASE"

# Connect to Qdrant
client = QdrantClient(url=BASE, prefer_grpc=False)

# Get sample points
points, _ = client.scroll(
    collection_name=COLL,
    limit=200,
    with_payload=True,
    with_vectors=False
)

# Extract doc_ids
ids = []
for p in points:
    doc_id = p.payload.get("doc_id")
    if doc_id:
        ids.append(str(doc_id))

# Shuffle and take 20
random.shuffle(ids)
ids = ids[:20]

# Force add 000455
ids.append("000455")

print("\n".join([i for i in ids if i]))
PY

echo "2) 在 qrels 中核对出现次数（应当全部>0）"
echo "   注意：doc_id 格式可能不同（零填充 vs 数字），需要标准化比较"

# Normalize doc_ids: remove leading zeros for comparison
python3 <<PY2 | tee .runs/check_ids_report.txt
import re

# Read collection doc_ids
with open('.runs/check_ids.txt', 'r') as f:
    coll_ids = [line.strip() for line in f if line.strip()]

# Normalize: convert to int then back to string to remove leading zeros
normalized_coll = {}
for id in coll_ids:
    try:
        # Try to convert to int to remove leading zeros
        normalized = str(int(id))
        normalized_coll[normalized] = id  # Keep original for reporting
    except ValueError:
        # If not a number, keep as is
        normalized_coll[id] = id

# Read qrels doc_ids
qrels_ids = set()
with open("$QRELS", 'r') as f:
    for line in f:
        if line.strip():
            parts = line.split('\t')
            if len(parts) >= 2:
                qrels_ids.add(parts[1].strip())

# Check coverage
total = len(normalized_coll)
ok = 0
missing = []

for norm_id, orig_id in normalized_coll.items():
    if norm_id in qrels_ids:
        ok += 1
    else:
        missing.append(orig_id)

coverage = (ok * 100.0 / total) if total > 0 else 0
print(f"total= {total}  ok= {ok}  coverage= {coverage:.1f}%")

if missing:
    print("MISSING:")
    for id in missing:
        print(id)
PY2

echo "3) 单点核对：展示 qrels 中与 000455 相关的前几行"
# Normalize 000455 to 455 for search
grep -n -m 5 -E $'\t455$' "$QRELS" || echo "qrels 未找到 455 (normalized from 000455)"

echo ""
echo "========================================================================"
echo "验收说明："
echo "  - 这是 HARD qrels 文件，只包含部分 doc_id（hard subset）"
echo "  - Hard qrels 包含 ~11,303 个唯一 doc_id，而集合有 50,000 个"
echo "  - 因此覆盖率不会达到 100%，这是正常的"
echo "  - 如果覆盖率 > 20%，说明 doc_id 恢复基本正确"
echo "  - 缺失的 doc_id 可能是因为它们不在 hard qrels 中（正常情况）"
echo "========================================================================"
echo ""
echo "完整报告已保存到: .runs/check_ids_report.txt"
