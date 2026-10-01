# Step 90–92 — Model pictures from 7zap.com

Goal: give every row of `models` a picture of the car, sourced from the OEM
catalog site **https://7zap.com/en/**.

7zap publishes, for each brand, a catalog page listing every model *generation*
with a photo of that generation:

```
https://7zap.com/en/catalog/cars/bmw/
  BMW 1' E82 (2007 - 2011)   https://img.7zap.com/images/oem/models/BMW_1-series_E82.webp
  BMW X5 G05 (2018 - 2020)   https://img.7zap.com/images/oem/models/BMW_X5_G05.webp
```

## Pipeline

| Script | What it does |
| --- | --- |
| `step90_fetch_7zap_catalog.py` | crawls the 7zap brand catalogs → `database_enriched/7zap/catalog_models.jsonl` (one row per model generation: name, years, catalog page, image URL) |
| `step91_match_7zap_images.py` | matches every `models` row to the best 7zap generation and writes the picture onto the row |
| `step92_download_7zap_images.py` | downloads the pictures to `database_enriched/model_images/<brand>/` and stores the local path |
| `sevenzap_lib.py` | shared HTML/markdown/TSV parsing, brand mapping, name normalisation |

```bash
python3 step90_fetch_7zap_catalog.py --db-brands      # crawl every brand used by the database
python3 step91_match_7zap_images.py --dry-run         # preview the matching
python3 step91_match_7zap_images.py                   # write image_* columns (backs the DB up first)
python3 step92_download_7zap_images.py                # fetch the .webp files
```

## New columns on `models`

| Column | Example |
| --- | --- |
| `image_url` | `https://img.7zap.com/images/oem/models/BMW_X5_G05.webp` |
| `image_local_path` | `database_enriched/model_images/bmw/BMW_X5_G05.webp` (filled by step 92) |
| `image_source_page` | `https://7zap.com/en/catalog/cars/bmw/x5-g05-parts-catalog/` |
| `image_match_name` | `X5 G05 (2018 - 2020)` |
| `image_match_score` | `0.64` |
| `image_match_method` | `exact` / `code` / `family` / `fuzzy` |

Reports: `database_enriched/csv_exports/90_7zap_model_images.csv` (everything
matched) and `90_7zap_unmatched_models.csv` (rows left without a picture, with
the closest candidate and its score for review).

## Matching logic (mode `family`, the default)

The database stores model families *and* engine/trim rows (`1 SERIES`, `116I`,
`3 SERIES – F30/F31/F34/F35`), while 7zap stores generations (`3' F30 LCI`).
Each candidate is scored on:

* normalised name similarity (accents, punctuation and filler words such as
  `SERIES`, `SALOON`, `FACELIFT` removed);
* **chassis-code overlap** — `C-CLASS (W204)` ↔ `C-Class W204`, `X5 (F15, F85)` ↔ `X5 F15`;
* **family key** — brand rules collapse trims to their family (`116I` → `1 SERIES`,
  `M140I` → `1 SERIES`, `C240` → `C CLASS`, `iX3` → `X3`), plus an alternative-family
  table for derivatives with no catalog entry of their own (`i7` → `7 SERIES`,
  `EQS` → `S CLASS`);
* **production-year overlap**, which selects the right generation inside a family;
* a penalty when the candidate carries a badge the query never asked for, so a
  `316D` does not inherit the `M3` photo.

Accept thresholds: `family` 0.45 (best-guess, every row that has a plausible
family gets a picture), `strict` 0.80 (exact/chassis-code only), `gen` 0.55
(only rows that name a generation themselves).

## Current state of the data

The crawl in this environment could only be run through a text proxy (direct
outbound HTTPS to 7zap.com is blocked in the sandbox), so the catalog was
**seeded for the two largest brands** from the live 7zap pages, captured in
`7zap_captures/*.tsv` and ingested with
`python3 step90_fetch_7zap_catalog.py --md-dir 7zap_captures`.

| Brand | DB models | matched | coverage |
| --- | --- | --- | --- |
| BMW | 379 | 362 | 95.5 % |
| Audi | 279 | 241 | 86.4 % |
| **total** | 6252 | 603 | 9.6 % |

Breakdown of the 603 matches: 37 exact, 114 chassis-code, 449 family, 3 fuzzy.
175 distinct pictures cover those 603 rows.

### Finishing the job (needs plain internet access)

```bash
pip install requests
python3 step90_fetch_7zap_catalog.py --db-brands   # ~70 brands, ~1.5 s per page
python3 step91_match_7zap_images.py                # re-match everything
python3 step92_download_7zap_images.py             # download every picture
```

Notes / limitations:

* 7zap serves one **region** per catalog page (USA by default) and switches
  regions client-side, so European-only generations (BMW `1' F20`, Audi `A1`,
  `A2`…) are missing from the seeded catalog — they are simply left unmatched
  rather than mis-matched. A full crawl should also collect the regional
  variants of each brand page.
* `database_enriched/model_images/` is git-ignored: the pictures are 7zap
  assets, re-downloadable at any time with step 92.
* Pictures are generation-level, so sibling trims legitimately share one photo.

---

## Step 93 - all brands, all regions (supersedes the step-90 crawl)

The region gap above is now solved, and so is brand enumeration.

**The brand catalog pages were the wrong entry point.** `…/catalog/cars/<brand>/`
renders exactly one region (the brand's default - USA for BMW/Audi/Toyota,
Global for Fiat/Opel, Europe for Skoda/Dacia…) and the region tabs are hash
links (`#region=europe`) resolved client-side; `?region=…` is ignored by the
server. No amount of brand-page crawling reaches `1' F20`.

**7zap's sitemap index does not have that problem.** It lists one sitemap per
*generation*, region-independent:

```
https://7zap.com/sitemap.xml
  -> https://7zap.com/sitemaps/cats/7zap_com/bmw/generation_1-series-f20.xml   <- Europe-only
  -> https://7zap.com/sitemaps/cats/7zap_com/opel/generation_astra-k.xml
```

and the generation slug maps 1:1 onto a model page that carries the picture,
the full name, the years and the region label:
`https://7zap.com/en/catalog/cars/bmw/1-series-f20-parts-catalog/`.

`step93_fetch_7zap_all_regions.py` walks that index. One request per
generation, threaded, resumable, merging into the same
`database_enriched/7zap/catalog_models.jsonl` that step 91 consumes - so
nothing already matched is lost.

```bash
pip install requests
python3 step93_fetch_7zap_all_regions.py --list-only          # count what exists, writes 7zap/generations.json
python3 step93_fetch_7zap_all_regions.py --db-brands          # crawl the brands our DB actually uses
python3 step93_fetch_7zap_all_regions.py --resume             # pick up after an interruption
python3 step91_match_7zap_images.py                           # re-match every model row
python3 step92_download_7zap_images.py                        # download the pictures
```

`--workers 4 --delay 0.5` (the defaults) is roughly 8 pages/s worst case and
polite; several thousand generations means tens of minutes, not hours. The
parser is covered offline by `python3 step93_selftest.py` (stubbed HTTP:
sitemap parsing, title/year/region/picture extraction, idempotent merge) -
useful because this sandbox has no route to 7zap.

### What the ceiling actually is

7zap carries **70 car brands** (`database_enriched/7zap/brands.json`). Our
database has 147. The overlap is the real upper bound on coverage:

| | brands | model rows |
| --- | --- | --- |
| on 7zap | 56 | 5 023 (80.3 %) |
| not on 7zap | 91 | 1 229 (19.7 %) |

Full per-brand detail: `database_enriched/csv_exports/90_7zap_brand_coverage.csv`.

The biggest absences are exotics and brands 7zap never carried parts for:
Ferrari (115 rows), Aston Martin (78), Bugatti (58), Isuzu (54), Bentley (45),
Maserati (44), Alpina (41), Brilliance (40), Jaguar (40), GWM (39), Land Rover
(35), Lotus (34), Tata (34), Daihatsu (33), Mahindra (33). Those rows cannot
get a 7zap picture by any means; a second source would be required, which is
outside what was asked for here.

So: ~80 % of model rows are reachable, and within a reachable brand the
family matcher has been giving 86-95 % (Audi, BMW), i.e. an expected end state
near 70-75 % of all 6 252 rows with a real generation photo.
