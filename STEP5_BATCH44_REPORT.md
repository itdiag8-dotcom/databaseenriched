# STEP 5 — Batch 44: Hummer + Cadillac + GMC + Pontiac LEMON Replacement (Step 53)

**Date:** 2026-10-01 · **Scripts:** `step53_step5_lemon_batch44_gm.py` + `step53b_estimate_override.py`
**Result:** 28 LEMON rows (Hummer 19, Cadillac 7, GMC 1, Pontiac 1) → **28 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 146 | **118** (−28) |
| LEMON Hummer / Cadillac / GMC / Pontiac | 19 / 7 / 1 / 1 | **0 / 0 / 0 / 0** |
| engines rows | 5,800 | **5,772** (−28) |
| New engines | — | **0** (GM's catalogue was already complete) |
| NULL power on batch targets | 28 | **0** |
| Orphans / count mismatches / fuel conflicts | — | **0 / 0 / 0** |

## Why one batch

These are the last four GM brands in the queue and they share one engine catalogue: the Vortec
6000 under a Hummer H2 is the same `LQ4` as under an Escalade, and the Atlas inline fives of the
H3 are the Colorado/Canyon engines. No new engine rows were needed — every target already
existed, which is what a shared catalogue should look like by this point in the project.

| Rows | Target | hp |
|---|---|---|
| Hummer H2 2003-2007 (5) | `LQ4` 6.0 V8 Vortec | 325 |
| Hummer H2 2008-2009 (2) | `L92` 6.2 V8 | 393 |
| Hummer H3 2006 / 2007 | `L52` 3.5 I5 / `LLR` 3.7 I5 Atlas | 220 / 242 |
| Hummer H3 + H3T `3700CC` 2008-2010 (5) | `LLR` 3.7 I5 Atlas | 239 |
| Hummer H3 + H3T `5300CC` 2008-2010 (5) | `LH8` 5.3 V8 (Alpha) | 300 |
| Cadillac Escalade 2002-2006 (5) | `LQ4` 6.0 V8 Vortec | 345 |
| Cadillac CTS `6200CC` 2015 | `LSA` 6.2 supercharged (CTS-V) | 556 |
| Cadillac STS 2011 | `LLT` 3.6 V6 DI | 302 |
| GMC Sierra `6000CC` VIN J 2012 | `LC8` 6.0 V8 gaseous-fuel capable | 306 |
| Pontiac Grand 2005 | `L61` 2.2 Ecotec | 140 |

## The two rows that had been parked

Both of the rows earlier batches set aside as un-decodable resolve here, and neither needed a
guess:

- **GMC Sierra 2012** carries VIN engine character **J**. On a 2012 HD truck that character is
  the gaseous-fuel-capable 6.0 (`LC8`), not the 360hp `L96`, so the VIN settles it without any
  knowledge of the trim.
- **Pontiac "GRAND" 2005** has a truncated nameplate that could be a Grand Am or a Grand Prix.
  But the question the database has to answer is which *engine*, and the 4.73 L (5 qt) fill only
  fits the 2.2 Ecotec — the 3.4 V6 and the 3800 Series III both take 4.5 qt. The engine is
  decodable even where the model name is not, and the row is mapped with that caveat recorded in
  its evidence string.

## Fixes

**4 ROW_FIXES** (`STEP53_VERIFIED`) — `LH8` and `LQ9` carried placeholder descriptors ("5.3
(est.)", "6 (est.)"), `L92` read simply "6.2", and `L61` was labelled with its late 182hp rating
alone. **step53b**: 1 normalization (`LLT` 5.2 → 5.67 L, the 3.6 DI's 6 qt) and 1 power sync.

## Skips

None.

## Files

- `step53_step5_lemon_batch44_gm.py`, `step53b_estimate_override.py`
- `database_enriched/csv_exports/61_lemon_step53_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step53_2026-10-01.db`

**Next: Batch 45 — Land Rover (15) + Jaguar (12).**
