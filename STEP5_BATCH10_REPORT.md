# Step 5 — Batch 10 Report: Kia LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step19_step5_lemon_batch10_kia.py` (+ `step19b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step19_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/27_lemon_batch10_decisions.csv` (per-variant, with evidence)

Batch 10 in LEMON-count order = **every remaining LEMON Kia variant** (392 rows, 32 models,
MY2000–2025). **378 variants remapped, 14 skipped**, 18 new engine rows, 39 fuel fixes (Hybrid 32,
Electric 7).

## Incident: second full workspace rewind (9th), caught post-apply

After `--apply`, verification showed `engines 17,556 / LEMON 12,259` — the **branch-point DB**, not
the post-Toyota baseline (5,709). The sandbox had rewound again between turns; the apply had landed on
the wrong baseline. Recovery: `git fetch origin && git reset --hard origin/...` (restored the
committed post-Toyota DB) **and re-ran `--apply`** — Kia rows/IDs are identical in both baselines
(batches 3–9 never insert/delete variants), so the rerun was clean. Final verify confirmed the correct
state. Standing rule: **verify the baseline (LEMON total + engines count) before every apply.**

## Method

Signals: cc + **lemon fuel column** + 2015 trim slugs. The fuel column again resolved hybrids:

| Signal | Resolution |
|---|---|
| Optima 2400cc + Hybrid (2012, 2016) + 2011 bare Hybrid | **G4KK** — 2.4 Theta II GDI hybrid (2011-2016 system 199-206hp) [wikibooks VIN table] |
| Optima 2000cc + Hybrid (2017-2020, VIN C/D/E/F) | **G4NE** — 2.0 GDI hybrid (system 192hp) [DB-linked to Optima] |
| Optima 2000cc + Petrol | G4KF 2.0T |
| Sorento/Sportage/Carnival 1600cc + Hybrid | **Smartstream 1.6 T-GDI Hybrid** (system 227-242hp) |
| Niro (all years) | Kappa 1.6 GDI Hybrid (system 139hp) — EV/PHEV minority noted |

Web-verified codes: **G4NH** = Forte(17+)/Soul(20+)/Seltos/K4 2.0 MPi Atkinson 147hp (wikibooks +
go-parts); **G6DP** = 3.3 T-GDI 365hp (Stinger/K900 — motorreviewer + go-parts); **G4KK** = Optima
Hybrid 2.4 (wikibooks); **G4NA** = Soul 2.0 14-19 (parts listings); Rio 01-02 1.5 = Mazda **B5-DE**
(wikibooks).

**Code-collision handling:** the DB's `G6DA` is a Ford 2.0 TDCi code (Focus/C-Max links) — the real
Kia Lambda 3.8 MPi shares the same code, so it got a separate descriptive row
`Lambda 3.8 MPi (G6DA-family)` (Sedona/Amanti/Sorento/Borrego 244-275hp). Same pattern for other
Lambda/Tau rows (3.5 GDI, 3.3 GDI, Telluride 3.8 GDI, Tau 4.6/5.0) to avoid the DB's mislabeled G6
rows ("BLAZER S10", 2.0 TDCi junk labels).

DB-vocabulary reuse (verified via engine links): G6AU (Amanti/Opirus+ Sorento 3.5 Sigma), G6CU
(Sedona 3.5), G6BV (Optima 2.5), G6EA (Optima/Rondo/Sportage 2.7 Delta — junk label fixed), G4JS/G4KC
(2.4), G4KD/G4KE (Forte 2.0/2.4), G4KF (2.0T), G4KJ (2.4 GDI), G4NC (2.0 GDI), G4FD/G4FC/G4ED
(1.6/1.6GDI/1.6), G4GC/G4GB (2.0/1.8), G4FJ (1.6T), G4CP (Sportage FE 2.0), G6DJ (3.8 GDI → K900).

## Top mappings (378 total)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| Lambda 3.3 GDI (Sedona 15+/Sorento 14+/Cadenza) | 34 | | G4KC (2.4 MPi) | 16 |
| G4FJ (1.6T: Forte GT/Optima/K5/Seltos/Soul) | 31 | | G4NH (2.0 MPi 147) | 15 |
| G4KJ (2.4 GDI: Optima/Sorento/Sportage) | 31 | | Lambda 3.8 MPi (G6DA-family) | 14 |
| G4KF (2.0T: Optima/Sorento/Sportage/Stinger) | 26 | | G4ED (1.6 Rio/Rio5) | 12 |
| G4FD (1.6 GDI Rio) | 21 | | G4KN (2.5 GDI) + G4NE (hyb) | 11 + 11 |
| G6EA (2.7 Delta) | 19 | | G4GC (2.0 Beta) | 18 |

New engines (18): Lambda 3.8 MPi / II 3.5 GDI / 3.3 GDI / Telluride 3.8 GDI, Tau 4.6 + 5.0,
**G6DP** (3.3TT), Smartstream 2.5 T-GDI + 1.6 T-GDI Hybrid, Kappa 1.6 HEV (Niro), G4NB/G4NA/**G4NH**/
**G4KK**, 1.5 B5 (Rio), Soul EV + EV6 + EV9 Electric. Row-fixes: G4KN, G4NE, G6EA completed/relabeled.
Fuel fixes: 39 (Hybrid 32 — Optima hybrids, Niro ×9, Sorento/Sportage/Carnival HEV; Electric 7 —
EV6 ×3, EV9 ×2, Soul EV ×2).

## Step 19b — spec normalization

18 ESTIMATE overrides + 4 majority normalizations + 20 power syncs + 3 NULL-power variant fills.
Spot-checks: G4FD 3.59L ✓, G4FJ 4.49L ✓, Theta 2.4 4.25L ✓, 3.8 GDI 6.1L ✓, 3.5 GDI 5W-20/5.19L ✓.
**Result: 0 ESTIMATE among step-19 targets, 0 power mismatches, 0 orphans, 0 count mismatches.**

### Known limitations (accepted)

- Euro-power DB rows carry Euro figures with US values noted (G4KF 211 vs US 245-274; G6DJ 335 vs
  K900 US 311).
- Single rows cover tune families (G4KF 2.0T across Optima/Sorento/Sportage/Stinger; Smartstream 2.5T
  for K5 GT 290 / Stinger GT 300).
- Niro bare rows mapped to the HEV majority (EV/PHEV variants noted in evidence).

## Skipped by design (14)

Forte bare 2014-2016 ×4 (1.8/2.0/1.6T), Forte5 bare 2014/2016/2017/2018 ×4 (EX 2.0 vs SX 1.6T),
K5 2025 bare ×1 (1.6T vs 2.5T), Optima 2001 bare ×1 (2.4 vs 2.7), Soul bare 2016-2019 ×4
(1.6/2.0/1.6T).

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 11,172 | 10,812 (−378 retired LEMON rows, +18 new) |
| LEMON total (all brands) | 5,709 | **5,331** |
| Kia LEMON remaining | 392 | 14 (intentional skips) |
| ESTIMATE / orphans / count / power mismatches | 0 | **0** |

**Next batch (LEMON-count order): Hyundai 391** → Lexus 322 → Honda 312 → Mazda 303 → Cadillac 269 →
Jaguar 258 → VW 237 → Infiniti 230 → … (~5,331 remaining across 37 brands).
