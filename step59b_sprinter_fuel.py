"""Step 59b: the one conflict step59 created rather than removed.

The Sprinter MY2023 variant sat on a stub engine code `654` whose fuel was Diesel, so it was a
conflict (variant Petrol vs engine Diesel). step59 relinked it to the real OM654 Sprinter row
that batch 43 created - which is also Diesel - so the relink alone left the conflict standing.
The variant's own label was the wrong half: the Sprinter's OM654 is a turbodiesel and was never
sold as a petrol, so the variant becomes Diesel.
"""
import sqlite3

DB = "database_enriched/car_database.db"
CODE = "OM654 2.0 I4 CDI (Sprinter, 161-168hp)"
con = sqlite3.connect(DB)
n = con.execute("UPDATE vehicle_variants SET fuel='Diesel' WHERE engine_code=? AND fuel='Petrol'", (CODE,)).rowcount
con.commit()
print(f"variants corrected Petrol -> Diesel: {n}")
print("fuel conflicts DB-wide:", con.execute("""SELECT count(*) FROM vehicle_variants v JOIN engines e
    ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel""").fetchone()[0])
print("orphan refs:", con.execute("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
con.close()
