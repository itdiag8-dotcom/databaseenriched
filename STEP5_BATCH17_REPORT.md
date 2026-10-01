# STEP 5 — Batch 17: Volkswagen LEMON Replacement (step26 / step26b / step26c)

**Date:** 2026-09-30 · **Scope:** 237 `LEMON_VOLKSWAGEN_*` variants, 19 models, MY2005–2025
**Result:** **234 mapped / 3 skipped** · LEMON total 3,535 → **3,301** · engines 9,065 → **8,846**
Verification: 0 orphan refs, 0 count mismatches, 0 fuel conflicts, 0 ESTIMATE specs, 0 spec-power mismatches.

## Signals used
Displacement (`1800CC…6000CC`) + VIN engine letters (VIN P/C/E/R Atlas, VIN 0/1/S/T/D/W, VIN 5/6/B, VIN 4/T/M/N) + **trim slugs** (`GOLFRAUTOMAT/GOLFRSTANDAR` = Golf R, `JETTATDI*`, `TIGUANR-LINE…`) + **fuel column** (12 rows already Diesel/Hybrid; 8 more mislabeled-Petrol TDI rows + 4 e-Golf rows needed fuel fixes).

## Engine families mapped (web-verified)
- **1.8T:** AWP 180 (Mk4 GTI/GLI), AWV 150 (New Beetle), AWM 170 (B5.5 Passat), CXBA/CXBB 170 (EA888 Gen3 — DB NULL rows filled; CXBA now n=27).
- **2.0T 200hp:** BPY (FSI 2006-08) → CCTA/CBFA (TSI 2008.5+) across Jetta GLI/GTI/Passat/CC/Tiguan (CCTA n=70 — biggest target).
- **2.0T Gen3/3B:** CXCA (US GTI 15-16 210hp), CXCB (GTI 17-21 220hp), CXDA (GLI 19-25 228 / GTI Mk8 241hp), CYFB (US Golf R 292hp — see collision below), DGUA (Tiguan Budack 184hp), plus new descriptive rows for Atlas 2.0T (235hp; 269hp evo4 2024+), Arteon 268hp, Beetle/Passat-GT low tune 174hp.
- **TDI lineage:** BEW → BRM (Pumpe-Düse 100hp), BHW (B5.5 Passat 134hp), CVCA (EA288 150hp — VW media: all 2015 Golf/Jetta/Passat/Beetle TDI = EA288, 140→150hp).
- **VR6 EA390:** BKL (Touareg 3.2 220hp), BUB (R32 Mk5/Eos 3.2 250hp), BLV (Passat B6 3.6 280), CNNA (CC/NMS 3.6 280), CGRA (Touareg 3.6 — pre-existing row, relabeled), CDVC (Atlas 3.6 276hp), 2.8 VR6 24v (Mk4 GTI 200hp, new row).
- **Oddballs:** AXQ 4.2 V8 (Touareg 306hp), 5.0 V10 TDI 310hp (US 2006-07 only — Autoblog + green.fandom; 2008 row skipped), 3.0 V6 TDI (221/240hp), 3.0 TSI Hybrid 380hp system, 6.0 W12 Phaeton 420hp, 1.4 TSI Hybrid (Jetta 170hp system), e-Golf EV 134hp, 1.5 TSI evo (Taos/Jetta 2022+ 158hp), Routan = Chrysler RT rebadge (3.8 197hp / 4.0 251hp descriptive rows — DB's EGH row is mislabeled junk, left for future audit).

## US-lineup findings
- **2019 Golf dropped the 1.8T for the 1.4T 147hp** (JD Power); 2021 = last US base Golf (1.4T); 2025 bare Golf skipped (GTI 241 vs R 328 unknown).
- **Golf Mk4.5 TDI sold in Canada as a full 2006 MY** (Wikipedia) → Golf 2006 1900cc = BRM with Diesel fuel fix.
- **Atlas 2.0T = 235hp (2021-2023 US; Canadian-market 2018+ per lemon rows), 269hp evo4 2024+ with V6 dropped** (US News + C/D).
- **Touareg V10 TDI: US 2006-2007 only** (2004 limited, then CARB-cancelled) — 2008 5000cc row skipped.
- **2015 Beetle TDI = EA288 150hp** (VW media release — replaced the 140hp EA189).

## Skips (3, intentional)
- Passat 2005 2800cc — anomalous (no 2.8 V6 in MY2005; B5 2.8 ended MY2000, B6 launched 2006).
- Touareg 2008 5000cc — V10 TDI cancelled in US after MY2007.
- Golf 2025 bare — GTI 241hp vs Golf R 328hp undeterminable.

## step26b + audit findings
20 ESTIMATE overrides + 6 normalizations + 28 power syncs. Externally verified: **GTI Mk8 0W-20/5.7L VW 508.00** (AMSOIL/shopdap — exactly the lemon majority), **2019+ 1.4T 0W-20 4.0L** (oilchangers), Golf R/GLI 5.7-6.0qt (dealer tech), EA288 TDI capacity kept at lemon-unanimous 5.48L (documented VW-spec confusion: official 4.7L vs VW site 6.3L).

## Incident: silent code collisions (NEW STANDING RULE)
The pre-apply assert checked targets exist in `engines` OR `NEW_ENGINES` — but two codes **already existed as other engines**: `CYFB` = Ford Transit 2.2 TDCi (my 2 Golf R petrol variants got linked to a Ford diesel row, and step26b overwrote the Ford spec's oil values) and `DGUA` = a NULL junk row (insert skipped, 7 Tiguan variants sat on NULLs). step26c repaired both: new "2.0 TSI EA888 Gen3 (Golf R)" row, Golf R relink, Ford CYFB spec+tech restored from pre_step26 backup, DGUA filled (184hp) incl. a pre-existing 2021 Tiguan NULL-power variant. CGRA also pre-existed (values correct, relabeled). CXBB spec power NULL → 170.
**Rule going forward:** when a rule target already exists in `engines`, assert its identity (fuel/displacement/brand compatibility) — existence alone is not enough.

## Incidents
- 9th full workspace rewind caught by baseline assert pre-work (no loss).
- Fixed in dry-run phase: Beetle 2015 VIN S/T rows wrongly matched the CVCA TDI rule (rule order — fixed with a fuel-column check); Beetle 1.8T rule year gap (2017).

## Next
Infiniti 230 → Dodge 207 → Buick 205 → Subaru 205 → Land Rover 194 (DB junk noted for LR batch: 306DT label "3 (est.)", EGH mislabel, AJ200/AJ41 vocabulary).
