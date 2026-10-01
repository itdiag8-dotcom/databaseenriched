# STEP 5 — Batch 23: Porsche LEMON Replacement (Step 32)

**Date:** 2026-10-01 · **Scripts:** `step32_step5_lemon_batch23_porsche.py` + `step32b_estimate_override.py` + `step32c_fix_vote_contamination.py` (rebuilt via shared `step5_lemon_lib.py` after a workspace rewind; decisions identical to the first verified pass)
**Result:** 193 LEMON Porsche rows → **185 mapped (95.9%) / 8 documented skips**

## Outcome

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 2,106 | **1,921** (−185) |
| engines rows | 7,679 | **7,512** (−185 LEMON engine rows −2 consolidated MCT/MDH +20 new) |
| Porsche LEMON rows | 193 | 8 (documented skips) |
| Orphans / count mismatches / Porsche fuel conflicts | — | **0 / 0 / 0** |

Porsche fuels after: Petrol 527 · Diesel 29 · Hybrid 32.

## Mapping decisions (key evidence)

Web-verified: youcanic VIN pos-5 engine letters (997/991/981/92A/95B), Wikipedia generation pages, 2019 Cayenne E3 + 2021 Panamera 971.2 press data, 2015 lemon crawl (EPA trim strings + oil), DB M-code vocab.

- **718**: 2.0T 300hp (new engine); 2.5 S → MDJ 350; 4.0 → MDW 394 volume-default.
- **911**: 997.1 2005-08 M96.05 325; 997.2 2009-11 MA1.02 345 (incl 3600CC_VINA 2012); 991.1 2012-14 MA1.04 350 / 3800CC MA1.03 400 / VINB-2012 = 997.2 GTS MA1.01S 408; 2015 EPA trims decoded (Carrera/4/Targa→MA1.04, S/4S→MA1.03, GTS 3.8 430 + Turbo S 560 new engines, GT3 MA1.75 475, Turbo MA1.71 520); 991.2 2016-19 3.0T 370; 3800CC_2017 = 991.2 Turbo MDA.BA 540; 992 379/572/502 (4 new engines).
- **Boxster/Cayman**: 987.1 M97.20 240/245, 987.2 MA1.20 255/265, 981 MA1.22/MA1.23, GTS 3.4 (new engine); 2015 trims decoded.
- **Cayenne**: base M02.2Y/M55.01/M55.02; 4800CC M48.01 385 (09-10) / M48.02 400 (S: 2014+VINB-2013; VIND-2013 GTS 420 — M48.02 stores 414=420PS) / M48.52 500 (bare 2013 Turbo) / MCF.TB 520 (958.2 Turbo 2015-18); Diesel MCR.CA 240; S E-Hybrid MCG.EA 413 (2017-18); E3: S 2.9TT 434, E-Hybrid PHEV 455 (2019/2021 Hybrid-flagged rows), base 3.0T 335 (2020/2022/2023 Petrol-flagged), Turbo 541 (2019/2021), Turbo S E-Hybrid 670 (2020 Hybrid-flagged), GTS 453 (2022-23).
- **Panamera**: M46.20 300/310; S Hybrid MCG.EA 375; 970.2 S/4S MCW.DA 420; 971.1 base 330 + 4 E-Hybrid PHEV 462 + Turbo 550 (new); 971.2 base 325 + GTS 473 (new); M48.40 400 / MCW.BA 520.
- **Macan**: MCY.PA 252/248/261; MCT.MA 340/348; MCT.LA 400; 2.9TT S 375 (new).

**Skips (8):** 911 3800CC_VIND 2012+2013 (pos5-D merges 997.2 Turbo 500/Turbo S 530); Cayenne 3600CC 2015-18 ×4 (base NA 300 / S TT 420 / GTS TT 440 — no leader); Macan 3000CC 2020+2021 (no 3.0L petrol Macan those years).

## Spec normalization (32b) + audit repairs (32c)

32b: 28 ESTIMATE overrides + 1 normalization + 22 power syncs from pre_step32 backup variant majorities (0W-40 dominant across air-cooled-era/987/981/M46/M48/M55 families). ESTIMATE among batch targets: **0**.

32c: MDJ oil → 0W-40/5.7L and MDW vis 0W-40 (LN Engineering C40 + NHTSA approved-oils PDF); MCT/MDH bare codes consolidated → MCT.LA @400hp (only 3.6 Macan 2017-18 = Turbo); **M18.00 identified as 918 Spyder** — 874 (887PS) → 887hp US combined, fuel → Hybrid; hybrid-family codes M06.EC/MCG.E/MCG.FA + 6 hybrid-named variants → Hybrid. Remaining documented NULL-power Porsche rows: MA1 (truncated code), MDK (no displacement) + the 8 LEMON skips.

## Files
- `step32_step5_lemon_batch23_porsche.py` · `step32b_estimate_override.py` · `step32c_fix_vote_contamination.py` · `step5_lemon_lib.py` (new shared batch engine)
- CSV: `database_enriched/csv_exports/40_lemon_step32_decisions.csv` (+ DRYRUN)
- Backup: `database_enriched/backups/car_database_backup_pre_step32_2026-10-01.db`

**Next: Lincoln 192 (batch 24).**
