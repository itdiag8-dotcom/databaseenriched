"""Step 13c: post-13b conflation fixes for batch 4 (Mercedes).
1. Metris split: AMSOIL/Wikiwand confirm Metris = M274.920 code (208hp van tune), but its 8qt/7.57L
   sump differs from the ~6.3qt cars -> separate DB engine row 'M274.920 (Metris)' (same convention
   as 'M274 PHEV (C350e)'), remap 8 variants, power 208.
2. S450 2018-2020 rule error: W222 S450 = M276.824 3.0 V6 BiTurbo 362hp (AMSOIL engine code;
   CarBuzz W222 gen table) - NOT M256 I6 (that arrived with W223 S500 2021+). Remap 3 variants.
3. S560e: system output 469hp (362 V6 + 121 e-motor, Car and Driver), fuel Hybrid, clean engine_type.
4. M276.824 spec row: ESTIMATE 5W-40/4.6 -> 0W-30 / 6.52L (6.9qt) per AMSOIL S560e/S450 lookup.
5. M274.920 spec row: stale power 211 (Euro) -> 241; oil -> car-only variant-weighted majority.
6. All other step-13 targets: normalize oil vis/cap to variant-weighted lemon majorities (refines
   step-13 first-code merges and step-13b distinct-code majorities).
Then: count_variants recompute, decisions CSV update, final audits.
"""
import sqlite3, csv, shutil
from collections import Counter
from datetime import date

DB = "database_enriched/car_database.db"
CSV = "database_enriched/csv_exports/21_lemon_batch4_decisions.csv"

AMSOIL_S560E = "https://www.amsoil.com/lookup/auto-and-light-truck/2019/mercedes-benz/s560e/3-0l-6-cyl-engine-code-276-824-p-turbo/ (S560e 276.824, 6.9 qt w/filter, 0W-30/0W-40)"
AMSOIL_S450 = "https://www.amsoil.com/lookup/auto-and-light-truck/2019/mercedes-benz/s450/3-0l-6-cyl-engine-code-276-824-d-turbo/ (2019-20 S450 engine code 276.824)"
AMSOIL_METRIS = "https://www.amsoil.com/lookup/auto-and-light-truck/2022/mercedes-benz/metris/2-0l-4-cyl-engine-code-274-920-7-turbo/ (2022 Metris engine code 274.920)"
WIKI_M274 = "https://www.wikiwand.com/en/Mercedes-Benz_M270/M274_engine (M274.920 DE20 tunes 156-253hp incl. 208hp)"
CARBUZZ_W222 = "https://carbuzz.com/cars/mercedes-benz/s-class/generations/ (2018-20 W222 S450 3.0TT V6 362hp)"
CD_S560E = "https://www.caranddriver.com/reviews/a24789240/2019-mercedes-benz-s560e-plug-in-hybrid-drive/ (S560e 362hp V6 + 121hp e-motor = 469hp system)"

METRIS = "M274.920 (Metris)"

shutil.copy(DB, f"database_enriched/backups/car_database_backup_pre_step13c_{date.today().isoformat()}.db")
con = sqlite3.connect(DB); cur = con.cursor()
bak = sqlite3.connect("database_enriched/backups/car_database_backup_pre_step13_2026-09-30.db"); bcur = bak.cursor()

dec = list(csv.DictReader(open(CSV, newline="")))
by_old = {r["old_engine_code"]: r for r in dec}

# ---------- 1. Metris split ----------
if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (METRIS,)).fetchone():
    cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
        cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP13_VERIFIED')""",
        (METRIS, "2.0 I4 Turbo (M274, van tune 208hp)", "Petrol", 1991, 208, 4))
    print(f"created engines row {METRIS}")
# spec row: copy all columns from M274.920 then override oil
cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_service_specs)")][1:]
src = cur.execute(f"SELECT {','.join(cols)} FROM engine_service_specs WHERE engine_code='M274.920'").fetchone()
cur.execute(f"INSERT INTO engine_service_specs (engine_code, {','.join(cols)}) VALUES (?{',?'*len(cols)})",
            (METRIS, *src))
cur.execute("""UPDATE engine_service_specs SET oil_viscosity='0W-30', oil_capacity_with_filter_l=7.57,
    oil_spec_source=? WHERE engine_code=?""",
    (f"lemon.dogeware.me LEMON majority 6/6 Metris rows (via step13c); engine code 274.920 [AMSOIL Metris] "
     f"[Wikiwand M274 208hp tune] | {AMSOIL_METRIS} | {WIKI_M274}", METRIS))
# technical specs copy
tcols = [c[1] for c in cur.execute("PRAGMA table_info(engine_technical_specs)")][1:]
tsrc = cur.execute(f"SELECT {','.join(tcols)} FROM engine_technical_specs WHERE engine_code='M274.920'").fetchone()
if tsrc and not cur.execute("SELECT 1 FROM engine_technical_specs WHERE engine_code=?", (METRIS,)).fetchone():
    cur.execute(f"INSERT INTO engine_technical_specs (engine_code, {','.join(tcols)}) VALUES (?{',?'*len(tcols)})",
                (METRIS, *tsrc))
    print(f"copied technical specs -> {METRIS}")
n = 0
for r in dec:
    if r["model"].upper() == "METRIS":
        cur.execute("""UPDATE vehicle_variants SET engine_code=?, engine_power_hp=208,
            engine_type='2.0 I4 Turbo (M274, van tune 208hp)' WHERE id=?""", (METRIS, r["variant_id"]))
        r["new_engine_code"] = METRIS
        r["evidence"] += f" | step13c: split van tune (8qt sump) [AMSOIL Metris]"
        n += 1
print(f"Metris: {n} variants -> {METRIS}")

# ---------- 2. S450 remap + 3. S560e power/fuel ----------
for r in dec:
    if r["model"] == "S450":
        cur.execute("""UPDATE vehicle_variants SET engine_code='M276.824',
            engine_power_hp=362, engine_type='3.0 V6 BiTurbo (M276)', fuel='Petrol' WHERE id=?""", (r["variant_id"],))
        r["new_engine_code"] = "M276.824"
        r["evidence"] += f" | step13c FIX: W222 S450 = M276.824 V6 362hp, not M256 [AMSOIL S450][CARBUZZ W222]"
for r in dec:
    if r["model"] in ("S560e", "S560E"):
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=469, fuel='Hybrid',
            engine_type='3.0 V6 BiTurbo PHEV (M276.824)' WHERE id=?""", (r["variant_id"],))
        r["evidence"] += f" | step13c: system output 469hp [CD S560e]"
print("S450 x3 -> M276.824 (362hp V6); S560e x2 -> 469hp Hybrid")

# M276.824 engine/spec rows: clean label, US 362hp tune, AMSOIL oil
cur.execute("""UPDATE engines SET engine_type='3.0 V6 BiTurbo (M276, PHEV-capable)', power_hp=362
    WHERE engine_code='M276.824'""")
cur.execute("""UPDATE engine_service_specs SET power_hp=362, oil_viscosity='0W-30',
    oil_capacity_with_filter_l=6.52,
    oil_spec_source=? WHERE engine_code='M276.824'""",
    (f"AMSOIL 2019 S560e lookup: 276.824, 6.9 qt w/filter, 0W-30 (via step13c) | {AMSOIL_S560E} | {AMSOIL_S450}",))

# ---------- 4+6. variant-weighted majority normalization ----------
tgts = sorted(set(r["new_engine_code"] for r in dec))
changed = 0
for tgt in tgts:
    if tgt in (METRIS, "M276.824"):   # already explicitly set above
        continue
    vis, cap = Counter(), Counter()
    for r in dec:
        if r["new_engine_code"] != tgt:
            continue
        s = bcur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?",
                         (r["old_engine_code"],)).fetchone()
        if s and s[0]: vis[s[0]] += 1
        if s and s[1]: cap[s[1]] += 1
    if not vis and not cap:
        continue
    mv = vis.most_common(1)[0][0] if vis else None
    mc = cap.most_common(1)[0][0] if cap else None
    nv, nc = sum(vis.values()), sum(cap.values())
    cur_s = cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?", (tgt,)).fetchone()
    if cur_s and (cur_s[0], cur_s[1]) == (mv, mc):
        continue
    note = (f"lemon.dogeware.me LEMON variant-majority (via step13c): vis {mv} x{vis[mv]}/{nv}, "
            f"cap {mc}L x{cap[mc]}/{nc}")
    cur.execute("UPDATE engine_service_specs SET oil_viscosity=?, oil_capacity_with_filter_l=?, oil_spec_source=? WHERE engine_code=?",
                (mv, mc, note, tgt))
    print(f"  {tgt}: {cur_s[0]}/{cur_s[1]} -> {mv}/{mc}   ({note})")
    changed += 1
print(f"majority-normalized: {changed} targets")

# M274.920 stale power in specs row (Euro 211)
cur.execute("UPDATE engine_service_specs SET power_hp=241 WHERE engine_code='M274.920' AND power_hp=211")

# ---------- 7. count_variants ----------
cur.execute("""UPDATE engines SET count_variants =
    (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")

# ---------- 8. CSV rewrite ----------
with open(CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
    w.writeheader(); w.writerows(dec)

con.commit()

# ---------- 9. audits ----------
print("\n--- audits ---")
bad = cur.execute("""SELECT COUNT(*) FROM engine_service_specs WHERE engine_code IN
    (SELECT DISTINCT new_engine_code FROM vehicle_variants) AND oil_spec_source LIKE 'ESTIMATE%'""").fetchone()[0]
print("ESTIMATE among step-13 target codes:", bad)
for t in ["M274.920", METRIS, "M276.824", "M256 3.0 I6 Turbo"]:
    e = cur.execute("SELECT power_hp, count_variants FROM engines WHERE engine_code=?", (t,)).fetchone()
    s = cur.execute("SELECT power_hp, oil_viscosity, oil_capacity_with_filter_l FROM engine_service_specs WHERE engine_code=?", (t,)).fetchone()
    print(f"  {t}: engines(pwr,cnt)={e} specs(pwr,vis,cap)={s}")
orph = cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
    WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0]
print("orphan variant->engine refs:", orph)
print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
con.close(); bak.close()
