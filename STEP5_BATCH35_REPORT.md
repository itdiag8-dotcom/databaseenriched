# STEP 5 — Batch 35: Alfa Romeo LEMON Replacement (Step 44)

**Date:** 2026-10-01 · **Scripts:** `step44_step5_lemon_batch35_alfa.py` + `step44b_estimate_override.py`
**Result:** 43 LEMON rows → **43 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 476 | **433** (−43) |
| LEMON Alfa Romeo | 43 | **0** |
| engines rows | 6,117 | **6,075** (−43 LEMON +1 new) |
| Alfa Romeo fuel conflicts | — | **0** |
| Alfa Romeo variants with NULL power | 43 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## Method

Alfa's second US era (MY2015-2025) is four nameplates and four powertrains, and the crawl kept
the displacement on 40 of 43 rows:

| Rows | Decode |
|---|---|
| 4C 2015-2020 (8) | **1750 TBi** `960A1.000`, 237 hp — the 4C's only engine. The three MY2015 rows are trim slugs (`4CBASE`, `4CSPIDER`, `4CLAUNCHEDIT`): body and equipment, same engine. |
| Giulia / Stelvio 2000CC (17) | **2.0 GME-T4**, 280 hp in Alfa tune (the same block Jeep and Dodge run at 268-270 hp) |
| Giulia / Stelvio 2900CC (15) | **Quadrifoglio 2.9 V6 twin-turbo** (type 690T, the Ferrari F154 architecture minus two cylinders), **505 hp** |
| Giulia / Stelvio 2025 (2) | 2.0 only — the Quadrifoglio left the US range after MY2024 |
| Tonale 1300CC 2024-2025 (3) | **Q4 plug-in hybrid**, 1.3 GSE turbo + rear e-axle, 285 hp combined |

The Tonale rows are the batch's one fuel correction: every US Tonale is a PHEV, but the crawl
files all three as Petrol, so they were relinked to the 1.3 GSE PHEV row and their variant fuel
set to Hybrid (including the `VINW` row, which is the same powertrain).

## 1 new engine

| Code | Engine | cc | hp |
|---|---|---|---|
| `690T 2.9 V6 TT (Quadrifoglio)` | 2.9 V6 twin-turbo, Giulia/Stelvio Quadrifoglio | 2891 | 505 |

## Fixes

**3 ROW_FIXES** (`STEP44_VERIFIED`) — `960A1.000` carried the junk descriptor *"Rear
side-section"* (a parts-catalogue string) and is now named as the 4C's 1750 TBi at 237 hp;
`2.0 Turbo GME` and the 1.3 GSE PHEV row gained their Alfa ratings alongside the Jeep/Dodge ones.

**step44b** — 1 ESTIMATE override (`960A1.000`, whose 3.1 L estimate was replaced by the crawl's
5.77 L), 1 normalization (`2.0 Turbo GME` → 0W-30 / 5.2 L, the published Giulia figure), 2 power
syncs; 0 ESTIMATE specs and 0 spec-vs-engine power mismatches remain.

## Skips

None.

## Evidence

[ALFAUS] Alfa Romeo USA model-year specifications (4C 1750 TBi 237 hp; Giulia/Stelvio 2.0
280 hp and Quadrifoglio 2.9 V6 TT 505 hp; Quadrifoglio withdrawn after MY2024; Tonale sold in
the US only as the Q4 PHEV, 285 hp combined) · [ALFAVOCAB] the FCA engine rows already in the
database.

## Files

- `step44_step5_lemon_batch35_alfa.py`, `step44b_estimate_override.py`
- `database_enriched/csv_exports/52_lemon_step44_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step44_2026-10-01.db`

**Next: Batch 36 — Audi (39 LEMON rows).**
