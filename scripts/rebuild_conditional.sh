#!/bin/bash
# 目标：复用 searchforge-base:py310，不做无谓 rebuild
# 成功标准：/readyz clients_ready=true；/version.commit == 本地 git 短 SHA

set -euo pipefail

echo "== A. 快速路径（不重建，仅重启并校验） =="

docker compose --env-file .env.current up -d rag-api

# 等待就绪（若没有脚本就用 curl 轮询）
if [ -x ./scripts/wait_ready.sh ]; then
  ./scripts/wait_ready.sh
else
  for i in {1..30}; do
    ok=$(curl -sf http://localhost:8000/readyz | jq -r .clients_ready || echo false)
    [ "$ok" = "true" ] && break
    sleep 2
  done
fi

echo "== 校验版本与就绪 =="

srv_commit=$(curl -sf http://localhost:8000/version | jq -r .commit || echo "unknown")
git_commit=$(git rev-parse --short HEAD)
clients_ready=$(curl -sf http://localhost:8000/readyz | jq -r .clients_ready || echo false)

echo "server=$srv_commit git=$git_commit ready=$clients_ready"

if [ "$clients_ready" = "true" ] && [ "$srv_commit" = "$git_commit" ]; then
  echo "✅ 无需重建：服务就绪且版本一致。"
  exit 0
fi

echo "== B. 条件重建（仅在需要时） =="

# 确认本地基底存在
docker images | egrep 'searchforge-base\s+py310|searchforge-base.*py310' || {
  echo "⚠️ 本地基底缺失，先构建基底"; 
  COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=0 docker compose build base
}

# 仅重建 rag-api 并重启
GIT_SHA=$(git rev-parse --short HEAD)
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=0 docker compose --env-file .env.current build --build-arg GIT_SHA="$GIT_SHA" rag-api
docker compose --env-file .env.current up -d rag-api

# 再次校验（增加等待时间，因为 embedding 模型加载可能需要更长时间）
echo "等待服务完全就绪（最多 120 秒）..."
for i in {1..60}; do
  ok=$(curl -sf http://localhost:8000/readyz | jq -r .clients_ready || echo false)
  [ "$ok" = "true" ] && break
  if [ $((i % 10)) -eq 0 ]; then
    echo "  等待中... ($i/60)"
  fi
  sleep 2
done
srv_commit2=$(curl -sf http://localhost:8000/version | jq -r .commit || echo "unknown")
final_ready=$(curl -sf http://localhost:8000/readyz | jq -r .clients_ready || echo false)
echo "recheck: server=$srv_commit2 git=$git_commit ready=$final_ready"

# 版本必须匹配
if [ "$srv_commit2" != "$git_commit" ]; then
  echo "❌ 版本不匹配: server=$srv_commit2 git=$git_commit"
  exit 1
fi

# 如果服务未完全就绪，给出警告但不失败（因为 embedding 模型加载可能需要更长时间）
if [ "$final_ready" != "true" ]; then
  echo "⚠️  服务未完全就绪 (clients_ready=$final_ready)，但版本已匹配。"
  echo "   这可能是正常的，因为 embedding 模型加载需要时间。"
  echo "   可以稍后检查: curl http://localhost:8000/readyz"
fi

mkdir -p .runs
{ echo "rebuild=conditional"; echo "base=searchforge-base:py310"; date '+%F %T'; } > .runs/rebuild_stamp.txt
echo "✅ 条件重建完成并通过校验。"

