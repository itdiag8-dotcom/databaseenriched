# Step 5 — Batch 4 Report: Mercedes LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step13_step5_lemon_batch4_mercedes.py` (+ `step13b_estimate_override.py`, `step13c_conflation_fixes.py`)
**Backups:** `database_enriched/backups/car_database_backup_pre_step13_2026-09-30.db` (pre-step-13) and `…_pre_step13c_2026-09-30.db` (pre-step-13c)
**Decisions log:** `database_enriched/csv_exports/21_lemon_batch4_decisions.csv` (per-variant, with evidence — updated in place by step 13c)

Per the user-selected LEMON-count order (biggest brand first), batch 4 = **every remaining LEMON
Mercedes variant** (968 rows, model years ~2000–2024, 149 trim bases).
**931 variants remapped, 37 skipped** (documented below), 931 LEMON codes retired,
23 + 1 new engine rows, 76 fuel fixes.

## Method — different from batches 1–3

Ford/Mopar batches keyed rules on **VIN 8th char + cc**. Mercedes LEMON codes are **US trim
names** (C300, E350, S600, C63 AMG…) with no cc or VIN signal, so rules are keyed on
**(trim base, year range) → engine code**, refined by 4MATIC/BASE slugs and fuel inside
`decide()`. Every generation split was verified against the web (7 research passes covering
C/E/S generations, ML/GLE/GL/GLS SUVs, compacts, roadsters, Sprinter/Metris vans, coupés,
G-Class, AMG GT, EQB/EQS). The **Wikibooks Mercedes VIN/engine table** was the primary
per-trim evidence; ~30 sources are embedded in the script's `CIT` dict and the decisions CSV.

### Key generation facts established (cited)

| Trim | Engine timeline | Evidence |
|---|---|---|
| C300 | W204 3.0/3.5 V6 (M272/M273) → 2015.5+ W205 2.0T **M274.920 241hp** → 2022 W206 M254 | FCP W205 guide, Wikibooks |
| C63 | M156 6.2 NA → 2015 **M177** 4.0TT → 2024 W206 **M139 PHEV 671hp** | handwiki W206, FCP |
| E350 | M272 3.5 NA → 2012 M276 3.0TT → 2018 **M264** 2.0T | handwiki W213, mbworld |
| E450 | 2019+ **M256** I6 mild-hybrid 362hp | handwiki W213 |
| S550 | M273 5.5 → 2010+ M278 4.7TT | carbuzz S-class generations |
| S600 | M137 5.8 V12 → M275 5.5TT → W222 **M277** 6.0TT | carbuzz, Wikibooks |
| A/CLA/GLA/GLB 250 | M270 (–2018) → 2019+ **M260** | Wikibooks, DB cross-ref |
| GLE450/GLS450/E450/S450 3.0TT | M276.823/820 V6 (2013–18) → 2019+ **M256** I6 | motorreviewer, mbworld |
| G550 | M273 5.5 → 2017 **M176** 4.0TT → 2025 M256 443hp | Wikipedia G-Class |
| Sprinter | OM642 3.0 (–2022 gas excluded), OM651 2.1, 2023+ **OM654** 168/208hp | Wikipedia Sprinter |
| Metris | **M274.920 van tune 208hp** (8 qt sump!) | AMSOIL 274.920, Wikiwand M274 |
| EQB/EQS | EQB300 225 / EQB350 288 / EQB250+ 190 / EQS450+ 329hp electric | mbusa.com |

## Top mappings (931 total)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| M177.980 (C63 4.0TT) | 46 | | M276.820 (3.0TT V6) | 24 |
| M273.965 (5.5 V8) | 33 | | M157.980 (5.5TT 577) | 24 |
| M275KE60LA (6.0TT V12) | 32 | | M157.981 (5.5TT 550) | 24 |
| M176 (G550 4.0TT) | 29 | | M113E55ML (E55 SC) | 24 |
| M275KE55LA (5.5TT V12) | 29 | | M156.980 (6.2 NA AMG) | 22 |
| M276.823 (3.0TT) | 27 | | M264 2.0T | 21 |
| M256 3.0 I6 Turbo | 27 | | M260 2.0T | 19 |
| M278.922 (4.7TT) | 26 | | OM642.940 (Bluetec SUV) | 20 |

New engines created (23 + 1): M256 / M256 AMG (53) / M254 / M264 / M260 / M260 AMG (35) /
M139 43-series / M139 AMG (45) / M139 PHEV (C63) / M176 / M178 (GT) / M152 / M137 / M155 (SLR) /
M113.943 / **M274.920 (Metris)** / M276 3.0 PHEV / M274 PHEV (C350e) / OM654 '654' /
EQB250+ / EQB300 / EQB350 / EQS450+ / W242 Electric (B250e).
Fuel fixes: 76 (Diesel 52, Hybrid 12, Electric 12).

## Step 13b — ESTIMATE override

60 of 83 spec rows on step-13 targets still carried batch-1-era ESTIMATE heuristics (5W-40
petrol / 5W-30 diesel). `step13b_estimate_override.py` recovered the trusted lemon-crawl values
(oil capacities are genuine qt→L conversions — verified against MB specs, e.g. ML350 8.5qt→8.04L,
Sprinter OM642 13.2qt→12.49L) from the pre-step-13 backup: **59 overridden, 1 left** (M276.824,
resolved in 13c below).

## Step 13c — conflation fixes (post-apply audit)

A systematic audit of every step-13 target against the variant-weighted lemon majority exposed
four issues, all fixed by `step13c_conflation_fixes.py`:

1. **Metris split.** AMSOIL + Wikiwand confirm the Metris is genuinely engine code **274.920**
   (208hp van tune), but its 8 qt / 7.57 L sump differs from the ~6.3 qt cars — one spec row
   can't serve both. Created a separate DB engine row **`M274.920 (Metris)`** (same convention as
   `M274 PHEV (C350e)`), moved 8 variants, power 208, oil 0W-30/7.57 L.
2. **S450 rule error (fixed).** W222 S450 2018–2020 = **M276.824 3.0 V6 BiTurbo 362hp**
   (AMSOIL engine-code lookup, CarBuzz W222 gen table) — *not* the M256 I6, which only arrived
   with the W223 S500 in 2021. 3 variants remapped M256 → M276.824.
3. **S560e power/fuel.** System output **469hp** (362 V6 + 121 e-motor, Car and Driver), fuel
   Hybrid, clean engine labels (the M276.824 row carried a garbage "3 (est.)" type).
   M276.824 spec row: ESTIMATE 5W-40/4.6 L → **0W-30 / 6.52 L (6.9 qt)** per AMSOIL — the last
   ESTIMATE among step-13 targets eliminated.
4. **Majority normalization.** Step-13's first-code merges left 14 targets with non-majority
   values (e.g. M113.943 7.47→8.04 L, M256 AMG 9.46→8.04 L, M273 GL450 8.51→8.99 L) and
   M274.920's spec row kept a stale Euro 211hp. All normalized to variant-weighted lemon
   majorities; 24 NULL/stale `power_hp` values in spec rows filled from `engines`.

**Known limitation (accepted, same as batches 1–3):** one spec row per engine code means
cross-model sump variation inside a code family (SUV vs sedan: M256 8.49 L SUV-majority vs
6.5 L sedans; AMG V8s ±0.5 L) is represented by the variant majority. Splits are only made
where the difference is material (van vs car) — per the standing rule that tune families
sharing one code are legitimate.

## Skipped by design (37)

- Bare **Sprinter** (2500, gas/diesel unknown) ×18 — US Sprinter 2500 came as both; no slug/fuel signal.
- **Maybach** base-trim unknown ×3; **C350 2015** ×2 (W204 V6 vs W205? transition); **C230 2000–02** ×2 (W202 M111 vs M104 ambiguity).
- 12 single-row ambiguities: C280 2000 (W202 M104?), S350 2006 (non-US), R350 2008 (gas/diesel split), E550 2017 (W212 vs W213 transition), SLK300/SLK55 2016, GLE450 2016, SL550 2020, GLA250 2020, CLA45 2019, C350 2015, GT 2024 (C192 trim ambiguity), etc.
- These stay on `LEMON_MERCEDES_*` codes until evidence resolves them (manual queue, not lost).

## Post-state (verified)

| Metric | Value |
|---|---|
| Engines | 13,908 |
| v_vehicle_with_service | 39,088 |
| LEMON remaining (all brands) | 8,525 |
| Mercedes LEMON remaining | 37 (intentional skips) |
| ESTIMATE among step-13 targets | **0** |
| Orphan variant→engine refs | 0 |
| count_variants mismatches | 0 |
| Spec rows missing for targets | 0 |
| engines↔specs power mismatches | 0 |

**Next batch (user-selected LEMON-count order): BMW 780** → Chevrolet 653 → Audi 576 →
Nissan 520 → Toyota 471 → Kia 392 → Hyundai 391 → Lexus 322 → Honda 312 → Mazda 303 → …
(43 brands, ~8,525 rows remaining).
