#!/usr/bin/env python3
"""Step 91 - attach a 7zap picture to every row of `models`.

Reads the catalog produced by step90 (database_enriched/7zap/catalog_models.jsonl)
and matches each `models` row to the best 7zap model generation, then stores the
picture on the row.

Columns added to `models` (created on first run):
    image_url          https://img.7zap.com/images/oem/models/BMW_1-series_E82.webp
    image_local_path   database_enriched/model_images/bmw/BMW_1-series_E82.webp (filled by step92)
    image_source_page  the 7zap catalog page the picture came from
    image_match_name   the 7zap model the picture belongs to ("1' E82 (2007 - 2011)")
    image_match_score  0..1 confidence of the match
    image_match_method exact | code | family | fuzzy

Matching modes
--------------
    --mode family  (default) best-guess: engine/trim rows such as BMW '116I'
                   inherit the picture of their model family generation
    --mode strict  only exact / chassis-code matches are written
    --mode gen     only rows that themselves name a generation or chassis code

Usage
-----
    python3 step91_match_7zap_images.py --dry-run
    python3 step91_match_7zap_images.py
    python3 step91_match_7zap_images.py --brands BMW Audi
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import shutil
import sqlite3
from collections import defaultdict
from difflib import SequenceMatcher

import sevenzap_lib as lib

NEW_COLUMNS = {
    "image_url": "TEXT",
    "image_local_path": "TEXT",
    "image_source_page": "TEXT",
    "image_match_name": "TEXT",
    "image_match_score": "REAL",
    "image_match_method": "TEXT",
}

REPORT_CSV = os.path.join(lib.REPO_ROOT, "database_enriched", "csv_exports", "90_7zap_model_images.csv")
UNMATCHED_CSV = os.path.join(lib.REPO_ROOT, "database_enriched", "csv_exports", "90_7zap_unmatched_models.csv")


# --------------------------------------------------------------------------
def backup_db(db_path: str) -> str:
    bdir = os.path.join(os.path.dirname(db_path), "backups")
    os.makedirs(bdir, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(bdir, f"car_database_before_step91_{stamp}.db")
    shutil.copy2(db_path, dest)
    return dest


def ensure_columns(con: sqlite3.Connection) -> None:
    have = {r[1] for r in con.execute("PRAGMA table_info(models)")}
    for col, typ in NEW_COLUMNS.items():
        if col not in have:
            con.execute(f"ALTER TABLE models ADD COLUMN {col} {typ}")


# --------------------------------------------------------------------------
def score_pair(brand: str, db_name: str, db_years: tuple[int | None, int | None],
               cand: lib.CatalogModel) -> tuple[float, str]:
    """Return (score, method) for a candidate 7zap model."""
    n_db = lib.normalize_name(db_name)
    n_c = lib.normalize_name(cand.model_name)
    if not n_db or not n_c:
        return 0.0, "none"

    # the 7zap name often starts with the brand ("MERCEDES C-CLASS"): drop it
    b_norm = lib.normalize_name(brand)
    if b_norm and n_c.startswith(b_norm + " "):
        n_c = n_c[len(b_norm) + 1:]

    t_db, t_c = lib.core_tokens(n_db), lib.core_tokens(n_c)
    s_db, s_c = " ".join(t_db), " ".join(t_c)

    sim = max(
        SequenceMatcher(None, n_db, n_c).ratio(),
        SequenceMatcher(None, s_db, s_c).ratio() if s_db and s_c else 0.0,
    )

    codes_db, codes_c = lib.chassis_codes(db_name), lib.chassis_codes(cand.model_name)
    code_hit = bool(codes_db & codes_c)

    fam_db = lib.family_key(brand, db_name)
    fam_c = lib.family_key(brand, cand.model_name)
    fam_hit = bool(fam_db and fam_c and fam_db == fam_c)
    fam_alt_hit = (not fam_hit) and bool(fam_c) and lib.alt_family(brand, fam_db) == fam_c

    contained = bool(t_db) and set(t_db).issubset(set(t_c))
    contains = bool(t_c) and set(t_c).issubset(set(t_db))

    score = 0.60 * sim
    method = "fuzzy"
    if n_db == n_c:
        score, method = 1.0, "exact"
    else:
        if code_hit:
            score += 0.28
            method = "code"
        if contained or contains:
            score += 0.18
            if method == "fuzzy":
                method = "family"
        if fam_hit:
            score = max(score + 0.14, 0.60)   # same family: always a usable picture
            if method == "fuzzy":
                method = "family"
        elif fam_alt_hit:
            score = max(score + 0.10, 0.50)
            if method == "fuzzy":
                method = "family"

    # a plain 316d should not inherit the M3 photo when both are "3 SERIES"
    extra = lib.variant_mismatch(db_name, cand.model_name)
    if extra and method != "exact":
        score -= min(0.12, 0.05 * extra)

    # year agreement picks the right generation inside a family
    y1, y2 = db_years
    c1, c2 = cand.year_from, cand.year_to
    if y1 and c1:
        a1, a2 = y1, (y2 or y1)
        b1, b2 = c1, (c2 or c1)
        overlap = min(a2, b2) - max(a1, b1)
        if overlap >= 0:
            score += min(0.18, 0.04 + 0.02 * overlap)
        else:
            score -= min(0.25, 0.02 * abs(overlap))
    elif c1:
        # no years on our side: mildly prefer the newest generation
        score += min(0.05, max(0.0, (c1 - 1980) / 1000))

    return max(0.0, min(1.0, score)), method


def best_match(brand: str, model_name: str, years_span: str,
               candidates: list[lib.CatalogModel]) -> tuple[lib.CatalogModel | None, float, str]:
    db_years = lib.parse_span(years_span)
    best, best_score, best_method = None, 0.0, "none"
    for cand in candidates:
        sc, method = score_pair(brand, model_name, db_years, cand)
        if sc > best_score:
            best, best_score, best_method = cand, sc, method
    return best, best_score, best_method


def row_names_generation(model_name: str) -> bool:
    return bool(lib.chassis_codes(model_name))


# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=lib.DB_PATH)
    ap.add_argument("--catalog", default=lib.CATALOG_JSONL)
    ap.add_argument("--mode", choices=["family", "strict", "gen"], default="family")
    ap.add_argument("--threshold", type=float, default=None, help="override accept threshold")
    ap.add_argument("--brands", nargs="*", help="limit to these database brand names")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    thresholds = {"family": 0.45, "strict": 0.80, "gen": 0.55}
    threshold = args.threshold if args.threshold is not None else thresholds[args.mode]

    catalog = lib.load_catalog(args.catalog)
    if not catalog:
        raise SystemExit(f"empty catalog: {args.catalog} - run step90 first")
    by_brand: dict[str, list[lib.CatalogModel]] = defaultdict(list)
    for c in catalog:
        by_brand[c.brand_slug].append(c)
    print(f"catalog: {len(catalog)} 7zap models across {len(by_brand)} brands")

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    if not args.dry_run:
        print("backup ->", backup_db(args.db))
        ensure_columns(con)

    sql = "SELECT id, brand_name, model_name, years_span FROM models"
    params: list = []
    if args.brands:
        sql += " WHERE brand_name IN (%s)" % ",".join("?" * len(args.brands))
        params = args.brands
    sql += " ORDER BY brand_name, model_name"
    rows = con.execute(sql, params).fetchall()

    updates, unmatched = [], []
    stats = defaultdict(int)
    for r in rows:
        slug = lib.brand_to_slug(r["brand_name"])
        cands = by_brand.get(slug or "", [])
        if not cands:
            stats["brand_not_in_catalog"] += 1
            unmatched.append((r["id"], r["brand_name"], r["model_name"], r["years_span"], "brand_not_crawled", 0.0))
            continue
        if args.mode == "gen" and not row_names_generation(r["model_name"]):
            stats["skipped_not_generation"] += 1
            continue
        cand, score, method = best_match(r["brand_name"], r["model_name"], r["years_span"] or "", cands)
        if args.mode == "strict" and method not in {"exact", "code"}:
            score = 0.0
        if cand and score >= threshold:
            label = cand.model_name + (f" ({cand.years_text.strip('()')})" if cand.years_text else "")
            updates.append((cand.image_url, cand.page_url, label, round(score, 3), method, r["id"]))
            stats[method] += 1
        else:
            stats["no_match"] += 1
            unmatched.append((r["id"], r["brand_name"], r["model_name"], r["years_span"],
                              cand.model_name if cand else "", round(score, 3)))

    print(f"\nrows considered : {len(rows)}")
    for k in sorted(stats):
        print(f"  {k:<24} {stats[k]}")
    print(f"  matched total            {len(updates)}  ({len(updates)/max(1,len(rows)):.1%})")

    if not args.dry_run:
        con.executemany(
            "UPDATE models SET image_url=?, image_source_page=?, image_match_name=?, "
            "image_match_score=?, image_match_method=? WHERE id=?",
            updates,
        )
        con.commit()

        os.makedirs(os.path.dirname(REPORT_CSV), exist_ok=True)
        with open(REPORT_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["model_id", "brand_name", "model_name", "years_span", "image_url",
                        "image_source_page", "image_match_name", "image_match_score", "image_match_method"])
            q = ("SELECT id, brand_name, model_name, years_span, image_url, image_source_page, "
                 "image_match_name, image_match_score, image_match_method FROM models "
                 "WHERE image_url IS NOT NULL ORDER BY brand_name, model_name")
            w.writerows(con.execute(q))
        with open(UNMATCHED_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["model_id", "brand_name", "model_name", "years_span", "closest_7zap_model", "score"])
            w.writerows(unmatched)
        print(f"\nreports -> {REPORT_CSV}\n           {UNMATCHED_CSV}")
    con.close()


if __name__ == "__main__":
    main()
