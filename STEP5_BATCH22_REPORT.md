# STEP 5 — BATCH 22: Land Rover (194 LEMON rows → 179 mapped / 15 documented skips)

**Scripts:** `step31_step5_lemon_batch22_landrover.py` (dry-run then apply), `step31b_estimate_override.py` (EST/sync, sed-derived from step30b), `step31c_fix_vote_contamination.py` (vote-audit repairs + sweeps)
**Backup:** `backups/car_database_backup_pre_step31_2026-09-30.db`
**Decisions CSV:** `csv_exports/39_lemon_batch22_decisions.csv` (+ `_DRYRUN`)

## Baseline → Result

| Metric | Before | After |
|---|---|---|
| LEMON rows | 2,285 | **2,106** (−179) |
| Total engines | 7,852 | **7,679** |
| Land Rover fuel | Diesel 131 / Hybrid 3 / Petrol 245 | Diesel 133 / Hybrid 5 / Petrol 247 |
| Orphan refs / count mismatches / NULL powers (LR non-LEMON) | — | **0 / 0 / 0** |

Remaining LR LEMON = 15 documented skips (genuinely unresolvable without VIN letter):
- `Range 2000CC bare` ×1 (P38 4.0 vs 4.6, no VIN letter)
- `Range 2022-25 bare` ×4 (L405 P530 N63TU3 vs L460 S68 transition ambiguity)
- `Range 3000CC bare` ×10 (SCV6 340 vs Td6 254 vs I6 395 — three-way without VIN letter)

## Method

Engine identification via **Wikibooks Land Rover VIN decoder** (position 6 for 1987-2016 non-LR2/DiscSport/Evoque; position 8 for LR2/DiscSport/Evoque '08-16 and for 2017+ models), corroborated by disco3.co.uk VIN wiki, KBB/CarBuzz/MotorTrend (2024 Defender), Car and Driver + Cars.USNews (US Velar D180 180hp diesel '18-19 confirmed; 2018 P250 = 247hp). LEMON rows carried VIN letters and cc markers but **no power hints**, so power came from trim-level decodes with era intercepts (e.g. 204PT: 240 GTDI '13-15, 237 '16-18, 247 Velar '17-18, 246 '19, 296 Defender/Discovery P300 '20+).

## Mappings applied (179 rows)

| Engine code | n | Power / Fuel | Notes |
|---|---|---|---|
| AJ126 | 117 | 335hp Petrol | 3.0 SCV6 340 SIC; consolidated to 335 (cross-brand majority incl. Jaguar) |
| 204PT | 97 | 237hp Petrol | 2.0 GTDI Ingenium, era intercepts 240→296 |
| 508PS | 42 | 510hp Petrol | 5.0 SC V8 (510 SC / 518 Defender V8) |
| 306DT | 25 | 254hp Diesel | 3.0 Td6 twin-turbo; **fuel fix ×10** (rows said Petrol) |
| AJ300P | 31 | 395hp Petrol | 3.0 I6 MHEV (395 P400 / 355 P360) |
| B6324S | 13 | 230hp Petrol | LR2 3.2 Volvo SI6 '08-12 |
| 25K4F | 14 | 177hp Petrol | Freelander 2.5 KV6 |
| AJ41 | 15 | 305hp Petrol | 4.4 NA AJ-V8 (LR3/RR/RRS '05-'09) |
| 508PN | 16 | 375hp Petrol | 5.0 NA AJ-V8 (LR4 '10-13) |
| M62B44 | 10 | 282hp Petrol | RR L322 BMW 4.4 '03-05; **ROW_FIX junk cc 3666→4398** |
| 428PS | 5 | 400hp Petrol | 4.2 SC AJ-V8 ('06-09) |
| 406PN | 4 | 216hp Petrol | LR3 4.0 Cologne V6 (US '05-07) |
| 204DTD | 11 | 180hp Diesel | 2.0d Ingenium; **fuel fix ×2** |
| 4.0 V8 (Rover OHV) | 3 | 182hp | NEW engine (Discovery II '00-02) |
| 4.6 V8 (Rover OHV) | 4 | 217hp | NEW engine (Disc II '03-04 / P38 '01-02) |
| P400e 2.0 PHEV (AJ200P + motor) | 3 | 398hp Hybrid | NEW; **fuel fix ×3 → Hybrid** |
| P440e/P550e 3.0 I6 PHEV | 2 | 434hp Hybrid | NEW; **fuel fix ×2 → Hybrid** |
| P530 4.4 V8 TT (N63TU3) | 2 | 523hp Petrol | NEW (RR/RRS '22-23) |
| P530 MHEV 4.4 V8 TT (S68) | 4 | 523hp Petrol | NEW (RR/Defender '24+) |

6 NEW engine rows created; 12 ROW_FIXES (displacement/junk corrections, incl. M62B44 3666→4398cc).

## Fuel fixes (17 rows)
306DT → Diesel ×10, 204DTD → Diesel ×2, P400e → Hybrid ×3, P440e/P550e → Hybrid ×2 (cross-brand physical-conflict rule; PHEV rows were listed Petrol but are Hybrid).

## step31b — EST overrides + power syncs
9 ESTIMATE overrides written with citations, 3 normalized to canonical names, 12 power syncs. Audit after: ESTIMATE 0, orphans 0, mismatches 0, spec-power mismatch 0.

## step31c — vote line-audit repairs (web-verified)
- **B6324S**: majority 5W-30/**9.22L** rejected — contamination (no SI6 takes 9L). Set **5W-30/7.7** [costaoils.com 2008 LR2 3.2L guide; landroverforums.com "LR Techniker": 7.7L / 8.1qt].
- **25K4F**: unanimous **0W-40**/5.2 rejected — appears in no source. Capacity 5.2L confirmed exactly [auto-data.net, engine code 25K4F]; set **5W-40**/5.2 [AMSOIL 2002 Freelander 2.5 spec: 5W-40 all-temps, 10W-40 above −20°C, 5.5qt w/ filter].
- **Pre-existing junk row fix**: id 4900 Discovery 2003 "4.0 V8" was mislinked to AJ34 (Jaguar 4.2 SC) with NULL power. Verified 2003-04 US Discovery II = **4.6 V8 217hp** [Toyota-4Runner forum review quoting Land Rover press kit; carsandbids SE7 listing; pcarmarket HSE listing]. Relinked → `4.6 V8 (Rover OHV)`, 217hp/161kW, engine_type "4.6 V8", production_end 2004. Counts recomputed (AJ34 47→46, 4.6 Rover OHV 4→5).

## Final state
engines 7,679 · LEMON 2,106 · LR fuel: Diesel 133 / Hybrid 5 / Petrol 247 · 0 orphans / 0 count mismatches / 0 NULL powers.
