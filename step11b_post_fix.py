"""Step 11b: post-apply fixes for step 11.
- Delete the two orphaned Caterham CSR junk engine rows ('2.3 16v 5MT'/'2.3 16v 6MT')
  (their variants 2193/2194 were remapped to 'Duratec 2.3 CSR' but the rows were left behind).
- Recompute engines.count_variants from actual vehicle_variants links (remaps bumped the
  target count but never the source, and newly created rows started at 0).
Deterministic; no dry-run needed.
"""
import sqlite3, csv

DB = "database_enriched/car_database.db"
con = sqlite3.connect(DB)
cur = con.cursor()
log = []

# 1. delete orphaned junk rows (specs first — FK)
for code in ("2.3 16v 5MT", "2.3 16v 6MT"):
    linked = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code=?", (code,)).fetchone()[0]
    if linked:
        raise SystemExit(f"ABORT: {code} still has {linked} variants — not orphaned, review manually")
    for t in ("engine_service_specs", "engine_technical_specs"):
        cur.execute(f"DELETE FROM {t} WHERE engine_code=?", (code,))
    cur.execute("DELETE FROM engines WHERE engine_code=?", (code,))
    log.append(f"deleted orphaned junk engine row {code}")

# 2. recompute count_variants for every engine from actual links
cur.execute("""UPDATE engines SET count_variants =
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")
log.append("recomputed engines.count_variants from actual vehicle_variants links (all 15k+ rows)")

con.commit()

print("=== VERIFY ===")
print("garbled rows gone:",
      cur.execute("SELECT COUNT(*) FROM engines WHERE engine_code IN ('M54256S5','G4KR','H4KR','25V6S1','2.3 16v 5MT','2.3 16v 6MT')").fetchone()[0], "(0 expected)")
print("count mismatches:",
      cur.execute("""SELECT COUNT(*) FROM (SELECT e.engine_code FROM engines e
        LEFT JOIN vehicle_variants v ON v.engine_code=e.engine_code
        GROUP BY e.engine_code HAVING e.count_variants != COUNT(v.id))""").fetchone()[0], "(0 expected)")
print("M73B54:", cur.execute("SELECT engine_code, count_variants FROM engines WHERE engine_code='M73B54'").fetchone())
print("C20LET:", cur.execute("SELECT engine_code, count_variants FROM engines WHERE engine_code='C20LET'").fetchone())
print("orphan variant->engine refs:",
      cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0], "(0 expected)")
print("totals:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0], "engines /",
      cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NOT NULL").fetchone()[0], "linked variants /",
      cur.execute("SELECT COUNT(*) FROM remapping_queue WHERE status='pending'").fetchone()[0], "queue pending")

with open("database_enriched/csv_exports/19_small_cleanups_log.csv", "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for l in log:
        w.writerow([l])
con.close()
print("done; log appended to 19_small_cleanups_log.csv")
