# JobHunter Agent 前端页面设置总结

## 1. 前端结构勘察结果

### 前端框架
- **框架类型**: React + TypeScript
- **UI 库**: Ant Design (antd)
- **构建工具**: Vite
- **路由**: React Router v6
- **项目位置**: `/home/andy/searchforge/ui/`

### 模板页面分析
- **参考页面**: `MortgageAssistantPage.tsx` (`ui/src/pages/MortgageAssistantPage.tsx`)
- **布局特点**: 两栏布局（左侧表单，右侧结果）
- **使用的组件**: Ant Design 的 `Row`, `Col`, `Card`, `Form`, `Tabs` 等
- **API 调用方式**: 使用 `fetch` 调用 `${API_BASE_URL}/api/mortgage-agent/*` 端点

## 2. 新创建的 JobHunter 页面

### 文件路径
- **页面组件**: `ui/src/pages/JobHunterPage.tsx`
- **路由配置**: 已在 `ui/src/App.tsx` 中添加

### 路由地址
- `/workbench/jobhunter`
- `/jobhunter` (简化路径)

### 三栏布局结构

#### 左侧栏（6/24 宽度）
- **功能**: 已分析的 JD 历史记录列表
- **组件**: `Card` + `List`
- **显示内容**:
  - 职位名称
  - 公司名称
  - 匹配度标签（A/B/C 分类）
  - 匹配分数（1-10）
  - 分析时间戳
- **交互**: 点击可选中历史记录（未来可扩展为加载历史分析结果）

#### 中间栏（10/24 宽度）
- **功能**: JD 输入 + 职业教练对话
- **组件**: `Card` + `Form` + 聊天区域
- **输入表单**:
  - 职位名称（可选）
  - 公司名称（可选）
  - 工作地点（可选）
  - 职位描述（必填，多行文本）
  - "分析 JD" 按钮
- **聊天区域**:
  - 消息历史显示（支持 Markdown 渲染）
  - 输入框 + 发送按钮
  - 支持多轮对话

#### 右侧栏（8/24 宽度）
- **功能**: JD 分析结果详情展示
- **组件**: `Card` + `Tabs`
- **Tab 1: JD 解读**
  - 🥇 核心要求（必须满足）- 金色背景
  - 🥈 重要要求（最好有）- 银色背景
  - 🥉 加分项（有更好）- 灰色背景
- **Tab 2: 适配度**
  - 匹配度评分（1-10）
  - 分类标签（A/B/C）
  - 建议标签（APPLY/MAYBE/SKIP）
  - ✅ 优势列表
  - ⚠️ 缺口列表
  - 💡 推荐理由

## 3. 需要连接的后端 API

### Flow 1: JD 解读 + 适配度分析
- **API 端点**: `POST /api/jobhunter/analyze`
- **请求体**:
  ```typescript
  {
    jd_input: {
      description: string;  // 必填
      title?: string;
      company?: string;
      location?: string;
      job_id?: string;
    }
  }
  ```
- **响应体**:
  ```typescript
  {
    ok: boolean;
    jd_summary?: {
      gold_points: string[];
      silver_points: string[];
      bronze_points: string[];
    };
    fit_summary?: {
      match_score: number;  // 1-10
      category: 'A' | 'B' | 'C';
      strengths: string[];
      gaps: string[];
      recommendation: 'APPLY' | 'MAYBE' | 'SKIP';
      reasoning_summary: string;
    };
    error?: string;
  }
  ```
- **状态**: ✅ 前端已实现，等待后端 API 对接

### Flow 2: 多轮职业教练对话
- **API 端点**: `POST /api/jobhunter/chat`
- **请求体**:
  ```typescript
  {
    jd_input: JobJDInput;
    history: Array<{ role: 'user' | 'assistant', content: string }>;
    user_message: string;
  }
  ```
- **响应体**:
  ```typescript
  {
    ok: boolean;
    response?: string;
    error?: string;
  }
  ```
- **状态**: ✅ 前端已实现，等待后端 API 对接

### Flow 3: 偏好/历史经验加权
- **API 端点**: `POST /api/jobhunter/preferences`
- **状态**: ⏳ 可稍后实现（前端暂未集成）

## 4. 当前实现状态

### ✅ 已完成
1. 创建了 `JobHunterPage.tsx` 三栏布局页面
2. 实现了左侧历史记录列表（UI 骨架）
3. 实现了中间 JD 输入表单和聊天区域
4. 实现了右侧分析结果展示（JD 解读 + 适配度两个 Tab）
5. 在 `App.tsx` 中添加了路由配置
6. 添加了清晰的注释和 TODO 标记
7. 使用了与 MortgageAssistantPage 一致的样式和组件风格

### ⏳ 待完成（后端对接）
1. 连接 Flow 1 API (`/api/jobhunter/analyze`)
2. 连接 Flow 2 API (`/api/jobhunter/chat`)
3. 实现历史记录的持久化（可选，当前使用内存状态）
4. 连接 Flow 3 API（偏好/历史经验加权，可稍后）

## 5. 下一步工作

### 前端
- [ ] 在 `api.types.ts` 中添加 JobHunter 相关的 TypeScript 类型定义
- [ ] 测试页面在不同屏幕尺寸下的响应式布局
- [ ] 添加错误处理和加载状态的优化

### 后端对接
- [ ] 确认后端 API 端点路径和请求/响应格式
- [ ] 实现 API 调用逻辑（当前已有 TODO 标记）
- [ ] 处理 API 错误情况
- [ ] 测试完整的用户流程

## 6. 技术栈总结

- **前端框架**: React 18 + TypeScript
- **UI 组件库**: Ant Design 5.x
- **路由**: React Router v6
- **Markdown 渲染**: react-markdown
- **HTTP 客户端**: 原生 fetch API
- **状态管理**: React Hooks (useState, useEffect)

## 7. 页面访问

启动前端开发服务器后，可通过以下路径访问：
- `http://localhost:5173/workbench/jobhunter`
- `http://localhost:5173/jobhunter`

页面已具备完整的三栏布局 UI 骨架，可以直接在浏览器中打开查看效果。下一步只需要对接后端 API 即可实现完整功能。
