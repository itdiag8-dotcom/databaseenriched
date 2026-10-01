"""Step 39c: correct two oil capacities that step39b's crawl-majority normalization degraded.

step39b normalizes each target's oil spec to the majority value found in the LEMON crawl rows.
That is right when the crawl agrees with the service data, but the crawl's majority is wrong for
two of this batch's targets:

- LA1 (3.4 V6 OHV, GM 60-degree): normalized 4.25 -> 3.78 L. The GM 60-degree V6 family
  (2.8/3.1/3.4/4.3) takes 4.5 US qt = 4.25 L with filter [GM34OIL]; 3.78 L is 4 qt, the
  no-filter figure. Restored to 4.25 L.
- L76 (6.0 V8 Gen IV): ESTIMATE 7.2 -> 8.32 L. The 6.0 Vortec/L76 takes 6 US qt = 5.67 L with
  filter [GM60OIL]; 8.32 L (8.8 qt) is a dry-sump Corvette-class figure that does not apply.
  Set to 5.67 L.

[GM34OIL] mgexp.com / gm-trucks.com / justanswer.com: GM 60-degree V6 crankcase capacity
          4.5 qt including filter.
[GM60OIL] justanswer.com 2007 Silverado 6.0L Vortec Max: "6 quarts with an oil filter";
          corvetteforum.com owners-manual quote for the related 6.2 LS3: 6.0 qt / 5.7 L.
"""
import sqlite3
import sys

DB = "database_enriched/car_database.db"
APPLY = "--apply" in sys.argv

# code -> (capacity with filter, capacity without filter, viscosity, note)
FIX = {
    "LA1": (4.25, 3.78, "5W-30", "GM 60-degree V6 (2.8/3.1/3.4/4.3) crankcase capacity 4.5 US qt = 4.25 L "
                           "with filter [GM34OIL]; step39c restored after a crawl-majority normalization to 3.78 L"),
    "L76": (5.67, 5.20, "5W-30", "GM 6.0 V8 Gen IV (L76/LS2-family truck and Zeta applications) 6 US qt = 5.67 L "
                           "with filter [GM60OIL]; step39c replaced an 8.32 L crawl-majority value"),
}

con = sqlite3.connect(DB)
cur = con.cursor()
for code, (cap, cap_nf, vis, note) in FIX.items():
    row = cur.execute("""SELECT oil_capacity_with_filter_l, oil_capacity_without_filter_l, oil_viscosity
                         FROM engine_service_specs WHERE engine_code=?""", (code,)).fetchone()
    print(f"{code}: {row} -> ({cap}, {cap_nf}, '{vis}')")
    if APPLY:
        cur.execute("""UPDATE engine_service_specs
                       SET oil_capacity_with_filter_l=?, oil_capacity_without_filter_l=?, oil_viscosity=?,
                           oil_spec_source=?, data_confidence='STEP39_VERIFIED'
                       WHERE engine_code=?""", (cap, cap_nf, vis, note, code))

if APPLY:
    con.commit()
    print("\n--- audit ---")
    for code in FIX:
        print(code, cur.execute("""SELECT oil_viscosity, oil_capacity_with_filter_l,
                                          oil_capacity_without_filter_l, data_confidence
                                   FROM engine_service_specs WHERE engine_code=?""", (code,)).fetchone())
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
        LEFT JOIN engines e ON e.engine_code=v.engine_code WHERE e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines e WHERE e.count_variants <>
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)""").fetchone()[0])
    print("fuel conflicts (Pontiac+Saturn):", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
        JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.car_brand IN ('Pontiac','Saturn') AND v.fuel <> e.fuel""").fetchone()[0])
    print("fuel conflicts (DB-wide):", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
        JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel <> e.fuel""").fetchone()[0])
    print("engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
else:
    print("\nDRY RUN - no changes. Re-run with --apply.")
con.close()
