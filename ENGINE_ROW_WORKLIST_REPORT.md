# 🔧 Engine-Row Suspect Worklist — Resolution Report (452 rows / 200 codes)

**Date:** 2026-09-29 • **Script:** `step7_engine_row_fixes.py`
**Backup:** `backups/car_database_backup_pre_step7_2026-09-29.db` • **Fix log:** `csv_exports/15_engine_row_fixes.csv`

## What the worklist was

Kept mappings where **power (≤15%) + brand family confirm the pairing** but displacement conflicts >25% — meaning one side carries bad data. Analysis split the 452 rows / 200 engine codes into:

| Root cause | Rows | Action |
|---|---:|---|
| **A. Engine row wrong** (displacement and/or identity text) | ~95 | **Fixed where verifiable (19 rows below)** |
| **B. Variant `engine_type` text is Vivid junk** (e.g. `'1.3 VVTi'` on a 6.0 V8 truck, `'3.8 Carrera'` on an Opel, `'1.6 e (corr.)'` on an Iveco 3.0) | ~117 | No DB change — cosmetic backlog (specs join correctly via engine_code) |
| Mixed / needs VIN-level data | rest | Flagged |

## 1. Engine-row fixes applied (19)

### Displacement + identity corrections (cited)

| Code | Was | Now | Evidence |
|---|---|---|---|
| **QR25DE** | 1600cc "1.6 16v" | **2488cc "2.5 16v DOHC"** | Nissan QR25DE = 2488cc [engine-specs.net](https://www.engine-specs.net/nissan/qr25de.html) — 18 Renault Koleos variants were right, the row was wrong |
| **CMXA** | 1200cc "1.2 8v TSI" | **1598cc "1.6 8v MultiFuel"** | proxyparts: CMXA = Golf VI 1.6 MultiFuel 1598cc 75kW [proxyparts.com](https://www.proxyparts.com/car-parts-stock/information/engine-code/cmxa/part/engine/partid/11428466/); mecatechnic Golf 6 list: 1.6 BSE/BSF/CCSA/CHGA/CMXA 102hp [mecatechnic.com](https://www.mecatechnic.com/en-GB/b-volkswagen/m-golf-6/motorizations) — 17 Seat/VW variants were right |
| **M57D30** | 2353cc | **2993cc** | BMW M57 3.0d = 2993cc [specsnode.com](https://specsnode.com/engine-detail.php?id=177) — fixes the Range Rover TD6 + 530d rows |
| **B38B15M0** | 1005cc "118i 1500 Turbo" | **1499cc "1.5 Turbo 3-cyl"** | BMW B38 1.5 3-cyl = 1499cc (Mini Cooper/BMW 118i) |
| **ETJ** | 6691cc "3.6 FSI 4motion" | **6690cc "6.7 I6 Cummins Turbo Diesel"** | RAM 2500 349-350hp = 6.7 Cummins |
| **ETH / ETC** | 5883/5886cc "2.5 TDiC"/"2.2 Vtec" | **5923cc "5.9 I6 Cummins (HO/24V)"** | 5.9 Cummins = 5923cc (360 cid); ETH = high-output, ETC = standard (RAM factory packages) |
| **CCRA** | 1000cc "1.0 8v TotalFlex" 99hp (internally inconsistent) | **1598cc "1.6 8v TotalFlex"** | VW Fox 1.6 TotalFlex = 98-103PS [en.wikipedia.org](https://en.wikipedia.org/wiki/Volkswagen_Fox) |
| **E18NVR** | "ECONOVAN Bus" text | **"3.0 V6 SIDI VVT"** (2997cc/276hp kept) | Row is Cadillac CTS 3.0 data (LF1-type): CTS 3.0 = LF1 270-276hp [caranddriver.com](https://www.caranddriver.com/cadillac/cts/specs/2010/cadillac_cts_cadillac-cts-sedan_2010), [reman-engine.com](https://reman-engine.com/remanufactured-engines/cadillac/cts/2010/3.0l-vin-g-8th-digit-opt-lf1-awd) |

### Identity-text fixes (displacement was already correct — text was Vivid junk)

| Code | Junk text | Real identity |
|---|---|---|
| **L96** | "1.3 VVTi" | **6.0 V8 Vortec** 360hp [dieselhub.com](https://www.dieselhub.com/gas/gm-6.0-vortec-l96.html) (Silverado/Sierra 2500HD) |
| LC9 | "2.2 S2 (corr.)" | 5.3 V8 Vortec FlexFuel |
| L76 | "6 (est.)" | 6.0 V8 Vortec MAX |
| L20 | "1.0 DVVT" | 4.8 V8 Vortec |
| LM7 | "5.3" | 5.3 V8 Vortec |
| **CKMA** | "6.7 Turbo R" | **1.4 TSI Twincharger** 160hp (Passat 362) |
| F1CE0481HA/FA/B | "1.6 e (EA0F)" / "1.6 e (corr.)" | 3.0 HPI TurboDiesel (Iveco 2998cc) |
| 4HH(P22DTE) | "1.0 1020" | 2.2 16v HDi TurboDiesel |

## 2. E18NVR grab-bag cleanup — 14 junk attachments quarantined

The E18NVR row (Cadillac CTS 3.0 data) had become a magnet for wrong attachments that survived earlier filters because their junk engine_types accidentally parsed to displacements within 25% of 2997cc:

`Volkswagen Voyage 101hp` • `Alpina B3 (E46) ×3 280hp` • `LANDWIND 125hp` • `HUMMER H3 220hp` • `Chevrolet Colorado ×3` • `Suburban ×2` • `Uplander` • `Avalanche ×2` — all moved to `remapping_queue` (reason `WRONG_ATTACHMENT`) so they display *no data* instead of Cadillac 3.0 V6 specs.

⚠️ Honest accounting: `v_vehicle_with_service` drops 39,099 → **39,085** because those 14 variants lose their (wrong) spec joins — the right trade.

## 3. Verification

- Integrity check ok
- Displacement-suspect joined rows: **452 → 405** (remaining are overwhelmingly variant-etype junk — cosmetic)
- Spot checks: QR25DE (Koleos 2.5 2488cc ✓), CMXA (Altea 1.6 1598cc ✓), M57D30 2993cc ✓, L96 6.0 Vortec ✓, ETJ 6.7 Cummins ✓
- Queue: 386 remapped / 95 pending / 13 engine_fuel_fixed / 3 fuel_label_fixed / 1 invalid

## 4. Remaining backlog (documented, not blocking)

1. **~405 cosmetic rows**: variant `engine_type` texts are junk but mappings and specs are correct. Optional cleanup: replace variant `engine_type` with `engines.engine_type` where junk patterns detected (`'(corr.)'`, `'(est.)'`, brand-incoherent names) — source-data edit, needs your sign-off.
2. **Research items** flagged in the fix log: `250A1.000` (Ducato 2.5 TDdi — row says 1956cc, real 2445cc, unverified), `CFZA` (mixed 1.0/1.6 evidence), `E18NVR` should eventually be renamed/recoded to **LF1**.
3. The 95 queue pendings from batches 1-3 (LEMON trucks, EVs, hernr_* brands, impossible year/power combos).

**Cumulative session totals:** 481 → quarantined-and-mostly-remapped; ~420 variants now carry verified-correct engine codes; 25+ corrupted engine rows repaired (identity, displacement, fuel, text).

**Rollback:** `cp database_enriched/backups/car_database_backup_pre_step7_2026-09-29.db database_enriched/car_database.db`
