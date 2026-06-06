# Founder Inspection Notes

**Sprint:** Client Configuration Wiring Sprint  
**Created:** 2026-03-18

---

## What Founder Should Inspect After This Sprint

1. **Default (Chen Kui):** Open `/workbench/unified-intake` — header "保险经纪人智能助手", tab "办公室工作台"
2. **Demo broker:** Open `/workbench/unified-intake?client=demo_broker` — different header and labels
3. **Config files:** `configs/clients/chen_kui/ui_copy.json`, `configs/clients/demo_broker/ui_copy.json`

---

## What Should Now Look More Reusable

- UI copy comes from config, not code
- Adding a new broker = new folder + ui_copy.json
- Same base, different client config

---

## How Founder Should Explain A → B Migration

> "We have one base. One industry template. Multiple client configs. To move from Client A to Client B, we create a new folder under configs/clients/ with their ui_copy and handoff phrases. No code change. The URL or environment can switch which client is active."
