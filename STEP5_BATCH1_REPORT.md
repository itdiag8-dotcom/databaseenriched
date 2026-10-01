# STEP 5 — LEMON Synthetic Engine-Code Replacement — BATCH 1 (US Trucks / Full-Size SUVs / Vans)

**Date:** 2026-09-29 · **Script:** `step9_step5_lemon_replacement.py` · **Backup:** `backups/car_database_backup_pre_step9_2026-09-29.db`
**Decisions log:** `csv_exports/17_lemon_replacement_decisions.csv` (one row per variant, with evidence key)

## Summary

| Metric | Value |
|---|---|
| LEMON variants before | 12,637 |
| **Variants remapped to real OEM codes** | **1,885** (Ford 633, Chevrolet 531, GMC 457, Dodge 96, Ram 95, Cadillac 45, Lincoln 28) |
| LEMON engine rows retired | 1,885 (1:1 with variants) |
| New real engine rows created | 47 (`data_confidence='STEP9_VERIFIED'`) |
| Variant fuel labels corrected (Petrol→Diesel) | 279 |
| In-scope rows deliberately skipped (insufficient signal) | 97 (full list below) |
| LEMON variants remaining (batch 2+) | 10,752 |
| Engines table | 17,919 → 16,081 |
| `v_vehicle_with_service` coverage | 39,086 (unchanged — all migrated specs preserved) |
| FK integrity | 1 pre-existing orphan (Rolls-Royce PARK WARD → `M73B54`, from an earlier step; not introduced here) |

## Method

Because lemon.dogeware.me is dead with zero Wayback snapshots, identity was reconstructed from
**DB-internal signals** (displacement `CC`, 8th-VIN character, year, fuel, and the 2015 trim-suffix
codes) cross-checked against **web references**. The lemon source itself encodes the 8th VIN
character (`VINx`), which is the deterministic OEM engine identifier for US trucks. Where
(displacement, year, model) is unique, displacement alone decides. Mapping rules live in
`decide()` in the script; every rule carries an evidence key (below).

The crawled LEMON fluid/technical data was **migrated onto the real codes** (merge-fill of NULL
fields into existing spec rows, else rename), preserving `oil_spec_source`/`coolant_source`
provenance. Example: `L83` now carries 0W-20 / 7.57 L w-filter / DEX-COOL 15.99 L from the
Silverado 5.3 crawl rows.

## Citations (evidence keys)

| Key | Source |
|---|---|
| LS | https://en.wikipedia.org/wiki/General_Motors_LS-based_small-block_engine (LM7/L59/LM4/L33/LQ4/LQ9/LY5/LC9/LMG/L76/LY6/L96/LFA/LZ1/LMF/LH8/LH9/L83/L8B/L82/L84/LV3/LV1/L92/L9H/L8T applications & VIN codes) |
| DURAMAX | https://en.wikipedia.org/wiki/Duramax_V8_engine (LB7/LLY/LBZ/LMM/LML/LGH/L5P years; LGH VIN L, LML VIN 8, L5P engine code Y) |
| VINCHART | https://www.silveradosierra.com/threads/which-engine-is-in-my-silverado-or-sierra.743113/ (VIN C=L82/L83, D=L84, R=L8B, K=L3B, T=LM2, 7=L8T, J/L=L87, 3/7=LC9) |
| LMG0 | https://carpartplanet.com/engines/chevrolet/silverado_1500/2009/5.3l-vin-0-8th-digit-opt-lmg (VIN 0 = LMG) |
| L84D | https://carpartplanet.com/engines/chevrolet/silverado_1500/2019/new-style-mirrors-mount-on-door-skin-5.3l-opt-l84-vin-d-8th-digit (VIN D = L84) |
| L96G | https://carpartplanet.com/engines/chevrolet/silverado_2500/2016/6.0l-gasoline-vin-g-8th-digit-opt-l96 (VIN G = L96 ⇒ VIN B = LC8 by elimination for those years) |
| COLORADO / CANYON | https://gmauthority.com/blog/gm/chevrolet/colorado/ , https://gmauthority.com/blog/gm/gmc/canyon/ (LK5/L52/LLV/LLR/LH8/LH9/LCV/LFX/LGZ/LWN by year) |
| GMA19 | https://gmauthority.com/blog/2018/04/2019-silverado-engines-power-and-torque-ratings-revealed/ (L84/L87 ratings) |
| MODULAR | https://en.wikipedia.org/wiki/Ford_Modular_engine (Triton family, displacements) |
| SUPERDUTY | https://en.wikipedia.org/wiki/Ford_Super_Duty (2005 3V 5.4 300 hp & V10 362 hp; 2008–2010 table) |
| V10 | https://www.dieselhub.com/gas/ford-6.8-triton-v10.html (V10 2V→3V 2005; E-series 2V through 2019; commercial through 2019) |
| F150VIN | https://engineoiljournal.com/ford-f150-vin-engine-code-chart/ (F-150 VIN table 2015–2020 / 2021+) |
| VEHQ | https://vehq.com/how-to-tell-what-engine-is-in-my-ford-f150/ (2021+ F-150: G 3.3, P 2.7, F 3.5EB, D PowerBoost, T 5.0, J 5.2, 1 3.0D) |
| F150LAB | https://f150lab.com/how-to-tell-what-engine-is-in-my-ford-f150/ (VIN 5 = 5.0L-4V 2018+; VIN 8 = 3.5 NA Cyclone) |
| FORDVIN | https://fordmasterx.com/ford-vin-number-decoding-chart/ (F = Coyote ’11–’17, G = 3.5 EB, P = 2.7, D = PowerBoost) |
| NAVIGATOR | https://en.wikipedia.org/wiki/Lincoln_Navigator (98–02 InTech DOHC 300 hp; 03+ 5.4 3V SOHC 300 hp) |
| RAMVIN | https://truckguider.com/dodge-ram-engine-codes-by-year-chart/ (X 3.9, Y 5.2, Z 5.9, 6/C 5.9 Cummins, K 3.7, N/P 4.7, 2 5.7 HEMI, A 6.7 Cummins) |
| RAM14 | https://www.ramtrucks.com/assets/pdf/brochures/14MY_Ram_Commercial_eBrochure.pdf (6.4 HEMI available 2014 HD) |
| RAMOIL | https://www.jcofontario.com/service-department/service-and-parts-tips/ram-2500-oil-type/ (5.7 std 2011–2018; 6.4 2014+; sole gas 2019+) |
| LEMON2015 | `lemon_crawl_2015.jsonl` primary crawl (F-150: 2.7 VIN P / 3.5 VIN 8 NA / 3.5 VIN G EB / 5.0 VIN F; E-series: 5.4 VIN L / 6.8 VIN S; 5.7 VIN T HEMI; 3.6 VIN G Pentastar; 2.4 VIN B = Eng CD ED6) |

## Target codes assigned (top)

6.7 Power Stroke 85 · 6.8 Triton V10 2V 81 · 5.4 Triton 2V 76 · 3.5 V6 EcoBoost 75 · L83 57 ·
L96 55 · L18 51 · LM7 49 · LQ4 47 · 6.0 Power Stroke 41 · LU3 39 · 6.7 Cummins ISB 38 · L20 37 ·
ESA (6.4 HEMI) 36 · L87 36 · 6.2 Boss V8 35 · L84 35 · LC8 33 · 4.6 Triton 2V 33 · LR4 32 ·
7.3 Godzilla V8 32 · L86 31 · LGH 31 · 5.4 Triton 3V 30 · LC9 30 · LCV 28 · L3B 28 · EZH 27 ·
6.8 Triton V10 3V 27 · LY6 27 · 7.3 Power Stroke 27 · L9H 25 · LWN 24 · LMM 23 · LY2 21 ·
3.7 Ti-VCT V6 19 · 3.5 Cyclone V6 18 · LGZ 18 · LY5 18 · LZ0 17 … (full table in decisions CSV)

## Fuel-label corrections (279 rows)

Lemon labeled diesel engines as "Petrol" on many rows. All of these engines are diesel-only in
the given applications, so the variant fuel was set to Diesel together with the remap:
6.0/6.4/6.7/7.3 Power Stroke, 6.7 Cummins ISB, LGH/LML/L5P Duramax (incl. VIN Y rows), LM2/LZ0
3.0 Duramax, LWN 2.8 Duramax, EXL 3.0 EcoDiesel. The engine rows were created/fixed with
fuel='Diesel' (incl. pre-existing L5P row).

## Deliberately skipped in-scope rows (97) — need human/extra evidence

| Group | Rows | Reason |
|---|---|---|
| F-150 3.5L no-VIN 2015-17 / 2021+ | 7 | NA Cyclone vs EcoBoost vs PowerBoost indistinguishable |
| F-150 3.5L VIN 4 (2019-20), VIN 8 (2018+) | 4 | VIN identity unverified across conflicting charts |
| Silverado/Sierra 5.3 no-VIN 2019-2021 | 3 | L82 vs L84 ambiguous |
| Silverado/Sierra 5.3 VIN F 2022 | 2 | Sources conflict: L82 vs L84 |
| Silverado/Sierra 6.0 VIN J 2012 | 2 | Identity unverified |
| Escalade bare 2002-2006 | 6 | 5.3 LM7 (2WD) vs 6.0 LQ9 (AWD) |
| Yukon bare 2016-2018 | 5 | 5.3 L83 vs Denali 6.2 L86 |
| Expedition bare 2005-2010 | 6 | 4.6 vs 5.4 |
| Expedition 5.4 2003-2004 | 2 | 2V vs 3V unverified |
| Ram HD gas bare 2014-2018 | (within 2500/3500 skips) | 5.7 vs 6.4 both offered [RAMOIL] |
| Dodge Pickup/Cab 5.9 Petrol 2004-2006 | 8 | 5.9 gas ended 2003 — fuel/code conflict, left as-is |
| GM 4.3 2000-2001 (L35 era) | 6 | LU3 start 2002 unverified for those years |
| GM 6.5 2000-2002 (9 rows, Petrol label) | 10 | 6.5 = diesel; identity/era unverified |
| E-series/Cutaway/E450/Excursion/Savana/Cutaway-RV bare rows | ~20 | no displacement/VIN signal |
| Silverado/Sierra bare 2019/2024/2025 | 6 | multiple engines |
| Transit-350 3.5 no-VIN 2015, ProMaster oddments | 2 | ambiguous |

## Notable mapping decisions

- **VIN B vs VIN G 6.0 (2012-2019):** VIN G = L96 confirmed [L96G]; VIN B mapped to LC8 (CNG
  bi-fuel) by elimination — the DB already holds both LC8 and L96 for those exact years from the
  xlsx source.
- **5.3 VIN R (2016-2018)** = L8B eAssist mild hybrid [VINCHART + LS L8B applications].
- **Express/Savana 4.3 VIN P (2018+)** = LV1 (van-specific EcoTec3, successor to L20) [LS].
- **E-series V10 = 2V in all years** (incl. VIN S), while Super Duty/chassis V10 = 3V from 2005
  [V10]; SD 5.4 split 2V (≤2004) / 3V (2005+) [SUPERDUTY]; F-150 5.4 3V from 2004 [MODULAR].
- **2023+ SD 6.8 VIN A** = 6.8 Godzilla; **7.3 VIN N/K 2020+** = 7.3 Godzilla; E-350/E-450 got
  the 7.3 from 2021.
- **Engine-row fixes** on existing rows: LFA `engine_type` junk → "6.0 V8 hybrid (two-mode)";
  L18 junk → "8.1 V8 Vortec"; L5P fuel → Diesel; L8T specs filled (6,564 cc / 401 hp).
- **L83 was absent** from the engines table (L82/L84 existed) — created with cited specs.

## Remaining LEMON inventory (batch 2 candidates)

10,752 rows: passenger cars & crossovers (Mustang, Charger/Challenger, 300, Camaro, Corvettes,
German/Japanese/Korean brands), SUVs (Grand Cherokee, Durango, Wrangler, Explorer, Edge, Escape…),
Ram 1500 bare (69), Transit/Transit Connect, Dakota, Sprinter, plus the 97 skipped above.
Priority by volume: Ford 743 remaining, Chevrolet 653, Mercedes-Benz 968, BMW 780, Audi 576,
Nissan 520, Toyota 471 …
