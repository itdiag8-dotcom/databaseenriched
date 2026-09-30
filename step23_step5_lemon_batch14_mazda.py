"""Step 23 (user-plan Step 5, batch 14): replace LEMON_MAZDA codes with real OEM engine codes.
303 rows, 27 models. Signals: cc + VIN + fuel column (Tribute hybrids) + year.
Rebadge twins mapped to Ford-family rows (Tribute=Escape: Zetec/Duratec/Hybrid; B-Series=Ranger).
New: MZR NA family, Skyactiv-G/D, BP Miata, KJ-ZEM Miller, Duratec 37, e-Skyactiv 3.3T/PHEV, MX-30 EV.
CX-50 Hybrid = Toyota A25A-FXS system (cross-brand, verified)."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "MAZDAVIN": "Mazda US lineup knowledge + lemon fuel column (Tribute Hybrid rows flagged)",
    "CX50TOY": "Mazda CX-50 Hybrid uses Toyota's hybrid system (A25A-FXS 2.5, 219hp system)",
    "DBLINKS": "DB links: L3-VE turbo (MPS), L5-VE 2.5 MZR, ZM/FP/FS Protege, KL 2.5 V6, 13B-MSP RX-8, 2.0 Zetec + 2.5 Duratec + 2.5 Hybrid + 3.0 V6 (Escape), 2.3 16v + 3.0/4.0 V6 + 2.5 Lima (Ranger)",
    "TRIBUTE": "Mazda Tribute = Ford Escape rebadge (2.0 Zetec 01-04, 2.3 MZR 05-08, 2.5 Duratec 09-11, 3.0 V6, Atkinson Hybrid 08-11); B-Series = Ford Ranger (2.3 DOHC, 2.5 Lima, 3.0 Vulcan, 4.0 Cologne)",
}

NEW_ENGINES = {
    "1.5 MZR (Mazda2)": ("1.5 I4 MZR (Mazda2 DE, 100hp)", "Petrol", 1498, 100, 4),
    "2.0 MZR (LF)": ("2.0 I4 MZR (Mazda3/6/Miata NC, 148-167hp)", "Petrol", 1999, 148, 4),
    "2.3 MZR NA (L3)": ("2.3 I4 MZR (Mazda3/Mazda5/Tribute, 153-160hp)", "Petrol", 2260, 153, 4),
    "Skyactiv-G 2.0 (PE)": ("2.0 I4 Skyactiv-G (Mazda3/CX-3/CX-5/Miata ND, 146-181hp)", "Petrol", 1998, 155, 4),
    "Skyactiv-G 2.5 (PY)": ("2.5 I4 Skyactiv-G (184-187hp NA; 227-250hp turbo)", "Petrol", 2488, 187, 4),
    "2.2 Skyactiv-D (CX-5)": ("2.2 I4 Skyactiv-D turbodiesel (CX-5 US, 168hp)", "Diesel", 2191, 168, 4),
    "1.8 BP (Miata NB)": ("1.8 I4 BP (Miata NB, 140-142hp)", "Petrol", 1839, 142, 4),
    "KJ-ZEM 2.3 Miller SC (Millenia S)": ("2.3 V6 Miller-cycle supercharged (Millenia S, 210hp)", "Petrol", 2255, 210, 6),
    "2.3 I4 Atkinson Hybrid (Escape/Tribute)": ("2.3 I4 Atkinson + e-motor (Escape/Tribute Hybrid, 153hp system)", "Hybrid", 2261, 153, 4),
    "3.7 V6 Duratec 37 (MZI)": ("3.7 V6 (Mazda6 09-13/CX-9 07-15, 272-274hp)", "Petrol", 3726, 273, 6),
    "2.5 PHEV e-Skyactiv": ("2.5 I4 + motors PHEV (CX-70/CX-90, 323hp system)", "Hybrid", 2488, 323, 4),
    "3.3T I6 e-Skyactiv G": ("3.3 I6 Turbo (CX-70/CX-90, 340-390hp)", "Petrol", 3283, 340, 6),
    "MX-30 Electric": ("Electric motor (MX-30, 143hp)", "Electric", None, 143, None),
}

ROW_FIXES = {
    "L3-VE": {"engine_type": "2.3 DISI Turbo (Speed3/Speed6/CX-7, 244-263hp)", "power_hp": 263},
    "FS": {"engine_type": "2.0 I4 FS (Protege/626/Protege5, US 130hp)", "power_hp": 130},
    "13B-MSP": {"engine_type": "1.3 Renesis rotary (RX-8, 197-238hp US)", "power_hp": 212},
    "3.0 V6": {"engine_type": "3.0 V6 (Ford Duratec 30: Escape/MPV/Mazda6; Vulcan OHV: Ranger/B3000)"},
    "L5-VE": {"engine_type": "2.5 I4 MZR (Mazda3/5/6, CX-7/CX-9, 157-170hp)"},
}

FUEL_FIX_BY_TARGET = {
    "2.3 I4 Atkinson Hybrid (Escape/Tribute)": "Hybrid", "2.5 I4 Hybrid": "Hybrid",
    "2.2 Skyactiv-D (CX-5)": "Diesel", "2.5 PHEV e-Skyactiv": "Hybrid",
    "MX-30 Electric": "Electric", "A25A-FXS": "Hybrid",
}

# (MODEL-upper, y0, y1, cc, target, evidence[, fuel_fix])  cc=None = bare/slug
R = [
    ("2", 2011, 2013, 1500, "1.5 MZR (Mazda2)", "Mazda2 1.5 MZR 100hp (VIN Y/Z) [NEW]"),
    ("2", 2011, 2011, None, "1.5 MZR (Mazda2)", "Mazda2 1.5 only US [NEW]"),
    ("3", 2004, 2009, None, "2.0 MZR (LF)", "Mazda3 BK 2.0 majority (2.3/Speed3 minority) [NEW]"),
    ("3", 2010, 2011, 2000, "2.0 MZR (LF)", "Mazda3 2.0 MZR 148hp [NEW]"),
    ("3", 2010, 2013, 2300, "L3-VE", "Mazdaspeed3 2.3 DISI T 263hp (VIN 3/4) [ROW_FIX L3-VE]"),
    ("3", 2012, 2013, 2000, "Skyactiv-G 2.0 (PE)", "Mazda3 Skyactiv 2.0 155hp (VIN 7/8/F/G/P; 2.0 MZR minority) [NEW]"),
    ("3", 2014, 2022, 2000, "Skyactiv-G 2.0 (PE)", "Mazda3 2.0 Skyactiv 155hp (VIN 7) [NEW]"),
    ("3", 2010, 2013, 2500, "L5-VE", "Mazda3 2.5 MZR 167hp (VIN 5/6/9) [ROW_FIX L5-VE]"),
    ("3", 2014, 2022, 2500, "Skyactiv-G 2.5 (PY)", "Mazda3 2.5 Skyactiv 184hp (VIN 3) [NEW]"),
    ("3", 2019, 2025, 2500, "Skyactiv-G 2.5 (PY)", "Mazda3 2.5 (186hp NA / 250hp turbo, VIN L/M same family) [NEW]"),
    ("3", 2023, 2025, None, "Skyactiv-G 2.5 (PY)", "Mazda3 2.5 only 2023+ US (2.0 dropped) [NEW]"),
    ("5", 2006, 2010, None, "2.3 MZR NA (L3)", "Mazda5 2.3 MZR 153hp only [NEW]"),
    ("5", 2012, 2015, None, "L5-VE", "Mazda5 2.5 MZR 157hp only (incl. trims) [ROW_FIX]"),
    ("6", 2003, 2008, 2300, "2.3 MZR NA (L3)", "Mazda6 2.3 MZR 160hp [NEW]"),
    ("6", 2003, 2008, 3000, "3.0 V6", "Mazda6 3.0 V6 Duratec 30 220hp [DB family, Escape-linked]"),
    ("6", 2009, 2013, 2500, "L5-VE", "Mazda6 2.5 MZR 170hp [ROW_FIX]"),
    ("6", 2009, 2013, 3700, "3.7 V6 Duratec 37 (MZI)", "Mazda6 3.7 V6 272hp [NEW]"),
    ("6", 2014, 2021, 2500, "Skyactiv-G 2.5 (PY)", "Mazda6 2.5 Skyactiv (184-187 NA / 227-250 turbo, VIN 5/6/M same family) [NEW]"),
    ("6", 2016, 2020, None, "Skyactiv-G 2.5 (PY)", "Mazda6 2.5 majority (2.5T GT minority) [NEW]"),
    ("626", 2000, 2002, 2000, "FS", "626 2.0 130hp [ROW_FIX FS]"),
    ("626", 2000, 2002, 2500, "KL", "626 2.5 V6 165hp [DB family]"),
    ("B2300", 2001, 2009, None, "2.3 16v", "B2300 = Ranger 2.3 DOHC Duratec 143hp [DB Ranger-linked][TRIBUTE]"),
    ("B2500", 2000, 2001, None, "2.5 OHC (Lima)", "B2500 = Ranger 2.5 Lima 119hp [DB Ranger-linked][TRIBUTE]"),
    ("B3000", 2000, 2007, None, "3.0 V6", "B3000 = Ranger 3.0 Vulcan OHV 150hp [DB Ranger-linked][TRIBUTE]"),
    ("B4000", 2000, 2009, None, "4.0 V6", "B4000 = Ranger 4.0 Cologne SOHC 160-207hp [DB Ranger-linked][TRIBUTE]"),
    ("CX-3", 2016, 2021, None, "Skyactiv-G 2.0 (PE)", "CX-3 2.0 Skyactiv 146hp only [NEW]"),
    ("CX-30", 2020, 2025, 2500, "Skyactiv-G 2.5 (PY)", "CX-30 2.5 (NA / turbo, VIN L/M same family) [NEW]"),
    ("CX-30", 2020, 2025, None, "Skyactiv-G 2.5 (PY)", "CX-30 2.5 only US [NEW]"),
    ("CX-5", 2013, 2013, None, "Skyactiv-G 2.5 (PY)", "CX-5 2.5 majority (2.0 base minority) [NEW]"),
    ("CX-5", 2014, 2018, 2000, "Skyactiv-G 2.0 (PE)", "CX-5 2.0 (VIN E) 155hp [NEW]"),
    ("CX-5", 2014, 2025, 2500, "Skyactiv-G 2.5 (PY)", "CX-5 2.5 (NA / turbo, VIN Y/L/M same family) [NEW]"),
    ("CX-5", 2017, 2018, None, "Skyactiv-G 2.5 (PY)", "CX-5 2.5 majority (2.0 base minority) [NEW]"),
    ("CX-5", 2019, 2019, 2200, "2.2 Skyactiv-D (CX-5)", "CX-5 2.2 Skyactiv-D diesel 168hp (VIN 2; rare US offering) [NEW]", "Diesel"),
    ("CX-50", 2023, 2024, None, "Skyactiv-G 2.5 (PY)", "CX-50 2.5 (NA / turbo) [NEW]"),
    ("CX-50", 2025, 2025, None, "A25A-FXS", "CX-50 Hybrid 2025 = Toyota A25A-FXS hybrid system 219hp [CX50TOY]", "Hybrid"),
    ("CX-7", 2007, 2009, None, "L3-VE", "CX-7 2.3T DISI 244hp only (launch engine) [ROW_FIX L3-VE]"),
    ("CX-7", 2010, 2012, 2300, "L3-VE", "CX-7 2.3T (VIN 3/L) [ROW_FIX L3-VE]"),
    ("CX-7", 2010, 2012, 2500, "L5-VE", "CX-7 2.5 MZR NA 161hp (VIN 5/M) [ROW_FIX]"),
    ("CX-70", 2025, 2025, 2500, "2.5 PHEV e-Skyactiv", "CX-70 PHEV 2.5 323hp system [NEW]", "Hybrid"),
    ("CX-70", 2025, 2025, 3300, "3.3T I6 e-Skyactiv G", "CX-70 3.3T I6 340/390hp [NEW]"),
    ("CX-9", 2007, 2011, None, "3.7 V6 Duratec 37 (MZI)", "CX-9 3.7 V6 273hp only [NEW]"),
    ("CX-9", 2012, 2015, 3700, "3.7 V6 Duratec 37 (MZI)", "CX-9 3.7 V6 274hp (VIN A/V) [NEW]"),
    ("CX-9", 2016, 2023, None, "Skyactiv-G 2.5 (PY)", "CX-9 2.5T 227-250hp only 2016+ [NEW]"),
    ("CX-90", 2024, 2025, 2500, "2.5 PHEV e-Skyactiv", "CX-90 PHEV 2.5 323hp system [NEW]", "Hybrid"),
    ("CX-90", 2024, 2025, 3300, "3.3T I6 e-Skyactiv G", "CX-90 3.3T I6 340/390hp [NEW]"),
    ("MPV", 2000, 2002, None, "KL", "MPV 2.5 V6 165hp [DB family]"),
    ("MPV", 2003, 2006, None, "3.0 V6", "MPV 3.0 V6 Duratec 30 200-220hp [DB family, Escape-linked]"),
    ("MX-30", 2022, 2023, None, "MX-30 Electric", "MX-30 EV only (CA market) [NEW]", "Electric"),
    ("MX-5", 2000, 2005, None, "1.8 BP (Miata NB)", "Miata NB 1.8 BP 140-142hp [NEW]"),
    ("MX-5", 2006, 2015, None, "2.0 MZR (LF)", "Miata NC 2.0 MZR 166-167hp (incl. 2015 trims) [NEW]"),
    ("MX-5", 2016, 2025, None, "Skyactiv-G 2.0 (PE)", "Miata ND 2.0 Skyactiv 155/181hp [NEW]"),
    ("MILLENIA", 2000, 2002, 2300, "KJ-ZEM 2.3 Miller SC (Millenia S)", "Millenia S 2.3 Miller supercharged 210hp [NEW]"),
    ("MILLENIA", 2000, 2002, 2500, "KL", "Millenia 2.5 V6 170hp [DB family]"),
    ("PROTEGE", 2000, 2001, 1600, "ZM", "Protege 1.6 105hp US (DB 98 Euro) [DB family]"),
    ("PROTEGE", 2000, 2000, 1800, "FP", "Protege 1.8 122hp [DB family]"),
    ("PROTEGE", 2001, 2003, 2000, "FS", "Protege 2.0 130hp [ROW_FIX FS]"),
    ("PROTEGE", 2002, 2003, None, "FS", "Protege 2.0 majority [ROW_FIX FS]"),
    ("PROTEGE5", 2002, 2003, None, "FS", "Protege5 2.0 130hp [ROW_FIX FS]"),
    ("RX-8", 2004, 2011, None, "13B-MSP", "RX-8 1.3 Renesis rotary 197-238hp [DB family][ROW_FIX label]"),
    ("TRIBUTE", 2001, 2004, 2000, "2.0 Zetec", "Tribute 2.0 = Escape Zetec 130hp [DB family][TRIBUTE]"),
    ("TRIBUTE", 2001, 2011, 3000, "3.0 V6", "Tribute 3.0 V6 Duratec 30 200-240hp [DB family, Escape-linked]"),
    ("TRIBUTE", 2005, 2007, 2300, "2.3 MZR NA (L3)", "Tribute 2.3 MZR 153hp [NEW][TRIBUTE]"),
    ("TRIBUTE", 2008, 2008, 2300, "2.3 I4 Atkinson Hybrid (Escape/Tribute)", "Tribute Hybrid 2008 = Escape Hybrid 2.3 Atkinson 153hp system [NEW][TRIBUTE]", "Hybrid"),
    ("TRIBUTE", 2009, 2011, 2500, "2.5 I4 Hybrid", "Tribute Hybrid 2009-11 = Escape Hybrid 2.5 153hp system [DB Escape-linked][TRIBUTE]", "Hybrid"),
]

def decide(model, year, code, fuel):
    parts = code.replace("LEMON_MAZDA_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc = None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
    mu = model.upper()
    # Tribute hybrid handling is in rules (fuel rows only exist as hybrid years)
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
    assert base_lemon == 4344, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 4344 (workspace rewind?)"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Mazda' AND engine_code LIKE 'LEMON_MAZDA%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        tgt, note, fuel_fix = decide(model, year, code, fuel)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"Mazda LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(16): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter(d[6] for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"

    if not apply:
        with open("database_enriched/csv_exports/31_lemon_batch14_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"Mazda",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Mazda",s[1],s[2],"","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step23_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP23_VERIFIED')""",
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

    with open("database_enriched/csv_exports/31_lemon_batch14_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"Mazda",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_MAZDA remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_MAZDA%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
