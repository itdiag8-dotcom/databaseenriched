"""Step 37c: two spec repairs around batch 28.

1. `EVA` (Chrysler 4.7 V8 PowerTech, used by the Mitsubishi Raider) had a correct 5.67 L oil
   capacity that step37b's crawl-majority normalisation overwrote with 4.73 L - the figure the
   LEMON crawl carries for the 3.7 V6. The 4.7 takes 6 US qt (5.67 L) with filter, so it is
   restored and the source note records why.
2. Battery-electric engine rows that came in from the vivid import carry a *heuristic* engine-oil
   spec (e.g. the i-MiEV's Y4F1 listed as "5W-30, 3.1 L"). Electric motors have no engine oil, so
   those ESTIMATE rows are deleted. LEMON-sourced EV codes already have NULL oil specs, which is
   the convention this aligns with; the BMW i3 (range-extender values, explicitly documented in
   its source note) and crawl-sourced rows are left untouched.

Run with --apply to write.
"""
import sqlite3, sys

DB = "database_enriched/car_database.db"
apply = "--apply" in sys.argv
con = sqlite3.connect(DB); cur = con.cursor()

print("1. EVA oil capacity")
print("   before:", cur.execute(
    "SELECT oil_viscosity, oil_capacity_with_filter_l, oil_spec_source FROM engine_service_specs WHERE engine_code='EVA'").fetchone())

ev = cur.execute("""SELECT e.engine_code, s.oil_viscosity, s.oil_capacity_with_filter_l
    FROM engines e JOIN engine_service_specs s ON s.engine_code=e.engine_code
    WHERE e.fuel='Electric' AND s.oil_spec_source LIKE 'ESTIMATE%'""").fetchall()
print(f"2. BEV rows with heuristic engine-oil specs: {len(ev)}")
for r in ev:
    print("  ", r)

if not apply:
    print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); sys.exit()

cur.execute("""UPDATE engine_service_specs SET oil_capacity_with_filter_l=5.67, oil_viscosity='5W-20',
    oil_spec_source=? WHERE engine_code='EVA'""",
    ("Chrysler 4.7L PowerTech V8 OEM service data: 6.0 US qt (5.67 L) with filter, 5W-20 "
     "(restored in step37c; step37b crawl-majority had pulled in the 3.7 V6 figure)",))
cur.executemany("DELETE FROM engine_service_specs WHERE engine_code=?", [(r[0],) for r in ev])
con.commit()

print("\n--- audit ---")
print("EVA:", cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code='EVA'").fetchone())
print("BEV rows still carrying engine oil (excl. i3 range-extender):", cur.execute("""SELECT COUNT(*)
    FROM engines e JOIN engine_service_specs s ON s.engine_code=e.engine_code
    WHERE e.fuel='Electric' AND s.oil_viscosity IS NOT NULL AND e.engine_code NOT LIKE 'i3%'""").fetchone()[0])
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e
    ON e.engine_code=v.engine_code WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close()
