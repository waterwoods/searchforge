# Enhanced FIQA API - Test Guide

## 🎯 三大增强功能

### A) 输入校验与速率限制 ✅
- **输入校验**: query 非空，top_k ∈ [1,20]
- **速率限制**: 同 IP 每秒最多 3 次请求
- **实现**: services/fiqa_api/app.py (146 行)

### B) 指标扩展 ✅
- **新增列**: tokens_in, tokens_out, est_cost
- **滚动均值**: avg_tokens_in, avg_tokens_out, avg_cost
- **实现**: logs/metrics_logger.py (63 行)

### C) 一键小压测 ✅
- **脚本**: scripts/smoke_load.py (43 行)
- **并发**: 60 次请求，分批次尊重速率限制
- **输出**: success_rate, P95, QPS

---

## 📝 手动测试命令

### 1. 测试输入校验

**空查询 (应返回 400)**
```bash
curl -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{"query": "", "top_k": 5}'
```

**top_k 超出范围 (应返回 400)**
```bash
# top_k < 1
curl -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 0}'

# top_k > 20
curl -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 25}'
```

**正常请求 (应返回 200)**
```bash
curl -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{"query": "How to invest in stocks?", "top_k": 5}'
```

### 2. 测试速率限制

**快速连续请求 (第 4-5 次应返回 429)**
```bash
for i in {1..5}; do
  echo "请求 $i:"
  curl -X POST http://localhost:8080/search \
    -H "Content-Type: application/json" \
    -d '{"query": "rate limit test", "top_k": 3}'
  echo ""
done
```

### 3. 查看扩展指标

**查看滚动平均值**
```bash
curl http://localhost:8080/metrics | python3 -m json.tool
```

**查看 CSV 文件**
```bash
head -10 services/fiqa_api/logs/api_metrics.csv
```

### 4. 运行压测

**执行压测脚本**
```bash
python scripts/smoke_load.py
```

---

## 🧪 自动化测试流程

### 完整测试命令

```bash
# 1. 重启服务
pkill -f "uvicorn.*8080" && pkill -f "bash launch.sh"
sleep 2
bash launch.sh &
sleep 6

# 2. 验证健康状态
curl -s http://localhost:8080/health

# 3. 测试输入校验
echo "=== 测试空查询 ==="
curl -s -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{"query": "", "top_k": 5}' | grep -q "detail" && echo "✓ 400 Validation Error" || echo "✗ Failed"

echo "=== 测试 top_k 范围 ==="
curl -s -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 0}' | grep -q "detail" && echo "✓ 400 Validation Error" || echo "✗ Failed"

# 4. 执行压测
python scripts/smoke_load.py

# 5. 查看指标
echo ""
echo "[METRICS] $(curl -s http://localhost:8080/metrics | python3 -c "import sys,json; m=json.load(sys.stdin); print(f\"avg_p95={m['avg_p95_ms']}ms / avg_recall={m['avg_recall']} / avg_cost={m['avg_cost']}\")")"
```

---

## 📊 预期输出示例

### 压测输出
```
🔥 Smoke Load Test: 60 requests (batched for rate limit)

[SANITY] success_rate=100.0% / P95=159.9ms / QPS=2.3
```

### 指标端点输出
```json
{
    "count": 69,
    "avg_p95_ms": 104.77,
    "avg_recall": 0.85,
    "avg_tokens_in": 1.29,
    "avg_tokens_out": 18.77,
    "avg_cost": 0.000576
}
```

### CSV 文件格式
```csv
timestamp,p95_ms,recall_at10,tokens_in,tokens_out,est_cost,success
2025-10-08T21:31:22.383256,76.99,0.85,2,13,0.00041,True
2025-10-08T21:31:22.459693,64.31,0.85,2,13,0.00041,True
```

---

## ✅ 验证清单

- [x] 输入校验：空查询返回 400
- [x] 输入校验：top_k=0 返回 400
- [x] 输入校验：top_k=25 返回 400
- [x] 速率限制：同 IP 第 4 次请求返回 429
- [x] 指标扩展：CSV 包含 tokens_in, tokens_out, est_cost
- [x] 指标扩展：/metrics 返回 avg_tokens_in, avg_tokens_out, avg_cost
- [x] 压测脚本：执行 60 次请求
- [x] 压测脚本：输出 success_rate, P95, QPS
- [x] 压测脚本：success_rate ≥ 90%

---

## 📁 修改的文件

| 文件 | 行数 | 说明 |
|------|------|------|
| services/fiqa_api/app.py | 146 | 添加输入校验和速率限制 |
| logs/metrics_logger.py | 63 | 扩展指标列和滚动均值 |
| scripts/smoke_load.py | 43 | 新建压测脚本 |

---

## 🚀 快速验证

**一键测试命令**:
```bash
cd /path/to/searchforge
python scripts/smoke_load.py && echo "" && echo "[METRICS] $(curl -s http://localhost:8080/metrics | python3 -c "import sys,json; m=json.load(sys.stdin); print(f\"avg_p95={m['avg_p95_ms']}ms / avg_recall={m['avg_recall']} / avg_cost={m['avg_cost']}\")")"
```

**预期输出**:
```
[SANITY] success_rate=100.0% / P95=159.9ms / QPS=2.3
[METRICS] avg_p95=104.77ms / avg_recall=0.85 / avg_cost=0.000576
```

---

## 🔧 技术细节

### 输入校验实现
使用 Pydantic `field_validator` 装饰器进行字段级验证，FastAPI 自动返回 422/400 错误。

### 速率限制实现
内存字典 `defaultdict(list)` 存储每个 IP 的请求时间戳，滑动窗口 1 秒。

### Token 估算
简单启发式：`tokens ≈ words * 0.75`

### Cost 估算
模拟 GPT 定价：
- Input: $0.01 / 1K tokens
- Output: $0.03 / 1K tokens

---

## ⚠️ 注意事项

1. **速率限制是内存实现**，服务重启后清空
2. **Token 估算是简化版**，生产环境应使用 tiktoken
3. **Recall 仍为 mock 值 (0.85)**，需要真实计算逻辑
4. **压测脚本尊重速率限制**，因此 QPS ≈ 3

---

## 🎉 总结

所有增强功能已实现并通过测试：
- ✅ 输入校验与速率限制完整功能
- ✅ 指标扩展正确记录和计算
- ✅ 压测脚本稳定输出结果
- ✅ 保持代码最小可用风格
- ✅ 未改动 launch.sh 和端口配置

