#!/usr/bin/env python3
"""
Step 4 (batch 1) — Review & remap the POWER_MISMATCH_CROSSBRAND quarantine rows
================================================================================
Web-verified engine codes (search -> cite -> replace), following the method of
MISSING_ENGINE_CODES_REPORT.md. Every remap carries its citation URL(s) into
remapping_queue.note.

Also in this batch (dependencies discovered during review):
  * re-quarantine 3 rows wrongly KEPT by the brand-family rule (Lexus GX,
    Chevrolet Cruze 2003, Chevrolet Equinox 2002 - Toyota/Subaru GT86-style
    platform partnership must not validate arbitrary code swaps)
  * fix engine rows with wrong identity data (1MZ-FE 429hp 'Jaguar supercharged'
    -> real 1MZ-FE; N52B30 1300cc -> 2996cc; N47D20/N47D20C 1482cc -> 1995cc;
    N63B44 547hp 'X5 M' -> 407hp)
  * create AJ126 (Jaguar 3.0 SC V6) + M47D20TU2 (BMW 320d) engine rows
  * move the 22 Jaguar F-Type/XF/XJ/F-Pace variants from 1MZ-FE to AJ126
  * move the X5 M (E70) 547hp variant from N63B44 to S63B44

Usage: python3 step4_remap_power_mismatch.py --apply   (no dry-run: mapping is
reviewed in the report first; backup taken automatically)
"""
import csv
import os
import shutil
import sqlite3
import sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'database_enriched', 'car_database.db')
BACKUP_DIR = os.path.join(ROOT, 'database_enriched', 'backups')
CSV_OUT = os.path.join(ROOT, 'database_enriched', 'csv_exports', '12_remap_batch1_decisions.csv')

# ---------------------------------------------------------------- citations
C = {
 's85':    "https://www.auto-data.net/en/bmw-m5-e60-5.0-v10-507hp-smg-9871",
 'm47n2':  "https://www.auto-abc.eu/BMW-3-serija/v2196-2005 + https://www.ultimatespecs.com/car-specs/BMW/51256/BMW-E90-3-Series-320d-Auto.html",
 'n53':    "https://www.auto-data.net/en/bmw-3-series-sedan-e90-330i-272hp-9934",
 'n63':    "https://www.auto-data.net/en/bmw-6-series-coupe-f13-650i-407hp-steptronic-17291",
 'giul':   "https://www.auto-data.net/en/alfa-romeo-giulietta-type-940-1.750-tb-235hp-16765",
 'f140':   "https://en.wikipedia.org/wiki/Ferrari_599",
 'vz':     "https://en.wikipedia.org/wiki/Holden_Commodore_(VZ)",
 'vy':     "https://en.wikipedia.org/wiki/Holden_Commodore_(VY)",
 'ls1':    "https://www.autoblog.com/features/gm-ls1-engine-specs-common-issues",
 'ls2':    "https://www.hsv.com.au/classics/see/vz/clubsport/",
 'boss':   "https://www.netcarshow.com/ford/2002-ba_falcon_xr8/ + https://grokipedia.com/page/Ford_Falcon_(BA)",
 '1mz':    "https://specsnode.com/engine-detail.php?id=37 + https://en.wikipedia.org/wiki/Toyota_MZ_engine",
 'aj126':  "https://enginefinders.co.uk/jaguar-aj126-petrol-engine + https://www.caranddriver.com/reviews/a15109109/2015-jaguar-xf-30-awd-test-review/",
 'm157':   "https://www.auto-data.net/en/mercedes-benz-s-class-w222-amg-s-63-585hp-speedshift-18886",
 'om648':  "https://www.classic.com/m/mercedes-benz/e/w211/sedan/e-320-cdi/",
 'cts':    "https://en.wikipedia.org/wiki/Cadillac_CTS",
 '6g74':   "https://en.mitsubishiclub.cz/engine_detail.php?id=52",
 '6g75':   "https://en.wikipedia.org/wiki/Mitsubishi_6G7_engine",
 'tsi':    "https://www.mytiguan.com/threads/volkswagen-2-0-tsi-tfsi-ea888-gen-1-2-3-engine-review.50534/ + https://www.auto-data.net/en/volkswagen-tiguan-i-2.0-tsi-200hp-4motion-8382",
 'mzkluger': "https://en.wikipedia.org/wiki/Toyota_Highlander + https://en.wikipedia.org/wiki/Toyota_MZ_engine",
 'n52':    "https://www.auto-data.net/en/bmw-3-series-sedan-e90-330i-258hp-9933",
 'n47ed':  "https://www.auto-data.net/en/bmw-3-series-sedan-f30-320d-163hp-efficientdynamics-edition-17213",
 'm54b25': "https://www.auto-data.net/en/bmw-5-series-e60-525i-192hp-9597",
 'gx':     "https://autopadre.com/horsepower-and-torque/lexus-gx-460",
 'cruze':  "https://en.wikipedia.org/wiki/Suzuki_Ignis",
 's63':    "https://www.auto-data.net/en/bmw-x5-m-e70-4.4-555hp-xdrive-steptronic-9771",
 '520i':   "https://www.auto-abc.eu/bmw-5-serija/v3208-2003",
}

# ------------------------------------------------- (variant_id, code, note)
REMAPS = [
 (19283, '940 A1.000', f"Giulietta QV 1750 TBi 235PS = 940A1000 {C['giul']}"),
 (15399, 'M47D20TU2',  f"E90 320d 163hp = M47D20TU2 {C['m47n2']}"),
 (23368, 'M47D20TU2',  f"E92 320d 163hp = M47D20TU2 {C['m47n2']}"),
 (21073, 'N53B30',     f"330i E90 LCI 272hp = N53B30A {C['n53']}"),
 (23355, 'N47D20C',    f"3 GT (F34) 320d ED 163hp = N47D20C {C['n47ed']}"),
 (23356, 'N47D20C',    f"3 GT (F34) 320d ED 163hp = N47D20C {C['n47ed']}"),
 (15765, 'N52B30',     f"330i E91 258hp = N52B30A {C['n52']}"),
 (15147, 'S85B50A',    f"M5 E60 507hp = S85B50A {C['s85']}"),
 (14598, 'M54B25',     f"525i E61 192hp = M54B25 {C['m54b25']}"),
 (25730, 'N63B44',     f"650i F13 407hp = N63B44A {C['n63']}"),
 (16660, 'F140C',      f"599 GTB Fiorano 620PS = F140C {C['f140']}"),
 (21329, 'F140C',      f"599 GTB Fiorano 612hp = F140C 620PS {C['f140']}"),
 (25992, 'F140C',      f"'599 SA' listed 620hp matches GTB F140C; SA Aperta is 661hp F140CE {C['f140']} - FLAGGED"),
 (25922, 'LS1',        f"Calais VZ 5.7 LS1 235kW=315hp {C['vz']}"),
 (21318, 'LS1',        f"Commodore Ute VU SS LS1 235kW {C['vy']}"),
 (21312, 'LS1',        f"Commodore Ute VY SS LS1 235kW=315hp {C['vy']}"),
 (21320, 'LS1',        f"Commodore Ute VY LS1 235kW {C['vy']}"),
 (21322, 'LS1',        f"Commodore Ute VY SII 245kW=329hp High Output LS1 {C['vy']}"),
 (21262, 'LS1',        f"Statesman WK LS1 5.7 {C['ls1']}"),
 (21264, 'LS1',        f"Statesman WL 354hp LS1 260kW {C['ls1']}"),
 (21324, 'LS2',        f"Commodore VE SS 6.0 LS2 270kW=362hp {C['vz']}"),
 (20972, 'LS1',        f"HSV Clubsport VX LS1 255kW {C['ls1']}"),
 (20974, 'LS1',        f"HSV Clubsport VY LS1 260kW {C['ls1']}"),
 (20976, 'LS1',        f"HSV Clubsport VY R8 LS1 C4B 285kW {C['ls1']}"),
 (20978, 'LS2',        f"HSV Clubsport VZ LS2 297kW=398hp {C['ls2']}"),
 (21352, 'LS1',        f"HSV Grange WH LS1 250kW {C['ls1']}"),
 (21353, 'LS1',        f"HSV Grange WK LS1 285kW {C['ls1']}"),
 (21355, 'LS2',        f"HSV Grange WL LS2 297kW {C['ls2']}"),
 (21251, 'BOSS260',    f"Falcon BA XR8 Boss 260 260kW=350hp {C['boss']}"),
 (21254, 'BOSS260',    f"Falcon BF XR8 Boss 260 {C['boss']}"),
 (21253, 'BOSS290',    f"Falcon BA (FPV/XR8 ute) Boss 290 290kW=389hp {C['boss']}"),
 (21255, 'BOSS290',    f"Falcon BF Boss 290 290kW=394hp {C['boss']}"),
 (14198, '3MZ-FE',     f"RX330 (MCU3_) 3.3 = 3MZ-FE {C['mzkluger']} (204hp vs 211 within tolerance)"),
 (19266, '3MZ-FE',     f"Harrier 2nd gen 3.3 = 3MZ-FE {C['mzkluger']}"),
 (19274, '1MZ-FE',     f"Kluger XU20 2001-2003 = 1MZ-FE (2004+ 3MZ-FE) {C['mzkluger']}"),
 (15618, 'OM648.961',  f"E320 CDI W211 (211.022) = OM648.961 204hp {C['om648']}; variant 224hp matches the later OM642 V6 (2005+) - verify VIN"),
 (11095, 'M157.985',   f"S63 AMG W222 585hp = M157.985 {C['m157']}"),
 (25586, 'M157.985',   f"S63 AMG Coupe C217 585hp = M157.985 {C['m157']}"),
 (24809, '6G75',       f"Pajero Sport 3.8 = 6G75 3828cc {C['6g75']} (220hp RU-market rating)"),
 (20467, '6G74',       f"Verada 3.5 V6 = 6G74 203-208PS {C['6g74']}"),
 (25363, '6G74',       f"Verada 3.5 V6 = 6G74 203-208PS {C['6g74']}"),
 (22542, 'CCZA',       f"Tiguan 2.0 TSI 200hp = CAWB/CCZA {C['tsi']}"),
]

PENDING = [
 (24981, f"520i E60: 2003-03/2005 = M54B22 170hp, later 2.0 = 150hp; listed 156hp matches neither {C['520i']} - verify engine plate/VIN"),
 (10908, f"CTS Sport Wagon introduced 2010 (US 2009 MY); 2007 CTS engines LY7 258hp / LLT 304hp; listed 276hp matches neither {C['cts']} - needs VIN"),
 (18988, f"Equinox introduced 2005; 2002 model-year invalid; closest LNJ 3.4 185hp (2005+) - needs verification"),
]
INVALID = [
 (14922, "NOVA 19hp with '650' engine_type is not a known production car (650cc/19hp microvehicle?) - source row corrupt"),
]

REQUARANTINE = [
 (10574, 'POWER_MISMATCH_CROSSBRAND', "296hp GX460 (URJ15_) on Subaru C16NZ2 99hp; wrongly kept by Toyota-Subaru family rule"),
 (17713, 'POWER_MISMATCH_CROSSBRAND', "Chevrolet Cruze (Japan, Suzuki Ignis-based) 99hp on Cadillac E18NVR 276hp; wrongly kept by GM family rule"),
 (18988, 'POWER_MISMATCH_CROSSBRAND', "Equinox 2002 188hp on Cadillac E18NVR 276hp; wrongly kept by GM family rule; model-year invalid"),
]

# then remapped immediately:
REQUARANTINE_REMAP = [
 (10574, '1UR-FE', f"GX460 (URJ150) 4.6 V8 = 1UR-FE 301hp {C['gx']}; note: GX460 launched 2010, listed year 2008 is off"),
 (17713, 'M15A',   f"Chevrolet Cruze (Japan) = Suzuki Ignis 1.5 M15A 99PS {C['cruze']}"),
]

ENGINE_FIXES = [
 ('1MZ-FE', dict(displacement_cc=2995, power_hp=201, engine_type='3.0 V6 24v DOHC VVT-i',
                 brand_example='Toyota', model_example='Camry / ES300 / RX300',
                 _why=f"was '3.0 V6 Supercharged' 429hp Jaguar C-X16 (AJ126 data merged in); real 1MZ-FE 2995cc 190-210hp {C['1mz']}")),
 ('N52B30', dict(displacement_cc=2996, power_hp=258, model_example='330i (E90)',
                 _why=f"displacement was 1300 (parse junk); real 2996cc, 330i 258hp {C['n52']}")),
 ('N47D20', dict(displacement_cc=1995, _why=f"displacement was 1482; N47 2.0 diesel = 1995cc {C['n47ed']}")),
 ('N47D20C', dict(displacement_cc=1995, _why=f"displacement was 1482; N47 2.0 diesel = 1995cc {C['n47ed']}")),
 ('N63B44', dict(power_hp=407, engine_type='4.4 V8 TwinTurbo', brand_example='Bmw',
                 model_example='650i (F13) / X5 xDrive50i',
                 _why=f"was 547hp 'X5 M' (that is S63B44); N63B44 = 407hp {C['n63']}")),
]

NEW_ENGINES = [
 ('AJ126', '3.0 V6 24v Supercharged', 'Petrol', 2995, 340, 6, 'Jaguar', 'F-Type / XF / XJ',
  f"Jaguar AJ126 3.0 SC V6 340-380PS {C['aj126']}"),
 ('M47D20TU2', '2.0 16v R4 diesel', 'Diesel', 1995, 163, 4, 'Bmw', '320d (E90/E92)',
  f"BMW M47N2 / M47D20TU2 163hp {C['m47n2']}"),
]

EXTRA_REMAPS = [
 # (selector_sql_params, new_code, note)  — engine identity fixes outside the queue
 ("SELECT id FROM vehicle_variants WHERE engine_code='1MZ-FE' AND car_brand='Jaguar'", 'AJ126',
  f"Jaguar 3.0 SC V6 = AJ126, not Toyota 1MZ-FE {C['aj126']}"),
 ("SELECT id FROM vehicle_variants WHERE engine_code='N63B44' AND engine_power_hp=547", 'S63B44',
  f"X5 M (E70) 555hp = S63B44A {C['s63']}"),
]


def main():
    if '--apply' not in sys.argv:
        sys.exit('usage: step4_remap_power_mismatch.py --apply')

    con = sqlite3.connect(DB)
    cur = con.cursor()

    # sanity: all target engine codes exist
    codes = {r[0] for r in cur.execute("SELECT engine_code FROM engines")}
    missing = [c for (_v, c, _n) in REMAPS + REQUARANTINE_REMAP if c not in codes]
    if missing:
        sys.exit(f"target engine codes missing from engines table: {missing}")

    n_before = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NULL").fetchone()[0]
    q_before = cur.execute("SELECT COUNT(*) FROM remapping_queue").fetchone()[0]
    specs_before = cur.execute("SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0]

    backup = os.path.join(BACKUP_DIR, f'car_database_backup_pre_step4_{date.today().isoformat()}.db')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(DB, backup)
    print(f"Backup: {backup}")

    # 1) re-quarantine wrongly-kept rows
    for vid, reason, detail in REQUARANTINE:
        cur.execute("""INSERT INTO remapping_queue
            (vehicle_variant_id, car_brand, car_model, car_year, variant_fuel, variant_power_hp,
             variant_engine_type, wrong_engine_code, wrong_engine_fuel, wrong_engine_power_hp,
             wrong_engine_displacement_cc, wrong_engine_brand_example, wrong_engine_model_example,
             reason, detail, status)
            SELECT v.id, v.car_brand, v.car_model, v.car_year, v.fuel, v.engine_power_hp,
                   v.engine_type, v.engine_code, e.fuel, e.power_hp, e.displacement_cc,
                   e.brand_example, e.model_example, ?, ?, 'pending'
            FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.id=?""",
            (reason, detail, vid))
        cur.execute("UPDATE vehicle_variants SET engine_code=NULL WHERE id=?", (vid,))

    # 2) engine-row identity fixes
    for code, fixes in ENGINE_FIXES:
        why = fixes.pop('_why')
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  engine fixed: {code} -> {fixes}  [{why[:60]}...]")

    # 3) new engine rows (+ empty spec rows so the views keep joining)
    for code, etype, fuel, disp, hp, cyl, bex, mex, why in NEW_ENGINES:
        if code not in codes:
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc,
                           power_hp, cylinders, brand_example, model_example, data_confidence)
                           VALUES (?,?,?,?,?,?,?,?, 'ESTIMATE')""",
                        (code, etype, fuel, disp, hp, cyl, bex, mex))
            cur.execute("INSERT INTO engine_service_specs (engine_code) VALUES (?)", (code,))
            cur.execute("INSERT INTO engine_technical_specs (engine_code) VALUES (?)", (code,))
            print(f"  engine created: {code} ({etype})  [{why[:60]}...]")

    # 4) extra identity remaps (Jaguar->AJ126, X5 M->S63B44)
    extra_done = 0
    for sql, new_code, note in EXTRA_REMAPS:
        ids = [r[0] for r in cur.execute(sql)]
        for vid in ids:
            cur.execute("UPDATE vehicle_variants SET engine_code=? WHERE id=?", (new_code, vid))
            extra_done += 1
        print(f"  extra remap: {len(ids)} variants -> {new_code}  ({note[:60]}...)")

    # 5) the queue remaps
    for vid, code, note in REMAPS:
        cur.execute("UPDATE vehicle_variants SET engine_code=? WHERE id=?", (code, vid))
        cur.execute("""UPDATE remapping_queue SET status='remapped', new_engine_code=?, note=?,
                       wrong_engine_code=COALESCE(NULLIF(wrong_engine_code,''), 'kept_'||?) WHERE vehicle_variant_id=?""",
                    (code, note, 'see_detail', vid))

    for vid, code, note in REQUARANTINE_REMAP:
        cur.execute("UPDATE vehicle_variants SET engine_code=? WHERE id=?", (code, vid))
        cur.execute("UPDATE remapping_queue SET status='remapped', new_engine_code=?, note=? WHERE vehicle_variant_id=?",
                    (code, note, vid))

    for vid, note in PENDING:
        cur.execute("UPDATE remapping_queue SET status='pending', note=? WHERE vehicle_variant_id=?", (note, vid))
    for vid, note in INVALID:
        cur.execute("UPDATE remapping_queue SET status='invalid_data', note=? WHERE vehicle_variant_id=?", (note, vid))

    # 6) recompute counts
    cur.execute("""UPDATE engines SET count_variants =
                   (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""")
    con.commit()

    # 7) verify
    print("\n=== VERIFICATION ===")
    print("integrity_check :", cur.execute("PRAGMA integrity_check").fetchone()[0])
    n_after = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NULL").fetchone()[0]
    print(f"variants NULL engine_code: {n_before} -> {n_after}")
    print(f"queue rows: {q_before} -> {cur.execute('SELECT COUNT(*) FROM remapping_queue').fetchone()[0]}")
    print("queue status:", cur.execute("SELECT status, COUNT(*) FROM remapping_queue GROUP BY 1 ORDER BY 2 DESC").fetchall())
    print(f"v_vehicle_with_service: {specs_before} -> {cur.execute('SELECT COUNT(*) FROM v_vehicle_with_service').fetchone()[0]}")
    print(f"extra identity remaps: {extra_done}")

    print("\nremapped rows now joined & power-consistent check (>30% off = problem):")
    bad = cur.execute("""
        SELECT v.id, v.car_brand, v.car_model, v.engine_power_hp, e.power_hp, v.engine_code
        FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.id IN (%s) AND v.engine_power_hp IS NOT NULL AND e.power_hp IS NOT NULL
          AND ABS(v.engine_power_hp-e.power_hp)*1.0/e.power_hp > 0.30"""
        % ",".join(str(v) for v, _c, _n in REMAPS + REQUARANTINE_REMAP)).fetchall()
    if bad:
        for b in bad: print("  STILL OFF:", b)
    else:
        print("  all remapped rows within 30% of their engine's power ✔")

    for spot in ["SELECT engine_code, count_variants FROM engines WHERE engine_code IN ('AJ126','M47D20TU2','LS1','LS2','1MZ-FE','S63B44','N63B44','F140C','1UR-FE','M15A','CCZA')"]:
        print("\nspot counts:", cur.execute(spot).fetchall())

    # export decisions
    os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
    with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['vehicle_variant_id', 'car_brand', 'car_model', 'car_year', 'variant_power_hp',
                    'old_engine_code', 'new_engine_code', 'status', 'note'])
        for row in cur.execute("""SELECT vehicle_variant_id, car_brand, car_model, car_year,
                                  variant_power_hp, wrong_engine_code, new_engine_code, status, note
                                  FROM remapping_queue
                                  WHERE status IN ('remapped','invalid_data') OR note IS NOT NULL
                                  ORDER BY status, car_brand"""):
            w.writerow(row)
    print(f"\nDecisions exported: {CSV_OUT}")
    print(f"Rollback: cp '{backup}' '{DB}'")
    con.close()


if __name__ == '__main__':
    main()
