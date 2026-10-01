"""Step 49c: clear the 24 Mini variants that an earlier pass left on placeholder engine rows.

Before this batch, 24 Mini "Cooper" variants (MY2007-2015) pointed at bare engine-family codes
the crawl had produced from its "Eng CD" strings - `B38`, `B48`, `N16`, `N18`, `W10`, `N12`,
`N14` and the `...M0` stubs - most of which carry no displacement, no power and no cylinder
count. They all have NULL variant power as a result. Batch 40 gave Mini a complete, verified
engine vocabulary, so this script attaches those variants to it:

  B38, B38A15M0        -> B38A15A  1.5 I3 turbo, 134hp (Cooper F56)
  B48, B46A20M0, B48A20B -> B46A20A 2.0 I4 turbo, 189hp (Cooper S F56)
  N16                  -> N16B16A  1.6 NA, 121hp (Cooper R56 LCI)
  N18                  -> N18B16A  1.6 turbo, 181hp (Cooper S R56 LCI)
  W10 (MY2007-2008)    -> W10B16 (Cooper, 115hp) - the R52 convertible's 1.6, not the 1.4 One

`N12` (118hp), `N14` (173hp), `W11` (168hp), `N18B16A` and `N18B16C` are real rows with real
data, so their variants only need the power backfilled. Placeholder rows left with zero variants
are retired; `B48A20B` keeps its three BMW 2 Active Tourer variants and only loses its junk
"Leaf Spring Suspension" descriptor.
"""
import sqlite3

DB = "database_enriched/car_database.db"
RELINK = {  # placeholder -> (target code, power)
    "B38": ("B38A15A", 134), "B38A15M0": ("B38A15A", 134),
    "B48": ("B46A20A", 189), "B46A20M0": ("B46A20A", 189), "B48A20B": ("B46A20A", 189),
    "N16": ("N16B16A", 121), "N18": ("N18B16A", 181),
    "W10": ("W10B16 (Cooper, 115hp)", 115),
}
BACKFILL = {"N12": 118, "N14": 173, "W11": 168, "N18B16A": 181, "N18B16C": 208}

con = sqlite3.connect(DB); cur = con.cursor()
cur.execute("""UPDATE engines SET engine_type='2.0 I4 Turbo B48A20B (BMW 2 Active Tourer 225i, 231hp)',
    data_confidence='STEP49C_VERIFIED' WHERE engine_code='B48A20B'""")

touched = set()
for ph, (tgt, hp) in RELINK.items():
    ids = [r[0] for r in cur.execute(
        "SELECT id FROM vehicle_variants WHERE car_brand='Mini' AND engine_code=? AND engine_power_hp IS NULL", (ph,))]
    if not ids:
        continue
    cur.execute("UPDATE vehicle_variants SET engine_code=?, engine_power_hp=? WHERE id IN (%s)"
                % ",".join("?" * len(ids)), [tgt, hp] + ids)
    print(f"  {ph} -> {tgt}: {len(ids)} variants @ {hp}hp")
    touched.update([ph, tgt])

for code, hp in BACKFILL.items():
    n = cur.execute("""UPDATE vehicle_variants SET engine_power_hp=? WHERE car_brand='Mini'
        AND engine_code=? AND engine_power_hp IS NULL""", (hp, code)).rowcount
    if n:
        print(f"  {code}: power backfilled on {n} variants @ {hp}hp")

for code in sorted(touched):
    n = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code=?", (code,)).fetchone()[0]
    if n == 0 and code in RELINK:
        cur.execute("DELETE FROM engine_service_specs WHERE engine_code=?", (code,))
        cur.execute("DELETE FROM engine_technical_specs WHERE engine_code=?", (code,))
        cur.execute("DELETE FROM engines WHERE engine_code=?", (code,))
        print(f"  retired empty placeholder: {code}")
    else:
        cur.execute("UPDATE engines SET count_variants=? WHERE engine_code=?", (n, code))

con.commit()
print("\n--- audit ---")
print("Mini NULL-power variants:", cur.execute(
    "SELECT COUNT(*) FROM vehicle_variants WHERE car_brand='Mini' AND engine_power_hp IS NULL").fetchone()[0])
print("Mini fuel conflicts:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
    JOIN engines e ON e.engine_code=v.engine_code WHERE v.car_brand='Mini' AND v.fuel<>e.fuel""").fetchone()[0])
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM engines e WHERE e.engine_code=v.engine_code)""").fetchone()[0])
print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines e WHERE e.count_variants <>
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)""").fetchone()[0])
print("engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
con.close()
