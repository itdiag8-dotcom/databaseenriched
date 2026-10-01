# STEP 5 — Batch 29: Ford + Mercury LEMON Replacement (Step 38)

**Date:** 2026-10-01 · **Scripts:** `step38_step5_lemon_batch29_ford_mercury.py` + `step38b_estimate_override.py` + `step38c_hybrid_rows_and_fuel_cleanup.py`
**Result:** 148 LEMON rows (Ford 85 + Mercury 63) → **148 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 1,022 | **874** (−148) |
| LEMON Ford / Mercury | 85 / 63 | **0 / 0** |
| engines rows | 6,645 | **6,501** (−148 LEMON +4 new) |
| Ford + Mercury fuel conflicts | 29 | **0** |
| DB-wide fuel conflicts | 210 | **181** |
| Orphans / count mismatches | — | **0 / 0** |

Ford fuels after: Petrol 1,932 · Diesel 1,079 · Hybrid 33 · Electric 4.
Mercury fuels after: Petrol 61 · Hybrid 2.

## Why Ford and Mercury are one batch

Mercury was a badge division with no engines of its own: Mariner=Escape, Milan=Fusion,
Montego=Five Hundred, Monterey=Freestar, Mountaineer=Explorer, Sable=Taurus, Grand
Marquis=Crown Victoria, Cougar/Mystique=Contour. Every one of the 63 Mercury rows resolves to a
Ford engine already needed by the Ford half of the batch, so a merged batch keeps one evidence
set and prevents the same engine being created twice. (All 63 Mercury variants in the database
were LEMON rows — the brand is now fully decoded.)

## Method — nameplate generation + displacement

- **Commercial chassis** — `Cutaway` 2000 = 5.4 Triton 2V **255**, 2008-12 = 5.4 Triton 3V **255**;
  `E450`, `F450`, `F550` = **6.8 Triton V10 305**, the standard engine on those chassis (the 7.3
  Power Stroke was the option, and the crawl rows carry no diesel marker).
- **Taurus / Sable** — 3.0 Vulcan OHV **155** (`2000-05`) → 3.5 Cyclone **263** (`2008-12`) →
  **288** (`2018-19`); `Montego`/Five Hundred = 3.0 Duratec **203**.
- **Escape / Mariner and Fusion / Milan** — 2.3 Duratec **153** (Escape family) / **160** (Fusion
  family), 2.5 Duratec **171** / **175**, 3.0 Duratec **200**→**240** and **221**→**240**
  (the 2008 and 2010 engine revisions respectively).
- **Explorer / Mountaineer** — 4.0 SOHC **210**, 4.6 Triton 3V **292**, 5.0 OHV **215**, then the
  2011 U502 with 3.5 Cyclone **290**; `Edge` **285**, `Flex` **262**/**287**.
- **Mustang** — 3.8 Essex **190** (`2000`), 2.3 EcoBoost **310** (`2021-23`) / **315** (`2024`),
  and the `5200CC 2020` row = 5.2 Voodoo flat-plane **526** (Shelby GT350).
- **Transit** — the `2010-13` "Transit" rows are the Transit Connect (2.0 Duratec **136**);
  `2017-18` = 3.7 Ti-VCT **275**, `2023` = 3.5 Ti-VCT **275**, `Transit-350 3500CC 2015` =
  3.5 EcoBoost **310**.
- **Police/fleet rows** — `Special` (`2014-18` + the `SPECIALSERVI` trim row) is the Taurus-based
  **Special Service Sedan**, which Ford built only with the **2.0 EcoBoost, 240 hp**, for
  detective and administrative use [WIKITAURUS6]; `SSV` (`2019-20`) is the **SSV Plug-In Hybrid
  Sedan**, a Fusion Energi for non-pursuit fleet duty — 2.0 Atkinson PHEV **188 hp**
  [AUTOBLOG_SSV].
- **Villager** = the Nissan Quest twin → Nissan **VG33E** 3.3 V6 **170**.

**Volume-defaults** (bare rows only, each stated in the evidence column): Escape 2.3, Explorer
4.0 then 3.5, Mustang base V6/EcoBoost, Freestar 3.9 (4.2 optional), Taurus/Sable Vulcan then
Cyclone, F-150 3.3/3.5 Ti-VCT (EcoBoost optional), Flex/Edge/Transit base V6, Grand Marquis
4.6 224 hp (239 hp with the dual-exhaust handling package).

## 4 new engines

| Code | Engine | cc | hp |
|---|---|---|---|
| `3.0 V6 (Vulcan)` | 3.0 V6 OHV Vulcan (Taurus/Sable 2000-2007) | 2986 | 155 |
| `4.2 V6 (Essex)` | 4.2 V6 OHV Essex (Freestar/Monterey) | 4195 | 201 |
| `4.6 Triton 3V` | 4.6 V8 Triton SOHC 3-valve (Explorer/Mountaineer/Mustang GT) | 4601 | 292 |
| `3.7 Ti-VCT V6 (Cyclone)` | 3.7 V6 Cyclone Ti-VCT (Transit/Mustang/Police Interceptor) | 3726 | 275 |

The other 23 targets were existing verified Ford rows (Triton 4.6/5.4/6.8, Cyclone 3.5, 3.3
Ti-VCT, EcoBoost 2.0/2.3/3.0/3.5, Duratec 2.0/2.3/2.5/3.0, 3.9 Essex, 5.2 Voodoo, 5.0, 4.0, 3.8,
2.0 Zetec, 2.0 Energi PHEV, VG33E).

## Fixes

**9 ROW_FIXES** — `2.0 Zetec` and `2.0 Duratec` were recorded as **6-cylinder**, and most of the
older Ford rows had bare "2.0"/"3.8"/"4.0"/"5.0" descriptors; all now carry family names and
their per-application ratings. The `3.8 V6` row's note records that it also holds Chrysler EGT
3.8 Wrangler variants (a pre-existing conflation left intact rather than silently split).

**step38b** — 4 ESTIMATE oil-spec overrides, 6 normalizations, 13 power syncs; 0 ESTIMATE specs
and 0 spec-vs-engine power mismatches remain among the 27 targets.

**step38c** — three repairs:
1. **Five rows were hybrids, not petrol.** The crawl gave them displacement only, so the
   displacement rule sent them to the same-size petrol engine — but the crawl's own `fuel` column
   flagged them Hybrid. Escape `2006`/`2007`/`2008` → `2.3 I4 Atkinson Hybrid` **155 hp
   combined**; Mariner `2009`/`2011` → `2.5 I4 Hybrid` **177 hp combined**. A pre-existing Fusion
   `2012` row with the identical contradiction was moved to `2.5 I4 Hybrid` **191 hp** as well.
2. `5.4 Triton 3V` oil capacity restored to **6.62 L** (7 US qt); step38b's crawl majority had
   carried the 2-valve engine's 6 qt.
3. **23 pre-existing fuel contradictions cleared**: Power Stroke variants recorded as Petrol →
   Diesel (18, incl. SDBA), `3.5 PowerBoost` → Hybrid (4), and the last `A16XER` Diesel row →
   Petrol. Ford and Mercury are now at **0** fuel conflicts.

## Skips

None. The 10 Ford variants still without a power figure are pre-existing non-LEMON European rows
(2.0/1.5 TDCi, 2.5 TD, ZSD-422) whose engine rows carry no rating.

## Evidence

[WIKITAURUS6] en.wikipedia.org Ford Taurus (sixth generation) — Police Interceptor / Special
Service Sedan engine table ·
[KBB_TAURUS] kbb.com + caranddriver.com Ford Taurus (3.5 V6 263 hp from 2010, 288 hp later) ·
[AUTOBLOG_SSV] autoblog.com Ford Special Service Plug-In Hybrid + carsaver.com 2020 model page ·
[FORDLINEUP]/[FDVOCAB] US lineup ratings by model year + the Ford engine rows verified in
steps 9, 12 and 23.

## Files

- `step38_step5_lemon_batch29_ford_mercury.py`, `step38b_estimate_override.py`,
  `step38c_hybrid_rows_and_fuel_cleanup.py`
- `database_enriched/csv_exports/46_lemon_step38_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step38_2026-10-01.db`

**Next: Batch 30 — Pontiac + Saturn (85 + 49 = 134 LEMON rows, shared GM engine family).**
