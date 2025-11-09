#!/usr/bin/env bash
set -euo pipefail

LOG_PREFIX="[BANDIT_SMOKE]"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
POLICY_FILE="${REPO_ROOT}/configs/policies.json"
WINNERS_FILE="${REPO_ROOT}/reports/winners.final.json"

export LOG_PREFIX REPO_ROOT POLICY_FILE WINNERS_FILE

python3 - <<'PY'
import json
import os
import pathlib

log = os.environ["LOG_PREFIX"]
policy_path = pathlib.Path(os.environ["POLICY_FILE"])
winners_path = pathlib.Path(os.environ["WINNERS_FILE"])

policies = json.loads(policy_path.read_text())
winners = json.loads(winners_path.read_text())

arms = policies.get("arms", [])
print(f"{log} arms: {', '.join(arms)}")

tiers = winners.get("tiers", {})
name_map = {
    "fast": "fast_v1",
    "balanced": "balanced_v1",
    "quality": "quality_v1",
}

for tier_key, policy_name in name_map.items():
    tier = tiers.get(tier_key)
    if not tier:
        continue
    summary = {
        "collection": tier.get("collection"),
        "top_k": tier.get("top_k"),
        "mmr": tier.get("mmr"),
        "mmr_lambda": tier.get("mmr_lambda"),
        "ef_search": tier.get("ef_search"),
        "expected_recall": tier.get("expected_recall"),
        "expected_p95_ms": tier.get("expected_p95_ms"),
    }
    print(f"{log} {policy_name}: {summary}")

print(f"{log} smoke check complete (no mutations performed)")
PY


