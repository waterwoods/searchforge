# Before / After Leak Checklist (Optional)

Use when demoing same-industry client switch on **append** path.

| Check | Before | After |
|-------|--------|-------|
| B: add-car → billing append | Customer draft contained **办公室** | Customer draft uses **本所** (when `append_boundary` set) |
| B: borderline “还有一个问题” | **办公室** in draft | **本所** + **先前** phrasing |
| A: same scenarios | **办公室** narrative | Unchanged (defaults) |
| B: talk-to-agent (non-append) | Already isolated (`ab_12`) | Unchanged |
| `demo_broker` append boundary | N/A / same as engine | Engine defaults (**办公室**) — proves fallback |
