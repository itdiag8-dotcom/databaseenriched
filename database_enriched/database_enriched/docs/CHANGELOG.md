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
