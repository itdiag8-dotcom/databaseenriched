# 🧭 Step 2 — Model-Name Case Normalization (Executed)

**Date:** 2026-09-29 • **Script:** `step2_normalize_model_names.py` (dry-run/apply)
**Backup:** `database_enriched/backups/car_database_backup_pre_step2_2026-09-29.db`

## Result

| Metric | Before | After |
|---|---:|---:|
| Variants failing the `(brand, model)` join to `models` | 1,748 | **0** ✅ |
| Models with wrong `total_variants` | 1,001 | **0** ✅ |
| `v_model_overview` models showing 0 variants | 2,414 | 2,364 (rest legitimately have no variants) |
| Duplicate variant groups | 1 | 1 (unchanged — no case-merge collisions) |
| `PRAGMA integrity_check` | ok | ok |

## What was changed

1. **1,655 variant renames** to the catalog casing (`ASTRA J` → `Astra J`, `FABIA` → `Fabia`, `TOURNEO CONNECT` → `Tourneo Connect`, `BRERA` → `Brera`…). Breakdown: 1,606 model-case only + 49 brand-and-model case (`Saturn` → `SATURN`, matching the catalog's casing). Full log: `csv_exports/10_model_name_changes.csv`. The **models catalog casing was left untouched** (deliberately — re-casing 2,078 ALL-CAPS catalog names risks breaking real names like `CR-V`).
2. **39 new model rows** added for pairs that exist only in variants (93 variant rows) — `source='derived_from_vehicle_variants'`, `status='added_missing'`, production years derived from variant years. List: `csv_exports/11_added_models.csv`. Notable legit additions: Subaru **Traviq**, Isuzu **N Series**, Renault **Mascott**, Mazda **Demio**, Nissan **Interstar**, Ford **E-Series/Courier/Endeavour**, Mahindra **Xylo**, Maruti **Ritz**, Donkervoort **D8 Gt**.
3. **`models.total_variants` recomputed for all 6,299 models.**

## ⚠️ Flagged for review in Step 3 (added as-is, not auto-corrected)

| Pattern | Rows | Likely truth |
|---|---|---|
| `SATURN Corsa/Agila/Zafira/Signum/Commodore Vz`, `Holden Corsa/Agila/Signum/Lacetti/Commodore Vz`, `Vauxhall Commodore Vz` | ~14 | Mis-branded rebadges (Opel/Vauxhall/Holden models under the wrong marque) — brand attribution fix |
| `Ford Crow Victoria` | 4 | Typo → `Crown Victoria` (exists in catalog) |
| `GWM Hower` | 1 | Probably `Hover` spelling variant |
| `Lancia K` / `Lancia Z`, `Renault Logan Mcv/Pick-Up`, `Suzuki Fun`, `Mahindra Meagle/Pick-Up` | 9 | Naming-style variants to consolidate |

## Rollback
```bash
cp database_enriched/backups/car_database_backup_pre_step2_2026-09-29.db \
   database_enriched/car_database.db
```
