# Founder Notes — Case Persistence (Unified Intake)

## One-sentence truth

**We already save real cases to disk** when the broker (or demo) asks the API to persist and the conversation is ready to become a case—but it’s **one JSON file plus a folder for uploads**, not a bank-grade database.

## What brokers can rely on today

- After a case exists, **status**, **follow-up plan** (who we’re waiting on + when to contact), **broker notes**, **new customer messages** (append), and **attachments** all **stick** across refreshes **on the same server** with the same `data/` directory.

## What they should not assume

- **Multi-server** deployments (Cloud Run replicas) will **not** share this file automatically.
- There is **no** built-in backup, encryption, or legal hold—**you** define retention and export policy.
- **Demo queue** is a **UI convenience** to seed examples; it is not the persistence layer.

## Commercial direction (plain language)

When you sell beyond a single machine: move **case records** to **PostgreSQL** and **files** to **S3-style storage**, keep **metadata in the database**, and use the current JSON layout as a **migration source**, not the long-term source of truth.

## Why this sprint mattered

Aligns **engineering reality** with **sales narrative**: you can honestly say “cases persist” while also saying “next step is enterprise storage” without contradiction.
