#!/bin/bash
# Space Cleanup Script - Cleans various caches and temporary files
# Supports --dry-run mode (default) and --run for actual cleanup

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DRY_RUN=true
LOG_FILE=""
TOTAL_FREED=0

# Find project root
find_project_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -f "$dir/pyproject.toml" ] || [ -f "$dir/Makefile" ]; then
            echo "$dir"
            return
        fi
        dir=$(dirname "$dir")
    done
    echo "$(pwd)"
}

PROJECT_ROOT=$(find_project_root "$(pwd)")

# Parse arguments
if [ "${1:-}" = "--run" ]; then
    DRY_RUN=false
    echo -e "${YELLOW}⚠️  REAL CLEANUP MODE - Files will be deleted!${NC}"
else
    echo -e "${BLUE}ℹ️  DRY-RUN MODE - No files will be deleted${NC}"
fi

# Setup logging
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/space_cleanup_$(date +%F_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=========================================="
echo "Space Cleanup Script"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"
echo "Mode: $([ "$DRY_RUN" = true ] && echo "DRY-RUN" || echo "REAL CLEANUP")"
echo "Log File: $LOG_FILE"
echo "Timestamp: $(date)"
echo "=========================================="
echo ""

# Helper functions
get_size() {
    local path="$1"
    if [ ! -e "$path" ]; then
        echo 0
        return
    fi
    du -sb "$path" 2>/dev/null | awk '{print $1}' || echo 0
}

format_size() {
    local bytes="$1"
    if [ "$bytes" -lt 1024 ]; then
        echo "${bytes}B"
    elif [ "$bytes" -lt 1048576 ]; then
        echo "$(awk "BEGIN {printf \"%.2f KB\", $bytes/1024}")"
    elif [ "$bytes" -lt 1073741824 ]; then
        echo "$(awk "BEGIN {printf \"%.2f MB\", $bytes/1048576}")"
    else
        echo "$(awk "BEGIN {printf \"%.2f GB\", $bytes/1073741824}")"
    fi
}

clean_directory() {
    local name="$1"
    local path="$2"
    local min_size_mb="${3:-10}"  # Skip if smaller than this (default 10MB)
    
    if [ ! -e "$path" ]; then
        echo -e "${YELLOW}⏭️  Skipping $name: path does not exist${NC}"
        return
    fi
    
    local size_before=$(get_size "$path")
    local size_mb=$((size_before / 1048576))
    
    if [ "$size_mb" -lt "$min_size_mb" ]; then
        echo -e "${YELLOW}⏭️  Skipping $name: size ($(format_size "$size_before")) < ${min_size_mb}MB${NC}"
        return
    fi
    
    echo -e "${BLUE}📊 $name${NC}"
    echo "   Path: $path"
    echo "   Size before: $(format_size "$size_before")"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "   ${YELLOW}[DRY-RUN] Would delete: $(format_size "$size_before")${NC}"
        TOTAL_FREED=$((TOTAL_FREED + size_before))
    else
        if rm -rf "$path" 2>/dev/null; then
            local size_after=$(get_size "$path")
            local freed=$((size_before - size_after))
            echo -e "   ${GREEN}✅ Deleted: $(format_size "$freed")${NC}"
            TOTAL_FREED=$((TOTAL_FREED + freed))
        else
            echo -e "   ${RED}❌ Failed to delete${NC}"
        fi
    fi
    echo ""
}

# Handle HuggingFace cache (with migration option)
clean_huggingface_cache() {
    local hf_cache="$HOME/.cache/huggingface/hub"
    
    if [ ! -e "$hf_cache" ]; then
        echo -e "${YELLOW}⏭️  Skipping HuggingFace cache: path does not exist${NC}"
        return
    fi
    
    local size_before=$(get_size "$hf_cache")
    local size_mb=$((size_before / 1048576))
    
    if [ "$size_mb" -lt 10 ]; then
        echo -e "${YELLOW}⏭️  Skipping HuggingFace cache: size < 10MB${NC}"
        return
    fi
    
    echo -e "${BLUE}📊 HuggingFace Cache${NC}"
    echo "   Path: $hf_cache"
    echo "   Size: $(format_size "$size_before")"
    
    # Check for HF_HOME environment variable
    if [ -n "${HF_HOME:-}" ]; then
        local target_dir="$HF_HOME/hub"
        echo "   HF_HOME detected: $HF_HOME"
        
        if [ "$DRY_RUN" = true ]; then
            echo -e "   ${YELLOW}[DRY-RUN] Would migrate to: $target_dir${NC}"
            echo -e "   ${YELLOW}[DRY-RUN] Would free: $(format_size "$size_before")${NC}"
            TOTAL_FREED=$((TOTAL_FREED + size_before))
        else
            mkdir -p "$target_dir"
            echo "   Migrating cache to $target_dir..."
            if rsync -a --remove-source-files "$hf_cache/" "$target_dir/" 2>/dev/null; then
                # Remove source directory if it's now empty
                rmdir "$hf_cache" 2>/dev/null || true
                echo -e "   ${GREEN}✅ Migrated to $target_dir${NC}"
                TOTAL_FREED=$((TOTAL_FREED + size_before))
            else
                echo -e "   ${RED}❌ Migration failed, deleting instead${NC}"
                rm -rf "$hf_cache" && TOTAL_FREED=$((TOTAL_FREED + size_before)) || echo -e "   ${RED}❌ Deletion also failed${NC}"
            fi
        fi
    else
        if [ "$DRY_RUN" = true ]; then
            echo -e "   ${YELLOW}[DRY-RUN] Would delete: $(format_size "$size_before")${NC}"
            echo -e "   ${BLUE}💡 Tip: Set HF_HOME to migrate cache to external drive${NC}"
            echo -e "   ${BLUE}   Add to ~/.zshrc or ~/.bashrc: export HF_HOME=/path/to/external/drive${NC}"
            TOTAL_FREED=$((TOTAL_FREED + size_before))
        else
            if rm -rf "$hf_cache"; then
                echo -e "   ${GREEN}✅ Deleted: $(format_size "$size_before")${NC}"
                TOTAL_FREED=$((TOTAL_FREED + size_before))
            else
                echo -e "   ${RED}❌ Failed to delete${NC}"
            fi
        fi
    fi
    echo ""
}

# Clean /tmp/raglab* directories (only non-active)
clean_tmp_raglab() {
    local tmp_dirs
    tmp_dirs=$(find /tmp -maxdepth 1 -type d -name 'raglab*' 2>/dev/null || true)
    
    if [ -z "$tmp_dirs" ]; then
        echo -e "${YELLOW}⏭️  No /tmp/raglab* directories found${NC}"
        return
    fi
    
    local total_size=0
    local count=0
    
    while IFS= read -r dir; do
        [ -z "$dir" ] && continue
        
        # Check if directory is in use (has active processes or recent modifications)
        local is_active=false
        
        # Check for processes using this directory (simplified check)
        if lsof "$dir" >/dev/null 2>&1; then
            is_active=true
        fi
        
        # Check modification time (if modified in last 10 minutes, consider active)
        if [ "$(uname)" = "Darwin" ]; then
            local mtime=$(stat -f %m "$dir" 2>/dev/null || echo 0)
        else
            local mtime=$(stat -c %Y "$dir" 2>/dev/null || echo 0)
        fi
        local age=$(( $(date +%s) - mtime ))
        if [ "$age" -lt 600 ]; then
            is_active=true
        fi
        
        if [ "$is_active" = true ]; then
            echo -e "${YELLOW}⏭️  Skipping active directory: $dir${NC}"
            continue
        fi
        
        local size=$(get_size "$dir")
        total_size=$((total_size + size))
        count=$((count + 1))
        
        echo -e "${BLUE}📊 /tmp/raglab* directory${NC}"
        echo "   Path: $dir"
        echo "   Size: $(format_size "$size")"
        
        if [ "$DRY_RUN" = true ]; then
            echo -e "   ${YELLOW}[DRY-RUN] Would delete: $(format_size "$size")${NC}"
        else
            if rm -rf "$dir"; then
                echo -e "   ${GREEN}✅ Deleted: $(format_size "$size")${NC}"
            else
                echo -e "   ${RED}❌ Failed to delete${NC}"
            fi
        fi
        echo ""
    done <<< "$tmp_dirs"
    
    if [ "$count" -eq 0 ]; then
        echo -e "${YELLOW}⏭️  No inactive /tmp/raglab* directories to clean${NC}"
    else
        TOTAL_FREED=$((TOTAL_FREED + total_size))
    fi
}

# Clean __pycache__ directories
clean_pycache() {
    echo -e "${BLUE}📊 Cleaning __pycache__ directories${NC}"
    
    local total_size=0
    local count=0
    
    while IFS= read -r pycache_dir; do
        [ -z "$pycache_dir" ] && continue
        
        local size=$(get_size "$pycache_dir")
        if [ "$size" -lt 1048576 ]; then  # Skip if < 1MB
            continue
        fi
        
        total_size=$((total_size + size))
        count=$((count + 1))
        
        echo "   Found: $pycache_dir ($(format_size "$size"))"
        
        if [ "$DRY_RUN" = true ]; then
            echo -e "   ${YELLOW}[DRY-RUN] Would delete${NC}"
        else
            if rm -rf "$pycache_dir"; then
                echo -e "   ${GREEN}✅ Deleted${NC}"
            else
                echo -e "   ${RED}❌ Failed${NC}"
            fi
        fi
    done < <(find "$PROJECT_ROOT" -type d -name '__pycache__' 2>/dev/null || true)
    
    if [ "$count" -eq 0 ]; then
        echo -e "${YELLOW}   No __pycache__ directories found or all are < 1MB${NC}"
    else
        echo "   Total: $count directories, $(format_size "$total_size")"
        TOTAL_FREED=$((TOTAL_FREED + total_size))
    fi
    echo ""
}

# Main cleanup sequence
echo "Starting cleanup..."
echo ""

# Cache directories
clean_directory "Poetry Cache (Linux)" "$HOME/.cache/pypoetry" 10
clean_directory "Poetry Cache (macOS)" "$HOME/Library/Caches/pypoetry" 10
clean_directory "Pip Cache (Linux)" "$HOME/.cache/pip" 10
clean_directory "Pip Cache (macOS)" "$HOME/Library/Caches/pip" 10
clean_directory "Frontend node_modules/.cache" "$PROJECT_ROOT/frontend/node_modules/.cache" 10

# HuggingFace cache (special handling)
clean_huggingface_cache

# Temporary directories
clean_tmp_raglab

# __pycache__ directories
clean_pycache

# Summary
echo "=========================================="
echo "Cleanup Summary"
echo "=========================================="
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Mode: DRY-RUN${NC}"
    echo -e "${YELLOW}Estimated space to be freed: $(format_size "$TOTAL_FREED")${NC}"
    echo ""
    echo "To actually perform cleanup, run:"
    echo "  make clean-space RUN=1"
else
    echo -e "${GREEN}Mode: REAL CLEANUP${NC}"
    echo -e "${GREEN}Space freed: $(format_size "$TOTAL_FREED")${NC}"
fi
echo ""
echo "Log file: $LOG_FILE"
echo "=========================================="

exit 0






