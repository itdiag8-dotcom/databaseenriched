# Metric Audit — 2026-09-11

**Requirement:** all imported data must be in metric (SI), not imperial.  
**Result:** ✅ **100% metric** — all capacities, distances, pressures, lengths, torques use metric units with explicit suffixes. No imperial units found. Added `power_kw` for strict SI compliance.

---

## Methodology

Scanned every file in `database_enriched/`:

```bash
grep -Rin -E "psi|inch|gallon|fahrenheit|°F|mpg|quart|ounce|lb-ft|mile" database_enriched/
grep -Rin -i "miles|psi|gallon|inch" database_enriched/csv_exports/ database_enriched/json/
```

- **Imperial hits:** 0 (the `foot` hit was false positive on HTML `footer` CSS)
- **Python regex audit** across 4 CSVs + JSON + DB schema: no `\bpsi\b`, `\binch`, `\bmiles?\b`, `\bgallon`, `\bfahrenheit`, `lb-ft` etc.
- **Header suffix check:** all measurable columns end with metric suffix `_mm` / `_bar` / `_l` / `_km` / `_nm` / `_cc` / `_rpm` / `_kw`

---

## Unit mapping (every column)

| Domain | Column examples | Unit | Metric? | Imperial equivalent (not used) |
|---|---|---|---|---|
| **Displacement** | `displacement_cc` | cubic centimetres (cc) | ✅ | cubic inches `cid` |
| **Power** | `power_hp` + `power_kw` (new) | hp (source PS) + **kW** (SI) | ✅ (hp kept for traceability, kw = hp × 0.7355) | hp alone would be imperial; kW added 2026-09-11 |
| **Bore / Stroke / Gap** | `bore_mm`, `stroke_mm`, `spark_plug_gap_mm`, `valve_clearance_*` (mm) | millimetres | ✅ | inches (`in`) |
| **Pressure** | `*_bar` (compression, fuel, oil) | bar (1 bar = 100 kPa = 14.5 psi) | ✅ | psi |
| **Capacity** | `*_capacity_l`, `oil_capacity_*_l`, `coolant_capacity_l` | litres (L) | ✅ | quarts / gallons |
| **Distance / Interval** | `*_interval_km`, `timing_chain_inspection_km` | kilometres (km) | ✅ | miles (`mi`) |
| **Torque** | `torque_nm` | Newton-meters (Nm) | ✅ | pound-feet (`lb-ft`) |
| **Speed** | `idle_rpm`, `torque_rpm`, `power_rpm` | revolutions per minute | ✅ (metric) | same |
| **Viscosity** | `oil_viscosity` (0W-20, 5W-30) | SAE grade (metric standard) | ✅ | — |
| **Temperature** | `coolant_type` (G12evo Pink Si-OAT etc.) | coolant spec, not temperature value | ✅ | No °F anywhere |
| **Volume per 100km / Consumption** | not stored | — | — | mpg not used |
| **Year** | `car_year`, `production_start/end` | calendar year | ✅ | — |

**Value ranges prove metric:**

- Oil capacity 2.8–9.5 L (≈ 3.0–10 qts if imperial, but we store L)
- Bore 71–95 mm (≈ 2.8–3.8 in imperial would be 2× smaller numbers, but we store 71–95)
- Compression 10–34 bar (≈ 145–493 psi if imperial, but we store 10–34)
- Torque 66–550 Nm (≈ 49–406 lb-ft, but we store Nm)
- Oil change interval 10 000–20 000 km (≈ 6 200–12 400 mi, but we store km)

All stored numbers fall in metric ranges, not imperial ranges.

---

## Fix applied 2026-09-11

- **Power:** original `power_hp` kept (source Europe uses PS = metric horsepower, 1 PS = 0.7355 kW, very close to imperial hp 0.7457 kW). To be strictly SI, added:
  - `engines.power_kw` (REAL)
  - `engine_service_specs.power_kw` (REAL)
  - `engine_technical_specs.power_kw` (REAL)
  - `vehicle_variants.engine_power_kw` (REAL)
  - CSV columns `power_kw` / `engine_power_kw`
  - JSON field `power_kw` (top-level + nested `service`/`technical`)
- Formula: `power_kw = ROUND(power_hp × 0.73549875, 1)`
  - Example: `312 A1.000` 133 hp → **97.8 kW**, `55253268` 168 hp → **123.6 kW**

No other imperial units were present, so no other conversion needed.

---

## Files changed

- `csv_exports/01_vehicles_deduped.csv` — added `engine_power_kw`
- `csv_exports/03_engine_service_specs.csv` — added `power_kw` after `power_hp`
- `csv_exports/04_engine_technical_diagnostics.csv` — added `power_kw` after `power_hp`
- `json/engine_specs_combined.json` — added `power_kw`
- `car_database.db` — 4 tables altered, 2 views recreated to include `power_kw`

Re-zipped as `database_enriched.zip` (1.8 MB).

---

## How to verify yourself

```bash
unzip -l database_enriched.zip
head -1 csv_exports/03_engine_service_specs.csv  # shows ...power_hp,power_kw,cylinders...
sqlite3 car_database.db "SELECT engine_code, power_hp, power_kw FROM engines LIMIT 3;"
# 312 A1.000|133|97.8
python3 -c "import csv; print(open('csv_exports/04_engine_technical_diagnostics.csv').readline())"
grep -i "psi\|mile\|gallon\|inch\|fahrenheit" csv_exports/* json/*  # should return nothing
```

---

## Conclusion

✅ **All imported data is metric.** No miles, inches, psi, gallons, Fahrenheit, lb-ft, mpg. Pressures in bar, distances in km, volumes in litres, lengths in mm, torque in Nm, displacement in cc, power now in both hp (source) and kW (SI). Ready for EU/DZ app use without conversion.
