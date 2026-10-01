## 2026-10-01 - Step 10: 1,738 duplicate variant rows removed (step63)
- vehicle_variants 39,182 -> 37,444. 1,332 groups of byte-identical rows (worst: eleven identical Toyota Prius 2015 / 2ZR-FXE rows) collapsed to one row each.
- Where they came from: the LEMON campaign made them. F21's near-duplicate rows differed only in power or engine_type text, and relinking them onto shared engine codes erased the difference. Step 9 produced the very last one - completing the kW column made a final pair match, which is why this script's baseline assert fired and had to move from 1,738 to 1,739.
- One pair is deliberately exempt. remapping_queue.vehicle_variant_id is NOT NULL and UNIQUE, and variants 31097/31098 each hold a queue row flagging a different wrong code (LLY vs LMM). Rather than destroy a pending remapping record, the variant stays: a row carrying unique downstream state is not a duplicate. The other 56 queue references were repointed at the surviving twin.
- All three derived counters recomputed, and two were already wrong: models.total_variants had drifted on 18 models, and engine_service_specs.count_variants was a stale snapshot disagreeing with engines.count_variants on 3,846 rows. Now 0 / 0 / 0.
- DATA_QUALITY_AUDIT.md updated: F11 resolved, F21 partly resolved (2,770 non-identical groups remain), F14 reclassified as not-a-defect - the 147 zero-variant engine rows are real 1990s European codes for cars the variants table does not cover, and are kept as a reference catalogue by decision.
- DB: 37,444 variants, 5,670 engines, 0 fuel conflicts / 0 orphans / 0 count mismatches, 45 documented NULL-power variants.
## 2026-10-01 - Step 9: kilowatt column completed (step62)
- Filled engine_power_kw on 12,869 variants and power_kw on 446 engine rows. Both columns are now complete wherever horsepower exists.
- The conversion factor was read off the database itself: the kW/hp ratio of the 26,268 already-populated variants clusters on 0.735-0.736, i.e. metric PS, so 0.7355 was used rather than the SAE factor.
- Existing values were not overwritten. The 59 rows whose stored kW disagrees with their own hp by >3% are exported to csv_exports/70_kw_outliers_step62.csv instead - they split into microcar rounding noise, SAE-vs-PS mixing (Z20LET 192hp stored as 147kW = 200 PS), and engine-vs-system power on the DW10 HYbrid4 rows.
- DB unchanged structurally: 39,182 variants, 5,670 engines, 0 conflicts / 0 orphans / 0 count mismatches.
## 2026-10-01 - Step 8: blank engine rows filled, power backfill finished (step61)
- NULL-power variants 535 -> 45; engine rows with no power 85 -> 14. 312 variants filled, 71 engine rows given a figure, 30 variants left blank on purpose.
- The unlock: most blank rows are truncated duplicates. N52, N63, M54, S63, N20, M57 are family stems, and the DB already holds the fully specified member rows. Where the variant names its car (BMW 550i, Ram 2500), the answer was already in the table - N63 -> 407 via N63B44 ("750i/550i 407hp"), N62 -> 355 via the row literally called "X5 48is", S63 -> 552 via S63B44B ("M5 4400 V8").
- Oil data caught three wrong fuels: ETL and ETM were filed as 6700cc PETROL Ram 3500 engines, but their service spec is 11.35 L of 10W-30 - the Cummins 6.7's twelve-quart fill. They and their 12 variants are now Diesel at 370hp, 6690cc. M57 was the same error, a BMW turbodiesel stem filed as Petrol with its four X5s.
- Research cases: the 38 Cummins variants split 350hp (2007-2012) / 370hp (2013+), with the Aisin-only 385/400/420 HO ratings documented as indistinguishable in these rows rather than guessed; ESA splits 410hp Ram HD / 470hp Wrangler 392; DSFE/DSFF are the Golf R Mk8 at 320hp; L15BY splits 174 Civic / 190 CR-V.
- 9 displacement repairs spotted in passing, including N53B3O0 at 630cc - the model designation 630i had leaked into the displacement column.
- Left blank on purpose: the 10 unidentified Teslas (NULL by design), 14 generic-descriptor rows, ESD/ESJ (Hellcat 717 vs Redeye 797 indistinguishable), MDK (992 Carrera vs Carrera S), BEA (TT 1.8T sold at 150/180/225).
- DB: 5,670 engines, 39,182 variants, 0 fuel conflicts / 0 orphans / 0 count mismatches.
## 2026-10-01 - Step 7: variant power backfill (step60)
- NULL-power variants 535 -> 357. 178 filled with hp and kW; 7 left blank on purpose; the remaining 342 are blocked behind engine rows that are themselves blank (Step 8) and 8 have no engine_code.
- The worklist called these 185 rows a trivial inherit-from-engine-row. They were not: only 19 of the 55 engine codes have siblings that unanimously agree with their row, so each code was ruled on individually. 131 COPY, 47 RULE, 7 SKIP.
- Rules that mattered: ESH 6.4 HEMI 392 splits by year (471 as the 2012-14 SRT8, 485 from 2015 as SRT 392/Scat Pack); LF3 splits by model, and the engine row's own descriptor spells out both tunes (CTS V-Sport 420 / XTS 410); N20B20A's row describes a 125i (215hp, 2795cc) and is wrong for the 228i/328i/428i/X1 at 245; N63B44A splits at the 2014 N63TU (407 -> 449); M54B30's 276hp is an Alpina figure, the 530i/X5 ran 228.
- 7 variants left NULL because their "engine code" is a generic descriptor (1.5 dCI, 2.0 16v, ZSD-422...) whose power came from another manufacturer's car. A blank cell beats a confident wrong one.
- Noted for later: 6 exact-duplicate CT4 variant rows, and 12,869 variants with hp but no kW.
- DB: 39,182 variants, 5,670 engines, 0 fuel conflicts / 0 orphans / 0 count mismatches.
## 2026-10-01 - Step 6: all 137 fuel conflicts resolved (step59/59b)
- Every variant now agrees with its engine row about what the car burns: 137 conflicts across 45 engine codes -> 0. Junk fuel labels ("Wankel", "Hybrid (Petrol-/ Electro.)") are gone too.
- Four outcomes by evidence: 49 variants relinked to an existing sibling (Corolla Hybrid -> 2ZR-FXE, Highlander Hybrid -> 2GR-FXE, RAV4 Hybrid -> 2AR-FXE/A25A-FXS, Previa -> plain 2AZ-FE); 30 relinked to one of 12 new rows (Toyota's i-FORCE MAX pair, RX400h/Altima/Pathfinder hybrids, Tucson/Elantra/Sonata hybrids, the Mercedes and PSA diesel hybrids, the S580e PHEV); 4 engine rows had the wrong fuel (X16SZR is a petrol, CHJA/CRJA are literally named "Hybrid", RHC is a diesel); 57 variant labels were wrong.
- Best evidence of the step: the Audi rows labelled Diesel carry 310/197/228hp - exactly the petrol figures of their non-conflicting siblings, where the TDIs of those years read 240. And "Wankel" is a layout, not a fuel, so the RX-8 rows became Petrol.
- Mild hybrid vs hybrid: the S450's EQ Boost cannot drive the car and the DB already treats such cars as Petrol (24 M256 variants), so the S450 moved to a new petrol row while the plug-in S560e kept M276.824.
- 7 junk descriptors fixed, 1 duplicate stub code (654) retired. 59b fixed the single conflict 59 left standing (Sprinter 2023 relinked to a diesel row while still labelled Petrol).
- DB: fuel conflicts 137->0; engines 5,659->5,670; 39,182 variants; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 49 (FINAL): Nissan + Subaru + Lincoln + Mazda + Toyota + Honda (step58/58b/58c)
- 21/21 rows mapped, 0 skips. THE LEMON QUEUE IS EMPTY: 0 LEMON variants, and 0 LEMON rows left in engines, engine_service_specs and engine_technical_specs.
- Decided on fill/viscosity as throughout: NV3500 and Titan 6.51 L -> VK56DE 317hp / VK56VDE 390hp (the 4.0 V6 takes 5.1 L); Versa 3.92 L -> MR18DE 122hp; six Subaru rows at 3.97 L -> EJ253 (Baja 165, Legacy 175, Impreza 173hp); MKS -> 3.7 Ti-VCT V6 273hp; Mazda3 4.54 L -> the new PY-VPS 2.5 Skyactiv-G 186hp (the 2.0 takes 4.2); Tundra 8.04 L -> 3UR-FE 381hp; CR-V 2025 -> L15BE 190hp.
- Toyota Crown 2025 is the batch's one fuel correction: 0W-8 is a grade Toyota uses only for its hybrid Dynamic Force fours, so the row is the 2.5 hybrid (A25A-FXS, 236hp), Petrol->Hybrid.
- 1 new engine (PY-VPS), 6 ROW_FIXES. 58b: 1 ESTIMATE override, 5 normalizations, 2 power syncs; 58c reverts two that let single rows redefine shared engines (3.7 Ti-VCT back to 6 qt, A25A-FXS back off the Crown's JDM 0W-8).
- DB: LEMON 21->0; engines 5,679->5,659; 39,182 variants; 0 orphans; 0 count mismatches.
- Campaign close: batches 42-49 this session cleared 242 rows with zero skips, including the 8 Audi "RS" rows and the 2 GM rows earlier batches had parked. Remaining known residuals are all pre-existing: 137 fuel conflicts, 89 NULL engine_code variants, 536 NULL-power variants (10 of them the deliberately NULL Tesla rows).
## 2026-10-01 - Step 5 Batch 48: Audi + Porsche + Volkswagen (step57/57b/57c)
- 19/19 rows mapped, 0 skips - including the eight bare "RS" rows batch 36 had deferred.
- The RS rows resolved without guessing: all eight carry only two fills, 7.09 L (2.5 five-cylinder, RS 3) and 7.57 L (2.9 V6 biturbo, RS 5 - this project's own EA839 fingerprint). Neither is near the 4.0 V8's 9+ L, which rules the RS 6/RS 7/RS Q8 out of every row. Both engines were missing from the DB and are added.
- Porsche: one nameplate, two engines, separated by fill - Cayenne 3.6 at 8.49 L is the NA V6 (300hp, 2015/2017), at 6.7 L the twin-turbo Cayenne S (420hp, 2016/2018); 911 3.8 VIN D 2012-13 = 991 Carrera S 400hp; Macan 3.0 2020-21 = Macan S 348hp.
- VW: Golf 2025 = GTI Mk8 EA888 241hp; Passat 2.8 2005 = 2.8 V6 30v 190hp (new ATQ row); Touareg 5.0 = V10 TDI 310hp, fuel corrected Petrol->Diesel.
- 5 ROW_FIXES (both Cayenne 3.6 rows were listed as 8-cylinder). 57b: 3 ESTIMATE overrides, 3 normalizations, 2 power syncs; 57c reverts all three normalizations, which had traded curated specs for single-row anecdotes (Touareg 11.45 L, Porsche A40 0W-40, VW 508 00 0W-20).
- DB: LEMON 40->21; engines 5,696->5,679; 0 orphans/count mismatches/fuel conflicts.
## 2026-10-01 - Step 5 Batch 47: Smart + Tesla + Daewoo (step56/56b)
- 31/31 rows mapped, 0 skips. Three brands with no shared hardware, batched because each poses the same question differently: what to do when the crawl's model name has lost what you need.
- Smart: fill tracks the generation change (3.31-3.4 L = 451 1.0 three-cylinder 70hp; 3.59 L from 2016 = 453 0.9 turbo 89hp). The MY2015 FORTWOELECTR trim row is the Electric Drive -> new 74hp BEV row, fuel Petrol->Electric.
- Daewoo: one US engine per nameplate - Lanos 1.6 (3.78 L), Nubira 2.0 (3.88-3.97 L), Leganza 2.2 (3.97 L), the last added as the new X22SE.
- Tesla: Model S/3/X/Y all truncate to "MODEL" with no displacement, fill or VIN, so the car is unrecoverable - but every Tesla is battery-electric. The 10 rows map to one explicit BEV (Tesla, model unidentified) engine, fuel corrected Petrol->Electric, power left NULL rather than invented: a smaller claim than the LEMON placeholders made, and unlike them a true one.
- 3 new engines (X22SE, smart ED, Tesla BEV). 4 ROW_FIXES for junk descriptors. 56b: 4 ESTIMATE overrides off placeholder fills, 1 normalization, 1 power sync.
- DB: LEMON 71->40; engines 5,725->5,696; 0 orphans/count mismatches/fuel conflicts.
## 2026-10-01 - Step 5 Batch 46: Kia + Hyundai (step55/55b/55c)
- 20/20 rows mapped, 0 skips, 0 new engines. One batch because HMG is one engine catalogue (Nu, Gamma, Lambda, Smartstream).
- Four targets confirmed by matching the crawl's fill/viscosity against specs already stored in this DB: G4FJ 4.5 L 5W-30 (Forte Koup SX / Forte5 SX 1.6 T-GDI 201hp), G4NA/G4NC 4.0 L 5W-20 (2.0 Nu), G4KN 5.8 L (K5 2025 2.5 Smartstream 191hp), G6BV 4.51 L (Optima 2001 2.5 V6, against the 2.4 four's 4.25 L).
- Genesis sedan: fill and viscosity disagreed about when the 3.8 Lambda MPi gave way to the Lambda II GDI (viscosity at MY2012, fill at MY2013). US model knowledge settled it at MY2012; 2010-11 -> G6DA 290hp, 2012-14 -> G6DJ 333hp, 2016 -> G6DJ 311hp, with the stale 2012 fill recorded as a caveat.
- 5 ROW_FIXES (G4FJ US/EU rating split, G4NBB, G4KN cylinders NULL, G6BV, G6DA). 55b: 1 ESTIMATE override, 5 normalizations, 1 power sync. 55c reverts 55b's G6DA fill (5.19 -> 5.7 L): the Lambda MPi shares its sump with the GDI engine 55b had just set to 5.69 L.
- DB: LEMON 91->71; engines 5,745->5,725; 0 orphans/count mismatches/fuel conflicts.
## 2026-10-01 - Step 5 Batch 45: Jaguar + Land Rover (step54/54b/54c)
- 27/27 rows mapped, 0 skips, 0 new engines. One batch because JLR is one engine catalogue by this period, and because both brands' rows arrive with the same problem: the crawl truncated "Range Rover Sport/Velar/Evoque" to "RANGE".
- With the nameplates gone the fill decided everything, and three targets' service specs already in this DB match the crawl to the decilitre: 204PT 7.0 L 0W-20 (RANGE 2022-2025 -> 2.0 Ingenium P250 246hp), AJ126 8.04 L (RANGE 3000CC 2014-2019 -> 3.0 V6 SC 340hp), AJ30 6.52 L (S-Type/X-Type -> 3.0 AJ-V6).
- RANGE 3000CC 2020-2025 steps up to 8.8 then 9.46 L, tracking the Ingenium straight six replacing the V6 -> AJ300P P400 395hp. RANGE 2000 at 5.82 L of 5W-40 is the P38's Rover OHV V8, 222hp.
- 2 ROW_FIXES (Rover V8 and AJ30 descriptors). 54b: 3 normalizations. 54c reverts 54b's AJ126 change (7.99 L/5W-20 back to the curated 8.04 L/0W-20, which the rest of the Jaguar fleet relies on).
- DB: LEMON 118->91; engines 5,772->5,745; 0 orphans/count mismatches/fuel conflicts.
## 2026-10-01 - Step 5 Batch 44: Hummer + Cadillac + GMC + Pontiac (step53/53b)
- 28/28 rows mapped, 0 skips, and 0 new engines needed - the last four GM brands share a catalogue the earlier GM batches had already completed.
- Hummer H2 -> LQ4 6.0 (325hp) then L92 6.2 (393hp) from 2008; H3/H3T -> L52 3.5 I5, LLR 3.7 I5 and LH8 5.3 V8 by displacement token; Escalade 2002-2006 -> LQ4 345hp; CTS 6200CC 2015 -> LSA 556hp; STS 2011 -> LLT 302hp.
- The two rows earlier batches had parked as un-decodable both resolved: GMC Sierra 2012 by its VIN engine character J (the gaseous-fuel-capable LC8, not the L96), and Pontiac "GRAND" 2005 by its 5 qt fill, which only fits the 2.2 Ecotec - the nameplate stays ambiguous but the engine does not.
- 4 ROW_FIXES: LH8, LQ9, L92 and L61 carried placeholder or incomplete descriptors.
- 53b: 1 normalization (LLT 5.2 -> 5.67 L), 1 power sync.
- DB: LEMON 146->118; engines 5,800->5,772; 0 orphans/count mismatches/fuel conflicts.
## 2026-10-01 - Step 5 Batch 43: Mercedes-Benz (step52/52b/52c)
- 37/37 rows mapped, 0 skips. 19 rows decode from the nameplate (Mercedes names its cars after their engines); the 18 Sprinter rows decode from the oil fill, where 12.5 L of 5W-30 is the 3.0 V6 OM642 and 10.5 L the 2.0 four OM654.
- 18 fuel corrections: every Sprinter row was filed as Petrol and is now Diesel.
- Maybach is the one badge worn by two cars here and the fill separates them: MY2021 at 9.5 L is the V12 S650 (621hp), 2022-2023 at 8.51 L the 4.0 V8 S580 (496hp). SLK300 2016 is the 2.0 turbo M274, not a V6. Sprinter 2024-2025 is the OM654 at 168hp.
- 8 new engines (M111 2.3 Kompressor, M112 2.8 V6, M276 3.5 V6, M276 3.0 BiTurbo, M278 4.7 V8 BiTurbo, M274 2.0 Turbo, OM642 and OM654 Sprinter): the DB had dozens of chassis-specific rows but no clean US-market entry per family.
- 6 ROW_FIXES: M279.980 (V12) was listed as an 8-cylinder, M112.972 (3.7 V6) likewise, and four rows carried junk crawl descriptors.
- 52b: 2 ESTIMATE overrides, 6 normalizations, 8 power syncs. 52c reverts 52b's plurality vote on the Sprinter V6 fill (10.59 -> 12.5 L).
- DB: LEMON 183->146; engines 5,829->5,800; 0 orphans/count mismatches; DB-wide fuel conflicts unchanged at 137 (the 32 remaining Mercedes mismatches are pre-existing hybrid/electric mislabels on untouched codes).
## 2026-10-01 - Step 5 Batch 42: Dodge + Jeep + Chrysler (step51/51b)
- 59/59 rows mapped (Dodge 23, Jeep 21, Chrysler 15), 0 skips. Merged into one batch because the three brands share a single engine catalogue; "BRAND:MODEL" rule keys keep the nameplates apart.
- Decoded on the crawl's oil-fill ladder: 4.25-4.56 L = EDZ 2.4 / ECN-ED3 World Engine / 420A, 4.73 L = EGA 3.3, EGL 3.8, the new EGW 3.2 and the 2.0 GME 4xe, 5.2 L = EGF 3.5, 5.67 L = 3.6 Pentastar, 6.62 L = 5.7 Hemi eTorque, 11.35 L of 15W-40 = 5.9 Cummins.
- The 2000-2001 LH cars (Concorde/Intrepid) record exactly 5 qt, which is the 3.2 V6 - an engine the DB was missing, now added as EGW 225hp. The Journey's three-year engine walk (3.5 -> 2.4 -> Pentastar) is visible in its fills.
- 5 fuel corrections: the four Ram 5900CC rows Petrol->Diesel (Cummins), Grand Cherokee 2025 Petrol->Hybrid (4xe, identified by its 5 qt fill vs the Pentastar's 6).
- 2 new engines (EGW, 420A). 8 ROW_FIXES: EGL/EGF/EGG/ED3 had wrong cylinder counts and ETH (5.9 Cummins I6) was listed as an 8-cylinder.
- 51b: 1 ESTIMATE override, 5 normalizations (incl. a swapped EDZ/EGA fill pair), 10 power syncs.
- DB: LEMON 242->183; engines 5,886->5,829; fuel conflicts 0 across all three brands; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 41: Suzuki (step50/50b)
- 29/29 rows mapped, 0 skips. Half the range is other people's engineering: Forenza/Reno/Verona = Daewoo (T20SED 126hp, X25D1 2.5 inline-six 155hp), Equator = Nissan Frontier (QR25DE 152 / VQ40DE 261), XL7 2007-09 = GM Theta with the LY7 3.6 V6 252hp. Suzuki's own: Aerio J23A 155 (new row), Grand Vitara H25A 165 -> H27A 185 -> J24B 166 / N32A 230, SX4 J20A 143, XL-7 H27A 185.
- The XL-7 -> XL7 rename in 2007 is a real engine change (2.7 V6 5.48 L -> GM 3.6 5.2 L), visible in the crawl's fills.
- 1 new engine (J23A). 6 ROW_FIXES: H27A carried the junk descriptor "BLAZER S10", J24B was recorded as a 6-cylinder, N32A was a bare "3.2 (est.)".
- 50b: 3 ESTIMATE overrides, 3 normalizations, 4 power syncs.
- DB: LEMON 271->242; engines 5,914->5,886; Suzuki fuel conflicts 0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 40: Mini (step49/49b/49c)
- 31/31 rows mapped, 0 skips. Every row is badged "Cooper", so the decode used the displacement tokens plus the crawl's oil fill: 4.54 L/5W-40 = Tritec W10B16 115hp, 4.2 L/5W-30 = N16 121hp, 4.2-4.6 L/0W-20 = B38 three-cylinder 134hp, 5.25 L = Cooper S 2.0 (B46 189hp, B48 201hp for the 2025 F66).
- The bare 2020-2024 rows resolve despite having no displacement token: 5.25 L is a litre above any three-cylinder row. The 1600CC MY2015 rows must be the outgoing N16, since the F56 is 1.5 or 2.0.
- 1 new engine (W10B16 Cooper 115hp - the DB only had the 90hp One). 4 ROW_FIXES, incl. B38A15A which was recorded as a 4-cylinder.
- 49c: 24 pre-existing Mini variants were sitting on bare "Eng CD" placeholder rows (B38, B48, N16, N18, W10, ...M0 stubs) with NULL power; they were relinked to the verified vocabulary, power was backfilled on N12/N14/W11/N18B16A/N18B16C, 6 emptied placeholders were retired and B48A20B lost its junk "Leaf Spring Suspension" descriptor.
- DB: LEMON 302->271; engines 5,950->5,914; Mini fuel conflicts 0; Mini NULL-power variants 55->0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 39: Lexus (step48/48b/48c)
- 31/31 rows mapped, 0 skips (12 flagged volume defaults). All rows were bare nameplate+year, so the decode ran on the crawl's oil fill AND viscosity: 0W-16/4.54 L identifies the 2.5 Dynamic Force (ES 250 A25A-FKS), 4.35 L the 2AR-FXE hybrid, 4.63 L the 8AR-FTS 2.0 turbo, 5.39-6.43 L the 2GR-FKS V6, 6.05 L the 2GR-FE, 5.20 L the SC 300's 2JZ-GE.
- ES 2018 was identified as the ES 300h from its 4.35 L fill and its fuel corrected Petrol->Hybrid. IS/RC 2018-2025 take the volume 350 V6 over the RC F / IS 500 V8 (flagged).
- No new engines needed. 4 ROW_FIXES: 2AR-FXE was recorded as a 6-cylinder, A25A-FKS had a NULL cylinder count.
- 48c: two pre-existing variants on the hybrid AVV5/AVV6 bodyshells (an ES and a Camry) were linked to 2AR-FXE but flagged Petrol; their fuel was corrected.
- DB: LEMON 333->302; engines 5,981->5,950; fuel conflicts on batch targets 1->0; Lexus NULL-power variants 31->0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 38: Saab (step47/47b)
- 34/34 rows mapped, 0 skips (2 flagged volume defaults). Three engineering sources separated by displacement token and crawl oil fill: Subaru-built 9-2X (EJ205 227hp / EJ253 165-173hp, 3.97 L), Saab's own 9-3 and 9-5 (B207R US 210hp, B284L 250-255hp, new B235E US 220hp, A20NHT 220hp) and the GM rebadges (9-7X LL8 275/291, LH6 300, LS2 390; 9-4X LF1 265).
- 1 new engine (B235E US 9-5 2.3T 220hp). 5 ROW_FIXES, incl. A20NHT which was recorded as a 6-cylinder.
- Volume defaults: the MY2006 9-2X row (both that year's cars are 2.5-litre) and the 9-4X 2011 row (3.0i over the Aero 2.8T) - both flagged in the decision CSV.
- 47b: 3 ESTIMATE overrides, 1 normalization, 3 power syncs.
- DB: LEMON 367->333; engines 6,014->5,981; Saab fuel conflicts 0; Saab NULL-power variants 34->0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 37: Isuzu (step46/46b) - completes the batch 26-37 run
- 35/35 rows mapped, 0 skips. Isuzu's own cars decoded from displacement tokens (X22SE 2.2 130hp, 6VD1 3.2 205hp, 6VE1 3.5 at 215/230/250hp by model); the GM rebadges decoded from nameplate + crawl oil fill (Hombre LN2, Ascender LL8 275/291 and Vortec 5300 LM4 290 for 2004 vs LH6 300 for 2005-06, i-280 LK5, i-290 LLV, i-350 L52, i-370 LLR).
- 2 new engines (X22SE, 6VD1). 6 ROW_FIXES: the GM Atlas rows had wrong cylinder counts - LLV is a 2.9 I4 (was 6), LLR and L52 are I5s (were 8 and 6).
- 46b: 1 ESTIMATE override, 3 normalizations (10W-30 kept for the 2000-2003 Isuzu engines, which is the period-correct spec), 5 power syncs.
- DB: LEMON 402->367; engines 6,047->6,014; Isuzu fuel conflicts 0; Isuzu NULL-power variants 35->0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 36: Audi (step45/45b/45c)
- 31/39 rows mapped, 8 documented skips. New decode signal: the per-row oil fill recorded by the crawl separates Audi's families (longitudinal 2.0 TFSI 4.6-4.7 L, transverse MQB 2.0 TFSI 5.7 L, 3.2 FSI 6.2-6.5 L, supercharged 3.0 TFSI 6.8 L, EA839 3.0 V6 7.6 L, V8s 8.7-9.65 L), which is what identifies A6 2020-2025 as the 55 TFSI V6 and RS 2013-2014 as the RS 5 4.2 FSI V8.
- 2 new engines (MQB 2.0 TFSI 220hp; EA839 3.0 V6 TFSI 335hp). 9 ROW_FIXES, incl. CYMC which had NULL type/power/cylinders and is now the B9 2.0 TFSI 252hp.
- Skips: the 8 bare "RS" rows for 2018-2025 - Audi sold 2-6 different RS models per year from MY2018 (2.5 I5, 2.9 V6 TT, 4.0 V8 TT, electric) and these rows carry no displacement, VIN or source URL. The 2016-2017 RS rows were resolved because their tech_source URL names "RS 7 Base".
- 45c: Q5 2013/2016 variants flagged Hybrid while linked to the petrol CNCD were given their own Q5 hybrid quattro engine row (2.0 TFSI + 40 kW, 245hp) instead of having their fuel flattened.
- DB: LEMON 433->402; engines 6,075->6,047; fuel conflicts on batch targets 2->0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 35: Alfa Romeo (step44/44b)
- 43/43 rows mapped, 0 skips. Four nameplates, four powertrains: 4C 1750 TBi 237hp (incl. 3 MY2015 trim-slug rows), Giulia/Stelvio 2.0 GME-T4 280hp, Quadrifoglio 2.9 V6 twin-turbo (690T) 505hp, Tonale Q4 PHEV 285hp.
- 1 new engine (690T 2.9 V6 TT). 3 ROW_FIXES incl. 960A1.000, which carried the junk parts-catalogue descriptor "Rear side-section" and is now the 4C's 1750 TBi.
- All three Tonale rows were recorded as Petrol; every US Tonale is a plug-in hybrid, so they were relinked to the 1.3 GSE PHEV row with fuel corrected to Hybrid.
- 44b: 1 ESTIMATE override, 1 normalization, 2 power syncs.
- DB: LEMON 476->433; engines 6,117->6,075; Alfa fuel conflicts 0; Alfa NULL-power variants 43->0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 34: Scion (step43/43b)
- 44/44 rows mapped, 0 skips, no volume defaults needed: Scion had no engines of its own and each nameplate ran a single engine per generation (xA/xB-I 1NZ-FE 103, xB-II 2AZ-FE 158, xD 2ZR-FE 128, tC 2AZ-FE 161 then 2AR-FE 179, iQ 1NR-FE 94, iM 2ZR-FAE 137).
- Non-Toyota engines identified: FR-S = Subaru FA20 flat-four (Toyota 4U-GSE) 200hp; iA = Mazda2 sedan with the 1.5 Skyactiv-G 106hp (1 new engine row).
- 4 ROW_FIXES: FA20 and 2AR-FE were recorded as 6-cylinder; 2ZR-FAE and 1NR-FE given family descriptors.
- 43b: 2 ESTIMATE overrides, 1 normalization, 1 power sync - no correction script needed.
- DB: LEMON 520->476; engines 6,160->6,117; Scion fuel conflicts 0; Scion NULL-power variants 44->0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 33: Fiat (step42/42b)
- 64/64 rows mapped, 0 skips. First batch decoded largely from the crawl's VIN engine digit: Fiat position-8 table gives R = 1.4 MultiAir NA (101hp, EAB), H = 1.4 MultiAir Turbo (EAF/EAM, 135-160hp), E = 83 kW electric.
- 21 MY2015 trim-slug rows handled by the trim table (Abarth 160/157, Turbo 135, Pop-Sport-Lounge 101, every 500L trim 160).
- Six BEV rows recorded as Petrol were corrected to Electric, including the MY2024 "500" row - the only US Fiat 500 that year was the new 500e.
- 3 new engines (1.4 MultiAir NA, 500e 83 kW, 500e 87 kW); existing 1.4 MultiAir Turbo, ED8 Tigershark and 1.3 GSE Turbo rows reused with updated descriptors.
- 42b: 0 overrides, 0 normalizations, 2 kept, 3 power syncs - no correction script needed.
- DB: LEMON 584->520; engines 6,221->6,160; Fiat fuel conflicts 0; Fiat NULL-power variants 64->0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 32: Genesis (step41/41b)
- 74/74 rows mapped, 0 skips. Four Hyundai families cover the whole brand: Theta II FR 2.0T, Lambda II 3.8/3.3T, Tau 5.0 V8, Smartstream 2.5T/3.5T.
- Key identification: the G70/G80 DH/Stinger 2.0T is the longitudinal G4KL (252hp), not the transverse Sonata G4KH; Smartstream codes confirmed as G4KR (2.5T 300hp) and G6DT (3.5T 375hp).
- Six BEV rows (GV60 x3, "Electrified" x3) were recorded as Petrol in the crawl; both got E-GMP dual-motor rows and their variant fuel corrected to Electric. The truncated "Electrified" nameplate (G80 365hp vs GV70 429hp) is mapped to the shared powertrain row with the ambiguity documented.
- 5 new engines (G4KL, G4KR, G6DT, GV60 Electric, E-GMP Dual Motor); 2 ROW_FIXES (G6DJ was an 8-cylinder 335hp row, corrected to the 3.8 V6 Lambda II at 311hp).
- 41b: 3 normalizations, 2 kept, 6 power syncs; crawl oil capacities matched the published Genesis figures, so no correction script was needed this batch.
- DB: LEMON 658->584; engines 6,290->6,221; Genesis fuel conflicts 0; Genesis NULL-power variants 74->0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 31: BMW (step40/40b/40c/40d)
- Hardest row shape so far: 80 of 83 codes are nameplate + year only (no displacement, no VIN, no trim). Decoded by nameplate generation + US volume engine; 83/83 mapped, 0 skips.
- Truncated names resolved: "M" = M roadster/M coupe (S52 240hp MY2000, S54 315hp 2001-02, Z4 M 330hp 2006-08); "ACTIVEHYBRID" = ActiveHybrid 3/5, N55 300hp + 55hp motor = 335hp combined (BMW US press kits).
- 2 new engines: N55B30 (ActiveHybrid) and N63B44 (ActiveHybrid). 10 ROW_FIXES (N55B30A/N52B30A cylinder counts 4->6, family descriptors).
- 40b: 5 ESTIMATE overrides, 8 normalized, 1 power sync. 40c: restored six BMW service fills the crawl majority had broken (N55 6.5L, B58 6.5L, B48 5.25L, S54 5.48L, M54 6.5L, N63TU 8.99L).
- 40d: cleared all 38 BMW fuel contradictions - V8 ActiveHybrid 7/X6 rows moved off the petrol N63 rows, N63B44A corrected from Hybrid to Petrol, i3 REx rows moved to the W20K06A range extender, N57D30T/B3815KT0 variant fuels fixed.
- DB: LEMON 741->658; engines 6,371->6,290; BMW fuel conflicts 38->0 (DB-wide 181->141); BMW NULL-power variants 83->0; 0 orphans/count mismatches.
## 2026-10-01 - Step 5 Batch 30: Pontiac + Saturn (step39/39b/39c)
- Merged GM badge-division batch (G6=Aura, G5=ION, Solstice=Sky, Torrent=Vue, Montana SV6=Relay, G3/Wave=Aveo, Astra=Opel, Vibe=Matrix). 133/134 rows mapped, 1 documented skip.
- Epsilon ratings decoded year by year (2.4 169->164, 3.5 200->224->219, 3.9 240->227->222, 3.6 252).
- Findings: Saturn Vue 3.5 V6 2005-07 = Honda J35S1/J35A3 sold by GM as L66 250hp (new row); VUE_2400CC_2007 is the Green Line BAS mild hybrid (new LAT row, fuel -> Hybrid), the first-gen Vue never had a petrol 2.4.
- 3 new engines (L66, L81, LAT); 10 ROW_FIXES (cylinder counts on L61/LE5/LNF/L91/1ZZ-FE/2AZ-FE, LZ4 power 211->219, conflation notes on L36 and L61).
- 39b: 3 ESTIMATE overrides, 6 normalized, 4 power syncs. 39c: reverted two bad crawl-majority oil capacities (LA1 -> 4.25L, L76 -> 5.67L).
- Skip: LEMON_PONTIAC_GRAND_2005 - bare "Grand" 2005 is Grand Prix or Grand Am, no displacement to disambiguate.
- DB: LEMON 874->741; engines 6,501->6,371; Pontiac/Saturn fuel conflicts 0; 0 orphans/count mismatches.
## 2026-10-01 — Step 5 Batch 29: Ford + Mercury (step38/38b/38c)
- Merged Ford-family batch (every Mercury is a Ford twin). Replaced 148/148 LEMON rows, zero skips. Decode = nameplate generation + displacement (Triton 4.6/5.4/6.8 chassis rows, Vulcan->Cyclone Taurus/Sable, Duratec 2.3/2.5/3.0 Escape-Mariner + Fusion-Milan, 4.0/4.6-3V/5.0 Explorer-Mountaineer, Mustang 3.8->2.3EB + 5.2 Voodoo, Transit Connect vs Transit).
- Police/fleet rows identified: "Special" 2014-18 = Taurus Special Service Sedan 2.0 EcoBoost 240hp; "SSV" 2019-20 = SSV Plug-In Hybrid Sedan (Fusion Energi) 2.0 Atkinson PHEV 188hp.
- 4 new engines (3.0 V6 Vulcan, 4.2 V6 Essex, 4.6 Triton 3V, 3.7 Ti-VCT Cyclone); 9 ROW_FIXES incl. 2.0 Zetec / 2.0 Duratec cylinders 6->4.
- 38b: 4 ESTIMATE overrides, 6 normalized, 13 power syncs. 38c: 5 crawl-Hybrid rows re-mapped to the Atkinson hybrids (Escape 2.3 155hp, Mariner 2.5 177hp) + Fusion 2012 191hp; 5.4 Triton 3V oil restored to 6.62L; 23 pre-existing fuel contradictions cleared (Power Stroke->Diesel, PowerBoost->Hybrid).
- DB: LEMON 1,022->874; engines 6,645->6,501; Ford+Mercury fuel conflicts 29->0 (DB-wide 210->181); 0 orphans/count mismatches.
## 2026-10-01 — Step 5 Batch 28: Mitsubishi (step37/37b/37c)
- Replaced 138/138 LEMON Mitsubishi rows, zero skips. Decode = nameplate generation + displacement (Eclipse 4G64/6G72 -> 4G69/6G75 263-265; 2018+ "Eclipse" rows = Eclipse Cross 4B40; Lancer 4G94->4B11 152/148 + 4B12; Outlander 4B12 168/166 + 6B31 220/224, 2000CC rows = Outlander Sport 148, 2021+ = PR25DD 181; Mirage 3A92 74/78; Raider = Dakota EKG/EVA).
- 1 new engine (4B40 1.5T Eclipse Cross 152hp); 4 i-MiEV rows fuel Petrol->Electric; 11 ROW_FIXES incl. 4G69 cylinders 6->4 (brand_example was BYD), 4B12 6->4, 3A92 4->3, Y4F1 "CITYROVER" -> i-MiEV traction motor 66hp.
- 37b: 9 ESTIMATE overrides, 3 normalized, 2 power syncs. 37c: EVA oil capacity restored to 5.67L (4.7 V8, not the 3.7's 4.73L); deleted heuristic engine-oil specs from 16 battery-electric engine rows.
- DB: LEMON 1,160->1,022; engines 6,782->6,645; 0 orphans/count mismatches/Mitsubishi fuel conflicts.
## 2026-10-01 — Step 5 Batch 27: GMC + Chevrolet (step36/36b/36c/36d)
- First merged engine-family batch (GMC and Chevrolet share one GM RPO catalogue). Replaced 208/209 LEMON rows; 1 documented skip (Sierra 6000CC VIN J 2012 - L96 vs LC8 unresolvable). Decode = RPO via displacement + VIN 8th digit + model year (Terrain K/5/3/V/X/U; Acadia LY7->LLT->LFX->LGX/LCV/LSY->LK0; Envoy LL8 270/275/291 + LM4->LH6; full-size L83/L82/L84).
- 5 new engines (L65 6.5 Detroit Diesel, LAP, LKW, LK0, Ultium e4WD Hummer EV 1000hp Electric); 16 fuel fixes in-batch (L65 x10 Diesel, Hummer EV x4 Electric, LH7 x2 Diesel); 12 ROW_FIXES incl. LU3/LL8/LFX cylinders 8->6.
- 36b: 5 ESTIMATE overrides, 5 normalized, 7 power syncs. 36c: 21 junk engine rows repaired (G16B "JETSTAR", LN2 NULL type+cylinders, LS1 brand_example Daewoo->Chevrolet). 36d: retired duplicate free-text code "6.5 TD V8 (L65)" into L65; A16XER Diesel->Petrol, LFA Petrol->Hybrid; 27 variant fuel fixes (Duramax->Diesel, two-mode/eAssist->Hybrid); L5P/L3B/LS9/LT5/LF3 power fills; 105 NULL powers backfilled.
- step5_lemon_lib: multi-brand batches (Cfg.brand accepts a list, "BRAND:MODEL" rule keys, brand-aware decide/extra_decide).
- DB: LEMON 1,368->1,160; engines 6,986->6,782; GMC+Chevrolet fuel conflicts 42->0 (DB-wide 271->205); 0 orphans/count mismatches.
## 2026-10-01 — Step 5 Batch 26: Acura (step35/35b/35c)
- Replaced 180/180 LEMON Acura rows, zero skips. Decode = nameplate generation + displacement + VIN engine digit (US/CA market, no diesels). 19 new engines (J37A1, J35Y5, J30Y1, J30AC, C32B, JNC1, K23A1, J35Y4 (+SH), J32A3, J35Z6, K24W7, J35Y6, K20C6, K20C8, K24V7, L15CA, B18B1, J37A5); 7 row-fixes incl. J37A2 cylinders 8->6 and the L15BE stub; 6 NSX NC1 rows fuel Petrol->Hybrid.
- 35b: 10 ESTIMATE overrides, 3 normalized, 23 power syncs. 35c: retired the vivid duplicate R23A2 (bogus 6-cylinder "2.3 Turbo") into K23A1, variant re-dated 2005->2007.
- step5_lemon_lib: punctuation-insensitive model matching (NSX-T) + 3-char VIN tokens (VINYD2/VINTB1).
- DB: LEMON 1,548->1,368; engines 7,148->6,986; 0 orphans/count mismatches/Acura fuel conflicts.
## 2026-10-01 — Step 5 Batch 25: Volvo (step34/34b)
- Replaced 184/184 LEMON Volvo rows, zero skips. Official Volvo VIN engine-code decode (pos 4-5: 40/49/61/90/94/95/98/99/10/A2/BR/BC/BK/H6/L1/06). 7 new engines; 14 T8 PHEV fuel fixes; B4204T27 row-fix to T6 316.
- DB: LEMON 1,732->1,548; engines 7,325->7,148; 0 orphans/mismatches/conflicts.
## 2026-10-01 — Step 5 Batch 24: Lincoln (step33/33b)
- Replaced 189/192 LEMON Lincoln rows (3 skips: MKS 3700CC 2010-12 lineup contradiction). 2 new engines (4.6 InTech DOHC, Corsair PHEV 266); Ford-family codes reused (2.0T/2.3/2.7/3.0/3.5EB/3.7/4.6/5.4/AJ30/AJ35); 3 PHEV fuel fixes.
- DB: LEMON 1,921->1,732; engines 7,512->7,325; 0 orphans/mismatches/conflicts.
## 2026-10-01 — Step 5 Batch 23: Porsche (step32/32b/32c, rebuilt after workspace rewind via new shared step5_lemon_lib.py)
- Replaced 185/193 LEMON Porsche rows with verified codes (8 documented skips). 20 new engines; MDW 394hp + MDJ 350hp fills; MCG.EA fuel->Hybrid.
- 32b: 28 ESTIMATE overrides, 22 power syncs. 32c: MDJ/MDW oil repairs (LN Engineering/NHTSA), MCT/MDH->MCT.LA 400hp consolidation, 918 Spyder 887hp Hybrid fix, hybrid-family fuel normalization.
- DB: LEMON 2,106->1,921; engines 7,679->7,512; 0 orphans/mismatches/conflicts.

## Batch 22 — Land Rover (2026-10-01)
- 194 LEMON rows → 179 mapped / 15 documented skips (Range 2000CC bare ×1, Range 2022-25 bare ×4, Range 3000CC bare ×10 — unresolvable without VIN letter). LEMON 2,285→2,106; engines 7,852→7,679.
- Engine decode via Wikibooks LR VIN decoder (pos 6 / pos 8 eras) + era intercepts for power (204PT 240→296; AJ300P 395/355; 508PS 510/518).
- 6 NEW engines (Rover OHV 4.0/4.6, P400e, P440e/P550e, P530 N63TU3, P530 S68); 12 ROW_FIXES (M62B44 cc 3666→4398); 17 fuel fixes (306DT→Diesel ×10, 204DTD→Diesel ×2, PHEV→Hybrid ×5).
- step31b: 9 EST overrides + 3 normalized + 12 power syncs; audit clean.
- step31c vote-audit repairs (web-verified): B6324S 9.22L→7.7L [costaoils + landroverforums], 25K4F 0W-40→5W-40 [AMSOIL + auto-data.net]; pre-existing junk row 4900 (Discovery 2003) mislinked AJ34→4.6 V8 (Rover OHV) @217hp [3 auction/review sources].
- Scripts: step31_step5_lemon_batch22_landrover.py, step31b_estimate_override.py, step31c_fix_vote_contamination.py; CSV 39; backup pre_step31.
