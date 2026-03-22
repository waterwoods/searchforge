# Founder Inspection Notes

## What to skim first (5 minutes)

1. `scenario_battery.json` — Read the **customer text** aloud; confirm it sounds like your WeChat / SMS threads.  
2. `battery_run_results.json` — For each `id`, scroll to **last** `turn_results` entry and check `client_reply_draft` and `collected_fields`.  
3. `FINAL_REPORT.md` — Sections **6–9** and the **中文宏观总结**.  

## Red flags to trust your gut on

- **Customer reply says they already sent something** when the thread only asked **whether they can send** → unacceptable for pilot.  
- **First message** of a session gets **“通知不完整”** style wording when the customer is clearly shopping → feels like the wrong bot.  
- **Workbench shows “ready”** but **driver** (or ZIP) is still in **still needed** → confusing for staff.  

## What is already “good enough for Chen Kui to watch”

- **Straight add-car** messages with **YMM + ZIP + delivery + self-driver** tend to **hand off cleanly** with sensible Chinese closure lines.  
- **Multi-turn slot completion** (vehicle first, ZIP second) **works** in this battery.  
- **Price-first** + second message with facts: **stays in flow** and completes.  

## What to say to a broker in one sentence

> “Rules handle the happy path and many real WeChat shapes well; the risk is **mis-reading ‘can I send’ as ‘I sent’** and **occasional wrong first reply** when the customer opens with ZIP/price worry before naming a car.”  

## Do not overclaim in meetings

These scenarios are **structured realism**, not research data. Use them for **engineering prioritization** and **demo script design**, not for market sizing.
