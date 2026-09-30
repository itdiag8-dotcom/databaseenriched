# STEP 5 — Batch 16: Jaguar LEMON Replacement (step25 / step25b)

**Date:** 2026-09-30 · **Scope:** 258 `LEMON_JAGUAR_*` variants, 19 models, MY2000–2025
**Result:** **246 mapped / 12 skipped** · LEMON total 3,781 → **3,535** · engines 9,306 → **9,065**
Verification: 0 orphan refs, 0 count mismatches, 0 ESTIMATE specs, 0 spec-power mismatches.

## Signals used
- Displacement marker (`2000CC/3000CC/5000CC`) + **VIN engine letter** (8th char: `VING/VINN/VINX/VINV/VINU/VIN7/VINZ/VIND/VINB/VINE/VINT/VINC/VINH/VINP/VIN6/VIN7`) + year + model name.
- 2015 lemon crawl (`lemon_crawl_2015.jsonl`) decodes the letters via trim names: F-Type Base 3.0 **VIN 7/T = 340hp**, S **VIN C/U = 380hp**; XF Supercharged 5.0 **VIN E/P**; XFR **VIN C/H**; XJ 3.0 **VIN 7/Z RWD, D AWD**.
- youcanic VIN table: **N = F-Pace turbo diesel**, V = F-Pace US 3.0.

## Engine genealogy (web-verified)
- **AJ-V8 eras:** AJ26→**AJ27** (4.0 NA 290hp, 1998+, X308/X100) → **AJ33/DB-AJ34** (4.2 NA 294-300hp) → 5.0 Gen III (**AJ133** family: NA 385, SC 510/550/575) — one row per code, variants carry per-tune power.
- SC lineage: **AJ27S** 4.0 SC 370hp (XKR/XJR 2000-03 — DB-convention code, AJ33S pattern; Wikipedia documents the Eaton-blown 4.0 without an official suffix) → **AJ33S** 4.2 SC 390-420hp → **AJ133/AJ133S** 5.0 SC (XFR 510, XKR 510, R-models 550, XJR575/SVR 575).
- **AJ126** 3.0 SC V6 340/380hp (XE/XF/XJ/F-Type/F-Pace) — 61 rows, largest target.
- **2.0 Ingenium:** `204PT` (Si4) spans Ford-GTDI 240hp (XF 2013-15, XE 2017 — Wikipedia XE: "Ford EcoBoost until 2017") and Ingenium P250/P300 247/296hp (2018+) — 38 rows; `204DTD` new (20d diesel 180hp, 9 rows, fuel fix).
- **AJ300P** new: 3.0 I6 MHEV twin-turbo + e-supercharger (P340 335 / P400 395hp) — replaced the SC V6 in the F-Pace for 2021 (MotorTrend/ConsumerGuide), 7 rows.
- **I-Pace Electric** new: EV-only model, 394hp (6 rows, fuel fix).

## US-lineup findings (drove the mapping)
- **XE:** Ford EcoBoost 2.0 (25t, VIN G) until 2017, Ingenium 2018+; 20d diesel 2017-19 (dropped 2020 per cars.com); 35t V6 through 2019.
- **XF X260:** 2016 = 3.0 340 only; 20d diesel 2017-19 (fueleconomy.gov + C/D test — Wikipedia's "no US diesel" claim is wrong); 2018 added 25t 247 + 30t 296; 2021+ = P250/P300 four only (JD Power).
- **F-Pace:** 2017 = 20d/35t 340/S 380; 2018 + 25t (conceptcarz 18MY trio); 2021 = I6 MHEV replaces V6, 2.0 = P250-only; SVR 550 → 542 (2024) → 567hp (2025).
- **Bare 2.0 rows 2018-19 = 30t 296hp gas by elimination** (N=diesel, X=P250, and 2021+ X-rows must be P250) — never ambiguous on fuel.
- **X-Type:** 2.5 + 3.0 both sold 2002-04 (KBB/Consumer Guide; 2.5 dropped for 2005) → 2005-08 = 3.0-only.

## Skips (12, intentional)
- **S-Type 2000-08 ×9:** 3.0 V6 (AJ30) vs 4.0/4.2 V8 both US-offered every year; rows carry no engine marker.
- **X-Type 2002-04 ×3:** 2.5 (AJ25) vs 3.0 (AJ30) both US-offered.

## Targets (246)
AJ126 ×61, AJ133 ×55, 204PT ×38, AJ133S ×22, AJ34 ×15, AJ33S ×13, 204DTD ×9, AJ27 ×9,
AJ300P ×7, AJ27S ×7, I-Pace Electric ×6, AJ30 ×4.
Row-fixes (labels): AJ133, AJ133S, AJ126, AJ33S, AJ34, AJ30, 204PT.
Fuel fixes: 9 → Diesel (204DTD), 6 → Electric (I-Pace).

## step25b spec normalization
7 ESTIMATE overrides + 1 normalization + 5 power syncs. **All values audited and externally verified:**
- 204PT 0W-20/7.0L (Ingenium petrol; costaoils: 7.4qt/7.0L; 30-page vote vs 4 Ford-GTDI 5W-30/5.39L)
- AJ126 0W-20/7.23L (crawl F-Type 7.65qt; AMSOIL corroborates code "V" = 3.0 SC V6)
- AJ133 5W-20 / AJ133S 0W-20, 7.23L (crawl XFR-S/XJR: 0W-20 primary, 5W-20 alternative)
- AJ300P 0W-20/9.08L (blauparts: 2021-23 F-Pace L6 = 9.0L/9.5qt)
- 204DTD 0W-30/6.43L (blauparts: STJLR.03.5007 0W-30 USA 2.0 diesel)
- AJ27 5W-30/6.52L, AJ27S 5W-30/5.86L, AJ30 5W-30/5.77L, AJ33S/AJ34 5W-30/7.76L (lemon majorities)

## Incidents
- **8th full workspace rewind** caught by the baseline assert pre-work (branch-point signature 12,637/17,916); recovered via `git fetch && git reset --hard origin/arena/01a0ee59-databaseenriched`, no loss.
- Fixed 3-tuple vs 4-tuple unpack bug in decide() skip branches pre-dry-run.

## Next
Volkswagen 237 → Infiniti 230 → Dodge 207 → Buick 205 → Subaru 205 → Land Rover 194 (note: DB's
306DT Lion-diesel row carries junk label "3 (est.)" and AJ200/AJ41 Land Rover vocabulary — fix in LR batch).
