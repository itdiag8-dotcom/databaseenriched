# STEP 5 — Batch 36: Audi LEMON Replacement (Step 45)

**Date:** 2026-10-01 · **Scripts:** `step45_step5_lemon_batch36_audi.py`, `step45b_estimate_override.py`, `step45c_q5_hybrid_fuel_fix.py`
**Result:** 39 LEMON rows → **31 mapped (79%) / 8 documented skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 433 | **402** (−31) |
| LEMON Audi | 39 | **8** (the bare "RS" rows, see Skips) |
| engines rows | 6,075 | **6,047** (−31 LEMON, +2 new, +1 in 45c) |
| Audi fuel conflicts on batch targets | 2 | **0** |
| Audi variants with NULL power (mapped rows) | 31 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## Method — decoding by oil fill volume

The Audi rows are bare nameplate+year with only three displacement tokens between them, so this
batch leans on a signal earlier batches did not need: **the oil fill the crawl recorded for each
row**. Audi's families separate cleanly by fill, which turns an otherwise ambiguous "A6 2021"
into a decidable row:

| Family | Fill |
|---|---|
| longitudinal 2.0 TFSI (A4/A6) | 4.6-4.7 L |
| transverse MQB 2.0 TFSI (A3/TT) | 5.5-5.7 L |
| 3.2 FSI V6 | 6.2-6.5 L |
| supercharged 3.0 TFSI | 6.8 L |
| EA839 3.0 V6 TFSI | 7.6 L |
| 4.0 V8 biturbo / 4.2 FSI V8 | 8.7 / 9.65 L |

| Rows | Fill | Target |
|---|---|---|
| A3 2016-2017, TT 2016-2017 (4) | 5.5-5.7 L | new `2.0 TFSI EA888 Gen3 (A3 8V / TT 8S, 220hp)` |
| A4 1800CC 2006 | 4.06 L | `AMB` 1.8T 20v, 170 hp |
| A4 3000CC 2006 | 6.43 L | `AVK` 3.0 V6, 220 hp — the A4 Cabriolet kept the 3.0 V6 into MY2006 |
| A5 2009 | 6.52 L | `CALA` 3.2 FSI V6, 265 hp (the A5's only US engine that year) |
| A6 2014-2015 (3, incl. 2 trim slugs) | 4.63 L | `CNCD` 2.0 TFSI, 220 hp |
| A6 2016-2018 (3) | 4.73 L | `CYMC` B9 2.0 TFSI, 252 hp |
| A6 2020-2025 (6) | 7.57 L | new `3.0 V6 TFSI EA839 (55 TFSI, A6/A7 335hp)` — far too large a fill for the 45 TFSI 2.0 |
| Q5 2010 | 6.24 L | `CALB` 3.2 FSI V6, 270 hp (the 2.0T Q5 only arrived for 2011) |
| Q5 3000CC 2013 (2, one `VING`) | 6.81 L | `CTUC` supercharged 3.0 TFSI, 272 hp |
| S5 2017 | 6.81 L | `CTWA` supercharged 3.0 TFSI, 333 hp (MY2017 S5 is still B8.5) |
| TT 2000-2003 (4) | 4.54 L | `ATC` 1.8T 20v, 180 hp |
| RS 2013-2014 (2) | 9.65 L | `4.2 V8 FSI (RS4/RS5)` — RS 5, 450 hp |
| RS 2016-2017 (2) | 8.70 / 7.09 L | `CRDB` 4.0 V8 biturbo — RS 7, 560 hp |

The two RS 7 rows are not a fill argument: `engine_technical_specs.tech_source` for both points at
`lemon.dogeware.me/Audi/<year>/RS 7 Base/…`, naming the model outright.

## 2 new engines

| Code | Engine | cc | hp |
|---|---|---|---|
| `2.0 TFSI EA888 Gen3 (A3 8V / TT 8S, 220hp)` | transverse MQB 2.0 turbo | 1984 | 220 |
| `3.0 V6 TFSI EA839 (55 TFSI, A6/A7 335hp)` | EA839 3.0 V6 turbo | 2995 | 335 |

(plus `2.0 TFSI Hybrid (Q5 Hybrid quattro, 245hp)` created by step45c, below)

## Skips — 8 bare "RS" rows (2018-2025)

From MY2018 Audi sold between two and six different RS models in the US every year — RS 3
(2.5 I5, 400 hp), RS 5 (2.9 V6 TT, 444 hp), RS 6 / RS 7 / RS Q8 (4.0 V8 TT, 591 hp) and the
RS e-tron GT (electric). The crawl truncated the nameplate to "RS", these rows carry no
displacement token, no VIN token and — unlike 2016-2017 — no source URL naming the model, and the
recorded 0W-30 / 7.1-7.6 L fill is shared by several of those engines. There is no honest decode,
so the rows keep their LEMON codes and are left for a future pass if better source data appears.

## Fixes

**9 ROW_FIXES** (`STEP45_VERIFIED`) — `CYMC` had a NULL engine type, NULL power and NULL cylinder
count and is now the B9 2.0 TFSI at 252 hp; `CALA`/`CALB`/`ATC` were carrying EU ratings and now
carry the US ones (265 / 270 / 180 hp); the rest gained family descriptors naming the cars.

**step45b** — 4 ESTIMATE overrides (`ATC`, `CALA`, `CALB`, `CTUC`), 6 normalizations and 6 power
syncs. Each normalization was checked against the Audi service figure before being kept: `CRDB`
8.32 → 8.7 L, `CYMC` 5.19 → 4.73 L, `CTWA` 0W-20/7.57 → 5W-40/6.81 L, `AVK` 0W-30 → 5W-40.

**step45c** — the only two fuel conflicts that touched a batch target: Q5 2013 and Q5 2016 rows
flagged `Hybrid` while linked to the petrol `CNCD`. Those cars are real (Q5 hybrid quattro, 2.0
TFSI + 40 kW motor, 245 hp combined), so rather than flattening the fuel the script gives them
their own engine row. The remaining 11 Audi conflicts (`BGB`, `CHJA`, `CTUA`, `CWZA`) are
pre-existing crawl errors on rows this batch never touched.

## Evidence

[AUDIUS] Audi of America model-year specifications · [LEMONFILL] per-row oil fill recorded by the
crawl in `engine_service_specs` · [LEMONURL] `engine_technical_specs.tech_source` naming "RS 7
Base" for the 2016 and 2017 RS rows.

## Files

- `step45_step5_lemon_batch36_audi.py`, `step45b_estimate_override.py`, `step45c_q5_hybrid_fuel_fix.py`
- `database_enriched/csv_exports/53_lemon_step45_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step45_2026-10-01.db`

**Next: Batch 37 — Isuzu (35 LEMON rows).**
