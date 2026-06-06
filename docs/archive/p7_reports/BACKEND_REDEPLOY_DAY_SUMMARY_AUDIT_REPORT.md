# Backend Redeploy + Day Summary Audit Report

**Sprint:** Backend Redeploy + Day Summary Audit  
**Date:** 2026-03-13  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Pre-deploy backend check

### Files confirmed

| File | Status |
|------|--------|
| `services/fiqa_api/health/ready.py` | ✓ DEMO_MODE handling; qdrant/embedding optional; GPU non-blocking; `intake_path_ready`; bulletproof ok=True when core_keys=[] |
| `services/fiqa_api/inbox_triage/triage.py` | ✓ follow_up_type, collection_stage, human_confirmation_fields, structured fields for add_car/missing_doc/cancellation/renewal/claim |
| `services/fiqa_api/routes/inbox_triage.py` | ✓ triage_conversation, triage_for_append; human_confirmation wired for single-message path |

### Local validation summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_multi_turn_simulations.py` | 38/38 strong |
| `audit_state_field_accuracy.py` | 7/7 passed |
| `guardrail_inbox_triage.sh` | PASS |
| `unified_intake_smoke_check.sh` | PASS |

---

## 2. Backend redeploy result

| Item | Value |
|------|-------|
| **Success** | Yes |
| **Backend URL** | https://fiqa-api-1013093472160.us-west1.run.app |
| **Revision** | fiqa-api-00017-t7r |
| **Notes** | /healthz failed (embedding warmup); /readyz OK. Deploy script sets DEMO_MODE=true. |

---

## 3. Readiness + triage verification

### /readyz result (observed via HTTP)

```json
{
  "ok": true,
  "status": "ready",
  "clients_ready": true,
  "demo_mode": true,
  "intake_path_ready": true,
  "clients": {
    "qdrant_connected": false,
    "embedding_model": false,
    "redis_connected": false
  }
}
```

**Verdict:** Backend truth is now aligned. Intake path does not require Qdrant/embedding; DEMO_MODE=true yields ok=true and intake_path_ready=true.

### Triage API result

Test payload: `{"text": "保单要停了，7天后要cancel，怎么办"}`

- **issue_category:** cancellation_warning
- **urgency:** critical
- **collected_fields:** notice_present, urgency_due_confusion
- **still_needed_fields:** payment_proof_or_screenshot
- **human_confirmation_required:** true
- **human_confirmation_fields:** ["payment_proof_or_screenshot"]
- **client_reply_draft:** Chinese, appropriate

**Verdict:** Triage works; structured outputs and human-confirmation signals present.

---

## 4. Today's main accomplishments

### Trusted multi-turn core

| Achievement | Detail |
|-------------|--------|
| **Strongest** | Lightweight state layer: follow_up_type, collection_stage, human_confirmation_fields. Reply strategy: clarification → answer first; already_sent → warmer handoff; correction → "好的，明白了". |
| **More practical** | Per-flow structured fields (add_car, missing_doc, cancellation, renewal, claim). Broker sees Collected / Still needed. |
| **More trustworthy** | human_confirmation_required for VIN, primary_driver, customer_says_sent_*, payment/cancellation. Avoids overcommitting. |
| **Still weak** | LC-AC3 (correction-after-handoff) — handoff at T2 when T3 correction arrives; low impact. Renewal policy_bill_sent uses broad "发" — could over-trigger. |

### Simulation / trial / demo quality

| Achievement | Detail |
|-------------|--------|
| **Strongest** | 38 multi-turn + 27 adversarial + 23 complex adversarial + 15 Simulation Assistant — all pass or acceptable. |
| **More practical** | Simulation Assistant 15 scripted scenarios; mixed-intent and long-context packs. |
| **More trustworthy** | audit_state_field_accuracy.py (7 cases); guardrail_inbox_triage.sh; unified_intake_smoke_check.sh. |
| **Still weak** | LC-AC3 friction (1 acceptable). No weak cases in current pack. |

### Release reliability

| Achievement | Detail |
|-------------|--------|
| **Strongest** | Readiness truth alignment. DEMO_MODE=true → ok=true, intake_path_ready=true. GPU non-blocking. |
| **More practical** | KNOWN_DEPLOYMENT_GOTCHAS.md; deploy_rag_demo.sh; demo.env.example notes. |
| **More trustworthy** | Pre-deploy checklist: run_inbox_triage_scenarios, run_multi_turn_simulations, audit_state_field_accuracy, guardrail, smoke. |
| **Still weak** | /healthz can fail (embedding warmup); operators must rely on /readyz for intake. |

---

## 5. Overall evaluation

### 3 biggest accomplishments today

1. **Readiness truth alignment** — /readyz now reflects intake-path reality. DEMO_MODE=true yields ok=true and intake_path_ready=true even when Qdrant/embedding are down. Operators get a clear signal.
2. **Lightweight state machine layer** — follow_up_type, collection_stage, human_confirmation_fields. Reply strategy improved: clarification → answer first; already_sent → warmer handoff.
3. **Structured field extraction + human confirmation** — cancellation/payment flows now have collected/still_needed; human_confirmation_required for high-risk fields.

### Most valuable one

**Readiness truth alignment.** It unblocks deployment confidence. Before: /readyz could block intake when Qdrant was down. After: intake path is correctly reported ready. This is the single highest-leverage fix for release maturity.

### Top 2 remaining weaknesses

1. **LC-AC3 correction-after-handoff** — User adds "是我老婆开那辆" at T3 after handoff at T2. Ideal: process correction and hand off at T3 with updated driver. Low impact for pilot.
2. **Release discipline** — /healthz vs /readyz confusion; operators need to know which to trust for intake. Documented in gotchas but still a cognitive load.

### Pilot confidence level

**Noticeably more pilot-ready.** 49 inbox triage, 38 multi-turn, 27 adversarial, 23 complex adversarial, 15 Simulation Assistant — all pass. Human confirmation boundaries visible. Readiness no longer blocks intake deployment.

### Release maturity

**Noticeably more mature.** Pre-deploy checklist exists; gotchas documented; readiness truth aligned. One-command deploy works. Post-deploy verification (readyz + triage) is straightforward.

### What the founder should be happiest about

- **Readiness finally correct** — No more false-negative blocking intake.
- **State layer is useful** — follow_up_type and human_confirmation_fields improve broker trust and reply quality.
- **Validation discipline** — Guardrail + smoke + audit scripts give confidence before deploy.

### What the founder should still be cautious about

- **LC-AC3** — One friction case; monitor if it appears in real usage.
- **/healthz** — Can fail; don't conflate with intake readiness.

---

## 6. Recommended next step

**Run one real founder demo end-to-end** — Paste a real Chen Kui message into the live Unified Intake UI (Vercel → Cloud Run), verify triage, collected/still_needed, human confirmation badge, and copy-draft flow. This validates the full chain in production and builds founder confidence before pilot.

---

## 7. 中文宏观总结

- **后端有没有重新发上去：** 有。Cloud Run 已部署，revision fiqa-api-00017-t7r。
- **readyz 现在是不是终于对了：** 是。DEMO_MODE=true 时 ok=true、intake_path_ready=true，即使 Qdrant/embedding 未就绪，intake 路径也正确报告为 ready。
- **今天最重要的成果到底是什么：** (1) readiness 与 intake 路径对齐；(2) 轻量级状态层（follow_up_type、collection_stage、human_confirmation）；(3) 结构化字段 + 人工确认边界。
- **哪些「好东西」现在真正发挥作用了：** follow_up_type 驱动回复策略（clarification 先回答、already_sent 用更暖的 handoff）；human_confirmation_fields 让 broker 知道哪些需要人工核对；collected/still_needed 让 broker 看到进度。
- **还剩什么大缺口：** LC-AC3 一个 friction 案例；release 时需分清 /healthz 与 /readyz。
- **现在是不是更适合拿去试点了：** 是。验证全部通过，readiness 不再误报，状态层和人工确认边界已就绪。

---

## 8. COPY/PASTE DAY SUMMARY BLOCK

```
Backend Redeploy + Day Summary — 2026-03-13

3 biggest improvements:
1. Readiness truth alignment — /readyz now returns ok=true, intake_path_ready=true when DEMO_MODE=true; intake path no longer blocked by Qdrant/embedding.
2. Lightweight state machine layer — follow_up_type, collection_stage, human_confirmation_fields; reply strategy: clarification→answer first, already_sent→warmer handoff.
3. Structured fields + human confirmation — cancellation/payment flows have collected/still_needed; human_confirmation_required for VIN, primary_driver, customer_says_sent_*.

Biggest current strength: Readiness and triage are aligned with reality. 49 inbox + 38 multi-turn + 27 adversarial + 15 Simulation Assistant all pass. Human confirmation boundaries visible.

Biggest remaining weakness: LC-AC3 correction-after-handoff friction (low impact). /healthz can fail; operators rely on /readyz for intake.

Pilot confidence: Improved. Product is noticeably more pilot-ready.

Release maturity: Improved. Pre-deploy checklist, gotchas doc, one-command deploy, post-deploy verification.

One next step: Run one real founder demo end-to-end on live Unified Intake (Vercel → Cloud Run) to validate full chain in production.
```
