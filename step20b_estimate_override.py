"""Step 14b: post-apply spec normalization for batch 5 (BMW).
1. Override ESTIMATE-heuristic oil specs on step-14 targets with variant-weighted lemon-crawl
   majorities from the pre_step20 backup (13b/13c pattern).
2. Normalize ALL step-14 targets to those majorities (fixes first-code merges).
3. Sync engine_service_specs.power_hp from engines (NULL/stale fills).
4. i3 Electric: note that oil spec = range-extender engine only (BEV has none).
"""
import sqlite3, csv
from collections import Counter

DB = "database_enriched/car_database.db"
BAK = "database_enriched/backups/car_database_backup_pre_step20_2026-09-30.db"
CSV = "database_enriched/csv_exports/28_lemon_batch11_decisions.csv"

con = sqlite3.connect(DB); cur = con.cursor()
bak = sqlite3.connect(BAK); bcur = bak.cursor()
dec = list(csv.DictReader(open(CSV, newline="")))
tgts = sorted(set(r["new_engine_code"] for r in dec))

overridden = normalized = kept = 0
for tgt in tgts:
    vis, cap = Counter(), Counter()
    for r in dec:
        if r["new_engine_code"] != tgt: continue
        s = bcur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?",
                         (r["old_engine_code"],)).fetchone()
        if s and s[0]: vis[s[0]] += 1
        if s and s[1]: cap[s[1]] += 1
    cur_s = cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l, oil_spec_source FROM engine_service_specs WHERE engine_code=?", (tgt,)).fetchone()
    if cur_s is None:
        print(f"  !! {tgt}: NO SPEC ROW"); continue
    if not vis and not cap:
        kept += 1; continue
    mv = vis.most_common(1)[0][0] if vis else cur_s[0]
    mc = cap.most_common(1)[0][0] if cap else cur_s[1]
    if (cur_s[0], cur_s[1]) == (mv, mc):
        # already majority - only refresh source note if ESTIMATE
        if (cur_s[2] or "").upper().startswith("ESTIMATE"):
            cur.execute("UPDATE engine_service_specs SET oil_spec_source=? WHERE engine_code=?",
                (f"lemon.dogeware.me LEMON variant-majority (via step20b): vis {mv} x{vis[mv]}/{sum(vis.values())}, "
                 f"cap {mc}L x{cap[mc]}/{sum(cap.values())}", tgt))
            overridden += 1
        continue
    was_est = (cur_s[2] or "").upper().startswith("ESTIMATE")
    note = (f"lemon.dogeware.me LEMON variant-majority (via step20b): vis {mv} x{vis[mv]}/{sum(vis.values())}, "
            f"cap {mc}L x{cap[mc]}/{sum(cap.values())}")
    cur.execute("UPDATE engine_service_specs SET oil_viscosity=?, oil_capacity_with_filter_l=?, oil_spec_source=? WHERE engine_code=?",
                (mv, mc, note, tgt))
    print(f"  {'EST->' if was_est else '     '}{tgt}: {cur_s[0]}/{cur_s[1]} -> {mv}/{mc}")
    if was_est: overridden += 1
    else: normalized += 1

# i3 note (values = range extender oil)
cur.execute("""UPDATE engine_service_specs SET oil_spec_source=
    'BMW i3: values are the 647cc 2-cyl RANGE-EXTENDER engine oil (0W-30 ~2.5L, lemon crawl majority 9/9 rows via step20b); pure-BEV i3 has no engine oil (single-speed reducer fluid separately)'
    WHERE engine_code='i3 Electric (I01)'""")

# power sync
synced = 0
for tgt in tgts:
    e = cur.execute("SELECT power_hp FROM engines WHERE engine_code=?", (tgt,)).fetchone()
    s = cur.execute("SELECT power_hp FROM engine_service_specs WHERE engine_code=?", (tgt,)).fetchone()
    if e and s and e[0] is not None and s[0] != e[0]:
        cur.execute("UPDATE engine_service_specs SET power_hp=? WHERE engine_code=?", (e[0], tgt))
        synced += 1
print(f"\noverridden(ESTIMATE): {overridden} | normalized: {normalized} | kept: {kept} | power synced: {synced}")

con.commit()
print("\n--- audit ---")
ph = ",".join("?"*len(tgts))
print("ESTIMATE among step-14 targets:", cur.execute(
    f"SELECT COUNT(*) FROM engine_service_specs WHERE engine_code IN ({ph}) AND oil_spec_source LIKE 'ESTIMATE%'", tuple(tgts)).fetchone()[0])
print("spec power mismatches vs engines:", sum(
    1 for t in tgts
    if (lambda e, s: e and s and e[0] is not None and s[0] != e[0])(
        cur.execute("SELECT power_hp FROM engines WHERE engine_code=?", (t,)).fetchone(),
        cur.execute("SELECT power_hp FROM engine_service_specs WHERE engine_code=?", (t,)).fetchone())))
print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close(); bak.close()
