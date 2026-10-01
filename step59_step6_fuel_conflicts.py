"""Step 59 (Step 6): resolve all 137 fuel conflicts between variants and their engine rows.

A "fuel conflict" is a variant whose `fuel` disagrees with the `fuel` of the engine row it points
at - a Corolla Hybrid attached to the petrol 2ZR-FE, an S400 HYBRID filed as Petrol, an RX-8
whose fuel is recorded as "Wankel". 137 of them survived the LEMON campaign because they predate
it; this step clears them.

Each of the 45 affected engine codes was classified into one of four outcomes:

1. **RELINK** - the variant is right and a correct sibling engine row already exists. A Corolla
   Hybrid belongs on `2ZR-FXE`, a Highlander Hybrid on `2GR-FXE`, a RAV4 Hybrid on `2AR-FXE`.
2. **RELINK to a new row** - the variant is right but its engine was missing from the catalogue.
   Twelve rows are added here, among them Toyota's two i-FORCE MAX hybrids, the Hyundai hybrid
   fours, the PSA HYbrid4 diesel hybrid and the S580e's PHEV.
3. **ENG_FUEL** - the engine row is wrong. `X16SZR` is an Opel 1.6 *petrol* recorded as Diesel;
   `CHJA` and `CRJA` are literally named "Hybrid" but were filed as Petrol.
4. **VAR_FUEL** - the variant label is wrong. The clearest cases are the Audi rows: four A8/A7
   variants on the 3.0 TFSI `CTUA` were labelled Diesel, but they carry **310hp**, exactly the
   petrol figure their non-conflicting siblings carry - a TDI would read 240. Same for `BGB`
   (197hp) and `CWZA` (228hp). Also here: "Wankel" is an engine layout, not a fuel, so the three
   RX-8 rows become Petrol.

The S450 is worth a note on where the line falls between a mild hybrid and a hybrid. Its EQ
Boost 48V system cannot drive the car, and the database already treats such cars as Petrol (all
24 `M256` CLS450/E450/GLE450 variants are Petrol). So the three S450 rows move to a new petrol
`M276 3.0 BiTurbo (S450)` row, while the genuinely plug-in S560e keeps `M276.824`.
"""
import sqlite3, csv, shutil, sys
from collections import Counter
from datetime import date

DB = "database_enriched/car_database.db"
apply = "--apply" in sys.argv

# code -> (engine_type, fuel, cc, hp, cylinders)
NEW_ENGINES = {
    "T24A-FTS (i-FORCE MAX)": ("2.4 I4 Turbo i-FORCE MAX hybrid (Crown/Grand Highlander/GX550/Land Cruiser, 326-340hp system)", "Hybrid", 2393, 326, 4),
    "V35A-FTS (i-FORCE MAX)": ("3.4 V6 TwinTurbo i-FORCE MAX hybrid (Tundra/Sequoia, 437hp system)", "Hybrid", 3444, 437, 6),
    "3MZ-FE Hybrid": ("3.3 V6 Atkinson + HSD (RX400h / Highlander Hybrid, 268hp system)", "Hybrid", 3311, 268, 6),
    "QR25DE Hybrid": ("2.5 I4 Atkinson + motor (Altima Hybrid 198 / Rogue Hybrid 176hp system)", "Hybrid", 2488, 176, 4),
    "QR25DER Hybrid": ("2.5 I4 supercharged + motor (Pathfinder/Murano Hybrid, 250hp system)", "Hybrid", 2488, 250, 4),
    "G4FT (1.6 T-GDI hybrid)": ("1.6 I4 T-GDI + motor (Tucson/Santa Fe/Sportage Hybrid, 226hp system)", "Hybrid", 1598, 226, 4),
    "G4LE (1.6 GDI Atkinson hybrid)": ("1.6 I4 GDI Atkinson + motor (Elantra Hybrid, 139hp system)", "Hybrid", 1580, 139, 4),
    "G4KK (2.4 GDI hybrid)": ("2.4 I4 GDI Atkinson + motor (Sonata Hybrid 2011-2015, 199hp system)", "Hybrid", 2359, 199, 4),
    "OM651 BlueTEC Hybrid": ("2.1 I4 BlueTEC diesel + motor (C 300 h / S 300 h / E 300 BlueTEC Hybrid, 204-231hp system)", "Hybrid", 2143, 204, 4),
    "DW10 HYbrid4": ("2.0 HDi diesel + rear e-motor (Peugeot 3008/508 HYbrid4, Citroen DS5 HYbrid4, 200hp system)", "Hybrid", 1997, 200, 4),
    "M256 PHEV (S580e)": ("3.0 I6 turbo + plug-in motor (S 580 e, 510hp system)", "Hybrid", 2999, 510, 6),
    "M276 3.0 BiTurbo (S450)": ("3.0 V6 BiTurbo with EQ Boost 48V (S450 2018-2020, 362hp)", "Petrol", 2996, 362, 6),
}

# (engine_code, variant_fuel, model_substring|None) -> (target_code, evidence)
RELINK = [
    ("2ZR-FE", "Hybrid", None, ("2ZR-FXE", "Corolla Hybrid uses the Atkinson-cycle 2ZR-FXE, not the petrol 2ZR-FE")),
    ("T24A-FTS", "Hybrid", None, ("T24A-FTS (i-FORCE MAX)", "Crown/Grand Highlander/GX550/Land Cruiser hybrids are the i-FORCE MAX version of this engine")),
    ("V35A-FTS", "Hybrid", None, ("V35A-FTS (i-FORCE MAX)", "Sequoia is i-FORCE MAX only; the hybrid gets its own row")),
    ("3MZ-FE", "Hybrid", None, ("3MZ-FE Hybrid", "RX400h and Highlander Hybrid run the Atkinson 3MZ-FE with HSD")),
    ("QR25DE", "Hybrid", None, ("QR25DE Hybrid", "Altima Hybrid and Rogue Hybrid pair the QR25DE with a motor")),
    ("VQ35DE", "Hybrid", None, ("QR25DER Hybrid", "Pathfinder Hybrid and Murano Hybrid use the supercharged 2.5 four, not the VQ35DE V6")),
    ("G4FJ", "Hybrid", "Tucson", ("G4FT (1.6 T-GDI hybrid)", "Tucson Hybrid is the 1.6 T-GDI hybrid, 226hp system")),
    ("G4FJ", "Hybrid", "Elantra", ("G4LE (1.6 GDI Atkinson hybrid)", "Elantra Hybrid is the 1.6 GDI Atkinson hybrid, 139hp system - not the T-GDI")),
    ("G4KJ", "Hybrid", None, ("G4KK (2.4 GDI hybrid)", "Sonata Hybrid 2011-2015 uses the Atkinson 2.4 GDI hybrid")),
    ("2GR-FKS", "Hybrid", None, ("2GR-FXE", "Highlander Hybrid uses the Atkinson 2GR-FXE")),
    ("2GR-FE", "Hybrid", None, ("2GR-FXE", "Highlander Hybrid uses the Atkinson 2GR-FXE")),
    ("2GR-FSE", "Hybrid", None, ("2GR-FXE", "GS450h runs the hybrid 2GR, not the direct-injection petrol GS350 engine")),
    ("2AR-FE", "Hybrid", None, ("2AR-FXE", "RAV4 Hybrid uses the Atkinson 2AR-FXE")),
    ("A25A-FKS", "Hybrid", None, ("A25A-FXS", "RAV4 Hybrid uses the Atkinson A25A-FXS")),
    ("OM651.921", "Hybrid", None, ("OM651 BlueTEC Hybrid", "C 300 h / S 300 h are diesel hybrids: OM651 plus a motor")),
    ("RHH (DW10CTED4)", "Hybrid", None, ("DW10 HYbrid4", "3008/508/DS5 HYbrid4 are diesel hybrids with a rear e-motor")),
    ("AHX(DW10FD)", "Hybrid", None, ("DW10 HYbrid4", "DS5 HYbrid4 is a diesel hybrid with a rear e-motor")),
    ("RHC(DW10CTED4)", "Hybrid", None, ("DW10 HYbrid4", "508 HYbrid4 moves to the explicit hybrid row so its code can go back to being a plain diesel")),
    ("M256 3.0 I6 Turbo", "Hybrid", None, ("M256 PHEV (S580e)", "S 580 e is a plug-in hybrid; the other 24 variants of M256 are EQ Boost mild hybrids and stay Petrol")),
    ("M276.824", "Petrol", "S450", ("M276 3.0 BiTurbo (S450)", "S450's EQ Boost 48V system cannot drive the car, so it is petrol - M276.824 stays with the plug-in S560e")),
    ("654", "Petrol", None, ("OM654 2.0 I4 CDI (Sprinter, 161-168hp)", "duplicate stub code for the Sprinter OM654 four, merged into the row batch 43 created")),
    ("2AZ-FXE", "Petrol", "PREVIA", ("2AZ-FE", "Previa is not a hybrid; it runs the plain 2AZ-FE")),
    ("2AZ-FXE", "Petrol", "CAMRY (MCV3_", ("2AZ-FE", "the XV30 Camry is not a hybrid; it runs the plain 2AZ-FE")),
]

# (engine_code, from_fuel, model_substring|None) -> (to_fuel, evidence)
VAR_FUEL = [
    ("2ZR-FXE", "Petrol", None, ("Hybrid", "every 2ZR-FXE car is a hybrid - Prius, Prius+, Auris Hybrid")),
    ("1NZ-FXE", "Petrol", None, ("Hybrid", "1NZ-FXE is the Prius/Prius c hybrid engine")),
    ("2AR-FSE", "Petrol", None, ("Hybrid", "IS300h and RC300h are hybrids")),
    ("2GR-FXE", "Petrol", None, ("Hybrid", "RX450h is a hybrid")),
    ("2AZ-FXE", "Petrol", "SAI", ("Hybrid", "the Toyota SAI is a hybrid-only model")),
    ("2AZ-FXE", "Petrol", "CAMRY Saloon", ("Hybrid", "the XV40 Camry Hybrid is a hybrid")),
    ("M272.974", "Petrol", None, ("Hybrid", "the only S400 of this generation was the S400 HYBRID")),
    ("M274 PHEV (C350e)", "Petrol", None, ("Hybrid", "C350e is a plug-in hybrid")),
    ("M276 3.0 PHEV", "Petrol", None, ("Hybrid", "S550e is a plug-in hybrid")),
    ("M139 PHEV (C63)", "Petrol", None, ("Hybrid", "C63 S E Performance is a plug-in hybrid")),
    ("ECA1", "Petrol", None, ("Hybrid", "the first-generation Insight is an IMA hybrid")),
    ("CHJA", "Petrol", None, ("Hybrid", "Q5/A6 hybrid - the engine row is named '2.0 TFSI Hybrid'")),
    ("CRJA", "Petrol", None, ("Hybrid", "Jetta Hybrid 1.4 TSI")),
    ("W242 Electric (B250e)", "Petrol", None, ("Electric", "the B250e is battery-electric")),
    ("13B-MSP", "Wankel", None, ("Petrol", "Wankel is an engine layout, not a fuel; the RX-8 burns petrol")),
    ("KFV (TU3JP)", "Hybrid (Petrol-/ Electro.)", None, ("Petrol", "the C3 Pluriel 1.4 8v is not a hybrid")),
    ("KFW (TU3JP)", "Hybrid", None, ("Petrol", "the Berlingo 1.4 8v is not a hybrid")),
    ("VQ35HR", "Hybrid", None, ("Petrol", "the 2009 Fuga 350 is not a hybrid; the Fuga Hybrid arrived in 2011")),
    ("M274.920", "Hybrid", None, ("Petrol", "M274.920 is a petrol-only engine code; the hybrid C-Class of this period is the OM651 diesel hybrid, which has its own row")),
    ("OM651.924", "Hybrid", None, ("Diesel", "the 2010 E-Class on OM651 is a plain diesel; the E300 BlueTEC Hybrid arrived in 2012")),
    ("Y30DT", "Petrol", None, ("Diesel", "Y30DT is the 3.0 CDTI V6 diesel")),
    ("GW4G15T", "Diesel", None, ("Petrol", "GW4G15T is a 1.5 turbo petrol")),
    ("X16SZR", "Diesel", None, ("Petrol", "X16SZR is an Opel 1.6 petrol")),
    ("CTUA", "Diesel", None, ("Petrol", "these A7/A8 rows carry 310hp, the 3.0 TFSI figure their non-conflicting siblings carry; a 3.0 TDI of these years reads 240hp")),
    ("BGB", "Diesel", None, ("Petrol", "these A3 rows carry 197hp, the 2.0 TFSI figure - not a TDI rating")),
    ("CWZA", "Diesel", None, ("Petrol", "these A3 rows carry 228hp, the 2.0 TFSI figure - not a TDI rating")),
]

ENG_FUEL = {
    "X16SZR": ("Petrol", "X16SZR is an Opel/Vauxhall 1.6 8v petrol, not a diesel"),
    "CHJA": ("Hybrid", "the row is the Audi 2.0 TFSI hybrid of the Q5/A6/A8 hybrid models"),
    "CRJA": ("Hybrid", "the row is the Jetta Hybrid's 1.4 TSI hybrid"),
    "RHC(DW10CTED4)": ("Diesel", "DW10CTED4 is a diesel; its HYbrid4 cars move to the explicit hybrid row"),
}

ROW_FIXES = {
    "M272.974": {"engine_type": "3.5 V6 + 15kW motor (S400 HYBRID W221 / ML450 HYBRID, 295hp system)", "cylinders": 6},
    "RHC(DW10CTED4)": {"engine_type": "2.0 HDi DW10CTED4 (Peugeot 508, 163hp)", "cylinders": 4},
    "X16SZR": {"engine_type": "1.6 I4 8v X16SZR (Astra/Corsa/Combo, 75-85hp)", "cylinders": 4},
    "2AZ-FXE": {"engine_type": "2.4 I4 Atkinson + HSD (Camry Hybrid / Alphard Hybrid / SAI, 187hp system)", "cylinders": 4},
    "3MZ-FE": {"engine_type": "3.3 V6 DOHC (RX330/Highlander/Sienna, 230hp)", "cylinders": 6},
    "OM651.924": {"engine_type": "2.1 I4 CDI BlueTEC (E-Class W212, 204hp)", "cylinders": 4},
    "2GR-FSE": {"engine_type": "3.5 V6 D-4S 2GR-FSE (GS350/IS350/GS450h base, 303-315hp)", "cylinders": 6},
}

con = sqlite3.connect(DB); cur = con.cursor()
base = cur.execute("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel").fetchone()[0]
assert base == 137, f"BASELINE MISMATCH: {base} conflicts, expected 137"

actions = []
def sel(code, fuel, model):
    q = "SELECT id, car_brand, car_model, car_year, fuel FROM vehicle_variants WHERE engine_code=? AND fuel=?"
    a = [code, fuel]
    if model:
        q += " AND car_model LIKE ?"; a.append(f"%{model}%")
    return cur.execute(q, a).fetchall()

for code, fuel, model, (tgt, why) in RELINK:
    rows = sel(code, fuel, model)
    assert rows, f"RELINK matched nothing: {code}/{fuel}/{model}"
    for vid, b, m, y, f in rows:
        actions.append((vid, b, m, y, code, fuel, "RELINK", tgt, "", why))
for code, fuel, model, (newf, why) in VAR_FUEL:
    rows = sel(code, fuel, model)
    assert rows, f"VAR_FUEL matched nothing: {code}/{fuel}/{model}"
    for vid, b, m, y, f in rows:
        actions.append((vid, b, m, y, code, fuel, "VAR_FUEL", "", newf, why))

print(f"variants touched: {len(actions)}  ({Counter(a[6] for a in actions)})")
print("new engine rows:", len(NEW_ENGINES), "| engine fuel fixes:", len(ENG_FUEL), "| descriptor fixes:", len(ROW_FIXES))

csv_path = f"database_enriched/csv_exports/67_fuel_conflict_step59_decisions{'' if apply else '_DRYRUN'}.csv"
with open(csv_path, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["variant_id", "brand", "model", "year", "engine_code", "old_fuel", "action", "new_engine_code", "new_fuel", "evidence"])
    w.writerows(actions)
print("csv:", csv_path)

if not apply:
    print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); sys.exit()

bak = f"database_enriched/backups/car_database_backup_pre_step59_{date.today().isoformat()}.db"
shutil.copy(DB, bak); print("backup:", bak)

for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
    if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
        cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp, cylinders,
                       count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP59_VERIFIED')""",
                    (code, etype, fuel, cc, hp, cyl))
        print("  created", code)
for code, fixes in ROW_FIXES.items():
    cur.execute(f"UPDATE engines SET {', '.join(f'{k}=?' for k in fixes)}, data_confidence='STEP59_VERIFIED' WHERE engine_code=?",
                (*fixes.values(), code))
for code, (fuel, why) in ENG_FUEL.items():
    cur.execute("UPDATE engines SET fuel=?, data_confidence='STEP59_VERIFIED' WHERE engine_code=?", (fuel, code))
    print(f"  engine fuel {code} -> {fuel}")

for vid, b, m, y, code, oldf, act, tgt, newf, why in actions:
    if act == "RELINK":
        cur.execute("""UPDATE vehicle_variants SET engine_code=?,
                       engine_power_hp=COALESCE(engine_power_hp,(SELECT power_hp FROM engines WHERE engine_code=?)),
                       engine_type=COALESCE(engine_type,(SELECT engine_type FROM engines WHERE engine_code=?))
                       WHERE id=?""", (tgt, tgt, tgt, vid))
    else:
        cur.execute("UPDATE vehicle_variants SET fuel=? WHERE id=?", (newf, vid))

retired = []
for code in set(a[4] for a in actions):
    n = cur.execute("SELECT count(*) FROM vehicle_variants WHERE engine_code=?", (code,)).fetchone()[0]
    if n == 0:
        cur.execute("DELETE FROM engine_service_specs WHERE engine_code=?", (code,))
        cur.execute("DELETE FROM engine_technical_specs WHERE engine_code=?", (code,))
        cur.execute("DELETE FROM engines WHERE engine_code=?", (code,))
        retired.append(code)
print("retired emptied codes:", retired or "none")

cur.execute("UPDATE engines SET count_variants=(SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)")
con.commit()

print("\n--- verify ---")
print("fuel conflicts:", cur.execute("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel").fetchone()[0])
print("orphan refs:", cur.execute("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
                                     WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT count(*) FROM engines e WHERE e.count_variants <>
                                          (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)""").fetchone()[0])
print("engines:", cur.execute("SELECT count(*) FROM engines").fetchone()[0])
print("NULL power among touched variants:", cur.execute(
    f"SELECT count(*) FROM vehicle_variants WHERE engine_power_hp IS NULL AND id IN ({','.join(str(a[0]) for a in actions)})").fetchone()[0])
con.close()
