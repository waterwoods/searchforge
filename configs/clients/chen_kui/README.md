# Chen Kui Client Pack

Client-specific phrasing, tone, and reply overrides for Chen Kui insurance office.

**Purpose:** Hot-swappable when adding another broker client.

**Load order:** Loaded last. Reply overrides merge into industry templates (shallow merge per key).

**Files:**
- `handoff_phrases.json` — Handoff reply strings (add_car / other, zh / en) when case is ready for broker
- `reply_overrides.json` — Optional overrides for industry reply templates (empty = use industry defaults)
- `ui_copy.json` — Client-specific UI copy (app title, office label, quick-start buttons). Target for future UI config loading; today UI still hardcoded.
