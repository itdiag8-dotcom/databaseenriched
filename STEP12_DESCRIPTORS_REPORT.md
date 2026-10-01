# Step 12 — Engine descriptor cleanup (`engine_type`)

**Date:** 2026-10-01 · **Scripts:** `step65_step12_descriptors.py`, `step65b_descriptor_leftovers.py`
**Decision CSVs:** `csv_exports/73_descriptors_step65.csv`, `csv_exports/75_descriptor_leftovers_step65b.csv`
**Worklist produced:** `csv_exports/74_suspect_cylinders_worklist.csv`
**Backups:** `backups/car_database_backup_pre_step65_2026-10-01.db`, `…_pre_step65b_2026-10-01.db`

## Result

| | before | after |
|---|---|---|
| engine rows with `(est.)`/`(corr.)` in the descriptor | 540 | **0** |
| variant rows with `(est.)`/`(corr.)` | 506 | **0** |
| engine rows whose descriptor says nothing about an engine | 254 | **3** |
| variant rows whose descriptor says nothing about an engine | 1,045 | **19** |
| engine rows with a NULL descriptor | 53 | **0** |
| engines / variants | 5,670 / 37,444 | 5,670 / 37,444 (unchanged) |

Invariants after both scripts: **0 fuel conflicts, 0 orphan references, 0 `count_variants` mismatches.**
2,705 column updates in total (1,626 + 1,079); no rows created or deleted.

## Two different problems, deliberately solved differently

### A. `(est.)` / `(corr.)` markers — stripped (879 rows)

These are *provenance* notes embedded in a *human-readable* field. The database already has a
column for provenance, `data_confidence`, and the two disagreed constantly:

| marker | `TRUSTED_AFTERMARKET` | `OEM_VERIFIED` | `ESTIMATE` |
|---|---|---|---|
| `(corr.)` | 281 | 4 | 85 |
| `(est.)` | 88 | — | 81 |

A row reading `"1.6 (est.)"` while `data_confidence = OEM_VERIFIED` is worse than no marker at
all: a consumer must pick which of the two fields to believe. The markers were removed from the
text; **`data_confidence` was not touched** and is now the single source of truth for reliability.

### B. 254 descriptors that describe no engine — rebuilt (747 rows incl. variants)

These arrived with the aftermarket catalogue import and fall into four groups:

- **another manufacturer's model name**: `GAZELLE` on nine Mercedes rows (M157.981 ×35 variants,
  M157.980 ×33), `HHR` on an M156, `NEDCAR`, `LEMANS`, `MALIBU`, `MATERIA (M4_)`, `WUNDERFUL RICH`
- **literal workshop operations**: `without tensioner pulley damper`, `Make centre right seat
  functional`, `Repair fuel distributor/rail`, `Radiator grille touch-up paint`, `Various checks`
- **stray catalogue fragments**: `Water tap`, `Plug Housing`, `Fording Ability`, `Tooth System`
- **bare numbers left behind by the markers**: `3 (est.)` ×21, `2 (est.)` ×15, `1 (est.)` ×9

Each was rebuilt from the row's own verified numbers as **`"5.5 L Petrol"`**. The original string
is preserved in the decision CSV.

## Three judgement calls worth recording

**1. No cylinder count in the rebuilt text — the obvious format would have laundered an error.**
The natural output is `"5.5 V8 Petrol"`, but these rows' cylinder counts cannot be trusted:
**78 of the 254 carry an implausible count.** `1AR-FE` (Toyota 2.7, a four) says 6; `B5254T12`
(Volvo 2.5, a five) says 6; `BARRA245T` (Ford Barra, a straight-six) says 8; `OM651.957`
(Mercedes 2.1, a four) says 6. That is not a coincidence — the junk descriptor and the junk
cylinder count came from the same bad import, so the rows with the worst text also have the worst
numbers. Writing those into prose would turn a numeric error into a sentence that reads like a
fact. Displacement and fuel — both corroborated during Steps 6-11 — carry the descriptor instead.

**2. No layout letter either.** `"V6"`/`"I4"` is not derivable from a cylinder count: BMW,
Mercedes and Volvo straight-sixes would all be mislabelled `V6`. Omitted rather than guessed.

**3. A badge is kept only when it belongs to the brand that uses it (33 engine + 52 variant rows).**
`T5` on a Volvo is that car's own output badge; `HHR` on a Mercedes is a Chevrolet model name
that leaked in. The rule checks the token against the row's own `brand_example`/`car_brand`:
Volvo `T3`-`T8`/`D3`-`D5`, Mini/BMW `Cooper`/`One`, Mercedes `AMG`, Audi `S`/`RS`. So
`B5254T12` → `2.5 L Petrol (T5)` and `M113.993` → `5.4 L Petrol (55 AMG)`, while `1AR-FE`
→ `2.7 L Petrol`, dropping `NEDCAR` entirely. A pleasing confirmation that the brand check works:
`1ND` carried `One D` with `brand_example = MINI` and was kept — the 1ND-TV really is the Toyota
diesel used in the Mini One D.

## What step65's own verification then exposed (step65b)

Two defects the first script could not see, both found by re-running the checks rather than
trusting the summary:

- **53 engine rows had a NULL descriptor, not an empty one**, so `WHERE engine_type IS NOT NULL`
  skipped them silently. All 53 had a usable displacement, several on high-traffic rows: `ESA`
  (6.4 HEMI, 29 variants), `N52`/`N51` (3.0, 27/20), `N63` (4.4, 15), and `ETL`/`ETM` — the
  Cummins pair unmasked by their oil data back in Step 8.
- **1,045 variants carried junk text of their own on a perfectly good engine row.** step65 only
  resynced variants that *repeated* their engine's junk string. 1,026 of these simply inherited
  the engine row's descriptor, which already described the engine correctly.

A `LIKE '% L %'` probe for variant/engine disagreement returned 4 hits, all false positives —
`LS460 **L** 4.6 V8` (long wheelbase) and `29 **L** 13`. The second was nonetheless a real find:
it was one of the 1,045.

## Documented exceptions (22 rows, left alone)

`Y4F1` (4 variants, `CITYROVER`), `3CG401` (`80`) and `5DC700` (`Various checks`) have **no
displacement recorded**, so there is nothing factual to build a descriptor from. Inventing one
would be worse than the junk string, which at least reads as obviously wrong. They are listed as
`SKIP_NO_DATA` in the CSVs, together with their 19 variants.

## Next

`csv_exports/74_suspect_cylinders_worklist.csv` — the 32 highest-confidence cylinder-count
suspects found while doing this, ranked by variant count, each with its cc-per-cylinder ratio.
This is the natural next step: Steps 11 and 12 both kept running into wrong cylinder counts, and
there is now a concrete list.
