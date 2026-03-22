# Add-Car Customer UX Options Spec

## Options compared (Loop 1)

### Option A — Stronger closure card only

Expand the green closure card with all sections inline: headline, summary tags, office next step, timing, reply digest.

- **Pros:** Single focal card; simple mental model.
- **Cons:** Dense; reply digest competes visually with confirmation tags.

### Option B — Confirmation summary + office banner (chosen)

Structured **“系统记录到的要点”** block + distinct **office timing / processing** banner + existing **办公室回复摘要**.

- **Pros:** Clear separation—*what we recorded* vs *what happens next* vs *what we said*; matches “formal intake” metaphor; low implementation risk (reuse triage payload already on last turn).
- **Cons:** Slightly taller card on mobile.

### Option C — Explicit staged progression (stepper)

Three labeled stages: 请求已提交 → 信息已记录 → 办公室处理中.

- **Pros:** Very explicit progression.
- **Cons:** More UI chrome; risk of feeling gimmicky or enterprise-heavy; extra state sync if stages ever drift from backend.

## Decision

**Option B** — Best balance of clarity, commercial seriousness, and **low risk** (no new backend state machine). Option A’s density would hurt scanning; Option C adds chrome without new truth from the server.
