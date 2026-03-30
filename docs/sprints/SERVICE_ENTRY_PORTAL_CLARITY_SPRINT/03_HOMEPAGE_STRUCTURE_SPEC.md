# Homepage / front-end structure spec (Unified Intake)

## Page shell (main `UnifiedIntakePage`)

1. **Branded identity header** (white card)  
   - Avatar + **金盾保险 · 陈魁团队**  
   - Subtitle: `portal_brand_tagline` (e.g. 汽车保险 · 客户统一受理与报送入口)

2. **Pilot / product boundary alert** (collapsible)  
   - Portal-oriented copy: 报送 → 业务记录 → 办公室确认后再对外联系.

3. **Tabs**  
   - Customer: `portal_tab_customer_label` + suffix  
   - Broker: existing office workbench label

## Customer entry tab (`CustomerEntryTab`)

4. **Trust / service hero card**  
   - Title: `portal_hero_title`  
   - Body: `portal_service_tagline` (single authoritative explanation)

5. **Add-car transaction ribbon** (when active)  
   - Unchanged structure; copy from existing add-car keys

6. **Empty-state entry card** (when no turns)  
   - Headline: `portal_empty_headline`  
   - Secondary: `portal_empty_secondary`  
   - **办理类型** grid: `portal_choose_path_label` + quick-start buttons  
   - Optional structured add-car block: `portal_add_car_quick_*`

7. **When conversation exists**  
   - **Section label**: `portal_thread_heading`  
   - **Thread card**: bubbles with portal role labels  
   - **Progress card** (pre-handoff): add-car title or `portal_generic_progress_title` + `portal_progress_annotation`  
   - **Input card**: transaction chips + textarea + **提交报送** / **提交补充**  
   - **Handoff closure card**: unchanged layout; summary label uses `portal_closure_reply_summary_label`

## Why this order

Matches how a real **受理台** works: **who → what this desk does → pick lane → see file building up → submit more → closed case + next step**.
