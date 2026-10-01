"""Step 48c: clear the one Lexus fuel conflict that sits on a step-48 target.

`2AR-FXE` is the ES 300h / Camry Hybrid engine (fuel Hybrid) and batch 39 relinked the MY2018 ES
LEMON row onto it. One pre-existing variant - ES chassis AVV6 recorded as MY2011 - was already
pointing at 2AR-FXE while flagged Petrol, as was a Camry AVV5 row. AVV6 and AVV5 *are* the hybrid
bodyshells, so the engine link is right and the fuel flag is the error; the fuel is corrected
rather than the link.

The other 9 Lexus fuel conflicts (2AR-FSE, 2GR-FSE, 2GR-FXE, 3MZ-FE, T24A-FTS) sit on rows this
batch never touched and are left for a later clean-up pass.
"""
import sqlite3

con = sqlite3.connect("database_enriched/car_database.db"); cur = con.cursor()
ids = [r[0] for r in cur.execute(
    "SELECT id FROM vehicle_variants WHERE engine_code='2AR-FXE' AND fuel<>'Hybrid'")]
cur.execute("UPDATE vehicle_variants SET fuel='Hybrid' WHERE id IN (%s)" % ",".join("?" * len(ids)), ids)
print("ES 300h variants corrected to Hybrid:", ids)
con.commit()
print("conflicts on 2AR-FXE:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
    JOIN engines e ON e.engine_code=v.engine_code WHERE v.engine_code='2AR-FXE' AND v.fuel<>e.fuel""").fetchone()[0])
print("Lexus conflicts total (pre-existing):", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
    JOIN engines e ON e.engine_code=v.engine_code WHERE v.car_brand='Lexus' AND v.fuel<>e.fuel""").fetchone()[0])
con.close()
