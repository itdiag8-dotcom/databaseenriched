#!/usr/bin/env python3
"""
Step 1 — Quarantine provably-wrong variant→engine mappings.

IMPORTANT DESIGN CONSTRAINT:
  Many car models from DIFFERENT brands legitimately share the same engine code
  in real life (platform sharing), e.g.:
    - VW-group CCZA / CAYC  -> Audi, Seat, Skoda, Volkswagen
    - Hyundai/Kia G4GC, G6BA, D4FB -> Hyundai, Kia
    - Fiat 1.3 MultiJet A13DTE      -> Fiat, Alfa Romeo, Opel, Vauxhall, Suzuki, Chevrolet
    - GM E18NVR / Z18XE family      -> Opel, Vauxhall, Saab, Holden (badge engineering)
  This script therefore does NOT quarantine a pairing just because the brand
  differs from the engine's example brand. It quarantines only pairings that
  are PHYSICALLY IMPOSSIBLE:

    R1 HARD_FUEL_CONFLICT
         Petrol <-> Diesel, Diesel <-> Ethanol/Wankel, Electric <-> anything.
         Soft label differences are KEPT: Petrol<->Hybrid (e.g. Toyota SAI with
         the correct 2AZ-FXE), Ethanol<->Petrol (flex-fuel), Wankel<->Petrol.
         Hybrid <-> Diesel/Electric is kept ONLY when displacement and power
         confirm the engine (real diesel-hybrids exist: Mercedes E 300 BlueTEC
         Hybrid, Peugeot 508/3008 Hybrid4, BMW i3 REX).

    R2 DISPLACEMENT_MISMATCH
         Displacement parsed from the variant's engine_type (e.g. "1.4 16v"
         -> 1400 cc) differs by more than 25% from engines.displacement_cc.
         Displacement does not change with tuning, so a confirmed mismatch
         means a different physical engine — regardless of brand.

    R3 POWER_MISMATCH_CROSSBRAND
         Power differs by more than 30%, the variant brand differs from the
         engine's example brand, AND displacement could not be confirmed as
         matching (unknown on either side). If displacement DOES match, the
         pairing is kept: shared engine, different tune (allowed in real life).

  Deliberately KEPT (not wrong, just imprecise — handled in later steps):
    - same-brand power spread  -> engine family with multiple tunes
      (e.g. BMW N47D20C at 114/143/163/177/184 hp, Mitsubishi 4G63T Evo)
    - cross-brand share with matching displacement & fuel
    - soft fuel-label differences

Quarantined variants get engine_code = NULL (so the app shows "no data"
instead of wrong service specs) and are moved into a review table
`remapping_queue` which keeps every value needed to re-map them correctly.

Usage:
  python3 step1_quarantine_wrong_mappings.py --dry-run
  python3 step1_quarantine_wrong_mappings.py --apply
"""
import argparse
import csv
import os
import re
import shutil
import sqlite3
import sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'database_enriched', 'car_database.db')
BACKUP_DIR = os.path.join(ROOT, 'database_enriched', 'backups')
CSV_OUT = os.path.join(ROOT, 'database_enriched', 'csv_exports', '08_remapping_queue.csv')

POWER_TOL = 0.30          # >30% power difference
DISP_TOL = 0.25           # >25% displacement difference

FUEL_SOFT_PAIRS = {
    frozenset({'Petrol', 'Hybrid'}),
    frozenset({'Ethanol', 'Petrol'}),
    frozenset({'Wankel', 'Petrol'}),
    frozenset({'Ethanol', 'Hybrid'}),
    frozenset({'Wankel', 'Hybrid'}),
}

# Brand families / platform-sharing groups. Two brands in the same set can
# legitimately share engines (badge engineering, joint platforms, engine
# customers). Used to avoid quarantining correct cross-brand mappings.
BRAND_FAMILIES = [
    # GM (incl. Opel/Vauxhall pre-2017, GM-DAT/Daewoo, Saab GM-era, Hummer H2)
    {'Chevrolet', 'GMC', 'Cadillac', 'Buick', 'Pontiac', 'Saturn', 'Oldsmobile',
     'Holden', 'Vauxhall', 'Opel', 'Saab', 'Daewoo', 'Hummer'},
    # Volkswagen Group (Bentley W12, Lamborghini V10, Porsche Cayenne share VW drivetrains)
    {'Volkswagen', 'Audi', 'Seat', 'Skoda', 'Porsche', 'Cupra', 'Bentley', 'Lamborghini'},
    # BMW + engine customers (Mini, Rolls-Royce, Alpina; L322 Range Rover TD6 = M57; Supra = B58)
    {'BMW', 'Mini', 'Rolls-Royce', 'Alpina', 'Land Rover', 'Toyota'},
    # Mercedes + shared-platform partners (Smart<->Renault Twingo, Infiniti Q30 = A-Class)
    {'Mercedes', 'Smart', 'Infiniti', 'Renault', 'Nissan'},
    # FCA / Stellantis (Dodge Ram trucks, Jeep, Iveco Daily uses Fiat F1C engines)
    {'Fiat', 'Abarth', 'Alfa Romeo', 'Lancia', 'Chrysler', 'Dodge', 'Jeep', 'Ram',
     'Maserati', 'Iveco'},
    # PSA (Opel/Vauxhall post-2017 share PSA drivetrains)
    {'Peugeot', 'Citroen', 'Citroën', 'DS', 'Opel', 'Vauxhall'},
    # Renault-Nissan-Mitsubishi
    {'Renault', 'Dacia', 'Nissan', 'Infiniti', 'Renault Samsung', 'Mitsubishi', 'Datsun'},
    # Hyundai Motor Group
    {'Hyundai', 'Kia', 'Genesis'},
    # Ford family + PAG era (Volvo/Jaguar/LR used Ford engines; Mazda partnerships)
    {'Ford', 'Lincoln', 'Mercury', 'Volvo', 'Mazda', 'Jaguar', 'Land Rover', 'Tata',
     'Polestar', 'Geely'},
    # Toyota group (GT86/BRZ with Subaru, Scion/Daihatsu in-house)
    {'Toyota', 'Lexus', 'Scion', 'Daihatsu', 'Subaru'},
    # Honda
    {'Honda', 'Acura'},
    # Suzuki-Maruti
    {'Suzuki', 'Maruti'},
]


def _norm_brand(b):
    if not b:
        return ''
    b = str(b).strip().lower()
    for a, r in (('ë', 'e'), ('é', 'e'), ('è', 'e'), ('ä', 'a'), ('ö', 'o'), ('ü', 'u')):
        b = b.replace(a, r)
    return b


def same_family(brand_a, brand_b):
    a, b = _norm_brand(brand_a), _norm_brand(brand_b)
    if not a or not b:
        return False
    if a == b:
        return True
    norm_sets = [{_norm_brand(x) for x in s} for s in BRAND_FAMILIES]
    return any(a in s and b in s for s in norm_sets)


# ---------------------------------------------------------------- helpers

def norm_fuel(f):
    if f is None:
        return None
    f = str(f).strip()
    if f.lower().startswith('hybrid'):
        return 'Hybrid'
    if f.lower().startswith('electric'):
        return 'Electric Motor'
    return f


def hard_fuel_conflict(f1, f2):
    a, b = norm_fuel(f1), norm_fuel(f2)
    if not a or not b or a == b:
        return False
    return frozenset((a, b)) not in FUEL_SOFT_PAIRS


LITRE_RE = re.compile(r'(?<![A-Za-z0-9.])(\d{1}\.\d{1})(?![\d.])')   # "1.4 16v" -> 1.4
CC_RE = re.compile(r'(?<![A-Za-z0-9])(\d{3,4})\s*cc', re.I)          # "1360 cc" -> 1360


def parse_disp_cc(s):
    """Extract displacement in cc from a free-text engine_type, or None."""
    if not s:
        return None
    m = LITRE_RE.search(s)
    if m:
        return int(round(float(m.group(1)) * 1000))
    m = CC_RE.search(s)
    if m:
        return int(m.group(1))
    return None


def displacement_check(vcc, ecc):
    """True=match, False=mismatch, None=cannot judge."""
    if vcc is None or ecc is None or ecc <= 0:
        return None
    return abs(vcc - ecc) / ecc <= DISP_TOL


def classify(rec):
    """rec: dict with variant + engine fields. Returns (reason, detail, kept_category)."""
    v, e = rec['v'], rec['e']
    vcc = parse_disp_cc(v['engine_type'])
    disp = displacement_check(vcc, e['displacement_cc'])   # True=match, False=mismatch, None=unknown

    same_brand = (v['car_brand'] or '').strip().lower() == (e['brand_example'] or '').strip().lower()
    power_diff = None
    if v['engine_power_hp'] is not None and e['power_hp'] is not None and e['power_hp'] > 0:
        power_diff = abs(v['engine_power_hp'] - e['power_hp']) * 1.0 / e['power_hp']

    # R1 — hard fuel conflict, with an override for plausible real-world hybrids:
    # "Hybrid" vs "Diesel"/"Electric" is often just label granularity, e.g.
    # Mercedes E 300 BlueTEC Hybrid (OM651), Peugeot 508/3008 Hybrid4 (DW10),
    # BMW i3 REX. If physical evidence (displacement, power) confirms the
    # engine, KEEP the pairing.
    if hard_fuel_conflict(v['fuel'], e['fuel']):
        hybrid_pair = 'Hybrid' in (norm_fuel(v['fuel']), norm_fuel(e['fuel']))
        if hybrid_pair and disp is not False and power_diff is not None and power_diff <= POWER_TOL:
            return (None, None, 'KEPT_hybrid_label_mismatch_plausible')
        d = f"variant fuel={v['fuel']} vs engine fuel={e['fuel']}"
        if disp is False:
            d += f"; displacement {vcc} vs {e['displacement_cc']} cc also mismatched"
        return ('HARD_FUEL_CONFLICT', d, None)

    # R2 — confirmed displacement mismatch (displacement never changes with tuning).
    # If power matches within 15% AND the brands share a platform family, the
    # MAPPING is most likely right and the conflict comes from bad data on one
    # side (junk variant engine_type text from Vivid, or a wrong displacement
    # value in the engine row, e.g. B38B15M0 listed as 1005 cc). Those rows are
    # KEPT and exported to a worklist for engine-row/etype fixes instead.
    if disp is False:
        power_close = power_diff is not None and power_diff <= 0.15
        if power_close and same_family(v['car_brand'], e['brand_example']):
            return (None, None, 'KEPT_displacement_conflict_power_and_family_confirm')
        pct = round(100.0 * abs(vcc - e['displacement_cc']) / e['displacement_cc'])
        d = (f"variant engine_type '{v['engine_type']}' -> {vcc} cc vs engine "
             f"{e['displacement_cc']} cc ({pct}% off)")
        if power_close:
            d += ("; NOTE: power matches within 15% - the ENGINE ROW's displacement may "
                  "be the wrong value (e.g. Range Rover TD6 <-> BMW M57); verify the "
                  "engine row before remapping")
        return ('DISPLACEMENT_MISMATCH', d, None)

    if power_diff is not None and power_diff > POWER_TOL:
        if disp is True:
            # same physical engine, different tune — legitimate (also cross-brand)
            return (None, None, 'KEPT_shared_engine_other_tune')
        if same_brand or same_family(v['car_brand'], e['brand_example']):
            # engine family with multiple tunes within one brand family
            return (None, None, 'KEPT_same_brand_power_spread')
        # R3 — cross-brand, power way off, displacement unverifiable
        return ('POWER_MISMATCH_CROSSBRAND',
                f"variant {v['engine_power_hp']} hp vs engine {e['power_hp']} hp "
                f"({int(round(power_diff * 100))}% off), brands {v['car_brand']} vs "
                f"{e['brand_example']}, displacement unverifiable", None)

    # no hard evidence of a wrong mapping
    if hard_pair_soft(v['fuel'], e['fuel']):
        return (None, None, 'KEPT_soft_fuel_label')
    return (None, None, 'clean')


def hard_pair_soft(f1, f2):
    a, b = norm_fuel(f1), norm_fuel(f2)
    return bool(a and b and a != b and frozenset((a, b)) in FUEL_SOFT_PAIRS)


# ---------------------------------------------------------------- main

def fetch_rows(cur):
    """Fetch joined rows with variant and engine fields kept in SEPARATE dicts."""
    cur.execute("""
        SELECT v.id, v.car_brand, v.car_model, v.car_year,
               v.fuel AS v_fuel, v.engine_power_hp AS v_power, v.engine_type, v.engine_code,
               e.power_hp AS e_power, e.displacement_cc AS e_disp,
               e.fuel AS e_fuel, e.brand_example, e.model_example
        FROM vehicle_variants v
        JOIN engines e ON e.engine_code = v.engine_code
    """)
    out = []
    for (vid, brand, model, year, v_fuel, v_power, v_etype, code,
         e_power, e_disp, e_fuel, e_brand, e_model) in cur.fetchall():
        out.append({
            'v': {'id': vid, 'car_brand': brand, 'car_model': model, 'car_year': year,
                  'fuel': v_fuel, 'engine_power_hp': v_power, 'engine_type': v_etype,
                  'engine_code': code},
            'e': {'power_hp': e_power, 'displacement_cc': e_disp, 'fuel': e_fuel,
                  'brand_example': e_brand, 'model_example': e_model},
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error('choose --dry-run or --apply')

    con = sqlite3.connect(DB)
    cur = con.cursor()

    already = cur.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='remapping_queue'").fetchone()[0]
    nulled = cur.execute(
        "SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NULL").fetchone()[0]
    if args.apply and already and nulled:
        sys.exit('Already applied: remapping_queue exists and variants are nulled. '
                 'Refusing to run twice (restore from backup first if needed).')

    rows = fetch_rows(cur)
    results = []
    for rec in rows:
        reason, detail, kept = classify(rec)
        results.append((rec, reason, detail, kept))

    quar = [(r, reason, detail) for (r, reason, detail, _k) in results if reason]
    worklist = [(r, kept) for (r, reason, _d, kept) in results
                if kept == 'KEPT_displacement_conflict_power_and_family_confirm']
    kept_cats = {}
    for (_r, _reason, _d, kept) in results:
        if kept:
            kept_cats[kept] = kept_cats.get(kept, 0) + 1
    clean = sum(1 for (_r, reason, _d, _k) in results if not reason and _k is None)

    print(f"Joined variant->engine rows evaluated : {len(rows):,}")
    print(f"  QUARANTINE                          : {len(quar):,}")
    by_reason = {}
    for (_r, reason, _d) in quar:
        by_reason[reason] = by_reason.get(reason, 0) + 1
    for k, v in sorted(by_reason.items(), key=lambda x: -x[1]):
        print(f"    {k:28s} {v:>6,}")
    print(f"  KEPT (deliberately preserved):")
    for k, v in sorted(kept_cats.items(), key=lambda x: -x[1]):
        print(f"    {k:28s} {v:>6,}")
    print(f"    {'clean (no finding)':28s} {clean:>6,}")
    print(f"\n  engine-row/etype fix worklist (kept, suspect data): {len(worklist):,} rows")
    wl_codes = {}
    for (r, _k) in worklist:
        wl_codes.setdefault(r['v']['engine_code'], 0)
        wl_codes[r['v']['engine_code']] += 1
    for c, n in sorted(wl_codes.items(), key=lambda x: -x[1])[:10]:
        print(f"    {c:15s} {n:>4} variants")

    print("\n--- sample quarantined rows ---")
    for (r, reason, detail) in quar[:12]:
        v = r['v']
        print(f"  [{reason}] {v['car_brand']} {v['car_model']} {v['car_year']} "
              f"{v['engine_power_hp']}hp '{v['engine_type']}' <- {v['engine_code']} "
              f"({r['e']['brand_example']} {r['e']['model_example']})")
        print(f"      {detail}")

    print("\n--- preserved cross-brand shares / tune families (must stay joined) ---")
    for code in ['CCZA', 'CAYC', 'G4GC', 'G6BA', 'D4FB', 'A13DTE', 'N47D20C', '4G63T', '2AZ-FXE']:
        cur.execute("""SELECT COUNT(*), COUNT(DISTINCT v.car_brand),
                       GROUP_CONCAT(DISTINCT v.car_brand)
                       FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code
                       WHERE v.engine_code=?""", (code,))
        n, nb, brands = cur.fetchone()
        print(f"  {code:10s} {n:>4} variants across {nb:>2} brands: {str(brands)[:80]}")

    if args.dry_run:
        print("\nDRY RUN — nothing changed.")
        return

    # ---------------- apply ----------------
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup = os.path.join(BACKUP_DIR, f'car_database_backup_pre_step1_{date.today().isoformat()}.db')
    shutil.copy2(DB, backup)
    print(f"\nBackup written: {backup}")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS remapping_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_variant_id INTEGER NOT NULL UNIQUE,
            car_brand TEXT NOT NULL, car_model TEXT NOT NULL, car_year INTEGER,
            variant_fuel TEXT, variant_power_hp INTEGER, variant_engine_type TEXT,
            variant_displacement_parsed_cc INTEGER,
            wrong_engine_code TEXT NOT NULL,
            wrong_engine_fuel TEXT, wrong_engine_power_hp INTEGER,
            wrong_engine_displacement_cc INTEGER,
            wrong_engine_brand_example TEXT, wrong_engine_model_example TEXT,
            reason TEXT NOT NULL, detail TEXT,
            status TEXT NOT NULL DEFAULT 'pending',  -- pending|remapped|verified|false_positive
            new_engine_code TEXT, note TEXT,
            quarantined_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    ins = """INSERT INTO remapping_queue
        (vehicle_variant_id, car_brand, car_model, car_year, variant_fuel,
         variant_power_hp, variant_engine_type, variant_displacement_parsed_cc,
         wrong_engine_code, wrong_engine_fuel, wrong_engine_power_hp,
         wrong_engine_displacement_cc, wrong_engine_brand_example,
         wrong_engine_model_example, reason, detail)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    upd = "UPDATE vehicle_variants SET engine_code=NULL WHERE id=?"
    for (r, reason, detail) in quar:
        v, e = r['v'], r['e']
        cur.execute(ins, (v['id'], v['car_brand'], v['car_model'], v['car_year'], v['fuel'],
                          v['engine_power_hp'], v['engine_type'], parse_disp_cc(v['engine_type']),
                          v['engine_code'], e['fuel'], e['power_hp'], e['displacement_cc'],
                          e['brand_example'], e['model_example'], reason, detail))
        cur.execute(upd, (v['id'],))

    # keep denormalised counts consistent
    cur.execute("""UPDATE engines SET count_variants =
                   (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")

    con.commit()

    # ---------------- verify ----------------
    print("\n=== VERIFICATION ===")
    print("integrity_check:", cur.execute("PRAGMA integrity_check").fetchone()[0])
    print("variants with NULL engine_code :", cur.execute(
        "SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NULL").fetchone()[0], "(expected", len(quar), ")")
    print("v_vehicle_with_service rows    :", cur.execute(
        "SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0], f"(was {len(rows):,})")
    print("remapping_queue rows           :", cur.execute(
        "SELECT COUNT(*) FROM remapping_queue").fetchone()[0])
    print("engines with count_variants=0  :", cur.execute(
        "SELECT COUNT(*) FROM engines WHERE count_variants=0").fetchone()[0])
    for label, mdl in [("Veyron (hernr_788)", "VEYRON%"), ("Maserati MC 12", "MC 12"),
                       ("Ferrari 599 GTB/GTO", "599 GTB%")]:
        r = cur.execute("""SELECT car_model, car_year, engine_code FROM vehicle_variants
                           WHERE car_model LIKE ?""", (mdl,)).fetchall()
        print(f"  spot-check {label}: {r}")
    for code in ['CCZA', 'G4GC', 'A13DTE', 'N47D20C', '2AZ-FXE']:
        cur.execute("""SELECT COUNT(*), COUNT(DISTINCT v.car_brand) FROM vehicle_variants v
                       JOIN engines e ON e.engine_code=v.engine_code WHERE v.engine_code=?""", (code,))
        n, nb = cur.fetchone()
        print(f"  preserved {code:9s}: {n} variants / {nb} brands still joined")

    # CSV export of the review queue
    os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
    with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['vehicle_variant_id', 'car_brand', 'car_model', 'car_year', 'variant_fuel',
                    'variant_power_hp', 'variant_engine_type', 'wrong_engine_code',
                    'wrong_engine_brand_example', 'wrong_engine_model_example', 'reason', 'detail'])
        for (r, reason, detail) in quar:
            v, e = r['v'], r['e']
            w.writerow([v['id'], v['car_brand'], v['car_model'], v['car_year'], v['fuel'],
                        v['engine_power_hp'], v['engine_type'], v['engine_code'],
                        e['brand_example'], e['model_example'], reason, detail])
    print(f"\nReview queue exported: {CSV_OUT}")

    # Worklist: kept rows where power+family confirm the mapping but the
    # displacement conflict means either the variant engine_type text or the
    # engine row's displacement is wrong -> fix data, do not remap.
    wl_out = os.path.join(ROOT, 'database_enriched', 'csv_exports', '09_engine_row_suspects.csv')
    with open(wl_out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['engine_code', 'engine_displacement_cc', 'engine_power_hp',
                    'engine_brand_example', 'engine_model_example',
                    'car_brand', 'car_model', 'car_year', 'variant_engine_type',
                    'parsed_displacement_cc', 'variant_power_hp'])
        for (r, _k) in worklist:
            v, e = r['v'], r['e']
            w.writerow([v['engine_code'], e['displacement_cc'], e['power_hp'],
                        e['brand_example'], e['model_example'],
                        v['car_brand'], v['car_model'], v['car_year'], v['engine_type'],
                        parse_disp_cc(v['engine_type']), v['engine_power_hp']])
    print(f"Engine-row suspect worklist exported: {wl_out}")
    print("Rollback: restore {0} , or run the surgical restore SQL in the step-1 report.".format(backup))
    con.close()


if __name__ == '__main__':
    main()
