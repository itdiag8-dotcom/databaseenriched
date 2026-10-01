"""Step 38c: hybrid re-mapping, oil-capacity restore and Ford-family fuel cleanup for batch 29.

1. Five batch-29 rows are **hybrids** that the crawl recorded with a displacement only, and the
   displacement rule sent them to the petrol engine of the same size. The crawl's own `fuel`
   column flags them as Hybrid, which is the tell:
     - Escape 2006/2007/2008 (Hybrid) -> the 2.3 Atkinson hybrid, 155hp combined;
     - Mariner 2009/2011 (Hybrid)     -> the 2.5 Atkinson hybrid, 177hp combined.
2. `5.4 Triton 3V` oil capacity restored to 6.62 L: the 3-valve 5.4 takes 7 US qt, while
   step38b's crawl majority carried the 2-valve engine's 6 qt (5.67 L).
3. Pre-existing Ford-family fuel contradictions cleared the same way as step36d did for GM:
   Power Stroke variants recorded as Petrol -> Diesel, 3.5 PowerBoost -> Hybrid, SDBA -> Diesel,
   and the last A16XER variant still carrying Diesel -> Petrol.

Run with --apply to write.
"""
import sqlite3, sys

DB = "database_enriched/car_database.db"
apply = "--apply" in sys.argv
con = sqlite3.connect(DB); cur = con.cursor()

# (variant_id, new_code, power) resolved by brand/model/year + fuel='Hybrid'
HYB = [
    ("Ford", "Escape", (2006, 2007, 2008), "2.3 I4 Atkinson Hybrid (Escape/Tribute)", 155,
     "Escape Hybrid 2005-2008: 2.3 Atkinson I4 + 70 kW motor, 155hp combined"),
    ("Mercury", "Mariner", (2009, 2011), "2.5 I4 Hybrid", 177,
     "Mariner Hybrid 2009-2011: 2.5 Atkinson I4 + motor, 177hp combined"),
    ("Ford", "Fusion", (2012,), "2.5 I4 Hybrid", 191,
     "Fusion Hybrid 2010-2012 (pre-existing row, same contradiction): 2.5 Atkinson I4 + motor, 191hp combined"),
]
VAR_FUEL = {"Diesel": ["7.3 Power Stroke", "6.0 Power Stroke", "6.7 Power Stroke", "6.4 Power Stroke", "SDBA"],
            "Hybrid": ["3.5 PowerBoost"],
            "Petrol": ["A16XER"]}

moves = []
for brand, model, years, tgt, hp, note in HYB:
    for vid, y, code, fuel in cur.execute(
            """SELECT id, car_year, engine_code, fuel FROM vehicle_variants
               WHERE car_brand=? AND car_model=? AND fuel='Hybrid'""", (brand, model)).fetchall():
        if y in years:
            moves.append((vid, brand, model, y, code, tgt, hp, note))
print("1. hybrid re-mappings")
for m in moves:
    print(f"   v{m[0]} {m[1]} {m[2]} {m[3]}: {m[4]} -> {m[5]} ({m[6]}hp) - {m[7]}")
print("2. 5.4 Triton 3V oil:", cur.execute(
    "SELECT oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code='5.4 Triton 3V'").fetchone())
print("3. variant fuel fixes")
for fuel, codes in VAR_FUEL.items():
    n = cur.execute(f"""SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IN ({','.join('?'*len(codes))})
                        AND fuel IS NOT NULL AND fuel<>?""", (*codes, fuel)).fetchone()[0]
    print(f"   -> {fuel}: {n} rows ({', '.join(codes)})")

if not apply:
    print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); sys.exit()

for vid, brand, model, y, code, tgt, hp, note in moves:
    cur.execute("UPDATE vehicle_variants SET engine_code=?, engine_power_hp=?, engine_type=(SELECT engine_type FROM engines WHERE engine_code=?) WHERE id=?",
                (tgt, hp, tgt, vid))
cur.execute("""UPDATE engine_service_specs SET oil_capacity_with_filter_l=6.62, oil_viscosity='5W-20',
    oil_spec_source=? WHERE engine_code='5.4 Triton 3V'""",
    ("Ford 5.4L 3V OEM service data: 7.0 US qt (6.62 L) with filter, 5W-20 (restored in step38c; "
     "step38b crawl-majority had carried the 2-valve engine's 6 qt)",))
for fuel, codes in VAR_FUEL.items():
    cur.execute(f"""UPDATE vehicle_variants SET fuel=? WHERE engine_code IN ({','.join('?'*len(codes))})
                    AND fuel IS NOT NULL AND fuel<>?""", (fuel, *codes, fuel))
cur.execute("""UPDATE engines SET count_variants =
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")
con.commit()

print("\n--- audit ---")
for b in ("Ford", "Mercury"):
    print(f"{b} fuel conflicts:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v JOIN engines e
        ON e.engine_code=v.engine_code WHERE v.car_brand=? AND v.fuel IS NOT NULL AND e.fuel IS NOT NULL
        AND v.fuel<>e.fuel""", (b,)).fetchone()[0])
print("DB-wide fuel conflicts:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v JOIN engines e
    ON e.engine_code=v.engine_code WHERE v.fuel IS NOT NULL AND e.fuel IS NOT NULL AND v.fuel<>e.fuel""").fetchone()[0])
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e
    ON e.engine_code=v.engine_code WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close()
