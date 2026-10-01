#!/usr/bin/env python3
"""Step 92 - download the 7zap model pictures referenced by `models.image_url`.

Files land in  database_enriched/model_images/<brand-slug>/<original-name>.webp
and the relative path is written back to `models.image_local_path`.

Each distinct picture is downloaded once, even when several model rows share it
(e.g. every BMW 116I/118I/120I row points at the 1' F20 photo).

Usage
-----
    python3 step92_download_7zap_images.py                 # everything still missing
    python3 step92_download_7zap_images.py --brands BMW
    python3 step92_download_7zap_images.py --limit 50
    python3 step92_download_7zap_images.py --jpeg          # also write a .jpg next to the .webp

Needs outbound HTTPS access to img.7zap.com.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from urllib.parse import urlparse

import sevenzap_lib as lib

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


def local_path_for(url: str, brand_slug: str) -> str:
    """Filesystem-safe destination; Commons names carry spaces and commas."""
    import re
    from urllib.parse import unquote

    name = unquote(os.path.basename(urlparse(url).path)) or "image.webp"
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:120]
    return os.path.join("database_enriched", "model_images", brand_slug, name)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=lib.DB_PATH)
    ap.add_argument("--brands", nargs="*")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    ap.add_argument("--jpeg", action="store_true", help="also save a JPEG copy (needs Pillow)")
    args = ap.parse_args()

    if requests is None:
        sys.exit("pip install requests")

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    sql = "SELECT id, brand_name, image_url FROM models WHERE image_url IS NOT NULL AND image_url<>''"
    params: list = []
    if args.brands:
        sql += " AND brand_name IN (%s)" % ",".join("?" * len(args.brands))
        params = args.brands
    rows = con.execute(sql, params).fetchall()

    # distinct url -> (brand slug, rows)
    wanted: dict[str, tuple[str, list[int]]] = {}
    for r in rows:
        slug = lib.brand_to_slug(r["brand_name"]) or "misc"
        entry = wanted.setdefault(r["image_url"], (slug, []))
        entry[1].append(r["id"])

    urls = list(wanted.items())
    if args.limit:
        urls = urls[: args.limit]
    print(f"{len(rows)} model rows -> {len(wanted)} distinct pictures "
          f"({len(urls)} to process)")

    session = requests.Session()
    session.headers.update({"User-Agent": lib.USER_AGENT})

    def headers_for(url: str) -> dict:
        if "7zap.com" in url:
            return {"Referer": lib.BASE + "/en/"}
        if "wikimedia.org" in url or "wikipedia.org" in url:
            # Wikimedia requires a descriptive, contactable User-Agent
            return {"User-Agent": "car-database-enrichment/1.0 (model picture backfill)"}
        return {}

    ok = skipped = failed = 0
    updates: list[tuple[str, int]] = []
    for i, (url, (slug, ids)) in enumerate(urls, 1):
        rel = local_path_for(url, slug)
        dest = os.path.join(lib.REPO_ROOT, rel)
        if os.path.exists(dest) and not args.force:
            skipped += 1
        else:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                resp = session.get(url, timeout=60, headers=headers_for(url))
                if resp.status_code != 200 or not resp.content:
                    raise RuntimeError(f"HTTP {resp.status_code}")
                with open(dest, "wb") as fh:
                    fh.write(resp.content)
                ok += 1
                if args.jpeg:
                    try:
                        from PIL import Image

                        img = Image.open(dest).convert("RGB")
                        img.save(os.path.splitext(dest)[0] + ".jpg", quality=88)
                    except Exception as exc:  # noqa: BLE001
                        print(f"  ! jpeg conversion failed for {rel}: {exc}")
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"  ! {url}: {exc}")
                time.sleep(args.delay)
                continue
            time.sleep(args.delay)
        updates.extend((rel, mid) for mid in ids)
        if i % 50 == 0:
            print(f"  [{i}/{len(urls)}] downloaded={ok} cached={skipped} failed={failed}")

    con.executemany("UPDATE models SET image_local_path=? WHERE id=?", updates)
    con.commit()
    print(f"\ndownloaded={ok} cached={skipped} failed={failed}; "
          f"{len(updates)} model rows now point at a local file")
    con.close()


if __name__ == "__main__":
    main()
