#!/usr/bin/env bash

set -euo pipefail

ROOT="${1:-$PWD}"
STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT="$ROOT/reports/cleanup_report_${STAMP}.md"
ARCHIVE_DIR="$ROOT/archives"
TRASH="$ROOT/.trash/$STAMP"
DRY="${DRY_RUN:-1}"         # 1=只报告不删除; 0=允许删除
APPLY="${APPLY:-0}"         # 1=执行归档+删除; 0=仅报告
KEEP_DOCS_REGEX='(^|/)(README|CONTRIBUTING|SECURITY|API)[^/]*\.md$|^docs/|/docs/|/SPEC|/Design'
KEEP_REPORTS_REGEX='^reports/(winners\.json|gold_.*\.(csv|tsv))$'

note(){ echo -e "==> $*"; }
warn(){ echo -e "\033[33m[WARN]\033[0m $*"; }
err(){  echo -e "\033[31m[ERR ]\033[0m $*"; }

mkdir -p "$ARCHIVE_DIR" "$TRASH" "$(dirname "$REPORT")"

note "环境与根路径"
echo "- PWD: $PWD" | tee "$REPORT"
echo "- ROOT: $ROOT" | tee -a "$REPORT"
echo "- DRY_RUN=$DRY  APPLY=$APPLY" | tee -a "$REPORT"

note "总体体积 & 文件数（before）" | tee -a "$REPORT"
du -sh "$ROOT" | tee -a "$REPORT" || true
find "$ROOT" -xdev -type f | wc -l | awk '{print "- files:",$1}' | tee -a "$REPORT"

note "TOP 15 最大目录（按体积）" | tee -a "$REPORT"
du -sh "$ROOT"/* 2>/dev/null | sort -h | tail -n 15 | tee -a "$REPORT" || true

note "TOP 20 最大文件" | tee -a "$REPORT"
if command -v find >/dev/null; then
  find "$ROOT" -xdev -type f -printf '%s\t%P\n' 2>/dev/null | sort -nr | head -n 20 | awk '{printf "- %s bytes\t%s\n",$1,$2}' | tee -a "$REPORT" || true
fi

# 1) 可再生目录候选（存在才处理）
REGEN_DIRS=(
  "node_modules" "dist" "build" ".venv" "__pycache__" ".cache" ".mypy_cache" ".pytest_cache"
  ".runs" "logs" "data/tmp" "experiments/tmp" "artifacts/tmp" "reports/tmp" "models/.cache"
)
CANDS_REGEN=()
echo -e "\n## 可再生目录候选" | tee -a "$REPORT"
for d in "${REGEN_DIRS[@]}"; do
  if [ -d "$ROOT/$d" ]; then
    du -sh "$ROOT/$d" 2>/dev/null | awk '{print "- " $2 "\t" $1}' | tee -a "$REPORT"
    CANDS_REGEN+=("$d")
  fi
done
if [ "${#CANDS_REGEN[@]}" -eq 0 ]; then
  echo "- 无可再生目录" | tee -a "$REPORT"
fi

# 2) 可删文档（谨慎，白名单保留）
echo -e "\n## 可删文档候选（排除白名单）" | tee -a "$REPORT"
DOCS=()
while IFS= read -r line; do
  [ -n "$line" ] && DOCS+=("$line")
done < <(find "$ROOT" -xdev -type f -name '*.md' \
  | sed "s|$ROOT/||" \
  | grep -Ev "$KEEP_DOCS_REGEX" || true)
for f in "${DOCS[@]}"; do echo "- $f"; done | tee -a "$REPORT"
DOCS_COUNT="${#DOCS[@]}"

# 3) 可删测试/临时脚本（白名单保留）
echo -e "\n## 可删测试/临时脚本候选" | tee -a "$REPORT"
TESTS=()
if [ -d "$ROOT/tests" ]; then
  while IFS= read -r line; do
    [ -n "$line" ] && TESTS+=("$line")
  done < <(cd "$ROOT" && find tests -type f | grep -Ev 'e2e|smoke' || true)
fi
for f in "${TESTS[@]}"; do echo "- $f"; done | tee -a "$REPORT"
TESTS_COUNT="${#TESTS[@]}"

# 4) 归档清单（仅在 APPLY=1 时打包）
ARCHIVE_LIST="$ARCHIVE_DIR/cleanup_${STAMP}_list.txt"
: > "$ARCHIVE_LIST"
for d in "${CANDS_REGEN[@]}"; do echo "$d" >> "$ARCHIVE_LIST"; done
for f in "${DOCS[@]}"; do echo "$f" >> "$ARCHIVE_LIST"; done
for f in "${TESTS[@]}"; do echo "$f" >> "$ARCHIVE_LIST"; done

echo -e "\n## 汇总" | tee -a "$REPORT"
echo "- 可再生目录数：${#CANDS_REGEN[@]}" | tee -a "$REPORT"
echo "- 可删文档数：$DOCS_COUNT" | tee -a "$REPORT"
echo "- 可删测试/脚本数：$TESTS_COUNT" | tee -a "$REPORT"
echo "- 归档清单：$ARCHIVE_LIST" | tee -a "$REPORT"

if [ "$DRY" = "1" ] || [ "$APPLY" = "0" ]; then
  warn "DRY-RUN 模式：不会修改任何文件。请审阅 $REPORT 后再执行 APPLY=1。"
  exit 0
fi

# 5) 执行归档 + 安全删除（移动到 .trash，再逐步清理）
note "开始归档与安全删除（移动到 $TRASH）" | tee -a "$REPORT"
mkdir -p "$TRASH"
while read -r p; do
  [ -z "$p" ] && continue
  # 保护重要产物
  if [[ "$p" =~ $KEEP_REPORTS_REGEX ]]; then
    warn "保留产物：$p"; continue
  fi
  if [ -e "$ROOT/$p" ]; then
    mkdir -p "$TRASH/$(dirname "$p")"
    mv "$ROOT/$p" "$TRASH/$p"
    echo "moved: $p" | tee -a "$REPORT"
  fi
done < "$ARCHIVE_LIST"

# 打包 trash 快照备用
( cd "$(dirname "$TRASH")" && tar -czf "$ARCHIVE_DIR/trash_snapshot_${STAMP}.tar.gz" "$(basename "$TRASH")" )
echo "- 已生成归档：$ARCHIVE_DIR/trash_snapshot_${STAMP}.tar.gz" | tee -a "$REPORT"

note "更新 .gitignore（幂等）" | tee -a "$REPORT"
GITIG="$ROOT/.gitignore"
touch "$GITIG"
add_ignore(){
  grep -qxF "$1" "$GITIG" || echo "$1" >> "$GITIG"
}
add_ignore "node_modules/"
add_ignore "dist/"
add_ignore "build/"
add_ignore ".venv/"
add_ignore "__pycache__/"
add_ignore ".cache/"
add_ignore ".mypy_cache/"
add_ignore ".pytest_cache/"
add_ignore ".runs/"
add_ignore "logs/"
add_ignore "data/tmp/"
add_ignore "experiments/tmp/"
add_ignore "artifacts/tmp/"
add_ignore "reports/tmp/"
add_ignore ".trash/"
add_ignore "archives/*.tar.gz"

note "重新统计（after）" | tee -a "$REPORT"
du -sh "$ROOT" | tee -a "$REPORT" || true
find "$ROOT" -xdev -type f | wc -l | awk '{print "- files:",$1}' | tee -a "$REPORT"

note "完成：报告已写入 $REPORT"

