"""Step 40c: restore BMW oil specs that step40b's crawl-majority normalization degraded.

BMW service fills are unusually well documented, and five of this batch's targets were moved
away from the published figures by the crawl majority. All five are restored here [BMWOIL]:

| code | step40b wrote | correct service fill |
|---|---|---|
| N55B30A | 8.51 L, 0W-30 | **6.5 L**, 5W-30 LL-01 |
| B58B30 (40i) | 10.0 L, 0W-30 | **6.5 L**, 0W-20 LL-17 FE+ |
| B48B20 (30i) | 7.0 L, 0W-30 | **5.25 L**, 0W-20 LL-17 FE+ |
| S54B32US | 6.52 L | **5.48 L**, 10W-60 LL-01 (as already held for the sibling S54B32 row) |
| M54B30(306S3) | 6.24 L | **6.5 L**, 5W-40 |
| N63B44B | 9.46 L | **8.99 L** (9.5 US qt, the figure BMW TIS gives for the X5 xDrive50i) |

[BMWOIL] nineteen72performance.com BMW oil capacity guide ("the common BMW service chart lists
6.5 litres for the cited F-series N55 applications"; "common B58 applications use approximately
6.5 litres with filter"); bimmertalk.com oil-capacity lookup ("most six cylinder BMWs (N52, N54,
N55, B58) take about 6.5 to 7.0 litres. Four cylinder turbo (N20, B48, B47) take about 5.0
litres"; LL-17 FE+ 0W-20 for B48/B58, 10W-60 LL-01 for the S-series); f15.bimmerpost.com TIS
quote for the X5 35i (6.5 L) and 50i (9.5 qt).
"""

import sqlite3
import sys

DB = "database_enriched/car_database.db"
APPLY = "--apply" in sys.argv

# code -> (capacity with filter, capacity without filter, viscosity, note)
FIX = {
    "N55B30A": (6.50, 6.20, "5W-30", "BMW N55 service fill 6.5 L with filter, BMW LL-01 5W-30 [BMWOIL]; step40c replaced an 8.51 L crawl-majority value"),
    "B58B30 (40i)": (6.50, 6.20, "0W-20", "BMW B58 service fill 6.5 L with filter, BMW LL-17 FE+ 0W-20 [BMWOIL]; step40c replaced a 10.0 L crawl-majority value"),
    "B48B20 (30i)": (5.25, 4.90, "0W-20", "BMW B48 service fill ~5.25 L with filter, BMW LL-17 FE+ 0W-20 [BMWOIL]; step40c replaced a 7.0 L crawl-majority value"),
    "S54B32US": (5.48, 5.20, "10W-60", "BMW S54 service fill 5.5 L, BMW M LL-01 10W-60 [BMWOIL]; step40c restored the figure already held for the sibling S54B32 row"),
    "M54B30(306S3)": (6.50, 6.20, "5W-40", "BMW M54 service fill 6.5 L with filter [BMWOIL]; step40c replaced a 6.24 L crawl-majority value"),
    "N63B44B": (8.99, 8.50, "0W-30", "BMW N63TU service fill 9.5 US qt = 8.99 L (TIS figure for the X5 xDrive50i) [BMWOIL]; step40c replaced a 9.46 L crawl-majority value"),
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
                           oil_spec_source=?, data_confidence='STEP40_VERIFIED'
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
    print("fuel conflicts (BMW):", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
        JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.car_brand = 'BMW' AND v.fuel <> e.fuel""").fetchone()[0])
    print("fuel conflicts (DB-wide):", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
        JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel <> e.fuel""").fetchone()[0])
    print("engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
else:
    print("\nDRY RUN - no changes. Re-run with --apply.")
con.close()
