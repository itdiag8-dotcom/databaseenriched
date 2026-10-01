# STEP 5 — Batch 21: Subaru LEMON Replacement (step30 / step30b / step30c)

**Date:** 2026-10-01 · **Scope:** 205 `LEMON_SUBARU_*` variants, 13 models, MY2005–2025
**Result:** **199 mapped / 6 skipped (documented ambiguity)** ·
LEMON total 2,484 → **2,285** · engines 8,047 → **7,852**
Verification: 0 orphan refs, 0 count mismatches, 0 fuel conflicts among Subaru-linked codes, 0 ESTIMATE specs among batch targets, 0 NULL powers on Subaru rows.

## Signals used
cc markers (2000/2400/2500/3000/3600CC), fuel column (XV 2014 mild-hybrid, Crosstrek 2021 PHEV,
Solterra mislabeled Petrol → Electric), trim slugs (WRXSTI* 2015, IMPREZA20I4D 2015 trims).

## Key disambiguations
- **Bare "Impreza" rows = non-WRX** (lemon split WRX off as its own model): 2.5i EJ253 (2006-11) /
  2.0 FB20B (2012+). Conversely **IMPREZA_2500CC 2012-13 = "Impreza WRX" EJ255 265hp** (Edmunds —
  WRX was Impreza-badged those years) and IMPREZA_2000CC_2005 = WRX EJ205 227hp.
- **WRX vs STI:** 2015 trim slugs (STI → EJ257 305, others → FA20F 268); 2019-21 split by
  displacement (2000CC = WRX FA20F 268, 2500CC = STI EJ257 310); 2022+ all FA24F 271.
- **Forester 2000CC 2014-18 = 2.0XT** (FA20F 250hp turbo, axed after 2018) — the 2.5 NA is the
  bare/2500CC row.

## Engine families mapped
- **EJ era:** EJ253 2.5 SOHC (Impreza 2.5i, Forester 2.5X, Outback/Legacy 2.5i — 28 rows; relabeled),
  EJ255 2.5T (Impreza WRX 265), EJ257 2.5T (STI 305/310), EJ205 2.0T (2005 WRX 227).
- **EZ flat-6:** EZ30D 245 (B9 Tribeca, Legacy/Outback 3.0R — Euro 241hp row relabeled to US 245),
  EZ36D 256 (Tribeca 3.6R, Legacy/Outback 3.6R — n=30 after).
- **FB modern:** FB20B 2.0 148-152 (Impreza/XV/Crosstrek — n=30), FB25 → relabeled FB25B 2.5
  173-175 (Legacy/Outback 2013-19, Forester 2018), NEW **FB25D 2.5 DI 182** (Forester 2019+,
  Legacy/Outback 2020+, Crosstrek Sport, Impreza RS — n=26).
- **FA D-4S + turbos:** FA20 (BRZ 200hp — n=22), FA24 (BRZ 2022+ 228), NEW **FA20F 2.0 Turbo DIT**
  (WRX 268 / Forester XT 250 — n=16), NEW **FA24F 2.4 Turbo DIT** (Ascent/Legacy XT/Outback XT 260 /
  WRX 2022+ 271 — n=21; codes per Wikipedia FA engine page).
- **Electrified:** NEW XV Crosstrek Hybrid 160hp combined (2014 mild hybrid, MotorWeek), NEW
  Crosstrek Hybrid PHEV 148hp, NEW **Solterra BEV 215hp** dual-motor (Edmunds/KBB) — 3 rows
  fuel-fixed Petrol → **Electric**.

## Skips (6)
Baja 2005-06 bare (2.5 NA 165 vs 2.5T 210), Legacy 2005-07 bare (2.5i vs GT 2.5T, both 2500cc),
Impreza 2500CC 2005 (2.5RS 173 vs STI 300).

## step30b spec normalization + step30c repairs
8 ESTIMATE overrides + 11 power syncs. Vote audit clean — every majority strong and factually
correct (EJ family 5W-30, FB family 0W-20 per Subaru spec; EJ253 x25/28, EZ36D x27/27, FB20B
x25/29). step30c: consolidated the two NULL-junk rows FB25BA/FB25BC (Forester 2014-17, specs
identical to FB25B) into the relabeled FB25 row — 8 variants relinked with 170hp fill; deleted the
all-NULL Solterra spec/tech rows (pure BEV, no oil spec — i3 precedent). Remaining ESTIMATE specs
on Subaru-linked codes (46) are pre-existing Euro-market rows (EE20Z diesel, EJ204/EJ20/EJ22E,
EL15, FB16, EZ30…) — out of US-batch scope, honestly flagged.

## Process notes
- **13th workspace rewind caught** by the baseline guard pre-work (12,637/17,916 signature);
  standard `git reset --hard` recovery, no loss.
- Year-split rules verified: FB25B arrival 2013 for Legacy/Outback (EJ253 through 2012), FB25D
  2019/2020 (Wikipedia FB engine), Forester XT axed after 2018 (torquenews), STI 305→310 at 2019,
  WRX FA20DIT 2015 / FA24F 2022+ (Wikipedia FA engine).

## DB state after batch 21
engines **7,852** · LEMON total **2,285** (Subaru 6 remaining = the documented skips) ·
Electric Subaru rows = 3. Next batches: Land Rover 194, Porsche 193, Lincoln 192, Volvo 184,
Acura 180, GMC 156, Mitsubishi 138, Ford 85, Pontiac 85, Genesis 74, Fiat 64, Mercury 63, Saturn 49,
Scion 44, Alfa Romeo 43, Isuzu 35, Saab 34, Mini 31, Suzuki 29, Hummer 19, Smart 12, Tesla 10, Daewoo 9.
