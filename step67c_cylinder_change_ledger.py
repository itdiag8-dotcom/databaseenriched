"""Step 14 ledger - every cylinder/displacement change made by step67 + step67b, in one file.

step67b was run twice (the second run added the `10v` rule), and the second run overwrote its own
decision CSV with only its own 14 rows. Rather than trust the CSVs, this rebuilds the record from
the data itself: the pre-Step-14 backup is diffed against the live database, so the ledger is
complete by construction even if a decision CSV is lost or overwritten.

Evidence is re-attached per row: from `80_cylinder_fixes_step67.csv` where the MagicMotorsport
layout token drove the change, otherwise by re-evaluating the step67b valve-count rules.

Usage: python3 step67c_cylinder_change_ledger.py
"""
import csv
import os
import sqlite3

BEFORE = "database_enriched/backups/car_database_backup_pre_step67_2026-10-01.db"
AFTER = "database_enriched/car_database.db"
SRC80 = "database_enriched/csv_exports/80_cylinder_fixes_step67.csv"
OUT = "database_enriched/csv_exports/82_cylinder_changes_step14_ledger.csv"


def snapshot(path):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    rows = {r[0]: r[1:] for r in con.execute(
        "SELECT engine_code, cylinders, displacement_cc, engine_type, brand_example, count_variants FROM engines")}
    con.close()
    return rows


def main():
    before, after = snapshot(BEFORE), snapshot(AFTER)

    ev80 = {}
    if os.path.exists(SRC80):
        for r in csv.DictReader(open(SRC80)):
            if r.get("action") == "FIX":
                ev80[r["engine_code"]] = r.get("evidence", "")

    ledger = []
    for code, a in after.items():
        b = before.get(code)
        if not b or (b[0], b[1]) == (a[0], a[1]):
            continue
        ledger.append(dict(
            engine_code=code, brand=b[3], descriptor=a[2],
            old_cylinders=b[0], new_cylinders=a[0],
            old_displacement_cc=b[1], new_displacement_cc=a[1],
            variants=a[4],
            step="step67 (MagicMotorsport layout token)" if code in ev80 else "step67b (valve count)",
            evidence=ev80.get(code, "")))

    for r in ledger:
        if r["evidence"]:
            continue
        import importlib.util
        spec = importlib.util.spec_from_file_location("s67b", "step67b_valve_count_cylinders.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        mt = m.VALVE.search(r["descriptor"] or "")
        _, why = m.rule(r["engine_code"], r["new_displacement_cc"], r["brand"],
                        int(mt.group(1)) if mt else 0, r["old_cylinders"])
        r["evidence"] = why or "valve-count rule"

    ledger.sort(key=lambda r: (r["step"], -r["variants"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ledger[0].keys()))
        w.writeheader(); w.writerows(ledger)

    import collections
    print(f"engine rows changed by Step 14 in total: {len(ledger)}  "
          f"(variants riding on them: {sum(r['variants'] for r in ledger)})")
    for k, v in collections.Counter(r["step"] for r in ledger).most_common():
        print(f"   {k:45} {v}")
    print(f"   displacement_cc also repaired on: "
          f"{sum(1 for r in ledger if r['old_displacement_cc'] != r['new_displacement_cc'])}")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
