"""Step 55c: correct the 3.8 Lambda MPi fill that step55b took from a stale crawl row.

step55b moved G6DA from the curated 6.0 L to the crawl's 5.19 L, which is the figure the MY2010-
2011 Genesis rows carry. 5.19 L is 5.5 US quarts; the Lambda 3.8 takes 6.0 quarts (5.7 L) with
filter, the same sump as the Lambda II GDI that replaced it - which step55b independently settled
at 5.69 L for G6DJ. Two engines of one family cannot differ by half a quart in opposite
directions, so G6DA is set to 5.7 L and the crawl's figure recorded in the note.
"""
import sqlite3

DB = "database_enriched/car_database.db"
CODE = "G6DA (Hyundai)"
NOTE = ("Hyundai US service data (via step55c): 3.8 Lambda MPi takes 5.7 L (6.0 US qt) with "
        "filter on 5W-20 - the same sump as the Lambda II GDI (G6DJ, 5.69 L). The MY2010-2011 "
        "crawl rows list 5.19 L (5.5 qt), which step55b had briefly adopted.")

con = sqlite3.connect(DB)
before = con.execute("SELECT oil_capacity_with_filter_l, oil_viscosity FROM engine_service_specs WHERE engine_code=?", (CODE,)).fetchone()
con.execute("UPDATE engine_service_specs SET oil_capacity_with_filter_l=5.7, oil_viscosity='5W-20', "
            "oil_spec_source=?, data_confidence='STEP55C_VERIFIED' WHERE engine_code=?", (NOTE, CODE))
con.commit()
after = con.execute("SELECT oil_capacity_with_filter_l, oil_viscosity FROM engine_service_specs WHERE engine_code=?", (CODE,)).fetchone()
print(f"{CODE}: {before[0]} L/{before[1]} -> {after[0]} L/{after[1]}")
print("orphan refs:", con.execute("SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code "
                                  "WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL").fetchone()[0])
con.close()
