#!/usr/bin/env bash
# === Goal: 快速恢复 fiqa_para_50k 的"老 doc_id" ===

# 前提：你在 RTX3080 机器上、目录为 ~/searchforge

set -euo pipefail

echo "[step0] goto project root"

cd ~/searchforge

echo "[step1] sanity check (qdrant pinned + api up)"

make diag-now || true

echo "[step2] 搜索权威映射 JSON（优先 .runs / snapshots / 旧备份）"

# 检查 jq 是否安装
if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq 未安装，请先安装 jq"
  exit 1
fi

MAP_CANDIDATES=$(
  (find "$HOME/searchforge" -type f -name "*docid*map*fiqa*para*.json" 2>/dev/null; \
   find "$HOME/searchforge/.runs" -type f -name "*docid*map*.json" 2>/dev/null; \
   find "$HOME/searchforge/snapshots" -type f -name "*docid*map*.json" 2>/dev/null) \
  | sort -u)

BEST_MAP=""
BEST_LEN=0

for f in $MAP_CANDIDATES; do
  LEN=$(jq 'length' "$f" 2>/dev/null || echo 0)
  # 经验：权威映射应在 49k~51k 条之间
  if [ "$LEN" -ge 49000 ] && [ "$LEN" -le 51000 ]; then
    if [ "$LEN" -gt "$BEST_LEN" ]; then
      BEST_LEN=$LEN
      BEST_MAP="$f"
    fi
  fi
done

if [ -n "${BEST_MAP}" ]; then
  echo "[step3A] 找到权威映射：$BEST_MAP （length=$BEST_LEN）→ 直接回写"
  mkdir -p .runs
  cp -f "$BEST_MAP" ./.runs/docid_map_fiqa_para_50k.json
  make docid-apply COLLECTION=fiqa_para_50k
  make docid-verify COLLECTION=fiqa_para_50k SAMPLE=200
  make policy-smoke
  echo "[done] 已用权威映射恢复 doc_id；验收通过。"
  exit 0
fi

echo "[step3B] 没有权威映射；尝试使用带旧 doc_id 的 manifest 生成映射"

MANI=$(
  (find experiments -type f -name "manifest_*50k*.*json*" 2>/dev/null; \
   find data -type f -name "manifest_*50k*.*json*" 2>/dev/null; \
   find snapshots -type f -name "manifest_*50k*.*json*" 2>/dev/null; \
   find data -type f -name "corpus_*50k*.jsonl" 2>/dev/null) \
  | head -n 1 || true)

if [ -n "${MANI:-}" ]; then
  echo "  - 发现 manifest/corpus: $MANI"
  # 确保路径是绝对路径
  if [ ! -f "$MANI" ]; then
    echo "[ERROR] Manifest file not found: $MANI"
    exit 1
  fi
  # 转换为绝对路径
  MANI_ABS=$(cd "$(dirname "$MANI")" && pwd)/$(basename "$MANI")
  echo "  - 使用绝对路径: $MANI_ABS"
  
  # 生成：由文本 SHA1 → 旧 doc_id 的映射
  export MANI="$MANI_ABS"
  python3 - <<'PY'
import json
import hashlib
import sys
import os

mani = os.environ.get("MANI")
if not mani:
    print("[ERROR] MANI environment variable not set", file=sys.stderr)
    sys.exit(1)

if not os.path.exists(mani):
    print(f"[ERROR] Manifest file not found: {mani}", file=sys.stderr)
    sys.exit(1)

out = ".runs/docid_map_fiqa_para_50k.json"
os.makedirs(".runs", exist_ok=True)

mp = {}

def sha1(t):
    """Compute SHA1 hash of normalized text."""
    if not t:
        return ""
    # Normalize: replace CRLF/LF with space, strip whitespace
    normalized = t.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').strip()
    return hashlib.sha1(normalized.encode('utf-8')).hexdigest()

# Handle JSONL files (corpus files)
if mani.endswith('.jsonl'):
    print(f"[INFO] Reading JSONL file: {mani}")
    with open(mani, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                text = d.get("text") or d.get("body") or d.get("content") or ""
                old = d.get("id") or d.get("doc_id") or d.get("docId") or d.get("docid")
                if not text or not old:
                    continue
                mp[sha1(text)] = str(old)
            except json.JSONDecodeError as e:
                if line_num % 10000 == 0:
                    print(f"[WARN] Failed to parse line {line_num}: {e}", file=sys.stderr)
                continue
    print(f"[INFO] Processed {line_num} lines from JSONL file")
else:
    # Handle JSON files (manifest files)
    print(f"[INFO] Reading JSON file: {mani}")
    try:
        with open(mani, 'r', encoding='utf-8') as f:
            m = json.load(f)
        # 兼容形态：[{id: "000123", text: "..."}] 或 [{doc_id:..., text:...}] 或 {"docs":[...]}
        docs = m.get("docs", m if isinstance(m, list) else [])
        if not docs:
            print(f"[WARN] No docs found in manifest. Keys: {list(m.keys()) if isinstance(m, dict) else 'N/A'}", file=sys.stderr)
        for d in docs:
            text = d.get("text") or d.get("body") or d.get("content") or ""
            old = d.get("id") or d.get("doc_id") or d.get("docId") or d.get("docid")
            if not text or not old:
                continue
            mp[sha1(text)] = str(old)
        print(f"[INFO] Processed {len(docs)} documents from JSON file")
    except Exception as e:
        print(f"[ERROR] Failed to parse manifest: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if not mp:
    print("[ERROR] No mappings generated. Check manifest file format.", file=sys.stderr)
    sys.exit(1)

with open(out, "w", encoding="utf-8") as f:
    json.dump(mp, f, ensure_ascii=False, indent=2)

print(f"[gen] wrote {len(mp)} pairs to {out}")
PY

  if [ ! -f ".runs/docid_map_fiqa_para_50k.json" ]; then
    echo "[ERROR] Failed to generate mapping file"
    exit 1
  fi

  MAP_LEN=$(jq 'length' .runs/docid_map_fiqa_para_50k.json 2>/dev/null || echo 0)
  if [ "$MAP_LEN" -lt 49000 ]; then
    echo "[WARN] Generated mapping has only $MAP_LEN entries (expected ~50k)"
    echo "[WARN] Continuing anyway..."
  fi

  echo "  - 回写映射到库（保持向量不变，仅替换 doc_id）"
  make docid-apply COLLECTION=fiqa_para_50k
  make docid-verify COLLECTION=fiqa_para_50k SAMPLE=200
  make policy-smoke
  echo "[done] 已用 manifest 生成映射并恢复；验收通过。"
  exit 0
fi

echo "[step3C] 既无权威映射，也无带旧 doc_id 的 manifest —— 停止（避免误修）。"
echo "建议："
echo "  1) 继续在 RTX3080 上找 .runs/docid_map_fiqa_para_50k.json / manifest_*50k*.json"
echo "  2) 或把你本地/TimeMachine/旧卷里的 manifest/映射拷过来后重跑本脚本"
exit 2

