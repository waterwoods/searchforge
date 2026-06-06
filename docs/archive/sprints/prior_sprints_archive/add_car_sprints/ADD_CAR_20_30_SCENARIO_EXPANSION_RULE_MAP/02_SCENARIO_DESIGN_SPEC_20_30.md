# 20–30 Scenario Design Spec

## Battery size

**30 scenarios** (`ACEXP-001` … `ACEXP-030`) in `scenario_battery.json`.

## Category coverage (required A–G)

| Bucket | Scenario IDs | Notes |
|--------|----------------|-------|
| **A — Clean / normal** | ACEXP-001 … 005 | One-bubble full info; 2-turn; 3-turn; EN-heavy; minimal opener + fill |
| **B — Partial / progressive** | ACEXP-006 … 010 | Vehicle→ZIP; ZIP→vehicle; driver late; delivery late; contact (phone) late |
| **C — Correction** | ACEXP-011 … 015 | Honda→Tesla; X5→X3; same-turn zip+model change; correction + materials sent; CN/EN “i meant” |
| **D — Materials** | ACEXP-016 … 023 | 材料/微信/截图/要不要/先发/看看行吗; 2-turn quote-ready + ask-send / already-sent |
| **E — Price / side questions** | ACEXP-024 … 028 | 便宜; 大概多少钱; garaging proof; office hours; 先帮我看看多少钱 + dense |
| **F — Driver phrasings** | *Distributed* | 我自己开 / 我一个人开 / 本人开 / 老婆老公开 / 儿子女儿 / 主要驾驶人是我老婆 appear across A,B,D,E,G (see matrix below) |
| **G — Dense / messy** | ACEXP-029, 030 | Ultra-dense single bubble; vague + jumpy + two-car confusion thread |

## Messiness distribution (targets)

| Tag | Target | Actual (v1 battery) |
|-----|--------|---------------------|
| `clean` | ≥5 | 5 (001–005) |
| `messy` | ≥8 | 17 |
| `edge` / broker-risky | ≥5 | 8 |
| Multi-turn mixed | 2–4 | Multiple; **030** is explicit 3-turn stress |

## Driver phrase matrix (category F)

| Phrase | Example scenario |
|--------|------------------|
| 我自己开 | 001, 010, 016, 019, 024, 030 |
| 我一个人开 | 012, 022 |
| 本人开 | 005, 017, 023 |
| 我老婆开 | 006, 015, 020 |
| 我老公开 | 007, 021 |
| 儿子开 | 018 |
| 女儿开 | 028 |
| 主要驾驶人是我老婆 | 020, 029 |

## Schema (per scenario)

- `id`, `name`, `messiness`, `coverage_category`, `focus[]`, `why_matters`, `expected_good_behavior`, `failure_looks_like`, `turns[]` with `role` + `text`.

## Relationship to older batteries

- **ACB** (`ADD_CAR_SCENARIO_BATTERY_EVALUATION`): historical 17-case pack; still run for regression comparison.
- **ADZM** (`ADD_CAR_DRIVER_ZIP_MATERIALS_STRESS_BATTERY`): ZIP/driver/materials stress; still run.
- **ACEXP**: this sprint’s **broader realism + edge** layer; primary source for gap analysis in `09_FINAL_REPORT.md`.
