# STEP 5 — Batch 27: GMC + Chevrolet LEMON Replacement (Step 36)

**Date:** 2026-10-01 · **Scripts:** `step36_step5_lemon_batch27_gm_truck.py` + `step36b_estimate_override.py` + `step36c_fix_gm_engine_rows.py` + `step36d_gm_fuel_and_duplicate_cleanup.py`
**Result:** 209 LEMON rows (GMC 156 + Chevrolet 53) → **208 mapped (99.5%) / 1 documented skip**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 1,368 | **1,160** (−208) |
| LEMON GMC / Chevrolet | 156 / 53 | **1 / 0** |
| engines rows | 6,986 | **6,782** (−208 LEMON +5 new −1 duplicate) |
| GMC + Chevrolet fuel conflicts | 42 | **0** |
| DB-wide fuel conflicts | 271 | **205** |
| GMC + Chevrolet variants with NULL power | 114 | **9** |
| Orphans / count mismatches | — | **0 / 0** |

GMC fuels after: Petrol 609 · Diesel 97 · Hybrid 6 · Electric 4.
Chevrolet fuels after: Petrol 1,675 · Diesel 221 · Hybrid 20 · Electric 9.

## Why GMC and Chevrolet are one batch

This is the first **merged engine-family batch**. GMC has never had its own engine catalogue: every
engine in the 209 rows is a GM corporate RPO shared with Chevrolet (and often Buick/Cadillac/
Pontiac/Saturn/Hummer/Isuzu) — Vortec and EcoTec3 V8s, the Atlas I6, the High Feature V6 family,
the Ecotec I4 family, the 6.5 Detroit Diesel and the Duramax. Decoding them together means one
evidence set, one vocabulary and no risk of the same RPO being created twice under two batches.
`step5_lemon_lib` was extended for this: `Cfg.brand` now accepts a list, rules may be keyed
`"BRAND:MODEL"` when a model name would be ambiguous, and decisions/skips carry the brand.

## Method — RPO code via displacement + VIN 8th digit + model year

**GMC**

- **Acadia** (Lambda → C1): LY7 3.6 275 (`2007`) → LLT 288 (`2008-12`) → LFX 288 (`2013-16`) →
  LGX 310 (`3600CC`, `2017-23`); LCV 2.5 193 (`2500CC`); LSY 2.0T **230** (`2020-21`) / **228**
  (`2022-23`, revised rating); **LK0 2.5T 328** as the sole engine for `2024-25`. [GMA_LK0]
- **Terrain**: VIN 8th digit is decisive — `K` = 2.4 LAF 182 (`2010-11`) / LEA 182 (`2012-17`),
  `5` = 3.0 **LFW** 264, `3` = 3.6 LFX 301, `V` = 1.5T LYX 170, `X` = 2.0T LTG 252,
  **`U` = 1.6 LH7 turbodiesel 137** (fuel corrected Petrol → Diesel). Bare `2021-25` rows = LYX
  175, the only engine after the 2.0T was dropped. [CPP_TERRAIN]
- **Envoy**: 4.2 Atlas I6 LL8 at 270 (`2002`), 275 (`2003-05`), **291** (`2006-09`); the 5.3 V8
  is **LM4** 290 for `2003-05` Envoy XL/Denali and **LH6** 300 with Displacement on Demand for
  `2006-09`. The `2000` row predates GMT360 and is the Jimmy-based Envoy trim → LU3 4.3 190.
  [TCC_ENVOY][JDP_ENVOY]
- **Hummer EV** (`2022-25`): GM Ultium tri-motor e4WD, 1,000 hp / 1,200 lb-ft, 205 kWh —
  **fuel Petrol → Electric** on all four rows. Later dual-motor EV2/EV2X trims (570-625 hp) are a
  detune of the same unit and are documented on the engine row rather than split. [CD_HUMMER]
- **S/T platform** (Jimmy, Safari, Sonoma, and Chevrolet S10/Cavalier): LU3 4.3 190 and LN2 2.2
  115/120, both single-engine families in these years.
- **Full-size**: Sierra 4.3 LU3 200 (`2000-01`); 5.3 EcoTec3 L82 355 (`2019`) → L84 355
  (`2022-25`); Yukon L83 355 (`2016-18`) → L82 (`2019-20`) → L84 (`2021`).
- **Heavy chassis**: C3500 7.4 **L29** 290 (`2000`, final year) → 8.1 **L18** 340 (`2001-02`);
  every `6500CC` row (C3500, the placeholder "Cab" and "Pickup" models, Savana) is the
  **6.5 Detroit Diesel V8 L65** — 10 rows fuel-corrected Petrol → **Diesel**. [GM65][GM74]

**Chevrolet**

- **Corvette** C5 `2001-04` = LS1 350 base (Z06 LS6 optional). **Camaro** = LLT 312 (`2010-11`) →
  LFX 323 (`2012-13`). **SSR** = LM4 5.3 300. **Silverado** = L82 355 (`2019`) → L84 355 (`2024-25`).
- **Cars**: Cavalier LN2 115; Cobalt/HHR 2.2 **LAP** 148/149; Impala 2.5 **LKW** 196;
  Malibu LFX 252 (`3600CC VIN7`), LUK 2.4 eAssist 182 (`2400CC 2014`), **LFV** 1.5T 160 (`2016`);
  Captiva Sport LEA 182; Blazer `2024-25` LSY 2.0T 228 (the 3.6 LGX 308 is RS-only). [GMA_BLAZER]
- **Canada-only Daewoo-built models**: **Optra / Optra5** (Lacetti, `2004-08`) = 2.0 D-TEC
  **T20SED** 119 hp, the car's only engine; **Epica** (`2004-06`) = the transverse **2.5 inline-six
  X25D1** 155 hp, not the 2.0 four. [OPTRA][EPICA]
- **Suzuki-built**: Metro 1.3 **G13BB** 79; Tracker 1.6 **G16B** 97 (`2000`) and the final-year
  `2004` LT → 2.5 V6 **H25A** 165.
- **Placeholder model names** "RV" and "Cutaway" are GM commercial chassis: `6500CC RV` = L65
  diesel (fuel-corrected), `2003-05 RV` = the P32 motorhome chassis whose only gas engine after the
  6.5 diesel was dropped is the 8.1 **L18** 340, and the Express/G-series `Cutaway` = 6.0 **LQ4** 300.

**Volume-defaults** (used only on bare rows with no displacement, each documented in the evidence
column): Acadia `2017` → 2.5 LCV; Sonoma `2004` and S10 → 2.2 LN2; Savana `2003` → 4.3 LU3;
Sierra/Silverado `2019` → 5.3 L82 and `2024-25` → 5.3 L84; Yukon `2016-20` → 5.3; Blazer → 2.0T LSY;
Camaro/Impala/Malibu/Cobalt/HHR/Cavalier/Corvette → the base engine, with the optional V8/V6 noted.

## 5 new engines

| Code | Engine | Fuel | cc | hp |
|---|---|---|---|---|
| `L65` | 6.5 V8 OHV turbodiesel (Detroit Diesel) | Diesel | 6500 | 195 |
| `LAP` | 2.2 I4 Ecotec VVT (Cobalt/HHR/G5) | Petrol | 2198 | 149 |
| `LKW` | 2.5 I4 Ecotec DI (Impala 2014-20) | Petrol | 2457 | 196 |
| `LK0` | 2.5 I4 Turbo DI (Acadia/Traverse 2024+) | Petrol | 2500 | 328 |
| `Ultium e4WD (Hummer EV)` | GM Ultium tri-motor e4WD, 205 kWh | **Electric** | — | 1000 |

The other 31 targets (LU3, LN2, LL8, LFX, LLT, LGX, LCV, LSY, LTG, LAF, LEA, LUK, LFW, LQ4, L18,
LS1, X25D1, T20SED, L82, L83, L84, LY7, LM4, LH6, L29, LFV, LYX, LH7, G13BB, G16B, H25A) already
existed and were reused.

## Fixes beyond the mapping

**12 ROW_FIXES in step36** — cylinder counts that were plainly wrong on engines shared with this
batch: **LU3 8→6** (4.3 V6), **LL8 8→6** (4.2 inline-six), **LFX 8→6** (3.6 V6), plus NULL-cylinder
fills on LCV/LSY/LTG/LGX/LEA/LAF/LUK/L82 and an L84 descriptor + 355 hp.

**step36b** — oil-spec normalization over the 36 targets: 5 ESTIMATE overrides (G13BB, G16B, LFW,
T20SED, X25D1), 5 normalizations (L18, LFV, LH7, LS1, LSY), 7 power syncs. **0 ESTIMATE oil specs
and 0 spec-vs-engine power mismatches remain among step-36 targets.**

**step36c** — 21 pre-existing junk engine rows repaired (descriptors only, no mapping change):
`G16B` engine_type was literally **"JETSTAR"**; bare "1.3"/"2.0"/"6.0"/"3.0 Petrol"/"2.4 16v"
placeholders replaced with real descriptors; **LN2** had NULL engine_type *and* NULL cylinders;
**LS1** was advertised as a **Daewoo Adventra** and is now exemplified by the 2001 Corvette;
brand/model/year examples filled for L29, L83, LM4, LFV, LYX, LH7.

**step36d** — integrity cleanup that the audit exposed:
- **Duplicate engine retired**: the crawl had already imported the 6.5 Detroit Diesel as the
  free-text code `6.5 TD V8 (L65)` (10 Chevrolet variants). Specs merged into the new RPO row
  `L65`, variants relinked and fuel-corrected, free-text row deleted → `L65` now holds 20 variants.
- **Engine fuels corrected**: `A16XER` (1.6 Ecotec **petrol**, filed as Diesel — 32 variants) and
  `LFA` (6.0 two-mode **hybrid**, filed as Petrol).
- **27 variant fuel corrections**: Duramax `L5P`/`LMM`/`LML`/`LBZ` rows labelled Petrol → Diesel
  (16), and `L8B`/`LZ1`/`LFA` two-mode/eAssist hybrids → Hybrid (11).
- **Missing engine metadata filled**: L5P 445 hp, L3B 310, LS9 638, LT5 755, LF3 420, LT1 6162 cc,
  plus cylinder counts on L87/L8T.
- **105 NULL variant powers backfilled** for GMC/Chevrolet from their engine rows.

## Skip (1, documented)

| Row | Reason |
|---|---|
| `LEMON_GMC_SIERRA_6000CC_VINJ_2012` (variant 34407) | GM reused VIN 8th digit **J** across engines: it is the 6.2 L86 from 2014, but for a MY2012 6.0-litre HD truck it points at either **L96** (360 hp petrol) or **LC8** (306 hp, gaseous-fuel capable) and no consulted source resolves the digit for that year. Two candidates differing by 54 hp *and* by fuel type — left as LEMON rather than guessed. |

The 9 remaining GMC/Chevrolet rows without a power figure are this skip plus 8 rows that carry **no
engine_code at all** (pre-existing crawl rows, outside the LEMON scope).

## Evidence

[GMA_LK0] gmauthority.com LK0 engine page + 2024 Acadia EPA ratings ·
[GMA_BLAZER] gmauthority.com 2024 Chevrolet Blazer ·
[CPP_TERRAIN] carpartplanet.com Terrain engine fitments by VIN digit + OEM part listings ·
[TCC_ENVOY] thecarconnection.com 2005/2006 Envoy specifications + cars.com 2006 Envoy ·
[JDP_ENVOY] jdpower.com GMC Envoy model history ·
[CD_HUMMER] caranddriver.com Hummer EV 2023/2024 + motortrend acceleration test ·
[OPTRA] chevycamaro.fandom Chevrolet Optra + autotrader.ca 2005 Optra + auto123 specs ·
[EPICA] ca.finance.yahoo.com "10 Canadian cars you can't buy in the U.S." ·
[GM65]/[GM74] GM 6.5 Detroit Diesel and Vortec 7400/8100 application history ·
[GMVOCAB]/[GMLINEUP] existing verified GM RPO rows in `engines` + US/CA lineup ratings.

## Files

- `step36_step5_lemon_batch27_gm_truck.py`, `step36b_estimate_override.py`,
  `step36c_fix_gm_engine_rows.py`, `step36d_gm_fuel_and_duplicate_cleanup.py`
- `database_enriched/csv_exports/44_lemon_step36_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step36_2026-10-01.db`

**Next: Batch 28 — Mitsubishi (138 LEMON rows).**
