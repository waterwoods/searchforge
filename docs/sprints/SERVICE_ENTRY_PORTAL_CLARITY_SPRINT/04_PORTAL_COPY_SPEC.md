# Portal copy hierarchy spec

## Config sources

- **TypeScript defaults**: `ui/src/api/clientConfig.ts` → `DEFAULT_UI_COPY`
- **Client override**: `configs/clients/<id>/ui_copy.json` (API whitelist in `config_loader.py`)

## Group A — Brand strip (main page)

| Key | Role |
|-----|------|
| `portal_brand_tagline` | Subtitle under broker name; anchors “受理/报送” not “聊天”. |

## Group B — Customer hero

| Key | Role |
|-----|------|
| `portal_hero_title` | H1-level title inside customer card |
| `portal_service_tagline` | Single paragraph: 报送 → 记录 → 办公室办理与跟进 |

## Group C — First screen / entry

| Key | Role |
|-----|------|
| `portal_empty_headline` | What to do first |
| `portal_empty_secondary` | Human path hint (联系人工) |
| `portal_choose_path_label` | Label above intent buttons |
| Quick-start `quick_start_buttons.*.label` | e.g. **办理加车报价** |

## Group D — Thread + input

| Key | Role |
|-----|------|
| `portal_thread_heading` | Section title above message list |
| `portal_customer_bubble_label` | Left/right bubble header for customer |
| `portal_office_bubble_label` | Bubble header for system/office side |
| `portal_loading_status` | Loading line |
| `portal_input_placeholder_empty` | Empty-state textarea |
| `portal_input_placeholder_continue` | Continue-state textarea |
| Primary button (first turn): **提交报送**; add-car: `customer_entry_submit_add_car` |
| `portal_submit_followup` | After first turn |

## Group E — Progress annotation

| Key | Role |
|-----|------|
| `portal_generic_progress_title` | Non–add-car progress card title |
| `portal_progress_annotation` | Short note in title row (replaces “实时更新” tone) |

## Group F — Closure / record

| Key | Role |
|-----|------|
| `handoff_*` (existing) | Headlines, case lines, same-request panel |
| `portal_closure_reply_summary_label` | Label above final draft text (**办公室办理摘要**) |
| `portal_session_restored_toast` | Persistence toast |

## Group G — Navigation chrome

| Key | Role |
|-----|------|
| `portal_tab_customer_label` | Tab text |
| `portal_tab_customer_suffix` | Tab qualifier |
| `app_title` | App shell title (portal-style default) |

## Wording rules

- **Prefer**: 报送、办理、记录、跟进、当前办理、办公室、提交、受理.  
- **Avoid overusing**: AI、聊天、对话、助手.  
- **English** in customer UI: minimize (e.g. keep internal tags only where already present).

## One-page summary

See `COPY_HIERARCHY_ONE_PAGER.md`.
