## Post-deploy visibility requirements

After deployment (or confirmation that the existing deployment is already current), the **Unified Intake → 场景仿真 (Simulation)** tab on the demo-facing frontend must show:

- **Role C as a distinct scenario card**
  - Labelled as a controlled-LLM Add-Car customer (manual stepping).
  - Retains persona / difficulty / max-turn knobs.
- **Role C Plus as its own visible scenario entry/card**
  - Clearly separate from Role C in the scenario list.
  - Text makes “一键多轮” / “一键跑完” semantics clear.
  - Uses the same backend Role C + triage stack, but surfaced as a lightweight auto-run path.
- **Calmer, low-eye-strain Simulation layout**
  - Scenario list in the left column with clear tags and hierarchy.
  - Middle column shows the replay thread with softer background, clearer bubble labels.
  - Right column remains the record-first Add-Car summary panel (状态 / 还缺什么 / 下一步 / 服务记录编号).
  - A full-width **Role C / C Plus 逐轮快照与结束报告** card appears under the main row when Role C lane is active.

## Preview verification checklist

Use whatever combination of live-browser inspection and bundle/API checks is practical. Mark each as one of: ✅ verified directly, (i) inferred, or ☐ not verified.

1. **Demo URL loads**
   - `https://ui-smoky-beta.vercel.app/` returns the lab dashboard landing.
   - `https://ui-smoky-beta.vercel.app/workbench/unified-intake` loads Unified Intake without error.
2. **Simulation tab reachable**
   - Tab strip includes **场景仿真**.
   - Direct URL `.../workbench/unified-intake?tab=simulation` loads without error.
3. **Role visibility**
   - Role C scenario card is present in the scenario list and selectable.
   - Role C Plus scenario card or sub-block is present, visibly distinct from Role C (e.g. title “Role C Plus · 一键多轮” or equivalent).
   - Selecting Role C still leaves Role C (manual) usable; Role C Plus does not replace it.
4. **Layout + readability**
   - Simulation hero card and copy at top remain legible and not cluttered.
   - Scenario list uses tags (角色、risk level) and card styling to make choices scannable.
   - Replay thread uses differentiated background colors and labels for 客户 vs 系统整理 bubbles.
   - Right-hand record panel shows service record id, current status, and next step with clear headings and tags.
   - Role C Plus snapshot / end-report block appears in a dedicated card with clear heading and muted background, not mixed randomly into the thread.
5. **Backend wiring sanity (read-only)**
   - Unified Intake page uses the same production API base as in prior deploy sprint (`VITE_API_BASE_URL` baked against Cloud Run).
   - No obvious “API unavailable” or CORS errors on initial page load.

## Acceptance criteria

This sprint is accepted when:

- **Visibility**
  - Role C and Role C Plus are both visible as separate entries/cards on the live Simulation tab of the demo-facing URL.
  - Original Role C behavior remains available and obviously not removed.
- **Readability / hierarchy**
  - The Simulation page presents:
    - A calm hero explanation section;
    - A left-column scenario list with clear card hierarchy;
    - A middle replay thread with clear role labeling;
    - A right record-first state panel;
    - A distinct Role C / C Plus snapshot + end-report section.
- **Deployment clarity**
  - There is an explicit note in the final report stating:
    - whether **a new frontend deploy** actually occurred in this sprint, and
    - which URL and alias Andy should open.
- **Founder-ready**
  - The final report cleanly separates:
    - items **verified directly** on the live URL;
    - items **inferred** from code and prior deploy sprints;
    - items **not yet verified** and called out as needing founder eyeball judgment.

