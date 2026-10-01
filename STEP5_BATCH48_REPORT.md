# STEP 5 — Batch 48: Audi + Porsche + Volkswagen LEMON Replacement (Step 57)

**Date:** 2026-10-01 · **Scripts:** `step57_step5_lemon_batch48_vag.py`, `step57b_estimate_override.py`, `step57c_spec_reverts.py`
**Result:** 19 LEMON rows (Audi 8, Porsche 8, Volkswagen 3) → **19 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 40 | **21** (−19) |
| LEMON Audi / Porsche / Volkswagen | 8 / 8 / 3 | **0 / 0 / 0** |
| engines rows | 5,696 | **5,679** (−19 LEMON +3 new) |
| Fuel corrections | — | **1** (Touareg V10 TDI → Diesel) |
| Orphans / count mismatches / fuel conflicts | — | **0 / 0 / 0** |

## The eight deferred Audi "RS" rows

Batch 36 skipped these because "RS" alone identifies no car — Audi sold the RS 3, RS 5, RS 6,
RS 7 and RS Q8 in the US across 2018-2025. They are resolved here without guessing, because the
eight rows carry **only two distinct fills**, nearly a quart apart, alternating by year:

| Fill | Rows | Engine |
|---|---|---|
| 7.09 L (7.5 qt) | 2018, 2020, 2024 | 2.5 TFSI five-cylinder — RS 3 |
| 7.57 L (8 qt) | 2019, 2021, 2022, 2023, 2025 | 2.9 V6 biturbo — RS 5 |

7.57 L is this project's own EA839 fingerprint (the 3.0 TFSI V6 was logged at 7.6 L back in the
Audi batch) and the 2.9 is that family's biturbo. Just as importantly, **neither** value is
anywhere near the 4.0 V8's nine-plus litres, which rules the RS 6, RS 7 and RS Q8 out of all
eight rows. Both engines were missing from the database and are added here.

## Porsche — one nameplate, two engines, told apart by fill

- Cayenne `3600CC` 2015 and 2017 record **8.49 L** — the naturally aspirated 3.6 V6, 300hp.
- Cayenne `3600CC` 2016 and 2018 record **6.7 L** — the twin-turbo 3.6 of the Cayenne S, 420hp.
- 911 `3800CC` 2012-2013, VIN D, 7.49 L of 0W-40 — the 991 Carrera S, 400hp.
- Macan `3000CC` 2020-2021 — the single-turbo 3.0 V6 Macan S, 348hp.

## Volkswagen

5.67 L of 0W-30 is the EA888 of the Mk8 GTI (241hp); 5.96 L of 5W-40 the 2.8 V6 30v of the last
Passat GLX (190hp, an engine the database lacked and now has as `ATQ`); and 13.53 L of 5W-40 the
**V10 TDI** of the Touareg — a diesel the crawl had filed as Petrol, corrected here.

## 3 new engines

| Code | Engine | hp |
|---|---|---|
| `2.5 TFSI EA855 evo (RS 3, 394-401hp)` | 2.5 I5 TFSI | 394-401 |
| `2.9 V6 TFSI biturbo (RS 4/RS 5, 444hp)` | 2.9 V6 biturbo EA839 | 444 |
| `ATQ` | 2.8 V6 30v (Passat B5.5 GLX) | 190 |

## Fixes

**5 ROW_FIXES** (`STEP57_VERIFIED`) — `M46.20` and `MCU.RA` were recorded as **8-cylinder**
engines when both Cayenne 3.6s are V6s; `MA1.03`, `MDC.NA` and the V10 TDI needed descriptors.

**step57b** — 3 ESTIMATE overrides, 3 normalizations, 2 power syncs. **step57c** reverts all
three normalizations: with only one or two rows voting, step57b's "majority" is an anecdote, and
here it had replaced the Touareg's curated 11.45 L with a single row's 13.53 L, moved the
Cayenne V6 off Porsche's A40 0W-40 approval, and moved the Mk8 GTI off VW 508 00's 0W-20.

## Skips

None. **The last deferred rows in the queue are now mapped.**

## Files

- `step57_step5_lemon_batch48_vag.py`, `step57b_estimate_override.py`, `step57c_spec_reverts.py`
- `database_enriched/csv_exports/65_lemon_step57_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step57_2026-10-01.db`

**Next: Batch 49 (final) — Nissan 7, Subaru 6, Lincoln 3, Mazda 2, Toyota 2, Honda 1 = 21 rows, the last of the LEMON queue.**
