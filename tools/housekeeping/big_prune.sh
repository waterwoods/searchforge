#!/usr/bin/env bash

set -euo pipefail

ROOT="${1:-$PWD}"
STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT="$ROOT/reports/big_prune_${STAMP}.md"
ARCHIVE_DIR="$ROOT/archives"
TRASH="$ROOT/.trash/$STAMP"
DRY="${DRY_RUN:-1}"   # 1=只报告; 0=允许删除
APPLY="${APPLY:-0}"   # 1=执行归档; 0=仅报告

note(){ echo "==> $*"; }

mkdir -p "$(dirname "$REPORT")" "$ARCHIVE_DIR" "$TRASH"

note "总体情况" | tee "$REPORT"
du -sh "$ROOT" | tee -a "$REPORT"
find "$ROOT" -xdev -type f | wc -l | awk '{print "- files:",$1}' | tee -a "$REPORT"

note "≥50MB 目录（top 20）" | tee -a "$REPORT"
du -sm "$ROOT"/* 2>/dev/null | sort -nr | awk '$1>=50{printf "- %4d MB\t%s\n",$1,$2}' | head -20 | tee -a "$REPORT" || true

note "≥50MB 文件（top 30）" | tee -a "$REPORT"
find "$ROOT" -xdev -type f -size +50M -printf '%s\t%P\n' 2>/dev/null \
  | sort -nr | head -30 | awk '{mb=$1/1024/1024; printf "- %7.1f MB\t%s\n",mb,$2}' | tee -a "$REPORT" || true

# 这些通常是大头（仅候选，存在才处理）
CAND_DIRS=( ".runs" "reports/artifacts" "experiments/data" "models" "reports/raw" )
echo -e "\n## 候选目录体积" | tee -a "$REPORT"
TO_ARCHIVE=()

for d in "${CAND_DIRS[@]}"; do
  if [ -d "$ROOT/$d" ]; then
    du -sh "$ROOT/$d" 2>/dev/null | awk '{print "- "$2"\t"$1}' | tee -a "$REPORT"
    TO_ARCHIVE+=("$d")
  fi
done
[ ${#TO_ARCHIVE[@]} -eq 0 ] && echo "- 无候选目录" | tee -a "$REPORT"

echo -e "\n## 保护清单（永远保留）" | tee -a "$REPORT"
echo "- 代码与配置：services/**, ui/**, configs/**, docker-compose.yml, Makefile, scripts/**" | tee -a "$REPORT"
echo "- 报告关键：reports/winners.json, reports/gold_*.csv/tsv, docs/**, README*" | tee -a "$REPORT"

if [ "$DRY" = "1" ] || [ "$APPLY" = "0" ]; then
  echo -e "\n[DRY-RUN] 仅报告，不做任何修改。报告见：$REPORT"
  exit 0
fi

note "归档+安全删除（移动到 $TRASH）" | tee -a "$REPORT"
for p in "${TO_ARCHIVE[@]}"; do
  [ -e "$ROOT/$p" ] || continue
  mkdir -p "$TRASH/$(dirname "$p")"
  mv "$ROOT/$p" "$TRASH/$p"
  echo "moved: $p" | tee -a "$REPORT"
done

# archives 里仅保留最新 1 个 trash_snapshot
note "打包回滚快照" | tee -a "$REPORT"
( cd "$(dirname "$TRASH")" && tar -czf "$ARCHIVE_DIR/trash_snapshot_${STAMP}.tar.gz" "$(basename "$TRASH")" )
echo "- 归档：$ARCHIVE_DIR/trash_snapshot_${STAMP}.tar.gz" | tee -a "$REPORT"

# 清理旧快照（保留最新1个）
ls -1t "$ARCHIVE_DIR"/trash_snapshot_*.tar.gz 2>/dev/null | tail -n +2 | xargs -r rm -f

note "更新 .gitignore（幂等）" | tee -a "$REPORT"
GITIG="$ROOT/.gitignore"; touch "$GITIG"
for line in \
  ".runs/" "reports/artifacts/" "reports/raw/" "experiments/data/" "models/" ".trash/" "archives/*.tar.gz"
do grep -qxF "$line" "$GITIG" || echo "$line" >> "$GITIG"; done

note "After 统计" | tee -a "$REPORT"
du -sh "$ROOT" | tee -a "$REPORT"
find "$ROOT" -xdev -type f | wc -l | awk '{print "- files:",$1}' | tee -a "$REPORT"

echo "完成：$REPORT"

