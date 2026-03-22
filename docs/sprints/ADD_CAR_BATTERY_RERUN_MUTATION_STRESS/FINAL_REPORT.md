# Add-Car Scenario Battery Re-Run + Mutation Stress Report

## 1. Sprint theme

- **What was evaluated:** Add-Car rule-path behavior after recent **ZIP extraction**, **driver micro-phrase**, and **already-sent question-vs-statement** hardening.
- **Why now:** Prior sprint looked good on fixed examples; this sprint **re-ran authoritative batteries** and added **mutation phrasing** to test generalization—not memorization.

## 2. Document set created

| # | Document |
|---|----------|
| 1 | `BATTERY_RERUN_BLUEPRINT.md` |
| 2 | `MUTATION_SCENARIO_DESIGN_SPEC.md` |
| 3 | `MUTATION_SCENARIO_PACK.md` + `mutation_scenario_pack.json` |
| 4 | `EVALUATION_CRITERIA.md` |
| 5 | `FIX_PRIORITY_SPEC.md` |
| 6 | `EXECUTION_OUTLINE.md` |
| 7 | `FOUNDER_INSPECTION_NOTES.md` |
| 8 | `FINAL_REPORT.md` (this file) |

**Runner added:** `scripts/run_add_car_mutation_battery.py`

## 3. Original battery re-run results

### What was rerun

| Command | Result |
|---------|--------|
| `PYTHONPATH=. python3 scripts/run_add_car_scenario_battery.py` | **17/17** scenarios completed (exit 0) |
| `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py` | **18/18** strong (exit 0) |
| `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 -u scripts/run_multi_turn_simulations.py` | **69** sims, **69 strong**, 0 weak (exit 0) |
| `bash scripts/guardrail_inbox_triage.sh` | **Guardrail: PASS** |

### What improved / weak cases

- **ZIP / driver / materials threads** in `ACB-*` and `ACE*` behaved consistently with **quote_ready** when slots were satisfied; **ACE03** (materials sent), **ACB-E03**, **ACB-M04** turn 2, and broker stress **BS11 / HT13** paths remain **strong** under guardrail.
- **No automated regression** detected (all packs exit 0; weak count 0).

### Broker review readiness

- **Sufficient for broker review** on Add-Car happy/messy paths covered by batteries.
- **Watch item (pre-existing):** `ACB-E07` turn 1 (“office 几点关门”) → `unclear` + generic incomplete-message reply is **awkward** for a real customer; **not** a regression from the three Add-Car fixes but visible if that scenario is demoed.

## 4. Mutation scenario pack

- **Count:** **10** new scenarios.
- **Categories:** ZIP formats (4), driver micro-phrases (3), already-sent intent (3).
- **Why they matter:** They **vary surface form** (spacing, glued `zip`, bare digits, short driver nouns, question vs statement) while keeping **California Chinese** realism.

## 5. Mutation scenario results

| Scenario ID | User message sequence (abridged) | Observed behavior (final turn) | Classification | Judgment |
|---------------|----------------------------------|----------------------------------|------------------|----------|
| MUT-Z01 | (1) Model Y 报价 → (2) `邮编95131，明天提车，就我一个人开` | `quote_ready`, handoff, Tesla Y in broker step | **Strong** | ZIP without space parses; clean handoff. |
| MUT-Z02 | (1) CR-V 缺邮编 → (2) `zip95131` | `quote_ready`, CR-V in broker step | **Strong** | Glued `zip95131` works. |
| MUT-Z03 | Single: `2024 Tesla，邮编95131，我自己开…` | `quote_ready` first turn | **Strong** | Dense bubble extracted. |
| MUT-Z04 | (1) X3 缺邮编 → (2) `95131` | `quote_ready` | **Strong** | Bare ZIP accepted as follow-up. |
| MUT-D01 | (1) RAV4 + zip + delivery → (2) `本人开` | Both turns handoff; T1 asked confirm main driver in broker line | **Strong** | Micro-phrase completes thread without confusion. |
| MUT-D02 | (1) civic + zip + delivery → (2) `我老婆开` | handoff; broker confirms driver | **Acceptable** | T1 already handoff without driver phrase—OK with broker “confirm driver”; copy could acknowledge 老婆 explicitly (polish). |
| MUT-D03 | (1) Lexus RX complete → (2) `儿子开` | handoff both turns | **Acceptable** | Same pattern as D02—safe, slightly redundant handoff copy on T2. |
| MUT-A01 | quote-ready RAV4 thread → `对了材料要不要先发给你` | No false “材料发过了”; generic quote-ready handoff repeated | **Acceptable** | **Intent guard holds**; customer reply does not answer the question. |
| MUT-A02 | quote-ready Camry → `要不我发你微信你看下行不行` | No false already-sent; generic handoff | **Acceptable** | Same as A01—safe but thin UX. |
| MUT-A03 | quote-ready Camry → `我已经发你微信了，截图发你了哈` | Customer: 材料发过了…; broker: verify WeChat | **Strong** | Statement path + broker action correct. |

## 6. Overall pattern analysis

### Clearly stronger

- **ZIP** variants (Chinese label, spacing, glued English, bare digits, embedded in long Chinese).
- **Already-sent statements** (WeChat + 截图) → **materials-aware** customer copy and **verify** broker guidance.

### Still fragile / awkward

- **Material-send questions and soft offers** (要不要发 / 要不我发你): **no misclassification** (major win), but **customer-facing** response does not guide **what to send**—feels like a **skipped beat** in a live thread.
- **Off-topic first bubbles** in otherwise Add-Car batteries (e.g. office hours) remain a **separate** routing weakness.

### Risky patterns (monitor)

- Repeated **generic** “报价资料已整理好了…” on **follow-up** turns when the customer introduced a **new pragmatic question** (A01/A02).

## 7. Fix-now / Fix-next / Acceptable / Defer

| Bucket | Item |
|--------|------|
| **Fix-now** | None (no trust-breaking mutation results; batteries green). |
| **Fix-next** | Short, explicit reply branch for “要不要发材料 / 要不我发微信” on quote-ready Add-Car threads. |
| **Acceptable** | MUT-D02/D03 second-turn redundancy; broker still instructed to confirm driver. |
| **Defer** | ACB-E07 office-hours routing (FAQ/office-info track). |

## 8. Final broker-confidence judgment

- **Safer for broker review on Add-Car?** **Yes**—especially on **ZIP**, **driver shorthand**, and **already-sent statement vs question** (no false “已发” on questions).
- **Biggest strength:** Extraction + intent guard **generalize** beyond the original strings.
- **Biggest remaining weakness:** **Conversational completeness** when the customer asks **whether** to send docs (not a classification bug).
- **Single best next fix:** Add a **targeted customer reply + broker hint** for material-send **questions/offers** on quote-ready Add-Car cases.

## 9. 中文宏观总结

这轮在 **关掉 LLM** 的规则路径上，重跑了 **17 条 Add-Car 电池**、**18 条 ACE 边缘用例**（也包含在 **69 条**多轮仿真里），并跑通 **guardrail 全套**；结果 **全部通过、无 weak**。说明之前针对 **邮编格式、驾驶人口语、材料已发/疑问** 的修复，在“老题”上 **没有回退**。

在此基础上新增了 **10 条**“变体题”专门刁难这三块：**邮编**各种写法（含粘连、纯数字第二泡）、**驾驶人**超短说法、以及 **要不要发 / 要不我发微信 / 已经发了** 的意图区分。变体下 **ZIP 和“已发”陈述**表现 **很稳**；“要不要发”类 **不会误判成已发**（这是最关键的 **不失信** 点），但 **客户可见回复**还可以更贴心（直接告诉可以发微信/截图）。

**结论：** Add-Car 给 Chen Kui 看 **可以更放心**，主要信心来自 **提取 + 意图边界**；若要更“像真人经纪助理”，下一步优先补 **材料发送问句** 的回复话术。

## 10. COPY/PASTE FOUNDER BLOCK

```
Add-Car Battery Re-Run + Mutation Stress (2026-03-21)
- Re-ran: 17 ACB battery scenarios; 18 ACE edge sims; 69 multi-turn sims (includes ACE); full guardrail_inbox_triage.sh → ALL PASS, 0 weak.
- Added: 10 mutation scenarios (ZIP / driver / materials intent).
- The 3 high-ROI themes (ZIP formats, driver micro-phrases, already-sent Q vs statement) HELD on old + new cases; no false “materials already sent” on question-style phrasing.
- Biggest remaining weakness: customer reply still generic on “要不要发你 / 要不我发微信” (safe, but not helpful).
- Andy can show Add-Car to Chen Kui with higher confidence on extraction + intent; optional polish: answer materials Q&A on quote-ready threads.
```
