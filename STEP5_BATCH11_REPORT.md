# Step 5 — Batch 11 Report: Hyundai LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step20_step5_lemon_batch11_hyundai.py` (+ `step20b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step20_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/28_lemon_batch11_decisions.csv` (per-variant, with evidence)

Batch 11 in LEMON-count order = **every remaining LEMON Hyundai variant** (391 rows, 23 models,
MY2000–2025). **385 variants remapped, 6 skipped**, 4 new engine rows, 4 fuel fixes (Electric).

## Baseline guard (rewind defense) worked

The pre-inventory check caught the **third full workspace rewind** (LEMON 12,637 / engines 17,916
instead of 5,331 / 10,812). Recovery: `git fetch && git reset --hard origin/...` — no work lost (all
batches committed+pushed). The script now **asserts the baseline (LEMON=5331) before doing anything**.

## Method

Signals: cc + **lemon fuel column** + trim slugs. The fuel column again did the heavy lifting:

| Signal | Resolution |
|---|---|
| Sonata 2000cc 2016-2025 (+VIN 1/3) all Hybrid | **G4NE** 2.0 GDI HEV (system 192-193hp); 2015 Petrol = 2.0T G4KF |
| Ioniq 2017-2021 Hybrid / 2022-2025 "Petrol" | HEV era → Kappa 1.6 HEV; 2022+ = **Ioniq 5/6 EV only** → new Electric row + fuel fix |
| Santa Fe 1600cc Hybrid / 2500cc Petrol (2021+) | 1.6T HEV (Smartstream row relabeled) / 2.5 GDI G4KN |

Web-verified: **US Tucson TL** = Nu 2.0 GDI 161-164hp (SE/Value) + Theta 2.4 GDI 181hp (SEL+) +
1.6T 177hp (Eco/Sport, 2016-2018) [hyundainews.com 2020 spec PDF, autoevolution]. Genesis logic:
2000cc = Coupe 2.0T only (sedan never had it), 4600/5000 = sedan Tau only, 2009 3.8 = sedan-only
(coupe launched 2010), 2015 coupe has its own slug, 2016 3.8 = sedan-only (coupe discontinued).

Heavy reuse of the DB G-family (G4GC/G6BA Tiburon-Coupe-linked, G4ED/G4FD Accent, G4JS Sirius,
G6CU/G6BV Sigma, G4NC Nu 2.0 GDI, G4KC→G4KJ Theta evolution) **plus rows created in batches 5-10**
(G4NB/NA/NH, Lambda/Tau family rows, G4KK/G4NE, Smartstream + Kappa HEV).

## Top mappings (385 total)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| G4KJ (2.4 Theta GDI) | 41 | | G4FD (1.6 GDI Accent/Veloster) | 23 |
| G4FJ (1.6T family) | 37 | | Lambda 3.8 MPi (Azera/Entourage/Veracruz/Genesis) | 18 |
| G4NH (2.0 MPi 147) | 35 | | G4KF (2.0T) + G4KN (2.5 GDI) + G4NE (HEV) | 14 + 13 + 11 |
| G4GC (2.0 Beta) | 24 | | G6DB (3.3 Lambda MPi, relabeled) | 12 |
| G6BA (2.7 Delta) | 24 | | G4NC (2.0 Nu GDI Tucson) | 8 |

New engines (4): G4LD (1.4T Eco), Sigma 3.0 (XG300), Lambda II 3.8 GDI (Genesis Coupe),
**Ioniq Electric** (35 EV engines now). Row-fixes (5 labels): G6DB junk "3.3" → full Lambda MPi label;
Tau 4.6 → include Equus/Genesis; Kappa HEV → include Ioniq; Smartstream 1.6T HEV → include Santa Fe;
Lambda 3.5 GDI → include Santa Fe. Fuel fixes: 4 (Ioniq 2022-2025 → Electric).

## Step 20b — spec normalization

4 ESTIMATE overrides + 12 majority normalizations + 4 power syncs. Spot-checks: Theta 2.4 4.25-4.29L ✓,
Nu 2.0 3.19-3.59L ✓, Delta 2.7 4.5L ✓, Tau 4.6 6.5L ✓, HEV 1.6T 0W-20/4.82L ✓.
**Result: 0 ESTIMATE among step-20 targets, 0 power mismatches, 0 orphans, 0 count mismatches.**

### Known limitations (accepted)

- Genesis Coupe 3.8 (2010-2014, 5 rows) skipped: sedan MPi vs Coupe GDI physically different, no signal.
- Bare rows mapped by majority with minority noted (Elantra 2.0, Santa Fe Sport 2.4, Veloster base,
  Sonata 2011/2012 2.4, Kona 2.0, Ioniq HEV-era).
- One suspicious row mapped with note: Tucson 2022 2500cc → 2.5 GDI (non-standard for US NX4).
- Euro-power DB rows keep Euro figures with US values noted (G4NC 176 vs US 164; G4KF 211 vs US 245-274).

## Skipped by design (6)

Genesis 3800cc 2010-2014 ×5 (sedan MPi vs Coupe GDI unknown) + Genesis 2016 bare ×1 (3.8 vs 5.0).

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 10,812 | 10,431 (−385 retired LEMON rows, +4 new) |
| LEMON total (all brands) | 5,331 | **4,946** |
| Hyundai LEMON remaining | 391 | 6 (intentional skips) |
| ESTIMATE / orphans / count / power mismatches | 0 | **0** |

**Next batch (LEMON-count order): Lexus 322** → Honda 312 → Mazda 303 → Cadillac 269 → Jaguar 258 →
VW 237 → Infiniti 230 → Dodge 207 → Buick 205 → … (~4,946 remaining across 36 brands).
