# OpenClaw MVP 快速启动指南

## 🚀 5 分钟完成剩余步骤

OpenClaw 已安装并配置完成，只需完成 Ollama 安装即可运行。

### 步骤 1: 安装 Ollama (需要 sudo)

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**验证**:
```bash
ollama --version
```

### 步骤 2: 拉取模型

```bash
ollama pull llama3.3
```

**验证**:
```bash
ollama list
# 应该看到: llama3.3
```

### 步骤 3: 启动 Ollama 服务

```bash
# 在后台启动
ollama serve &

# 或使用 systemd (如果已配置)
systemctl --user start ollama
```

**验证**:
```bash
curl http://127.0.0.1:11434/api/tags
```

### 步骤 4: 测试模型

```bash
ollama run llama3.3 "hello"
```

**预期**: 模型返回一段文本响应

### 步骤 5: 运行 Smoke Test

```bash
cd ~/searchforge
./scripts/openclaw_smoke_test.sh
```

**预期结果**:
- ✅ Gateway 启动成功
- ✅ Agent 响应消息
- ✅ 成功执行 `ls` 命令

### 步骤 6: 访问 Dashboard

打开浏览器: http://127.0.0.1:18789/

在聊天中输入: "List files in current directory"

## ⚡ 一键脚本（如果已安装 Ollama）

```bash
# 确保 Ollama 运行
ollama serve > /dev/null 2>&1 &

# 拉取模型（如果未拉取）
ollama pull llama3.3

# 运行 smoke test
cd ~/searchforge && ./scripts/openclaw_smoke_test.sh
```

## 🐛 常见问题

### Ollama 安装失败

**错误**: `sudo: a password is required`

**解决**: 手动执行安装命令，输入密码：
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 模型拉取慢

**原因**: 模型文件较大（几 GB）

**解决**: 耐心等待，或使用更小的模型：
```bash
ollama pull llama3  # 更小的模型
```

### Gateway 启动失败

**检查**:
```bash
# 查看日志
tail -f /tmp/openclaw-gateway.log

# 检查端口
lsof -i :18789

# 检查配置
cd ~/ai-tools/openclaw
pnpm openclaw doctor
```

## 📊 验证清单

完成以下检查后，OpenClaw MVP 即可运行：

- [ ] `ollama --version` 有输出
- [ ] `ollama list` 显示 llama3.3
- [ ] `ollama run llama3.3 "hello"` 返回响应
- [ ] `curl http://127.0.0.1:11434/api/tags` 成功
- [ ] `./scripts/openclaw_smoke_test.sh` 通过
- [ ] http://127.0.0.1:18789/ 可访问

---

**预计完成时间**: 5-10 分钟（取决于网络速度）
