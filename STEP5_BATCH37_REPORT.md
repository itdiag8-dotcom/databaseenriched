# STEP 5 — Batch 37: Isuzu LEMON Replacement (Step 46)

**Date:** 2026-10-01 · **Scripts:** `step46_step5_lemon_batch37_isuzu.py` + `step46b_estimate_override.py`
**Result:** 35 LEMON rows → **35 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 402 | **367** (−35) |
| LEMON Isuzu | 35 | **0** |
| engines rows | 6,047 | **6,014** (−35 LEMON +2 new) |
| Isuzu fuel conflicts | — | **0** |
| Isuzu variants with NULL power | 35 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## Method

Isuzu's last US decade splits in two, and the batch decodes each half differently.

**Isuzu's own cars** — displacement tokens carry the Amigo and Rodeo rows:

| Rows | Target | hp |
|---|---|---|
| Amigo/Rodeo 2200CC (5) | new `X22SE` 2.2 DOHC I4 | 130 |
| Amigo/Rodeo 3200CC (5) | new `6VD1` 3.2 V6 | 205 |
| Rodeo 2004 (1) | `6VE1` 3.5 V6 — the only engine left in its final year | 250 |
| Axiom 2002-2004 (3) | `6VE1` | 230 → 250 for 2004 |
| Trooper 2000-2002, VehiCROSS 2000-2001 (5) | `6VE1` | 215 |

**GM rebadges** — decoded from the nameplate plus the crawl's oil fill:

| Rows | Fill | Target | hp |
|---|---|---|---|
| Hombre 2000 | 4.16 L | `LN2` 2.2 I4 (Chevrolet S-10) | 120 |
| Ascender 4200CC + bare 2003/2007/2008 (6) | 6.62 L | `LL8` 4.2 I6 Atlas | 275 → 291 from 2006 |
| Ascender 5300CC 2004 | 5.67 L | `LM4` Vortec 5300 | 290 |
| Ascender 5300CC 2005-2006 | 5.67 L | `LH6` Vortec 5300 with Displacement on Demand | 300 |
| i-280 2006 | 4.73 L | `LK5` 2.8 I4 Atlas | 175 |
| i-290 2007-2008 | 4.73 L | `LLV` 2.9 I4 Atlas | 185 |
| i-350 2006 | 5.67 L | `L52` 3.5 I5 Atlas | 220 |
| i-370 2007-2008 | 5.67 L | `LLR` 3.7 I5 Atlas | 242 |

The Ascender 5.3 rows are the one place where the year matters inside a single displacement: GM
switched the Vortec 5300 from the aluminium-block LM4 to the DoD-equipped LH6 for MY2005, so the
2004 row and the 2005-2006 rows take different engines.

## 2 new engines

| Code | Engine | cc | hp |
|---|---|---|---|
| `X22SE` | 2.2 I4 DOHC 16v (Amigo/Rodeo 2000-2003) | 2198 | 130 |
| `6VD1` | 3.2 V6 DOHC 24v (Amigo/Rodeo/Trooper) | 3165 | 205 |

## Fixes

**6 ROW_FIXES** (`STEP46_VERIFIED`) — the GM Atlas rows were carrying wrong cylinder counts and
placeholder types: `LLV` ("2.9", 6 cylinders) is a 2.9 **I4**, `LLR` ("3.7 (est.)", 8 cylinders)
and `L52` ("3.5", 6 cylinders) are **I5**s, and `LK5`, `LH6` and `6VE1` gained descriptors naming
the cars and their ratings.

**step46b** — 1 ESTIMATE override (`6VE1` → 5W-30 / 4.73 L), 3 normalizations and 5 power syncs.
The two viscosity normalizations (`X22SE` and `6VD1` → 10W-30) were kept deliberately: 10W-30 is
what Isuzu specified for these engines in 2000-2003, and it is what the crawl recorded on every
Rodeo row. 0 ESTIMATE specs and 0 spec-vs-engine power mismatches remain.

## Skips

None.

## Evidence

[ISUZUUS] Isuzu US model-year specifications (own engines and the GM rebadges) ·
[LEMONFILL] per-row oil fill recorded by the crawl, which separates the 2.2 I4 (4.54 L), the
V6s and Atlas fours (4.73 L), the Atlas fives and Vortec 5300 (5.67 L) and the 4.2 I6 (6.62 L).

## Files

- `step46_step5_lemon_batch37_isuzu.py`, `step46b_estimate_override.py`
- `database_enriched/csv_exports/54_lemon_step46_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step46_2026-10-01.db`

**Next: Batch 38 — Saab (34 LEMON rows).**
