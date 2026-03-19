# OpenClaw MVP 安装与运行指南

## 📋 概述

本文档说明如何在 `~/ai-tools/openclaw` 安装并运行 OpenClaw 的最小可用 Demo（MVP），实现通过对话触发本地命令执行（如 `ls`）。

**安装路径**: `~/ai-tools/openclaw`  
**配置文件**: `~/.openclaw/openclaw.json`  
**Gateway 端口**: `18789`  
**默认模型**: Ollama (本地，无需 API Key)

## ✅ 成功标准

- ✅ OpenClaw 安装在 `~/ai-tools/openclaw`
- ✅ Agent 可启动、可对话
- ✅ 成功执行一次本地命令（如 `ls`）并返回结果
- ✅ 有 smoke test 脚本可复现测试
- ✅ 有完整文档说明

## 🚀 快速开始

### 1. 环境准备

**系统要求**:
- Linux/macOS/WSL2
- Node.js >= 22.12.0
- pnpm >= 10.0.0

**检查环境**:
```bash
node --version  # 需要 >= 22.12.0
npm --version
```

**安装 Node.js 22** (如果未安装):
```bash
# 使用 nvm
source ~/.nvm/nvm.sh
nvm install 22
nvm use 22

# 或使用其他方式安装 Node 22
```

**安装 pnpm**:
```bash
npm install -g pnpm
```

### 2. 安装 OpenClaw

```bash
# 创建目录
mkdir -p ~/ai-tools && cd ~/ai-tools

# 克隆仓库
git clone https://github.com/openclaw/openclaw.git openclaw

# 进入目录
cd ~/ai-tools/openclaw

# 安装依赖（确保使用 Node 22）
source ~/.nvm/nvm.sh  # 如果使用 nvm
nvm use 22
pnpm install

# 构建 UI
pnpm ui:build

# 构建主项目
pnpm build
```

### 3. 安装 Ollama (本地模型)

OpenClaw 需要模型来运行 Agent。我们使用 Ollama 提供本地模型，无需 API Key。

**安装 Ollama**:
```bash
# Linux/macOS (需要 sudo)
curl -fsSL https://ollama.ai/install.sh | sh

# 或手动下载: https://ollama.ai/download
```

**启动 Ollama 服务**:
```bash
ollama serve
```

**拉取模型** (在另一个终端):
```bash
ollama pull llama3.3
# 或使用其他模型: ollama pull qwen2.5-coder:32b
```

**验证 Ollama**:
```bash
curl http://127.0.0.1:11434/api/tags
ollama list
```

### 4. 配置 OpenClaw

配置文件已自动创建在 `~/.openclaw/openclaw.json`，包含：

- **模型配置**: 使用 Ollama (llama3.3)
- **Exec 工具**: 启用，安全策略为 `allowlist`
- **Gateway**: 端口 18789，本地 loopback

**关键配置项**:

```json5
{
  agents: {
    defaults: {
      model: { primary: "ollama/llama3.3" },
    },
  },
  tools: {
    exec: {
      host: "gateway",
      security: "allowlist",
      ask: "on-miss",
      safeBins: ["ls", "pwd", "echo", "cat", ...],
    },
  },
  gateway: {
    port: 18789,
  },
  models: {
    providers: {
      ollama: {
        baseUrl: "http://127.0.0.1:11434/v1",
        apiKey: "ollama-local",
      },
    },
  },
}
```

**执行审批配置**: `~/.openclaw/exec-approvals.json`

已预配置允许的命令:
- `/usr/bin/ls`
- `/usr/bin/echo`
- `/usr/bin/pwd`

### 5. 启动 OpenClaw

**方式 1: 使用 Smoke Test 脚本 (推荐)**

```bash
cd ~/searchforge
./scripts/openclaw_smoke_test.sh
```

脚本会自动:
- 检查环境
- 检查/启动 Ollama
- 启动 Gateway
- 测试执行 `ls` 命令

**方式 2: 手动启动**

```bash
cd ~/ai-tools/openclaw

# 设置环境变量
export OLLAMA_API_KEY="ollama-local"
export OPENCLAW_STATE_DIR="$HOME/.openclaw"

# 确保使用 Node 22
source ~/.nvm/nvm.sh
nvm use 22

# 启动 Gateway
pnpm openclaw gateway --port 18789 --verbose
```

**方式 3: 后台服务 (可选)**

```bash
# 安装为 systemd 服务 (Linux)
pnpm openclaw onboard --install-daemon

# 或使用 launchd (macOS)
# 同上命令
```

### 6. 测试命令执行

**通过 Dashboard**:
1. 打开浏览器: http://127.0.0.1:18789/
2. 在聊天中输入: "List files in current directory"
3. 或: "Run ls and show me the output"

**通过 CLI**:
```bash
cd ~/ai-tools/openclaw
source ~/.nvm/nvm.sh
nvm use 22

# 发送消息
pnpm openclaw agent --message "List files in current directory using ls"
```

**预期结果**:
- Agent 理解请求
- 调用 `exec` 工具执行 `ls`
- 返回文件列表

## 🔧 配置说明

### Exec 工具安全策略

OpenClaw 的 `exec` 工具支持多层安全控制:

1. **Security 模式**:
   - `deny`: 拒绝所有命令
   - `allowlist`: 仅允许白名单命令
   - `full`: 允许所有命令（危险）

2. **Ask 模式**:
   - `off`: 不提示
   - `on-miss`: 命令不在白名单时提示
   - `always`: 总是提示

3. **Safe Bins**: 仅限 stdin 的安全二进制，无需白名单即可运行

**当前配置** (安全):
- `security: "allowlist"` - 仅允许白名单命令
- `ask: "on-miss"` - 新命令需要审批
- 已预配置: `ls`, `echo`, `pwd`

**添加新命令到白名单**:

编辑 `~/.openclaw/exec-approvals.json`:
```json
{
  "agents": {
    "main": {
      "allowlist": [
        {
          "id": "new-command",
          "pattern": "/usr/bin/your-command",
          "lastUsedAt": 0,
          "lastUsedCommand": "your-command",
          "lastResolvedPath": "/usr/bin/your-command"
        }
      ]
    }
  }
}
```

或通过 Dashboard: http://127.0.0.1:18789/ → Nodes → Exec approvals

### 禁用危险命令

危险命令（如 `rm -rf`, `sudo`）默认被阻止。如需允许，必须:

1. 在 `exec-approvals.json` 中明确添加
2. 设置 `security: "full"` (不推荐)
3. 通过 Dashboard 审批

**推荐**: 保持 `security: "allowlist"`，仅添加必要的命令。

## 📝 文件结构

```
~/ai-tools/openclaw/          # OpenClaw 源码
  ├── dist/                    # 构建输出
  ├── src/                     # 源代码
  └── package.json

~/.openclaw/                   # OpenClaw 配置和数据
  ├── openclaw.json            # 主配置文件
  ├── exec-approvals.json      # 执行审批配置
  └── workspace/               # Agent 工作区
```

## 🧪 Smoke Test

运行一键测试:

```bash
cd ~/searchforge
./scripts/openclaw_smoke_test.sh
```

脚本功能:
- ✅ 检查 Node.js 和 pnpm
- ✅ 检查/安装 Ollama
- ✅ 检查/拉取模型
- ✅ 启动 Gateway
- ✅ 测试执行 `ls` 命令
- ✅ 显示 Gateway 状态

## 🐛 常见问题

### 1. Node.js 版本不匹配

**错误**: `Unsupported engine: wanted: {"node":">=22.12.0"}`

**解决**:
```bash
source ~/.nvm/nvm.sh
nvm install 22
nvm use 22
```

### 2. Ollama 未运行

**错误**: `Connection refused` 或模型不可用

**解决**:
```bash
# 检查 Ollama
ollama serve

# 检查服务
curl http://127.0.0.1:11434/api/tags

# 拉取模型
ollama pull llama3.3
```

### 3. Gateway 启动失败

**检查日志**:
```bash
tail -f /tmp/openclaw-gateway.log
```

**检查端口占用**:
```bash
lsof -i :18789
```

**检查配置**:
```bash
cd ~/ai-tools/openclaw
pnpm openclaw doctor
```

### 4. 命令执行被拒绝

**原因**: 命令不在白名单

**解决**:
1. 通过 Dashboard 审批
2. 或编辑 `~/.openclaw/exec-approvals.json` 添加命令

### 5. pnpm 命令未找到

**原因**: pnpm 安装在 Node 20，但当前使用 Node 22

**解决**:
```bash
source ~/.nvm/nvm.sh
nvm use 22
npm install -g pnpm
```

## 📊 验证步骤

### 1. 环境验证

```bash
node --version    # >= 22.12.0
pnpm --version    # >= 10.0.0
ollama --version  # 已安装
```

### 2. 服务验证

```bash
# Ollama
curl http://127.0.0.1:11434/api/tags

# Gateway
curl http://127.0.0.1:18789/health
```

### 3. 功能验证

```bash
# 通过 CLI 测试
cd ~/ai-tools/openclaw
source ~/.nvm/nvm.sh
nvm use 22
pnpm openclaw agent --message "List files in current directory"
```

### 4. Dashboard 验证

打开浏览器: http://127.0.0.1:18789/

- ✅ 页面加载
- ✅ 可以发送消息
- ✅ Agent 响应
- ✅ 可以执行命令

## 🔗 相关链接

- **OpenClaw 官方文档**: https://docs.openclaw.ai
- **GitHub 仓库**: https://github.com/openclaw/openclaw
- **Ollama 文档**: https://ollama.ai
- **配置参考**: `~/ai-tools/openclaw/docs/zh-CN/gateway/configuration.md`

## 📌 注意事项

1. **安全**: 默认配置使用 `allowlist` 模式，仅允许安全命令
2. **模型**: 使用本地 Ollama，无需 API Key，但需要 GPU/CPU 资源
3. **端口**: Gateway 默认端口 18789，确保未被占用
4. **路径**: 所有路径使用绝对路径或 `~` 展开
5. **Node 版本**: 必须使用 Node 22+，否则构建/运行会失败

## 🎯 下一步

- 添加更多命令到白名单
- 配置其他模型（如 Anthropic Claude, OpenAI）
- 连接消息渠道（WhatsApp, Telegram, Discord）
- 自定义 Agent 身份和行为
- 启用沙箱隔离（更安全）

---

**最后更新**: 2026-02-19  
**维护者**: OpenClaw MVP Setup  
**版本**: 1.0.0
