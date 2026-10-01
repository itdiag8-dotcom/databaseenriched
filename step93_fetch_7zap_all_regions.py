#!/usr/bin/env python3
"""Step 93 - complete, all-region 7zap catalog crawl.

Why this exists
---------------
`step90_fetch_7zap_catalog.py` reads the brand catalog pages
(https://7zap.com/en/catalog/cars/<brand>/). Those pages are rendered for ONE
region at a time (USA by default) and switch region client-side, so a crawl of
them only ever sees part of the catalog: BMW `1' F20`, Audi `A1`, Opel European
models and so on never appear.

7zap's sitemap index, however, lists one sitemap per model generation for every
brand and every region:

    https://7zap.com/sitemap.xml
      -> https://7zap.com/sitemaps/cats/7zap_com/bmw/generation_1-series-f20.xml
      -> https://7zap.com/sitemaps/cats/7zap_com/audi/generation_a1-typ-8x.xml
         ...

and the generation slug maps directly onto the model page:

    https://7zap.com/en/catalog/cars/bmw/1-series-f20-parts-catalog/

which carries the model picture, the full model name, the production years and
the region label. This script walks that list and builds the complete catalog.

Usage
-----
    python3 step93_fetch_7zap_all_regions.py --list-only          # just count what is out there
    python3 step93_fetch_7zap_all_regions.py --db-brands          # every brand used by car_database.db
    python3 step93_fetch_7zap_all_regions.py --brands bmw audi opel
    python3 step93_fetch_7zap_all_regions.py --workers 6 --delay 0.4
    python3 step93_fetch_7zap_all_regions.py --resume             # skip models already in the catalog

Results are merged into database_enriched/7zap/catalog_models.jsonl, the same
file step91 consumes. Re-run step91 afterwards to re-match the database, then
step92 to download the pictures.

Needs outbound HTTPS access to 7zap.com.
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import os
import queue
import re
import sqlite3
import sys
import threading
import time

import sevenzap_lib as lib

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

SITEMAP_INDEX = lib.BASE + "/sitemap.xml"
GEN_SITEMAP_RE = re.compile(
    r"https://7zap\.com/sitemaps/cats/7zap_com/([a-z0-9\-]+)/generation_([a-z0-9\-\._]+)\.xml",
    re.I,
)
MODEL_IMG_RE = re.compile(r"https://img\.7zap\.com/images/oem/models/[^\"'\s)<>]+", re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
OG_TITLE_RE = re.compile(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', re.I)
OG_IMAGE_RE = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', re.I)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
REGION_RE = re.compile(r"region\.png[^>]*>\s*([A-Za-z][A-Za-z \-]{2,30})", re.I)
TAG_RE = re.compile(r"<[^>]+>")

TITLE_TAIL_RE = re.compile(
    r"\s*(?:OEM\s+)?(?:Spare\s+)?Parts?\s+Catalog(?:ue)?.*$|\s*[—\-|]\s*7zap.*$", re.I
)


# --------------------------------------------------------------------------
def make_session():
    if requests is None:
        sys.exit("pip install requests")
    s = requests.Session()
    s.headers.update({"User-Agent": lib.USER_AGENT, "Accept-Language": "en"})
    return s


def get(session, url: str, retries: int = 3, pause: float = 1.0) -> str | None:
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=40)
            if r.status_code == 200:
                return r.text
            if r.status_code in (404, 410):
                return None
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1:
                print(f"  ! {url}: {exc}")
        time.sleep(pause * (attempt + 1))
    return None


def list_generations(session, brands: set[str] | None) -> list[tuple[str, str]]:
    """[(brand_slug, generation_slug)] for every generation in the sitemap index."""
    xml = get(session, SITEMAP_INDEX)
    if not xml:
        sys.exit("could not read the sitemap index")
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for brand, gen in GEN_SITEMAP_RE.findall(xml):
        brand, gen = brand.lower(), gen.lower()
        if brands and brand not in brands:
            continue
        if (brand, gen) in seen:
            continue
        seen.add((brand, gen))
        pairs.append((brand, gen))
    return pairs


def clean_title(raw: str) -> str:
    txt = html_mod.unescape(TAG_RE.sub(" ", raw or ""))
    txt = re.sub(r"\s+", " ", txt).strip()
    return TITLE_TAIL_RE.sub("", txt).strip(" -—|")


def parse_model_page(html: str, brand_slug: str, gen_slug: str) -> lib.CatalogModel | None:
    """Pull name / years / picture / region out of one 7zap model page."""
    img = None
    m = OG_IMAGE_RE.search(html)
    if m and "/oem/models/" in m.group(1):
        img = m.group(1)
    if not img:
        found = MODEL_IMG_RE.search(html)
        img = found.group(0) if found else None
    if not img:
        return None

    title, raw_title = "", ""
    for rx in (OG_TITLE_RE, H1_RE, TITLE_RE):
        m = rx.search(html)
        if m:
            raw_title = re.sub(r"\s+", " ", html_mod.unescape(TAG_RE.sub(" ", m.group(1)))).strip()
            title = clean_title(m.group(1))
            if title:
                break

    label = lib.brand_label_for(brand_slug)
    name = title
    # strip the leading brand name ("BMW 5' G99 M5 Touring (2024)")
    for prefix in (label, brand_slug.replace("-", " ")):
        if prefix and name.lower().startswith(prefix.lower() + " "):
            name = name[len(prefix) + 1:]
            break
    years_text = ""
    ym = re.search(
        r"\(?\s*((?:19|20)\d{2})"
        r"(?:\s*[-–—]\s*((?:19|20)\d{2}|\.\.\.|…|present|now|current)?)?"
        r"\s*\)?\s*$",
        name, re.I)
    if ym:
        years_text = ym.group(0).strip()
        name = name[: ym.start()].strip(" -–—")
        # the opening paren of "(2011 - 2015)" may now dangle
        if name.count("(") > name.count(")"):
            name = name.rstrip(" (").strip()
    if not name:
        name = gen_slug.replace("-", " ").upper()
    if not years_text and raw_title:
        # "... (Typ 8X) 2010 Parts Catalog" - the years sit in the stripped tail
        ym2 = re.search(
            r"((?:19|20)\d{2})(?:\s*[-–—]\s*((?:19|20)\d{2}))?\s*(?:OEM\s+)?Parts?\s+Catalog",
            raw_title, re.I)
        if ym2:
            years_text = ym2.group(0)[: ym2.group(0).lower().find("parts")].strip()
    y1, y2 = lib.parse_years(years_text)
    if ym and y1 and y2 == y1:
        tail = (ym.group(2) or "").lower()
        dash = bool(re.search(r"[-–—]", ym.group(0)))
        if dash and (not tail or tail in {"...", "…", "present", "now", "current"}):
            y2 = None  # open-ended generation, still in production

    region = None
    rm = REGION_RE.search(html)
    if rm:
        region = re.sub(r"\s+", " ", html_mod.unescape(rm.group(1))).strip()

    return lib.CatalogModel(
        brand_slug=brand_slug,
        brand_label=label,
        model_name=name,
        year_from=y1,
        year_to=y2,
        years_text=years_text,
        page_url=f"{lib.BASE}/en/catalog/cars/{brand_slug}/{gen_slug}-parts-catalog/",
        image_url=img,
        slug=f"{gen_slug}-parts-catalog",
        source="7zap" + (f":{region.lower()}" if region else ""),
    )


# --------------------------------------------------------------------------
def crawl(pairs: list[tuple[str, str]], workers: int, delay: float, out_path: str) -> int:
    work: "queue.Queue[tuple[str, str]]" = queue.Queue()
    for p in pairs:
        work.put(p)
    results: list[lib.CatalogModel] = []
    lock = threading.Lock()
    done = {"n": 0, "ok": 0}

    def worker() -> None:
        session = make_session()
        while True:
            try:
                brand, gen = work.get_nowait()
            except queue.Empty:
                return
            url = f"{lib.BASE}/en/catalog/cars/{brand}/{gen}-parts-catalog/"
            html = get(session, url)
            row = parse_model_page(html, brand, gen) if html else None
            with lock:
                done["n"] += 1
                if row:
                    results.append(row)
                    done["ok"] += 1
                if done["n"] % 50 == 0:
                    print(f"  [{done['n']}/{len(pairs)}] pictures found: {done['ok']}")
                if len(results) >= 250:
                    lib.save_catalog(results, out_path, merge=True)
                    results.clear()
            time.sleep(delay)
            work.task_done()

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(max(1, workers))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if results:
        lib.save_catalog(results, out_path, merge=True)
    return done["ok"]


def db_brand_slugs() -> set[str]:
    con = sqlite3.connect(lib.DB_PATH)
    names = [r[0] for r in con.execute("SELECT DISTINCT brand_name FROM models")]
    con.close()
    return {s for s in (lib.brand_to_slug(n) for n in names) if s}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brands", nargs="*", help="7zap brand slugs to crawl")
    ap.add_argument("--db-brands", action="store_true", help="only brands used by car_database.db")
    ap.add_argument("--out", default=lib.CATALOG_JSONL)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--delay", type=float, default=0.5, help="pause per request inside each worker")
    ap.add_argument("--limit", type=int, help="stop after N generations (smoke test)")
    ap.add_argument("--resume", action="store_true", help="skip generations already in the catalog")
    ap.add_argument("--list-only", action="store_true", help="only list what the sitemap offers")
    args = ap.parse_args()

    session = make_session()
    wanted: set[str] | None = None
    if args.brands:
        wanted = {b.lower() for b in args.brands}
    elif args.db_brands:
        wanted = db_brand_slugs()

    pairs = list_generations(session, wanted)
    by_brand: dict[str, int] = {}
    for b, _ in pairs:
        by_brand[b] = by_brand.get(b, 0) + 1
    print(f"sitemap offers {len(pairs)} model generations across {len(by_brand)} brands")

    if args.list_only:
        os.makedirs(lib.DATA_DIR, exist_ok=True)
        path = os.path.join(lib.DATA_DIR, "generations.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"counts": by_brand, "generations": pairs}, fh, indent=1, sort_keys=True)
        print("->", path)
        for b in sorted(by_brand, key=lambda k: -by_brand[k])[:25]:
            print(f"  {b:<18} {by_brand[b]}")
        return

    if args.resume:
        have = {(c.brand_slug, c.slug) for c in lib.load_catalog(args.out)}
        pairs = [(b, g) for b, g in pairs if (b, f"{g}-parts-catalog") not in have]
        print(f"{len(pairs)} generations still to fetch after --resume")
    if args.limit:
        pairs = pairs[: args.limit]

    found = crawl(pairs, args.workers, args.delay, args.out)
    total = len(lib.load_catalog(args.out))
    print(f"\n{found} model pictures collected; catalog now holds {total} rows -> {args.out}")
    print("next: python3 step91_match_7zap_images.py && python3 step92_download_7zap_images.py")


if __name__ == "__main__":
    main()
