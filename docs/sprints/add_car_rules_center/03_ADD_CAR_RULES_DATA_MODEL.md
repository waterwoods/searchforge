# Add-Car Rules Data Model / Config Spec

**Sprint:** Minimal Business Rules Center for Add-Car Quote  
**Purpose:** Define what parts of Add-Car Quote are configurable now.

---

## 1. Configurable (Business-Editable)

| Key | Label (中文) | Config Source | Notes |
|-----|-------------|---------------|-------|
| `first_reply_zh` | 这类客户第一句怎么回（中文） | reply_templates.add_car.zh | First-turn reply when add-car intent |
| `first_reply_en` | 这类客户第一句怎么回（英文） | reply_templates.add_car.en | Same, English |
| `ask_vehicle_zh` | 缺年份车型时问什么（中文） | add_car_rules.ask_vehicle.zh | Next-step when vehicle missing |
| `ask_vehicle_en` | 缺年份车型时问什么（英文） | add_car_rules.ask_vehicle.en | Same, English |
| `ask_zip_zh` | 缺邮编时问什么（中文） | add_car_rules.ask_zip.zh | Next-step when zip missing |
| `ask_zip_en` | 缺邮编时问什么（英文） | add_car_rules.ask_zip.en | Same, English |
| `ask_delivery_driver_zh` | 缺提车/驾驶人时问什么（中文） | add_car_rules.ask_delivery_driver.zh | Next-step when delivery/driver missing |
| `ask_delivery_driver_en` | 缺提车/驾驶人时问什么（英文） | add_car_rules.ask_delivery_driver.en | Same, English |
| `handoff_zh` | 转办公室时说什么（中文） | handoff_phrases.add_car.zh | When case ready for broker |
| `handoff_en` | 转办公室时说什么（英文） | handoff_phrases.add_car.en | Same, English |

---

## 2. Default Values (Current Hardcoded)

| Key | Default (zh) | Default (en) |
|-----|--------------|--------------|
| first_reply | 可以先帮你看这台车的报价。把车子的年份、车型、VIN（有的话）、提车日期、地址邮编和主要驾驶人发我，我先帮你算。 | I can start a quote for the new car. Send me the year, make/model, VIN if you have it, delivery date, zip or address, and main driver and I will check it. |
| ask_vehicle | 先把年份和车型发我，我就能帮你算。 | Send me the year and make/model first so I can run the quote. |
| ask_zip | 先把地址邮编发我，我就能帮你算。 | Send me the zip or address first and I will run the quote. |
| ask_delivery_driver | 提车日期和主要驾驶人发我一下，我好安排报价。 | Send me the delivery date and main driver so I can prepare the quote. |
| handoff | 您说的报价资料已整理好了，办公室会尽快出价，有结果会联系您。 | Got your quote details. Our office will review and follow up with you. |

---

## 3. NOT Configurable Yet

| Area | Reason |
|------|--------|
| Collection order | Logic fixed; changing would require code changes |
| Handoff threshold (vehicle+zip+delivery/driver) | Logic fixed; changing would risk breaking flow |
| Extraction logic | Regex/patterns; engineering-level |
| Intent markers | Config-driven but not in Rules Center scope |

---

## 4. Config File Structure

**New file:** `configs/industries/insurance/add_car_rules.json`

```json
{
  "version": "1",
  "description": "Add-Car Quote next-step prompts. Editable by business users.",
  "ask_vehicle": {
    "zh": "先把年份和车型发我，我就能帮你算。",
    "en": "Send me the year and make/model first so I can run the quote."
  },
  "ask_zip": {
    "zh": "先把地址邮编发我，我就能帮你算。",
    "en": "Send me the zip or address first and I will run the quote."
  },
  "ask_delivery_driver": {
    "zh": "提车日期和主要驾驶人发我一下，我好安排报价。",
    "en": "Send me the delivery date and main driver so I can prepare the quote."
  }
}
```

**Existing:** `reply_templates.json` (add_car), `handoff_phrases.json` (add_car)

---

## 5. Draft vs Published

- **Draft:** Stored in `configs/industries/insurance/add_car_rules_draft.json` or in-memory + localStorage
- **Published:** `configs/industries/insurance/add_car_rules.json` (and reply_templates.json overrides)
- **Backend:** Load from draft when present; else published. API can accept `?use_draft=true` for preview.

---

*See also: 04_SAFETY_GUARDRAIL_SPEC.md*
