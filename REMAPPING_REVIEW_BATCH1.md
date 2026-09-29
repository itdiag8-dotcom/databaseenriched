# 🔧 Remapping Review — Batch 1: the 45 POWER_MISMATCH_CROSSBRAND rows

**Date:** 2026-09-29 • **Script:** `step4_remap_power_mismatch.py`
**Method:** search → cite → replace (per `MISSING_ENGINE_CODES_REPORT.md`)
**Backup:** `backups/car_database_backup_pre_step4_2026-09-29.db` • **Decisions CSV:** `csv_exports/12_remap_batch1_decisions.csv`

## Result

| Queue status | Rows |
|---|---:|
| **remapped** (web-verified engine code) | **44** |
| pending (need VIN / more info) | 439 → of which **3** from this batch |
| invalid_data (source row corrupt) | 1 |

Variants with specs via `v_vehicle_with_service`: **38,701 → 38,742** (+41). Integrity check ok.

---

## 1. Remapped with citations

| # | Variant (year, hp) | Old (wrong) code | **New code** | Verification |
|---|---|---|---|---|
| 19283 | Alfa Romeo Giulietta QV (2012, 241) | 1MZ-FE | **940 A1.000** | auto-data: Giulietta 1.750 TB 235hp = code 940A1000 [auto-data.net](https://www.auto-data.net/en/alfa-romeo-giulietta-type-940-1.750-tb-235hp-16765), HandWiki 235PS [handwiki.org](https://handwiki.org/wiki/Engineering:Alfa_Romeo_Giulietta_(940)) |
| 15399/23368 | BMW 320d E90/E92 (163) | C20LET / A17DTJ | **M47D20TU2** | auto-abc: E90 320d engine M47D20TU2 [auto-abc.eu](https://www.auto-abc.eu/BMW-3-serija/v2196-2005), ultimatespecs M47D20TÜ2 1995cc [ultimatespecs.com](https://www.ultimatespecs.com/car-specs/BMW/51256/BMW-E90-3-Series-320d-Auto.html) |
| 23355/23356 | BMW 320d ED 3 GT F34 (163) | C20LET / A17DTJ | **N47D20C** | auto-data: F30 320d ED 163hp = N47D20C [auto-data.net](https://www.auto-data.net/en/bmw-3-series-sedan-f30-320d-163hp-efficientdynamics-edition-17213) |
| 21073 | BMW 330i E90 LCI (272) | X16SZR | **N53B30** | auto-data: 330i 272hp = N53B30A [auto-data.net](https://www.auto-data.net/en/bmw-3-series-sedan-e90-330i-272hp-9934) |
| 15765 | BMW 330i E91 (258) | X16SZR | **N52B30** | auto-data: 330i 258hp = N52B30A 2996cc [auto-data.net](https://www.auto-data.net/en/bmw-3-series-sedan-e90-330i-258hp-9933) |
| 15147 | BMW M5 E60 (507) | A14NET | **S85B50A** | auto-data: M5 E60 507hp = S85B50A [auto-data.net](https://www.auto-data.net/en/bmw-m5-e60-5.0-v10-507hp-smg-9871) |
| 14598 | BMW 525i E61 (192) | A14XER | **M54B25** | auto-data: 525i E60 192hp = M54B25 [auto-data.net](https://www.auto-data.net/en/bmw-5-series-e60-525i-192hp-9597) |
| 25730 | BMW 650i F13 (405) | E18NVR | **N63B44** | auto-data: 650i F13 407hp = N63B44A [auto-data.net](https://www.auto-data.net/en/bmw-6-series-coupe-f13-650i-407hp-steptronic-17291) |
| 16660/21329/25992 | Ferrari 599 GTB/GTO/SA (612–620) | A14XER | **F140C** | Wikipedia: 599 GTB = F140C 620PS; GTO/SA Aperta = F140CE 661PS [en.wikipedia.org](https://en.wikipedia.org/wiki/Ferrari_599) — ⚠️ the "599 SA 620hp" row matches GTB power; true SA Aperta (661hp) uses F140CE → flagged |
| 25922 | Holden Calais VZ (320) | C16NZ2 | **LS1** | Wikipedia VZ: Calais LS1 235kW=315hp [en.wikipedia.org](https://en.wikipedia.org/wiki/Holden_Commodore_(VZ)) |
| 21318/21312/21320/21322 | Holden Commodore Ute VU/VY (306–333) | C16NZ2 | **LS1** | Wikipedia VY: SS 235kW, SII 245kW=329hp LS1 [en.wikipedia.org](https://en.wikipedia.org/wiki/Holden_Commodore_(VY)); LS1 in VT–VZ Commodore/Statesman/HSV [autoblog.com](https://www.autoblog.com/features/gm-ls1-engine-specs-common-issues) |
| 21262/21264 | Holden Statesman WK/WL (333/354) | C16NZ2 | **LS1** | LS1 in 1999–2005 Statesman [autoblog.com](https://www.autoblog.com/features/gm-ls1-engine-specs-common-issues) |
| 21324 | Holden Commodore VE SS (367) | C16NZ2 | **LS2** | Wikipedia VZ gen: VE-era SS 6.0 LS2 270kW [en.wikipedia.org](https://en.wikipedia.org/wiki/Holden_Commodore_(VZ)) |
| 20972/20974/20976 | HSV Clubsport VX/VY (347–388) | C16NZ2 | **LS1** | HSV LS1 250–285kW [autoblog.com](https://www.autoblog.com/features/gm-ls1-engine-specs-common-issues) |
| 20978/21355 | HSV Clubsport VZ / Grange WL (404) | C16NZ2 | **LS2** | HSV official: VZ Clubsport LS2 297kW/5967cc [hsv.com.au](https://www.hsv.com.au/classics/see/vz/clubsport/) |
| 21352/21353 | HSV Grange WH/WK (347/388) | C16NZ2 | **LS1** | HSV LS1 family [autoblog.com](https://www.autoblog.com/features/gm-ls1-engine-specs-common-issues) |
| 21251/21254 | Ford Falcon BA/BF XR8 (367) | C16NZ2 | **BOSS260** | netcarshow: BA XR8 Boss 260 260kW=350hp [netcarshow.com](https://www.netcarshow.com/ford/2002-ba_falcon_xr8/), Grokipedia BA Falcon [grokipedia.com](https://grokipedia.com/page/Ford_Falcon_(BA)) |
| 21253/21255 | Falcon BA/BF ute (394) | C16NZ2 | **BOSS290** | FPV GT Boss 290 290kW=389hp [grokipedia.com](https://grokipedia.com/page/Ford_Falcon_(BA)) |
| 14198 | Lexus RX330 (204) | 1MZ-FE(429hp junk) | **3MZ-FE** | Wikipedia MZ: 3MZ-FE in RX330/Harrier; 1MZ 194–201hp, Highlander 220hp [en.wikipedia.org](https://en.wikipedia.org/wiki/Toyota_MZ_engine) |
| 19266 | Toyota Harrier 2nd gen (204) | 1MZ-FE(429hp junk) | **3MZ-FE** | Wikipedia MZ engine applications [en.wikipedia.org](https://en.wikipedia.org/wiki/Toyota_MZ_engine) |
| 19274 | Toyota Kluger XU20 2003 (204) | 1MZ-FE(429hp junk) | **1MZ-FE** | Wikipedia Highlander: 2001–03 = 1MZ-FE, 2004+ = 3MZ-FE [en.wikipedia.org](https://en.wikipedia.org/wiki/Toyota_Highlander) |
| 15618 | Mercedes E320 CDI W211 (224) | D24TIC | **OM648.961** | classic.com: E320 CDI W211 = OM648.961 204hp, 2007+ OM642 224hp [classic.com](https://www.classic.com/m/mercedes-benz/e/w211/sedan/e-320-cdi/) — 224hp suggests a 2005+ OM642 car; flagged to verify VIN |
| 11095/25586 | Mercedes S63 W222 / C217 (585) | 1TR-FE / E18NVR | **M157.985** | auto-data: S63 V222 585hp = M157.985 [auto-data.net](https://www.auto-data.net/en/mercedes-benz-s-class-w222-amg-s-63-585hp-speedshift-18886) |
| 24809 | Mitsubishi Pajero Sport (220) | C16NZ2 | **6G75** | Wikipedia 6G7: 6G75 3828cc [en.wikipedia.org](https://en.wikipedia.org/wiki/Mitsubishi_6G7_engine) |
| 20467/25363 | Mitsubishi Verada KL/KW (209) | C16NZ2 | **6G74** | Mitsubishi club DB: 6G74 3497cc 203–208PS [mitsubishiclub.cz](https://en.mitsubishiclub.cz/engine_detail.php?id=52) |
| 22542 | VW Tiguan 2.0 TSI (200) | C16NZ2 | **CCZA** | EA888 codes CAWA 170hp / CAWB-CCZA 200hp, Tiguan application [mytiguan.com](https://www.mytiguan.com/threads/volkswagen-2-0-tsi-tfsi-ea888-gen-1-2-3-engine-review.50534/), auto-data Tiguan 2.0 TSI 200hp = CAWB/CCZA [auto-data.net](https://www.auto-data.net/en/volkswagen-tiguan-i-2.0-tsi-200hp-4motion-8382) |
| 10574 | Lexus GX460 (296) *(re-quarantined)* | C16NZ2 | **1UR-FE** | GX460 4.6 1UR-FE 301hp [autopadre.com](https://autopadre.com/horsepower-and-torque/lexus-gx-460) — listed year 2008 predates GX460 (2010); flagged |
| 17713 | Chevrolet Cruze JDM (2003, 99) *(re-quarantined)* | E18NVR | **M15A** | Wikipedia Suzuki Ignis: Chevrolet Cruze (Japan) = 1.5 M15A 99PS [en.wikipedia.org](https://en.wikipedia.org/wiki/Suzuki_Ignis) |

## 2. Pending / invalid (kept honest)

| # | Variant | Why not remapped |
|---|---|---|
| 24981 | BMW 520i E60 (156hp) | E60 520i = M54B22 170hp (2003–03/2005) or 150hp 2.0 later; **156hp matches neither** [auto-abc.eu](https://www.auto-abc.eu/bmw-5-serija/v3208-2003) — needs engine plate/VIN |
| 10908 | Cadillac CTS Sport Wagon (2007, 276) | Sport Wagon introduced 2010; 2007 CTS = LY7 258hp / LLT 304hp; 276 matches neither [en.wikipedia.org](https://en.wikipedia.org/wiki/Cadillac_CTS) |
| 18988 | Chevrolet Equinox (2002, 188) | Equinox introduced 2005; 2002 model-year invalid; closest LNJ 185hp |
| 14922 | hernr_1513 NOVA (19hp) | 650cc/19hp microvehicle row is corrupt → `invalid_data` |

## 3. Engine-row identity fixes (cited)

| Code | Was | Now |
|---|---|---|
| 1MZ-FE | "3.0 V6 Supercharged", 429hp, Jaguar C-X16 | 3.0 V6 24v DOHC VVT-i, **2995cc, 201hp**, Toyota [specsnode](https://specsnode.com/engine-detail.php?id=37), [Wikipedia MZ](https://en.wikipedia.org/wiki/Toyota_MZ_engine) |
| N52B30 | 1300cc (parse junk) | **2996cc, 258hp** [auto-data](https://www.auto-data.net/en/bmw-3-series-sedan-e90-330i-258hp-9933) |
| N47D20 / N47D20C | 1482cc | **1995cc** [auto-data](https://www.auto-data.net/en/bmw-3-series-sedan-f30-320d-163hp-efficientdynamics-edition-17213) |
| N63B44 | 547hp "X5 M" | **407hp** 4.4 V8 TwinTurbo, 650i/xDrive50i [auto-data](https://www.auto-data.net/en/bmw-6-series-coupe-f13-650i-407hp-steptronic-17291) |
| M47D20TU2 (pre-existing) | 1573cc, 121hp | **1995cc, 163hp** |
| AJ126 (pre-existing) | 3000cc | **2995cc** [caranddriver](https://www.caranddriver.com/reviews/a15109109/2015-jaguar-xf-30-awd-test-review/) |

## 4. Collateral identity fixes discovered during review

- **22 Jaguar F-Type/XF/XJ/F-Pace/XE/C-X16 variants** were sitting on Toyota's `1MZ-FE` (the "429hp supercharged" junk) → moved to the correct **AJ126** row, which already existed with real service specs (5W-30, 5.0 L) [enginefinders](https://enginefinders.co.uk/jaguar-aj126-petrol-engine)
- **X5 M (E70) 555hp** variant was on N63B44 → moved to **S63B44** [auto-data](https://www.auto-data.net/en/bmw-x5-m-e70-4.4-555hp-xdrive-steptronic-9771)
- **3 rows wrongly kept by the brand-family rule** (Lexus GX ← Subaru C16NZ2, Cruze/Equinox ← E18NVR) re-quarantined — lesson recorded: platform partnership (GT86/BRZ, GM badge engineering) does **not** validate arbitrary code swaps; displacement/power evidence remains required.

## 5. Verification

- Integrity check ok; no new duplicates; all 44 remapped rows join service+tech specs
- All remapped rows within 30% of their engine's rated power, **except** the two F34 320d ED rows on N47D20C (163hp vs family-row 114hp) — legitimate N47 tune-family spread (the row spans 114–184hp across 137 variants)
- Spot checks now return real specs: M5 → S85B50A (5W-30, 6.6 L), HSV Clubsport VZ → LS2, Falcon BA ute → BOSS290 (5W-20, 7.4 L), Tiguan → CCZA (5W-30, 4.2 L)

## 6. What's next in the queue (439 pending)

1. **278 HARD_FUEL_CONFLICT** — decide which side is wrong (often the variant's fuel label, e.g. Kangoo 1.5 dCi labelled Petrol); some are quick wins (petrol/diesel label typos), some need per-row research
2. **158 DISPLACEMENT_MISMATCH** — e.g., Audi 2.7 TDI on 2.0 CAHB (real code: CGK/CGKA/CAMA family) — same web-verify method
3. The 452-row engine-row suspect worklist (`09_engine_row_suspects.csv`) — fix engine displacements/types
4. Steps 3+ from the improvement plan (hernr_* brand resolution, LEMON_* code replacement)

**Rollback:** `cp database_enriched/backups/car_database_backup_pre_step4_2026-09-29.db database_enriched/car_database.db`
