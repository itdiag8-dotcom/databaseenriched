
## Batch 22 — Land Rover (2026-10-01)
- 194 LEMON rows → 179 mapped / 15 documented skips (Range 2000CC bare ×1, Range 2022-25 bare ×4, Range 3000CC bare ×10 — unresolvable without VIN letter). LEMON 2,285→2,106; engines 7,852→7,679.
- Engine decode via Wikibooks LR VIN decoder (pos 6 / pos 8 eras) + era intercepts for power (204PT 240→296; AJ300P 395/355; 508PS 510/518).
- 6 NEW engines (Rover OHV 4.0/4.6, P400e, P440e/P550e, P530 N63TU3, P530 S68); 12 ROW_FIXES (M62B44 cc 3666→4398); 17 fuel fixes (306DT→Diesel ×10, 204DTD→Diesel ×2, PHEV→Hybrid ×5).
- step31b: 9 EST overrides + 3 normalized + 12 power syncs; audit clean.
- step31c vote-audit repairs (web-verified): B6324S 9.22L→7.7L [costaoils + landroverforums], 25K4F 0W-40→5W-40 [AMSOIL + auto-data.net]; pre-existing junk row 4900 (Discovery 2003) mislinked AJ34→4.6 V8 (Rover OHV) @217hp [3 auction/review sources].
- Scripts: step31_step5_lemon_batch22_landrover.py, step31b_estimate_override.py, step31c_fix_vote_contamination.py; CSV 39; backup pre_step31.
