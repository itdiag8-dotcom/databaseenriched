"""Step 36d: GM-family data-integrity cleanup exposed by batch 27.

All of this is pre-existing damage that batch 27 surfaced while auditing GMC + Chevrolet:

A. Duplicate engine code. The crawl had already imported the 6.5L Detroit Diesel V8 under the
   free-text code "6.5 TD V8 (L65)" (10 Chevrolet variants). Batch 27 created the proper RPO
   row L65 for the same engine, so the free-text row is merged into L65 and retired.
B. Engine rows whose fuel is simply wrong: A16XER (1.6 Ecotec petrol, filed as Diesel) and
   LFA (6.0 two-mode hybrid, filed as Petrol).
C. Variant rows the crawl labelled Petrol that are not petrol: the Duramax codes
   (L5P/LMM/LML/LBZ) and the two-mode / eAssist hybrids (L8B, LZ1, LFA).
D. Missing engine metadata (power/cylinders/displacement/engine_type) on GM codes that GMC and
   Chevrolet variants point at: L5P, L3B, LS9, LT5, LF3, LT1, L87, L8T, LC8, LZ1.
E. Backfill of NULL vehicle_variants.engine_power_hp for GMC/Chevrolet rows whose engine row
   does carry a rating, then a count_variants recompute.

Run with --apply to write.
"""
import sqlite3, sys

DB = "database_enriched/car_database.db"
apply = "--apply" in sys.argv
con = sqlite3.connect(DB); cur = con.cursor()

LEGACY, TARGET = "6.5 TD V8 (L65)", "L65"

ENG_FIX = {
    "L65": {"engine_type": "6.5 V8 OHV turbodiesel (Detroit Diesel 6.5TD; C/K3500, chassis cab, "
                           "Savana/Express, P-chassis motorhome: 180-215hp by application, 195hp typical)"},
    "A16XER": {"engine_type": "1.6 I4 DOHC 16v Ecotec Family 1 (Astra/Aveo/Cruze, 114-115hp)", "fuel": "Petrol"},
    "LFA": {"engine_type": "6.0 V8 OHV Atkinson-cycle, GM 2-Mode Hybrid (Tahoe/Yukon/Escalade Hybrid 2008-2009, 332hp engine / 379hp system)",
            "fuel": "Hybrid"},
    "LZ1": {"engine_type": "6.0 V8 OHV Atkinson-cycle, GM 2-Mode Hybrid (Tahoe/Yukon/Escalade/Silverado Hybrid 2010-2013, 332hp engine / 379hp system)"},
    "L5P": {"engine_type": "6.6 V8 Duramax turbodiesel (Silverado/Sierra HD 2017+, 445hp / 910 lb-ft)",
            "power_hp": 445, "cylinders": 8},
    "L3B": {"engine_type": "2.7 I4 Turbo High-Output (Silverado/Sierra 1500 2019+, 310hp)", "power_hp": 310},
    "LS9": {"engine_type": "6.2 V8 OHV supercharged (Corvette ZR1 2009-2013, 638hp)",
            "power_hp": 638, "displacement_cc": 6162, "cylinders": 8},
    "LT5": {"engine_type": "6.2 V8 OHV supercharged Gen V (Corvette ZR1 2019, 755hp)",
            "power_hp": 755, "displacement_cc": 6162, "cylinders": 8},
    "LF3": {"engine_type": "3.6 V6 DI twin-turbo (CTS V-Sport 420hp / XTS 410hp)",
            "power_hp": 420, "cylinders": 6},
    "LT1": {"engine_type": "6.2 V8 OHV Gen V EcoTec3 DI (Corvette Stingray / Camaro SS, 455hp)",
            "displacement_cc": 6162, "cylinders": 8},
    "L87": {"cylinders": 8},
    "L8T": {"engine_type": "6.6 V8 OHV gasoline (Silverado/Sierra HD 2020+, 401hp)", "cylinders": 8},
    "LC8": {"engine_type": "6.0 V8 OHV Vortec, gaseous-fuel capable (HD trucks/vans, 306hp)"},
}

VAR_FUEL = {"Diesel": ["L5P", "LMM", "LML", "LBZ"], "Hybrid": ["L8B", "LZ1", "LFA"]}

print("A. duplicate merge")
print(f"   {LEGACY}: {cur.execute('SELECT COUNT(*) FROM vehicle_variants WHERE engine_code=?', (LEGACY,)).fetchone()[0]} variants"
      f" -> {TARGET} ({cur.execute('SELECT COUNT(*) FROM vehicle_variants WHERE engine_code=?', (TARGET,)).fetchone()[0]} variants)")
print("B/D. engine-row fixes")
for code, f in ENG_FIX.items():
    row = cur.execute("SELECT engine_type, fuel, power_hp, cylinders, displacement_cc FROM engines WHERE engine_code=?", (code,)).fetchone()
    print(f"   {code}: {row} + {f}")
print("C. variant fuel fixes")
for fuel, codes in VAR_FUEL.items():
    n = cur.execute(f"""SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IN ({','.join('?'*len(codes))})
                        AND fuel IS NOT NULL AND fuel<>?""", (*codes, fuel)).fetchone()[0]
    print(f"   -> {fuel}: {n} rows ({', '.join(codes)})")
n_pw = cur.execute("""SELECT COUNT(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.car_brand IN ('GMC','Chevrolet') AND v.engine_power_hp IS NULL AND e.power_hp IS NOT NULL""").fetchone()[0]
print(f"E. power backfill candidates (pre-fix): {n_pw}")

if not apply:
    print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); sys.exit()

# A - spec-first merge, then relink and retire
spec_cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_service_specs)")]
tech_cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_technical_specs)")]
for table, cols in (("engine_service_specs", spec_cols), ("engine_technical_specs", tech_cols)):
    cols = [c for c in cols if c != "engine_code"]
    src = cur.execute(f"SELECT {','.join(cols)} FROM {table} WHERE engine_code=?", (LEGACY,)).fetchone()
    if src is None:
        continue
    if cur.execute(f"SELECT 1 FROM {table} WHERE engine_code=?", (TARGET,)).fetchone():
        cur.execute(f"UPDATE {table} SET {', '.join(f'{c}=COALESCE({c}, ?)' for c in cols)} WHERE engine_code=?",
                    (*src, TARGET))
    else:
        cur.execute(f"INSERT INTO {table} (engine_code, {','.join(cols)}) VALUES (?{',?'*len(cols)})", (TARGET, *src))
    cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (LEGACY,))
cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel='Diesel' WHERE engine_code=?", (TARGET, LEGACY))
cur.execute("DELETE FROM engines WHERE engine_code=?", (LEGACY,))
print(f"  merged {LEGACY} -> {TARGET}")

# B/D
for code, f in ENG_FIX.items():
    f = dict(f); f["data_confidence"] = "STEP36_VERIFIED"
    cur.execute(f"UPDATE engines SET {', '.join(k + '=?' for k in f)} WHERE engine_code=?", (*f.values(), code))

# C
for fuel, codes in VAR_FUEL.items():
    cur.execute(f"""UPDATE vehicle_variants SET fuel=? WHERE engine_code IN ({','.join('?'*len(codes))})
                    AND fuel IS NOT NULL AND fuel<>?""", (fuel, *codes, fuel))

# E
cur.execute("""UPDATE vehicle_variants SET engine_power_hp=
    (SELECT power_hp FROM engines WHERE engine_code=vehicle_variants.engine_code)
    WHERE car_brand IN ('GMC','Chevrolet') AND engine_power_hp IS NULL
      AND (SELECT power_hp FROM engines WHERE engine_code=vehicle_variants.engine_code) IS NOT NULL""")
cur.execute("""UPDATE engines SET count_variants =
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")
con.commit()

print("\n--- audit ---")
print("GMC+Chevrolet fuel conflicts:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v JOIN engines e
    ON e.engine_code=v.engine_code WHERE v.car_brand IN ('GMC','Chevrolet') AND v.fuel IS NOT NULL
    AND e.fuel IS NOT NULL AND v.fuel<>e.fuel""").fetchone()[0])
print("DB-wide fuel conflicts:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v JOIN engines e
    ON e.engine_code=v.engine_code WHERE v.fuel IS NOT NULL AND e.fuel IS NOT NULL AND v.fuel<>e.fuel""").fetchone()[0])
print("GMC+Chevrolet NULL power:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants
    WHERE car_brand IN ('GMC','Chevrolet') AND engine_power_hp IS NULL""").fetchone()[0])
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e
    ON e.engine_code=v.engine_code WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close()
