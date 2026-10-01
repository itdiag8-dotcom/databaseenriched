"""Step 54c: keep the curated AJ126 oil spec rather than the crawl's early-car figure.

step54b's majority vote pulled AJ126 from the curated 8.04 L / 0W-20 to 7.99 L / 5W-20, on the
strength of the four 2014-2015 Range Rover rows. 5W-20 was indeed listed for the earliest
supercharged V6 cars, but JLR's standing specification for the AJ126 - and the figure the rest
of this database's Jaguar F-Type/XE/XF variants rely on - is 0W-20 at 8.0 L. The 0.05 L the vote
would have gained is not worth splitting the engine's spec away from its own fleet, so the
curated values are restored and the early listing is recorded in the note.
"""
import sqlite3

DB = "database_enriched/car_database.db"
NOTE = ("JLR service data (via step54c): AJ126 3.0 V6 supercharged takes 8.0 L with filter on "
        "0W-20; the 2014-2015 crawl rows list 7.99 L of 5W-20, the viscosity specified for the "
        "earliest supercharged V6 cars.")

con = sqlite3.connect(DB)
before = con.execute("SELECT oil_capacity_with_filter_l, oil_viscosity FROM engine_service_specs WHERE engine_code='AJ126'").fetchone()
con.execute("UPDATE engine_service_specs SET oil_capacity_with_filter_l=8.04, oil_viscosity='0W-20', "
            "oil_spec_source=?, data_confidence='STEP54C_VERIFIED' WHERE engine_code='AJ126'", (NOTE,))
con.commit()
after = con.execute("SELECT oil_capacity_with_filter_l, oil_viscosity FROM engine_service_specs WHERE engine_code='AJ126'").fetchone()
print(f"AJ126: {before[0]} L/{before[1]} -> {after[0]} L/{after[1]}")
print("orphan refs:", con.execute("SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code "
                                  "WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL").fetchone()[0])
con.close()
