"""Step 19 (user-plan Step 5, batch 10): replace LEMON_KIA codes with real OEM engine codes.
392 rows, 32 models. Signals: cc + lemon fuel column (Optima hybrids = G4KK 2.4 / G4NE 2.0) + slugs.
DB G-codes reused (G6AU/G6CU/G6BV/G6EA/G4JS/G4KC/G4KJ/G4KD/G4KE/G4KF/G4GJ?/G4GC/G4GB/G4ED/G4FD/G4FC/G4FJ/G6DJ/G4CP/G4NE).
G6DA is a Ford TDCi code in this DB -> Lambda 3.8 MPi gets a separate descriptive row.
New: G4NH/G4NA/G4NB/G4KK/G6DP/Smartstream 2.5T/1.6T-HEV/Niro HEV/Lambda 3.8-3.5-3.3 rows/Tau 4.6-5.0/EVs."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "WIKIBOOKS": "https://en.wikibooks.org/wiki/Vehicle_Identification_Numbers_(VIN_codes)/KIA/VIN_Codes (G4KJ=Optima 2.4 GDI 11-15; G4KK=Optima Hybrid 2.4 11-16; G4NH=Forte 17-18/Soul 20-25 2.0; Rio 01-02 1.5=B5-DE; Sportage 95-02 2.0=FE)",
    "GOPARTS_NH": "https://www.go-parts.com/garage/hyundai-kia-nu-engine-family-smartstream-g2-0-nu-mpi-atkinson-kia-soul-kia-forte-kia-k4-2019-2026 (G4NH = Forte/K4/Seltos/Soul 2.0 MPi Atkinson 147hp)",
    "MOTORREVIEWER": "https://www.motorreviewer.com/engine.php?engine_id=141 (G6DH = 3.3 GDI NA; G6DP = 3.3 T-GDI twin-turbo Stinger/Genesis)",
    "GOPARTS_DP": "https://www.go-parts.com/garage/hyundai-kia-lambda-ii-t-gdi-engine-genesis-g80-genesis-g70-kia-stinger-2017-2023 (G6DP = 3.3TT 365hp Stinger/G70/G80/G90 2017-2023)",
    "EBAY_G4NA": "https://www.ebay.com/b/Complete-Engines-for-Kia-Soul/33615/bn_1419823 (G4NA = Soul/Forte 2.0 14-19; G4NH = Soul 20-22)",
    "DBLINKS": "DB engine links (G6AU=Opirus/Sorento, G6CU=Carnival II, G6BV=Magentis 2.5, G6EA=Magentis MG/Rondo, G4NE=Optima Hybrid 2.0, G6DJ=Genesis 3.8 GDI, G4CP=Joice FE 2.0)",
}

NEW_ENGINES = {
    "Lambda 3.8 MPi (G6DA-family)": ("3.8 V6 Lambda MPi (Sedona/Amanti/Sorento/Borrego, 244-275hp)", "Petrol", 3778, 262, 6),
    "Lambda II 3.5 GDI (Sorento/Carnival/Sedona)": ("3.5 V6 Lambda II GDI (Sorento/Sedona/Carnival, 266-290hp)", "Petrol", 3470, 276, 6),
    "Lambda 3.3 GDI (Cadenza/Sedona/Sorento)": ("3.3 V6 Lambda II GDI (Cadenza/Sedona/Sorento, 276-293hp)", "Petrol", 3342, 276, 6),
    "Lambda 3.8 GDI (Telluride/Palisade)": ("3.8 V6 Lambda II GDI (Telluride/Palisade, 291hp)", "Petrol", 3778, 291, 6),
    "Tau 4.6 MPi (Borrego)": ("4.6 V8 Tau MPi (Borrego, 361hp)", "Petrol", 4627, 361, 8),
    "Tau 5.0 GDI (K900/Equus)": ("5.0 V8 Tau GDI (K900/Equus, 420hp)", "Petrol", 5038, 420, 8),
    "G6DP": ("3.3 V6 Lambda II T-GDI (Stinger/K900/Genesis, 365hp)", "Petrol", 3342, 365, 6),
    "Smartstream 2.5 T-GDI (K5/Stinger GT)": ("2.5 I4 Turbo (K5 GT 290hp / Stinger GT 300hp)", "Petrol", 2497, 290, 4),
    "Smartstream 1.6 T-GDI Hybrid (Sorento/Sportage/Carnival)": ("1.6 I4 T-GDI + motor HEV (system 227-242hp)", "Hybrid", 1598, 227, 4),
    "Kappa 1.6 GDI Hybrid (Niro)": ("1.6 I4 GDI + motor HEV (system 139hp)", "Hybrid", 1580, 139, 4),
    "G4NB": ("1.8 I4 Nu MPi (Forte LX 145-148hp)", "Petrol", 1799, 147, 4),
    "G4NA": ("2.0 I4 Nu MPi (Soul/Forte 164hp)", "Petrol", 1999, 164, 4),
    "G4NH": ("2.0 I4 Nu MPi Atkinson (Forte/K4/Seltos/Soul, 147hp)", "Petrol", 1999, 147, 4),
    "G4KK": ("2.4 I4 Theta II GDI + motor HEV (Optima Hybrid 11-16, system 199-206hp)", "Hybrid", 2359, 199, 4),
    "1.5 DOHC (B5-family, Rio)": ("1.5 I4 DOHC (Rio 01-05, 105hp)", "Petrol", 1495, 105, 4),
    "Soul EV Electric": ("Electric motor (Soul EV, 109hp)", "Electric", None, 109, None),
    "EV6 Electric": ("Electric motors (EV6 RWD 225hp / AWD 320hp / GT 576hp)", "Electric", None, 225, None),
    "EV9 Electric": ("Electric motors (EV9 RWD 215hp / AWD 379hp)", "Electric", None, 215, None),
}

ROW_FIXES = {
    "G4KN": {"engine_type": "2.5 I4 GDI Smartstream (K5/Sportage/Tucson, 187-194hp)", "power_hp": 194},
    "G4NE": {"engine_type": "2.0 I4 GDI + motor HEV (Optima Hybrid 17-20, system 192hp)", "power_hp": 192},
    "G6EA": {"engine_type": "2.7 V6 Delta (Optima/Rondo/Sportage, 165-185hp)"},
}

FUEL_FIX_BY_TARGET = {
    "Smartstream 1.6 T-GDI Hybrid (Sorento/Sportage/Carnival)": "Hybrid",
    "Kappa 1.6 GDI Hybrid (Niro)": "Hybrid", "G4KK": "Hybrid", "G4NE": "Hybrid",
    "Soul EV Electric": "Electric", "EV6 Electric": "Electric", "EV9 Electric": "Electric",
}

# (MODEL-upper, y0, y1, cc, target, evidence[, fuel_fix])  cc=None = bare/slug
R = [
    ("AMANTI", 2004, 2006, None, "G6AU", "Amanti/Opirus 3.5 Sigma 192-200hp [DBLINKS]"),
    ("AMANTI", 2007, 2009, None, "Lambda 3.8 MPi (G6DA-family)", "Amanti 3.8 Lambda 263hp [NEW]"),
    ("BORREGO", 2009, 2009, 3800, "Lambda 3.8 MPi (G6DA-family)", "Borrego 3.8 275hp [NEW]"),
    ("BORREGO", 2009, 2009, 4600, "Tau 4.6 MPi (Borrego)", "Borrego 4.6 Tau 361hp [NEW]"),
    ("CADENZA", 2014, 2020, None, "Lambda 3.3 GDI (Cadenza/Sedona/Sorento)", "Cadenza 3.3 GDI 290-293hp [MOTORREVIEWER G6DH-family][NEW]"),
    ("CARNIVAL", 2022, 2024, None, "Lambda II 3.5 GDI (Sorento/Carnival/Sedona)", "Carnival 3.5 GDI 290hp only [NEW]"),
    ("CARNIVAL", 2025, 2025, 1600, "Smartstream 1.6 T-GDI Hybrid (Sorento/Sportage/Carnival)", "Carnival Hybrid 1.6T 242hp system [NEW]", "Hybrid"),
    ("CARNIVAL", 2025, 2025, 3500, "Lambda II 3.5 GDI (Sorento/Carnival/Sedona)", "Carnival 3.5 GDI [NEW]"),
    ("EV6", 2022, 2024, None, "EV6 Electric", "EV6 EV only [NEW]", "Electric"),
    ("EV9", 2024, 2025, None, "EV9 Electric", "EV9 EV only [NEW]", "Electric"),
    ("FORTE", 2010, 2013, 2000, "G4KD", "Forte 2.0 Theta 156hp [DB family]"),
    ("FORTE", 2010, 2013, 2400, "G4KE", "Forte SX 2.4 173-176hp [DB family]"),
    ("FORTE", 2017, 2019, None, "G4NH", "Forte 2.0 MPi 147hp only (1.8 dropped 2017) [WIKIBOOKS][GOPARTS_NH][NEW]"),
    ("FORTE", 2020, 2024, 1600, "G4FJ", "Forte GT 1.6T 201hp [DB family]"),
    ("FORTE", 2020, 2024, 2000, "G4NH", "Forte 2.0 MPi 147hp [GOPARTS_NH][NEW]"),
    ("FORTE5", 2014, 2018, None, None, "Forte5: EX 2.0 vs SX 1.6T unknown"),
    ("K4", 2025, 2025, 1600, "G4FJ", "K4 GT 1.6T 180hp [GOPARTS family]"),
    ("K4", 2025, 2025, 2000, "G4NH", "K4 2.0 MPi 147hp [GOPARTS_NH]"),
    ("K5", 2021, 2025, 1600, "G4FJ", "K5 1.6T 180hp [DB family]"),
    ("K5", 2021, 2023, 2500, "G4KN", "K5 2.5 GDI 194hp [ROW_FIX G4KN]"),
    ("K5", 2024, 2025, 2500, "Smartstream 2.5 T-GDI (K5/Stinger GT)", "2024+ K5 GT 2.5T 290hp (2.5 NA dropped) [NEW]"),
    ("K900", 2015, 2017, 3800, "G6DJ", "K900 3.8 GDI 311hp US (DB G6DJ 335 Euro) [DB family]"),
    ("K900", 2015, 2017, 5000, "Tau 5.0 GDI (K900/Equus)", "K900 5.0 Tau 420hp [NEW]"),
    ("K900", 2019, 2020, None, "G6DP", "K900 2019+ 3.3TT 365hp only US [GOPARTS_DP][NEW]"),
    ("NIRO", 2017, 2025, None, "Kappa 1.6 GDI Hybrid (Niro)", "Niro 1.6 GDI HEV 139hp system (EV/PHEV minority noted) [NEW]", "Hybrid"),
    ("OPTIMA", 2002, 2005, 2400, "G4JS", "Optima 2.4 Sirius 138hp [DB family]"),
    ("OPTIMA", 2006, 2010, 2400, "G4KC", "Optima 2.4 Theta MPi 161-175hp [DB family]"),
    ("OPTIMA", 2002, 2010, 2700, "G6EA", "Optima 2.7 Delta 165-185hp [DBLINKS][ROW_FIX label]"),
    ("OPTIMA", 2012, 2020, 1600, "G4FJ", "Optima 1.6T 178hp [DB family]"),
    ("OPTIMA", 2012, 2016, 2000, "G4KF", "Optima 2.0T 245-274hp US (DB 211 Euro) [DB family]"),
    ("OPTIMA", 2017, 2020, 2000, "G4KF", "Optima 2.0T [DB family]"),
    ("OPTIMA", 2012, 2020, 2400, "G4KJ", "Optima 2.4 GDI 192-200hp [WIKIBOOKS VIN7][DB family]"),
    ("RIO", 2001, 2005, None, "1.5 DOHC (B5-family, Rio)", "Rio 1.5 B5-DE DOHC 105hp [WIKIBOOKS][NEW]"),
    ("RIO", 2006, 2011, None, "G4ED", "Rio 1.6 Alpha II 110hp [DB family]"),
    ("RIO", 2012, 2023, None, "G4FD", "Rio 1.6 GDI 130-138hp [DB family]"),
    ("RIO5", 2006, 2011, None, "G4ED", "Rio5 1.6 [DB family]"),
    ("RONDO", 2007, 2010, 2400, "G4KC", "Rondo 2.4 Theta 162-175hp [DB family]"),
    ("RONDO", 2007, 2010, 2700, "G6EA", "Rondo 2.7 Delta 182-192hp [DB family]"),
    ("SEDONA", 2002, 2005, None, "G6CU", "Sedona 3.5 Sigma 194hp [DBLINKS]"),
    ("SEDONA", 2006, 2012, None, "Lambda 3.8 MPi (G6DA-family)", "Sedona 3.8 Lambda MPi 244-245hp [NEW]"),
    ("SEDONA", 2014, 2014, None, "Lambda II 3.5 GDI (Sorento/Carnival/Sedona)", "2014 Sedona 3.5 GDI 266hp [NEW]"),
    ("SEDONA", 2015, 2021, None, "Lambda 3.3 GDI (Cadenza/Sedona/Sorento)", "Sedona 3.3 GDI 276hp [MOTORREVIEWER G6DH-family][NEW]"),
    ("SEPHIA", 2000, 2001, None, "G4GB", "Sephia 1.8 125hp (G4GB family, links Cerato) [DB family]"),
    ("SORENTO", 2003, 2006, None, "G6AU", "Sorento 3.5 Sigma 192hp [DBLINKS]"),
    ("SORENTO", 2007, 2009, None, "Lambda 3.8 MPi (G6DA-family)", "Sorento 3.8 Lambda 262hp [NEW]"),
    ("SORENTO", 2011, 2011, 2400, "G4KC", "Sorento 2.4 MPi 175hp (GDI from 2012) [DB family]"),
    ("SORENTO", 2012, 2020, 2400, "G4KJ", "Sorento 2.4 GDI 190-192hp [DB family]"),
    ("SORENTO", 2011, 2013, 3500, "Lambda II 3.5 GDI (Sorento/Carnival/Sedona)", "Sorento 3.5 GDI 276-290hp [NEW]"),
    ("SORENTO", 2014, 2020, 3300, "Lambda 3.3 GDI (Cadenza/Sedona/Sorento)", "Sorento 3.3 GDI 290hp [NEW]"),
    ("SORENTO", 2016, 2018, 2000, "G4KF", "Sorento 2.0T 240hp (VIN 1) [DB family]"),
    ("SORENTO", 2021, 2025, 1600, "Smartstream 1.6 T-GDI Hybrid (Sorento/Sportage/Carnival)", "Sorento Hybrid 1.6T 227hp system [NEW]", "Hybrid"),
    ("SORENTO", 2021, 2025, 2500, "G4KN", "Sorento 2.5 GDI 191hp (2.5T minority) [ROW_FIX G4KN]"),
    ("SOUL", 2010, 2011, 1600, "G4FC", "Soul 1.6 Gamma 122hp [DB family]"),
    ("SOUL", 2012, 2015, 1600, "G4FD", "Soul 1.6 GDI 138hp [DB family]"),
    ("SOUL", 2016, 2022, 1600, "G4FJ", "Soul Turbo 1.6T 175-201hp [DB family]"),
    ("SOUL", 2010, 2011, 2000, "G4GC", "Soul 2.0 Beta 142hp [DB family]"),
    ("SOUL", 2012, 2019, 2000, "G4NA", "Soul 2.0 Nu MPi 164hp [EBAY_G4NA][NEW]"),
    ("SOUL", 2020, 2022, 2000, "G4NH", "Soul 2.0 MPi 147hp [WIKIBOOKS VIN U][GOPARTS_NH][NEW]"),
    ("SOUL", 2023, 2025, None, "G4NH", "Soul 2.0 only [GOPARTS_NH][NEW]"),
    ("SPECTRA", 2000, 2004, None, "G4GB", "Spectra 1.8 125-135hp [DB family]"),
    ("SPECTRA", 2005, 2009, None, "G4GC", "Spectra 2.0 Beta 138-141hp [DB family]"),
    ("SPECTRA5", 2005, 2009, None, "G4GC", "Spectra5 2.0 [DB family]"),
    ("SPORTAGE", 2000, 2002, None, "G4CP", "Sportage 2.0 FE DOHC 139hp (links Joice) [DBLINKS]"),
    ("SPORTAGE", 2005, 2010, 2000, "G4GC", "Sportage 2.0 Beta 141hp [DB family]"),
    ("SPORTAGE", 2005, 2010, 2700, "G6EA", "Sportage 2.7 Delta 173-185hp [DB family]"),
    ("SPORTAGE", 2011, 2011, None, "G4KC", "2011 Sportage 2.4 only US 176hp [DB family]"),
    ("SPORTAGE", 2012, 2022, 2000, "G4KF", "Sportage SX 2.0T 240-261hp [DB family]"),
    ("SPORTAGE", 2012, 2016, 2400, "G4KC", "Sportage 2.4 GDI 176hp [DB family]"),
    ("SPORTAGE", 2017, 2022, 2400, "G4KJ", "Sportage 2.4 GDI 181hp [DB family]"),
    ("SPORTAGE", 2023, 2025, 1600, "Smartstream 1.6 T-GDI Hybrid (Sorento/Sportage/Carnival)", "Sportage Hybrid 1.6T 227hp system [NEW]", "Hybrid"),
    ("SPORTAGE", 2023, 2025, 2500, "G4KN", "Sportage 2.5 GDI 187hp [ROW_FIX G4KN]"),
    ("SELTOS", 2021, 2025, 1600, "G4FJ", "Seltos 1.6T 175hp AWD [DB family]"),
    ("SELTOS", 2021, 2025, 2000, "G4NH", "Seltos 2.0 MPi 146hp [GOPARTS_NH][NEW]"),
    ("STINGER", 2018, 2021, 2000, "G4KF", "Stinger 2.0T 255hp US (DB 211 Euro) [DB family]"),
    ("STINGER", 2022, 2023, 2500, "Smartstream 2.5 T-GDI (K5/Stinger GT)", "Stinger GT 2.5T 300hp [NEW]"),
    ("STINGER", 2018, 2023, 3300, "G6DP", "Stinger GT 3.3TT 365hp [GOPARTS_DP][MOTORREVIEWER][NEW]"),
    ("TELLURIDE", 2020, 2025, None, "Lambda 3.8 GDI (Telluride/Palisade)", "Telluride 3.8 GDI 291hp only [NEW]"),
]

def decide(model, year, code, fuel):
    parts = code.replace("LEMON_KIA_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc = None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
    mu = model.upper()
    up = code.upper()
    # slug special cases
    if mu == "FORTE" and "KOUPE" in up:
        return ("G4FJ", "Forte Koup EX/SX 1.6T 201hp [DB family]", None)
    if mu == "FORTE" and "FORTEEX" in up:
        return ("G4NC", "Forte EX 2.0 GDI 173hp [DB family]", None)
    if mu == "FORTE" and "FORTELX" in up:
        return ("G4NB", "Forte LX 1.8 145hp [NEW G4NB]", None)
    if mu == "FORTE5" and "FORTE5EX" in up:
        return ("G4NC", "Forte5 EX 2.0 GDI [DB family]", None)
    if mu == "FORTE5" and "SX" in up:
        return ("G4FJ", "Forte5 SX 1.6T 201hp [DB family]", None)
    if mu == "SOUL" and "SOULEV" in up:
        return ("Soul EV Electric", "Soul EV 109hp [NEW]", "Electric")
    if mu == "OPTIMA":
        if year == 2011 and cc is None:
            if fuel == "Hybrid":
                return ("G4KK", "Optima Hybrid 2.4 GDI launch 206hp system [WIKIBOOKS G4KK][NEW]", "Hybrid")
            return (None, "Optima 2011 bare: 2.4/2.0T unknown", None)
        if cc == 2000:
            if fuel == "Hybrid":
                return ("G4NE", "Optima Hybrid 2.0 GDI 192hp system (VIN C/D/E/F) [DBLINKS G4NE][ROW_FIX]", "Hybrid")
            return ("G4KF", "Optima 2.0T (petrol) [DB family]", None)
        if cc == 2400:
            if fuel == "Hybrid":
                return ("G4KK", "Optima Hybrid 2.4 GDI 199-206hp system [WIKIBOOKS G4KK][NEW]", "Hybrid")
    if mu == "OPTIMA" and cc is None and year <= 2010:
        return (None, f"Optima {year} bare: 2.4 vs 2.7 unknown", None)
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands:
        if cc is not None:
            return (None, f"{model} {year} {cc}cc: no rule", None)
        return (None, f"no rule for {model} {year} (bare)", None)
    r = cands[0]
    if r[4] is None:
        return (None, r[5], None)
    fuel_fix = r[6] if len(r) > 6 else FUEL_FIX_BY_TARGET.get(r[4])
    return (r[4], r[5], fuel_fix)

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Kia' AND engine_code LIKE 'LEMON_KIA%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        tgt, note, fuel_fix = decide(model, year, code, fuel)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"Kia LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(16): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter(d[6] for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"

    if not apply:
        with open("database_enriched/csv_exports/27_lemon_batch10_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"Kia",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Kia",s[1],s[2],"","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step19_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP19_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
            print(f"  created {code}")
    for code, fixes in ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  row-fix {code}: {fixes}")

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

    with open("database_enriched/csv_exports/27_lemon_batch10_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"Kia",d[1],d[2],d[3],d[4],d[6] or "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_KIA remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_KIA%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
