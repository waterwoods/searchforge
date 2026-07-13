# Evidence — P20 Post-Submit Customer Supplement Backend Hotfix (2026-07-13)

| Field | Value |
|---|---|
| Severity | **High** |
| Problem | Frontend允许 submitted 后进入 Story/Basics/Photos 补充，但 backend `PATCH /fields` 返回 `409 already_submitted` |
| Policy Decision | 保留 formal submit 一次性与幂等；在已 submitted 场景对现有 PATCH 仅开放严格客户字段白名单 |
| Scope | H5 intake PATCH path + focused tests/docs |
| Backend / Schema | Backend changed; **no schema migration** |

---

## Root Cause

- `patch_intake_fields()` 在检测 `_is_submitted(case)` 后直接抛 `already_submitted`，导致所有 submitted 后字段 PATCH 被拒绝。
- 前端补充路由已修复，形成前后端产品能力错位。

## Implemented Backend Policy

- **Pre-submit**：PATCH 行为保持不变。
- **Post-submit**：
  - 仅允许当前客户可编辑字段（按 step 白名单）；
  - 非白名单字段拒绝（`post_submit_field_not_allowed`）；
  - 接受后写入 facts + provenance + timeline supplement 事件；
  - submitted 状态不回滚、不重开提交流程。

## Allowed Fields (post-submit via existing PATCH)

- `injury`: `anyone_injured`, `injury_status`
- `time_location`: `accident_datetime`, `accident_location`
- `story`: `accident_description`
- `vehicle_other_party`: `own_vehicle_info`, `other_party_plate`, `other_party_info`, `police_involved`, `police_reported`

## Prohibited Fields

- 任意不在上述白名单内字段（例如 `claim_phase`, `tenant/client ownership`, `case_id`, `submit timestamps`, provenance internals 等）通过 PATCH 注入将被拒绝。

## Provenance Behavior

- Post-submit accepted patch 使用 `source=customer_confirmed`、`status=customer_supplement` 写入 `known_fact_provenance`。
- 维持 Track B 优先级保护：低优先来源（如 wecom text/AI）不能静默覆盖 customer supplement。

## Timeline / Audit Behavior

- Post-submit PATCH 记录 `h5_post_submit_supplement` 事件。
- 事件 metadata 包含：
  - `step`
  - `fields`
  - `post_submit=true`
  - `submitted_at`
  - `changes`（before/after delta，仅记录变化字段）
- 因而 Broker 可区分：原提交值、后续补充、当前生效值。

## Submit Semantics

- Duplicate formal submit 逻辑保持原样（idempotent / already_submitted）。
- submitted 状态保持 submitted，不触发二次 formal submit。

## Tests

- `PYTHONPATH=. python3 -m pytest tests/test_h5_claim_intake_form.py -q` → **20 passed**
- `PYTHONPATH=. python3 -m pytest tests/test_p20_track_b_backend_foundation.py -q` → **6 passed**
- `PYTHONPATH=. python3 -m pytest tests/test_p19m1_mini_program_logic.py -q` → **23 passed**
- `cd miniapp && npm test` → **114/114 passed**

新增/更新聚焦覆盖点：

- post-submit Story supplement accepted + provenance/timeline delta + submitted unchanged
- post-submit Basics(police) supplement accepted + missing_items 刷新
- post-submit non-editable field rejected
- duplicate formal submit still idempotent
- wecom/AI overwrite guard remains effective after supplement

## Schema Migration

- **Not required**（使用既有 `known_fact_provenance` / `claim_timeline` / `h5_intake_state` JSON 结构与 helper）。

## Rollback Note

- 可直接回滚 `h5_task_intake.py` 相关改动到 guard-only 版本；将恢复 submitted PATCH 全拒绝的旧行为。

## Manual Verification

- **Required (not auto-PASS):**
  - submitted 任务进入 Basics 编辑并保存成功
  - 返回 Task Home/Review 缺失项消失
  - 任务仍为 submitted
  - 无第二次 formal submit
  - Broker/workbench 可见 supplement 事件与 before/after

