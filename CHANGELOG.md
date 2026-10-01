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
