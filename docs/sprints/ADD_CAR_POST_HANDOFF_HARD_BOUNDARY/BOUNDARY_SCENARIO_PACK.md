# Boundary Scenario Pack — Post-Handoff Add-Car

**Machine-readable source:** `configs/case_boundary_append_scenarios.json`  
**Runner:** `scripts/run_case_boundary_battery.py` (expects `LLM_GENERATION_ENABLED=0` for deterministic rules)

## Coverage (23 scenarios)

| ID | Intent | Expected |
|----|--------|----------|
| CB-01 | Materials / screenshot after handoff | same_case |
| CB-02 | Pivot to 账单 | new_issue |
| CB-03 | Coverage + 顺便问 | same_case |
| CB-04 | Pivot to claim | new_issue |
| CB-05 | Vague “还有一个问题” | borderline |
| CB-06 | Office hours | borderline |
| CB-07 | Pivot 账单 (EN system line) | new_issue |
| CB-08 | 加车先这样 + claim | new_issue |
| CB-09 | 再问另一个 (vague) | borderline |
| CB-10 | 删车 pivot | new_issue |
| CB-11 | claim pivot | new_issue |
| CB-12 | Vehicle correction | same_case |
| CB-13 | Short ZIP | same_case |
| CB-14 | 删车 pivot (另外一个事情) | new_issue |
| CB-15 | Renewal thread → add car | new_issue |
| CB-16 | Claim thread → billing | new_issue |
| CB-17 | 不是这个车 / 另一个保险 (vague) | borderline |
| CB-18 | Second vehicle same quote | same_case |
| CB-19 | 续保 pivot after add-car handoff | new_issue |
| CB-20 | 要不要发 VIN | same_case |
| CB-21 | Mixed VIN + billing | new_issue |
| CB-22 | 先处理这个再问别的 (vague) | borderline |
| CB-23 | 全险多少钱 (quote follow-up) | same_case |

## Labels (for manual review)

Most rows: **rule-based good enough**.  
CB-05, CB-09, CB-17, CB-22: **human confirmation better** (borderline).  
Long ambiguous pivots: **future LLM assist candidate** (optional ranking only).
