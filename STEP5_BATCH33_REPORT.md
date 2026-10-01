# STEP 5 — Batch 33: Fiat LEMON Replacement (Step 42)

**Date:** 2026-10-01 · **Scripts:** `step42_step5_lemon_batch33_fiat.py` + `step42b_estimate_override.py`
**Result:** 64 LEMON rows → **64 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 584 | **520** (−64) |
| LEMON Fiat | 64 | **0** |
| engines rows | 6,221 | **6,160** (−64 LEMON +3 new) |
| Fiat fuel conflicts | — | **0** |
| Fiat variants with NULL power | 64 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## Method — the first batch decoded mostly from VIN digits

Fiat's US re-entry (MY2012-2025) sold five nameplates plus the 500e, all on three FCA engines
and two electric drives, and seven of the crawl rows carry the VIN engine digit. Fiat's
position-8 table resolves those exactly [WIKIBOOKS_FIATVIN][FIAT500USA_VIN]:

| VIN 8 | Engine | Applications in these rows |
|---|---|---|
| `R` | 1.4 I4 MultiAir **naturally aspirated** (EAB), 101 hp | 500 2013/2014 |
| `H` | 1.4 I4 MultiAir **Turbo** (EAF/EAM), 135-160 hp | 500 2013/2014, 500X 2017/2018 |
| `W` / `T` / `B` | 500X 1.4 Turbo / 2.4 Tigershark | 500X 2016-2018 |
| `E` | 83 kW electric motor | 500e |

The rest is nameplate + year, and the US line-up is single-engined in nearly every case: 500L =
1.4 Turbo only (2014-2020); 124 Spider = 1.4 Turbo only; 500X = 1.4 Turbo or 2.4 Tigershark
180 hp (2016-18) then the 1.3 GSE Turbo 177 hp (2019-23); 500/500c = the 101 hp NA 1.4 unless
the trim says Turbo or Abarth.

**21 of the 64 rows are MY2015 trim slugs** (`..._2015_500ABARTHAUT`, `..._2015_500LTREKKING`),
handled by the trim table: Abarth = **160 hp** (157 with the automatic), Turbo = **135 hp** (the
Abarth engine detuned [WR_500T]), Pop/Sport/Lounge = **101 hp**, and every 500L trim = **160 hp**
because the 500L had no other engine.

### Six electric rows recorded as petrol

`500E` 2013/2014 (83 kW, 111 hp), `500E` 2025 and `500` 2024 are battery-electric; the crawl has
them as `fuel='Petrol'`. Note the MY2024 `500` row: the **only** Fiat 500 sold in the US that
year was the new-generation 500e, so that row is electric too. All four variants were moved to
the new 500e rows and their fuel corrected to Electric. (The 2013-2019 and 2024-2025 cars are
different motors — 83 kW/111 hp versus 87 kW/117 hp — so they get separate rows.)

## 3 new engines

| Code | Engine | cc | hp | fuel |
|---|---|---|---|---|
| `1.4 MultiAir NA (500/500c)` | 1.4 I4 MultiAir FIRE naturally aspirated (EAB) | 1368 | 101 | Petrol |
| `500e Electric (83 kW)` | Electric motor 83 kW (500e 2013-2019) | — | 111 | Electric |
| `500e Electric (87 kW)` | Electric motor 87 kW (500e 2024-2025) | — | 117 | Electric |

The three petrol targets that already existed were reused rather than duplicated:
`1.4 MultiAir Turbo (Dart/Renegade)` (now 40 variants), `ED8` 2.4 Tigershark MultiAir2 and
`1.3 GSE Turbo (Renegade)`.

## Fixes

**2 ROW_FIXES** (`STEP42_VERIFIED`) — both targets were named after Dodge/Jeep applications only;
their descriptors now list the Fiat ratings as well (1.4 Turbo: Abarth 160 / 500 Turbo 135 /
500L-500X 160 / 124 Spider 160; Tigershark: 500X 180).

**step42b** — 0 ESTIMATE overrides, 0 normalizations, 2 specs kept as-is, 3 power syncs; 0
ESTIMATE specs and 0 spec-vs-engine power mismatches remain among the targets. No `step42c`
correction script was needed.

## Skips

None.

## Evidence

[WIKIBOOKS_FIATVIN] en.wikibooks.org Fiat VIN codes (position-8 engine table, with the EAF/EAM/
EAB engine families and their model-year applications) · [FIAT500USA_VIN] fiat500usa.com
"Decoding the Fiat 500 VIN" (E = 83 kW electric motor, H = 1.4 turbo, R = 1.4 non-turbo) ·
[KBB_500_2013] kbb.com 2013 Fiat 500 specs (Pop/Sport/Lounge 101 hp, Turbo 135 hp, Abarth
160 hp) · [WR_500T] windingroad.com 2013 Fiat 500 Turbo ("the same 1.4-liter turbocharged
MultiAir four found in the Abarth … down from 160 horsepower to 135") · [FIATUS]/[FIATVOCAB]
FCA US model-year specifications + the FCA engine rows already in the database.

## Files

- `step42_step5_lemon_batch33_fiat.py`, `step42b_estimate_override.py`
- `database_enriched/csv_exports/50_lemon_step42_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step42_2026-10-01.db`

**Next: Batch 34 — Scion (44 LEMON rows).**
