# STEP 5 — Batch 32: Genesis LEMON Replacement (Step 41)

**Date:** 2026-10-01 · **Scripts:** `step41_step5_lemon_batch32_genesis.py` + `step41b_estimate_override.py`
**Result:** 74 LEMON rows → **74 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 658 | **584** (−74) |
| LEMON Genesis | 74 | **0** |
| engines rows | 6,290 | **6,221** (−74 LEMON +5 new) |
| Genesis fuel conflicts | — | **0** |
| Genesis variants with NULL power | 74 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

Genesis fuels after: Petrol 68 · Electric 6.

## Method — a young brand with a short engine list

Genesis has only existed since MY2017, each model year offers one or two engines, and the crawl
kept the displacement on 68 of 74 rows, so the mapping is nearly mechanical once the four
Hyundai families are pinned down:

| Family | Code | Output | Applications in these rows |
|---|---|---|---|
| Theta II FR turbo | `G4KL` *(new)* | 252 | G70 2.0T 2019-2023 |
| Lambda II | `G6DJ` | 311 | G80 3.8 2017-2020 |
| Lambda II T-GDI | `G6DP` | 365 | G70/G80 Sport/G90 3.3T |
| Tau V8 GDI | `Tau 5.0 GDI (K900/Equus)` | 420 | G80/G90 5.0 2017-2022 |
| Smartstream G2.5 T | `G4KR` *(new)* | 300 | G80/GV80/GV70 2021+, G70 2024-25 |
| Smartstream G3.5 T | `G6DT` *(new)* | 375 | G80/GV80/GV70 3.5T, G90 2023+ |

The one real identification problem was the 2.0T. Hyundai builds **two** 2.0 T-GDI Theta IIs,
and they are not interchangeable: the transverse `G4KH` (Sonata/Santa Fe, 245-275 hp) and the
longitudinal `G4KL`, which Wikipedia's Theta article lists as "for the RWD based applications …
252-255 PS … Genesis G70 (2017-2023), Genesis G80 (DH) (2017-2020), Kia Stinger (2017-2023)"
[WIKI_THETA]. The G70 is rear-drive, so these rows are `G4KL`, 252 hp.

Two Smartstream codes were confirmed the same way: `G4KR` is the 2.5 T-GDI at 300 hp, listed
against Genesis G80/GV80 2021-2023 and the Kia Stinger [AUTOFILES_G4KR]; `G6DT` is the
Smartstream G3.5 T-GDi [MR_SMART], 375 hp in the G80/GV80/GV70/G90 (409 hp with the 48 V
e-supercharger on the long-wheelbase G90, noted in the evidence but not used as a default).

### The six electric rows

`GV60` (3 rows) and `ELECTRIFIED` (3 rows) are battery-electric cars that the crawl recorded as
**`fuel='Petrol'`** — the same contradiction class as the batch-29 hybrids, caught before writing
rules this time. Both got E-GMP dual-motor rows and their variant fuel corrected to Electric:

- `GV60 Electric (E-GMP AWD)` — US GV60s are dual-motor AWD, Advanced **314 hp**, Performance 429.
- `E-GMP Dual Motor (Genesis Electrified)` — the crawl truncates the nameplate, and both the
  **Electrified G80** (365 hp) and **Electrified GV70** (429 hp) were on sale 2023-2025. Rather
  than guess the model, both map to the shared E-GMP dual-motor row with the Electrified G80's
  365 hp as the recorded figure and the ambiguity stated in the evidence column.

## 5 new engines

| Code | Engine | cc | hp | fuel |
|---|---|---|---|---|
| `G4KL` | 2.0 I4 Theta II FR T-GDI (G70/G80 DH/Stinger) | 1998 | 252 | Petrol |
| `G4KR` | 2.5 I4 Smartstream T-GDI | 2497 | 300 | Petrol |
| `G6DT` | 3.5 V6 Smartstream T-GDI | 3470 | 375 | Petrol |
| `GV60 Electric (E-GMP AWD)` | E-GMP dual-motor AWD | — | 314 | Electric |
| `E-GMP Dual Motor (Genesis Electrified)` | E-GMP dual-motor AWD | — | 365 | Electric |

## Fixes

**2 ROW_FIXES** (`STEP41_VERIFIED`) — `G6DJ` was recorded as an **8-cylinder** 335 hp row; it is
the 3.8 Lambda II V6 (311 hp in the G80). `G6DP` gained its application list.

**step41b** — 0 ESTIMATE overrides needed, 3 normalizations, 2 kept, 6 power syncs; 0 ESTIMATE
specs and 0 spec-vs-engine power mismatches remain among the 8 targets. Unlike batches 29-31 the
crawl's capacities checked out against the service data and were kept: `G4KR` 6.15 L (6.6 qt),
`G6DJ` 6.89 L (7.3 qt) and the Tau V8 9.19 L (9.7 qt) all match the published Genesis figures
[G80OIL], so no `step41c` correction script was needed.

## Skips

None.

## Evidence

[WIKI_THETA] en.wikipedia.org Hyundai Theta engine (G4KL = FR/RWD 2.0 T-GDI, 252-255 PS, G70 /
G80 DH / Stinger) · [AUTOFILES_G4KR] autofiles.com Smartstream G4KR Turbo (300 hp; Genesis G80
and GV80 2021-2023, Kia Stinger) · [MR_SMART] motorreviewer.com Hyundai/Kia engine index
(Smartstream G2.5 T-GDi = G4KP/G4KR, G3.5 MPi/GDi = G6DU/G6DT) · [G80OIL] carscounsel.com and
autofiles.com Genesis G80 oil capacities (2.5T 6.6 qt 0W-30, 3.8 and 3.3T 7.3 qt 5W-30, 5.0 V8
9.7 qt 5W-20; the Tau V8's Hyundai code is G8BE) · [GENESISUS]/[GENVOCAB] Genesis Motor America
model-year specifications + the Hyundai-group engine rows already in the database.

## Files

- `step41_step5_lemon_batch32_genesis.py`, `step41b_estimate_override.py`
- `database_enriched/csv_exports/49_lemon_step41_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step41_2026-10-01.db`

**Next: Batch 33 — Fiat (64 LEMON rows).**
