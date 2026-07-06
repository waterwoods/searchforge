# P18.11 — Environment Strategy & Development Rules

**Date:** 2026-07-05  
**Type:** 环境策略 + 开发规则 — **不写代码、不部署**  
**Audience:** Andy、工程、Cursor / OpenClaw agents  
**Authority:** 本文是 **local / QA / GCP / production 边界** 的 canonical rules；不 supersede B0 Contract、ADR-001–005、P18.7 行为 spec，但 **优先于** 任何 loop 内的临时假设。

**Prerequisite:** P18.10 Loop 0 · `docs/runbooks/CHEN_KUI_DEMO_ENVIRONMENT.md` · `docs/CURRENT_PRODUCT_SHAPE.md`

**Purpose:** 把 2026-07-05 确认的环境策略写成 **未来每个开发 loop 必须遵守的规则**，避免 local / QA / GCP / production 混用导致数据丢失、验收无效、WeCom live path 被破坏。

---

## 1. 一句话原则

> **Local 只辅助开发；正式验收与 demo 必须在 GCP QA 上完成。**  
> **Postgres（Cloud SQL）是唯一持久化真相；local JSON 是 dev-only 兼容路径。**  
> **Seed / reset 只碰 demo-tagged records；绝不删真实数据。**

---

## 2. Cloud-first QA 原则

### 2.1 定义

| 层级 | 含义 |
|------|------|
| **Local** | 工程师 laptop：`localhost:5173` + `127.0.0.1:8001`；可选 `data/unified_intake_cases.json` |
| **GCP QA** | Vercel QA UI + Cloud Run API + Postgres（Cloud SQL / Neon 对齐路径） |
| **Production** | 同一技术栈，但承载真实 broker 数据与 live WeCom traffic |

### 2.2 规则

| # | 规则 |
|---|------|
| 1 | **Local 只能做开发辅助**：快速改 UI、跑 unit test、debug 单函数、本地 screen sketch |
| 2 | **正式验收必须在 GCP QA**：Loop 完成报告中的「验收通过」必须以 QA Workbench + Cloud Run API + Cloud SQL 上的结果为准 |
| 3 | **Local 通过 ≠ sprint 通过**：local 8001 green 只代表「代码可能没问题」，不代表 demo-ready |
| 4 | **Demo rehearsal 在 QA**：陈总 demo、broker 30 秒测试、Must-have checklist 均在 QA URL 执行 |
| 5 | **Local fallback 仅限 engineering recovery**：Cloud Run 503 时用 `restore_8001_readiness.sh` 继续 coding — **不是** demo path |

### 2.3 Local 允许 vs 禁止

| ✅ Local 允许 | ❌ Local 禁止 |
|--------------|--------------|
| 改 TSX / Python 并 hot reload | 以 local JSON 结果作为 loop 最终验收 |
| 跑 `pytest` / `test_wecom_slice.py` | 在 local seed 后声称「demo cases 已就绪」而不做 cloud seed |
| 读 Cloud SQL 做 inspect（只读） | 混用 local JSON 与 Cloud SQL 作为同一 case 的 truth |
| `seed_chen_kui_demo.py --target local` 做 layout sketch | 用 local Workbench 给 broker / 陈总演示 |

---

## 3. Dev / QA / Prod 隔离原则

### 3.1 三环境对照

| 维度 | **Dev (local)** | **QA (GCP)** | **Prod** |
|------|-----------------|--------------|----------|
| **UI** | `localhost:5173` | `https://ui-smoky-beta.vercel.app` | 未来 paid pilot URL（待定） |
| **API** | `127.0.0.1:8001` | `https://fiqa-api-g7zatxrycq-uw.a.run.app` | 独立 Cloud Run service / revision |
| **DB** | JSON file 或 laptop Postgres（inspect） | Cloud SQL / Neon via `SERVICE_RECORD_DATABASE_URL` | 独立 DB instance；**禁止**与 QA 共用 |
| **WeCom** | 不连 live callback | Live callback → Cloud Run（Q0.11.1）；drain 可控 | Live traffic；**禁止** demo reset 操作 |
| **Seed / reset** | `--target local` | `--target cloud` / `--cloud` | **禁止** automated seed/reset |
| **验收权重** | 0（辅助） | **100%（正式）** | N/A（非 demo sprint 范围） |

### 3.2 隔离规则

| # | 规则 |
|---|------|
| 1 | **Dev 写入不得 assumed 为 QA 可见**：local JSON seed 不会出现在 Vercel Workbench |
| 2 | **QA 写入必须显式**：`seed_chen_kui_demo.py --target cloud` 或 API 经 Cloud Run |
| 3 | **Prod 与 QA DB 分离**：即使同为 Postgres，不得共用 `SERVICE_RECORD_DATABASE_URL` |
| 4 | **Env flags 不混用**：Cloud Run Secret Manager 中的 DB URL、queue flags、API keys 与 local `.env` 是不同配置面；改 local `.env` 不影响 Cloud Run |
| 5 | **Deploy 不默认发生**：每个 loop 默认 **不 deploy**；deploy 是显式 operator 动作，不是 Cursor loop 的隐含步骤 |
| 6 | **Readiness 语义分离**：local `DEMO_MODE` 放松 `/readyz`；QA/prod 必须 `UNIFIED_INTAKE_INTAKE_CORE_READINESS=1` + PG-primary flags（见 `CURRENT_PRODUCT_SHAPE.md`） |

### 3.3 配置真相源

| 配置 | 真相源 |
|------|--------|
| QA API → DB | Cloud Run Secret Manager `SERVICE_RECORD_DATABASE_URL` |
| QA UI → API | Vercel env `VITE_API_BASE_URL`（build-time bake） |
| Local API → DB | `.env` 或 `.env.cloudrun`（**仅当 intentionally 指向 QA DB 做 inspect**） |
| Demo seed/reset | `scripts/seed_chen_kui_demo.py` / `scripts/reset_chen_kui_demo.sh` |
| 环境 sanity check | `scripts/check_chen_kui_demo_environment.sh [--cloud-api]` |

---

## 4. 陈总 Demo 主环境原则

### 4.1 Authoritative demo stack

陈总 demo、broker rehearsal、Loop 正式验收 **必须** 使用以下组合：

```
┌─────────────────────────────────────────────────────────────┐
│  QA UI (Vercel)                                              │
│  https://ui-smoky-beta.vercel.app/workbench/unified-intake   │
│  Customer entry: /add-car                                    │
├─────────────────────────────────────────────────────────────┤
│  GCP Cloud Run API                                           │
│  https://fiqa-api-g7zatxrycq-uw.a.run.app                    │
├─────────────────────────────────────────────────────────────┤
│  GCP Cloud SQL / Postgres                                    │
│  SERVICE_RECORD_DATABASE_URL (Secret Manager on Cloud Run)   │
├─────────────────────────────────────────────────────────────┤
│  WeCom live path (Path B)                                    │
│  WeCom KF → Cloud Run /api/wecom/kf/callback → inbox/outbox  │
│  → drain → case rows in Postgres                             │
└─────────────────────────────────────────────────────────────┘
```

**Local is not the demo path.**

### 4.2 两条 demo path

| Path | 用途 | 入口 | 数据 |
|------|------|------|------|
| **Path A — Seed-backed Workbench** | Loop 1 screen-proof；live 失败 fallback | QA Workbench URL | `seed_chen_kui_demo.py --target cloud` |
| **Path B — WeCom live** | Loop 2–3 live lane 验收 | WeCom KF 消息 | Cloud Run callback → Postgres |

Path A 与 Path B 可共存：seed rows 带 `workbench_test=true`，live cases 无此 tag。

### 4.3 Demo 前必做

```bash
# 1. Cloud seed
PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target cloud

# 2. 环境 sanity
bash scripts/check_chen_kui_demo_environment.sh --cloud-api

# 3. 打开 QA Workbench 目视确认 5 cases
# https://ui-smoky-beta.vercel.app/workbench/unified-intake
```

### 4.4 已知对齐风险（必须知晓）

1. **Cloud Run DB ≠ laptop Postgres**：API `total_count=0` 但 laptop 有数据 → Secret Manager 指向不同 DB → 对齐后 re-seed  
2. **Office ownership**：`UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP=1` 时需匹配 `X-Org-Id`；seed cases 用 `client_id=chen_kui`  
3. **Vercel API key**：browser 需 build-time `VITE_UNIFIED_INTAKE_INTAKE_API_KEY`

---

## 5. Seed / Reset 安全原则

### 5.1 Demo 数据标记（强制）

所有 demo seed 创建的 case **必须** 携带：

| 字段 | 值 | 位置 |
|------|-----|------|
| `demo_name` | `chen_kui_p18` | `extra.demo_name` 或 `demo_flags.demo_name` |
| `workbench_test` | `true` | `extra.workbench_test` |

**未标记 demo 的数据 = 真实数据。** Reset 脚本不得触碰未标记 rows。

### 5.2 Reset 安全保证

| # | 保证 |
|---|------|
| 1 | **只删 demo-tagged rows**：`demo_name=chen_kui_p18` AND `workbench_test=true` |
| 2 | **禁止** `TRUNCATE service_records` 或无 WHERE 的 DELETE |
| 3 | **禁止** reset `sync_cursor` / WeCom queue state（demo rehearsal 不应影响 live dedup） |
| 4 | **Fail closed**：`--target cloud` 时若无 `SERVICE_RECORD_DATABASE_URL` → 脚本必须 abort |
| 5 | **Dry-run 优先**：`--dry-run` 确认将删除的 row count 后再执行 |
| 6 | **Local reset 不影响 Cloud**：`reset_chen_kui_demo.sh`（无 `--cloud`）只清 local JSON |

### 5.3 命令对照

| 操作 | Local (dev) | QA/GCP (正式) |
|------|-------------|---------------|
| Seed | `python3 scripts/seed_chen_kui_demo.py` | `python3 scripts/seed_chen_kui_demo.py --target cloud` |
| Reset | `bash scripts/reset_chen_kui_demo.sh --reseed` | `bash scripts/reset_chen_kui_demo.sh --cloud --reseed` |
| 安全检查 | 目视 JSON 文件 | `check_chen_kui_demo_environment.sh --cloud-api` |

---

## 6. Modular Architecture 原则

实现时必须保持模块边界清晰。**不要把 WeCom / GCP / OCR / LLM 逻辑写死进核心 Case logic。**

```
┌─────────────────────────────────────────────────────────────┐
│  Channel Adapter                                             │
│  WeCom / Web / future SMS                                    │
│  → ingress, egress, dedup, reply templates                   │
├─────────────────────────────────────────────────────────────┤
│  Raw Event / Message Layer                                   │
│  record_messages / inbox events / evidence_events / timeline │
│  → append-only; 不被 summary 覆盖                            │
├─────────────────────────────────────────────────────────────┤
│  Case Engine                                                 │
│  case type, known facts, missing fields, risk flags, status  │
│  → 业务逻辑核心；不依赖特定 channel                          │
├─────────────────────────────────────────────────────────────┤
│  Extraction Layer (optional)                                 │
│  rules / OCR / LLM — replaceable                             │
│  → demo: rules only; OCR/LLM 不 wired 进 WeCom path          │
├─────────────────────────────────────────────────────────────┤
│  Workbench View                                              │
│  display-only view model, not business logic core            │
│  → 读 case JSON；不做 carrier/quote 决策                     │
├─────────────────────────────────────────────────────────────┤
│  Broker Action                                               │
│  Confirm / Manual Handle / Done                              │
│  → 唯一可改变 case 终态的人类门控                            │
└─────────────────────────────────────────────────────────────┘
```

### 6.1 层间规则

| # | 规则 |
|---|------|
| 1 | **Channel Adapter** 只做 ingress/egress；case 创建/merge 委托 Case Engine |
| 2 | **Raw Event** append-only；summary 是解释层，不覆盖 raw message |
| 3 | **Case Engine** 不 import WeCom SDK / Vercel / GCS |
| 4 | **Workbench View** 只读 API；不做业务决策 |
| 5 | **Broker Action** 是唯一 human gate；AI 不可 skip Confirm |
| 6 | **Extraction Layer** demo 阶段 rules-only；新 extraction 策略不得破坏 Case Engine 接口 |

### 6.2 关键文件归属

| 层 | 关键文件 |
|----|----------|
| Channel Adapter | `wecom/slice.py`, `reply.py`, `send_msg.py` |
| Raw Event | `record_messages`, `evidence_events` |
| Case Engine | `case_store.py`, `active_case_bridge.py` |
| Extraction | `intent.py`, `identity.py` |
| Workbench View | `BrokerWorkbenchTab.tsx` |
| Broker Action | `PATCH /cases/{id}/confirm` |

---

## 7. Cursor Development Rule（每个 Loop 必遵）

**以后每个 loop — 无论 Cursor、OpenClaw 还是人工 — 在写第一行代码前和完成报告时，必须明确回答以下四项：**

| # | 问题 | 必须说明 |
|---|------|----------|
| 1 | **使用哪个环境？** | `local` / `QA (Vercel + Cloud Run + Cloud SQL)` / 仅 unit test 无 runtime |
| 2 | **数据写到哪里？** | local JSON / Cloud SQL via seed script / Cloud SQL via live WeCom / 无写入（read-only） |
| 3 | **是否影响 Cloud SQL？** | `YES — seed N rows` / `YES — live WeCom may create rows` / `NO — UI-only` / `NO — local JSON only` |
| 4 | **是否影响 WeCom live path？** | `YES — touches slice.py / callback / drain` / `NO — Workbench or seed only` |

### 7.1 Loop 开始声明模板

每个 loop 开始时，agent 必须在回复 **开头** 写入：

```markdown
## Loop N Environment Declaration

- **Environment:** [local | QA | local+QA | test-only]
- **Data target:** [none | local JSON | Cloud SQL seed | Cloud SQL live]
- **Cloud SQL impact:** [none | seed/demo-tagged only | potential live writes]
- **WeCom live path impact:** [none | read-only inspect | code change — list files]
```

### 7.2 Loop 完成报告追加项

在 P18.10 §8 报告格式基础上，**追加**：

```markdown
### Environment & data summary
- **Verified on QA:** [YES/NO — URL or reason]
- **Cloud seed/reset run:** [commands + row counts]
- **WeCom live tested:** [YES/NO/N/A]
- **Any prod / non-demo data touched:** [NONE — required]
```

### 7.3 默认 Loop 环境矩阵（P18 sprint）

| Loop | 开发环境 | 正式验收环境 | Cloud SQL | WeCom live |
|------|----------|--------------|-----------|------------|
| Loop 1 | Local + QA | **QA Workbench** | seed `--target cloud` | **NO** |
| Loop 2 | Local + QA | **QA + WeCom live** | seed + live writes | **YES** |
| Loop 3 | Local + QA | **QA + WeCom live** | seed + live writes | **YES** |
| Loop 4 | QA | **QA** | reset + reseed | optional rehearsal |

---

## 8. 明确禁止（Hard No）

以下行为 **一律禁止**，无例外：

| # | 禁止项 | 原因 |
|---|--------|------|
| 1 | **Local-only acceptance** — 只在 local 8001 验收就报 loop 完成 | QA 才是正式环境；local 与 QA 数据路径不同 |
| 2 | **混用 local JSON 和 Cloud SQL** — 同一 case 在两个 truth source 间切换 | 双写/双读导致 phantom cases 与验收假象 |
| 3 | **不标记 demo data** — seed case 缺少 `demo_name` + `workbench_test` | reset 无法安全区分 demo vs 真实 |
| 4 | **直接清 production tables** — `TRUNCATE`、无 WHERE 的 DELETE、`DROP` | 不可逆数据丢失 |
| 5 | **Reset sync_cursor / WeCom queue for demo** | 破坏 live dedup；影响非 demo 消息 |
| 6 | **Demo day deploy / 现场改 Cloud Run env** | 不可控；P18.9 / P18.10 红线 |
| 7 | **Local Workbench 给 broker / 陈总演示** | 非 authoritative demo path |
| 8 | **假设 local `.env` 变更会同步到 Cloud Run** | 配置面隔离；必须 explicit deploy |
| 9 | **Loop 内 implicit deploy** — 改代码后未经 operator 确认就 deploy | deploy 是显式动作 |
| 10 | **Schema migration on Cloud SQL live** | P18 sprint 零 migration 策略 |

---

## 9. 与其他文档关系

```
CURRENT_PRODUCT_SHAPE.md     — 持久化 truth + pilot flags
CHEN_KUI_DEMO_ENVIRONMENT.md — Demo URL + seed/reset 命令（operational）
P18.10 Loop 0               — Sprint loop 顺序 + 红线
P18.11 本文                  — 环境策略 + 开发规则（canonical rules）
```

| 文档 | P18.11 关系 |
|------|-------------|
| `CURRENT_PRODUCT_SHAPE.md` | PG-primary / JSON dev-only — 本文 §2–3 的操作化 |
| `CHEN_KUI_DEMO_ENVIRONMENT.md` | Demo URL 与命令 — 本文 §4–5 引用，不重复 |
| `P18.10` | Loop 顺序 — 本文 §7.3 追加环境矩阵 |
| `RUNTIME_PATH_STANDARD.md` | Local port 8001 — 本文 §2 明确其为 dev-only |
| `wecom_q0_cloud_run_network_decision.md` | Cloud Run + Cloud SQL 网络 — prod/QA 部署约束 |

---

## 10. Loop 开始前 Checklist（复制使用）

**每次 Loop 开始前，复制以下 checklist 到 issue / Cursor chat / 报告顶部，逐项填写。**

```markdown
# Loop Environment Checklist — Loop ___ : _______________

**Date:** ___________
**Operator / Agent:**

## A. 环境声明（必填，开工前）

- [ ] 本 loop **正式验收环境** 已确认：☐ QA (Vercel + Cloud Run + Cloud SQL)  ☐ 仅 local dev  ☐ test-only
- [ ] **Environment:** _______________________
- [ ] **Data target:** _______________________
- [ ] **Cloud SQL impact:** _______________________
- [ ] **WeCom live path impact:** _______________________

## B. 开工前读取

- [ ] 已读 `docs/p18_11_environment_strategy_and_dev_rules.md`
- [ ] 已读 `docs/runbooks/CHEN_KUI_DEMO_ENVIRONMENT.md`
- [ ] 已读本 loop 对应 P18.10 §2 边界（允许/禁止/验收标准）

## C. QA 环境 sanity（正式验收 loop 必填）

- [ ] `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` → PASS
- [ ] Cloud Run API 可达：`https://fiqa-api-g7zatxrycq-uw.a.run.app/readyz`
- [ ] QA Workbench 可达：`https://ui-smoky-beta.vercel.app/workbench/unified-intake`
- [ ] Cloud Run `SERVICE_RECORD_DATABASE_URL` 与 seed 目标 DB 一致（非空、非错库）

## D. Seed / reset（若本 loop 需要 demo data）

- [ ] Seed 使用 `--target cloud`（非 local-only 验收）
- [ ] 所有 seed cases 含 `demo_name=chen_kui_p18` + `workbench_test=true`
- [ ] Reset（若有）使用 `--cloud` 且 **仅** demo-tagged rows
- [ ] 未执行 `TRUNCATE` / 无 WHERE DELETE / 未 reset `sync_cursor`

## E. 禁止项确认

- [ ] 本 loop **不会** 以 local-only 作为最终验收
- [ ] 本 loop **不会** 混用 local JSON 与 Cloud SQL 作为同一 truth
- [ ] 本 loop **不会** 不标记 demo data
- [ ] 本 loop **不会** 清 production tables 或非 demo rows
- [ ] 本 loop **不会** 未经确认 deploy / 改 Cloud Run env / schema migration

## F. WeCom live（Loop 2+ 必填）

- [ ] 是否 touch `slice.py` / callback / drain：☐ YES ☐ NO
- [ ] 若 YES：已计划跑 `test_wecom_slice.py` + generic hello 安全检查
- [ ] 若 YES：已确认 Cloud Run queue flags 当前值（`gcloud run services describe`）

## G. 完成时追加（loop 结束时填写）

- [ ] **Verified on QA:** ☐ YES (URL: _______) ☐ NO (reason: _______)
- [ ] **Cloud seed/reset run:** _______________________
- [ ] **WeCom live tested:** ☐ YES ☐ NO ☐ N/A
- [ ] **Any prod / non-demo data touched:** ☐ NONE ☐ YES — STOP AND REPORT

---

**GO / NO-GO:** ☐ GO — 所有必填项已确认  ☐ NO-GO — blocker: _______________
```

---

## 附录 — 快速命令参考

| 目的 | 命令 |
|------|------|
| Local dev 启动 | `bash scripts/run_demo_local.sh` |
| Cloud seed | `PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target cloud` |
| Cloud reset + reseed | `bash scripts/reset_chen_kui_demo.sh --cloud --reseed` |
| 环境检查 | `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` |
| WeCom drain | `PYTHONPATH=. python3 scripts/wecom_drain_queues.py` |
| Cloud Run 503 recovery（engineering only） | `bash scripts/restore_8001_readiness.sh` |

---

*Document version: P18.11 v1 · 2026-07-05 · Environment rules only — no code*
