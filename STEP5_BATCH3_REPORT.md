# Step 5 — Batch 3 Report: Ford LEMON Replacement (ALL remaining Ford)

**Date:** 2026-09-30 · **Script:** `step12_step5_lemon_batch3.py` (+ `step12b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step12_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/20_lemon_batch3_decisions.csv` (per-variant, with evidence)

Scope expanded per user choice from "Explorer/Edge/Escape" to **every remaining LEMON_FORD variant**
(743 rows, model years 2000–2024, 41 models). **658 variants remapped, 85 skipped** (documented
below), 658 LEMON codes retired, 21 new engine rows, 15 fuel fixes.

## Method

Same as batches 1–2: `(model, year, cc, VIN-8th char, fuel, trim-slug)` → real OEM engine code.
VIN engine codes were verified against **Ford's own fleet VIN guides** (fordpro.com PDFs for 2013/2014
and 2022), the fordmasterx decoding chart, forum/reman listings carrying **actual VINs**, and
model-year engine lineups (fordauthority, Wikipedia, KBB, dealership spec pages). All citations are
embedded in the script's `CIT` dict and the decisions CSV.

### Key VIN-char facts established (cited)

| VIN 8th char | Engine | Evidence |
|---|---|---|
| `8` | 3.5L Ti-VCT V6 **NA** (Cyclone) — cars/crossovers | Ford fleet VIN2013/2014 PDFs ("8 = 3.5L Ti-VCT V-6 288hp") |
| `8` | 3.5L EcoBoost **turbo** on 2021+ F-150 (code reuse across groups!) | eBay listings w/ real VIN `1FTFW1E84MFA97848`, Hollander interchange |
| `T` | 3.5L GTDI EcoBoost (SHO/PI/Flex EB) | Ford fleet VIN PDFs ("T = 3.5L GTDI 365hp") |
| `4` | 3.5L EcoBoost standard 375hp (2019–20 F-150) | ford-trucks.com (vs `T` = 450hp HO) |
| `H` | 2.3L EcoBoost I4 (Mustang/Ranger/Explorer/Bronco) | 2022 Ford fleet guide, americanmuscle, fordmasterx |
| `D` | 2.3L EcoBoost on 2020–23 Mustang; 1.5 EB on Escape | eBay listing w/ real VIN `1FA6P8TD3L5114302` |
| `9` | 2.0L EcoBoost I4 (Escape/Fusion/Edge/Taurus/Maverick) | fordmasterx |
| `P` | 2.7L Nano EcoBoost | fordmasterx |
| `B` / `W` | 3.3L V6 NA / 3.3L V6 **Hybrid** (2020+ Explorer/PIU) | go-parts.com engine ID guide |
| `C` | 3.0L EcoBoost 400hp (2020+ PIU/Explorer ST) | futureford.com 2021 PIU options + VIN `1FM5K8AC4MGB99635` |
| `K`/`R` | 3.7L (PIU) | model lineup (fordauthority 2018 Explorer) |
| `X` | 1.6L EcoBoost (Escape/Transit Connect) | fordmasterx family |
| `E` | 1.0L EcoBoost (Fiesta/Focus/Ecosport) | model lineups |
| `J` | 1.6L Ti-VCT (Fiesta) | model lineup |
| `L` | 2.0 (Ecosport) | model lineup |
| `2` | 2.0 GDI (2019+ Transit Connect) | akinsford/automotive-fleet |
| `7` / `A` | 2.5 I4 (Escape/Fusion/Transit Connect) | fordmasterx + TC lineups |
| `3` | 2.5 hybrid (Maverick) | Maverick lineup |
| `6` / `D` | 1.5 EcoBoost (Escape 2020–22 / 2017–19) | Escape lineups |
| `Y` | 6.8 V10 (2012 Super Duty) | cc-unique |
| `5` | 5.0 Coyote (2018+) | prior batch-1 research |

### Notable research saves

- **Explorer 2.3 EcoBoost 2016–2019 is real** — initial instinct said "impossible" (no 2.3 in gen-5),
  but fordauthority/autoevolution/KBB confirm the 2.3 EB (280 hp) replaced the 2.0 EB in the 2016
  refresh. 4 rows kept instead of skipped.
- **F-150 3.5 `8`**: `8` means *NA Cyclone* on cars/crossovers but *3.5 EcoBoost turbo* on the
  14th-gen F-150 (2021+) — verified via a real VIN in a parts listing, since generic charts
  conflict here.
- **Police model split**: 2014–19 rows are a mix of Taurus PI (`8`=3.5 NA, `T`=3.5 EB) and Explorer
  PIU (`K`/`R`=3.7); 2020+ rows are PIU (`B`=3.3 NA, `W`=3.3 hybrid, `C`=3.0 EB); bare 2019
  Hybrid = Police Responder Hybrid Sedan (Fusion 2.0 Atkinson).

## Top mappings (658 total)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| 2.0 T 16v Ecoboost | 66 | | 3.0 V6 | 37 |
| 3.5 Cyclone V6 | 62 | | 4.6 V8 | 32 |
| 2.3 EcoBoost (new) | 45 | | 4.0 V6 | 29 |
| 2.5 I4 Duratec 25 (new) | 42 | | 3.5 V6 EcoBoost | 26 |
| 2.7 EcoBoost | 22 | | 3.7 Ti-VCT V6 | 24 |
| 2.0 Duratec GDI (new) | 23 | | 1.5 EcoBoost (new) | 23 |
| 6.8 Triton V10 2V | 18 | | 5.0 Coyote V8 | 14 |
| 3.0 V6 EcoBoost (new) | 13 | | 1.0 EcoBoost (new) | 12 |
| 3.3 V6 Hybrid (new) | 10 | | 3.3 Ti-VCT V6 | 10 |

Full distribution in the decisions CSV.

## New engine rows (21, `STEP12_VERIFIED`)

`2.3 EcoBoost` · `1.6 EcoBoost` · `1.5 EcoBoost` · `1.0 EcoBoost` · `2.5 I4 (Duratec 25)` ·
`2.5 I4 Hybrid` · `2.5 OHC (Lima)` · `2.0 Duratec GDI` · `2.0 Atkinson Hybrid` ·
`2.0 Energi (PHEV)` · `3.3 V6 Hybrid` · `3.0 V6 EcoBoost` · `3.9 V8 (AJ35)` (Thunderbird) ·
`3.9 V6 (Essex)` (Mustang 2004) · `5.4 V8 Supercharged (GT500)` · `5.8 V8 Supercharged (GT500)` ·
`5.2 V8 (Voodoo)` (GT350) · `5.4 V8 Supercharged (Ford GT)` · `2.0 SPI 8v` (Escort) ·
`E-Transit Electric` · `Focus Electric` — the last two are the DB's 2nd/3rd **Electric** engines.

## Fuel fixes (15)

Police 3.3 `W` ×5 → Hybrid · Maverick 2.5 ×3 → Hybrid · C-Max Energi ×3 → Hybrid ·
E-Transit ×3 → Electric · Focus Electric ×1 → Electric.

## Spec handling

- Lemon-crawl specs migrated onto targets via COALESCE; ESTIMATE-source rows **not** propagated.
- Step 12b: 4 shared targets that pre-dated this batch kept heuristic ESTIMATE oil specs
  (`2.0 T 16v Ecoboost`, `3.0 V6`, `4.0 V6`, `4.6 V8`) — overridden with the lemon-crawl majority
  values (e.g. 4.0 SOHC = 5W-30 4.73 L uniform across all 31 source rows). **0 ESTIMATE specs
  remain among step-12 targets.**

## Skipped (85 rows, all documented in dry-run output)

| Group | Rows | Reason |
|---|---|---|
| Transit bare 2010–2023 | 7 | Connect vs full-size mixed, no cc |
| Special/SSV 2014–2020 | 5 | Special Service Vehicle — base model unknown |
| Cutaway 2000–2012 | 5 | 5.4/6.8/7.3/6.0 all offered |
| F-450/F-550 bare 2000–04 | 10 | 6.8 V10 vs 7.3 PSD |
| E-450 bare 2000–05 | 4 | same |
| Freestar 2004–07 | 4 | 3.9 vs 4.2 both offered |
| Windstar bare 2001–03 | 3 | 3.0 vs 3.8 |
| Taurus bare 02–05/10–12/18–19 + 3.0 2000–01 | 11 | Vulcan/Duratec; 3.5/SHO/2.0 |
| Focus bare 2000–07 + 2.0 2004 | 8 | Zetec/SPI/Duratec 2.0/2.3 PZEV |
| Mustang bare 2000/2021–24 + 5.2 2020 | 6 | 3.8/4.6; 2.3/5.0/Mach-E; GT350 vs GT500 |
| F-150 3.5 no-VIN 2016/17 + bare 22–24 | 5 | NA vs EB; no signal |
| Explorer bare 2001/2011, Escape bare 06–08, Edge bare 2011, Flex bare 10–12/19, Expedition 05–06, Excursion 2001, Transit-350 2015, Ranger 3.0 2024 (impossible petrol) | 13 | multiple engines / impossible combo |

## Result

| Metric | Before | After |
|---|---|---|
| LEMON variants (all brands) | 10,114 | **9,456** (−658) |
| LEMON_FORD variants | 743 | 85 (skips only) |
| Engines | 15,452 | 14,815 (−658 LEMON, +21 verified) |
| Orphan variant→engine refs | 0 | **0** |
| count_variants mismatches | 0 | **0** (recomputed) |
| v_vehicle_with_service | 39,088 | 39,088 (unchanged) |

**Next:** the import brands (~8,000 LEMON rows — Mercedes 968, BMW 780, Audi 576, Nissan 520,
Toyota 471, Kia 392, Hyundai 391, Lexus 322, Honda 312, Mazda 303, ...), then the 85 Ford skips
can be revisited if a per-VIN data source surfaces.
