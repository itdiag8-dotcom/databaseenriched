"""Step 40d: clear BMW's 38 pre-existing variant/engine fuel contradictions.

Step 40 introduced `N55B30 (ActiveHybrid)` for the inline-six ActiveHybrids. Auditing BMW
afterwards showed the same contradiction the batch-29 Escape/Mariner rows had, on a larger
scale: BMW's hybrids were filed on the petrol engine rows (or vice versa), giving 38 rows where
`vehicle_variants.fuel` disagrees with `engines.fuel`.

1. **The V8 ActiveHybrids.** Ten variants marked Hybrid sit on petrol N63 rows (`N63B44A` 5,
   `N63B44` 3, `N63` 2): the ActiveHybrid 7 (F01H/F02H, 4.4 V8 + 20hp motor, 455hp combined)
   and the ActiveHybrid X6 (E72, 4.4 V8 + two motors, 480hp combined) [WIKI_AHX6]. They move to
   a new `N63B44 (ActiveHybrid)` row.
2. **`N63B44A` is not a hybrid engine.** 24 of its 31 variants are plain petrol 550i/650i/750i/
   X5-X6 xDrive50i rows at 405-449hp; only the five hybrids (now moved) justified `fuel=Hybrid`.
   The row becomes Petrol, 449hp, 8 cylinders.
3. **i3 REx.** Two i3 variants marked Hybrid sit on the pure-electric drive row `IB1P25B`; the
   range-extender car's combustion engine is the 647cc two-cylinder `W20K06A`, which is already
   in the DB as Hybrid. They move there.
4. **Two diesels marked Petrol** (`N57D30T`: 535d 2015, X5 2015) and **one i8 marked Petrol**
   (`B3815KT0`, a PHEV row) get their variant fuel corrected.

Junk engine_type strings on the touched rows (`N63B44A` "4.4 (est.)", `IB1P25B` "Retrofit
leather multifunction steering wheel", `N57D30T` NULL) are replaced at the same time.
"""
import sqlite3
import sys

DB = "database_enriched/car_database.db"
APPLY = "--apply" in sys.argv

AH_V8 = "N63B44 (ActiveHybrid)"

con = sqlite3.connect(DB)
cur = con.cursor()


def run(sql, params=()):
    if APPLY:
        cur.execute(sql, params)
        return cur.rowcount
    return cur.execute("SELECT COUNT(*) FROM (" + sql.split(" WHERE ", 1)[0]
                       .replace("UPDATE vehicle_variants SET engine_code=?, engine_power_hp=?", "SELECT 1 FROM vehicle_variants")
                       .replace("UPDATE vehicle_variants SET engine_code=?", "SELECT 1 FROM vehicle_variants")
                       .replace("UPDATE vehicle_variants SET fuel=?", "SELECT 1 FROM vehicle_variants")
                       + " WHERE " + sql.split(" WHERE ", 1)[1] + ")", params).fetchone()[0]


# 1. new V8 ActiveHybrid engine row
if APPLY:
    cur.execute("""INSERT OR IGNORE INTO engines
        (engine_code, engine_type, fuel, displacement_cc, power_hp, cylinders,
         brand_example, model_example, year_example, count_variants, data_confidence)
        VALUES (?,?,?,?,?,?,?,?,?,0,?)""",
        (AH_V8, "4.4 V8 TwinTurbo + e-motor (ActiveHybrid 7 455hp / ActiveHybrid X6 480hp combined)",
         "Hybrid", 4395, 455, 8, "BMW", "7 (F01, F02, F03, F04)", 2011, "STEP40_VERIFIED"))
    print("created", AH_V8)

moved = 0
for src in ("N63B44A", "N63B44", "N63"):
    n = run("UPDATE vehicle_variants SET engine_code=? WHERE car_brand='BMW' AND engine_code=? AND fuel='Hybrid'",
            (AH_V8, src))
    print(f"  V8 ActiveHybrid rows moved off {src}: {n}")
    moved += n

n55 = run("UPDATE vehicle_variants SET engine_code=? WHERE car_brand='BMW' AND engine_code='N55B30A' AND fuel='Hybrid'",
          ("N55B30 (ActiveHybrid)",))
print(f"  I6 ActiveHybrid rows moved off N55B30A: {n55}")

rex = run("UPDATE vehicle_variants SET engine_code=? WHERE car_brand='BMW' AND engine_code='IB1P25B' AND fuel='Hybrid'",
          ("W20K06A",))
print(f"  i3 REx rows moved to W20K06A: {rex}")

d1 = run("UPDATE vehicle_variants SET fuel=? WHERE car_brand='BMW' AND engine_code='N57D30T' AND fuel<>'Diesel'",
         ("Diesel",))
d2 = run("UPDATE vehicle_variants SET fuel=? WHERE car_brand='BMW' AND engine_code='B3815KT0' AND fuel<>'Hybrid'",
         ("Hybrid",))
print(f"  variant fuel corrected: N57D30T -> Diesel {d1}, B3815KT0 -> Hybrid {d2}")

ROW_FIXES = {
    "N63B44A": ("4.4 V8 TwinTurbo N63 (550i/650i/750i/X5-X6 xDrive50i, 405-449hp)", "Petrol", 449, 8),
    "N63B44": ("4.4 V8 TwinTurbo N63 (750i/550i 407hp)", "Petrol", 407, 8),
    "IB1P25B": ("i3 eDrive synchronous electric motor (IB1P25B, 102-170hp)", "Electric", 170, None),
    "N57D30T": ("3.0 I6 Diesel N57 (535d/X5 xDrive35d applications)", "Diesel", None, 6),
}
if APPLY:
    for code, (etype, fuel, hp, cyl) in ROW_FIXES.items():
        sets, params = ["engine_type=?", "fuel=?", "data_confidence='STEP40_VERIFIED'"], [etype, fuel]
        if hp is not None:
            sets.append("power_hp=?"); params.append(hp)
        if cyl is not None:
            sets.append("cylinders=?"); params.append(cyl)
        params.append(code)
        cur.execute(f"UPDATE engines SET {', '.join(sets)} WHERE engine_code=?", params)
        print(f"  row-fix {code}: {etype} [{fuel}]")

    cur.execute("""UPDATE engines SET count_variants =
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")
    cur.execute("""DELETE FROM engines WHERE count_variants = 0 AND engine_code LIKE 'LEMON%'""")
    con.commit()

    print("\n--- audit ---")
    print("BMW fuel conflicts:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
        JOIN engines e ON e.engine_code=v.engine_code WHERE v.car_brand='BMW' AND v.fuel<>e.fuel""").fetchone()[0])
    print("DB-wide fuel conflicts:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
        JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel""").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
        LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines e WHERE e.count_variants <>
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)""").fetchone()[0])
    print("engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    print("ActiveHybrid rows:", cur.execute("""SELECT engine_code, count_variants FROM engines
        WHERE engine_code LIKE '%ActiveHybrid%'""").fetchall())
else:
    print("\nDRY RUN - no changes. Re-run with --apply.")
con.close()
