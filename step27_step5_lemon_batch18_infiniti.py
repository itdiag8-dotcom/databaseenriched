"""Step 27 (user-plan Step 5, batch 18): replace LEMON_INFINITI codes with real OEM engine codes.
230 rows, 32 models, MY2000-2025. Signals: model name encodes displacement (FX35/M56/Q45...),
cc markers (Q50/Q60/Q70/QX70), fuel column (hybrids), trim slugs (Q60IPL, Q50HYBRID*).
DB Nissan-batch vocabulary reused (VQ35DE/HR, VQ37VHR, VQ25HR, VQ30DE, VK45DE, VK50VE, VK56DE/VD,
VG33E, SR20DE, VR30DDTT, KR20DDET, M274DE20 = the Q50 2.0t row). New: VH41DE (Q45 G50),
VQ35DD (QX60 2017+), QR25DER Hybrid (QX60), VQ35HR Hybrid (M35h/Q50/Q70 Direct Response 360hp).
Web-verified: Q50 hybrid dropped after 2018, 2.0t dropped for 2020 (so 2019 bare = skip);
Q60 4cyl dropped for 2019; QX70 V8 discontinued for 2015; QX60 hybrid = QR25DER 250hp net;
2017 QX60 3.5 = VQ35DD 295hp (Infiniti press kit)."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "Q50WIKI": "https://en.wikipedia.org/wiki/Infiniti_Q50 (engines: M274 DE20 2.0T, VR30DDTT 300/400, VQ35HR+HM34 hybrid 360hp, VQ37VHR; hybrid discontinued after 2018 MY; cancelled 2024)",
    "CARGURUSQ50": "https://www.cargurus.com/research/articles/infiniti-q50-buying-guide + https://www.edmunds.com/infiniti/q50/2020/review/ (Q50 Hybrid dropped for 2019; 2.0t dropped for 2020 -> 2020+ all 3.0t 300/400)",
    "GCRHYB": "https://www.greencarreports.com/news/1118910_out-of-juice-infiniti-q50-hybrid-luxury-sedan-dropped (Q50 Hybrid = 3.5 V6 + motor, 360hp; killed for 2019; QX60 hybrid axed earlier)",
    "KBBQ6019": "https://www.kbb.com/infiniti/q60/2019/ (2019 Q60 drops the 4-cylinder; all trims 3.0t 300 / Red Sport 400)",
    "CARSQX70": "https://www.cars.com/research/infiniti-qx70/ (QX70 V-8 discontinued for 2015) + https://www.kbb.com/infiniti/qx70/ (2017 sole engine 3.7 325hp)",
    "INFPRESS17": "https://usa.infinitinews.com/en-US/releases/us-2017-infiniti-qx60-press-kit (2017 QX60 3.5 = VQ35DD 295hp direct injection, up from 265; QX60 Hybrid = QR25DER 2.5 SC I4 230hp + 15kW motor = 250 net)",
    "QX60WIKI": "https://en.wikipedia.org/wiki/Infiniti_QX60 (QX60 Hybrid 2014-2017; 2017+ 295hp DIG; 2nd gen 2022 = VQ35DD 295hp + 9AT)",
    "NISSANBATCH": "DB Nissan-batch vocabulary: VQ35DE (n=133), VQ35HR (n=30), VQ37VHR (n=54), VQ25HR G25 (n=7), VQ30DE, VK45DE, VK50VE 390, VK56DE, VK56VD, VG33E, SR20DE, VR30DDTT 400, KR20DDET VC-T, M274DE20 'Q50 2.0 16v Turbo' 208hp (n=2)",
    "USLINEUP": "US Infiniti lineup knowledge (FX/EX/G/M/Q-series hp values: EX35 297, FX35 280/303, FX45 315-325, FX50 390, G35 260-306, G37 328/IPL 348, M35 275/303, M37 330, M45 325/340, M56 420, Q45 VH41DE 266 / VK45DE 340, QX4 VG33E 168 / VQ35DE 240, QX56 315/320/400, QX80 400, QX50 325/268 VC-T, QX30 208 M274, I30 227, I35 255, JX35 265, G20 140, Q40 328)",
}

NEW_ENGINES = {
    "VH41DE": ("4.1 V8 (Q45 G50 1997-2000, 266hp)", "Petrol", 4130, 266, 8),
    "VQ35DD": ("3.5 V6 Direct Injection (QX60 2017+ / Pathfinder, 295hp)", "Petrol", 3498, 295, 6),
    "QR25DER Hybrid (QX60)": ("2.5 I4 Supercharged + 15kW motor (QX60 Hybrid, 250hp net)", "Hybrid", 2488, 250, 4),
    "VQ35HR Hybrid (Direct Response)": ("3.5 V6 VQ35HR + HM34 motor (M35h/Q50/Q70 Hybrid, 360hp net)", "Hybrid", 3498, 360, 6),
}

ROW_FIXES = {
    "VQ35HR": {"engine_type": "3.5 V6 VQ35HR (G35 07-08 306 / EX35 297 / FX35 09-12 303 / M35 09-10 303hp)", "power_hp": 306},
    "VQ35DE": {"engine_type": "3.5 V6 VQ35DE (G35 260-298 / I35 255 / JX35+QX60 14-16 265 / QX4 240 / M35 06-08 275 / FX35 03-08 280hp)", "power_hp": 280},
    "VQ37VHR": {"engine_type": "3.7 V6 VVEL VQ37VHR (G37+Q40+Q60 328 / IPL 348 / M37+Q70 330 / EX37+FX37+QX50+QX70 325hp)"},
    "VQ25HR": {"engine_type": "2.5 V6 VQ25HR (G25, 218hp)", "power_hp": 218},
    "VQ30DE": {"engine_type": "3.0 V6 VQ30DE (I30/Maxima, 227hp)", "power_hp": 227},
    "VK45DE": {"engine_type": "4.5 V8 VK45DE (Q45 02-06 340 / M45 325-340 / FX45 315-325hp)", "power_hp": 340},
    "VK50VE": {"engine_type": "5.0 V8 VK50VE (FX50 / QX70 5.0, 390hp)", "power_hp": 390},
    "VK56DE": {"engine_type": "5.6 V8 VK56DE (QX56 04-10 315-320 / Titan+Armada 305-320hp)", "power_hp": 317},
    "VK56VD": {"engine_type": "5.6 V8 VK56VD DI (QX56 11-13 + QX80 400 / M56 420hp)", "power_hp": 400},
    "VG33E": {"engine_type": "3.3 V6 OHV VG33E (QX4/Pathfinder 2000, 168hp)", "power_hp": 168},
    "SR20DE": {"engine_type": "2.0 I4 DOHC SR20DE (G20/Primera, 140hp)", "power_hp": 140},
    "VR30DDTT": {"engine_type": "3.0 V6 TwinTurbo VR30DDTT (Q50/Q60 3.0t 300hp + Red Sport 400 / Z 400hp)"},
    "KR20DDET": {"engine_type": "2.0 I4 VC-Turbo KR20DDET (Altima 248hp / QX50+QX55 268hp)"},
    "M274DE20": {"engine_type": "2.0 I4 Turbo Mercedes M274 (Q50/Q60 2.0t + QX30, 208hp)", "power_hp": 208},
}

FUEL_FIX_BY_TARGET = {"QR25DER Hybrid (QX60)": "Hybrid", "VQ35HR Hybrid (Direct Response)": "Hybrid"}

# identity expectations for the NEW standing rule: {target: (fuel, cc)} for pre-existing rows
IDENTITY = {
    "VQ35HR": ("Petrol", 3500), "VQ35DE": ("Petrol", 3500), "VQ37VHR": ("Petrol", 3700),
    "VQ25HR": ("Petrol", 2500), "VQ30DE": ("Petrol", 3000), "VK45DE": ("Petrol", 4494),
    "VK50VE": ("Petrol", 5026), "VK56DE": ("Petrol", 5550), "VK56VD": ("Petrol", 5600),
    "VG33E": ("Petrol", 3275), "SR20DE": ("Petrol", 1998), "VR30DDTT": ("Petrol", 2993),
    "KR20DDET": ("Petrol", 1997), "M274DE20": ("Petrol", 2000),
}

# (MODEL-upper, y0, y1, cc, target, evidence, pfix)  cc=None = bare
R = [
    ("EX35", 2008, 2012, None, "VQ35HR", "EX35 = VQ35HR 297hp [USLINEUP]", 297),
    ("EX37", 2013, 2013, None, "VQ37VHR", "EX37 = VQ37VHR 325hp [USLINEUP]", 325),
    ("FX35", 2003, 2008, None, "VQ35DE", "FX35 03-08 = VQ35DE 280hp [USLINEUP]", 280),
    ("FX35", 2009, 2012, None, "VQ35HR", "FX35 09-12 = VQ35HR 303hp [USLINEUP]", 303),
    ("FX37", 2013, 2013, None, "VQ37VHR", "FX37 = VQ37VHR 325hp [USLINEUP]", 325),
    ("FX45", 2003, 2008, None, "VK45DE", "FX45 = VK45DE 315-325hp [USLINEUP][ROW_FIX VK45DE]", 320),
    ("FX50", 2009, 2013, None, "VK50VE", "FX50 = VK50VE 390hp [USLINEUP][ROW_FIX VK50VE]", 390),
    ("G20", 2000, 2002, None, "SR20DE", "G20 = SR20DE 140hp (Primera P11) [USLINEUP][ROW_FIX SR20DE]", 140),
    ("G25", 2011, 2012, None, "VQ25HR", "G25 = VQ25HR 218hp [USLINEUP][ROW_FIX VQ25HR]", 218),
    ("G35", 2003, 2004, None, "VQ35DE", "G35 sedan 03-04 = VQ35DE 260hp [USLINEUP]", 260),
    ("G35", 2005, 2006, None, "VQ35DE", "G35 05-06 = VQ35DE 280hp (coupe 298 minority) [USLINEUP]", 280),
    ("G35", 2007, 2008, None, "VQ35HR", "G35 07-08 = VQ35HR 306hp [USLINEUP]", 306),
    ("G37", 2008, 2013, None, "VQ37VHR", "G37 = VQ37VHR 328hp [USLINEUP]", 328),
    ("I30", 2000, 2001, None, "VQ30DE", "I30 = VQ30DE 227hp [USLINEUP][ROW_FIX VQ30DE]", 227),
    ("I35", 2002, 2004, None, "VQ35DE", "I35 = VQ35DE 255hp [USLINEUP]", 255),
    ("JX35", 2013, 2013, None, "VQ35DE", "JX35 = VQ35DE 265hp [USLINEUP]", 265),
    ("M35", 2006, 2008, None, "VQ35DE", "M35 Y50 06-08 = VQ35DE 275hp [USLINEUP]", 275),
    ("M35", 2009, 2010, None, "VQ35HR", "M35 09-10 = VQ35HR 303hp [USLINEUP]", 303),
    ("M35H", 2012, 2013, None, "VQ35HR Hybrid (Direct Response)", "M35h = VQ35HR + HM34 360hp net (fuel label wrong -> Hybrid) [NEW][GCRHYB]", 360),
    ("M37", 2011, 2013, None, "VQ37VHR", "M37 = VQ37VHR 330hp [USLINEUP]", 330),
    ("M45", 2003, 2004, None, "VK45DE", "M45 Y34 = VK45DE 340hp [USLINEUP]", 340),
    ("M45", 2006, 2010, None, "VK45DE", "M45 Y50 = VK45DE 325hp [USLINEUP]", 325),
    ("M56", 2011, 2013, None, "VK56VD", "M56 = VK56VD 420hp [USLINEUP][ROW_FIX VK56VD]", 420),
    ("Q40", 2015, 2015, None, "VQ37VHR", "Q40 = G37 carryover VQ37VHR 328hp (AWD/RWD) [USLINEUP]", 328),
    ("Q45", 2000, 2001, None, "VH41DE", "Q45 G50 00-01 = VH41DE 4.1 266hp [NEW][USLINEUP]", 266),
    ("Q45", 2002, 2006, None, "VK45DE", "Q45 F50 = VK45DE 340hp [USLINEUP]", 340),
    ("QX4", 2000, 2000, None, "VG33E", "QX4 2000 = VG33E 3.3 168hp [USLINEUP][ROW_FIX VG33E]", 168),
    ("QX4", 2001, 2003, None, "VQ35DE", "QX4 01-03 = VQ35DE 240hp [USLINEUP]", 240),
    ("QX56", 2004, 2007, None, "VK56DE", "QX56 04-07 = VK56DE 315hp [USLINEUP]", 315),
    ("QX56", 2008, 2010, None, "VK56DE", "QX56 08-10 = VK56DE 320hp [USLINEUP]", 320),
    ("QX56", 2011, 2013, None, "VK56VD", "QX56 11-13 = VK56VD 400hp [USLINEUP]", 400),
    ("QX80", 2014, 2025, None, "VK56VD", "QX80 = VK56VD 400hp all years [USLINEUP]", 400),
    ("QX50", 2014, 2017, None, "VQ37VHR", "QX50 (EX37 rebadge) = VQ37VHR 325hp [USLINEUP]", 325),
    ("QX50", 2019, 2025, None, "KR20DDET", "QX50 2019+ = KR20DDET VC-Turbo 268hp [USLINEUP][ROW_FIX KR20DDET]", 268),
    ("QX55", 2022, 2025, None, "KR20DDET", "QX55 = VC-Turbo 268hp [USLINEUP][ROW_FIX KR20DDET]", 268),
    ("QX30", 2017, 2019, None, "M274DE20", "QX30 = Mercedes M274 2.0t 208hp (GLA-based) [ROW_FIX M274DE20]", 208),
    ("QX60", 2014, 2016, 3500, "VQ35DE", "QX60 3.5 14-16 = VQ35DE 265hp [INFPRESS17]", 265),
    ("QX60", 2017, 2017, 3500, "VQ35DD", "QX60 2017 = VQ35DD 295hp DIG [INFPRESS17][NEW VQ35DD]", 295),
    ("QX60", 2014, 2017, 2500, "QR25DER Hybrid (QX60)", "QX60 Hybrid = QR25DER + 15kW, 250hp net (fuel col Hybrid) [INFPRESS17][NEW]", 250),
    ("QX60", 2018, 2025, None, "VQ35DD", "QX60 18-20 + 2nd-gen 22-25 = VQ35DD 295hp [INFPRESS17][QX60WIKI][NEW VQ35DD]", 295),
    ("QX70", 2014, 2014, 3700, "VQ37VHR", "QX70 3.7 (VIN C) = VQ37VHR 325hp [USLINEUP]", 325),
    ("QX70", 2014, 2014, 5000, "VK50VE", "QX70 5.0 (VIN B) = VK50VE 390hp [USLINEUP]", 390),
    ("QX70", 2015, 2017, None, "VQ37VHR", "QX70 15-17 = 3.7 325hp only (V8 dropped for 2015) [CARSQX70]", 325),
    ("Q50", 2014, 2014, None, "VQ35HR Hybrid (Direct Response)", "Q50 2014 launch Hybrid (fuel col Hybrid) = 360hp net [NEW][GCRHYB]", 360),
    ("Q50", 2015, 2015, None, "VQ37VHR", "Q50 2015 3.7 petrol trims = VQ37VHR 328hp [USLINEUP]", 328),
    ("Q50", 2016, 2019, 2000, "M274DE20", "Q50 2.0t (VIN C) = Mercedes M274 208hp [Q50WIKI][ROW_FIX M274DE20]", 208),
    ("Q50", 2016, 2019, 3000, "VR30DDTT", "Q50 3.0t (VIN E) = VR30DDTT 300hp (Red Sport 400 minority) [Q50WIKI]", 300),
    ("Q50", 2016, 2018, 3500, "VQ35HR Hybrid (Direct Response)", "Q50 Hybrid (fuel col Hybrid) = 360hp net [NEW][GCRHYB]", 360),
    ("Q50", 2020, 2024, None, "VR30DDTT", "Q50 2020+ = 3.0t only (2.0t dropped 2020, hybrid 2019) [CARGURUSQ50]", 300),
    ("Q60", 2014, 2014, None, "VQ37VHR", "Q60 2014 = VQ37VHR 328hp (G37 coupe carryover) [USLINEUP]", 328),
    ("Q60", 2015, 2015, None, "VQ37VHR", "Q60 2015 trims = VQ37VHR 328hp (IPL 348 special-case) [USLINEUP]", 328),
    ("Q60", 2017, 2018, 2000, "M274DE20", "Q60 2.0t (VIN C) = M274 208hp [Q50WIKI-family][ROW_FIX M274DE20]", 208),
    ("Q60", 2017, 2018, 3000, "VR30DDTT", "Q60 3.0t (VIN E) = VR30DDTT 300hp (Red Sport 400 minority) [Q50WIKI-family]", 300),
    ("Q60", 2019, 2022, None, "VR30DDTT", "Q60 2019+ = 3.0t only (4cyl dropped 2019) [KBBQ6019]", 300),
    ("Q70", 2014, 2018, 3500, "VQ35HR Hybrid (Direct Response)", "Q70 Hybrid (fuel col Hybrid) = 360hp net [NEW][GCRHYB]", 360),
    ("Q70", 2014, 2019, 3700, "VQ37VHR", "Q70 3.7 = VQ37VHR 330hp [USLINEUP]", 330),
    ("Q70", 2014, 2019, 5600, "VK56VD", "Q70 5.6 = VK56VD 420hp [USLINEUP]", 420),
    ("Q70L", 2015, 2019, 3700, "VQ37VHR", "Q70L 3.7 = VQ37VHR 330hp [USLINEUP]", 330),
    ("Q70L", 2015, 2019, 5600, "VK56VD", "Q70L 5.6 = VK56VD 420hp [USLINEUP]", 420),
]

def decide(model, year, code, fuel):
    parts = code.replace("LEMON_INFINITI_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc = None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
    mu = model.upper()
    cu = code.upper()
    # Q50 2015: hybrid slugs vs petrol trims
    if mu == "Q50" and year == 2015:
        if "HYBRID" in cu:
            return ("VQ35HR Hybrid (Direct Response)", "Q50 Hybrid 2015 = 360hp net (trim slug + fuel col) [GCRHYB][NEW]", "Hybrid", 360)
        return ("VQ37VHR", "Q50 2015 3.7 trims (Base/Premium/Sport) = VQ37VHR 328hp [USLINEUP]", None, 328)
    # Q60 2015 IPL = 348hp
    if mu == "Q60" and year == 2015 and "IPL" in cu:
        return ("VQ37VHR", "Q60 IPL 2015 = VQ37VHR 348hp [USLINEUP]", None, 348)
    # known-ambiguous bare row -> skip
    if mu == "Q50" and year == 2019 and cc is None:
        return (None, "Q50 2019 bare: 2.0t (208) vs 3.0t (300/400) both offered (hybrid gone, 2.0t until 2020)", None, None)
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands:
        return (None, f"no rule for {model} {year} cc={cc}", None, None)
    r = cands[0]
    fuel_fix = FUEL_FIX_BY_TARGET.get(r[4])
    if fuel_fix and fuel == fuel_fix: fuel_fix = None
    return (r[4], r[5], fuel_fix, r[6])

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == 3301, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 3301 (workspace rewind?)"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Infiniti' AND engine_code LIKE 'LEMON_INFINITI%' ORDER BY car_model, car_year, engine_code""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        tgt, note, fuel_fix, pfix = decide(model, year, code, fuel)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix, pfix))
    print(f"Infiniti LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(20): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter(d[6] for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"
    # NEW identity assert (batch-17 rule): existing target rows must match expected fuel/displacement
    for tgt, (efuel, ecc) in IDENTITY.items():
        row = cur.execute("SELECT fuel, displacement_cc FROM engines WHERE engine_code=?", (tgt,)).fetchone()
        if row is None: continue
        if row[0] and efuel and row[0] != efuel:
            raise AssertionError(f"IDENTITY CONFLICT {tgt}: engines.fuel={row[0]}, expected {efuel}")
        if row[1] and ecc and abs(row[1] - ecc) / ecc > 0.06:
            raise AssertionError(f"IDENTITY CONFLICT {tgt}: engines.cc={row[1]}, expected ~{ecc}")
    print("identity assert: OK")

    if not apply:
        with open("database_enriched/csv_exports/35_lemon_batch18_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
            for d in decisions: w.writerow([d[0],"Infiniti",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Infiniti",s[1],s[2],"","","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step27_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP27_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
            print(f"  created {code}")
    for code, fixes in ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  row-fix {code}")

    lemon_retired = defaultdict(list)
    for vid, model, year, old, new, note, fuel_fix, pfix in decisions:
        cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=COALESCE(?, fuel) WHERE id=?", (new, fuel_fix, vid))
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=COALESCE(?, COALESCE(engine_power_hp,
            (SELECT power_hp FROM engines WHERE engine_code=?)),
            COALESCE((SELECT power_hp FROM engines WHERE engine_code=?), engine_power_hp)),
            engine_type=COALESCE(engine_type, (SELECT engine_type FROM engines WHERE engine_code=?)) WHERE id=?""",
            (pfix, new, new, new, vid))
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

    with open("database_enriched/csv_exports/35_lemon_batch18_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
        for d in decisions: w.writerow([d[0],"Infiniti",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_INFINITI remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_INFINITI%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
