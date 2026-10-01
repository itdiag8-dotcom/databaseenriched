"""Step 35c: retire the pre-existing R23A2 duplicate of K23A1 (Acura RDX 2.3 turbo).

The vivid import created engine `R23A2` ("2.3 Turbo All-wheel Drive", 2298cc, 239hp, listed as
6-cylinder) with a single variant "Acura RDX 2005". There is no Honda engine called R23A2: the
first-generation RDX (TB1/TB2) shipped one engine only, the K23A1 2.3 i-VTEC turbo I4, 240hp,
and the model did not go on sale until MY2007.

  - https://en.wikipedia.org/wiki/Acura_RDX  (gen1 2007-2012, 2.3 L K23A1 turbo I4, 240 bhp, sole engine)
  - https://www.troublecodes.net/acura/rdx-2-3l-tl-3-23-5l-tsx-2-4l-2004-2009/  (OBD engine id: RDX 2.3L 2007-09 = K23A1)
  - https://www.rpmrons.com/Acurakits1.html  (RDX TURBO K23A1, 2300cc, 2007-2012)

The R23A2 technical-spec row is additionally self-inconsistent: bore 81.4 x stroke 73.6 only
reaches 2298cc across *six* cylinders, i.e. it was synthesised from the wrong cylinder count
(the real K23A1 is a 4-cylinder, 86.0 x 99.0 mm), so none of its derived geometry is carried over.

Action: relink the orphaned variant to K23A1, correct its year/production window and power,
then drop the R23A2 engine + spec rows. Run after step35b.
"""
import sqlite3, sys

DB = "database_enriched/car_database.db"
apply = "--apply" in sys.argv
con = sqlite3.connect(DB); cur = con.cursor()

v = cur.execute("SELECT id, car_brand, car_model, car_year, engine_code, engine_power_hp, "
                "production_start, production_end FROM vehicle_variants WHERE engine_code='R23A2'").fetchall()
print("R23A2 variants:", v)
if not cur.execute("SELECT 1 FROM engines WHERE engine_code='K23A1'").fetchone():
    sys.exit("K23A1 missing - run step35 first")
if not v:
    print("nothing to do (already migrated)"); sys.exit(0)

if not apply:
    print("DRY RUN - would relink %d variant(s) to K23A1 (year 2005->2007, prod 2007-2012, "
          "hp 239->240, engine_type corrected) and delete R23A2 from engines/"
          "engine_service_specs/engine_technical_specs. Re-run with --apply." % len(v))
    sys.exit(0)

cur.execute("""UPDATE vehicle_variants SET engine_code='K23A1', car_year=2007,
    production_start=2007, production_end=2012, engine_power_hp=240, engine_power_kw=179.0,
    engine_type='2.3 I4 DOHC i-VTEC Turbo (RDX 2007-2012, 240hp)'
    WHERE engine_code='R23A2'""")
print(f"  relinked {cur.rowcount} variant(s) R23A2 -> K23A1")
for t in ("engine_service_specs", "engine_technical_specs", "engines"):
    cur.execute(f"DELETE FROM {t} WHERE engine_code='R23A2'")
    print(f"  deleted R23A2 from {t} ({cur.rowcount})")
cur.execute("""UPDATE engines SET count_variants =
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)
    WHERE engine_code='K23A1'""")
con.commit()

print("\n--- audit ---")
print("K23A1:", cur.execute("SELECT engine_code, engine_type, fuel, displacement_cc, power_hp, "
                            "cylinders, count_variants FROM engines WHERE engine_code='K23A1'").fetchone())
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e
    ON e.engine_code=v.engine_code WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close()
