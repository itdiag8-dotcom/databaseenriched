# STEP 5 — Batch 28: Mitsubishi LEMON Replacement (Step 37)

**Date:** 2026-10-01 · **Scripts:** `step37_step5_lemon_batch28_mitsubishi.py` + `step37b_estimate_override.py` + `step37c_ev_oil_and_eva_capacity.py`
**Result:** 138 LEMON Mitsubishi rows → **138 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 1,160 | **1,022** (−138) |
| LEMON Mitsubishi | 138 | **0** |
| engines rows | 6,782 | **6,645** (−138 LEMON +1 new) |
| Orphans / count mismatches / Mitsubishi fuel conflicts | — | **0 / 0 / 0** |
| Mitsubishi variants with NULL power | 8 | **8** (pre-existing, see below) |

Mitsubishi fuels after: Petrol 539 · Diesel 144 · Electric 9.

## Method — nameplate generation + displacement

Mitsubishi's North American range is small and each nameplate had at most two engines per
generation, so displacement in the crawl code resolves every row; no VIN digit was needed
(the Lancer/Outlander `VINU`/`VINW` tokens agree with displacement and are kept in the evidence).

- **Eclipse** — 3G `2005`: 4G64 2.4 **147** / 6G72 3.0 **200**. 4G `2006-12`: 4G69 2.4 **162** /
  6G75 3.8 **263**, the V6 uprated to **265** for `2009-12` with the revised fascia and dual
  exhaust. The bare `2011` row takes the GS volume engine. [MMPR06][WIKIECL][DRVCHI05]
- **Eclipse Cross** — the crawl files it under "Eclipse", so the `2018-2025` rows are the
  crossover: 4B40 1.5 turbo **152**, its only engine. [MMLINEUP]
- **Galant / Endeavor / Montero** — one PS-platform V6 at three factory ratings: Galant 3.8
  **230** (Ralliart tune 258, documented on the engine row), Endeavor **225**, Montero **215**;
  Galant 2.4 = 4G69 **160**, which is also the only engine left for the bare `2010-12` rows.
- **Lancer** — 4G94 2.0 **120** (`2005-07`) → 4B11 2.0 **152** (`2008-15`) → **148** (`2016-17`,
  VIN U, revised rating); the 2.4 rows (VIN W) are 4B12 **168**. [MMLINEUP][CD_OLS]
- **Outlander** — 4G69 **160** (`2005-06`) → 4B12 2.4 **168** (`2007-13`) / **166** (`2014-20`)
  and 6B31 3.0 **220** (`2007-13`) / **224** (`2014-20`); `2021-25` is the 4th-generation CMF-C
  car with the Nissan-derived **PR25DD** 2.5 **181**.
- **Outlander Sport** — the `2000CC` Outlander rows and the `OUTLANDERSPO` trim row are the
  smaller RVR-based car: 4B11 2.0 **148**, with 4B12 2.4 **168** on the VIN W rows. Car and Driver
  and TrueCar both list 4B11 as the OEM code for the 148-hp 2.0. [CD_OLS][TRUECAR_OLS]
- **Mirage** — 3A92 1.2 three-cylinder **74** (`2014-16`) → **78** from the 2017 facelift; the five
  `2015` trim rows (DE/ES × auto/manual, RF) all take the same single engine.
- **Raider** — a rebadged Dodge Dakota, so the Chrysler codes apply: EKG 3.7 V6 **210** standard,
  EVA 4.7 V8 **230** on the `4700CC` rows. [RAIDER]
- **i-MiEV** — Y4F1 traction motor, 49 kW / **66 hp**; all four rows fuel-corrected
  Petrol → **Electric**. [IMIEV]

## New engine (1)

| Code | Engine | Fuel | cc | hp |
|---|---|---|---|---|
| `4B40` | 1.5 I4 DOHC MIVEC turbo DI (Eclipse Cross 2018-2025) | Petrol | 1498 | 152 |

All 13 other targets (4G64, 4G69, 4G94, 4B11, 4B12, 6G72, 6G75, 6B31, 3A92, EKG, EVA, PR25DD,
Y4F1) already existed and were reused.

## Fixes

**11 ROW_FIXES** — the Mitsubishi rows were full of placeholder descriptors and wrong cylinder
counts: **4G69 cylinders 6→4** (and `brand_example` was *BYD*), **4B12 6→4**, 3A92 4→**3**
(it is a three-cylinder), plus real descriptors for 4B11/6G75/6B31/4G94/4G64/EKG/EVA. **Y4F1**
("CITYROVER") is now described as the i-MiEV traction motor and rated 66 hp.

**step37b** — 9 ESTIMATE oil-spec overrides (3A92, 4B11, 4B12, 4G64, 4G69, 4G94, 6B31, 6G72,
6G75), 3 normalizations, 2 power syncs.

**step37c** — two spec repairs: EVA's oil capacity restored to **5.67 L** (the 4.7 V8 takes 6 US
qt; step37b's crawl majority had pulled in the 3.7 V6's 4.73 L), and the **heuristic engine-oil
specs deleted from 16 battery-electric engine rows** (the i-MiEV's Y4F1 was listed as "5W-30,
3.1 L"). LEMON-sourced EV codes already carry NULL oil specs, so this aligns the vivid-imported
ones with that convention; the BMW i3 row, whose values are explicitly the range-extender's, is
left alone.

## Skips

None. The 8 Mitsubishi variants still without a power figure are pre-existing non-LEMON rows
(Adventure/Freeca `4D56IT`, Montero/Nativa/Shogun Sport/Triton `4M41IT`, Grunder `2.4 16v`) whose
engine rows carry no rating; they are outside this batch's scope and are left for a later
engine-row pass rather than guessed at.

## Evidence

[MMPR06] media.mitsubishicars.com 2006 Eclipse powertrain press kit ·
[WIKIECL] en.wikipedia.org Mitsubishi Eclipse (4th generation) ·
[DRVCHI05] drivechicago.com 2006 Eclipse review (2005 ratings: 147hp I4, 200hp 3.0 V6) ·
[CD_OLS] caranddriver.com Outlander Sport + cars.com 2023 Outlander Sport ·
[TRUECAR_OLS] truecar.com Outlander Sport specs (OEM engine code 4B11 for the 148hp 2.0) ·
[RAIDER] Dakota/Raider shared-powertrain history · [IMIEV] i-MiEV Y4F1 motor specification ·
[MMLINEUP]/[MMVOCAB] US/CA lineup ratings by model year + existing verified rows in `engines`.

## Files

- `step37_step5_lemon_batch28_mitsubishi.py`, `step37b_estimate_override.py`,
  `step37c_ev_oil_and_eva_capacity.py`
- `database_enriched/csv_exports/45_lemon_step37_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step37_2026-10-01.db`

**Next: Batch 29 — Ford + Mercury (85 + 63 = 148 LEMON rows, shared Ford engine family).**
