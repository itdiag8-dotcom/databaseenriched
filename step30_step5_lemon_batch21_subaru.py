"""Step 30 (user-plan Step 5, batch 21): replace LEMON_SUBARU codes with real OEM engine codes.
205 rows, 13 models, MY2005-2025 -> 199 mapped / 6 documented skips.
Signals: cc markers (2000/2400/2500/3000/3600CC), fuel column (XV 2014 mild-hybrid, Crosstrek 2021
PHEV, Solterra mislabeled Petrol -> Electric), trim slugs (WRXSTI* 2015, IMPREZA20I4D 2015).
Key disambiguations: lemon "WRX" model rows have no STI except slugs (2015) or 2500CC (2019-21 =
STI 2.5T vs WRX 2.0T split by displacement); bare IMPREZA = NON-WRX (lemon split WRX off) so
2.5i EJ253 / 2.0 FB20B by era; IMPREZA_2500CC 2012-13 = "Impreza WRX" EJ255 265 (Edmunds) and
IMPREZA_2000CC_2005 = WRX EJ205 227 (2002-05 WRX was Impreza-badged; jspecauto).
DB Subaru vocab (Euro catalog) reused with junk labels repaired: EJ253 2.5 SOHC, EJ255/EJ257 2.5T,
EJ205 2.0T, EZ30D 3.0 H6 (241hp Euro=245PS -> US 245), EZ36D 3.6 H6 (258 -> US 256), FB20B 2.0,
FB25 -> relabeled FB25B 2.5 (2013-19), FA20 D-4S (BRZ 197 Euro -> 200 US), FA24 D-4S (GR86/BRZ 228).
New rows: FA20F 2.0 Turbo DIT (WRX 268 / Forester XT 250), FA24F 2.4 Turbo DIT (Ascent/XT 260 /
WRX 2022+ 271 - Wikipedia FA engine), FB25D 2.5 DI 182 (Forester 19+ / Legacy- Outback 20+ /
Crosstrek Sport / Impreza RS), XV Crosstrek Hybrid 160 (mild, MotorWeek), Crosstrek Hybrid PHEV
148, Solterra BEV 215 (Edmunds/KBB - fuel fix -> Electric).
Web-verified: FB25B 170-175 / FB25D 182 arrival years (Wikipedia FB engine, reman-engine);
Forester XT FA20DIT 250 axed after 2018 (torquenews); FA24F 260/271 (Wikipedia FA engine);
XV Hybrid 160 combined (MotorWeek/USNews); STI 305 through 2018, 310 for 2019-21 (jdcustoms);
2015 WRX FA20DIT 268 + STI EJ257 305 (KBB); 2013 Impreza WRX 265 (Edmunds); 2005 WRX EJ205 227
(crawfordperformance); 2024 Impreza RS 182 (CarAndDriver); Solterra 215 dual-motor (Edmunds/KBB).
Skips (6): Baja 2005-06 bare (2.5 NA 165 vs 2.5T 210), Legacy 2005-07 bare (2.5i vs GT 2.5T),
Impreza 2500CC 2005 (2.5RS 173 vs STI 300).
"""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "FBWIKI": "https://en.wikipedia.org/wiki/Subaru_FB_engine (FB25D DI 182hp: 2019 Forester, 2020+ Legacy/Outback; FB25B 170-175 predecessor) + reman-engine.com/size/2.5-liter-subaru (FB25B 170hp 2011-18 Forester / 2013-19 Legacy+Outback)",
    "FAWIKI": "https://en.wikipedia.org/wiki/Subaru_FA_engine (FA24F turbo: Ascent/Legacy XT/Outback XT 260hp, 2022+ WRX 271hp; FA20 = 2.0 D-4S; FA24 = 2.4 D-4S GR86)",
    "FORESTERXT": "https://www.torquenews.com/1084/subaru-gives-3-reasons-why-they-axed-popular-forester-20xt (Forester 2.0XT = FA20 turbo 250hp, axed after 2018; 2019+ Forester = 2.5 DI 182hp only)",
    "WRXVA": "https://www.kbb.com/subaru/wrx/2015/ + jdcustomsusa.com (2015 WRX = FA20DIT 268hp; STI EJ257 305hp through 2018, 310hp 2019-2021) + usecarscout.com (VA-gen powertrain table)",
    "IMPREZAWRX": "https://www.edmunds.com/subaru/impreza-wrx/2013/review/ (2013 Impreza WRX = 2.5T 265hp - WRX was Impreza-badged 2012-13) + crawfordperformance.com (2005 WRX = EJ205 227hp) + jspecauto.com (EJ205 = 2002-05 WRX)",
    "XVHYB": "https://motorweek.org/road_tests/2014_subaru_xv_crosstrek_hybrid/ + cars.usnews.com (2014 XV Crosstrek Hybrid = 2.0 + motor, 160hp combined, mild hybrid)",
    "SOLTERRA": "https://www.edmunds.com/subaru/solterra/2023/ + https://www.kbb.com/subaru/solterra/2023/ (Solterra = dual-motor AWD BEV 215hp, 72.8kWh; only powertrain)",
    "IMPREZARS": "https://www.caranddriver.com/reviews/a43482394/2024-subaru-impreza-rs-drive/ (2024 Impreza RS = 2.5 DI flat-4 182hp; base = 2.0)",
    "SUBARUVOCAB": "DB Subaru vocabulary (Euro catalog): EJ253 2.5 SOHC 170 (n=6), EJ255 2.5T (n=14), EJ257 2.5T STi (n=12), EJ205 2.0T (n=8), EZ30D 3.0 H6 241 (n=6), EZ36D 3.6 H6 258 (n=3), FB20B 2.0 150 (n=1), FB25 '2.5 (est.)' 173 (n=2, relabeled FB25B), FA20 D-4S 197 (n=11), FA24 GR86 228 (n=4)",
    "SUBARUHIST": "US Subaru lineup history (Outback 2.5i EJ253 175hp 05-09 / 170hp 10-12; Legacy 3.0R + Outback 3.0R EZ30D 245; Tribeca 3.6R EZ36D 256 from 2008; B9 Tribeca EZ30D 245; Impreza 2.5i EJ253 173 (06-07) / 170 (08-11); 2012+ Impreza 2.0 FB20B 148/152; Crosstrek 148->152hp 2018; BRZ FA20 200hp; Forester 2.5X EJ253 173 (05-08) / 170 (09-13); Baja 2.5 NA 165 vs Turbo 210)",
}

NEW_ENGINES = {
    "FA20F": ("2.0 Boxer Turbo DIT (FA20F: WRX 2015-21 268hp / Forester XT 2014-18 250hp)", "Petrol", 1998, 268, 4),
    "FA24F": ("2.4 Boxer Turbo DIT (FA24F: Ascent/Legacy XT/Outback XT 260hp / WRX 2022+ 271hp)", "Petrol", 2387, 260, 4),
    "FB25D": ("2.5 Boxer DI (FB25D: Forester 2019+ / Legacy+Outback 2020+ / Crosstrek Sport / Impreza RS, 182hp)", "Petrol", 2498, 182, 4),
    "XV Crosstrek Hybrid (2014-15)": ("2.0 FB20B + electric motor (XV Crosstrek Hybrid mild hybrid, 160hp combined)", "Hybrid", 1995, 160, 4),
    "Crosstrek Hybrid PHEV": ("2.0 FB20D DI + dual motors (Crosstrek Hybrid PHEV 2019-23, 148hp combined)", "Hybrid", 1995, 148, 4),
    "Solterra BEV": ("Dual AC synchronous motors 72.8kWh (Solterra AWD BEV, 215hp)", "Electric", None, 215, None),
}

ROW_FIXES = {
    "EJ253": {"engine_type": "2.5 Boxer SOHC (EJ253: Impreza 2.5i 173/170 / Outback 175/170 / Legacy / Forester 2.5X 173/170hp)"},
    "EJ205": {"engine_type": "2.0 Boxer Turbo (EJ205: Impreza WRX 2002-05 US 227hp / Euro-JDM WRX 218)"},
    "EZ30D": {"engine_type": "3.0 H6 EZ30D (Outback 3.0R / Legacy 3.0R / B9 Tribeca, 245hp)", "power_hp": 245},
    "EZ36D": {"engine_type": "3.6 H6 EZ36D (Tribeca 3.6R 2008+ / Legacy+Outback 3.6R 2010-19, 256hp)", "power_hp": 256},
    "FB20B": {"engine_type": "2.0 Boxer (FB20B: Impreza/XV/Crosstrek 148-152hp)", "power_hp": 152},
    "FB25": {"engine_type": "2.5 Boxer (FB25B: Legacy+Outback 2013-19 173-175 / Forester 2011-18 170hp)", "power_hp": 175},
    "FA20": {"engine_type": "2.0 Boxer D-4S (FA20: BRZ/GR86-86, 200hp US / 197 Euro)", "power_hp": 200},
    "FA24": {"engine_type": "2.4 Boxer D-4S (FA24: BRZ/GR86 2022+, 228hp)"},
}

FUEL_FIX_BY_TARGET = {"Solterra BEV": "Electric"}

IDENTITY = {
    "EJ253": ("Petrol", 2500), "EJ255": ("Petrol", 2500), "EJ257": ("Petrol", 2500),
    "EJ205": ("Petrol", 1994), "EZ30D": ("Petrol", 3000), "EZ36D": ("Petrol", 3630),
    "FB20B": ("Petrol", 1995), "FB25": ("Petrol", 2498), "FA20": ("Petrol", 2000),
    "FA24": ("Petrol", 2387),
}

# (MODEL-upper, y0, y1, cc, target, evidence, pfix)   cc=None = bare
R = [
    ("ASCENT", 2019, 2025, None, "FA24F", "Ascent = 2.4T FA24F 260hp sole [FAWIKI][NEW]", 260),
    ("B9", 2006, 2007, None, "EZ30D", "B9 Tribeca = 3.0 H6 EZ30D 245hp sole [SUBARUHIST][ROW_FIX EZ30D]", 245),
    ("BRZ", 2013, 2020, None, "FA20", "BRZ gen1 (incl. 2015 trims) = FA20 D-4S 200hp [SUBARUHIST][ROW_FIX FA20]", 200),
    ("BRZ", 2022, 2025, None, "FA24", "BRZ gen2 = FA24 D-4S 228hp [FAWIKI][SUBARUHIST]", 228),
    ("CROSSTREK", 2017, 2017, None, "FB20B", "Crosstrek gen1 2017 = 2.0 148hp [SUBARUHIST][ROW_FIX FB20B]", 148),
    ("CROSSTREK", 2018, 2020, None, "FB20B", "Crosstrek 2018-20 = 2.0 152hp [SUBARUHIST][ROW_FIX FB20B]", 152),
    ("CROSSTREK", 2016, 2016, 2000, "FB20B", "Crosstrek 2016 2.0 = 148hp [SUBARUHIST]", 148),
    ("CROSSTREK", 2022, 2025, 2000, "FB20B", "Crosstrek 2.0 (2000CC) = 152hp [SUBARUHIST]", 152),
    ("CROSSTREK", 2021, 2025, 2500, "FB25D", "Crosstrek Sport 2.5 DI = FB25D 182hp [FBWIKI][IMPREZARS-family][NEW]", 182),
    ("FORESTER", 2005, 2008, None, "EJ253", "Forester 2.5X 2005-08 = EJ253 173hp [SUBARUHIST]", 173),
    ("FORESTER", 2009, 2013, None, "EJ253", "Forester 2.5X 2009-13 = EJ253 170hp [SUBARUHIST]", 170),
    ("FORESTER", 2019, 2025, None, "FB25D", "Forester 2019+ = 2.5 DI 182hp sole (XT axed) [FORESTERXT][FBWIKI][NEW]", 182),
    ("FORESTER", 2014, 2018, 2000, "FA20F", "Forester 2.0XT 2014-18 = FA20 turbo 250hp [FORESTERXT][NEW FA20F]", 250),
    ("FORESTER", 2018, 2018, 2500, "FB25", "Forester 2.5i 2018 = FB25B 170hp [FBWIKI]", 170),
    ("IMPREZA", 2006, 2007, None, "EJ253", "Impreza 2.5i 2006-07 = EJ253 173hp (lemon 'Impreza' excludes WRX) [SUBARUHIST]", 173),
    ("IMPREZA", 2008, 2011, None, "EJ253", "Impreza 2.5i 2008-11 = EJ253 170hp [SUBARUHIST]", 170),
    ("IMPREZA", 2014, 2016, None, "FB20B", "Impreza 2014-16 = 2.0 148hp [SUBARUHIST]", 148),
    ("IMPREZA", 2017, 2023, None, "FB20B", "Impreza 2017-23 = 2.0 152hp [SUBARUHIST]", 152),
    ("IMPREZA", 2005, 2005, 2000, "EJ205", "Impreza 2000CC 2005 = WRX EJ205 227hp (WRX was Impreza-badged) [IMPREZAWRX]", 227),
    ("IMPREZA", 2012, 2013, 2000, "FB20B", "Impreza 2012-13 = 2.0 148hp (2.0-only US) [SUBARUHIST]", 148),
    ("IMPREZA", 2024, 2025, 2000, "FB20B", "Impreza base 2.0 2024-25 = 152hp [IMPREZARS]", 152),
    ("IMPREZA", 2012, 2013, 2500, "EJ255", "Impreza 2500CC 2012-13 = Impreza WRX EJ255 265hp [IMPREZAWRX]", 265),
    ("IMPREZA", 2024, 2025, 2500, "FB25D", "Impreza RS 2024-25 = 2.5 DI 182hp [IMPREZARS][NEW FB25D]", 182),
    ("LEGACY", 2008, 2012, 2500, "EJ253", "Legacy 2.5i 2008-12 = EJ253 170hp [SUBARUHIST]", 170),
    ("LEGACY", 2013, 2014, 2500, "FB25", "Legacy 2.5i 2013-14 = FB25B 173hp [FBWIKI][SUBARUHIST]", 173),
    ("LEGACY", 2015, 2019, 2500, "FB25", "Legacy 2.5i 2015-19 = FB25B 175hp [FBWIKI][SUBARUHIST]", 175),
    ("LEGACY", 2020, 2025, 2500, "FB25D", "Legacy 2020+ = FB25D 182hp [FBWIKI][NEW]", 182),
    ("LEGACY", 2008, 2009, 3000, "EZ30D", "Legacy 3.0R = EZ30D 245hp [SUBARUHIST][ROW_FIX EZ30D]", 245),
    ("LEGACY", 2010, 2019, 3600, "EZ36D", "Legacy 3.6R = EZ36D 256hp [SUBARUHIST][ROW_FIX EZ36D]", 256),
    ("LEGACY", 2020, 2024, 2400, "FA24F", "Legacy XT/Sport 2.4T = FA24F 260hp [FAWIKI][NEW]", 260),
    ("OUTBACK", 2005, 2009, 2500, "EJ253", "Outback 2.5i 2005-09 = EJ253 175hp [SUBARUHIST]", 175),
    ("OUTBACK", 2010, 2012, 2500, "EJ253", "Outback 2.5i 2010-12 = EJ253 170hp [SUBARUHIST]", 170),
    ("OUTBACK", 2013, 2014, 2500, "FB25", "Outback 2.5i 2013-14 = FB25B 173hp [FBWIKI][SUBARUHIST]", 173),
    ("OUTBACK", 2015, 2019, 2500, "FB25", "Outback 2.5i 2015-19 = FB25B 175hp [FBWIKI][SUBARUHIST]", 175),
    ("OUTBACK", 2020, 2025, 2500, "FB25D", "Outback 2020+ = FB25D 182hp [FBWIKI][NEW]", 182),
    ("OUTBACK", 2005, 2009, 3000, "EZ30D", "Outback 3.0R = EZ30D 245hp [SUBARUHIST][ROW_FIX EZ30D]", 245),
    ("OUTBACK", 2010, 2019, 3600, "EZ36D", "Outback 3.6R = EZ36D 256hp [SUBARUHIST][ROW_FIX EZ36D]", 256),
    ("OUTBACK", 2020, 2024, 2400, "FA24F", "Outback XT 2.4T = FA24F 260hp [FAWIKI][NEW]", 260),
    ("SOLTERRA", 2023, 2025, None, "Solterra BEV", "Solterra = dual-motor BEV 215hp sole (fuel col -> Electric) [SOLTERRA][NEW]", 215),
    ("TRIBECA", 2008, 2014, None, "EZ36D", "Tribeca 2008+ = 3.6R EZ36D 256hp sole [SUBARUHIST][ROW_FIX EZ36D]", 256),
    ("WRX", 2016, 2018, None, "FA20F", "WRX 2016-18 = FA20F 268hp (STI slugged/2.5 elsewhere) [WRXVA][NEW FA20F]", 268),
    ("WRX", 2022, 2025, None, "FA24F", "WRX 2022+ = FA24F 271hp [FAWIKI][NEW FA24F]", 271),
    ("WRX", 2019, 2021, 2000, "FA20F", "WRX 2.0T (2000CC) = FA20F 268hp [WRXVA]", 268),
    ("WRX", 2019, 2021, 2500, "EJ257", "WRX STI 2.5T (2500CC) = EJ257 310hp [WRXVA]", 310),
    ("XV", 2013, 2013, None, "FB20B", "XV Crosstrek 2013 = 2.0 148hp [SUBARUHIST][ROW_FIX FB20B]", 148),
    ("XV", 2015, 2015, 2000, "FB20B", "XV Crosstrek 2.0 = 148hp [SUBARUHIST]", 148),
]

SKIP_REASONS = {
    ("BAJA"): "Baja 2005-06 bare: 2.5 NA 165hp vs 2.5 Turbo 210hp both offered - cannot resolve",
    ("LEGACY"): "Legacy 2005-07 bare: 2.5i EJ253 vs GT 2.5T EJ255 both 2.5 - ambiguous",
}

def parse_code(code):
    m = re.match(r"^LEMON_SUBARU_(.+)$", code)
    if not m: return None
    toks = m.group(1).split("_")
    yi = next((i for i, t in enumerate(toks) if re.fullmatch(r"(19|20)\d\d", t)), None)
    if yi is None: return None
    year = int(toks[yi])
    cc = None
    model_toks = []
    for t in toks[:yi]:
        if re.fullmatch(r"\d+CC", t): cc = int(t[:-2])
        elif not re.fullmatch(r"VIN[A-Z0-9]", t): model_toks.append(t)
    return " ".join(model_toks), year, cc, "_".join(toks[yi+1:])

def decide(model, year, cc, code, fuel):
    mu, cu = model.upper(), code.upper()
    # intercepts: fuel-column and trim-slug rows
    if mu == "XV" and fuel == "Hybrid":
        return ("XV Crosstrek Hybrid (2014-15)", "XV Crosstrek Hybrid (fuel col Hybrid) = 2.0 + motor 160hp combined [XVHYB][NEW]", None, 160)
    if mu == "CROSSTREK" and fuel == "Hybrid":
        return ("Crosstrek Hybrid PHEV", "Crosstrek Hybrid PHEV (fuel col Hybrid) = 2.0 DI + motors 148hp combined [XVHYB-family][NEW]", None, 148)
    if mu == "IMPREZA" and year == 2015 and cu.endswith(("20I4D", "BASE4", "LIMIT", "PREMI", "SPORT")):
        return ("FB20B", "Impreza 2015 trims (2.0i 4dr/Base/Limited/Premium/Sport) = 2.0 148hp [SUBARUHIST]", None, 148)
    if mu == "WRX" and year == 2015:
        if "STI" in cu:
            return ("EJ257", "WRX STI 2015 = EJ257 305hp [WRXVA]", None, 305)
        return ("FA20F", "WRX 2015 (Base/Limited/Premium trims) = FA20F 268hp [WRXVA][NEW FA20F]", None, 268)
    if mu == "IMPREZA" and year == 2005 and cc == 2500:
        return (None, "Impreza 2500CC 2005: 2.5 RS (EJ253 173) vs STI (EJ257 300) both 2.5 - ambiguous", None, None)
    if mu == "BRZ" and year == 2015:
        return ("FA20", "BRZ 2015 trims (Limited/Premium/Series.Blue) = FA20 200hp [SUBARUHIST]", None, 200)
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands:
        return (None, SKIP_REASONS.get(mu, f"no rule for Subaru {model} {year} cc={cc}"), None, None)
    r = cands[0]
    fuel_fix = FUEL_FIX_BY_TARGET.get(r[4])
    if fuel_fix and fuel == fuel_fix: fuel_fix = None
    return (r[4], r[5], fuel_fix, r[6])

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == 2484, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 2484 (workspace rewind?)"
    base_eng = cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0]
    assert base_eng == 8047, f"BASELINE MISMATCH: engines={base_eng}, expected 8047"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Subaru' AND engine_code LIKE 'LEMON%' ORDER BY car_model, car_year, engine_code""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        p = parse_code(code)
        assert p, f"unparseable code: {code}"
        pm, py, cc, post = p
        assert pm.upper() == model.upper(), f"model parse mismatch {code} vs {model}"
        tgt, note, fuel_fix, pfix = decide(model, year, cc, code, fuel)
        if tgt is None: skips.append((vid, model, year, code, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix, pfix))
    print(f"Subaru LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print(f"  SKIP: {s[1]} {s[2]} [{s[3]}] - {s[4]}")
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(30): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter((d[4], d[6]) for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"
    for tgt, (efuel, ecc) in IDENTITY.items():
        cc_fix = ROW_FIXES.get(tgt, {}).get("displacement_cc")
        row = cur.execute("SELECT fuel, displacement_cc FROM engines WHERE engine_code=?", (tgt,)).fetchone()
        if row is None: continue
        if row[0] and efuel and row[0] != efuel:
            raise AssertionError(f"IDENTITY CONFLICT {tgt}: engines.fuel={row[0]}, expected {efuel}")
        if cc_fix and row[1] and row[1] != cc_fix:
            print(f"  identity: {tgt} cc {row[1]} junk -> queued ROW_FIX to {cc_fix}"); continue
        if row[1] and ecc and abs(row[1] - ecc) / ecc > 0.07:
            raise AssertionError(f"IDENTITY CONFLICT {tgt}: engines.cc={row[1]}, expected ~{ecc}")
    print("identity assert: OK")

    if not apply:
        with open("database_enriched/csv_exports/38_lemon_batch21_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
            for d in decisions: w.writerow([d[0],"Subaru",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Subaru",s[1],s[2],s[3],"","","SKIP",s[4]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step30_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP30_VERIFIED')""",
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
    tgts = tuple(set(d[4] for d in decisions))
    cur.execute(f"""UPDATE vehicle_variants SET engine_power_hp=
        (SELECT power_hp FROM engines WHERE engine_code=vehicle_variants.engine_code)
        WHERE engine_code IN ({','.join('?'*len(tgts))}) AND engine_power_hp IS NULL""", tgts)

    with open("database_enriched/csv_exports/38_lemon_batch21_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
        for d in decisions: w.writerow([d[0],"Subaru",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON Subaru remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand='Subaru' AND engine_code LIKE 'LEMON%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
