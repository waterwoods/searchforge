#!/usr/bin/env bash
set -euo pipefail

# Protected volumes (exact names - do NOT delete these)
PROTECTED=(
  "searchforge_redis_data"
  "searchforge_qdrant_data"
  "buildx_buildkit_ssx-tmp0_state"
)

echo "════════════════════════════════════════════════════════════════"
echo "  Docker Safe Volume Pruner"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Capture before state
echo "== BEFORE =="
docker system df
echo ""

# Show protected volumes
echo "🛡️  Protected volumes (will NOT be deleted):"
for vol in "${PROTECTED[@]}"; do
  if docker volume inspect "$vol" &>/dev/null; then
    echo "  ✓ $vol"
  else
    echo "  - $vol (not found)"
  fi
done
echo ""

# Get all dangling/unused volumes
echo "🔍 Detecting dangling/unused volumes..."
DANGLING_VOLUMES=$(docker volume ls -qf dangling=true || true)

if [[ -z "$DANGLING_VOLUMES" ]]; then
  echo "✅ Nothing to prune. All volumes are in use."
  exit 0
fi

# Build candidate list (dangling volumes NOT in protected list)
CANDIDATES=()
while IFS= read -r vol; do
  # Skip if volume is in protected list
  if [[ " ${PROTECTED[*]} " =~ " ${vol} " ]]; then
    continue
  fi
  CANDIDATES+=("$vol")
done <<< "$DANGLING_VOLUMES"

# Check if we have candidates
if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
  echo "✅ Nothing to prune. All dangling volumes are protected."
  exit 0
fi

# Get detailed volume information with sizes
echo ""
echo "📦 Candidate volumes for deletion:"
echo ""

TOTAL_SIZE=0
VOLUME_INFO_FILE=$(mktemp)

# Get volume information from docker system df -v
docker system df -v | grep -A 1000 "^VOLUME" > "$VOLUME_INFO_FILE" || true

# Display candidates with sizes and calculate total
for vol in "${CANDIDATES[@]}"; do
  # Find size for this volume
  size=$(grep "^$vol " "$VOLUME_INFO_FILE" | awk '{print $4}' || echo "0B")
  echo "  • $vol [$size]"
  
  # Convert size to GB for summing (approximate)
  if [[ "$size" =~ ([0-9.]+)GB ]]; then
    size_gb="${BASH_REMATCH[1]}"
    TOTAL_SIZE=$(echo "$TOTAL_SIZE + $size_gb" | bc -l 2>/dev/null || echo "$TOTAL_SIZE")
  elif [[ "$size" =~ ([0-9.]+)MB ]]; then
    size_mb="${BASH_REMATCH[1]}"
    size_gb=$(echo "$size_mb / 1024" | bc -l 2>/dev/null || echo "0")
    TOTAL_SIZE=$(echo "$TOTAL_SIZE + $size_gb" | bc -l 2>/dev/null || echo "$TOTAL_SIZE")
  fi
done

rm -f "$VOLUME_INFO_FILE"

echo ""
printf "📊 TOTAL RECLAIMABLE: %.2f GB\n" "$TOTAL_SIZE"
echo ""

# Ask for confirmation
echo "════════════════════════════════════════════════════════════════"
echo "⚠️  WARNING: This will permanently delete ${#CANDIDATES[@]} volume(s)."
echo "════════════════════════════════════════════════════════════════"
echo ""
read -p "Type YES (all caps) to proceed: " confirmation

if [[ "$confirmation" != "YES" ]]; then
  echo ""
  echo "❌ Cancelled. No volumes were deleted."
  exit 0
fi

echo ""
echo "🗑️  Deleting candidate volumes..."

# Delete candidates
for vol in "${CANDIDATES[@]}"; do
  echo "  Removing: $vol"
  docker volume rm "$vol" || echo "  ⚠️  Failed to remove $vol (may be in use)"
done

echo ""
echo "== AFTER =="
docker system df

echo ""
echo "✅ Volume pruning complete!"
echo ""
echo "Reclaimed space summary:"
docker system df | awk '
  NR==1 {print; next}
  /Local Volumes/ {print}
'

exit 0

