# 在 LangSmith UI 中查看 LangGraph 图形视图的指南

## 📍 重要说明

LangSmith 的图形化视图主要在 **"Runs" 标签页**中查看，而不是 "Threads" 标签页。

- **"Runs" 标签页**: 显示所有的 traces（单次执行），包括 LangGraph 的节点层级结构
- **"Threads" 标签页**: 用于分组多个相关的 traces（如对话历史），目前我们未配置，所以显示 "No threads found"（这是正常的）

## 🎯 如何查看图形化视图

### 步骤 1: 进入 "Runs" 标签页

1. 访问你的 LangSmith 项目：https://smith.langchain.com/
2. 选择项目：`searchforge-mortgage` 或 `searchforge-ops`
3. **点击顶部的 "Runs" 标签**（不是 "Threads"）

### 步骤 2: 选择一个 Trace

在左侧列表中，你应该能看到：
- `single_home_graph_run` - Mortgage graph 的执行
- `system_health_graph_run` - Ops graph 的执行

**点击其中一个 trace**（例如 `single_home_graph_run`）

### 步骤 3: 查看节点层级结构

在右侧详情面板中，你应该能看到：

1. **节点层级列表**：
   ```
   single_home_graph_run (3.96s)
   ├── stress_check (0.00s)
   ├── _need_safety_upgrade_router (0.00s)
   ├── safety_upgrade (0.00s)
   ├── mortgage_programs (0.24s)
   ├── strategy_lab (0.00s)
   └── llm_explanation (3.57s)
       └── mortgage_llm_explanation (3.56s)
   ```

2. **每个节点都可以展开**查看：
   - 输入参数
   - 输出结果
   - 执行时间
   - 错误信息（如果有）

### 步骤 4: 查看图形视图（如果可用）

在某些版本的 LangSmith 中，trace 详情页可能有以下选项：

1. **查看 "Graph" 标签**（如果存在）：
   - 在 trace 详情页的顶部标签栏中查找 "Graph" 或 "Diagram"
   - 这会显示节点之间的连接关系图

2. **查看 Waterfall 视图**：
   - 在左侧面板，查找 "Waterfall" 下拉菜单
   - 这显示节点的时间线视图

3. **查看 Mermaid 图表**（如果支持）：
   - 某些 trace 详情页可能包含 Mermaid 图表
   - 查看是否有 "View Graph" 或类似的按钮

## 🎨 备用方案：使用生成的 Mermaid 图表

如果 LangSmith UI 中没有显示你想要的图形视图，可以使用我们生成的 Mermaid 图表文件：

### 文件位置

1. **Single Home Graph**: `docs/langgraph_single_home_diagram.md`
2. **System Health Graph**: `docs/langgraph_system_health_diagram.md`

### 查看方式

#### 方式 1: 在线 Mermaid 编辑器（推荐）

1. 访问 https://mermaid.live/
2. 打开 `docs/langgraph_single_home_diagram.md` 文件
3. 复制其中的 Mermaid 代码（在 ` ```mermaid` 和 ` ``` ` 之间）
4. 粘贴到 mermaid.live 编辑器
5. 你可以：
   - 实时预览图形
   - 下载为 PNG 或 SVG
   - 编辑和自定义样式

#### 方式 2: GitHub

如果你将这个项目推送到 GitHub：
- GitHub 自动支持 Mermaid 渲染
- 直接在 GitHub 上打开 `.md` 文件就能看到图形

#### 方式 3: VS Code

1. 安装插件：`Markdown Preview Mermaid Support`
2. 打开 `.md` 文件
3. 按 `Cmd+Shift+V` (Mac) 或 `Ctrl+Shift+V` (Windows/Linux) 预览

## 🔍 当前在 LangSmith 中能看到的信息

即使没有完整的图形视图，你在 LangSmith 的 "Runs" 标签页中也能看到：

✅ **完整的执行流程**：
- 每个节点的执行顺序
- 节点之间的层级关系
- 执行时间

✅ **详细的输入/输出**：
- 每个节点的输入参数
- 每个节点的输出结果
- 中间状态的变化

✅ **性能指标**：
- 每个节点的执行时间
- 总执行时间
- LLM 调用的 tokens 和成本

✅ **错误追踪**：
- 如果某个节点失败，能看到详细的错误信息
- 执行路径的中断点

## 💡 提示

1. **展开节点**：点击左侧层级结构中的节点，可以展开查看详细信息
2. **查看 LLM 调用**：展开 `llm_explanation` 节点，可以看到嵌套的 `mortgage_llm_explanation`，包括完整的 prompt 和 response
3. **比较多个 traces**：使用 "Compare" 功能可以并排比较多个执行结果

## 🚀 下一步

如果你想看到更完整的图形化视图，可以：

1. **使用生成的 Mermaid 图表**（最简单）：
   - 访问 https://mermaid.live/
   - 查看 `docs/langgraph_single_home_diagram.md` 中的 Mermaid 代码

2. **配置 LangGraph Studio**（高级）：
   - 可以使用 LangGraph Studio 来可视化开发
   - 但这需要额外的配置，主要用于开发阶段

3. **等待 LangSmith 更新**：
   - LangSmith 团队正在持续改进图形可视化功能
   - 未来版本可能会有更好的图形视图支持

## 📝 总结

- ✅ Traces 已经成功发送到 LangSmith（在 "Runs" 标签页中可见）
- ✅ 可以看到完整的节点层级结构和执行流程
- ❌ "Threads" 标签页显示 "No threads found" 是正常的（我们未配置 thread grouping）
- 💡 完整的图形视图可以使用生成的 Mermaid 图表文件查看

当前的 LangSmith 实现已经足够用于：
- 调试执行流程
- 查看每个节点的输入/输出
- 性能分析
- 错误追踪

完整的流程图可以使用生成的 Mermaid 图表文件查看，这对于理解整体架构更有帮助。

