# STEP 5 — Batch 26: Acura LEMON Replacement (Step 35)

**Date:** 2026-10-01 · **Scripts:** `step35_step5_lemon_batch26_acura.py` + `step35b_estimate_override.py` + `step35c_fix_r23a2_duplicate.py`
**Result:** 180 LEMON Acura rows → **180 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 1,548 | **1,368** (−180) |
| engines rows | 7,148 | **6,986** (−180 LEMON +19 new −1 duplicate) |
| Orphans / count mismatches / Acura fuel conflicts | — | **0 / 0 / 0** |
| Acura variants with NULL power | — | **0** |

Acura fuels after: Petrol 189 · Hybrid 11 (NSX NC1 ×6, MDX Sport Hybrid ×2, ILX Hybrid ×2, RLX Sport Hybrid ×1).

## Method — lineup + displacement + VIN engine digit

Acura has never sold a diesel in North America, so every row is petrol or hybrid and the decode is
driven by the model generation, the crawled displacement, and the VIN engine digit where present.

**Nameplate → engine timelines used (all US/Canada market):**

- **MDX** — J35A3 240 (`2001-02`) → J35A5 265 (`2003-06`) → J37A1 3.7 300 (`2007-13`) →
  J35Y5 3.5 Earth Dreams 290 (`2014-25`); **J30Y1** 3.0 Sport Hybrid 321 combined for the
  `2018`/`2020` rows the crawl flags as Hybrid; **J30AC** 3.0 twin-scroll turbo 355 for the
  `3000CC` Type S rows (`2023-25`). [WIKIMDX][PRRJ][TROUBLE][DNJ]
- **RDX** — K23A1 2.3 i-VTEC turbo 240 (`2007-12`, incl. the `VINTB1`/`VINTB2` 2300CC rows) →
  J35Z2 3.5 273 (`2013-15`) / **279** after the 2016 facelift (`2016-18`, same code, VCM gen3) →
  K20C4 2.0T 272 (`2019-25`). [WIKIRDX][WIKIJ][RPMRONS]
- **TL** — J32A1 225 (as the `3.2TL` rows, `2000-03`) → J32A3 270 (`2004-06`) / 258 under the
  revised SAE rating (`2007-08`) → J35Z6 3.5 280 FWD volume engine (`2009-14`). [TROUBLE][MDXERS]
- **TSX** — K24A2 200 (`2004-05`) / 205 (`2006-08`) → K24Z3 201 (`2009-14`); the `3500CC VIN4`
  rows are the V6 sedan → J35Z6 280. [TROUBLE][RPMRONS]
- **TLX** — K24W7 206 (`2400CC`) / J35Y6 290 (`3500CC`) for UB1-UB3 (`2015-20`) → K20C6 2.0T 272
  (`2000CC`) / J30AC 355 (`3000CC` Type S) for UB5-UB7 (`2021-25`). [WIKITLX][DNJ][WIKIJ]
- **ILX** — R20A5 2.0 150 (`VIN1`) / K24Z7 2.4 201 (`VIN2`,`VIN6`) / LEA1 1.5 IMA 111 combined
  (`1500CC`, 2013-14 only) → single K24V7 2.4 201 + 8DCT (`2016-22`). [WIKIILX][RPMRONS]
- **Integra** — B18B1 1.8 140 volume-default for the DC rows (`2000-01`, GS-R/Type R optional);
  L15CA 1.5T 200 (`1500CC` + bare 2023) and K20C8 Type S 320 (`2000CC`) for DE4/DE5. [ACNEWS15][WIKIINT]
- **NSX** — C32B 3.2 290 for every `2000-05` NSX and NSX-T row (the 3.0 automatic was gone before
  these model years); JNC1 3.5 twin-turbo Sport Hybrid 573 (`2017-21`) → 600 for the 2022 Type S
  final year, all six rows fuel-corrected Petrol → **Hybrid**. [ACHYB][LINEUP]
- **RL / RLX / ZDX** — J35A8 300 (`2005-08`) → J37A2 300 (`2009-12`); RLX J35Y4 310 with the
  Hybrid-flagged `2016` row going to the new `J35Y4 SH (Sport Hybrid)` 377 combined; ZDX J37A5 300.
  [PRRJ][RLXPR][ULTRLX][MDXERS]
- **Canada-only** — 1.6EL = D16Y8 127, 1.7EL = D17A2 127, CSX = K20Z2 155 volume-default
  (Type-S K20Z3 197 optional). [ELWIKI][AUTOPIAN]
- **ADX 2025** — L15BE 1.5T 190, per Acura's own engine release. [ACNEWS15]

**VIN tokens.** The crawl's VIN digits for Acura (ILX `1`/`2`/`6`, MDX `2`/`YD2`, RDX
`TB1`/`TB2`/`3`/`4`, TSX `2`/`4`) discriminate drivetrain or chassis within a single displacement,
not the engine, so displacement alone resolves them; they are retained verbatim in the evidence
column for traceability.

**Volume-defaults** (documented, used only where a bare row has no displacement): 3.2CL/3.2TL base
225 (Type-S 260 optional), Integra LS/GS 140, RSX 160, CSX 155, TL 2009-14 FWD 280 (SH-AWD J37A4
305 optional), TSX 2009-14 201, 2021 TLX 272, MDX/RDX/RL/RLX/ZDX/3.5RL/NSX all had a single
non-optional engine in the years concerned.

## 19 new engines

`K24V7` · `B18B1` · `L15CA` · `K20C8` · `J37A1` · `J35Y5` · `J30Y1` · `J30AC` · `C32B` · `JNC1` ·
`K23A1` · `J35Y4` · `J35Y4 SH (Sport Hybrid)` · `J32A3` · `J35Z6` · `K24W7` · `J35Y6` · `K20C6` · `J37A5`

## 7 row-fixes on pre-existing engines

| Code | Fix | Why |
|---|---|---|
| `J35A3` | engine_type `CORVETTE` → `3.5 V6 SOHC VTEC (MDX 2001-2002, 240hp)`, hp 243→240 | junk placeholder string; 240hp is the published MDX YD1 rating |
| `J35A5` | engine_type `3.5 EXi Vtec` → MDX 2003-06 descriptor, hp 256→265 | published +20hp update for MY2003 |
| `J37A2` | cylinders **8→6**, hp 305→300, engine_type → RL 2009-2012 | a 3.7 V6 was recorded as an 8-cylinder |
| `L15BE` | engine_type filled, hp NULL→190, cylinders NULL→4, cc 1500→1498 | was an empty stub; ADX 2025 rating |
| `D16Y8`, `D17A2`, `R20A5` | engine_type descriptors | Acura EL / ILX applications added |

## step35b — spec normalization

10 ESTIMATE oil specs overridden with variant-weighted LEMON-crawl majorities, 3 targets
normalized, 23 service-spec power values synced. ESTIMATE rows remaining among step-35 targets: **0**.

## step35c — R23A2 duplicate retired

The vivid import carried an engine `R23A2` ("2.3 Turbo All-wheel Drive", 2298cc, 239hp, **6
cylinders**) with one variant "Acura RDX 2005". No such Honda code exists — the first-generation
RDX shipped only the K23A1 2.3 turbo **I4** and went on sale for MY2007. Its technical-spec row was
also self-inconsistent (bore 81.4 × stroke 73.6 only reaches 2298cc across six cylinders, versus
the real 86.0 × 99.0 four), so no geometry was carried over. The variant was relinked to K23A1
(year 2005→2007, production window 2007-2012, 239→240hp) and the R23A2 engine/service/technical
rows deleted. K23A1 now carries 8 variants.

## Files

- `step35_step5_lemon_batch26_acura.py` · `step35b_estimate_override.py` · `step35c_fix_r23a2_duplicate.py`
- CSV `43_lemon_step35_decisions.csv` (+DRYRUN) · Backup `pre_step35_2026-10-01.db`
- `step5_lemon_lib.py` extended: model-name matching is now punctuation-insensitive (`NSX-T` ↔ `NSX_T`)
  and the VIN token pattern accepts 3-character codes (`VINYD2`, `VINTB1`).

**Next: GMC + Chevrolet 209 (batch 27).**
