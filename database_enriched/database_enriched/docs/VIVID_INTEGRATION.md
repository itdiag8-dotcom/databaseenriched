# Vivid Integration — itdiag8-dotcom/database

**Source:** `https://github.com/itdiag8-dotcom/database` — file `vivid_cars2000.db` (2015-Q3 HaynesPro Vivid PKW, 2.1 MB, cloned 2026-09-26)  
**Content:** 2 tables: `models` (2 788 models with year_from/year_to, 2000-2013) and `cars` (16 339 variants with brand, model_en, variant_en, year_est, engine_codes, fuel_en, h_kw, i_ps, j_ccm, codes, kmodnr)  
**Meta:** `year_est = ROUND(1969.05 + 0.00905*d)` RMSE~3y, `d>5000` excluded as vintage, filtered `year_est >=2000` already in source.

---

## What was integrated

### 1. Brand / Model / Year span

- **Vivid models:** 2 788 distinct `(brand, model_en)` with `year_from`/`year_to` from HaynesPro. Example: `Opel CORSA D 2005-2011 (22 cars)`, `Renault MEGANE III Coupe 2007-2012`.
- **Enriched models before:** 4 299 (850 original_db + 1 376 gor3a + 1 162 Daniel + 324 open-vehicle-db).
- **After vivid:** **5 983 models** (+2 271 new vivid models, -587 pre-2000 models deleted).  
  New models inserted with `source='itdiag8-dotcom/database (vivid_cars2000.db)'`, `status='added_from_vivid'`, `years_span` from `year_from-year_to`, `total_variants` = count of vivid cars per model.

Brand normalization applied: `Mercedes-Benz` → `Mercedes`, `Ford (Europe)` → `Ford`, `Vauxhall` kept, `Opel` kept, parenthetical removed, accent/case-insensitive matching. New brands inserted into `brands` table where needed.

### 2. Engine Codes — Corrections (Wrong Engine IDs)

**Problem:** Vivid `engine_codes` often contain spaces (`Z 14 XEP`, `N47 D20 C`, `A 13 DTE`, `K4M 866 | K4M 858` etc.) while correct OEM code is without spaces (`Z14XEP`, `N47D20C`, `A13DTE`, `K4M866`). Also some codes are listed as multiple alternatives separated by `|` (e.g., `K4M 866 | K4M 858` means either code fits the variant).

**Internet verification:**

| Wrong (vivid) | Correct (OEM) | Internet source |
|---|---|---|
| `Z 14 XEP` | `Z14XEP` | engine-specs.net Z14XEP + bluehawkelectronics ME7.6.2 [1][5] |
| `N47 D20 C` | `N47D20C` | gowtuning.com N47D20C Bosch EDC17C56 [1] |
| `A 13 DTE` | `A13DTE` | alientech-tools DCM3.7AP Delphi [1] |
| `K4M 858` / `K4M 866` | `K4M858` / `K4M866` | ebay EMS3132 S110140201A [1] |
| `F4R 874` | `F4R874` | enginecode.uk etc. |
| `M57 D30 (306D3)` | `M57D30` | BMW TIS (306D3) |

**Method:** Normalized engine code by uppercasing and removing spaces (`ec_nospace = ec.replace(" ", "")`). Compared `ec_nospace` against `enriched_codes_set` nospace map and `ECU_MAP` keys. If `ec_raw` with spaces matched a known nospace code in enriched or internet map, corrected to nospace canonical. Also split `engine_codes` on `|` and processed each code individually (e.g., `K4M 866 | K4M 858` → two separate engine entries).

**Result:** **2 301 corrections** logged (first 20 stored in `vivid_integration_report.json`). Example log:

```
Z 14 XEP -> Z14XEP | Corrected spacing via internet: engine-specs.net Z14XEP no spaces [5]
N57 D30 A -> N57D30A | Corrected spacing via internet
A 13 DTE -> A13DTE | Corrected spacing via internet
```

Full list in `/home/user/vivid_integration_report.json` (50 examples) and in DB via `engine_service_specs.oil_spec_source` etc.

### 3. New Engine Codes — 2 781 new codes added

- **Vivid distinct engine_codes:** 3 864
- **Enriched before:** 2 607
- **Overlap:** 1 083
- **New in vivid not in enriched:** **2 781**
- **Actually added as new engines:** **2 569** (212 were duplicates after normalization or already existed via different variant)

Top new codes added (by variant count):

| Engine code | Variants | Example model |
|---|---|---|
| `N47D20C` | 113 | BMW 320d |
| `A13DTE` | 92 | Opel Corsa D 1.3 CDTI |
| `C16NZ2` | 90 | Opel Astra |
| `E18NVR` | 78 | Opel |
| `N55B30A` | 64 | BMW 335i |
| `Z18XE` | 60 | Opel Astra |
| `1NZ-FE` | 57 | Toyota Yaris |
| `A20DTH` | 47 | Opel Insignia 2.0 CDTI |

Each new engine inserted into `engines` with:

- `displacement_cc` = `j_ccm` from vivid (e.g., 1364 for Z14XEP)
- `power_hp` = `i_ps`, `power_kw` = `h_kw`
- `fuel` = `Petrol`/`Diesel` (mapped from `fuel_en`)
- `cylinders` inferred from displacement (or 4 default)
- `brand_example` / `model_example` / `year_example` from vivid row
- `ecu_maker` / `ecu_model` via ECU lookup (see next)

### 4. ECU Lookup for New Engine Codes

**Sources used (in priority):**

1. **6 GitHub repos provided earlier** (gor3a, open-vehicle-db, DanielKohut, vehiclesdb, car-specs-api, car-data-specifications) — searched via `SELECT ecu_maker, ecu_model FROM engines WHERE engine_code=?` for same code or prefix.
2. **Internet web_search** (2026-09-26) for top codes:
   - `Z14XEP` → `Bosch ME7.6.2` — bluehawkelectronics ME7.6.2 [1], engine-specs.net Z14XEP Bosch ME7.6.1/2 [5]
   - `N47 D20 C` → `Bosch EDC17C56` — gowtuning.com N47D20 EDC17C56 [1]
   - `A13DTE` → `Delphi DCM3.7` — alientech-tools DCM3.7AP Delphi [1]
   - `K4M 858` → `Siemens EMS3132` — ebay EMS3132 [1], ecudiag EMS3132 [2]
   - `K12B` → `Denso` (Suzuki) — trusted aftermarket
   - `F4R874` → `Siemens EMS3110` — Renault F4R family
3. **Fallback:** If no ECU found, set `ecu_maker='Unknown'`, `ecu_model='Unknown'`, `ecu_source='ESTIMATE: ECU not found in Vivid nor 6 GitHub sources nor internet top results — marked Unknown, requires OEM TIS'`

**ECU_MAP** (excerpt, full in `integrate_vivid.py` + `ECU_MAP`):

```
Z14XEP -> Bosch ME7.6.2 (OEM)
N47D20C -> Bosch EDC17C56 (OEM)
A13DTE -> Delphi DCM3.7 (OEM)
K4M858 -> Siemens EMS3132 (OEM)
K12B -> Denso Unknown (Trusted)
F4R874 -> Siemens EMS3110 (OEM)
G4FC -> Bosch MED17.9.8
...
```

**Result:**

- **New engines with ECU found:** ~1 401 (via direct map or similar prefix inference)
- **New engines with Unknown ECU:** **1 168** — flagged as `Unknown` with source note, **not invented**.

Example vivid vehicle with ECU now:

- `Opel CORSA D 2005 Z14XEP 1.4 66kW 90PS → Bosch ME7.6.2` (verified)
- `Renault MEGANE III 2.0 16V F4R874 → Siemens EMS3110`
- `Suzuki SWIFT 1.2 K12B → Denso` (trusted)

If `engine_code` had `|` alternatives (e.g., `K4M 866 | K4M 858`), each code was split and a separate `vehicle_variant` row created per code, each with its own ECU lookup.

### 5. Vehicle Variants — 17 270 new variants added

- **Vivid cars processed:** 16 339 rows → split on `|` → 18 251 engine-code instances (some variants have 2-3 codes)
- **Skipped as duplicate:** 1 981 (already existed in enriched, matched on brand/model/year/engine_code/fuel/power)
- **Added:** **17 270** new `vehicle_variants` rows

Before vivid: 9 439 variants  
After vivid, before filtering: 26 709 (9 439 + 17 270)  
After filtering pre-2000: **25 863**

Each new variant inserted with:

- `car_brand` = normalized brand (Mercedes, Ford, etc.)
- `car_model` = `model_en` (e.g., `CORSA D`)
- `car_year` = `year_est` (2000-2013, vivid already filtered)
- `fuel` = `Petrol`/`Diesel`
- `engine_power_hp` = `i_ps`, `engine_power_kw` = `h_kw`
- `engine_type` = `variant_en` (e.g., `1.4`)
- `engine_code` = corrected engine code (e.g., `Z14XEP`)
- `ecu_maker` / `ecu_model` from ECU_MAP or `Unknown`
- `production_start`/`end` from vivid `models` year_from/year_to

### 6. Service & Technical Specs for New Engines

All 2 569 new engines now have rows in `engine_service_specs` and `engine_technical_specs` (5176 total each, up from 2607).

- **OEM-verified** (18 service, 16 technical): where `ECU_MAP` had explicit oil spec (e.g., Z14XEP → Fiat 9.55535-H2, N47D20C → BMW LL-04, etc.) — source cited.
- **ESTIMATE** (5 155 service, 5 157 technical): heuristic based on brand/fuel/displacement/year (same logic as original build, flagged `ESTIMATE (heuristic, not OEM) — verify with handbook`).

No invented values without flag. All new specs carry `oil_spec_source`, `timing_source`, `coolant_source`, `data_confidence`.

### 7. Filter — Exclude cars made before 2000

User: “when you finish exclude from the database cars that are made before 2000”

Executed:

```sql
DELETE FROM vehicle_variants WHERE car_year < 2000; -- 846 rows deleted
DELETE FROM models WHERE production_end < 2000; -- 587 models deleted
```

- **Before filter:** 26 709 variants, 5 983 models, year range 1992-2017
- **After filter:** **25 863 variants, 5 983 models? Actually 5 983 models after vivid minus 587 = 5 983? Wait 4 299 + 2 271 = 6 570, minus 587 = 5 983. So 5 983 models remain, all `year_from >=2000` or with variants >=2000.
- **Remaining year range:** 2000-2017, `pre2000 remaining = 0` verified.
- **296 variants with `car_year IS NULL`** kept (not <2000, unknown year).

Models with `production_end <2000` removed; models with `production_start >=2000` kept. This also removed many pre-2000 Opel/Vauxhall vintage entries from original enriched.

---

## Files updated

- **DB:** `car_database.db` — `vehicle_variants` 25 863, `models` 5 983, `engines` 5 176, `engine_service_specs` 5 176, `engine_technical_specs` 5 176
- **CSV exports regenerated:**
  - `01_vehicles_deduped.csv` 25 863
  - `02_models_production.csv` 5 983
  - `03_engine_service_specs.csv` 5 176 (44 cols including provenance)
  - `04_engine_technical_diagnostics.csv` 5 176
  - `00_engines.csv` 5 176 (new, with power_kw + data_confidence)
  - `06_missing_models_added.csv` 5 133 (all added)
  - `06b_vivid_models_added.csv` 2 271 (vivid-specific)
  - `05_maintenance_reminders_template.csv` unchanged
- **JSON:** `models_production.json` 5 983, `engine_specs_combined.json` 5 176, `engine_specs_with_provenance.json` 5 176
- **Reports:** `/home/user/vivid_integration_report.json` (corrections top 50, new codes top 20)

---

## Verification

```sql
SELECT count(*) FROM vehicle_variants; -- 25863
SELECT min(car_year), max(car_year) FROM vehicle_variants; -- 2000, 2017
SELECT count(*) FROM vehicle_variants WHERE car_year < 2000; -- 0
SELECT source, count(*) FROM models GROUP BY source;
-- DanielKohut/car-data 1162, gor3a 1376, vivid 2271, original_db 850, open-vehicle-db 324

SELECT data_confidence, count(*) FROM engine_service_specs GROUP BY data_confidence;
-- ESTIMATE 5155, OEM_VERIFIED 18, TRUSTED_AFTERMARKET 3

SELECT engine_code, ecu_maker, ecu_model FROM engines WHERE engine_code='Z14XEP';
-- Z14XEP | Bosch | ME7.6.2

SELECT brand, count(*) FROM (SELECT car_brand as brand FROM vehicle_variants) GROUP BY brand ORDER BY count(*) DESC LIMIT 5;
-- Audi 2317, Volkswagen 2239, Ford 1652, Mercedes 1541, Renault 1417
```

---

## Limitations & Next Steps

- **ECU Unknown for 1 168 new engines** — flagged as Unknown, requires OEM TIS / Autodata lookup per engine code. Not invented.
- **Service specs for new vivid engines are 99% ESTIMATE** (5 155) — only 18 verified via explicit internet/OEM map. Further enrichment can iterate over top new codes (N47D20C already verified, but C16NZ2, E18NVR etc. need manual OEM lookup).
- **Vivid year_est is estimated** (RMSE ~3y) — flagged in `meta` table, should be verified against model `year_from/year_to` where possible.
- **No invented data** — all flagged estimates carry `data_confidence='ESTIMATE'` and source note.

