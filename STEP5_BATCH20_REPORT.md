# STEP 5 — Batch 20: Buick LEMON Replacement (step29 / step29b / step29c)

**Date:** 2026-10-01 · **Scope:** 205 `LEMON_BUICK_*` variants, 16 models, MY2000–2025
**Result:** **205 mapped / 0 skipped** — second brand fully cleared (after Infiniti) ·
LEMON total 2,689 → **2,484** · engines 8,250 → **8,047**
Verification: 0 orphan refs, 0 count mismatches, 0 fuel conflicts among Buick-linked codes, 0 ESTIMATE specs among batch targets, 0 spec-power mismatches, 0 NULL powers on Buick rows.

## Signals used
cc markers (2400CC/3600CC/5300CC…), VIN letters (VINR 2.4 eAssist, VIN3/VINS 3.6, VINZ 2.5 eAssist,
VINX 2.0T, VINV/VINK 2.0T/2.4, VINL 1.3T, VIN2/VINP 1.2T, VIN8/VINB/VINM 1.4T), fuel column
(eAssist rows labeled Hybrid), trim slugs (ENCLAVECONVE/LEATH/PREMI = 2015 Enclave → year rule).
Nearly every group carried a cc marker or fell in sole-engine years — zero skips needed.

## Engine families mapped (DB GM vocabulary from Chevy/Cadillac batches reused)
- **3.6 High-Feature genealogy:** LY7 240–275 (Allure/LaCrosse 05-08, Rendezvous Ultra 245,
  Enclave 2008 275) → LLT 280–288 (LaCrosse 10-13, Enclave 09-12) → LFX 288–304 (Enclave 13-17,
  LaCrosse 14-16) → **LGX 310** (LaCrosse 17-19, Enclave 2018+, Regal GS 18-20) — gmauthority
  confirmed the LaCrosse LGX RPO. LF1 3.0 255 (LaCrosse 2010 CXS).
- **3800/3100/3400/3500/3900 OHV fleet:** L36 (LeSabre 205, Park Avenue 205, Regal 195 base — GS L67
  trim never slugged), L26 3800-III (LaCrosse/Allure 200, Lucerne 197 — row repaired from NULL type),
  LG8 3.1 175 (Century), LA1 3.4 185 (Rendezvous 02-05), LX9 3.5 (Rendezvous 195, Terraza 196),
  LZ9 3.9 (Terraza 240, Lucerne 09-11 227).
- **Trucks/BOF:** LL8 4.2 I6 275→291 (Rainier), LM4/LH6 5.3 290→300 (Rainier AFM), LS4 5.3 FWD 300
  (LaCrosse Super — DB already had Allure LS4 links), LD8 4.6 Northstar 275 (Lucerne = DTS sibling).
- **Modern 4-cyl turbo lineage:** LTG 2.0T 259 (Regal 14-17) / 250 (Regal 18-20, Verano Turbo) /
  252 (Envision 16-20) — LTG n=142 after batch; NEW `2.0 Turbo (Regal 2011-13)` 220 (LNF-family,
  CXL Turbo; GS 270 same family — RPO ambiguous per CobaltSS forum so descriptive row used);
  LSY 2.0T 228 (Envision 2021+ — NULL row filled, oil 0W-20/5.01L verified via AMSOIL);
  NEW `LWC` 1.6T SIDI 200 (Cascada — C&D engine order code); LUV 1.4T 138 (Encore all years — the
  153hp LE2 option died for 2020 per Car and Driver); LIH 1.2T 137 (Encore GX, Envista); L3T 1.3T
  155 (Encore GX); LE2 1.4T 153 hygiene-filled (NULL junk row, 4 pre-existing Encore 16-19 links).
- **2.4/2.5 NA + eAssist policy:** LAF 182 (LaCrosse 10-11, Regal 11-12), LEA 180-182 (Verano 2.4,
  Regal 1SV 2017), LCV 2.5 194-197 (Envision 2.5, LaCrosse eAssist 2018-19), LUK 2.4 eAssist 182
  (LaCrosse 2012-16 VINR, Regal 2013). **eAssist mild hybrids kept Petrol** per the DB's established
  convention (5 pre-existing LUK links are Petrol) — 3 Hybrid-labeled LEMON rows fuel-fixed → Petrol.
  Step29c extended the same treatment to 2 pre-existing Chevrolet Malibu BAS-hybrid rows on the
  shared LE5 petrol row (caught by the fuel-conflict audit).

## US-lineup findings (web-verified)
- **Lucerne:** 3.8 = 197hp (not 227), 3.9 = 227, 4.6 = 275 (Edmunds/autoevolution).
- **Rendezvous:** 3.4 185 (02-03 sole; 04-05 std) + 3.6 245 Ultra (04-06); 2006 3.5; **2007 = 3.5
  FWD-only** (jdpower/conceptcarz).
- **Terraza:** 3.5 196 std (05-06) + 3.9 240 opt (06); **3.9 sole from 2007** (jdpower).
- **Rainier:** 4.2 275→291hp and 5.3 290→300hp (AFM) at 2006 (consumerguide/grokipedia).
- **Regal:** 2011 = 2.4 182 / 2.0T 220; 2012 +GS 270 +eAssist; 2014 = single 2.0T 259; 2018-20 =
  2.0T 250 + GS 3.6 310 (cars.com/consumerguide/motortrend).
- **Enclave:** sole 3.6 every year: 275 (08) → 288 (09-12 LLT) → 288 (13-16 LFX) → 310 (2018+) —
  no skips despite 20 bare rows.
- **Encore:** 1.4T 138hp all years; the 153hp LE2 was optional 2016-19 only and killed for 2020
  (Car and Driver/GM Authority); Encore GX = 1.2T 137 / 1.3T 155.
- **LaCrosse:** 3.6 280 (10-13) → 304 (14-16) → 310 LGX (17-19); 2.5 eAssist 194 (18-19);
  2017 was V6-only (iseecars), eAssist returned 2018.

## step29b spec normalization
2 ESTIMATE overrides + 6 majority normalizations + 11 power syncs. Vote line-audit: all majorities
plausible (LAF/LH6/LSY/LTG/LUV/Y7 unanimous; L36 10W-30 x10/17 correct for the 3800; LLT 5.2L
x7/10). LSY 0W-20/5.3qt externally verified (AMSOIL 2021 Envision LSY page — also confirms the
LSY engine code). No contamination (unlike batch 19's EZH case).

## Process notes
- **12th workspace rewind caught** by the baseline guard pre-work (12,637/17,916 signature);
  `git reset --hard origin/arena/...` recovery, no loss.
- IDENTITY assert queued one junk-cc bypass (LSY 2000→1998 via ROW_FIX).
- 4 pre-existing NULL powers swept (LE2 Encore links); 2 pre-existing Malibu BAS-hybrid fuel labels
  fixed (step29c). ESTIMATE specs on 4 Chinese-market codes (Excelle F16D3/A16LET/RA 420, LL6)
  deliberately left — no lemon data, honestly flagged.

## DB state after batch 20
engines **8,047** · LEMON total **2,484** · LTG n=142, L36 n=53, LGX n=78, LFX n=76, LLT n=65.
Next batches (LEMON-count order): Subaru 205, Land Rover 194, Porsche 193, Lincoln 192, Volvo 184,
Acura 180, GMC 156, Mitsubishi 138, Ford 85, Pontiac 85, Genesis 74, Fiat 64, Mercury 63, Saturn 49,
Scion 44, Alfa Romeo 43, Isuzu 35, Saab 34, Mini 31, Suzuki 29, Hummer 19, Smart 12, Tesla 10, Daewoo 9.
