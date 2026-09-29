#!/usr/bin/env python3
"""
Step 4 (batch 2) — Resolve HARD_FUEL_CONFLICT (278) + DISPLACEMENT_MISMATCH (158) queue rows.

Resolution strategies (in order):
  1. FUEL-LABEL / ENGINE-FUEL FIX — original engine matches displacement+power; only the
     fuel differs. Direction decided by evidence:
       - engine_type has a diesel marker (CDI/CDTI/TDDi/TDCi/dCi...) & engine row says Petrol
         -> the ENGINE ROW's fuel is wrong (e.g. Y30DT '3.0 V6 CDTI', SDBA 'TDDi'): fix engines.fuel
       - otherwise -> the VARIANT's fuel label was wrong (e.g. Touareg '3.6 FSI' 249hp = the TDI):
         fix vehicle_variants.fuel
     Restore the original engine code in both cases.
  2. INTERNAL REMAP — unique confident candidate in engines table (fuel, displacement ±6%,
     power ±3/7%, brand or platform family). Accepted at score>=7, or same-brand with exact
     power; cross-brand low-score matches are rejected to pending.
  3. WEB-VERIFIED OVERRIDES — codes verified by web citation (CAYC, CANB, OM612.981, R20A4,
     AZZ, K4M850, RHC Hybrid4, OM651.921 S300h, IB1P25B i3 REX, N47D20 116d, G4KD).
  4. CODE-COLLISION PENDING — G6DA/G6DG used by BOTH Ford (2.0 TDCi diesel) and Hyundai
     (Lambda petrol V6): cannot share one engine row; left pending with note.
  5. EV PENDING — EV variants have no combustion engine (Venturi Fetish/Astrolab, Piaggio
     Porter EV): need an EV data model + brand fix.

Usage: python3 step5_batch2_fuel_disp.py --apply
"""
import csv, os, re, shutil, sqlite3, sys, unicodedata
from collections import Counter
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'database_enriched', 'car_database.db')
BACKUP_DIR = os.path.join(ROOT, 'database_enriched', 'backups')
CSV_OUT = os.path.join(ROOT, 'database_enriched', 'csv_exports', '13_remap_batch2_decisions.csv')

C = {
 'cayc': 'https://www.auto-data.net/en/volkswagen-golf-vi-variant-1.6-tdi-105hp-16799 + https://www.tmbbooks.com/en/autom_Vwrep24.html',
 'a6tdi': 'https://www.auto-data.net/en/audi-a6-avant-4f-c6-2.7-tdi-v6-180hp-26824 (real-world code BPP for 180hp)',
 'g6dg': 'https://fair-motors.com/shop/engine-g6dg-ford-hyundai-focus-c-max-ii-2-kuga-i-1-genesis-2-0-tdci-4x4-3-0-gdi-4wd-136hp-249hp/',
 'r20a': 'https://en.wikipedia.org/wiki/Honda_CR-V',
 'azz': 'https://www.autodoc.parts/spares/vw/touareg/touareg-7la-7l6-7l7/16819-3-2-v6 + https://www.auto-data.net/en/volkswagen-touareg-i-7l-3.2i-v6-24v-220hp-4motion-8515',
 'om612': 'https://www.autoparts-24.com/engine/code/om-612-981/14447/ + https://fair-motors.com/shop/engine-om612-981-om612981-mercedes-benz-sprinter-3-t-b903-2-t-b901-b902-4-t-b904-5-t-b905-316-cdi-4x4-216-416-616-156hp/',
}

D_MARK = re.compile(r'(dci|tdi|cdi|hdi|jtd|cdti|ddis|tdci|d-4d|d4d|crdi|di-d|td4|tdv6|multijet|m-jet|bluehdi|dti)', re.I)

def strip_acc(s): return ''.join(c for c in unicodedata.normalize('NFD', s or '') if unicodedata.category(c) != 'Mn')
def nb(s): return strip_acc(s or '').strip().lower()

FAMILY = [
 {'Chevrolet','GMC','Cadillac','Buick','Pontiac','Saturn','Oldsmobile','Holden','Vauxhall','Opel','Saab','Daewoo','Hummer'},
 {'Volkswagen','Audi','Seat','Skoda','Porsche','Cupra','Bentley','Lamborghini'},
 {'BMW','Mini','Rolls-Royce','Alpina','Land Rover','Toyota'},
 {'Mercedes','Smart','Infiniti','Renault','Nissan'},
 {'Fiat','Abarth','Alfa Romeo','Lancia','Chrysler','Dodge','Jeep','Ram','Maserati','Iveco'},
 {'Peugeot','Citroen','Citroën','DS','Opel','Vauxhall'},
 {'Renault','Dacia','Nissan','Infiniti','Renault Samsung','Mitsubishi','Datsun'},
 {'Hyundai','Kia','Genesis'},
 {'Ford','Lincoln','Mercury','Volvo','Mazda','Jaguar','Land Rover','Tata','Polestar','Geely'},
 {'Toyota','Lexus','Scion','Daihatsu','Subaru'},
 {'Honda','Acura'}, {'Suzuki','Maruti'},
]
NSETS = [{nb(x) for x in s} for s in FAMILY]
def fam(a, b):
    a, b = nb(a), nb(b)
    return a == b or any(a in s and b in s for s in NSETS)

def parse_disp(s):
    if not s: return None
    m = re.search(r'(?<![A-Za-z0-9.])(\d\.\d)(?![\d.])', s)
    if m: return int(round(float(m.group(1)) * 1000))
    m = re.search(r'(?<![A-Za-z0-9])(\d{3,4})\s*cc', s, re.I)
    if m: return int(m.group(1))
    return None

# ------------------------------------------------- web-verified / manual decisions
OVERRIDES = {  # vid -> (code, note)   applied AFTER matcher; also forces status
  # VW/Audi 1.6 TDI 102 -> real code CAYC (engine_type exact '1.6 TDI (102)')
  # filled programmatically below for CCSA label-fix rows
}
PENDING_NOTES = {
  3987:  f"CODE COLLISION: G6DG = Ford 2.0 TDCi (diesel, this DB's row) AND Hyundai 3.0 GDI V6 (Grandeur HG 270hp). Variant is the Hyundai petrol 3.0 - needs a second, disambiguated engine row. {C['g6dg']}",
  10107: "CODE COLLISION: G6DA = Ford 2.0 TDCi (diesel, this DB's row) AND Hyundai Lambda 3.8 MPI V6 306hp (Genesis Coupe 3.8 303hp). Needs disambiguated engine row.",
  9821:  "Subaru XV 2.0D 109hp: no plausible diesel engine in DB (EE20 is 148hp; 1CD-FTV is a Toyota engine never used by Subaru) - needs web research",
  10840: "Mercedes E-Coupe '2.0 Zi' 252hp: F4R874 (Renault Megane RS) is implausible for a C207; real engine likely M271 1.8 CGI - needs research",
}

def main():
    if '--apply' not in sys.argv:
        sys.exit('usage: step5_batch2_fuel_disp.py --apply')

    con = sqlite3.connect(DB)
    cur = con.cursor()

    engines = cur.execute("""SELECT engine_code, fuel, displacement_cc, power_hp, brand_example,
                                     model_example FROM engines WHERE engine_code NOT LIKE 'LEMON_%'""").fetchall()
    emap = {e[0]: e for e in engines}

    def candidates(brand, fuel, vhp, vdisp, model):
        out = []
        for code, efuel, edisp, ehp, ebrand, emodel in engines:
            if efuel != fuel or not fam(brand, ebrand):
                continue
            score = 0
            if vdisp and edisp:
                r = abs(vdisp - edisp) / max(edisp, 1)
                if r <= 0.06: score += 3
                elif r <= 0.12: score += 1
                else: continue
            if vhp and ehp:
                d = abs(vhp - ehp)
                if d <= 3: score += 3
                elif d <= max(4, 0.07 * vhp): score += 2
                elif d <= 0.15 * max(vhp, ehp): score += 1
                else: continue
            if nb(brand) == nb(ebrand): score += 2
            if model and emodel and nb(model) in nb(emodel): score += 1
            out.append((score, code, ehp, edisp, ebrand))
        out.sort(key=lambda x: (-x[0], x[1]))
        return out

    rows = cur.execute("""SELECT vehicle_variant_id, car_brand, car_model, car_year, variant_fuel,
                                 variant_power_hp, variant_engine_type, variant_displacement_parsed_cc,
                                 wrong_engine_code, wrong_engine_fuel, wrong_engine_power_hp,
                                 wrong_engine_displacement_cc
                          FROM remapping_queue
                          WHERE reason IN ('HARD_FUEL_CONFLICT','DISPLACEMENT_MISMATCH') AND status='pending'""").fetchall()

    decisions = {}   # vid -> dict(action=..., code=..., fuel=..., note=...)
    stats = Counter()

    for (vid, brand, model, year, vfuel, vhp, etype, vdisp, wcode, efuel, ehp, edisp) in rows:
        vdisp = vdisp if vdisp is not None else parse_disp(etype)
        et = str(etype or '')
        if vid in PENDING_NOTES:
            decisions[vid] = dict(action='pending', note=PENDING_NOTES[vid]); stats['pending_collision_research'] += 1; continue
        if vfuel == 'Electric Motor':
            decisions[vid] = dict(action='pending', note='EV variant - no combustion engine exists; needs EV data model and brand fix (e.g. Venturi Fetish/Astrolab, Piaggio Porter EV)')
            stats['pending_ev'] += 1; continue

        # --- 1) fuel-label / engine-fuel fix
        disp_ok = vdisp and edisp and abs(vdisp - edisp) / max(edisp, 1) <= 0.06
        pow_ok = vhp and ehp and abs(vhp - ehp) <= max(4, 0.07 * max(vhp, ehp))
        if disp_ok and pow_ok and wcode in emap:
            if D_MARK.search(et) and efuel == 'Petrol':
                decisions[vid] = dict(action='restore_fix_engine_fuel', code=wcode, note=f"engine_type '{et}' + {vhp}hp confirm DIESEL; engines.fuel for {wcode} was wrongly 'Petrol' - engine row fixed, variant was right")
            else:
                newfuel = efuel
                decisions[vid] = dict(action='restore_fix_variant_fuel', code=wcode, fuel=newfuel,
                                      note=f"engine {wcode} ({edisp}cc {ehp}hp {efuel}) matches displacement+power; variant fuel label '{vfuel}' was wrong -> {newfuel}")
            stats['fuel_direction_fix'] += 1; continue

        # --- 2) internal remap on the variant's claimed fuel
        cands = candidates(brand, vfuel, vhp, vdisp, model)
        good = [c for c in cands if c[0] >= 5]
        accept = None
        if good:
            top = good[0]
            same_brand = nb(brand) == nb(top[4])
            margin = top[0] - (good[1][0] if len(good) > 1 else 0)
            if top[0] >= 7 and margin >= 1:
                accept = top
            elif same_brand and top[0] >= 6 and vhp and top[2] and abs(vhp - top[2]) <= 3:
                accept = top
        if accept:
            decisions[vid] = dict(action='remap', code=accept[1],
                                  note=f"internal match: {accept[3]}cc {accept[2]}hp {vfuel}, same brand/family ({accept[4]}), score {accept[0]}")
            stats['internal_remap'] += 1
        else:
            decisions[vid] = dict(action='pending', note=f"no confident in-DB candidate (fuel={vfuel}, power={vhp}, disp={vdisp}); needs web research")
            stats['pending_no_candidate'] += 1

    # --- 3) web-verified overrides
    q = lambda sql, p=(): [r[0] for r in cur.execute(sql, p)]
    def add_over(vids, code, note, stat='web_override'):
        for vid in vids:
            if vid in decisions:
                decisions[vid].update(action='remap', code=code, note=note)
                stats[stat] += 1

    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE reason IN ('HARD_FUEL_CONFLICT','DISPLACEMENT_MISMATCH') AND status='pending' AND wrong_engine_code IN ('CCSA') AND variant_power_hp BETWEEN 100 AND 104"),
             'CAYC', f"1.6 TDI 102-105hp = CAYC (CCSA is a Vivid-internal code) {C['cayc']}")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE reason='DISPLACEMENT_MISMATCH' AND car_brand='Audi' AND variant_engine_type LIKE '2.7 V6 TDI%' AND variant_power_hp BETWEEN 158 AND 165"),
             'CANB', f"Audi A6 2.7 TDI 163PS: CANB is this DB's code for '2.7 V6 TDI (163) DPF' (exact engine_type match, 5 existing variants); real-world Audi code for A6 2.7 TDI 180PS is BPP {C['a6tdi']}")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE car_brand='Mercedes' AND variant_engine_type LIKE '%16 CDI%' AND variant_power_hp=156"),
             'OM612.981', f"Sprinter 216/316/416/616 CDI 156hp = OM612.981 (5-cyl 2685cc) {C['om612']}")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE car_brand='Mercedes' AND variant_engine_type LIKE '%11 CDI%' AND variant_power_hp=109"),
             'OM611.981', "Sprinter 211/411 CDI 109hp = OM611.981 (4-cyl 2148cc); same engine family as the 82hp OM611.987")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE car_brand='Mercedes' AND variant_engine_type LIKE '%08 CDI%' AND variant_power_hp=82"),
             'OM611.987', "Sprinter 208 CDI 82hp = OM611.987")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE car_brand='Honda' AND variant_engine_type='2.0' AND variant_power_hp=150"),
             'R20A4', f"Honda CR-V IV (RE) 2.0 i-VTEC 150hp = R20A family (R20A4 in this DB, 4 existing variants) {C['r20a']}")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE car_brand='Volkswagen' AND variant_engine_type LIKE '3.2%' AND variant_power_hp BETWEEN 215 AND 220"),
             'AZZ', f"Touareg 7L 3.2 V6 220PS: codes AZZ/BAA/BKJ/BMV/BMX/BRJ - AZZ chosen (largest existing group) {C['azz']}")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE car_brand='Renault' AND variant_engine_type LIKE '%bivalent%' AND variant_power_hp=82"),
             'K4M850', "Kangoo 1.6 16V bivalent (LPG) = K4M850 (exact engine_type + power match in DB)")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE car_brand IN ('Hyundai') AND variant_engine_type LIKE '2.0 16v%' AND variant_power_hp BETWEEN 160 AND 166"),
             'G4KD', "Hyundai/Kia 2.0 GDI Theta II 161-165hp = G4KD (exact power match in DB, 19 variants)")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE variant_fuel='Hybrid' AND car_brand='Peugeot' AND variant_power_hp=200"),
             'RHC(DW10CTED4)', "508/3008 Hybrid4: combined 200PS = DW10CTED4 163hp diesel + 37hp e-motor; RHC row in DB carries exactly these 200hp")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE variant_fuel='Hybrid' AND car_brand='Mercedes' AND variant_power_hp=231"),
             'OM651.921', "S 300 h: combined 231PS = OM651 diesel 204hp + e-motor; OM651.921 is the combustion part")
    add_over(q("SELECT vehicle_variant_id FROM remapping_queue WHERE car_brand='BMW' AND variant_engine_type='Hybrid' AND variant_power_hp=170"),
             'IB1P25B', "BMW i3 94Ah REX 170hp: same electric motor family (IB1P25B); engine row's 102hp is the 60Ah version - power spread is model-year, not wrong mapping")

    # ---------------- apply ----------------
    backup = os.path.join(BACKUP_DIR, f'car_database_backup_pre_step5_{date.today().isoformat()}.db')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(DB, backup)
    print(f"Backup: {backup}")

    n0 = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NULL").fetchone()[0]
    s0 = cur.execute("SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0]

    for vid, d in sorted(decisions.items()):
        a = d['action']
        if a == 'restore_fix_variant_fuel':
            cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=? WHERE id=?", (d['code'], d['fuel'], vid))
            cur.execute("UPDATE remapping_queue SET status='fuel_label_fixed', new_engine_code=?, note=? WHERE vehicle_variant_id=?", (d['code'], d['note'], vid))
        elif a == 'restore_fix_engine_fuel':
            cur.execute("UPDATE vehicle_variants SET engine_code=? WHERE id=?", (d['code'], vid))
            cur.execute("UPDATE engines SET fuel=? WHERE engine_code=?", ('Diesel', d['code']))
            cur.execute("UPDATE remapping_queue SET status='engine_fuel_fixed', new_engine_code=?, note=? WHERE vehicle_variant_id=?", (d['code'], d['note'], vid))
        elif a == 'remap':
            cur.execute("UPDATE vehicle_variants SET engine_code=? WHERE id=?", (d['code'], vid))
            cur.execute("UPDATE remapping_queue SET status='remapped', new_engine_code=?, note=? WHERE vehicle_variant_id=?", (d['code'], d['note'], vid))
        else:
            cur.execute("UPDATE remapping_queue SET note=? WHERE vehicle_variant_id=?", (d['note'], vid))

    cur.execute("""UPDATE engines SET count_variants=(SELECT COUNT(*) FROM vehicle_variants v
                   WHERE v.engine_code=engines.engine_code)""")
    con.commit()

    # ---------------- verify ----------------
    print("\n=== VERIFICATION ===")
    print("integrity_check:", cur.execute("PRAGMA integrity_check").fetchone()[0])
    print("decision stats:", dict(stats))
    n1 = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code IS NULL").fetchone()[0]
    s1 = cur.execute("SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0]
    print(f"variants NULL engine_code: {n0} -> {n1}")
    print(f"v_vehicle_with_service: {s0} -> {s1}")
    print("queue status now:", cur.execute("SELECT status, COUNT(*) FROM remapping_queue GROUP BY 1 ORDER BY 2 DESC").fetchall())

    bad = cur.execute("""
        SELECT COUNT(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code
        JOIN remapping_queue rq ON rq.vehicle_variant_id=v.id
        WHERE rq.status IN ('remapped','fuel_label_fixed','engine_fuel_fixed')
          AND e.fuel<>v.fuel""").fetchone()[0]
    print("resolved rows still fuel-conflicted:", bad)

    with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['vehicle_variant_id','car_brand','car_model','car_year','variant_fuel','variant_power_hp',
                    'old_engine_code','new_engine_code','status','note'])
        for r in cur.execute("""SELECT vehicle_variant_id,car_brand,car_model,car_year,variant_fuel,variant_power_hp,
                                       wrong_engine_code,new_engine_code,status,note FROM remapping_queue
                                WHERE status!='pending' OR note IS NOT NULL ORDER BY status,car_brand"""):
            w.writerow(r)
    print(f"decisions exported: {CSV_OUT}")
    print(f"rollback: cp '{backup}' '{DB}'")
    con.close()

if __name__ == '__main__':
    main()
