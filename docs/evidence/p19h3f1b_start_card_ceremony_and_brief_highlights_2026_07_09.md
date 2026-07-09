# P19H-3f-1b — Start Card Ceremony + Claim Brief Highlights

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** P19H-3f-1b Start Card = Case Creation Ceremony · P19H-3e-1b Claim Case Brief `highlights[]`  
**Deploy:** No

---

## 1. Goal

1. Pin Start Card as the formal Claim case creation ceremony (product contract + tests).
2. Add deterministic lightweight `highlights[]` to `claim_case_brief` so Chen can scan a case in ~10 seconds.

---

## 2. Start Card ceremony rule

```text
Formal customer-facing Claim case MUST emit Start Card.
No Start Card means no customer-facing formal Claim case has started.
```

Marker: `【事故记录已开始 ✅】`  
Disclaimer: `这不代表已经向保险公司正式报案。`

Contract doc: `docs/p19h3f1b_start_card_case_creation_ceremony.md`

---

## 3. Equivalent Start Ceremony surfaces

| Surface | Rule |
|---------|------|
| WeCom explicit start | 我要理赔 / 开始理赔 / 新事故 → create Claim + Start Card |
| H5 Task Page | Page itself = Start Ceremony; append to existing formal case |
| Future mini program | Start page = equivalent ceremony |
| Broker-created case | Mark formal; customer gets Start Notice on next touch |

**Not ceremony:** random narrative, random photo, injury click alone, insurance Q&A.

---

## 4. What was tested (Start Card)

| Case | Expected |
|------|----------|
| 我要理赔 | Creates Claim; reply has Start Card markers + disclaimer |
| Random narrative | No Claim; no Start Card |
| Random photo | No Claim; no Start Card |
| Injury click alone | No Claim; no Start Card |
| 我要理赔 / 开始理赔 / 新事故 | All emit Start Card |

File: `tests/test_p19h3f1_case_boundary_policy.py` (incl. `test_13_formal_claim_paths_emit_start_card`)

---

## 5. Highlights[] behavior

- Location: `build_claim_case_brief()` in `claim_workbench_display.py`
- Max 5 items; factual markers and gaps only
- Levels: `important` · `missing` · `received`
- Kinds: `injury` · `evidence` · `basics` · `missing_info`
- No fault / liability / coverage / carrier filing language

---

## 6. Example generated highlights

**Injury confirmed, photo received, basics complete:**

```json
[
  {"level": "important", "label": "受伤情况已确认：没有受伤", "kind": "injury"},
  {"level": "received", "label": "已收到 1 张照片", "kind": "evidence"},
  {"level": "received", "label": "事故基本经过已记录", "kind": "basics"}
]
```

**Injury unknown, gaps:**

```json
[
  {"level": "missing", "label": "还缺受伤情况确认", "kind": "injury"},
  {"level": "missing", "label": "还缺对方保险信息", "kind": "missing_info"},
  {"level": "missing", "label": "还缺照片", "kind": "missing_info"}
]
```

**Injury yes:**

```json
[
  {"level": "important", "label": "有人受伤，陈总需优先人工确认", "kind": "injury"}
]
```

---

## 7. UI result

`ClaimCaseBriefPanel` shows **重点速览** chip row above **还缺什么** when `highlights[]` is present. No full redesign.

---

## 8. Tests result

| Suite | Result |
|-------|--------|
| `tests/test_p19h3f1_case_boundary_policy.py` | PASS (36 incl. ceremony) |
| `tests/test_p19h3e1_claim_timeline_case_brief.py` | PASS |
| `tests/test_p19h3e1b_claim_case_brief_highlights.py` | PASS (7) |
| `pytest -k claim` | PASS |
| `pytest -k h5` | PASS |
| `ui npm run build` | PASS |

---

## 9. QA gate result

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result: FAIL** — pre-existing seed/demo alignment (missing 张先生/王女士 in API page; tag mismatches). Not caused by this sprint. No deploy performed.

---

## 10. Constraints honored

- No schema change
- No deploy
- No OCR / ASR / damage AI
- No fault / coverage / carrier filing judgment
- No LLM brief
- No True End Card / `broker_done`
- No large UI refactor

---

## 11. Known limitations

- Highlights are deterministic only; no LLM summarization
- H5 / mini-program Start Ceremony equivalence is documented but not re-tested end-to-end here
- QA gate seed drift remains; fix in separate seed sprint

---

## 12. Next recommended prompt

1. **P19H-3f-1b Deploy + Start Card Ceremony + Highlights Smoke**
2. **P19H-3f-2 True End Card on Broker Done**
