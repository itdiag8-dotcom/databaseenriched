# STEP 5 — Batch 39: Lexus LEMON Replacement (Step 48)

**Date:** 2026-10-01 · **Scripts:** `step48_step5_lemon_batch39_lexus.py`, `step48b_estimate_override.py`, `step48c_es300h_fuel_fix.py`
**Result:** 31 LEMON rows → **31 mapped (100%) / 0 skips** (12 volume defaults, flagged)

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 333 | **302** (−31) |
| LEMON Lexus | 31 | **0** |
| engines rows | 5,981 | **5,950** (−31 LEMON, no new rows needed) |
| Lexus fuel conflicts on batch targets | 1 | **0** |
| Lexus variants with NULL power | 31 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## Method — fill *and* viscosity

Every row is a bare nameplate+year (ES, IS and RC for 2016-2025 plus a single SC 2000), so the
decode runs entirely on the service data the crawl attached to each row. Toyota's families
separate by fill, and the newest one separates by **viscosity**: 0W-16 is specified for the 2.5
Dynamic Force engine and nothing else in this line-up.

| Fill / viscosity | Engine |
|---|---|
| 4.35 L, 0W-20 | `2AR-FXE` 2.5 hybrid (ES 300h) |
| 4.54 L, **0W-16** | `A25A-FKS` 2.5 Dynamic Force (ES 250) |
| 4.63 L, 0W-20 | `8AR-FTS` 2.0 turbo (IS/RC 200t-300) |
| 5.39 L, 0W-20 | `2GR-FKS` 3.5 V6 (ES 350) |
| 5.67-6.43 L, 0W-20 | `2GR-FKS` 3.5 V6 (IS/RC 350) |
| 6.05 L, 0W-20 | `2GR-FE` 3.5 V6 (pre-2018 ES 350) |
| 5.20 L, 5W-30 | `2JZ-GE` 3.0 I6 (SC 300) |

- **ES**: 2016-2017 `2GR-FE` 268 hp → **2018 `2AR-FXE`**, where the fill drops to 4.35 L, which
  only the ES 300h hybrid matches; the row's fuel is corrected from Petrol to Hybrid → 2019-2020
  `2GR-FKS` 302 hp → 2021-2025 `A25A-FKS` 203 hp on the 0W-16 signature.
- **IS / RC**: 2016-2017 `8AR-FTS` 241 hp, then `2GR-FKS` 311 hp from 2018.
- **SC 2000**: 5.2 L is the SC 300's straight six (225 hp); the SC 400's V8 takes 5.6 L.

### Volume defaults (12)

From MY2018 the IS and RC ranges also contain a 5.0 V8 halo car (RC F from 2018, IS 500 from
2022, both `2UR-GSE` 472 hp) whose fill overlaps the V6's, so the 2018-2025 IS and RC rows take
the volume 350 V6. Flagged in the decision CSV rather than presented as certainties.

## New engines

None — the Toyota/Lexus vocabulary already in the database covered every target.

## Fixes

**4 ROW_FIXES** (`STEP48_VERIFIED`) — `2AR-FXE` was recorded as a **6-cylinder** (it is the 2.5
inline four) and `A25A-FKS` had a NULL cylinder count; `2GR-FE` and `2GR-FKS` gained descriptors
listing their per-model ratings instead of a single car's.

**step48b** — 0 ESTIMATE overrides, 2 normalizations (`2GR-FKS` 5.48 → 6.43 L, `2JZ-GE` 5.39 →
5.2 L), 0 power syncs; the crawl data agreed with the existing specs almost everywhere.

**step48c** — the fuel conflicts touching a batch target: a pre-existing ES variant on the AVV6
(ES 300h) bodyshell and a Camry variant on the AVV5 shell, both linked to `2AR-FXE` but flagged
Petrol. AVV5/AVV6 are the hybrid bodyshells, so the fuel flag was corrected rather than the
engine link. The other 9 Lexus conflicts sit on rows this batch never touched.

## Skips

None.

## Evidence

[LEXUSUS] Lexus USA model-year specifications · [LEMONFILL] per-row oil fill and viscosity
recorded by the crawl.

## Files

- `step48_step5_lemon_batch39_lexus.py`, `step48b_estimate_override.py`, `step48c_es300h_fuel_fix.py`
- `database_enriched/csv_exports/56_lemon_step48_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step48_2026-10-01.db`

**Next: Batch 40 — Mini (31 LEMON rows).**
