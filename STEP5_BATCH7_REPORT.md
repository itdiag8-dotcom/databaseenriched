# Step 5 — Batch 7 Report: Audi LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step16_step5_lemon_batch7_audi.py` (+ `step16b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step16_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/24_lemon_batch7_decisions.csv` (per-variant, with evidence)

Per the user-selected LEMON-count order, batch 7 = **every remaining LEMON Audi variant** (576 rows,
31 models, years 2000–2025). **537 variants remapped, 39 skipped** (documented below), 537 LEMON codes
retired, 16 new engine rows, 5 row-fixes, 21 fuel fixes (Diesel 11, Electric 10).

## Method

Audi LEMON codes carry **cc** and sometimes a VIN char. The DB's deep VAG vocabulary (APB, AUK, CAEB,
CTUA/CTWA, CREC, BCY…) served as target vocabulary; US-market generation facts verified on the web:

| Question | Answer | Evidence |
|---|---|---|
| A8 D5 "4000cc VIN E" rows | **A8 L 60 TFSI = 4.0T V8 453hp** (real US trim, 2020+) | Car and Driver, truecar, KBB |
| A8 D4 4.2 / 4.0T | **CDRA** 372hp (2010-12) / **CTG** 420→435hp (2013-17) | auto-data.net, motorinsel.eu |
| R8 4.2 | **BYH** 420hp (2007-10; US 430hp 2010+) | motorinsel.uk |
| TT RS 8J | CEPA 335 / **CEPB 360hp** (US 2012.5+) | australiancar.reviews, TTForum |
| S3 8V | 2.0T **292hp** (CYFB family; DB's CYFB row is a mislabeled Ford — not touched, descriptive row created) | ETKA registry, carparts.com, bar-tek |
| Q7 2011–2015 (bare/trims) | **3.0 TDI only** in the US (240hp CRCA) — incl. "PREMIUM" slugs without TDI badge | US-market lineup |
| Q7 2009-10 3.0 diesel | 225hp (new row) | — |
| Q5 3000cc petrol 2014-17 | SQ5-family 3.0T (VIN G/7 = 3.0 TFSI codes); **2013 skipped** (no US 3.0 petrol Q5) | VIN cross-reference |
| Junk labels decoded | **CTNA** = A8 W12 6.3 500hp (6299cc); **CTGA** = A8 D4 4.0T (435hp); NULL rows **DBPA/DHHA/DLRA** completed (B9 45 TFSI 252 / TT 245 / TTS 288) | displacement + existing links |

## Top mappings (537 total)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| CTWA (3.0T 333hp: S4/S5/A6/A7/A8/Q8) | 64 | | BGB (2.0TFSI EA113) | 25 |
| DBPA (B9 2.0T 45 TFSI) | 40 | | CTGE (4.0T S6/S7) | 24 |
| CTUD (3.0T 354hp: S4 B9/SQ5/Q5-3.0T) | 37 | | CREC (Q7 3.0T) | 18 |
| CWZA (2.0T 228: A3/Q3/Q5) | 34 | | AUK (3.2 FSI) | 17 |
| CNCD (2.0T 220 B8.5) | 29 | | CTUA (3.0T 310) | 17 |

New engines (16): ATW (B5 1.8T 150), S3 8V/8Y 2.0T rows, S6 C6 & S8 D3 5.2 V10, S8 D5 4.0T 563,
RS4/RS5 4.2 FSI, R8 42/4S 5.2 V10 rows, TTS 8J, TT RS 8S 394hp, Q7 US TDI 225hp, SQ7/SQ8 4.0T 500hp,
**Q4 e-tron + e-tron Electric** (Electric engines now 13), A8 D5 60 TFSI 4.0T.
Row-fixes: CTNA/CTGA junk labels relabeled; DBPA/DHHA/DLRA NULL rows completed.
Fuel fixes: 21 (Q7 TDI 11, Q4/e-tron Electric 10).

## Step 16b — spec normalization

31 ESTIMATE overrides + 10 majority fixes + 18 power syncs; 20 pre-existing NULL-power variants filled.
**Result: 0 ESTIMATE among step-16 targets, 0 power mismatches, 0 orphan refs, 0 count mismatches.**
Plausibility spot-checks: EA113 2.0T 4.54L ✓, 3.2 FSI 6.52L ✓, 1.8T 3.5L ✓, TT RS 6.52L ✓,
W12 11.46–12.49L (12qt) ✓.

### Known limitations (accepted, noted)

- Shared Euro rows keep Euro power figures with US values noted in evidence (BAS 295 vs US 300,
  BFM 330 vs 335, BAR 345 vs 350/354, CTFA 512 vs 520, CRDB 552 vs 560).
- One row per engine family: CTWA covers 310–335hp 3.0T tunes; CWZA covers 201–228hp 2.0T;
  DBPA covers 248–252hp B9 2.0T; R8 4S row covers 532/562/602hp trims.

## Skipped by design (39)

- **A6 bare rows ×13** (2014-2025, 2.0T vs 3.0T unknown) + A6 2015 trims ×2.
- **RS bare ×13** (2013-2025: RS5/RS6/RS7/RSQ8 unknown; only 2003=RS6, 2007-08=RS4 were mappable).
- **TT** ×6 (Mk1 180/225 ×4; 2016-17 TT/TTS/TTRS ×2).
- A4 2006 1800/3000cc ×2 (no US B7 1.8T/3.0 — Euro/Canada rows), A5 2009 ×1 (2.0T vs 3.2),
  Q5 2010 ×1 (2.0T vs 3.2), Q5 2013 3000cc ×2 (no US 3.0 petrol Q5), S5 2017 ×1 (B8.5 vs B9 transition),
  A3 2016/2017 ×2 (1.8T vs 2.0T).

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 12,658 | 12,136 (−537 retired LEMON rows, +16 new) |
| LEMON total (all brands) | 7,228 | **6,691** |
| Audi LEMON remaining | 576 | 39 (intentional skips) |
| ESTIMATE among step-16 targets | — | **0** |
| Orphan refs / count mismatches / power mismatches | 0 | 0 |

**Next batch (LEMON-count order): Nissan 520** → Toyota 471 → Kia 392 → Hyundai 391 → Lexus 322 →
Honda 312 → Mazda 303 → Cadillac 269 → Jaguar 258 → VW 237 → … (~6,691 remaining).
