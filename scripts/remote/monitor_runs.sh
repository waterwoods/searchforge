#!/bin/bash
# Quick monitoring script for remote experiments
REMOTE_USER_HOST="${REMOTE_USER_HOST:-andy@100.67.88.114}"

echo "=== Active tmux sessions ==="
ssh "${REMOTE_USER_HOST}" "tmux ls 2>/dev/null || echo 'No sessions found'"
echo ""

echo "=== Completion status ==="
for exp in B_single B_multi C_single C_multi; do
    status=$(ssh "${REMOTE_USER_HOST}" "[ -f /tmp/autotuner_${exp}.status ] && cat /tmp/autotuner_${exp}.status || echo 'Not done'")
    echo "${exp}: ${status}"
done
echo ""

echo "=== Recent logs (last 5 lines each) ==="
for exp in B_single B_multi C_single C_multi; do
    echo "--- ${exp} ---"
    ssh "${REMOTE_USER_HOST}" "find ~/runs -name '*${exp}' -type d -exec sh -c 'ls -t {}/logs/*.log 2>/dev/null | head -1 | xargs tail -5 2>/dev/null' \; 2>/dev/null | head -5 || echo 'No logs yet'"
    echo ""
done
