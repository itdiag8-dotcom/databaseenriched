"""Step 29c: post-batch-20 audit repairs (step27c precedent: fix pre-existing conflicts caught
by the batch fuel-conflict audit).
1. LE5 (2.4 petrol row, shared by Captiva/Malibu/HHR/Cobalt/Solstice + Chinese LaCrosse) carries
   2 CHEVROLET Malibu variants labeled Hybrid: the 2008-2010 Malibu Hybrid was a BAS belt-alternator
  -starter MILD hybrid built around the same LE5 2.4 petrol engine - same situation as the LUK
   eAssist rows normalized to Petrol in step 29 (DB convention: micro/mild hybrids on shared petrol
   engine rows keep the Petrol fuel label). Fuel-fix both -> Petrol.
2. Sweep 4 NULL variant powers on LE2 (Encore 2016-19 pre-existing links; step 29 filled the LE2
   engines row 1399cc/153hp).
ESTIMATE specs remaining on Buick-linked codes (A16LET/F16D3/RA 420/LL6 = Chinese Excelle/LaCrosse
engines, no lemon data) are left as-is - honestly flagged, out of US-batch scope.
"""
import sqlite3

DB = "database_enriched/car_database.db"
con = sqlite3.connect(DB); cur = con.cursor()

cur.execute("""UPDATE vehicle_variants SET fuel='Petrol' WHERE engine_code='LE5' AND fuel='Hybrid'""")
print(f"fuel-fixed LE5 mild-hybrid variants -> Petrol: {cur.rowcount} (Malibu BAS 2008/2010)")

cur.execute("""UPDATE vehicle_variants SET engine_power_hp=
    (SELECT power_hp FROM engines WHERE engine_code='LE2')
    WHERE engine_code='LE2' AND engine_power_hp IS NULL""")
print(f"swept LE2 NULL powers: {cur.rowcount} (Encore 2016-19 -> 153hp)")

con.commit()

print("\n--- audit ---")
print("fuel conflicts among Buick-linked targets:",
      cur.execute("""SELECT v.engine_code, e.fuel, v.fuel, COUNT(*) FROM vehicle_variants v
        JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IN (SELECT DISTINCT engine_code FROM vehicle_variants WHERE car_brand='Buick' AND engine_code NOT LIKE 'LEMON%')
        AND v.fuel != e.fuel GROUP BY 1,2,3""").fetchall() or "NONE")
print("NULL powers on Buick non-LEMON:",
      cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand='Buick' AND engine_power_hp IS NULL AND engine_code NOT LIKE 'LEMON%'").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
con.close()
