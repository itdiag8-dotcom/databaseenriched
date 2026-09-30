# STEP 5 — Batch 18: Infiniti LEMON Replacement (step27 / step27b / step27c)

**Date:** 2026-09-30 · **Scope:** 230 `LEMON_INFINITI_*` variants, 32 models, MY2000–2025
**Result:** **230 mapped / 0 skipped** — first brand fully cleared, no skips needed ·
LEMON total 3,301 → **3,071** · engines 8,846 → **8,620**
Verification: 0 orphan refs, 0 count mismatches, 0 fuel conflicts, 0 ESTIMATE specs, 0 spec-power mismatches.

## Signals used
Model names encode displacement (FX35/M56/Q45/QX56…), cc markers (Q50/Q60/Q70/Q70L/QX70),
fuel column (hybrids), trim slugs (Q50HYBRID*, Q60IPL→348hp). The identity assert (new batch-17
rule) ran for the first time and passed.

## Engine families mapped
- **VQ V6:** VQ30DE 227 (I30), VQ35DE 240-303 across G35/I35/JX35/QX4/M35/FX35/QX60-14-16 (n=156),
  VQ35HR 297-306 (EX35/FX35-09+/G35-07+/M35-09+), VQ35DD 295 (QX60 2017+ — Infiniti press kit
  confirms the DIG 3.5 arrived for 2017, not 2022), VQ37VHR 325-348 (n=106, biggest target).
- **VK V8:** VK45DE 315-340 (Q45/M45/FX45), VK50VE 390 (FX50/QX70 5.0), VK56DE 315-320
  (QX56 04-10), VK56VD 400/420 (QX56 11-13/QX80/M56/Q70 5.6; row power fixed 360→400).
- **Modern:** VR30DDTT 300/400 (Q50/Q60 3.0t, n=23; Red Sport = same family row), KR20DDET VC-T
  268 (QX50 2019+/QX55; Altima 248hp documented in same row), M274DE20 208 (Q50/Q60 2.0t + QX30 —
  the Mercedes-sourced engine; DB even had a pre-existing 'Q50 2.0 16v Turbo' row for it).
- **Hybrids (new rows):** VQ35HR Hybrid "Direct Response" 360hp net (M35h/Q50/Q70/Q50-2015 hybrids,
  13 lemon rows + 3 pre-existing Euro-catalog hybrids relinked in step27c), QR25DER Hybrid 250hp
  net (QX60 supercharged-2.5 + 15kW motor, per Infiniti press kit).
- **Ancestors:** VH41DE 4.1 266hp (Q45 G50 2000-01, new row), VG33E 3.3 168 (QX4 2000), SR20DE 140 (G20).

## US-lineup findings (web-verified)
- **Q50:** hybrid dropped after 2018, **2.0t dropped for 2020** (2020+ = all 3.0t) — the 2019 rows
  carried cc markers so even they were unambiguous (2000CC = M274, 3000CC = VR30).
- **Q60:** four-cylinder dropped for 2019 (all 3.0t 300/400; KBB).
- **QX70: V8 discontinued for 2015** (cars.com) — 2015-2017 = 3.7 325hp only, so the bare
  AWD/RWD rows needed no skip.
- **QX60:** hybrid 2014-2017 only; 3.5 = VQ35DE 265hp (14-16) → **VQ35DD 295hp (2017+)**.

## Fuel fixes
4 → Hybrid (M35h 2012-13 mislabeled Petrol; Q50 2015 hybrid trims). Step27c additionally relinked
3 pre-existing Euro-catalog M/Q70 hybrids off the plain VQ35HR petrol row (found by the fuel-
conflict audit; conflicts pre-dated this batch).

## step27b spec normalization
7 ESTIMATE overrides + 5 normalizations + 13 power syncs. Values audited: VR30DDTT 0W-20/5.44L
and KR20DDET 0W-20/4.73 (VC-T documented 0W-20), VK56VD 5W-30/6.51 (6.9qt), VQ35DE 5W-30/4.73,
M274DE20 0W-30/6.27 (unanimous viscosity; caps span 5.67-6.62 across RWD/AWD). All consistent.

## Incidents
- 10th full workspace rewind caught by baseline assert pre-work (no loss).
- Dry-run fix: Q50 2019 rows carry cc markers (mappable) — skip rule narrowed to bare rows only,
  resulting in 230/230 with zero skips.

## Next
Dodge 207 → Buick 205 → Subaru 205 → Land Rover 194 (DB junk queued for LR batch: 306DT label
"3 (est.)", EGH mislabel, AJ200/AJ41 vocabulary) → Porsche 193.
