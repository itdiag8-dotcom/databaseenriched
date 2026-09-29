# 🏷️ Step 3 Report — `hernr_*` Brand Rebadging + Mis-Brand Fixes

**Date:** 2026-09-29 • **Script:** `step8_step3_brand_rebadge.py`
**Backup:** `backups/car_database_backup_pre_step8_2026-09-29.db` • **Decisions:** `csv_exports/16_brand_rebadge_decisions.csv`

## The mystery, solved

The 83 `hernr_NNN` brand buckets came from the **Vivid WorkshopData** source (`vivid_cars2000.db`, found in the repo root). Its `models` table carries `hernr` (Hersteller-Nummer) + `kmodnr` (TecDoc model number) — but the `brand` column was already broken to `hernr_NNN` at the source, so the names had to be reconstructed. Each bucket was identified from its **model lineup + engine codes**, then **web-verified** (citation per row below).

## Result

| | Before | After |
|---|---:|---:|
| Variants under `hernr_*` brands | 743 | **0** |
| Variants under `Citroën` / `Saic Mg` / `SATURN` / `SHELBY` / `Jmc` / `Volga` | 586 | **0** (renamed) |
| Brands | 188 | **236** (48 real manufacturers created) |
| Models | 6,299 | **6,281** (18 duplicate model rows merged) |
| NULL engine_code | 96 | **95** (Hummer H3 → L52 bonus remap) |
| Queue | 386 remapped / 95 pending | **387 / 94** |

Integrity ok • no hernr remnants in variants/models/engines/queue • no accented-case duplicate brands left.

## The 83 mappings (with evidence)

### European / classic makers
| hernr | → Brand | Evidence |
|---|---|---|
| 124 | **Zastava** | Koral = TU1JP/128 A.064 engines [kmotorshop.com](https://www.kmotorshop.com/en/device/car-list/10214); "10 (188)" = Zastava 10 (Punto 188 clone, 188 A4.000) |
| 171 | **Santana** | PS10/Aníbal (Iveco 8140.43) + 300/350 (DV6ATED4) — Santana Motor, Spain |
| 609 | **AC** | Cobra Mk IV (291N) LS3/LS9 |
| 694 | **Renault Trucks** | Mascott light trucks |
| 705 | **Rolls-Royce** | Phantom/Ghost/Wraith/Park Ward/Corniche |
| 774 | **Pontiac** | Solstice |
| 775 | **Daewoo** | Lanos (ZAZ's Lanos is 1139) |
| 788 | **Bugatti** | Veyron EB 16.4 |
| 802 | **Lotus** | Elise/Exige/Evora/Europa/2-Eleven |
| 803 | **Morgan** | Aero 8/Plus Four/Roadster |
| 815 | **Bentley** | Continental/Arnage/Mulsanne/Azure |
| 907 | **Westfield** | Seven (Ford FYDA, Vauxhall Z16LER) + **XTR with Audi TT 1.8T AMU 224hp = Westfield XTR4** [diseno-art.com](http://www.diseno-art.com/encyclopedia/vehicles/road/cars/westfield_xtr4.html), [wikipedia.org](https://en.wikipedia.org/wiki/Westfield_XTR2) |
| 1138 | **Smart** | Fortwo/Forfour/Crossblade (63v) |
| 1480 | **Aixam** | A.751 0.5D Z482 quadricycle [smallcarsclub.com](https://smallcarsclub.com/catalog/aixam/aixam-a-741-a-751/) |
| 1490 | **Caterham** | "Seven (CF)" = Caterham's TecDoc chassis code [autodoc.co.uk](https://www.autodoc.co.uk/spares/caterham/seven/seven-cf/5810-2-3-csr) |
| 1513 | **Ligier** | Be Up + Nova (Lombardini LDW502) [wikipedia.org](https://en.wikipedia.org/wiki/Ligier) |
| 1516 | **Marcos** | TS250 2.5 Ford V6 175hp / TS500 5.0 Rover V8 320hp [carthrottle.com](https://www.carthrottle.com/post/nkvver3) |
| 1520 | **Metrocab** | "TAXI" 2L-T 2446cc 90PS 2001 = MCW Metrocab TTT [wikipedia.org](https://en.wikipedia.org/wiki/MCW_Metrocab) |
| 1558 | **Wiesmann** | GT MF3/MF4/MF5 |
| 2164 | **Maybach** | Maybach (240_) 57/62 |
| 2755 | **Spyker** | C8/C12 |
| 2760 | **KTM** | X-Bow |
| 1526 | **Infiniti** | G/M/EX/FX (37v) |
| 1533 | **Perodua** | Myvi/Kancil/Kelisa/Viva/Axia/Alza |
| 3514 | **Smart** | "CITY" EV 41hp 2007 = smart fortwo electric drive London trial (41 hp magnetic motor + smart SA-248 option text) [mbusa.com](https://media.mbusa.com/releases/the-new-smart-electric-drive) |
| 908* | *(n/a in variants)* | — |

### Asian makers
| hernr | → Brand | Evidence |
|---|---|---|
| 178 | **Tata** | Indica/Indigo/Safari/Xenon/Aria |
| 181 | **Piaggio** | Porter/Ape/Quargo/M500 |
| 701 | **Lamborghini** | Gallardo/Murciélago/Aventador |
| 1139 | **ZAZ** | Slavuta/Forza/Vida/Lanos Pick-up |
| 1280 | **Mahindra** | Bolero/Scorpio/Maxx/Quadro |
| 1505 | **Acura** | MDX/TL/RL/RSX/CL/RDX |
| 1506 | **Hummer** | H2/H3 — **bonus: H3 3.5 220hp remapped to L52 (GM Vortec 3500 I5)** |
| 1518 | **McLaren** | MP4/650S |
| 2589 | **Landwind** | Jiangling Landwind SUV |
| 2852 | **Chana** | CV6 = Chana Era CV6/Benni 1.3 86hp (JL474Q2) [auta5p.eu](https://auta5p.eu/lang/en/katalog/auto.php?idf=Chana-Era-CV6-2560) |
| 2855 | **Soueast** | Delicia Bus 4G63-S4M/4G64/EQ491i [ebay.com](https://www.ebay.com/itm/402726324395) ("DONGNAN SOUEAST DELICIA BUS") |
| 2857 | **Eunos** | 800 Saloon (E65, TA) 2.5 163HP 2497cc = EUNOS 800 (JDM Mazda Xedos 9) — exact TecDoc listing [kmotorshop.com](https://www.kmotorshop.com/en/article-detail/view/94437/) |
| 2863 | **Dongfeng Fengxing** | FUTURE MPV = Fengxing Lingzhi, "also known as Future" [wikipedia.org](https://en.wikipedia.org/wiki/Dongfeng_Liuzhou_Motor) |
| 2866 | **Hafei** | Saibao 3 |
| 2867 | **Foton** | Alpha/Aumark/Forland/Sea Lion/T-Serie |
| 2887 | **Chery** | A1/A3/A5/Tiggo/E5/Eastar/Cristal (58v) |
| 2888 | **Jinbei** | Haise VI Bus |
| 2901 | **Dadi** | City Courser engines 491QE/4G64S4M/4GZ4/4JB1 [diycarserviceparts.co.uk](https://www.diycarserviceparts.co.uk/dadi_city_courser_2004-present_2237cc_103hp), [autopartner.pl](https://sklep.autopartner.pl/cars/engine-types/5951/dadi-city-courser) |
| 2902 | **Gonow** | GA1020 chassis + JM491Q/ME & GA491QE = Gonow pickup platform [auto-che.com](http://auto-che.com/v/ga/ga1020-115-gonow.html); Troy/Victor also at Karakoram Motors (PK assembler) [karakorammotors.com](https://karakorammotors.com/troy.html) |
| 2903 | **GWM** | Hover/Coolbear/Deer/Fengjun/Sailing/Sing/Steed/**Tengyi (Voleex)** — consolidated with existing GWM brand |
| 2904 | **Mitsuoka** | Galue/Himiko/Nouera/Orochi/Ray/Ryoga/Viewt/La Seyde |
| 2906 | **Baolong** | Pegasus MPV (licensed Delica Space Gear, 4G63/4G64) [tractors.fandom.com](https://tractors.fandom.com/wiki/Baolong_Pegasus) |
| 3070 | **Naza** | Citra/Forza/Ria/Suria/Sutera (Malaysian Kia rebadges) |
| 3071 | **BAW** | HAICE Bus 491QME + YC4F90-21 [cinaautoparts.com](https://www.cinaautoparts.com/baw-haice-bus-taxi-auto-parts-catalogue.html) ("BAW haice bus") |
| 3086 | **Lifan** | 320/520/620/X60/Fengshun |
| 3122 | **BYD** | F0/F3/F6/Flyer/G3/G6/M6 |
| 3127 | **Saipa** | Pride 1.4 97hp 2004 — Iranian Kia Pride [autocade.net](https://autocade.net/index.php/SAIPA_Pride) |
| 3133 | **MG** | "7" 2.5 V6 2497cc 177hp = MG7 [automobile-catalog.com](https://www.automobile-catalog.com/car/2007/1704605/mg_mg7_2_5.html) |
| 3156 | **Shuanghuan** | SCEO |
| 3497 | **Dr Motor** | DR1/DR2/DR5 |
| 3742 | **Luxgen** | "7" SUV 2.2T G22T 2198cc 178PS = Luxgen 大7 SUV [haicj.com](http://www.haicj.com/pcar_1149228.html) |
| 3762 | **Besturn** | B70 1.8 CA4GD5 [wikiwand.com](https://wikiwand.com/en/articles/Besturn_B70_RS) |
| 3913 | **Haima** | V10 1.0 HMAGM10-VF [autohome.com.cn](https://www.autohome.com.cn/news/201112/281380.html) |

### Consolidations into existing brands
| hernr | → Brand | Note |
|---|---|---|
| 2590 | **Geely** | BL/CK/HQ/MR/PU/MK/Panda/Vision/Urban Nanny + Maple Hisoon/Marindo [automobile.fandom.com](https://automobile.fandom.com/wiki/Geely_Automobile) |
| 3332, 3697 | **Geely** | Emgrand EC7; GX2 (Gleagle) |
| 2864, 3297 | **Ford** | AU/TW Falcon, Everest, Laser, Lynx, i-MAX |
| 3035 | **Volkswagen** | CN-market Tiguan (CGM/CCZA), model merged into TIGUAN (5N_) |
| 3047 | **Lti Vehicles** | TX = TX4 (VM R425 + CN-market 4G69 152PS) [wikipedia.org](https://en.wikipedia.org/wiki/TX4) |
| 3124 | **BMW** | 5 SERIES (E60); engine "M54256S5" = garbled M54B25 |
| 3129 | **Honda** | CN-market Odyssey (K24Z2) |
| 3130, 3137 | **Toyota** | CN-market FJ Cruiser/Highlander/LC200/Prado; models merged into FJ CRUISER (GSJ1_), Highlander, LAND CRUISER (VDJ20_, UZJ20_) |
| 3141 | **Nissan** | CN-market Teana/Tiida |
| 3208, 4260 | **Renault Samsung** | QM3/QM5/SM7 |
| 3276 | **HSV** | Clubsport/Avalanche — created as separate make (Holden Special Vehicles) |
| 2242, 3300 | **LDV** | V80 (Maxus) + Fora (Turkish-market "Fargo Fora" = LDV Maxus) [wikipedia.org](https://en.wikipedia.org/wiki/LDV_Maxus) |
| 1553 | **UAZ** | Hunter/Patriot/Pickup/2206 |
| 1556 | **Venturi** | Fetish/Astrolab/America (EV rows now correctly branded) |
| 3652 | **Huanghai** | Plutus pickup, FAW-Dachai 3.2 [wikipedia.org](https://en.wikipedia.org/wiki/Huanghai_Plutus) |
| 3677 | **Inokom** | Lorimas AU26 / HD trucks (Malaysian-assembled Hyundai) [paultan.org](https://paultan.org/2013/04/08/inokom-rolls-out-10000th-lorimas-au26-truck/) |
| 3158 | **Golden Dragon** | XML bus (金旅 XML6xxx codes) [cn.auto-che.com](https://cn.auto-che.com/v/xml/xml6601j88-259-golden-dragon.html) |
| 4176 | **Higer** | H5C light bus (4RB2 + DK4B) [chinabuses.org](https://m.chinabuses.org/news/6968.html) |
| 3495 | **Artega** | GT (VW 3.6 BWS 300hp) |

## Mis-brand fixes (non-hernr)

| Old | New | Why |
|---|---|---|
| **Citroën** (486v) | **Citroen** | Vivid used the accented spelling (hernr_21 = "Citroën"); DB convention is unaccented → 711 variants now unified |
| Saic Mg | MG | MG3/MG6 are SAIC MGs |
| SATURN | Saturn | case |
| SHELBY | Shelby | case |
| Jmc | JMC | case (Jiangling) |
| Volga | GAZ | "Siber" = GAZ Siber |

## Bonus outcomes

- **Hummer H3 3.5 (220hp) → L52** (GM Vortec 3500 I5) remapped — the variant quarantined in Step 7's E18NVR cleanup is now correctly mapped (NULL 96→95, specs 39,085→39,086)
- **5 previously brand-blocked queue rows unblocked** with updated notes: Caterham Seven (CF), Marcos TS250/TS500, GWM Tengyi C50, smart fortwo ed, Landwind 2.4
- **Source intel recovered from `vivid_cars2000.db`**: its 2,788-row models table (hernr+kmodnr+years) also identified buckets that never reached the variants table — Noble (M12/M400), RUF (CTR3/Rt12/3800), Tesla (Model S), IKCO (Samand/Dena), Fisker (Karma), GAZ (Volga/Gazelle), Bristol, Lincoln, Maruti — useful if those models are ever imported

## Follow-ups flagged

1. Marcos TS250/TS500, smart ed 41hp, GWM Tengyi C50 1.5T, Landwind 2.4, Caterham Seven (CF) 2.0T — brand-blocked pendings now only need **engine-row creation/research** (web-cited)
2. Vivid's garbled engine codes exposed by this pass: `M54256S5` (→M54B25), `G4KR/H4KR` 1399cc (→G4EE), `25V6S1` (MG7 KV6) — candidates for a future engine-code cleanup batch
3. Models table now has a few "same car, two names" pairs (e.g. GWM 'Hover' + 'HOVER') from source merges — cosmetic, listed in CSV 16

**Rollback:** `cp database_enriched/backups/car_database_backup_pre_step8_2026-09-29.db database_enriched/car_database.db`
