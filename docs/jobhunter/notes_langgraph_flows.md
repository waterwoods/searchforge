# JobHunter LangGraph Flows 文档

本文档记录了 JobHunter 模块中的三个 LangGraph Flow 的使用方式和架构说明。

这是三个可复用的 LangGraph flow，方便以后挂到 Web / K8s / 评估系统上。

---

## Flow 1: JD 解读 + 适配度（单次分析闭环）

### 文件位置
- `services/fiqa_api/jobhunter/graphs/jd_analysis_graph.py`

### 功能
一次性完成 JD 解读和适配度分析，适用于单次分析场景。

### 输入
- `jd_input: JobJDInput` - JD 输入信息（包含 description、title、company 等）
- `candidate_profile: str | None` - 可选的候选人画像

### 输出
- `jd_summary: JobJDSummary` - JD 解读结果（金银铜要点、核心技能、推荐等）
- `fit_summary: JobFitSummary | None` - 适配度分析结果（优势、缺口、行动建议）

### 使用示例

#### Python 代码调用
```python
from services.fiqa_api.jobhunter.graphs.jd_analysis_graph import run_jd_analysis
from services.fiqa_api.jobhunter.schemas import JobJDInput

jd_input = JobJDInput(
    job_id="123",
    company="Anthropic",
    title="Staff Engineer",
    location="SF",
    description="...",
)

result = run_jd_analysis(jd_input, candidate_profile="...")
jd_summary = result["jd_summary"]
fit_summary = result["fit_summary"]
```

#### CLI 调用
```bash
# 使用默认候选人画像
python -m experiments.jobhunter.jd_explainer_cli \
  --from-scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
  --job-id 4741102008 \
  --use-default-profile
```

---

## Flow 2: JD 职业教练对话（多轮对话闭环）

### 文件位置
- `services/fiqa_api/jobhunter/graphs/jd_chat_graph.py`

### 功能
基于 JD 分析和适配度分析结果，提供多轮对话能力。支持用户提问关于职位要求、适配度、面试准备等问题。

### 输入
- `jd_input: JobJDInput` - JD 输入信息
- `jd_summary: JobJDSummary` - JD 解读结果（必需）
- `fit_summary: JobFitSummary | None` - 适配度分析结果（可选）
- `candidate_profile: str | None` - 候选人画像（可选）
- `history: List[Dict[str, str]]` - 对话历史
- `last_user_message: str` - 当前用户消息

### 输出
- `last_response: str` - 助手回复
- `history: List[Dict[str, str]]` - 更新后的对话历史（包含当前轮次）

### 使用示例

#### Python 代码调用
```python
from services.fiqa_api.jobhunter.graphs.jd_chat_graph import build_jd_chat_graph
from services.fiqa_api.jobhunter.schemas import JDChatState

# 先运行 Flow 1 获取分析结果
from services.fiqa_api.jobhunter.graphs.jd_analysis_graph import run_jd_analysis
result = run_jd_analysis(jd_input, candidate_profile)

# 构建 chat graph
chat_graph = build_jd_chat_graph().compile()

# 初始化 chat state
chat_state: JDChatState = {
    "jd_input": jd_input,
    "jd_summary": result["jd_summary"],
    "fit_summary": result["fit_summary"],
    "candidate_profile": candidate_profile,
    "history": [],
    "last_user_message": "这个职位需要哪些核心技能？",
    "last_response": None,
}

# 调用 graph
result_state = chat_graph.invoke(chat_state)
response = result_state["last_response"]
```

#### CLI 调用
```bash
# 使用默认候选人画像，进入多轮对话模式
python -m experiments.jobhunter.jd_chat_coach_cli \
  --scored-file data/jobhunter/scored/jobs_scored_data_ml_platform_latest.json \
  --job-id 4741102008 \
  --use-default-profile
```

---

## Flow 3: 偏好 & 历史经验闭环（影响排序和建议）

### 文件位置
- `services/fiqa_api/jobhunter/graphs/preferences_graph.py`

### 功能
整合用户偏好评分（RLHF-style feedback）和历史经验，计算最终排序分数。用于对职位列表进行重新排序。

### 输入
- `job_id: str` - 职位 ID
- `job_meta: Dict[str, Any]` - 职位元信息（包含 match_score、category 等）
- `model_preference_score: float | None` - 可选的模型偏好分数

### 输出
- `user_rating: int | None` - 用户评分（1-5，如果存在）
- `final_score: float` - 最终综合分数（用于排序）

### 计算公式
```
final_score = base_score + (user_rating - 3) * 0.7
```
其中：
- `base_score` = `model_preference_score`（如果提供）或 `job_meta.match_score`
- `user_rating` = 1-5，中位数是 3
- `(rating - 3) * 0.7` 会在 -1.4 到 +1.4 之间调整分数

### 使用示例

#### Python 代码调用
```python
from services.fiqa_api.jobhunter.graphs.preferences_graph import run_preferences_analysis

job_meta = {
    "company": "Anthropic",
    "title": "Staff Engineer",
    "match_score": 8.5,
    "category": "A",
}

result = run_preferences_analysis(
    job_id="123",
    job_meta=job_meta,
    model_preference_score=8.5,  # 可选
)

final_score = result["final_score"]
user_rating = result["user_rating"]
```

#### 在报告生成中使用（示例）
```python
# 对每个 job 计算 final_score
for job in jobs:
    result = run_preferences_analysis(
        job_id=job["job_id"],
        job_meta={"match_score": job["match_score"], ...},
    )
    job["final_score"] = result["final_score"]

# 按 final_score 排序
jobs.sort(key=lambda x: x["final_score"], reverse=True)
```

---

## 架构说明

### State 定义
所有 Flow 的 State 都定义在 `services/fiqa_api/jobhunter/schemas.py` 中：
- `JDAnalysisState` - Flow 1 的 state
- `JDChatState` - Flow 2 的 state
- `JobHistoryState` - Flow 3 的 state

### 模块依赖
所有 Flow 都复用现有模块：
- Flow 1: `jd_interpreter.py`, `job_fit_analyzer.py`
- Flow 2: 复用 Flow 1 的结果，使用 `clients.get_openai_client()`
- Flow 3: `preferences_store.py`

### 扩展性
这三个 Flow 都是最小可用的实现，可以方便地：
- 挂到 Web API（FastAPI/Flask）
- 部署到 K8s
- 集成到评估系统
- 添加更多节点和边（例如：RAG 检索、多模型对比等）

---

## LangSmith Tracing

所有 3 个 flow 都已接入 LangSmith tracing。如果设置了环境变量（`LANGSMITH_API_KEY` 和 `LANGSMITH_TRACING`），所有 flow 执行都会自动发送 trace 到 LangSmith。

详细配置和使用说明请参考：[notes_langsmith_tracing.md](./notes_langsmith_tracing.md)

## 测试

每个 graph 文件都包含 `if __name__ == "__main__"` 的 smoke test，可以直接运行：

```bash
# 测试 Flow 1
python -m services.fiqa_api.jobhunter.graphs.jd_analysis_graph

# 测试 Flow 2
python -m services.fiqa_api.jobhunter.graphs.jd_chat_graph

# 测试 Flow 3
python -m services.fiqa_api.jobhunter.graphs.preferences_graph
```



