# Mutation Scenario Design Spec

## Goal

After the original battery passes, **attack the same three surfaces** the recent sprint hardened—using **new** phrasing not present in `scenario_battery.json` / ACE*, so we are not only “memorizing” old strings.

## Target surfaces

### Area A — ZIP mutation

Stress formats common in WeChat / bilingual typing:

- `邮编` + digits **without** space (`邮编95131`).
- English `zip` **jammed** to digits (`zip95131`).
- **Bare** 5-digit follow-up after a ZIP prompt (`95131`).
- **Single bubble** with vehicle + `邮编` + driver + delivery (dense Chinese).

**Pass signal:** `quote_ready_status` reaches `quote_ready` when enough slots exist; broker step references vehicle and remaining confirmations; no spurious re-ask for ZIP already provided.

### Area B — Driver micro-phrases

Stress short, colloquial primary-driver statements:

- `本人开`, `我一个人开` (covered across pack + battery).
- `我老婆开`, `儿子开` / family driver shorthand.

**Pass signal:** No spurious handoff that ignores driver ambiguity when required; when combined with complete vehicle+zip+delivery, broker guidance still mentions confirming driver before bind where policy expects it.

### Area C — Already-sent **intent** (question vs statement)

Stress:

- **Questions / offers:** “要不要先发给你”, “要不我发你微信你看下行不行”.
- **Statements:** “我已经发你微信了，截图发你了哈”.

**Pass signal:**

- **Trust-breaking failure:** Customer-facing copy treats a **question** as “材料已发”.
- **Strong:** Statement triggers materials-aware tone + broker “verify WeChat / materials” guidance.
- **Acceptable:** No wrong already-sent claim, but reply is generic and does not answer “要不要发”.

## Count

- **10** mutation scenarios total (`MUT-Z*`, `MUT-D*`, `MUT-A*`), stored in `mutation_scenario_pack.json`.

## Execution

`PYTHONPATH=. python3 scripts/run_add_car_mutation_battery.py`  
(JSON: add `--json`.)

## Classification labels (human)

Per final turn (or per scenario): **Strong** | **Acceptable** | **Weak** | **Trust-breaking** — see `EVALUATION_CRITERIA.md`.
