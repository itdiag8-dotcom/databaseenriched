# STEP 7 — Variant Power Backfill (Step 60)

**Date:** 2026-10-01 · **Script:** `step60_step7_power_backfill.py`
**Result:** 535 NULL-power variants → **357**; 178 filled, 7 deliberately left blank

| Bucket | Before | After |
|---|---|---|
| Variants with no `engine_power_hp` | **535** | **357** |
| …whose engine row knows the answer | 185 | **7** (documented skips) |
| …whose engine row is blank too | 342 | 342 *(Step 8)* |
| …with no `engine_code` at all | 8 | 8 *(later)* |
| Fuel conflicts / orphans / count mismatches | 0 / 0 / 0 | **0 / 0 / 0** |

`engine_power_kw` was filled alongside on all 178 rows, at the DB's own convention
(kW = hp × 0.7355, verified against populated rows: 188hp → 138.3kW).

## This was not a copy job

The worklist called these 185 rows a "trivial backfill — inherit the engine row's power". They
are not. Only **19 of the 55 engine codes** have populated sibling variants that unanimously
agree with their engine row; for the other 36 the row's number is one tune among several, and
copying it blindly would have written 36 wrong figures. Every code was ruled on individually.

### COPY — 131 variants, the row's figure stands
Either the siblings agree (`L87` 420hp across 33 Escalade/Tahoe/Silverado rows, `CXBA`/`CXBB`
170hp across 22 US 1.8T rows, `ED6` 188hp) or the row's descriptor names exactly this
application (`S63B44A` 555hp on an X6 M, `CJWB`/`CJWE`/`CTWB` on the Q7s they describe). Several
are rounding differences between metric PS and hp — `BHE` 250 PS = 247hp, `KFV` 75 PS = 74hp,
`Z16XE1` 105 PS = 103hp — not disagreements.

### RULE — 47 variants, the row's figure was wrong for these cars

| Code | Rule | Evidence |
|---|---|---|
| `ESH` ×12 | 2012-14 → **471**, 2015+ → **485** | The 6.4 HEMI 392 was rerated in 2015 when SRT8 became SRT 392 / Scat Pack. Every pre-2015 sibling (Charger, 300, Durango, Grand Cherokee) reads 471. |
| `LF3` ×12 | Cts → **420**, XTS → **410** | The engine row's own descriptor spells out both tunes: "CTS V-Sport 420hp / XTS 410hp". |
| `N20B20A` ×11 | **245** | 228i/328i/428i/X1 xDrive28i 2014-16 all ran the 240hp SAE / 245 PS tune; the F22/F30/F32 siblings read 245. The row's 215hp *and its 2795cc* describe a 125i — both wrong for these cars. |
| `N63B44A` ×8 | 2012 → **407**, X6 2014 → **449** | The 2014 X6 xDrive50i got the N63TU; the 2012 550i/650i/750i did not. Eight siblings of the earlier era read 407-408. |
| `M54B30` ×2 | **228** | 530i and X5 3.0i ran 231 PS = 228hp; six BMW siblings read 228. The row's 276hp is an Alpina B3 3.3 figure. |
| `N52B30` ×2 | **261** | The 130i ran 265 PS = 261hp, matching the Z4 3.0si siblings; the 215/218/227 siblings are 120i/125i/128i. |

The `L3B` Cadillac CT4 case went the other way and stayed a COPY: 310hp is the CT4-badged
rating (Premium Luxury/Sport) and 325hp belongs to the CT4-V — nothing in these rows says V, so
310 stands. Sources: Cadillac Society 2020-11-18 and the 2022/2023 CT4 trim tables.

### SKIP — 7 variants left NULL on purpose
Six "engine codes" are not codes at all but generic displacement descriptors shared by unrelated
engines, so the row's power came from another manufacturer's car:

| Code | Why no number is honest |
|---|---|
| `1.5 dCI` ×2 | Spans 56-109hp across Renault/Nissan; the 2009 Megane and Scenic each had two tunes. |
| `ZSD-422` | The 2015 Transit alone offered the 2.2 TDCi in 100/125/155 PS. |
| `1.8 16v` | Row's 130hp is a Chery Tiggo; the Caliber 1.8 is a GEMA World engine. |
| `2.0 16v` | Row's 134hp is a Citroën Jumpy; the car is a Grand Vitara. |
| `2.2 dCi` | Row's 134hp is the Almera/X-Trail M9R; the Interstar is a Master-based van on the G9T. |
| `2.4 16v` | Row's 168hp is a Hyundai Sonata; the Grunder is a Galant with the 4G69. |

A blank cell is better than a confident wrong one. These are a natural part of the later
"generic descriptor" cleanup alongside the 544 `(est.)`/`(corr.)` rows.

## Incidental findings (not fixed here)

- **6 exact-duplicate variant rows**: the 12 Cadillac CT4 `L3B` rows are two per model year,
  identical in every column but `id`. Probably the 310hp and 325hp trims collapsed into one
  shape. Candidate for a dedup step.
- **12,869 variants have `engine_power_hp` but no `engine_power_kw`** — a pure arithmetic fill,
  worth a one-liner step of its own.
- The 17 variants under 30hp are all genuine: Renault Twizy, Piaggio Ape, Aixam, Ligier.

## Files

- `step60_step7_power_backfill.py`
- `database_enriched/csv_exports/68_power_backfill_step60_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step60_2026-10-01.db` (local, untracked)

**Next: Step 8 — the 342 variants blocked behind 85 engine rows that have no power figure of their own.**
