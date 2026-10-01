"""Step 20 (user-plan Step 5, batch 11): replace LEMON_HYUNDAI codes with real OEM engine codes.
391 rows, 23 models. Signals: cc + lemon fuel column (Sonata 2016+ 2000cc = Hybrid; Ioniq 2022+ = EV)
+ trim slugs. Heavy reuse of DB G-family + rows created in batches 5-10 (G4NB/G4NH/Na, Lambda/Tau,
G6DP-family, G4KK/G4NE, Smartstream HEV, Kappa HEV).
New: G4LD (1.4T Eco), Sigma 3.0 (XG300), Lambda II 3.8 GDI (Genesis Coupe), Ioniq Electric."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "TUCSON2020": "https://www.hyundainews.com/assets/documents/original/39952-2020TucsonProductGuidespecs010820pptx.pdf (US Tucson TL: Nu 2.0 GDI 161-164hp SE/Value + Theta 2.4 GDI 181hp SEL+; 1.6T 177hp Eco/Sport)",
    "TUCSONAE": "https://www.autoevolution.com/cars/hyundai-tucson-2018.html (Tucson 2018-2020 engine list: 2.0 164hp, 2.4 181hp, 1.6T 177hp)",
    "WIKIBOOKS": "https://en.wikibooks.org/wiki/Vehicle_Identification_Numbers_(VIN_codes)/KIA/VIN_Codes (engine-code cross-reference)",
    "GOPARTS_NH": "https://www.go-parts.com/garage/hyundai-kia-nu-engine-family-smartstream-g2-0-nu-mpi-atkinson-kia-soul-kia-forte-kia-k4-2019-2026 (G4NH = Nu 2.0 MPi Atkinson 147hp family)",
    "DBLINKS": "DB engine links (G4GC/G6BA=Hyundai Coupe/Santa Fe, G4ED/G4FD=Accent, G4JS=SORENTO I Sirius, G6CU=XG 3.5 Sigma, G6BV=Magentis/Sonata 2.5 Sigma, G4NC=i40/ix35 Nu 2.0 GDI, G4FJ=Veloster/Tucson 1.6T)",
}

NEW_ENGINES = {
    "G4LD": ("1.4 I4 T-GDI Kappa (Elantra Eco, 128hp)", "Petrol", 1368, 128, 4),
    "Sigma 3.0 V6 (XG300)": ("3.0 V6 Sigma (XG300, 192hp)", "Petrol", 2972, 192, 6),
    "Lambda II 3.8 GDI (Genesis Coupe)": ("3.8 V6 Lambda II GDI (Genesis Coupe, 306-348hp)", "Petrol", 3778, 348, 6),
    "Ioniq Electric": ("Electric motors (Ioniq 5: 168-320hp; Ioniq 6)", "Electric", None, 168, None),
}

ROW_FIXES = {
    "G6DB": {"engine_type": "3.3 V6 Lambda MPi (Azera/Sonata/Santa Fe, 234-249hp)"},
    "Tau 4.6 MPi (Borrego)": {"engine_type": "4.6 V8 Tau MPi (Borrego/Equus/Genesis, 361-385hp)"},
    "Kappa 1.6 GDI Hybrid (Niro)": {"engine_type": "1.6 I4 GDI + motor HEV (Niro/Ioniq, system 139hp)"},
    "Smartstream 1.6 T-GDI Hybrid (Sorento/Sportage/Carnival)": {"engine_type": "1.6 I4 T-GDI + motor HEV (Sorento/Sportage/Carnival/Santa Fe, system 227-242hp)"},
    "Lambda II 3.5 GDI (Sorento/Carnival/Sedona)": {"engine_type": "3.5 V6 Lambda II GDI (Sorento/Carnival/Sedona/Santa Fe, 266-290hp)"},
}

FUEL_FIX_BY_TARGET = {"Ioniq Electric": "Electric"}

# (MODEL-upper, y0, y1, cc, target, evidence[, fuel_fix])  cc=None = bare/slug
R = [
    ("ACCENT", 2000, 2002, 1500, "G4EB", "Accent 1.5 Alpha SOHC (92hp US) [DB family]"),
    ("ACCENT", 2001, 2002, 1600, "G4ED", "Accent 1.6 Alpha DOHC (non-US/Canada) [DB family, links Accent]"),
    ("ACCENT", 2000, 2002, None, "G4EB", "Accent 1.5 only US [DB family]"),
    ("ACCENT", 2003, 2011, None, "G4ED", "Accent 1.6 Alpha 104-110hp [DB family]"),
    ("ACCENT", 2012, 2017, None, "G4FD", "Accent 1.6 GDI 138hp (incl. 2015 trims) [DB family]"),
    ("ACCENT", 2018, 2022, None, "G4FD", "Accent 1.6 GDI 130hp (Smartstream; note US 130) [DB family]"),
    ("AZERA", 2006, 2006, None, "Lambda 3.8 MPi (G6DA-family)", "Azera 3.8 Lambda 263hp launch [DB family]"),
    ("AZERA", 2007, 2011, 3300, "G6DB", "Azera 3.3 Lambda MPi 234-249hp [ROW_FIX G6DB]"),
    ("AZERA", 2007, 2011, 3800, "Lambda 3.8 MPi (G6DA-family)", "Azera 3.8 Lambda 260-265hp [DB family]"),
    ("AZERA", 2012, 2014, None, "Lambda 3.3 GDI (Cadenza/Sedona/Sorento)", "Azera HG 3.3 GDI 293hp only [DB family]"),
    ("AZERA", 2015, 2017, None, "Lambda 3.3 GDI (Cadenza/Sedona/Sorento)", "Azera 3.3 GDI 293hp (incl. 2015 trims) [DB family]"),
    ("ELANTRA", 2000, 2010, None, "G4GC", "Elantra XD/HD 2.0 Beta 138-140hp US [DB family]"),
    ("ELANTRA", 2011, 2016, None, "G4NB", "Elantra MD 1.8 Nu 148hp [DB family G4NB]"),
    ("ELANTRA", 2017, 2025, None, "G4NH", "Elantra base 2.0 MPi 147hp majority (1.6T/1.4T minority) [GOPARTS_NH]"),
    ("ELANTRA", 2017, 2020, 1400, "G4LD", "Elantra Eco 1.4T 128hp [NEW G4LD]"),
    ("ELANTRA", 2017, 2025, 1600, "G4FJ", "Elantra GT/Sport/N Line 1.6T 161-201hp [DB family]"),
    ("ELANTRA", 2017, 2025, 2000, "G4NH", "Elantra 2.0 MPi 147hp (Nu; G4NH-family) [GOPARTS_NH]"),
    ("ENTOURAGE", 2007, 2009, None, "Lambda 3.8 MPi (G6DA-family)", "Entourage 3.8 Lambda 260-265hp [DB family]"),
    ("EQUUS", 2011, 2011, None, "Tau 4.6 MPi (Borrego)", "Equus 2011 4.6 Tau 385hp only [ROW_FIX label]"),
    ("EQUUS", 2012, 2016, None, "Tau 5.0 GDI (K900/Equus)", "Equus 5.0 Tau GDI 429hp [DB family]"),
    ("GENESIS", 2009, 2009, 3800, "Lambda 3.8 MPi (G6DA-family)", "Genesis sedan 3.8 MPi 290-306hp (no coupe yet) [DB family]"),
    ("GENESIS", 2009, 2016, 4600, "Tau 4.6 MPi (Borrego)", "Genesis sedan 4.6 Tau 375-385hp [ROW_FIX label]"),
    ("GENESIS", 2012, 2016, 5000, "Tau 5.0 GDI (K900/Equus)", "Genesis sedan 5.0 Tau GDI 429hp [DB family]"),
    ("GENESIS", 2010, 2016, 2000, "G4KF", "Genesis Coupe 2.0T 210-274hp (sedan never 2.0T) [DB family]"),
    ("GENESIS", 2015, 2015, None, "Lambda 3.8 MPi (G6DA-family)", "Genesis sedan 3.8 (2015 non-coupe) [DB family]"),
    ("GENESIS", 2015, 2015, 3800, "Lambda 3.8 MPi (G6DA-family)", "Genesis sedan 3.8 2015 (coupe has own slug) [DB family]"),
    ("GENESIS", 2016, 2016, 3800, "Lambda 3.8 MPi (G6DA-family)", "Genesis sedan 3.8 (coupe discontinued) [DB family]"),
    ("IONIQ", 2017, 2021, None, "Kappa 1.6 GDI Hybrid (Niro)", "Ioniq HEV 1.6 GDI 139hp system (EV/PHEV minority) [ROW_FIX label]"),
    ("IONIQ", 2022, 2025, None, "Ioniq Electric", "Ioniq 5/6 EV only from 2022 [NEW][fuel fix]", "Electric"),
    ("KONA", 2018, 2025, 1600, "G4FJ", "Kona 1.6T 175-195hp [DB family]"),
    ("KONA", 2018, 2025, 2000, "G4NH", "Kona 2.0 MPi 147hp (Nu) [GOPARTS_NH]"),
    ("KONA", 2019, 2024, None, "G4NH", "Kona gas 2.0 majority (1.6T/EV minority) [GOPARTS_NH]"),
    ("KONA", 2025, 2025, None, "G4NH", "2025 Kona 2.0 only US (1.6T dropped) [GOPARTS_NH]"),
    ("PALISADE", 2020, 2025, None, "Lambda 3.8 GDI (Telluride/Palisade)", "Palisade 3.8 GDI 291hp only [DB family]"),
    ("SANTA", 2001, 2006, 2400, "G4JS", "Santa Fe 2.4 Sirius 138-145hp [DB family]"),
    ("SANTA", 2001, 2009, 2700, "G6BA", "Santa Fe 2.7 Delta 170-185hp [DB family]"),
    ("SANTA", 2003, 2006, 3500, "G6CU", "Santa Fe 3.5 Sigma 194hp [DB family]"),
    ("SANTA", 2007, 2009, 3300, "G6DB", "Santa Fe 3.3 Lambda MPi 242hp [ROW_FIX G6DB]"),
    ("SANTA", 2010, 2010, 2400, "G4KC", "Santa Fe 2.4 Theta MPi 175hp [DB family]"),
    ("SANTA", 2011, 2012, 2400, "G4KJ", "Santa Fe 2.4 Theta GDI 190hp (VIN B) [DB family]"),
    ("SANTA", 2010, 2012, 3500, "Lambda II 3.5 GDI (Sorento/Carnival/Sedona)", "Santa Fe 3.5 Lambda II GDI 276hp (VIN G) [ROW_FIX label]"),
    ("SANTA", 2013, 2020, 2000, "G4KF", "Santa Fe Sport 2.0T 240-264hp (VIN A) [DB family]"),
    ("SANTA", 2013, 2020, 2400, "G4KJ", "Santa Fe Sport 2.4 GDI 190hp (VIN D) [DB family]"),
    ("SANTA", 2013, 2019, None, "G4KJ", "Santa Fe Sport 2.4 GDI majority (2.0T / 3.3 XL minority) [DB family]"),
    ("SANTA", 2022, 2025, None, "G4KN", "Santa Fe 2.5 GDI majority (1.6T HEV / 2.5T minority) [DB family]"),
    ("SANTA", 2021, 2025, 1600, "Smartstream 1.6 T-GDI Hybrid (Sorento/Sportage/Carnival)", "Santa Fe Hybrid 1.6T 226-232hp system [ROW_FIX label]"),
    ("SANTA", 2021, 2025, 2500, "G4KN", "Santa Fe 2.5 GDI 191hp (2.5T 277hp minority) [DB family]"),
    ("SONATA", 2000, 2001, 2500, "G6BV", "Sonata EF 2.5 Sigma V6 168-170hp [DB family]"),
    ("SONATA", 2000, 2005, 2400, "G4JS", "Sonata EF 2.4 Sirius 138-149hp [DB family]"),
    ("SONATA", 2002, 2005, 2700, "G6BA", "Sonata 2.7 Delta 170-181hp [DB family]"),
    ("SONATA", 2006, 2010, 2400, "G4KC", "Sonata NF 2.4 Theta MPi 162-175hp [DB family]"),
    ("SONATA", 2006, 2010, 3300, "G6DB", "Sonata NF 3.3 Lambda MPi 234-249hp [ROW_FIX G6DB]"),
    ("SONATA", 2011, 2011, None, "G4KJ", "Sonata YF 2.4 GDI 198hp majority (2.0T minority) [DB family]"),
    ("SONATA", 2012, 2012, None, "G4KJ", "Sonata YF 2.4 GDI majority (2.0T minority) [DB family]"),
    ("SONATA", 2012, 2014, 2000, "G4KF", "Sonata 2.0T 274hp (VIN B) [DB family]"),
    ("SONATA", 2012, 2014, 2400, "G4KJ", "Sonata 2.4 GDI (VIN C) [DB family]"),
    ("SONATA", 2015, 2015, 2000, "G4KF", "Sonata Sport 2.0T 245hp [DB family]"),
    ("SONATA", 2015, 2016, 2400, "G4KJ", "Sonata 2.4 GDI [DB family]"),
    ("SONATA", 2015, 2019, 1600, "G4FJ", "Sonata Eco 1.6T 178hp [DB family]"),
    ("SONATA", 2017, 2019, 2400, "G4KJ", "Sonata 2.4 GDI (VIN C era) [DB family]"),
    ("SONATA", 2016, 2025, 2000, "G4NE", "Sonata Hybrid 2.0 GDI HEV 192-193hp system (VIN 1/3; 2015-2025 hybrid era) [DB family G4NE]"),
    ("SONATA", 2020, 2025, 1600, "G4FJ", "Sonata 1.6T 180hp (SE/SEL) [DB family]"),
    ("SONATA", 2020, 2025, 2500, "G4KN", "Sonata 2.5 GDI 191hp (2.5T N Line 290hp minority) [DB family]"),
    ("TIBURON", 2000, 2008, 2000, "G4GC", "Tiburon 2.0 Beta 138-140hp [DB family, links Coupe]"),
    ("TIBURON", 2003, 2008, 2700, "G6BA", "Tiburon 2.7 Delta 167-172hp [DB family, links Coupe]"),
    ("TIBURON", 2000, 2001, None, "G4GC", "Tiburon 2.0 only (pre-2003) [DB family]"),
    ("TUCSON", 2005, 2009, 2000, "G4GC", "Tucson 2.0 Beta 140-141hp [DB family]"),
    ("TUCSON", 2005, 2009, 2700, "G6BA", "Tucson 2.7 Delta 173-184hp [DB family]"),
    ("TUCSON", 2010, 2010, None, "G4KC", "2010 Tucson 2.4 MPi 176hp only (LM launch) [DB family]"),
    ("TUCSON", 2011, 2015, 2000, "G4NC", "Tucson 2.0 Nu GDI 164hp [DB family]"),
    ("TUCSON", 2011, 2011, 2400, "G4KC", "Tucson 2.4 MPi 176hp [DB family]"),
    ("TUCSON", 2012, 2015, 2400, "G4KJ", "Tucson 2.4 GDI 181hp [DB family]"),
    ("TUCSON", 2016, 2018, 1600, "G4FJ", "Tucson Eco/Sport 1.6T 175-186hp [DB family]"),
    ("TUCSON", 2016, 2021, 2000, "G4NC", "Tucson SE/Value 2.0 Nu GDI 161-164hp [TUCSON2020]"),
    ("TUCSON", 2018, 2021, 2400, "G4KJ", "Tucson SEL+ 2.4 Theta GDI 181hp [TUCSON2020]"),
    ("TUCSON", 2022, 2025, 1600, "G4FJ", "Tucson NX4 1.6T 180hp [DB family]"),
    ("TUCSON", 2022, 2022, 2500, "G4KN", "Tucson NX4 2.5 GDI (rare/US-non-standard row) [DB family]"),
    ("VELOSTER", 2012, 2014, None, "G4FD", "Veloster 1.6 GDI 138hp base (Turbo minority) [DB family]"),
    ("VELOSTER", 2012, 2017, None, "G4FD", "Veloster 1.6 GDI base majority (Turbo minority) [DB family]"),
    ("VELOSTER", 2019, 2022, None, "G4NH", "Veloster base 2.0 MPi 147hp majority (1.6T / N 2.0T minority) [GOPARTS_NH]"),
    ("VELOSTER", 2019, 2021, 1600, "G4FJ", "Veloster Turbo 1.6T 201hp [DB family]"),
    ("VELOSTER", 2019, 2021, 2000, "G4NH", "Veloster base 2.0 MPi 147hp (N 2.0T 250-275hp minority) [GOPARTS_NH]"),
    ("VENUE", 2020, 2025, None, "G4FG", "Venue 1.6 MPi 121hp (Gamma II) [DB family]"),
    ("VERACRUZ", 2007, 2012, None, "Lambda 3.8 MPi (G6DA-family)", "Veracruz 3.8 Lambda 260-265hp [DB family]"),
    ("XG300", 2001, 2001, None, "Sigma 3.0 V6 (XG300)", "XG300 3.0 Sigma 192hp [NEW]"),
    ("XG350", 2002, 2005, None, "G6CU", "XG350 3.5 Sigma 194hp [DB family, links XG]"),
]

def decide(model, year, code, fuel):
    parts = code.replace("LEMON_HYUNDAI_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc = None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
    mu = model.upper()
    up = code.upper()
    # trim-slug special cases
    if mu == "ELANTRA":
        if "GT" in up and "GTAUT" in up or "GTST" in up:
            return ("G4NC", "Elantra GT 2.0 GDI 173hp [DB family]", None)
        if "LIMIT" in up: return ("G4NB", "Elantra Limited 1.8 [DB family G4NB]", None)
        if "SEAUT" in up or "SESTA" in up: return ("G4NB", "Elantra SE 1.8 [DB family G4NB]", None)
        if "SPORT" in up: return ("G4NC", "Elantra Sport 2.0 GDI 173hp [DB family]", None)
    if mu == "VELOSTER" and "TURB" in up:
        return ("G4FJ", "Veloster Turbo 1.6T 201hp [DB family]", None)
    if mu == "VELOSTER" and ("BASE" in up or "REFL" in up):
        return ("G4FD", "Veloster 1.6 GDI base [DB family]", None)
    if mu == "AZERA" and ("BASE" in up or "LIMIT" in up):
        return ("Lambda 3.3 GDI (Cadenza/Sedona/Sorento)", "Azera 3.3 GDI 293hp [DB family]", None)
    if mu == "EQUUS" and ("SIGNATU" in up or "ULTIMAT" in up):
        return ("Tau 5.0 GDI (K900/Equus)", "Equus 5.0 Tau 429hp [DB family]", None)
    if mu == "GENESIS" and "COUPE" in up:
        return ("Lambda II 3.8 GDI (Genesis Coupe)", "Genesis Coupe 3.8 GDI 348hp [NEW]", None)
    if mu == "SANTA" and "SANTAFE" in up:
        return ("G4KJ", "Santa Fe 2.4 GDI 190hp (GLS/Limited trims) [DB family]", None)
    # Genesis 3.8 2010-2014: sedan MPi vs coupe GDI ambiguous
    if mu == "GENESIS" and cc == 3800 and 2010 <= year <= 2014:
        return (None, "Genesis 3.8 2010-2014: sedan MPi vs Coupe GDI unknown", None)
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands:
        if cc is not None:
            return (None, f"{model} {year} {cc}cc: no rule", None)
        return (None, f"no rule for {model} {year} (bare)", None)
    r = cands[0]
    fuel_fix = r[6] if len(r) > 6 else FUEL_FIX_BY_TARGET.get(r[4])
    return (r[4], r[5], fuel_fix)

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    # baseline guard
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == 5331, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 5331 (workspace rewind?)"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Hyundai' AND engine_code LIKE 'LEMON_HYUNDAI%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        tgt, note, fuel_fix = decide(model, year, code, fuel)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"Hyundai LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(16): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter(d[6] for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"

    if not apply:
        with open("database_enriched/csv_exports/28_lemon_batch11_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"Hyundai",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Hyundai",s[1],s[2],"","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step20_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP20_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
            print(f"  created {code}")
    for code, fixes in ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  row-fix {code}")

    lemon_retired = defaultdict(list)
    for vid, model, year, old, new, note, fuel_fix in decisions:
        cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=COALESCE(?, fuel) WHERE id=?", (new, fuel_fix, vid))
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=COALESCE(engine_power_hp,
            (SELECT power_hp FROM engines WHERE engine_code=?)),
            engine_type=COALESCE(engine_type, (SELECT engine_type FROM engines WHERE engine_code=?)) WHERE id=?""", (new, new, vid))
        lemon_retired[old].append((vid, year, model))

    spec_cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_service_specs)")]
    tech_cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_technical_specs)")]

    def merge_specs(table, cols, lc, target):
        cols = [c for c in cols if c != "engine_code"]
        cur.execute(f"SELECT {','.join(cols)} FROM {table} WHERE engine_code=?", (lc,))
        src = cur.fetchone()
        if src is None: return
        if table == "engine_service_specs":
            srow = cur.execute("SELECT oil_spec_source FROM engine_service_specs WHERE engine_code=?", (lc,)).fetchone()
            if srow and srow[0] and "ESTIMATE" in srow[0].upper():
                cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (lc,)); return
        if cur.execute(f"SELECT 1 FROM {table} WHERE engine_code=?", (target,)).fetchone():
            sets = ", ".join(f"{c}=COALESCE({c}, ?)" for c in cols)
            cur.execute(f"UPDATE {table} SET {sets} WHERE engine_code=?", (*src, target))
        else:
            cur.execute(f"INSERT INTO {table} (engine_code, {','.join(cols)}) VALUES (?{',?'*len(cols)})", (target, *src))

    for lc, vids in lemon_retired.items():
        tgt = cur.execute("SELECT engine_code FROM vehicle_variants WHERE id=?", (vids[0][0],)).fetchone()[0]
        merge_specs("engine_service_specs", spec_cols, lc, tgt)
        merge_specs("engine_technical_specs", tech_cols, lc, tgt)
        cur.execute("DELETE FROM engine_service_specs WHERE engine_code=?", (lc,))
        cur.execute("DELETE FROM engine_technical_specs WHERE engine_code=?", (lc,))
        cur.execute("DELETE FROM engines WHERE engine_code=?", (lc,))

    cur.execute("""UPDATE engines SET count_variants =
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")

    with open("database_enriched/csv_exports/28_lemon_batch11_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"Hyundai",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_HYUNDAI remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_HYUNDAI%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
