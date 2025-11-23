#!/usr/bin/env bash
# Fast restore fiqa_para_50k doc_id (RTX3080 / andy-wsl)

set -euo pipefail

cd ~/searchforge

# 1) 确认权威映射存在
MAP_FILE=".runs/docid_map_fiqa_para_50k.json"
test -f "$MAP_FILE" || { echo "mapping not found: $MAP_FILE"; exit 1; }

# 转换为绝对路径
MAP_ABS=$(cd "$(dirname "$MAP_FILE")" && pwd)/$(basename "$MAP_FILE")
echo "[INFO] Using mapping file: $MAP_ABS"

# 获取映射文件中的条目数（作为期望值）
EXPECTED_COUNT=$(jq 'length' "$MAP_ABS")
echo "[INFO] Mapping file contains $EXPECTED_COUNT entries"

# 2) 回写 doc_id（不改向量与文本）
# 注意：有些点可能没有文本字段，所以匹配数可能略少于总数
make docid-apply COLLECTION=fiqa_para_50k MAP="$MAP_ABS" EXPECTED_COUNT="$EXPECTED_COUNT"

# 3) 验证（抽样200条必须0误差）
make docid-verify COLLECTION=fiqa_para_50k MAP="$MAP_ABS" SAMPLE=200 EXPECTED_COUNT="$EXPECTED_COUNT"

# 4) 冒烟质量检查（应 success_rate=1.0）
make policy-smoke

