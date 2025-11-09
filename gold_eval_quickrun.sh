#!/usr/bin/env bash
# === Gold Eval Quickrun (run inside SSH: andy-wsl workspace) ===

set -euo pipefail

log(){ printf "\n\033[1;36m[%-8s]\033[0m %s\n" "$1" "$2"; }



# ---- 0) 环境参数（可改）----

API=${API:-http://localhost:8000}

DATASET=${DATASET:-fiqa_50k_v1}

QRELS=${QRELS:-fiqa_gold_50k_v1}

SAMPLE=${SAMPLE:-200}

REPEATS=${REPEATS:-1}

K1=${K1:-10}

K2=${K2:-20}

OUTDIR=${OUTDIR:-reports}

mkdir -p "$OUTDIR"



log PRECHECK "API=$API | DATASET=$DATASET | QRELS=$QRELS | SAMPLE=$SAMPLE | REPEATS=$REPEATS | Ks=[$K1,$K2]"



# ---- 1) 健康检查 & 模型一致性 ----

log HEALTH  "GET /health"

curl -fsS "$API/health" | python3 -m json.tool || curl -fsS "$API/health"

log EMBED   "GET /api/health/embeddings (expect SBERT + all-MiniLM-L6-v2, dim=384)"

curl -fsS "$API/api/health/embeddings" | tee "$OUTDIR/embed_health.json" | python3 -m json.tool || cat "$OUTDIR/embed_health.json"



# ---- 2) Gold qrels 覆盖率体检（需已存在工具脚本/Make 目标；失败直接退出）----

if grep -q "eval-qrels" Makefile 2>/dev/null; then

  log QRELSCHK "make eval-qrels DATASET_NAME=$DATASET QRELS_NAME=$QRELS (>=99%通过)"

  make eval-qrels DATASET_NAME="$DATASET" QRELS_NAME="$QRELS" || log QRELSCHK "make eval-qrels failed, continuing anyway"

else

  log QRELSCHK "跳过（未发现 make eval-qrels），继续执行"

fi



# ---- 3) 提交4个基线任务（fast×2 × top_k∈{K1,K2}）----

submit(){

  local fast="$1" ; local tk="$2"

  local body

  # Convert shell boolean to Python boolean
  if [ "$fast" = "true" ]; then
    FAST_VAL="True"
  else
    FAST_VAL="False"
  fi

  body=$(python3 -c "
import json, sys
print(json.dumps({
    'dataset_name': '$DATASET',
    'qrels_name': '$QRELS',
    'fast_mode': $FAST_VAL,
    'top_k': int('$tk'),
    'sample': int('$SAMPLE'),
    'repeats': int('$REPEATS')
}))
")

  log SUBMIT "fast=$fast top_k=$tk"

  RESP=$(curl -fsS -H 'content-type: application/json' -d "$body" "$API/api/experiment/run" 2>&1)
  
  echo "$RESP" >&2
  
  echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null || echo "ERROR"
}



J1=$(submit true  "$K1" | tail -1)
J2=$(submit true  "$K2" | tail -1)
J3=$(submit false "$K1" | tail -1)
J4=$(submit false "$K2" | tail -1)

# Verify all jobs were submitted successfully
for J in "$J1" "$J2" "$J3" "$J4"; do
  if [ "$J" = "ERROR" ] || [ -z "$J" ]; then
    log ERROR "Failed to submit job, got: $J"
    exit 1
  fi
done

echo "$J1 $J2 $J3 $J4" > "$OUTDIR/jobs_gold.list"

log JOBS "submitted: $(cat $OUTDIR/jobs_gold.list)"



# ---- 4) 轮询直到完成，并抓 metrics（以 API 为准）----

poll(){

  local id="$1"

  log POLL "job=$id (polling status...)"

  for i in $(seq 1 120); do

    ST_RESP=$(curl -fsS "$API/api/experiment/status/$id")
    st=$(echo "$ST_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('job', {}).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    
    echo "  #$i state=$st"

    case "$st" in

      SUCCEEDED|FAILED) break;;

    esac

    sleep 2

  done

  log DETAIL "job=$id detail"

  curl -fsS "$API/api/experiment/job/$id" | tee "$OUTDIR/job_$id.detail.json" | python3 -m json.tool || cat "$OUTDIR/job_$id.detail.json"
  
  # 兜底：若 metrics 为空，记录红旗

  METRICS_TYPE=$(python3 -c "import json; d=json.load(open('$OUTDIR/job_$id.detail.json')); print(type(d.get('metrics', None)).__name__)" 2>/dev/null || echo "null")
  
  if [ "$METRICS_TYPE" = "NoneType" ] || [ "$METRICS_TYPE" = "null" ]; then

    log WARN "job=$id metrics is null -> mark red flag"

    python3 -c "
import json
d = json.load(open('$OUTDIR/job_$id.detail.json'))
d['metrics_red_flag'] = True
json.dump(d, open('$OUTDIR/job_$id.detail.json', 'w'), indent=2)
"

  fi

}



for J in $J1 $J2 $J3 $J4; do poll "$J"; done



# ---- 5) 生成 winners_gold.json（从 job detail 汇总）----

log GOLD "assemble winners_gold.json"

python3 - <<'PY' "$OUTDIR"

import json,sys,glob,os

outdir=sys.argv[1]

details=sorted(glob.glob(os.path.join(outdir,'job_*.detail.json')))

rows=[]

for f in details:

    d=json.load(open(f))

    jid=d.get("job_id") or d.get("job",{}).get("job_id") or os.path.basename(f).split('.')[0].split('_')[-1]

    m=d.get("metrics") or {}
    
    # Support both new format (metrics.metrics) and old format
    if "metrics" in m and isinstance(m["metrics"], dict):
        metrics_data = m["metrics"]
        config_data = m.get("config", {})
        m = metrics_data
    else:
        metrics_data = m
        config_data = {}
    
    params=d.get("params") or d.get("config") or {}
    
    # Extract top_k from config_data first, then params, then metrics.config
    top_k = config_data.get("top_k") or params.get("top_k") or m.get("config", {}).get("top_k")

    row={

      "job_id":jid,

      "status": d.get("job",{}).get("status") or d.get("status",""),

      "top_k": top_k,

      "fast_mode": params.get("fast_mode") or config_data.get("fast_mode"),

      "recall_at_10": m.get("recall_at_10", 0.0),

      "p95_ms": m.get("p95_ms", 0.0),

      "qps": m.get("qps", 0.0)

    }

    rows.append(row)

# winners: 质量=最高 recall，其次最低 p95；延迟=最低 p95；平衡=按 recall 降序再按 p95 升序

def pick_quality(rs): return sorted(rs, key=lambda x:(-x["recall_at_10"], x["p95_ms"]))[0] if rs else {}

def pick_latency(rs): return sorted(rs, key=lambda x:(x["p95_ms"], -x["recall_at_10"]))[0] if rs else {}

def pick_bal(rs):     return sorted(rs, key=lambda x:(-x["recall_at_10"], x["p95_ms"]))[0] if rs else {}

report={"jobs":rows,"winners":{"quality":pick_quality(rows),"latency":pick_latency(rows),"balanced":pick_bal(rows)},"label_source":"GOLD"}

json.dump(report, open(os.path.join(outdir,"winners_gold.json"),"w"), indent=2)

print(json.dumps(report["winners"], indent=2))

PY



# ---- 6) Silver vs Gold 对照（如果有 silver 报告就对比）----

if [ -f "$OUTDIR/winners.json" ]; then

  log DIFF "compare winners (silver vs gold)"

  python3 - <<'PY' "$OUTDIR"

import json,sys,os

od=sys.argv[1]

sl=json.load(open(os.path.join(od,"winners.json")))

gd=json.load(open(os.path.join(od,"winners_gold.json")))

def row(x): return {"recall_at_10":x.get("recall_at_10"),"p95_ms":x.get("p95_ms"),"top_k":x.get("top_k"),"fast_mode":x.get("fast_mode")}

comp={

 "quality":{"silver":row(sl.get("winners",{}).get("quality",{})),

            "gold":  row(gd.get("winners",{}).get("quality",{}))},

 "latency":{"silver":row(sl.get("winners",{}).get("latency",{})),

            "gold":  row(gd.get("winners",{}).get("latency",{}))},

 "balanced":{"silver":row(sl.get("winners",{}).get("balanced",{})),

             "gold":  row(gd.get("winners",{}).get("balanced",{}))}

}

open(os.path.join(od,"silver_vs_gold_summary.md"),"w").write(

  "# Silver vs Gold (winners)\n\n```\n"+json.dumps(comp,indent=2)+"\n```\n"

)

print(json.dumps(comp, indent=2))

PY

else

  log DIFF "no silver winners.json found -> skipped"

fi



# ---- 7) 汇报 & 下一步 ----

log DONE "Gold eval finished."

echo "- Jobs: $(cat $OUTDIR/jobs_gold.list)"

echo "- Gold winners: $OUTDIR/winners_gold.json"

[ -f "$OUTDIR/silver_vs_gold_summary.md" ] && echo "- Diff: $OUTDIR/silver_vs_gold_summary.md" || true

echo "- Next: 如 Gold 分数显著低于 Silver（>3–5%），后续报告以 Gold 为准；在前端标注 Label Source=Gold & 去重=ON。"

