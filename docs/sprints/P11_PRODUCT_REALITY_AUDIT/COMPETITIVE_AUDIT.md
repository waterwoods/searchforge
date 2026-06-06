# Competitive Audit — Unified Intake

**Method:** Pretend you are a competing broker software company (AMS add-on, WeChat CRM, generic AI assistant vendor) attacking Unified Intake in a broker sales call.

---

## TOP 30 Competitive Weaknesses (how competitors attack)

| # | Weakness | Attack line |
|---|----------|-------------|
| 1 | No WeChat inbox sync | "You still copy-paste — we read your WeChat directly" |
| 2 | Manual paste every message | "Our bot replies in-thread; zero extra steps" |
| 3 | No OCR / screenshot reading | "Brokers send photos — we extract text automatically" |
| 4 | No carrier / AMS integration | "We pull policy data; you don't re-type VIN" |
| 5 | No multi-user auth / roles | "Your assistant and broker need separate logins and audit trail" |
| 6 | Single-founder support | "What happens when your vendor is on vacation?" |
| 7 | Engineer labels in UI (PG, API URL) | "This looks like a developer demo, not office software" |
| 8 | Wrong default tab (Customer Entry) | "Your team won't find the feature — adoption dies Day 1" |
| 9 | Hidden training path (Simulation) | "We include onboarding; they hide their practice mode" |
| 10 | Add-Car vs cancellation story split | "They sell add-car portal; you need cancellation triage" |
| 11 | No billing portal / Stripe | "Can't expense without proper invoice system" |
| 12 | No SLA / uptime guarantee | "Insurance is same-day — 503 during business hours kills trust" |
| 13 | Cases on localhost in demo | "Is my client data on their laptop?" |
| 14 | No mobile app | "Brokers live on phone — this is desktop-only" |
| 15 | Generic "AI" positioning | "ChatGPT does drafts free — why pay?" |
| 16 | No testimonial / reference customers | "Who else pays for this?" |
| 17 | 7-day trial too short | "Real cancellation cases don't arrive on schedule" |
| 18 | Draft quality inconsistent | "Wrong names in reply = E&O risk" |
| 19 | No compliance certification | "Where's your SOC2 / data processing agreement?" |
| 20 | English "case" in Chinese UI | "Not built for 华人经纪 office" |
| 21 | No analytics / ROI dashboard | "Show me hours saved — they can't" |
| 22 | No multi-office / franchise | "You're one broker; we scale to 50 offices" |
| 23 | Paste-only — no structured client portal | "Customers fill forms; you don't chase zip codes" |
| 24 | Qdrant/vectors optional — knowledge gap | "Their lookup is broken half the time" |
| 25 | `/demo` RAG confuses product story | "Is it intake or search? They don't know" |
| 26 | No automatic follow-up reminders | "We ping you when client hasn't replied" |
| 27 | No template library by carrier | "Mercury vs GEICO — we know the wording" |
| 28 | Founder-dependent deploy | "Every broker waits for their engineer to deploy" |
| 29 | No WeChat Official Account integration | "We are inside WeChat; they are a browser tab" |
| 30 | Pricing not published | "Hidden price = hidden maturity" |

---

## TOP 30 Competitive Advantages (Unified Intake counters)

| # | Advantage | Why it matters to Chen Kui |
|---|-----------|----------------------------|
| 1 | **Insurance-specific case structure** | Not generic chat — Case focus, urgency, next move built for broker ops |
| 2 | **Same-day action queue** | Cancellation triage is the pain; competitors sell CRM, not urgency |
| 3 | **Collected / Still needed chips** | Solves "did they send the dec page?" without thread archaeology |
| 4 | **Human-in-the-loop — no auto-send** | E&O-safe; broker controls every customer message |
| 5 | **Human confirmation badge** | Know when to verify AI-collected facts |
| 6 | **Editable draft → copy to WeChat** | Fits existing workflow; no new channel for customer |
| 7 | **Reopen + paste follow-up** | Multi-day cases preserved; WeChat bots often lose context |
| 8 | **Chinese + English messy paste** | Built for 陈魁-style mixed messages |
| 9 | **Cancellation / missing doc / add-car scenarios** | Pre-validated triangle vs generic AI |
| 10 | **Guardrail 13/13 regression** | Quality tested on broker scenarios (competitors rarely show this) |
| 11 | **7-day trial with real paste** | Try on actual messages before paying |
| 12 | **Low price point ($49–99/mo)** | Cheaper than AMS add-ons or full CRM |
| 13 | **No long implementation** | URL + kickoff vs 90-day CRM rollout |
| 14 | **Founder-direct support** | Fast fix for Day 1 confusion (weakness at scale, strength for pilot) |
| 15 | **Demo queue for safe training** | Practice without touching live clients |
| 16 | **Copy case snapshot for support** | Faster resolution than ticket systems |
| 17 | **Postgres durable cases (prod)** | Cases survive refresh when deployed correctly |
| 18 | **Product-only mode** | Hides lab junk — focused surface vs platform bloat |
| 19 | **CUSTOMER_LANGUAGE_GUIDE** | Broker-first terminology (when applied in UI) |
| 20 | **Explicit "what we don't promise"** | Honest scope vs overselling competitors |
| 21 | **Add-car structured path** | Revenue workflow when paste path works |
| 22 | **Workbench queue preview — 下一步 on card** | Scan without opening every record |
| 23 | **Waiting on client / done statuses** | Lightweight ops without full CRM |
| 24 | **Manual payment acceptable** | 华人经纪 often prefer WeChat/Zelle vs corporate card |
| 25 | **California auto focus** | Not generic global insurance platform |
| 26 | **No vendor lock-in to WeChat API** | Works even if WeChat policy changes |
| 27 | **Single purpose — message triage** | Easier to adopt than "replace your entire stack" |
| 28 | **Observation log + fix-now loop** | Product improves from real broker feedback |
| 29 | **intake_core readiness** | Triage works without vector DB dependency |
| 30 | **Speed to first paid pilot** | Competitors need quarters; this needs one broker week |

---

## Competitive verdict

**Unified Intake wins** when the broker's pain is **urgent message triage + reply drafting** in a WeChat-heavy office and they accept manual paste.

**Unified Intake loses** when the broker expects **inbox sync, OCR, CRM replacement, or enterprise SLA** on Day 1.

**Defensible niche for paid pilot:** Cancellation + missing document + draft reply — not Add-Car portal, not RAG lookup, not platform.

---

*End of competitive audit*
