# Step 5 — Batch 15 Report: Cadillac LEMON Replacement

**Date:** 2026-09-30 · **Scripts:** `step24_step5_lemon_batch15_cadillac.py` (+ `step24b_estimate_override.py`)
**Backup:** `database_enriched/backups/car_database_backup_pre_step24_2026-09-30.db`
**Decisions log:** `database_enriched/csv_exports/32_lemon_batch15_decisions.csv` (per-variant, with evidence)

Batch 15 in LEMON-count order = **every remaining LEMON Cadillac variant** (269 rows after batch 1's
45 Escalade rows; 24 models, MY2000–2025). **262 variants remapped, 7 skipped**, 8 new engine rows,
8 row-fixes, 6 fuel fixes (Electric 4, Hybrid 2).

## Incidents this batch

1. **Rewind #7** caught by the baseline guard pre-inventory (LEMON 12,637 → reset to origin, no loss).
2. **The pre-apply target assert fired** (batch-6 lesson): Catera's "3.0 V6 (Opel L81)" was in the
   rules but missing from NEW_ENGINES — fixed before any DB change.
3. Diagnosed a tooling gotcha: piping dry-run output through `head` kills the script (SIGPIPE) before
   the CSV is written — dry runs now run un-truncated.

## Method

Signals: cc + VIN + lemon fuel column (the 5 Escalade Hybrid rows were pre-flagged) + year. The GM
vocabulary from batches 1/6 covered most targets (LFX/LLT/LF1/LY7, LS6/LS2/L92/L9H/L86/LM2/LFA/LSA,
LD8/L37, LCV/LTG/L3B, Voltec EREV). Web-verified Northstar genealogy (Wikipedia/Hot Rod/xlr-net):

| Engine | Facts applied |
|---|---|
| **LH2** (new row) | RWD Northstar 4.6 320hp — STS/SRX/XLR (the DB's "LH8" row is a 5.3 truck code, untouched) |
| **LC3** | 4.4 SC: STS-V 469hp / XLR-V 443hp |
| LD8 / L37 | FWD 4.6: DeVille/Eldorado/Seville/DTS 275hp (L37 300hp noted) |
| **LTA** (new) | CT6-V 4.2TT Blackwing 550hp |
| **LF4** (junk row fixed!) | was "2.5 / 2492cc / 156hp" → 3.6TT 464hp ATS-V / 472hp CT4-V Blackwing |
| **LGW / LGX / LT4 / L87** (NULL rows filled) | 3.0TT 404hp / 3.6 335hp / 6.2 SC 640-668hp / 6.2 EcoTec3 420hp |
| LSA | relabeled CTS-V 2009-15, 556hp |

CTS-V generations mapped correctly: LS6 (2004-05) → LS2 (2006-07) → LSA (2009-14) → **LT4 (2016-19)**;
2015 6200cc row skipped as anomalous (no 2015 CTS-V existed). Escalade lineage: L59/LQ4 → L92/L9H →
L86 → L87 + **LM2 3.0 Duramax** (diesel fix) + **LFA two-mode hybrid** (Hybrid fix) + Voltec **ELR**.
EVs: LYRIQ + OPTIQ (39 EV engines now).

## Top mappings (262 total)

| Target | Rows | | Target | Rows |
|---|---|---|---|---|
| LTG (2.0T: ATS/CTS/CT4/CT5/XT4/XT5/XT6) | 73 | | LH2 (RWD Northstar) | 18 |
| LGX (3.6 DI XT5/XT6/CT6) | 22 | | LFX (3.6) + LF1 (3.0) | 16 + 15 |
| LD8 (FWD Northstar) | 20 | | LT4 + LSA (V-series) | 10 + 9 |

New engines (8): LH2, 3.0 V6 (Opel L81, Catera), LA3 3.2, LP1 2.8 (Canada), LP9 2.8T (Canada),
LTA 4.2TT Blackwing, LYRIQ Electric, OPTIQ Electric. Fuel fixes: 6 (LYRIQ/OPTIQ ×4 Electric;
Escalade LFA hybrid already flagged but engine-side fixed; ELR → Hybrid).

## Step 24b — spec normalization

7 ESTIMATE overrides + 5 majority normalizations + 10 power syncs + 22 NULL-power variant fills.
Spot-checks: LD8 7.09L ✓ (7.5qt), LH2 7.57L ✓, LT4 0W-40/8.51L ✓, LGW 6.15L ✓, LTG 0W-20/5.01L ✓.
**Result: 0 ESTIMATE among step-24 targets, 0 power mismatches, 0 orphans, 0 count mismatches.**

### Known limitations (accepted)

- Escalade 2015 slug rows → L86 (2015 = EcoTec3 420hp ✓); 2014 bare → L9H 403hp (pre-EcoTec3).
- CTS 2008 bare → LLT DI majority (LY7 base minority); CTS 3.6 rows note Vsport LF3 minority.
- Canada-market rows mapped with notes (CTS 2.8 LP1, SRX 2.8T LP9).
- LS-family capacities from lemon majority (5.67L) — within family norms, left as merged values.

## Skipped by design (7)

Escalade 2002-2006 bare ×5 (5.3 vs 6.0 unknown), CTS 2015 6200cc ×1 (anomalous — no 2015 CTS-V),
STS 2011 bare ×1 (3.6 vs 4.6).

## Post-state (verified)

| Metric | Before | After |
|---|---|---|
| Engines | 9,564 | 9,306 (−262 retired LEMON rows, +8 new) |
| LEMON total (all brands) | 4,043 | **3,781** |
| Cadillac LEMON remaining | 269 | 7 (intentional skips) |
| ESTIMATE / orphans / count / power mismatches | 0 | **0** |

**Next batch (LEMON-count order): Jaguar 258** → VW 237 → Infiniti 230 → Dodge 207 → Buick 205 →
Subaru 205 → Land Rover 194 → Porsche 193 → Lincoln 192 → … (~3,781 remaining across 32 brands).
