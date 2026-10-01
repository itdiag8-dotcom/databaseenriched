# Step 5 — Batch 13 Report: Honda LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step22_step5_lemon_batch13_honda.py` (+ `step22b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step22_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/30_lemon_batch13_decisions.csv` (per-variant, with evidence)

Batch 13 in LEMON-count order = **every remaining LEMON Honda variant** (312 rows, 19 models,
MY2000–2025). **311 variants remapped, 1 skipped** — the cleanest hit-rate of any large batch.
22 new engine rows, 13 row-fixes, 52 fuel fixes (all Hybrid).

## Baseline guard caught rewind #5

Pre-inventory check showed LEMON 12,637 (branch point) — recovered via `git reset --hard origin/...`
before any work; the script's baseline assert (LEMON=4,655) then passed.

## Method

Signals: cc + VIN (Accord CP2/CS1/CP3, Crosstour TF1/TF2, Pilot 3/4) + **lemon fuel column** +
trim slugs. The fuel column resolved every hybrid split:

| Signal | Resolution |
|---|---|
| Accord 2000cc Hybrid (2014-17, 2019-25) | **Honda 2.0 i-MMD Hybrid** (196-214hp system) |
| Accord 2000cc Petrol 2018 | **K20C4 2.0T 252hp** (motorreviewer) |
| CR-V 2000cc Hybrid 2020+ | 2.0 i-MMD 212hp system |
| Civic 1500cc Hybrid 2013-15 | Civic Hybrid 1.5 IMA 110hp |
| Civic 2000cc Hybrid 2025 | Civic e:HEV 2.0 i-MMD 200hp (hybrid-only 2025) |
| CR-Z (all) / Insight (all) / Clarity | CR-Z 1.5 IMA / Insight gen1 1.0→1.3 IMA, 2010-14 LDA1, 2019-22 1.5 i-MMD / Clarity PHEV |

Web-verified codes: **R20Z1** = 155hp Civic/Accord 2.0 (motorreviewer; also HR-V 2023+ 158hp),
**K20C4** = 252hp 2018+ Accord 2.0T, **D17A2** = Civic 2001-05 (proxyparts registry).

**Cross-brand rebadge handled:** Passport 2000-2002 = **Isuzu 6VD1 3.2 V6** (Rodeo twin, 205hp) —
kept as its own row rather than a Honda J-code, per the standing physical-fact rule.

## Top mappings (311 total)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| J35Y Earth Dreams 3.5 (Pilot/Ridgeline/Odyssey/Passport 2016+) | 34 | | K24Z3 (Accord/Crosstour 2.4) | 10 |
| L15B7 1.5T (Civic/CR-V/Accord 2016+) | 26 | | CR-Z 1.5 IMA Hybrid | 10 |
| J35A9 (Pilot/Ridgeline 250hp) | 26 | | J35A8 (Odyssey 2011-17) | 10 |
| Honda 2.0 i-MMD Hybrid | 18 | | J35A6 (Odyssey/Pilot 06-10) | 9 |
| K24A1 (CR-V/Element 2.4) | 14 | | R20Z1 (Civic/HR-V 2.0) | 12 |
| J35Y1 (Accord V6 278hp) | 12 | | R18Z4 (HR-V 1.8) + K24W + L15B2 | 7+8+8 |

New engines (22): D16Y8, D17A2, B20Z2, R18Z1, R20Z1, K24W, K24Z9, K20C4, J30A1, H22A4, F20C1,
F22C1, L15B2, Isuzu 6VD1, Honda 2.0/1.5 i-MMD Hybrid, CR-Z 1.5 IMA, Civic Hybrid 1.5 IMA,
Insight 1.0/1.3 IMA, Clarity PHEV, J35Y. Row-fixes (13 — the DB's J35 rows carried junk labels):
J35A4 "CORVETTE"→Odyssey/Pilot 240hp, J35A6 "CORVETTE (corr.)"→244hp, J35A9 "CROWN ROYAL"→250hp,
J35A8 295→248hp, J35Z2→271hp, J35Y1 NULL→278hp, K24A1 "for engines without EGR"→CR-V/Element,
K24A4 190→160hp, K24Z7 188→205hp (Civic Si), R18Z4 "LUV"→HR-V, J30A4 "BASSARA"→Accord V6,
L15B7 NULL→190hp, LDA1 label widened. Fuel fixes: 52 → Hybrid.

## Step 22b — spec normalization

16 ESTIMATE overrides + 1 normalization + 29 power syncs + 11 NULL-power variant fills.
Spot-checks: J35 4.25L ✓ (4.5qt US), K24 4.16L ✓, R18 3.69L ✓, L15 3.59L ✓, F22C1 4.82L ✓ (5.1qt),
K24Z3 3.97L ✓ (4.2qt). **Result: 0 ESTIMATE among step-22 targets, 0 power mismatches, 0 orphans,
0 count mismatches.**

### Known limitations (accepted)

- Bare-row majority mappings noted (Accord 2.4 majorities 2002-17; CR-V/HR-V single-engine eras).
- Single rows cover tune families (L15B7 174-205hp across Civic/CR-V/Accord; R20Z1 155-158hp;
  J35Y 280hp across four nameplates; i-MMD 196-212hp systems).
- Clarity mapped to PHEV majority (Fuel Cell minority noted).

## Skipped by design (1)

CR-V 2025 bare — 1.5T vs hybrid unknown (cc rows carry the split).

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 10,143 | 9,852 (−311 retired LEMON rows, +22 new) |
| LEMON total (all brands) | 4,655 | **4,344** |
| Honda LEMON remaining | 312 | 1 (intentional skip) |
| ESTIMATE / orphans / count / power mismatches | 0 | **0** |

**Next batch (LEMON-count order): Mazda 303** → Cadillac 269 → Jaguar 258 → VW 237 → Infiniti 230 →
Dodge 207 → Buick 205 → Subaru 205 → … (~4,344 remaining across 34 brands).
