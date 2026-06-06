# Client Handoff Phrase Wiring Spec

**Purpose:** Define which handoff phrases become client-aware and where hardcoding remains.

---

## 1. Handoff Phrases to Become Client-Aware

| Key | Used when | Current chen_kui | demo_broker (new) |
|-----|-----------|------------------|---------------------|
| `customer_requested_human` | Talk to Agent | "已帮您转给陈奎办公室" | "已帮您转给客服团队" |
| `add_car` | Add-car handoff | "办公室会尽快出价" | "客服团队会尽快出价" |
| `remove_car` | Remove-car handoff | "办公室会尽快处理" | "客服团队会尽快处理" |
| `other` | Generic handoff | "办公室会尽快处理" | "客服团队会尽快处理" |
| `other_received` | Already-sent follow-up | "办公室会尽快处理" | "客服团队会尽快处理" |
| `other_corrected` | Correction follow-up | "办公室会尽快处理" | "客服团队会尽快处理" |
| `other_clarification` | Clarification follow-up | "办公室会优先核实" | "客服团队会优先核实" |

---

## 2. Where Current Hardcoding Exists

| Location | Hardcoded text |
|----------|----------------|
| `triage.py` line ~881 | "好的，已帮您转给陈奎办公室，他们会尽快联系您。" |
| `triage.py` line ~2261 | Same as above |
| `triage.py` line ~2371 | "办公室会尽快核实" |
| `triage.py` line ~2375–2377 | "办公室会尽快出价" / "办公室会尽快处理" |
| `triage.py` line ~2400 | "办公室会尽快处理，有结果会联系您。" |
| `triage.py` line ~2418 | "办公室会尽快处理" |
| `inbox_triage.py` line ~348 | "好的，已帮您转给陈奎办公室，他们会尽快联系您。" |
| `triage.py` talk_to_agent fallback | "联系陈奎", "找陈奎" (markers only; keep for intent detection) |

---

## 3. Client Config Files

| Client | Path | Status |
|--------|------|--------|
| chen_kui | `configs/clients/chen_kui/handoff_phrases.json` | Exists |
| demo_broker | `configs/clients/demo_broker/handoff_phrases.json` | **Create** |

---

## 4. What Remains Hardcoded for Now

- **broker_next_step** — "Customer requested human contact. Call or message back promptly." (English, internal)
- **client_prep** — "Customer wants to speak with office." (English, internal)
- **Talk-to-agent markers** — "联系陈奎", "找陈奎" in fallback markers (intent detection; keep generic)
- **Generic fallbacks** — When config missing: "办公室" (generic) not "陈奎办公室"

---

*End of Spec*
