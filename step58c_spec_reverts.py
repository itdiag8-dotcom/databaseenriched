"""Step 58c: protect two shared engine specs from single-row crawl votes (final batch).

- `3.7 Ti-VCT V6` serves 79 variants, most of them F-150s and Mustangs, which take 5.67 L
  (6 qt). step58b moved the code to 5.2 L on the strength of the three Lincoln MKS rows; the MKS
  does take 5.5 qt, but it is the exception and is recorded as such in the note.
- `A25A-FXS` serves 66 variants worldwide. The single MY2025 Crown row's 0W-8 at 4.25 L is the
  JDM specification; the US figure for this engine is 0W-16/0W-20 at 4.54 L. 0W-8 remains the
  evidence that identified the row as a hybrid - it just should not redefine the engine.
"""
import sqlite3

DB = "database_enriched/car_database.db"
REVERTS = [
    ("3.7 Ti-VCT V6", 5.67, "5W-20",
     "Ford service data (via step58c): 3.7 Ti-VCT V6 takes 5.67 L (6.0 qt) with filter on 5W-20 in the "
     "F-150/Mustang applications that make up most of this code's variants; the Lincoln MKS and Taurus "
     "take 5.2 L (5.5 qt)."),
    ("A25A-FXS", 4.54, "0W-20",
     "Toyota service data (via step58c): A25A-FXS takes 4.54 L with filter on 0W-16 (0W-20 acceptable) "
     "in US applications. The MY2025 Crown crawl row lists the JDM 0W-8 at 4.25 L - the grade that "
     "identified the row as a hybrid, but not the figure for the whole engine."),
]

con = sqlite3.connect(DB)
for code, cap, vis, note in REVERTS:
    b = con.execute("SELECT oil_capacity_with_filter_l, oil_viscosity FROM engine_service_specs WHERE engine_code=?", (code,)).fetchone()
    con.execute("UPDATE engine_service_specs SET oil_capacity_with_filter_l=?, oil_viscosity=?, "
                "oil_spec_source=?, data_confidence='STEP58C_VERIFIED' WHERE engine_code=?", (cap, vis, note, code))
    print(f"  {code}: {b[0]} L/{b[1]} -> {cap} L/{vis}")
con.commit(); con.close()
