"""Step 12b (step65b) - the two leftovers step65's verification exposed.

1. **53 engine rows whose `engine_type` is NULL** (not empty - which is why step65's
   `WHERE engine_type IS NOT NULL` filter skipped them). All 53 have a displacement recorded,
   including high-traffic rows: `ESA` 6.4 HEMI (29 variants), `N52`/`N51` 3.0 (27/20), `N63` 4.4
   (15), `ETL`/`ETM` - the Cummins pair unmasked back in step 8. Same rebuild as step65.

2. **1,045 variants carrying a junk descriptor of their own**, on an engine row that is fine.
   step65 only resynced variants that repeated their engine's junk string, so these survived
   ("for vehicles with compressor boost" x46, "LIANA (ER)" x32, "HUAPU" x15). 1,026 of them can
   simply inherit their engine row's descriptor, which already describes the engine correctly.
   The brand-verified badge rule from step65 applies here too, extended with Audi's S-badge, so
   an Audi "S5 quattro" variant becomes "3.0 V6 TFSI (S5 quattro)" rather than losing the trim.

Usage: python3 step65b_descriptor_leftovers.py [--apply]
"""
import csv
import os
import re
import shutil
import sqlite3
import sys

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step65b_2026-10-01.db"
CSV_OUT = "database_enriched/csv_exports/75_descriptor_leftovers_step65b.csv"
APPLY = "--apply" in sys.argv

SIGNAL = re.compile(r"\d\.\d|\d,\d|\d{3,4}\s*(cc)?|\b[VIHWR]\d\b|TDI|TSI|CRD|HDI|dCi|VTEC|HEMI|"
                    r"Electric|Hybrid|EcoBoost|Turbo", re.I)
BADGES = [
    (re.compile(r"^[TD][3-8]$"), ("volvo",)),
    (re.compile(r"^(Cooper|Cooper S|Cooper D|One|One D)$", re.I), ("mini", "bmw")),
    (re.compile(r"\bAMG\b"), ("mercedes", "mercedes-benz")),
    (re.compile(r"^(S|RS)\d( quattro)?$", re.I), ("audi",)),
]


def badge(text, brand):
    b = (brand or "").strip().lower()
    for pat, brands in BADGES:
        if pat.search(text or "") and any(b.startswith(x) for x in brands):
            return text
    return None


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    g = lambda q: con.execute(q).fetchone()[0]
    rows = []

    for e in con.execute("""SELECT engine_code, displacement_cc, fuel, count_variants FROM engines
                            WHERE engine_type IS NULL""").fetchall():
        if not e["displacement_cc"]:
            rows.append(dict(table="engines", ref=e["engine_code"], action="SKIP_NO_DATA",
                             old=None, new=None, note="NULL descriptor and no displacement"))
            continue
        rows.append(dict(table="engines", ref=e["engine_code"], action="FILL_NULL", old=None,
                         new=f"{e['displacement_cc'] / 1000:.1f} L {e['fuel']}",
                         note=f"descriptor was NULL on a row with {e['count_variants']} variants"))

    filled = {r["ref"]: r["new"] for r in rows if r["action"] == "FILL_NULL"}
    for v in con.execute("""SELECT v.id, v.car_brand, v.engine_code, v.engine_type AS vt,
                                   e.engine_type AS et
                            FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code = v.engine_code
                            WHERE v.engine_type IS NOT NULL""").fetchall():
        if SIGNAL.search(v["vt"]):
            continue
        src = v["et"] if (v["et"] and SIGNAL.search(v["et"])) else filled.get(v["engine_code"])
        if not src:
            rows.append(dict(table="vehicle_variants", ref=v["id"], action="SKIP_NO_SOURCE",
                             old=v["vt"], new=None,
                             note="engine row has no usable descriptor either"))
            continue
        keep = badge(v["vt"], v["car_brand"])
        rows.append(dict(table="vehicle_variants", ref=v["id"], action="INHERIT_ENGINE",
                         old=v["vt"], new=src + (f" ({keep})" if keep else ""),
                         note="kept the brand's own badge" if keep else "junk variant descriptor"))

    from collections import Counter
    for k, n in sorted(Counter((r["table"], r["action"]) for r in rows).items()):
        print(f"  {k[0]:17} {k[1]:15} {n}")

    out = CSV_OUT if APPLY else CSV_OUT.replace(".csv", "_DRYRUN.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {out}")

    if not APPLY:
        print("\nDRY RUN - no changes. Re-run with --apply\nsamples:")
        for r in [x for x in rows if x["action"] == "FILL_NULL"][:5]:
            print(f"   engine  {r['ref'][:18]:20} NULL -> '{r['new']}'")
        for r in [x for x in rows if x["action"] == "INHERIT_ENGINE"][:8]:
            print(f"   variant {r['ref']:<8} '{r['old'][:32]}' -> '{r['new'][:42]}'")
        return

    shutil.copy2(DB, BACKUP)
    print(f"\nbackup -> {BACKUP}")
    n = 0
    for r in rows:
        if r["new"] is None:
            continue
        if r["table"] == "engines":
            con.execute("UPDATE engines SET engine_type=? WHERE engine_code=?", (r["new"], r["ref"]))
        else:
            con.execute("UPDATE vehicle_variants SET engine_type=? WHERE id=?", (r["new"], r["ref"]))
        n += 1
    con.commit()
    print(f"  applied {n} updates")

    print("\n--- verify ---")
    bad_e = [r[0] for r in con.execute("SELECT engine_code,engine_type FROM engines WHERE engine_type IS NOT NULL")
             if not SIGNAL.search(r[1])]
    bad_v = [r[0] for r in con.execute("SELECT id,engine_type FROM vehicle_variants WHERE engine_type IS NOT NULL")
             if not SIGNAL.search(r[1])]
    print("engine rows still without engine information:", len(bad_e), bad_e[:6])
    print("variant rows still without engine information:", len(bad_v))
    print("NULL engine descriptors:", g("SELECT count(*) FROM engines WHERE engine_type IS NULL"))
    print("markers remaining:", g("""SELECT count(*) FROM engines WHERE engine_type LIKE '%(est.)%'
        OR engine_type LIKE '%(corr.)%"""[:0] + "SELECT count(*) FROM engines WHERE engine_type LIKE '%(est.)%' OR engine_type LIKE '%(corr.)%'"))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("engines:", g("SELECT count(*) FROM engines"), "| variants:", g("SELECT count(*) FROM vehicle_variants"))
    con.close()


if __name__ == "__main__":
    main()
