"""Step 36c: repair pre-existing junk GM engine rows touched by batch 27.

These rows predate the Step 5 work (ESTIMATE / crawl-imported) and carried placeholder or
plainly wrong metadata: engine_type "JETSTAR" on a Suzuki G16B, bare "2.0"/"6.0"/"1.3"
descriptors, a NULL engine_type + NULL cylinder count on LN2, and LS1 advertised as a Daewoo.
Nothing here changes a variant mapping - only the engines-table descriptors, cylinder counts
and brand/model/year examples. Power nominals are deliberately left alone where one RPO code
legitimately spans several ratings (that split is carried on the variants via power_fill and
documented in engine_type).

Run with --apply to write.
"""
import sqlite3, sys

DB = "database_enriched/car_database.db"
apply = "--apply" in sys.argv

FIX = {
    "G13BB": {"engine_type": "1.3 I4 SOHC 16v Suzuki G13BB (Swift/Wagon R+/Chevrolet Metro, 76-79hp)"},
    "G16B": {"engine_type": "1.6 I4 SOHC 16v Suzuki G16B (Vitara/Grand Vitara/Chevrolet Tracker, 94-99hp)"},
    "H25A": {"engine_type": "2.5 V6 DOHC 24v Suzuki H25A (Grand Vitara 155hp / Chevrolet Tracker LT 165hp)"},
    "L18": {"engine_type": "8.1 V8 OHV Vortec 8100 big-block (C/K2500-3500, Suburban 2500, P-chassis motorhome, 340hp)"},
    "L29": {"engine_type": "7.4 V8 OHV Vortec 7400 big-block (C/K2500-3500 1996-2000, 290hp)",
            "brand_example": "GMC", "model_example": "C3500", "year_example": 2000},
    "L83": {"engine_type": "5.3 V8 EcoTec3 DI + Active Fuel Management (Silverado/Sierra/Tahoe/Yukon 2014-2019, 355hp)",
            "brand_example": "Chevrolet", "model_example": "Silverado", "year_example": 2014},
    "LM4": {"engine_type": "5.3 V8 Vortec 5300 aluminium block (Envoy XL/Denali, SSR, Rainier, Ascender, 290-300hp)",
            "brand_example": "GMC", "model_example": "Envoy", "year_example": 2003},
    "LH6": {"engine_type": "5.3 V8 Vortec 5300 w/ Displacement on Demand (Envoy Denali 300 / Rainier 300 / trucks 295-310hp)"},
    "LFV": {"engine_type": "1.5 I4 Ecotec Turbo DI (Malibu 160 / Equinox 170hp)",
            "brand_example": "Chevrolet", "model_example": "Malibu", "year_example": 2016},
    "LYX": {"engine_type": "1.5 I4 Ecotec Turbo DI (Terrain/Equinox 2018-2025, 170hp / 175hp from 2021)",
            "brand_example": "GMC", "model_example": "Terrain", "year_example": 2018},
    "LH7": {"engine_type": "1.6 I4 turbodiesel (Terrain/Equinox/Cruze 2017-2019, 137hp)",
            "brand_example": "GMC", "model_example": "Terrain", "year_example": 2018},
    "LFW": {"engine_type": "3.0 V6 DI High Feature (Equinox/Terrain 264hp / Cadillac CTS 270hp)"},
    "LQ4": {"engine_type": "6.0 V8 OHV Vortec 6000 iron block (pickups/vans/cutaway chassis 300-325hp, Hummer H2 316hp)"},
    "LTG": {"engine_type": "2.0 I4 Ecotec Turbo DI (ATS/CTS/Camaro/Malibu 272-276hp / Terrain-Equinox 252hp)"},
    "T20SED": {"engine_type": "2.0 I4 DOHC D-TEC (Daewoo Nubira/Rezzo, Chevrolet Optra 119-128hp)"},
    "X25D1": {"engine_type": "2.5 I6 DOHC 24v transverse XK (Daewoo Magnus / Chevrolet Epica / Suzuki Verona, 154-155hp)"},
    "LAF": {"engine_type": "2.4 I4 Ecotec DI (Equinox/Terrain/Regal 2010-2011, 182hp)"},
    "LLT": {"engine_type": "3.6 V6 DI High Feature (CTS/STS 304 / Camaro 312 / Acadia-Traverse 288hp)"},
    "LY7": {"engine_type": "3.6 V6 DOHC High Feature VVT (CTS/SRX/STS 255-260 / Acadia-Outlook 275hp)"},
    "LN2": {"engine_type": "2.2 I4 OHV (Cavalier/Sunfire 115hp / S10-Sonoma 120hp)", "cylinders": 4},
    "LS1": {"engine_type": "5.7 V8 OHV Gen III (Corvette C5 345-350 / Camaro-Firebird 305-325 / Holden-HSV 300-335hp)",
            "brand_example": "Chevrolet", "model_example": "Corvette", "year_example": 2001},
}

con = sqlite3.connect(DB); cur = con.cursor()
for code, fixes in FIX.items():
    before = cur.execute("""SELECT engine_type, cylinders, brand_example, model_example, year_example
                            FROM engines WHERE engine_code=?""", (code,)).fetchone()
    if before is None:
        print(f"  !! {code}: no engines row"); continue
    print(f"  {code}: engine_type {before[0]!r} -> {fixes.get('engine_type', before[0])!r}"
          + (f" | cylinders {before[1]} -> {fixes['cylinders']}" if "cylinders" in fixes else "")
          + (f" | example {before[2]}/{before[3]}/{before[4]} -> {fixes.get('brand_example')}/"
             f"{fixes.get('model_example')}/{fixes.get('year_example')}" if "brand_example" in fixes else ""))
    if apply:
        f = dict(fixes); f["data_confidence"] = "STEP36_VERIFIED"
        cur.execute(f"UPDATE engines SET {', '.join(k + '=?' for k in f)} WHERE engine_code=?",
                    (*f.values(), code))

if not apply:
    print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); sys.exit()
con.commit()
print("\n--- audit ---")
ph = ",".join("?" * len(FIX))
print("remaining NULL engine_type among fixed rows:", cur.execute(
    f"SELECT COUNT(*) FROM engines WHERE engine_code IN ({ph}) AND engine_type IS NULL", tuple(FIX)).fetchone()[0])
print("remaining NULL cylinders among fixed rows:", cur.execute(
    f"SELECT COUNT(*) FROM engines WHERE engine_code IN ({ph}) AND cylinders IS NULL", tuple(FIX)).fetchone()[0])
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e
    ON e.engine_code=v.engine_code WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close()
