# STEP 5 — Batch 19: Mopar Group LEMON Replacement (step28 / step28b / step28c)

**Date:** 2026-09-30 · **Scope:** 441 `LEMON_{DODGE,CHRYSLER,JEEP}_*` variants (Dodge 207 + Chrysler 136 + Jeep 98, single grouped batch per user directive), ~45 models, MY2000–2025
**Result:** **382 mapped / 59 skipped (documented ambiguity)** ·
LEMON total 3,071 → **2,689** · engines 8,620 → **8,250** (12 new rows created, 382 retired LEMON rows deleted)
Verification: 0 orphan refs, 0 count mismatches, 0 fuel conflicts among targets, 0 ESTIMATE specs among targets, 0 spec-power mismatches, 0 NULL powers on batch targets (49 stale NULLs swept).

## Signals used
cc markers (2400CC/VINB = 2.4, 1400CC/VINH = 1.4T…), VIN 8th-digit letters (VINT = 5.7 eTorque,
VINP = 3.0 Hurricane — confirmed by an eBay GW-L engine listing and AMSOIL's "engine code [P]" page,
VINJ = 6.4, VINX = 3.2 Pentastar, VIN1 = 1.3 GSE, VINA = 2.0), fuel column (Pacifica PHEV = Hybrid,
Sprinter diesel mislabels), trim slugs (TOWNCOUNTRYL/S/T, CVTRADESMAN, GRANDCARAVAN, VIPERBASE/GT/GTS,
COMPASSLIMIT, PATRIOTLIMIT). Truncated lemon model names resolved per-row: "GRAND" = Grand Caravan
(Dodge) / Grand Voyager (Chrysler 2000) / Grand Wagoneer (Jeep), "TOWN" = Town & Country, "PT" = PT
Cruiser, "C/V" = Grand Caravan C/V, "SRT 4" = Neon SRT-4.

## Engine families mapped
- **Pentastar V6 (n=247 after batch):** 3.6 = 283hp (200/Avenger/Journey/T&C/Grand Caravan/C/V),
  287hp (Pacifica 2020+/Voyager 2020+); 3.2 = 271hp (Cherokee KL VINX). The shared `3.6 Pentastar`
  engines row had NULL power — filled with the variant-mode (283).
- **2.4/2.0/1.8 four-cylinder lineage:** EDZ 2.4 150hp (PT/Sebring JR/Stratus/Voyager/Caravan 2000-07),
  ED3 = 2.4 World GEMA 172-173hp (Caliber/Compass/Patriot/Sebring JS 2007+/200 2011-14/Avenger/Journey),
  ECN = 2.0 World GEMA 158hp, NEW `1.8 World Engine (GEMA)` 148hp, ED8 = **2.4 Tigershark MultiAir2
  184hp (junk NULL row repaired** — type/displacement/power filled; Dart 2.4, Renegade 2.4, Compass
  2018-22 180hp, pre-existing 2015-17 200/Dart/Cherokee links swept), NEW `2.0 TigerShark (Dart)` 160hp,
  NEW `1.4 MultiAir Turbo (Dart/Renegade)` 160hp (Stellantis press kit), `2.4 16v Turbo SRT-4`
  215hp 2003 / 230hp 2004-05 (row relabeled, power corrected from 205).
- **Modern small turbos:** NEW `1.3 GSE Turbo (Renegade)` 177hp (2019+ incl. bare 2022-23 = 1.3T-only
  US from 2021), NEW `1.3 GSE PHEV (Hornet R/T)` 288hp net **+ fuel fix Petrol→Hybrid** (R/T was a 2024
  MY introduction so 2023 bare Hornet = GT 2.0 268hp → `2.0 Turbo GME` row, exact power match),
  `2.0 Turbo GME` 268/200hp (Hornet GT; **Compass 2023+ = 2.0T 200hp** — the 2.4 died after MY2022).
- **V6 SOHC/OHV fleet (Euro-catalog rows reused):** EER 2.7 (200/189hp by era), EGF 3.5 JS 235hp,
  EGG 3.5 LH 250hp (300M/LHS/Prowler/Concorde/Intrepid 3500cc), NEW `3.2 V6 (LH)` 220hp (Intrepid 2001),
  EGX = Crossfire 3.2 M112 215hp, `3.5 V6 (LX)` 250hp (Challenger 2008 SE), EGA 3.3 (180/175hp),
  EGH 3.8 (215/197hp), `4.0 V6 (Chrysler, Routan)` relabeled = **4.0 OHV minivan 251hp** (T&C/GC 2008-10),
  EGS relabeled = **4.0 SOHC 260/253hp** (Nitro R/T / Pacifica 2007-08; was junk "ZEBRA Pickup" row),
  EKG 3.7 PowerTech 210hp (Dakota 2004 = year-off for 3.7-from-2005).
- **HEMI / SRT:** EZC 5.7 345hp (Chassis Cab 2006-08 gas-only), EZH 5.7 390hp (Chassis Cab 2010),
  NEW `5.7 HEMI V8 eTorque (Wagoneer)` 392hp, ESG 6.4 471hp (Grand Wagoneer VINJ), `3.0 Hurricane I6`
  420hp SO (Wagoneer VINP/3000CC + 2024-25 Hurricane-only years — V8s dropped for 2024 per carscoops),
  NEW `3.0 Hurricane I6 H.O. (Grand Wagoneer)` 510hp / 540hp 2025 (spec set 0W-40 MS-A0921).
- **Viper generations:** NEW `8.0 V10 (Viper Gen II)` 450hp (2000-02, Wikipedia SR II), `8.3 V10 SRT`
  500hp (2003-06), `8.4 V10 SRT10` 600hp (2008-10), NEW `8.4 V10 (Viper Gen V)` 640/645hp (2013-17
  incl. 2015 Base/GT/GTS trims); step28 also **relinked 1 pre-existing 2013 Viper variant** that sat on
  the Gen-IV 599hp row.
- **Cummins diesel (fuel-column errors corrected):** 5900cc 2005-07 Pickup/Chassis-Cab rows labelled
  Petrol → **Diesel** + ETH `5.9 I6 Cummins CR HO` 325hp (2004.5-07 rating; dieselpowerproducts/
  puredieselpower). 2004 rows skipped (mid-year 305/325 split), 2008-09 skipped (5.9 ended 2007.5 —
  physically impossible; a 6.7 would carry 6700cc).
- **Sprinter:** 2003-06 = OM612DE27LA 2.7 I5 diesel 154hp (2003-04 fuel fix Petrol→Diesel; row cc
  junk 2184→2685 corrected, code itself says 2.7), 2007-09 = M272E35 3.5 V6 petrol 254hp (KBB confirms
  the 2007 pair 3.5 gas / 3.0 OM642 TD; fuel column decided).
- **Minivan 3.0 / coupé 3.0:** `6G72(SOHC24V)` reused — 150hp (Caravan/Voyager/Grand Voyager 2000
  3.0 Mitsubishi) and 200hp (Sebring/Stratus coupe, Eclipse-platform).
- **Pacifica PHEV:** NEW `3.6 V6 Pentastar PHEV (Pacifica Hybrid)` 260hp total system (Stellantis
  product media; fuel column already Hybrid) — 7 rows 2017-2024.

## Skips (59, all documented in CSV)
- 2-engine ambiguity on bare rows: T&C 2000-07 & Grand Caravan 2001-07 (3.3 vs 3.8), Compass/Patriot
  2007-16 (2.0 vs 2.4), Sebring 2000/02/03, Stratus 2000-03, Cirrus 2000, Concorde 2000-01,
  Intrepid 2000, Avenger 2000 (2.0/2.5), Journey 2009-11 (2.4 vs 3.5), Caliber 2007/11/12,
  Wagoneer 2023 (5.7 vs Hurricane SO), Grand Cherokee 2022/2025 (3.6/5.7/4xe resp. 3.6/4xe).
- Physical impossibilities: Pacifica 3.8 2008 (4.0-only year), Ram 5900cc 2004 (mid-year Cummins
  SO/HO split) and 2008-09 (5.9 out of production).

## step28b spec normalization + step28c line-audit repairs
10 ESTIMATE overrides, 10 majority normalizations, 22 power syncs. Line-audit (majority-vote hazard
rule) caught 3 contaminations, repaired in step28c: **EZH** (5.7 HEMI, n=177 variants) had been flipped
to 15W-40/11.35L by a single x1/1 diesel Chassis-Cab trim vote → reverted to 5W-20/6.62; **M272E35**
(flipped to 12.5L by 3 Sprinter votes vs 38 Mercedes-car variants) → reverted to 0W-30/8.04;
**3.5 V6 (LX)** (single-vote 0W-40/6.62) → reverted to 10W-30/5.67. The unanimous x6/6
`3.0 Hurricane I6` 0W-20/7.09 was externally verified correct (blauparts/AMSOIL: SO = 0W-20 MS-6395,
7.1L/7.5qt — which also independently confirms the VINP = Hurricane decode). Hurricane H.O. spec set
0W-40 (MS-A0921).

## Process notes
- 11th rewind caught before work started (baseline assert LEMON=3,071/engines=8,620 passed);
  `git reset --hard origin/arena/...` recovery as usual.
- First apply crashed on `execute(?, (lc))` string-not-tuple bug AFTER backup creation but BEFORE
  commit → transaction rolled back cleanly (verified LEMON still 3,071); fixed `(lc,)` and re-applied.
- IDENTITY assert (batch-17 rule) caught one real dict bug pre-apply (ESG/EGS swap — ESG is the 6.4
  HEMI 6400cc, EGS the 4.0 SOHC 3952cc) and queued two junk-cc bypasses (ED8 2400→2360, OM612 2184→2685).
- 49 stale NULL variant powers swept on batch targets (ED3×7, ECN×1, EZC×12, EZH×17, ESG×12).
- Citations recorded in the decisions CSV evidence column (36_lemon_batch19_decisions.csv): Wikipedia
  Grand Wagoneer WS + Viper SR II, Stellantis press kits (Dart, Pacifica PHEV), edmunds (Sebring 2007,
  T&C 2008), dieselpowerproducts/puredieselpower (Cummins), kbb/moparpartsgiant (Sprinter),
  drivepetersen (Compass 2.0T), motales (LH 3.2), blauparts/AMSOIL (Hurricane oil specs + VIN P),
  carscoops/moparinsiders/roadandtrack/topspeed (Wagoneer V8 drop, Hornet, GC-not-Hurricane).

## DB state after batch 19
engines **8,250** · LEMON total **2,689** (Dodge 23, Chrysler 15, Jeep 21 remaining — the 59 documented
skips) · 0 orphans / count-mismatches / fuel-conflicts among targets · 3.6 Pentastar n=247 (power
filled 283) · ED8 n=31 (repaired row) · next batches: Buick 205, Subaru 205, Land Rover 194, Porsche 193,
Lincoln 192, Volvo 184, Acura 180, GMC 156, Mitsubishi 138, Ford 85, Pontiac 85, Genesis 74, Fiat 64,
Mercury 63, Saturn 49, Scion 44, Alfa Romeo 43, Isuzu 35, Saab 34, Mini 31, Suzuki 29, Hummer 19,
Smart 12, Tesla 10, Daewoo 9.
