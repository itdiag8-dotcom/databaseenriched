# STEP 5 — Batch 47: Smart + Tesla + Daewoo LEMON Replacement (Step 56)

**Date:** 2026-10-01 · **Scripts:** `step56_step5_lemon_batch47_sdt.py` + `step56b_estimate_override.py`
**Result:** 31 LEMON rows (Smart 12, Tesla 10, Daewoo 9) → **31 mapped (100%) / 0 skips**

| Metric | Before | After |
|---|---|---|
| LEMON rows (all brands) | 71 | **40** (−31) |
| LEMON Smart / Tesla / Daewoo | 12 / 10 / 9 | **0 / 0 / 0** |
| engines rows | 5,725 | **5,696** (−31 LEMON +3 new) |
| Fuel corrections | — | **11** (10 Tesla + 1 smart ED → Electric) |
| Orphans / count mismatches / fuel conflicts | — | **0 / 0 / 0** |

## Three brands, one question

These three have no hardware in common. They are batched together because each is a handful of
rows and because each poses the same question in a different form: what do you do when the
crawl's model name has lost the information you need?

**Smart kept its information.** One nameplate, one engine per generation, and the fill tracks
the generation change exactly: 3.31-3.4 L through the 451 (1.0 three-cylinder, 70hp US) and
3.59 L from 2016, the 453's 0.9 turbo (89hp). The MY2015 `FORTWOELECTR` trim row is the
Electric Drive, and is corrected from Petrol to Electric against a new 74hp BEV engine row.

**Daewoo kept its information too.** Lanos, Nubira and Leganza each had exactly one US engine,
and the fills agree: 3.78 L for the 1.6, 3.88-3.97 L for the 2.0, 3.97 L for the 2.2 — the last
of which had no engine row in this database and is added as `X22SE`.

**Tesla has lost it entirely.** Every Model S, 3, X and Y truncates to `MODEL`; there is no
displacement, no fill, no VIN, and one row per year — the crawl itself could not keep the four
cars apart. What *is* knowable is that every Tesla ever built is battery-electric, and that is
what these rows now say: a single explicit `BEV (Tesla, model unidentified)` engine, fuel
corrected from Petrol to **Electric**, and power deliberately left NULL rather than invented.
That is a far smaller claim than the ten `LEMON_TESLA_MODEL_*` placeholders made — and unlike
them, it is true.

## 3 new engines

| Code | Engine |
|---|---|
| `X22SE` | 2.2 I4 DOHC Family II (Leganza US, 131hp) |
| `Electric Drive (smart ForTwo ED)` | 17.6 kWh BEV drive unit, 74hp |
| `BEV (Tesla, model unidentified)` | BEV drive unit, model and power not recoverable |

## Fixes

**4 ROW_FIXES** (`STEP56_VERIFIED`) — `M132.910` ("1 (est.)"), `M281.910` ("with manual
adjustment"), `A16DMS` and `X20SED` all carried junk or bare descriptors.
**step56b** — 4 ESTIMATE overrides (all four off the junk 2.8/3.2 L placeholder fills onto the
crawl's measured values), 1 normalization, 1 power sync.

## Skips

None.

## Known residual

The 10 Tesla variants have NULL `engine_power_hp` by design, as documented above.

## Files

- `step56_step5_lemon_batch47_sdt.py`, `step56b_estimate_override.py`
- `database_enriched/csv_exports/64_lemon_step56_decisions.csv` (+ `_DRYRUN`)
- `database_enriched/backups/car_database_backup_pre_step56_2026-10-01.db`

**Next: Batch 48 — Porsche (8) + Volkswagen (3) + the 8 deferred Audi RS rows.**
