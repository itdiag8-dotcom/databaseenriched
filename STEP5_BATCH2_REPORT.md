# STEP 5 — LEMON Synthetic Engine-Code Replacement — BATCH 2 (Mopar: SUVs / LX cars / Jeep / Ram 1500)

**Date:** 2026-09-30 · **Scripts:** `step10_step5_lemon_batch2.py` + `step10b_estimate_override.py`
**Backups:** `backups/car_database_backup_pre_step10_2026-09-29.db`, `..._pre_step10b_...db`
**Decisions log:** `csv_exports/18_lemon_batch2_decisions.csv` (per-variant, with evidence key)

## Summary

| Metric | Value |
|---|---|
| **Variants remapped to real OEM codes** | **638** (Jeep 232, Dodge 262, Chrysler 90, Ram 54) |
| LEMON engine rows retired | 638 |
| New engine rows created | 12 (`STEP10_VERIFIED`) |
| Variant fuel labels corrected | 38 (34 Petrol→Diesel, 4 Petrol→Hybrid) |
| In-scope rows deliberately skipped | 15 (all 653 in-scope rows accounted for) |
| LEMON variants remaining (batches 3+) | 10,114 |
| Engines table | 16,081 → 15,454 |
| `v_vehicle_with_service` coverage | 39,086 (unchanged) |

## Scope (user-directed batch 2)

Grand Cherokee, Wrangler, Gladiator, Cherokee, Liberty, Commander, Durango, Charger, Challenger,
Magnum, Dakota, Nitro, Chrysler 300, Aspen, Ram 1500.

## Citations (evidence keys)

| Key | Source |
|---|---|
| HEMI | https://en.wikipedia.org/wiki/Chrysler_Hemi_engine — 5.7 applications + 2009 VCT revision (power table per car/truck); 6.1 SRT8 apps 2005-2010; 6.2 Hellcat apps (Challenger/Charger 2015+, GC Trackhawk 2018-21, Durango SRT Hellcat 2021+, Ram TRX 2021-24); 6.4 "Apache" 392 apps + 2015 485 hp bump |
| POWERTech | https://en.wikipedia.org/wiki/Chrysler_PowerTech_engine — 4.7 V8: Dakota 2000-2007, Durango 2000-2009, GC 1999-2009, Commander 2006-2009, Aspen 2007-2009 |
| LEMON2015 | `lemon_crawl_2015.jsonl` primary crawl — ground truth: 3.6L = VIN G, 5.7L = VIN T, 3.0L EcoDiesel = VIN M, 2.4L = VIN B (Eng CD ED6/ED8), 3.2L = VIN S, 2.0L = VIN N; Challenger Eng CD **EZC/EZH** (5.7) and **ESG/ESH** (6.4) |
| RAMVIN | https://truckguider.com/dodge-ram-engine-codes-by-year-chart/ |
| HURRICANE | https://www.edmartincdjr.com/ram-1500-3.0l-hurricane-twin-turbo-i6-engine-overview + https://www.almachryslerjeepdodgeram.com/dodge-ram-hurricane-engine-specs/ — 3.0 twin-turbo I6 replaces the 5.7 for 2025 Ram 1500 (SO 420 hp) |
| RAMOIL | https://www.jcofontario.com/service-department/service-and-parts-tips/ram-2500-oil-type/ (5.7 std 2011-2018; 6.4 2014+) |

## Target codes assigned

3.6 Pentastar 172 · EZH 121 (5.7 VCT) · EVA 40 (4.7) · EKG 40 (3.7) · EXL 29 (3.0 EcoDiesel) ·
6.2 Hellcat V8 29 · ESH 24 (6.4 485hp) · ESF 21 (6.1 SRT8) · 2.0 Turbo GME 19 · 3.5 V6 (LX) 17 ·
EER 15 (2.7) · EZD 14 (5.7 pre-VCT) · 4.0 I6 (AMC) 13 · EZC 11 (5.7 LX pre-VCT) · ESG 10 (6.4 470hp) ·
5.9 Magnum V8 8 · EDZ 8 (2.4) · 3.2 Pentastar 7 · 2.5 I4 (AMC) 7 · ED6 6 · EGH 5 (3.8 JK) ·
ESA 5 (Wrangler 392) · 3.9 Magnum V6 4 · 2.0 Turbo GME (4xe) 4 · 3.0 CRD (OM642) 3 · R428 2 (2.8 CRD) ·
3.0 Hurricane I6 2 · 5.2 Magnum V8 1 · 5.7 HEMI Hybrid 1

## Key mapping decisions

- **5.7 HEMI three-way split:** VIN T (crawl ground truth) → EZH; no-VIN LX cars (300/Charger/Magnum)
  2005-2008 → EZC (340 hp pre-VCT), 2009+ → EZH; no-VIN trucks/SUVs (Durango/GC/Commander/Aspen)
  2004-2008 → EZD (345 hp), 2009+ → EZH. Challenger 5.7 (2009+) → EZH.
- **6.4 split:** ESG = Apache 470 hp (2011-2014 SRT8, per-crawl Eng CD ESG) · ESH = 485 hp 2015+
  (crawl Eng CD ESH; engine row aligned to 485 hp/6,415 cc) · Durango SRT 2018+ → ESH ·
  Wrangler Rubicon 392 2021+ → ESA (470 hp truck-family tune).
- **6.2 → `6.2 Hellcat V8`** (707 hp): Challenger/Charger 2015+, GC Trackhawk 2018-21, Durango SRT
  Hellcat 2021+, Ram 1500 TRX 2021-24. (Redeye/Demon sub-variants not distinguishable — noted.)
- **Jeep diesels:** 3.0 VIN M (2014+) → EXL (VM A630 EcoDiesel); WK 3.0 CRD **2007-2009 → new
  `3.0 CRD (OM642)`** (different engine — Mercedes OM642); Liberty 2.8 → new `R428`.
- **2025 Ram 3.0 VIN P → new `3.0 Hurricane I6`** (only 3.0 offered in 2025 Ram; EcoDiesel ended 2023).
- **GC 2.0 2022+ → `2.0 Turbo GME (4xe)`** PHEV (fuel fixed to Hybrid); Wrangler/Cherokee 2.0 VIN N →
  `2.0 Turbo GME` (gas).
- **Engine-row fixes:** EDZ `2.4 V6` → **2.4 PowerTech I4** (wrong config); EZC 383→340 hp (300C/Magnum
  R/T per HEMI wiki); EXL typed/sized; ESH aligned; EZH typed.
- **Aspen 5.7 Hybrid → new `5.7 HEMI Hybrid`** (two-mode, 399 hp per HEMI wiki).

## Step 10b — estimate-override follow-up (also benefits batch 1)

The batch-1/2 spec migration merge-fills NULLs only. Audit found **32 target engines** whose
service-spec rows still carried "ESTIMATE (heuristic, not OEM)" placeholders (LM7, LQ4, LQ9, LR4,
LY2/LY5/LY6, L18, LB7/LBZ, LU3, LC9/LMG, L20, L52/LLV/LLR/LH8, L92/L9H, LFA/LZ1, EXL, EZD, EVA,
EKG, EER, ESF, EGH, EDZ, ESG-642, L52, '3.5 V6 EcoBoost') while real crawled lemon specs existed
for the same engines (recovered from pre-step9/pre-step10 backups). Those were overridden with the
newest-year trusted lemon row (e.g. EXL now 5W-40 / 8.51 L / 13.72 L coolant from the Gladiator
EcoDiesel crawl). OEM/lemon-sourced values were never touched. **0 ESTIMATE sources remain among
all step-9/10 target engines.**

## Deliberately skipped (15 rows)

| Group | Rows | Reason |
|---|---|---|
| Nitro 4.0 (2007-2011) | 5 | 4.0 V6 (EVJ?) identity unverified |
| Cherokee 3.2 VIN X (2018-2022) | 5 | VIN X unverified (crawl ground truth says S) |
| GC bare 2022/2025 | 2 | 3.6 vs 4xe ambiguous |
| Dakota 3.7 2004 | 1 | gen-3 Dakota (3.7) started 2005 |
| Cherokee bare 2001 | 1 | XJ 2.5 vs 4.0 ambiguous |
| Challenger bare 2008 | 1 | SE 3.5 vs SRT8 6.1 ambiguous |

## Remaining LEMON inventory (batch 3+)

10,114 rows: Mercedes 968, BMW 780, Ford 743 (cars/SUVs/crossovers), Chevrolet 653, Audi 576,
Nissan 520, Toyota 471, Kia 392, Hyundai 391, Lexus 322, Honda 312, Mazda 303 …
Next per user plan: Ford Explorer/Edge/Escape, then the import brands.
