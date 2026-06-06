# pipelines/ — SearchForge Data Pipelines

**Status:** LAB ONLY — optional  
**Unified Intake paid pilot:** Not used  
**Mounted in product_only:** No  
**Safe to ignore:** Yes  
**Archived:** No  
**Experimental:** Yes

---

## Historical purpose

ETL, corpus ingestion, batch indexing, and offline pipeline runners for SearchForge R&D.

## Product truth

Broker case persistence is Postgres via `SERVICE_RECORD_DATABASE_URL`. Optional Qdrant wedge uses targeted ingest scripts under `scripts/`, not this directory tree.
