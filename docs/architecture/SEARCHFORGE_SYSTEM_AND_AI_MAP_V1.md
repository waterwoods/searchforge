# SearchForge System and AI Map V1

**Date:** 2026-08-05  
**Scope:** Architecture diagrams for founder / FDE review  
**Runtime truth:** `docs/CURRENT_PRODUCT_SHAPE.md` · Reality: `docs/founder/SEARCHFORGE_CURRENT_REALITY_MAP_2026-08-05.md`  
**Secrets:** none in this document

---

## A. System architecture

```mermaid
flowchart TB
  subgraph Customer["Customer channel"]
    WX[WeChat / Mini Program]
  end

  subgraph API["Cloud Run FastAPI — fiqa-api / fiqa-api-qa"]
    CMD[Claim / H5 customer commands]
    DET[Deterministic Case workflow]
    LG[LangGraph Accident Story subworkflow]
    GR[Guardrails + kill switches]
    FB[Deterministic fallback / manual intake]
  end

  subgraph Persist["System of record"]
    PG[(Postgres / Cloud SQL)]
    EV[CaseEvent + projections]
    GCS[(GCS media — evidence photos)]
  end

  subgraph Broker["Broker surfaces"]
    WB[Vercel Broker Workbench]
    TL[Timeline / Brief / next action]
  end

  subgraph Obs["Observability"]
    MET[Durable metrics events]
    LS[LangSmith — redacted traces]
  end

  WX -->|API commands| CMD
  CMD --> DET
  CMD -->|propose / confirm stamp only| LG
  LG --> GR
  GR -->|LLM fail / timeout / invalid| FB
  GR -->|valid draft| WX
  WX -->|customer confirmation| DET
  DET --> EV
  EV --> PG
  DET --> GCS
  EV --> WB
  WB --> TL
  LG --> MET
  DET --> MET
  LG --> LS
  MET --> PG
```

**Hard boundary:** LangGraph may propose and stamp confirmed facts; it must not submit, close, or accept claims.

---

## B. Customer sequence

```mermaid
sequenceDiagram
  actor C as Customer
  participant MP as Mini Program
  participant API as FastAPI
  participant LG as LangGraph
  participant PG as Postgres
  participant B as Broker Workbench

  C->>MP: Free-form accident description
  MP->>API: propose (accident-story)
  API->>LG: normalize → extract → validate
  LG-->>API: AI draft + ≤3 missing questions
  API-->>MP: guided_view (draft ≠ fact)
  C->>MP: Answer missing questions
  C->>MP: Confirm facts
  MP->>API: Start Claim + customer_confirmed stamp
  API->>PG: Deterministic CreateClaim + events
  API-->>MP: Case status / next step
  B->>API: Load projection
  API->>PG: Read CaseEvent / Brief layers
  API-->>B: Original / AI proposal / confirmed facts + next action
  B->>B: Broker review (only confirmed = office truth)
```

---

## C. Safety boundary

```mermaid
flowchart TD
  IN[Customer story propose] --> FLAG{ACCIDENT_STORY_ASSISTANT_ENABLED?}
  FLAG -->|0 / office not allowlisted| MAN[Manual intake path]
  FLAG -->|1| LLM{LLM enabled + healthy?}
  LLM -->|timeout / invalid JSON / exception| GR[Guardrail]
  LLM -->|OK| VAL[Validate ≤3 Q / unknown≠no]
  VAL -->|conflict / unsafe| GR
  VAL -->|OK| DRAFT[Return AI draft for customer confirm]
  GR --> DET[Deterministic extractor or calm fallback copy]
  DET --> MAN
  MAN --> CLAIM[Start Claim still usable]
  DRAFT --> CONF{Customer confirms?}
  CONF -->|yes| STAMP[Stamp customer_confirmed]
  CONF -->|no / edit| MAN
  STAMP --> CLAIM
```

Customer-visible fallback copy (ZH) is server-owned in `accident_story_assistant/flags.py` — AI failure must not block submission.

---

## D. Infrastructure and environment map

```mermaid
flowchart LR
  subgraph Local["Local development"]
    LAPI[run_demo_local.sh :8001]
    LMP[WeChat DevTools / Preview]
    LUI[ui Vite local]
  end

  subgraph QA["Cloud QA"]
    QCR[fiqa-api-qa us-west1]
    QDB[(caseiq-qa on caseiq-pilot-pg)]
    QGCS[caseiq-wecom-media-qa]
    QV[Vercel Preview ui-waterwoods-…]
    QLS[LangSmith pilot project]
  end

  subgraph Prod["Production — separate"]
    PCR[fiqa-api]
    PDB[(caseiq)]
    PV[Vercel ui-smoky-beta]
  end

  subgraph Ext["External AI / ops"]
    OAI[OpenAI API]
    GH[GitHub]
    SM[Secret Manager]
  end

  LAPI --> QCR
  LMP --> QCR
  LUI --> QCR
  QCR --> QDB
  QCR --> QGCS
  QCR --> OAI
  QCR --> QLS
  QV --> QCR
  PCR --> PDB
  PV --> PCR
  QCR --> SM
  PCR --> SM
  GH --> QCR
```

| Environment | API | DB | Workbench | Mini Program | Accident Story |
|-------------|-----|----|-----------|--------------|----------------|
| Local | `:8001` | optional PG or JSON legacy | Vite | DevTools | flags via `.env` |
| Cloud QA | `fiqa-api-qa` | `caseiq-qa` | waterwoods Preview | `apiProfile=qa` | Restricted pilot target |
| Production | `fiqa-api` | `caseiq` | `ui-smoky-beta` | production profile | **Not authorized** by freeze |

Naming SSOT: `docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md`.

---

## E. Layer ownership (one glance)

| Layer | Owner | Probabilistic? |
|-------|-------|----------------|
| Claim lifecycle / status | Deterministic commands | No |
| Request More / office accept | Deterministic + broker | No |
| Accident fact proposal | LangGraph + optional LLM | Yes (bounded) |
| Fact authority | Customer confirm stamp | Human |
| Broker office truth | Confirmed facts only | Human |
| Tracing | LangSmith redacted meta | Observability only |
| Kill switch | Env flags on Cloud Run | Ops |

---

## Related code entry points

| Concern | Path |
|---------|------|
| Flags / kill switch | `services/fiqa_api/inbox_triage/accident_story_assistant/flags.py` |
| Graph | `.../accident_story_assistant/graph.py` |
| Guardrails | `.../guardrails.py` |
| Mini Program Start Claim | `miniapp/pages/start-claim/` |
| Broker Brief layers | claim workbench display (Brief labels) |
| Deploy naming | `docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md` |
