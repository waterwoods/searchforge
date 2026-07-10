# P19H-3j — H5 vs WeCom Channel UX Policy

**Date:** 2026-07-10  
**Sprint:** P19H-3j  
**Status:** Implemented (not deployed)

---

## 1. Why dual-channel remains

Customers live in WeChat. Accident intake spans days — photos, plates, insurance, narrative details arrive at different times. A single channel cannot serve both:

- **Trust + convenience** — WeCom is where Chen's customers already talk.
- **Structure + review** — H5 is where fields, checklist, and submit live.

Dual-channel is necessary. Dual-channel must **not** become two competing forms.

---

## 2. Channel responsibilities

### H5 (formal task center)

- Full accident intake wizard
- Received / missing checklist (dashboard)
- Structured fields with customer confirmation
- Evidence review
- **Review + Submit to broker** (H5-only)
- Resume later via signed `h5t1` token

### WeCom (supplement + recovery)

- Start the task (Start Card)
- Status / progress (`进度`, `补资料`, `链接`, …)
- Quick text supplement (append to timeline)
- Quick photo supplement (attach to active Claim)
- Notifications and broker communication
- Exception cards (collision, lane switch) — rare

---

## 3. Critical boundary

| Rule | Meaning |
|------|---------|
| WeCom supplements are **accepted** | Text/photo append to `claim_timeline` + `known_facts` with `wecom_customer_text` / `customer_supplement` provenance |
| WeCom is **not** a parallel full form | Ordinary acks are short; no giant raw URL every message |
| H5 is **Review + Submit authority** | `POST /api/h5/tasks/{token}/submit` only path to broker handoff |
| Broker confirms in Workbench | `broker_done` manual; no automation |

---

## 4. Reply policy matrix

| Scenario | Customer input | Reply |
|----------|----------------|-------|
| **1 — Entry / status** | `进度`, `补资料`, `链接`, `事故资料`, `继续填写`, `上传照片`, explicit H5 request | Status / Start Card + H5 link (`继续补充事故资料` / `打开事故资料页面`) |
| **2 — Ordinary text supplement** | Plate, insurance, narrative on submitted Claim | Short ack: 已记录 + 陈总会查看；optional「回复进度或链接」；**no raw URL** |
| **3 — Text + missing items** | Supplement on open (not submitted) Claim with kernel missing items | Ack + `还缺 X 项` + compact `【继续补充事故资料】` + URL |
| **4 — Photo supplement** | Photo on active Claim | Short ack; H5 CTA only if missing-items or ready-to-submit policy applies |
| **5 — Ready not submitted** | Enough fields, review step, not yet submitted | Strong CTA: `【提交给陈总审核】` + URL |
| **6 — Submitted Claim** | Ordinary supplement after H5 submit | Short ack only; status commands still return H5 |

---

## 5. When to show H5 CTA

**Show:**

- Customer asks for status / link / materials
- Open Claim (not H5-submitted) with `get_claim_missing_items()` > 0
- Open Claim at review step (`is_ready_for_h5_submit`)
- Start / canonical H5 entry

**Do not show (ordinary supplement):**

- Submitted Claim + successful text/photo supplement
- No urgent missing-field action required
- Customer did not ask for link/status

---

## 6. URL handling

Preferred order:

1. WeCom `msgmenu` view button (Start / Status cards — unchanged)
2. Compact CTA label + URL (`【继续补充事故资料】`)
3. Plain URL only as fallback inside status card footer

No URL shortener. Token format and security unchanged.

Implementation: `services/fiqa_api/wecom/channel_ux_policy.py`

---

## 7. Review + Submit authority (preserved)

- WeCom text/photo → timeline + provisional known facts
- H5 PATCH → customer-confirmed structured fields (`h5_task` / `h5_form`)
- H5 submit → `intake_ready_for_broker`
- Broker Workbench → broker-confirmed final facts

---

## 8. Why not mini-program

H5 + policy above solves channel-role confusion without app-store / mini-program overhead. Revisit only if H5 open/upload friction stays high in pilot.

---

## 9. Future improvements

- Workbench provenance UI (source tags visible in drawer)
- Native WeCom template cards for supplement CTAs
- Add Car task dashboard (same policy pattern)
- Optional msgmenu for missing-items nudge (today: compact text CTA)

---

*Code: `channel_ux_policy.py`, `reply.py`, `claim_basics.py`, `media_intake.py`*
