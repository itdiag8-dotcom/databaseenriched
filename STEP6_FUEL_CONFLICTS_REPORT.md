# STEP 6 — Fuel Conflicts Resolved (Step 59)

**Date:** 2026-10-01 · **Scripts:** `step59_step6_fuel_conflicts.py`, `step59b_sprinter_fuel.py`
**Result:** 137 conflicts → **0**

| Metric | Before | After |
|---|---|---|
| Variants whose `fuel` disagrees with their engine row | **137** | **0** |
| Engine codes involved | 45 | — |
| engines rows | 5,659 | **5,670** (+12 new, −1 retired stub) |
| Orphans / count mismatches | 0 / 0 | **0 / 0** |
| Junk fuel labels (`Wankel`, `Hybrid (Petrol-/ Electro.)`) | 4 | **0** |

A fuel conflict is a variant pointing at an engine row that disagrees with it about what the car
burns — a Corolla Hybrid attached to the petrol `2ZR-FE`, an S400 HYBRID filed as Petrol, an RX-8
whose fuel is recorded as "Wankel". These predate the LEMON campaign and survived it untouched.

## Method

Each of the 45 affected engine codes was classified into one of four outcomes, and the decision
always turned on which side held the better evidence.

**1 · RELINK to an existing row (49 variants).** The variant was right and the correct sibling
already existed: Corolla Hybrid → `2ZR-FXE`, Highlander Hybrid → `2GR-FXE`, RAV4 Hybrid →
`2AR-FXE`/`A25A-FXS`, GS450h → `2GR-FXE`, Previa and XV30 Camry → the plain `2AZ-FE`.

**2 · RELINK to a new row (30 variants, 12 rows added).** The variant was right but its engine
was missing from the catalogue:

| New row | For |
|---|---|
| `T24A-FTS (i-FORCE MAX)`, `V35A-FTS (i-FORCE MAX)` | Toyota's two hybrid truck engines |
| `3MZ-FE Hybrid`, `QR25DE Hybrid`, `QR25DER Hybrid` | RX400h/Highlander Hybrid; Altima/Rogue Hybrid; the supercharged Pathfinder/Murano Hybrid |
| `G4FT`, `G4LE`, `G4KK` | Tucson Hybrid, Elantra Hybrid, Sonata Hybrid |
| `OM651 BlueTEC Hybrid`, `DW10 HYbrid4` | Mercedes and PSA **diesel** hybrids |
| `M256 PHEV (S580e)`, `M276 3.0 BiTurbo (S450)` | separating plug-ins from mild hybrids |

**3 · ENG_FUEL — the engine row was wrong (4 codes, 11 variants).** `X16SZR` is an Opel 1.6
**petrol** that had been recorded as Diesel. `CHJA` and `CRJA` are literally named "Hybrid" in
their own descriptors yet were filed as Petrol. `RHC(DW10CTED4)` is a diesel that had been filed
as Hybrid because its HYbrid4 cars shared the code — those cars moved to `DW10 HYbrid4` first,
then the row went back to Diesel.

**4 · VAR_FUEL — the variant label was wrong (57 variants).** The cleanest evidence in the whole
step: four A8/A7 variants on the 3.0 TFSI `CTUA` were labelled Diesel, but they carry **310hp** —
exactly the petrol figure their non-conflicting siblings carry, where a 3.0 TDI of those years
reads 240. `BGB` (197hp) and `CWZA` (228hp) tell the same story. Also here: **"Wankel" is an
engine layout, not a fuel**, so the three RX-8 rows become Petrol, and the lone
`Hybrid (Petrol-/ Electro.)` label on a C3 Pluriel 1.4 goes with it.

## Where the line falls between a mild hybrid and a hybrid

The S450's EQ Boost 48V system cannot move the car on its own, and this database already treats
such cars as Petrol — all 24 `M256` CLS450/E450/GLE450 variants are Petrol. So the three S450
rows move to a new petrol `M276 3.0 BiTurbo (S450)` row, while the genuinely plug-in S560e keeps
`M276.824`. The same logic put the S580e on its own PHEV row rather than on the mild-hybrid
`M256`.

## Also fixed

- **7 junk descriptors** (`STEP59_VERIFIED`): `M272.974` read "LANDE Pickup", `RHC(DW10CTED4)`
  read "3000 GT (Z16A)", plus `(est.)`/`(corr.)` placeholders on `2AZ-FXE`, `3MZ-FE`,
  `OM651.924`, `X16SZR`, `2GR-FSE`.
- **1 stub code retired**: `654`, a duplicate of the Sprinter's OM654 row, emptied and removed.
- **step59b**: the single conflict step59 left standing — the Sprinter MY2023 variant was relinked
  to a Diesel row while still labelled Petrol; the OM654 Sprinter was never sold as a petrol.

## Files

- `step59_step6_fuel_conflicts.py`, `step59b_sprinter_fuel.py`
- `database_enriched/csv_exports/67_fuel_conflict_step59_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step59_2026-10-01.db` (local, untracked)

**Next: Step 7 — the 536 NULL-power variants, 186 of which are a direct backfill from their engine row.**
