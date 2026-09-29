#!/usr/bin/env python3
"""
STEP 10b: follow-up to steps 9/10 - where a target engine's service-spec row still carries
ESTIMATE-heuristic oil/coolant values (pre-lemon placeholders), override them with the real
crawled lemon specs for that engine (recovered from the pre-step9/pre-step10 backups).
Never touches OEM- or lemon-sourced values. Also aligns ESH/EZH engine rows.
"""
import sqlite3, csv, shutil, sys
from datetime import date

DB = "database_enriched/car_database.db"
APPLY = "--apply" in sys.argv

OIL_FIELDS = ['oil_viscosity','oil_standard','oil_acea','oil_oem_spec','oil_capacity_with_filter_l',
              'oil_capacity_without_filter_l','oil_change_interval_km','oil_change_interval_months']
COOL_FIELDS = ['coolant_type','coolant_spec','coolant_capacity_l','coolant_change_interval_km','coolant_change_interval_months']

con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=ON")

# lemon->target mapping (batch 1 + 2)
mapping = {}
for f in ('17_lemon_replacement_decisions.csv', '18_lemon_batch2_decisions.csv'):
    for r in csv.DictReader(open(f'database_enriched/csv_exports/{f}')):
        mapping[r['old_engine_code']] = r['new_engine_code']

b9 = sqlite3.connect('database_enriched/backups/car_database_backup_pre_step9_2026-09-29.db').cursor()
b10 = sqlite3.connect('database_enriched/backups/car_database_backup_pre_step10_2026-09-29.db').cursor()

def lemon_row(lemon_code):
    cols = OIL_FIELDS + COOL_FIELDS + ['oil_spec_source', 'coolant_source']
    q = f"SELECT {','.join(cols)} FROM engine_service_specs WHERE engine_code=?"
    r = b9.execute(q, (lemon_code,)).fetchone() or b10.execute(q, (lemon_code,)).fetchone()
    return r

def lemon_year(code):
    import re
    m = re.search(r'_(\d{4})(?:_|$)', code)
    return int(m.group(1)) if m else 0

targets = sorted(set(mapping.values()))
fixed_oil, fixed_coolant = [], []
for target in targets:
    cur_row = cur.execute("SELECT oil_spec_source, coolant_source FROM engine_service_specs WHERE engine_code=?", (target,)).fetchone()
    if not cur_row:
        continue
    oil_src, cool_src = cur_row
    oil_is_estimate = oil_src and ('ESTIMATE' in oil_src or 'vivid' in oil_src.lower())
    cool_is_estimate = (not cool_src) or ('ESTIMATE' in (cool_src or '')) or ('vivid' in (cool_src or '').lower())
    if not (oil_is_estimate or cool_is_estimate):
        continue
    # candidate lemon rows for this target, newest year first (deterministic)
    lemons = sorted([lc for lc, t in mapping.items() if t == target], key=lemon_year, reverse=True)
    best_oil = best_cool = None
    for lc in lemons:
        r = lemon_row(lc)
        if not r: continue
        oil_vals, cool_vals = r[:len(OIL_FIELDS)], r[len(OIL_FIELDS):len(OIL_FIELDS)+len(COOL_FIELDS)]
        if best_oil is None and any(v is not None for v in oil_vals):
            best_oil = (oil_vals, r[-2], lc)
        if best_cool is None and any(v is not None for v in cool_vals):
            best_cool = (cool_vals, r[-1], lc)
        if best_oil and best_cool: break
    if oil_is_estimate and best_oil:
        sets = ", ".join(f"{c}=?" for c in OIL_FIELDS) + ", oil_spec_source=?, data_confidence='TRUSTED_LEMON'"
        vals = list(best_oil[0]) + [f"{best_oil[1]} (via step10b estimate-override from {best_oil[2]})"]
        cur.execute(f"UPDATE engine_service_specs SET {sets} WHERE engine_code=?", (*vals, target))
        fixed_oil.append((target, best_oil[2], best_oil[0][0], best_oil[0][4]))
    if cool_is_estimate and best_cool:
        sets = ", ".join(f"{c}=?" for c in COOL_FIELDS) + ", coolant_source=?"
        vals = list(best_cool[0]) + [f"{best_cool[1]} (via step10b estimate-override from {best_cool[2]})"]
        cur.execute(f"UPDATE engine_service_specs SET {sets} WHERE engine_code=?", (*vals, target))
        fixed_coolant.append((target, best_cool[2], best_cool[0][0], best_cool[0][2]))

# engine-row alignment (ESH pre-existed with Apache-style rating; EZH cosmetic)
cur.execute("UPDATE engines SET power_hp=485, displacement_cc=6415, engine_type='6.4 V8 HEMI SRT 392 (485hp)' WHERE engine_code='ESH'")
cur.execute("UPDATE engines SET engine_type='5.7 V8 HEMI (VCT)' WHERE engine_code='EZH'")

print(f"oil-spec estimate overrides: {len(fixed_oil)} targets")
for t in fixed_oil: print("  ", t)
print(f"coolant-spec estimate overrides: {len(fixed_coolant)} targets")

if not APPLY:
    print("DRY RUN - no changes. Re-run with --apply.")
    con.rollback(); con.close(); sys.exit(0)

bak = f"database_enriched/backups/car_database_backup_pre_step10b_{date.today().isoformat()}.db"
shutil.copy(DB, bak)
con.commit()
print("backup:", bak)
print("\n=== VERIFY: remaining ESTIMATE oil sources among step9/10 targets ===")
n = 0
for t in targets:
    r = cur.execute("SELECT oil_spec_source FROM engine_service_specs WHERE engine_code=?", (t,)).fetchone()
    if r and 'ESTIMATE' in (r[0] or ''):
        print("  STILL ESTIMATE:", t, r[0][:50]); n += 1
print("still estimate:", n)
print("EXL spec now:", cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l, coolant_capacity_l, oil_spec_source FROM engine_service_specs WHERE engine_code='EXL'").fetchone())
print("LM7 spec now:", cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l, oil_spec_source FROM engine_service_specs WHERE engine_code='LM7'").fetchone())
print("3.5 V6 EcoBoost spec now:", cur.execute("SELECT oil_viscosity, oil_capacity_with_filter_l, oil_spec_source FROM engine_service_specs WHERE engine_code='3.5 V6 EcoBoost'").fetchone())
print("v_vehicle_with_service:", cur.execute("SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0])
con.close()
