# STEP 5 — Batch 34: Scion LEMON Replacement (Step 43)

**Date:** 2026-10-01 · **Scripts:** `step43_step5_lemon_batch34_scion.py` + `step43b_estimate_override.py`
**Result:** 44 LEMON rows → **44 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 520 | **476** (−44) |
| LEMON Scion | 44 | **0** |
| engines rows | 6,160 | **6,117** (−44 LEMON +1 new) |
| Scion fuel conflicts | — | **0** |
| Scion variants with NULL power | 44 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## Method — a channel with no engines of its own

Scion (MY2004-2016) was Toyota's US youth brand: every car is a rebadged Toyota, Subaru or
Mazda, and each nameplate was sold with exactly **one** engine per generation, so nameplate +
year is a complete decode with no volume-default guessing anywhere in the batch.

| Nameplate | Donor | Engine | hp |
|---|---|---|---|
| xA 2005-06, xB 2005-06 (NCP31) | Toyota ist / bB | `1NZ-FE` 1.5 | 103 |
| xB 2008-15 (AZE151) | Toyota Corolla Rumion | `2AZ-FE` 2.4 | 158 |
| xD 2008-14 | Toyota ist / Urban Cruiser | `2ZR-FE` 1.8 | 128 |
| tC 2005-10 (AT10) | Avensis platform | `2AZ-FE` 2.4 | 161 |
| tC 2011-16 (AT20) | Camry/RAV4 | `2AR-FE` 2.5 | 179 |
| iQ 2012-15 | Toyota iQ | `1NR-FE` 1.33 | 94 |
| iM 2016 | Toyota Auris / Corolla iM | `2ZR-FAE` 1.8 Valvematic | 137 |
| iA 2016 | **Mazda2 sedan** | `Skyactiv-G 1.5 (P5)` | 106 |
| FR-S 2013-16 | **Subaru BRZ** | `FA20` 2.0 Boxer D-4S | 200 |

Two nameplates are not Toyota-engined at all and are the only interesting calls in the batch:
the **FR-S** runs Subaru's FA20 flat-four (Toyota's own designation is 4U-GSE) and the **iA** is
a Mazda-built Mazda2 sedan with the 1.5 Skyactiv-G — the one engine here that needed a new row.

Seven MY2015 rows carry trim slugs (`..._2015_TCAUTOMATICT`). Because each nameplate had a
single engine, the slug only distinguishes manual from automatic, so the trim rules point at the
same targets as the surrounding years.

## 1 new engine

| Code | Engine | cc | hp |
|---|---|---|---|
| `Skyactiv-G 1.5 (P5)` | 1.5 I4 Skyactiv-G (Mazda2/Demio, Scion iA / Yaris iA) | 1496 | 106 |

## Fixes

**4 ROW_FIXES** (`STEP43_VERIFIED`) — `FA20` and `2AR-FE` were both recorded as **6-cylinder**
(the FA20 is a flat-four, the 2AR-FE an inline-four); `2ZR-FAE` and `1NR-FE` had bare
displacement strings and now name the Valvematic/Dual VVT-i families and their ratings.

**step43b** — 2 ESTIMATE oil-spec overrides (`1NR-FE` → 0W-20/3.5 L, `2ZR-FAE` → 0W-20/4.16 L),
1 normalization (`2AZ-FE` → 4.25 L, the Toyota 4.5 US qt figure), 1 power sync; 0 ESTIMATE specs
and 0 spec-vs-engine power mismatches remain. The crawl values matched the Toyota service data
this time, so no `step43c` was needed.

## Skips

None.

## Evidence

[SCIONUS] Toyota/Scion US model-year specifications per nameplate (engine and SAE rating) ·
[TOYVOCAB] the Toyota/Subaru/Mazda engine rows already verified in earlier steps.

## Files

- `step43_step5_lemon_batch34_scion.py`, `step43b_estimate_override.py`
- `database_enriched/csv_exports/51_lemon_step43_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step43_2026-10-01.db`

**Next: Batch 35 — Alfa Romeo (43 LEMON rows).**
