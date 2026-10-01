#!/usr/bin/env python3
"""Step 94 - fallback pictures from Wikidata / Wikimedia Commons.

Why this exists
---------------
7zap carries 70 car brands; the database has 147. Ferrari, Aston Martin,
Bugatti, Isuzu, Bentley, Maserati, Jaguar, Land Rover, Tesla ... simply have no
7zap parts catalog, which is 91 brands / 1 229 model rows that step 90-93 can
never illustrate (see database_enriched/csv_exports/90_7zap_brand_coverage.csv).

Wikidata covers exactly that gap:

    ?model wdt:P31/wdt:P279* wd:Q3231690   # instance of (a subclass of) automobile model
    ?model wdt:P176|wdt:P1716 ?brand       # manufacturer / brand
    ?model wdt:P18 ?image                  # the picture, hosted on Wikimedia Commons

The brand is bound *by label or alias*, not by a hard-coded QID, so "GWM"
resolves to Great Wall Motor and "DS" to DS Automobiles, and both "Land Rover"
entities are picked up at once. A small ALIASES table fixes the handful of
database spellings that are not Wikidata labels ("Maruti", "Ikco", "Lti
Vehicles"...).

Licensing (important, unlike 7zap)
----------------------------------
Commons pictures are free but nearly all require **attribution**, so this step
also pulls the author and licence for every file from the Commons API and
stores them next to the picture. step 91 writes them into
`models.image_credit` / `models.image_license`; publish them with the image.

Usage
-----
    python3 step94_fetch_wikidata_images.py --list-brands     # what is missing / resolvable
    python3 step94_fetch_wikidata_images.py                   # every DB brand absent from 7zap
    python3 step94_fetch_wikidata_images.py --brands Ferrari Jaguar
    python3 step94_fetch_wikidata_images.py --all-db-brands   # also brands 7zap already covers
    python3 step94_fetch_wikidata_images.py --no-credits      # skip the Commons licence lookup

Writes database_enriched/wikidata/catalog_models.jsonl (same shape as the 7zap
catalog), then:

    python3 step91_match_7zap_images.py --catalog database_enriched/wikidata/catalog_models.jsonl
    python3 step92_download_7zap_images.py

Offline test: python3 step94_selftest.py
Needs outbound HTTPS to query.wikidata.org and commons.wikimedia.org.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.parse

import sevenzap_lib as lib

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia asks for a descriptive, contactable User-Agent.
UA = "car-database-enrichment/1.0 (model picture backfill; contact: repo owner)"

# database brand_name -> the label/alias Wikidata actually knows
ALIASES = {
    "Maruti": "Maruti Suzuki",
    "Ikco": "Iran Khodro",
    "Lti Vehicles": "LTI",
    "Dr Motor": "DR Automobiles",
    "Chana": "Changan Automobile",
    "HSV": "Holden Special Vehicles",
    "LDV": "LDV Group",
    "AC": "AC Cars",
    "Renault Samsung": "Renault Samsung Motors",
    "Mitsubishi Fuso": "Mitsubishi Fuso Truck and Bus Corporation",
    "Besturn": "FAW Besturn",
    "Dadi": "Dadi Auto",
    "Naza": "NAZA",
    "Great Wall": "Great Wall Motor",
    "GWM": "Great Wall Motor",
    "Tata": "Tata Motors",
    "Mahindra": "Mahindra & Mahindra",
    "Lynk & Co": "Lynk & Co",
    "Alpina": "Alpina",
    "Lotus": "Lotus Cars",
    "Jaguar": "Jaguar Cars",
    "Rover": "Rover Company",
    "Triumph": "Triumph Motor Company",
    "Shelby": "Shelby American",
    "Saleen": "Saleen Automotive",
    "Westfield": "Westfield Sportscars",
    "Marcos": "Marcos Engineering",
    "Metrocab": "Metrocab",
    "Golden Dragon": "Golden Dragon Bus",
    "Dongfeng Fengxing": "Dongfeng Fengxing",
    "Oreion Motors": "Oreion Motors",
}

MODELS_QUERY = """
SELECT ?m ?mLabel ?img (YEAR(MIN(?s)) AS ?y1) (YEAR(MAX(?e)) AS ?y2) WHERE {
  ?b rdfs:label|skos:altLabel %(label)s .
  { ?m wdt:P176 ?b } UNION { ?m wdt:P1716 ?b }
  ?m wdt:P31/wdt:P279* wd:Q3231690 ;
     wdt:P18 ?img .
  OPTIONAL { ?m wdt:P571 ?s }
  OPTIONAL { ?m wdt:P576 ?e }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}
GROUP BY ?m ?mLabel ?img
"""

BRAND_PROBE_QUERY = """
SELECT ?lbl ?b ?bLabel (COUNT(DISTINCT ?m) AS ?n) WHERE {
  VALUES ?lbl { %(labels)s }
  ?b rdfs:label|skos:altLabel ?lbl .
  ?m wdt:P31/wdt:P279* wd:Q3231690 .
  { ?m wdt:P176 ?b } UNION { ?m wdt:P1716 ?b }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}
GROUP BY ?lbl ?b ?bLabel ORDER BY ?lbl DESC(?n)
"""


# --------------------------------------------------------------------------
def make_session():
    if requests is None:
        sys.exit("pip install requests")
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/sparql-results+json"})
    return s


def sparql(session, query: str, retries: int = 4) -> dict | None:
    """Run a SPARQL query; WDQS throttles hard, so back off politely."""
    for attempt in range(retries):
        try:
            r = session.get(SPARQL_ENDPOINT, params={"query": query, "format": "json"}, timeout=120)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 503):
                wait = int(r.headers.get("Retry-After", 0)) or 10 * (attempt + 1)
                print(f"  .. throttled, waiting {wait}s")
                time.sleep(wait)
                continue
            print(f"  ! HTTP {r.status_code} from WDQS")
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1:
                print(f"  ! {exc}")
        time.sleep(3 * (attempt + 1))
    return None


def literal(label: str) -> str:
    return '"%s"@en' % label.replace("\\", "\\\\").replace('"', '\\"')


def commons_filename(image_url: str) -> str:
    """.../Special:FilePath/Ferrari%20F40%207.jpg -> 'Ferrari F40 7.jpg'"""
    tail = image_url.rsplit("/", 1)[-1]
    return urllib.parse.unquote(tail).replace("_", " ")


def strip_brand(name: str, brand: str) -> str:
    """'Ferrari 348' -> '348'; keeps the name if it is only the brand."""
    prefixes = sorted({brand, ALIASES.get(brand, brand)}, key=len, reverse=True)
    for prefix in prefixes:  # longest first: "Maruti Suzuki Swift" -> "Swift"
        if prefix and name.lower().startswith(prefix.lower() + " "):
            stripped = name[len(prefix) + 1:].strip()
            if stripped:
                return stripped
    return name


COMPACT_QUERY = """
SELECT DISTINCT ?out WHERE {
  VALUES ?lbl { %(labels)s }
  ?b rdfs:label|skos:altLabel ?lbl .
  { ?m wdt:P176 ?b } UNION { ?m wdt:P1716 ?b }
  ?m wdt:P31/wdt:P279* wd:Q3231690 ; wdt:P18 ?img ; rdfs:label ?name .
  FILTER(LANG(?name)="en")
  OPTIONAL { ?m wdt:P571 ?s } OPTIONAL { ?m wdt:P576 ?e }
  BIND(CONCAT(STR(?lbl),"|",?name,"|",COALESCE(STR(YEAR(?s)),""),"|",
              COALESCE(STR(YEAR(?e)),""),"|",STRAFTER(STR(?m),"entity/"),"|",
              STRAFTER(STR(?img),"FilePath/"),";;") AS ?out)
}
"""


def parse_capture(text: str, brand_for_label: dict[str, str] | None = None) -> list[lib.CatalogModel]:
    """Parse the compact `brand|name|y1|y2|QID|file.jpg;;` records produced by
    COMPACT_QUERY (format=csv). Lets the catalog be seeded from a saved
    response instead of a live query."""
    rows: list[lib.CatalogModel] = []
    seen: set[tuple[str, str]] = set()
    for rec in text.replace("\n", "").split(";;"):
        rec = rec.strip().strip("\\")
        if not rec or rec.count("|") < 5:
            continue
        label, name, y1, y2, qid, filename = [c.strip() for c in rec.split("|", 5)]
        brand = (brand_for_label or {}).get(label, label)
        slug = lib.brand_to_slug(brand) or brand.lower().replace(" ", "-")
        if (slug, qid) in seen:
            continue
        seen.add((slug, qid))
        yf = int(y1) if y1.isdigit() else None
        yt = int(y2) if y2.isdigit() else None
        years_text = (f"({yf} - {yt})" if yf and yt else f"({yf} - )" if yf else "")
        rows.append(lib.CatalogModel(
            brand_slug=slug,
            brand_label=brand,
            model_name=strip_brand(name, brand),
            year_from=yf,
            year_to=yt,
            years_text=years_text,
            page_url=f"http://www.wikidata.org/entity/{qid}",
            image_url=f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}?width=1024",
            slug=qid,
            source="wikidata",
        ))
    return rows


def parse_models(payload: dict, brand_name: str) -> list[lib.CatalogModel]:
    """SPARQL JSON -> catalog rows (one per Wikidata model entity)."""
    rows: list[lib.CatalogModel] = []
    slug = lib.brand_to_slug(brand_name) or brand_name.lower().replace(" ", "-")
    seen: set[str] = set()
    for b in payload.get("results", {}).get("bindings", []):
        img = b.get("img", {}).get("value")
        label = b.get("mLabel", {}).get("value", "")
        entity = b.get("m", {}).get("value", "")
        if not img or not label or label.startswith("Q"):  # unlabelled entity
            continue
        qid = entity.rsplit("/", 1)[-1]
        if qid in seen:
            continue
        seen.add(qid)
        y1 = b.get("y1", {}).get("value")
        y2 = b.get("y2", {}).get("value")
        y1 = int(y1) if y1 and y1.lstrip("-").isdigit() else None
        y2 = int(y2) if y2 and y2.lstrip("-").isdigit() else None
        years_text = ""
        if y1:
            years_text = f"({y1} - {y2})" if y2 else f"({y1} - )"
        rows.append(
            lib.CatalogModel(
                brand_slug=slug,
                brand_label=brand_name,
                model_name=strip_brand(label, brand_name),
                year_from=y1,
                year_to=y2,
                years_text=years_text,
                page_url=entity,
                # ask Commons for a sane width instead of the 4000px original
                image_url=img.replace("http://", "https://") + "?width=1024",
                slug=qid,
                source="wikidata",
            )
        )
    return rows


def fetch_credits(session, rows: list[lib.CatalogModel], batch: int = 40) -> int:
    """Fill .credit / .license from the Commons API (attribution is required)."""
    by_file: dict[str, list[lib.CatalogModel]] = {}
    for r in rows:
        by_file.setdefault(commons_filename(r.image_url.split("?")[0]), []).append(r)
    files = sorted(by_file)
    done = 0
    for i in range(0, len(files), batch):
        chunk = files[i:i + batch]
        params = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "extmetadata",
            "iiextmetadatafilter": "Artist|LicenseShortName|Credit",
            "titles": "|".join("File:" + f for f in chunk),
        }
        try:
            r = session.get(COMMONS_API, params=params, timeout=60)
            pages = r.json().get("query", {}).get("pages", {})
        except Exception as exc:  # noqa: BLE001
            print(f"  ! commons credits: {exc}")
            continue
        for page in pages.values():
            title = page.get("title", "")[len("File:"):]
            info = (page.get("imageinfo") or [{}])[0].get("extmetadata", {})
            artist = _plain(info.get("Artist", {}).get("value", ""))
            lic = _plain(info.get("LicenseShortName", {}).get("value", ""))
            for row in by_file.get(title, []):
                row.credit = artist
                row.license = lic
                done += 1
        time.sleep(0.3)
    return done


def _plain(html: str) -> str:
    import html as html_mod
    import re

    txt = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", html_mod.unescape(txt)).strip()


# --------------------------------------------------------------------------
def db_brands() -> list[tuple[str, int]]:
    con = sqlite3.connect(lib.DB_PATH)
    rows = con.execute(
        "SELECT brand_name, COUNT(*) FROM models GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall()
    con.close()
    return [(r[0], r[1]) for r in rows]


def brands_on_7zap() -> set[str]:
    if not os.path.exists(lib.BRANDS_JSON):
        return set()
    with open(lib.BRANDS_JSON, encoding="utf-8") as fh:
        return set(json.load(fh))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brands", nargs="*", help="database brand names to query")
    ap.add_argument("--all-db-brands", action="store_true",
                    help="query every brand, not only the ones missing from 7zap")
    ap.add_argument("--out", default=lib.WIKIDATA_JSONL)
    ap.add_argument("--delay", type=float, default=1.5, help="pause between SPARQL queries")
    ap.add_argument("--no-credits", action="store_true", help="skip the Commons licence lookup")
    ap.add_argument("--list-brands", action="store_true", help="only show what would be queried")
    ap.add_argument("--from-capture", help="import a saved COMPACT_QUERY response instead of querying")
    args = ap.parse_args()

    sevenzap = brands_on_7zap()
    counts = dict(db_brands())
    if args.brands:
        targets = [(b, counts.get(b, 0)) for b in args.brands]
    else:
        targets = [(b, n) for b, n in db_brands()
                   if args.all_db_brands or (lib.brand_to_slug(b) or "") not in sevenzap]

    print(f"{len(targets)} brands to query on Wikidata "
          f"({sum(n for _, n in targets)} database model rows)")
    if args.list_brands:
        for b, n in targets:
            alias = ALIASES.get(b)
            print(f"  {b:<22} {n:>4} rows" + (f"   -> queried as '{alias}'" if alias else ""))
        return

    if args.from_capture:
        with open(args.from_capture, encoding="utf-8") as fh:
            rows = parse_capture(fh.read(), {v: k for k, v in ALIASES.items()})
        total = lib.save_catalog(rows, args.out, merge=True)
        print(f"{len(rows)} models imported from {args.from_capture}; "
              f"catalog holds {total} rows -> {args.out}")
        return

    session = make_session()
    all_rows: list[lib.CatalogModel] = []
    empty: list[str] = []
    for i, (brand, n) in enumerate(targets, 1):
        label = ALIASES.get(brand, brand)
        payload = sparql(session, MODELS_QUERY % {"label": literal(label)})
        rows = parse_models(payload, brand) if payload else []
        if not rows:
            empty.append(brand)
        all_rows.extend(rows)
        print(f"  [{i}/{len(targets)}] {brand:<22} {len(rows):>3} pictures  ({n} db rows)")
        time.sleep(args.delay)

    if not args.no_credits and all_rows:
        print(f"\nfetching licence / author for {len(all_rows)} Commons files ...")
        print(f"  {fetch_credits(session, all_rows)} rows carry attribution")

    total = lib.save_catalog(all_rows, args.out, merge=True)
    print(f"\n{len(all_rows)} Wikidata models written; catalog holds {total} rows -> {args.out}")
    if empty:
        print(f"no picture found for {len(empty)} brands: {', '.join(sorted(empty))}")
    print("\nnext:\n"
          f"  python3 step91_match_7zap_images.py --catalog {args.out}\n"
          "  python3 step92_download_7zap_images.py")


if __name__ == "__main__":
    main()
