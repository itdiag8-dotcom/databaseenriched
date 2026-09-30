"""Step 18 (user-plan Step 5, batch 9): replace LEMON_TOYOTA codes with real OEM engine codes.
471 rows, 31 models. Signals: cc + VIN chars + trims + lemon fuel column (hybrid flags).
New: 2GR-FKS, M20A-FKS/XS, T24A-FTS, V35A-FTS, FA24, G16E-GTS, Supra B48/B58 links, Mirai FCEV,
bZ4X EV. Also unifies fuel label 'Electric Motor' -> 'Electric' (DB inconsistency)."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "FRONTIER38": "unused-nissan",
    "TOYOTAVIN": "Toyota US lineup knowledge; lemon fuel column (Hybrid flags) cross-checked",
    "TUNDRAV35A": "Tundra 2022+ = V35A-FTS 3.4TT (i-FORCE 389hp gas; i-FORCE MAX hybrid 437hp shares engine)",
    "LC2024": "2024+ Land Cruiser (250 series) US = T24A-FTS i-FORCE MAX hybrid only, 326hp",
    "SEQ2022": "2023+ Sequoia = V35A-FTS i-FORCE MAX hybrid only, 437hp (2022 MY launch)",
    "SIENNA2021": "2021+ Sienna = A25A-FXS hybrid only, 245hp",
    "VENZA2021": "2021+ Venza = A25A-FXS hybrid only, 219hp",
    "CAMRY2025": "2025 Camry (XV80) = all-hybrid A25A-FXS, 225/232hp",
    "CROWN": "Crown 2023+ = A25A-FXS 236hp (XLE/Limited) or T24A-FTS MAX 340hp (Platinum)",
    "GRH": "GR86 2022+ = FA24 228hp; GR Corolla 2023+ = G16E-GTS 300hp; 86 2017-20 = FA20",
    "SUPRA": "Supra 3.0 = B58 335hp (2020) / 382hp (2021+); Supra 2.0 = B48 255hp (2020-2023)",
    "PRIUSG5": "Prius 2023+ (gen5) = M20A-FXS 194hp system; gen4 2ZR-FXE 121hp; gen3 2ZR-FXE 134hp",
}

NEW_ENGINES = {
    "2GR-FKS": ("3.5 V6 D-4S (295-308hp by model; Camry 301hp)", "Petrol", 3456, 301, 6),
    "M20A-FKS": ("2.0 I4 Dynamic Force (Corolla hatch 168hp)", "Petrol", 1987, 168, 4),
    "M20A-FXS": ("2.0 I4 Hybrid (Prius gen5, 194hp system)", "Hybrid", 1987, 194, 4),
    "T24A-FTS": ("2.4 I4 Turbo i-FORCE (228/270/278hp; MAX hybrid 326-362hp)", "Petrol", 2393, 278, 4),
    "V35A-FTS": ("3.4 V6 TwinTurbo i-FORCE (389hp; MAX hybrid 437hp)", "Petrol", 3444, 389, 6),
    "FA24": ("2.4 Boxer D-4S (GR86 228hp)", "Petrol", 2387, 228, 4),
    "G16E-GTS": ("1.6 I3 Turbo (GR Corolla 300hp)", "Petrol", 1618, 300, 3),
    "B48B20 (Supra 2.0)": ("2.0 I4 Turbo (Supra 2.0 255hp)", "Petrol", 1998, 255, 4),
    "Mirai FCEV": ("Hydrogen fuel cell + e-motor (gen1 151hp / gen2 182hp)", "Electric", None, 182, None),
    "bZ4X Electric": ("Electric motors (bZ4X 201hp FWD / 214hp AWD)", "Electric", None, 201, None),
}

ROW_FIXES = {
    "1NZ-FXE": {"fuel": "Hybrid", "engine_type": "1.5 VVT-i Hybrid (Prius gen1/2, Prius c)", "power_hp": 76},
    "2ZR-FXE": {"engine_type": "1.8 VVT-i Hybrid (Prius gen3/4, Corolla Hybrid; system 121-134hp)"},
    "A25A-FKS": {"engine_type": "2.5 I4 Dynamic Force (Camry/RAV4 gas 203hp)", "power_hp": 203},
    "A25A-FXS": {"engine_type": "2.5 I4 Hybrid (system 208-245hp)", "power_hp": 208},
    "2ZZ-GE": {"power_hp": 180},
}

# engines whose every application is hybrid/EV -> safe global fuel fix
FUEL_FIX_BY_TARGET = {
    "A25A-FXS": "Hybrid", "2ZR-FXE": "Hybrid", "1NZ-FXE": "Hybrid", "M20A-FXS": "Hybrid",
    "Mirai FCEV": "Electric", "bZ4X Electric": "Electric",
}

# (MODEL-upper, y0, y1, cc, target, evidence[, fuel_fix])
R = [
    ("4RUNNER", 2005, 2009, 4000, "1GR-FE", "4Runner 4.0 236-270hp [DB family]"),
    ("4RUNNER", 2005, 2009, 4700, "2UZ-FE", "4Runner 4.7 V8 [DB family]"),
    ("4RUNNER", 2015, 2015, None, "1GR-FE", "4Runner trims 4.0 [DB family]"),
    ("4RUNNER", 2016, 2024, None, "1GR-FE", "4Runner 4.0 only (5th gen) [DB family]"),
    ("4RUNNER", 2025, 2025, None, "T24A-FTS", "2025 4Runner 2.4T only (i-FORCE / MAX hybrid share engine) [NEW]"),
    ("4RUNNER", 2025, 2025, 2400, "T24A-FTS", "2025 4Runner (new gen) 2.4T i-FORCE 278hp (VIN A/B; MAX hybrid shares engine) [NEW]"),
    ("86", 2017, 2020, None, "FA20", "86 2.0 boxer 200/205hp [DB family]"),
    ("AVALON", 2005, 2009, None, "2GR-FE", "Avalon 3.5 only (XX30) [DB family]"),
    ("AVALON", 2015, 2018, 2500, "2ZR-FXE", "Avalon Hybrid 2.5 (system 200hp) [DB family]"),
    ("AVALON", 2015, 2018, 3500, "2GR-FE", "Avalon 3.5 268hp [DB family]"),
    ("AVALON", 2019, 2022, 2500, "A25A-FXS", "Avalon Hybrid (system 215hp) [DB family]"),
    ("AVALON", 2019, 2022, 3500, "2GR-FKS", "Avalon 3.5 301hp [NEW 2GR-FKS]"),
    ("C-HR", 2018, 2022, None, "3ZR-FE", "C-HR 2.0 144hp US [DB family]"),
    ("CAMRY", 2005, 2009, 2400, "2AZ-FE", "Camry 2.4 [DB family]"),
    ("CAMRY", 2005, 2006, 3000, "1MZ-FE", "Camry 3.0 V6 (late 1MZ) [DB family]"),
    ("CAMRY", 2005, 2008, 3300, "3MZ-FE", "Camry 3.3 V6 210hp [DB family]"),
    ("CAMRY", 2007, 2009, 3500, "2GR-FE", "Camry 3.5 268hp [DB family]"),
    ("CAMRY", 2015, 2017, 3500, "2GR-FE", "Camry 3.5 (VIN K) [DB family]"),
    ("CAMRY", 2018, 2024, 3500, "2GR-FKS", "Camry 3.5 301hp (VIN Z) [NEW 2GR-FKS]"),
    ("CAMRY", 2019, 2024, 2500, "A25A-FXS", "Camry Hybrid (system 208hp) [DB family]"),
    ("CAMRY", 2019, 2024, None, "A25A-FKS", "Camry 2.5 gas 203hp (VIN 1/6 = calibrations) [DB family]", None),
    ("CAMRY", 2025, 2025, 2500, "A25A-FXS", "2025 Camry all-hybrid 225/232hp (VIN A/B) [CAMRY2025]", "Hybrid"),
    ("CELICA", 2005, 2005, None, "2ZZ-GE", "Celica GTS 1.8 180hp (last year) [DB family]"),
    ("COROLLA", 2005, 2008, None, "1ZZ-FE", "Corolla 1.8 130hp [DB family]"),
    ("COROLLA", 2009, 2012, 1800, "2ZR-FE", "Corolla 1.8 132hp [DB family]"),
    ("COROLLA", 2009, 2012, 2400, "2AZ-FE", "Corolla XRS 2.4 158hp [DB family]"),
    ("COROLLA", 2015, 2015, None, "2ZR-FE", "Corolla 1.8 trims [DB family]"),
    ("COROLLA", 2016, 2018, None, "2ZR-FE", "Corolla 1.8 [DB family]"),
    ("COROLLA", 2019, 2025, 1800, "2ZR-FE", "Corolla 1.8 139hp [DB family]"),
    ("COROLLA", 2019, 2025, None, "2ZR-FE", "Corolla 1.8 sedan [DB family]"),
    ("COROLLA", 2019, 2025, 2000, "M20A-FKS", "Corolla hatch 2.0 168hp [NEW M20A-FKS]"),
    ("CROWN", 2023, 2025, 2400, "T24A-FTS", "Crown Platinum 2.4T MAX hybrid 340hp [CROWN]", "Hybrid"),
    ("CROWN", 2023, 2025, 2500, "A25A-FXS", "Crown XLE/Limited 2.5 hybrid 236hp [CROWN]", "Hybrid"),
    ("ECHO", 2005, 2005, None, "1NZ-FE", "Echo 1.5 108hp (last year) [DB family]"),
    ("FJ", 2007, 2009, None, "1GR-FE", "FJ Cruiser 4.0 239hp [DB family]"),
    ("GR", 2023, 2025, None, "G16E-GTS", "GR Corolla 1.6T 300hp [GRH][NEW]"),
    ("GR86", 2022, 2025, None, "FA24", "GR86 2.4 228hp [GRH][NEW]"),
    ("GRAND", 2024, 2025, 2400, "T24A-FTS", "Grand Highlander Hybrid MAX 2.4T 362hp [CROWN family]", "Hybrid"),
    ("GRAND", 2024, 2025, 2500, "A25A-FXS", "Grand Highlander Hybrid 2.5 245hp (VIN B/C) [DB family]"),
    ("HIGHLANDER", 2005, 2007, 2400, "2AZ-FE", "Highlander 2.4 base [DB family]"),
    ("HIGHLANDER", 2005, 2007, 3300, "3MZ-FE", "Highlander 3.3 [DB family]"),
    ("HIGHLANDER", 2008, 2009, 3300, "3MZ-FE", "Highlander 3.3 (last year) [DB family]"),
    ("HIGHLANDER", 2008, 2009, 3500, "2GR-FE", "Highlander 3.5 270hp [DB family]"),
    ("HIGHLANDER", 2009, 2019, 2700, "1AR-FE", "Highlander 2.7 187hp (VIN A) [DB family]"),
    ("HIGHLANDER", 2015, 2016, 3500, "2GR-FE", "Highlander 3.5 (VIN K) [DB family]"),
    ("HIGHLANDER", 2017, 2019, 3500, "2GR-FKS", "Highlander 3.5 295hp (VIN Z) [NEW 2GR-FKS]"),
    ("HIGHLANDER", 2020, 2022, 3500, "2GR-FKS", "Highlander 3.5 [NEW 2GR-FKS]"),
    ("HIGHLANDER", 2020, 2025, 2500, "A25A-FXS", "Highlander Hybrid 2.5 243hp (VIN A/B) [DB family]"),
    ("HIGHLANDER", 2020, 2022, None, "2GR-FKS", "Highlander 3.5 gas [NEW 2GR-FKS]"),
    ("HIGHLANDER", 2023, 2025, 2400, "T24A-FTS", "Highlander 2.4T 265hp gas [NEW]"),
    ("HIGHLANDER", 2023, 2025, None, "T24A-FTS", "Highlander 2.4T gas (2023+ dropped V6) [NEW]"),
    ("LAND CRUISER", 2005, 2007, None, "2UZ-FE", "LC 100 series 4.7 [DB family]"),
    ("LAND CRUISER", 2008, 2020, None, "3UR-FE", "LC 200 series 5.7 381hp [DB family]"),
    ("LAND CRUISER", 2024, 2025, None, "T24A-FTS", "LC 250 i-FORCE MAX hybrid only 326hp [LC2024][NEW]", "Hybrid"),
    ("MATRIX", 2005, 2008, None, "1ZZ-FE", "Matrix 1.8 base/XR (XRS 2ZZ minority) [DB family]"),
    ("MATRIX", 2009, 2009, 1800, "2ZR-FE", "Matrix 1.8 132hp [DB family]"),
    ("MATRIX", 2009, 2009, 2400, "2AZ-FE", "Matrix XR/S 2.4 158hp [DB family]"),
    ("MIRAI", 2016, 2024, None, "Mirai FCEV", "Mirai hydrogen FCEV 151/182hp [NEW][fuel fix Electric]"),
    ("MR2", 2005, 2005, None, "1ZZ-FE", "MR2 Spyder 1.8 138hp (last year) [DB family]"),
    ("PRIUS", 2005, 2009, None, "1NZ-FXE", "Prius gen2 1.5 hybrid (system 110hp) [DB family]"),
    ("PRIUS", 2015, 2015, None, "2ZR-FXE", "Prius gen3 1.8 hybrid 134hp / Prius v / PHV [DB family]"),
    ("PRIUS", 2016, 2022, None, "2ZR-FXE", "Prius gen4 1.8 hybrid 121hp [DB family]"),
    ("PRIUS", 2023, 2025, None, "M20A-FXS", "Prius gen5 2.0 hybrid 194hp [PRIUSG5][NEW]"),
    ("RAV4", 2005, 2005, None, "2AZ-FE", "RAV4 2.4 161hp [DB family]"),
    ("RAV4", 2006, 2008, 2400, "2AZ-FE", "RAV4 2.4 [DB family]"),
    ("RAV4", 2006, 2009, 3500, "2GR-FE", "RAV4 3.5 V6 269hp [DB family]"),
    ("RAV4", 2009, 2018, 2500, "2AR-FE", "RAV4 2.5 179hp [DB family]"),
    ("RAV4", 2009, 2018, None, "2AR-FE", "RAV4 2.5 (incl. 2015 trims) [DB family]"),
    ("RAV4", 2019, 2025, 2500, "A25A-FXS", "RAV4 Hybrid 2.5 219hp (VIN 6/W) [DB family]"),
    ("RAV4", 2019, 2025, None, "A25A-FKS", "RAV4 gas 2.5 203hp [DB family]"),
    ("SEQUOIA", 2005, 2007, None, "2UZ-FE", "Sequoia 4.7 [DB family]"),
    ("SEQUOIA", 2008, 2009, 4700, "2UZ-FE", "Sequoia 4.7 [DB family]"),
    ("SEQUOIA", 2008, 2020, 5700, "3UR-FE", "Sequoia 5.7 381hp (incl. VIN W/Y) [DB family]"),
    ("SEQUOIA", 2019, 2020, None, "3UR-FE", "Sequoia 5.7 only [DB family]"),
    ("SEQUOIA", 2022, 2025, None, "V35A-FTS", "Sequoia 3.4TT i-FORCE MAX hybrid only 437hp [SEQ2022][NEW]", "Hybrid"),
    ("SIENNA", 2005, 2006, None, "3MZ-FE", "Sienna 3.3 230hp [DB family]"),
    ("SIENNA", 2007, 2016, None, "2GR-FE", "Sienna 3.5 266hp (incl. 2015 trims) [DB family]"),
    ("SIENNA", 2017, 2020, None, "2GR-FKS", "Sienna 3.5 296hp [NEW 2GR-FKS]"),
    ("SIENNA", 2022, 2025, 2500, "A25A-FXS", "Sienna hybrid-only 245hp (VIN R/S) [SIENNA2021][DB family]", "Hybrid"),
    ("SIENNA", 2022, 2025, None, "A25A-FXS", "Sienna hybrid-only [SIENNA2021]", "Hybrid"),
    ("SUPRA", 2020, 2020, None, "B58B30 (40i)", "2020 Supra 3.0 B58 335hp [SUPRA][DB BMW family]"),
    ("SUPRA", 2022, 2025, 2000, "B48B20 (Supra 2.0)", "Supra 2.0 B48 255hp (VIN 2) [SUPRA][NEW]"),
    ("SUPRA", 2022, 2024, 3000, "B58B30 (M40i/M340i)", "Supra 3.0 B58 382hp (2021+) [SUPRA][DB BMW family]"),
    ("SUPRA", 2025, 2025, None, "B58B30 (M40i/M340i)", "2025 Supra 3.0 382hp [SUPRA]"),
    ("TACOMA", 2005, 2015, 2700, "2TR-FE", "Tacoma 2.7 159hp (VIN X) [DB family]"),
    ("TACOMA", 2005, 2015, 4000, "1GR-FE", "Tacoma 4.0 236hp (VIN U) [DB family]"),
    ("TACOMA", 2016, 2023, 2700, "2TR-FE", "Tacoma 2.7 (VIN X) [DB family]"),
    ("TACOMA", 2016, 2023, 3500, "2GR-FKS", "Tacoma 3.5 278hp (VIN Z) [NEW 2GR-FKS]"),
    ("TACOMA", 2024, 2025, None, "T24A-FTS", "2024+ Tacoma 2.4T only [NEW]"),
    ("TACOMA", 2024, 2025, 2400, "T24A-FTS", "2024+ Tacoma 2.4T i-FORCE 228/270/278hp (VIN B-E; MAX 326hp shares engine) [NEW]"),
    ("TUNDRA", 2005, 2009, 4000, "1GR-FE", "Tundra 4.0 [DB family]"),
    ("TUNDRA", 2005, 2009, 4700, "2UZ-FE", "Tundra 4.7 [DB family]"),
    ("TUNDRA", 2007, 2009, 5700, "3UR-FE", "Tundra 5.7 381hp [DB family]"),
    ("TUNDRA", 2015, 2019, 4600, "1UR-FE", "Tundra 4.6 310hp (VIN M) [DB family]"),
    ("TUNDRA", 2015, 2019, 5700, "3UR-FE", "Tundra 5.7 (VIN W/Y) [DB family]"),
    ("TUNDRA", 2022, 2025, 3400, "V35A-FTS", "Tundra 3.4TT i-FORCE 389hp (VIN A/C; MAX 437 hybrid shares engine) [TUNDRAV35A][NEW]"),
    ("TUNDRA", 2025, 2025, None, "V35A-FTS", "Tundra 3.4TT only 2025 [TUNDRAV35A][NEW]"),
    ("TUNDRA", 2022, 2024, None, "V35A-FTS", "Tundra 3.4TT only (VIN A/C; MAX shares engine) [TUNDRAV35A][NEW]"),
    ("VENZA", 2009, 2016, 2700, "1AR-FE", "Venza 2.7 182hp (VIN A) [DB family]"),
    ("VENZA", 2009, 2016, 3500, "2GR-FE", "Venza 3.5 268hp (VIN K) [DB family]"),
    ("VENZA", 2022, 2024, None, "A25A-FXS", "Venza hybrid-only 219hp [VENZA2021][DB family]", "Hybrid"),
    ("YARIS", 2007, 2020, None, "1NZ-FE", "Yaris 1.5 106hp (hatch; iA sedan Mazda 1.5 minority) [DB family]"),
    ("BZ4X", 2023, 2025, None, "bZ4X Electric", "bZ4X EV 201/214hp [NEW][fuel fix Electric]"),
]

def decide(model, year, code):
    parts = code.replace("LEMON_TOYOTA_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc = None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
    mu = model.upper()
    if mu == "PRIUS" and "PRIUSC" in code:
        return ("1NZ-FXE", "Prius c 1.5 hybrid 99hp [DB family]", "Hybrid")
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands:
        if cc is not None:
            return (None, f"{model} {year} {cc}cc: no cc rule", None)
        return (None, f"no rule for {model} {year} (bare)", None)
    r = cands[0]
    fuel = r[6] if len(r) > 6 else None
    if fuel is None: fuel = FUEL_FIX_BY_TARGET.get(r[4])
    return (r[4], r[5], fuel)

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code FROM vehicle_variants
        WHERE car_brand='Toyota' AND engine_code LIKE 'LEMON_TOYOTA%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code in rows:
        tgt, note, fuel_fix = decide(model, year, code)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"Toyota LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(18): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter(d[6] for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"

    if not apply:
        with open("database_enriched/csv_exports/26_lemon_batch9_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"Toyota",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Toyota",s[1],s[2],"","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step18_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    # fuel-label unification ('Electric Motor' -> 'Electric')
    n1 = cur.execute("UPDATE engines SET fuel='Electric' WHERE fuel='Electric Motor'").rowcount
    n2 = cur.execute("UPDATE vehicle_variants SET fuel='Electric' WHERE fuel='Electric Motor'").rowcount
    print(f"fuel label unified 'Electric Motor'->'Electric': {n1} engines, {n2} variants")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP18_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
            print(f"  created {code}")
    for code, fixes in ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  row-fix {code}: {fixes}")

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

    with open("database_enriched/csv_exports/26_lemon_batch9_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"Toyota",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_TOYOTA remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_TOYOTA%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    print("fuel labels:", [r[0] for r in cur.execute("SELECT DISTINCT fuel FROM engines ORDER BY 1")])
    con.close()

if __name__ == "__main__":
    main()
