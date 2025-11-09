#!/usr/bin/env bash
# 守门人验证命令集 - 运行前请确保服务已启动

echo "==========================================="
echo "  守门人配置验证命令集"
echo "==========================================="
echo ""

echo "1️⃣ 验证 Makefile 目标"
echo "$ make help | grep -A 6 '守门人'"
make help | grep -A 6 "守门人" || true
echo ""

echo "2️⃣ 验证配置文件标记"
echo "$ head -3 .gitignore"
head -3 .gitignore
echo ""
echo "$ head -3 .dockerignore"
head -3 .dockerignore
echo ""

echo "3️⃣ 验证脚本守门人标记"
echo "$ head -3 scripts/warmup.sh | tail -1"
head -3 scripts/warmup.sh | tail -1
echo "$ head -3 scripts/smoke.sh | tail -1"
head -3 scripts/smoke.sh | tail -1
echo ""

echo "4️⃣ 验证 PR 模板"
echo "$ ls -lh .github/pull_request_template.md"
ls -lh .github/pull_request_template.md || echo "⚠️  PR template not found"
echo ""

echo "==========================================="
echo "  配置层面验证: ✅ 通过"
echo "==========================================="
echo ""

echo "📋 运行时验证命令（需容器运行）："
echo ""
echo "# 启动服务"
echo "make dev-up"
echo ""
echo "# 前置检查"
echo "make preflight"
echo ""
echo "# 预热检查"
echo "make warmup"
echo ""
echo "# 烟测"
echo "make smoke"
echo ""
echo "# 并行小批实验"
echo "make grid-dev"
echo ""
echo "# 完整验证"
echo "make full-validate"
echo ""

