# STEP 5 — Batch 24: Lincoln LEMON Replacement (Step 33)

**Date:** 2026-10-01 · **Scripts:** `step33_step5_lemon_batch24_lincoln.py` + `step33b_estimate_override.py` (first batch on shared `step5_lemon_lib.py`)
**Result:** 192 LEMON Lincoln rows → **189 mapped (98.4%) / 3 documented skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 1,921 | **1,732** (−189) |
| engines rows | 7,512 | **7,325** (−189 LEMON +2 new) |
| Orphans / count mismatches / fuel conflicts | — | **0 / 0 / 0** |

Lincoln fuels after: Petrol 209 · Hybrid 11.

## Key decisions (all web-cited in script)
- **MKS**: 2009 bare 3.5 275; 2010-12 3500CC = 3.5 NA 273 volume-default (EB 355 shares bucket); **2010-12 3700CC = SKIP** (3.7 not offered until 2013 — Edmunds); 2013-16: 3700CC = 3.7 300 / 3500CC = 3.5 EB 365 (only 3.5 left).
- **MKT**: 3.7 268→300 (2013+); 3.5 EB 355→365; 2000CC_VIN9 2013-16 = 2.0T 240 livery-only (Wikipedia MKT).
- **LS**: V6 AJ30 210/220 (2002)/232 (2003+); V8 AJ35 252→280; 2006 bare = V8-only 280 (wikicars).
- **Town Car**: 4.6 2V 200hp (2000-02) → 239hp (2003+) (cars.com/fastestlaps).
- **MKZ**: 3.5 263 (07-12); 2.0T 240 (13-16) → 245 (17+); 3.7 300; 3.0TT 350 FWD/400 AWD (default 400, USNews); Hybrid 2.5 191 (2011) → 2.0 188 (13-20).
- **MKX**: 3.5 265 → 3.7 305 → 3.7 303 + 2.7TT 335; 2015 AWD/FWD trim slugs = 3.7 303 volume-default.
- **Nautilus**: 2.0T 245 (2019) → 250 (2020+); 2.7TT 335. **Corsair**: 2.0T 250 / 2.3T 295; 2023+ 2500CC = Grand Touring PHEV 266 (fuel→Hybrid, ×3).
- **Continental**: 2000-02 4.6 DOHC 275 (new engine "4.6 V8 DOHC (InTech)"); 2017-20: 3.7 305 / 2.7TT 335 / 3.0TT 400.
- **Aviator** 2003-05 = InTech 302 (new engine); 2020-25 = 3.0TT 400 volume-default. **Blackwood** 5.4 InTech 300; **Mark LT** 5.4 Triton 3V 300; **Zephyr** 3.0 221; **MKC** 2.0T 240 / 2.3T 285.

**Skips (3):** MKS 3700CC 2010/2011/2012 — 3.7 not offered until MY2013 (lineup contradiction).

## Files
- `step33_step5_lemon_batch24_lincoln.py` · `step33b_estimate_override.py` (5 normalizations, 11 power syncs; ESTIMATE 0)
- CSV `41_lemon_step33_decisions.csv` (+DRYRUN) · Backup `pre_step33_2026-10-01.db`

**Next: Volvo 184 (batch 25).**
