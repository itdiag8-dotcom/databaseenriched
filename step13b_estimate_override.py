"""Step 13b: override ESTIMATE-heuristic oil specs on step-13 Mercedes targets with trusted
lemon-crawl majority values recovered from the pre_step13 backup (step-10b/12b pattern).
Only overrides where retired LEMON rows for that target carried real crawled specs."""
import sqlite3, csv
from collections import Counter

DB = "database_enriched/car_database.db"
BAK = "database_enriched/backups/car_database_backup_pre_step13_2026-09-30.db"

dec = list(csv.DictReader(open("database_enriched/csv_exports/21_lemon_batch4_decisions.csv")))
by_target = {}
for r in dec:
    by_target.setdefault(r["new_engine_code"], []).append(r["old_engine_code"])

con = sqlite3.connect(DB); cur = con.cursor()
bak = sqlite3.connect(BAK); bcur = bak.cursor()

fixed = kept = 0
for tgt, lemons in sorted(by_target.items()):
    row = cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l, oil_spec_source FROM engine_service_specs WHERE engine_code=?", (tgt,)).fetchone()
    if not row or not (row[2] or "").startswith("ESTIMATE"):
        continue
    vals = Counter()
    for lc in set(lemons):
        r2 = bcur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l, oil_spec_source FROM engine_service_specs WHERE engine_code=?", (lc,)).fetchone()
        if r2 and r2[0] and r2[1] and "lemon" in (r2[2] or "").lower():
            vals[(r2[0], r2[1])] += 1
    if not vals:
        kept += 1
        continue
    (vis, cap), n = vals.most_common(1)[0]
    total = sum(vals.values())
    note = (f"lemon.dogeware.me LEMON majority {n}/{total} rows (via step13b) "
            f"[source rows: {', '.join(sorted(set(l for l in lemons))[:3])}...]")
    cur.execute("""UPDATE engine_service_specs SET oil_viscosity=?, oil_capacity_with_filter_l=?, oil_spec_source=?
                   WHERE engine_code=?""", (vis, cap, note, tgt))
    print(f"  {tgt}: {row[0]}/{row[1]} -> {vis}/{cap}  ({n}/{total} lemon rows)")
    fixed += 1

con.commit()
print(f"\noverridden: {fixed} | left as ESTIMATE (no lemon data): {kept}")
print("ESTIMATE remaining among step-13 targets:",
      cur.execute("""SELECT COUNT(*) FROM engine_service_specs WHERE engine_code IN
        (SELECT DISTINCT new_engine_code FROM vehicle_variants WHERE engine_code IS NOT NULL)
        AND oil_spec_source LIKE 'ESTIMATE%'""").fetchone()[0], "(informational, all brands)")
con.close(); bak.close()
