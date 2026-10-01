#!/usr/bin/env python3
"""Step 90 - crawl 7zap.com and build the model-picture catalog.

7zap publishes, for every brand, a catalog page that lists each model
generation together with a photo of that generation:

    https://7zap.com/en/catalog/cars/bmw/
      -> BMW 1' E82 (2007 - 2011)
         https://img.7zap.com/images/oem/models/BMW_1-series_E82.webp

This script walks the brand index, downloads each brand catalog page and
writes one JSON line per model generation to

    database_enriched/7zap/catalog_models.jsonl

Usage
-----
    python3 step90_fetch_7zap_catalog.py                 # all brands
    python3 step90_fetch_7zap_catalog.py --brands bmw audi mercedes
    python3 step90_fetch_7zap_catalog.py --db-brands     # only brands present in car_database.db
    python3 step90_fetch_7zap_catalog.py --html-dir ./saved_pages   # offline parse
    python3 step90_fetch_7zap_catalog.py --md-dir ./markdown_pages  # offline parse (markdown)

Needs outbound HTTPS access to 7zap.com (the `--html-dir` / `--md-dir`
modes let you parse pages fetched elsewhere).
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import time

import sevenzap_lib as lib

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

BRAND_LINK_RE = re.compile(r'href="(?:https://7zap\.com)?/en/catalog/cars/([a-z0-9-]+)/[^"]*"[^>]*title="([^"]*)"')


def make_session():
    if requests is None:
        sys.exit("pip install requests  (or use --html-dir / --md-dir)")
    s = requests.Session()
    s.headers.update({"User-Agent": lib.USER_AGENT, "Accept-Language": "en"})
    return s


def get(session, url: str, retries: int = 3, pause: float = 1.0) -> str | None:
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 200:
                return r.text
            if r.status_code == 404:
                return None
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {url}: {exc}")
        time.sleep(pause * (attempt + 1))
    return None


def discover_brands(session) -> dict[str, str]:
    """Return {slug: label} for every car brand linked from the home page."""
    html = get(session, lib.BASE + "/en/") or ""
    brands: dict[str, str] = {}
    for slug, title in BRAND_LINK_RE.findall(html):
        label = title.replace(" OEM Parts Catalog", "").replace(" Parts Catalog", "").strip()
        brands.setdefault(slug, label or slug.title())
    return brands


def db_brand_slugs() -> list[str]:
    con = sqlite3.connect(lib.DB_PATH)
    names = [r[0] for r in con.execute("SELECT DISTINCT brand_name FROM models ORDER BY 1")]
    con.close()
    slugs = []
    for n in names:
        s = lib.brand_to_slug(n)
        if s and s not in slugs:
            slugs.append(s)
    return slugs


def crawl(brands: dict[str, str], delay: float) -> list[lib.CatalogModel]:
    session = make_session()
    rows: list[lib.CatalogModel] = []
    for i, (slug, label) in enumerate(sorted(brands.items()), 1):
        url = lib.CATALOG_URL.format(slug=slug)
        html = get(session, url)
        if not html:
            print(f"[{i}/{len(brands)}] {slug}: no page")
            continue
        found = lib.parse_catalog_html(html, slug, label)
        rows.extend(found)
        print(f"[{i}/{len(brands)}] {slug}: {len(found)} models")
        time.sleep(delay)
    return rows


def parse_dir(path: str, markdown: bool) -> list[lib.CatalogModel]:
    rows: list[lib.CatalogModel] = []
    for fn in sorted(os.listdir(path)):
        full = os.path.join(path, fn)
        if not os.path.isfile(full):
            continue
        slug = re.sub(r"\.(html?|md|txt|tsv)$", "", fn)
        slug = re.sub(r"_chunk\d+$", "", slug)
        text = open(full, encoding="utf-8", errors="ignore").read()
        label = lib.brand_label_for(slug)
        if fn.endswith(".tsv"):
            found = lib.parse_catalog_tsv(text, slug, label)
        elif markdown or fn.endswith(".md"):
            found = lib.parse_catalog_markdown(text, slug, label)
        else:
            found = lib.parse_catalog_html(text, slug, label)
        rows.extend(found)
        print(f"{fn}: {len(found)} models")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brands", nargs="*", help="7zap brand slugs to crawl")
    ap.add_argument("--db-brands", action="store_true", help="crawl the brands used by car_database.db")
    ap.add_argument("--html-dir", help="parse saved HTML pages instead of crawling")
    ap.add_argument("--md-dir", help="parse saved markdown/TSV captures instead of crawling")
    ap.add_argument("--out", default=lib.CATALOG_JSONL)
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between requests")
    ap.add_argument("--no-merge", action="store_true", help="overwrite instead of merging")
    args = ap.parse_args()

    if args.html_dir:
        rows = parse_dir(args.html_dir, markdown=False)
    elif args.md_dir:
        rows = parse_dir(args.md_dir, markdown=True)
    else:
        session = make_session()
        discovered = discover_brands(session)
        if args.brands:
            wanted = {s: discovered.get(s, s.title()) for s in args.brands}
        elif args.db_brands:
            wanted = {s: discovered.get(s, s.title()) for s in db_brand_slugs() if s in discovered}
        else:
            wanted = discovered
        print(f"brands to crawl: {len(wanted)}")
        os.makedirs(lib.DATA_DIR, exist_ok=True)
        with open(lib.BRANDS_JSON, "w", encoding="utf-8") as fh:
            import json

            json.dump(discovered, fh, indent=2, ensure_ascii=False, sort_keys=True)
        rows = crawl(wanted, args.delay)

    total = lib.save_catalog(rows, args.out, merge=not args.no_merge)
    print(f"\n{len(rows)} models parsed, catalog now holds {total} rows -> {args.out}")


if __name__ == "__main__":
    main()
