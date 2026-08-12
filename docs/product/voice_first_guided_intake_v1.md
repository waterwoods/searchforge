# Voice-first Guided Intake V1

**Status:** additive Mini Program front door (not a replacement architecture)
**Objective:** Let a customer speak the accident story first, then reuse Accident Story / Start Claim.

## Principle

VOICE IS INPUT → AI IS PROPOSAL → CUSTOMER CONFIRMATION IS AUTHORITY → Postgres / Case workflow remains system of record.

## Reuse map

| Existing component | Role in Voice-first |
|---|---|
| `pages/start-claim/start-claim` | Host page (`pages[0]`); voice door + guided + full form |
| `utils/voiceStoryInput.ts` + Chirp STT routes | Speech → editable transcript (never case truth) |
| `POST .../start-claim/story/transcribe` | Same Google Chirp SpeechProvider |
| Accident Story LangGraph (`accident_story_assistant`) | Normalize → extract → guardrails → ≤3 follow-ups |
| `POST .../accident-story/propose` | AI proposal (deterministic default; LLM optional) |
| Guided UX (`guidedAccidentStory.ts`) | Structured review + missing questions + confirm |
| `POST .../customer/start-claim` | Authoritative case create (Reliability Fix 2 path) |
| `?mode=text\|full\|legacy` / `?voice=0` | Escape to existing text / full intake |

## Customer states

IDLE → RECORDING → PROCESSING SPEECH → AI ORGANIZING → REVIEW / MISSING QUESTIONS → CUSTOMER CONFIRM → Start Claim

Every failure offers retry, text input, or full form. No dead ends.

## Escape / kill

- Config: `voiceFirstIntakeEnabled` (default `true` in `config.defaults.ts`)
- Query: `?mode=text`, `?mode=full`, `?mode=legacy`, `?voice=0`
- Backend Accident Story kill: `ACCIDENT_STORY_ASSISTANT_ENABLED=0` (manual intake still works)

## Out of scope (V1)

Realtime voice agent, streaming dialogue, liability automation, photo CV, GPS, new DB/queue/RAG, broker assistant, deploy.
