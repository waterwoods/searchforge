# P1 UX Polish — Code Walkthrough V1

**Status:** Teaching note for Founder review (10 minutes)  
**Date:** 2026-08-09  
**Scope:** Three UI/copy polish fixes only — no lifecycle, API, or deploy changes  
**Commit intent:** `fix(ux): polish guided intake trust and broker next action`

---

## 1. What the three UX problems were

1. **Customer AI trust was invisible.** Guided Intake already produced draft state and set `storyAssistNote`, but the note was not rendered. When AI fell back (`used_fallback`), customers had no calm explanation that they could still confirm or fill manually.

2. **Confirm screen had three equal-looking buttons.** `信息正确，提交` competed with `修改` and `重新描述` as full secondary buttons, raising hesitation.

3. **Broker Brief buried `下一步` and overclaimed with `理赔结论`.** Brokers had to scroll past AI layers and fact grids before seeing the next action; the title sounded like a carrier claim conclusion.

---

## 2. Files / functions changed

| Area | Path | What changed |
|------|------|----------------|
| Trust mapper | `miniapp/utils/guidedAccidentStory.ts` | `resolveGuidedTrustNote`, `guidedTrustNote`, `guidedUsedFallback` in `buildGuidedUiState` |
| Start Claim page | `miniapp/pages/start-claim/start-claim.ts` | Sets `storyAssistNote` from `guided.guidedTrustNote` |
| Start Claim UI | `miniapp/pages/start-claim/start-claim.wxml` + `.wxss` | Renders trust note; demotes confirm secondary actions to text links |
| Broker Brief | `ui/src/features/intake/components/ClaimCaseBriefPanel.tsx` | Title `案件摘要`; `下一步` moved early (after accept/ack banners) |
| Copy consistency | `ui/src/features/intake/utils/claimPilotCopy.ts` | `panelSubtitle` wording |
| Tests | `miniapp/tests/guidedAccidentStory.test.ts`, `ClaimCaseBriefPanel.scanOrder.test.ts` | Trust/fallback/CTA/scan order |

---

## 3. What data / state each UI consumes

**Customer**

- Backend proposal field `used_fallback` (boolean) on the Accident Story propose response.
- Mapper → `guidedTrustNote` + `guidedUsedFallback`.
- Page field `storyAssistNote` (same string) rendered in WXML.
- Fallback **never** shows `fallback_reason_category` to the customer.

**Broker**

- Existing Brief fields: `summary`, `next_best_question` / primary status label / `nextAction` prop → `resolvedNext`.
- Accept / supplement-ack banners still use Cap2 primary status gates unchanged.
- AI layers still read `accident_story_assistant` provenance bag.

---

## 4. Why these are UX changes, not business-logic changes

- No new endpoints, schema, flags, or lifecycle commands.
- Confirm still calls the same `onConfirmAndSubmit` → `submitStartClaim`.
- Edit / redescribe still call `onEditFromConfirm` / `onRedescribe`.
- Broker `resolvedNext` computation is unchanged; only layout order and title copy changed.

---

## 5. Fallback flow: backend → UI copy

```
proposeAccidentStory(story)
  → proposal.used_fallback === true | false
  → buildGuidedUiState(proposal, phase)
  → resolveGuidedTrustNote(used_fallback)
       false → 「AI已帮您整理，请确认后再提交。」
       true  → 「AI暂时无法完整整理，您仍可直接确认或手动补充。」
  → storyAssistNote / guidedTrustNote rendered in Start Claim
```

If propose returns null, Start Claim forces `manual_all` and uses the same fallback trust line — intake remains usable.

---

## 6. Primary / secondary CTA hierarchy

- **One** `btn-primary` in the confirm block: `信息正确，提交` → `onConfirmAndSubmit`.
- `修改` / `重新描述` are `guided-confirm-link` text actions (underlined, muted), not `btn-secondary` peers.
- Tap targets kept via padding / min-height on the link row.

---

## 7. Broker next action — already existed, only repositioned

`resolvedNext` was already computed from `nextAction` prop, primary status label, or `brief.next_best_question`.  
It now renders immediately after summary / policy chip / accept-ack banners, **before** AI layers and the fact grid (`data-testid="claim-brief-next-action"`).

---

## 8. Exact 10-minute Founder reading order

### 0–3 min — customer guided / fallback rendering

1. Open `miniapp/utils/guidedAccidentStory.ts` — jump to `GUIDED_TRUST_NOTE_*` and `resolveGuidedTrustNote`.
2. Skim `buildGuidedUiState` return fields `guidedTrustNote` / `guidedUsedFallback`.
3. Open `miniapp/pages/start-claim/start-claim.wxml` — search `guided-trust-note` and `storyAssistNote`.

### 3–6 min — confirm CTA hierarchy

1. Same WXML file — search `guidedShowConfirm`.
2. Confirm: one `btn-primary` + `guided-confirm-secondary` with two links.
3. Optional: `miniapp/pages/start-claim/start-claim.wxss` classes `guided-confirm-link`.

### 6–10 min — Broker Brief title / next action

1. Open `ui/src/features/intake/components/ClaimCaseBriefPanel.tsx`.
2. Confirm card title `案件摘要`.
3. Search `claim-brief-next-action` — verify it sits after accept/ack banners and before `accident-story-assistant-layers`.

**Do not** read entire files; **do not** require Founder phone QA for this polish.

---

*Unrelated local note (not in this commit): working tree may still contain an accidental mass edit in `services/fiqa_api/inbox_triage/triage.py` — preserve / revert separately.*
