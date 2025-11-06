#!/usr/bin/env bash

set -euo pipefail

ROOT="${1:-$PWD}"
STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT="$ROOT/reports/docs_tests_orphans_${STAMP}.md"
TRASH="$ROOT/.trash/${STAMP}"
ARCHIVE="$ROOT/archives/trash_docs_tests_${STAMP}.tar.gz"
DRY="${DRY_RUN:-1}"   # 1=仅报告; 0=允许移动
APPLY="${APPLY:-0}"   # 1=执行归档; 0=只报告

note(){ echo "==> $*"; }

mkdir -p "$(dirname "$REPORT")" "$TRASH" "$(dirname "$ARCHIVE")"

echo "# Prune Report (${STAMP})" | tee "$REPORT"
du -sh "$ROOT" | awk '{print "Repo size: **"$1"**"}' | tee -a "$REPORT"
echo >> "$REPORT"

# 1) 文档 *.md 候选（保留 README/CHANGELOG/CONTRIBUTING/LICENSE 与 docs/**，排除 .trash）

KEEP_MD_REGEX='^(README|CHANGELOG|CONTRIBUTING|LICENSE)(\.md)?$'
mapfile -t ALL_MD < <(find "$ROOT" -type f -name '*.md' -not -path '*/.trash/*' -printf '%P\n' | sort)
MD_CAND=()

for f in "${ALL_MD[@]}"; do
  base="$(basename "$f")"
  case "$f" in
    docs/*) continue;;
    .trash/*) continue;;
  esac
  if [[ ! "$base" =~ $KEEP_MD_REGEX ]]; then
    MD_CAND+=("$f")
  fi
done

# 2) tests 目录（排除 .trash）

mapfile -t TEST_DIRS < <(find "$ROOT" -type d \( -iname 'tests' -o -iname 'test' \) -not -path '*/.trash/*' -printf '%P\n' | sort)

# 3) 孤儿脚本（scripts/**, tools/** 下的 .sh/.py 未被 Makefile/其他代码引用，排除 housekeeping 脚本本身）

mapfile -t CAND_SCRIPTS < <(find "$ROOT"/{scripts,tools} -type f \( -name '*.sh' -o -name '*.py' \) -not -path '*/.trash/*' -printf '%P\n' 2>/dev/null | sort || true)
ORPHANS=()

if [ ${#CAND_SCRIPTS[@]} -gt 0 ]; then
  for rel in "${CAND_SCRIPTS[@]}"; do
    # 排除 housekeeping 脚本本身
    [[ "$rel" =~ tools/housekeeping/ ]] && continue
    # 在仓库内搜索是否被引用（包括 Makefile/py/sh/ts/js/yaml 等，排除 .trash）
    if ! grep -RqsF "$rel" --exclude-dir=.trash "$ROOT"/* 2>/dev/null; then
      ORPHANS+=("$rel")
    fi
  done
fi

# 4) 其他一次性产物（排除 .trash）

mapfile -t TRASHY < <(find "$ROOT" -type d \( -name '__pycache__' -o -name '.pytest_cache' \) -not -path '*/.trash/*' -printf '%P\n' | sort)
mapfile -t LOGS   < <(find "$ROOT" -type f -name '*.log' -not -path '*/.trash/*' -printf '%P\n' | sort)

# 汇总报告

echo "## Candidates" | tee -a "$REPORT"
echo "- MD files (excluding README*/docs/**): ${#MD_CAND[@]}" | tee -a "$REPORT"
echo "- Test dirs: ${#TEST_DIRS[@]}" | tee -a "$REPORT"
echo "- Orphan scripts: ${#ORPHANS[@]}" | tee -a "$REPORT"
echo "- Caches/logs: $(( ${#TRASHY[@]}+${#LOGS[@]} ))" | tee -a "$REPORT"
echo >> "$REPORT"

dump_list(){ local title="$1"; shift; local arr=("$@"); echo "### $title (${#arr[@]})" | tee -a "$REPORT"; for x in "${arr[@]}"; do echo "- $x" | tee -a "$REPORT"; done; echo >> "$REPORT"; }

dump_list "MD to prune" "${MD_CAND[@]}"
dump_list "Test dirs" "${TEST_DIRS[@]}"
dump_list "Orphan scripts" "${ORPHANS[@]}"
dump_list "Caches" "${TRASHY[@]}"
dump_list "Logs" "${LOGS[@]}"

[ "$DRY" = "1" ] || [ "$APPLY" = "0" ] && { echo -e "\n[DRY-RUN] 仅报告，未做改动。\n报告: $REPORT"; exit 0; }

# 执行归档移动

move_it(){ 
  local p="$1"
  [ -e "$ROOT/$p" ] || return 0
  mkdir -p "$TRASH/$(dirname "$p")"
  if ! mv "$ROOT/$p" "$TRASH/$p" 2>/dev/null; then
    # 如果移动失败，尝试使用 sudo 或跳过
    echo "Warning: failed to move $p, skipping" | tee -a "$REPORT"
    return 1
  fi
  return 0
}

note "Archiving to $TRASH"
for f in "${MD_CAND[@]}"; do move_it "$f" || true; done
for d in "${TEST_DIRS[@]}"; do move_it "$d" || true; done
for f in "${ORPHANS[@]}"; do move_it "$f" || true; done
for d in "${TRASHY[@]}"; do move_it "$d" || true; done
for f in "${LOGS[@]}";   do move_it "$f" || true; done

note "Packing snapshot $ARCHIVE"
( cd "$ROOT/.trash" && tar -czf "$ARCHIVE" "$(basename "$TRASH")" )
echo "- archive: $ARCHIVE" | tee -a "$REPORT"

echo -e "\nDone. You can restore from .trash or the archive if needed.\nReport: $REPORT"

