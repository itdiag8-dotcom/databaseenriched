# STEP 11 — Cylinders, Displacement, and a Systematic Column Bug (Steps 64 / 64b)

**Date:** 2026-10-01 · **Scripts:** `step64_step11_engine_attributes.py`, `step64b_ev_attributes.py`

| Metric | Before | After |
|---|---|---|
| Engine rows with NULL cylinders | **104** | **36** — all electric/FCEV, correct |
| …of which combustion rows genuinely missing it | **68** | **0** |
| Engine rows with NULL displacement | **73** | **49** — all electric/FCEV, correct |
| …of which combustion rows genuinely missing it | **24** | **0** |
| Rows with a model designation in the displacement column | **14** | **0** |
| Electric rows carrying cylinders/displacement | **13** | **0** |
| Implausible cylinder/displacement combinations | 9 | **0** |

## "104 NULL cylinders" was three different problems

**1. Not missing at all (36 + 49 rows).** Leaf, i3, Bolt, Tesla, Mirai, the Ultium Hummer — an
electric motor has no cylinders and no displacement, so NULL is the correct value, not a gap.
These are left alone and documented, the same call made for the 147 zero-variant rows in Step 10.
Counting them as defects was overstating the problem by roughly half.

**2. Genuinely missing (68 cylinders + 24 displacements).** Overwhelmingly the same family stems
and sales codes Step 8 gave a power figure to. Where the row's own descriptor names the layout
("6.2 V8 Supercharged", "4.0 H6 NA") the text decided; otherwise the engine family did, exactly
as in Step 8.

**3. A systematic bug, not a typo.** Step 8 found `N53B3O0` recorded as **630cc** because the
model designation "630i" had leaked into the displacement column. It turns out to be a pattern —
13 more rows have it, and every one of them states its true displacement in the same string:

| Code | Descriptor | Was | Now |
|---|---|---|---|
| `M275KE55LA` | "CL600 5500 V8 TwinTurbo" | 600cc, 8cyl | **5513cc, 12cyl** |
| `N62B48TU` | "650i 4800 V8" | 650cc | 4799cc |
| `N62B36` / `N62B40` / `N62NB40` | "735i 3600 V8" / "740i 4000 V8" | 735 / 740cc | 3600 / 3999cc |
| `M62TUB35` / `M62TUB44` | "735i 3500 V8" / "740i 4400 V8" | 735 / 740cc | 3498 / 4398cc |
| `M57D30A` / `M57TU2D30TOP` | "730d 3000 D" / "635d 3000 D" | 730 / 635cc, **3cyl** | 2993cc, 6cyl |
| `M67D39` / `M67TUD39` / `M67D44` | "740d 3900 D" / "745d 4400 D" | 740 / 745cc, **3cyl** | 3901 / 4423cc, 8cyl |
| `M51D25S` | "725tds 2500 D" | 725cc, **3cyl** | 2497cc, 6cyl |

Note the knock-on: the cylinder counts were wrong *because* the displacement was. Something
derived "under 1 litre → 3 cylinders", so a 3.0 straight-six diesel was recorded as a triple and
a 4.4 V8 diesel likewise. The bug corrupted two columns from one bad value.

`M275KE55LA` is the worst of them: a CL600's M275 is a **5.5 V12 biturbo**, so its descriptor's
"V8" was wrong too, and that has been corrected as well.

## 16 more cylinder counts contradicted by their own descriptor

`EZ36D` said "3.6 H6" with 8 cylinders; `N74B66A` "6.6 V12" with 8; `ETJ`/`ETC` Cummins
straight-sixes with 8; `B3815KT0` (i8) "1.5 I3" with 4; `1LR-GUE` (LFA) "4.8 V10" with 8. All
corrected from the token in their own text.

**One was excluded:** `D4FD-L` reads "3.0 -24 V6" on a 1685cc Hyundai 1.7 diesel. There the
*descriptor* is the wrong half, not the cylinder count, so changing cylinders to 6 would have
made it worse. It belongs to the descriptor cleanup and is logged there.

## Step 11b — the mirror-image defect

13 pure-electric rows carried **4 cylinders**, inherited from an integration default. Cleared.
Hybrids were deliberately left alone: a hybrid genuinely has a combustion engine, so `2AR-FXE`
at 2493cc/4cyl is correct.

One of the 13 turned out not to be electric at all. `A14XFL` — fuel Electric, 151hp, 4
cylinders, no displacement, on an Opel/Vauxhall **Ampera** — is the European Chevrolet Volt, and
A14XFL designates its 1.4 petrol range extender. The database already models that car correctly
as `Voltec 1.4 EREV (Volt)`: 1398cc, 4 cylinders, fuel **Hybrid**. A14XFL now matches its own
twin instead of being an "electric engine with four cylinders". Its descriptors were junk too —
"216 1.6i" on the engine row and "FEITENG Closed Off-Road Vehicle" on a Vauxhall Ampera
variant — and both were replaced.

## Files

- `step64_step11_engine_attributes.py`, `step64b_ev_attributes.py`
- `database_enriched/csv_exports/72_engine_attributes_step64.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step64_2026-10-01.db` (local, untracked)

**Next: the 544 `(est.)`/`(corr.)` descriptors and the junk ones found along the way
(`D4FD-L`, `CHZC` "for vehicles with brake booster", `OM660.951` "Repair seating frame").**
