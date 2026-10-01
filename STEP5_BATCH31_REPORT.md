# STEP 5 — Batch 31: BMW LEMON Replacement (Step 40)

**Date:** 2026-10-01 · **Scripts:** `step40_step5_lemon_batch31_bmw.py` + `step40b_estimate_override.py` + `step40c_oil_spec_corrections.py` + `step40d_bmw_hybrid_and_fuel_cleanup.py`
**Result:** 83 LEMON rows → **83 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 741 | **658** (−83) |
| LEMON BMW | 83 | **0** |
| engines rows | 6,371 | **6,290** (−83 LEMON +2 new) |
| BMW fuel conflicts | 38 | **0** |
| DB-wide fuel conflicts | 181 | **141** |
| BMW variants with NULL power | 83 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## The hardest row shape in the queue

Every other batch had displacements to work with. BMW's 83 rows have **none** — no `_NNNNCC_`,
no VIN digit, no trim in 80 of 83 codes. A row is literally `LEMON_BMW_X5_2013`. The crawl also
truncates sub-brand names, so two nameplates needed identifying before any rule could be written:

- **`M`** (2000-2002, 2006-2008) is the **M roadster / M coupe**. An `M3` or `M5` row would have
  kept its digit (and other brands' rows in this crawl do), so these are the two-word names.
  2000 is still the US-spec S52B32 240 hp; 2001-02 is the S54B32 at 315 hp; the 2006-08 rows are
  the Z4 M at 330 hp.
- **`ACTIVEHYBRID`** (2012-2016) is the ActiveHybrid 3/5 sedan — and here the crawl's `fuel`
  column (Hybrid on all five) confirms it. BMW's US press kits give the same powertrain for both:
  the 300 hp N55 inline-six plus a 55 hp motor inside the 8-speed, **335 hp combined**
  [BMWPR_AH5][BMWPR_AH3][CD_AH3]. ActiveHybrid 5 is a MY2012 car and ActiveHybrid 3 a MY2013 car,
  so the whole 2012-2016 span is covered by one rule.

Everything else is nameplate generation + the US volume engine for the year, which works because
BMW's US lineup per nameplate is narrow (often a single engine):

| Nameplate | Decode |
|---|---|
| X3 | E83 3.0i M54 **225** → E83 LCI 3.0si/xDrive30i N52 **260** → F25 xDrive28i N52 **240** → G01 xDrive30i B48 **248** |
| X4 / X2 / X1 | B48 2.0 turbo: xDrive30i **248**, X2 xDrive28i **228**, U11 X1 xDrive28i **241** |
| X5 | MY2000 E53 was **4.4i only** (M62TU **282**) → xDrive35i N55 **300** → G05 xDrive40i B58 **335** |
| X6 | E71/F16 xDrive35i N55 **300** → G06 xDrive40i B58 **335** |
| Z3 / Z4 | 2.3 M52TU **170** → 2.5i M54 **184** → E85 3.0i N52 **215** → E89 sDrive30i N52 **255** → G29 sDrive30i B48 **255** |
| 535i / 550i 2017 | the F07 5 Series GT, the last US cars with those badges: N55 **300**, N63TU **445** |

Three trim-suffixed rows were handled by TRIM rules: `X5_2015_X5M` → S63B44T2 **567 hp**,
`X5_2015_X5XDRIVE50I` → N63TU **445 hp**, `ACTIVEHYBRID_2015_ACTIVEHYBRID` → the N55 hybrid.

## 2 new engines

| Code | Engine | cc | hp | fuel |
|---|---|---|---|---|
| `N55B30 (ActiveHybrid)` | 3.0 I6 TwinPower Turbo + 55 hp motor (ActiveHybrid 3/5) | 2979 | 335 | Hybrid |
| `N63B44 (ActiveHybrid)` | 4.4 V8 TwinTurbo + motor (ActiveHybrid 7 455 / X6 480) | 4395 | 455 | Hybrid |

## Fixes

**10 ROW_FIXES** (`STEP40_VERIFIED`) — the BMW rows were full of wrong cylinder counts (`N55B30A`
and `N52B30A` recorded as 4-cylinder) and single-application descriptors; each now names the
engine family and its spread of ratings.

**step40b** — 5 ESTIMATE oil-spec overrides, 8 normalizations, 1 power sync; 0 ESTIMATE specs and
0 spec-vs-engine power mismatches remain among the 14 targets.

**step40c** — BMW service fills are published, and six of step40b's crawl-majority values
contradicted them, so they were restored [BMWOIL]: `N55B30A` 8.51 → **6.5 L**, `B58B30 (40i)`
10.0 → **6.5 L**, `B48B20 (30i)` 7.0 → **5.25 L** (plus 0W-20 LL-17 FE+ instead of 0W-30),
`S54B32US` 6.52 → **5.48 L** (10W-60, matching its sibling `S54B32` row), `M54B30(306S3)` 6.24 →
**6.5 L**, `N63B44B` 9.46 → **8.99 L** (the 9.5 US qt TIS figure for the X5 xDrive50i).

**step40d — all 38 BMW fuel contradictions cleared.** The audit after step 40 showed BMW's own
hybrids filed on petrol engine rows, the same failure mode as the batch-29 Escape/Mariner rows:

1. Ten Hybrid variants sitting on petrol N63 rows (`N63B44A` 5, `N63B44` 3, `N63` 2) are the
   **ActiveHybrid 7** (455 hp) and **ActiveHybrid X6** (480 hp) → moved to the new
   `N63B44 (ActiveHybrid)` row.
2. Four Hybrid variants on `N55B30A` are ActiveHybrid 3/5/7 cars → moved to
   `N55B30 (ActiveHybrid)` (that row now holds 9 variants: 5 LEMON + 4 pre-existing).
3. `N63B44A` itself was marked **Hybrid** although 24 of its 31 variants are plain petrol
   550i/650i/750i/xDrive50i rows → row corrected to Petrol, 449 hp, 8 cylinders.
4. Two i3 variants marked Hybrid were on the pure-electric `IB1P25B` drive row → moved to
   `W20K06A`, the i3 REx's 647 cc two-cylinder range extender.
5. Two diesels marked Petrol (`N57D30T`) and one i8 marked Petrol (`B3815KT0`) → variant fuel
   corrected.

## Skips

None.

## Evidence

[BMWPR_AH5] press.bmwgroup.com/usa "The BMW ActiveHybrid 5" (300 hp N55 + 55 hp motor = 335 hp
combined) · [BMWPR_AH3] press.bmwgroup.com/usa "The all-new BMW ActiveHybrid 3" (same
powertrain; "the second hybrid model from BMW — after the ActiveHybrid 5 — to use an in-line
6-cylinder engine") · [CD_AH3] caranddriver.com 2013 ActiveHybrid 3 test (spec box: 3.0 I6
300 hp + 55 hp motor, 335 hp combined, 1.3 kWh pack) · [BMWOIL] nineteen72performance.com BMW
oil-capacity guide, bimmertalk.com oil-capacity lookup, f15.bimmerpost.com TIS quotes ·
[BMWUSSPEC]/[BMWVOCAB] BMW NA model-year specifications per nameplate + the BMW engine rows
already in the database.

## Files

- `step40_step5_lemon_batch31_bmw.py`, `step40b_estimate_override.py`,
  `step40c_oil_spec_corrections.py`, `step40d_bmw_hybrid_and_fuel_cleanup.py`
- `database_enriched/csv_exports/48_lemon_step40_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step40_2026-10-01.db`

**Next: Batch 32 — Genesis (74 LEMON rows).**
