# Weakness families, case battery, and validation spec

## Main weakness families (priority order)

| Priority | Family | Examples | Risk if wrong |
|----------|--------|----------|----------------|
| 1 | Isolated follow-up / already-sent + “还缺什么” | 材料我微信发过了，还缺什么？；VIN发微信了还要补什么吗 | Routed to `missing_document` with empty slots, or `unclear` |
| 1 | Material / registration resend receipt | registration照片又发邮箱了，你收到了吗？ | `unclear`, no verify signal |
| 2 | Spouse / household / second vehicle | 老婆那台塞纳报一下价；家里还有一台CR-V也要一起报 | `unclear`, no Add-Car structuring |
| 3 | Re-shop / too expensive / coverage (Add-Car context) | 上次报的价太贵，换一家company，coverage调低 | Thin vehicle/delivery slots |
| — | (Secondary) | Mixed EN/ZH, dealer/finance variants | Polish only if time allows |

## Case battery (16 scenarios — script: `scripts/run_high_risk_add_car_pg_stage2_sprint_battery.py`)

| ID | Family | Example wording (abbrev.) | “Good enough” | Ideal Stage-2 signal |
|----|--------|---------------------------|---------------|----------------------|
| H01 | Direct strong | Full Tesla add-car | `customer_question`, quote-ready or near-ready | `quote_ready` + concrete vehicle |
| H02 | Direct + WeChat VIN | Camry + VIN微信发过了 | Strong slots + materials flag | Verify materials + quote |
| H03 | VIN delay | BMW X5, VIN等两天 | Delivery + VIN pending clear | `need_more` honest on VIN |
| H04 | Weak follow-up | Camry quote 还缺什么 | `customer_question`, non-empty `still_needed` | Checklist-style gaps |
| H05 | Weak follow-up | 材料微信发过了还缺什么 | Not `missing_document` dead-end | Full add-car gap list + materials sent |
| H06 | Material follow-up | registration又发邮箱收到吗 | Actionable category + verify | `verify_carrier_received` |
| H07 | Weak follow-up | VIN发微信还要补什么 | Add-car structured path | Same as H04/H05 |
| H08 | Spouse driver | RAV4 + 老婆也会开 + quote | `customer_question`, multi-driver | Driver list + zip/year gaps |
| H09 | Spouse vehicle | 老婆塞纳报一下价 + zip | Add-Car, not `unclear` | Year/model/delivery gaps explicit |
| H10 | Household second car | 家里CR-V一起报 + 都会开 | Add-Car, not `unclear` | Multi-driver + zip partial |
| H11 | Re-shop | 太贵换company + coverage + zip | `customer_question`, zip carried | Vehicle/delivery gaps explicit |
| H12 | Re-shop | 太高换公司 + 2023 Accord | Slots as strong as rules allow | Same |
| H13 | Multi-turn | 想加车 → Mazda CX-5 full | Progressive completion | Moves toward quote-ready |
| H14 | Append | Prius + append VIN | Append + dual-write extra message/state | VIN captured in thread |
| H15 | Almost quote-prep | Lexus RX + phone | Quote-ready or one field left | Clear “almost there” |
| H16 | Minimal | 想加车 | Collecting, no false handoff | Broad `still_needed` |

## Structured-data quality criteria

- `issue_category` matches broker mental model (Add-Car vs doc verify vs unclear).
- `still_needed_fields` non-empty when intent is Add-Car but information is incomplete.
- `collected_fields` reflect materials-sent, zip, partial vehicle where utterance supports it.
- `quote_ready_status` (`need_more` / `quote_ready`) aligns with slot completeness.

## Postgres validation criteria

- Counts: N `service_records`, N `structured_record_data`, messages ≥ N (append > 1 msg), `state_history` ≥ N.
- `structured_record_data.quote_readiness` and `missing_fields_summary` populated when JSON has `quote_ready_status` / `still_needed_fields`.
- Spot-check: rows skimmable for office triage (category + missing summary + readiness).

## Stage-2 readiness criteria (honest, no full Stage-2)

- Office can see **what is missing** for quote-prep.
- **Not** blocked on `unclear` when customer clearly continues Add-Car or doc receipt threads.

## Acceptance criteria

- `bash scripts/guardrail_inbox_triage.sh` **PASS**.
- Battery **16/16** completes under rule path; **0** `unclear` for scripted high-risk rows after fixes.
- Disposable Postgres dual-write run shows coherent counts and non-null `missing_fields_summary` where expected.
