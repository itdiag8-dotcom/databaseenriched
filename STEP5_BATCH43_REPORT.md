# STEP 5 — Batch 43: Mercedes-Benz LEMON Replacement (Step 52)

**Date:** 2026-10-01 · **Scripts:** `step52_step5_lemon_batch43_mercedes.py`, `step52b_estimate_override.py`, `step52c_sprinter_fill_fix.py`
**Result:** 37 LEMON rows → **37 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 183 | **146** (−37) |
| LEMON Mercedes | 37 | **0** |
| engines rows | 5,829 | **5,800** (−37 LEMON +8 new) |
| Fuel corrections | — | **18** (Sprinter → Diesel) |
| NULL power on batch targets | 37 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## Method

Mercedes names its cars after their engines, so 19 of the 37 rows decode straight from the
nameplate — C280 is a 2.8 V6, S500 a 5.0 V8, SLK55 a 5.5 AMG V8. The remaining 18 are Sprinters,
which carry no such clue, and there the oil fill carries the batch: 10-12.5 L of 5W-30 is a
commercial diesel, and the drop from 12.5 L to 10.5 L marks the switch from the 3.0 V6 OM642 to
the 2.0 four OM654.

| Rows | Target | hp |
|---|---|---|
| C230 2000, 2002 | new `M111 2.3 Kompressor` | 192 |
| C280 2000 | new `M112 2.8 V6` | 194 |
| C350 2015 (2 trim rows) | new `M276 3.5 V6` | 302 |
| CLA45 2019 | `M133.980` 2.0 turbo AMG | 375 |
| E550 2017 / SL550 2020 | new `M278 4.7 V8 BiTurbo` | 402 / 449 |
| GLA250 2020 | `M260 2.0T` | 221 |
| GLE450 2016 | new `M276 3.0 V6 BiTurbo` | 362 |
| GT 2024 | `M177.980` 4.0 V8 BiTurbo | 577 |
| Maybach 2021 / 2022-2023 | `M279.980` V12 / `M176 4.0 V8 BiTurbo` | 621 / 496 |
| R350 2008 | `M272.980` 3.5 V6 | 268 |
| S350 2006 / S500 2006 | `M112.972` 3.7 V6 / `M113.966` 5.0 V8 | 245 / 302 |
| SLK300 2016 | new `M274 2.0 Turbo` | 241 |
| SLK55 2016 | `M152 5.5 V8 NA` | 415 |
| Sprinter 2010-2023, no cc token (12) | new `OM642 3.0 V6 CDI (Sprinter)` | 188 |
| Sprinter `2000CC` 2019-2022 + 2024-2025 (6) | new `OM654 2.0 I4 CDI (Sprinter)` | 161 / 168 |

Three decodes are worth the detail:

- **Maybach** is the one badge in this batch worn by two different cars, and the fill separates
  them: MY2021 records 9.5 L, the V12's sump, so that row is the S650; 2022 and 2023 record
  8.51 L, the 4.0 V8 of the S580, the V12 having left the range.
- **SLK300 2016** is not a V6. The SLK300 badge arrived on the 2.0 turbo M274 (241hp), and the
  6.34 L fill agrees with the four, not with a 3.5.
- **Sprinter 2024-2025** records 10.03 L and no V6 was offered any more, so those rows are the
  OM654 in its 168hp tune.

## 18 fuel corrections

Every Sprinter row was filed as Petrol. Ten to twelve and a half litres of 5W-30 in a commercial
van is a diesel, and neither the OM642 nor the OM654 was ever sold here in any other form, so all
18 are now Diesel.

## 8 new engines

`M111 2.3 Kompressor`, `M112 2.8 V6`, `M276 3.5 V6`, `M276 3.0 V6 BiTurbo`, `M278 4.7 V8
BiTurbo`, `M274 2.0 Turbo`, `OM642 3.0 V6 CDI (Sprinter)`, `OM654 2.0 I4 CDI (Sprinter)`.

The database held dozens of chassis-specific Mercedes rows (`M272.967`, `M278.922`, …) but no
clean entry for the engines as the US market knows them, and several of the existing rows carry
scrambled descriptors. Rather than attach US cars to an arbitrary European variant number, this
batch adds one clean row per engine family and leaves the chassis rows untouched.

## Fixes

**6 ROW_FIXES** (`STEP52_VERIFIED`) — `M279.980` was recorded as an **8-cylinder** when the M279
is a V12, `M112.972` likewise as an 8 when the 3.7 is a V6, and four rows carried junk
descriptors harvested from the crawl (`M177.980` read "for vehicles with compressor boost").

**step52b** — 2 ESTIMATE overrides, 6 normalizations, 8 power syncs.
**step52c** — step52b's plurality vote had set the Sprinter V6 fill to 10.59 L on the strength of
5 rows out of 12, against 7 rows at ~12.5 L; the engine row is restored to **12.5 L** with the
2019+ figure kept in the note.

## Skips

None.

## Known residual

32 Mercedes variants still have a fuel mismatch against their engine row (`M272.974`,
`M274.920`, `OM651.921`, `W242 Electric`, …). All are pre-existing hybrid/electric mislabels on
codes this batch never touched — the DB-wide conflict count is unchanged at 137.

## Files

- `step52_step5_lemon_batch43_mercedes.py`, `step52b_estimate_override.py`, `step52c_sprinter_fill_fix.py`
- `database_enriched/csv_exports/60_lemon_step52_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step52_2026-10-01.db`

**Next: Batch 44 — Hummer (19) + Cadillac (7) + the GMC/Pontiac leftovers.**
