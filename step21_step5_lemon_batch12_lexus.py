"""Step 21 (user-plan Step 5, batch 12): replace LEMON_LEXUS codes with real OEM engine codes.
322 rows, 19 models. Nearly all bare rows + trim slugs (model names encode engines: IS350/LS600H...)
+ cc/VIN rows. DB Toyota-family vocabulary reused; 4 new rows (1UZ-FE, 2UR-FXE, RZ450e EV).
Junk labels fixed: 2JZ-GE ('300'), 8AR-FTS ('2 (est.)'), 1LR-GUE, 2GR-FXE."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "UXCANDD": "https://www.caranddriver.com/lexus/ux-2023 (UX hybrid-only from 2023; UX200 dropped after 2022; 181hp system)",
    "LEXUSMHTN": "https://www.lexusofmanhattan.com/blog/2024/september/27/why-everyone-loves-the-lexus-ux-250h.htm (UX250h preferred; UX200 FWD-only discontinued 2022)",
    "DBLINKS": "DB engine links: 4GR-FSE=IS250, 3GR-FSE=GS300, 2GR-FSE=GS350, 2UR-GSE=IS-F, 3UZ-FE=LS430, 1UR-FE=GX460, 3UR-FE=LX570, 2AR-FXE=HS/ES300h, 1LR-GUE=LFA (all Lexus-linked in DB)",
}

NEW_ENGINES = {
    "1UZ-FE": ("4.0 V8 (LS400/SC400, 290hp)", "Petrol", 3969, 290, 8),
    "2UR-FXE": ("5.0 V8 Hybrid (LS600h, 438hp system)", "Hybrid", 4969, 438, 8),
    "RZ450e Electric": ("Electric motors (RZ450e, 308hp)", "Electric", None, 308, None),
}

ROW_FIXES = {
    "2JZ-GE": {"engine_type": "3.0 I6 DOHC (IS300/GS300/SC300, 215-220hp)"},
    "8AR-FTS": {"engine_type": "2.0 I4 Turbo (IS/RC/GS 200t-300, NX 200t/300; 235-241hp)", "power_hp": 241},
    "1LR-GUE": {"engine_type": "4.8 V10 (LFA, 553hp US)", "power_hp": 553},
    "2GR-FXE": {"engine_type": "3.5 V6 Hybrid (GS450h/RX450h, 295hp system)"},
    "4GR-FSE": {"engine_type": "2.5 V6 DI (IS250, 204hp)"},
}

FUEL_FIX_BY_TARGET = {
    "2UR-FXE": "Hybrid", "2ZR-FXE": "Hybrid", "2AR-FXE": "Hybrid", "2GR-FXE": "Hybrid",
    "M20A-FXS": "Hybrid", "A25A-FXS": "Hybrid", "RZ450e Electric": "Electric",
}

# (MODEL-upper, y0, y1, cc, target, evidence[, fuel_fix])  cc=None = bare/slug
R = [
    ("CT", 2011, 2017, None, "2ZR-FXE", "CT 200h 1.8 hybrid 134hp (only CT) [DB family]"),
    ("ES", 2000, 2003, None, "1MZ-FE", "ES300 3.0 only (XX10) [DB family]"),
    ("ES", 2004, 2006, None, "3MZ-FE", "ES330 3.3 218hp US (DB 211 Euro) [DB family]"),
    ("ES", 2007, 2015, None, "2GR-FE", "ES350 3.5 268-272hp (300h minority 2013+) [DB family]"),
    ("GS", 2000, 2005, None, "2JZ-GE", "GS300 3.0 I6 majority (GS400/430 minority) [ROW_FIX 2JZ-GE]"),
    ("GS", 2006, 2006, None, "3GR-FSE", "GS300 3.5 DI 245hp majority (GS430 minority) [DB family]"),
    ("GS", 2007, 2011, None, "2GR-FSE", "GS350 3.5 DI 305hp majority (300/460/450h minorities) [DB family]"),
    ("GS", 2013, 2020, None, "2GR-FSE", "GS350 3.5 DI 306-311hp majority (300/450h minorities) [DB family]"),
    ("GX", 2003, 2009, None, "2UZ-FE", "GX470 4.7 only [DB family]"),
    ("GX", 2010, 2023, None, "1UR-FE", "GX460 4.6 only 301hp [DB family]"),
    ("GX", 2024, 2025, None, "T24A-FTS", "GX550 2.4T i-FORCE MAX hybrid-only 349hp [NEW-era row]", "Hybrid"),
    ("HS", 2010, 2012, None, "2AR-FXE", "HS 250h 2.5 hybrid 187hp only [DB family]"),
    ("IS", 2001, 2005, None, "2JZ-GE", "IS300 3.0 I6 only US [ROW_FIX 2JZ-GE]"),
    ("IS", 2006, 2015, None, "4GR-FSE", "IS250 2.5 DI 204hp majority (IS350 minority) [DB family]"),
    ("IS", 2018, 2025, 2000, "8AR-FTS", "IS300 2.0T 241hp (VIN A) [ROW_FIX 8AR-FTS]"),
    ("IS", 2018, 2025, 3500, "2GR-FSE", "IS350 3.5 DI 306-311hp (VIN 8) [DB family]"),
    ("LC", 2018, 2025, None, "2UR-GSE", "LC500 5.0 V8 471hp majority (500h minority) [DB family]"),
    ("LFA", 2012, 2012, None, "1LR-GUE", "LFA 4.8 V10 553hp [ROW_FIX 1LR-GUE]"),
    ("LS", 2000, 2000, None, "1UZ-FE", "LS400 4.0 290hp (last year) [NEW 1UZ-FE]"),
    ("LS", 2001, 2006, None, "3UZ-FE", "LS430 4.3 290hp only [DB family]"),
    ("LS", 2007, 2017, None, "1UR-FE", "LS460 4.6 380-386hp majority (600h minority) [DB family]"),
    ("LS", 2018, 2025, None, "V35A-FTS", "LS500 3.4TT 416hp majority (500h minority; same V35A family as Tundra) [DB family]"),
    ("LX", 2000, 2007, None, "2UZ-FE", "LX470 4.7 only [DB family]"),
    ("LX", 2008, 2021, None, "3UR-FE", "LX570 5.7 383hp only [DB family]"),
    ("LX", 2022, 2025, None, "V35A-FTS", "LX600 3.4TT 409hp only US [DB family]"),
    ("NX", 2016, 2017, None, "8AR-FTS", "NX 200t 2.0T 235hp gas (300h captured by 2500cc rows) [ROW_FIX 8AR-FTS]"),
    ("NX", 2018, 2021, None, "8AR-FTS", "NX300 2.0T 235hp majority (300h minority) [ROW_FIX 8AR-FTS]"),
    ("NX", 2022, 2025, None, "T24A-FTS", "NX350 2.4T 275hp majority (350h/450h minorities) [DB family]"),
    ("NX", 2016, 2016, 2500, "2AR-FXE", "NX300h 2.5 hybrid 194hp (VIN J/W) [DB family]"),
    ("RC", 2018, 2025, 2000, "8AR-FTS", "RC300 2.0T 241hp (VIN A) [ROW_FIX 8AR-FTS]"),
    ("RC", 2018, 2025, 3500, "2GR-FSE", "RC350 3.5 DI 306-311hp (VIN 8) [DB family]"),
    ("RX", 2000, 2003, None, "1MZ-FE", "RX300 3.0 220hp [DB family]"),
    ("RX", 2004, 2006, None, "3MZ-FE", "RX330 3.3 230hp (400h minority) [DB family]"),
    ("RX", 2007, 2015, None, "2GR-FE", "RX350 3.5 270-275hp (450h minority) [DB family]"),
    ("RX", 2016, 2022, None, "2GR-FKS", "RX350 3.5 D-4S 295-300hp (450h minority) [DB family]"),
    ("RX", 2023, 2025, None, "T24A-FTS", "RX350 2.4T 275hp majority (350h/500h minorities) [DB family]"),
    ("RX", 2012, 2015, 3500, "2GR-FE", "RX350 3.5 (VIN B/C) [DB family]"),
    ("RX", 2016, 2016, 3500, "2GR-FKS", "RX350 3.5 D-4S (VIN F/G) [DB family]"),
    ("RX", 2023, 2025, 2400, "T24A-FTS", "RX350 2.4T 275hp (VIN A/H; RX500h HEV minority same engine) [DB family]"),
    ("RZ", 2023, 2025, None, "RZ450e Electric", "RZ450e EV only [NEW]", "Electric"),
    ("SC", 2002, 2010, None, "3UZ-FE", "SC430 4.3 convertible only [DB family]"),
    ("TX", 2024, 2025, None, "T24A-FTS", "TX350 2.4T majority (500h/550h minorities) [DB family]"),
    ("UX", 2019, 2022, None, "M20A-FXS", "UX250h 2.0 hybrid 181hp majority (UX200 gas minority) [UXCANDD][LEXUSMHTN]", "Hybrid"),
    ("UX", 2023, 2025, 2000, "M20A-FXS", "UX hybrid-only from 2023, 181hp system (VIN 6/9/B/C) [UXCANDD]", "Hybrid"),
]

def decide(model, year, code, fuel):
    parts = code.replace("LEMON_LEXUS_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc = None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
    mu = model.upper()
    up = code.upper()
    # trim-slug special cases (name encodes the powertrain)
    if "300H" in up or "450H" in up or "600H" in up:  # ES300H / NX300H / GS450H / LS600H
        if mu == "ES": return ("2AR-FXE", "ES300h 2.5 hybrid 200hp [DB family]", "Hybrid")
        if mu == "NX": return ("2AR-FXE", "NX300h 2.5 hybrid 194hp [DB family]", "Hybrid")
        if mu == "GS": return ("2GR-FXE", "GS450h 3.5 hybrid 295hp [DB family]", "Hybrid")
        if mu == "LS": return ("2UR-FXE", "LS600h 5.0 hybrid 438hp [NEW 2UR-FXE]", "Hybrid")
    if mu == "IS" and "IS250" in up: return ("4GR-FSE", "IS250 2.5 DI 204hp [DB family]", None)
    if mu == "IS" and "IS350" in up: return ("2GR-FSE", "IS350 3.5 DI 306hp [DB family]", None)
    if mu == "GS" and "GS350" in up: return ("2GR-FSE", "GS350 3.5 DI 306hp [DB family]", None)
    if mu == "LS" and "LS460" in up: return ("1UR-FE", "LS460 4.6 386hp [DB family]", None)
    if mu == "RC" and "RCF" in up: return ("2UR-GSE", "RC F 5.0 V8 467hp [DB family]", None)
    if mu == "RC" and "RC350" in up: return ("2GR-FSE", "RC350 3.5 DI 306hp [DB family]", None)
    if mu == "NX" and "NX200T" in up: return ("8AR-FTS", "NX 200t 2.0T 235hp [ROW_FIX 8AR-FTS]", None)
    if mu == "RX" and "RX350" in up: return ("2GR-FE", "RX350 3.5 270hp [DB family]", None)
    if mu == "GX" and "GX460" in up: return ("1UR-FE", "GX460 4.6 301hp [DB family]", None)
    if mu == "LX" and "LX570" in up: return ("3UR-FE", "LX570 5.7 383hp [DB family]", None)
    if mu == "ES" and "ES350" in up: return ("2GR-FE", "ES350 3.5 268hp [DB family]", None)
    # skip known-ambiguous bare rows
    if mu == "ES" and year >= 2016: return (None, "ES 2016+: 350 vs 300h (vs 250) unknown", None)
    if mu == "IS" and 2016 <= year <= 2017: return (None, "IS 2016-17: 200t vs 350 unknown", None)
    if mu == "IS" and year >= 2018 and cc is None: return (None, "IS 2018+ bare (cc rows carry split)", None)
    if mu == "RC" and year >= 2016 and cc is None: return (None, "RC bare 2016+: 300 vs 350 (F) unknown", None)
    if mu == "SC" and year <= 2001: return (None, "SC 2000-2001: SC300 I6 vs SC400 V8 unknown", None)
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands:
        if cc is not None:
            return (None, f"{model} {year} {cc}cc: no rule", None)
        return (None, f"no rule for {model} {year} (bare)", None)
    r = cands[0]
    fuel_fix = r[6] if len(r) > 6 else FUEL_FIX_BY_TARGET.get(r[4])
    return (r[4], r[5], fuel_fix)

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == 4946, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 4946 (workspace rewind?)"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Lexus' AND engine_code LIKE 'LEMON_LEXUS%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        tgt, note, fuel_fix = decide(model, year, code, fuel)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"Lexus LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(16): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter(d[6] for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"

    if not apply:
        with open("database_enriched/csv_exports/29_lemon_batch12_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"Lexus",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Lexus",s[1],s[2],"","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step21_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP21_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
            print(f"  created {code}")
    for code, fixes in ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  row-fix {code}")

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

    with open("database_enriched/csv_exports/29_lemon_batch12_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"Lexus",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_LEXUS remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_LEXUS%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
