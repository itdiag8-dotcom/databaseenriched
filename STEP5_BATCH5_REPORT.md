# Step 5 — Batch 5 Report: BMW LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step14_step5_lemon_batch5_bmw.py` (+ `step14b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step14_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/22_lemon_batch5_decisions.csv` (per-variant, with evidence)

Per the user-selected LEMON-count order, batch 5 = **every remaining LEMON BMW variant** (780 rows,
91 models, years 2000–2025). **697 variants remapped, 83 skipped** (documented below), 697 LEMON
codes retired, 24 new engine rows, 15 row-fixes, 50 fuel fixes (Hybrid 28, Diesel 13, Electric 9).

## Method — trim-name + cc rules

BMW LEMON codes are US **model names** (328i, 550i, X5, M3, Alpina…) with no VIN signal, but —
unlike Mercedes — the X3/X4/X5/X6/X7/Z4 codes carry a **cc segment** (`LEMON_BMW_X5_3000CC_2016`),
which separates trims (28i/30i vs 35i/M40i vs 50i) on SUVs/roadsters. Rules are therefore keyed on
**(model, year range, cc)** for X/Z models and **(model, year range)** for cars, since each BMW
car trim has exactly one engine per generation. All generation splits were web-verified (~45
sources in the script's `CIT` dict). Notable verification work:

| Question | Answer | Evidence |
|---|---|---|
| F01 740i/Li engine | **N54** 315hp (2011–12) → **N55** (2013 FL) | Wikipedia F01, bmwblog 2011 740Li first drive |
| 750i G11 LCI power | 445hp (2016–18) → **523hp** (2019+) | ultimatespecs G11 LCI |
| G70 760i (2023+) | **S68** 4.4TT 48V, 536hp | The Drive, bmwblog |
| US 540d (2018) | **B57D30** 261hp | autoevolution, cars.com |
| Alpina timeline | 500hp SC (07–08) → 540hp (2013+) → 600hp (G12 17–20) → 612hp (21+) | horsepowerspecs, C&D 2013 B7, Edmunds 2011 |
| M2 family | N55 365 → S55 Comp 405 (2019) → S58 453 (G87) | carbuzz generations |
| X5/X7 V8 years | 50i 445/456hp → M50i **523hp from 2020**; M60i (2024+) also 523 | C&D 2020 M50i, KBB 2024 |
| X1 2023 (US) | **single trim** xDrive28i 241hp → mappable | KBB 2023 |
| E90 323i (2006–11) | Canadian-market N52B25 200hp | auto-data.net, eBay engine listing |
| 528i 2011 anomaly | late **E60** (N52) — its 6.52L sump matches 2010, not F10's 5.01L | lemon spec fingerprint |

## Top mappings (697 total, 57 target codes)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| N55B30A (3.0T 300hp: 335i/535i/640i/X3-X6 35i/Z4 35i) | 71 | | N20B20 (328i/28i US 240hp) | 23 |
| B48B20 (30i) | 54 | | N63B44 (750i/550i/650i 400hp) | 23 |
| B58B30 (40i) | 54 | | M54B25 (325i/525i) | 18 |
| N63B44B (N63TU 445hp) | 42 | | S63B44B (F10 M5/M6 560hp) | 18 |
| B58B30 (M40i/M340i 382hp) | 37 | | N62B48B (550i/650i/750i 360hp) | 16 |
| N63B44TU2 (523hp M-perf) | 34 | | N62B44 (545i/745i/645Ci/X5 4.4i) | 15 |
| M54B30(306S3) (330i/530i/X5 3.0i) | 25 | | B48 2.0 PHEV (330e/530e) | 13 |
| N54B30O0 (N54 300hp) | 24 | | |

New engines (24): S58B30 (M3/M4) 473hp + S58B30 (M2) 453hp + S55B30 (M2 Comp) 405hp +
N55B30 (M2) 365hp + N55B30 (M235i/135is) 320hp + B48 2.0T (M235i GC) 301hp +
S63B44T2 (M5 F90/M8) 600hp + N63B44TU2 (523hp) + S68 (760i) 536hp + B58B30 (40i) +
B58B30 (M40i/M340i) + B48B20 (30i) + N20B20 (328i/28i US) + B48 2.0 PHEV (30e/740e) +
B58 3.0 PHEV (745e) + N20 2.0 PHEV (X5 40e) + B57D30 (540d) + N47D20 (328d) +
**i3 Electric (I01)** (9th Electric engine) + 4 Alpina rows (E65 SC / F01-F06 540 / G12 600 / 612).
15 row-fixes on reused rows (junk displacement corrections like N55B30A 3926→2979cc,
N54B30O0 2265→2979cc, M52TUB28 2470→2793cc; i8 B3815KT0 → Hybrid 357hp).

## Step 14b — spec normalization (13b/13c pattern, combined)

- **29 ESTIMATE** heuristic oil specs on targets overridden with variant-weighted lemon-crawl
  majorities from the pre-step-14 backup; **12 further targets normalized** to majorities
  (first-code merges); 30 stale/NULL spec `power_hp` synced from `engines` (incl. N63B44 specs
  547→407, i8 228→357); 15 pre-existing NULL-power Euro variants filled.
- Verified plausibility: M54/N52/N54/N55 I6 ≈ 6.52L (6.9qt) ✓, M cars 10W-60 ✓ (S54 5.48L,
  S65 8.8L — the famous big sump), S85 9.27L, M73B54 7.57L — this correctly fixes step-11's
  8.0 value, which was quarts entered as litres (8.0qt = 7.57L) ✓.
- **i3 Electric note:** the lemon oil values (0W-30/2.6L) are the 647cc 2-cyl **range-extender**
  engine's oil; pure-BEV i3s have no engine oil — recorded in the spec source.
- **Result: 0 ESTIMATE among step-14 targets, 0 spec-power mismatches, 0 orphan refs,
  0 count_variants mismatches.**

### Known limitation (accepted, as batches 1–4)

One spec row per engine code means same-code tune/sump variation is represented by the variant
majority: B58B30 (40i) 335hp row covers 320–375hp tunes (340i→G60 540i) and the 640i Gran
Turismo's larger 8.38L sump (2 rows vs ~50 at 6.52L); B48B20 (30i) 255hp covers 241–255hp;
N63B44B 8.99L covers G11 750i's ~10.4L; S62B50 6.52L (M5 majority) vs Z8's 7.57L oil-cooled sump.
Splits are only made where tune families differ materially (M2's three engines, M235i vs 228i).

## Skipped by design (83)

- **No cc/trim signal on multi-engine models**: X5 ×17, X3 ×13, X6 ×13, Z4 ×10, X4 ×6 (bare rows:
  30i vs 35i vs 50i vs diesel unknown).
- **Bare model, engine unknown**: 'M' ×6 (M3/M5/M6/Z3M/Z4M), X2 ×6 (228i 228hp vs M35i 301hp),
  ActiveHybrid ×5 (3/5/7/X6 hybrids all different), Z3 ×3, X1 2024+ ×2 (28i vs M35i).
- **Non-existent US model-year**: 535i 2017, 550i 2017 (F10 ended 2016; G30 = 540i/M550i).
- These stay on `LEMON_BMW_*` codes pending evidence (manual queue, not lost).

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 13,908 | 13,235 (−697 retired LEMON rows, +24 new) |
| LEMON total (all brands) | 8,525 | **7,828** |
| BMW LEMON remaining | 780 | 83 (intentional skips) |
| ESTIMATE among step-14 targets | — | **0** |
| Orphan refs / count mismatches / power mismatches | 0 | 0 |
| Electric / Hybrid engines | 8 / 270 | 9 / 271 |

**Next batch (LEMON-count order): Chevrolet 653** → Audi 576 → Nissan 520 → Toyota 471 →
Kia 392 → Hyundai 391 → Lexus 322 → Honda 312 → Mazda 303 → … (43 brands, ~7,828 remaining).
