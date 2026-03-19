# Step 5B Seeds and Trust Tiers Update

**Date**: 2026-02-20  
**Purpose**: Add major insurance companies as discovery seeds and ensure correct trust tier classification

---

## Trust Tier Classification (Summary)

| Tier | Type | Domains | Score bonus |
|------|------|---------|-------------|
| **T0** | CA government (authoritative) | dmv.ca.gov, insurance.ca.gov, ca.gov | +30 |
| **T1** | Commercial insurers | geico.com, progressive.com, allstate.com, farmers.com, nationwide.com, libertymutual.com, travelers.com, aaa.com, usaa.com | +20 |
| **T2** | Reputable third-party | naic.org, iii.org, consumerreports.org, nerdwallet.com, valuepenguin.com, thezebra.com | +10 |
| **T3** | Unknown | (any other) | +2 |

CA government domains are top-tier authoritative for CA regulations. Insurance company domains are "commercial" tier—allowed and scored higher than unknown domains, but lower than .gov.

---

## What Was Added

### 1. Seed URLs Added

**File**: `scripts/discover_auto_insurance_sources.py`  
**Location**: Lines 41-50 (SEED_URLS list)

**Added seed URL**:
- `https://www.libertymutual.com/auto-insurance` (Liberty Mutual auto insurance page)

**Note**: The following insurers were already present in the seed list:
- ✅ Nationwide (`https://www.nationwide.com/personal/insurance/auto/`)
- ✅ State Farm (`https://www.statefarm.com/insurance/auto`)
- ✅ Progressive (`https://www.progressive.com/auto/`)
- ✅ Allstate (`https://www.allstate.com/auto-insurance`)
- ✅ Farmers (`https://www.farmers.com/insurance/auto`)
- ✅ GEICO (`https://www.geico.com/information/aboutinsurance/auto/`)

**Total seed URLs**: 9 (2 T0 gov + 7 T1 insurers)

### 2. Trust Tier Mapping Updated

**File**: `scripts/discover_auto_insurance_sources.py`  
**Location**: Lines 53-68 (DOMAIN_TRUST_TIERS dictionary)

**Added to T1 tier**:
- `libertymutual.com`

**Current T1 tier domains** (major insurers):
- `geico.com`
- `progressive.com`
- `statefarm.com`
- `allstate.com`
- `farmers.com`
- `nationwide.com`
- `libertymutual.com` ← **NEW**

**T0 tier** (unchanged - official CA government):
- `dmv.ca.gov`
- `insurance.ca.gov`
- `ca.gov`

---

## Code Changes Summary

### Files Modified
1. **`scripts/discover_auto_insurance_sources.py`**
   - **Line 49**: Added Liberty Mutual seed URL
   - **Line 58**: Added `libertymutual.com` to T1 trust tier set
   - **Lines 42-49**: Added comment clarifying seed URL organization

### Exact Changes

```python
# Before (line 49):
    "https://www.nationwide.com/personal/insurance/auto/",
]

# After (line 49-50):
    "https://www.nationwide.com/personal/insurance/auto/",
    "https://www.libertymutual.com/auto-insurance",
]
```

```python
# Before (line 58):
    "T1": {  # Top insurers already used
        "geico.com", "progressive.com", "statefarm.com", "allstate.com", "farmers.com", "nationwide.com"
    },

# After (line 58):
    "T1": {  # Top insurers - major insurance companies
        "geico.com", "progressive.com", "statefarm.com", "allstate.com", "farmers.com", "nationwide.com", "libertymutual.com"
    },
```

---

## How to Revert

To revert these changes:

1. **Remove Liberty Mutual seed URL**:
   - File: `scripts/discover_auto_insurance_sources.py`
   - Line 50: Delete the line `"https://www.libertymutual.com/auto-insurance",`

2. **Remove Liberty Mutual from T1 tier**:
   - File: `scripts/discover_auto_insurance_sources.py`
   - Line 58: Remove `, "libertymutual.com"` from the T1 set

3. **Restore original comment** (optional):
   - Line 57: Change comment back to `"T1": {  # Top insurers already used`

---

## Expected Behavior

### Robots.txt Compliance

The discovery script **always checks robots.txt** before fetching any URL (see `RobotsTxtChecker` class, lines 87-112). 

**Expected behavior when a domain is blocked by robots.txt**:
1. The seed URL check happens in `discover_from_seed()` method (line 320)
2. If blocked, a warning is logged: `"Blocked by robots.txt: {url}"`
3. The seed is skipped (no links discovered from that seed)
4. Discovery continues with the next seed URL
5. The blocked seed does not appear in candidates.json

**Note**: Some insurers (e.g., State Farm) may block crawlers via robots.txt. This is expected behavior and the script will automatically skip them. No manual intervention needed.

### Trust Tier Scoring

When a URL from a T1 insurer domain is discovered:
- **Score bonus**: +20.0 points (line 221-223)
- **Reason tag**: `"T1_top_insurer"` (line 223)
- This ensures T1 insurer pages rank higher than unknown domains (+2.0) but lower than T0 gov pages (+30.0)

### Seed URL Selection Criteria

All seed URLs follow these criteria:
- ✅ Use specific `/auto/` or `/car-insurance/` type pages (not homepages)
- ✅ Stable, publicly accessible pages
- ✅ Likely to contain links to other insurance-related content
- ✅ From major, reputable insurance companies

---

## Verification

### Quick Syntax Check
```bash
python3 -m py_compile scripts/discover_auto_insurance_sources.py
```
✅ Should exit with code 0 (no errors)

### Quick Test Run (2 minutes)
```bash
python3 scripts/discover_auto_insurance_sources.py \
  --max-runtime-minutes 2 \
  --max-candidates 80 \
  --output-dir /tmp/discovery_test_$(date +%Y%m%d_%H%M%S)
```

**Expected output**:
- Processes seeds (including Liberty Mutual if not blocked)
- Discovers candidate URLs from seed pages
- Writes `candidates.json` and `passing.json` to output directory
- If Liberty Mutual is blocked by robots.txt, you'll see: `"Blocked by robots.txt: https://www.libertymutual.com/auto-insurance"`

### Verify T1 Tier Classification
```bash
# Check that libertymutual.com is in T1 tier
grep -A 1 '"T1"' scripts/discover_auto_insurance_sources.py | grep libertymutual
```
✅ Should show: `"libertymutual.com"`

---

## Audit Trail

### Change Log
- **2026-02-20**: Added Liberty Mutual to seeds and T1 tier
  - Added: `https://www.libertymutual.com/auto-insurance` to SEED_URLS
  - Added: `libertymutual.com` to T1 trust tier
  - Verified: All other major insurers already present (Nationwide, State Farm, Progressive, Allstate, Farmers, GEICO)

### No Secrets Added
✅ No API keys, tokens, or credentials were added in this change.  
✅ Only public URLs and domain names were modified.

---

## Related Files

- **Discovery script**: `scripts/discover_auto_insurance_sources.py`
- **Long-run wrapper**: `scripts/run_step5b_discovery_longrun_2h.sh`
- **Verification script**: `scripts/verify_discovered_sources.py`
