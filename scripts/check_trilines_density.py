#!/usr/bin/env python3
"""
Check trilines CSV density.
Ensures .runs/real_large_trilines.csv has:
- >= 60 rows (policy x budget combinations)
- >= 8 distinct budgets
- >= 2 distinct policies
"""

import argparse
import csv
import sys
from pathlib import Path

DEFAULT_CSV_PATH = Path(".runs/real_large_trilines.csv")
# Updated thresholds for denser grid with policy dimension
# Expected: 3 policies x 15 budgets (200-1600 in 100ms steps) = 45 rows minimum
# But we want to be more lenient: >= 60 rows, >= 8 budgets, >= 2 policies
MIN_ROWS = 60
MIN_BUDGETS = 8
MIN_POLICIES = 2


def main():
    parser = argparse.ArgumentParser(description="Check trilines CSV density.")
    parser.add_argument("--path", type=str, help=f"Path to CSV file (default: {DEFAULT_CSV_PATH}).")
    parser.add_argument("--min-rows", type=int, help=f"Minimum number of rows (default: {MIN_ROWS}).")
    parser.add_argument("--min-budgets", type=int, help=f"Minimum number of distinct budgets (default: {MIN_BUDGETS}).")
    parser.add_argument("--min-policies", type=int, help=f"Minimum number of distinct policies (default: {MIN_POLICIES}).")
    args = parser.parse_args()
    
    csv_path = Path(args.path) if args.path else DEFAULT_CSV_PATH
    min_rows = args.min_rows if args.min_rows is not None else MIN_ROWS
    min_budgets = args.min_budgets if args.min_budgets is not None else MIN_BUDGETS
    min_policies = args.min_policies if args.min_policies is not None else MIN_POLICIES
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        print("   Run 'make real-large-paired' or 'make trilines-refresh' first")
        sys.exit(1)

    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    row_count = len(rows)
    if row_count < min_rows:
        print(f"❌ CSV has only {row_count} rows, need at least {min_rows}")
        print(f"   Expected at least {min_rows} rows (policy x budget), got {row_count}")
        print(f"   File: {csv_path}")
        sys.exit(1)

    # Check for unique combinations
    budgets = set()
    policies = set()
    for row in rows:
        budget = row.get("budget_ms") or row.get("budget")
        if budget:
            budgets.add(budget)
        policy = row.get("policy")
        if policy:
            policies.add(policy)

    unique_budgets = len(budgets)
    unique_policies = len(policies)
    
    if unique_budgets < min_budgets:
        print(f"❌ CSV has only {unique_budgets} unique budgets, need at least {min_budgets}")
        print(f"   Found budgets: {sorted(budgets)}")
        print(f"   File: {csv_path}")
        sys.exit(1)
    
    if unique_policies < min_policies:
        print(f"❌ CSV has only {unique_policies} unique policies, need at least {min_policies}")
        print(f"   Found policies: {sorted(policies)}")
        print(f"   File: {csv_path}")
        sys.exit(1)

    print(f"✅ CSV density check passed:")
    print(f"   Rows: {row_count} (>= {min_rows})")
    print(f"   Unique budgets: {unique_budgets} (>= {min_budgets})")
    print(f"   Unique policies: {unique_policies} (>= {min_policies})")
    print(f"   Budgets: {sorted(budgets)}")
    print(f"   Policies: {sorted(policies)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

