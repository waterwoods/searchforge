# P4 Pilot Finish Line — Founder QA Package

**Date:** 2026-07-24  
**Status:** READY FOR FOUNDER QA (Conditional Go)  
**Objective:** One consistent, stable product for the first Chen Pilot — no new features.

---

## 1. One user-facing objective

A first-time customer can complete S1–S6 calmly with one next action per screen, consistent 陈总 / 我的报案 wording, and no over-promised AUTO Prefill behavior.

**Out of scope:** CRM, identity redesign, Cap 01–03 default enablement, new workflows, UX redesign.

---

## 2. Preview / flags / build

| Item | Pilot posture | Notes |
|------|---------------|--------|
| Mini Program `smartClaimStartEnabled` | **OFF (intentional)** | Committed in `config.defaults.ts` + `config.qa.ts`. Cap 01–03 not part of default Pilot walk. |
| Cap 01–03 Founder validation | Optional, separate | Enable only in gitignored `config.local.ts` + Cloud QA `P4_CUSTOMER_LOOKUP_MOCK=1`. |
| `apiProfile` (local DevTools) | `qa` via `config.local.ts` | Points at Cloud QA HTTPS for Experience Preview. |
| Build Gate | **PASS** | `cd miniapp && npm run build:gate` |
| Deployment QA Gate | **PASS** | `READY FOR FOUNDER QA` — serving `fiqa-api-qa-00021-bbh` @ 100% |
| Warm tip | Before gate / Preview | If cold: `curl -sf …/health/live` once (15s curl can fail on cold start). |

### Founder Preview steps (mandatory order)

1. Commit / pull this freeze  
2. Deploy Cloud QA if backend hub title not yet live (client remaps legacy title anyway)  
3. WeChat DevTools: **清缓存 → 重新编译**  
4. New Preview QR  
5. Walk S1–S6 as a stressed, non-technical customer (55–65)

---

## 3. Expected S1–S6 behavior

| Step | Expect |
|------|--------|
| **S1** Open / Service Home | One primary: **开始报案** or **继续办理当前报案**; contact **联系陈总** |
| **S2** Start Claim → submit | Accident facts; CTA **提交给陈总**; success feels “told 陈总 what happened” |
| **S3** Task Home | Hub title **我的报案**; one Today; CTA matches Today |
| **S4** Insurance Card | Upload → if more work remains, receipt says **已收到。下一步：…** (not “审核”); lands hub with next work |
| **S5** Photos | One primary **完成并继续**; secondary **先离开，稍后再继续** only |
| **S6** Review → Receipt | **确认并交给陈总** → calm receipt; leave via **返回首页** / **返回我的报案** (not “新报案”) |

### Continuity checks

| Check | Expect |
|-------|--------|
| Insurance Card continuity | Never “陈总会继续审核” while customer still owes Today work |
| Photos | No three competing footer buttons; no “回读服务器 / 经纪人状态” |
| Receipt | Waiting copy only when truly waiting |
| Resume / One Active Case | Continue current case; contact **联系陈总** to start a new one |
| Contact | Always **联系陈总** (never 联系保险顾问 on customer path) |

---

## 4. Known limitations (honest)

| Limitation | Severity | Pilot handling |
|------------|----------|----------------|
| Smart Claim Start / Cap 01–03 **OFF** | Medium | Intentional. Default walk does not validate mock lookup chips. |
| AUTO Prefill is presentation / classification only | Medium | When Cap path is later enabled, copy says **请确认以下信息** — does not promise CRM sync. |
| Contact = WeChat message homework | Medium | Modal only; no in-app chat for Pilot. |
| Capsule Home may land Start Claim (`pages[0]`) | Medium | Platform constraint; Continue uses Entry / Service Home. |
| Physical device Preview not run in this engineering loop | High | Founder-owned; this package is the walk script. |
| Task Home density (Why/After) | Low | Post-Pilot polish. |

---

## 5. Automated evidence (this loop)

| Gate | Result |
|------|--------|
| `miniapp` `npm run build:gate` | **PASS** (apiProfile qa → Cloud QA host) |
| `miniapp` unit tests | **363 pass** / 3 fail = `P26H_UI_FIXTURE_JSON` QA fixture only (pre-existing) |
| P4 Cap 03 + Integration 01 pytest | **PASS** |
| H5 dashboard title pytest | **PASS** (`我的报案`) |
| `bash scripts/run_deployment_qa_gate.sh` | **READY FOR FOUNDER QA** |

---

## 6. Copy / hub SSOT (Pilot)

| Surface | Canonical |
|---------|-----------|
| Broker name | 陈总 |
| Hub | 我的报案 |
| Hub return | 返回我的报案 / 查看我的报案 |
| Review submit | 确认并交给陈总 |
| Start Claim submit | 提交给陈总 |
| Contact | 联系陈总 |

Server dashboard title and client legacy remap both use **我的报案** (no mixed 我的事故资料 on customer path).

---

## 7. Go / No-Go

**Verdict: Conditional Go**

- Go for Founder device Preview + S1–S6 after cache clear / rebuild.  
- Condition: Founder confirms physical Preview feels natural; only then approve first Chen Pilot.  
- Cap 01–03 remain OFF unless Founder explicitly schedules a separate Cap QA pass.
