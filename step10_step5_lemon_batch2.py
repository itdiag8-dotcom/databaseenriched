#!/usr/bin/env python3
"""
STEP 10 = USER-PLAN STEP 5 (batch 2): LEMON synthetic engine-code replacement.
Scope: Mopar mainline - Grand Cherokee, Wrangler, Gladiator, Cherokee, Liberty, Commander,
Durango, Charger, Challenger, Magnum, Dakota, Nitro, Chrysler 300, Aspen, Ram 1500.

Method identical to step 9 (batch 1): (model, year, cc, VIN-8th char, fuel) -> real OEM code,
web-verified (see CITATIONS). Specs migrate onto real codes; LEMON rows retired.
Gated: --apply to write. Backup: backups/car_database_backup_pre_step10_<date>.db
"""
import sqlite3, sys, re, shutil, csv, os
from datetime import date
from collections import defaultdict
import importlib.util

spec = importlib.util.spec_from_file_location("s9", os.path.join(os.path.dirname(__file__), "step9_step5_lemon_replacement.py"))
s9 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s9)
parse_code = s9.parse_code

DB = "database_enriched/car_database.db"
APPLY = "--apply" in sys.argv

CITATIONS = {
    "HEMI": "https://en.wikipedia.org/wiki/Chrysler_Hemi_engine (5.7 apps + 2009 VCT revision; 6.1 SRT8 apps 2005-2010; 6.2 Hellcat apps; 6.4/392 Apache apps + 2015 485hp)",
    "POWERTech": "https://en.wikipedia.org/wiki/Chrysler_PowerTech_engine (4.7 V8: Dakota 2000-2007, Durango 2000-2009, GC 1999-2009, Commander 2006-2009, Aspen 2007-2009)",
    "LEMON2015": "lemon_crawl_2015.jsonl (ground truth: 3.6L VIN G, 5.7L VIN T, 3.0L VIN M EcoDiesel, 2.4L VIN B = Eng CD ED6/ED8, 3.2L VIN S, 2.0L VIN N; Challenger Eng CD EZC/EZH/ESG/ESH)",
    "RAMVIN": "https://truckguider.com/dodge-ram-engine-codes-by-year-chart/",
    "HURRICANE": "https://www.edmartincdjr.com/ram-1500-3.0l-hurricane-twin-turbo-i6-engine-overview + https://www.almachryslerjeepdodgeram.com/dodge-ram-hurricane-engine-specs/ (3.0 twin-turbo I6 replaces 5.7 HEMI for 2025 Ram 1500; SO 420hp)",
    "RAMOIL": "https://www.jcofontario.com/service-department/service-and-parts-tips/ram-2500-oil-type/",
}

# engine rows to create when missing: code -> (engine_type, fuel, cc, hp, cyl)
NEW_ENGINES = {
    "ESH": ("6.4 V8 HEMI SRT 392 (485hp)", "Petrol", 6415, 485, 8),
    "6.2 Hellcat V8": ("6.2 V8 HEMI supercharged (Hellcat)", "Petrol", 6166, 707, 8),
    "3.5 V6 (LX)": ("3.5 V6 SOHC (LX cars)", "Petrol", 3518, 250, 6),
    "3.2 Pentastar": ("3.2 V6 Pentastar", "Petrol", 3239, 271, 6),
    "2.0 Turbo GME": ("2.0 I4 Turbo GME-T4", "Petrol", 1995, 268, 4),
    "2.0 Turbo GME (4xe)": ("2.0 I4 Turbo GME-T4 PHEV (4xe)", "Hybrid", 1995, 375, 4),
    "5.7 HEMI Hybrid": ("5.7 V8 HEMI two-mode hybrid", "Hybrid", 5654, 399, 8),
    "4.0 I6 (AMC)": ("4.0 I6 PowerTech (AMC)", "Petrol", 3956, 190, 6),
    "2.5 I4 (AMC)": ("2.5 I4 PowerTech (AMC)", "Petrol", 2464, 120, 4),
    "R428": ("2.8 I4 CRD turbodiesel (VM)", "Diesel", 2776, 150, 4),
    "3.0 CRD (OM642)": ("3.0 V6 CRD turbodiesel (Mercedes OM642)", "Diesel", 2987, 215, 6),
    "3.0 Hurricane I6": ("3.0 I6 Hurricane twin-turbo (SO)", "Petrol", 2993, 420, 6),
}

ROW_FIXES = {
    "EDZ": {"engine_type": "2.4 PowerTech I4", "cylinders": 4},          # was '2.4 V6' - wrong config
    "EZC": {"power_hp": 340, "engine_type": "5.7 V8 HEMI (LX, pre-VCT)"}, # 300C/Magnum R/T 340hp [HEMI]
    "EXL": {"engine_type": "3.0 V6 EcoDiesel (VM A630)", "displacement_cc": 2987},
}

TARGETS = {
    "Dodge": {"Durango", "Charger", "Challenger", "Dakota", "Magnum", "Nitro"},
    "Chrysler": {"300", "Aspen"},
    "Jeep": {"Grand Cherokee", "Wrangler", "Gladiator", "Cherokee", "Liberty", "Commander"},
    "Ram": {"1500"},
}

P36 = "3.6 Pentastar"
HEMI_SPLIT_CARS = ("Charger", "300", "Magnum")   # pre-2009 EZC vs 2009+ EZH
HEMI_SPLIT_TRUCKS = ("Durango", "Grand Cherokee", "Commander", "Aspen")  # pre-2009 EZD vs 2009+ EZH

def decide(brand, model, year, cc, vin, fuel, trim):
    """Return (new_code, note) or (None, reason)."""
    f = (fuel or "").lower()
    diesel = "diesel" in f
    hybrid = "hybrid" in f

    # ---------- 5.7 HEMI ----------
    if cc == 5700:
        if model == "Aspen" and hybrid: return ("5.7 HEMI Hybrid", "Aspen HEV 5.7 two-mode 399hp [HEMI]")
        if vin == "T": return ("EZH", "5.7 HEMI VCT = VIN T 2009+ [LEMON2015][HEMI]")
        if model == "Challenger":  # 2009+ only, all VCT
            return ("EZH", "Challenger R/T 5.7 = VCT EZH 2009+ [HEMI]")
        if model in HEMI_SPLIT_CARS:
            return ("EZC" if year <= 2008 else "EZH", "LX 5.7: EZC 340hp pre-VCT, EZH VCT 2009+ [HEMI]")
        if model in HEMI_SPLIT_TRUCKS or brand == "Ram":
            return ("EZD" if year <= 2008 else "EZH", "truck/SUV 5.7: EZD 345hp pre-VCT, EZH VCT 2009+ [HEMI]")
        return (None, "5.7 unmatched")
    # ---------- 6.1 SRT8 ----------
    if cc == 6100: return ("ESF", "6.1 HEMI SRT8 425hp 2005-2010 [HEMI]")
    # ---------- 6.4 ----------
    if cc == 6400:
        if model == "Wrangler": return ("ESA", "Wrangler Rubicon 392 = 6.4 Apache 470hp 2021+ [HEMI]")
        if model == "Durango": return ("ESH", "Durango SRT 6.4 475hp 2018+ [HEMI]")
        return ("ESG" if year <= 2014 else "ESH",
                "6.4 392: Apache 470hp (ESG) 2011-2014; 485hp (ESH) 2015+ [HEMI][LEMON2015]")
    # ---------- 6.2 Hellcat ----------
    if cc == 6200:
        return ("6.2 Hellcat V8",
                "6.2 supercharged: Challenger/Charger 2015+, GC Trackhawk 2018-21, Durango SRT Hellcat 2021+, Ram TRX 2021-24 [HEMI]")
    # ---------- 3.6 Pentastar ----------
    if cc == 3600 and year >= 2011:
        return (P36, "3.6 Pentastar = VIN G (2011+ Mopar) [LEMON2015]")
    # ---------- LX 3.5 / 2.7 ----------
    if cc == 3500 and model in ("Charger", "Challenger", "300", "Magnum"):
        return ("3.5 V6 (LX)", "LX 3.5 SOHC V6 250hp 2005-2010 [HEMI era/PowerTech family]")
    if cc == 2700 and model in ("Charger", "300", "Magnum"):
        return ("EER", "2.7 LX V6 [DB code EER]")
    # ---------- 4.7 PowerTech ----------
    if cc == 4700: return ("EVA", "4.7 PowerTech V8 [POWERTech]")
    # ---------- 3.7 PowerTech ----------
    if cc == 3700:
        if model == "Dakota" and year <= 2004: return (None, "Dakota gen3 (3.7) started 2005 - 2004 row unverified")
        return ("EKG", "3.7 PowerTech V6 [POWERTech]")
    # ---------- Magnum-era trucks ----------
    if cc == 3900: return ("3.9 Magnum V6", "3.9 Magnum V6 through 2003 [RAMVIN]")
    if cc == 5200: return ("5.2 Magnum V8", "5.2 Magnum V8 through 2003 [RAMVIN]")
    if cc == 5900:
        if year <= 2003: return ("5.9 Magnum V8", "5.9 Magnum V8 through 2003 [RAMVIN]")
        return (None, "5.9 petrol after 2003 - conflict")
    # ---------- AMC-era Jeep engines ----------
    if cc == 4000 and model in ("Wrangler", "Grand Cherokee", "Cherokee"):
        return ("4.0 I6 (AMC)", "4.0 AMC I6 (through 2004 GC / 2006 Wrangler) [POWERTech-era Jeep]")
    if cc == 2500 and model in ("Wrangler", "Cherokee", "Dakota"):
        return ("2.5 I4 (AMC)", "2.5 AMC I4 base (TJ/XJ/Dakota through 2002-2004) [AMC family]")
    # ---------- Jeep 2.4 ----------
    if cc == 2400 and model in ("Wrangler", "Liberty"):
        return ("EDZ", "2.4 PowerTech I4 (TJ 2003-2006 / Liberty KJ) [LEMON2015-era]")
    # ---------- Jeep 3.0 diesels ----------
    if cc == 3000 and model == "Grand Cherokee":
        if vin == "M" and year >= 2014: return ("EXL", "3.0 EcoDiesel = VIN M [LEMON2015]")
        if 2007 <= year <= 2009: return ("3.0 CRD (OM642)", "WK 3.0 CRD = Mercedes OM642 2007-2009 [OM642 family]")
        return (None, "GC 3.0 combo unmatched")
    if cc == 3000 and vin == "M": return ("EXL", "3.0 EcoDiesel = VIN M [LEMON2015]")
    # ---------- Ram 1500 / Hurricane ----------
    if brand == "Ram" and cc == 3000:
        if year >= 2025: return ("3.0 Hurricane I6", "2025 Ram 3.0 = Hurricane twin-turbo I6 (only 3.0; EcoDiesel ended 2023) [HURRICANE]")
        if year <= 2023: return ("EXL", "3.0 EcoDiesel [LEMON2015]")
        return (None, "Ram 3.0 2024 - no 3.0 offered")
    # ---------- 2.0 GME turbo ----------
    if cc == 2000 and model in ("Wrangler", "Cherokee"):
        return ("2.0 Turbo GME", "2.0 GME-T4 turbo = VIN N [LEMON2015]")
    if cc == 2000 and model == "Grand Cherokee" and year >= 2022:
        return ("2.0 Turbo GME (4xe)", "GC 2.0 2022+ = 4xe PHEV only (375hp combined) [GME family]")
    # ---------- Pentastar 3.2 (Cherokee KL) ----------
    if cc == 3200 and model == "Cherokee":
        if vin == "S": return ("3.2 Pentastar", "3.2 Pentastar = VIN S [LEMON2015]")
        if not vin: return ("3.2 Pentastar", "only 3.2 at this size in KL [LEMON2015]")
        return (None, f"Cherokee 3.2 VIN {vin} unverified - skipped")
    if cc == 2400 and model == "Cherokee":
        return ("ED6", "2.4 TigerShark = VIN B (ED6 gas / ED8 flex - ED6 assumed) [LEMON2015]")

    # ---------- model-specific bare/no-VIN ----------
    if model == "Wrangler" and cc is None:
        if trim and year == 2015: return (P36, "JK 2015 = 3.6 Pentastar [LEMON2015]")
        if 2007 <= year <= 2011: return ("EGH", "JK 3.8 V6 2007-2011 [EGH]")
        if 2012 <= year <= 2018: return (P36, "JK 3.6 Pentastar 2012+ [LEMON2015]")
        return (None, "wrangler bare unmatched")
    if model == "Gladiator" and cc is None: return (P36, "Gladiator only gas engine = 3.6 Pentastar [LEMON2015]")
    if model == "Liberty" and cc is None and 2007 <= year <= 2012:
        return ("EKG", "Liberty KK gas = 3.7 only [POWERTech]")
    if cc == 2800 and model == "Liberty": return ("R428", "Liberty KJ 2.8 CRD (VM R428) 2005-2006 [VM family]")
    if model == "Nitro" and cc == 4000: return (None, "Nitro 4.0 V6 (EVJ?) unverified - skipped")
    if model == "Charger" and cc is None: return (None, "charger bare unmatched")
    if model == "Challenger" and cc is None: return (None, "challenger bare (2008: 3.5 vs 6.1) - skipped")
    if model == "Grand Cherokee" and cc is None and not trim:
        return (None, "GC bare 2022+ (3.6 vs 4xe) - skipped")
    if brand == "Ram" and cc == 4700 and vin == "P": return ("EVA", "4.7 flex (VIN P) [RAMVIN]")
    if brand == "Ram" and cc == 3600: return (P36, "3.6 Pentastar [LEMON2015]")
    if brand == "Ram" and cc == 5700: return ("EZH", "5.7 HEMI VCT EZH 2013+ [HEMI][RAMOIL]")

    return (None, "batch2 combo unmatched")

FUEL_OVERRIDE = {
    "EXL": "Diesel", "R428": "Diesel", "3.0 CRD (OM642)": "Diesel",
    "2.0 Turbo GME (4xe)": "Hybrid", "5.7 HEMI Hybrid": "Hybrid",
}

def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys=ON")

    rows = list(cur.execute("""SELECT id, car_brand, car_model, car_year, fuel, engine_code
        FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'"""))
    decisions, unmapped = [], []
    for vid, brand, model, year, fuel, code in rows:
        if model not in TARGETS.get(brand, set()):
            continue
        p = parse_code(code)
        if not p:
            unmapped.append((vid, brand, model, year, code, "unparseable")); continue
        cc, vin, ycode, trim = p
        new_code, note = decide(brand, model, year, cc, vin, fuel, trim)
        if not new_code:
            unmapped.append((vid, brand, model, year, code, note)); continue
        ff = FUEL_OVERRIDE.get(new_code)
        if ff and (fuel or "").lower() != ff.lower() and not (fuel and ff.lower() in fuel.lower()):
            fuel_fix = ff
        else:
            fuel_fix = None
        decisions.append((vid, brand, model, year, code, new_code, note, fuel_fix))

    print(f"in-scope mapped: {len(decisions)} | unmapped/skipped: {len(unmapped)}")
    reasons = defaultdict(list)
    for vid, brand, model, year, code, why in unmapped:
        reasons[(brand, model, why)].append((year, code))
    print("=== UNMAPPED (skipped) groups ===")
    for k in sorted(reasons, key=lambda k: -len(reasons[k])):
        print(f"  {k}: {len(reasons[k])} rows  e.g. {reasons[k][:3]}")

    if not APPLY:
        with open("database_enriched/csv_exports/18_lemon_batch2_decisions_DRYRUN.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions:
                w.writerow(list(d[:5]) + [d[5], d[7] or "", d[6]])
        print("DRY RUN - no changes. Re-run with --apply.")
        con.close(); return

    # ---------- APPLY ----------
    existing = {r[0] for r in cur.execute("SELECT engine_code FROM engines")}
    missing = {d[5] for d in decisions} - existing - set(NEW_ENGINES.keys())
    if missing:
        print("FATAL: targets missing from engines and NEW_ENGINES:", missing); sys.exit(1)

    bak = f"database_enriched/backups/car_database_backup_pre_step10_{date.today().isoformat()}.db"
    shutil.copy(DB, bak)
    print(f"backup: {bak}")

    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,))
        if not cur.fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP10_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
    for code, fixes in ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))

    lemon_retired = defaultdict(list)
    for vid, brand, model, year, old, new, note, fuel_fix in decisions:
        cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=COALESCE(?, fuel) WHERE id=?", (new, fuel_fix, vid))
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=COALESCE(engine_power_hp,
                        (SELECT power_hp FROM engines WHERE engine_code=?)),
                        engine_type=COALESCE(engine_type, (SELECT engine_type FROM engines WHERE engine_code=?))
                        WHERE id=?""", (new, new, vid))
        lemon_retired[old].append((vid, year, brand, model))

    spec_cols_s = [c[1] for c in cur.execute("PRAGMA table_info(engine_service_specs)")]
    spec_cols_t = [c[1] for c in cur.execute("PRAGMA table_info(engine_technical_specs)")]
    def merge_specs(table, cols, lemon_code, target):
        cols = [c for c in cols if c != "engine_code"]
        cur.execute(f"SELECT {','.join(cols)} FROM {table} WHERE engine_code=?", (lemon_code,))
        src = cur.fetchone()
        if src is None: return
        cur.execute(f"SELECT 1 FROM {table} WHERE engine_code=?", (target,))
        if cur.fetchone():
            sets = ", ".join(f"{c}=COALESCE({c}, ?)" for c in cols)
            cur.execute(f"UPDATE {table} SET {sets} WHERE engine_code=?", (*src, target))
        else:
            cur.execute(f"INSERT INTO {table} (engine_code, {','.join(cols)}) VALUES (?, {','.join('?'*len(cols))})", (target, *src))
        cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (lemon_code,))

    migrated = 0
    for lemon_code, vs in sorted(lemon_retired.items(), key=lambda kv: kv[1][0][1]):
        target = cur.execute("SELECT engine_code FROM vehicle_variants WHERE id=?", (vs[0][0],)).fetchone()[0]
        merge_specs("engine_service_specs", spec_cols_s, lemon_code, target)
        merge_specs("engine_technical_specs", spec_cols_t, lemon_code, target)
        cur.execute("SELECT count_variants FROM engines WHERE engine_code=?", (lemon_code,))
        r = cur.fetchone()
        n = r[0] if r else 0
        cur.execute("""UPDATE engines SET displacement_cc=COALESCE(displacement_cc,
              (SELECT displacement_cc FROM engines WHERE engine_code=?)),
              fuel=COALESCE(fuel, (SELECT fuel FROM engines WHERE engine_code=?)) WHERE engine_code=?""",
              (lemon_code, lemon_code, target))
        cur.execute("UPDATE engines SET count_variants=count_variants+? WHERE engine_code=?", (n, target))
        cur.execute("DELETE FROM engines WHERE engine_code=?", (lemon_code,))
        migrated += 1

    con.commit()
    print(f"variants remapped: {len(decisions)} | lemon engine codes retired: {migrated}")

    with open("database_enriched/csv_exports/18_lemon_batch2_decisions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions:
            w.writerow(list(d[:5]) + [d[5], d[7] or "", d[6]])

    print("\n=== VERIFY ===")
    scope_pairs = [(b, m) for b in TARGETS for m in TARGETS[b]]
    ph = ",".join(["(?,?)"] * len(scope_pairs))
    q = f"SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%' AND (car_brand, car_model) IN ({ph})"
    print("remaining LEMON in scope:", cur.execute(q, [x for p in scope_pairs for x in p]).fetchone()[0])
    print("total LEMON remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON' || '%'").fetchone()[0])
    print("engines count:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("v_vehicle_with_service:", cur.execute("SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0])
    bad = cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0]
    print("orphan variant->engine refs (1 pre-existing expected):", bad)
    con.close()

if __name__ == "__main__":
    main()
