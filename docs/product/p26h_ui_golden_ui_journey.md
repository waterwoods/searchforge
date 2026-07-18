# P26H-UI — Mini Program Golden UI Journey

## Status

**CONDITIONAL GO** — local + in-process QA UI path PASS; deployed HTTP QA needs
`P26H_QA_BASE_URL` + support key on a QA runtime with fixture flags enabled.

See also: `docs/product/p26h_golden_customer_flow_harness.md` ·
`bash scripts/run_claim_release_gate.sh --local|--qa`

## 1. Why P26H missed the blank page

P26H local validated:

- Constitution task routes (`insurance` → request-item page path)
- server case ownership / projection / resume

It did **not** bootstrap the destination Mini Program page or assert WXML-bound primary UI.

Founder defect:

1. Task Home maps `system_default` insurance → `/pages/request-item/request-item`
2. Page TS correctly entered evidence upload mode (`inputMode === "evidence"`)
3. WXML still gated the work surface on `nextAction`
4. `system_default` has no Slice1 `nextAction` → shell rendered blank (“补充资料” with no upload controls)

API/service PASS ≠ page render PASS.

## 2. UI automation architecture

```
run_golden_customer_ui_flow.sh --local
  → miniapp/tests/goldenUiJourney.test.ts
      → Task Home card resolve + tap route
      → request-item / photos / story Page() bootstrap via miniprogramMocks
      → Empty Page Gate (requestItemWorkSurface)
      → test-safe upload completion
      → Task Home Constitution card state re-check
```

Uses the existing Mini Program test mechanism (`Page()` capture + page method calls).
Does not invent completion only in a resolver function.

## 3. Defect reproduction

Permanent tripwire (still FAIL on the legacy shape):

```text
FAIL
Task: insurance_card
Source: system_default
Expected page: insurance upload
Actual page: request-item / blank
Owning layer: Page Bootstrap
Detail: inputMode=evidence nextAction=false showWorkSurface=undefined
```

Repair: `showWorkSurface` / `showFooterCta` from `resolveRequestItemWorkSurface`, bound in `request-item.wxml`.

## 4. Tasks / pages covered

| Task | Source | Page | Assertions |
|---|---|---|---|
| insurance_card | system_default | request-item | route, bootstrap, upload control, no 无需此步骤, upload lifecycle, Task Home completed |
| accident_photos | system_default | photos | tap route, slots render, completion truth |
| accident_story | system_default | story | tap route, saved description renders |
| insurance_card | broker_requested | request-item | nextAction + reason instructions + evidence mode |

## 5. Commands

```bash
# UI journey (local)
bash scripts/run_golden_customer_ui_flow.sh --local

# Service/API journey
bash scripts/run_golden_customer_flow.sh --local

# Packaging
cd miniapp && npm run build:gate
```

## 6. Release gate

```bash
bash scripts/run_claim_release_gate.sh --local   # → READY FOR QA DEPLOY
bash scripts/run_claim_release_gate.sh --qa      # → READY FOR FOUNDER QA (HTTP only)
```

QA UI command:

```bash
P26H_QA_BASE_URL=https://<qa-host> \
UNIFIED_INTAKE_SUPPORT_API_KEY=<key> \
  bash scripts/run_golden_customer_ui_flow.sh --qa
```

Uses ephemeral fixture cases (`demo_name=p26h_ephemeral`) and permanently asserts:

- `system_default` insurance → request-item work surface with `nextAction=null`
- legacy nextAction-only shape → empty-page FAIL
- broker_requested path unchanged
- insurance completion updates Task Home via real fixture evidence contract

Without transport credentials, `--qa` fails closed (Fixture Runner).

## 7. Sample PASS

```text
PASS
Golden UI Journey: 11 assertions
Layers: Task Home, Mini Program Route, Page Bootstrap, Upload State Machine, Constitution Projection
```

## 8. Verdict

**CONDITIONAL GO** — local + inprocess QA UI PASS; emit READY FOR FOUNDER QA only
after deployed HTTP release gate PASS.
