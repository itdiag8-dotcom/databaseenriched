"""Step 30c: post-batch-21 audit repairs.
1. FB25BA / FB25BC are NULL-type junk engine rows whose only links are Subaru Forester 2014-17
   (identical 0W-20/4.82 specs = the FB25B). Consolidate: relink the 8 variants to the relabeled
   'FB25' (FB25B) row with power fill 170hp (2014-18 Forester 2.5i), merge their spec rows,
   delete the two junk rows.
2. Solterra BEV: pure battery-electric - delete the all-NULL oil-spec and tech-spec rows copied
   from the LEMON template (i3 precedent: BEVs have no engine oil spec; coolant-only rows are
   meaningless when every field is NULL). The engines row (Electric, 215hp) stays.
"""
import sqlite3

DB = "database_enriched/car_database.db"
con = sqlite3.connect(DB); cur = con.cursor()

spec_cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_service_specs)")]
tech_cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_technical_specs)")]

for junk in ("FB25BA", "FB25BC"):
    n = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code=?", (junk,)).fetchone()[0]
    # merge specs into FB25 (COALESCE pattern)
    for table, cols in (("engine_service_specs", spec_cols), ("engine_technical_specs", tech_cols)):
        cc = [c for c in cols if c != "engine_code"]
        cur.execute(f"SELECT {','.join(cc)} FROM {table} WHERE engine_code=?", (junk,))
        src = cur.fetchone()
        if src is None: continue
        if cur.execute(f"SELECT 1 FROM {table} WHERE engine_code='FB25'").fetchone():
            sets = ", ".join(f"{c}=COALESCE({c}, ?)" for c in cc)
            cur.execute(f"UPDATE {table} SET {sets} WHERE engine_code='FB25'", (*src,))
        else:
            cur.execute(f"INSERT INTO {table} (engine_code, {','.join(cc)}) VALUES (?{',?'*len(cc)})", ("FB25", *src))
        cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (junk,))
    cur.execute("DELETE FROM engines WHERE engine_code=?", (junk,))
    print(f"  consolidated {junk}: {n} variants relinked to FB25, junk row deleted")

cur.execute("""UPDATE vehicle_variants SET engine_code='FB25', engine_power_hp=170
    WHERE engine_code IN ('FB25BA','FB25BC')""")
print(f"  relinked+filled {cur.rowcount} Forester 2014-17 variants (FB25B 170hp)")

cur.execute("DELETE FROM engine_service_specs WHERE engine_code='Solterra BEV'")
cur.execute("DELETE FROM engine_technical_specs WHERE engine_code='Solterra BEV'")
print("  deleted all-NULL Solterra BEV spec/tech rows (pure BEV, no oil spec)")

cur.execute("""UPDATE engines SET count_variants =
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")

con.commit()

print("\n--- audit ---")
print("NULL powers on Subaru non-LEMON:",
      cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand='Subaru' AND engine_power_hp IS NULL AND engine_code NOT LIKE 'LEMON%'").fetchone()[0])
print("fuel conflicts among Subaru-linked:",
      cur.execute("""SELECT v.engine_code, e.fuel, v.fuel, COUNT(*) FROM vehicle_variants v
        JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IN (SELECT DISTINCT engine_code FROM vehicle_variants WHERE car_brand='Subaru' AND engine_code NOT LIKE 'LEMON%')
        AND v.fuel != e.fuel GROUP BY 1,2,3""").fetchall() or "NONE")
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
print("FB25 row:", cur.execute("SELECT engine_type, power_hp, count_variants FROM engines WHERE engine_code='FB25'").fetchone())
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close()
