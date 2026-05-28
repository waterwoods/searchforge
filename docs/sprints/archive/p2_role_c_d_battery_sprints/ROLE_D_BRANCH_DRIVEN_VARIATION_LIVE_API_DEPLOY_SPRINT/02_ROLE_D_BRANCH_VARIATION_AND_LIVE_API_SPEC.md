# Role D — Branch variation & live API (Spec)

## Branch-driven design (v1)

### Interpretation

- The **custom note** is scanned with a small set of **regex keyword rules**.
- Each match maps to a **branch family** (e.g. price-sensitive, materials-sent, household vehicle).
- Families are ordered by **priority**; at most **four** families apply per scenario build (avoid chaos).

### What the note influences

- **Turn 0:** unchanged behavior—note is still woven into the first customer line (`对了，{note}`).
- **Turns ≥ 1:** up to four families each pick a **distinct later slot** (indices `1 .. n-1`) and append one **canned suffix** from a small rotating pool.
- **Determinism:** slot hints and suffix choice use a **djb2-style hash** of `note|templateId|difficulty|baseTurns` so the same config yields the same script.

### Branch families (minimum set)

| Family ID | Example keywords (illustrative) |
|-----------|----------------------------------|
| `materials_sent` | 微信, 材料, 发过, dec, declaration |
| `household_vehicle` | 配偶, 家庭, spouse, 另一台车 |
| `price_sensitive` | 便宜, 太贵, price sensitive, premium, 比价 |
| `coverage_concern` | coverage, liability, collision, comprehensive, 险种 |
| `typo_correction` | typo, 记错, 笔误, 纠正, 打错 |
| `mixed_zh_en_style` | 中英, mixed, 夹英文 |
| `fragmented_style` | 碎片, 分几次, fragmented |

### Bounded control

- **No new turns** added; turn count stays identical to the template × difficulty script.
- **No LLM**; only rule + template text.
- **De-dupe:** skip appending a suffix if the turn already contains an early substring of that suffix.

### Transparency

- Scenario **subtitle** includes `自述分支：…` listing activated families (Chinese labels).

## Live API integration target

- Replay path: `ScenarioReplayTab` → `triageMessage(..., softRoute: 'add_car', clientId from context)` → `POST /api/inbox/triage` (`ui/src/api/inboxTriage.ts`).
- Each **Next step** sends the scripted customer line plus prior `conversation_turns`—backend state, missing fields, and reply drive the **right-hand panel** and flow step tags.

## Deploy & smoke acceptance

### Deploy

- **Frontend:** Vercel production build must pass `assertVercelProductionApiBase`: `VITE_API_BASE_URL` is **https** and **not** localhost (see `ui/vite.config.ts`).
- **CLI one-off:** `vercel deploy --prod --yes -b VITE_API_BASE_URL=https://<cloud-run-host>` when dashboard env is wrong.
- **Backend:** Deploy only if triage or API contract changes (not required for Role-D-only UI work).

### Smoke (minimum)

1. `GET` production UI → 200.
2. `GET` Cloud Run `/readyz` → 200.
3. `POST /api/inbox/triage` with `soft_route: add_car` → JSON reply with `client_reply_draft` / structured hints.

### Known configuration risk

- If Vercel project env stores `VITE_API_BASE_URL=http://localhost:8001`, **build fails by design**—fix in Vercel env or pass `-b` on CLI.
