#!/bin/bash
#
# 一键核验脚本: verify_effective_params.sh
# 功能: 对比"计划值 vs 展示值 vs 生效值"，并标注哪一层改写了参数
#
# 使用方法:
#   cd /Users/nanxinli/Documents/dev/searchforge
#   bash scripts/verify_effective_params.sh
#
# 依赖: jq, curl
#

set -euo pipefail

# 配置
API_BASE="${APP_DEMO_URL:-http://localhost:8001}"
ENV_FILE="${ENV_FILE:-.env}"

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 辅助函数
function info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

function warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

function error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

function check_dependencies() {
    info "检查依赖..."
    
    if ! command -v jq &> /dev/null; then
        error "未找到 jq，请安装: brew install jq"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        error "未找到 curl"
        exit 1
    fi
    
    info "依赖检查通过 ✅"
}

function load_env_values() {
    info "读取 .env 文件中的计划值..."
    
    # 检查 .env 文件是否存在
    if [[ ! -f "$ENV_FILE" ]]; then
        warn ".env 文件不存在，使用默认值"
        ENV_HEAVY_NUM_CANDIDATES=1500
        ENV_HEAVY_RERANK_TOPK=300
        ENV_PLAY_B_QPS=120
        ENV_PLAY_B_DURATION=180
        ENV_BS_QDRANT_OVERRIDE=0
        ENV_BS_QDRANT_MAX_CONCURRENCY=32
        ENV_BS_QDRANT_BATCH_SIZE=1
    else
        # 读取 .env 文件
        source <(grep -E '^(HEAVY_NUM_CANDIDATES|HEAVY_RERANK_TOPK|PLAY_B_QPS|PLAY_B_DURATION_SEC|PLAY_B_NUM_CANDIDATES|PLAY_B_RERANK_TOPK|BS_QDRANT_OVERRIDE|BS_QDRANT_MAX_CONCURRENCY|BS_QDRANT_BATCH_SIZE)=' "$ENV_FILE" 2>/dev/null || true)
        
        ENV_HEAVY_NUM_CANDIDATES="${HEAVY_NUM_CANDIDATES:-${PLAY_B_NUM_CANDIDATES:-1500}}"
        ENV_HEAVY_RERANK_TOPK="${HEAVY_RERANK_TOPK:-${PLAY_B_RERANK_TOPK:-300}}"
        ENV_PLAY_B_QPS="${PLAY_B_QPS:-120}"
        ENV_PLAY_B_DURATION="${PLAY_B_DURATION_SEC:-180}"
        ENV_BS_QDRANT_OVERRIDE="${BS_QDRANT_OVERRIDE:-0}"
        ENV_BS_QDRANT_MAX_CONCURRENCY="${BS_QDRANT_MAX_CONCURRENCY:-32}"
        ENV_BS_QDRANT_BATCH_SIZE="${BS_QDRANT_BATCH_SIZE:-1}"
    fi
    
    info "ENV 计划值:"
    info "  - HEAVY_NUM_CANDIDATES: $ENV_HEAVY_NUM_CANDIDATES"
    info "  - HEAVY_RERANK_TOPK:    $ENV_HEAVY_RERANK_TOPK"
    info "  - PLAY_B_QPS:           $ENV_PLAY_B_QPS"
    info "  - PLAY_B_DURATION:      $ENV_PLAY_B_DURATION"
    info "  - BS_QDRANT_OVERRIDE:   $ENV_BS_QDRANT_OVERRIDE"
}

function fetch_api_values() {
    info "调用 API 获取实时生效值..."
    
    # 1. GET /ops/black_swan/status → playbook_params (计划值)
    BS_STATUS_JSON=$(curl -s "$API_BASE/ops/black_swan/status" || echo '{}')
    BS_MODE=$(echo "$BS_STATUS_JSON" | jq -r '.mode // "N/A"')
    BS_NUM_CANDIDATES=$(echo "$BS_STATUS_JSON" | jq -r '.playbook_params.num_candidates // "N/A"')
    BS_RERANK_TOPK=$(echo "$BS_STATUS_JSON" | jq -r '.playbook_params.rerank_topk // "N/A"')
    BS_QPS=$(echo "$BS_STATUS_JSON" | jq -r '.playbook_params.burst_qps // "N/A"')
    
    # 2. GET /ops/qdrant/config → override, concurrency, batch_size
    QDRANT_CONFIG_JSON=$(curl -s "$API_BASE/ops/qdrant/config" || echo '{}')
    QDRANT_OVERRIDE=$(echo "$QDRANT_CONFIG_JSON" | jq -r '.override // false')
    QDRANT_CONCURRENCY=$(echo "$QDRANT_CONFIG_JSON" | jq -r '.concurrency // "N/A"')
    QDRANT_BATCH_SIZE=$(echo "$QDRANT_CONFIG_JSON" | jq -r '.batch_size // "N/A"')
    QDRANT_SOURCE=$(echo "$QDRANT_CONFIG_JSON" | jq -r '.source // "N/A"')
    
    # 3. GET /ops/qdrant/stats → hits_60s, avg_query_ms (验证链路)
    QDRANT_STATS_JSON=$(curl -s "$API_BASE/ops/qdrant/stats" || echo '{}')
    QDRANT_HITS_60S=$(echo "$QDRANT_STATS_JSON" | jq -r '.hits_60s // 0')
    QDRANT_AVG_MS=$(echo "$QDRANT_STATS_JSON" | jq -r '.avg_query_ms_60s // "N/A"')
    
    # 4. GET /ops/summary → window60s (验证运行状态)
    OPS_SUMMARY_JSON=$(curl -s "$API_BASE/ops/summary" || echo '{}')
    SUMMARY_TPS=$(echo "$OPS_SUMMARY_JSON" | jq -r '.window60s.tps // 0')
    
    info "API 返回值:"
    info "  - Black Swan Mode:        $BS_MODE"
    info "  - Black Swan Candidates:  $BS_NUM_CANDIDATES"
    info "  - Black Swan Rerank:      $BS_RERANK_TOPK"
    info "  - Black Swan QPS:         $BS_QPS"
    info "  - Qdrant Override:        $QDRANT_OVERRIDE"
    info "  - Qdrant Concurrency:     $QDRANT_CONCURRENCY"
    info "  - Qdrant Batch Size:      $QDRANT_BATCH_SIZE"
    info "  - Qdrant Source:          $QDRANT_SOURCE"
}

function fetch_qa_feed_values() {
    info "调用 QA Feed 获取最近一条实际执行参数..."
    
    # GET /ops/qa/feed?limit=1 → 最近一条
    QA_FEED_JSON=$(curl -s "$API_BASE/ops/qa/feed?limit=1" || echo '{}')
    QA_OK=$(echo "$QA_FEED_JSON" | jq -r '.ok // false')
    
    if [[ "$QA_OK" == "true" ]]; then
        QA_TOPK=$(echo "$QA_FEED_JSON" | jq -r '.items[0].topk // "N/A"')
        QA_RERANK_K=$(echo "$QA_FEED_JSON" | jq -r '.items[0].rerank_k // "N/A"')
        QA_MODE=$(echo "$QA_FEED_JSON" | jq -r '.items[0].mode // "N/A"')
        QA_LATENCY=$(echo "$QA_FEED_JSON" | jq -r '.items[0].latency_ms // "N/A"')
        
        info "QA Feed 最近一条:"
        info "  - Mode:      $QA_MODE"
        info "  - TopK:      $QA_TOPK"
        info "  - Rerank_K:  $QA_RERANK_K"
        info "  - Latency:   ${QA_LATENCY}ms"
    else
        warn "QA Feed 未启用或无数据"
        QA_TOPK="N/A"
        QA_RERANK_K="N/A"
    fi
}

function compare_values() {
    echo ""
    info "============================================"
    info "          参数对照表 (计划 vs 生效)           "
    info "============================================"
    echo ""
    
    # 表头
    printf "%-30s %-15s %-15s %-20s %-10s\n" "参数名" "计划值(.env)" "生效值(API)" "覆盖源" "状态"
    printf "%-30s %-15s %-15s %-20s %-10s\n" "------------------------------" "---------------" "---------------" "--------------------" "----------"
    
    # num_candidates
    if [[ "$ENV_HEAVY_NUM_CANDIDATES" == "$BS_NUM_CANDIDATES" ]]; then
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "num_candidates" "$ENV_HEAVY_NUM_CANDIDATES" "$BS_NUM_CANDIDATES" "ENV (透传)" "${GREEN}" "✅ 一致" "${NC}"
    else
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "num_candidates" "$ENV_HEAVY_NUM_CANDIDATES" "$BS_NUM_CANDIDATES" "被改写!" "${RED}" "❌ 不一致" "${NC}"
    fi
    
    # rerank_topk
    if [[ "$ENV_HEAVY_RERANK_TOPK" == "$BS_RERANK_TOPK" ]]; then
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "rerank_topk" "$ENV_HEAVY_RERANK_TOPK" "$BS_RERANK_TOPK" "ENV (透传)" "${GREEN}" "✅ 一致" "${NC}"
    else
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "rerank_topk" "$ENV_HEAVY_RERANK_TOPK" "$BS_RERANK_TOPK" "被改写!" "${RED}" "❌ 不一致" "${NC}"
    fi
    
    # qps
    if [[ "$ENV_PLAY_B_QPS" == "$BS_QPS" ]]; then
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "qps" "$ENV_PLAY_B_QPS" "$BS_QPS" "ENV (透传)" "${GREEN}" "✅ 一致" "${NC}"
    else
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "qps" "$ENV_PLAY_B_QPS" "$BS_QPS" "被改写!" "${RED}" "❌ 不一致" "${NC}"
    fi
    
    # Qdrant override
    if [[ "$ENV_BS_QDRANT_OVERRIDE" == "1" ]] && [[ "$QDRANT_OVERRIDE" == "true" ]]; then
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "qdrant_override" "$ENV_BS_QDRANT_OVERRIDE" "true" "ENV (透传)" "${GREEN}" "✅ 一致" "${NC}"
    elif [[ "$ENV_BS_QDRANT_OVERRIDE" == "0" ]] && [[ "$QDRANT_OVERRIDE" == "false" ]]; then
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "qdrant_override" "$ENV_BS_QDRANT_OVERRIDE" "false" "ENV (透传)" "${GREEN}" "✅ 一致" "${NC}"
    else
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "qdrant_override" "$ENV_BS_QDRANT_OVERRIDE" "$QDRANT_OVERRIDE" "被改写!" "${RED}" "❌ 不一致" "${NC}"
    fi
    
    # Qdrant concurrency
    if [[ "$ENV_BS_QDRANT_MAX_CONCURRENCY" == "$QDRANT_CONCURRENCY" ]]; then
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "qdrant_concurrency" "$ENV_BS_QDRANT_MAX_CONCURRENCY" "$QDRANT_CONCURRENCY" "ENV (透传)" "${GREEN}" "✅ 一致" "${NC}"
    else
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "qdrant_concurrency" "$ENV_BS_QDRANT_MAX_CONCURRENCY" "$QDRANT_CONCURRENCY" "被改写!" "${RED}" "❌ 不一致" "${NC}"
    fi
    
    # Qdrant batch_size
    if [[ "$ENV_BS_QDRANT_BATCH_SIZE" == "$QDRANT_BATCH_SIZE" ]]; then
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "qdrant_batch_size" "$ENV_BS_QDRANT_BATCH_SIZE" "$QDRANT_BATCH_SIZE" "ENV (透传)" "${GREEN}" "✅ 一致" "${NC}"
    else
        printf "%-30s %-15s %-15s %-20s %b%-10s%b\n" "qdrant_batch_size" "$ENV_BS_QDRANT_BATCH_SIZE" "$QDRANT_BATCH_SIZE" "被改写!" "${RED}" "❌ 不一致" "${NC}"
    fi
    
    echo ""
}

function show_rewrite_details() {
    info "============================================"
    info "         参数改写详情与文件位置              "
    info "============================================"
    echo ""
    
    # num_candidates 上限检查
    if [[ "$BS_NUM_CANDIDATES" != "N/A" ]] && [[ $BS_NUM_CANDIDATES -gt 2000 ]]; then
        warn "num_candidates=$BS_NUM_CANDIDATES 超过 macros.py 上限 2000！"
        warn "  → 被截断位置: modules/autotune/macros.py:67"
        warn "  → 被截断位置: modules/autotuner/brain/constraints.py:26"
        warn "  → 修复建议: 提高上限到 5000"
    else
        info "num_candidates=$BS_NUM_CANDIDATES 未超过上限 (2000) ✅"
    fi
    
    # rerank_topk vs num_candidates
    if [[ "$BS_RERANK_TOPK" != "N/A" ]] && [[ "$BS_NUM_CANDIDATES" != "N/A" ]]; then
        if [[ $BS_RERANK_TOPK -gt $BS_NUM_CANDIDATES ]]; then
            warn "rerank_topk=$BS_RERANK_TOPK > num_candidates=$BS_NUM_CANDIDATES！"
            warn "  → 会被截断位置: modules/search/search_pipeline.py:789"
            warn "  → 实际生效: min($BS_RERANK_TOPK, $BS_NUM_CANDIDATES) = $BS_NUM_CANDIDATES"
        else
            info "rerank_topk=$BS_RERANK_TOPK <= num_candidates=$BS_NUM_CANDIDATES ✅"
        fi
    fi
    
    # Qdrant override
    if [[ "$QDRANT_SOURCE" == "override" ]]; then
        info "Qdrant 使用覆盖值 (BS_QDRANT_OVERRIDE=1) ✅"
    else
        info "Qdrant 使用默认值 (BS_QDRANT_OVERRIDE=0)"
    fi
    
    echo ""
}

function show_recommendations() {
    info "============================================"
    info "              修复建议汇总                   "
    info "============================================"
    echo ""
    
    echo "【P0 - 立即修复】"
    echo "  1. 提高 Ncand_max 上限:"
    echo "     - modules/autotune/macros.py:67"
    echo "       Ncand_max = max(100, min(5000, Ncand_max))  # 2000 → 5000"
    echo "     - modules/autotuner/brain/constraints.py:26"
    echo "       'Ncand_max': (500, 5000)  # 2000 → 5000"
    echo ""
    echo "  2. 增加 candidate_k 校验:"
    echo "     - modules/search/search_pipeline.py:646 前增加:"
    echo "       MAX_CANDIDATE_K = int(os.getenv('MAX_CANDIDATE_K', '5000'))"
    echo "       if override_k > MAX_CANDIDATE_K:"
    echo "           logger.warning(f'candidate_k={override_k} exceeds limit, clamping')"
    echo "           override_k = MAX_CANDIDATE_K"
    echo ""
    echo "【P1 - 短期改进】"
    echo "  3. 前端参数透传:"
    echo "     - frontend/src/lib/api.ts 增加 params 字段"
    echo "     - services/fiqa_api/app_v2.py 支持参数覆盖"
    echo ""
    echo "  4. 统一 ENV 变量命名:"
    echo "     - HEAVY_NUM_CANDIDATES → BLACK_SWAN_MODE_B_NUM_CANDIDATES"
    echo "     - HEAVY_RERANK_TOPK   → BLACK_SWAN_MODE_B_RERANK_TOPK"
    echo ""
    echo "【P2 - 长期优化】"
    echo "  5. 参数优先级框架: 请求参数 > BS覆盖 > ENV > 默认值"
    echo "  6. 前端参数UI: 允许用户自定义Mode B参数"
    echo "  7. 监控告警: 参数被改写时记录日志"
    echo ""
}

# 主流程
function main() {
    echo ""
    info "=========================================="
    info "  SearchForge 参数核验工具 v1.0            "
    info "=========================================="
    echo ""
    
    check_dependencies
    load_env_values
    fetch_api_values
    fetch_qa_feed_values
    compare_values
    show_rewrite_details
    show_recommendations
    
    echo ""
    info "核验完成！详细报告请查看: reports/guardrails_audit.md"
    echo ""
}

main "$@"

