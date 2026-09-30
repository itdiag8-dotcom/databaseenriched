# Step 5 — Batch 6 Report: Chevrolet LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step15_step5_lemon_batch6_chevrolet.py` (+ `step15b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step15_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/23_lemon_batch6_decisions.csv` (per-variant, with evidence)

Per the user-selected LEMON-count order, batch 6 = **every remaining LEMON Chevrolet variant** (653 rows,
49 models, years 2000–2025). **600 variants remapped, 53 skipped** (documented below), 600 LEMON codes
retired, 20+3 new engine rows, 10 row-fixes, 31 fuel fixes (Hybrid 13, Diesel 10, Electric 8).

## Method — like the Ford batch: cc + VIN 8th char

Chevrolet LEMON codes carry **cc in the code** (nearly always) and often a **VIN 8th char**
(`LEMON_CHEVROLET_EQUINOX_3600CC_VIN3_2017`), so rules key on **(model, year, cc, VIN)** — the same
method proven in batch 3 (Ford). The DB's existing GM RPO vocabulary (150+ codes: LM7, LU3, LLT, LFX,
LTG, LS-family, Duramax…) served as target vocabulary. Key decode facts established (cited):

| Signal | Meaning | Evidence |
|---|---|---|
| Camaro VIN `J`/`W`/`V`/`3`/`P` | L99 (auto) / LS3 (manual) / LLT / LFX / LSA | Camaro5 forum, ussealparts LS guide |
| GM truck VIN `X/W` 4.3, `V` 4.8, `T` LM7, `Z` L59, `U` LQ4, `N` LQ9, `G` 8.1, `F` 6.5TD, `1/2` 6.6D | Vortec decode | Sloppy Mechanics wiki, itstillruns |
| 2018 Equinox RPOs | 1.5T=**LYX**, 2.0T=**LTG**, 1.6TD=**LH7** | GM Authority spec sheet, NHTSA TSB |
| 2016 Malibu 1.5T | **LFV** (163hp debut) | GM Authority |
| 2014-15 Cruze 2.0TD | **LUZ** 151hp | GM Authority |
| TrailBlazer EXT 5.3 | **LM4** (VIN P, 294hp) | reman-engine, auto-data |
| 2021+ Trailblazer 1.2T/1.3T | **LIH** 137hp / **L3T** 155hp (VIN L) | Gordon Chevy, Weber Brothers |
| 2013 Traverse 3.6 | still **LLT** (order code) | Car and Driver spec, AMSOIL lookup |
| 'Chevy' generic rows (63) | Vortec by (cc, year): L35→LU3 4.3; LR4→LY2→L20 4.8; LM7→LY5→LMG 5.3; LQ4→LY6→L96 6.0; L31/L30/L29/L18; LBZ→LMM→LML Duramax; 6.5TD | VIN charts above |

## Top mappings (600 total, 77 target codes)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| LTG (2.0T) | 34 | | LCV (2.5 SIDI) | 17 |
| LUW (1.8) | 24 | | L36 (3.8 3800) | 15 |
| LGX (3.6) | 23 | | L35 (4.3 Vortec) | 14 |
| LFX (3.6 SIDI) | 23 | | LA1 (3.4) | 18 |
| LUH (1.4T) | 21 | | L61 (2.2) | 19 |
| LE5 (2.4) | 19 | | LU3 (4.3) | 17 |

New engines (20 + 3 fix-ups): LSJ (Cobalt SS SC), LD9 (2.4 Twin Cam), LFV/LYX (1.5T), LH7 (1.6TD),
LUZ (2.0TD), LZ9 (3.9), LT2/LT6 (C8), LM4 (TB EXT), LG8 (3.1), L77 (Caprice PPV), 6.5 TD V8,
MR20DD (City Express), Voltec 1.4/1.5 EREV (Volt Gen1/2), **Bolt EV Electric** + **Spark EV Electric**
(Electric engines now 11), 1.8 Hybrid (Malibu), 1.4 16v (Spark US), + LUH/LIH/L3T created during
apply-fix. Row-fixes: **1ZZ-FE 1600→1794cc** (Prizm; corrects a long-standing error), LS4 303hp,
LZ4/LZE/LNJ/L82/LL8/LS1/J20A labels.

## Step 15b — spec normalization

18 ESTIMATE overrides + 11 majority fixes + 32 power syncs; then NULL-power engine rows filled
(LGX 310, LT1 455, LCV 196, LEA 182, LN2 120) and propagated to 128 pre-existing variants + 6 spec rows.
Verified plausible: L35/L36/LA1/LNJ 4.25L (4.5qt GM V6) ✓, LL8 6.62L (7qt) ✓, LS1 6.15L (6.5qt) ✓,
LS2 5.2L ✓, LS3 5.67L ✓, L3T 0W-20/4.49L ✓.
**Result: 0 ESTIMATE among step-15 targets, 0 spec-power mismatches, 0 orphan refs, 0 count mismatches.**

### Flags (accepted limitations, noted)

- **LS7 = 9.93L** — crawl shows a genuine year split (2006-08 Z06 = 7.57L/8qt, 2009-13 = 9.93L/10.5qt);
  majority took 2009+. Worth verifying against GM's 8.5qt figure.
- **LT1 = 9.27L** — single-source (one 2014 Corvette lemon row; C7 base is usually cited 6.5qt —
  this row may be a dry-sump/Z51 car).
- Spark 1.4 row created as descriptive "1.4 16v (Spark US)" — engine identity certain (sole 98hp engine
  2016-22), RPO (LVV) not web-verified this session.
- LCV/LKW and LE5/LEA/LE9 families share one row per era (port/SIDI and flex variants share physical engine).

## Skipped by design (53)

- Bare multi-engine rows: Camaro 2010-13 (V6/V8) ×4, Corvette 2001-04 (LS1 vs Z06 LS6) ×4, Impala
  2014/2016/2020 ×3, Malibu 2016 ×1, Blazer 2024-25 ×2, Silverado 2019/2024/25 ×3, Cobalt/HHR 2008 ×2,
  Cavalier 2001 ×1, Captiva 2014-15 ×2, Cutaway 2003-05 ×3, S10 ×2, Tracker 2000/2004 ×2, SSR 2003-04 ×2.
- Canadian Daewoo-derived: Optra/Optra5 ×10, Epica ×3 (engine codes uncertain).
- Transition/ambiguous: Malibu 2012 3.6 (LY7 vs LFX) ×1, Malibu 2014 2.4 ×1, Metro ×2, RV chassis ×5
  (Workhorse vs GM, 6.5TD vs 8.1).
- LUK 2.4 eAssist engine row left power-NULL (combined output uncertain).

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 13,235 | 12,658 (−600 retired LEMON rows, +23 new) |
| LEMON total (all brands) | 7,828 | **7,228** |
| Chevrolet LEMON remaining | 653 | 53 (intentional skips) |
| ESTIMATE among step-15 targets | — | **0** |
| Orphan refs / count mismatches / power mismatches | 0 | 0 |

**Next batch (LEMON-count order): Audi 576** → Nissan 520 → Toyota 471 → Kia 392 → Hyundai 391 →
Lexus 322 → Honda 312 → Mazda 303 → … (~7,228 remaining across 41 brands).
