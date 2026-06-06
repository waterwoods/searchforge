# Add-Car Progress / Handoff / Closure Spec

## States (customer mental model)

| Phase | Customer should think |
|-------|----------------------|
| Collecting | “Office is still gathering what they need for this quote.” |
| Quote-ready / almost | “Enough for pricing path; office still may verify.” |
| Handoff (`handoff_ready`) | “This request is **with the office** now; I should not treat this as back-and-forth with a bot.” |

## Progress (pre-handoff)

- Keep existing structured tags (已收集 / 还需 / 报价状态).  
- **Card title** encodes transaction: `加车报价 · 进度`.  
- Internal tags like `可保存` are broker-oriented; customer progress card should not emphasize “save” — prefer **信息收集中** vs collection stage tags already shown on bubbles.

## Handoff / closure (post-handoff)

When `handoff_ready`:

1. **Closure headline** (above system reply): e.g. **本请求已提交办公室处理** (Add-Car variant configurable).  
2. **System reply** (existing `client_reply_draft`): office-realistic next steps.  
3. **Processing line**: e.g. office continues this add-car quote; no need to resubmit.  
4. **Boundary hint**: other topics → **提交新问题**.  
5. **Actions**: 查看工作台 / 提交新问题 (unchanged intent, clearer framing).

## Config keys

| Key | Purpose |
|-----|---------|
| `handoff_closure_headline_add_car` | Headline when Add-Car handoff |
| `handoff_closure_headline_generic` | Headline for other flows |
| `handoff_closure_processing_add_car` | Second line under reply |
| `handoff_case_created_line` | When `case_id` present |
| `handoff_case_pending_line` | When no case id yet |
| `handoff_new_issue_hint` | New-request boundary |
| `add_car_handoff_toast` | Toast on successful add-car handoff |

## Backend alignment

`handoff_phrases.json` → `add_car.zh` should reinforce **submitted to office / 办公室处理**, not only “资料好了”.
