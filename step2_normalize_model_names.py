#!/usr/bin/env python3
"""
Step 2 — Normalize model-name casing so vehicle_variants join to models.

Problem (audit F7): 15,241 variant model names are ALL-CAPS (Vivid style,
e.g. 'ASTRA J') while the models catalog uses mixed case ('Astra J').
1,748 variants failed the exact (brand, model) join; 1,606 of those match a
models row case-insensitively. 47 (brand, model) pairs exist only in variants.

What this script does (apply mode):
  1. RENAMES variant (car_brand, car_model) to the canonical casing stored in
     the models catalog — only when a case/accent-insensitive match exists and
     is unambiguous. The models table is the catalog of record; its casing
     stays untouched (cosmetic re-casing of 2,078 ALL-CAPS catalog names is
     deliberately NOT done here — too risky for names like 'CR-V').
  2. ADDS a models row for the 47 pairs that genuinely do not exist in the
     catalog (source='derived_from_vehicle_variants', status='added_missing',
     production years derived from the variant years). Likely typos in these
     (e.g. 'Crow Victoria') are flagged in the report, NOT auto-merged.
  3. RECOMPUTES models.total_variants for every model (1,001 were wrong).
  4. Verifies + exports a change log CSV for full auditability.

Nothing is deleted. Rollback = restore the pre-step2 backup.

Usage:
  python3 step2_normalize_model_names.py --dry-run
  python3 step2_normalize_model_names.py --apply
"""
import argparse
import csv
import os
import shutil
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'database_enriched', 'car_database.db')
BACKUP_DIR = os.path.join(ROOT, 'database_enriched', 'backups')
CSV_CHANGES = os.path.join(ROOT, 'database_enriched', 'csv_exports', '10_model_name_changes.csv')
CSV_ADDED = os.path.join(ROOT, 'database_enriched', 'csv_exports', '11_added_models.csv')


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s or '') if unicodedata.category(c) != 'Mn')


def norm_b(s):
    return strip_accents(s or '').strip().lower()


def norm_m(s):
    return (s or '').strip().lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error('choose --dry-run or --apply')

    con = sqlite3.connect(DB)
    cur = con.cursor()

    # ---------- baseline stats ----------
    def orphan_count():
        return cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
            WHERE NOT EXISTS(SELECT 1 FROM models m
                             WHERE m.brand_name=v.car_brand AND m.model_name=v.car_model)""").fetchone()[0]

    def wrong_totals():
        return cur.execute("""SELECT COUNT(*) FROM (
            SELECT m.id FROM models m LEFT JOIN vehicle_variants v
              ON v.car_brand=m.brand_name AND v.car_model=m.model_name
            GROUP BY m.id HAVING m.total_variants <> COUNT(v.id))""").fetchone()[0]

    dup_sql = """SELECT COUNT(*) FROM (
        SELECT car_brand, car_model, car_year, fuel, engine_power_hp, engine_type,
               engine_code, ecu_maker, ecu_model, COUNT(*) c
        FROM vehicle_variants GROUP BY 1,2,3,4,5,6,7,8,9 HAVING c>1)"""
    before = {'orphans': orphan_count(), 'wrong_totals': wrong_totals(), 'dup_groups': cur.execute(dup_sql).fetchone()[0],
              'zero_models': cur.execute("SELECT COUNT(*) FROM v_model_overview WHERE vehicle_variants_count=0").fetchone()[0]}

    # ---------- build catalog index ----------
    models_rows = cur.execute("SELECT id, brand_name, model_name FROM models").fetchall()
    index = defaultdict(list)
    exact = set()
    for mid, b, m in models_rows:
        exact.add((b, m))
        index[(norm_b(b), norm_m(m))].append((mid, b, m))

    variants = cur.execute("SELECT id, car_brand, car_model FROM vehicle_variants").fetchall()

    renames = []        # (vid, old_b, old_m, new_b, new_m, kind)
    ambiguous = []      # flagged, untouched
    missing = defaultdict(list)   # key -> [(vid, brand, model)]

    for vid, b, m in variants:
        if (b, m) in exact:
            continue
        cands = index.get((norm_b(b), norm_m(m)), [])
        if not cands:
            missing[(norm_b(b), norm_m(m))].append((vid, b, m))
            continue
        if len(cands) == 1:
            _mid, nb, nm = cands[0]
            kind = 'model_case' if b == nb else 'brand_and_model_case'
            if b == nb and strip_accents(b) == strip_accents(nb):
                kind = 'model_case'
            renames.append((vid, b, m, nb, nm, kind))
        else:
            # prefer candidate whose brand string matches the variant exactly
            same_brand = [c for c in cands if c[1] == b]
            if len(same_brand) == 1:
                _mid, nb, nm = same_brand[0]
                renames.append((vid, b, m, nb, nm, 'model_case_ambig_brand'))
            else:
                ambiguous.append((vid, b, m, [f"{c[1]}/{c[2]}" for c in cands]))

    kinds = Counter(r[5] for r in renames)
    print(f"variants evaluated                : {len(variants):,}")
    print(f"orphans before                    : {before['orphans']:,}")
    print(f"  -> rename to catalog casing     : {len(renames):,}  {dict(kinds)}")
    print(f"  -> genuinely missing pairs      : {len(missing)} pairs / {sum(len(v) for v in missing.values()):,} variant rows")
    print(f"  -> ambiguous (flagged, skipped) : {len(ambiguous)}")
    print(f"models with wrong total_variants  : {before['wrong_totals']:,}")
    print(f"duplicate variant groups before   : {before['dup_groups']}")

    print("\n--- sample renames ---")
    for r in renames[:10]:
        print(f"  #{r[0]}: [{r[1]} | {r[2]}]  ->  [{r[3]} | {r[4]}]  ({r[5]})")

    print("\n--- missing pairs to be ADDED as models ---")
    for key, vs in sorted(missing.items(), key=lambda x: -len(x[1]))[:50]:
        print(f"  {vs[0][1]} | {vs[0][2]}  ({len(vs)} variants)")

    if ambiguous:
        print("\n--- ambiguous (will NOT touch) ---")
        for a in ambiguous[:10]:
            print(f"  #{a[0]}: [{a[1]} | {a[2]}] candidates={a[3]}")

    # ---------- what the new model rows would look like ----------
    plan = []
    for key, vs in missing.items():
        casings = Counter((b, m) for _vid, b, m in vs)
        # prefer a casing that is not ALL-CAPS, else most common
        best = sorted(casings.items(), key=lambda x: (-x[1], x[0][1].isupper(), x[0]))
        (nb, nm), _ = best[0]
        years = [y for (y,) in cur.execute(
            "SELECT DISTINCT car_year FROM vehicle_variants WHERE car_brand=? AND car_model=? AND car_year IS NOT NULL", (nb, nm))]
        ps = min(years) if years else None
        pe = max(years) if years else None
        span = f"{ps}" if ps == pe else (f"{ps}-{pe}" if ps else "")
        plan.append((nb, nm, ps, pe, span, len(vs)))

    if args.dry_run:
        print("\nDRY RUN — nothing changed.")
        return

    # ================= APPLY =================
    backup = os.path.join(BACKUP_DIR, f'car_database_backup_pre_step2_{date.today().isoformat()}.db')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(DB, backup)
    print(f"\nBackup written: {backup}")

    # 1) renames
    cur.executemany("UPDATE vehicle_variants SET car_brand=?, car_model=? WHERE id=?",
                    [(r[3], r[4], r[0]) for r in renames])

    # 2) add missing models
    added = 0
    for nb, nm, ps, pe, span, nv in plan:
        bid = cur.execute("SELECT id FROM brands WHERE name=?", (nb,)).fetchone()
        if not bid:
            cur.execute("INSERT INTO brands(name) VALUES (?)", (nb,))
            bid = cur.execute("SELECT id FROM brands WHERE name=?", (nb,)).fetchone()
        try:
            cur.execute("""INSERT INTO models(brand_id, brand_name, model_name, production_start,
                            production_end, years_span, total_variants, source, status)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                        (bid[0], nb, nm, ps, pe, span, 0, 'derived_from_vehicle_variants', 'added_missing'))
            added += 1
        except sqlite3.IntegrityError as e:
            print(f"  SKIP add {nb}/{nm}: {e}")

    # 3) recompute total_variants for ALL models
    cur.execute("""UPDATE models SET total_variants =
                   (SELECT COUNT(*) FROM vehicle_variants v
                    WHERE v.car_brand=models.brand_name AND v.car_model=models.model_name)""")

    con.commit()

    # ---------- verify ----------
    print("\n=== VERIFICATION ===")
    print("integrity_check :", cur.execute("PRAGMA integrity_check").fetchone()[0])
    print(f"orphans after               : {orphan_count():,}  (was {before['orphans']:,})")
    print(f"models wrong totals after   : {wrong_totals():,}  (was {before['wrong_totals']:,})")
    print(f"models added                : {added}")
    print(f"v_model_overview zero-count : {cur.execute('SELECT COUNT(*) FROM v_model_overview WHERE vehicle_variants_count=0').fetchone()[0]:,} (was {before['zero_models']:,})")
    dups_after = cur.execute(dup_sql).fetchone()[0]
    print(f"duplicate variant groups    : {dups_after} (was {before['dup_groups']}) — new ones are case-merge artifacts, flagged for the later dedup step")
    for check in [('Opel', 'ASTRA J'), ('Skoda', 'FABIA'), ('Ford', 'TOURNEO CONNECT'), ('Lexus', 'IS')]:
        n = cur.execute("""SELECT COUNT(*) FROM vehicle_variants v JOIN models m
                           ON m.brand_name=v.car_brand AND m.model_name=v.car_model
                           WHERE v.car_brand=? AND v.car_model=?""", check).fetchone()[0]
        old = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand=? AND car_model=?", check).fetchone()[0]
        print(f"  spot-check {check}: {old} variants, {n} now join models")

    # exports
    os.makedirs(os.path.dirname(CSV_CHANGES), exist_ok=True)
    with open(CSV_CHANGES, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['vehicle_variant_id', 'old_brand', 'old_model', 'new_brand', 'new_model', 'kind'])
        w.writerows(renames)
    with open(CSV_ADDED, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['brand', 'model', 'production_start', 'production_end', 'years_span', 'variants'])
        w.writerows(plan)
    print(f"\nChange log : {CSV_CHANGES}")
    print(f"Added models: {CSV_ADDED}")
    print(f"Rollback: cp '{backup}' '{DB}'")
    con.close()


if __name__ == '__main__':
    main()
