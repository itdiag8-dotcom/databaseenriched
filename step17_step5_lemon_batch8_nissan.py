"""Step 17 (user-plan Step 5, batch 8): replace LEMON_NISSAN codes with real OEM engine codes.
520 rows, 25 models. Nissan US lineup is nearly single-engine-per-model/year; signals = cc + VIN chars
+ 2015 trim slugs. DB VAG-equivalent Nissan vocabulary (QR/VQ/VK/MR/HR families) reused.
New: PR25DD, KR20DDET, KR15DDET, VQ38DD, VR30DDTT, Leaf EM57, Ariya EV, Cummins ISV 5.0."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "FRONTIER38": "https://autofiles.com/engine-type/nissan/vq/vq38dd/ (2020+ Frontier = VQ38DD 3.8 310hp, 0W-20)",
    "CROWN38": "https://www.crownnissan.com/nissan-frontier-info.html (2022 Frontier 3.8L V6 310hp)",
    "KICKS": "https://www.autopadre.com/horsepower-and-torque/nissan-kicks (Kicks 1.6 122hp to 2024; 2.0L 141hp from 2025)",
    "ARIYA": "https://www.nissanusa.com/vehicles/discontinued/ariya.html (Ariya 238hp FWD / 389hp e-4ORCE)",
}

NEW_ENGINES = {
    "PR25DD": ("2.5 I4 DI (2019+ Altima / 2021+ Rogue, 181-188hp)", "Petrol", 2488, 188, 4),
    "KR20DDET": ("2.0 I4 VC-Turbo (Altima 2.0T, 248hp)", "Petrol", 1997, 248, 4),
    "KR15DDET": ("1.5 I4 VC-Turbo (2022+ Rogue, 201hp)", "Petrol", 1497, 201, 4),
    "VQ38DD": ("3.8 V6 (2020+ Frontier, 310hp)", "Petrol", 3796, 310, 6),
    "VR30DDTT": ("3.0 V6 TwinTurbo (2023+ Z, 400hp)", "Petrol", 2993, 400, 6),
    "Leaf Electric (EM57)": ("Electric motor (Leaf 24-62kWh, 110-147hp)", "Electric", None, 147, None),
    "Ariya Electric": ("Electric motors (Ariya 238hp FWD / 389hp e-4ORCE)", "Electric", None, 238, None),
    "5.0 Cummins ISV V8 TD": ("5.0 V8 Cummins turbodiesel (Titan XD, 310hp)", "Diesel", 5045, 310, 8),
}

FUEL_FIX = {
    "Leaf Electric (EM57)": "Electric", "Ariya Electric": "Electric", "5.0 Cummins ISV V8 TD": "Diesel",
}

# (MODEL-upper, y0, y1, cc, target, evidence)  cc=None = bare/slug row
R = [
    ("350Z", 2005, 2006, None, "VQ35DE", "350Z 3.5 VQ35DE (2006 rev-up 300hp) [DB family]"),
    ("350Z", 2007, 2009, None, "VQ35HR", "350Z 3.5 HR 306hp 2007+ [DB family]"),
    ("370Z", 2009, 2020, None, "VQ37VHR", "370Z 3.7 332-350hp incl. Nismo [DB family]"),
    ("Z", 2023, 2025, None, "VR30DDTT", "Nissan Z 3.0TT 400hp [NEW VR30DDTT]"),
    ("ALTIMA", 2005, 2018, 2500, "QR25DE", "Altima 2.5 (175-182hp; VIN A 2013+) [DB family]"),
    ("ALTIMA", 2005, 2018, 3500, "VQ35DE", "Altima 3.5 (270-300hp; VIN B 2013+) [DB family]"),
    ("ALTIMA", 2025, 2025, None, "PR25DD", "2025 Altima 2.5 only (VC-T dropped) [NEW PR25DD]"),
    ("ALTIMA", 2019, 2024, 2000, "KR20DDET", "Altima 2.0T VC-Turbo 248hp (VIN A) [NEW]"),
    ("ALTIMA", 2019, 2025, 2500, "PR25DD", "Altima 2.5 new-gen DI 188hp (VIN B) [NEW PR25DD]"),
    ("ARIYA", 2023, 2025, None, "Ariya Electric", "Ariya EV only (238/389hp) [ARIYA][NEW]"),
    ("ARMADA", 2005, 2011, None, "VK56DE", "Armada 5.6 305-317hp [DB family]"),
    ("ARMADA", 2012, 2015, 5600, "VK56DE", "Armada 5.6 317hp (VIN A/B) [DB family]"),
    ("ARMADA", 2017, 2025, None, "VK56VD", "Armada 5.6 VD 390hp [DB family]"),
    ("CUBE", 2009, 2014, None, "MR18DE", "Cube 1.8 only US [DB family]"),
    ("FRONTIER", 2005, 2019, 2500, "QR25DE", "Frontier King Cab 2.5 152hp (VIN B 2012+) [DB family]"),
    ("FRONTIER", 2005, 2019, 4000, "VQ40DE", "Frontier 4.0 261hp (VIN A/D) [DB family]"),
    ("FRONTIER", 2020, 2025, None, "VQ38DD", "Frontier 3.8 VQ38DD only 2020+ 310hp [FRONTIER38][NEW]"),
    ("GT-R", 2009, 2014, None, "VR38DETT", "GT-R R35 3.8TT 485-545hp [DB family]"),
    ("JUKE", 2011, 2017, None, "MR16DDT", "Juke 1.6T 188hp (Nismo/RS same family) [DB family]"),
    ("KICKS", 2018, 2024, None, "HR16DE", "Kicks 1.6 122hp [DB family][KICKS]"),
    ("KICKS", 2025, 2025, None, "MR20DE", "Kicks 2.0 141hp (2025 new gen) [KICKS][DB family]"),
    ("LEAF", 2011, 2025, None, "Leaf Electric (EM57)", "Leaf EV only, EM57 110-147hp [NEW]"),
    ("MAXIMA", 2005, 2023, None, "VQ35DE", "Maxima 3.5 only (265-300hp) [DB family]"),
    ("MURANO", 2005, 2025, None, "VQ35DE", "Murano 3.5 only (245-260hp) [DB family]"),
    ("NV1500", 2012, 2021, None, "VQ40DE", "NV1500 4.0 only [DB family]"),
    ("NV200", 2013, 2021, None, "MR20DE", "NV200 2.0 only 131hp US [DB family]"),
    ("NV2500", 2012, 2021, 4000, "VQ40DE", "NV2500 4.0 (VIN B) [DB family]"),
    ("NV2500", 2012, 2016, 5600, "VK56DE", "NV2500 5.6 317hp (VIN A) [DB family]"),
    ("NV2500", 2017, 2021, 5600, "VK56VD", "NV2500 5.6 VD 375hp (VIN A) [DB family]"),
    ("NV3500", 2012, 2021, 4000, "VQ40DE", "NV3500 4.0 (VIN B) [DB family]"),
    ("NV3500", 2012, 2016, 5600, "VK56DE", "NV3500 5.6 317hp [DB family]"),
    ("NV3500", 2017, 2021, 5600, "VK56VD", "NV3500 5.6 VD 375hp [DB family]"),
    ("PATHFINDER", 2005, 2007, None, "VQ40DE", "Pathfinder 4.0 only [DB family]"),
    ("PATHFINDER", 2008, 2012, 4000, "VQ40DE", "Pathfinder 4.0 (VIN A 2012) [DB family]"),
    ("PATHFINDER", 2008, 2012, 5600, "VK56DE", "Pathfinder 5.6 310hp (VIN B 2012) [DB family]"),
    ("PATHFINDER", 2013, 2025, None, "VQ35DE", "Pathfinder 3.5 only 2013+ (260-284hp) [DB family]"),
    ("QUEST", 2005, 2017, None, "VQ35DE", "Quest 3.5 only (235-260hp) [DB family]"),
    ("ROGUE", 2008, 2020, None, "QR25DE", "Rogue 2.5 170hp (incl. Select) [DB family]"),
    ("ROGUE", 2021, 2021, None, "PR25DD", "2021 Rogue 2.5 only 181hp [NEW PR25DD]"),
    ("ROGUE", 2021, 2021, 2500, "PR25DD", "Rogue 2.5 (VIN A) [NEW PR25DD]"),
    ("ROGUE", 2021, 2025, 1500, "KR15DDET", "Rogue 1.5T VC-Turbo 201hp (VIN B; 2022MY) [NEW]"),
    ("ROGUE", 2022, 2025, None, "KR15DDET", "2022+ Rogue 1.5T only [NEW KR15DDET]"),
    ("SENTRA", 2005, 2006, 1800, "QG18DE", "Sentra 1.8 [DB family]"),
    ("SENTRA", 2005, 2012, 2500, "QR25DE", "Sentra SE-R / Spec-V 2.5 175-200hp [DB family]"),
    ("SENTRA", 2007, 2012, 2000, "MR20DE", "Sentra 2.0 [DB family]"),
    ("SENTRA", 2013, 2016, None, "MR18DE", "Sentra 1.8 only 2013+ 130hp [DB family]"),
    ("SENTRA", 2017, 2019, 1600, "HR16DE", "Sentra S 1.6 base 124hp [DB family]"),
    ("SENTRA", 2017, 2019, 1800, "MR18DE", "Sentra 1.8 (VIN split) [DB family]"),
    ("SENTRA", 2020, 2025, None, "MR20DE", "Sentra 2.0 only 2020+ 149hp [DB family]"),
    ("TITAN", 2012, 2015, 5600, "VK56DE", "Titan 5.6 317hp (VIN A/B) [DB family]"),
    ("TITAN", 2005, 2015, None, "VK56DE", "Titan 5.6 only (305-317hp; VIN A/B 2012+) [DB family]"),
    ("TITAN", 2016, 2019, 5000, "5.0 Cummins ISV V8 TD", "Titan XD 5.0 Cummins diesel 310hp (VIN B) [NEW]"),
    ("TITAN", 2016, 2019, 5600, "VK56VD", "Titan XD 5.6 gas 390hp (VIN A) [DB family]"),
    ("TITAN", 2020, 2024, None, "VK56VD", "Titan 5.6 VD 400hp [DB family]"),
    ("VERSA", 2009, 2012, 1600, "HR16DE", "Versa 1.6 [DB family]"),
    ("VERSA", 2009, 2012, 1800, "MR18DE", "Versa 1.8 [DB family]"),
    ("VERSA", 2013, 2025, None, "HR16DE", "Versa/Note 1.6 only 2013+ (109-122hp) [DB family]"),
    ("XTERRA", 2005, 2015, None, "VQ40DE", "Xterra 4.0 only 261hp (incl. Pro-4X) [DB family]"),
]

def decide(model, year, code):
    parts = code.replace("LEMON_NISSAN_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc = None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
    mu = model.upper()
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands:
        if cc is not None:
            return (None, f"{model} {year} {cc}cc: no cc rule", None)
        return (None, f"no rule for {model} {year} (bare)", None)
    r = cands[0]
    return (r[4], r[5], FUEL_FIX.get(r[4]))

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code FROM vehicle_variants
        WHERE car_brand='Nissan' AND engine_code LIKE 'LEMON_NISSAN%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code in rows:
        tgt, note, fuel_fix = decide(model, year, code)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"Nissan LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(16): print(f"  {c:3} {t}")
    # pre-apply: assert every target exists or is in NEW_ENGINES
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"

    if not apply:
        with open("database_enriched/csv_exports/25_lemon_batch8_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"Nissan",d[1],d[2],d[3],d[4],d[5] or "",d[6] or ""])
            for s in skips: w.writerow([s[0],"Nissan",s[1],s[2],"","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step17_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP17_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
            print(f"  created {code}")

    lemon_retired = defaultdict(list)
    for vid, model, year, old, new, note, fuel_fix in decisions:
        cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=COALESCE(?, fuel) WHERE id=?", (new, fuel_fix, vid))
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=COALESCE(engine_power_hp,
            (SELECT power_hp FROM engines WHERE engine_code=?)),
            engine_type=COALESCE(engine_type, (SELECT engine_type FROM engines WHERE engine_code=?)) WHERE id=?""", (new, new, vid))
        lemon_retired[old].append((vid, year, model))

    spec_cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_service_specs)")]
    tech_cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_technical_specs)")]

    def merge_specs(table, cols, lc, target):
        cols = [c for c in cols if c != "engine_code"]
        cur.execute(f"SELECT {','.join(cols)} FROM {table} WHERE engine_code=?", (lc,))
        src = cur.fetchone()
        if src is None: return
        if table == "engine_service_specs":
            srow = cur.execute("SELECT oil_spec_source FROM engine_service_specs WHERE engine_code=?", (lc,)).fetchone()
            if srow and srow[0] and "ESTIMATE" in srow[0].upper():
                cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (lc,)); return
        if cur.execute(f"SELECT 1 FROM {table} WHERE engine_code=?", (target,)).fetchone():
            sets = ", ".join(f"{c}=COALESCE({c}, ?)" for c in cols)
            cur.execute(f"UPDATE {table} SET {sets} WHERE engine_code=?", (*src, target))
        else:
            cur.execute(f"INSERT INTO {table} (engine_code, {','.join(cols)}) VALUES (?{',?'*len(cols)})", (target, *src))

    for lc, vids in lemon_retired.items():
        tgt = cur.execute("SELECT engine_code FROM vehicle_variants WHERE id=?", (vids[0][0],)).fetchone()[0]
        merge_specs("engine_service_specs", spec_cols, lc, tgt)
        merge_specs("engine_technical_specs", tech_cols, lc, tgt)
        cur.execute("DELETE FROM engine_service_specs WHERE engine_code=?", (lc,))
        cur.execute("DELETE FROM engine_technical_specs WHERE engine_code=?", (lc,))
        cur.execute("DELETE FROM engines WHERE engine_code=?", (lc,))

    cur.execute("""UPDATE engines SET count_variants =
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")

    with open("database_enriched/csv_exports/25_lemon_batch8_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"Nissan",d[1],d[2],d[3],d[4],d[5] or "",d[6] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_NISSAN remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_NISSAN%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
