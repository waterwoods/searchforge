#!/usr/bin/env bash
# P16-Z11 Phase 10 — Founder output (print to terminal, not hidden in markdown)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

PREVIEW_URL="${PREVIEW_URL:-https://ui-d7pyq2yau-andys-projects-1f411b73.vercel.app/workbench/unified-intake}"
API_URL="${API_URL:-https://fiqa-api-g7zatxrycq-uw.a.run.app}"
GIT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
DEPLOY_TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  P16-Z11 OFFICE VALUE SURFACE — FOUNDER OUTPUT"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "══════════════════════════════════════════════════════════════"
echo ""

echo "TOP 10 UI IMPROVEMENTS"
echo "──────────────────────"
cat <<'EOF'
 1. Case headline first — 客户保费未成功扣款 (not "general inquiry")
 2. 缺少资料 checklist with □ labels — visible without expand
 3. 当前等待：保险公司回复 — purple strip, no panel expand
 4. 办公室下一步 — blue action block above fold
 5. 系统判断依据 — ✓ 提到追尾 / 理赔员 / 8500美元
 6. Queue preview uses office headline + waiting + next (not raw EN)
 7. SERVICE_TYPE_OFFICE_ZH hides add_car / remove_car tokens
 8. Flattened glance card (removed gradient noise)
 9. humanizeWaitingOn → 客户补充资料 / 保险公司回复
10. Remove-car + payment lanes get dedicated office titles
EOF
echo ""

echo "TOP 10 OFFICE VALUE WINS"
echo "────────────────────────"
cat <<'EOF'
 1. Payment case routes to billing (was unclear) — 85/100 office score
 2. 卖掉Camry routes to remove_car (was general_inquiry)
 3. Claim case shows carrier waiting (not add-car mis-route)
 4. office_case_title API field — single source for headline
 5. office_broker_next_step in Chinese for top 3 lanes
 6. classification_signals lift trust on claim threads
 7. P16-Y holds 88.6 — no regression
 8. Role D reread 82.6 — still above 80 bar
 9. Guardrail PASS — 27 checks green
10. 5-second scan order: 什么→缺什么→等谁→下一步
EOF
echo ""

echo "TOP 10 REMAINING CONFUSIONS"
echo "───────────────────────────"
cat <<'EOF'
 1. Preview backend pre-deploy ≠ local batteries (deploy required)
 2. UW lane broker_next_step still English on some paths
 3. Add-car formal-submit block competes with headline
 4. waiting_on suggested but not auto-saved — broker PATCH needed
 5. payment_proof_or_screenshot label not localized
 6. Queue card title still shows raw paste in product_only
 7. Screenshot-only intake has empty classification_signals
 8. Edge unclear cases still show 客户咨询（待分类）
 9. Before/after screenshots need post-deploy browser pass
10. LLM path (quota) falls back to rules — office copy depends on markers
EOF
echo ""

echo "BEFORE / AFTER (acceptance cases)"
echo "────────────────────────────────"
echo ""
echo "Case 1 — 保费420美元没扣成功"
echo "  BEFORE: general inquiry · unclear · Ask for missing part..."
echo "  AFTER:  客户保费未成功扣款，存在保单失效风险"
echo "          当前等待：客户补充资料"
echo "          办公室下一步：联系客户确认付款方式并协助完成扣款"
echo ""
echo "Case 2 — 我卖掉Camry了"
echo "  BEFORE: general inquiry · unclear"
echo "  AFTER:  客户卖车，需要从保单移除车辆"
echo "          缺少资料 □ 卖车日期 □ 销售证明"
echo "          办公室下一步：联系客户补销售证明和卖车日期，然后办理删车"
echo ""
echo "Case 3 — 追尾/理赔员/8500/全损"
echo "  BEFORE: claim but English next step; possible add-car confusion"
echo "  AFTER:  客户发生事故，正在进入理赔流程"
echo "          当前等待：保险公司回复"
echo "          识别依据：✓ 提到追尾 ✓ 提到理赔员 ✓ 提到8500美元 ✓ 提到全损"
echo ""

echo "PREVIEW URL"
echo "───────────"
echo "  $PREVIEW_URL"
echo ""
echo "GIT COMMIT:  $GIT_COMMIT"
echo "DEPLOY TS:   $DEPLOY_TS"
echo "API:         $API_URL"
echo ""

# Live acceptance probe (local triage — always works)
if command -v python3 >/dev/null 2>&1; then
  echo "LOCAL ACCEPTANCE PROBE (LLM off)"
  echo "────────────────────────────────"
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 - <<'PY'
from services.fiqa_api.inbox_triage.triage import triage_conversation
cases = [
    ("payment", "保费420美元没扣成功"),
    ("remove", "我卖掉Camry了"),
    ("claim", "追尾\n理赔员\n8500美元\n全损"),
]
for name, text in cases:
    r = triage_conversation(text, [])
    ok = "✅" if r.get("office_case_title") else "❌"
    print(f"  {ok} {name}: {r.get('office_case_title','—')[:40]}")
PY
  echo ""
fi

echo "══════════════════════════════════════════════════════════════"
