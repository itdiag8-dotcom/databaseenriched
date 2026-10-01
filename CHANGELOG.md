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
