# Step 95 - picture catalog in the dashboard (7zap-style selection flow)

The local dashboard (`database_enriched/server.js` + `dashboard/index.html`) selected a
car through four dropdowns: brand → model → engine type → engine code. That is
precise but blind: you had to already know the model name. 7zap solves the same
problem visually - a grid of brands, then a grid of **generation cards with a
picture, a name and the production years** - and that is what this step adds,
reusing the pictures collected in steps 90-94.

## What the dashboard looks like now

A **Catalog / Editor** switch sits in the header; the catalog is the landing
view.

1. **Brands** - 147 tiles, each with a cover picture taken from that brand's
   best-matched model, the model and variant counts, and a coverage bar reading
   `x/y with picture`. An A–Z jump bar and a filter box narrow the grid, and
   *with picture only* hides brands that have none.
2. **Models** - generation cards exactly like a 7zap brand page: picture,
   model name, years, and pills for variant and engine counts. Each card also
   shows **which catalogue entry the picture came from** (`picture: 1' E82
   (2007 - 2011)`) so a wrong family match is obvious at a glance, plus a
   `7zap` / `wikidata` source badge.
3. **Engine types** - the chosen model is repeated as a large card with its
   picture, source-page link and attribution; below it, one tile per engine
   type.
4. **Engine codes** - one tile per code with fuel and power; clicking it jumps
   straight into the existing editor with all four dropdowns pre-selected, so
   nothing about editing or the staged-save workflow changes.

## Server-side additions (`server.js`)

| route | purpose |
| --- | --- |
| `GET /api/catalog/brands` | brand tiles: counts, picture coverage, cover image |
| `GET /api/catalog/brands/:brand/models` | model cards incl. image, match name/score/method, credit, licence |
| `GET /api/catalog/stats` | coverage summary shown under the breadcrumb |
| `GET /model_images/<brand>/<file>` | serves pictures already downloaded by step 92 |
| `GET /img?u=<url>` | **proxy + disk cache** for pictures not downloaded yet |

The proxy is the piece that makes the catalog usable immediately: the database
currently stores 781 image URLs but **zero local files** (step 92 has not been
run yet), and hot-linking `img.7zap.com` from a browser page can be refused.
`/img` fetches with a proper `User-Agent`/`Referer`, writes the bytes to
`model_images/_cache/<sha1>.<ext>` and serves them from there afterwards, so the
grid gets faster as you browse and keeps working offline. The host allow-list is
limited to `img.7zap.com`, `7zap.com`, `commons.wikimedia.org` and
`upload.wikimedia.org`; anything else returns 403.

`server.listen` now honours `HOST` (default stays `127.0.0.1`, so the dashboard
remains local-only unless you deliberately set `HOST=0.0.0.0`).

## Attribution

Commons pictures are free **only if credited**, so model cards print the stored
`image_credit` / `image_license`, and fall back to "Wikimedia Commons · author
and licence on the source page" for rows seeded without the credit lookup.
7zap tiles show no credit line.

## Testing without a browser

`node dashboard/catalog_smoke_test.mjs` (with the server running) executes the
dashboard's own JavaScript against the real API behind a stubbed DOM and walks
all four levels. Current output:

```
brands level  : 147 tiles
models level  : 379 tiles, 362 pictures      (BMW)
types level   : 1 (E81) -> 5 tiles
codes level   : 116d 2000 D -> 1 engine codes
attribution   : credit line rendered
CATALOG SMOKE TEST OK
```

## Running it

```bash
cd database_enriched
node server.js            # http://localhost:3000, catalog opens by default
```

Brands whose pictures are still missing simply show a lettered tile; running
step 93/94 and then step 92 fills them in - after which `/model_images/...`
serves the local files and the proxy is no longer touched.
