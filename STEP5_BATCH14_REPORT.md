# Step 5 — Batch 14 Report: Mazda LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step23_step5_lemon_batch14_mazda.py` (+ `step23b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step23_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/31_lemon_batch14_decisions.csv` (per-variant, with evidence)

Batch 14 in LEMON-count order = **every remaining LEMON Mazda variant** (303 rows, 27 models,
MY2000–2025). **301 variants remapped, 2 skipped**, 13 new engine rows, 5 row-fixes,
11 fuel fixes (Hybrid 8, Electric 2, Diesel 1).

## Baseline guard caught rewind #6

Pre-inventory check showed LEMON 12,637 (branch point) — `git reset --hard origin/...` restored the
correct DB before any work; the baseline assert (LEMON=4,344) then passed.

## Method

Signals: cc + VIN + fuel column + year. Two rebadge families mapped onto **Ford-family rows from
batch 1** per the standing physical-fact rule:

| Rebadge | Mapping |
|---|---|
| **Tribute = Ford Escape twin** | 2.0 Zetec (01-04) · 2.3 MZR NA (05-07) · 3.0 V6 Duratec 30 · 2008 Hybrid = new 2.3 Atkinson Hybrid row · 2009-11 Hybrid = existing "2.5 I4 Hybrid" (Escape-linked) |
| **B-Series = Ford Ranger twin** | B2300 = 2.3 16v DOHC · B2500 = 2.5 OHC (Lima) · B3000 = 3.0 V6 (Vulcan) · B4000 = 4.0 V6 (Cologne) |

Cross-brand powertrain reuse (verified): **CX-50 Hybrid 2025 = Toyota A25A-FXS hybrid system**
(219hp) — mapped to the existing Toyota row. **CX-5 2019 "2200cc VIN 2" = the rare US 2.2
Skyactiv-D diesel** (168hp, Diesel fuel fix). MPV 2000-02 = KL 2.5 V6 → 2003-06 = 3.0 Duratec 30.

Single-family row policy (like Toyota's T24A/V35A): **Skyactiv-G 2.5 (PY)** covers the 184-187hp NA
and 227-250hp turbo tunes (Mazda3/6, CX-30/5/50/9 2016+) — VIN L/M letters stay within the family.
Boundary enforced after spot-check: Mazda3 2.5 = **L5-VE MZR through 2013, PY Skyactiv from 2014**.

## Top mappings (301 total)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| Skyactiv-G 2.5 (PY family) | 65 | | 2.0 MZR (LF) | 21 |
| Skyactiv-G 2.0 (PE) | 39 | | 3.7 V6 Duratec 37 (MZI) | 18 |
| L5-VE (2.5 MZR 2010-13) | 29 | | L3-VE (2.3 DISI Turbo) + 2.3 MZR NA | 13 + 13 |
| 3.0 V6 (Duratec 30/Vulcan) | 28 | | 13B-MSP (RX-8) + KL + 2.3 16v | 8 + 9 + 9 |

New engines (13): 1.5 MZR (Mazda2), 2.0 MZR (LF), 2.3 MZR NA, Skyactiv-G 2.0 (PE) / 2.5 (PY),
2.2 Skyactiv-D, 1.8 BP (Miata NB), KJ-ZEM Miller SC (Millenia S — the oddball),
2.3 Atkinson Hybrid (Escape/Tribute), 3.7 Duratec 37, 2.5 PHEV e-Skyactiv (CX-70/90),
3.3T I6 e-Skyactiv G, MX-30 Electric. Row-fixes: L3-VE relabeled 2.3 DISI Turbo 263hp, FS 130hp,
13B-MSP → Renesis 212hp, 3.0 V6 dual-application label, L5-VE label.

## Step 23b — spec normalization

9 ESTIMATE overrides + 3 majority normalizations + 18 power syncs.
Spot-checks: Skyactiv 0W-20/4.16-4.25L ✓, KL 3.97L ✓, L3-VE turbo 5.67L ✓, ZM 2.93L ✓.
**Result: 0 ESTIMATE among step-23 targets, 0 power mismatches, 0 orphans, 0 count mismatches.**

### Known limitations (accepted)

- Bare-row majority mappings noted (Mazda3 BK 2.0, CX-5 2.5, Mazda6 2.5, Protege 2.0).
- Single PY row spans NA + turbo tunes; single LF row spans 148-167hp (Mazda3 vs Miata NC).
- Tribute/B-Series mapped to shared Ford rows (existing DB convention, application noted).

## Skipped by design (2)

Mazda3 2019 / 2020 bare — 2.0 vs 2.5 unknown (cc rows carry the split).

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 9,852 | 9,564 (−301 retired LEMON rows, +13 new) |
| LEMON total (all brands) | 4,344 | **4,043** |
| Mazda LEMON remaining | 303 | 2 (intentional skips) |
| ESTIMATE / orphans / count / power mismatches | 0 | **0** |

**Next batch (LEMON-count order): Cadillac 269** → Jaguar 258 → VW 237 → Infiniti 230 → Dodge 207 →
Buick 205 → Subaru 205 → Land Rover 194 → Porsche 193 → … (~4,043 remaining across 33 brands).
