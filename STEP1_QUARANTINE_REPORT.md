# 🛡️ Step 1 — Quarantine of Wrong Engine Mappings (Executed)

**Date:** 2026-09-29
**Database:** `database_enriched/car_database.db`
**Script:** `step1_quarantine_wrong_mappings.py` (rerunnable, `--dry-run` / `--apply`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step1_2026-09-29.db` (full file copy taken *before* any change)

---

## 1. What was done

Variant→engine mappings that are **physically impossible** were quarantined:
the variant's `engine_code` was set to `NULL` (so the app shows *no data* instead
of **wrong** oil/plug/compression specs) and every value needed to re-map it
correctly was preserved in a new **`remapping_queue`** table.

**481 mappings quarantined out of 39,182 (1.2 %).**

| Reason | Rows | Meaning |
|---|---:|---|
| `HARD_FUEL_CONFLICT` | 278 | petrol variant ↔ diesel engine (and similar) — one side must be wrong |
| `DISPLACEMENT_MISMATCH` | 158 | displacement parsed from the variant's engine_type differs >25% from the engine row — different physical engine |
| `POWER_MISMATCH_CROSSBRAND` | 45 | power off >30%, brands unrelated, displacement unverifiable (the Veyron/MC12/599 absurdities) |

## 2. How legitimate cross-brand engine sharing was protected ⚠️

Many models from different brands share the same engine code in real life
(VW-group `CCZA` in Audi/Seat/Škoda/VW, Hyundai/Kia `G4GC`, Fiat 1.3 MultiJet
`A13DTE` in Opel/Vauxhall/Chevrolet). The rules were designed so that **sharing
is never mistaken for an error**:

| Real-world situation | How it was handled | Rows |
|---|---|---:|
| Same engine, same tune, several brands | Fuel + displacement + power all agree → untouched (part of "clean") | ~12,600 |
| Same engine, different tune (e.g. `N47D20C` 114–184 hp) | Displacement matches → **KEPT** (`KEPT_shared_engine_other_tune`) | 270 |
| Different tune within one brand family (e.g. `4G63T` Evo, `OM651` 120–204 hp) | Family + fuel agree → **KEPT** (`KEPT_same_brand_power_spread`) | 159 |
| Soft fuel-label difference (Petrol↔Hybrid, Ethanol↔Petrol, Wankel↔Petrol) | Same engine in reality (e.g. Toyota SAI ↔ `2AZ-FXE`) → **KEPT** | 89 |
| **Real diesel-hybrids / EREV** (Mercedes E 300 BlueTEC Hybrid `OM651.924`, Peugeot 508/3008/DS5 Hybrid4 `DW10`, BMW i3 REX `IB1P25B`) | "Hybrid" vs "Diesel/Electric" label + displacement & power confirm → **KEPT** | 12 |
| Displacement conflict BUT power matches ≤15% AND brands share a platform family (badge engineering: Opel↔Vauxhall↔Holden, Mini↔BMW, Chevy↔Cadillac) | Mapping most likely right, bad data on one side → **KEPT**, exported to fix-worklist | 452 |

A **brand-family map** (GM, VW Group, BMW+Mini, FCA/Stellantis, PSA+Opel,
Renault-Nissan-Mitsubishi, Hyundai-Kia, Ford+PAG incl. Volvo/JLR, Toyota+Subaru,
Honda, Suzuki-Maruti) is embedded in the script and used by the rules.

### Preserved (verified after apply)
- `CCZA`: 69 variants / 4 brands • `CAYC`: 66 / 4 • `G4GC`: 79 / 2 • `G6BA`: 65 / 2 • `D4FB`: 85 / 2
- `A13DTE`: **105 variants / 24 brands → 24 variants / 3 brands** (Chevrolet, Opel, Vauxhall — the *real* 1.3 MultiJet users; the 81 junk assignments incl. Maserati MC12 were quarantined)
- `N47D20C`: 135 variants (BMW tune family) • `4G63T`: 48 (Lancer/Evo) • `2AZ-FXE`: 11 (Toyota/Lexus hybrids)
- Bugatti Veyron 16.4 keeps its correct `8.0 W16` specs (5W-30, 9.5 L); only the junk `hernr_788`/`E18NVR` rows were quarantined

## 3. What changed in the DB

| Item | Before | After |
|---|---:|---:|
| `vehicle_variants` rows | 39,182 | 39,182 (unchanged — no data deleted) |
| variants with `engine_code = NULL` | 0 | **481** |
| `v_vehicle_with_service` (usable spec rows) | 39,182 | 38,701 |
| new table `remapping_queue` | — | 481 rows (all `status='pending'`) |
| `engines.count_variants` | — | recomputed to stay consistent |
| `PRAGMA integrity_check` | ok | **ok** |

New files:
- `database_enriched/csv_exports/08_remapping_queue.csv` — the 481 rows to re-map
- `database_enriched/csv_exports/09_engine_row_suspects.csv` — 452 kept rows where either the variant's `engine_type` text is junk (Vivid artifacts like `'3.8 Carrera'` on a Fiat Idea) or the **engine row's displacement is wrong** (e.g. `B38B15M0` listed 1005 cc vs real 1499 cc; `QR25DE` listed 1600 cc vs real 2488 cc; `M57D30` listed 2353 cc vs real 2926 cc)

## 4. How to review the queue

```sql
-- pending items, worst first
SELECT car_brand, car_model, car_year, variant_power_hp, wrong_engine_code,
       wrong_engine_brand_example, wrong_engine_model_example, reason, detail
FROM remapping_queue WHERE status='pending'
ORDER BY CASE reason WHEN 'HARD_FUEL_CONFLICT' THEN 1
                     WHEN 'DISPLACEMENT_MISMATCH' THEN 2 ELSE 3 END;

-- after verifying the correct code (web-verified, citation in note):
UPDATE remapping_queue SET status='remapped', new_engine_code='<code>', note='<source>'
WHERE vehicle_variant_id = <id>;
UPDATE vehicle_variants SET engine_code='<code>' WHERE id = <id>;
```

The web-verification workflow already proven in `MISSING_ENGINE_CODES_REPORT.md`
(search → cite → replace) is the right method for the 45 `POWER_MISMATCH_CROSSBRAND`
rows and the displaced engines; the 278 fuel conflicts need a case-by-case decision
on *which side* is wrong (often the variant's fuel label, e.g. Renault Kangoo
`1.5 dCi` labelled Petrol).

## 5. Rollback (if ever needed)

**Option A — full restore:**
```bash
cp database_enriched/backups/car_database_backup_pre_step1_2026-09-29.db \
   database_enriched/car_database.db
```
**Option B — surgical (keeps everything else done since):**
```sql
UPDATE vehicle_variants
SET engine_code = (SELECT wrong_engine_code FROM remapping_queue
                   WHERE vehicle_variant_id = vehicle_variants.id)
WHERE id IN (SELECT vehicle_variant_id FROM remapping_queue);
DROP TABLE remapping_queue;
```

## 6. Next steps

1. **Step 2 — model-name case normalization** (fixes 1,606 orphan variants + 1,001 wrong `models.total_variants`)
2. **Step 3 — resolve the 83 `hernr_*` placeholder brands** (Smart, Daewoo, Mahindra, Bugatti…)
3. **Step 4 — re-map the 481 quarantined rows** using the citation-based pilot method
4. **Engine-row fixes** for the 452 worklist rows (`09_engine_row_suspects.csv`) — correct engine displacements instead of remapping
