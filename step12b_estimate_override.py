"""Step 12b: override remaining ESTIMATE-heuristic oil specs on step-12 shared targets with the
trusted lemon-crawl majority values recovered from the pre_step12 backup (step-10b pattern).
COALESCE in step 12 would not overwrite non-null (heuristic) values on pre-existing target rows.
"""
import sqlite3

DB = "database_enriched/car_database.db"
BAK = "database_enriched/backups/car_database_backup_pre_step12_2026-09-30.db"

# target -> (viscosity, capacity L, note); values = majority of retired LEMON rows (lemon crawl)
OVERRIDES = {
    "2.0 T 16v Ecoboost": ("5W-30", 5.39,
        "lemon crawl majority (Escape/Edge/Explorer/Taurus 2.0 EcoBoost 2013-2018 = 5W-30 5.39 L; "
        "2019+ rows said 5.2 L; Fusion no-VIN rows 0W-20 4.25 L treated as outlier)"),
    "3.0 V6": ("5W-20", 5.67,
        "lemon crawl majority (Escape 3.0 2005-2012 / Fusion 3.0 / Five Hundred / Freestyle = 5W-20 5.67 L; "
        "Ranger/Windstar Vulcan rows said 4.25 L)"),
    "4.0 V6": ("5W-30", 4.73,
        "lemon crawl uniform (Explorer/Ranger/Mustang 4.0 SOHC = 5W-30 4.73 L, all 31 rows)"),
    "4.6 V8": ("5W-20", 5.67,
        "lemon crawl majority (Crown Victoria/Explorer/Mustang 4.6 2003+ = 5W-20 5.67 L; "
        "2000-2002 rows said 4.73 L)"),
}

con = sqlite3.connect(DB)
cur = con.cursor()
bak = sqlite3.connect(BAK)
bcur = bak.cursor()

for code, (vis, cap, note) in OVERRIDES.items():
    cur_row = cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l, oil_spec_source FROM engine_service_specs WHERE engine_code=?", (code,)).fetchone()
    print(f"{code}: now {cur_row}")
    if not cur_row:
        cur.execute("""INSERT INTO engine_service_specs (engine_code, oil_viscosity, oil_capacity_with_filter_l, oil_spec_source)
                       VALUES (?,?,?,?)""", (code, vis, cap, f"lemon.dogeware.me LEMON (majority, via step12b): {note}"))
        print(f"  -> inserted {vis} / {cap} L")
    else:
        cur.execute("""UPDATE engine_service_specs SET oil_viscosity=?, oil_capacity_with_filter_l=?, oil_spec_source=?
                       WHERE engine_code=?""", (vis, cap, f"lemon.dogeware.me LEMON (majority, via step12b): {note}", code))
        print(f"  -> overridden {vis} / {cap} L")

con.commit()
print("\n=== VERIFY ===")
print("ESTIMATE-heuristic rows left among step-12 targets:",
      cur.execute("""SELECT COUNT(*) FROM engine_service_specs WHERE engine_code IN
        ('2.3 EcoBoost','1.6 EcoBoost','1.5 EcoBoost','1.0 EcoBoost','2.5 I4 (Duratec 25)','2.5 I4 Hybrid',
         '2.5 OHC (Lima)','2.0 Duratec GDI','2.0 Atkinson Hybrid','2.0 Energi (PHEV)','3.3 V6 Hybrid',
         '3.0 V6 EcoBoost','3.9 V8 (AJ35)','3.9 V6 (Essex)','5.4 V8 Supercharged (GT500)',
         '5.8 V8 Supercharged (GT500)','5.2 V8 (Voodoo)','5.4 V8 Supercharged (Ford GT)','2.0 SPI 8v',
         'E-Transit Electric','Focus Electric','2.0 T 16v Ecoboost','3.5 Cyclone V6','3.0 V6','4.6 V8',
         '4.0 V6','3.5 V6 EcoBoost','3.7 Ti-VCT V6')
        AND oil_spec_source LIKE 'ESTIMATE%'""").fetchone()[0])
for code in OVERRIDES:
    print(" ", cur.execute("SELECT engine_code, oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?", (code,)).fetchone())
con.close(); bak.close()
