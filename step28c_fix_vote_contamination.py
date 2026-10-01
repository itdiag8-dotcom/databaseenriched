"""Step 28c: repair step28b majority-vote contaminations + set Hurricane H.O. spec.
step28b line-audit findings (majority-vote hazard rule):
- EZH (5.7 HEMI V8 VCT, n=177 variants: Durango/Ram/Charger/300/GC/Challenger) was flipped to
  15W-40/11.35L by a SINGLE x1/1 vote (a diesel Chassis Cab trim entry). 5.7 HEMI = SAE 5W-20
  (MS-6395), 7 qt / 6.6L. REVERT to pre-batch 5W-20/6.62.
- M272E35 (n=43, mostly Mercedes GLK350/SLK350/CLK350/C350 = 8.0L sump) was flipped to 5W-40/12.5
  by 2-3 Sprinter trim votes. Row keeps the MB-car spec 0W-30/8.04 (pre-batch). REVERT.
- '3.5 V6 (LX)' (n=18: 300/Charger/Magnum/Challenger 3.5 SOHC) was flipped to 0W-40/6.62 by a
  SINGLE x1/1 vote. 3.5 LX = 10W-30, ~5qt. REVERT to pre-batch 10W-30/5.67.
- '3.0 Hurricane I6' 0W-20 x6/6 + 7.09L CONFIRMED correct (blauparts/amsoil: SO = 0W-20 MS-6395,
  7.1L/7.5qt; also confirms engine code [P] = Hurricane SO -> VINP decode used in step28).
- '3.0 Hurricane I6 H.O. (Grand Wagoneer)': H.O. spec = SAE 0W-40 (MS-A0921) per blauparts
  (High-Output 0W-40 vs Standard-Output 0W-20). SET 0W-40 / 7.1L if missing or wrong.
"""
import sqlite3

DB = "database_enriched/car_database.db"
con = sqlite3.connect(DB); cur = con.cursor()

REVERTS = {
    "EZH": ("5W-20", 6.62,
            "step28c revert: step28b single-vote (x1/1 diesel Chassis Cab trim) contamination rejected; "
            "5.7 HEMI V8 = SAE 5W-20 (MS-6395), 7qt/6.6L (pre-batch value restored)"),
    "M272E35": ("0W-30", 8.04,
             "step28c revert: step28b 2-3 Sprinter-trim votes vs 38+ Mercedes-car variants on shared row; "
             "M272 E35 cars = ~8.0L sump (pre-batch value restored)"),
    "3.5 V6 (LX)": ("10W-30", 5.67,
             "step28c revert: step28b single-vote (x1/1 Challenger trim) contamination rejected; "
             "3.5 SOHC LX = 10W-30 ~5qt (pre-batch value restored)"),
}
for code, (vis, cap, note) in REVERTS.items():
    cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?", (code,))
    row = cur.fetchone()
    if row is None:
        print(f"  !! {code}: NO SPEC ROW"); continue
    cur.execute("UPDATE engine_service_specs SET oil_viscosity=?, oil_capacity_with_filter_l=?, oil_spec_source=? WHERE engine_code=?",
                (vis, cap, note, code))
    print(f"  REVERT {code}: {row[0]}/{row[1]} -> {vis}/{cap}")

# Hurricane H.O. spec (blauparts: High-Output = SAE 0W-40 MS-A0921; capacity ~7.1L like SO)
ho = cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?",
                 ("3.0 Hurricane I6 H.O. (Grand Wagoneer)",)).fetchone()
if ho is None:
    cur.execute("""INSERT INTO engine_service_specs (engine_code, oil_viscosity, oil_capacity_with_filter_l, oil_spec_source, power_hp)
        SELECT '3.0 Hurricane I6 H.O. (Grand Wagoneer)', '0W-40', 7.1,
        'step28c set: Hurricane H.O. = SAE 0W-40 (MS-A0921), 7.1L/7.5qt [blauparts.com Jeep GW 3.0L Hurricane oil kit page: SO=0W-20 MS-6395, HO=0W-40]',
        (SELECT power_hp FROM engines WHERE engine_code='3.0 Hurricane I6 H.O. (Grand Wagoneer)')""")
    print("  SET Hurricane H.O. spec row: 0W-40/7.1 (was missing)")
elif ho[0] != "0W-40":
    cur.execute("UPDATE engine_service_specs SET oil_viscosity='0W-40', oil_capacity_with_filter_l=COALESCE(?,7.1),"
                " oil_spec_source='step28c set: Hurricane H.O. = SAE 0W-40 (MS-A0921) [blauparts GW 3.0 Hurricane kit]' WHERE engine_code=?",
                (ho[1], "3.0 Hurricane I6 H.O. (Grand Wagoneer)"))
    print(f"  SET Hurricane H.O.: {ho[0]}/{ho[1]} -> 0W-40/{ho[1] or 7.1}")
else:
    print(f"  Hurricane H.O. already {ho[0]}/{ho[1]}")

con.commit()

print("\n--- audit: final spec state of key batch targets ---")
for code in ["EZH", "M272E35", "3.5 V6 (LX)", "3.0 Hurricane I6", "3.0 Hurricane I6 H.O. (Grand Wagoneer)",
             "5.7 HEMI V8 eTorque (Wagoneer)", "ETH", "OM612DE27LA", "3.6 Pentastar", "3.6 V6 Pentastar PHEV (Pacifica Hybrid)",
             "1.3 GSE PHEV (Hornet R/T)", "8.0 V10 (Viper Gen II)", "8.4 V10 (Viper Gen V)"]:
    r = cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l, power_hp FROM engine_service_specs WHERE engine_code=?", (code,)).fetchone()
    e = cur.execute("SELECT power_hp, count_variants FROM engines WHERE engine_code=?", (code,)).fetchone()
    print(f"  {code:38} spec={r if r else None} engines(power,n)={e}")

print("\n--- audit: fuel conflicts among batch targets ---")
rows = cur.execute("""SELECT v.engine_code, e.fuel, v.fuel, COUNT(*) FROM vehicle_variants v
    JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.car_brand IN ('Dodge','Chrysler','Jeep') AND v.engine_code IN
    (SELECT DISTINCT new_engine_code FROM (SELECT '3.6 Pentastar' AS new_engine_code) UNION ALL
     SELECT 'ED3' UNION ALL SELECT 'EDZ' UNION ALL SELECT 'EER' UNION ALL SELECT 'ED8' UNION ALL SELECT 'EGA' UNION ALL SELECT 'EGH'
     UNION ALL SELECT 'EGG' UNION ALL SELECT 'ECN' UNION ALL SELECT '1.4 MultiAir Turbo (Dart/Renegade)' UNION ALL SELECT '6G72(SOHC24V)'
     UNION ALL SELECT '1.3 GSE Turbo (Renegade)' UNION ALL SELECT 'EGS' UNION ALL SELECT '3.6 V6 Pentastar PHEV (Pacifica Hybrid)'
     UNION ALL SELECT 'EGF' UNION ALL SELECT '2.0 TigerShark (Dart)' UNION ALL SELECT '8.4 V10 (Viper Gen V)'
     UNION ALL SELECT '4.0 V6 (Chrysler, Routan)' UNION ALL SELECT '2.0 Turbo GME' UNION ALL SELECT '2.0 SOHC 16v (Neon)'
     UNION ALL SELECT '3.2 Pentastar' UNION ALL SELECT '3.0 Hurricane I6 H.O. (Grand Wagoneer)' UNION ALL SELECT 'ETH'
     UNION ALL SELECT 'OM612DE27LA' UNION ALL SELECT '8.3 V10 SRT' UNION ALL SELECT 'EZC' UNION ALL SELECT '2.4 16v Turbo SRT-4'
     UNION ALL SELECT 'M272E35' UNION ALL SELECT 'EGX' UNION ALL SELECT '4.0 I6 (AMC)' UNION ALL SELECT '3.5 V6 (LX)'
     UNION ALL SELECT '8.4 V10 SRT10' UNION ALL SELECT '8.0 V10 (Viper Gen II)' UNION ALL SELECT 'ESG' UNION ALL SELECT 'EZH'
     UNION ALL SELECT 'EKG' UNION ALL SELECT '3.2 V6 (LH)' UNION ALL SELECT '1.8 World Engine (GEMA)'
     UNION ALL SELECT '1.3 GSE PHEV (Hornet R/T)' UNION ALL SELECT '5.7 HEMI V8 eTorque (Wagoneer)' UNION ALL SELECT '3.0 Hurricane I6')
    AND v.fuel != e.fuel GROUP BY 1,2,3""").fetchall()
if not rows: print("  none")
for r in rows: print("  CONFLICT:", r)
con.close()
