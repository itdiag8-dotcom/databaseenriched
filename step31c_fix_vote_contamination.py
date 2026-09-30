"""Step 31c: post-batch-22 audit repairs (vote line-audit findings + sweeps).
1. B6324S (3.2 I6 Volvo SI6, LR2 2008-12): step31b majority set 5W-30/9.22L - capacity is a
   contamination (no SI6 application takes 9L). External sources: 5W-30, 7.7L / 8.1 qt
   (costaoils.com 2008 LR2 3.2L guide + landroverforums.com 'LR Techniker': 7.7L/8.1qt).
   SET 5W-30 / 7.7.
2. 25K4F (2.5 V6 KV6, Freelander 2002-05): step31b unanimous 0W-40/5.2 - capacity 5.2L is
   confirmed exactly (auto-data.net: oil capacity 5.2L, engine code 25K4F), but 0W-40 appears
   in no source; AMSOIL US-spec sheet lists 10W-40/10W-50 (above -20C) or 5W-40/5W-50 (all
   temps). SET 5W-40 / 5.2.
3. Sweeps + global audit (fuel conflicts among LR-linked, NULL powers, ESTIMATE).
"""
import sqlite3

DB = "database_enriched/car_database.db"
con = sqlite3.connect(DB); cur = con.cursor()

REPAIRS = {
    "B6324S": ("5W-30", 7.7,
        "step31c repair: step31b 9.22L capacity rejected (contamination); LR2 3.2 SI6 = 5W-30, "
        "7.7L/8.1qt [costaoils.com 2008 LR2 3.2L guide + landroverforums.com LR Techniker]"),
    "25K4F": ("5W-40", 5.2,
        "step31c repair: step31b 0W-40 rejected (no source); KV6 = 5W-40 all-temps / 10W-40 above "
        "-20C, 5.5qt with filter [AMSOIL 2002 Freelander 2.5 spec + auto-data.net 5.2L sump]"),
}
for code, (vis, cap, note) in REPAIRS.items():
    cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?", (code,))
    row = cur.fetchone()
    if row is None:
        print(f"  !! {code}: NO SPEC ROW"); continue
    cur.execute("UPDATE engine_service_specs SET oil_viscosity=?, oil_capacity_with_filter_l=?, oil_spec_source=? WHERE engine_code=?",
                (vis, cap, note, code))
    print(f"  REPAIR {code}: {row[0]}/{row[1]} -> {vis}/{cap}")

con.commit()

print("\n--- audit: final spec state of batch targets ---")
for code in ["B6324S", "25K4F", "306DT", "AJ126", "AJ300P", "508PN", "508PS", "AJ41", "428PS",
             "M62B44", "204PT", "204DTD", "4.0 V8 (Rover OHV)", "4.6 V8 (Rover OHV)",
             "P400e 2.0 PHEV (AJ200P + motor)", "P440e/P550e 3.0 I6 PHEV",
             "P530 4.4 V8 TT (N63TU3)", "P530 MHEV 4.4 V8 TT (S68)"]:
    r = cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l, power_hp FROM engine_service_specs WHERE engine_code=?", (code,)).fetchone()
    e = cur.execute("SELECT power_hp, fuel, count_variants FROM engines WHERE engine_code=?", (code,)).fetchone()
    print(f"  {code:34} spec={r} engines={e}")

print("\n--- audit: fuel conflicts among LR-linked codes ---")
rows = cur.execute("""SELECT v.engine_code, e.fuel, v.fuel, COUNT(*) FROM vehicle_variants v
    JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.engine_code IN (SELECT DISTINCT engine_code FROM vehicle_variants WHERE car_brand='Land Rover' AND engine_code NOT LIKE 'LEMON%')
    AND v.fuel != e.fuel GROUP BY 1,2,3""").fetchall()
for r in rows: print("  CONFLICT:", r)
if not rows: print("  none")

print("\nNULL powers on LR non-LEMON:",
      cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand='Land Rover' AND engine_power_hp IS NULL AND engine_code NOT LIKE 'LEMON%'").fetchone()[0])
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
print("LR fuels:", dict(cur.execute("SELECT fuel, COUNT(*) FROM vehicle_variants WHERE car_brand='Land Rover' GROUP BY fuel").fetchall()))
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close()
