# STEP 97 — Fuse box data import from startmycar.com

## Goal
Enrich `database_enriched/car_database.db` with fuse box information (fuse position,
fuse type, amperage, circuit description + diagram image URL) matched 1:1 to the
models already present in the database, scraped from https://www.startmycar.com.
Models missing on startmycar.com will be sourced from another website in a later step.

## Schema added
- `fusebox_generations` — one row per model generation (model_id FK → models.id,
  brand/model names, startmycar slugs, generation name/code, year range,
  representative year scraped, source URL).
- `fusebox_boxes` — one row per physical fuse box (name, diagram `image_url`,
  `image_blob` reserved for the binary image).
- `fusebox_fuses` — one row per fuse/relay (position_no, element_type, amperage,
  description). Duplicate position numbers are intentional (engine/trim variants).

## Method
- Granularity chosen by owner: **one dataset per generation** (representative =
  newest year page of that generation), brands processed **alphabetically**.
- The sandbox has no direct egress to startmycar.com, so pages are fetched through
  the agent's page-fetch tool and transcribed to `fusebox_scrape/parsed/*.json`,
  then loaded with `load_fusebox_parsed.py` (idempotent).
- Diagram image binaries cannot be downloaded from the sandbox (blocked egress).
  `download_fusebox_images.py` fills `fusebox_boxes.image_blob` from the stored
  URLs — run it on any machine with normal internet access.
- Progress/resume state: `fusebox_scrape/state.json`.

## Progress (this batch)
| Brand | Models with data scraped | Generations | Boxes | Fuses/relays |
|---|---|---|---|---|
| Abarth | 500, 595, 695, Grande Punto (124 & Punto Evo have no data on site) | 5 | 9 | 177 |
| Acura | MDX (g4 2021-2026, g3 2013-2020) — in progress | 2 | 7 | 216 |
| **Total** | | **7** | **16** | **393** |

## Coverage notes
- startmycar.com lists ~91 makes. 59 DB brands are NOT on the site (AC, Alpina,
  Bentley, Lamborghini, Lada, Lotus, McLaren, Rolls-Royce, …) — full list in
  `fusebox_scrape/state.json` → to be covered from a second source later.
- Fuse tables are per-generation; many year pages inside a generation share the
  same table, which is why one representative year per generation is scraped.

## Next batches (alphabetical)
Acura (remaining: MDX g2/g1, TL, RDX, TSX, TLX, ILX, Integra, CL, RL, RLX, RSX,
ZDX, NSX, Legend, hybrids) → Alfa Romeo → Aston Martin → Audi → Austin → BMW → …
