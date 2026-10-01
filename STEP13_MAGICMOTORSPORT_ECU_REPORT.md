# Step 13 — ECU enrichment from the MagicMotorsport Flex vehicle list

**Date:** 2026-10-01 · **Scripts:** `step66_magicmotorsport_import.py`, `step66b_engines_codes_descriptors.py`
**Source:** `vehicles-list (3).csv` — 15,948 rows, committed by the user to `main`.
Re-obtain with: `git show "origin/main:vehicles-list (3).csv" > /tmp/mms/source.csv`
**Decision CSVs:** `csv_exports/76_ecu_import_step66.csv` (6,880 writes),
`csv_exports/77_ecu_conflicts_step66.csv` (8,498 not applied),
`csv_exports/78_engines_codes_descriptors_step66b.csv` (705)
**Backups:** `backups/car_database_backup_pre_step66_2026-10-01.db`, `…_pre_step66b_…db`

## Result

| | before | after |
|---|---|---|
| variants with a real ECU (model set, maker not `Unknown`) | 22,042 | **25,779** / 37,444 |
| variants with NULL `ecu_model` | 11,686 | **8,686** |
| variants with `ecu_maker = 'Unknown'` | 3,716 | **2,979** |
| engine rows with a real ECU | 4,011 | **4,235** / 5,670 |
| variants with NULL `engine_code` | 89 | **85** |
| Step-12 placeholder descriptors upgraded | — | **36** |

7,585 column updates. 0 fuel conflicts, 0 orphan references, 0 `count_variants` mismatches;
engines 5,670 and variants 37,444 both unchanged.

## Getting the data

The page is an Elementor/DataTables front end over
`wp-json/wp-vehicle/api/v1/vehicles/list`, which paginates on `page` + `per_page` and ignores
every filter parameter I tried (`brand`, `brands`, `search`, `s`). `bash` has no network in this
sandbox, so the ~20 MB of JSON could not be pulled in through the agent at all; the CSV export
committed to the repo was the workable route. The sandbox's file-attachment channel silently
dropped the upload twice before that.

## What the source is, and the three ways it can mislead

It is a *tuning tool* compatibility list: for each vehicle it names the physical controller the
Flex tool connects to. That makes it authoritative about ECU hardware — and it is the reason for
three guards, each of which fired on real rows:

**1. It lists gearbox controllers next to engine controllers.** 2,591 rows are `TCM`, 143 `OTHER`,
57 `ACM`; only 13,157 are `ECM`. The maker column makes the risk obvious — `ZF` (783 rows) and
`GETRAG` (167) build transmissions, not engine ECUs. An Abarth 500 appears twice: Bosch ME7.9.10
(ECM) and Marelli MTA CFC319 (TCM). Our schema has one ECU pair per row, meaning the engine's, so
**2,791 non-ECM rows were held back** rather than written.

**2. One engine code can carry several different ECUs.** `312A1000` appears with five. A value is
written only when every ECM row in the matched group agrees, or when narrowing to the exact power
figure makes it agree. **7,184 variants ended ambiguous and were left untouched**, listed with
their candidates in the conflicts CSV.

**3. A "disagreement" is usually not a correction.** This was the main finding. Of 4,457 rows
where the source differed from a value we already held:

| | rows | verdict |
|---|---|---|
| genuinely different ECU | 2,973 | source wins — **2,568 applied**, 405 withheld (weak key, see below) |
| source more specific (`8GMF` → `8GMF MPC5565`) | 589 | applied — gains the microcontroller part |
| **ours more specific** (`MED9.1.5` → `MED9.1`) | 514 | **kept ours** — the source would drop the subversion |
| identical after normalisation (`Simos PCR 2.1` vs `Simos PCR2.1`) | 280 | **no write** — pure formatting churn |
| same ECU, different maker name (`Siemens` vs `Continental` on `SID208`) | 101 | **kept ours** — see below |

Applying all 4,457 blindly, which is what "source wins" reads like on paper, would have degraded
514 rows, rewritten 280 for whitespace, and half-migrated a naming convention.

## Four judgement calls

**Overwrites require an engine-code match.** A match on brand + model name + power is good enough
to *fill* a blank but not to overturn a stored ECU: model names differ across catalogues (our
`500 Assetto Corse` vs their `500`). **419 such rows kept our value** and were exported instead.

**The Siemens/Continental question was deliberately not settled here.** Siemens VDO became
Continental in 2007, so both names are defensible for the same `SID201`/`SID208`/`EMS2102`. The
source says Continental on 101 of our rows — but we hold 1,771 `Siemens` rows overall. Migrating
101 of them would leave the vocabulary in a worse state than either convention. It is logged as a
vocabulary decision for a later pass, not quietly applied.

**Aston Martin is the case that proves the source right.** 2013 DB9 and V12 Vantage rows said
`Ford/EEC-VI`; the source says `Bosch/ME17.8.31`. Our own database already had the 2013 V12
Vantage S and Vanquish — same year, same 5.9 V12 — on `Bosch ME17.8.31`. Our EEC-VI rows were the
stale ones, and the internal contradiction is now gone.

**`engine_code` is a foreign key, so it was filled with extreme caution.** Only **4 of the 89**
blank codes were written: a code is accepted only when the brand/model/power match is unanimous
*and* the code already exists in `engines` — otherwise the write would manufacture exactly the
orphan references the previous steps drove to zero. 85 remain blank, which is the correct outcome.

## Descriptor upgrades (36)

Step 12 deliberately rebuilt junk descriptors as bare `"5.5 L Petrol"` because the cylinder counts
behind them were untrustworthy. Where the source names the engine properly, that placeholder is
now replaced — `1AR-FE` → `2.7L VVTi Petrol`, `CJTA` → `3.0L TFSI Petrol`, `B3LA` →
`1.0L LPi 12v Petrol`. Only placeholders were touched; descriptors that already said something
specific were left alone. Three filters stopped bad upgrades:

- descriptions that only repeat the displacement (`"2.0L"`) — **7 rejected**, they would have
  dropped the fuel word and the brand badge (`1.6 L Petrol (Cooper)` → `1.6L`)
- a displacement that contradicts ours by more than 0.15 L — **2 rejected**
- petrol technology on a diesel row or vice versa — e.g. `CYRB`, a 2,198 cc diesel in our data,
  which the source would have labelled `2.0L TFSI`

## Residual

- **7,184 ambiguous variants** + 8,498 total non-applied rows in `77_ecu_conflicts_step66.csv` —
  the ambiguous ones are resolvable with the API's `produced_from_year`/`produced_to_year`, which
  the CSV export does not carry.
- **18,877 variants had no counterpart in the source at all** — mostly US-market and older models
  outside a European tuning tool's coverage.
- 450 engine rows ambiguous, 3,983 with no match.
- The Siemens/Continental vocabulary decision.
