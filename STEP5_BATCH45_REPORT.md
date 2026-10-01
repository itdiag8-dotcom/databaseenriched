# STEP 5 — Batch 45: Jaguar + Land Rover LEMON Replacement (Step 54)

**Date:** 2026-10-01 · **Scripts:** `step54_step5_lemon_batch45_jlr.py`, `step54b_estimate_override.py`, `step54c_aj126_spec_revert.py`
**Result:** 27 LEMON rows (Jaguar 12, Land Rover 15) → **27 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 118 | **91** (−27) |
| LEMON Jaguar / Land Rover | 12 / 15 | **0 / 0** |
| engines rows | 5,772 | **5,745** (−27) |
| New engines | — | **0** |
| NULL power on batch targets | 27 | **0** |
| Orphans / count mismatches / fuel conflicts | — | **0 / 0 / 0** |

## Why one batch

By this period Jaguar and Land Rover are one engineering company sharing one engine catalogue
(AJ-V6, AJ126, Ingenium), and both brands' rows arrive with the same problem: the crawl
truncated the nameplate to uselessness. "RANGE" could be a Range Rover, a Range Rover Sport, a
Velar or an Evoque.

## Method — the database recognising its own numbers

With the nameplates gone the oil fill is the only usable evidence, and here it is unusually
decisive, because three targets' service specs *already in this database* match the crawl's
figures to the decilitre:

| Crawl rows | Fill / viscosity | Stored engine spec | Target |
|---|---|---|---|
| RANGE 2022-2025 (no cc), 4 rows | 7.0 L 0W-20 | `204PT` = **7.0 L 0W-20** | 2.0 Ingenium P250, 246hp |
| RANGE `3000CC` 2014-2015, 2018-2019 | 7.99 L | `AJ126` = **8.04 L** | 3.0 V6 supercharged, 340hp |
| S-Type 2000-2008, X-Type 2002-2004 | 6.24-6.81 / 5.77 L | `AJ30` = **6.52 L** | 3.0 AJ-V6, 231-240hp |

The remaining six Range Rover rows step up in fill exactly as the big Ingenium straight six
replaced the supercharged V6 — 8.8 L from 2020 and 9.46 L from 2023, against the V6's 8 L — so
they are `AJ300P` P400 cars at 395hp. The single MY2000 row records 5.82 L of **5W-40**, the
Rover OHV V8 of the P38 (222hp), which shares nothing with the rest of the batch and is
unmistakable for it.

On the Jaguars the fill also rules an engine *out*: the S-Type's 4.0 V8 takes well over seven
litres, so the 6.3-6.5 L rows are V6 cars.

## Fixes

**2 ROW_FIXES** (`STEP54_VERIFIED`) — descriptors for the Rover V8 and `AJ30`.
**step54b** — 3 normalizations (the Rover V8 to its correct 5.82 L of 5W-40, `AJ30` to 5W-30).
**step54c** — reverts step54b's third normalization: it had pulled `AJ126` from the curated
8.04 L / 0W-20 to 7.99 L / 5W-20 on the strength of the four 2014-2015 rows. 5W-20 was listed
for the earliest supercharged V6 cars, but 0W-20 is JLR's standing spec and the figure the rest
of this database's F-Type/XE/XF variants rely on; 0.05 L is not worth splitting an engine's spec
away from its own fleet.

## Skips

None.

## Files

- `step54_step5_lemon_batch45_jlr.py`, `step54b_estimate_override.py`, `step54c_aj126_spec_revert.py`
- `database_enriched/csv_exports/62_lemon_step54_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step54_2026-10-01.db`

**Next: Batch 46 — Kia (14) + Hyundai (6).**
