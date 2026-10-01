"""Step 22 (user-plan Step 5, batch 13): replace LEMON_HONDA codes with real OEM engine codes.
312 rows, 19 models. Signals: cc + VIN + lemon fuel column (Accord/CR-V/Civic hybrid splits) + slugs.
DB Honda codes reused (junk labels fixed: J35s 'CORVETTE'/'CROWN ROYAL', K24A1, R18Z4 'LUV'...).
New: D16/D17, B20Z2, R18Z1/R20Z1, K24W/K24Z9/K20C4, J30A1, H22A4, F20C/F22C1, L15B2, Isuzu 6VD1
(Passport = Rodeo rebadge), i-MMD/IMA hybrid rows, Clarity PHEV, J35Y Earth Dreams."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "MRR20": "https://www.motorreviewer.com/engine.php?engine_id=165 (R20Z1 = 155hp Civic/Accord 2.0)",
    "MRK20C": "https://www.motorreviewer.com/engine.php?engine_id=137 (K20C4 = 252hp 2018+ Accord 2.0T; K20C1 = 306hp Type R)",
    "PROXY": "https://www.proxyparts.com/wiki/engine-codes/make/honda/model/civic/ (Civic codes D17A2, LDA2, R18A2...)",
    "DBLINKS": "DB engine links + displacement fingerprints (F23A 2.3, K24 family, J35 family, R18A1, L15A1/A7, LDA1 1.3 IMA Hybrid)",
    "PASSPORT": "Honda Passport 1998-2002 = Isuzu Rodeo rebadge, 3.2 V6 6VD1 205hp",
}

NEW_ENGINES = {
    "D16Y8": ("1.6 SOHC VTEC (Civic 2000, 127hp)", "Petrol", 1590, 127, 4),
    "D17A2": ("1.7 SOHC i-VTEC (Civic 2001-05, 117hp)", "Petrol", 1668, 117, 4),
    "B20Z2": ("2.0 DOHC (CR-V 2000-01, 146hp)", "Petrol", 1973, 146, 4),
    "R18Z1": ("1.8 SOHC i-VTEC (Civic 2012-15, 143hp)", "Petrol", 1799, 143, 4),
    "R20Z1": ("2.0 SOHC i-VTEC (Civic 2016+/HR-V 2023+, 155-158hp)", "Petrol", 1997, 158, 4),
    "K24W": ("2.4 i-VTEC Earth Dreams (Accord/CR-V 2013-17, 185-189hp)", "Petrol", 2356, 189, 4),
    "K24Z9": ("2.4 i-VTEC (CR-V 2012-16, 185hp)", "Petrol", 2354, 185, 4),
    "K20C4": ("2.0 VTEC Turbo (Accord 2018-22, 252hp)", "Petrol", 1996, 252, 4),
    "J30A1": ("3.0 V6 i-VTEC (Accord 2000-02, 200hp)", "Petrol", 2997, 200, 6),
    "H22A4": ("2.2 DOHC VTEC (Prelude, 195hp)", "Petrol", 2157, 195, 4),
    "F20C1": ("2.0 DOHC VTEC (S2000 2000-03, 240hp)", "Petrol", 1997, 240, 4),
    "F22C1": ("2.2 DOHC VTEC (S2000 2004-09, 237hp)", "Petrol", 2157, 237, 4),
    "L15B2": ("1.5 SOHC i-VTEC (Fit 2015-20, 130hp)", "Petrol", 1496, 130, 4),
    "Isuzu 6VD1 3.2 V6 (Passport)": ("3.2 V6 SOHC (Isuzu Rodeo/Passport, 205hp)", "Petrol", 3165, 205, 6),
    "Honda 2.0 i-MMD Hybrid": ("2.0 Atkinson i-VTEC + motors (Accord/CR-V/Civic e:HEV, 196-212hp system)", "Hybrid", 1993, 204, 4),
    "Honda 1.5 i-MMD Hybrid": ("1.5 Atkinson i-VTEC + motors (Insight 2019-22, 151hp system)", "Hybrid", 1496, 151, 4),
    "CR-Z 1.5 IMA Hybrid": ("1.5 i-VTEC + IMA (CR-Z, 130hp system)", "Hybrid", 1496, 130, 4),
    "Civic Hybrid 1.5 IMA": ("1.5 SOHC i-VTEC + IMA (Civic Hybrid 2012-15, 110hp system)", "Hybrid", 1497, 110, 4),
    "Insight 1.0 IMA (ECA1)": ("1.0 3-cyl + IMA (Insight gen1 2000-01, 73hp system)", "Hybrid", 995, 71, 3),
    "Insight 1.3 IMA (gen1)": ("1.3 i-DSI + IMA (Insight gen1 2002-06, 93hp system)", "Hybrid", 1339, 88, 4),
    "Clarity PHEV (1.5 + motor)": ("1.5 Atkinson + motors PHEV (Clarity, 212hp system)", "Hybrid", 1496, 212, 4),
    "J35Y (Earth Dreams 3.5 V6)": ("3.5 V6 Earth Dreams DI (Pilot/Ridgeline/Odyssey/Passport 2016+, 280hp)", "Petrol", 3471, 280, 6),
}

ROW_FIXES = {
    "J30A4": {"engine_type": "3.0 V6 i-VTEC (Accord 2003-07, 244hp)"},
    "K24A1": {"engine_type": "2.4 i-VTEC (CR-V 2002-06/Element, 160hp)"},
    "K24A4": {"engine_type": "2.4 i-VTEC (Accord 2003-07, 160hp)", "power_hp": 160},
    "J35A4": {"engine_type": "3.5 V6 i-VTEC (Odyssey/Pilot 2000-05, 210-240hp)", "power_hp": 240},
    "J35A6": {"engine_type": "3.5 V6 i-VTEC (Odyssey/Pilot 2006-10, 244-250hp)", "power_hp": 244},
    "J35A9": {"engine_type": "3.5 V6 i-VTEC (Pilot/Ridgeline 2009-15, 250hp)", "power_hp": 250},
    "J35A8": {"engine_type": "3.5 V6 i-VTEC (Odyssey 2011-17, 248hp)", "power_hp": 248},
    "J35Z2": {"engine_type": "3.5 V6 i-VTEC (Accord/Crosstour 2008-12, 271-274hp)", "power_hp": 271},
    "J35Y1": {"engine_type": "3.5 V6 Earth Dreams (Accord/Crosstour 2013-17, 278hp)", "power_hp": 278},
    "K24Z7": {"engine_type": "2.4 i-VTEC (Civic Si 2012-15, 205hp)", "power_hp": 205},
    "R18Z4": {"engine_type": "1.8 SOHC i-VTEC (HR-V 2016-22, 141hp)"},
    "L15B7": {"engine_type": "1.5 VTEC Turbo (Civic/CR-V/Accord 2016+, 174-192hp)", "power_hp": 190},
    "LDA1": {"engine_type": "1.3 i-VTEC IMA (Insight 2010-14 / Civic Hybrid, 98hp system)"},
}

FUEL_FIX_BY_TARGET = {
    "Honda 2.0 i-MMD Hybrid": "Hybrid", "Honda 1.5 i-MMD Hybrid": "Hybrid",
    "CR-Z 1.5 IMA Hybrid": "Hybrid", "Civic Hybrid 1.5 IMA": "Hybrid",
    "Insight 1.0 IMA (ECA1)": "Hybrid", "Insight 1.3 IMA (gen1)": "Hybrid",
    "Clarity PHEV (1.5 + motor)": "Hybrid", "LDA1": "Hybrid",
}

# (MODEL-upper, y0, y1, cc, target, evidence[, fuel_fix])  cc=None = bare/slug/V rows
R = [
    ("ACCORD", 2000, 2001, 2300, "F23A", "Accord 2.3 VTEC 135-150hp [DB family]"),
    ("ACCORD", 2000, 2001, 3000, "J30A1", "Accord V6 3.0 200hp [NEW]"),
    ("ACCORD", 2002, 2007, None, "K24A4", "Accord 2.4 160hp majority (3.0 minority) [ROW_FIX]"),
    ("ACCORD", 2008, 2011, None, "K24Z3", "Accord 2.4 190-200hp majority (3.5 minority) [DB family]"),
    ("ACCORD", 2012, 2012, None, "K24Z3", "Accord 2012 2.4 majority (3.5 minority) [DB family]"),
    ("ACCORD", 2013, 2017, None, "K24W", "Accord 2.4 Earth Dreams 185-189hp majority [NEW K24W]"),
    ("ACCORD", 2012, 2012, 2400, "K24Z3", "Accord 2.4 190-200hp (VIN CP2/CS1) [DB family]"),
    ("ACCORD", 2012, 2012, 3500, "J35Z2", "Accord V6 271hp (VIN CP3) [ROW_FIX]"),
    ("ACCORD", 2013, 2017, 2400, "K24W", "Accord 2.4 Earth Dreams (VIN 1/2) [NEW K24W]"),
    ("ACCORD", 2013, 2017, 3500, "J35Y1", "Accord V6 278hp (VIN 2/3) [ROW_FIX J35Y1]"),
    ("ACCORD", 2014, 2017, 2000, "Honda 2.0 i-MMD Hybrid", "Accord Hybrid 2.0 i-MMD 196-214hp system [NEW]", "Hybrid"),
    ("ACCORD", 2018, 2018, 2000, "K20C4", "Accord 2.0T 252hp (petrol row; Hybrid has own fuel flag) [MRK20C][NEW]"),
    ("ACCORD", 2019, 2025, 2000, "Honda 2.0 i-MMD Hybrid", "Accord Hybrid 2.0 i-MMD 204hp [NEW]", "Hybrid"),
    ("ACCORD", 2018, 2025, 1500, "L15B7", "Accord 1.5T 192hp [ROW_FIX L15B7]"),
    ("CR-V", 2000, 2001, None, "B20Z2", "CR-V 2.0 B20 146hp [NEW]"),
    ("CR-V", 2002, 2006, None, "K24A1", "CR-V 2.4 160hp [ROW_FIX K24A1]"),
    ("CR-V", 2007, 2011, None, "K24Z1", "CR-V 2.4 166-180hp [DB family]"),
    ("CR-V", 2012, 2016, 2400, "K24Z9", "CR-V 2.4 185hp (VIN 3/4) [NEW K24Z9]"),
    ("CR-V", 2012, 2016, None, "K24Z9", "CR-V 2.4 185hp (incl. 2015 trims) [NEW K24Z9]"),
    ("CR-V", 2017, 2018, 1500, "L15B7", "CR-V 1.5T 190hp [ROW_FIX L15B7]"),
    ("CR-V", 2020, 2025, 1500, "L15B7", "CR-V 1.5T 190hp [ROW_FIX L15B7]"),
    ("CR-V", 2020, 2025, 2000, "Honda 2.0 i-MMD Hybrid", "CR-V Hybrid 2.0 i-MMD 212hp system [NEW]", "Hybrid"),
    ("CR-Z", 2011, 2016, None, "CR-Z 1.5 IMA Hybrid", "CR-Z 1.5 IMA 130hp only [NEW]", "Hybrid"),
    ("CR-Z", 2014, 2014, 1500, "CR-Z 1.5 IMA Hybrid", "CR-Z 1.5 IMA (VIN 1) [NEW]", "Hybrid"),
    ("CIVIC", 2000, 2000, None, "D16Y8", "Civic 1.6 127hp [NEW]"),
    ("CIVIC", 2001, 2005, None, "D17A2", "Civic 1.7 117hp [PROXY][NEW]"),
    ("CIVIC", 2006, 2011, None, "R18A1", "Civic 1.8 140hp [DB family]"),
    ("CIVIC", 2012, 2012, None, "R18Z1", "Civic 1.8 143hp [NEW]"),
    ("CIVIC", 2013, 2015, 1500, "Civic Hybrid 1.5 IMA", "Civic Hybrid 1.5 IMA 110hp [NEW]", "Hybrid"),
    ("CIVIC", 2013, 2015, 1800, "R18Z1", "Civic 1.8 [NEW]"),
    ("CIVIC", 2013, 2015, 2400, "K24Z7", "Civic Si 2.4 205hp [ROW_FIX]"),
    ("CIVIC", 2016, 2025, 1500, "L15B7", "Civic 1.5T 174-205hp (Si shares engine; Type R K20C1 minority) [ROW_FIX]"),
    ("CIVIC", 2016, 2024, 2000, "R20Z1", "Civic 2.0 155hp (Type R minority) [MRR20][NEW]"),
    ("CIVIC", 2025, 2025, 2000, "Honda 2.0 i-MMD Hybrid", "Civic e:HEV 2.0 hybrid 200hp (2025 hybrid-only) [NEW]", "Hybrid"),
    ("CLARITY", 2017, 2021, None, "Clarity PHEV (1.5 + motor)", "Clarity PHEV 212hp majority (Fuel Cell minority) [NEW]", "Hybrid"),
    ("CROSSTOUR", 2012, 2015, 2400, "K24Z3", "Crosstour 2.4 192hp [DB family]"),
    ("CROSSTOUR", 2012, 2012, 3500, "J35Z2", "Crosstour V6 271-278hp (VIN TF1/TF2) [ROW_FIX]"),
    ("CROSSTOUR", 2013, 2015, 3500, "J35Y1", "Crosstour V6 278hp Earth Dreams (VIN 1/2) [ROW_FIX]"),
    ("ELEMENT", 2003, 2011, None, "K24A1", "Element 2.4 160-166hp [ROW_FIX K24A1]"),
    ("FIT", 2007, 2008, None, "L15A1", "Fit 1.5 109hp [DB family]"),
    ("FIT", 2009, 2014, None, "L15A7", "Fit 1.5 117hp US (DB 120 Euro) [DB family]"),
    ("FIT", 2015, 2020, None, "L15B2", "Fit 1.5 130hp [NEW]"),
    ("HR-V", 2016, 2022, None, "R18Z4", "HR-V 1.8 141hp [ROW_FIX R18Z4]"),
    ("HR-V", 2023, 2025, None, "R20Z1", "HR-V 2.0 158hp 2023+ (R20Z-family) [MRR20][NEW]"),
    ("INSIGHT", 2000, 2001, None, "Insight 1.0 IMA (ECA1)", "Insight 1.0 IMA 73hp [NEW]", "Hybrid"),
    ("INSIGHT", 2002, 2006, None, "Insight 1.3 IMA (gen1)", "Insight 1.3 IMA 93hp [NEW]", "Hybrid"),
    ("INSIGHT", 2010, 2014, None, "LDA1", "Insight 1.3 IMA 98hp system [DB family][ROW_FIX label]", "Hybrid"),
    ("INSIGHT", 2019, 2022, None, "Honda 1.5 i-MMD Hybrid", "Insight 1.5 i-MMD 151hp [NEW]", "Hybrid"),
    ("ODYSSEY", 2000, 2004, None, "J35A4", "Odyssey 3.5 210-240hp [ROW_FIX]"),
    ("ODYSSEY", 2005, 2010, None, "J35A6", "Odyssey 3.5 244-250hp [ROW_FIX]"),
    ("ODYSSEY", 2011, 2017, None, "J35A8", "Odyssey 3.5 248hp [ROW_FIX]"),
    ("ODYSSEY", 2018, 2025, None, "J35Y (Earth Dreams 3.5 V6)", "Odyssey 3.5 280hp [NEW]"),
    ("PASSPORT", 2000, 2002, None, "Isuzu 6VD1 3.2 V6 (Passport)", "Passport = Isuzu Rodeo rebadge, 3.2 V6 205hp [PASSPORT][NEW]"),
    ("PASSPORT", 2019, 2025, None, "J35Y (Earth Dreams 3.5 V6)", "Passport 3.5 280hp [NEW]"),
    ("PILOT", 2003, 2005, None, "J35A4", "Pilot 3.5 240hp [ROW_FIX]"),
    ("PILOT", 2006, 2008, None, "J35A6", "Pilot 3.5 244hp [ROW_FIX]"),
    ("PILOT", 2009, 2015, None, "J35A9", "Pilot 3.5 250hp (VIN 3/4) [ROW_FIX]"),
    ("PILOT", 2009, 2015, 3500, "J35A9", "Pilot 3.5 250hp (VIN 3/4) [ROW_FIX]"),
    ("PILOT", 2016, 2025, None, "J35Y (Earth Dreams 3.5 V6)", "Pilot 3.5 280hp [NEW]"),
    ("PRELUDE", 2000, 2001, None, "H22A4", "Prelude 2.2 VTEC 195hp [NEW]"),
    ("RIDGELINE", 2006, 2014, None, "J35A9", "Ridgeline 3.5 250hp [ROW_FIX]"),
    ("RIDGELINE", 2017, 2025, None, "J35Y (Earth Dreams 3.5 V6)", "Ridgeline 3.5 280hp [NEW]"),
    ("S2000", 2000, 2003, None, "F20C1", "S2000 2.0 240hp [NEW]"),
    ("S2000", 2004, 2009, None, "F22C1", "S2000 2.2 237hp [NEW]"),
]

def decide(model, year, code, fuel):
    parts = code.replace("LEMON_HONDA_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc = None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
    mu = model.upper()
    # fuel-conditional rules (lemon fuel column is authoritative for hybrid splits)
    if mu == "ACCORD" and cc == 2000 and year >= 2014:
        if fuel == "Hybrid":
            return ("Honda 2.0 i-MMD Hybrid", f"Accord Hybrid 2.0 i-MMD {year} [NEW]", "Hybrid")
        if year <= 2022:
            return ("K20C4", f"Accord 2.0T 252hp petrol {year} [MRK20C][NEW]", None)
        return (None, f"Accord {year} 2000cc petrol: no such US engine", None)
    if mu == "CIVIC" and cc == 2000 and year >= 2025:
        return ("Honda 2.0 i-MMD Hybrid", "Civic e:HEV 2.0 hybrid 200hp (hybrid-only 2025) [NEW]", "Hybrid")
    if mu == "CIVIC" and year == 2025 and cc is None:
        if fuel == "Hybrid":
            return ("Honda 2.0 i-MMD Hybrid", "Civic e:HEV 2025 (bare hybrid row) [NEW]", "Hybrid")
        return (None, "Civic 2025 bare: trim unknown", None)
    if mu == "CR-V" and year == 2025 and cc is None:
        return (None, "CR-V 2025 bare: 1.5T vs hybrid unknown", None)
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
    assert base_lemon == 4655, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 4655 (workspace rewind?)"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Honda' AND engine_code LIKE 'LEMON_HONDA%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        tgt, note, fuel_fix = decide(model, year, code, fuel)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"Honda LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(16): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter(d[6] for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"

    if not apply:
        with open("database_enriched/csv_exports/30_lemon_batch13_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"Honda",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Honda",s[1],s[2],"","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step22_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP22_VERIFIED')""",
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

    with open("database_enriched/csv_exports/30_lemon_batch13_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"Honda",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_HONDA remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_HONDA%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
