# STEP 10 — Duplicate Variant Rows Removed (Step 63)

**Date:** 2026-10-01 · **Script:** `step63_step10_dedup_variants.py`
**Result:** variants **39,182 → 37,444** (−1,738); every derived counter resynced

| Metric | Before | After |
|---|---|---|
| Exactly-duplicated variant rows | **1,739** (1,332 groups) | **1** (deliberately exempt) |
| `vehicle_variants` | 39,182 | **37,444** |
| `engines.count_variants` mismatches | 0 | **0** |
| `models.total_variants` mismatches | **18** | **0** |
| `engine_service_specs.count_variants` mismatches | **3,846** | **0** |
| Orphaned `remapping_queue` references | 0 | **0** |
| Fuel conflicts / orphan engine refs | 0 / 0 | **0 / 0** |

## Where the duplicates came from

The audit's healthy-signs list says "no exact duplicate variants", and when it was written that
was true. **The LEMON campaign created them.** F21 recorded 2,486 groups of same-car rows that
differed only in power or `engine_type` text; as the campaign relinked those rows onto shared
engine codes and normalised their power and fuel, the differences disappeared and the rows
became byte-identical. Step 9 produced the last one by itself — completing the kW column made a
final pair match, which is why this script's baseline assert fired on the first run and had to
be moved from 1,738 to 1,739.

Worst cases: eleven identical `Toyota Prius 2015 / 2ZR-FXE / 99hp` rows, eleven `Nissan Versa
2015 / HR16DE`, ten `Nissan Juke 2015 / MR16DDT`. 539 of the deleted rows are model-year 2015 —
the LEMON crawl year.

Nothing in the schema distinguishes rows within a group: there is no trim, VIN or body-style
column. As data they are indistinguishable copies, and any query that counts vehicles was
counting them several times over.

## Method

Keeper = lowest `id` in each group. Full before/after list of all 1,738 deletions in
`database_enriched/csv_exports/71_duplicate_variants_step63.csv`.

**The referential catch.** `remapping_queue.vehicle_variant_id` points at variant rows, and 57
of those pointed at a row about to be deleted. 56 were repointed at the surviving twin. The 57th
could not be: variants 31097/31098 (a 2007 Chevy pair) each hold their own queue row flagging a
*different* wrong code — `LLY` on one, `LMM` on the other — because they were queued before the
two variants converged. The column is both `NOT NULL` and `UNIQUE`, so that reference could
neither be repointed nor cleared.

Rather than destroy a pending remapping record to delete a redundant row, **variant 31098 is
exempted and the pair stays**. A row that carries unique downstream state is not really a
duplicate. It is recorded in F21 of the audit so it does not read as an oversight later.

## Derived counters

Dedup invalidates every cached count, so all three were recomputed from scratch — and two were
already wrong before this step: `models.total_variants` had drifted on 18 models (Citroën C3
Picasso said 5, actual 18), and `engine_service_specs.count_variants` was a stale snapshot
disagreeing with `engines.count_variants` on **3,846 rows**, 3,605 of them low. It had not been
maintained since the campaign began. All three now agree with the data.

## Files

- `step63_step10_dedup_variants.py`
- `database_enriched/csv_exports/71_duplicate_variants_step63.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step63_2026-10-01.db` (local, untracked)

## Audit doc updated

`DATA_QUALITY_AUDIT.md`: F11 marked **resolved**, F21 marked **partly resolved** with the
remaining 2,770 non-identical groups quantified, F14 **reclassified as not-a-defect** (the 147
zero-variant engines are kept as a reference catalogue by decision), and the "no exact duplicate
variants" healthy-sign corrected.
