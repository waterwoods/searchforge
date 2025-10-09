# AutoTuner 数据流图 - Mermaid 源码

本文件包含 AutoTuner 系统的 Mermaid 图表源码，可用于生成 PNG 图片。

## 使用方式

### 方式 1：在线渲染
访问 [Mermaid Live Editor](https://mermaid.live/) 粘贴以下代码生成图片。

### 方式 2：命令行渲染
```bash
# 安装 mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# 渲染图片
mmdc -i autotuner_flow_mermaid.md -o autotuner_flow.png -w 1920 -H 1080
```

---

## 图表 1：完整数据流图

```mermaid
graph TD
    A[查询请求] -->|指标窗口| B[AutoTuner State]
    B -->|TuningInput| C{Brain 启用?}
    C -->|是| D[Brain Decider]
    C -->|否| E[原有逻辑]
    
    D -->|查询甜点| F[Memory Hook]
    F -->|有甜点| G[返回靠拢动作]
    F -->|无甜点| H[规则决策]
    
    H -->|守护检查| I{冷却期?}
    I -->|是| J[noop]
    I -->|否| K[滞回带检查]
    
    K -->|误差大| L{延迟超标?}
    K -->|误差小| J
    
    L -->|是+召回富余| M[降ef/ncand]
    L -->|否| N{召回不足?}
    
    N -->|是+延迟富余| O[升ef/rerank]
    N -->|否| P{near_T?}
    
    P -->|是| Q[升T]
    P -->|否| J
    
    M --> R[Apply Action]
    O --> R
    Q --> R
    G --> R
    
    R -->|clip_params| S[参数裁剪]
    S -->|clip_joint| T[联合约束]
    T --> U[更新参数]
    
    U -->|observe| V[Memory System]
    V -->|EWMA| W[更新甜点]
    
    U --> X[执行查询]
    X -->|指标回流| B
    
    style A fill:#e1f5ff
    style J fill:#ffebee
    style M fill:#fff9c4
    style O fill:#f3e5f5
    style Q fill:#e8f5e9
    style U fill:#e3f2fd
    style W fill:#fce4ec
```

---

## 图表 2：时序图（窗口→决策→应用→记忆）

```mermaid
sequenceDiagram
    participant User as 用户查询
    participant Pipeline as SearchPipeline
    participant Tuner as AutoTuner State
    participant Brain as Brain Decider
    participant Memory as Memory System
    participant Apply as Apply Module
    participant Search as Vector Search

    User->>Pipeline: search(query)
    Pipeline->>Search: 执行检索 (当前参数)
    Search-->>Pipeline: 返回结果 + 延迟
    
    Pipeline->>Tuner: 更新指标窗口
    Tuner->>Tuner: 计算窗口 P95 & 召回率
    
    alt 达到采样桶边界
        Tuner->>Brain: decide_tuning_action(inp)
        
        Brain->>Memory: query(bucket_id)
        alt 有甜点
            Memory-->>Brain: SweetSpot
            Brain-->>Tuner: Action(follow_memory)
        else 无甜点
            Brain->>Brain: 执行规则决策
            Brain-->>Tuner: Action(bump_ef/drop_ef/noop)
        end
        
        Tuner->>Apply: apply_action(params, action)
        Apply->>Apply: clip_params + clip_joint
        Apply-->>Tuner: 新参数
        
        Tuner->>Memory: observe(sample)
        Memory->>Memory: 更新 EWMA + 甜点
        
        Tuner->>Pipeline: 应用新参数
    end
    
    Pipeline-->>User: 返回搜索结果
```

---

## 图表 3：多参数调优流程图

```mermaid
flowchart TD
    Start([开始]) --> CheckCooldown{冷却期?}
    CheckCooldown -->|是| MicroStep[单参数微步调整]
    CheckCooldown -->|否| CheckMemory{记忆甜点?}
    
    CheckMemory -->|是| SteadyNudge[steady_nudge]
    CheckMemory -->|否| CheckPerf{性能指标}
    
    CheckPerf -->|高延迟+好召回| LatencyDrop[latency_drop bundle]
    CheckPerf -->|低召回+好延迟| RecallGain[recall_gain bundle]
    CheckPerf -->|宏观偏置| MacroBias[基于 L/R 选择]
    CheckPerf -->|不确定| RoundRobin[轮询策略]
    
    LatencyDrop --> Scale[缩放步长]
    RecallGain --> Scale
    SteadyNudge --> Scale
    MacroBias --> Scale
    RoundRobin --> Scale
    
    Scale --> FeasCheck{可行性预测}
    FeasCheck -->|不可行| Shrink[渐进缩减]
    Shrink --> FeasCheck
    FeasCheck -->|可行| AtomicApply[atomic 应用]
    
    AtomicApply --> JointClip[联合约束裁剪]
    JointClip --> Done([完成])
    
    MicroStep --> Done
    
    style Start fill:#e8f5e9
    style Done fill:#e3f2fd
    style MicroStep fill:#fff9c4
    style SteadyNudge fill:#f3e5f5
    style LatencyDrop fill:#ffebee
    style RecallGain fill:#e1f5ff
```

---

## 图表 4：系统架构图（简化版）

```mermaid
graph LR
    A[SearchPipeline] --> B[AutoTuner State]
    B --> C[Brain Decider]
    C --> D[Memory System]
    C --> E[Apply Module]
    E --> F[Constraints]
    E --> B
    D --> C
    
    subgraph "Brain 决策器"
        C
        D
    end
    
    subgraph "参数应用层"
        E
        F
    end
    
    style A fill:#e3f2fd
    style B fill:#fff9c4
    style C fill:#f3e5f5
    style D fill:#fce4ec
    style E fill:#e8f5e9
    style F fill:#ffebee
```

---

## 导出命令

```bash
# 导出所有图表
mmdc -i autotuner_flow_mermaid.md -o ../figs/autotuner_flow.png -w 1920 -H 1080
```

**注意**：如果无法安装 mermaid-cli，可以使用在线工具：
1. 访问 https://mermaid.live/
2. 粘贴上述代码
3. 点击"Download PNG"按钮

---

## 图表说明

### 完整数据流图
展示从查询请求到参数更新的完整流程，包括：
- Brain 启用判断
- 记忆钩子优先查询
- 规则决策逻辑（守护、滞回带、性能指标）
- 参数裁剪与联合约束
- 记忆系统更新

### 时序图
展示关键组件之间的交互时序：
- 用户查询触发
- 指标窗口累积
- 采样桶边界触发决策
- 记忆查询与决策
- 参数应用与记忆更新

### 多参数调优流程图
展示多参数联合决策的完整流程：
- 冷却期微步调整
- 记忆甜点稳态微调
- 性能指标驱动的预设策略
- 可行性预测与渐进缩减
- 原子化应用与约束裁剪

### 系统架构图
简化版的系统组件关系图，展示主要模块之间的依赖关系。
