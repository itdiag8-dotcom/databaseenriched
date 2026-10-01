# STEP 5 — Batch 42: Dodge + Jeep + Chrysler LEMON Replacement (Step 51)

**Date:** 2026-10-01 · **Scripts:** `step51_step5_lemon_batch42_fca.py` + `step51b_estimate_override.py`
**Result:** 59 LEMON rows (Dodge 23, Jeep 21, Chrysler 15) → **59 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 242 | **183** (−59) |
| LEMON Dodge / Jeep / Chrysler | 23 / 21 / 15 | **0 / 0 / 0** |
| engines rows | 5,886 | **5,829** (−59 LEMON +2 new) |
| Fuel conflicts (all three brands) | — | **0** |
| NULL power on batch targets | 59 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## Why one batch

The three brands are one engine catalogue — the same `EDZ` 2.4, `EGA` 3.3, World Engine,
Pentastar, Hemi and Cummins rows serve all of them — so running them separately would mean
maintaining the same vocabulary three times and risking three different answers to the same
question. The merged batch uses `"BRAND:MODEL"` rule keys to keep the nameplates apart.

## Method — the fill ladder

| Fill | Engine |
|---|---|
| 4.25-4.56 L (4.5-4.8 qt) | `EDZ` 2.4, `ECN`/`ED3` World Engine, `420A` 2.0 |
| 4.73 L (5 qt) | `EGA` 3.3, `EGL` 3.8, new `EGW` 3.2, 2.0 GME 4xe |
| 5.2 L | `EGF` 3.5 V6 |
| 5.67 L (6 qt) | `3.6 Pentastar` |
| 6.62 L (7 qt) | `5.7 HEMI eTorque` |
| 11.35 L, 15W-40 | `ETH` 5.9 Cummins turbodiesel |

| Rows | Target | hp |
|---|---|---|
| Cirrus 2000, Sebring 2000-2003, Stratus 2000-2003 (8) | `EDZ` 2.4 | 150 |
| Concorde 2000-2001, Intrepid 2000 (3) | new `EGW` 3.2 V6 | 225 |
| Pacifica 3800CC 2008 | `EGL` 3.8 V6 | 197 |
| Town & Country 2000-2007, Grand Caravan 2001-2007 (15) | `EGA` 3.3 V6 | 180 |
| Avenger 2000 | new `420A` 2.0 | 140 |
| Caliber 2007-2012 (3) | `ECN` 2.0 World Engine | 158 |
| Compass + Patriot 2007-2016 (18), Journey 2010 | `ED3` 2.4 World Engine | 172-173 |
| Journey 2009 | `EGF` 3.5 V6 | 235 |
| Journey 2011, Grand Cherokee 2022 | `3.6 Pentastar` | 283 / 293 |
| Ram `5900CC` 2004-2009 (4) | `ETH` 5.9 Cummins | 325 |
| Grand Cherokee 2025 | `2.0 Turbo GME (4xe)` | 375 |
| Wagoneer 2023 | `5.7 HEMI V8 eTorque` | 392 |

Three decodes deserve a note:

- The **2000-2001 LH cars** record exactly 5 qt. The 2.7 V6 takes 6 qt and the 3.5 takes 5.5, so
  these are 3.2 V6 cars — an engine the database was missing entirely until this batch.
- The **Journey** changes engine three years running and the fills follow it exactly: 5.2 L (3.5
  V6, 2009) → 4.25 L (2.4 four, 2010) → 5.67 L (Pentastar, 2011).
- **Grand Cherokee 2025** records 5 qt, which is the 2.0 GME of the **4xe plug-in hybrid**, not
  the Pentastar's 6 qt.

## 5 fuel corrections

The four Ram `5900CC` rows were filed as Petrol; 11.35 L of 15W-40 is a Cummins, so they are now
Diesel. The Grand Cherokee 2025 row becomes Hybrid with the 4xe powertrain.

## 2 new engines

| Code | Engine | cc | hp |
|---|---|---|---|
| `EGW` | 3.2 V6 SOHC 24v (Concorde LXi / Intrepid ES) | 3231 | 225 |
| `420A` | 2.0 I4 DOHC 16v (Neon / Avenger / Sebring coupe) | 1996 | 140 |

## Fixes

**8 ROW_FIXES** (`STEP51_VERIFIED`) — `EGL`, `EGF`, `EGG` and `ED3` were all recorded with the
wrong cylinder count (8 or 6 where the engines are V6s and an inline four), `ETH` was listed as
an 8-cylinder when the 5.9 Cummins is an **I6**, and `EDZ`, `EGA`, `ECN` gained US ratings.

**step51b** — 1 ESTIMATE override (`EGL`), 5 normalizations and 10 power syncs. Each
normalization was sanity-checked: `EDZ` 4.73 → 4.25 L and `EGA` 4.25 → 4.73 L correct a pair of
swapped fills, `EGW` moves to the period-correct 10W-30, the Pentastar to 5W-30 and the 4xe to
0W-20.

## Skips

None.

## Evidence

[FCAUS] Chrysler/Dodge/Jeep US model-year specifications · [LEMONFILL] per-row oil fill and
viscosity recorded by the crawl.

## Files

- `step51_step5_lemon_batch42_fca.py`, `step51b_estimate_override.py`
- `database_enriched/csv_exports/59_lemon_step51_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step51_2026-10-01.db`

**Next: Batch 43 — Hummer (19 LEMON rows).**
