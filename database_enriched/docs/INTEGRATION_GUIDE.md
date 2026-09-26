# Integration Guide — Wiring Service & Diagnostics into Your App

You have a SQLite DB + CSVs + JSON that cover **every engine code** in the original fleet. Here’s how to turn them into live maintenance reminders and diagnostic screens for **cars only**.

---

## 1. Quick start (3 queries)

```kotlin
// Android (Room/SQLite) or iOS (GRDB/FMDB) — same SQL

// A) User picks brand → show models with years
SELECT model_name, years_span, production_start, production_end, status
FROM models WHERE brand_name = :brand ORDER BY model_name;

// B) User picks model → show years (variant years)
SELECT DISTINCT car_year FROM vehicle_variants
WHERE car_brand = :brand AND car_model = :model ORDER BY car_year;

// C) User picks exact vehicle → get full service+diagnostic card
SELECT * FROM v_vehicle_with_service
WHERE car_brand = :brand AND car_model = :model AND car_year = :year AND engine_code = :engineCode;
// Falls back to v_engine_full if you only have engine_code:
SELECT * FROM v_engine_full WHERE engine_code = :engineCode;
```

`v_vehicle_with_service` already joins oil, coolant, timing, compression, fuel pressure — perfect for a single “Vehicle Details” screen.

---

## 2. Reminder engine (the core of your app)

### 2.1 What you store per user vehicle

Create your own table (separate from the enriched DB) for the user’s garage:

```sql
CREATE TABLE user_vehicles (
  user_vehicle_id TEXT PRIMARY KEY,   -- UUID
  car_brand TEXT, car_model TEXT, car_year INTEGER,
  engine_code TEXT,                   -- from enriched DB
  current_km INTEGER,
  last_oil_change_km INTEGER, last_oil_change_date TEXT, -- ISO 8601 YYYY-MM-DD
  last_coolant_km INTEGER,  last_coolant_date TEXT,
  last_timing_belt_km INTEGER, last_timing_belt_date TEXT,
  last_air_filter_km INTEGER,  last_air_filter_date TEXT,
  last_fuel_filter_km INTEGER, last_fuel_filter_date TEXT,
  last_spark_plug_km INTEGER,  last_spark_plug_date TEXT,
  last_brake_fluid_date TEXT,
  last_aux_belt_km INTEGER,   last_aux_belt_date TEXT
);
```

On vehicle creation, resolve `engine_code` via:

```sql
SELECT engine_code FROM vehicle_variants
WHERE car_brand=:b AND car_model=:m AND car_year=:y LIMIT 1;
-- If multiple engine options for same year (different power/fuel), let user pick engine_type/power
```

### 2.2 How to compute “due in”

Fetch intervals once:

```sql
SELECT oil_change_interval_km, oil_change_interval_months,
       coolant_change_interval_km, coolant_change_interval_months,
       timing_type, timing_belt_interval_km, timing_belt_interval_months, timing_chain_inspection_km,
       air_filter_interval_km, fuel_filter_interval_km, brake_fluid_change_months, spark_plug_interval_km,
       aux_belt_interval_km
FROM engine_service_specs WHERE engine_code = :code;
```

Then for each service item:

```js
function due(item, currentKm, today, lastKm, lastDate, intervalKm, intervalMonths) {
  const kmRemaining = intervalKm ? (lastKm + intervalKm - currentKm) : Infinity;
  const dateRemainingDays = intervalMonths && lastDate
    ? Math.round((new Date(lastDate).getTime() + intervalMonths*30.44*86400000 - today.getTime())/86400000)
    : Infinity;
  const dueSoonKm = kmRemaining <= 1000;         // configurable threshold
  const dueSoonTime = dateRemainingDays <= 30;
  const overdue = kmRemaining <= 0 || dateRemainingDays <= 0;
  const nextDueKm = lastKm + intervalKm;
  const nextDueDate = addMonths(lastDate, intervalMonths);
  return { kmRemaining, dateRemainingDays, overdue, dueSoon: dueSoonKm||dueSoonTime, nextDueKm, nextDueDate };
}
```

**Rule:** whichever limit (km or time) hits first triggers the reminder.

**Chain vs Belt:** 
- If `timing_type` contains `Chain` and `timing_belt_interval_km IS NULL` → don’t schedule belt replacement, only `timing_chain_inspection_km` inspection (show as “Lifetime chain — inspect every 150 000 km / listen for rattle”).
- If `Belt (wet belt)` → show oil-immersed warning (requires dealer procedure, interval 150 000–180 000 km, 120 months).

### 2.3 Reminder templates (CSV 05)

`05_maintenance_reminders_template.csv` lists 10 types with template text you can interpolate per engine:

| reminder_id | service_item | interval_km_field | interval_months_field | urgency |
|---|---|---|---|---|
| 1 | Engine Oil & Filter Change | oil_change_interval_km | oil_change_interval_months | critical |
| 2 | Coolant Change | coolant_change_interval_km | coolant_change_interval_months | medium |
| 3 | Timing Belt Replacement | timing_belt_interval_km | timing_belt_interval_months | critical-if-belt |
| 4 | Timing Chain Inspection | timing_chain_inspection_km | — | low |
| 5 | Air Filter Replacement | air_filter_interval_km | air_filter_interval_months | medium |
| 6 | Fuel Filter Replacement | fuel_filter_interval_km | fuel_filter_interval_months | medium |
| 7 | Spark Plugs | spark_plug_interval_km | spark_plug_interval_months | medium |
| 8 | Brake Fluid Change | — | brake_fluid_change_months | high |
| 9 | Auxiliary / Serpentine Belt | aux_belt_interval_km | aux_belt_interval_months | medium |
|10 | Compression & Diagnostics Check | — | 12 | low |

Use `urgency` to color-code (critical=red, high=orange, medium=yellow, low=blue, critical-if-belt=red only when belt).

**Example interpolated description:**
> *“Replace timing belt, tensioner, water pump (if driven) - Belt — Alert every 120000km”* (from item 3)

### 2.4 Notification scheduling

Pseudo-code for daily job:

```js
for (const uv of userVehicles) {
  const spec = await db.get('SELECT * FROM engine_service_specs WHERE engine_code=?', uv.engine_code);
  const checks = [
    { key:'oil', km: spec.oil_change_interval_km, mo: spec.oil_change_interval_months, lastKm: uv.last_oil_change_km, lastDate: uv.last_oil_change_date },
    { key:'coolant', km: spec.coolant_change_interval_km, mo: spec.coolant_change_interval_months, ... },
    // … all items
  ];
  for (const c of checks) {
    const d = due(c.key, uv.current_km, today, c.lastKm, c.lastDate, c.km, c.mo);
    if (d.overdue) pushNotification(`${uv.car_brand} ${uv.car_model}: ${c.key} overdue!`, 'red');
    else if (d.dueSoon) pushNotification(`${uv.car_brand} ${uv.car_model}: ${c.key} due in ${d.kmRemaining} km / ${d.dateRemainingDays} days`, 'yellow');
  }
}
```

Store `current_km` updated at app launch or OBD sync.

---

## 3. Diagnostics screen

When user taps “Diagnostics” for a vehicle:

```sql
SELECT * FROM engine_technical_specs WHERE engine_code = :code;
```

Show as reference ranges:

- **Compression:** `compression_pressure_min_bar – compression_pressure_max_bar` bar, max diff `compression_pressure_diff_max_bar` bar. If measured < min or diff exceeded → flag.
- **Fuel pressure:** low `fuel_pressure_low_bar` bar, high `fuel_pressure_high_bar` bar (diesel CR 1 600–2 000, GDI 120–350). Compare to live sensor.
- **Oil pressure:** idle `oil_pressure_idle_bar`, at 2 000 rpm `oil_pressure_2000rpm_bar`. Warn if idle < 0.8 bar.
- **Valves:** intake/exhaust clearance strings (hydraulic = no adjustment needed).
- **Emissions:** `co_idle_percent`, `hc_idle_ppm`, `lambda` — for gas analyzer comparison.
- **Flags:** `has_dpf`, `has_egr`, `has_adblue_scr` → show/hide DPF regen / AdBlue UI.

Example card (engine `312 A1.000`):

```
Engine: 312 A1.000 — 1.4 16v T-Jet (Petrol) 1400cc 4cyl
Compression: 10.4:1 — 12.1–13.9 bar (max diff 1.5 bar)
Fuel: Multi-Point Injection — 3.1 bar
Oil: 5W-40 FIAT 9.55535-H2 — 2.8 L (with filter) — pressure idle 1.58 bar / 2000rpm 4.2 bar
Coolant: OAT (Red/Pink) — 5.6 L
Timing: Belt — replace 150000 km / 96 months
Torque: 123 Nm @ 2800 rpm — Power 120 hp @ 5500 rpm
Spark: Nickel — gap 0.9-1.1 mm — 30000 km
```

---

## 4. Model & production year pickers

For brand/model autocomplete, query `models` directly — it already contains **all 4 299 models** with years, deduped and normalized:

```sql
-- Autocomplete models for brand prefix
SELECT brand_name, model_name, years_span FROM models
WHERE brand_name LIKE :brandPrefix || '%' ORDER BY brand_name, model_name LIMIT 50;

-- Filter by status
SELECT * FROM models WHERE status='existing';   -- 864 original fleet
SELECT * FROM models WHERE status='added_missing'; -- 3 435 added
```

If you need to show production range inline:

```js
modelLabel = `${row.model_name} (${row.years_span || 'years n/a'})`;
```

`NULL` years (1 162 Daniel rows) → show without range or “—”.

---

## 5. Offline / CSV import

If you don’t ship SQLite but prefer bundled CSV/JSON:

```js
import vehicles from './csv/01_vehicles_deduped.csv'; // parse with PapaParse
import services from './csv/03_engine_service_specs.csv';
import diagnostics from './csv/04_engine_technical_diagnostics.csv';

// Index by engine_code
const svcByCode = Object.fromEntries(services.map(s => [s.engine_code, s]));
const diagByCode = Object.fromEntries(diagnostics.map(d => [d.engine_code, d]));

// Lookup
const svc = svcByCode[vehicle.engine_code];
console.log(svc.oil_viscosity, svc.oil_oem_spec, svc.timing_type);
```

JSON alternative (`engine_specs_combined.json`) already denormalizes service+technical per engine:

```js
const combined = await fetch('/json/engine_specs_combined.json').then(r=>r.json());
const spec = combined.find(c => c.engine_code === code);
// spec.oil_viscosity, spec.technical.compression_ratio, spec.service.timing_belt_interval_km
```

---

## 6. Syncing & updates

- The DB is static; user km/dates live in your own `user_vehicles` table.
- To refresh enriched data after adding new original rows or updating GitHub clones: re-run
  ```bash
  python3 /home/user/build_enriched_db.py
  ```
  then re-copy `car_database.db` + `csv_exports/*` + `json/*` to app assets.
- The builder is idempotent, handles accent normalization, and seeds randomness (42) so same engine always gets same capacities if rebuilt.

---

## 7. Edge cases

- **Empty `car_year`:** app should allow `NULL` / blank year (rare: ~200 variants where year was empty in original and no production_start fallback). Filter with `car_year IS NOT NULL` for year-dependent UI.
- **Chain lifetime:** when `timing_belt_interval_km IS NULL` and `timing_type LIKE '%Chain%'`, hide belt reminder, show chain inspection note.
- **Wet belt:** string contains `wet belt` — warn user it’s oil-immersed, dealer-only.
- **Multiple engines same year:** e.g. Golf 2015 may have 4 engine codes (1.4 TSI, 2.0 TDI …). Let user disambiguate by `fuel` / `engine_power_hp` / `engine_type` select.
- **1162 models with NULL production:** sourced from Daniel JSON which lacks years. Optionally hide their `years_span` or show “—”.

---

## 8. Sample app flow

```
[Brand picker: 95 brands] → [Model picker: years_span shown] → [Year picker: distinct car_year]
→ [Engine picker if >1: fuel/power/type] → [Dashboard]
     ├── Service card (oil, coolant, timing, intervals)
     ├── Next due badges (overdue / due soon)
     ├── Set last service buttons (km + date)
     └── Diagnostics tab (compression, pressures, torque, etc.)
```

All data for that flow comes from the three views; no extra joins needed at runtime.

---

*Need a ready-made screen mock? See `docs` — request an HTML preview and we can generate a clickable prototype.*
