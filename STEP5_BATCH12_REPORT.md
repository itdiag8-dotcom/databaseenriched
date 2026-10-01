# Step 5 — Batch 12 Report: Lexus LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step21_step5_lemon_batch12_lexus.py` (+ `step21b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step21_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/29_lemon_batch12_decisions.csv` (per-variant, with evidence)

Batch 12 in LEMON-count order = **every remaining LEMON Lexus variant** (322 rows, 19 models,
MY2000–2025). **291 variants remapped, 31 skipped**, 3 new engine rows, 34 fuel fixes (Hybrid 31,
Electric 3).

## Baseline guard caught rewind #4

Pre-inventory check showed LEMON 12,637 / engines 17,916 (the branch point again). `git reset --hard
origin/...` restored the correct DB; the script's baseline assert (LEMON=4,946) then passed. No work lost.

## Method

Lexus LEMON codes are nearly all bare or **trim slugs that literally encode the powertrain**
(IS250/IS350/RCF/GX460/LS600H/NX300H/RX350…) — those mapped directly. cc/VIN rows carried the 2018+
IS/RC splits (2000cc VIN A = 2.0T 8AR-FTS; 3500cc VIN 8 = 2GR-FSE). Web-verified: **UX became
hybrid-only from 2023** (UX200 dropped after 2022, 181hp system — Car and Driver + Lexus dealer).

The DB's Toyota-family vocabulary (built in batch 9) covered nearly everything: 1MZ/3MZ/2GR-FE/FKS/FSE,
2UZ/3UZ/1UR/3UR, 4GR/3GR, 2ZR-FXE, 2AR-FXE, A25A-FXS, T24A-FTS, V35A-FTS, M20A-FXS, 2UR-GSE, 1LR-GUE.

| Model-era | Mapping |
|---|---|
| CT 200h / HS 250h | 2ZR-FXE / 2AR-FXE (hybrid-only models, fuel fixed) |
| ES 300→330→350 | 1MZ-FE → 3MZ-FE → 2GR-FE (ES300h slug → 2AR-FXE) |
| GS | 2JZ-GE (00-05) → 3GR-FSE (06) → 2GR-FSE (07-20); GS450h → 2GR-FXE |
| GX | 2UZ-FE (470) → 1UR-FE (460) → **T24A-FTS hybrid** (GX550 2024+, fuel fixed) |
| IS/RC | 2JZ-GE (IS300) → 4GR-FSE (IS250) / 2GR-FSE (IS350) / 8AR-FTS (300 2.0T) / 2UR-GSE (F) |
| LS | 1UZ-FE (LS400 '00) → 3UZ-FE (430) → 1UR-FE (460; 600h → new **2UR-FXE**) → V35A-FTS (LS500 3.4TT 416hp) |
| LX | 2UZ-FE (470) → 3UR-FE (570) → V35A-FTS (LX600 2022+) |
| NX | 8AR-FTS (200t/300) / 2AR-FXE (300h, incl. 2500cc VIN J/W) / T24A-FTS (NX350) |
| RX | 1MZ→3MZ→2GR-FE→2GR-FKS→T24A-FTS (2023+ 2.4T; VIN A/H) |
| UX | M20A-FXS hybrid (2019+ majority; hybrid-only 2023+) |
| LC 500 / LFA / RZ | 2UR-GSE / 1LR-GUE (553hp corrected) / new **RZ450e Electric** |

New engines (3): 1UZ-FE (LS400), 2UR-FXE (LS600h 438hp), RZ450e Electric (36 EV engines now).
Row-fixes (5 junk labels): 2JZ-GE ("300"), 8AR-FTS ("2 (est.)" → 241hp), 1LR-GUE (571→553hp US),
2GR-FXE, 4GR-FSE. Fuel fixes: 34 (CT/HS/NX300h/GS450h/LS600h/GX550/UX → Hybrid; RZ → Electric).

## Step 21b — spec normalization

9 ESTIMATE overrides + 7 majority normalizations + 5 power syncs + 3 NULL-power fills.
**One lemon-majority value rejected after verification:** 3UR-FE 9.27L → set to **8.0L** (documented:
LX570 8.5qt/8.0L 0W-20, Tundra 7.4qt/7.0L 5W-30 — the lemon crawl's 9.27 exceeds both; AMSOIL +
costaoils + seatcoversolutions sources). Other spot-checks: 2GR-FSE 6.43L ✓, 3UZ-FE 5.2L ✓
(LS430 5.4qt), 8AR-FTS 4.63L ✓, 2UR-GSE 8.61L ✓, 3GR-FSE 6.34L ✓.
**Result: 0 ESTIMATE among step-21 targets, 0 power mismatches, 0 orphans, 0 count mismatches.**

### Known limitations (accepted)

- Bare-row majority mappings noted (IS250 over IS350, LC500 over 500h, LS460 over 600h, NX300 over
  300h, UX250h over UX200, RX350 over hybrids, LS500 over 500h).
- V35A-FTS single row spans Tundra 389 / LX600 409 / LS500 416hp tunes (noted in evidence).
- T24A-FTS single row spans NX350/TX350/RX350 275hp + GX550/RX500h hybrid-MAX versions.

## Skipped by design (31)

ES 2016-2025 bare ×10 (350/300h/250 split), IS 2016-2017 ×2 + IS 2018-2025 bare ×8 (cc rows carry
the split), RC bare 2016-2025 ×9 (300 vs 350 vs F), SC 2000-2001 ×2 (SC300 vs SC400).

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 10,431 | 10,143 (−291 retired LEMON rows, +3 new) |
| LEMON total (all brands) | 4,946 | **4,655** |
| Lexus LEMON remaining | 322 | 31 (intentional skips) |
| ESTIMATE / orphans / count / power mismatches | 0 | **0** |

**Next batch (LEMON-count order): Honda 312** → Mazda 303 → Cadillac 269 → Jaguar 258 → VW 237 →
Infiniti 230 → Dodge 207 → Buick 205 → Subaru 205 → … (~4,655 remaining across 35 brands).
