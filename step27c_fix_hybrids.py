"""Step 27c: relink 3 pre-existing Euro-catalog Infiniti hybrids (M Y51 2010, M35 2009,
Q70 Y51 2012 — fuel=Hybrid) from the plain VQ35HR petrol row to the new
'VQ35HR Hybrid (Direct Response)' row (same 3.5 + HM34 360hp powertrain, created in step27).
Found by the post-batch fuel-conflict audit; conflicts pre-dated this batch (pre_step27 backup)."""
import sqlite3

DB = "database_enriched/car_database.db"
con = sqlite3.connect(DB); cur = con.cursor()
HYB = "VQ35HR Hybrid (Direct Response)"
n = cur.execute("UPDATE vehicle_variants SET engine_code=? WHERE engine_code='VQ35HR' AND car_brand='Infiniti' AND fuel='Hybrid'", (HYB,)).rowcount
print(f"relinked {n} Infiniti hybrid variants to {HYB}")
cur.execute("""UPDATE engines SET count_variants =
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")
cur.execute("UPDATE engine_service_specs SET power_hp=360 WHERE engine_code=? AND power_hp IS NULL", (HYB,))
con.commit()
print("fuel conflicts Infiniti:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v JOIN engines e ON v.engine_code=e.engine_code
    WHERE v.car_brand='Infiniti' AND v.fuel IS NOT NULL AND e.fuel IS NOT NULL AND v.fuel != e.fuel""").fetchone()[0])
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close()
