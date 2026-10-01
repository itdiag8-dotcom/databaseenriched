# STEP 5 — Batch 49 (FINAL): Nissan + Subaru + Lincoln + Mazda + Toyota + Honda (Step 58)

**Date:** 2026-10-01 · **Scripts:** `step58_step5_lemon_batch49_tail.py`, `step58b_estimate_override.py`, `step58c_spec_reverts.py`
**Result:** 21 LEMON rows → **21 mapped (100%) / 0 skips** — and the LEMON queue is **empty**.

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 21 | **0** |
| `LEMON*` rows in `engines` | 21 | **0** |
| engines rows | 5,679 | **5,659** (−21 LEMON +1 new) |
| Fuel corrections | — | **1** (Crown → Hybrid) |
| Orphans / count mismatches | — | **0 / 0** |

## Decisions

| Rows | Evidence | Target | hp |
|---|---|---|---|
| Nissan NV3500 2012-2013 | 6.51 L (the 4.0 V6 takes 5.1) | `VK56DE` 5.6 V8 | 317 |
| Nissan Titan 2017-2019 | 6.51 L, 0W-20 | `VK56VDE` 5.6 V8 DIG | 390 |
| Nissan Versa 2007-2008 | 3.92 L | `MR18DE` 1.8 | 122 |
| Subaru Baja 2005-06, Legacy 2005-07, Impreza 2.5 2005 | 3.97 L flat four | `EJ253` 2.5 SOHC | 165 / 175 / 173 |
| Lincoln MKS `3700CC` 2010-2012 | 5.2 L, 5W-20 | `3.7 Ti-VCT V6` | 273 |
| Mazda 3 2019-2020 | 4.54 L (the 2.0 takes 4.2) | new `PY-VPS` 2.5 Skyactiv-G | 186 |
| Toyota Crown 2025 | 4.25 L and **0W-8** | `A25A-FXS` 2.5 hybrid | 236 |
| Toyota Tundra 2020 | 8.04 L | `3UR-FE` 5.7 V8 | 381 |
| Honda CR-V 2025 | volume engine | `L15BE` 1.5 turbo | 190 |

The Crown is the batch's only fuel correction and a good last example of the method: **0W-8** is
a grade Toyota specifies for its hybrid Dynamic Force fours and nothing else, so the row is the
2.5 hybrid and its fuel goes from Petrol to Hybrid. The Mazda contributes the project's last new
engine — the 2.5 Skyactiv-G, which had been missing while its 2.0 sibling was present.

## Fixes

**6 ROW_FIXES** (`STEP58_VERIFIED`). **step58b**: 1 ESTIMATE override, 5 normalizations, 2 power
syncs. **step58c** reverts two of them — `3.7 Ti-VCT V6` (79 variants, mostly F-150s at 6 qt)
had been pulled to the MKS's 5.5 qt, and `A25A-FXS` (66 variants worldwide) to the Crown row's
JDM 0W-8.

---

# Step 5 complete — the LEMON campaign

| | Start of Step 5 | Now |
|---|---|---|
| LEMON placeholder variants | 1,300+ | **0** |
| `LEMON*` rows in `engines` / `engine_service_specs` / `engine_technical_specs` | thousands | **0 / 0 / 0** |
| engines rows | — | 5,659 |
| vehicle_variants | — | 39,182 |
| Orphan references | — | **0** |
| `count_variants` mismatches | — | **0** |

Every placeholder is gone: no variant, engine, service-spec or technical-spec row carries a
`LEMON` code any more. This session alone closed batches 42-49 (FCA, Mercedes-Benz, the last GM
brands, JLR, Hyundai/Kia, Smart+Tesla+Daewoo, VAG and this tail), 242 rows, with **zero skips** —
including the eight Audi "RS" rows and the two GM rows earlier batches had set aside as
un-decodable.

## Known residuals (pre-existing, not introduced by Step 5)

- **137 fuel conflicts** DB-wide, almost all hybrid/electric variants attached to petrol engine
  rows on codes no LEMON batch touched (32 Mercedes, 11 Audi, 9 Lexus, …).
- **89 variants with a NULL `engine_code`** and **536 with NULL power**, of which 10 are the
  Tesla rows deliberately left NULL in batch 47.
- Scattered junk descriptors and wrong cylinder counts remain on codes outside the LEMON
  working set; batches 26-49 fixed 60+ of them opportunistically.

## Files

- `step58_step5_lemon_batch49_tail.py`, `step58b_estimate_override.py`, `step58c_spec_reverts.py`
- `database_enriched/csv_exports/66_lemon_step58_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step58_2026-10-01.db`

**Next: no LEMON work remains.** The natural follow-ups are the 137 fuel conflicts and the 89
NULL-`engine_code` variants, both of which predate this campaign.
