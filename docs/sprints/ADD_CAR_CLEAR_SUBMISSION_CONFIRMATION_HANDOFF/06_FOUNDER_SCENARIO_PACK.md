# Founder Scenario Pack

Use these when manually inspecting **customer entry** after implementation. Pair with `founder_scenario_pack.json` (plain `turns[]` messages) + `scripts/run_add_car_submission_confirmation_sprint_scenarios.py` for rule-level checks.

| # | Scenario | What to verify |
|---|----------|----------------|
| 1 | Clean Add-Car → full info → handoff | Closure shows tags + timing; draft sounds formally submitted |
| 2 | Partial Add-Car → completion → handoff | Progress → closure transition; still_needed cleared in snapshot |
| 3 | Add-Car with correction → handoff | Snapshot reflects rule brain after correction; boundary hint intact |
| 4 | Materials sent / ask-to-send → handoff | Handoff phrase + snapshot coexist; no chatty extra prompts |
| 5 | Quote-ready but missing one field | `almost_ready` or `need_more` visible in pre-handoff; at handoff snapshot honest |
| 6 | Complete → customer checks accuracy | Intro copy invites verify + same-case append |
| 7 | Complete → when will office respond | Timing line visible; wording not overpromising |
| 8 | Complete → “new issue” boundary | `handoff_new_issue_hint` still prominent below actions |

## Why this pack

Covers **submission**, **confirmation**, **waiting**, and **one-request boundary** without expanding scenario inventory to unrelated intents.
