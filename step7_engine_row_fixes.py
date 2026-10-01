#!/usr/bin/env python3
"""
Step 7 — Engine-row suspect worklist (452 rows / 200 codes).

Two root causes found:
  A) ENGINE ROW WRONG (displacement and/or identity text): fixed here with citations.
     QR25DE 1600->2488cc, M57D30 2353->2993, CMXA 1200->1598 (VW 1.6 MultiFuel!),
     B38B15M0 1005->1499, ETJ/ETH/ETC Cummins texts+cc, CCRA 1.0->1.6 TotalFlex,
     E18NVR (Cadillac CTS 3.0 LF1-type row) junk text 'ECONOVAN Bus' fixed +
     non-Cadillac junk attachments re-quarantined.
  B) VARIANT ETYPE JUNK (117 variants, e.g. '1.3 VVTi' on a 6.0 V8 truck,
     '3.8 Carrera' on an Opel): engine rows are RIGHT; the variant engine_type
     text is a Vivid artifact. No DB change (cosmetic backlog, reported).

Usage: python3 step7_engine_row_fixes.py --apply
"""
import csv, os, re, shutil, sqlite3, sys, unicodedata
from collections import Counter, defaultdict
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'database_enriched', 'car_database.db')
BACKUP_DIR = os.path.join(ROOT, 'database_enriched', 'backups')
CSV_OUT = os.path.join(ROOT, 'database_enriched', 'csv_exports', '15_engine_row_fixes.csv')

CIT = {
 'QR25DE': 'https://www.engine-specs.net/nissan/qr25de.html (2488cc)',
 'M57D30': 'https://specsnode.com/engine-detail.php?id=177 (M57 2993cc)',
 'CMXA': 'https://www.proxyparts.com/car-parts-stock/information/engine-code/cmxa/part/engine/partid/11428466/ (1598cc 75kW) + https://www.mecatechnic.com/en-GB/b-volkswagen/m-golf-6/motorizations (1.6 BSE/BSF/CCSA/CHGA/CMXA 102hp)',
 'L96': 'https://www.dieselhub.com/gas/gm-6.0-vortec-l96.html (6.0 V8 360hp)',
 'E18NVR': 'https://www.caranddriver.com/cadillac/cts/specs/2010/cadillac_cts_cadillac-cts-sedan_2010 (CTS 3.0 = LF1 270hp) + https://reman-engine.com/remanufactured-engines/cadillac/cts/2010/3.0l-vin-g-8th-digit-opt-lf1-awd',
 'CUMMINS': 'ETJ 6.7 Cummins 6690cc 350hp / ETH-ETC 5.9 Cummins (ETH high-output 325hp, ETC standard 235hp) - RAM 2500 factory packages',
 'B38': 'BMW B38 1.5 3-cyl Turbo = 1499cc (well-established OEM data)',
 'FOX': 'https://en.wikipedia.org/wiki/Volkswagen_Fox (1.6 8v TotalFlex 98-103PS)',
}

# code -> (displacement or None, engine_type or None, why)
FIXES = [
 ('QR25DE', 2488, '2.5 16v DOHC', f"was 1600cc/1.6 16v - QR25DE is Nissan 2.5 2488cc {CIT['QR25DE']}"),
 ('M57D30', 2993, None, f"was 2353cc - M57 3.0d = 2993cc {CIT['M57D30']}"),
 ('CMXA', 1598, '1.6 8v MultiFuel', f"was 1200cc/1.2 8v TSI - CMXA = VW Golf 1.6 MultiFuel 1598cc 102hp {CIT['CMXA']}"),
 ('B38B15M0', 1499, '1.5 Turbo 3-cyl', f"was 1005cc - B38 1.5 = 1499cc {CIT['B38']}"),
 ('E18NVR', None, '3.0 V6 SIDI VVT', f"engine_type was junk 'ECONOVAN Bus'; row data (2997cc/276hp/Cadillac CTS) = LF1-type 3.0 V6 {CIT['E18NVR']}"),
 ('ETJ', 6690, '6.7 I6 Cummins Turbo Diesel', f"was '3.6 FSI 4motion' 6691cc - RAM 2500 349-350hp = 6.7 Cummins {CIT['CUMMINS']}"),
 ('ETH', 5923, '5.9 I6 Cummins HO Turbo Diesel', f"was '2.5 TDiC AWD' 5883cc - 5.9 Cummins = 5923cc (360 cid) {CIT['CUMMINS']}"),
 ('ETC', 5923, '5.9 I6 Cummins 24V Turbo Diesel', f"was '2.2 Vtec (corr.)' 5886cc - 5.9 Cummins = 5923cc {CIT['CUMMINS']}"),
 ('CCRA', 1598, '1.6 8v TotalFlex', f"was 1000cc/1.0 with 99hp (internally inconsistent); VW Fox 1.6 TotalFlex = 98-103PS {CIT['FOX']}"),
 ('L96', None, '6.0 V8 Vortec', f"engine_type was junk '1.3 VVTi'; L96 = 6.0 Vortec V8 360hp, 5967cc correct {CIT['L96']}"),
 ('LC9', None, '5.3 V8 Vortec FlexFuel', "engine_type was junk '2.2 S2 (corr.)'; LC9 = 5.3 Vortec FlexFuel 5328cc correct"),
 ('L76', None, '6.0 V8 Vortec MAX', "engine_type was junk '6 (est.)'"),
 ('L20', None, '4.8 V8 Vortec', "engine_type was junk '1.0 DVVT'"),
 ('LM7', None, '5.3 V8 Vortec', "engine_type was '5.3' (kept), displacement 5327cc correct"),
 ('CKMA', None, '1.4 TSI Twincharger', "engine_type was junk '6.7 Turbo R'; CKMA = 1.4 TSI 160hp 1390cc correct"),
 ('F1CE0481HA', None, '3.0 HPI TurboDiesel', "engine_type was junk '1.6 e (EA0F)'; F1CE = Iveco 3.0 2998cc"),
 ('F1CE0481FA', None, '3.0 HPI TurboDiesel', "engine_type was junk '1.6 e (corr.)'"),
 ('F1CE0481B', None, '3.0 HPI TurboDiesel', "engine_type was junk '1.6 e (corr.)'"),
 ('4HH(P22DTE)', None, '2.2 16v HDi TurboDiesel', "engine_type was junk '1.0 1020'; 4HH/P22DTE = 2.2 HDi 2198cc"),
]


def parse_disp(s):
    if not s: return None
    m = re.search(r'(?<![A-Za-z0-9.])(\d\.\d)(?![\d.])', s)
    if m: return int(round(float(m.group(1)) * 1000))
    return None


def main():
    if '--apply' not in sys.argv:
        sys.exit('usage: step7_engine_row_fixes.py --apply')
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # --- pre-state
    def suspect_count():
        n = 0
        for (vetype, edisp, vhp, ehp, ebrand, vbrand) in cur.execute("""
                SELECT v.engine_type, e.displacement_cc, v.engine_power_hp, e.power_hp, e.brand_example, v.car_brand
                FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code"""):
            if edisp is None or edisp <= 0 or vhp is None or ehp is None: continue
            vd = parse_disp(vetype)
            if vd is None: continue
            if abs(vd - edisp) / edisp <= 0.25: continue
            if abs(vhp - ehp) > 0.15 * max(vhp, ehp): continue
            n += 1
        return n
    n0 = suspect_count()

    backup = os.path.join(BACKUP_DIR, f'car_database_backup_pre_step7_{date.today().isoformat()}.db')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(DB, backup)
    print(f"Backup: {backup}")

    # --- 1) engine row fixes
    for code, disp, etype, why in FIXES:
        before = cur.execute("SELECT displacement_cc, engine_type FROM engines WHERE engine_code=?", (code,)).fetchone()
        if disp is not None:
            cur.execute("UPDATE engines SET displacement_cc=? WHERE engine_code=?", (disp, code))
        if etype is not None:
            cur.execute("UPDATE engines SET engine_type=? WHERE engine_code=?", (etype, code))
        after = cur.execute("SELECT displacement_cc, engine_type FROM engines WHERE engine_code=?", (code,)).fetchone()
        print(f"  {code:14s} {before} -> {after}")

    # --- 2) E18NVR: quarantine non-Cadillac junk attachments
    junk = cur.execute("""SELECT v.id, v.car_brand, v.car_model, v.engine_power_hp FROM vehicle_variants v
                          WHERE v.engine_code='E18NVR' AND v.car_brand <> 'Cadillac'""").fetchall()
    print(f"\nE18NVR non-Cadillac attachments to quarantine: {len(junk)}")
    for (vid, b, m, hp) in junk:
        print(f"    #{vid} {b} {m} {hp}hp")
        cur.execute("""INSERT INTO remapping_queue
            (vehicle_variant_id, car_brand, car_model, car_year, variant_fuel, variant_power_hp,
             variant_engine_type, wrong_engine_code, wrong_engine_fuel, wrong_engine_power_hp,
             wrong_engine_displacement_cc, wrong_engine_brand_example, wrong_engine_model_example,
             reason, detail, status)
            SELECT v.id, v.car_brand, v.car_model, v.car_year, v.fuel, v.engine_power_hp, v.engine_type,
                   v.engine_code, e.fuel, e.power_hp, e.displacement_cc, e.brand_example, e.model_example,
                   'WRONG_ATTACHMENT', ?, 'pending'
            FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.id=?""",
            (f"E18NVR row is Cadillac CTS 3.0 (LF1-type) data; {b} {m} does not use this engine - "
             f"survived earlier filters via junk engine_type parse", vid))
        cur.execute("UPDATE vehicle_variants SET engine_code=NULL WHERE id=?", (vid,))

    cur.execute("""UPDATE engines SET count_variants=(SELECT COUNT(*) FROM vehicle_variants v
                   WHERE v.engine_code=engines.engine_code)""")
    con.commit()

    # --- 3) verify
    print("\n=== VERIFICATION ===")
    print("integrity_check:", cur.execute("PRAGMA integrity_check").fetchone()[0])
    n1 = suspect_count()
    print(f"displacement-suspect joined rows: {n0} -> {n1} (remaining are mostly variant-etype junk, cosmetic)")
    print("spot checks:")
    for c in ['QR25DE', 'CMXA', 'M57D30', 'L96', 'ETJ', 'E18NVR']:
        print("  ", cur.execute("SELECT engine_code, engine_type, displacement_cc, power_hp FROM engines WHERE engine_code=?", (c,)).fetchone())
    for r in cur.execute("""SELECT car_brand, car_model, engine_power_hp, engine_code FROM vehicle_variants
                            WHERE car_model LIKE '%Koleos%' OR (car_model LIKE '%ALTEA%' AND engine_code='CMXA') LIMIT 4"""):
        print("  variant:", r)
    print("queue:", cur.execute("SELECT status, COUNT(*) FROM remapping_queue GROUP BY 1 ORDER BY 2 DESC").fetchall())
    print("NULL engine_code:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NULL").fetchone()[0])
    print("v_vehicle_with_service:", cur.execute("SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0])

    with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['engine_code', 'new_displacement_cc', 'new_engine_type', 'why', 'citation_note'])
        for code, disp, etype, why in FIXES:
            w.writerow([code, disp, etype, why, ''])
        for (vid, b, m, hp) in junk:
            w.writerow([f'variant#{vid}', '', '', f'E18NVR wrong attachment quarantined', f'{b} {m} {hp}hp'])
    print(f"\nfix log: {CSV_OUT}\nrollback: cp '{backup}' '{DB}'")
    con.close()

if __name__ == '__main__':
    main()
