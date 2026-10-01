"""Step 10 (step63) - remove the exactly-duplicated vehicle_variants rows and resync every
derived counter.

1,739 variant rows are byte-identical to another row in every column except `id` - 1,332 groups,
4.4% of the table. (The count was 1,738 before Step 9: completing the kW column made one more
pair identical, since the two rows had differed only in that one being blank.) The worst case is eleven identical "Toyota Prius 2015 / 2ZR-FXE / 99hp"
rows. Nothing in the schema distinguishes them: there is no trim, no VIN, no body-style column,
so as data they are indistinguishable copies, and any query that counts vehicles counts them
multiple times.

Keeper = lowest `id` in each group. Before the losers are deleted, the `remapping_queue` rows
that point at a doomed variant are repointed at its keeper, so no reference is orphaned.

Three derived counters are then recomputed from scratch, because dedup invalidates them:
  - `engines.count_variants`
  - `models.total_variants`      (18 rows had already drifted before this step)
  - `engine_service_specs.count_variants`  (a stale snapshot: 3,846 rows disagreed with
     engines.count_variants, 3,605 of them low - it has not been maintained since the campaign)

Usage: python3 step63_step10_dedup_variants.py [--apply]
"""
import csv
import os
import shutil
import sqlite3
import sys

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step63_2026-10-01.db"
CSV_OUT = "database_enriched/csv_exports/71_duplicate_variants_step63.csv"
APPLY = "--apply" in sys.argv


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    g = lambda q, *a: con.execute(q, a).fetchone()[0]

    cols = [c[1] for c in con.execute("PRAGMA table_info(vehicle_variants)") if c[1] != "id"]
    key = ", ".join(f"coalesce({c}, '~')" for c in cols)

    groups = con.execute(f"""
        SELECT min(id) AS keeper, count(*) AS n, group_concat(id) AS ids,
               car_brand, car_model, car_year, engine_code, fuel, engine_power_hp
        FROM vehicle_variants GROUP BY {key} HAVING count(*) > 1
        ORDER BY n DESC, car_brand, car_model""").fetchall()
    losers, rows = [], []
    for gr in groups:
        ids = sorted(int(i) for i in gr["ids"].split(","))
        for bad in ids[1:]:
            losers.append(bad)
            rows.append(dict(deleted_id=bad, kept_id=gr["keeper"], group_size=gr["n"],
                             brand=gr["car_brand"], model=gr["car_model"], year=gr["car_year"],
                             engine_code=gr["engine_code"], fuel=gr["fuel"], hp=gr["engine_power_hp"]))
    print(f"duplicate groups: {len(groups)} | rows to delete: {len(losers)}")
    assert len(groups) == 1332 and len(losers) == 1739, "baseline changed - re-check before applying"

    marks = ",".join("?" * len(losers))
    rq = g(f"SELECT count(*) FROM remapping_queue WHERE vehicle_variant_id IN ({marks})", *losers)
    print(f"remapping_queue rows to repoint: {rq}")
    print(f"variants {g('SELECT count(*) FROM vehicle_variants')} -> "
          f"{g('SELECT count(*) FROM vehicle_variants') - len(losers)}")

    out = CSV_OUT if APPLY else CSV_OUT.replace(".csv", "_DRYRUN.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {out}")
    print("\nlargest groups:")
    for gr in groups[:8]:
        print(f"   x{gr['n']:<3} {gr['car_brand']} {gr['car_model']} {gr['car_year']} "
              f"{gr['engine_code']} {gr['engine_power_hp']}hp")

    if not APPLY:
        print("\nDRY RUN - no changes. Re-run with --apply")
        return

    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    shutil.copy2(DB, BACKUP)
    print(f"\nbackup -> {BACKUP}")

    # 1. repoint remapping_queue at the surviving row.
    #    vehicle_variant_id is both NOT NULL and UNIQUE, so a loser whose keeper ALREADY holds a
    #    queue row can neither be repointed nor cleared. There is exactly one such case: variants
    #    31097/31098, a Chevy 2007 pair whose queue rows flag different wrong codes (LLY and LMM)
    #    because they were queued before the two variants converged. That distinct payload is
    #    worth more than the duplicate row is worth removing, so the variant is EXEMPTED from
    #    deletion and the pair stays. A row carrying unique downstream state is not a duplicate.
    taken = {r[0] for r in con.execute(
        "SELECT vehicle_variant_id FROM remapping_queue WHERE vehicle_variant_id IS NOT NULL")}
    n_rq = 0
    exempt = []
    for r in rows:
        if r["deleted_id"] not in taken:
            continue
        if r["kept_id"] in taken:
            exempt.append(r["deleted_id"])
            continue
        n_rq += con.execute("UPDATE remapping_queue SET vehicle_variant_id=? WHERE vehicle_variant_id=?",
                            (r["kept_id"], r["deleted_id"])).rowcount
        taken.add(r["kept_id"])
    losers = [i for i in losers if i not in exempt]
    marks = ",".join("?" * len(losers))
    print(f"  repointed {n_rq} remapping_queue references; exempted {len(exempt)} variant(s) "
          f"that hold their own queue row: {exempt}")

    # 2. delete the duplicates
    n_del = con.execute(f"DELETE FROM vehicle_variants WHERE id IN ({marks})", losers).rowcount
    print(f"  deleted {n_del} duplicate variant rows")

    # 3. recompute every derived counter
    n_e = con.execute("""UPDATE engines SET count_variants =
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""").rowcount
    n_m = con.execute("""UPDATE models SET total_variants =
        (SELECT count(*) FROM vehicle_variants v WHERE v.car_brand = models.brand_name
            AND v.car_model = models.model_name)""").rowcount
    n_s = con.execute("""UPDATE engine_service_specs SET count_variants =
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code = engine_service_specs.engine_code)""").rowcount
    con.commit()
    print(f"  recomputed counters: engines {n_e}, models {n_m}, engine_service_specs {n_s}")

    print("\n--- verify ---")
    print("remaining exact duplicates:",
          g(f"SELECT count(*) FROM (SELECT 1 FROM vehicle_variants GROUP BY {key} HAVING count(*)>1)"),
          "(expected 1: the exempted Chevy pair)")
    print("orphaned remapping_queue refs:", g("""SELECT count(*) FROM remapping_queue r
        LEFT JOIN vehicle_variants v ON v.id=r.vehicle_variant_id
        WHERE r.vehicle_variant_id IS NOT NULL AND v.id IS NULL"""))
    print("engines count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("models total mismatches:", g("""SELECT count(*) FROM models m WHERE m.total_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.car_brand=m.brand_name AND v.car_model=m.model_name)"""))
    print("service-spec count mismatches:", g("""SELECT count(*) FROM engine_service_specs s
        JOIN engines e ON e.engine_code=s.engine_code WHERE coalesce(s.count_variants,-1)<>coalesce(e.count_variants,-1)"""))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("orphan engine refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("NULL-power variants:", g("SELECT count(*) FROM vehicle_variants WHERE engine_power_hp IS NULL"))
    print("variants:", g("SELECT count(*) FROM vehicle_variants"), "| engines:", g("SELECT count(*) FROM engines"),
          "| engines now at 0 variants:", g("SELECT count(*) FROM engines WHERE count_variants=0"))
    con.close()


if __name__ == "__main__":
    main()
