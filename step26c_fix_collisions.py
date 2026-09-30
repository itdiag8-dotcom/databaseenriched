"""Step 26c: repair two silent code collisions from batch 17 (VW).
1. CYFB: pre-existing FORD Transit 2.2 TDCi row - the 2 Golf R variants were linked to it
   (petrol variants on a diesel engine row) and step26b overwrote the Ford spec's oil values
   with Golf R votes. Fix: new row '2.0 TSI EA888 Gen3 (Golf R)' (CYFB is the true US Golf R
   code per GTS but collides in this DB), relink the 2 Golf R variants, restore the Ford CYFB
   spec + tech rows from the pre_step26 backup.
2. DGUA: pre-existing NULL junk row - NEW_ENGINES insert skipped (row existed), so 7 Tiguan
   variants sit on a NULL row. Fix: fill engine_type/displacement/power/cylinders/fuel,
   spec power 184, and the pre-existing Tiguan 2021 NULL-power variant.
3. CGRA: pre-existed with correct values (3597cc/280hp) - relabel only.
4. CXBB: spec power NULL -> 170 (engines row value).
Lesson (new standing rule): pre-apply assert must check the target row's IDENTITY when the
code already exists (existing row may be a different brand's engine), not just existence."""
import sqlite3
from datetime import date

DB = "database_enriched/car_database.db"
BAK = "database_enriched/backups/car_database_backup_pre_step26_2026-09-30.db"

con = sqlite3.connect(DB); cur = con.cursor()
bak = sqlite3.connect(BAK); bcur = bak.cursor()

# 1. Golf R: new row + relink + spec
GOLFR = "2.0 TSI EA888 Gen3 (Golf R)"
if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (GOLFR,)).fetchone():
    cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
        cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP26C_VERIFIED')""",
        (GOLFR, "2.0 TSI EA888 Gen3 (US Golf R 2015-18, 292hp IS38; US code CYFB)", "Petrol", 1984, 292, 4))
    print(f"created {GOLFR}")
n = cur.execute("UPDATE vehicle_variants SET engine_code=? WHERE engine_code='CYFB' AND car_brand='Volkswagen'", (GOLFR,)).rowcount
print(f"relinked {n} Golf R variants")
if not cur.execute("SELECT 1 FROM engine_service_specs WHERE engine_code=?", (GOLFR,)).fetchone():
    cur.execute("""INSERT INTO engine_service_specs (engine_code, oil_viscosity, oil_capacity_with_filter_l,
        power_hp, oil_spec_source) VALUES (?,?,?,?,?)""",
        (GOLFR, "5W-40", 5.67, 292, "lemon.dogeware.me LEMON variant-majority (via step26b): vis 5W-40 x2/2, cap 5.67L x2/2 (AMSOIL: Golf R 502.00-family 5.7L)"))
    print(f"created spec for {GOLFR}")

# 2. restore Ford CYFB spec + tech rows from backup
for table in ["engine_service_specs", "engine_technical_specs"]:
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({table})")]
    cur.execute(f"DELETE FROM {table} WHERE engine_code='CYFB'")
    src = bcur.execute(f"SELECT {','.join(cols)} FROM {table} WHERE engine_code='CYFB'").fetchone()
    if src:
        cur.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})", src)
        print(f"restored Ford CYFB {table} from backup")
    else:
        print(f"no backup {table} row for CYFB (none existed)")

# 3. DGUA row fill + Tiguan 2021 NULL power variant + spec power
cur.execute("""UPDATE engines SET engine_type='2.0 TSI EA888 Gen3B Budack (Tiguan 2018+, 184hp)',
    fuel='Petrol', displacement_cc=1984, power_hp=184, cylinders=4 WHERE engine_code='DGUA'""")
print("filled DGUA engine row")
n = cur.execute("UPDATE vehicle_variants SET engine_power_hp=184 WHERE engine_code='DGUA' AND engine_power_hp IS NULL").rowcount
print(f"filled {n} DGUA variant power(s)")
cur.execute("UPDATE engine_service_specs SET power_hp=184 WHERE engine_code='DGUA' AND (power_hp IS NULL OR power_hp != 184)")

# 4. CGRA relabel
cur.execute("UPDATE engines SET engine_type='3.6 VR6 FSI EA390 (Touareg 3.6, 276-280hp US)' WHERE engine_code='CGRA'")
# 5. CXBB spec power
cur.execute("UPDATE engine_service_specs SET power_hp=170 WHERE engine_code='CXBB' AND (power_hp IS NULL OR power_hp != 170)")

cur.execute("""UPDATE engines SET count_variants =
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")
con.commit()

print("\n--- verify ---")
print("CYFB variants (Ford only expected):", cur.execute("SELECT car_brand, car_model, COUNT(*) FROM vehicle_variants WHERE engine_code='CYFB' GROUP BY 1,2").fetchall())
print("Golf R row:", cur.execute("SELECT engine_type, fuel, power_hp, count_variants FROM engines WHERE engine_code=?", (GOLFR,)).fetchone())
print("DGUA row:", cur.execute("SELECT engine_type, fuel, displacement_cc, power_hp, count_variants FROM engines WHERE engine_code='DGUA'").fetchone())
print("fuel conflicts (variant fuel vs engine fuel) on VW batch targets:",
      cur.execute("""SELECT COUNT(*) FROM vehicle_variants v JOIN engines e ON v.engine_code=e.engine_code
        WHERE v.car_brand='Volkswagen' AND v.engine_code IN ('CYFB','DGUA',?)
        AND v.fuel IS NOT NULL AND e.fuel IS NOT NULL AND v.fuel != e.fuel""", (GOLFR,)).fetchone()[0])
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close(); bak.close()
