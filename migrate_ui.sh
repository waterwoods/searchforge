#!/bin/bash
# UI 迁移脚本 - 迁移执行官
# 使用前请修改以下变量为实际值

set -e  # 遇到错误立即退出

# === 需填写的变量（按实际修改）===
SRC_HOST="${SRC_HOST:-mbp.local}"           # 旧 Mac 的可 SSH 访问主机名/IP
SRC_DIR="${SRC_DIR:-~/searchforge/ui}"      # 旧 Mac 上 ui 目录的绝对路径
DEST_REPO="${DEST_REPO:-/home/andy/searchforge}"  # RTX3080 上仓库根目录

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="${DEST_REPO}/reports/UI_MIGRATE_${TIMESTAMP}.md"

echo "=== UI 迁移执行官 ==="
echo "源主机: ${SRC_HOST}"
echo "源目录: ${SRC_DIR}"
echo "目标仓库: ${DEST_REPO}"
echo ""

# === 1) 预检 ===
echo "[1/5] 预检..."
mkdir -p "${DEST_REPO}/reports"
cd "${DEST_REPO}"

# 确认是 git 仓库
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "错误: ${DEST_REPO} 不是 git 仓库"
    exit 1
fi

# 检查工作区状态（仅警告，不阻止）
GIT_STATUS=$(git status --porcelain)
if [ -n "$GIT_STATUS" ]; then
    echo "警告: git 工作区有未提交的更改（继续执行）"
fi

# 备份现有 ui/ 目录
BACKUP_DIR=""
if [ -d ui ]; then
    BACKUP_DIR="ui_bak_${TIMESTAMP}"
    mv ui "${BACKUP_DIR}"
    echo "已备份现有 ui/ 到 ${BACKUP_DIR}/"
else
    echo "ui/ 目录不存在，无需备份"
fi

# === 2) 迁移（rsync）===
echo ""
echo "[2/5] 迁移（rsync）..."
echo "正在从 ${SRC_HOST}:${SRC_DIR} 同步到 ${DEST_REPO}/ui/ ..."

# 测试 SSH 连接
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "${SRC_HOST}" "echo 'SSH 连接测试成功'" >/dev/null 2>&1; then
    echo "错误: 无法连接到 ${SRC_HOST}"
    echo "请检查："
    echo "  1. 主机名/IP 是否正确"
    echo "  2. SSH 密钥是否已配置"
    echo "  3. MacBook Pro 是否在线且允许 SSH 连接"
    echo ""
    echo "可以通过以下方式设置："
    echo "  export SRC_HOST=192.168.x.x  # 使用 IP 地址"
    echo "  或修改脚本中的 SRC_HOST 变量"
    exit 1
fi

# 执行 rsync
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude '.next' \
    --exclude 'dist' \
    --exclude '.git' \
    "${SRC_HOST}:${SRC_DIR}/" "${DEST_REPO}/ui/" 2>&1 | tee /tmp/rsync_${TIMESTAMP}.log

RSYNC_EXIT_CODE=${PIPESTATUS[0]}
if [ $RSYNC_EXIT_CODE -ne 0 ]; then
    echo "错误: rsync 失败（退出码: $RSYNC_EXIT_CODE）"
    exit 1
fi

echo "rsync 同步完成"

# === 3) 校验 ===
echo ""
echo "[3/5] 校验..."

# 检查关键文件
if [ ! -f ui/package.json ]; then
    echo "错误: package.json 缺失"
    exit 1
fi

# 打印 package.json 信息
echo "package.json 内容摘要:"
node -e "const p=require('./ui/package.json');console.log(JSON.stringify({name:p.name,scripts:p.scripts},null,2))" 2>/dev/null || {
    echo "警告: 无法解析 package.json（可能需要安装 node）"
    echo "package.json 前20行:"
    head -20 ui/package.json
}

# 统计文件数和体积
UI_SIZE=$(du -sh ui 2>/dev/null | awk '{print $1}' || echo "未知")
FILE_COUNT=$(find ui -type f 2>/dev/null | wc -l || echo "未知")

echo ""
echo "文件统计:"
echo "  总体积: ${UI_SIZE}"
echo "  文件数: ${FILE_COUNT}"

# 检查关键目录
echo ""
echo "关键目录检查:"
[ -d ui/src ] && echo "  ✓ src/ 存在" || echo "  ✗ src/ 缺失"
[ -d ui/public ] && echo "  ✓ public/ 存在" || echo "  ✗ public/ 缺失"
if [ -f ui/vite.config.ts ] || [ -f ui/vite.config.js ]; then
    echo "  ✓ vite.config.* 存在"
else
    echo "  ⚠ vite.config.* 未找到"
fi

# 列出 ui 目录内容（前20项）
echo ""
echo "ui/ 目录内容（前20项）:"
ls -la ui | head -20

# === 4) 软链（可选）===
echo ""
echo "[4/5] 兼容性检查..."
if [ -d frontend ] && [ ! -L frontend ]; then
    echo "警告: frontend/ 已存在且不是软链，跳过创建"
elif [ ! -e frontend ]; then
    ln -s ui frontend
    echo "已创建软链: frontend -> ui"
else
    echo "frontend 软链已存在，跳过"
fi

# === 5) 报告 ===
echo ""
echo "[5/5] 生成迁移报告..."

cat > "${REPORT_FILE}" <<EOF
# UI 迁移报告

**迁移时间**: $(date '+%Y-%m-%d %H:%M:%S')
**时间戳**: ${TIMESTAMP}

## 迁移配置

- **源主机**: ${SRC_HOST}
- **源目录**: ${SRC_DIR}
- **目标仓库**: ${DEST_REPO}
- **目标目录**: ${DEST_REPO}/ui/

## 备份信息

$(if [ -n "$BACKUP_DIR" ]; then echo "- **备份目录**: ${BACKUP_DIR}/"; else echo "- **备份目录**: 无（ui/ 目录不存在）"; fi)

## Rsync 配置

- **排除规则**: node_modules, .next, dist, .git
- **同步模式**: 归档模式（-avz）
- **日志文件**: /tmp/rsync_${TIMESTAMP}.log

## 文件统计

- **总体积**: ${UI_SIZE}
- **文件数**: ${FILE_COUNT}

## Package.json 摘要

\`\`\`json
$(node -e "const p=require('./ui/package.json');console.log(JSON.stringify({name:p.name,scripts:p.scripts},null,2))" 2>/dev/null || echo "无法解析 package.json")
\`\`\`

## 关键文件检查

$(if [ -d ui/src ]; then echo "- ✓ src/ 目录存在"; else echo "- ✗ src/ 目录缺失"; fi)
$(if [ -d ui/public ]; then echo "- ✓ public/ 目录存在"; else echo "- ✗ public/ 目录缺失"; fi)
$(if [ -f ui/vite.config.ts ] || [ -f ui/vite.config.js ]; then echo "- ✓ vite.config.* 存在"; else echo "- ⚠ vite.config.* 未找到"; fi)

## 软链状态

$(if [ -L frontend ]; then echo "- ✓ frontend -> ui 软链已创建"; elif [ -d frontend ]; then echo "- ⚠ frontend/ 目录已存在（非软链）"; else echo "- frontend 软链未创建"; fi)

## 后续步骤

### 1. API 健康检查

确保后端 API 服务正在运行（端口 8000）：

\`\`\`bash
# 检查 API 就绪状态
curl -sf http://localhost:8000/ready && echo "API 就绪"

# 检查 embeddings 健康状态
curl -sf http://localhost:8000/api/health/embeddings && echo "Embeddings 健康"
\`\`\`

### 2. 安装依赖

\`\`\`bash
cd ${DEST_REPO}/ui
npm ci || npm install
\`\`\`

### 3. 启动前端开发服务器

\`\`\`bash
cd ${DEST_REPO}/ui
npm run dev -- --port 5173 --open
\`\`\`

### 4. 代理配置确认

如果前端需要代理 API 请求，请确认 \`vite.config.*\` 中的代理配置：

\`\`\`javascript
// 示例配置
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
\`\`\`

## 注意事项

1. ✅ **端口配置**: 未修改任何端口配置（API 保持 8000，前端使用 5173）
2. ✅ **代码修改**: 未进行任何代码改写，仅搬运和校验
3. ✅ **回滚点**: $(if [ -n "$BACKUP_DIR" ]; then echo "备份目录 ${BACKUP_DIR}/ 可作为回滚点"; else echo "无需回滚（ui/ 目录原本不存在）"; fi)

## 迁移完成

迁移已成功完成。所有文件已从 ${SRC_HOST}:${SRC_DIR} 同步到 ${DEST_REPO}/ui/

---

*报告生成时间: $(date '+%Y-%m-%d %H:%M:%S')*
EOF

echo "迁移报告已生成: ${REPORT_FILE}"
echo ""
echo "=== 迁移完成 ==="
echo "报告位置: ${REPORT_FILE}"
echo ""
echo "下一步:"
echo "  1. 检查迁移报告: cat ${REPORT_FILE}"
echo "  2. 安装依赖: cd ui && npm ci"
echo "  3. 启动开发服务器: cd ui && npm run dev -- --port 5173"

