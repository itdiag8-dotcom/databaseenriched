# STEP 8 — Blank Engine Rows & the Last of the Missing Power (Step 61)

**Date:** 2026-10-01 · **Script:** `step61_step8_engine_power.py`
**Result:** NULL-power variants **535 → 45**; blank engine rows **85 → 14**

| Metric | Start of today | After Step 7 | **After Step 8** |
|---|---|---|---|
| Variants with no `engine_power_hp` | 536 | 357 | **45** |
| Engine rows with no `power_hp` | 85 | 85 | **14** |
| Fuel conflicts / orphans / count mismatches | 137 / 0 / 0 | 0 / 0 / 0 | **0 / 0 / 0** |

312 variants filled, 71 engine rows given a power figure, 30 variants left blank on purpose.
`engine_power_kw` filled alongside on all 312.

## The key observation: most blank rows are truncated duplicates

`N52`, `N63`, `M54`, `S63`, `N20`, `M57` are not engine codes — they are **family stems**, and
the database already holds the fully specified member rows with power, displacement and an
application descriptor. When the variant names its car (`BMW 550i`, `BMW 328i`, `Ram 2500`), the
answer is whatever this database already says about that same car. That made the biggest clusters
internally resolvable, and it keeps the table consistent rather than importing a second opinion:

| Stem | n | Resolved to | Via the DB's own row |
|---|---|---|---|
| `N52` | 27 | 233 / 258 / 268 | `N51B30US` 233 (US 128i/328i), `N52B30A` 258 (X3 3.0si), `N52B30O1` 268 ("X5 30si") |
| `N51` | 20 | 233 | `N51B30US`, the same SULEV 328i |
| `N63` | 15 | 407 | `N63B44`, descriptor "750i/550i 407hp" — every variant here is pre-2014, so pre-N63TU |
| `N55` | 8 | 302 | `N55B30A`, descriptor names X5/X6 xDrive35i |
| `N62` | 4 | 355 | `N62B48`, descriptor "X5 48is 4800 V8" |
| `S63` | 3 | 552 | `S63B44B`, descriptor "M5 4400 V8" |
| `M54`/`M56` | 8 | 189 / 231 | `M54B25` (325Ci), `M54306S3` (530i) |
| `N20`/`N26`/`N54` | 13 | 240 / 245 / 302 | `N20B20 (328i/28i US)`, `N26B20A`, `N54B30O0` |

## Three rows the oil data caught

`ETL` and `ETM` were recorded as **6700cc petrol** Ram 3500 engines. No such engine exists. Their
`engine_service_specs` rows read **11.35 L of 10W-30** — the Cummins 6.7's twelve-quart fill and
its viscosity. They are diesels: fuel corrected on the rows and their 12 variants, displacement
corrected to 6690cc, power set to 370hp. `M57` was the same kind of error — BMW's 3.0 turbodiesel
family stem filed as Petrol, along with its four X5 variants.

This is the `[LEMONFILL]` signal from the LEMON campaign doing its third job: it identified
engine families, then disambiguated trims, and now it has caught a wrong fuel type.

## The research cases

- **`6.7 Cummins ISB` (38 variants)** splits by era: 350hp for 2007.5-2012, 370hp from 2013. The
  385/400/420hp ratings are Aisin-only high-output options on the 3500 and nothing in these rows
  records the transmission, so the standard-output rating is used throughout and the ambiguity is
  documented rather than guessed. Sources: Cummins' own 2021 ratings table, Drivingline's
  '07.5-'18 6.7L history.
- **`ESA` (43)** splits by brand: the 6.4 HEMI is 410hp in the Ram HD and 470hp in the Jeep
  Wrangler Rubicon 392.
- **`DSFE`/`DSFF`** are the Golf R Mk8's EA888 evo4, 235kW = 320hp (autoparts-24 engine-code
  index; the US rating is quoted at 315hp).
- **`L15BY`** splits by model — 174hp in the Civic, 190hp in the CR-V, exactly the spread the
  DB's own `L15B7` descriptor already records.
- **`ERC`** splits by brand: 287hp Pacifica, 285hp Wrangler.

## Nine displacement repairs spotted in passing

`N54B30` was 1200cc for a 3.0 TwinTurbo, `N53B3O0` was **630cc** — the model designation 630i had
leaked into the displacement column — `N51B30` 1300→2996, `N52B25` 1300→2497, the three Mercedes
M266 rows 1200/1300→1498/2034, and the two Cummins rows 6700→6690.

## 30 variants and 14 engine rows deliberately left blank

| Code | n | Why no number is honest |
|---|---|---|
| `BEV (Tesla, model unidentified)` | 10 | The catch-all row for Teslas whose model could not be identified; Tesla outputs run 283-1,020hp. NULL by design. |
| `2.0 TDCi`, `2.5 TD`, `1.9 dCi`, `3.0 dCi`, `2.5 TDI`, `1.6 16v CRDI` | 14 | Generic displacement descriptors, not codes — the 2015 Ford range alone sold the 2.0 TDCi in six tunes. |
| `ESD`, `ESJ` | 2 | Their 6.62 L / 0W-40 spec confirms a supercharged 6.2 Hellcat, but the 2020 Charger offered both 717hp and 797hp and nothing separates the two codes. |
| `MDK` | 1 | 8.28 L / 0W-40 confirms a 992 — not whether it is the 385hp Carrera or the 450hp Carrera S. |
| `BEA` | 3 | The TT 1.8T's 4.54 L / 0W-30 fill is common to its 150, 180 and 225hp tunes. |

Plus 8 variants with no `engine_code` at all, and the 7 generic-descriptor skips from Step 7.
Two of the 14 remaining blank engine rows (`5.9 Cummins ISB`, `Duratec 2.3 CSR`, `VVC`) have no
variants and belong to the zero-variant cleanup.

## Files

- `step61_step8_engine_power.py`
- `database_enriched/csv_exports/69_engine_power_step61_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step61_2026-10-01.db` (local, untracked)

**Next: the 147 zero-variant engine rows, then 105 NULL cylinders / 73 NULL displacement, then
the 544 `(est.)`/`(corr.)` descriptors.**
