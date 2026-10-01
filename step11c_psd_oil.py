"""Step 11c: Power Stroke oil-capacity fixes on the sibling rows missed by step 11.
step 11 fixed '7.3 Power Stroke' (12.87->14.2) and '6.0 Power Stroke' (16.08->14.2);
the database also carries parallel rows '7.3 V8 Powerstroke', 'T444E' (same engine,
International navistar), '6.4 V8 Powerstroke', '6.7 V8 Powerstroke' with 9.5 L oil —
10 US qt, wrong for every Power Stroke application.
Cited: 7.3/6.4 = 15 US qt (14.2 L) w/ filter; 6.7 = 13 US qt (12.3 L). See CIT in
step11_small_cleanups.py (egrperformance / prosourcediesel / suncentauto).
"""
import sqlite3, csv

DB = "database_enriched/car_database.db"
con = sqlite3.connect(DB)
cur = con.cursor()
CIT = ("egrperformance.com/blogs/news/6-7-powerstroke-oil-capacity + "
       "prosourcediesel.com (7.3/6.0/6.4 = 15 US qt = 14.2 L w/filter; 6.7 = 13 US qt = 12.3 L)")

FIX = {"7.3 V8 Powerstroke": 14.2, "T444E": 14.2, "6.4 V8 Powerstroke": 14.2, "6.7 V8 Powerstroke": 12.3}
log = []
for code, cap in FIX.items():
    row = cur.execute("SELECT oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?", (code,)).fetchone()
    if not row:
        log.append(f"  {code}: no spec row, skipped"); continue
    old = row[0]
    if abs((old or 0) - cap) < 0.01:
        log.append(f"  {code}: already {cap} L"); continue
    cur.execute("""UPDATE engine_service_specs SET oil_capacity_with_filter_l=?, oil_spec_source=?
                   WHERE engine_code=?""",
                (cap, f"corrected Step 11c (was {old} L = 10 US qt, wrong for PSD): {CIT}", code))
    log.append(f"  {code}: oil {old} -> {cap} L")

con.commit()
print("\n".join(log))
print("\n=== VERIFY ===")
for r in cur.execute("""SELECT engine_code, oil_capacity_with_filter_l FROM engine_service_specs
    WHERE engine_code LIKE '%Power Stroke%' OR engine_code LIKE '%Powerstroke%' OR engine_code='T444E'
    ORDER BY engine_code"""):
    print("  ", r)

with open("database_enriched/csv_exports/19_small_cleanups_log.csv", "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["=== step 11c: PSD sibling oil fixes ==="])
    for l in log:
        w.writerow([l])
con.close()
