"""Step 57c: undo three step57b "normalizations" that traded curated specs for single crawl rows.

step57b adopts the most common fill/viscosity among a code's LEMON rows. With only one or two
rows voting that is not a majority, it is an anecdote, and three of its six changes replaced
better data:

- `5.0 V10 TDI (Touareg)`: 11.45 L -> 13.53 L on the strength of one row. The curated figure is
  restored; 13.53 L (14.3 qt) is recorded in the note as the crawl's listing.
- `M46.20` (Cayenne 3.6): viscosity 0W-40 -> 5W-30. Porsche's approval list for this engine is
  the 0W-40/5W-40 A40 grades; the fill (8.49 vs 8.51 L) was never in dispute.
- `CXDA` (Golf GTI Mk8): 0W-20 -> 0W-30. VW 508 00 is a 0W-20 specification.
"""
import sqlite3

DB = "database_enriched/car_database.db"
REVERTS = [
    ("5.0 V10 TDI (Touareg)", 11.45, "5W-40",
     "VW service data (via step57c): Touareg 5.0 V10 TDI takes 11.45 L with filter on 5W-40 (VW 506 01). "
     "The single MY2008 crawl row lists 13.53 L, which step57b had briefly adopted."),
    ("M46.20", 8.49, "0W-40",
     "Porsche service data (via step57c): Cayenne 3.6 V6 takes ~8.5 L with filter on an A40-approved "
     "0W-40/5W-40 grade; the MY2015 crawl row's 5W-30 is not on the approval list."),
    ("CXDA", 5.67, "0W-20",
     "VW service data (via step57c): EA888 Gen3B (GTI Mk8) takes 5.67 L on VW 508 00, a 0W-20 "
     "specification; the MY2025 crawl row's 0W-30 had been adopted by step57b."),
]

con = sqlite3.connect(DB)
for code, cap, vis, note in REVERTS:
    before = con.execute("SELECT oil_capacity_with_filter_l, oil_viscosity FROM engine_service_specs WHERE engine_code=?", (code,)).fetchone()
    con.execute("UPDATE engine_service_specs SET oil_capacity_with_filter_l=?, oil_viscosity=?, "
                "oil_spec_source=?, data_confidence='STEP57C_VERIFIED' WHERE engine_code=?", (cap, vis, note, code))
    print(f"  {code}: {before[0]} L/{before[1]} -> {cap} L/{vis}")
con.commit()
print("orphan refs:", con.execute("SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code "
                                  "WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL").fetchone()[0])
con.close()
