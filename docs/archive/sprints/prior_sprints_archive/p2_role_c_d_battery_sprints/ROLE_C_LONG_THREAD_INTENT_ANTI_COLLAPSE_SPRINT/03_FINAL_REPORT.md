# Final report — ROLE C long-thread intent anti-collapse

## Environment

- **API:** `http://127.0.0.1:8001` (live fiqa_api; `/health/live` 200).
- **Client:** `chen_kui`.
- **Role C model (observed):** `gpt-4o-mini`.
- **Battery:** `scripts/run_role_c_add_car_battery.py`, `--truth-chain`, `ROLE_C_SIMULATION_MAX_TURNS=8`, **`--max-turns 7`** (see `01_BLUEPRINT.md` for cap rationale).
- **Artifacts:** per-case JSONL under `_battery_traces/c1.jsonl` … `c5.jsonl` (local run).

## API observability gap (verified)

- `POST /api/inbox/triage` **did not include** `add_car_turn_intent` in JSON (curl spot-check and battery traces).
- Workspace `triage.py` **does** populate `add_car_turn_intent` when `is_add_car` (lines ~4457–4463)—**running process likely stale vs repo**, or a response-shaping path drops the field.
- **Impact:** This sprint could not use `intent_family` from the wire for continuity; oracles that depend on it under-fired (`INTENT_LATE_GENERIC`, `REPLY_CONTACT_GAP_TAIL_MISMATCH`).

## Per-case highlights

### C1 — price_sensitive / tough

- **Truth-chain:** `case_b711c980b8cb`, `formal_submitted_at` set after inject.
- **Late turns:** Customer pressed **deductible delta + timeline**; reply repeated the same **quote-detail deferral + contact tail** block.
- **Oracle:** `REPLY_REPEATED_BLOCK` on last turn (four consecutive identical stems).

### C2 — elderly / tough

- **Oracle:** `STATE_POST_SUBMIT_LIFECYCLE_COLLECTING` mid-thread while runner had `case_id` (post-submit truth)—customer supplied name/phone then system asked for year/model; lifecycle **collecting** with persisted case.

### C3 — family_vehicle / realistic

- **Late turns:** Coverage / multi-driver questions answered with **generic office-handoff rotation** (“已进入办公室处理阶段” / “加车要点已写入…” / “资料已到办公室”) with **little engagement** with coverage substance.

### C4 — materials_first / realistic

- **Friction:** Same thread mixed **“可以，先发我，办公室一起核”** with **“加车资料已到办公室”**—truth-safe pieces but **jarring** for “收到了吗” questions.

### C5 — fragmented / tough

- **Early handoff** (turn 2); late turns **timeline / channel / options** collapsed to **same handoff template family** as C3/C4.

## Issue harvest (grouped)

**A. Intent collapse**

- Late-turn **quote_detail** + **timeline** linguistically distinct customer lines received **same** reply stem family (C1, C3).
- **Cannot confirm** `intent_family` flattening on the wire (field missing from API).

**B. Reply weakness**

- **REPLY_REPEATED_BLOCK** (C1).
- **Contact-gap tail** appended even when customer **explicitly** provided name/phone but structured `still_needed` still listed `name` (C1, C2, C3, C4, C5).

**C. Truth / state mismatch**

- **Post-submit** runner truth vs **`lifecycle_status: collecting`** (C2).
- **`still_needed_fields: ["name"]`** persisting after customer messages containing name+phone (multiple runs)—append/truth extraction lag vs reply layer.

**D. Persona / difficulty**

- **Tough vs realistic** differences **faded** post-submit; both devolved to **office-phase template rotation**.

**E. Demo / product clarity**

- Broker would struggle to explain **why** a **timeline** question got a **static quote-prep deferral** paragraph.
- Right-rail story vs bubble **diverges** when lifecycle jumps (C2).

## Top 5 ranked (pilot risk)

1. **Long-thread reply collapse on quote/timeline turns** — trust + demo killer (C1 oracle + C3/C5 qualitative).
2. **Lifecycle / post-submit coherence** — `collecting` under `case_id` breaks Zendesk-style scannability (C2).
3. **Contact tail + stale `still_needed`** — reads as **robotic** and ignores latest customer text (all runs).
4. **Mixed “send materials” vs “already at office”** — broker credibility (C4).
5. **`add_car_turn_intent` not returned live** — blocks regression and Intent-layer proof (curl + traces).

## Founder answers (中文)

1. **Intent 最强处：** 逻辑上 `add_car_intent.py` 在仓库里已能把 receipt / timeline / quote detail 等分开；但**本次 live API 未返回** `add_car_turn_intent`，无法在长线程上验收这一条。
2. **最明显塌缩：** ** late-turn 条款/时间线 ** 被同一套「办公室核对后确认 + 联系尾」反复打发。
3. **Reply 最容易变笨：** **post-submit 下的 quote_detail / timeline / coverage 解释型** 追问。
4. **append truth：** **部分不稳**——客户已口述姓名电话但 `still_needed` 仍卡 name；C2 出现 **case_id 已有但 lifecycle 回到 collecting**。
5. **Persona / difficulty：** **后期不明显**，都落进办公室阶段模板轮换。
6. **下一轮最值得修：** **长线程下按 intent 分支的 reply 多样性 + 与 still_needed 同步**；并 **保证 API 暴露 intent + 修 post-submit lifecycle 一致性**。

## Verdict

- Sprint **worth it:** surfaced **repeat-block** and **state/tail** issues that short runs miss.
- **Industrial long-thread quality:** **not yet**—late turns still **template-heavy**.
- **Next:** small implementation sprint: wire **`add_car_turn_intent` in live responses**, fix **post-submit lifecycle / identity merge**, add **timeline vs quote_detail** reply heads (within truth).
