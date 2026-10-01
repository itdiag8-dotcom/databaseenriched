"""Step 11b - electric rows that still carry combustion attributes.

Step 11 established that NULL cylinders/displacement is the CORRECT state for an electric or
hydrogen row. The mirror-image defect also exists: 13 pure-electric rows list **4 cylinders**,
inherited from whatever default the integration used. Hybrids are deliberately excluded - a
hybrid genuinely has a combustion engine, so 2AR-FXE at 2493cc/4cyl is right.

One row is a different animal. `A14XFL` is fuel=Electric, 151hp, 4 cylinders, no displacement,
on an Opel/Vauxhall **Ampera** - which is the European Chevrolet Volt, a range-extender whose
1.4 petrol engine is exactly what A14XFL designates. The database already models the Volt
correctly as `Voltec 1.4 EREV (Volt)`: 1398cc, 4 cylinders, fuel **Hybrid**. A14XFL is brought
into line with its own twin rather than left as an "electric engine with four cylinders".
Its descriptors were junk as well ("216 1.6i" on the engine row, "FEITENG Closed Off-Road
Vehicle" on a Vauxhall Ampera variant).
"""
import sqlite3

DB = "database_enriched/car_database.db"
EV_CYL = ["EM61", "EM780.992", "EM780.994", "5AM400", "4ET50", "LUU", "3CG401", "3CG400",
          "IB1P25B", "5DC700", "EABA", "EAGA"]
DESC = "1.4 I4 EREV range extender + electric (Ampera/Volt, 151hp system)"

con = sqlite3.connect(DB)
n = 0
for code in EV_CYL:
    n += con.execute("UPDATE engines SET cylinders=NULL WHERE engine_code=? AND cylinders IS NOT NULL",
                     (code,)).rowcount
print(f"cleared bogus cylinder counts on {n} electric rows")

con.execute("UPDATE engines SET fuel='Hybrid', displacement_cc=1398, cylinders=4, engine_type=? "
            "WHERE engine_code='A14XFL'", (DESC,))
v = con.execute("UPDATE vehicle_variants SET fuel='Hybrid', engine_type=? WHERE engine_code='A14XFL'",
                (DESC,)).rowcount
print(f"A14XFL -> Hybrid 1398cc/4cyl, descriptor fixed (+{v} variants)")
con.commit()

g = lambda q: con.execute(q).fetchone()[0]
print("\n--- verify ---")
print("electric rows still carrying cylinders:", g("""SELECT count(*) FROM engines
    WHERE fuel='Electric' AND cylinders IS NOT NULL"""))
print("electric rows carrying a displacement:", g("""SELECT count(*) FROM engines
    WHERE fuel='Electric' AND displacement_cc IS NOT NULL"""))
print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
    (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
con.close()
