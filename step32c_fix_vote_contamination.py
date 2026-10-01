"""Step 32c: post-batch-23 audit repairs (vote line-audit + junk sweeps + consolidation).
1. MDJ oil 4.68L (crawl noise) -> 0W-40/5.7L (C40, LN Engineering 982 2.5 DJUA 6qt/5.7L);
   MDW vis -> 0W-40 (C40 8.5qt/8L, cap 7.99 kept) [NHTSA MC-10172079 C40=0W-40/5W-40].
2. Consolidation: bare 'MCT' + 'MDH' (Macan 2017-18 3.6, NULL power) -> MCT.LA @400hp -
   the only 3.6L Macan 2017-18 is the Turbo 3.6TT 400hp.
3. 918 Spyder (M18.00): 874hp = 887PS conversion -> 887hp US combined; fuel Petrol -> Hybrid
   (918 = PHEV: 4.6 V8 608hp + 2 e-motors).
4. Hybrid-family fuel fixes: M06.EC / MCG.E / MCG.FA engines.fuel Petrol -> Hybrid (all their
   variants are Panamera/Cayenne S Hybrid family); hybrid-named MCG.EA variants -> Hybrid.
5. Sweeps + final audits.
"""
import sqlite3

DB = "database_enriched/car_database.db"
con = sqlite3.connect(DB); cur = con.cursor()

assert cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0] == 1921
assert cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0] == 7514

print("--- 1. oil spec repairs (web-verified) ---")
for code, (vis, cap, note) in {
    "MDJ": ("0W-40", 5.7, "step32c repair: lemon 4.68L rejected; 718 2.5 C40 0W-40, 6qt/5.7L [docs.lnengineering.com/article/31-porsche-engine-oil-capacities-and-specifications + NHTSA MC-10172079 C40=0W-40/5W-40]"),
    "MDW": ("0W-40", 7.99, "step32c fill: 718 4.0 C40 0W-40, 8.5qt/8.0L (cap 7.99 kept) [docs.lnengineering.com + NHTSA MC-10172079]"),
}.items():
    row = cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?", (code,)).fetchone()
    cur.execute("UPDATE engine_service_specs SET oil_viscosity=?, oil_capacity_with_filter_l=?, oil_spec_source=? WHERE engine_code=?",
                (vis, cap, note, code))
    print(f"  {code}: {row} -> {vis}/{cap}")

print("\n--- 2. consolidation MCT/MDH -> MCT.LA (Macan Turbo 3.6TT 400hp) ---")
for old in ("MCT", "MDH"):
    vids = cur.execute("SELECT id FROM vehicle_variants WHERE engine_code=?", (old,)).fetchall()
    if not vids:
        print(f"  {old}: no variants"); continue
    for (vid,) in vids:
        cur.execute("""UPDATE vehicle_variants SET engine_code='MCT.LA', engine_power_hp=400,
            engine_power_kw=298, engine_type=COALESCE(engine_type,'3.6 V6 TT') WHERE id=?""", (vid,))
    for table in ("engine_service_specs", "engine_technical_specs"):
        cols = [c[1] for c in cur.execute(f"PRAGMA table_info({table})") if c[1] != "engine_code"]
        src = cur.execute(f"SELECT {','.join(cols)} FROM {table} WHERE engine_code=?", (old,)).fetchone()
        if src:
            if cur.execute("SELECT 1 FROM " + table + " WHERE engine_code='MCT.LA'").fetchone():
                sets = ", ".join(f"{c}=COALESCE({c}, ?)" for c in cols)
                cur.execute(f"UPDATE {table} SET {sets} WHERE engine_code='MCT.LA'", (*src,))
            else:
                cur.execute(f"INSERT INTO {table} (engine_code, {','.join(cols)}) VALUES (?{',?'*len(cols)})", ('MCT.LA', *src))
        cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (old,))
    cur.execute("DELETE FROM engines WHERE engine_code=?", (old,))
    print(f"  consolidated {len(vids)} {old} variant(s) -> MCT.LA @400hp; retired engine row")
cur.execute("""UPDATE engines SET count_variants =
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""")

print("\n--- 3. 918 Spyder M18.00 fix ---")
cur.execute("""UPDATE vehicle_variants SET engine_power_hp=887, engine_power_kw=661,
    fuel='Hybrid', engine_type='4.6 V8 NA + 2 e-motors (918 Spyder PHEV 887hp combined)' WHERE engine_code='M18.00'""")
cur.execute("""UPDATE engines SET power_hp=887, fuel='Hybrid',
    engine_type='4.6 V8 NA + 2 e-motors (918 Spyder PHEV 887hp combined US; 608hp V8 alone)' WHERE engine_code='M18.00'""")
cur.execute("UPDATE engine_service_specs SET power_hp=887 WHERE engine_code='M18.00'")
print("  M18.00 = 918 Spyder: 874 (887PS conv) -> 887hp US combined; fuel -> Hybrid (PHEV)")

print("\n--- 4. hybrid-family fuel fixes ---")
for code in ("M06.EC", "MCG.E", "MCG.FA"):
    cur.execute("UPDATE engines SET fuel='Hybrid' WHERE engine_code=?", (code,))
    print(f"  engines.fuel {code} -> Hybrid")
n = cur.execute("""UPDATE vehicle_variants SET fuel='Hybrid' WHERE car_brand='Porsche' AND fuel='Petrol'
    AND car_model LIKE '%Hybrid%' AND engine_code IN ('M06.EC','MCG.E','MCG.FA','MCG.EA')""").rowcount
print(f"  {n} hybrid-named Petrol variant(s) -> Hybrid")
con.commit()

print("\n--- final audit ---")
print("fuel conflicts Porsche:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.car_brand='Porsche' AND v.fuel != e.fuel""").fetchone()[0])
print("NULL powers Porsche non-LEMON:", cur.execute("""SELECT engine_code, COUNT(*) FROM vehicle_variants
    WHERE car_brand='Porsche' AND engine_power_hp IS NULL AND engine_code NOT LIKE 'LEMON%' GROUP BY 1""").fetchall())
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
print("Porsche fuels:", dict(cur.execute("SELECT fuel, COUNT(*) FROM vehicle_variants WHERE car_brand='Porsche' GROUP BY fuel").fetchall()))
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close()
