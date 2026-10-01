# STEP 5 — Batch 41: Suzuki LEMON Replacement (Step 50)

**Date:** 2026-10-01 · **Scripts:** `step50_step5_lemon_batch41_suzuki.py` + `step50b_estimate_override.py`
**Result:** 29 LEMON rows → **29 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 271 | **242** (−29) |
| LEMON Suzuki | 29 | **0** |
| engines rows | 5,914 | **5,886** (−29 LEMON +1 new) |
| Suzuki fuel conflicts | — | **0** |
| Suzuki variants with NULL power (mapped rows) | 29 | **0** |
| Orphans / count mismatches | — | **0 / 0** |

## Method

Suzuki's last US decade was half its own engineering and half other people's — the Forenza, Reno
and Verona are Daewoos, the Equator is a Nissan Frontier, the second-generation XL7 is a GM Theta
with GM's High Feature V6. Each nameplate ran one engine per generation, and the crawl's oil fill
confirms every assignment.

| Rows | Target | hp | Fill |
|---|---|---|---|
| Aerio 2005-2007 (3) | new `J23A` 2.3 I4 | 155 | 4.73 L |
| Equator 2500CC / 4000CC 2009 | `QR25DE` / `VQ40DE` | 152 / 261 | 4.63 / 5.11 L |
| Forenza + Reno 2005-2008 (8) | `T20SED` 2.0 Daewoo D-TEC | 126 | 3.97 L |
| Grand Vitara 2005 | `H25A` 2.5 V6 | 165 | 5.48 L |
| Grand Vitara 2006-2008 (3) | `H27A` 2.7 V6 | 185 | 4.77 L |
| Grand Vitara 2400CC / 3200CC 2009 | `J24B` / `N32A` | 166 / 230 | 4.77 / 6.0 L |
| SX4 2007-2009 (3) | `J20A` 2.0 I4 | 143 | 4.44 L |
| Verona 2005-2006 (2) | `X25D1` 2.5 **inline-six** | 155 | 6.43 L |
| XL-7 2005-2006 (2) | `H27A` 2.7 V6 | 185 | 5.48 L |
| XL7 2007-2009 (3) | `LY7` 3.6 V6 High Feature | 252 | 5.2 L |

Two decodes are worth highlighting. The **Verona** is a mid-size sedan with a transverse
**straight six** (Daewoo's XK), and its 6.43 L fill matches nothing else Suzuki sold. The
**XL-7 → XL7** rename in 2007 is a genuine engine change, not a spelling change: Suzuki's own 2.7
V6 (5.48 L) gave way to GM's 3.6 (5.2 L), and the crawl's fills show the switch.

## 1 new engine

| Code | Engine | cc | hp |
|---|---|---|---|
| `J23A` | 2.3 I4 DOHC 16v (Aerio 2004-2007) | 2298 | 155 |

## Fixes

**6 ROW_FIXES** (`STEP50_VERIFIED`) — `H27A` carried the junk descriptor *"BLAZER S10"* and is
now the Grand Vitara/XL-7 2.7 V6 at 185 hp; `J24B` was recorded as a **6-cylinder** (it is the
2.4 inline four); `N32A` was a bare "3.2 (est.)"; `J20A`, `T20SED` and `X25D1` gained descriptors
naming the Suzuki applications and US ratings.

**step50b** — 3 ESTIMATE overrides (`H27A`, `J24B` and a viscosity correction to 5W-30), 3
normalizations (`J20A` 5.2 → 4.44 L, plus two sub-0.1 L adjustments on the Nissan engines) and 4
power syncs; 0 ESTIMATE specs and 0 spec-vs-engine power mismatches remain.

## Skips

None. (One pre-existing Suzuki variant unrelated to this batch still has NULL power.)

## Evidence

[SUZUKIUS] Suzuki US model-year specifications, including the Daewoo, Nissan and GM sources ·
[LEMONFILL] per-row oil fill recorded by the crawl.

## Files

- `step50_step5_lemon_batch41_suzuki.py`, `step50b_estimate_override.py`
- `database_enriched/csv_exports/58_lemon_step50_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step50_2026-10-01.db`

**Next: Batch 42 — Dodge (23 LEMON rows).**
