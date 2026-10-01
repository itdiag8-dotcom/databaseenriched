"""Step 52c: restore the Sprinter OM642 oil fill that step52b's majority vote degraded.

step52b picks the most common fill among the variants of a code. For the Sprinter V6 the 12
rows split 4x 12.5 L + 3x 12.49 L (2010-2018, the deep-sump van) against 5x 10.59 L (2019-2023),
so the minority value won a plurality and the engine row was left claiming 10.59 L. The OM642 in
the Sprinter takes 12.5 L (13.2 US qt); only the 2019+ vans take ~10.6 L. The engine row is
restored to 12.5 L with the later figure recorded in the note.
"""
import sqlite3

DB = "database_enriched/car_database.db"
CODE = "OM642 3.0 V6 CDI (Sprinter, 188hp)"
NOTE = ("Mercedes-Benz Sprinter service data (via step52c): OM642 3.0 V6 CDI takes 12.5 L "
        "(13.2 US qt) with filter in the 2010-2018 van; the 2019+ Sprinter takes ~10.6 L. "
        "step52b's plurality vote had wrongly adopted the later figure for the whole code.")

con = sqlite3.connect(DB)
before = con.execute("SELECT oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?", (CODE,)).fetchone()
con.execute("UPDATE engine_service_specs SET oil_capacity_with_filter_l=12.5, oil_spec_source=?, "
            "data_confidence='STEP52C_VERIFIED' WHERE engine_code=?", (NOTE, CODE))
con.commit()
after = con.execute("SELECT oil_capacity_with_filter_l,oil_viscosity FROM engine_service_specs WHERE engine_code=?", (CODE,)).fetchone()
print(f"{CODE}: {before[0]} -> {after[0]} L / {after[1]}")
print("orphan refs:", con.execute("SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code "
                                  "WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL").fetchone()[0])
con.close()
