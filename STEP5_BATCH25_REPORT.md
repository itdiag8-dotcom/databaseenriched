# STEP 5 — Batch 25: Volvo LEMON Replacement (Step 34)

**Date:** 2026-10-01 · **Scripts:** `step34_step5_lemon_batch25_volvo.py` + `step34b_estimate_override.py`
**Result:** 184 LEMON Volvo rows → **184 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 1,732 | **1,548** (−184) |
| engines rows | 7,325 | **7,148** (−184 LEMON +7 new) |
| Orphans / count mismatches / fuel conflicts | — | **0 / 0 / 0** |

Volvo fuels after: Petrol 397 · Diesel 207 · Hybrid 14 (T8 PHEVs).

## Method — official Volvo VIN engine codes (pos 4-5)
Decoded from the official Volvo VIN decoders (NHTSA vpic MY2019, volvotechinfo MY2022, Wikibooks Volvo VIN table):
- **P3 2015-17**: 40/26/27 = B4204T11 T5 2.0 Drive-E **240**; 49 = B4204T9 T6 2.0 twincharged **302**; 61 = B5254T12 T5 2.5 I5 **250**; 90 + bare 3000CC = B6304T4 T6 3.0 **300**; 94/95 = B6324S5 3.2 **240**.
- **SPA 2017-22**: 10/98 = B4204T23 T5 **250**; 99/A2 = B4204T27 T6 **316**; BR/BC = T8 PHEV **400**; H6 = T8 Extended Range **455**; BK = T8 Polestar Engineered **415** (all fuel→Hybrid, 14 rows).
- **MHEV era**: B5 247 (S60/V60 2022+, XC60 2022-24, XC90 2023-24); B6 295 (S90 + V90CC rows 2022+, XC60/XC90 2023+); XC40: T4 187 (2019-22) → B4 194 (2023+, C&D/MT/KBB verified).
- **P2/P1 volume-defaults**: 2.4i 168 (S40/V50/V70); 2.5T 208 (S60 P2, XC70 P2, S80 05-06, XC90); P1 T5 218→227 (C70/C30); 2.9 T6 272; 4.4 V8 311; 3.2 235; S80 T6 3.0 281 (new B6304T2); V60CC 2015 trim = 2.5 T5 250.
- Volume-defaults documented per model-year (XC90 2016 T6 316 → 2017-22 T5 250 → 2023+ B5 247; S90/V90 2017-21 T5 250 → 2022+ B6 295 — regular V90 US ended MY2021, 2022+ rows are V90CC).
- 7 new engines (B4204T23, B6304T2, XC40 T4/B4, B5/B6 MHEV, T8 PHEV); ROW_FIX B4204T27 → T6 316hp.

**Skips: none** — every row decodable via cc + VIN engine code + verified lineup.

## Files
- `step34_step5_lemon_batch25_volvo.py` · `step34b_estimate_override.py` (10 ESTIMATE overrides, 4 normalizations, 8 power syncs)
- CSV `42_lemon_step34_decisions.csv` (+DRYRUN) · Backup `pre_step34_2026-10-01.db`
- Remaining documented NULL-power Volvo rows (pre-existing, non-batch): B4204T12 ×1, B4204T43 ×2.

**Next: Acura 180 (batch 26).**
