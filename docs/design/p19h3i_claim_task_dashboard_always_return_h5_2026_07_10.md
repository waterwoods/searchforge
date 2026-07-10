# P19H-3i — Claim Task Dashboard + Always-return H5 Entry

**Date:** 2026-07-10  
**Sprint:** P19H-3i  
**Status:** Implemented on `sprint/p16-trust-layer`

---

## 1. Product problem

After an accident, customers repeatedly supplement claim information across days — photos, other-party plate, insurance, narrative details. Pure WeCom chat makes it easy to get lost: no persistent task center, no clear “what’s next,” and no reliable way to reopen the same structured intake.

---

## 2. Core principle

| Surface | Role |
|---------|------|
| **H5 task dashboard** | Source of truth for structured fields; visible status, received/missing, next action |
| **WeCom** | Entry, notification, convenient supplement channel |
| **Broker Workbench** | Timeline + known facts; broker confirmation finalizes |

**H5 confirmed fields** = structured source of truth (`source: h5_form`, `customer_confirmed`).  
**WeCom text/photo supplement** = customer supplement (`source: wecom_customer_text`, `customer_supplement`).  
**Broker confirmation** = office final fact (`source: broker`, `broker_confirmed`).

---

## 3. Customer flow

```text
Start (WeCom「我要理赔」)
  → H5 wizard (structured steps)
  → Submit to Chen review
  → Continue supplement (WeCom text/photo OR H5 dashboard)
  → Broker review / Done
```

After submit, the customer is **not** asked to restart. Status cards and supplement acks include **继续补充事故资料** with the same H5 task link.

---

## 4. WeCom command policy

When an **active Claim** exists (not `broker_done`), these texts route to **Claim Status Card** with H5 link:

- 进度 / 状态 / 查进度
- 补资料 / 补充资料
- 链接
- 事故资料
- 继续填写 / 继续补充
- 上传照片

Behavior:

- Return current Claim status (已提交给陈总审核 when submitted)
- Include H5 task dashboard link labeled **继续补充事故资料**
- Do **not** start a new Claim
- Do **not** route to Add Car (unless explicit「我要加车」)

---

## 5. Supplement policy

| Input | Policy |
|-------|--------|
| WeCom text (plate, insurance, narrative) | Append to active Claim timeline; ack with optional H5 link |
| WeCom photo | Attach to active Claim when bound; ack mentions 进度/链接 for H5 |
| H5 PATCH | Authoritative for structured wizard fields (blocked after submit) |
| Extracted WeCom facts | Stored with `known_fact_provenance` as customer supplement |

WeCom supplements are **accepted** and **labeled** — not silently promoted over H5 confirmed fields.

---

## 6. H5 dashboard (Scope A)

Top panel on `/task/claim/:taskToken`:

- **Title:** 我的事故资料
- **Subtitle:** 你可以随时回来补充资料。陈总会看到这里的最新记录。
- **Status:** 资料收集中 / 已提交给陈总审核 / 陈总已确认
- **Received / Missing / Next action / Primary CTA**
- After submit: subtitle explains supplement is still allowed; CTA = 继续补充资料

Wizard stepper and submit flow unchanged below the dashboard.

---

## 7. Why not mini-program yet

H5 dashboard + always-return WeCom link solves ~80% of “where is my task?” friction without app-store / mini-program registration overhead. Mini-program remains an option only if H5 open/upload friction stays high in pilot.

---

## 8. Spark Driver / TurboTax analogy

| Pattern | Our implementation |
|---------|-------------------|
| One current task | Single active Claim per lane |
| Progress dashboard | H5 dashboard_summary + Status Card |
| Resume later | H5 link on 进度 / 链接 / supplement ack |
| Next best action | dashboard `next_action` + primary CTA |
| Formal handoff | Submit → broker review |

---

## 9. Remaining gaps

- Real WeCom photo route with inline H5 URL (today: reply points to 进度/链接)
- Full provenance UI in Workbench (today: key_facts suffix + timeline)
- Add Car task dashboard (separate sprint)
- Mini-program (deferred)
- `broker_done` automation (explicitly out of scope)

---

## 10. Photo supplement policy (code comment reference)

```text
# Product rule (P19H-3i): WeCom photos append to active Claim timeline when bound.
# H5 remains preferred for structured review; reply directs customer to 进度/链接 for dashboard.
```

See `services/fiqa_api/wecom/reply.py` — `_MEDIA_ACK_CLAIM_GUIDED_BOUND`.
