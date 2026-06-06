# Fix-Now / Fix-Next / Acceptable / Defer

How to use this: each finding from the battery gets **one** bucket. Goal is **calibrated** response—fix what hurts broker trust first; don’t churn on polish.

## Fix-now

Criteria:

- Causes **wrong category** or **false materials-sent** behavior.
- Drops **must-have slots** when they are clearly present in customer text (ZIP, driver).
- Emits **generic “内容不完整”** on simple operational questions when Add-Car context is about to continue.

Examples from this sprint (see `06_FINAL_REPORT.md`):

- **ZIP after `邮编`** not detected (word-boundary / format issue).
- **“要不要发你”** (question) misread as **“发过了”** (already sent).
- **“我自己开”** not recognized as driver (substring logic misses common phrasing).

## Fix-next

Criteria:

- Playbook correct but **UX friction** (echoing entire customer preamble in acknowledgements).
- **Redundant** checklist tail in replies when the customer already supplied year/model/zip/driver in the same bubble.
- **Dual-vehicle** first turn: only one vehicle acknowledged—recoverable on turn 2, but could be clearer earlier.

## Acceptable (for now)

Criteria:

- **Handoff** appropriate; broker step actionable.
- Minor **label noise** in `still_needed_fields` vs broker text (e.g., “confirm driver” while delivery already anchors timing)—office can still work the case.

## Defer

Criteria:

- Requires **LLM product decision** (tone variety, richer paraphrase) without changing trust boundaries.
- **Perfect** naturalness / shortest possible drafts—nice-to-have vs broker trust.

## Anti-patterns

- **Do not** “fix” by adding brittle keyword lists without a small test + battery re-run.
- **Do not** broaden Add-Car detection so far that premium-review or document flows collapse—prefer **surgical** extraction fixes.
