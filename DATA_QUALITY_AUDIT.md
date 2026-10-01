# 🔍 Data Quality Audit Report — `car_database.db`

**Audit date:** 2026-09-29
**Target:** `database_enriched/car_database.db` (25 MB, SQLite 3.x)
**Mode:** READ-ONLY — no data, schema, or file was modified during this audit.
**Method:** 60+ automated checks across 6 dimensions: structural integrity, referential integrity, completeness, accuracy/validity, consistency, and repository hygiene. All queries re-runnable (see Appendix B).

---

## 1. Database snapshot audited

| Table | Rows | Description |
|---|---:|---|
| `brands` | 188 | Brand names (103 real + 85 junk/placeholder — see F8) |
| `models` | 6,260 | Model catalog with production years + source tracking |
| `vehicle_variants` | 39,182 | Core table: brand, model, year, fuel, power, engine code, ECU |
| `engines` | 17,916 | One row per engine code (only **5,279 are real OEM codes**) |
| `engine_service_specs` | 17,916 | Maintenance: oil, coolant, timing, filters, plugs, intervals |
| `engine_technical_specs` | 17,916 | Diagnostics: compression, pressures, idle RPM, torque, emissions |

Plus 3 views (`v_engine_full`, `v_model_overview`, `v_vehicle_with_service`).

---

## 2. Scorecard

| Dimension | Score | Verdict |
|---|:---:|---|
| Structural integrity (PKs, file, no dupes) | **9/10** | ✅ Excellent |
| Referential integrity (joins variant↔engine↔specs) | **9/10** | ✅ Excellent (but model join broken by case — F7) |
| Completeness (how filled the columns are) | **4/10** | ⚠️ Weak — 71% of engines lack core attributes |
| Accuracy (values correct for the vehicle) | **4/10** | 🔴 Wrong engine mappings + power conflicts exist |
| Consistency (vocabularies, labels, casing) | **5/10** | ⚠️ Mixed encodings across tables |
| Documentation & repo hygiene | **5/10** | ⚠️ Docs outdated; duplicate copies in repo |
| **Overall** | **≈ 55/100** | **Usable with caution — fix P0 issues before customer-facing use** |

---

## 3. What is healthy ✅

- `PRAGMA integrity_check` = **ok**; file is not corrupted.
- **Zero broken foreign keys**: every one of the 39,182 variants joins to an engine, and every engine joins 1:1 to both spec tables (`v_vehicle_with_service` = 39,182 rows).
- **No exact duplicate variants**, no case-insensitive duplicate models, no duplicate engine PKs.
- **No impossible values**: years all within 2000–2025; power 5–987 hp; cylinders 1–16; idle RPM within 400–2000; compression min ≤ max; no zero/negative service intervals; `production_end ≥ production_start` everywhere.
- `data_confidence` populated on 100% of spec rows — provenance tracking is a real strength of this DB.
- Oil capacities for EV/diesel flagged sensibly in places (e.g., diesel rows say "N/A (Glow Plug)").

---

## 4. Findings (by severity)

### 🔴 CRITICAL — wrong data that can mislead a mechanic

#### F1. Wrong engine-code assignments (approx. 388 confirmed, 742 suspected)
388 variants have an engine code whose power differs **> 50 %** from the variant's own power (742 differ > 30 %). These are not tuning variants — they are **impossible pairings**:

| Variant (brand, model) | Variant hp | Assigned code | Code actually belongs to | Engine hp |
|---|---:|---|---|---:|
| hernr_788 "VEYRON EB 16.4" | 1001 | `E18NVR` | Cadillac CTS 1.8 | 276 |
| Maserati MC 12 | 632 | `A13DTE` | Chevrolet Aveo 1.3 D | 94 |
| Ferrari 599 GTB/GTO | 620 | `A14XER` | Chevrolet Aveo 1.4 | 99 |
| hernr_2164 "MAYBACH (240_)" | 612 | `A13DTE` | Chevrolet Aveo 1.3 D | 94 |
| Mercedes S-Class (W222) | 585 | `2KD-FTV` | Toyota Dyna 2.5 D | 101 |
| Alpina B7 (E65) | 500 | `A13DTE` | Chevrolet Aveo 1.3 D | 94 |

**Impact:** a diagnostics/maintenance app would show oil capacity, plug gaps and compression pressures of a completely different engine. Note the correct rows also exist (e.g., Bugatti Veyron 16.4 correctly has `8.0 W16`, Ferrari 599 Fiorano has `F140C`) — the bad rows come from the Vivid integration matching unmatched models to arbitrary engines.

#### F2. Engine codes shared across many brands — 1,011 codes / 12,642 variants
Some sharing is legitimate platform reuse (VW `CCZA` → Audi/Seat/Škoda/VW; Hyundai/Kia `G4GC`). But others are contamination from fuzzy matching:
- `A13DTE` (Fiat 1.3 JTD) attached to **24 brands** incl. Alpina, Maserati, Maybach, Honda CR-V
- `C16NZ2` (Opel 1.6) → 24 brands incl. Lexus, Subaru, Cadillac, Lada
- `E18NVR` (GM 1.8) → 21 brands incl. Bugatti, Volkswagen, Alpina

#### F3. Variant power vs engine power conflicts — 12,992 rows
The `engines` table stores a **single** power per engine code, but **2,223 codes legitimately span multiple outputs** (families like `N47D20C`, `4B11`). Average |Δ| = 15.5 hp, but the tail is huge (max 725 hp). Root cause: **data model** — `engine_code` alone is not a unique key for power; the family code vs. tune-specific code distinction was lost.

#### F4. Fuel type conflicts between tables — 385 rows
e.g., Hyundai Grandeur petrol variant joined to diesel engine `G6DG`; VW Golf VI petrol variant joined to diesel `CCSA`; Subaru XV diesel joined to petrol `A16LET`.

---

### 🟠 HIGH — big coverage/structure gaps

#### F5. 70 % of engines are synthetic `LEMON_*` codes with almost no technical data
- **12,637 of 17,916 engines (70.5 %)** carry synthetic codes like `LEMON_ACURA_1.6EL_2000`.
- **7,310** contain `_0CC_` (displacement unknown → zero), **2,535** contain a VIN suffix.
- Consequence: **12,740 engines (71 %) have NULL** power, cylinders, bore/stroke, compression, timing type, oil standard, change intervals, coolant type, ECU. The LEMON rows essentially contain only fluid capacities.
- ⚠️ `MISSING_ENGINE_CODES_REPORT.md` documents replacing codes down to 12,290 synthetic on a 17,615-engine DB — **that state is not this file** (this DB still has 12,637; the older nested copy `database_enriched/database_enriched/` has 17,590). The fix was applied to a different working copy and never landed here.

#### F6. Core-attribute completeness (share of rows NULL/blank)

| Table | Field | NULL % |
|---|---|---:|
| engines | power_hp, power_kw | 71.3 % |
| engines | engine_type, cylinders, ECU maker/model | 71.1 % |
| engines | displacement_cc | 30.0 % |
| vehicle_variants | engine_power_hp / kW, engine_type, ECU | 34.0–34.2 % |
| engine_service_specs | timing_type, oil_standard, intervals, coolant, filters, plugs | 71.1 % |
| engine_technical_specs | bore, stroke, compression, idle RPM, torque, valve clearance… | 68–71 % |
| models | production_start/end | 20.6 % |

#### F7. Model-name case mismatch breaks the variants↔models join
- **15,241 variant model names are ALL-CAPS** (Vivid style: `ASTRA J`, `FABIA`) vs mixed-case `models` rows.
- **1,748 variants fail the exact `(brand, model)` join**; of these **1,606 would match case-insensitively** → pure case problem; **47 models are genuinely missing**.
- `models.total_variants` is wrong for **1,001 models**; `v_model_overview` reports 0 variants for **2,414 models**.
- 2,078 ALL-CAPS names also live inside `models` itself.

#### F8. `hernr_*` placeholder brands hide real marques
83 pseudo-brands (`hernr_1138`…), 339 models, 743 variants. They are unresolved Vivid "Hersteller-Nr" buckets holding recognizable cars:
- `hernr_1138` = **Smart** (Fortwo, Roadster, Forfour)
- `hernr_1139` = **Daewoo/Zaz** (Lanos, Slavuta)
- `hernr_1280` = **Mahindra** (Bolero)
- `hernr_788` = **Bugatti** (Veyron) — see F1

#### F9. Confidence labels disagree between tables — 1,444 engines
`engines.data_confidence` ≠ `engine_service_specs.data_confidence` for 1,444 codes (1,395 are TRUSTED_AFTERMARKET in engines but ESTIMATE in service; totals also differ: 25/1,406 vs 18/3). Users can't tell which label to trust.

---

### 🟡 MEDIUM — normalization and hygiene issues

| # | Finding | Count | Example |
|---|---|---:|---|
| F10 | DPF/EGR/AdBlue flags use 4 vocabularies (`NULL`, `-`, `No`, `Yes`) | 12,740 NULL / 3,239 `-` / 776 `No` / 1,161 `Yes` | `-` = petrol/EV, `No` = diesel w/o DPF, NULL = unknown — implicit, undocumented |
| F11 | Fuel vocabulary inconsistent between tables | 385 conflicts + stray values | variants: `Hybrid (Petrol-/ Electro.)` (1), `Electric Motor`; engines has only 5 values |
| F12 | Malformed oil viscosities | 18 | `15-W40` (7), lowercase `0w-30` (11) |
| F13 | Model-name typos / case errors | ~47 models | Ford **Crow Victoria** (Crown Victoria exists), GWM **Hower** (Hover exists), Donkervoort **D8 Gt**; Ford E-Series & Courier missing |
| F14 | Orphan engines never used by any variant | 155 | Real codes (`AKL`, `AGN`, `AHH`, `AFN`…) that lost their variants during integration |
| F15 | Models without production years | 1,291 (20.6 %) | mostly `DanielKohut/car-data` additions |
| F16 | Variant year outside model production window | 358 | e.g., variant 2002 for a 2008– model |
| F17 | Variants with NULL year | 296 | |
| F18 | EVs modeled as combustion cars | 30 variants / 14 engines | all 30 EV variants carry oil viscosity & capacity specs; 8 engines have displacement = 0 |
| F19 | Engine "codes" that are descriptions | 528 | `engine_code = engine_type` (`1.4 16v T-Jet MTA`); 10 purely numeric codes (`55253268` = Fiat part number) |
| F20 | Near-duplicate engine codes (case/space-insensitive) | 12 pairs | `OM651 DE 22 LA` ×2, `2.0 dCI` ×2, `1.9 DDiS` ×2 |
| F21 | Same engine listed >1× per (brand, model, year) | 2,486 groups / 3,273 redundant rows | some legit (different ECU), many differ only by power or engine_type text |
| F22 | Suspicious oil capacities | 8 rows + 4,877 quart-multiples | `LEMON_FORD_CAB_7300CC_*` = 16.08 L (exactly 17 US qt — verify unit conversion) |

---

### 🟢 LOW — documentation & repository hygiene

| # | Finding |
|---|---|
| F23 | `brands` contains both `Citroen` and `Citroën`; casing oddities (`SATURN`, `SHELBY`, `Saic Mg`, `Jmc`, `Dr Motor`) |
| F24 | Docs are stale: README claims **95 brands / 4,299 models / 2,607 engines**; actual = **188 / 6,260 / 17,916**. CHANGELOG stops at the 2026-09-11 state. |
| F25 | ~~Repo bloat: nested duplicate snapshot `database_enriched/database_enriched/` (older DB, 38,921 variants/17,590 engines), 3 zip archives (~30 MB), `.git` ≈ 42 MB.~~ **Partly resolved 2026-10-01:** the nested duplicate (171 MB, 27 files, all stale copies) and the 60 tracked DB backups (1.5 GB) are no longer versioned; its one unique file was kept as `csv_exports/07_missing_engine_codes_2026-09-26_baseline.csv`. The 3 zips and the history blobs remain. |
| F26 | `backups/car_database_backup_2026-09-26.db` is **byte-identical** to the live DB — only one restore point. |
| F27 | `ecu_maker='Unknown'` for 1,161 engines (better as NULL). |
| F28 | No `CHECK` constraints or `COLLATE NOCASE` unique indexes; FKs declared but not enforced by default (`PRAGMA foreign_keys` is off per-connection in SQLite). |

---

## 5. Improvement plan (prioritized, no changes applied)

### P0 — Safety-critical (do before customer-facing use)

1. **Purge or re-map the wrong engine assignments (F1, F2, F4).**
   - Export the suspicious list: variants joined to engines where `|variant_hp − engine_hp| / engine_hp > 0.30` OR fuel differs OR (brand ≠ engine.brand_example AND power differs > 20 %).
   - For each, either NULL the `engine_code` (and drop the join in views) or attach the correct OEM code. The pilot method in `MISSING_ENGINE_CODES_REPORT.md` (web-verified codes with citations) is exactly right — extend it from 30 to the full 742-row list.
   - Tighten the fuzzy matcher in `integrate_vivid.py`: **never** accept a code match when power differs > 20 % or fuel differs; require brand compatibility (allow only known platform-sharing pairs).

2. **Fix the engine identity model (F3).**
   - Option A (cheap): add `power_hp`/`power_kw` to the variant→engine mapping and treat `(engine_code, power_hp)` as the lookup key.
   - Option B (better): split `engines` into `engine_families` (code, displacement, architecture) and `engine_tunes` (code, power, torque, fuel, ECU) — mirrors reality (e.g., N47D20C at 114/143/163/177 hp).
   - At minimum add `power_hp_min` / `power_hp_max` to `engines` and validate variants against the range.

### P1 — Make the LEMON 70 % actually useful

3. **Continue synthetic-code replacement (F5).** 12,637 remain; prioritize by variant popularity (vehicles on the road in your market). Sources: Wikipedia engine infoboxes, enginecode.uk, OEM TSBs — the pilot's citation-based workflow is good practice.
4. **Deep-crawl Lemon "Common Specs" pages** for compression, oil pressure, valve clearance — `tech_source` shows only ~65 pages were used; the crawler (`crawl_lemon_full.py`) already supports it.
5. **Resolve `hernr_*` brands (F8).** The model names are readable (Smart Fortwo, Daewoo Lanos, Mahindra Bolero, Bugatti Veyron) — a 1–2 hour manual mapping table fixes 743 variants.
6. **Normalize model-name casing (F7).** Rebuild `models.model_name` to canonical title-case, dedupe case-insensitively, then re-join. Add `COLLATE NOCASE` unique index on `models(brand_name, model_name)` and recompute `total_variants`. Fixes 1,606 orphan variants + 1,001 wrong counts at once.

### P2 — Consistency & cleanup

7. **Standardize vocabularies:** flags to `Yes/No/NULL` (F10); fuel to an enum `Petrol/Diesel/Hybrid/Electric/LPG/E85/Wankel` (F11); oil viscosity validated against `^\d{1,2}W-\d{2}$` (F12); one `data_confidence` source of truth, synced across the 3 tables (F9); `Unknown` ECU → NULL (F27).
8. **Model catalog fixes:** add the 47 missing models, fix typos (Crow→Crown Victoria, Hower→Hover), merge Citroën, backfill production years for the 1,291 NULL models from Wikipedia/model-page ranges (F13, F15, F23).
9. **EV handling:** either a separate `ev_specs` table (battery kWh, motor type) or explicit NULLs for combustion-only fields; drop `displacement_cc=0` in favor of NULL (F18).
10. **Engine code hygiene:** merge the 12 case/space-duplicate codes (F20); replace description-codes with real codes where known or flag with `is_synthetic` boolean column instead of string-matching `LEMON_` (F19); delete or archive the 155 orphan engines (F14).
11. **Deduplicate same-car rows** (F21): keep distinct rows only when ECU or transmission genuinely differs; collapse the rest.

### P3 — Process & repo

12. **Add a data-quality gate script** (`audit_db.py`) run before every integration — Appendix B is a starting skeleton; fail the build on: new orphan joins, power mismatches > 30 %, fuel conflicts, vocabulary drift.
13. **Update the docs** (README/CHANGELOG/SCHEMA) to the real counts and add the "known limitations" section (F24).
14. **Slim the repo** (partly done 2026-10-01: nested duplicate and backups untracked, see F25): `git rm -r` the nested `database_enriched/database_enriched/` duplicate and the 3 zips; add `*.zip`, `*.db` (except a canonical one), `lemon_crawl_*.jsonl` to `.gitignore`; consider Git LFS for the DB (F25). Keep rotating backups (F26).
15. **Harden the schema:** `PRAGMA foreign_keys=ON` in every connection (incl. `server.js`), `CHECK` constraints on fuel/power/year ranges, `COLLATE NOCASE` indexes, and an `import_log` table (source, date, rows added/updated, checks passed) so provenance is queryable.

---

## 6. Suggested target metrics

| Metric | Now | Target (3 months) |
|---|---:|---:|
| Variants with verified-correct engine code (power within 10 % & fuel match) | ~66 % | > 95 % |
| Engines with real OEM code | 29.5 % | > 60 % |
| Engines with power + fuel + displacement filled | ~29 % | > 75 % |
| Variants failing (brand, model) join | 1,748 | 0 |
| Placeholder brands | 83 | 0 |
| Confidence-label conflicts | 1,444 | 0 |
| Fuel-vocabulary conflicts | 385 | 0 |

---

## Appendix A — Audit environment

- DB opened URI read-only: `file:database_enriched/car_database.db?mode=ro`
- Backup hash check: `backups/car_database_backup_2026-09-26.db` ≡ live DB (identical MD5)
- Git worktree confirmed clean after audit (`git status` empty)

## Appendix B — Re-runnable check queries (selection)

```sql
-- F1 wrong engine mapping candidates
SELECT v.*, e.power_hp AS engine_hp, e.brand_example, e.model_example
FROM vehicle_variants v JOIN engines e ON e.engine_code = v.engine_code
WHERE v.engine_power_hp IS NOT NULL AND e.power_hp IS NOT NULL
  AND ABS(v.engine_power_hp - e.power_hp) * 1.0 / e.power_hp > 0.30;

-- F2 engine codes spanning brands
SELECT engine_code, COUNT(DISTINCT car_brand) brands, COUNT(*) variants
FROM vehicle_variants GROUP BY engine_code HAVING brands > 1;

-- F4 fuel conflicts
SELECT v.car_brand, v.car_model, v.car_year, v.engine_code, v.fuel, e.fuel
FROM vehicle_variants v JOIN engines e ON e.engine_code = v.engine_code
WHERE v.fuel <> e.fuel;

-- F5 synthetic codes
SELECT COUNT(*) FROM engines WHERE engine_code LIKE 'LEMON_%';

-- F7 case-mismatch orphans
SELECT COUNT(*) FROM vehicle_variants v
WHERE NOT EXISTS (SELECT 1 FROM models m
                  WHERE m.brand_name = v.car_brand AND m.model_name = v.car_model);

-- F9 confidence conflicts
SELECT e.engine_code, e.data_confidence, s.data_confidence
FROM engines e JOIN engine_service_specs s ON s.engine_code = e.engine_code
WHERE e.data_confidence <> s.data_confidence;

-- F15/F16/F17 year issues
SELECT COUNT(*) FROM models WHERE production_start IS NULL;
SELECT COUNT(*) FROM vehicle_variants v JOIN models m
  ON m.brand_name = v.car_brand AND m.model_name = v.car_model
WHERE v.car_year IS NOT NULL AND m.production_start IS NOT NULL
  AND (v.car_year < m.production_start OR v.car_year > m.production_end + 1);
```
