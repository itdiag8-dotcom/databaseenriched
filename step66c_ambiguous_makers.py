"""Step 13c (step66c) - recover the ECU *maker* where the ECU *model* is genuinely ambiguous.

Step 13 left 7,184 variants untouched because their engine code maps to more than one ECU in the
source. I had assumed the API's year columns (absent from the CSV export) would separate them.
**They do not.** Fetched directly from the API, the three Chrysler 300 `EZH` rows are
ids 4058/4059/4060, all `produced_from_year=2011`, `produced_to_year=2023`, identical in model,
power and fuel - differing only in ECU: `GPEC2` vs `GPEC2A`. Same story for the `ERB` 304 ps pair
at ids 4056/4057.

The ambiguity is therefore real rather than missing metadata: a single vehicle shipped with more
than one ECU hardware revision, and a tuning-tool list documents every one the tool can talk to.
No amount of extra source data will collapse those rows into one answer.

But in 5,091 of the 7,184 cases **every candidate shares the same maker** - Delco `E37`/`E38`,
Bosch `MED17.5`/`MED17.1`, Continental `GPEC2`/`GPEC2A`. We cannot say which revision a given car
got, yet we can say with certainty who built it. This script writes `ecu_maker` for those rows
and deliberately leaves `ecu_model` NULL: a half-known fact recorded honestly beats either a
guess or a blank.

The candidate models are exported to the CSV so the choice stays auditable.

Usage: python3 step66c_ambiguous_makers.py --source <file.csv> [--apply]
"""
import argparse
import csv
import importlib.util
import os
import shutil
import sqlite3
from collections import Counter, defaultdict

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step66c_2026-10-01.db"
CSV_OUT = "database_enriched/csv_exports/79_ambiguous_makers_step66c.csv"
CONFLICTS = "database_enriched/csv_exports/77_ecu_conflicts_step66.csv"

spec = importlib.util.spec_from_file_location("s66", "step66_magicmotorsport_import.py")
s66 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s66)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = s66.load_source(args.source)
    by_code = defaultdict(list)
    for r in rows:
        if (r.get("type_of_ecu") or "").upper() != "ECM":
            continue
        c = s66.norm_code(r.get("engine_code"))
        maker, ecu = s66.norm_maker(r.get("ecu_maker")), (r.get("ecu_name") or "").strip()
        if c and maker and ecu:
            by_code[c].append((maker, ecu))

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    ambiguous = [r for r in csv.DictReader(open(CONFLICTS)) if r["issue"].startswith("ambiguous")]

    decisions, stats = [], Counter()
    for r in ambiguous:
        cands = by_code.get(s66.norm_code(r["engine_code"]))
        if not cands:
            stats["code_not_in_source"] += 1
            continue
        makers = {m for m, _ in cands}
        if len(makers) > 1:
            stats["makers_disagree_too"] += 1
            continue
        maker = next(iter(makers))
        v = con.execute("SELECT ecu_maker, ecu_model FROM vehicle_variants WHERE id=?",
                        (r["id"],)).fetchone()
        if v is None:
            stats["variant_missing"] += 1
            continue
        if v["ecu_maker"] == maker:
            stats["maker_already_right"] += 1
            continue
        if v["ecu_maker"] not in (None, "Unknown"):
            stats["maker_differs_kept_ours"] += 1
            continue
        stats["maker_filled"] += 1
        decisions.append(dict(id=r["id"], brand=r["brand"], model=r["model"],
                              engine_code=r["engine_code"], new_maker=maker,
                              ecu_model="(left NULL - genuinely ambiguous)",
                              candidates=" | ".join(sorted({e for _, e in cands}))))

    print("outcomes:")
    for k, v in sorted(stats.items()):
        print(f"   {k:28} {v}")

    os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
    out = CSV_OUT if args.apply else CSV_OUT.replace(".csv", "_DRYRUN.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(decisions[0].keys()))
        w.writeheader(); w.writerows(decisions)
    print(f"  wrote {out} ({len(decisions)} rows)")

    if not args.apply:
        print("\nDRY RUN - no changes. Re-run with --apply\nsamples:")
        for d in decisions[:10]:
            print(f"   variant {d['id']:<7} {str(d['brand'])[:12]:13} {str(d['engine_code'])[:10]:11} "
                  f"maker={d['new_maker']:16} candidates: {d['candidates'][:46]}")
        return

    shutil.copy2(DB, BACKUP)
    print(f"\nbackup -> {BACKUP}")
    for d in decisions:
        con.execute("UPDATE vehicle_variants SET ecu_maker=? WHERE id=?", (d["new_maker"], d["id"]))
    con.commit()
    print(f"  applied {len(decisions)} maker fills (ecu_model deliberately left NULL)")

    g = lambda q: con.execute(q).fetchone()[0]
    print("\n--- verify ---")
    print("variants with a known ECU maker:", g("SELECT count(*) FROM vehicle_variants WHERE ecu_maker IS NOT NULL AND ecu_maker<>'Unknown'"))
    print("variants with a known ECU model:", g("SELECT count(*) FROM vehicle_variants WHERE ecu_model IS NOT NULL"))
    print("maker known but model unknown  :", g("SELECT count(*) FROM vehicle_variants WHERE ecu_maker IS NOT NULL AND ecu_maker<>'Unknown' AND ecu_model IS NULL"))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    con.close()


if __name__ == "__main__":
    main()
