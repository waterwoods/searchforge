# Add-Car-first pilot spec

## Product truth vs appearance (before this sprint)

| Dimension | Truth | Appearance risk (prior) |
|-----------|--------|-------------------------|
| Hero | Add-Car strongest | Title “客户统一受理与报送” felt category-generic |
| Tagline | Flagship = Add-Car | “汽车保险 · 客户统一受理与报送入口” implied equal coverage |
| Empty state | Recommend Add-Car first | “三种方式任选其一” flattened hierarchy |
| Pilot alert | Scope should be honest | Copy described generic “客户统一受理” without maturity gradient |
| Quick-start | Add-Car already primary button | Badge said “常用”, weaker than “recommended flagship path” |

## Add-Car-first pilot framing (target)

- **Say strongly:** Add-Car is the **primary path** for the pilot; structured + conversational Add-Car is the **hero workflow**.
- **Say explicitly:** Other车险事项 are **supported** but **整理深度 / 成熟度因场景而异**—no “全能助手” claim.
- **Visual / IA:** Keep all quick-start buttons; **elevate** Add-Car via default primary styling (existing), **推荐主路径** badge (configurable), and copy order (Add-Car first in numbered guidance).

## Intended improvements (page / flow / state / handoff)

- **Page:** Hero title and service tagline lead with Add-Car; header strip tagline matches “旗舰流程” language; customer tab suffix “报送入口（加车优先）”.
- **Flow:** Empty-state headline steers to Add-Car first; placeholder steers freeform users toward buttons/structured Add-Car when appropriate.
- **State:** No change to triage state machine—**presentation-only**.
- **Handoff:** Existing Add-Car handoff strings unchanged in this sprint; they already reinforce office-boundary authority.

## Emphasize

- Add-Car as **试点最成熟** / **旗舰流程** / **推荐主路径**.
- Office confirmation and non-autonomous boundary (pilot intro + existing tags).

## De-emphasize

- Language that sounds like **任意车险事项同等深度**.
- Implication that the tool is a **full office OS** (pilot intro “不做” line retained).

## Acceptance criteria

1. First screen (customer tab, empty thread) makes Add-Car the **obvious** first action.
2. Pilot intro states **Add-Car-first** and **maturity gradient** for other intents.
3. No backend / triage behavior change required for acceptance.
4. `npm run build` passes for `ui/`.
5. Client packs without new keys still get sensible defaults via `mergeUiCopy`.
