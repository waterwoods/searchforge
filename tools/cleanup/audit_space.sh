#!/bin/bash
set -Eeuo pipefail

# Disk usage audit script for WSL2 Linux host with Docker + GPU libs
# This script is read-only and does NOT delete anything

# Function to format size and mark hotspots (≥5GB)
format_size() {
    local size_line="$1"
    local size_str=$(echo "$size_line" | awk '{print $1}')
    local path=$(echo "$size_line" | awk '{for(i=2;i<=NF;i++) printf "%s ", $i; print ""}' | sed 's/[[:space:]]*$//')
    
    # Convert size to bytes for comparison (handles K, M, G, T suffixes)
    local size_bytes=0
    if echo "$size_str" | grep -qiE '[0-9]+G'; then
        size_bytes=$(echo "$size_str" | sed 's/G//i' | awk '{printf "%.0f", $1 * 1024 * 1024 * 1024}')
    elif echo "$size_str" | grep -qiE '[0-9]+M'; then
        size_bytes=$(echo "$size_str" | sed 's/M//i' | awk '{printf "%.0f", $1 * 1024 * 1024}')
    elif echo "$size_str" | grep -qiE '[0-9]+K'; then
        size_bytes=$(echo "$size_str" | sed 's/K//i' | awk '{printf "%.0f", $1 * 1024}')
    elif echo "$size_str" | grep -qiE '[0-9]+T'; then
        size_bytes=$(echo "$size_str" | sed 's/T//i' | awk '{printf "%.0f", $1 * 1024 * 1024 * 1024 * 1024}')
    else
        # Assume bytes if no suffix
        size_bytes=$(echo "$size_str" | awk '{printf "%.0f", $1}')
    fi
    
    local hotspot_threshold=$((5 * 1024 * 1024 * 1024))  # 5GB in bytes
    
    if [ "$size_bytes" -ge "$hotspot_threshold" ]; then
        echo "**HOTSPOT** $size_line"
    else
        echo "$size_line"
    fi
}

echo "# Disk Usage Audit Report"
echo ""
echo "Generated: $(date -Iseconds)"
echo ""
echo "---"
echo ""

# ========================================
# Host Basics
# ========================================
echo "## Host Basics"
echo ""
echo "### Filesystem Usage"
df -hT / /var /home || true
echo ""

echo "### Top 50 Large Paths (≥1GB threshold)"
echo ""
if sudo du -xh / --threshold=1G --max-depth=2 2>/dev/null | sort -h | tail -n 50 | while IFS= read -r line; do
    format_size "$line"
done; then
    :
else
    echo "(No paths ≥1GB found or permission denied)"
fi
echo ""

# ========================================
# CUDA / GPU
# ========================================
echo "## CUDA / GPU"
echo ""
echo "### CUDA Installations"
ls -ldh /usr/local/cuda* 2>/dev/null || echo "(No CUDA installations found)"
echo ""

echo "### CUDA Directory Sizes"
if sudo du -xh /usr/local/cuda* --max-depth=1 2>/dev/null | sort -h | while IFS= read -r line; do
    format_size "$line"
done; then
    :
else
    echo "(No CUDA directories found or permission denied)"
fi
echo ""

echo "### NVIDIA GPUs"
nvidia-smi -L 2>/dev/null || echo "(nvidia-smi not available)"
echo ""

# ========================================
# Model & Cache Dirs
# ========================================
echo "## Model & Cache Directories"
echo ""

echo "### HuggingFace, PyTorch, and pip Caches"
if du -xh ~/.cache/{huggingface,torch,pip} --max-depth=2 2>/dev/null | sort -h | while IFS= read -r line; do
    format_size "$line"
done; then
    :
else
    echo "(Cache directories not found or empty)"
fi
echo ""

echo "### /models Directory"
if du -xh /models --max-depth=2 2>/dev/null | sort -h | while IFS= read -r line; do
    format_size "$line"
done; then
    :
else
    echo "(/models directory not found)"
fi
echo ""

echo "### Miniconda Package Cache"
if du -xh ~/miniconda3/pkgs --max-depth=1 2>/dev/null | sort -h | while IFS= read -r line; do
    format_size "$line"
done; then
    :
else
    echo "(Miniconda pkgs directory not found)"
fi
echo ""

# ========================================
# Docker
# ========================================
echo "## Docker"
echo ""
echo "### Docker System Disk Usage"
docker system df -v 2>/dev/null || echo "(Docker not available or permission denied)"
echo ""

echo "### Docker Root Directory (Top 50)"
if sudo du -xh /var/lib/docker --max-depth=2 2>/dev/null | sort -h | tail -n 50 | while IFS= read -r line; do
    format_size "$line"
done; then
    :
else
    echo "(Permission denied or Docker not installed)"
fi
echo ""

echo "### Docker Volumes (Top 50)"
if sudo du -xh /var/lib/docker/volumes --max-depth=2 2>/dev/null | sort -h | tail -n 50 | while IFS= read -r line; do
    format_size "$line"
done; then
    :
else
    echo "(Permission denied or no volumes found)"
fi
echo ""

# ========================================
# Package Caches & Logs
# ========================================
echo "## Package Caches & Logs"
echo ""

echo "### APT Cache"
if sudo du -xh /var/cache/apt --max-depth=1 2>/dev/null | sort -h | while IFS= read -r line; do
    format_size "$line"
done; then
    :
else
    echo "(Permission denied or APT cache not found)"
fi
echo ""

echo "### Systemd Journal Disk Usage"
sudo journalctl --disk-usage 2>/dev/null || echo "(journalctl not available or permission denied)"
echo ""

echo "### Trash Directory"
if du -xh ~/.local/share/Trash --max-depth=1 2>/dev/null | sort -h | while IFS= read -r line; do
    format_size "$line"
done; then
    :
else
    echo "(Trash directory not found or empty)"
fi
echo ""

# ========================================
# Project-Local
# ========================================
echo "## Project-Local (searchforge)"
echo ""
echo "### Top 50 Large Paths in ~/searchforge"
if du -xh ~/searchforge --max-depth=2 2>/dev/null | sort -h | tail -n 50 | while IFS= read -r line; do
    format_size "$line"
done; then
    :
else
    echo "(Permission denied or directory not found)"
fi
echo ""

echo "---"
echo ""
echo "## Summary"
echo ""
echo "**HOTSPOT** indicates paths ≥5GB that may require attention."
echo ""
echo "Audit completed: $(date -Iseconds)"


