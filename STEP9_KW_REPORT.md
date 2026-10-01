# STEP 9 — Kilowatt Column Completed (Step 62)

**Date:** 2026-10-01 · **Script:** `step62_step9_kw_backfill.py`
**Result:** every row that has horsepower now has kilowatts

| Metric | Before | After |
|---|---|---|
| Variants with hp but no kW | **12,869** | **0** |
| Engine rows with hp but no kW | **446** | **0** |
| Fuel conflicts / orphans / count mismatches | 0 / 0 / 0 | **0 / 0 / 0** |

Power in kW is not a judgement call — it is the same number in different units. The only real
question was which conversion the database itself uses, and the already-populated rows answer
it: the kW/hp ratio clusters hard on **0.735-0.736** across 26,268 variants and 5,210 engine
rows. That is metric horsepower (1 PS = 0.7355 kW), not SAE, so 0.7355 is the factor applied.

Existing values were left alone; only NULLs were filled.

## Audit of the values that were already there

59 rows store a kW figure that disagrees with their own hp by more than 3%, and they are listed
in `database_enriched/csv_exports/70_kw_outliers_step62.csv` rather than silently rewritten.
Three patterns show up:

- **Rounding noise on microcars** — `LDW502` at 5hp/4.0kW. Harmless.
- **SAE-vs-PS mixing** — `Z20LET`/`Z20LER` 192hp stored as 147.0kW (147kW is 200 PS).
- **Engine power stored against system power** — the `DW10 HYbrid4` rows read 163hp but 147kW;
  163hp is the diesel engine alone and 147kW is the 200hp HYbrid4 system total. Worth revisiting
  when the hybrid rows are reviewed.

## Files

- `step62_step9_kw_backfill.py`
- `database_enriched/csv_exports/70_kw_outliers_step62.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step62_2026-10-01.db` (local, untracked)
