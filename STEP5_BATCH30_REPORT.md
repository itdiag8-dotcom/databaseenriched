# STEP 5 — Batch 30: Pontiac + Saturn LEMON Replacement (Step 39)

**Date:** 2026-10-01 · **Scripts:** `step39_step5_lemon_batch30_pontiac_saturn.py` + `step39b_estimate_override.py` + `step39c_oil_capacity_corrections.py`
**Result:** 134 LEMON rows (Pontiac 85 + Saturn 49) → **133 mapped (99.3%) / 1 documented skip**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 874 | **741** (−133) |
| LEMON Pontiac / Saturn | 85 / 49 | **1 / 0** |
| engines rows | 6,501 | **6,371** (−133 LEMON +3 new) |
| Pontiac + Saturn fuel conflicts | 0 | **0** |
| DB-wide fuel conflicts | 181 | **181** |
| Orphans / count mismatches | — | **0 / 0** |

## Why Pontiac and Saturn are one batch

Both were GM divisions badge-engineering the same platforms in exactly these years, so each row's
engine is already defined by its platform sibling:

| Platform | Pontiac | Saturn | Engines |
|---|---|---|---|
| Epsilon | G6 | Aura | 2.4 LE5, 3.5 LX9/LZ4, 3.6 LY7, 3.9 LZ9 |
| Delta | G5 / Pursuit | ION | 2.2 L61/LAP, 2.4 LE5 |
| Kappa | Solstice | Sky | 2.4 LE5, 2.0 LNF turbo |
| Theta | Torrent | Vue | 2.2 L61, 2.4 LE5/LAT, 3.4 LNJ, 3.5 L66, 3.6 LY7 |
| Lambda | — | Outlook | 3.6 LY7 → LLT |
| U-body | Montana SV6 | Relay | 3.5 LX9, 3.9 LZ9 |
| GM-DAT / Opel / NUMMI | G3, Wave, Vibe | Astra | 1.6 L91/F16D3, 1.8 Z18XER, 1ZZ-FE/2ZR-FE/2AZ-FE |

Decoding them together meant one evidence set and no duplicate engine rows: 26 of the 29 targets
were GM codes already verified in the step 27/36 GMC+Chevrolet batch.

## Method — nameplate + displacement + model-year rating

The Epsilon cars (G6, Aura) are rated three different ways in five years, and the crawl gives
only displacement, so the rating is taken from the year [WIKIG6]:

| | 2005 | 2006 | 2007 | 2008-2010 |
|---|---|---|---|---|
| 2.4 LE5 | — | 169 | 169 | **164** (SAE re-rating) |
| 3.5 | **200** (LX9) | 200 (LX9) | **224** (LZ4, VVT added) | **219** (LZ4) |
| 3.6 LY7 | — | — | 252 | 252 |
| 3.9 LZ9 | — | 240 | 227 auto / 240 manual | **222** (convertible only) |

Other decisions: Bonneville 3.8 L36 205 and the GXP's 4.6 Northstar LD8 275; Grand Prix 3.8 L26
200 (the supercharged L32 was GTP-only, so the base engine is the volume default) and the GXP's
5.3 LS4 303; G8 3.6 LY7 256 / 6.0 L76 361 / GXP 6.2 LS3 415; GTO 6.0 LS2 400; Montana SV6 and
Relay 3.5 LX9 200 → 3.9 LZ9 240 once the 3.5 was dropped; Torrent 3.4 LNJ 185 with the GXP's
3.6 LY7 264; Vibe = NUMMI Matrix, 1.8 1ZZ-FE 126 → 2ZR-FE 132 and 2.4 2AZ-FE 158; G3/Wave =
Aveo, 1.6 L91 106 / F16D3 103; Astra = Opel Astra H 1.8 Z18XER 138; Outlook 3.6 LY7 275 → LLT 288.

### Two findings

1. **The Saturn Vue's V6 is a Honda engine.** From 2004 to 2007 every six-cylinder Vue used
   Honda's J35S1/J35A3 with a Honda five-speed, catalogued by GM as **L66**, 250 hp — the only
   GM vehicle ever to ship a Honda engine [WIKIVUE][CG_VUE]. The three `VUE_3500CC_2005..2007`
   rows go to the new `L66` row, *not* to GM's 3.5 LZ4, which only appears on the second-
   generation Vue from 2008 (219 hp).
2. **`LEMON_SATURN_VUE_2400CC_2007` is a hybrid.** The first-generation Vue was never offered
   with a petrol 2.4; the only 2.4 was the Green Line's BAS mild hybrid (**LAT**, 170 hp), and
   only in 2007 [WIKIVUE]. The row's fuel was corrected to Hybrid. (The 2008-2010 `VUE_2400CC`
   rows are the second-generation petrol LE5 169 hp and stay petrol.)

## 3 new engines

| Code | Engine | cc | hp | fuel |
|---|---|---|---|---|
| `L66` | 3.5 V6 SOHC 24v = Honda J35S1/J35A3 as fitted by GM (Vue 2004-07) | 3471 | 250 | Petrol |
| `L81` | 3.0 V6 DOHC 24v (Saturn L-series/L300, Opel-derived) | 2962 | 182 | Petrol |
| `LAT` | 2.4 I4 Ecotec BAS mild hybrid (Vue/Aura Green Line) | 2384 | 170 | Hybrid |

## Fixes

**10 ROW_FIXES** (`STEP39_VERIFIED`) — `L61`, `LE5`, `LNF`, `L91`, `1ZZ-FE` and `2AZ-FE` were all
recorded with wrong cylinder counts or bare displacement strings; `LZ4` was carrying the Impala's
211 hp as its headline figure (now 219, with the 224 hp VVT variant noted). Two rows keep a
documented pre-existing conflation rather than being silently split: `L36` also holds Holden
Ecotec 3.8 rows, and `L61` also holds Alfa Romeo 2.2 JTS rows.

**step39b** — 3 ESTIMATE oil-spec overrides, 6 normalizations, 4 power syncs; 0 ESTIMATE specs
and 0 spec-vs-engine power mismatches remain among the 29 targets.

**step39c** — reverted two crawl-majority oil capacities that were worse than what they replaced
(the batch-29 lesson applied as a standing check): `LA1` back to **4.25 L** (the GM 60° V6 takes
4.5 US qt with filter; 3.78 L is the no-filter figure) and `L76` to **5.67 L** (the 6.0 Vortec
takes 6 US qt; the crawl's 8.32 L is a dry-sump Corvette-class number).

## Skips

| Row | Reason |
|---|---|
| `LEMON_PONTIAC_GRAND_2005` | Ambiguous nameplate. Pontiac sold both the **Grand Prix** (3.8 L26 200 hp) and the **Grand Am** (2.2 L61 140 hp / 3.4 LA1 170 hp) in 2005, the crawl truncates both to "Grand", and this row carries no displacement to separate them. The displacement-bearing 2005 Grand rows (3800CC, 5300CC) are unambiguously Grand Prix and were mapped; only the bare row stays LEMON. |

## Known residual (not this batch)

Nine `Saturn Astra` variants with NULL years carry Opel diesel codes (`X17DTL`, `Y17DT`,
`X20DTL`, `Y20DTH`, `Z13DTH`, `Z17DTH`, `Z19DTJ` ×2, `Z19DTH`). Saturn never sold a diesel in
North America — these are Opel Astra H rows mis-branded Saturn upstream. They are internally
consistent (variant fuel = engine fuel = Diesel) so they raise no conflict, and rebranding rows is
out of scope for Step 5; logged here for a later brand-hygiene pass.

## Evidence

[WIKIG6] en.wikipedia.org Pontiac G6 (year-by-year engine and rating table) ·
[WIKIVUE] en.wikipedia.org Saturn Vue (first-gen engine list incl. L66 = Honda J35S1 250 hp and
the 2.4 LAT Green Line) · [CG_VUE] consumerguide.com 2002-07 Saturn Vue (2.2 143 hp, 2.4 170 hp,
3.0 181 hp, Honda 3.5 250 hp) · [GM34OIL]/[GM60OIL] GM 60° V6 and 6.0 Vortec oil capacities ·
[GMLINEUP]/[GMVOCAB] GM US/Canada lineup ratings by model year + the GM engine rows verified in
steps 27 and 36.

## Files

- `step39_step5_lemon_batch30_pontiac_saturn.py`, `step39b_estimate_override.py`,
  `step39c_oil_capacity_corrections.py`
- `database_enriched/csv_exports/47_lemon_step39_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step39_2026-10-01.db`

**Next: Batch 31 — BMW (83 LEMON rows).**
