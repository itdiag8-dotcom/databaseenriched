# Step 5 — Batch 9 Report: Toyota LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step18_step5_lemon_batch9_toyota.py` (+ `step18b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step18_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/26_lemon_batch9_decisions.csv` (per-variant, with evidence)

Batch 9 in LEMON-count order = **every remaining LEMON Toyota variant** (471 rows, 31 models,
MY2005–2025). **469 variants remapped, 2 skipped**, 10 new engine rows, 118 fuel fixes (Hybrid 107,
Electric 11) — the hybrid-heaviest batch so far.

## Incident: full workspace rewind (8th, most severe)

At the start of this batch the sandbox was found **fully rewound to the branch point `5bf3811`**
(LEMON 12,637, engines 17,916 — batches 3–8 gone from the working tree). All 10 commits were intact
on origin, so recovery was: `git fetch origin && git reset --hard origin/arena/01a0ee59-databaseenriched`.
No work lost — every batch had ended commit+push. Lesson reinforced: **always end the turn pushed.**

## Method

Signals: cc + VIN chars + 2015 trim slugs + **the lemon `fuel` column** (it correctly flagged hybrids:
Camry/Corolla/Grand/Highlander/RAV4/Avalon hybrid rows were already `Hybrid`), which resolved the
gas-vs-hybrid VIN splits without guessing:

| Signal | Resolution |
|---|---|
| Camry 2500 plain = Hybrid vs VIN1/6 = Petrol | plain → A25A-FXS hybrid; VIN1/6 → A25A-FKS gas |
| Corolla 1800 VIN C/D = Hybrid | Corolla Hybrid 2ZR-FXE 121hp |
| RAV4 2500 VIN 6/W = Hybrid; bare = Petrol | VIN → A25A-FXS; bare 2019+ → A25A-FKS gas |
| Tundra 3400 VIN A/C = Petrol (both) | both → V35A-FTS (i-FORCE 389hp; MAX hybrid 437hp shares the engine) |
| Tacoma 2024+ 2400 B–E = Petrol | all → T24A-FTS (228/270/278 gas; MAX 326 shares the engine) |

Hybrid-only US lineups (web-verified, fuel fixed): **2025 Camry (all-hybrid XV80)**, **Sienna 2021+**,
**Venza 2021+**, **Sequoia 2023+ (i-FORCE MAX)**, **Land Cruiser 2024+ (250 series)**, **Crown 2023+**
(A25A-FXS 236hp / T24A-FTS MAX 340hp), Grand Highlander (2500 = A25A-FXS, 2400 = Hybrid MAX 362hp),
Prius (gen2 1NZ-FXE / gen3-4 2ZR-FXE / **gen5 M20A-FXS 194hp**), Mirai (hydrogen FCEV), bZ4X (EV).

Supra linked to the BMW rows created in batch 5: 2020 → `B58B30 (40i)` 335hp; 2021+ →
`B58B30 (M40i/M340i)` 382hp; 2.0 → new `B48B20 (Supra 2.0)` 255hp. GR86 → FA24; GR Corolla
("GR" rows) → G16E-GTS; 86 → FA20.

## Top mappings (469 total)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| A25A-FXS (2.5 hybrid family) | 63 | | 2ZR-FXE (Prius/Corolla H) | 21 |
| 2GR-FE (3.5 V6 family) | 41 | | T24A-FTS (2.4T i-FORCE) | 23 |
| 2GR-FKS (3.5 D-4S) | 39 | | 2UZ-FE (4.7 V8) | 18 |
| 3UR-FE (5.7 V8) | 35 | | 1NZ-FE (1.5) | 15 |
| 1GR-FE (4.0 V6) | 33 | | V35A-FTS (3.4TT) | 15 |
| 2ZR-FE (1.8) | 27 | | 2TR-FE (2.7) | 15 |

New engines (10): 2GR-FKS, M20A-FKS, M20A-FXS, T24A-FTS, V35A-FTS, FA24, G16E-GTS,
B48B20 (Supra 2.0), Mirai FCEV, bZ4X Electric. Row-fixes: 1NZ-FXE (fuel→Hybrid), 2ZR-FXE label,
A25A-FKS/FXS NULL rows completed, 2ZZ-GE power 180.

**Fuel-label unification:** `Electric Motor` → `Electric` (14 engines + 30 variants) — engines table
now has exactly 5 fuel values (Diesel/Electric/Ethanol/Hybrid/Petrol).

## Step 18b — spec normalization

17 ESTIMATE overrides + 5 majority normalizations + 15 power syncs + 8 NULL-power variant fills.
Two majority values manually corrected after review (lemon-majority ≠ OEM spec): **B58 6.52L**
(BMW official, restored) and **2AR-FE 0W-20** (Toyota US spec). All other values plausible
(1GR-FE 5.2L ✓, 2UZ-FE 6.15L ✓, 3UR-FE 7.47L ✓, 2ZR-FE 0W-16 ✓, V35A-FTS 7.28L ✓).
**Result: 0 ESTIMATE among step-18 targets, 0 power mismatches, 0 orphans, 0 count mismatches.**

### Known limitations (accepted)

- Euro-power rows carry Euro figures (3UR-FE 362 vs US 381; 1GR-FE 278 vs US 236-270; 1AR-FE 188 vs
  182; 2AR-FE 181 vs 179) — noted in evidence.
- T24A-FTS / V35A-FTS single rows cover multiple tunes and the hybrid MAX variants (same engine
  + motor); system power differences noted in engine_type.
- Matrix 2005-2008 bare → 1ZZ-FE (base/XR majority; 2ZZ XRS minority noted).

## Skipped by design (2)

- **Crown 2025 bare** — A25A-FXS vs T24A-FTS MAX unknown.
- **Tundra 2020 bare** — 4.6 1UR-FE vs 5.7 3UR-FE unknown.

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 11,631 | 11,172 (−469 retired LEMON rows, +10 new) |
| LEMON total (all brands) | 6,178 | **5,709** |
| Toyota LEMON remaining | 471 | 2 (intentional skips) |
| ESTIMATE / orphans / count / power mismatches | 0 | **0** |

**Next batch (LEMON-count order): Kia 392** → Hyundai 391 → Lexus 322 → Honda 312 → Mazda 303 →
Cadillac 269 → Jaguar 258 → VW 237 → Infiniti 230 → … (~5,709 remaining across 38 brands).
