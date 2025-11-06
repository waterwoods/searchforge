#!/bin/bash
# Judger Pack 快速验证脚本

set -e

echo "🧪 Judger Pack 系统验证"
echo "========================"
echo ""

# 检查必需文件
echo "1️⃣ 检查文件..."
if [ ! -f "scripts/judger_sample.py" ]; then
    echo "❌ 采样器不存在"
    exit 1
fi
if [ ! -f "services/fiqa_api/templates/judge.html" ]; then
    echo "❌ 标注页模板不存在"
    exit 1
fi
echo "✅ 所有必需文件存在"
echo ""

# 运行采样器
echo "2️⃣ 生成测试批次..."
python scripts/judger_sample.py --n 10
echo ""

# 检查生成的文件
BATCH_FILE=$(ls -t reports/judge_batch_*.json | head -1)
if [ ! -f "$BATCH_FILE" ]; then
    echo "❌ 批次文件未生成"
    exit 1
fi
BATCH_ID=$(basename "$BATCH_FILE" | sed 's/judge_batch_//' | sed 's/.json//')
echo "✅ 批次已生成: $BATCH_ID"
echo ""

# 检查批次内容
echo "3️⃣ 验证批次数据..."
TOTAL=$(cat "$BATCH_FILE" | python3 -c "import json,sys; print(json.load(sys.stdin)['total'])")
echo "   样本数: $TOTAL"
if [ "$TOTAL" -lt 1 ]; then
    echo "❌ 批次数据无效"
    exit 1
fi
echo "✅ 批次数据有效"
echo ""

# 模拟投票
echo "4️⃣ 模拟投票数据..."
VOTE_FILE="reports/judge_votes_${BATCH_ID}.jsonl"
cat > "$VOTE_FILE" << EOF
{"batch_id": "$BATCH_ID", "qid": 0, "pick": "on", "reason": "测试投票1", "timestamp": $(date +%s), "ts_iso": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
{"batch_id": "$BATCH_ID", "qid": 1, "pick": "on", "reason": "测试投票2", "timestamp": $(date +%s), "ts_iso": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
{"batch_id": "$BATCH_ID", "qid": 2, "pick": "same", "reason": "测试投票3", "timestamp": $(date +%s), "ts_iso": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
{"batch_id": "$BATCH_ID", "qid": 3, "pick": "on", "reason": "测试投票4", "timestamp": $(date +%s), "ts_iso": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
{"batch_id": "$BATCH_ID", "qid": 4, "pick": "off", "reason": "测试投票5", "timestamp": $(date +%s), "ts_iso": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF
echo "✅ 已创建 5 条模拟投票"
echo ""

# 验证投票文件
echo "5️⃣ 验证投票数据..."
VOTE_COUNT=$(wc -l < "$VOTE_FILE" | tr -d ' ')
echo "   投票数: $VOTE_COUNT"
if [ "$VOTE_COUNT" -ne 5 ]; then
    echo "❌ 投票数据异常"
    exit 1
fi
echo "✅ 投票数据有效"
echo ""

echo "========================"
echo "✅ 所有验证通过！"
echo ""
echo "📍 下一步："
echo "   1. 启动 API: cd services/fiqa_api && uvicorn app:app --host 0.0.0.0 --port 8080"
echo "   2. 访问标注页: http://localhost:8080/judge?batch=$BATCH_ID"
echo "   3. 查看汇总: curl http://localhost:8080/judge/summary.json | jq"
echo "   4. 查看面板: http://localhost:8080/debug"
echo ""


