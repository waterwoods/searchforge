#!/usr/bin/env bash
# macOS 磁盘审计助手 - Documents 文件夹扫描脚本
# 找出大于指定阈值的文件和文件夹，输出 Markdown + CSV 报告

set -euo pipefail

# =============================================================================
# 配置参数（默认值）
# =============================================================================
SCAN_PATH="$HOME/Documents"
FILE_MIN_MB=20
DIR_MIN_MB=100
TOP_N=200
EXCLUDE_PATTERNS=".git,.venv,node_modules,.pytest_cache,__pycache__,.mypy_cache,.ruff_cache,.ipynb_checkpoints"

# 输出文件
REPORT_MD="scan_report.md"
REPORT_CSV="scan_report.csv"

# =============================================================================
# 用法说明
# =============================================================================
usage() {
    cat <<'EOF'
用法: ./scan_documents.sh [选项]

选项:
  --path <dir>          扫描目录（默认: ~/Documents）
  --file-min <mb>       文件最小阈值，MB（默认: 20）
  --dir-min <mb>        目录最小阈值，MB（默认: 100）
  --top <n>             输出前 N 项（默认: 200）
  --exclude "<list>"    排除模式，逗号分隔（默认: .git,.venv,node_modules...）
  -h, --help            显示此帮助信息

示例:
  ./scan_documents.sh                                    # 默认扫描
  ./scan_documents.sh --path "$HOME/Documents/dev" --file-min 10
  ./scan_documents.sh --dir-min 200 --top 300
  ./scan_documents.sh --exclude ".git,.venv,node_modules,.DS_Store"

EOF
    exit 0
}

# =============================================================================
# 解析命令行参数
# =============================================================================
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --path)
                SCAN_PATH="$2"
                shift 2
                ;;
            --file-min)
                FILE_MIN_MB="$2"
                shift 2
                ;;
            --dir-min)
                DIR_MIN_MB="$2"
                shift 2
                ;;
            --top)
                TOP_N="$2"
                shift 2
                ;;
            --exclude)
                EXCLUDE_PATTERNS="$2"
                shift 2
                ;;
            -h|--help)
                usage
                ;;
            *)
                echo "❌ 未知参数: $1"
                echo "使用 --help 查看帮助"
                exit 1
                ;;
        esac
    done
}

# =============================================================================
# 构建排除条件数组
# =============================================================================
build_exclude_args() {
    IFS=',' read -ra PATTERNS <<< "$EXCLUDE_PATTERNS"
    exclude_args=()
    for pattern in "${PATTERNS[@]}"; do
        # 匹配两种情况：路径中的任意目录（*/*pattern/*）和根目录的隐式目录（*/pattern/*）
        exclude_args+=("-not" "-path" "*/*${pattern}/*")
    done
}

# =============================================================================
# 打印配置信息
# =============================================================================
print_config() {
    echo "═══════════════════════════════════════════════════════════════════"
    echo "           macOS 磁盘审计助手 - Documents 扫描"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "📁 扫描路径: $SCAN_PATH"
    echo "📄 文件阈值: > ${FILE_MIN_MB} MB"
    echo "📂 目录阈值: > ${DIR_MIN_MB} MB"
    echo "🔢 输出数量: Top $TOP_N"
    echo "🚫 排除模式: $EXCLUDE_PATTERNS"
    echo "📊 报告文件: $REPORT_MD, $REPORT_CSV"
    echo ""
}

# =============================================================================
# 扫描大文件
# =============================================================================
scan_large_files() {
    local temp_file=$(mktemp)
    
    echo "🔍 扫描大文件（>$FILE_MIN_MB MB）..." >&2
    
    # 使用 find 查找大文件，并使用 NUL 分隔符，然后用 du 计算大小
    find "$SCAN_PATH" -type f -size +${FILE_MIN_MB}M \
        "${exclude_args[@]}" \
        -print0 2>/dev/null | \
        xargs -0 du -k 2>/dev/null | \
        awk '{
            size_kb = $1
            $1 = ""
            sub(/^[ \t]+/, "", $0)
            path = $0
            size_mb = size_kb / 1024
            printf "%.1f|FILE|%s\n", size_mb, path
        }' | \
        sort -t'|' -k1 -rn | \
        head -n "$TOP_N" > "$temp_file"
    
    echo "$temp_file"
}

# =============================================================================
# 扫描大文件夹
# =============================================================================
scan_large_dirs() {
    local temp_file=$(mktemp)
    
    echo "🔍 扫描大目录（>$DIR_MIN_MB MB）..." >&2
    
    # 获取一级子目录并计算大小
    find "$SCAN_PATH" -maxdepth 1 -mindepth 1 -type d \
        -print0 2>/dev/null | \
        while IFS= read -r -d '' dir; do
            # 跳过排除的目录
            should_exclude=false
            IFS=',' read -ra PATTERNS <<< "$EXCLUDE_PATTERNS"
            for pattern in "${PATTERNS[@]}"; do
                if [[ "$dir" == *"/${pattern}" ]]; then
                    should_exclude=true
                    break
                fi
            done
            
            if [ "$should_exclude" = false ]; then
                # 计算目录大小（KB）
                dir_size_kb=$(du -sk "$dir" 2>/dev/null | cut -f1)
                # 使用 awk 计算 MB（不依赖 bc）
                dir_size_mb=$(awk "BEGIN {printf \"%.1f\", $dir_size_kb / 1024}")
                
                # 只输出大于阈值的目录（使用 awk 进行数值比较）
                if awk "BEGIN {exit !($dir_size_mb > $DIR_MIN_MB)}"; then
                    echo "$dir_size_mb|DIR|$dir"
                fi
            fi
        done | \
        sort -t'|' -k1 -rn > "$temp_file"
    
    echo "$temp_file"
}

# =============================================================================
# 格式化输出（人类可读表格）
# =============================================================================
format_terminal_output() {
    local file_temp=$1
    local dir_temp=$2
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "[大文件 > $FILE_MIN_MB MB]"
    echo "═══════════════════════════════════════════════════════════════════"
    
    if [ -s "$file_temp" ]; then
        awk -F'|' '{printf "  %8s MB  %s\n", $1, $3}' "$file_temp"
    else
        echo "  （无匹配文件）"
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "[大目录 > $DIR_MIN_MB MB]"
    echo "═══════════════════════════════════════════════════════════════════"
    
    if [ -s "$dir_temp" ]; then
        awk -F'|' '{printf "  %8s MB  %s\n", $1, $3}' "$dir_temp"
    else
        echo "  （无匹配目录）"
    fi
    
    echo ""
}

# =============================================================================
# 生成 Markdown 报告
# =============================================================================
generate_markdown_report() {
    local file_temp=$1
    local dir_temp=$2
    
    {
        echo "# Documents 磁盘审计报告"
        echo ""
        echo "**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "**扫描路径**: \`$SCAN_PATH\`"
        echo "**文件阈值**: > $FILE_MIN_MB MB"
        echo "**目录阈值**: > $DIR_MIN_MB MB"
        echo ""
        echo "---"
        echo ""
        echo "## 大文件 (> $FILE_MIN_MB MB)"
        echo ""
        echo "| Size (MB) | Path |"
        echo "|-----------|------|"
        
        if [ -s "$file_temp" ]; then
            awk -F'|' '{printf "| %.1f | `%s` |\n", $1, $3}' "$file_temp"
        else
            echo "| - | （无匹配文件） |"
        fi
        
        echo ""
        echo "---"
        echo ""
        echo "## 大目录 (> $DIR_MIN_MB MB)"
        echo ""
        echo "| Size (MB) | Path |"
        echo "|-----------|------|"
        
        if [ -s "$dir_temp" ]; then
            awk -F'|' '{printf "| %.1f | `%s` |\n", $1, $3}' "$dir_temp"
        else
            echo "| - | （无匹配目录） |"
        fi
    } > "$REPORT_MD"
    
    echo "✅ Markdown 报告已生成: $REPORT_MD"
}

# =============================================================================
# 生成 CSV 报告
# =============================================================================
generate_csv_report() {
    local file_temp=$1
    local dir_temp=$2
    
    {
        echo "Type,SizeMB,Path"
        
        if [ -s "$file_temp" ]; then
            awk -F'|' '{printf "%s,%.1f,%s\n", $2, $1, $3}' "$file_temp"
        fi
        
        if [ -s "$dir_temp" ]; then
            awk -F'|' '{printf "%s,%.1f,%s\n", $2, $1, $3}' "$dir_temp"
        fi
    } > "$REPORT_CSV"
    
    echo "✅ CSV 报告已生成: $REPORT_CSV"
}

# =============================================================================
# 生成迁移建议（如果检测到 MyCloud）
# =============================================================================
generate_migration_suggestions() {
    local file_temp=$1
    local dir_temp=$2
    
    if [ -d "/Volumes/MyCloud" ]; then
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "💡 检测到 /Volumes/MyCloud 已挂载"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        echo "建议迁移命令示例（请先 --dry-run 测试）："
        echo ""
        
        # 生成迁移建议（最多显示 5 个最大的）
        {
            if [ -s "$file_temp" ]; then
                head -n 5 "$file_temp"
            fi
            if [ -s "$dir_temp" ]; then
                head -n 5 "$dir_temp"
            fi
        } | awk -F'|' -v scan_path="$SCAN_PATH" '{
            # 计算相对路径
            gsub(scan_path, "", $3)
            sub(/^\//, "", $3)
            dst_path = "/Volumes/MyCloud/Archive/'$(date +%Y%m%d-%H%M)'/" $3
            
            printf "rsync -av --dry-run \"%s\" \"%s\"\n", $3, dst_path
        }' | head -n 10
        
        echo ""
        echo "⚠️  以上命令包含 --dry-run，实际执行前请移除此参数"
        echo ""
    fi
}

# =============================================================================
# 显示快速命令小抄
# =============================================================================
show_quick_commands() {
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📋 快速命令小抄"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "# 1. Documents 下最大 30 个子项"
    echo "du -sk ~/Documents/* 2>/dev/null | sort -n | tail -n 30 | \\"
    echo "  awk '{printf \"%8.1f MB\\t%s\\n\", \$1/1024, \$2}'"
    echo ""
    echo "# 2. Documents 下 >20MB 的文件（排除常见目录）"
    echo "find ~/Documents -type f -size +20m \\"
    echo "  -not -path '*/.git/*' -not -path '*/.venv/*' \\"
    echo "  -not -path '*/node_modules/*' \\"
    echo "  -print0 | xargs -0 ls -lhS | head -n 200"
    echo ""
}

# =============================================================================
# 主函数
# =============================================================================
main() {
    parse_args "$@"
    
    # 检查扫描路径是否存在
    if [ ! -d "$SCAN_PATH" ]; then
        echo "❌ 错误: 路径不存在: $SCAN_PATH"
        exit 1
    fi
    
    # 构建排除条件
    build_exclude_args
    
    # 打印配置
    print_config
    
    # 扫描
    file_temp=$(scan_large_files)
    dir_temp=$(scan_large_dirs)
    
    # 生成报告
    format_terminal_output "$file_temp" "$dir_temp"
    generate_markdown_report "$file_temp" "$dir_temp"
    generate_csv_report "$file_temp" "$dir_temp"
    generate_migration_suggestions "$file_temp" "$dir_temp"
    show_quick_commands
    
    # 清理临时文件
    rm -f "$file_temp" "$dir_temp"
    
    echo "═══════════════════════════════════════════════════════════════════"
    echo "✅ 扫描完成！"
    echo "═══════════════════════════════════════════════════════════════════"
}

# 运行主函数
main "$@"

