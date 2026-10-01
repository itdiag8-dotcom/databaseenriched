"""Step 24 (user-plan Step 5, batch 15): replace LEMON_CADILLAC codes with real OEM engine codes.
314 rows, 24 models. Signals: cc + VIN + fuel column (Escalade Hybrid rows) + year.
DB GM vocabulary reused (LFX/LLT/LF1/LY7/LS6/LS2/L92/L9H/L86/L87/LM2/LFA/LSA/LC3/LD8/L37/LCV/LTG/L3B/
Voltec EREV). Verified: RWD Northstar 4.6 = LH2 320hp (not LH8); 4.4 SC = LC3 (STS-V 469 / XLR-V 443).
New: LH2, LA3 3.2, LP1/LP9 2.8, LTA 4.2TT Blackwing, LYRIQ/OPTIQ EV. Junk rows fixed: LF4 ('2.5'!),
LGW/LGX/LT4/L87 NULLs, LSA 556hp, LY7 255hp."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "NORTHSTAR": "https://en.wikipedia.org/wiki/Northstar_engine_series (RWD 4.6 = LH2 320hp STS/SRX/XLR; 4.4 SC = LC3: STS-V 469hp, XLR-V 443hp; LD8 275 / L37 300 FWD)",
    "HOTRODLC3": "https://www.hotrod.com/how-to/hrdp-2006-cadillac-supercharged-northstar-v8 (LC3 RPO confirmed)",
    "XLRNET": "https://www.xlr-net.com/forums/threads/supercharging-my-xlr.11676/ (LH2 VIN A = 320hp RWD Northstar)",
    "DBLINKS": "DB GM rows: LFX/LLT/LF1/LY7 (3.6/3.0 family), LS6/LS2 (CTS-V gen1), L92/L9H/L86/L87 (6.2), LM2 3.0 Duramax, LFA 6.0 two-mode hybrid, LSA (CTS-V gen2), LC3 4.4 SC, LD8/L37 FWD Northstar, LCV 2.5, LTG 2.0T, L3B 2.7T, Voltec EREV",
    "GMUS": "Cadillac US lineup knowledge (ATS/CTS/CT4/CT5/CT6/XT* generations + VIN splits from lemon codes)",
}

NEW_ENGINES = {
    "LH2": ("4.6 V8 Northstar RWD (STS/SRX/XLR, 320hp)", "Petrol", 4565, 320, 8),
    "3.0 V6 (Opel L81)": ("3.0 V6 (Opel Omega/Catera, 200hp)", "Petrol", 2962, 200, 6),
    "LA3": ("3.2 V6 (CTS 2003-05, 220hp)", "Petrol", 3175, 220, 6),
    "LP1": ("2.8 V6 (CTS 2005-07, 210hp)", "Petrol", 2792, 210, 6),
    "LP9": ("2.8 V6 Turbo (SRX 2010-11, 300hp)", "Petrol", 2792, 300, 6),
    "LTA": ("4.2 V8 TwinTurbo Blackwing (CT6-V, 550hp)", "Petrol", 4177, 550, 8),
    "LYRIQ Electric": ("Electric motors (LYRIQ: 340hp RWD / 500hp AWD)", "Electric", None, 500, None),
    "OPTIQ Electric": ("Electric motors (OPTIQ: 300hp FWD / 373hp AWD)", "Electric", None, 300, None),
}

ROW_FIXES = {
    "LF4": {"engine_type": "3.6 V6 TwinTurbo (ATS-V 464hp / CT4-V Blackwing 472hp)", "displacement_cc": 3564, "power_hp": 464},
    "LGW": {"engine_type": "3.0 V6 TwinTurbo (CT6 404hp / CT5-V 360hp)", "power_hp": 404},
    "LGX": {"engine_type": "3.6 V6 DI (XT5/XT6/CT6, 310-335hp)", "power_hp": 335},
    "LT4": {"engine_type": "6.2 V8 Supercharged (CTS-V 640hp / CT5-V Blackwing 668hp)", "displacement_cc": 6162, "power_hp": 640},
    "L87": {"engine_type": "6.2 V8 EcoTec3 (Escalade/Tahoe 420hp)", "power_hp": 420},
    "LSA": {"engine_type": "6.2 V8 Supercharged (CTS-V 2009-15, 556hp)", "power_hp": 556},
    "LY7": {"engine_type": "3.6 V6 (CTS/SRX/STS 2004-08, 255-260hp)", "power_hp": 255},
    "LLT": {"engine_type": "3.6 V6 DI (CTS/STS 2008-11, 304hp)"},
}

FUEL_FIX_BY_TARGET = {"LM2": "Diesel", "LFA": "Hybrid", "Voltec 1.4 EREV (Volt)": "Hybrid",
                      "LYRIQ Electric": "Electric", "OPTIQ Electric": "Electric"}

# (MODEL-upper, y0, y1, cc, target, evidence[, fuel_fix])  cc=None = bare/slug
R = [
    ("ATS", 2013, 2019, 2000, "LTG", "ATS 2.0T 272hp (VIN X) [DB family]"),
    ("ATS", 2013, 2016, 2500, "LCV", "ATS 2.5 NA 202hp (VIN A) [DB family LCV 196]"),
    ("ATS", 2013, 2019, 3600, None, None),  # resolved by VIN in decide()
    ("CT4", 2020, 2025, 2000, "LTG", "CT4 2.0T 237hp (VIN K) [DB family]"),
    ("CT4", 2020, 2025, 2700, "L3B", "CT4-V 2.7T 325hp (VIN L; Silverado L3B family) [DB family]"),
    ("CT4", 2022, 2025, 3600, "LF4", "CT4-V Blackwing 3.6TT 472hp [ROW_FIX LF4]"),
    ("CT5", 2020, 2025, 2000, "LTG", "CT5 2.0T 237hp (VIN K) [DB family]"),
    ("CT5", 2020, 2025, 3000, "LGW", "CT5-V 3.0TT 360hp (VIN W) [ROW_FIX LGW]"),
    ("CT5", 2022, 2025, 6200, "LT4", "CT5-V Blackwing 6.2 SC 668hp [ROW_FIX LT4]"),
    ("CT6", 2016, 2018, 2000, "LTG", "CT6 2.0T 265-272hp (VIN X) [DB family]"),
    ("CT6", 2016, 2018, 3000, "LGW", "CT6 3.0TT 404hp (VIN 6) [ROW_FIX LGW]"),
    ("CT6", 2016, 2020, 3600, "LGX", "CT6 3.6 335hp (VIN S) [ROW_FIX LGX]"),
    ("CT6", 2019, 2020, 4200, "LTA", "CT6-V 4.2TT Blackwing 550hp (VIN J) [NEW LTA]"),
    ("CTS", 2004, 2005, 3200, "LA3", "CTS 3.2 V6 220hp [NEW LA3]"),
    ("CTS", 2003, 2003, None, "LA3", "2003 CTS = 3.2 only [NEW LA3]"),
    ("CTS", 2004, 2008, 3600, "LY7", "CTS 3.6 255-258hp [ROW_FIX LY7]"),
    ("CTS", 2004, 2005, 5700, "LS6", "CTS-V 5.7 LS6 400hp [DB family]"),
    ("CTS", 2005, 2007, 2800, "LP1", "CTS 2.8 V6 210hp (Canada row) [NEW LP1]"),
    ("CTS", 2006, 2007, 6000, "LS2", "CTS-V 6.0 LS2 400hp [DB family]"),
    ("CTS", 2008, 2008, None, "LLT", "2008 CTS 3.6 DI 304hp majority (LY7 base minority) [ROW_FIX LLT]"),
    ("CTS", 2009, 2014, 6200, "LSA", "CTS-V 6.2 SC LSA 556hp [ROW_FIX LSA]"),
    ("CTS", 2010, 2014, 3000, "LF1", "CTS 3.0 270hp (VIN 5; DB 276) [DB family]"),
    ("CTS", 2010, 2017, 3600, "LFX", "CTS 3.6 DI 318-321hp (VIN 3; Vsport LF3 minority) [DB family]"),
    ("CTS", 2014, 2019, 2000, "LTG", "CTS 2.0T 272hp (VIN X) [DB family]"),
    ("CTS", 2016, 2019, 6200, "LT4", "CTS-V gen3 6.2 SC 640hp [ROW_FIX LT4]"),
    ("CATERA", 2000, 2001, None, "3.0 V6 (Opel L81)", "Catera = Opel Omega 3.0 V6 200hp [NEW]"),
    ("DTS", 2006, 2011, None, "LD8", "DTS 4.6 Northstar 275hp [DB family]"),
    ("DEVILLE", 2000, 2005, None, "LD8", "DeVille 4.6 Northstar 275hp (DTS trim L37 300hp minority) [DB family]"),
    ("ELDORADO", 2000, 2002, None, "LD8", "Eldorado ETC 4.6 Northstar (LD8/L37) [DB family]"),
    ("SEVILLE", 2000, 2004, None, "LD8", "Seville SLS 4.6 LD8 275hp (STS L37 300hp minority) [DB family]"),
    ("ELR", 2014, 2016, None, "Voltec 1.4 EREV (Volt)", "ELR = Voltec Gen1 PHEV (system 207/233hp) [DB family][fuel fix Hybrid]"),
    ("ESCALADE", 2000, 2000, None, "L59", "2000 Escalade 5.3 Vortec 285hp only [DB family]"),
    ("ESCALADE", 2002, 2013, 5300, "L59", "Escalade 5.3 Vortec 285-295hp [DB family]"),
    ("ESCALADE", 2002, 2005, 6000, "LQ4", "Escalade 6.0 Vortec 345hp [DB family]"),
    ("ESCALADE", 2007, 2009, None, "L92", "Escalade 6.2 403hp [DB family]"),
    ("ESCALADE", 2010, 2013, None, "L9H", "Escalade 6.2 403hp (L92 successor) [DB family]"),
    ("ESCALADE", 2009, 2013, 6000, "LFA", "Escalade Hybrid 6.0 two-mode 332hp system [DB family][fuel fix Hybrid]"),
    ("ESCALADE", 2014, 2014, None, "L9H", "2014 Escalade 6.2 403hp (pre-EcoTec3) [DB family]"),
    ("ESCALADE", 2015, 2020, None, "L86", "Escalade 6.2 EcoTec3 420hp (incl. 2015 trims) [DB family]"),
    ("ESCALADE", 2021, 2023, 6200, "L87", "Escalade 6.2 EcoTec3 DFM 420hp (VIN L) [ROW_FIX L87]"),
    ("ESCALADE", 2021, 2024, 3000, "LM2", "Escalade 3.0 Duramax diesel 277hp (VIN T) [DB family][fuel fix Diesel]"),
    ("LYRIQ", 2023, 2025, None, "LYRIQ Electric", "LYRIQ EV only (340/500hp) [NEW][fuel fix Electric]"),
    ("OPTIQ", 2025, 2025, None, "OPTIQ Electric", "OPTIQ EV only (300/373hp) [NEW][fuel fix Electric]"),
    ("SRX", 2004, 2009, 3600, "LY7", "SRX 3.6 255-260hp [ROW_FIX LY7]"),
    ("SRX", 2004, 2009, 4600, "LH2", "SRX 4.6 Northstar RWD 320hp [NORTHSTAR][NEW LH2]"),
    ("SRX", 2010, 2011, 2800, "LP9", "SRX 2.8T 300hp (Canada row) [NEW LP9]"),
    ("SRX", 2010, 2016, 3000, "LF1", "SRX 3.0 265-268hp (incl. 2015 trims) [DB family]"),
    ("SRX", 2012, 2016, None, "LF1", "SRX 3.0 only 2012+ (incl. 2015 trims) [DB family]"),
    ("STS", 2005, 2007, 3600, "LY7", "STS 3.6 255hp [ROW_FIX LY7]"),
    ("STS", 2008, 2010, 3600, "LLT", "STS 3.6 DI 298-302hp [ROW_FIX LLT]"),
    ("STS", 2005, 2011, 4600, "LH2", "STS 4.6 Northstar RWD 320hp [NORTHSTAR][NEW LH2]"),
    ("STS", 2006, 2009, 4400, "LC3", "STS-V 4.4 SC Northstar 469hp [NORTHSTAR][DB family]"),
    ("XLR", 2004, 2009, None, "LH2", "XLR 4.6 Northstar RWD 320hp [NORTHSTAR][NEW LH2]"),
    ("XLR", 2006, 2009, 4400, "LC3", "XLR-V 4.4 SC Northstar 443hp [NORTHSTAR][DB family]"),
    ("XT4", 2019, 2025, None, "LTG", "XT4 2.0T 237hp only [DB family]"),
    ("XT5", 2017, 2019, None, "LFX", "XT5 3.6 310hp [DB family]"),
    ("XT5", 2020, 2025, 2000, "LTG", "XT5 2.0T 237hp (VIN 4) [DB family]"),
    ("XT5", 2020, 2025, 3600, "LGX", "XT5 3.6 310hp (VIN S) [ROW_FIX LGX]"),
    ("XT6", 2020, 2020, None, "LGX", "XT6 3.6 310hp [ROW_FIX LGX]"),
    ("XT6", 2021, 2025, 2000, "LTG", "XT6 2.0T 237hp [DB family]"),
    ("XT6", 2021, 2025, 3600, "LGX", "XT6 3.6 310hp [ROW_FIX LGX]"),
    ("XTS", 2013, 2013, None, "LFX", "XTS 3.6 304hp (Vsport LF3 minority) [DB family]"),
]

def decide(model, year, code, fuel):
    parts = code.replace("LEMON_CADILLAC_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc = None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
    mu = model.upper()
    # ATS 3.6: VIN S = ATS-V LF4; VIN 3 / bare = LFX
    if mu == "ATS" and cc == 3600:
        if "VINS" in code.upper():
            return ("LF4", "ATS-V 3.6TT 464hp (VIN S) [ROW_FIX LF4]", None)
        return ("LFX", "ATS 3.6 321hp (VIN 3) [DB family]", None)
    # Escalade 2015 trim slugs -> 6.2 L86
    if mu == "ESCALADE" and "ESCALADE" in code.upper() and "ESV" not in code.upper() and cc is None and 2015 <= year <= 2020:
        pass  # falls through to bare rule below
    # skip known-ambiguous bare rows
    if mu == "ESCALADE" and cc is None and 2002 <= year <= 2005:
        return (None, "Escalade 2002-2005 bare: 5.3 vs 6.0 unknown", None)
    if mu == "ESCALADE" and cc is None and year >= 2024:
        return (None, "Escalade 2024+ bare: 6.2 vs 3.0D vs V-series unknown", None)
    if mu == "CTS" and cc == 6200 and year == 2015:
        return (None, "CTS 2015 6200cc: no 2015 CTS-V existed (anomalous row)", None)
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands:
        if cc is not None:
            return (None, f"{model} {year} {cc}cc: no rule", None)
        return (None, f"no rule for {model} {year} (bare)", None)
    r = cands[0]
    if r[4] is None:
        return (None, r[5], None)
    fuel_fix = r[6] if len(r) > 6 else FUEL_FIX_BY_TARGET.get(r[4])
    return (r[4], r[5], fuel_fix)

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == 4043, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 4043 (workspace rewind?)"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Cadillac' AND engine_code LIKE 'LEMON_CADILLAC%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        tgt, note, fuel_fix = decide(model, year, code, fuel)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"Cadillac LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(16): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter(d[6] for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"

    if not apply:
        with open("database_enriched/csv_exports/32_lemon_batch15_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"Cadillac",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Cadillac",s[1],s[2],"","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step24_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP24_VERIFIED')""",
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

    with open("database_enriched/csv_exports/32_lemon_batch15_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"Cadillac",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_CADILLAC remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_CADILLAC%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
