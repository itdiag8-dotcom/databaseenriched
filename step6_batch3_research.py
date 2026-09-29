#!/usr/bin/env python3
"""
Step 6 — Batch 3: web-researched resolution of remaining fuel-conflict pendings
+ G6DA/G6DG engine-row disambiguation (Ford diesel vs Hyundai Lambda petrol).

Key facts (web-verified 2026-09-29, citations in REMAPPING_REVIEW_BATCH3.md):
  * Hyundai Lambda: G6DA = 3.8 MPi (3778cc, 263-310PS; Grandeur TG, Carnival VQ,
    Opirus/Amanti, Genesis Coupe pre-GDI); G6DG = 3.0 GDI (2999cc, 266-270PS;
    Grandeur HG, Cadenza/K7 VG); G6DH = 3.3 GDI (3342cc, 290-294PS) - the DB's
    G6DH row (3000cc/247hp 'Azera') was mislabeled.
  * G6DA/G6DG primary keys are occupied by Ford Duratorq 2.0 TDCi diesel rows,
    so Hyundai Lambda rows are created with ' (Hyundai)' suffix.
  * Alpina D3/D4/D5/XD3 350PS = BMW N57D30 biturbo (2993cc) tuned by Alpina.
  * Alpina B10 V8S = M62B48 4837cc 375hp (Alpina code F5).
  * Rolls-Royce Park Ward 5.4 = BMW M73B54 5379cc 326hp.
  * Maserati MC12 = Enzo-derived F140 V12, 632PS -> F140B row (Enzo, 650PS).

Usage: python3 step6_batch3_research.py --apply
"""
import csv, os, shutil, sqlite3, sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'database_enriched', 'car_database.db')
BACKUP_DIR = os.path.join(ROOT, 'database_enriched', 'backups')
CSV_OUT = os.path.join(ROOT, 'database_enriched', 'csv_exports', '14_remap_batch3_decisions.csv')

LAM = 'https://en.wikipedia.org/wiki/Hyundai_Lambda_engine + https://www.allcarpartsonline.com.au/kia-grand-carnival-engine-3.8-petrol-g6da-vq-01-06'
ALP = 'https://en.wikipedia.org/wiki/Alpina_B5_(F10) + https://www.automobile-catalog.com/car/2012/1762115/alpina_d5_biturbo.html'
B10 = 'https://www.bmwblog.com/2020/05/02/the-rare-bmw-alpina-roadster-v8-limited-edition/ + https://x.com/candvbmw/status/1981716043945930989'
RR  = 'https://www.carsart.net/en/cars/rolls-royce/silver-seraph/silver-seraph/5400cc-i-v12-326hp'
MC  = 'https://fastestlaps.com/models/maserati-mc12 (F140 Enzo chassis/engine)'

# --- new engine rows (code, type, fuel, cc, hp, cyl, brand, model, why) ---
NEW_ENGINES = [
 ('G6DA (Hyundai)', '3.8 V6 MPi Lambda', 'Petrol', 3778, 266, 6, 'Hyundai', 'Grandeur TG / Carnival VQ / Opirus / Genesis Coupe', LAM),
 ('G6DG (Hyundai)', '3.0 V6 GDI Lambda II', 'Petrol', 2999, 270, 6, 'Hyundai', 'Grandeur HG / Cadenza (VG)', LAM),
 ('M62B48', '4.8 V8 Alpina B10 V8S', 'Petrol', 4837, 375, 8, 'Alpina', 'B10 V8S (E39)', B10),
]
# M73B54 created only if absent (dynamic below)

ENGINE_FIXES = [
 ('G6DH', dict(displacement_cc=3342, power_hp=292, engine_type='3.3 V6 GDI Lambda II',
               model_example='Grandeur HG / Cadenza / Santa Fe (DM)'),
  f"G6DH is the 3.3 GDI Lambda II (3342cc, 290-294PS), was mislabeled 3000cc/247hp {LAM}"),
 ('N57D30B', dict(displacement_cc=2993),
  f"N57 3.0 diesel = 2993cc, was 4004cc (parse junk) {ALP}"),
]

REMAPS = [
 # Hyundai/Kia Lambda group
 (3987, 'G6DG (Hyundai)', f"Grandeur HG 3.0 GDI 266hp = G6DG 270PS {LAM}"),
 (23803, 'G6DG (Hyundai)', f"Cadenza VG 3.0 GDI 271hp = G6DG 270PS {LAM}"),
 (10107, 'G6DA (Hyundai)', f"Genesis Coupe 3.8 MPi 303hp = G6DA (306PS pre-GDI 2008-2010) {LAM}"),
 (11527, 'G6DA (Hyundai)', f"Grand Carnival VQ 3.8 petrol = G6DA (confirmed by parts listings) {LAM}"),
 (17617, 'G6DA (Hyundai)', f"Grandeur TG 3.8 265hp = G6DA (GRANDEUR 2006-2011 3.8 G6DA TG) {LAM}"),
 (18221, 'G6DA (Hyundai)', f"Opirus/Amanti GH 3.8 267hp = G6DA 267PS {LAM}"),
 (23805, 'G6DH',           f"Cadenza '3.5 (est.)' 290hp = 3.3 GDI G6DH 290-294PS (mislabeled displacement) {LAM}"),
 # Alpina D-family
 (25533, 'N57D30B', f"Alpina XD3 (F25) 350PS = Alpina-tuned N57D30 biturbo 2993cc {ALP}"),
 (25534, 'N57D30B', f"Alpina D3 (F30) 350PS = Alpina N57D30 biturbo {ALP}"),
 (25535, 'N57D30B', f"Alpina D3 Estate (F31) 350PS = Alpina N57D30 {ALP}"),
 (26212, 'N57D30B', f"Alpina D4 Coupe (F32) 350PS = Alpina N57D30 {ALP}"),
 (26213, 'N57D30B', f"Alpina D4 Convertible (F33) 350PS = Alpina N57D30 {ALP}"),
 (9979,  'N57D30B', f"Alpina D5 Touring (F11) 350PS = Alpina N57D30 {ALP}"),
 (10853, 'N57D30B', f"Alpina D5 (F10) 350PS = Alpina N57D30 {ALP}"),
 # Alpina B10 V8S / Rolls / Maserati
 (13615, 'M62B48', f"Alpina B10 V8S (E39) 375hp = M62B48 4837cc (Alpina code F5) {B10}"),
 (14420, 'M62B48', f"Alpina B10 V8S Estate 375hp = M62B48 {B10}"),
 (15158, 'F140B',  f"Maserati MC12 632PS = Enzo-derived F140 V12 (detuned); F140B = Enzo 650PS {MC}"),
 # BMW
 (23294, 'N53B30A', "E92 325i 211hp = N53B30A (exact power match in DB, 2996cc)"),
 (23304, 'N53B30A', "E92 325i 211hp = N53B30A"),
 (26802, 'N57D30A', "BMW 535d is by definition the N57 3.0d six; variant fuel label 'Petrol' was wrong -> Diesel (name-verified)"),
 (26857, 'N57D30A', "X5 with N57 = 30d/40d diesel; variant fuel label 'Petrol' was wrong -> Diesel (name-verified)"),
 (27968, 'N57D30T', "X5 2016 diesel = N57D30T family (row displacement 2613cc is parse junk, real 2993cc)"),
 # Jaguar / Land Rover
 (21303, '3.0 V6 D S', "Jaguar XF 3.0D S 275PS = Lion AJ-V6D; DB row '3.0 V6 D S' 271hp is the closest (description-code, flagged for code cleanup)"),
 (10410, 'AJ126', "Discovery IV 3.0 SC 340PS = AJ126 (335hp row, same brand Land Rover)"),
 (25160, 'AJ126', "Range Rover IV 3.0 SC 340PS = AJ126"),
 (24770, 'AJ126', "Range Rover Sport 3.0 SC 340PS = AJ126"),
 # Nissan / Honda / Mitsubishi / Daihatsu / Kia / Toyota
 (26571, 'VQ35DE', "Murano Z51 3.5 249hp = VQ35DE (sibling variants 249hp exact)"),
 (17750, 'J35A8',  "Lagreat (JDM Odyssey) 3.5 248hp = J35A8 (sibling 2004 248hp exact)"),
 (22305, '4G64(SOHC16V)', "L300 2.4 114hp = 4G64 SOHC (sibling 114hp exact; description-code, flagged)"),
 (19230, 'EF-VE',  "MOVE 0.7 58hp = EF-VE (sibling 58hp; engine row lists conservative 48hp)"),
 (17658, 'K3-VE',  "BE-GO 1.3 86hp = K3-VE (92hp row, Toyota/Daihatsu family)"),
 (14907, 'G4HG',   "Picanto 1.1 65hp = G4HG 66hp (Hyundai/Kia family)"),
 (20683, 'QG18DE', "Sentra 1.8 120hp = QG18DE 125hp (4%)"),
 (20679, 'QR25DE', "Sentra 2.5 175hp = QR25DE 171hp (Renault row = Nissan family)"),
 (25062, 'YD25DDTi', "Urvan NV350 2.5 dCi 129hp = YD25DDTi low tune (family 126-190PS; row is 188hp top tune)"),
 (18201, '1MZ-FE', "Camry Solara 3.0 186hp = 1MZ-FE (186-192hp depending on year)"),
 (22499, '3MZ-FE', "Kluger 2006 273hp = 3.3 Hybrid system power (3MZ-FE + e-motor, 268-272PS)"),
 (19576, 'Z22SE',  "Astra TwinTop 2.2 150hp = Z22SE 145hp (GM family, 3%)"),
 # Mercedes
 (13603, 'M271E18ML', "C200 Kompressor S203 163hp = M271E18ML 161hp (1.2%)"),
 (16923, 'M156.985',  "CLK 63 AMG 481hp = M156 family (CLK63 Black Series 481-507PS; row 487hp)"),
 (16924, 'M156.985',  "CLK 63 AMG Cabrio 481hp = M156.985"),
 (14342, 'M113E50',   "E 500 T 4-matic (211.283) 306hp = M113E50 302hp (pre-facelift W211 5.0 V8)"),
 (19621, 'OM611.981', "Sprinter Classic 109hp = OM611.981 (109hp exact)"),
 (19625, 'OM611.981', "Sprinter Classic 109hp = OM611.981"),
 # others
 (24265, 'F1CE3481L', "Iveco Daily IV 150hp = F1CE 3.0 146hp (2.7%)"),
 (23599, 'A13DTE',    "Chrysler/Lancia Ypsilon '1.2' diesel 95hp = 1.3 MultiJet A13DTE 94hp (displacement label wrong)"),
 (19438, 'CFGB',       "Octavia 2.0 TDI 170PS = CFGB (168hp row, VAG family)"),
 (23100, 'CMXA',       "Rapid Spaceback 1.2 TSI 105hp = CMXA 103hp (VAG family, 2%)"),
 (9821,  'EE20Z',      "Subaru XV 2.0D 109hp = EE20 boxer diesel, early EU tune 110PS (row is the 148PS 2011+ tune; same engine, service data identical)"),
 (19272, 'EE20Z',      "Subaru Impreza 2.0D 109hp = EE20 early EU tune (see XV)"),
 (25384, 'M73B54',     f"Rolls-Royce Park Ward 5.4 326hp = BMW M73B54 5379cc {RR}"),
]

# dynamic lookups: (vid, brand_list, fuel, cc_min, cc_max, hp_min, hp_max, note)
DYNAMIC = [
 (20761, ['Volkswagen','Audi','Seat','Skoda'], 'Diesel', 2900, 3050, 200, 220, "Touareg 7L 3.0 V6 TDI 211PS"),
 (14456, ['Volkswagen','Audi','Seat','Skoda'], 'Petrol', 1550, 1620, 110, 120, "Golf V 1.6 FSI 115hp (BAG/BLF/BLP family)"),
 (25164, ['Opel','Vauxhall','Chevrolet'], 'Petrol', 1580, 1620, 193, 205, "Zafira Tourer C 1.6 Turbo 200PS"),
 (20158, ['Volkswagen','Audi'], 'Petrol', 1750, 1800, 160, 180, "Passat 3B 1.8T 170hp"),
 (13102, ['Opel','Vauxhall'], 'Petrol', 1580, 1620, 80, 95, "Combo B 1.6 8v/16v 84-87hp"),
 (13422, ['Opel','Vauxhall'], 'Petrol', 1580, 1620, 80, 95, "Combo Mk II 1.6 87hp"),
 (20312, ['Opel','Vauxhall'], 'Petrol', 1580, 1620, 80, 95, "Combo Mk II 1.6 84hp"),
 (17837, ['Daewoo','Chevrolet'], 'Petrol', 1980, 2050, 138, 148, "Tosca 2.0 143hp"),
 (17869, ['Daewoo','Chevrolet'], 'Petrol', 2350, 2450, 133, 145, "Winstorm/Captiva 2.4 140hp"),
 (20196, ['Chrysler'], 'Petrol', 3400, 3650, 240, 265, "Pacifica CS 3.5/3.8"),
 (25180, ['Toyota'], 'Diesel', 2400, 3000, 100, 125, "Dyna 2001 diesel ~110hp (2KD/1KZ/5L family)"),
 (15148, ['Lamborghini'], 'Petrol', 5900, 6300, 550, 600, "Murcielago 6.2 V12 579hp"),
]

FUEL_FIXES = {  # vid -> fuel  (variant fuel label corrections alongside restore)
 26802: 'Diesel', 26857: 'Diesel',
}

PENDING_NOTES = {
 24741: "E81 '320 d (corr.)' 90hp: no BMW diesel makes 90hp - source power value corrupt; needs VIN",
 26636: "218d (F45) 95hp: 218d is 143hp - source power value corrupt ('Forward-/Backflow' junk etype)",
 17686: "Honda City '1.5 FF' 95hp: no matching Honda 1.5 (L15A is 90/120hp) - needs research",
 19160: "Diamante 2.5 205hp: 6A13 is 160-170hp, 6G74 3.5 is 214hp - neither fits 205hp; needs research",
 18188: "Tanto 64hp = 660 turbo KF-DET, not in DB (K3/KF-VE rows are NA) - needs new row",
 20036: "Morgan Aeromax 4.4 333hp: M62B44 is 282hp; Aero 8 4.4 rated 286-333 depending on source - needs research",
 17414: "hernr_1490 'SEVEN (CF)' 2.0 Turbo 204hp - brand identification needed (Step 3) before engine mapping",
 16239: "hernr_1516 TS 250 2.5 V6 180hp - brand identification needed (Step 3)",
 16240: "hernr_1516 TS 500 5.0 V8 320hp - brand identification needed (Step 3)",
 21361: "hernr_2903 TENGYI C50 1.5 126hp - brand identification needed (Step 3)",
 18714: "hernr_3514 CITY EV 41hp - EV, needs EV data model + brand fix",
 26147: "Berlingo Electric 67hp - EV, needs EV data model",
}

LEMON_NO_DATA = [26947, 28118, 33644, 27161, 28447, 34352, 31097, 31098]
# 26802/26857/27968 handled in REMAPS (name-verified restores)


def main():
    if '--apply' not in sys.argv:
        sys.exit('usage: step6_batch3_research.py --apply')
    con = sqlite3.connect(DB)
    cur = con.cursor()
    codes = {r[0] for r in cur.execute("SELECT engine_code FROM engines")}

    # sanity
    missing = [c for (_v, c, _n) in REMAPS if c not in codes and c not in
               {e[0] for e in NEW_ENGINES} | {'M73B54'}]
    if missing:
        # M73B54 may need creation
        if 'M73B54' in missing and 'M73B54' not in codes:
            NEW_ENGINES.append(('M73B54', '5.4 V12 24v', 'Petrol', 5379, 326, 12, 'Rolls-Royce',
                                'Silver Seraph / Park Ward', 'https://www.carsart.net/en/cars/rolls-royce/silver-seraph/silver-seraph/5400cc-i-v12-326hp'))
            missing.remove('M73B54')
        if missing:
            sys.exit(f"missing target codes: {missing}")

    backup = os.path.join(BACKUP_DIR, f'car_database_backup_pre_step6_{date.today().isoformat()}.db')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(DB, backup)
    print(f"Backup: {backup}")
    n0 = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NULL").fetchone()[0]
    s0 = cur.execute("SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0]

    # 1) new engine rows + empty spec rows
    for code, etype, fuel, cc, hp, cyl, brand, model, why in NEW_ENGINES:
        if code not in codes:
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                           cylinders, brand_example, model_example, data_confidence)
                           VALUES (?,?,?,?,?,?,?,?, 'ESTIMATE')""", (code, etype, fuel, cc, hp, cyl, brand, model))
            cur.execute("INSERT INTO engine_service_specs (engine_code) VALUES (?)", (code,))
            cur.execute("INSERT INTO engine_technical_specs (engine_code) VALUES (?)", (code,))
            print(f"  engine created: {code} ({etype})")

    # 2) engine-row fixes
    for code, fixes, why in ENGINE_FIXES:
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  engine fixed: {code} -> {fixes}")

    # 3) fixed remaps (+ fuel label fixes)
    for vid, code, note in REMAPS:
        cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=COALESCE(?, fuel) WHERE id=?",
                    (code, FUEL_FIXES.get(vid), vid))
        cur.execute("UPDATE remapping_queue SET status='remapped', new_engine_code=?, note=? WHERE vehicle_variant_id=?",
                    (code, note, vid))

    # 4) dynamic lookups
    for vid, brands, fuel, ccmin, ccmax, hpmin, hpmax, note in DYNAMIC:
        ph = ",".join("?" * len(brands))
        rows = cur.execute(f"""SELECT engine_code, power_hp, displacement_cc, brand_example FROM engines
                               WHERE fuel=? AND displacement_cc BETWEEN ? AND ? AND power_hp BETWEEN ? AND ?
                                 AND brand_example IN ({ph}) AND engine_code NOT LIKE 'LEMON_%'""",
                           (fuel, ccmin, ccmax, hpmin, hpmax, *brands)).fetchall()
        # prefer exact power match, then unique
        if len(rows) == 1:
            cur.execute("UPDATE vehicle_variants SET engine_code=? WHERE id=?", (rows[0][0], vid))
            cur.execute("UPDATE remapping_queue SET status='remapped', new_engine_code=?, note=? WHERE vehicle_variant_id=?",
                        (rows[0][0], f"{note} -> unique in-DB candidate {rows[0][0]} ({rows[0][1]}hp {rows[0][2]}cc, {rows[0][3]})", vid))
        else:
            cur.execute("UPDATE remapping_queue SET note=? WHERE vehicle_variant_id=?",
                        (f"{note}: {len(rows)} in-DB candidates {[r[0] for r in rows[:4]]} - needs disambiguation", vid))

    # 5) pendings with notes
    for vid, note in PENDING_NOTES.items():
        cur.execute("UPDATE remapping_queue SET note=? WHERE vehicle_variant_id=?", (note, vid))
    for vid in LEMON_NO_DATA:
        cur.execute("UPDATE remapping_queue SET note=? WHERE vehicle_variant_id=?",
                    ("LEMON source row without power/engine data (US truck, Duramax codes LML/LMM/LY on a petrol-labelled row) - verify VIN before mapping", vid))

    cur.execute("""UPDATE engines SET count_variants=(SELECT COUNT(*) FROM vehicle_variants v
                   WHERE v.engine_code=engines.engine_code)""")
    con.commit()

    print("\n=== VERIFICATION ===")
    print("integrity_check:", cur.execute("PRAGMA integrity_check").fetchone()[0])
    n1 = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NULL").fetchone()[0]
    s1 = cur.execute("SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0]
    print(f"variants NULL engine_code: {n0} -> {n1}")
    print(f"v_vehicle_with_service: {s0} -> {s1}")
    print("queue:", cur.execute("SELECT status, COUNT(*) FROM remapping_queue GROUP BY 1 ORDER BY 2 DESC").fetchall())
    bad = cur.execute("""SELECT COUNT(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code
        JOIN remapping_queue rq ON rq.vehicle_variant_id=v.id
        WHERE rq.status='remapped' AND e.fuel<>v.fuel AND v.fuel<>'Hybrid'""").fetchone()[0]
    print("remapped rows with hard fuel conflicts:", bad)
    badp = cur.execute("""SELECT v.id, v.car_model, v.engine_power_hp, e.power_hp FROM vehicle_variants v
        JOIN engines e ON e.engine_code=v.engine_code JOIN remapping_queue rq ON rq.vehicle_variant_id=v.id
        WHERE rq.status='remapped' AND rq.note LIKE '%Alpina%' OR rq.status='remapped' AND v.id IN (3987,23803,10107,11527,17617,18221,23805)""").fetchall()
    print("spot list:", badp)
    for r in cur.execute("""SELECT v.car_brand, v.car_model, v.car_year, v.fuel, v.engine_power_hp, v.engine_code,
                                   s.oil_viscosity, s.oil_capacity_with_filter_l
                            FROM vehicle_variants v JOIN engine_service_specs s ON s.engine_code=v.engine_code
                            WHERE v.id IN (3987, 10853, 13615, 25384, 15158, 10410, 13603)"""):
        print("  spot:", r)

    with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['vehicle_variant_id','car_brand','car_model','car_year','old_engine_code','new_engine_code','status','note'])
        for r in cur.execute("""SELECT vehicle_variant_id,car_brand,car_model,car_year,wrong_engine_code,
                                       new_engine_code,status,note FROM remapping_queue
                                WHERE status!='pending' OR note IS NOT NULL ORDER BY status,car_brand"""):
            w.writerow(r)
    print(f"\ndecisions: {CSV_OUT}\nrollback: cp '{backup}' '{DB}'")
    con.close()

if __name__ == '__main__':
    main()
