# STEP 5 — Batch 38: Saab LEMON Replacement (Step 47)

**Date:** 2026-10-01 · **Scripts:** `step47_step5_lemon_batch38_saab.py` + `step47b_estimate_override.py`
**Result:** 34 LEMON rows → **34 mapped (100%) / 0 skips** (2 volume defaults, flagged)

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 367 | **333** (−34) |
| LEMON Saab | 34 | **0** |
| engines rows | 6,014 | **5,981** (−34 LEMON +1 new) |
| Saab fuel conflicts | — | **0** |
| Saab variants with NULL power | 34 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## Method

In these years "Saab" is three engineering teams at once: Trollhättan's own 9-3 and 9-5, two
badge-engineered GM products (9-7X = TrailBlazer, 9-4X = Cadillac SRX) and a badge-engineered
Subaru (9-2X = Impreza). The displacement tokens plus the crawl's oil fills keep them apart —
3.97 L on the Subaru boxers, 3.88 L on the Saab B235, 5.96-6.38 L on the B207/B284, and the
familiar GM 5.67 / 6.62 L on the 9-7X.

| Rows | Target | hp |
|---|---|---|
| 9-2X 2000CC 2005 | `EJ205` 2.0 boxer turbo (Aero) | 227 |
| 9-2X 2500CC 2005 | `EJ253` 2.5 boxer SOHC (Linear) | 165 |
| 9-2X 2006 | `EJ253` — **volume default** | 173 |
| 9-3 2000CC 2005-2008, 9-3 + 9-3X 2011-2012 (10) | `B207R US` 2.0 turbo | 210 |
| 9-3 2800CC 2006-2007 / 2008 | `B284L EU/RW/US` 2.8 V6 turbo | 250 / 255 |
| 9-4X 2011 | `LF1` 3.0 V6 DI — **volume default** | 265 |
| 9-5 2005-2008 (4) | new `B235E US (9-5 2.3T, 220hp)` | 220 |
| 9-5 2011 | `A20NHT` 2.0 turbo (Insignia-based car) | 220 |
| 9-7X 4200CC 2005 / 2006-2009 | `LL8` 4.2 I6 Atlas | 275 / 291 |
| 9-7X 5300CC 2005-2009 (5) | `LH6` 5.3 V8 with DoD | 300 |
| 9-7X 6000CC 2008-2009 | `LS2` 6.0 V8 (9-7X Aero) | 390 |

The two 2012 rows carrying `VINR` and `VINZ` are emissions variants of the same B207R 2.0T, which
was the only US 9-3 engine in the car's final two years, so they resolve to the same target.

### Volume defaults (2)

The MY2006 9-2X row has no displacement token and **both** of that year's cars are 2.5-litre
(Linear EJ253 173 hp, Aero EJ255 turbo 230 hp), so it takes the higher-volume Linear engine.
The 9-4X 2011 row takes the volume 3.0i rather than the Aero 2.8T. Both are flagged in the
decision CSV rather than being presented as certainties.

## 1 new engine

| Code | Engine | cc | hp |
|---|---|---|---|
| `B235E US (9-5 2.3T, 220hp)` | 2.3 I4 16v turbo, US 9-5 base tune | 2290 | 220 |

## Fixes

**5 ROW_FIXES** (`STEP47_VERIFIED`) — `A20NHT` was recorded as a **6-cylinder** (it is an inline
four) and now names the 9-5 application; `B207R US` and `B284L EU/RW/US` carry their US ratings
(210 and 250 hp); `LS2` and `LF1` gained the Saab applications in their descriptors.

**step47b** — 3 ESTIMATE overrides (`A20NHT`, `B207R US`, `B284L EU/RW/US`), 1 normalization
(`LS2` 6.15 → 5.67 L) and 3 power syncs; 0 ESTIMATE specs and 0 spec-vs-engine power mismatches
remain among the batch targets.

## Skips

None.

## Evidence

[SAABUS] Saab US model-year specifications across all five nameplates · [LEMONFILL] per-row oil
fill recorded by the crawl, which separates the Subaru boxers (3.97 L), the Saab B235 (3.88 L),
the B207/B284 (5.96-6.38 L) and the GM engines (5.67 / 6.62 L).

## Files

- `step47_step5_lemon_batch38_saab.py`, `step47b_estimate_override.py`
- `database_enriched/csv_exports/55_lemon_step47_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step47_2026-10-01.db`

**Next: Batch 39 — Lexus (31 LEMON rows).**
