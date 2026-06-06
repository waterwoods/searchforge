# Same-Case vs New-Issue After Handoff — Spec

## Prior thread domain inference

`_infer_prior_case_domain(source_text)` treats a thread as **add_car** when:

- Customer text matches add-vehicle markers, or  
- System text contains add-car handoff markers (e.g. 办公室会尽快出价).

## Same-case signals (append)

Treat as **same case** (no `case_boundary`) when:

- **Correction** of vehicle fields (`follow_up_type=correction`) except explicit cross-topic pivots (“另外一个保险问题”等).
- **Materials / already_sent** (截图、发微信、VIN 补发) with no cross-domain hit.
- **Short factual slot fill** (ZIP, year, driver) on add-car thread.
- **Second vehicle** on same quote when phrasing matches `_SAME_THREAD_EXTRA_VEHICLE_MARKERS` or domains stay in add_car with controlled pivot.
- **Quote-side questions** (保额、全险、deductible、coverage 能调吗) on add-car prior — even if “顺便问” appears.

## New-issue signals

**Immediate `new_issue`** when last message domains intersect **cross-issue set** for prior add_car:

- `claim`, `billing`, `remove_car`, **`premium`** (续保 / 保费 / renewal-style markers)

Plus strong pivot + ambiguous domain handled as borderline per `triage.py`.

## Borderline

- **Office hours** on add-car thread (`office` domain + prior add_car).
- **Pivot phrase** with **no** domain markers.
- **Pivot + add_car** without “another vehicle” markers (unclear if new car vs clarification).

## Broker-facing tags

- `conversation_summary` prefix: `Boundary: new_issue (...)` or `Boundary: borderline (...)`.
- `broker_next_step` prefix: `Case boundary: ...` or `Case boundary unclear—...`.

## Customer-facing drafts

- `new_issue`: continuity line + topic-specific line + **portal suffix** (zh) recommending 「提交新问题」for unrelated items when prior was add_car.
- `borderline`: single neutral forward + ask to clarify if not the same topic.
