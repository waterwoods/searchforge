# LangSmith LangGraph 可视化指南

LangSmith 中查看 LangGraph 的图形化可视化有几种方式：

## 方式 1: 在 LangSmith UI 中查看（推荐）

### 查看 "Threads" 视图

1. **切换到 Threads 标签页**：
   - 在 LangSmith 项目页面，点击顶部的 **"Threads"** 标签（而不是 "Runs"）
   - Threads 视图会显示执行流和节点连接关系

2. **查看单个 Thread**：
   - 点击左侧列表中的某个 trace
   - 在右侧详情面板中，应该能看到节点之间的连接图

3. **查看 Graph 视图**（如果可用）：
   - 在某些 trace 详情页，可能会有 **"Graph"** 标签
   - 点击后可以看到 LangGraph 的节点和边的可视化

### 查看 Waterfall 视图

在 "Runs" 视图中：
- 左侧面板有一个下拉菜单显示 "Waterfall"
- 这个视图可以显示节点的执行顺序和依赖关系

## 方式 2: 使用 LangGraph 的内置可视化功能

我们可以在代码中生成 LangGraph 的 Mermaid 图表。让我创建一个工具来生成这些图表：
