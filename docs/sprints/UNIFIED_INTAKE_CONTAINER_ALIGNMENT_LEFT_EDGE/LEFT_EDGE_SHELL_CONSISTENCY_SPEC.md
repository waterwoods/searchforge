# Left Edge / Shell Consistency Spec

## Problem statement (baseline)

The customer tab wrapped its primary white container in `maxWidth: 920` + `margin: 0 auto` + horizontal padding `6px`, while the title strip, info alert, and tabs used the **full inner width** of the 1280 shell. Visually, the customer surface felt **inset and “floating”** relative to the modules above.

## Target rules

1. **Single horizontal gutter** for shell content: parent `padding: 10px 18px 28px` remains the only outer horizontal inset.
2. **Customer primary shell** (`CustomerEntryTab` outer white card): spans `width: 100%` of the tab content area so its **left border** lines up with the title card and tabs.
3. **Internal rhythm**: customer white card body horizontal padding uses **18px** to match the title strip’s horizontal padding (`14px 18px 16px` on the chrome card).
4. **Tab bar**: `paddingLeft: 0` on `tabBarStyle` — no ad-hoc 2px nudge vs. content.

## Broker tab

Unchanged: already used `width: '100%'` without a narrower centered column; continues to align with chrome.

## Density note

Removing the 920 cap **widens** the customer column on large viewports; vertical spacing and card nesting from the density sprint are unchanged. If future readability work needs a cap, it should apply **consistently** to chrome + tabs + panels (one shared column token), not only the customer tab.
