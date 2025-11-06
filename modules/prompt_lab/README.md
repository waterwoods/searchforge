# Prompt Lab - Structured Output Experimentation

A lightweight module for experimenting with structured output from LLMs using JSON Mode and Function Calling.

## Features

✅ **Strict Contracts**: Input/output dataclasses with JSON Schema validation  
✅ **Dual Modes**: JSON Mode (`response_format`) and Function Calling (tools)  
✅ **Provider Abstraction**: Clean interface with OpenAI adapter and MockProvider  
✅ **Retry Logic**: Automatic schema validation with repair hints  
✅ **Zero I/O Core**: Pure business logic, no network/file dependencies in modules  
✅ **Fast Tests**: <1s unit tests using mocks (0.47s actual)  
✅ **Lab Script**: Demo with JSONL + HTML output, works without API key

## Quick Start

### Run Tests (Fast, No API Key Needed)

```bash
pytest tests/test_prompt_lab.py -v
# 11 passed in 0.47s
```

### Run Lab Demo

```bash
python labs/run_query_rewriter_lab.py
```

The lab script:
- Tests 8 sample queries (Chinese + English)
- Runs 4 experiments (JSON/Function × temp 0.0/0.2)
- Falls back to MockProvider if no `OPENAI_API_KEY`
- Outputs to `labs/out/`:
  - `query_rewriter_results.jsonl` - raw results
  - `query_rewriter_report.html` - visual report

### Basic Usage

```python
from modules.prompt_lab import RewriteInput, MockProvider, QueryRewriter

# Create provider (Mock for testing)
provider = MockProvider()
rewriter = QueryRewriter(provider)

# Query rewriting
input_data = RewriteInput(
    query="最新的AI发展",
    locale="zh-CN",
    time_range="最近一周"
)

# JSON Mode
output = rewriter.rewrite(input_data, mode="json")
print(output.topic, output.entities, output.query_rewrite)

# Function Calling
output = rewriter.rewrite(input_data, mode="function")
```

### Use with OpenAI API

```python
from modules.prompt_lab import OpenAIProvider, QueryRewriter, RewriteInput
from modules.prompt_lab.providers import ProviderConfig

# Configure OpenAI provider
config = ProviderConfig(temperature=0.0, max_tokens=500, model="gpt-4o-mini")
provider = OpenAIProvider(config, api_key="your-api-key")
rewriter = QueryRewriter(provider)

# Use as normal
result = rewriter.rewrite(input_data, mode="json")
```

## Architecture

### Contracts (`contracts.py`)

Pure data structures with JSON Schema validation:

```python
@dataclass
class RewriteInput:
    query: str
    locale: Optional[str] = None
    time_range: Optional[str] = None

@dataclass
class RewriteOutput:
    topic: str
    entities: List[str]
    time_range: Optional[str]
    query_rewrite: str
    filters: Dict[str, Optional[str]]  # date_from, date_to
```

**Key Functions:**
- `validate(data: dict) -> bool` - Validates against JSON Schema
- `from_dict(data: dict) -> RewriteOutput` - Construct from validated dict

### Providers (`providers.py`)

Abstract interface with implementations:

- `RewriterProvider` - Abstract base class
- `MockProvider` - Deterministic mock (no network, for tests)
- `OpenAIProvider` - OpenAI API adapter (lazy client init)

**Modes:**
- `json` - Uses `response_format={"type": "json_object"}`
- `function` - Uses tools/function calling

### Query Rewriter (`query_rewriter.py`)

Core rewriting logic with six key components:

1. **`[CORE: role-prompt]`** - System prompt engineering
2. **`[CORE: json-mode]`** - JSON Mode implementation
3. **`[CORE: function-calling]`** - Function calling implementation
4. **`[CORE: schema-validate]`** - Strict schema validation
5. **`[CORE: retry-repair]`** - Retry with repair hints on failure
6. **`[CORE: normalize]`** - Entity/text normalization

**Main Methods:**
- `build_messages(input)` - Construct chat messages
- `call_json_mode(messages)` - Execute JSON Mode
- `call_function_calling(messages)` - Execute Function Calling
- `rewrite(input, mode, max_retries)` - Main entry point

## Tests

All tests use `MockProvider` for zero-latency, deterministic results:

```bash
pytest tests/test_prompt_lab.py -v
```

**Test Coverage:**
- ✅ Contract validation (valid/invalid schemas)
- ✅ JSON Mode with valid mock response
- ✅ Function Calling with valid mock response
- ✅ Retry logic (invalid → repair → valid)
- ✅ Normalization (whitespace, empty entities)
- ✅ No I/O guarantee
- ✅ Message building
- ✅ Invalid mode handling
- ✅ Max retries exceeded

**Runtime:** ~0.47s (target: <1s)

## Design Principles

1. **Pure Core** - No I/O in `modules/prompt_lab/*`. Provider handles network.
2. **Strict Validation** - All outputs must pass JSON Schema validation.
3. **Testability** - MockProvider enables fast, deterministic tests.
4. **Retry Safety** - Single retry with repair hint if schema validation fails.
5. **Provider Agnostic** - Easy to add new providers (Anthropic, local models, etc.)

## Extending

### Add New Provider

```python
from modules.prompt_lab.providers import RewriterProvider

class MyCustomProvider(RewriterProvider):
    def rewrite(self, messages: List[Dict], mode: str) -> Dict:
        # Your implementation
        return {"topic": "...", ...}
```

### Customize Schema

Modify `REWRITE_OUTPUT_SCHEMA` in `contracts.py` and update `RewriteOutput` dataclass accordingly.

## Chinese Summary (中文总结)

**Prompt Lab** 是一个轻量级的结构化输出实验模块：

- ✅ 支持 JSON Mode 和 Function Calling 两种模式
- ✅ 严格的 JSON Schema 校验（additionalProperties=false）
- ✅ 自动重试修复机制
- ✅ 无需 API 密钥即可测试（使用 MockProvider）
- ✅ 快速测试（11 个测试 0.47 秒完成）
- ✅ 包含可视化实验脚本

**文件结构：**
```
modules/prompt_lab/
  ├── contracts.py       # 数据契约 + JSON Schema
  ├── providers.py       # 提供者抽象（Mock / OpenAI）
  └── query_rewriter.py  # 核心重写逻辑

tests/test_prompt_lab.py  # 快速单元测试
labs/run_query_rewriter_lab.py  # 演示脚本
```

**运行演示：**
```bash
python labs/run_query_rewriter_lab.py
# 输出：labs/out/query_rewriter_results.jsonl + .html
```
