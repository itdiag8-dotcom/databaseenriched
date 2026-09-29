#!/usr/bin/env python3
"""
Step 8 — STEP 3: hernr_* brand rebadging + mis-brand fixes.

Resolves all 83 `hernr_NNN` brand buckets (Vivid WorkshopData Hersteller-Nummern
whose names were lost at source) to their real manufacturers, plus other
mis-brand issues found along the way:

  - 'Citroën' (486v) vs 'Citroen' (225v) split -> merged to 'Citroen'
  - 'Saic Mg' -> 'MG';  'SATURN' -> 'Saturn';  'SHELBY' -> 'Shelby'
  - 'Jmc' -> 'JMC';  'Volga' -> 'GAZ' (GAZ Siber)
  - hernr_2903 -> 'GWM' (consolidates with existing GWM variants)

Every hernr mapping is evidence-based (model + engine-code matches, web-verified;
see STEP3_BRAND_REBADGE_REPORT.md for citations).

Usage: python3 step8_step3_brand_rebadge.py --apply
"""
import csv, os, shutil, sqlite3, sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'database_enriched', 'car_database.db')
BACKUP_DIR = os.path.join(ROOT, 'database_enriched', 'backups')
CSV_OUT = os.path.join(ROOT, 'database_enriched', 'csv_exports', '16_brand_rebadge_decisions.csv')

# hernr_NNN -> (real brand, evidence)
HERNR_MAP = {
 '124':  ('Zastava', 'Koral = TU1JP/128A.064 (kmotorshop ZASTAVA KORAL 1.1); "10 (188)" = Zastava 10 (Fiat Punto 188 clone)'),
 '171':  ('Santana', 'PS10/ANIBAL = Santana Anibal w/ Iveco 8140.43; 300/350 = Santana 350 w/ DV6ATED4'),
 '178':  ('Tata', 'INDICA/INDIGO/SAFARI/XENON/ARIA are Tata models'),
 '181':  ('Piaggio', 'PORTER/APE/QUARGO/M500 = Piaggio commercial vehicles'),
 '609':  ('AC', 'COBRA Mk IV (291N) 2008 LS3/LS9 = AC Cars'),
 '694':  ('Renault Trucks', 'MASCOTT = Renault Trucks Mascott'),
 '701':  ('Lamborghini', 'GALLARDO/MURCIÉLAGO/AVENTADOR'),
 '705':  ('Rolls-Royce', 'PHANTOM/GHOST/WRAITH/PARK WARD/CORNICHE'),
 '774':  ('Pontiac', 'SOLSTICE = Pontiac Solstice'),
 '775':  ('Daewoo', 'LANOS Hatchback/Saloon = Daewoo Lanos'),
 '788':  ('Bugatti', 'VEYRON EB 16.4'),
 '802':  ('Lotus', 'ELISE/EXIGE/EVORA/EUROPA/2-ELEVEN'),
 '803':  ('Morgan', 'AERO 8/PLUS FOUR/ROADSTER'),
 '815':  ('Bentley', 'CONTINENTAL/ARNAGE/MULSANNE/AZURE'),
 '907':  ('Westfield', 'SEVEN with Ford FYDA/Vauxhall Z16LER engines + XTR with Audi TT 1.8T AMU 224hp = Westfield XTR4 (diseno-art.com, wikipedia Westfield XTR2)'),
 '1138': ('Smart', 'FORTWO/FORFOUR/CABRIO 450/CROSSBLADE'),
 '1139': ('ZAZ', 'SLAVUTA/FORZA/VIDA/LANOS PICK-UP = ZAZ (Zaporozhia)'),
 '1280': ('Mahindra', 'BOLERO/SCORPIO/MAXX/QUADRO'),
 '1480': ('Aixam', 'A.751 0.5D 14hp Z482 = Aixam A.751 quadricycle (smallcarsclub.com)'),
 '1490': ('Caterham', 'SEVEN (CF) 2.0T 204hp - (CF) is Caterham chassis code in TecDoc catalogs (autodoc.co.uk "Caterham Seven (CF)")'),
 '1505': ('Acura', 'MDX/TL/RL/RSX/CL/RDX'),
 '1506': ('Hummer', 'HUMMER H2/H3'),
 '1513': ('Ligier', 'BE UP + NOVA with Lombardini LDW502 = Ligier microcars (Wikipedia Ligier)'),
 '1516': ('Marcos', 'TS250 2.5 V6 180hp + TS500 5.0 V8 320hp = Marcos TS250/TS500 (carthrottle.com)'),
 '1518': ('McLaren', 'MP4/650S'),
 '1520': ('Metrocab', 'TAXI 2.4TD 2L-T 90hp 2001 = MCW Metrocab TTT (Wikipedia MCW Metrocab: Toyota 2L-T 2446cc 90PS)'),
 '1526': ('Infiniti', 'G/M/EX/FX/QX'),
 '1533': ('Perodua', 'KANCIL/KELISA/MYVI/VIVA/AXIA/ALZA/KENARI'),
 '1553': ('UAZ', 'HUNTER (3151)/PATRIOT/PICKUP (2360)/2206'),
 '1556': ('Venturi', 'FETISH/ASTROLAB/AMERICA'),
 '1558': ('Wiesmann', 'GT MF3/MF4/MF5 Roadsters/Coupes'),
 '2164': ('Maybach', 'MAYBACH (240_) 57/62'),
 '2242': ('LDV', 'FORA 2.5D VM40C 120hp = Fargo Fora, the Turkish-market LDV Maxus (Wikipedia LDV Maxus)'),
 '2589': ('Landwind', 'LANDWIND SUV = Jiangling Landwind'),
 '2590': ('Geely', 'BL/CK/HQ/MR/PU/MK/PANDA/VISION/URBAN NANNY = Geely; HISOON/MARINDO = Shanghai Maple (Geely sub-brand) (automobile.fandom.com Geely)'),
 '2755': ('Spyker', 'C8/C12'),
 '2760': ('KTM', 'X-BOW'),
 '2852': ('Chana', 'CV6 = Chana Era CV6/Benni 1.3 86hp JL474Q2 + STAR pickup (auta5p.eu, enginedesk.net)'),
 '2855': ('Soueast', 'DELICIA Bus 2.0 4G63S4M/4G64/EQ491i = Soueast Delica (ebay part listing "DONGNAN SOUEAST DELICIA BUS 4G63-S4M, 4G64-S4M, EQ491i")'),
 '2857': ('Eunos', '800 Saloon (E65, TA) 2.5 V6 2497cc 163hp = EUNOS 800 (JDM Mazda Xedos 9) - exact TecDoc listing (kmotorshop.com)'),
 '2863': ('Dongfeng Fengxing', 'FUTURE MPV 4G63/4G64/EQ491i 2001 = Dongfeng Fengxing Lingzhi, "also known as Future" (Wikipedia Dongfeng Liuzhou Motor)'),
 '2864': ('Ford', 'FALCON/EVEREST/LASER/LYNX/I-MAX = Ford AU/TW models'),
 '2866': ('Hafei', 'SAIBAO 3 Saloon = Hafei Saibao'),
 '2867': ('Foton', 'ALPHA/AUMARK/FORLAND/SEA LION/T-SERIE/SUP = Foton commercial'),
 '2887': ('Chery', 'A1/A3/A5/TIGGO/E5/EASTAR/CRISTAL/FORWIN = Chery'),
 '2888': ('Jinbei', 'HAISE VI Bus = Jinbei Haise VI (Hiace clone)'),
 '2901': ('Dadi', 'CITY COURSER/ELEGANTEST/PICK UP w/ 491QE,4G64S4M,4GZ4,4JB1 = Dadi (diycarserviceparts.com, autopartner.pl)'),
 '2902': ('Gonow', 'COXSWAIN/JETSTAR/KYLIN/TROY/VICTOR w/ JM491QME,GA491QE,4G64S4M,4JB1 = Gonow GA1020 platform (auto-che.com Gonow GA1020; karakorammotors.com Troy/Victor)'),
 '2903': ('GWM', 'HOVER/COOLBEAR/DEER/FENGJUN/SAILING/SING/STEED/TENGYI (Voleex) = Great Wall Motor; consolidated with existing GWM brand'),
 '2904': ('Mitsuoka', 'GALUE/HIMIKO/NOUERA/OROCHI/RAY/RYOGA/VIEWT/LA SEYDE = Mitsuoka'),
 '2906': ('Baolong', 'PEGASUS MPV 4G63/4G64/EQ491 = Guangzhou Baolong Pegasus, licensed Delica Space Gear (tractors.fandom.com Baolong Pegasus)'),
 '3035': ('Volkswagen', 'TIGUAN CGM/CCZA 2.0 TSI = Chinese-market VW Tiguan (5N)'),
 '3047': ('Lti Vehicles', 'TX 2.5TD VM R425 DOHC 102hp + TX 2.4 4G69 152hp petrol = TX4 (Wikipedia TX4: VM R425 + China-market 4G69 152PS)'),
 '3070': ('Naza', 'CITRA/FORZA/RIA/SURIA/SUTERA = Naza (Malaysian Kia rebadges)'),
 '3071': ('BAW', 'HAICE Bus 491QME 2.2 + YC4F9021 2.7D = BAW Haice minibus (cinaautoparts.com "BAW haice bus" 491QME/YC4F90-21)'),
 '3076': ('Brilliance', 'BS6 4G63 122hp/4G64 129hp = Brilliance BS6 (Zunchi/M1/"Galena") (grokipedia Brilliance BS6)'),
 '3086': ('Lifan', '320/520/620/X60/FENGSHUN = Lifan'),
 '3122': ('BYD', 'F0/F3/F6/FLYER/G3/G6/M6 = BYD'),
 '3124': ('BMW', '5 SERIES (E60) 2.5 192hp, engine "M54256S5" = garbled BMW M54B25'),
 '3127': ('Saipa', 'PRIDE Hatchback/Saloon 1.4 97hp 2004 = Saipa Pride, Iranian Kia Pride continuation (autocade.net SAIPA Pride)'),
 '3129': ('Honda', 'ODYSSEY MPV F23B/K24A6/K24Z2 = Chinese-market Honda Odyssey (Guangqi)'),
 '3130': ('Toyota', 'FJ CRUISER 1GR-FE + HIGHLANDER 1AR-FE/2GR-FE/3AR-FE = Chinese-market Toyota'),
 '3133': ('MG', '7 2.5 V6 177hp 2497cc = MG7 2.5 V6 130kW (automobile-catalog.com MG MG7 2.5)'),
 '3137': ('Toyota', 'LAND CRUISER 200 1GR/2UZ + PRADO 1GR-FE = Chinese-market Toyota'),
 '3141': ('Nissan', 'TEANA (J31/J32)/TIIDA = Chinese-market Nissan'),
 '3156': ('Shuanghuan', 'SCEO Closed Off-Road Vehicle = Shuanghuan SCEO'),
 '3158': ('Golden Dragon', 'XML bus w/ YC4F9023, 491QME, XC4G24 = Golden Dragon (金旅 XML6xxx, cn.auto-che.com)'),
 '3208': ('Renault Samsung', 'QM5 = Renault Samsung QM5'),
 '3276': ('HSV', 'CLUBSPORT/AVALANCHE (VY/VZ/VE/VF) = Holden Special Vehicles'),
 '3297': ('Ford', 'FALCON Pickup/Saloon (BA/BF) = Ford Australia'),
 '3300': ('LDV', 'V80 Box/Bus = LDV Maxus V80'),
 '3332': ('Geely', 'EC 7 Saloon/RV = Geely Emgrand EC7'),
 '3495': ('Artega', 'GT 3.6 BWS 300hp = Artega GT (VW 3.6 VR6)'),
 '3497': ('Dr Motor', 'DR 1/DR 2/DR 5 = DR Automobiles (existing Dr Motor brand)'),
 '3514': ('Smart', 'CITY EV 41hp 2007 + smart option text = smart fortwo electric drive 2007 London trial (41 hp magnetic motor, mbusa.com)'),
 '3652': ('Huanghai', 'PLUTUS 3.2D CA4DC2-10E3 = Huanghai Plutus pickup, FAW-Dachai 3.2 (Wikipedia Huanghai Plutus)'),
 '3677': ('Inokom', 'LORIMAS 2.6D D4BB + HD 5000 3.9D D4DC = Inokom-assembled Hyundai trucks (paultan.org: Lorimas AU26)'),
 '3697': ('Geely', 'GX2 1.3/1.5 MR479Q/QN = Geely GX2 (Gleagle)'),
 '3742': ('Luxgen', '7 Closed Off-Road Vehicle 2.2T G22T 178hp = Luxgen 7 SUV (纳智捷大7 SUV G22T, haicj.com)'),
 '3762': ('Besturn', 'B70 1.8 CA4GD5 139hp = FAW Besturn B70 1.8 (wikiwand Besturn B70)'),
 '3913': ('Haima', 'V10 1.0 75hp HMAGM10-VF = Haima mini (autohome.com.cn HMAGM10-VF)'),
 '4176': ('Higer', 'H5C 2.4 4RB2 + 2.5D DK4B1 = Higer H5C light bus (chinabuses.org)'),
 '4260': ('Renault Samsung', 'QM3/QM5/SM7 = Renault Samsung'),
}

# other mis-brand renames: old -> new
MISBRAND = {
 'Citroën': 'Citroen',   # 486-variant split from the Vivid source (hernr_21 = Citroën)
 'Saic Mg': 'MG',
 'SATURN': 'Saturn',
 'SHELBY': 'Shelby',
 'Jmc': 'JMC',
 'Volga': 'GAZ',          # 'Siber' = GAZ Siber
}

# model renames/merges during rebadge: (old_brand, old_model) -> new_model_name
MODEL_RENAME = {
 ('hernr_3035', 'TIGUAN'): 'TIGUAN (5N_)',
 ('hernr_3130', 'FJ CRUISER'): 'FJ CRUISER (GSJ1_)',
 ('hernr_3130', 'HIGHLANDER'): 'Highlander',
 ('hernr_3137', 'LAND CRUISER 200'): 'LAND CRUISER (VDJ20_, UZJ20_)',
}

QUEUE_NOTE_UPDATES = [
 ("car_brand='hernr_1490'", 'Brand identified: CATERHAM Seven (CF) 2.0 Turbo 204hp 2001 - engine mapping still needs research (Caterham Ford Duratec era)'),
 ("car_brand='hernr_1516'", 'Brand identified: MARCOS - TS250 2.5 Ford V6 175-180hp / TS500 5.0 Rover V8 320hp (carthrottle.com) - needs engine-row creation'),
 ("car_brand='hernr_2903' AND car_model LIKE '%TENGYI%'", 'Brand identified: GWM Tengyi/Voleex C50 - 1.5T engine code (GW4G15T?) needs verification'),
 ("car_brand='hernr_3514'", 'Brand identified: SMART fortwo electric drive (2007 London trial, 41hp magnetic motor, Zebra battery, mbusa.com) - needs EV engine row'),
 ("car_brand='hernr_2589'", 'Brand identified: LANDWIND (Jiangling) 2.4 125hp - engine = Mitsubishi 4G64 family, exact code needs verification'),
]


def get_or_create_brand(cur, name):
    row = cur.execute("SELECT id FROM brands WHERE name=?", (name,)).fetchone()
    if row:
        return row[0], False
    cur.execute("INSERT INTO brands(name) VALUES (?)", (name,))
    return cur.execute("SELECT id FROM brands WHERE name=?", (name,)).fetchone()[0], True


def rebrand(cur, old, new, created_brands, moved, merged_models):
    """Move all variants/models/engine-examples/queue-rows from brand `old` to `new`."""
    nvar = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand=?", (old,)).fetchone()[0]
    if nvar == 0:
        return 0
    bid, created = get_or_create_brand(cur, new)
    if created:
        created_brands.append(new)

    # models: rename or merge into existing (newbrand, model_name)
    for (mid, mname) in cur.execute("SELECT id, model_name FROM models WHERE brand_name=?", (old,)).fetchall():
        new_mname = MODEL_RENAME.get((old, mname), mname)
        existing = cur.execute("SELECT id FROM models WHERE brand_name=? AND model_name=?", (new, new_mname)).fetchone()
        if existing and existing[0] != mid:
            cur.execute("UPDATE vehicle_variants SET car_brand=?, car_model=? WHERE car_model=? AND car_brand=?",
                        (new, new_mname, mname, old))
            cur.execute("DELETE FROM models WHERE id=?", (mid,))
            merged_models.append((f'{old}/{mname}', f'{new}/{new_mname}'))
        else:
            cur.execute("UPDATE models SET brand_id=?, brand_name=?, model_name=? WHERE id=?", (bid, new, new_mname, mid))
            cur.execute("UPDATE vehicle_variants SET car_brand=?, car_model=? WHERE car_brand=? AND car_model=?",
                        (new, new_mname, old, mname))
    # any variants whose model row was absent (orphans): plain brand update
    cur.execute("UPDATE vehicle_variants SET car_brand=? WHERE car_brand=?", (new, old))
    # cosmetic: engine examples + queue rows
    cur.execute("UPDATE engines SET brand_example=? WHERE brand_example=?", (new, old))
    cur.execute("UPDATE remapping_queue SET car_brand=? WHERE car_brand=?", (new, old))
    cur.execute("UPDATE remapping_queue SET wrong_engine_brand_example=? WHERE wrong_engine_brand_example=?", (new, old))
    # if new brand had an empty brand row and we created one, or 'Great Wall' etc. left empty: harmless
    return nvar


def main():
    if '--apply' not in sys.argv:
        sys.exit('usage: step8_step3_brand_rebadge.py --apply')
    con = sqlite3.connect(DB)
    cur = con.cursor()

    brands_before = cur.execute("SELECT COUNT(*) FROM brands").fetchone()[0]
    nvar_before = cur.execute("SELECT COUNT(*) FROM vehicle_variants").fetchone()[0]
    nhernr_before = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand LIKE 'hernr%'").fetchone()[0]

    backup = os.path.join(BACKUP_DIR, f'car_database_backup_pre_step8_{date.today().isoformat()}.db')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(DB, backup)
    print(f"Backup: {backup}\n")

    created_brands, merged_models = [], []
    decisions = []

    print(f"=== 1) hernr buckets -> real brands ({len(HERNR_MAP)} buckets, {nhernr_before} variants) ===")
    for num, (new, why) in HERNR_MAP.items():
        old = f'hernr_{num}'
        n = rebrand(cur, old, new, created_brands, [], merged_models)
        decisions.append([old, new, n, why])
        print(f"  {old:12s} -> {new:20s} ({n:3d} variants)")

    print(f"\n=== 2) mis-brand fixes ===")
    for old, new in MISBRAND.items():
        n = rebrand(cur, old, new, created_brands, [], merged_models)
        decisions.append([old, new, n, 'mis-brand rename'])
        print(f"  {old:12s} -> {new:20s} ({n:3d} variants)")

    print(f"\n=== 3) queue note updates for Step-3-blocked rows ===")
    for cond, note in QUEUE_NOTE_UPDATES:
        rows = cur.execute(f"SELECT vehicle_variant_id, car_brand, car_model FROM remapping_queue WHERE {cond}").fetchall()
        for (vid, b, m) in rows:
            cur.execute("UPDATE remapping_queue SET note=? WHERE vehicle_variant_id=?",
                        (f"{note} [updated by Step 3]", vid))
            print(f"  #{vid} {b} {m}: note updated")

    # 4) optional win: Hummer H3 3.5 220hp -> L52 if engine row exists
    print(f"\n=== 4) opportunistic remap: Hummer H3 3.5 (220hp) -> L52 ===")
    h3 = cur.execute("""SELECT v.id, v.engine_code, rq.status FROM vehicle_variants v
                        LEFT JOIN remapping_queue rq ON rq.vehicle_variant_id=v.id
                        WHERE v.car_brand='Hummer' AND v.car_model='HUMMER H3' AND v.engine_power_hp BETWEEN 215 AND 225""").fetchall()
    l52 = cur.execute("SELECT engine_code, power_hp, displacement_cc FROM engines WHERE engine_code='L52'").fetchone()
    print(f"  H3 220hp variants: {h3}; L52 engine row: {l52}")
    if h3 and l52:
        for (vid, code, status) in h3:
            if code is None:
                cur.execute("UPDATE vehicle_variants SET engine_code='L52' WHERE id=?", (vid,))
                cur.execute("""UPDATE remapping_queue SET status='remapped', new_engine_code='L52',
                               note=COALESCE(note,'') ||
                               ' | Step 3: brand=Hummer identified; H3 3.5 220hp = GM Vortec 3500 L52 I5' 
                               WHERE vehicle_variant_id=?""", (vid,))
                print(f"    #{vid} remapped to L52")

    con.commit()

    # 5) verify
    print(f"\n=== VERIFICATION ===")
    print("integrity_check:", cur.execute("PRAGMA integrity_check").fetchone()[0])
    left_v = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand LIKE 'hernr%'").fetchone()[0]
    left_m = cur.execute("SELECT COUNT(*) FROM models WHERE brand_name LIKE 'hernr%'").fetchone()[0]
    left_e = cur.execute("SELECT COUNT(*) FROM engines WHERE brand_example LIKE 'hernr%'").fetchone()[0]
    left_q = cur.execute("SELECT COUNT(*) FROM remapping_queue WHERE car_brand LIKE 'hernr%'").fetchone()[0]
    print(f"remaining hernr: variants={left_v} models={left_m} engines={left_e} queue={left_q} (all must be 0)")
    print(f"variants total: {nvar_before} -> {cur.execute('SELECT COUNT(*) FROM vehicle_variants').fetchone()[0]}")
    print(f"brands: {brands_before} -> {cur.execute('SELECT COUNT(*) FROM brands').fetchone()[0]} (new: {created_brands})")
    print(f"merged model rows (collisions resolved): {len(merged_models)}")
    for a, b in merged_models[:20]:
        print(f"    {a} -> {b}")
    print(f"models: {cur.execute('SELECT COUNT(*) FROM models').fetchone()[0]}")
    print("NULL engine_code:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NULL").fetchone()[0])
    print("v_vehicle_with_service:", cur.execute("SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0])
    print("spot checks:")
    for b in ['Smart', 'Geely', 'Zastava', 'GWM', 'Citroen', 'Toyota', 'MG', 'Luxgen', 'Eunos']:
        n = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand=?", (b,)).fetchone()[0]
        m = cur.execute("SELECT COUNT(DISTINCT car_model) FROM vehicle_variants WHERE car_brand=?", (b,)).fetchone()[0]
        print(f"    {b:12s} {n:4d} variants, {m:3d} models")
    print("queue:", cur.execute("SELECT status, COUNT(*) FROM remapping_queue GROUP BY 1 ORDER BY 2 DESC").fetchall())

    with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['old_brand', 'new_brand', 'variants_moved', 'evidence'])
        for row in decisions:
            w.writerow(row)
    print(f"\ndecisions: {CSV_OUT}")
    print(f"rollback: cp '{backup}' '{DB}'")
    con.close()


if __name__ == '__main__':
    main()
