# Step 11 — Small Cleanups Report

**Date:** 2026-09-29 · **Scripts:** `step11_small_cleanups.py` (+ `step11b_post_fix.py`, `step11c_psd_oil.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step11_2026-09-29.db`
**Decision logs:** `database_enriched/csv_exports/19_small_cleanups_log.csv`, `19_small_cleanups_decisions.csv`

All five approved cleanup areas executed, plus two data-driven additions discovered during
dry-run verification (engine-table junk etypes, PSD sibling rows). Everything was dry-run
inspected before `--apply`.

## 1. Garbled engine codes (4 rows retired, 7 variants remapped)

| Junk code | Correct code | What it really is | Variants |
|---|---|---|---|
| `M54256S5` | `M54B25` | BMW M54B25 2.5 I6 (cc corrected 2457→2494) | 1 (E60 523i 20695) |
| `G4KR` | `G4EE` | Kia Alpha 1.4 DOHC 1399cc (2 Saipa variants) | 2 |
| `H4KR` | `G4EE` | same (2 Saipa variants) | 2 |
| `25V6S1` | `KV6` | Rover/MG KV6 2.5 V6 2497cc 177hp (existing row) | 2 (MG 20851, 24335) |

Citations: Wikipedia BMW M54 · drom.ru/kia/engine/g4ee + kiaclub.cz (G4EE = Alpha 1.4, 1,399 cc).

## 1b. C20LET row correction

The `C20LET` engine row held **Ford 1.4 TDCi data** (a mis-code; real C20LET = Opel 2.0 16v Turbo,
204 hp, 1998 cc). Six wrongly attached variants moved to their true sibling codes:
10687 Fiesta→`F6JD`, 25313 Duster→`K9K858`, 20879/20887 Massif→`F1CE0481FA`,
20881/20885 Massif→`F1CE0481HA`. Row corrected to the Opel specs; inherited spec row cleared.
The one legitimate user — Caterham Seven CF 2.0 Turbo (variant 17414, queue #227 pending) — was
then remapped onto it (autodoc.co.uk Caterham CF 2.0 Turbo 204 hp = C20 LET).

## 2. Remaining pending queue items resolved (6 of 94 → queue now 88 pending)

| Variant | Model | New engine | Evidence |
|---|---|---|---|
| 16239 | Marcos TS250 | `LCBD` | Ford 2.5 V6 Duratec 175–180 hp (autodata24, vindecoderz) |
| 16240 | Marcos TS500 | `5.0 Rover V8` (new row) | 5.0 V8 320 hp Rover V8 (ultimatespecs, carthrottle) |
| 18714 | smart fortwo ed (450) | `smart ED (450)` (new row, Electric) | Zytek 30 kW/41 hp, Zebra battery (Wikipedia smart ed, topspeed) |
| 21361 | GWM Voleex C50 | `GW4G15T` | 1.5T petrol 1497 cc 133 hp (chinamobil.ru, coolcarsinchina) |
| 15974 | Landwind 2.4 | `4G64S4M` | Mitsubishi 4G64 2.4 (myenginespecs) + DB siblings |
| 17414 | Caterham CF 2.0T | `C20LET` | see 1b above |

Also: Caterham CSR junk codes `2.3 16v 5MT`/`2.3 16v 6MT` (variants 2193/2194) → new row
`Duratec 2.3 CSR` (2.3 Ford Duratec Cosworth-tuned, 2261 cc — Wikipedia Caterham 7).
`GW4G15T` engine row itself was wrong (Diesel/141 hp) → fixed to Petrol/133 hp/1497 cc and its
variant 3631 fuel/power corrected (chinamobil.ru).

## 3. New engine rows (4) — `STEP11_VERIFIED`

`5.0 Rover V8` (Marcos TS500) · `smart ED (450)` (first Electric-fuel engine row) ·
`Duratec 2.3 CSR` (Caterham CSR/CSR260) · `M73B54` (BMW 5.4 V12 326 hp — closes the last
pre-existing orphan reference, Rolls-Royce Park Ward 25384).

## 4. OEM spec fills (cited, `oil_spec_source` now carries the citation)

| Engine | Filled | Source |
|---|---|---|
| `G6DA` (Ford 2.0 TDCi) | 5W-30 · 5.5 L · WSS-M2C913-C/D | enginecrux.com + kugaownersclub.co.uk |
| `G6DG` (Ford 2.0 TDCi) | 5W-30 · 5.5 L · WSS-M2C913-C/D | same |
| `G6DA (Hyundai)` 3.8 | 5W-30 · 6.0 L | OEM fill (Hyundai Lambda II) |
| `G6DG (Hyundai)` 3.0 | 5W-30 · 6.9 L | OEM fill |
| `M62B48` | oil 7.5 L | OEM fill (Alpina B10 V8) |
| `M73B54` | 5W-40 · oil 8.0 L · coolant 15 L | OEM fill (BMW/RR M73) |

No ESTIMATE markers remain on any step-11 target row.

## 5. Power Stroke capacity fixes

- `7.3 Power Stroke` oil 12.87 → **14.2 L** (15 US qt)
- `6.0 Power Stroke` oil 16.08 → **14.2 L** (swapped/inflated value corrected)
- `6.7 Power Stroke` coolant 1.41 L **cleared** (impossible; lemon parse error)
- Sibling rows found during verification and fixed the same way (step 11c):
  `7.3 V8 Powerstroke`, `T444E` (International twin), `6.4 V8 Powerstroke`: 9.5 → **14.2 L**;
  `6.7 V8 Powerstroke`: 9.5 → **12.3 L** (13 US qt).
- `6.4 Power Stroke` 14.19 L and `6.7 Power Stroke` 12.3 L confirmed correct qt conversions — untouched.
- Citations: egrperformance.com · prosourcediesel.com · suncentauto.com.

## 6. Cosmetic engine_type cleanup (5,214 variant rows + 54 engine rows)

- **4,308 junk-pattern** variant etypes (`(est.)`, `(corr.)`, commas, repair-shop notes like
  "Central Joint, wishbone", >35 chars) — replaced from the linked engine row when that etype is
  itself clean, else NULL.
- **906 displacement-spoof** etypes (parsed liter/cc disagrees >12 % with the linked engine's cc).
  Dry-run sampling showed blind copying was unsafe — some engine-table etypes are junk too — so the
  applied rule propagates an engine etype **only if it is clean and its own parsed displacement
  matches the engine cc**; otherwise the variant etype is NULLed (2,378 propagated / 2,836 NULLed
  across both categories combined).
- **54 engine rows** whose etype was actually a car-model/body-style string ("BLAZER Closed
  Off-Road Vehicle", "TIIDA Saloon (SC11X)", "940 II Estate (945)"…) — replaced with an honest
  label derived strictly from the row's own displacement+fuel columns ("2.3 Diesel", "Electric").

`step11b_post_fix.py` then deleted the two orphaned Caterham junk rows and **recomputed
`engines.count_variants` from actual variant links** (remaps had drifted counts ±1–2 across ~60 rows).

## Result

| Metric | Before | After |
|---|---|---|
| Engines | 15,454 | 15,452 (−6 junk, +4 verified) |
| Queue pending | 94 | 88 (−6 resolved with citations) |
| Queue remapped | 387 | 393 |
| Orphan variant→engine refs | 1 | **0** |
| Junk-pattern variant etypes | 4,308+ | **0** |
| count_variants mismatches | ~60 | **0** |
| LEMON variants remaining | 10,114 | 10,114 (unchanged — next: batch 3 Ford) |

Verification: garbled codes gone; C20LET = Opel 2.0 16v Turbo 204 hp with exactly 1 correct variant;
M73B54 = 5.4 V12 with the Rolls-Royce Park Ward variant; all FK constraints satisfied.

**Next:** Step 5 batch 3 — Ford Explorer/Edge/Escape (~743 LEMON rows), then the import brands
(~8,000).
