# Step 5 — Batch 8 Report: Nissan LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step17_step5_lemon_batch8_nissan.py` (+ `step17b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step17_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/25_lemon_batch8_decisions.csv` (per-variant, with evidence)

Batch 8 in LEMON-count order = **every remaining LEMON Nissan variant** (520 rows, 25 models,
MY2005–2025). **513 variants remapped, 7 skipped** (documented below), 8 new engine rows,
32 fuel fixes (Electric 28, Diesel 4).

## Method

Nissan's US lineup is nearly one-engine-per-model: the DB's QR/VQ/VK/MR/HR family vocabulary covered
almost everything (QR25DE, VQ35DE/HR, VQ37VHR, VQ40DE, VK56DE/VD, VR38DETT, MR18/MR20, HR16DE,
MR16DDT, QG18DE). Signals: cc + VIN chars + 2015 trim slugs (S/SV/SL/NISMO = same engine).

Web-verified facts:

| Question | Answer | Evidence |
|---|---|---|
| Frontier 2020–2025 bare rows | **VQ38DD** 3.8 V6 310hp (debuted MY2020, 9-speed; 0W-20) | autofiles.com VQ38DD registry, crownnissan.com |
| 2025 Kicks (new generation) | **2.0L 141hp** (1.6 HR16DE through 2024) | autopadre.com Kicks 2018-2025 |
| Ariya (0CC rows = EV) | 238hp FWD / 389hp e-4ORCE | nissanusa.com (discontinued page) |
| 2019+ Altima split | 2.0T VC-Turbo **KR20DDET** 248hp (VIN A) / new-gen 2.5 **PR25DD** 188hp (VIN B) | Nissan PR family (DB-family derived) |
| 2022+ Rogue | 1.5T VC-Turbo **KR15DDET** 201hp (the 2021 1500cc row = 2022MY) | Nissan PR family |
| Titan XD "5000cc VIN B" | **5.0 Cummins ISV V8 turbodiesel** 310hp | Cummins/Nissan documentation |

## Top mappings (513 total)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| VQ35DE (Altima/Maxima/Murano/Pathfinder/Quest) | 91 | | VK56VD (Titan XD/Armada 17+/NV 17+) | 29 |
| VQ40DE (Frontier/XTerra/NV/Pathfinder) | 81 | | MR20DE (Sentra 07-12/20+/NV200/Kicks 25) | 24 |
| QR25DE (Altima/Sentra SE-R/Rogue/Frontier) | 69 | | MR18DE (Sentra/Versa/Cube) | 22 |
| VK56DE (Titan/Armada/Pathfinder/NV) | 48 | | VQ37VHR (370Z incl. Nismo) | 18 |
| HR16DE (Versa/Sentra/Kicks) | 37 | | Leaf Electric EM57 | 17 |

New engines (8): PR25DD, KR20DDET, KR15DDET (VC-Turbo family), VQ38DD, VR30DDTT (2023+ Z, 400hp),
**Leaf EM57 + Ariya Electric** (Electric engines now 15), 5.0 Cummins ISV V8 TD (Titan XD).
Fuel fixes: 32 (Leaf 17 + Ariya 11 → Electric; Titan XD 4 → Diesel).

## Step 17b — spec normalization

10 ESTIMATE overrides + 2 majority normalizations + 8 power syncs + 5 NULL-power variant fills.
**Result: 0 ESTIMATE among step-17 targets, 0 power mismatches, 0 orphan refs, 0 count mismatches.**
Plausibility spot-checks: VQ35DE 4.85L ✓, VQ40DE 5.09L ✓, VK56DE 6.51L ✓, QR25DE 4.61L ✓,
VR38DETT 0W-40/5.44L ✓ (GT-R spec), MR16DDT 0W-20/4.49L ✓ (Juke 1.6T).

### Known limitations (accepted)

- Shared rows keep Euro power figures where they differ (VR38DETT 479 vs US 485-545 by year;
  VK56VD 360 vs US 390/400; VQ37VHR 325 vs US 332-350; MR20DE 139 vs US 131-149).
- QG18DE oil 2.69L is the merged-data majority (shop range 2.9-3.2L) — left as merged value.

## Skipped by design (7)

- **Titan 2017–2019 bare ×3** — 5.6 gas vs 5.0 Cummins XD unknown.
- **NV3500 2012/2013 bare ×2** — 4.0 vs 5.6 unknown.
- **Versa 2007–2008 bare ×2** — 1.6 vs 1.8 unknown.

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 12,136 | 11,631 (−513 retired LEMON rows, +8 new) |
| LEMON total (all brands) | 6,691 | **6,178** |
| Nissan LEMON remaining | 520 | 7 (intentional skips) |
| ESTIMATE / orphans / count / power mismatches | 0 | **0** |

**Next batch (LEMON-count order): Toyota 471** → Kia 392 → Hyundai 391 → Lexus 322 → Honda 312 →
Mazda 303 → Cadillac 269 → Jaguar 258 → VW 237 → … (~6,178 remaining across 39 brands).
