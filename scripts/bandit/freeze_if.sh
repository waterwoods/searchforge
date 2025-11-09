#!/usr/bin/env bash
set -euo pipefail

MODE=${MODE:-reward}
APPLY=${APPLY:-0}
BASE_URL=${BANDIT_HEALTH_BASE_URL:-http://localhost:8000}

SUMMARY_PATH="$(ls -t reports/BANDIT_SUMMARY_*.md 2>/dev/null | head -n 1 || true)"
if [[ -z "${SUMMARY_PATH}" ]]; then
  echo "[BANDIT_FREEZE][ERROR] 未找到 reports/BANDIT_SUMMARY_* 报告，请先运行 summarize.py"
  exit 1
fi

ROUNDS_PATH="$(ls -t reports/BANDIT_ROUNDS_*.md 2>/dev/null | head -n 1 || true)"
if [[ -z "${ROUNDS_PATH}" ]]; then
  echo "[BANDIT_FREEZE][WARN] 未找到 BANDIT_ROUNDS 报告，后续理由中将缺少最新轮次上下文"
fi

ROUNDS_ARG="${ROUNDS_PATH:-}"

PYTHON_RESULT="$(
python3 - "${MODE}" "${SUMMARY_PATH}" "${ROUNDS_ARG}" <<'PY'
import json
import sys
from pathlib import Path

mode = sys.argv[1].lower()
summary_path = Path(sys.argv[2])
rounds_arg = sys.argv[3] if len(sys.argv) > 3 else ""
rounds_path = Path(rounds_arg) if rounds_arg else None

if mode not in {"reward", "quality", "latency"}:
    raise SystemExit(f"unsupported MODE={mode}")

with summary_path.open("r", encoding="utf-8") as handle:
    lines = handle.readlines()

state_rows = {}
collect_state = False
for line in lines:
    stripped = line.strip()
    if stripped == "## State Overview":
        collect_state = True
        continue
    if collect_state:
        if not stripped or not stripped.startswith("|"):
            if stripped and not stripped.startswith("|"):
                continue
            if not stripped:
                break
        if stripped.startswith("| ---"):
            continue
        parts = [part.strip() for part in stripped.split("|")[1:-1]]
        if len(parts) < 6:
            continue
        if parts[0].lower() == "arm":
            continue
        arm = parts[0]
        try:
            avg_reward = float(parts[2])
        except ValueError:
            avg_reward = 0.0
        try:
            last_p95 = float(parts[3])
        except ValueError:
            last_p95 = 0.0
        try:
            last_recall = float(parts[4])
        except ValueError:
            last_recall = 0.0
        state_rows[arm] = {
            "avg_reward": avg_reward,
            "last_p95": last_p95,
            "last_recall": last_recall,
        }

round_rows = {}
if rounds_path and rounds_path.exists():
    with rounds_path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    collecting = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("| round ") and "arm" in stripped:
            collecting = True
            continue
        if not collecting:
            continue
        if not stripped or not stripped.startswith("|"):
            if collecting and not stripped:
                break
            continue
        if stripped.startswith("| ---"):
            continue
        parts = [part.strip() for part in stripped.split("|")[1:-1]]
        if len(parts) < 10:
            continue
        try:
            round_idx = int(parts[0])
        except ValueError:
            continue
        arm = parts[1]
        try:
            p95 = float(parts[3])
        except ValueError:
            p95 = 0.0
        try:
            recall = float(parts[4])
        except ValueError:
            recall = 0.0
        existing = round_rows.get(arm)
        if not existing or round_idx >= existing["round"]:
            round_rows[arm] = {"round": round_idx, "p95": p95, "recall": recall}

for arm, data in state_rows.items():
    fallback = round_rows.get(arm)
    if fallback:
        if data["last_p95"] <= 0:
            data["last_p95"] = fallback["p95"]
        if data["last_recall"] <= 0:
            data["last_recall"] = fallback["recall"]

if not state_rows:
    raise SystemExit("no arms found in summary report")

def pick_candidate(mode_name: str):
    arms = list(state_rows.items())
    if mode_name == "reward":
        return max(arms, key=lambda item: item[1].get("avg_reward", float("-inf")))
    if mode_name == "quality":
        return max(arms, key=lambda item: item[1].get("last_recall", float("-inf")))
    if mode_name == "latency":
        return min(arms, key=lambda item: item[1].get("last_p95", float("inf")))
    raise ValueError(mode_name)

selected_arm, metrics = pick_candidate(mode)
metric_key = {
    "reward": "avg_reward",
    "quality": "last_recall",
    "latency": "last_p95",
}[mode]

metric_value = metrics.get(metric_key, 0.0)

output = {
    "arm": selected_arm,
    "metric": metric_key,
    "value": metric_value,
    "avg_reward": metrics.get("avg_reward", 0.0),
    "last_recall": metrics.get("last_recall", 0.0),
    "last_p95": metrics.get("last_p95", 0.0),
    "summary": summary_path.name,
    "rounds": rounds_path.name if rounds_path else "",
}
print("|".join([
    output["arm"],
    output["metric"],
    f"{output['value']:.6f}",
    f"{output['avg_reward']:.6f}",
    f"{output['last_recall']:.6f}",
    f"{output['last_p95']:.2f}",
    output["summary"],
    output["rounds"],
]))
PY
)"

if [[ -z "${PYTHON_RESULT}" ]]; then
  echo "[BANDIT_FREEZE][ERROR] 无法从报告中解析候选臂"
  exit 1
fi

IFS='|' read -r ARM METRIC_NAME METRIC_VALUE AVG_REWARD LAST_RECALL LAST_P95 SUMMARY_FILE ROUNDS_FILE <<<"${PYTHON_RESULT}"

printf "[BANDIT_FREEZE] recommend arm=%s mode=%s metric=%s value=%s avg_reward=%s recall=%s p95=%s summary=%s rounds=%s\n" \
  "${ARM}" "${MODE}" "${METRIC_NAME}" "${METRIC_VALUE}" "${AVG_REWARD}" "${LAST_RECALL}" "${LAST_P95}" "${SUMMARY_FILE}" "${ROUNDS_FILE:-n/a}"

if [[ "${APPLY}" == "1" ]]; then
  ENCODED_ARM="$(
  python3 - "${ARM}" <<'PY'
import sys
import urllib.parse
print(urllib.parse.quote(sys.argv[1]))
PY
)"
  RESPONSE="$(curl -sSf -X POST "${BASE_URL}/api/admin/policy/apply?name=${ENCODED_ARM}")"
  printf "[BANDIT_FREEZE] applied arm=%s response=%s\n" "${ARM}" "${RESPONSE}"
fi

