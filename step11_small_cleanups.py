#!/usr/bin/env python3
"""
STEP 11: small cleanups (user-approved list)
 1. Garbled engine codes: M54256S5->M54B25, G4KR/H4KR->G4EE, 25V6S1->KV6,
    plus C20LET row correction (row held Ford 1.4 TDCi data; real C20LET = Opel 2.0 16v Turbo)
    with remaps of 6 wrongly-attached variants to their correct codes.
 2. The 5 unblocked pendings: Marcos TS250/TS500, smart ed, GWM Tengyi C50, Landwind 2.4,
    Caterham Seven (CF) 2.0T; plus Caterham CSR junk codes.
 3. OEM spec fills: G6DA/G6DG (Ford 2.0 TDCi rows), G6DA/G6DG (Hyundai), M62B48, M73B54 (new row),
    Power Stroke capacity corrections (F22).
 4. Cosmetic engine_type cleanup on variants (junk patterns + displacement-spoof texts).
Gated: --apply to write. Backup: backups/car_database_backup_pre_step11_<date>.db
"""
import sqlite3, sys, re, shutil, csv
from datetime import date

DB = "database_enriched/car_database.db"
APPLY = "--apply" in sys.argv

CIT = {
    "M54B25": "https://en.wikipedia.org/wiki/BMW_M54 (M54B25 = 2,494 cc)",
    "G4EE": "https://www.drom.ru/catalog/kia/engine/g4ee/ + https://en.kiaclub.cz/engine_detail.php?id=27 (G4EE = Kia Alpha 1.4 DOHC 1,399 cc 75-97 hp; Kia Pride/Rio)",
    "KV6": "Rover/MG KV6 2.5 V6 2497cc 177hp (existing DB row)",
    "C20LET": "https://www.autodoc.co.uk/car-parts/timing-chain-kit-15065/caterham/seven/seven-cf/20729-2-0-turbo (Caterham Seven CF 2.0 Turbo 204hp 1998cc = C20 LET)",
    "F6JD": "existing DB row (Ford 1.4 TDCi 1399cc 70hp)",
    "K9K858": "existing DB row; sibling Duster 2012 1.5 dCi 109hp variants use K9K898/856/858",
    "F1CE0481FA_HA": "existing DB rows (Iveco 3.0 HPI TurboDiesel 146/176hp); sibling Massif variants use them",
    "TS250": "https://autodata24.com/marcos/ts/ts-250/details + https://www.vindecoderz.com/EN/Marcos/Marcasite/2004/TS250%202.5%20MT/specs-features/19015 (2.5 Ford V6 Duratec 24V 175-180hp)",
    "TS500": "https://www.ultimatespecs.com/car-specs/Marcos/28718/Marcos-TS500-50-V8.html + https://www.carthrottle.com/post/nkvver3 (5.0 V8 320hp; Rover V8)",
    "SMARTED": "https://en.wikipedia.org/wiki/Smart_electric_drive + https://www.topspeed.com/cars/smart/2007-smart-fortwo-electric-vehicle/ (first-gen 450 ed: Zytek 30 kW/41hp, Zebra battery, London 2007)",
    "GW4G15T": "https://www.chinamobil.ru/eng/great-wall/voleex-c50/?view=props + https://www.coolcarsinchina.com/2022/11/19/great-wall-voleex-c50-is-a-compact-sedan-in-china/ (Voleex/Tengyi C50 1.5T GW4G15T petrol 1497cc 133hp)",
    "4G64S4M": "https://myenginespecs.com/mitsubishi/mitsubishi-4g64-engine-specs-configuration-and-service-intervals/ (Mitsubishi 4G64 2.4) + DB sibling Landwind variants",
    "CSR": "https://en.wikipedia.org/wiki/Caterham_7 (CSR: 2.3 Ford Duratec, Cosworth-tuned, 200/260hp)",
    "FORD_TDCI": "https://enginecrux.com/ford-duratorq-2-0-tdci-engine-overview-and-specs/ (2.0 TDCi oil 5.5 L w/ filter, 5W-30) + https://www.kugaownersclub.co.uk/threads/oil-change-diy-guide-2-0-tdci-loads-of-pics.883/ (booklet 5.5 L 5W-30 ACEA A1/B1)",
    "G6DA_HY": "https://mymotorlist.com/engines/hyundai/g6da/ (3.8 Lambda: 5W-30, 6.0 L)",
    "G6DG_HY": "https://mymotorlist.com/engines/hyundai/g6dg/ (3.0 GDI: 5W-30, 6.9 L)",
    "ALPINA": "https://thealpinaregister.com/forums/viewtopic.php?t=12671 (B10 V8 oil ~7.5 L)",
    "M73B54": "https://www.auto-data.net/en/rolls-royce-silver-seraph-5.4-i-v12-326hp-10938 (oil 8 L 5W-40, coolant 15 L) + http://wiki.bavariantechnic.com/index.php?title=Engine_Oil_Change_Capacities (M73 8.5 qt = 8.0 L) + https://mymotorlist.com/engines/bmw/m73b54/",
    "PSD": "https://www.egrperformance.com/blogs/news/6-7-powerstroke-oil-capacity + https://prosourcediesel.com/blog/ford-powerstroke/how-much-oil-a-guide-to-your-diesel-truck-oil-change/ + https://www.suncentauto.com/blog/7-3-powerstroke-oil-capacity.html (7.3/6.0/6.4 = 15 qt = 14.2 L w/filter; 6.7 = 13 qt = 12.3 L)",
}

NEW_ENGINES = {
    "5.0 Rover V8": ("5.0 V8 Rover (Marcos TS500)", "Petrol", 5000, 320, 8, CIT["TS500"]),
    "smart ED (450)": ("Electric motor 30 kW (Zytek, Zebra battery)", "Electric", None, 41, None, CIT["SMARTED"]),
    "Duratec 2.3 CSR": ("2.3 I4 Ford Duratec (Cosworth-tuned, CSR/CSR260)", "Petrol", 2261, None, 4, CIT["CSR"]),
    "M73B54": ("5.4 V12 (BMW M73)", "Petrol", 5379, 326, 12, CIT["M73B54"]),
}

con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=ON")
log = []
dec_rows = []   # per-variant decisions: [variant_id, brand, model, field, old, new, evidence]

def merge_specs(lemon, target):
    """Migrate specs only when source is trusted (not ESTIMATE) and target lacks data.
    Retired engine's spec rows are always removed."""
    for table in ("engine_service_specs", "engine_technical_specs"):
        cur.execute(f"SELECT * FROM {table} WHERE engine_code=?", (lemon,))
        src = cur.fetchone()
        if src:
            cols = [c[1] for c in cur.execute(f"PRAGMA table_info({table})")]
            d = dict(zip(cols, src))
            src_txt = (d.get("oil_spec_source") or "") + (d.get("coolant_source") or "")
            if "ESTIMATE" in src_txt:
                log.append(f"  skip spec migrate {lemon}->{target} (source is ESTIMATE)")
            else:
                cur.execute(f"SELECT 1 FROM {table} WHERE engine_code=?", (target,))
                if cur.fetchone():
                    sets = ", ".join(f"{c}=COALESCE({c}, ?)" for c in cols if c != "engine_code")
                    cur.execute(f"UPDATE {table} SET {sets} WHERE engine_code=?",
                                (*[d[c] for c in cols if c != "engine_code"], target))
                else:
                    cur.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
                                tuple(d[c] for c in cols))
        cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (lemon,))
    cur.execute("SELECT count_variants FROM engines WHERE engine_code=?", (lemon,))
    r = cur.fetchone()
    if r and r[0]:
        cur.execute("UPDATE engines SET count_variants=count_variants+? WHERE engine_code=?", (r[0], target))
    cur.execute("DELETE FROM engines WHERE engine_code=?", (lemon,))

def remap_variant(vid, new_code, why):
    old = cur.execute("SELECT engine_code FROM vehicle_variants WHERE id=?", (vid,)).fetchone()
    if old is None:
        log.append(f"  SKIP variant {vid} (not found)"); return
    cur.execute("UPDATE vehicle_variants SET engine_code=? WHERE id=?", (new_code, vid))
    log.append(f"  variant {vid}: {old[0]} -> {new_code} ({why})")

def set_queue(vid, new_code, note):
    cur.execute("SELECT id FROM remapping_queue WHERE vehicle_variant_id=? AND status='pending'", (vid,))
    r = cur.fetchone()
    if r:
        cur.execute("UPDATE remapping_queue SET status='remapped', new_engine_code=?, note=? WHERE id=?",
                    (new_code, f"{note} [Step 11]", r[0]))
        log.append(f"  queue {r[0]}: pending -> remapped ({new_code})")

print("=== 1. GARBLED CODES ===")
for old, new, why in [
    ("M54256S5", "M54B25", CIT["M54B25"]),
    ("G4KR", "G4EE", CIT["G4EE"]),
    ("H4KR", "G4EE", CIT["G4EE"]),
    ("25V6S1", "KV6", CIT["KV6"]),
]:
    vs = [r[0] for r in cur.execute("SELECT id FROM vehicle_variants WHERE engine_code=?", (old,))]
    for v in vs:
        remap_variant(v, new, why)
        set_queue(v, new, why)
    merge_specs(old, new)
    log.append(f"  engine row {old} retired ({len(vs)} variants moved)")

# fix displacements on target rows (cited)
cur.execute("UPDATE engines SET displacement_cc=2494 WHERE engine_code='M54B25'")
cur.execute("UPDATE engines SET displacement_cc=1399 WHERE engine_code='G4EE'")
log.append("  M54B25 displacement 2457->2494; G4EE 1400->1399 [cited]")

print("=== 1b. C20LET row correction ===")
# remap wrongly-attached variants
for vid, new, why in [
    (10687, "F6JD", CIT["F6JD"]),
    (25313, "K9K858", CIT["K9K858"]),
    (20879, "F1CE0481FA", CIT["F1CE0481FA_HA"]),
    (20887, "F1CE0481FA", CIT["F1CE0481FA_HA"]),
    (20881, "F1CE0481HA", CIT["F1CE0481FA_HA"]),
    (20885, "F1CE0481HA", CIT["F1CE0481FA_HA"]),
]:
    remap_variant(vid, new, why)
# correct the engine row to the real Opel C20LET
cur.execute("""UPDATE engines SET engine_type='2.0 16v Turbo (C20 LET)', fuel='Petrol',
    displacement_cc=1998, power_hp=204, cylinders=4 WHERE engine_code='C20LET'""")
log.append("  C20LET engine row corrected to Opel 2.0 16v Turbo 204hp petrol")
# clear Ford-data specs on C20LET (identity changed; specs pending OEM source)
cur.execute("""UPDATE engine_service_specs SET
    oil_viscosity=NULL, oil_standard=NULL, oil_acea=NULL, oil_oem_spec=NULL,
    oil_capacity_with_filter_l=NULL, oil_capacity_without_filter_l=NULL,
    oil_change_interval_km=NULL, oil_change_interval_months=NULL,
    coolant_type=NULL, coolant_spec=NULL, coolant_capacity_l=NULL,
    oil_spec_source='cleared in Step 11: row previously held mis-attached Ford 1.4 TDCi data (engine identity corrected to Opel C20LET)',
    coolant_source=NULL WHERE engine_code='C20LET'""")
log.append("  C20LET spec row cleared (was Ford 1.4 TDCi data)")

print("=== 2a. NEW ENGINE ROWS (before remaps) ===")
for code, (etype, fuel, cc, hp, cyl, cit) in NEW_ENGINES.items():
    cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,))
    if not cur.fetchone():
        cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
            cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP11_VERIFIED')""",
            (code, etype, fuel, cc, hp, cyl))
        log.append(f"  created engine row {code}: {etype}")

print("=== 2. FIVE PENDINGS (+ Caterham CSR junk codes) ===")
for vid, new, why in [
    (17414, "C20LET", CIT["C20LET"]),
    (16239, "LCBD", CIT["TS250"]),
    (16240, "5.0 Rover V8", CIT["TS500"]),
    (18714, "smart ED (450)", CIT["SMARTED"]),
    (21361, "GW4G15T", CIT["GW4G15T"]),
    (15974, "4G64S4M", CIT["4G64S4M"]),
    (2193, "Duratec 2.3 CSR", CIT["CSR"]),
    (2194, "Duratec 2.3 CSR", CIT["CSR"]),
]:
    remap_variant(vid, new, why)
    set_queue(vid, new, why)

# GW4G15T row was wrong (Diesel/141hp) - real: petrol turbo 133hp
cur.execute("""UPDATE engines SET fuel='Petrol', power_hp=133, displacement_cc=1497,
    engine_type='1.5 16v Turbo (petrol)' WHERE engine_code='GW4G15T'""")
cur.execute("""UPDATE vehicle_variants SET fuel='Petrol', engine_power_hp=133 WHERE id=3631""")
cur.execute("""UPDATE engine_service_specs SET oil_viscosity=NULL, oil_capacity_with_filter_l=NULL,
    oil_spec_source='cleared in Step 11: ESTIMATE was based on wrong fuel (diesel); petrol 1.5T specs pending OEM source'
    WHERE engine_code='GW4G15T'""")
log.append("  GW4G15T row fixed: Petrol, 133hp, 1497cc; variant 3631 fuel/power fixed; bad estimate cleared")

print("=== 4. OEM SPEC FILLS (cited) ===")
def fill_specs(code, fields, source_note):
    sets = ", ".join(f"{k}=?" for k in fields) + ", oil_spec_source=?"
    cur.execute(f"SELECT 1 FROM engine_service_specs WHERE engine_code=?", (code,))
    if not cur.fetchone():
        base = dict(engine_code=code, oil_spec_source=source_note)
        cols = ["engine_code"] + list(fields) + ["oil_spec_source"]
        vals = [code] + list(fields.values()) + [source_note]
        cur.execute(f"""INSERT INTO engine_service_specs (engine_code, {','.join(list(fields))}, oil_spec_source)
                        VALUES (?,?,{','.join('?'*len(fields))})""", (code, *fields.values(), source_note))
    else:
        cur.execute(f"UPDATE engine_service_specs SET {sets} WHERE engine_code=?",
                    (*fields.values(), source_note, code))
    log.append(f"  spec fill {code}: {fields}")

fill_specs("G6DA", {"oil_viscosity": "5W-30", "oil_capacity_with_filter_l": 5.5,
    "oil_oem_spec": "Ford WSS-M2C913-C/D, ACEA A1/B1-A5/B5"},
    f"OEM fill Step 11 (Ford 2.0 TDCi 136hp): {CIT['FORD_TDCI']}")
fill_specs("G6DG", {"oil_viscosity": "5W-30", "oil_capacity_with_filter_l": 5.5,
    "oil_oem_spec": "Ford WSS-M2C913-C/D, ACEA A1/B1-A5/B5"},
    f"OEM fill Step 11 (Ford 2.0 TDCi 136hp): {CIT['FORD_TDCI']}")
fill_specs("G6DA (Hyundai)", {"oil_viscosity": "5W-30", "oil_capacity_with_filter_l": 6.0},
    f"OEM fill Step 11 (Hyundai 3.8 Lambda): {CIT['G6DA_HY']}")
fill_specs("G6DG (Hyundai)", {"oil_viscosity": "5W-30", "oil_capacity_with_filter_l": 6.9},
    f"OEM fill Step 11 (Hyundai 3.0 GDI): {CIT['G6DG_HY']}")
fill_specs("M62B48", {"oil_capacity_with_filter_l": 7.5},
    f"OEM fill Step 11 (Alpina B10 V8/V8S): {CIT['ALPINA']}")
fill_specs("M73B54", {"oil_viscosity": "5W-40", "oil_capacity_with_filter_l": 8.0, "coolant_capacity_l": 15.0},
    f"OEM fill Step 11 (Rolls-Royce Silver Seraph / BMW M73): {CIT['M73B54']}")

# Power Stroke capacity corrections (F22)
cur.execute("""UPDATE engine_service_specs SET oil_capacity_with_filter_l=14.2, oil_capacity_without_filter_l=13.25,
    oil_spec_source=? WHERE engine_code='7.3 Power Stroke'""",
    (f"corrected Step 11 (was 12.87 L): 15 US qt w/filter, ~14 qt w/o: {CIT['PSD']}",))
cur.execute("""UPDATE engine_service_specs SET oil_capacity_with_filter_l=14.2, oil_capacity_without_filter_l=13.25,
    oil_spec_source=? WHERE engine_code='6.0 Power Stroke'""",
    (f"corrected Step 11 (was 16.08 L w/filter / 14.19 w/o - swapped/inflated): 15 US qt w/filter: {CIT['PSD']}",))
cur.execute("""UPDATE engine_service_specs SET coolant_capacity_l=NULL,
    coolant_source='cleared Step 11: 1.41 L physically impossible for 6.7 V8 diesel (parse error in lemon data); pending OEM source'
    WHERE engine_code='6.7 Power Stroke'""")
log.append("  7.3 PSD oil 12.87->14.2 L; 6.0 PSD 16.08->14.2 L (15 qt, cited); 6.7 PSD coolant 1.41 L cleared (impossible)")

print("=== 5. COSMETIC ENGINE_TYPE CLEANUP ===")
JUNK_RE = re.compile(r"\(est\.\)|\(corr\.\)|,|^Repair |^Retrofit |without SA")
# engine-table etypes that are actually car-model/body-style strings (bad source join)
BODY_RE = re.compile(r"Closed Off-Road|Off-Road|Saloon|Roadster| MPV| Bus| Wagon|Hatchback|Convertible|Coupé|Coupe\)| Estate")

def parse_cc(text):
    nums = [int(float(x) * 1000) for x in re.findall(r"\d\.\d(?![\d])", text)]
    nums += [int(x) for x in re.findall(r"(?<![\d.])\d{4}(?![\d.])", text)]
    return [n for n in nums if 900 <= n <= 9000]

def etype_clean(t, eng_cc=None):
    """Engine-table etype usable as replacement: no junk/body-style words, sane length,
    and any displacement it mentions must agree with the engine's own cc."""
    if not t or JUNK_RE.search(t) or BODY_RE.search(t) or len(t) > 35:
        return False
    if eng_cc:
        nums = parse_cc(t)
        if any(abs(n - eng_cc) / eng_cc > 0.12 for n in nums):
            return False
    return True

# 5a. engine rows whose etype is a car-model/body-style string -> derive honest label
fixed_eng = 0
eng_meta = {}
for ecode, etype, cc, fuel, cyl in list(cur.execute(
        "SELECT engine_code, engine_type, displacement_cc, fuel, cylinders FROM engines")):
    if etype and BODY_RE.search(etype):
        t = f"{cc/1000:.1f} {fuel}" if cc else fuel
        cur.execute("UPDATE engines SET engine_type=? WHERE engine_code=?", (t, ecode))
        log.append(f"  engine row {ecode}: junk etype '{etype}' -> '{t}' (derived from own cc/fuel/cyl columns)")
        fixed_eng += 1
        eng_meta[ecode] = (t, cc)
    else:
        eng_meta[ecode] = (etype, cc)

fixed_pattern = fixed_spoof = 0
rows = list(cur.execute("SELECT id, engine_type, engine_code FROM vehicle_variants WHERE engine_type IS NOT NULL"))
for vid, etype, ecode in rows:
    replace = None
    if JUNK_RE.search(etype or "") or len(etype or "") > 35:
        replace = "pattern"; fixed_pattern += 1
    elif ecode and ecode in eng_meta:
        cc = eng_meta[ecode][1]
        if cc:
            nums = parse_cc(etype)
            if any(abs(n - cc) / cc > 0.12 for n in nums):
                replace = "spoof"; fixed_spoof += 1
    if replace:
        # propagate engine-table etype ONLY if it is itself clean & self-consistent; else NULL
        new_t = None
        if ecode in eng_meta:
            e_t, e_cc = eng_meta[ecode]
            if etype_clean(e_t, e_cc):
                new_t = e_t
        cur.execute("UPDATE vehicle_variants SET engine_type=? WHERE id=?", (new_t, vid))
        bm = cur.execute("SELECT car_brand, car_model FROM vehicle_variants WHERE id=?", (vid,)).fetchone() or ("", "")
        dec_rows.append([vid, bm[0], bm[1], "engine_type-" + replace, etype, new_t or "NULL",
                         "DB-internal consistency (etype vs linked engine cc)"])
log.append(f"  etype cleaned: {fixed_pattern} junk-pattern rows, {fixed_spoof} displacement-spoof rows, {fixed_eng} engine-row junk etypes")

print()
for line in log:
    print(line)

if not APPLY:
    print("\nDRY RUN - no changes. Re-run with --apply.")
    con.rollback(); con.close(); sys.exit(0)

bak = f"database_enriched/backups/car_database_backup_pre_step11_{date.today().isoformat()}.db"
shutil.copy(DB, bak)
con.commit()
print(f"\nbackup: {bak}")

print("\n=== VERIFY ===")
print("orphan variant->engine refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v
    LEFT JOIN engines e ON e.engine_code=v.engine_code WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0], "(0 expected - M73B54 now exists)")
print("garbled rows gone:", cur.execute("SELECT COUNT(*) FROM engines WHERE engine_code IN ('M54256S5','G4KR','H4KR','25V6S1','2.3 16v 5MT','2.3 16v 6MT')").fetchone()[0], "(0 expected)")
print("C20LET:", cur.execute("SELECT engine_code, engine_type, fuel, displacement_cc, power_hp, count_variants FROM engines WHERE engine_code='C20LET'").fetchone())
print("M73B54:", cur.execute("SELECT engine_code, engine_type, displacement_cc, power_hp, cylinders, count_variants FROM engines WHERE engine_code='M73B54'").fetchone())
print("queue pending now:", cur.execute("SELECT COUNT(*) FROM remapping_queue WHERE status='pending'").fetchone()[0])
print("remaining junk-pattern etypes:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_type IS NOT NULL AND (engine_type LIKE '%(est.%' OR engine_type LIKE '%(corr.%' OR length(engine_type)>35 OR engine_type LIKE '%,%')").fetchone()[0])
with open("database_enriched/csv_exports/19_small_cleanups_log.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["entry"]); [w.writerow([l]) for l in log]
with open("database_enriched/csv_exports/19_small_cleanups_decisions.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["variant_id", "brand", "model", "field", "old", "new", "evidence"])
    for r in dec_rows:
        w.writerow([("" if c is None else c) for c in r])
con.close()
