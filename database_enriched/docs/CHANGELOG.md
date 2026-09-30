# Changelog — From Original to Enriched

**Original file:** `uploads/all_cars_from_xlsx.csv` (read-only)  
**Enriched output:** `database_enriched/*` (this folder)  
**Build date:** 2026-09-11

---

## Summary

| Area | Original | Enriched | Change |
|---|---|---|---|
| Rows | 9 746 | 9 439 | **-307** duplicates removed |
| `car_year` empty | 586 (NOT NULL attempted) | nullable, filled where possible | Schema relaxed to `INTEGER NULL`; empty → `production_start` fallback else NULL |
| `car_year` coverage | 9 160 filled | 9 239 filled (200 rescued via production fallback) | +200 years recovered |
| Distinct `car_brand` | 84 | 95 canonical (144 raw) | +11 canonical brands from external sources; 49 duplicate capitalizations/accent variants merged |
| Distinct `car_model` | 864 | 4 299 | **+3 435** added missing models |
| Models with production years | 864 (derived) | 3 137 with years + 1 162 NULL | All models now have `production_start`/`end` columns; added sources provide years where available |
| Distinct `engine_id` | 2 607 distinct | 2 607 distinct (same set) | — |
| Engine service specs | 0 | 2 607 | **New table/CSV** per engine_code |
| Engine diagnostic specs | 0 | 2 607 | **New table/CSV** per engine_code |
| Brands table | — | 95 rows | New |
| Models table | — | 4 299 rows | New |
| Engines table | — | 2 607 rows | New |
| Vehicle variants table | — | 9 439 rows | New (deduped source) |
| Views | — | 3 (`v_engine_full`, `v_model_overview`, `v_vehicle_with_service`) | New |

---

## Detailed changes

### 1. Deduplication

- **Before:** 9 746 rows included 307 exact duplicates (same brand, model, year, engine_id, engine_type, ecu_maker, ecu_model, fuel, power).
- **After:** 9 439 rows. Dedup key logged in builder: `seen[(brand.lower(), model.lower(), car_year, engine_id.lower(), engine_type.lower(), ecu_maker.lower(), ecu_model.lower(), fuel.lower(), power_hp)]`.
- **Verification:** `wc -l` 9747 → 9440 lines in `01_vehicles_deduped.csv` (header + 9439).

### 2. `car_year` nullability

- **Attempt 1 failed:** SQLite `NOT NULL` constraint raised `sqlite3.IntegrityError: NOT NULL constraint failed: vehicle_variants.car_year` on row 587 (empty year).
- **Fix:** `vehicle_variants.car_year INTEGER` (no NOT NULL) + application logic: if `car_year` empty, fill from model’s `production_start` if that is numeric, else store `NULL`. No rows lost.

### 3. `engine_service_specs` column fix

- **Attempt 1 failed:** `sqlite3.OperationalError: 40 values for 39 columns` on both `engine_service_specs` and `engine_technical_specs` (hard-coded 40 `?` placeholders for 39 columns; extra `transmission_oil_type` phantom column).
- **Fix:** placeholders reduced to 39, insert lists aligned to 39 columns. Build now succeeds with 2 607 rows each.

### 4. Brand normalization

- **Before:** external sources introduced accent/case variants: `AUDI` vs `Audi` (14 vs 235 variants), `Bmw` (10) vs `BMW` (333), `Citroen` vs `Citroën`, `Mercedes-Benz` vs `Mercedes`, `FORD` vs `Ford`, etc. — total 144 distinct brand strings.
- **After:** NFKD accent stripping + lowercasing + synonym map (`Mercedes-Benz`→`Mercedes`, `VW`→`Volkswagen`, `Citroën`→`Citroen` treated as same) + canonical display map (e.g. `bmw`→`BMW`, `volkswagen`→`Volkswagen`) → **95** brands. `models.brand_name` and `vehicle_variants.car_brand` updated; duplicate brand rows deleted (49 removed). `models` dedup checked — 0 duplicate `(brand,model)` after update.

### 5. Added missing car models

- **Sources:** `gor3a/vehicle-makes-models` (2 621), `plowman/open-vehicle-db` (1 678), `DanielKohut/car-data` (4 202 after JSON comma fix).
- **Filtering (cars only):**
  - `gor3a` kept only if brand normalized already exists or in 60-brand passenger whitelist.
  - `Daniel` & `open-vehicle-db` kept only if brand already in original (prevents bike/truck/ATV models).
- **Dedup:** lowercased `(brand,model)` against existing + accumulating added set → 3 435 unique added.
- **Production years:** gor3a/open-vehicle-db contributed 2 273 with years; Daniel contributed 1 162 year-less rows stored as `NULL` / `""` with note.
- **Storage:** `models` table (`status='added_missing'`), `02_models_production.csv`, `06_missing_models_added.csv` (provenance), `json/models_production.json`.

### 6. New: production start/end for all models

- **Existing 864 models:** `production_start = MIN(car_year)`, `production_end = MAX(car_year)` across variants.
- **Added 3 435 models:** harvested as above; stored as nullable INTEGER.
- **Vehicle-level:** `vehicle_variants.production_start/end` joined per `(brand,model)` for easy lookup; also added to `01_vehicles_deduped.csv` as extra columns.

### 7. New: engine_service_specs (2 607 rows)

- Per-engine heuristics (brand+fuel+displacement+year+engine_type keywords, seed 42) generate: oil viscosity/standard/ACEA/OEM spec/capacity, coolant type/spec/capacity, timing type (Belt/Chain/wet) + intervals, air/fuel/brake/spark/aux intervals.
- All 2 607 engine codes covered (100 %).
- See README §2 for mapping tables.

### 8. New: engine_technical_specs (2 607 rows)

- Heuristics + physics (bore/stroke from volume) generate: bore/stroke, compression ratio/pressures, fuel pressures, oil pressures, idle RPM, valve clearances, ignition timing, spark plugs, torque/power curves, emissions, DPF/EGR/AdBlue flags, ECU.
- See README §3.

### 9. New: reminders template

- `05_maintenance_reminders_template.csv` — 10 service types with `urgency` + interpolatable description/action, plus final NOTE row explaining `last_service + interval` logic. Engine-specific intervals joined at runtime via `engine_code`.

### 10. New: SQLite DB + views

- Tables: `brands`, `models`, `engines`, `vehicle_variants`, `engine_service_specs`, `engine_technical_specs`.
- Views: `v_engine_full` (engines+service+tech), `v_model_overview` (models+variant count), `v_vehicle_with_service` (vehicle+service+tech).
- Indexes: `models(brand_name)`, `vehicle_variants(car_brand,car_model)`, `vehicle_variants(engine_code)`, `engines(fuel)`.

### 11. Bug fixes of external source

- `DanielKohut/car-data` JSON was broken (`"]\n    "` missing comma between brand arrays, e.g. after `Amphicar` list). Fixed via `re.sub(r'\]\s*\n\s*"(?=[A-Z])', '],\n    "', txt)` → validated `json.load` succeeds; 4 202 models recovered.

### 12. Documentation

- Added `docs/README.md`, `SCHEMA.md`, `INTEGRATION_GUIDE.md`, `SOURCES.md`, `CHANGELOG.md` (this file) — none existed before. All are inline-preview-safe (no external CDN).

---

## Migration impact for your app

- **Breaking if you assumed `car_year` always int:** it is now `INTEGER NULL` — handle `NULL` in picker (filter or show “—”).
- **Breaking if you assumed brand strings are as in original XLSX:** canonical brands differ in case (`Bmw`→`BMW`, `Mercedes`→`Mercedes`, `AUDI`→`Audi`). Update brand pickers to use `brands` table; it contains the normalized set.
- **New columns:** `vehicle_variants.production_start/end` and `models.production_start/end` — adapt list screens to show range.
- **New joins required for reminders/diagnostics:** previously no engine specs; now join `engine_service_specs` / `engine_technical_specs` by `engine_code`.

---

## Reproducibility

- Builder script: `/home/user/build_enriched_db.py` (1667 lines) + inline patch; `random.seed(42)`.
- Re-run produces identical row counts unless original CSV or clones under `/tmp/repo_*` change.
- External clones pinned to 2026-09-11 fetch; counts logged (`Found 2621 gor models, 1678 ovdb models, 4202 daniel models`).

---

## 2026-09-29 — Step 1: Quarantine of wrong engine mappings (data-safety fix)

- 481 variant→engine mappings that were physically impossible (hard fuel conflicts, >25% displacement mismatches, >30% cross-brand power mismatches) had `engine_code` set to NULL and were moved to the new **`remapping_queue`** table for review/remapping (`status='pending'`).
- Legitimate cross-brand engine sharing was explicitly preserved via a brand-family map (GM, VW Group, FCA, PSA+Opel, Renault-Nissan, Hyundai-Kia, Ford+PAG, Toyota+Subaru, BMW+Mini) and hybrid-aware fuel rules: real diesel-hybrids (Mercedes E300de, Peugeot 508/3008 Hybrid4, BMW i3 REX), tune families (N47D20C, 4G63T, OM651) and badge-engineered shares (A13DTE: Fiat/Opel/Vauxhall/Chevrolet) are all still joined.
- 452 kept-but-suspect rows exported to `csv_exports/09_engine_row_suspects.csv` (wrong engine-row displacement, e.g. B38B15M0 1005cc vs real 1499cc, or junk Vivid engine_type text).
- `engines.count_variants` recomputed. View `v_vehicle_with_service`: 39,182 → 38,701 rows.
- Tooling: `step1_quarantine_wrong_mappings.py` (dry-run/apply), report: `STEP1_QUARANTINE_REPORT.md`, pre-change backup: `backups/car_database_backup_pre_step1_2026-09-29.db`.

## 2026-09-29 — Step 2: model-name case normalization

- 1,655 variant (brand, model) values renamed to the models-catalog casing (Vivid ALL-CAPS artifacts, e.g. 'ASTRA J' → 'Astra J'). Variants↔models orphan joins: 1,748 → 0.
- 39 models added for pairs existing only in variants (Subaru Traviq, Isuzu N Series, Ford E-Series, Mazda Demio…) with derived production years; flagged mis-branded rebadges (SATURN Corsa/Agila…) and typos (Crow Victoria) for Step 3.
- models.total_variants recomputed for all rows (1,001 wrong counts fixed). Change logs: csv_exports/10_model_name_changes.csv, 11_added_models.csv. Backup: backups/car_database_backup_pre_step2_2026-09-29.db. Report: STEP2_NORMALIZATION_REPORT.md.

## 2026-09-29 — Step 4 batch 1: remapped the 45 POWER_MISMATCH_CROSSBRAND rows (web-verified)

- 44 of 45 quarantined power-mismatch variants remapped to verified engine codes with citations (report: REMAPPING_REVIEW_BATCH1.md, decisions: csv_exports/12_remap_batch1_decisions.csv). 3 rows left pending (ambiguous: 520i E60 156hp, CTS Sport Wagon 2007, Equinox 2002), 1 marked invalid_data (NOVA 19hp).
- Engine identity fixes: 1MZ-FE (was 429hp Jaguar junk -> 2995cc/201hp Toyota), N52B30 (1300->2996cc), N47D20/C (1482->1995cc), N63B44 (547->407hp), M47D20TU2, AJ126 (2995cc).
- 22 Jaguar 3.0 SC V6 variants moved from 1MZ-FE to AJ126; X5 M E70 moved to S63B44; 3 rows wrongly kept by the brand-family rule re-quarantined and 2 of them remapped (GX460 -> 1UR-FE, JDM Cruze -> M15A).
- v_vehicle_with_service: 38,701 -> 38,742. Backup: backups/car_database_backup_pre_step4_2026-09-29.db.

## 2026-09-29 — Step 4 batch 2: fuel conflicts + displacement mismatches resolved

- 303 more quarantined variants restored to correct engines (38,742 -> 39,045 with specs; NULL codes 440 -> 137). Report: REMAPPING_REVIEW_BATCH2.md, decisions: csv_exports/13_remap_batch2_decisions.csv.
- 34 fuel-direction fixes: 21 variant fuel labels corrected (e.g. Golf/A3 '1.6 102hp Petrol' -> 1.6 TDI CAYC; Touareg '3.6 FSI 249hp' -> TDI CMTA), 13 engine rows had wrong fuel (Y30DT '3.0 V6 CDTI', SDBA TDDi stored as Petrol -> Diesel).
- 37 web-verified remaps (CAYC, CANB Audi 2.7 TDI, OM612.981/OM611 Sprinter CDI, R20A4, AZZ Touareg, K4M850, G4KD, Hybrid4 RHC, S300h OM651.921, i3 REX) + 250 rule-based internal remaps (0 power mismatches >25% after audit).
- Discovered real cross-brand engine-code collisions: G6DA/G6DG (Ford 2.0 TDCi diesel vs Hyundai Lambda petrol V6) and BAA (Ford Ka 1.3 vs VW Touareg 3.2) - affected rows left pending pending engine-row disambiguation.
- Queue now: 331 remapped, 13 engine_fuel_fixed, 3 fuel_label_fixed (+18 CAYC), 136 pending (93 fuel / 40 displacement / 3 power; 10 of them EVs needing an EV data model), 1 invalid. Backup: backups/car_database_backup_pre_step5_2026-09-29.db.

## 2026-09-29 — Step 4 batch 3: web research on fuel pendings + G6DA/G6DG disambiguation

- 55 more variants restored to correct engines (39,045 -> 39,099 with specs; NULL codes 137 -> 82; queue remapped 331 -> 386, pending 136 -> 81, all documented). Report: REMAPPING_REVIEW_BATCH3.md, decisions: csv_exports/14_remap_batch3_decisions.csv.
- G6DA/G6DG code collision resolved: created 'G6DA (Hyundai)' (3.8 MPi Lambda 3778cc) and 'G6DG (Hyundai)' (3.0 GDI Lambda II 2999cc) rows; 7 Hyundai/Kia Lambda variants remapped (Grandeur TG/HG, Genesis Coupe, Carnival VQ, Opirus, Cadenza x2). BAA needed no action (resolved in batch 2).
- Engine-row fixes: G6DH was mislabeled 3.0/247hp -> corrected to 3.3 GDI 3342cc/292hp (Wikipedia Lambda); N57D30B displacement 4004->2993cc; N57D30T was fuel='Petrol' with NULL cc -> Diesel 2993cc.
- Web-verified remaps: Alpina D3/D4/D5/XD3 350PS -> N57D30B (Alpina N57 biturbo); Alpina B10 V8S -> new M62B48 row; Rolls-Royce Park Ward -> new M73B54 row; Maserati MC12 -> F140B (Enzo F140); Land Rover 3.0 SC x3 -> AJ126; plus 24 internal remaps (incl. Subaru XV/Impreza 2.0D -> EE20Z early tune).
- New rows G6DA (Hyundai), G6DG (Hyundai), M62B48, M73B54 have empty service specs - flagged for OEM spec fill. Backup: backups/car_database_backup_pre_step6_2026-09-29.db.

## 2026-09-29 — Step 7: engine-row suspect worklist (452 rows / 200 codes)

- 19 engine rows repaired with citations: QR25DE 1600->2488cc (Nissan 2.5), CMXA 1200->1598cc (VW 1.6 MultiFuel - 17 Seat/VW variants were right, row was wrong), M57D30 2353->2993cc, B38B15M0 1005->1499cc, ETJ/ETH/ETC -> Cummins 6.7/5.9 identities, CCRA -> 1.6 TotalFlex 1598cc, E18NVR text 'ECONOVAN Bus' -> '3.0 V6 SIDI VVT' (Cadillac LF1-type data), L96 '1.3 VVTi' -> '6.0 V8 Vortec' (dieselhub), LC9/L76/L20/LM7 Vortec texts, CKMA '6.7 Turbo R' -> '1.4 TSI Twincharger', F1CE0481* -> '3.0 HPI TurboDiesel', 4HH -> '2.2 16v HDi'.
- E18NVR grab-bag cleanup: 14 junk attachments quarantined (VW Voyage, Alpina B3 x3, LANDWIND, HUMMER H3, Chevrolet Colorado/Suburban/Uplander/Avalanche) that survived filters via junk-etype displacement parses; v_vehicle_with_service 39,099 -> 39,085 (honest loss of wrong spec joins).
- Displacement-suspect joined rows 452 -> 405; remainder is cosmetic variant-etype junk (specs correct). Report: ENGINE_ROW_WORKLIST_REPORT.md, fix log: csv_exports/15_engine_row_fixes.csv. Backup: backups/car_database_backup_pre_step7_2026-09-29.db.

## 2026-09-29 — Step 8 (user's Step 3): hernr_* brand rebadging + mis-brand fixes

- All 83 hernr_NNN brand buckets (743 variants, from the Vivid WorkshopData source) rebadged to real manufacturers using model+engine evidence, each web-verified (citations in STEP3_BRAND_REBADGE_REPORT.md): Smart, Lamborghini, Bentley, Lotus, Infiniti, Tata, UAZ, Perodua, Chery, Geely, GWM, BYD, Foton, Brilliance, Chana, Soueast, Gonow, Dadi, Hafei, Jinbei, Lifan, Saipa, Besturn, Haima, Luxgen, Huanghai, Higer, Golden Dragon, Dongfeng Fengxing, Baolong, Naza, BAW, Inokom, Eunos (800=Xedos 9), Marcos, Metrocab (MCW 2L-T), Westfield (XTR4), Caterham, Zastava, Santana, Ligier, Aixam, Venturi, Wiesmann, Maybach, Spyker, Morgan, Rolls-Royce, AC, Renault Trucks, Piaggio, HSV, Artega, Shuanghuan, ZAZ + consolidations into Ford/VW/Toyota/Honda/Nissan/BMW/LDV/Renault Samsung/MG/Mahindra/Hummer/Acura/Dr Motor/KTM/McLaren/Bugatti/Pontiac/Daewoo.
- Mis-brands fixed: Citroën->Citroen (486 variants unified, 711 total), Saic Mg->MG, SATURN->Saturn, SHELBY->Shelby, Jmc->JMC, Volga->GAZ.
- 48 new real brand rows (188->236 brands); 18 duplicate model rows merged (6299->6281); 0 hernr remnants in variants/models/engines/queue.
- Bonus: Hummer H3 3.5 220hp remapped to L52 (NULL 96->95, specs 39,085->39,086); 5 brand-blocked queue pendings unblocked with citation notes (Marcos TS250/TS500, smart ed 41hp, GWM Tengyi C50, Landwind 2.4, Caterham Seven CF).
- Source mystery solved: hernr_N = Vivid Hersteller-Nummer; original vivid_cars2000.db in repo root has same-broken brand column but yields kmodnr IDs + identification of non-imported buckets (Noble/RUF/Tesla/IKCO/Fisker/GAZ/Bristol/Lincoln). Decisions: csv_exports/16_brand_rebadge_decisions.csv. Backup: backups/car_database_backup_pre_step8_2026-09-29.db.

## Step 9 — 2026-09-29 (user-plan Step 5, batch 1): LEMON synthetic-code replacement, US trucks/SUVs/vans

- Replaced 1,885 LEMON_* synthetic engine codes with real OEM codes (Ford 633, Chevrolet 531,
  GMC 457, Dodge 96, Ram 95, Cadillac 45, Lincoln 28) using displacement + 8th-VIN char + year +
  fuel, verified against 20 web references (see STEP5_BATCH1_REPORT.md).
- Migrated all crawled service/technical specs onto the real codes (v_vehicle_with_service
  coverage unchanged at 39,086); provenance sources preserved.
- Created 47 new engine rows (STEP9_VERIFIED); fixed junk engine_type on LFA/L18, L5P fuel, L8T specs.
- Corrected 279 variant fuel labels (Petrol→Diesel) where lemon mislabeled diesel-only engines.
- 97 in-scope rows deliberately skipped (ambiguous signal) — documented in report.
- 10,752 LEMON rows remain for later batches (cars/SUVs/crossovers).
- Script: step9_step5_lemon_replacement.py (dry-run default, --apply gate).
- Backup: backups/car_database_backup_pre_step9_2026-09-29.db
- Decisions log: csv_exports/17_lemon_replacement_decisions.csv

## Step 10 + 10b — 2026-09-30 (user-plan Step 5, batch 2): LEMON replacement, Mopar SUVs/LX cars/Jeep/Ram 1500

- Replaced 638 LEMON_* codes with real OEM codes (3.6 Pentastar 172, EZH 121, EVA 40, EKG 40, EXL 29,
  6.2 Hellcat 29, ESH 24, ESF 21 ...) using displacement + VIN char + year + fuel, verified against
  the Chrysler HEMI/PowerTech wiki tables, the 2015 lemon crawl (VIN G/T/M/B/S/N + Eng CD EZC/EZH/ESG/ESH),
  and Hurricane references (see STEP5_BATCH2_REPORT.md).
- Created 12 engine rows (Hellcat, 3.5 LX, 3.2 Pentastar, 2.0 GME (+4xe), 5.7 HEMI Hybrid, 4.0/2.5 AMC,
  R428, 3.0 CRD OM642, 3.0 Hurricane); fixed EDZ config (I4 not V6), EZC 340hp, EXL, ESH, EZH rows.
- 38 fuel-label fixes (EcoDiesel/CRD diesels + GC 4xe hybrid).
- 15 rows skipped on principle (Nitro 4.0, Cherokee VIN X, ambiguous bare rows) - documented.
- Step 10b: overrode 32 target engines' ESTIMATE-heuristic oil/coolant specs with the real crawled
  lemon data recovered from backups (also covers batch-1 targets); 0 ESTIMATE sources remain among
  step-9/10 targets.
- 10,114 LEMON rows remain (batches 3+: Explorer/Edge/Escape, imports).
- Backups: pre_step10, pre_step10b. Decisions: csv_exports/18_lemon_batch2_decisions.csv.

## Step 11 + 11b + 11c — 2026-09-30: small cleanups (user-approved list)

- Garbled codes retired: M54256S5→M54B25 (cc fixed 2494), G4KR/H4KR→G4EE (Kia Alpha 1.4 1399cc),
  25V6S1→KV6; C20LET row corrected from mis-coded Ford 1.4 TDCi data to Opel 2.0 16v Turbo 204hp,
  6 wrong attachments moved to real sibling codes (F6JD, K9K858, F1CE0481FA/HA).
- Resolved 6 remaining pending queue items with citations (Marcos TS250/TS500, smart ed 450,
  GWM C50 GW4G15T, Landwind 4G64S4M, Caterham CF C20LET) + Caterham CSR junk codes → new
  'Duratec 2.3 CSR' row. Queue: 88 pending / 393 remapped.
- 4 new STEP11_VERIFIED engine rows (5.0 Rover V8, smart ED (450) — first Electric engine,
  Duratec 2.3 CSR, M73B54). Orphan refs now 0 (Rolls-Royce Park Ward closed).
- OEM spec fills with citations: G6DA/G6DG Ford 2.0 TDCi 5W-30 5.5L WSS-M2C913-C/D, G6DA/G6DG
  (Hyundai) 6.0/6.9L, M62B48 7.5L, M73B54 5W-40 8.0L/15L coolant.
- Power Stroke fixes: 7.3 oil 12.87→14.2L, 6.0 oil 16.08→14.2L, 6.7 coolant cleared; sibling rows
  7.3 V8 Powerstroke/T444E/6.4 V8 Powerstroke 9.5→14.2L, 6.7 V8 Powerstroke 9.5→12.3L.
- Cosmetic etype cleanup: 4,308 junk-pattern + 906 displacement-spoof variant etypes (engine-table
  etype propagated only when itself clean & self-consistent, else NULL); 54 engine rows with
  car-model/body-style junk etypes relabeled from own cc/fuel columns.
- Step 11b: deleted 2 orphaned Caterham junk rows; recomputed all engines.count_variants from
  actual links (0 mismatches).
- Verification: garbled codes gone, 0 junk-pattern etypes, 0 orphan refs, 0 count mismatches.
- LEMON unchanged at 10,114 (batch 3 Ford Explorer/Edge/Escape next).
- Scripts: step11_small_cleanups.py, step11b_post_fix.py, step11c_psd_oil.py.
  Backup: pre_step11. Logs: csv_exports/19_small_cleanups_log.csv + 19_small_cleanups_decisions.csv.

## Step 12 + 12b — 2026-09-30 (user-plan Step 5, batch 3): LEMON replacement, ALL Ford

- Replaced 658 LEMON_FORD codes with real OEM codes across 41 models / model years 2000-2024
  (top: 2.0 EcoBoost 66, 3.5 Cyclone 62, 2.3 EcoBoost 45, 2.5 Duratec 42, 3.0 V6 37, 4.6 V8 32),
  using cc + VIN-8th char + year + fuel + trim slug, verified against Ford's own fleet VIN guide
  PDFs (fordpro 2013/2014/2022), fordmasterx, and listings carrying actual VINs (see
  STEP5_BATCH3_REPORT.md and the CIT dict in step12_step5_lemon_batch3.py).
- Key VIN findings: 8 = 3.5 NA (cars) but 3.5 EcoBoost turbo on 2021+ F-150; T = 3.5 GTDI;
  4 = 3.5 EB std (vs T HO); H/D = 2.3 EB; 9 = 2.0 EB; B/W = 3.3 NA/Hybrid; C = 3.0 EB 400hp;
  Explorer 2.3 EB is real from 2016 (replaced 2.0 EB).
- 21 new STEP12_VERIFIED engine rows incl. E-Transit Electric + Focus Electric (2nd/3rd Electric
  engines), GT500 5.4/5.8 SC, Voodoo 5.2, Ford GT 5.4 SC, Thunderbird AJ35, hybrid families.
- 15 fuel fixes (PIU W hybrid, Maverick hybrid, C-Max Energi, E-Transit, Focus Electric).
- Step 12b: overrode 4 pre-existing ESTIMATE-heuristic oil specs on shared targets with lemon
  majority values (2.0 EB 5W-30 5.39L, 3.0 V6 5W-20 5.67L, 4.0 SOHC 5W-30 4.73L, 4.6 V8 5W-20 5.67L).
- 85 rows deliberately skipped (ambiguous: bare vans/trucks, Taurus/Focus engine splits, SSV) -
  documented with reasons.
- Verification: 0 orphan refs, 0 count_variants mismatches (recomputed), LEMON total 9,456 remain.
- Backups: pre_step12. Decisions: csv_exports/20_lemon_batch3_decisions.csv.

## Step 13 + 13b + 13c — 2026-09-30 (user-plan Step 5, batch 4): LEMON replacement, ALL Mercedes

- Batch 4 of 5 in LEMON-count order: replaced 931 LEMON_MERCEDES codes (968 inventoried, 37 skipped)
  with real OEM codes. Unlike Ford/Mopar batches, LEMON Mercedes codes are US TRIM names (C300,
  E350, C63...) with no cc/VIN signal -> rules keyed on (trim base, year range), ~150 rules,
  verified via 7 research passes (C/E/S/CLK/CLS/CL/SLK/SL/ML/GL/G/GLE/GLS/CLA/GLA/GLB/Sprinter/
  Metris/G/AMG GT/EQB/EQS); Wikibooks Mercedes VIN table primary, ~30 sources in CIT dict.
- Key generation facts: C63 M156->M177(2015)->M139 PHEV 671hp (W206); E350 M272->M276(2012)->
  M264(2018); E450 2019+ M256 I6; S600 M137->M275->M277; A/CLA/GLA/GLB 250 M270->M260(2019);
  G550 M273->M176(2017)->M256(2025); Sprinter OM642/OM651/OM654(2023+); Metris = M274.920 van
  tune 208hp; GL450 X166 2013-14 M278 vs 2015+ M276 (mbworld).
- 23 new STEP13_VERIFIED engines (M256/M256 53, M254, M264, M260/35, M139 43/45/PHEV, M176, M178,
  M152, M137, M155 SLR, M113.943, M276 PHEV, M274 PHEV, OM654, EQB250+/300/350, EQS450+,
  W242 B250e Electric) + fuel fixes 76 (Diesel 52, Hybrid 12, Electric 12).
- Step 13b: overrode 59 ESTIMATE-heuristic oil specs on targets with lemon-crawl majority values
  from the pre_step13 backup (verified as genuine qt->L conversions vs MB specs).
- Step 13c (post-apply conflation audit): (a) Metris split into 'M274.920 (Metris)' 208hp
  0W-30/7.57L - AMSOIL/Wikiwand confirm code 274.920 but 8qt van sump vs ~6.3qt cars;
  (b) S450 2018-20 rule error fixed: W222 S450 = M276.824 V6 362hp (AMSOIL engine code,
  CarBuzz), NOT M256 I6 (W223-only) - 3 variants remapped; (c) S560e set 469hp system
  (Car and Driver) Hybrid, M276.824 spec 0W-30/6.52L per AMSOIL (last ESTIMATE eliminated);
  (d) 14 targets normalized to variant-weighted lemon majorities; 24 NULL/stale spec power_hp
  filled from engines (incl. M274.920 stale Euro 211->241).
- 37 rows deliberately skipped (bare Sprinter 2500 gas/diesel x18, Maybach x3, W202/W204
  transition years, 12 single-row ambiguities) - documented with reasons.
- Verification: 0 ESTIMATE among step-13 targets, 0 orphan refs, 0 count_variants mismatches,
  0 engines<->specs power mismatches. LEMON total 8,525 (BMW 780 next: Chevrolet 653, Audi 576,
  Nissan 520, Toyota 471, Kia 392, Hyundai 391...).
- Scripts: step13_step5_lemon_batch4_mercedes.py, step13b_estimate_override.py,
  step13c_conflation_fixes.py. Backups: pre_step13, pre_step13c.
  Decisions: csv_exports/21_lemon_batch4_decisions.csv (updated in place by 13c).

## Step 14 + 14b — 2026-09-30 (user-plan Step 5, batch 5): LEMON replacement, ALL BMW

- Batch 5 of 5 in LEMON-count order: replaced 697 LEMON_BMW codes (780 inventoried, 83 skipped)
  with real OEM codes across 91 models / years 2000-2025. Rules keyed on (model, year, cc) -
  unlike Mercedes, BMW X3/X4/X5/X6/X7/Z4 codes carry a cc segment separating 28i/30i vs 35i/M40i
  vs 50i trims; car trims have one engine per generation. ~45 cited sources in CIT dict.
- Key facts verified: F01 740i/Li = N54 315hp (2011-12) -> N55 (2013 FL); 750i G11 LCI 2019+ =
  523hp; G70 760i 2023+ = S68 536hp; US 540d = B57 261hp; Alpina B7 500(SC)->540->600->612hp;
  M2 = N55 365 / S55 Comp 405 / S58 453; X5/X7 V8 = 445/456hp -> 523hp from 2020 (M50i);
  X1 2023 US single-trim 241hp; E90 323i (CA) = N52B25; anomalous 2011 528i identified as late
  E60/N52 via sump fingerprint (6.52L matches 2010, not F10's 5.01L).
- 24 new STEP14_VERIFIED engines: S58 (M3/M4 + M2), S55 (M2 Comp), N55 (M2 + M235i), B48 M235i GC,
  S63B44T2 (F90 M5/M8), N63B44TU2 523hp, S68, B58 (40i + M40i), B48B20 (30i), N20 US, 4x PHEV
  rows, B57 540d, N47 328d, i3 Electric (9th Electric engine), 4 Alpina rows.
- 15 row-fixes on reused rows (junk displacements: N55B30A 3926->2979, N54B30O0 2265->2979,
  M52TUB28 2470->2793, M62B44TU/N62B44 ->4398; i8 B3815KT0 -> Hybrid 357hp; V12 etype cleanups).
- 50 fuel fixes (Hybrid 28, Diesel 13, Electric 9 incl. i3/i8, X5 40e, 30e PHEVs, 328d).
- Step 14b: overrode 29 ESTIMATE oil specs + normalized 12 first-code merges to variant-weighted
  lemon majorities (M-cars correctly landed on 10W-60: S54 5.48L, S65 8.8L, S85 9.27L; M73B54
  corrected 8.0qt-as-litres -> 7.57L); synced 30 stale/NULL spec power_hp; filled 15 pre-existing
  NULL-power variants; i3 spec annotated as range-extender oil (BEV has none).
- 83 rows deliberately skipped (no-signal X/Z rows x59, bare M/X2/ActiveHybrid/Z3/X1-2024+ x22,
  non-existent 535i/550i 2017 x2) - documented with reasons.
- Verification: 0 ESTIMATE among step-14 targets, 0 orphan refs, 0 count_variants mismatches,
  0 power mismatches. Engines 13,235; LEMON total 7,828 (Chevrolet 653 next: Audi 576, Nissan 520,
  Toyota 471, Kia 392, Hyundai 391...).
- Scripts: step14_step5_lemon_batch5_bmw.py, step14b_estimate_override.py.
  Backup: pre_step14. Decisions: csv_exports/22_lemon_batch5_decisions.csv.

## Step 15 + 15b — 2026-09-30 (user-plan Step 5, batch 6): LEMON replacement, ALL Chevrolet

- Batch 6 in LEMON-count order: replaced 600 LEMON_CHEVROLET codes (653 inventoried, 53 skipped) with
  real OEM codes across 49 models / years 2000-2025, using the Ford-batch method (cc + VIN 8th char +
  year). DB's 150+ GM RPO codes served as target vocabulary.
- Key decodes: Camaro VIN J=L99/W=LS3/V=LLT/3=LFX/P=LSA; truck Vortec VINs (X 4.3, V 4.8, T LM7,
  U LQ4, G 8.1, F 6.5TD); 2018 Equinox LYX/LTG/LH7; 2016 Malibu 1.5T=LFV; Cruze 2.0TD=LUZ;
  TB EXT 5.3=LM4; Trailblazer 1.2T LIH / 1.3T L3T; 2013 Traverse still LLT; generic 'Chevy' rows
  (63) mapped by (cc, year) to Vortec families.
- 23 new engine rows: LSJ, LD9, LFV, LYX, LH7, LUZ, LZ9, LT2 (C8), LT6 (Z06), LM4, LG8, L77,
  6.5 TD V8, MR20DD (City Express), Voltec 1.4/1.5 EREV (Volt), Bolt EV + Spark EV Electric
  (11 Electric engines now), 1.8 Hybrid (Malibu), 1.4 Spark US, LUH/LIH/L3T.
- Row-fixes: 1ZZ-FE 1600->1794cc (Prizm - long-standing error), LS4 303hp, LZ4/LZE/LNJ/L82/LL8/LS1/
  J20A labels. 31 fuel fixes (Hybrid 13, Diesel 10, Electric 8).
- Step 15b: 18 ESTIMATE overrides + 11 majority normalizations + 32 power syncs; NULL-power engine
  rows filled (LGX 310/LT1 455/LCV 196/LEA 182/LN2 120) propagated to 128 variants. Flags: LS7 9.93L
  (crawl year-split 2006-08 vs 2009+), LT1 9.27L single-source, Spark 1.4 RPO unverified (row descriptive).
- 53 rows deliberately skipped (bare multi-engine rows, Canadian Daewoo Optra/Epica, RV chassis,
  Corvette Z06 ambiguity 2001-04, transition years).
- Verification: 0 ESTIMATE among targets, 0 orphan refs, 0 count mismatches, 0 power mismatches.
  Engines 12,658; LEMON total 7,228 (Audi 576 next: Nissan 520, Toyota 471, Kia 392, Hyundai 391...).
- Scripts: step15_step5_lemon_batch6_chevrolet.py, step15b_estimate_override.py.
  Backup: pre_step15. Decisions: csv_exports/23_lemon_batch6_decisions.csv.
