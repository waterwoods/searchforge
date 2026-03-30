# ADD-CAR STATE PARITY + WORKBENCH RECORD IDENTITY — Blueprint

## Sprint goal

Strengthen Add-Car industrial continuity by aligning **record identity** and **lifecycle/state language** between the customer entry closure surface and the **office workbench** (queue + open case), without redesigning the engine or broadening product scope.

## Why now

`PROJECT_TRUTH_SWITCH.md` and **Add-Car Industrial Scorecard V1** both flag **STATE** and **office-side parity** as the main remaining trust gap after PAGE and handoff copy improvements: the customer sees a strong **服务记录编号** and status strip, while the workbench queue historically emphasized operational tags without the same **visible case id** or **aligned lifecycle wording**.

## Scorecard basis

- Source: `docs/sprints/ADD_CAR_INDUSTRIAL_SCORECARD_V1_SPRINT/02_ADD_CAR_INDUSTRIAL_SCORECARD_V1.md`
- Prior STATE score: **3 / 5** — progress card + `AddCarCaseStatusStrip` on customer side; **workbench queue parity for record id / status** called out as thinner.
- This sprint executes the scorecard **runner-up**: workbench state/record parity, scoped to low-risk UI + client copy.

## Scope

- Add-Car / unified intake **record id visibility** on workbench queue cards and opened case header.
- **Lifecycle status tag parity** with customer-side `LIFECYCLE_STATUS_LABELS` (same Chinese labels and colors where applicable).
- Client-pack strings for workbench CTA and case-id hint (`configs/clients/chen_kui/ui_copy.json` + `DEFAULT_UI_COPY`).
- Lightweight sprint documentation (this folder only).

## Non-scope

- Full page redesign, workflow engine rewrite, new backend state machine.
- Non–Add-Car expansion, auth, CRM, billing.
- Full `AddCarCaseStatusStrip` clone on every queue row (would add noise and layout risk in one pass).

## Target outcome

A broker can scan the **服务记录队列**, see the **same monospace copyable id** the customer saw after handoff, open a row with language that reads **“本条服务记录”**, and see the **same lifecycle vocabulary** (e.g. 已交办公室 vs legacy 已移交) as the customer status strip.
