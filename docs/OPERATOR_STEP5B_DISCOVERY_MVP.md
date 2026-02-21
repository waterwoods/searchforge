# Step 5B MVP: Auto-Discover New Insurance Information Sources

## Overview

This MVP implements an automated discovery pipeline that finds new candidate URLs for auto-insurance RAG data sources. The pipeline discovers candidates from seed pages, scores them with best-practice heuristics, filters to passing candidates, and optionally appends safe domains to `data_sources.json`.

## Quick Start

### Run the MVP Pipeline

```bash
bash scripts/run_step5b_discovery_mvp.sh
```

This command:
1. Discovers candidate URLs from seed pages
2. Scores and filters candidates
3. Verifies passing candidates (crawls 5 pages)
4. Generates output files

**Expected runtime:** 5-10 minutes

### Output Files

All outputs are written to `results/auto_insurance_discovery/`:

- **`candidates.json`**: All discovered candidates with scores and metadata
- **`passing.json`**: Filtered list of passing candidates (score >= 15.0, max 5 per domain)
- **`REPORT.md`**: Human-readable summary with top candidates and statistics
- **`verify_corpus.jsonl`**: Verification crawl results (5 pages from 1-2 passing sources)

## Acceptance Criteria

✅ **PASS** if:
1. Pipeline completes in <10 minutes
2. `candidates.json` contains 10-30 candidates
3. `passing.json` contains 5-15 URLs across 2-5 domains
4. `REPORT.md` is generated with summary
5. `verify_corpus.jsonl` contains 5 documents

## Discovery Strategy

### Seed Pages

The discovery starts from curated seed URLs:
- `dmv.ca.gov` - California DMV insurance requirements
- `insurance.ca.gov` - California Department of Insurance
- `geico.com`, `progressive.com`, `statefarm.com` - Top insurers
- `allstate.com`, `farmers.com`, `nationwide.com` - Additional insurers

### Discovery Process

1. **Fetch seed pages** and extract outgoing links
2. **Normalize URLs** (remove query params, fragments, trailing slashes)
3. **Filter links**:
   - Exclude binary files (PDF, DOC, images, etc.)
   - Exclude non-content pages (login, account, careers, etc.)
   - Exclude URLs with long query strings (>100 chars)
4. **Check robots.txt** for each candidate URL
5. **Fetch and extract** content from candidates
6. **Score candidates** using heuristics

### Scoring Heuristics

Candidates are scored based on:

1. **Domain Trust Tier**:
   - T0 (30 pts): Official CA gov domains (`dmv.ca.gov`, `insurance.ca.gov`)
   - T1 (20 pts): Top insurers already used (`geico.com`, `progressive.com`, etc.)
   - T2 (10 pts): Reputable sources (`naic.org`, `iii.org`, `nerdwallet.com`, etc.)
   - T3 (2 pts): Unknown domains

2. **Keyword Matching**:
   - URL keywords: +2 pts per match (insurance, auto, car, liability, coverage, etc.)
   - Title keywords: +1.5 pts per match

3. **Content Quality**:
   - 1200+ chars: +15 pts
   - 500+ chars: +8 pts
   - 200+ chars: +3 pts

4. **Penalties**:
   - Long query string: -5 pts

### Filtering Rules

A candidate **passes** if:
- Not blocked by robots.txt
- Score >= 15.0
- Max 5 URLs per domain

## Verification

The verification step:
- Loads `passing.json`
- Selects 1-2 domains
- Fetches up to 5 pages total
- Extracts text content
- Writes `verify_corpus.jsonl`

**Note:** Verification does NOT touch Qdrant. It only creates a small JSONL file for manual review.

## Optional: Append to data_sources.json

If passing domains are safe and from reputable sources, you can append them to `data_sources.json`:

```bash
python3 scripts/append_discovered_to_data_sources.py
```

This script:
- Reads `passing.json`
- Groups URLs by domain
- Creates a new `ds_auto_discovered_001` entry
- Appends to `docs/prompt2_input/data_sources.json`
- **Does NOT modify** existing `ds_001` through `ds_005` entries

**Warning:** Only run this if you've manually reviewed the passing candidates and confirmed they're safe.

## Manual Review Checklist

Before appending to `data_sources.json`, verify:

- [ ] Passing domains are reputable (gov, known insurers, or trusted consumer sites)
- [ ] URLs are publicly accessible and don't require authentication
- [ ] Content is relevant to auto insurance
- [ ] Robots.txt allows crawling
- [ ] No personal information or sensitive data in URLs

## Troubleshooting

### Discovery returns few candidates

**Possible causes:**
- Seed pages changed or are down
- Robots.txt blocking many URLs
- Network issues

**Solutions:**
- Check seed URLs are accessible
- Review `candidates.json` for robots.txt blocks
- Increase `max_candidates` in `discover_auto_insurance_sources.py`

### All candidates have low scores

**Possible causes:**
- Seed pages don't link to insurance content
- Content extraction failing

**Solutions:**
- Review `candidates.json` for content_length values
- Check if titles are being extracted correctly
- Adjust scoring thresholds if needed

### Verification fails

**Possible causes:**
- URLs are no longer accessible
- Network timeout

**Solutions:**
- Check URLs manually in browser
- Increase timeout in `verify_discovered_sources.py`
- Review `passing.json` for valid URLs

## File Structure

```
scripts/
  discover_auto_insurance_sources.py    # Main discovery script
  verify_discovered_sources.py          # Verification crawl script
  run_step5b_discovery_mvp.sh           # Runner script
  append_discovered_to_data_sources.py # Optional: append to data_sources.json

results/auto_insurance_discovery/
  candidates.json                        # All candidates
  passing.json                           # Filtered passing candidates
  REPORT.md                              # Human-readable report
  verify_corpus.jsonl                    # Verification crawl results
```

## Constraints

- **Respects robots.txt**: Never crawls blocked domains
- **English-first**: Defaults to English sources (Chinese is a plus but not required)
- **Allowlist-by-domain**: Main guardrail; unknown domains get low scores
- **No quirky hacks**: Uses best-practice heuristics only
- **Small and reversible**: Changes are minimal and can be rolled back

## Next Steps

After MVP:
1. Review `REPORT.md` and `passing.json`
2. Manually verify top candidates
3. (Optional) Run `append_discovered_to_data_sources.py` if safe
4. Integrate into production pipeline if successful
