"""Step 9 (step62) - fill the empty engine_power_kw / power_kw cells, and audit the ones already
filled.

Noted as an aside in Step 7: 12,869 variants carry a horsepower figure but no kilowatt figure,
and 446 engine rows have the same gap. Power in kW is not a judgement call - it is the same
number in different units - so this is pure arithmetic. The only question was which conversion
the database itself uses, and the populated rows answer it: the ratio kW/hp clusters hard on
0.735-0.736 across 26,268 variants and 5,210 engine rows, i.e. metric horsepower
(1 PS = 0.7355 kW). That is the factor used here.

Existing values are NOT overwritten - the step only fills NULLs - but rows whose stored kW
disagrees with their hp by more than 3% are reported, since a handful are clearly wrong
(the observed spread runs from 0.248 to 1.570).

Usage: python3 step62_step9_kw_backfill.py [--apply]
"""
import csv
import os
import shutil
import sqlite3
import sys

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step62_2026-10-01.db"
CSV_OUT = "database_enriched/csv_exports/70_kw_outliers_step62.csv"
PS_TO_KW = 0.7355
TOL = 0.03
APPLY = "--apply" in sys.argv


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    g = lambda q: con.execute(q).fetchone()[0]

    v_gap = g("SELECT count(*) FROM vehicle_variants WHERE engine_power_hp IS NOT NULL AND engine_power_kw IS NULL")
    e_gap = g("SELECT count(*) FROM engines WHERE power_hp IS NOT NULL AND power_kw IS NULL")
    print(f"variants missing kW: {v_gap} | engine rows missing kW: {e_gap}")

    outliers = con.execute("""
        SELECT 'variant' AS kind, id AS ref, car_brand || ' ' || coalesce(car_model,'') AS what,
               engine_code, engine_power_hp AS hp, engine_power_kw AS kw
        FROM vehicle_variants
        WHERE engine_power_kw IS NOT NULL AND engine_power_hp > 0
          AND abs(engine_power_kw / (engine_power_hp * ?) - 1) > ?
        UNION ALL
        SELECT 'engine', rowid, coalesce(brand_example,'') || ' ' || coalesce(model_example,''),
               engine_code, power_hp, power_kw
        FROM engines
        WHERE power_kw IS NOT NULL AND power_hp > 0
          AND abs(power_kw / (power_hp * ?) - 1) > ?
        """, (PS_TO_KW, TOL, PS_TO_KW, TOL)).fetchall()
    print(f"rows whose stored kW disagrees with hp by >{TOL:.0%}: {len(outliers)}")

    out = CSV_OUT if APPLY else CSV_OUT.replace(".csv", "_DRYRUN.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "ref", "what", "engine_code", "hp", "stored_kw", "expected_kw"])
        for r in outliers:
            w.writerow([r["kind"], r["ref"], r["what"].strip(), r["engine_code"], r["hp"],
                        r["kw"], round(r["hp"] * PS_TO_KW, 1)])
    print(f"  wrote {out}")
    for r in outliers[:12]:
        print(f"   {r['kind']:8} {r['engine_code'][:22]:24} {r['hp']}hp stored {r['kw']}kW "
              f"(expected {round(r['hp'] * PS_TO_KW, 1)})")

    if not APPLY:
        print("\nDRY RUN - no changes. Re-run with --apply")
        return

    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    shutil.copy2(DB, BACKUP)
    print(f"\nbackup -> {BACKUP}")
    nv = con.execute("""UPDATE vehicle_variants SET engine_power_kw = round(engine_power_hp * ?, 1)
                        WHERE engine_power_hp IS NOT NULL AND engine_power_kw IS NULL""", (PS_TO_KW,)).rowcount
    ne = con.execute("""UPDATE engines SET power_kw = round(power_hp * ?, 1)
                        WHERE power_hp IS NOT NULL AND power_kw IS NULL""", (PS_TO_KW,)).rowcount
    con.commit()
    print(f"  filled kW on {nv} variants and {ne} engine rows")

    print("\n--- verify ---")
    print("variants still missing kW:", g("SELECT count(*) FROM vehicle_variants WHERE engine_power_hp IS NOT NULL AND engine_power_kw IS NULL"))
    print("engine rows still missing kW:", g("SELECT count(*) FROM engines WHERE power_hp IS NOT NULL AND power_kw IS NULL"))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("variants:", g("SELECT count(*) FROM vehicle_variants"), "| engines:", g("SELECT count(*) FROM engines"))
    con.close()


if __name__ == "__main__":
    main()
