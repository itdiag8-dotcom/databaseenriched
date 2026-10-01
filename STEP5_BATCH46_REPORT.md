# STEP 5 — Batch 46: Kia + Hyundai LEMON Replacement (Step 55)

**Date:** 2026-10-01 · **Scripts:** `step55_step5_lemon_batch46_hmg.py`, `step55b_estimate_override.py`, `step55c_lambda_fill_fix.py`
**Result:** 20 LEMON rows (Kia 14, Hyundai 6) → **20 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 91 | **71** (−20) |
| LEMON Kia / Hyundai | 14 / 6 | **0 / 0** |
| engines rows | 5,745 | **5,725** (−20) |
| New engines | — | **0** |
| NULL power on batch targets | 20 | **0** |
| Orphans / count mismatches / fuel conflicts | — | **0 / 0 / 0** |

## Method

Hyundai and Kia share one engine catalogue (Nu, Gamma, Lambda, Smartstream), so they run as one
batch. Four of the targets are confirmed the way the JLR batch was: the crawl's fill and
viscosity match a spec already stored in this database.

| Crawl rows | Fill / viscosity | Stored spec | Target |
|---|---|---|---|
| Forte Koup SX 2015 (2 trims), Forte5 2016-2017 | 4.49-4.54 / 5W-30 | `G4FJ` = **4.5 / 5W-30** | 1.6 T-GDI, 201hp |
| Forte 2014/2016, Forte5 2018 | 4.0 / 5W-20 | `G4NA`,`G4NC` = **4.0 / 5W-20** | 2.0 Nu |
| K5 2025 | 5.77 / 0W-20 | `G4KN` = **5.8** | 2.5 Smartstream, 191hp |
| Optima 2001 | 4.49 | `G6BV` = **4.51** (the 2.4 four = 4.25) | 2.5 V6 Delta, 170hp |

Kia Forte rows then split on which body the crawl was describing: the sedan takes the volume
1.8 LX engine, the Forte5 hatchback was never sold with the 1.8 and takes the 2.0 GDI (2014) or,
once the fill returns to 4.0 L of 5W-20 in 2018, the 2.0 MPi at 147hp.

### When two signals disagree

The Genesis sedan rows are the interesting case. The fill steps from 5.19 L to 5.69 L and the
viscosity from 5W-20 to 5W-30, which brackets the change from the 3.8 Lambda MPi to the 3.8
Lambda II GDI — but the two signals disagree about *when*: viscosity changes for MY2012, fill
only for MY2013. US model knowledge settles it (the GDI engine arrived for MY2012), so
2010-2011 are `G6DA` at 290hp and 2012-2014 are `G6DJ` at 333hp, with the 2012 row's stale fill
recorded as a caveat in the evidence string rather than allowed to outvote the engine change.

## Fixes

**5 ROW_FIXES** (`STEP55_VERIFIED`) — descriptors for `G4FJ` (which carries different US and EU
ratings, 201 vs 184hp), `G4NBB`, `G4KN` (cylinder count was NULL), `G6BV` and `G6DA`.

**step55b** — 1 ESTIMATE override (`G4NBB`, off a 2.8 L placeholder onto the Nu family's 4.0 L),
5 normalizations, 1 power sync. **step55c** — reverts one of them: step55b had moved `G6DA` to
the crawl's 5.19 L (5.5 qt), but the Lambda 3.8 takes 6.0 qt, the same sump as the Lambda II GDI
that replaced it — and step55b had independently settled `G6DJ` at 5.69 L. Two engines of one
family cannot differ by half a quart in opposite directions; `G6DA` is set to 5.7 L.

## Skips

None.

## Files

- `step55_step5_lemon_batch46_hmg.py`, `step55b_estimate_override.py`, `step55c_lambda_fill_fix.py`
- `database_enriched/csv_exports/63_lemon_step55_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step55_2026-10-01.db`

**Next: Batch 47 — Smart (12) + Tesla (10) + Daewoo (9).**
