# STEP 5 — Batch 40: Mini LEMON Replacement (Step 49)

**Date:** 2026-10-01 · **Scripts:** `step49_step5_lemon_batch40_mini.py`, `step49b_estimate_override.py`, `step49c_mini_placeholder_cleanup.py`
**Result:** 31 LEMON rows → **31 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 302 | **271** (−31) |
| LEMON Mini | 31 | **0** |
| engines rows | 5,950 | **5,914** (−31 LEMON, +1 new, −6 placeholders retired in 49c) |
| Mini fuel conflicts | — | **0** |
| Mini variants with NULL power | 55 | **0** (31 from the batch + 24 pre-existing, see 49c) |
| Orphans / count mismatches | — | **0 / 0** |

## Method

All 31 rows carry the same nameplate, "Cooper", so the decode runs on the displacement tokens the
crawl kept on 18 of them plus the oil fill on the rest. Mini's US engines across these years form
four families whose fills do not overlap:

| Rows | Engine | Fill | hp |
|---|---|---|---|
| 2005-2006 (2) | new `W10B16 (Cooper, 115hp)` 1.6 Tritec NA | 4.54 L, 5W-40 | 115 |
| 2011-2013, 1600CC 2015 ×2 (5) | `N16B16A` 1.6 NA (R56 LCI) | 4.20-4.25 L, 5W-30 | 121 |
| 2014, 2016, 1500CC 2017-2024 (10) | `B38A15A` 1.5 **three-cylinder** turbo (F56) | 4.21-4.63 L, 0W-20 | 134 |
| 2000CC 2017-2024, bare 2020-2024 (13) | `B46A20A` 2.0 turbo (Cooper S) | 5.25 L, 0W-20 | 189 |
| 2025 (1) | `B48A20A` 2.0 turbo (F66 Cooper S) | 5.25 L, 0W-20 | 201 |

Two details are worth calling out. The **bare 2020-2024 rows** look ambiguous but are not: their
5.25 L fill is a full litre above any three-cylinder row, so they are Cooper S cars. And the
**1600CC MY2015** rows must be the outgoing N16 — the F56 Cooper that replaced it is 1.5 or 2.0,
never 1.6.

## 1 new engine

| Code | Engine | cc | hp |
|---|---|---|---|
| `W10B16 (Cooper, 115hp)` | 1.6 I4 16v Tritec (Cooper R50/R52/R53) | 1598 | 115 |

The database already had `W10B16A` at 90 hp — that is the **One**, not the Cooper.

## Fixes

**4 ROW_FIXES** (`STEP49_VERIFIED`) — `B38A15A` was recorded as a **4-cylinder** (the B38 is
BMW's 1.5 **three**-cylinder); `B46A20A`, `B48A20A` and `N16B16A` gained US ratings and
descriptors naming the bodies they appear in.

**step49b** — 4 ESTIMATE overrides (all four targets had the same placeholder 5W-30 / 2.8 L
estimate and now carry the crawl's measured fills: 4.49 L, 5.25 L, 5.25 L and 4.2 L), 0
normalizations, 4 power syncs.

**step49c — placeholder cleanup.** 24 Mini variants (MY2007-2015) were sitting on bare
engine-family codes an earlier pass had created from the crawl's "Eng CD" strings (`B38`, `B48`,
`N16`, `N18`, `W10`, plus `...M0` stubs), most with no displacement, power or cylinder count,
which is why every one of them had NULL power. Now that Mini has a verified vocabulary they were
relinked to it — `B38`/`B38A15M0` → `B38A15A`, `B48`/`B46A20M0`/`B48A20B` → `B46A20A`, `N16` →
`N16B16A`, `N18` → `N18B16A`, and the MY2007-2008 `W10` rows → the new Cooper 1.6 (they are R52
convertibles, not 1.4 Ones). `N12`, `N14`, `W11`, `N18B16A` and `N18B16C` are real rows, so their
variants only needed power backfilled. Six emptied placeholders were retired, and `B48A20B` lost
its junk *"Leaf Spring Suspension"* descriptor.

## Skips

None.

## Evidence

[MINIUS] Mini USA model-year specifications · [LEMONFILL] per-row oil fill and viscosity
recorded by the crawl.

## Files

- `step49_step5_lemon_batch40_mini.py`, `step49b_estimate_override.py`, `step49c_mini_placeholder_cleanup.py`
- `database_enriched/csv_exports/57_lemon_step49_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step49_2026-10-01.db`

**Next: Batch 41 — Suzuki (29 LEMON rows).**
