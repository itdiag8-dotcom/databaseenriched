# Database Schema — car_database.db

**DB:** `car_database.db` (SQLite 3, `PRAGMA foreign_keys=OFF` at build, 95 brands, 6 tables + 3 views)  
**Car year nullable:** `vehicle_variants.car_year INTEGER NULL` so empty production rows don’t violate constraints.  
**Engine code PK:** every distinct `engine_id` (2 607) enriches exactly one service row + one diagnostic row.

---

## ER Overview

```
brands 1──∞ models
                ↑
                | (brand_name, model_name)
vehicle_variants ──→ engines 1──1 engine_service_specs
                    engines 1──1 engine_technical_specs
vehicle_variants.engine_code → engines.engine_code
models.brand_id → brands.id
```

---

## Table: `brands`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `name` | TEXT UNIQUE | Canonical display, accent/case-normalized. e.g. `BMW`, `Volkswagen`, `Citroen`, `Mercedes` (not `Bmw`, `Citroën`, `Mercedes-Benz`) |

95 rows. Canonical list derived from 144 raw variants, deduped via `NFKD` accent stripping + lowercasing + synonym map.

```sql
SELECT name FROM brands ORDER BY name;
```

---

## Table: `models`

One row per distinct `(brand,model)` — covers *all* models, existing + added.

| Column | Type | Constraint | Example |
|---|---|---|---|
| `id` | INTEGER PK | | 1 |
| `brand_id` | INTEGER NOT NULL | FK → brands.id | 42 |
| `brand_name` | TEXT NOT NULL | denormalized, UNIQUE(brand_name, model_name) | `Fiat` |
| `model_name` | TEXT NOT NULL | | `500` |
| `production_start` | INTEGER | nullable (NULL if source had no years, e.g. Daniel 1 162) | 2007 |
| `production_end` | INTEGER | nullable | 2024 |
| `years_span` | TEXT | e.g. `"2008-2016"` or `"2015"` | `2007-2024` |
| `total_variants` | INTEGER | count of deduped variants for this model (0 for added missing) | 19 |
| `source` | TEXT | `original_db` / `gor3a/vehicle-makes-models` / `plowman/open-vehicle-db` / `DanielKohut/car-data` | `original_db` |
| `status` | TEXT | `existing` / `added_missing` | `existing` |

Indexes: `idx_models_brand(brand_name)`  
Counts: 4 299 total = 864 existing + 3 435 added; 3 137 with years, 1 162 NULL.

**Query production range:**
```sql
SELECT production_start, production_end, years_span FROM models
WHERE brand_name='Alfa Romeo' AND model_name='Giulia';
-- Returns: 2015, 2026, "2015-2026"
```

---

## Table: `engines`

One row per distinct engine code (from original `engine_id`; fallback `engine_type_fuel_power` if empty).

| Column | Type | Example |
|---|---|---|
| `engine_code` | TEXT PK | `312 A1.000` |
| `engine_type` | TEXT | `1.4 16v T-Jet` |
| `fuel` | TEXT | `Petrol` / `Diesel` |
| `displacement_cc` | INTEGER | 1400 |
| `power_hp` | INTEGER | 120 |
| `cylinders` | INTEGER | 4 |
| `ecu_maker` | TEXT | `Bosch` |
| `ecu_model` | TEXT | `ME7.9.10` |
| `brand_example` | TEXT | `Fiat` (first variant seen for this engine) |
| `model_example` | TEXT | `Grande Punto` |
| `year_example` | INTEGER | 2008 |
| `count_variants` | INTEGER | how many vehicle rows share this engine (1–… ) |

2 607 rows. `displacement_cc` parsed from engine_type (`1.4 16v` → 1400) or estimated from power if missing. `cylinders` from keyword (`V6`/`V8`/`L4`) or displacement heuristic.

---

## Table: `vehicle_variants`

Deduped vehicle rows (from original CSV) with production columns joined.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `car_brand` | TEXT NOT NULL | canonical brand (matches brands.name) |
| `car_model` | TEXT NOT NULL | |
| `car_year` | INTEGER | nullable — empty strings in source become NULL |
| `fuel` | TEXT | |
| `engine_power_hp` | INTEGER | |
| `engine_type` | TEXT | e.g. `1.9 JTD 16v` |
| `engine_code` | TEXT | FK → engines.engine_code |
| `ecu_maker` | TEXT | |
| `ecu_model` | TEXT | |
| `production_start` | INTEGER | nullable — from models production map |
| `production_end` | INTEGER | nullable |

Indexes: `idx_vehicle_brand_model(car_brand, car_model)`, `idx_vehicle_engine(engine_code)`  
Count: 9 439 (9 746 − 307 duplicates). Dedup key described in README.

```sql
-- All variants for a model with service intervals
SELECT v.car_year, v.engine_code, v.engine_type, s.oil_viscosity, s.timing_type
FROM vehicle_variants v
JOIN engine_service_specs s ON s.engine_code=v.engine_code
WHERE v.car_brand='Volkswagen' AND v.car_model='Golf' ORDER BY v.car_year;
```

---

## Table: `engine_service_specs`

**PK `engine_code` — one row per engine (2 607). All fields nullable except PK but populated for every engine.**

| Column | Type | Unit / Example |
|---|---|---|
| `engine_code` | TEXT PK | `312 A1.000` |
| `engine_type` | TEXT | `1.4 16v T-Jet` |
| `fuel` | TEXT | `Petrol` |
| `displacement_cc` | INTEGER | cc |
| `power_hp` | INTEGER | hp |
| `cylinders` | INTEGER | |
| `brand_example` | TEXT | `Fiat` |
| `model_example` | TEXT | `Grande Punto` |
| `year_example` | INTEGER | |
| `oil_viscosity` | TEXT | `5W-30` / `0W-20` |
| `oil_standard` | TEXT | `VW 507 00 (LongLife) - ACEA C3` |
| `oil_acea` | TEXT | `C3` / `A3/B4` / `C5` |
| `oil_oem_spec` | TEXT | `VW 507 00` |
| `oil_capacity_with_filter_l` | REAL | litres, 2.8–9.5 |
| `oil_capacity_without_filter_l` | REAL | |
| `oil_change_interval_km` | INTEGER | 10 000–20 000 |
| `oil_change_interval_months` | INTEGER | 12 |
| `coolant_type` | TEXT | `G12evo Pink Si-OAT`, `Toyota SLLC Pink OAT` |
| `coolant_spec` | TEXT | `Si-OAT` / `OAT` / `HOAT` |
| `coolant_capacity_l` | REAL | litres, 4–15 |
| `coolant_change_interval_km` | INTEGER | 60 000–120 000 |
| `coolant_change_interval_months` | INTEGER | 36–60 |
| `timing_type` | TEXT | `Belt` / `Chain` / `Belt (wet belt)` |
| `timing_belt_interval_km` | INTEGER | nullable (NULL if Chain) |
| `timing_belt_interval_months` | INTEGER | |
| `timing_chain_inspection_km` | INTEGER | nullable (NULL if Belt); 150 000–200 000 |
| `air_filter_interval_km` | INTEGER | 60 000 |
| `air_filter_interval_months` | INTEGER | 48 |
| `fuel_filter_interval_km` | INTEGER | 60 000 / 80 000 |
| `fuel_filter_interval_months` | INTEGER | 48 |
| `brake_fluid_type` | TEXT | `DOT 4 LV` / `DOT 4` |
| `brake_fluid_change_months` | INTEGER | 24 |
| `spark_plug_type` | TEXT | `Iridium / Platinum - NGK / Bosch` / `N/A (Glow Plug)` |
| `spark_plug_gap_mm` | TEXT | `0.7-0.8 mm` / `0.9-1.1 mm` / `-` |
| `spark_plug_interval_km` | INTEGER | nullable (NULL for diesel) |
| `spark_plug_interval_months` | INTEGER | |
| `aux_belt_interval_km` | INTEGER | 80 000 / 100 000 |
| `aux_belt_interval_months` | INTEGER | 60 |
| `count_variants` | INTEGER | denormalized |

*Heuristic mapping detailed in README §2; seed 42 for reproducible randomness.*

---

## Table: `engine_technical_specs`

**PK `engine_code` — diagnostic reference (2 607).**

| Column | Type | Example / Unit |
|---|---|---|
| `engine_code` | TEXT PK | same as above |
| `engine_type` | TEXT | |
| `fuel` | TEXT | |
| `displacement_cc` | INTEGER | |
| `cylinders` | INTEGER | |
| `bore_mm` | REAL | mm, 71–96 |
| `stroke_mm` | REAL | derived from volume |
| `compression_ratio` | TEXT | `10.4:1` |
| `compression_pressure_min_bar` | REAL | bar, petrol 10.5–12.5 / diesel 24–28 |
| `compression_pressure_max_bar` | REAL | min + 1.5–6 |
| `compression_pressure_diff_max_bar` | REAL | max cycl. diff, 1–4 |
| `fuel_system_type` | TEXT | `Common Rail`, `Direct Injection (GDI)`, `Multi-Point Injection (MPI)` |
| `fuel_pressure_low_bar` | REAL | lift pump, 3–6.5 |
| `fuel_pressure_high_bar` | REAL | MPI = same as low, GDI 50–350, Diesel 1 350–2 000 |
| `fuel_octane_requirement` | TEXT | `95 RON` / `98 RON recommended for Turbo` / `Diesel EN590` |
| `oil_pressure_idle_bar` | REAL | 1.0–2.0 |
| `oil_pressure_2000rpm_bar` | REAL | 3.0–5.5 |
| `idle_rpm` | INTEGER | 650–820 |
| `valve_clearance_intake` | TEXT | `0.10-0.20 mm (hydraulic auto)` |
| `valve_clearance_exhaust` | TEXT | |
| `ignition_timing` | TEXT | `ECU controlled (knock regulated)` or `6–12° BTDC @ idle` |
| `spark_plug_type` | TEXT | |
| `spark_plug_gap_mm` | TEXT | |
| `spark_plug_interval_km` | INTEGER | |
| `torque_nm` | INTEGER | Nm |
| `torque_rpm` | INTEGER | |
| `power_hp` | INTEGER | |
| `power_rpm` | INTEGER | 3 500–6 000 |
| `co_idle_percent` | TEXT | `0.2–0.5` or `-` (diesel) |
| `hc_idle_ppm` | TEXT | `80–200` or `-` |
| `lambda` | TEXT | `0.97-1.03` or `Lean - Excess air` |
| `has_dpf` | TEXT | `Yes`/`No`/`-` |
| `has_egr` | TEXT | |
| `has_adblue_scr` | TEXT | |
| `ecu_maker` | TEXT | |
| `ecu_model` | TEXT | |
| `brand_example` | TEXT | |
| `model_example` | TEXT | |
| `year_example` | INTEGER | |

Index: `idx_engines_fuel(fuel)`

---

## Views

### `v_engine_full`
```sql
CREATE VIEW v_engine_full AS
SELECT e.engine_code, e.engine_type, e.fuel, e.displacement_cc, e.power_hp, e.cylinders,
       s.oil_viscosity, s.oil_standard, s.oil_oem_spec, s.oil_capacity_with_filter_l, ...
       s.timing_type, s.timing_belt_interval_km, ...
       t.compression_ratio, t.compression_pressure_min_bar, t.compression_pressure_max_bar,
       t.fuel_system_type, t.fuel_pressure_low_bar, t.fuel_pressure_high_bar,
       t.oil_pressure_idle_bar, t.oil_pressure_2000rpm_bar, t.idle_rpm, t.torque_nm, t.torque_rpm
FROM engines e
JOIN engine_service_specs s ON s.engine_code=e.engine_code
JOIN engine_technical_specs t ON t.engine_code=e.engine_code;
```
One row per engine, combined service+diagnostic.

### `v_model_overview`
```sql
SELECT m.brand_name, m.model_name, m.production_start, m.production_end, m.years_span,
       m.total_variants, m.source, m.status,
       COUNT(v.id) as vehicle_variants_count
FROM models m LEFT JOIN vehicle_variants v ON v.car_brand=m.brand_name AND v.car_model=m.model_name
GROUP BY m.id;
```
Model list with live variant count.

### `v_vehicle_with_service`
```sql
SELECT v.id as vehicle_id, v.car_brand, v.car_model, v.car_year, v.fuel, v.engine_power_hp,
       v.engine_type, v.engine_code, v.production_start, v.production_end,
       s.oil_viscosity, s.oil_oem_spec, s.oil_capacity_with_filter_l,
       s.timing_type, s.timing_belt_interval_km,
       t.compression_pressure_min_bar, t.compression_pressure_max_bar, t.fuel_pressure_high_bar, t.oil_pressure_idle_bar
FROM vehicle_variants v
JOIN engine_service_specs s ON s.engine_code=v.engine_code
JOIN engine_technical_specs t ON t.engine_code=v.engine_code;
```
Ready for “select vehicle → show service card”.

---

## CSV exports mapping

All CSVs are UTF-8, comma-separated, header row, LF line endings.

| CSV | Corresponding table/view | Rows |
|---|---|---|
| `01_vehicles_deduped.csv` | `vehicle_variants` | 9 439 + header |
| `02_models_production.csv` | `models` | 4 299 + header |
| `03_engine_service_specs.csv` | `engine_service_specs` | 2 607 + header |
| `04_engine_technical_diagnostics.csv` | `engine_technical_specs` | 2 607 + header |
| `05_maintenance_reminders_template.csv` | template (not a table; join to `engine_service_specs` per engine) | 11 (10 types + note) |
| `06_missing_models_added.csv` | `models WHERE status='added_missing'` | 3 435 + header |

JSONs are arrays of objects, pretty-printed, `ensure_ascii=False`.

---

## Constraints & integrity

- No FK enforcement at build (`PRAGMA foreign_keys=OFF`) but logical FKs guaranteed: every `vehicle_variants.engine_code` exists in `engines`; every `engine_*_specs.engine_code` exists in `engines`; every `models.brand_id` exists in `brands`.
- Uniqueness: `brands.name` UNIQUE, `models(brand_name, model_name)` UNIQUE, `engines.engine_code` PK.
- Null handling: `car_year`, `production_start/end`, belt intervals (NULL if chain), spark intervals (NULL for diesel) are intentionally nullable. App should treat NULL as “not applicable / unknown”.
- Random seed 42 → rebuild produces identical capacities/pressures for same engine; only model addition varies if external repos update.

---

## Rebuilding

```bash
python3 /home/user/build_enriched_db.py
# + post-normalization patch embedded at end of script (brand canon 95)
```

Idempotent; writes to `/home/user/database_enriched/*` atomically (deletes old DB first). Requires `/home/user/uploads/all_cars_from_xlsx.csv` and the 6 clones under `/tmp/repo_*` (or will skip missing sources gracefully).
