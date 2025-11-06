# AutoTuner 流程图生成指南

本目录包含 AutoTuner 系统的流程图资源。

## 文件清单

- `autotuner_flow_mermaid.md` - Mermaid 图表源码（包含 4 个图表）
- `autotuner_flow.png` - （待生成）完整数据流图
- `README.md` - 本文件

## 快速生成 PNG 图片

### 方法 1：在线工具（推荐）

1. 访问 [Mermaid Live Editor](https://mermaid.live/)
2. 打开 `autotuner_flow_mermaid.md`
3. 复制对应图表的 Mermaid 代码
4. 粘贴到编辑器
5. 点击右上角 "Actions" → "PNG" 下载图片

### 方法 2：命令行工具

```bash
# 安装 mermaid-cli（需要 Node.js）
npm install -g @mermaid-js/mermaid-cli

# 生成图片
cd /Users/nanxinli/Documents/dev/searchforge/docs/figs

# 导出完整数据流图
mmdc -i autotuner_flow_mermaid.md -o autotuner_flow.png -w 1920 -H 1080 -b transparent
```

### 方法 3：使用 VS Code 插件

1. 安装 VS Code 插件：`Markdown Preview Mermaid Support`
2. 打开 `autotuner_flow_mermaid.md`
3. 按 `Cmd+Shift+V`（Mac）或 `Ctrl+Shift+V`（Windows）预览
4. 右键图表 → "Copy as PNG"

## 图表说明

### 1. 完整数据流图（推荐用于演示）
- 尺寸：1920x1080
- 展示从查询到参数更新的完整流程
- 适合：系统架构讲解、培训材料

### 2. 时序图（推荐用于技术文档）
- 尺寸：1600x1200
- 展示组件间的时序交互
- 适合：接口对接文档、调试手册

### 3. 多参数调优流程图
- 尺寸：1200x1600
- 展示多参数决策的完整逻辑
- 适合：算法说明、技术评审

### 4. 系统架构图（简化版）
- 尺寸：1200x800
- 展示主要组件关系
- 适合：技术选型、快速理解

## 自定义样式

如需修改图表颜色或样式，可编辑 `autotuner_flow_mermaid.md` 中的 `style` 语句：

```mermaid
style NodeID fill:#color
```

常用配色方案：
- 蓝色系：`#e3f2fd` (浅蓝), `#1976d2` (深蓝)
- 绿色系：`#e8f5e9` (浅绿), `#388e3c` (深绿)
- 黄色系：`#fff9c4` (浅黄), `#f57f17` (深黄)
- 红色系：`#ffebee` (浅红), `#c62828` (深红)

## 故障排查

### 问题：mmdc 命令找不到
**解决**：确保已安装 Node.js 和 mermaid-cli
```bash
node --version  # 应显示 v14+ 版本
npm install -g @mermaid-js/mermaid-cli
```

### 问题：生成的图片不清晰
**解决**：增加输出尺寸
```bash
mmdc -i input.md -o output.png -w 2560 -H 1440
```

### 问题：中文显示为方框
**解决**：指定中文字体
```bash
mmdc -i input.md -o output.png -w 1920 -H 1080 --cssFile custom.css
```

custom.css 内容：
```css
body {
    font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
}
```

## 参考资源

- [Mermaid 官方文档](https://mermaid.js.org/)
- [Mermaid Live Editor](https://mermaid.live/)
- [Mermaid CLI GitHub](https://github.com/mermaid-js/mermaid-cli)
