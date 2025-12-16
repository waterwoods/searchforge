#!/usr/bin/env python3
"""
visualize_langgraph.py - 生成 LangGraph 的可视化图表

这个脚本会：
1. 加载 LangGraph 定义
2. 生成 Mermaid 图表代码
3. 保存为 .md 文件，可以在 GitHub 或支持 Mermaid 的编辑器中查看
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def visualize_single_home_graph():
    """生成 single_home_graph 的 Mermaid 图表"""
    from services.fiqa_api.mortgage.graphs.single_home_graph import _build_single_home_graph
    
    graph = _build_single_home_graph()
    
    # Get the graph structure
    try:
        # LangGraph 有 get_graph() 方法可以获取图结构
        graph_structure = graph.get_graph()
        
        # 生成 Mermaid 图表
        mermaid_code = graph_structure.draw_mermaid()
        
        output_file = project_root / "docs" / "langgraph_single_home_diagram.md"
        
        content = f"""# Single Home Graph - LangGraph 可视化

这个文件包含 single_home_graph 的 Mermaid 图表。你可以在以下地方查看：

1. **GitHub**: 直接在 GitHub 上查看这个 .md 文件（GitHub 支持 Mermaid）
2. **VS Code**: 安装 "Markdown Preview Mermaid Support" 插件后预览
3. **在线工具**: 访问 https://mermaid.live/ 粘贴下面的代码

## Graph Structure

```mermaid
{mermaid_code}
```

## 节点说明

- **stress_check**: 执行核心压力检查
- **safety_upgrade**: 如果需要升级（tight/high_risk），搜索更安全的房屋选项
- **mortgage_programs**: 查找相关的抵押贷款援助项目
- **strategy_lab**: 运行策略实验室分析（what-if 场景）
- **llm_explanation**: 生成 LLM 解释

## 流程说明

1. **Entry** → `stress_check` (总是第一个执行)
2. **Router** → 根据 `stress_band` 决定：
   - `need_upgrade`: 执行安全升级流程
   - `skip_upgrade`: 跳过安全升级
3. **安全升级路径**: `stress_check` → `safety_upgrade` → `mortgage_programs` → `strategy_lab` → `llm_explanation`
4. **直接路径**: `stress_check` → `strategy_lab` → `llm_explanation`
"""
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding='utf-8')
        
        print(f"✅ 已生成图表文件: {output_file}")
        print(f"\n查看方式：")
        print(f"1. 在 GitHub 上打开: {output_file.relative_to(project_root)}")
        print(f"2. 或在 VS Code 中预览（需要安装 Mermaid 插件）")
        print(f"3. 或访问 https://mermaid.live/ 粘贴 Mermaid 代码")
        
        return True
        
    except AttributeError:
        # 如果 graph.get_graph() 或 draw_mermaid() 不可用，手动生成
        print("⚠️  LangGraph 的 draw_mermaid() 方法不可用，使用手动生成的图表...")
        return visualize_single_home_graph_manual()


def visualize_single_home_graph_manual():
    """手动生成 single_home_graph 的 Mermaid 图表"""
    
    output_file = project_root / "docs" / "langgraph_single_home_diagram.md"
    
    mermaid_code = """graph TD
    Start([开始]) --> stress_check[stress_check<br/>压力检查]
    
    stress_check --> router{路由器<br/>是否需要升级?}
    
    router -->|need_upgrade<br/>tight/high_risk| safety_upgrade[safety_upgrade<br/>安全升级]
    router -->|skip_upgrade<br/>loose/ok| strategy_lab[strategy_lab<br/>策略实验室]
    
    safety_upgrade --> mortgage_programs[mortgage_programs<br/>抵押贷款项目]
    mortgage_programs --> strategy_lab
    
    strategy_lab --> llm_explanation[llm_explanation<br/>LLM 解释]
    
    llm_explanation --> End([结束])
    
    style stress_check fill:#e1f5ff
    style router fill:#fff4e1
    style safety_upgrade fill:#ffe1f5
    style mortgage_programs fill:#ffe1f5
    style strategy_lab fill:#e1ffe1
    style llm_explanation fill:#f5e1ff
"""
    
    content = f"""# Single Home Graph - LangGraph 可视化

这个文件包含 single_home_graph 的 Mermaid 图表。

## Graph Structure

```mermaid
{mermaid_code}
```

## 节点说明

- **stress_check**: 执行核心压力检查，计算 DTI、压力带等
- **safety_upgrade**: 如果压力带是 tight/high_risk，搜索更安全的房屋选项
- **mortgage_programs**: 查找相关的抵押贷款援助项目（MCP server）
- **strategy_lab**: 运行策略实验室分析，生成 what-if 场景
- **llm_explanation**: 生成借款人友好的叙述和建议

## 执行流程

1. **Entry** → `stress_check` (总是第一个执行)
2. **Router** → 根据 `stress_band` 决定：
   - `need_upgrade` (tight/high_risk): 执行完整的安全升级流程
   - `skip_upgrade` (loose/ok): 跳过安全升级，直接进入策略实验室
3. **安全升级路径**: 
   ```
   stress_check → safety_upgrade → mortgage_programs → strategy_lab → llm_explanation
   ```
4. **直接路径**: 
   ```
   stress_check → strategy_lab → llm_explanation
   ```

## 在 LangSmith 中查看

在 LangSmith UI 中：
1. 打开你的项目 (searchforge-mortgage)
2. 点击一个 `single_home_graph_run` trace
3. 在详情页查看节点的层级结构和执行顺序
4. 切换到 "Threads" 标签页可能看到更好的图形化视图

## 查看这个图表

### 方式 1: GitHub（推荐）
- 直接在 GitHub 上查看这个文件，GitHub 会自动渲染 Mermaid 图表

### 方式 2: 在线 Mermaid Live Editor
1. 访问 https://mermaid.live/
2. 复制上面的 Mermaid 代码
3. 粘贴到编辑器中
4. 点击 "Download PNG" 或 "Download SVG" 保存为图片

### 方式 3: VS Code
1. 安装插件：`Markdown Preview Mermaid Support`
2. 打开这个文件
3. 按 `Cmd+Shift+V` (Mac) 或 `Ctrl+Shift+V` (Windows/Linux) 预览
"""
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(content, encoding='utf-8')
    
    print(f"✅ 已生成图表文件: {output_file}")
    print(f"\n📊 查看方式：")
    print(f"   1. GitHub: 在浏览器中打开 {output_file.relative_to(project_root)}")
    print(f"   2. 在线工具: https://mermaid.live/ 粘贴 Mermaid 代码")
    print(f"   3. VS Code: 安装 Mermaid 插件后预览")
    
    return True


def visualize_system_health_graph():
    """生成 system_health_graph 的 Mermaid 图表"""
    
    output_file = project_root / "docs" / "langgraph_system_health_diagram.md"
    
    mermaid_code = """graph TD
    Start([开始]) --> health_check[health_check<br/>健康检查]
    
    health_check --> router{路由器<br/>是否需要升级?}
    
    router -->|need_upgrade<br/>degraded/critical| safety_upgrade[safety_upgrade<br/>安全升级建议]
    router -->|skip_upgrade<br/>healthy/warning| strategy_lab[strategy_lab<br/>策略实验室]
    
    safety_upgrade --> strategy_lab
    
    strategy_lab --> llm_explanation[llm_explanation<br/>LLM 解释]
    
    llm_explanation --> End([结束])
    
    style health_check fill:#e1f5ff
    style router fill:#fff4e1
    style safety_upgrade fill:#ffe1f5
    style strategy_lab fill:#e1ffe1
    style llm_explanation fill:#f5e1ff
"""
    
    content = f"""# System Health Graph - LangGraph 可视化

这个文件包含 system_health_graph 的 Mermaid 图表。

## Graph Structure

```mermaid
{mermaid_code}
```

## 节点说明

- **health_check**: 执行系统健康检查，计算健康带、分数、风险标志等
- **safety_upgrade**: 如果健康带是 degraded/critical，生成安全配置建议
- **strategy_lab**: 运行策略实验室分析，生成 what-if 场景
- **llm_explanation**: 生成 SRE 友好的叙述和建议

## 执行流程

1. **Entry** → `health_check` (总是第一个执行)
2. **Router** → 根据 `health_band` 决定：
   - `need_upgrade` (degraded/critical): 执行安全升级建议
   - `skip_upgrade` (healthy/warning): 跳过安全升级，直接进入策略实验室
3. **安全升级路径**: 
   ```
   health_check → safety_upgrade → strategy_lab → llm_explanation
   ```
4. **直接路径**: 
   ```
   health_check → strategy_lab → llm_explanation
   ```

## 在 LangSmith 中查看

在 LangSmith UI 中：
1. 打开你的项目 (searchforge-ops)
2. 点击一个 `system_health_graph_run` trace
3. 在详情页查看节点的层级结构和执行顺序

## 查看这个图表

### 方式 1: GitHub（推荐）
- 直接在 GitHub 上查看这个文件，GitHub 会自动渲染 Mermaid 图表

### 方式 2: 在线 Mermaid Live Editor
1. 访问 https://mermaid.live/
2. 复制上面的 Mermaid 代码
3. 粘贴到编辑器中
4. 点击 "Download PNG" 或 "Download SVG" 保存为图片

### 方式 3: VS Code
1. 安装插件：`Markdown Preview Mermaid Support`
2. 打开这个文件
3. 按 `Cmd+Shift+V` (Mac) 或 `Ctrl+Shift+V` (Windows/Linux) 预览
"""
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(content, encoding='utf-8')
    
    print(f"✅ 已生成图表文件: {output_file}")
    
    return True


def main():
    print("🎨 LangGraph 可视化图表生成器")
    print("=" * 60)
    print()
    
    print("生成 Single Home Graph 图表...")
    visualize_single_home_graph()
    
    print("\n生成 System Health Graph 图表...")
    visualize_system_health_graph()
    
    print("\n" + "=" * 60)
    print("✅ 所有图表已生成！")
    print("\n💡 提示：")
    print("   - 在 LangSmith UI 中，切换到 'Threads' 标签页可以看到更详细的图形化视图")
    print("   - 使用生成的 .md 文件可以在 GitHub 或支持 Mermaid 的编辑器中查看图表")


if __name__ == "__main__":
    main()

