"""Step 45c: clear the two Audi fuel conflicts that sit on a step-45 target.

`CNCD` (2.0 TFSI longitudinal, 220hp, Petrol) is one of the engines batch 36 relinked LEMON rows
onto. Two pre-existing variants - Q5 2013 and Q5 2016 - were already pointing at it while carrying
fuel='Hybrid'. Those cars are real: the Q5 hybrid quattro paired the 2.0 TFSI with a 40 kW motor
for 245hp combined. The fuel flag was right and the engine link was wrong, so this script gives
them their own engine row instead of flattening the fuel.

The other 11 Audi fuel conflicts (BGB, CHJA, CTUA, CWZA) are pre-existing crawl errors on rows
batch 36 never touched and are left for a later clean-up pass.
"""
import sqlite3
from datetime import date

DB = "database_enriched/car_database.db"
CODE = "2.0 TFSI Hybrid (Q5 Hybrid quattro, 245hp)"
con = sqlite3.connect(DB); cur = con.cursor()

cur.execute("""INSERT OR IGNORE INTO engines
    (engine_code, engine_type, fuel, displacement_cc, power_hp, cylinders,
     brand_example, model_example, year_example, count_variants, data_confidence)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
    (CODE, "2.0 I4 Turbo TFSI + 40kW motor, hybrid quattro (Q5 Hybrid, 245hp combined)",
     "Hybrid", 1984, 245, 4, "Audi", "Q5", 2013, 0, "STEP45C_VERIFIED"))

ids = [r[0] for r in cur.execute(
    "SELECT id FROM vehicle_variants WHERE car_brand='Audi' AND engine_code='CNCD' AND fuel='Hybrid'")]
for vid in ids:
    cur.execute("UPDATE vehicle_variants SET engine_code=?, engine_power_hp=245 WHERE id=?", (CODE, vid))
print("relinked Q5 hybrid variants:", ids)

for code in (CODE, "CNCD"):
    n = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code=?", (code,)).fetchone()[0]
    cur.execute("UPDATE engines SET count_variants=? WHERE engine_code=?", (n, code))
    print(f"  {code}: count_variants={n}")

con.commit()
print("\n--- audit ---")
print("Audi conflicts on step-45 targets:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
    JOIN engines e ON e.engine_code=v.engine_code WHERE v.car_brand='Audi' AND v.fuel<>e.fuel
    AND v.engine_code IN ('CNCD','CYMC','CTUC','CTWA','CALA','CALB','AMB','AVK','ATC','CRDB',
    '4.2 V8 FSI (RS4/RS5)','2.0 TFSI EA888 Gen3 (A3 8V / TT 8S, 220hp)',
    '3.0 V6 TFSI EA839 (55 TFSI, A6/A7 335hp)',?)""", (CODE,)).fetchone()[0])
print("Audi conflicts total (pre-existing):", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
    JOIN engines e ON e.engine_code=v.engine_code WHERE v.car_brand='Audi' AND v.fuel<>e.fuel""").fetchone()[0])
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM engines e WHERE e.engine_code=v.engine_code)""").fetchone()[0])
print("engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
con.close()
