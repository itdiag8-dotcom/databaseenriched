"""Step 29 (user-plan Step 5, batch 20): replace LEMON_BUICK codes with real OEM engine codes.
205 rows, 16 models, MY2000-2025 — first pass targets ZERO skips (every group carries cc/VIN
markers or has sole-engine years). Signals: cc markers (2400CC/3600CC...), VIN letters (VINR/LUK
2.4 eAssist, VIN3/VINS 3.6, VINZ 2.5 eAssist, VINX LTG, VINV/VINK 2.0T/2.4, VINL 1.3T, VIN2/VINP
1.2T, VIN8/VINB/VINM 1.4T), fuel column (eAssist rows labeled Hybrid), trim slugs (ENCLAVECONVE/
LEATH/PREMI = 2015 Enclave trims -> LFX year rule).
DB GM vocabulary reused (Chevy batch 6 + Cadillac batch 15 + Euro catalog): LY7/LLT/LFX/LGX 3.6
genealogy, LF1 3.0, L36/L26/L67 3800, LG8 3.1, LA1 3.4, LX9/LZ9 3500/3900 High-Value, LS4 5.3 FWD,
LD8 4.6 Northstar, LL8 4.2 I6, LM4/LH6 5.3, LTG 2.0T, LAF/LEA/LUK 2.4 family, LUV 1.4T, LE2 1.4T
(hygiene fill), LIH 1.2T, L3T 1.3T, LCV 2.5, LSY 2.0T (fill).
Web-verified: Lucerne 3.8=197/3.9=227/4.6=275 (edmunds); Rendezvous 3.4 185 -> +3.6 245 Ultra
04-05 -> 3.5 195 (06+, 2007 FWD-only) (jdpower/conceptcarz); Terraza 3.5 196 std / 3.9 240 (std
from 2007) (jdpower/grokipedia); Rainier 4.2 275->291 / 5.3 290->300 (consumerguide/grokipedia);
Regal 2011 2.4 182 + 2.0T 220, 2012 GS 270, 2014 single 259, 2018+ 250 + GS 3.6 310 (cars.com/
consumerguide/motortrend); LaCrosse 2010-13 3.6 280 LLT -> 2014-16 304 LFX -> 2017-19 310 LGX,
2.5 eAssist 194 (2018-19), 2.4 eAssist LUK 2012-16 (gmauthority/iseecars/motorweek); Enclave sole
3.6: 275 (08) -> 288 (09-12 LLT) -> 288 (13-16 LFX) -> 310 (2018+ LGX) (jdpower/carbuzz); Encore
1.4T 138 all years, 153hp LE2 killed for 2020 (caranddriver/gmauthority); Encore GX 1.2T 137 /
1.3T 155; Cascada 1.6T LWC 200hp (caranddriver spec sheets).
Fuel policy: eAssist mild hybrids kept Petrol per DB convention (pre-existing LUK links Regal
2014-16/Malibu Eco are Petrol) -> 3 Hybrid-labeled LEMON rows fuel-fixed to Petrol.
"""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "LUCERNE": "https://www.edmunds.com/buick/lucerne/2006/review/ (Lucerne 3.8 V6 197hp / 4.6 Northstar 275hp) + autoevolution (3.9 227hp 2009-11)",
    "RENDEZVOUS": "https://www.jdpower.com/cars/history/buick/rendezvous + conceptcarz.com/vehicle/series.aspx?modelID=877 (2002-03 3.4 185 only; 2004-05 +3.6 245 Ultra; 2006 3.5 195/201; 2007 3.5 FWD-only)",
    "TERRAZA": "https://www.jdpower.com/cars/history/buick/terraza + grokipedia.com/page/Buick_Terraza (2005 3.5 LX9 196-200 sole; 2006 3.5 std + 3.9 LZ9 240 opt; 2007 3.9 240 std) + carsdirect 2006 (196hp)",
    "RAINIER": "https://consumerguide.com/used/2004-07-buick-rainier/ + grokipedia.com/page/Buick_Rainier (4.2 I6 275hp 04-05 -> 291hp 06-07; 5.3 V8 290hp 04-05 -> 300hp 06-07 AFM)",
    "REGAL": "https://www.cars.com/research/buick-regal/test-drive/ + consumerguide.com/used/2011-14-buick-regal/ + motortrend 2012 Regal (2011: 2.4 182 / 2.0T 220; 2012: +eAssist +GS 270; 2014: single 2.0T 259; 2018-20: 2.0T 250 + GS 3.6 310)",
    "GSRPO": "cobaltss.net forum (2012 Regal GS turbo = LNF-family high-output 'LDK/LHU' - no clean single RPO, descriptive row used)",
    "LACROSSE": "https://www.iseecars.com/car/buick-lacrosse/generations + gmauthority.com/blog/2017/10/quick-drive-review-2018-buick-lacrosse-eassist/ (2017-19: 3.6 LGX 310hp; 2018-19 eAssist 2.5 194hp) + motorweek (eAssist introduced on LaCrosse 2012)",
    "ENCLAVE": "https://www.jdpower.com/cars/history/buick/enclave + carbuzz.com/best-buick-enclave-model-years-for-reliability/ (2008 3.6 275 -> 2009 288 -> gen2 2018 310; sole engine every year)",
    "ENCORE": "https://www.caranddriver.com/buick/encore-2020 + gmauthority.com/blog/2019/05/2020-buick-encore-kills-more-powerful-turbo-engine/ (Encore 1.4T 138hp; 153hp LE2 optional 2016-19, killed for 2020; GX 1.2T 137 / 1.3T 155)",
    "CASCADA": "https://www.caranddriver.com/buick/cascada/specs/2016/ (engine order code LWC, 1.6L turbo SIDI 200hp/206lb-ft) + motogallery.com (1598cc DOHC)",
    "ENVISION": "GM Envision lineup knowledge (2016 2.0T 252 sole; 2017-20 2.5 197 base + 2.0T 252; 2021+ 2.0T LSY 228 sole) - consistent with DB LCV/LTG/LSY rows",
    "VERANO": "Buick Verano lineup knowledge (2012-17 2.4 180 base + 2.0T LTG 250 Turbo from 2013) - LEA/LTG DB rows",
    "GMVOCAB": "DB GM vocabulary (Chevy/Cadillac batches + Euro catalog): L36 3.8 3800-II 207(LeSabre 205/Regal 195), L26 3800-III (Allure 200 links), L67 3.8 SC 232, LG8 3.1 175, LA1 3.4 188, LX9 3.5, LZ9 3.9 240, LF1 3.0, LY7 3.6 255(Enclave/Allure links), LLT 3.6 304, LFX 3.6 322, LGX 3.6 335, LS4 5.3 FWD 303(Allure links), LD8 4.6 279(DTS), LL8 4.2 I6, LM4/LH6 5.3, LTG 2.0T 276, LAF/LEA 2.4 182, LUK 2.4 eAssist(Regal 14-16 links), LUV 1.4T 140(Encore 16-19 links), LE2 1.4T NULL, LIH 1.2T 137, L3T 1.3T 155, LCV 2.5 196, LSY 2.0T NULL(CT6 link)",
}

NEW_ENGINES = {
    "LWC": ("1.6 I4 Turbo SIDI (Cascada 2016-19, 200hp)", "Petrol", 1598, 200, 4),
    "2.0 Turbo (Regal 2011-13)": ("2.0 I4 Turbo (Regal CXL Turbo 220hp / GS 270hp, LNF-family)", "Petrol", 1998, 220, 4),
}

ROW_FIXES = {
    "L26": {"engine_type": "3.8 V6 3800 Series III OHV (LeSabre 205 / LaCrosse+Allure 200 / Lucerne 197hp)", "power_hp": 200},
    "LUK": {"engine_type": "2.4 I4 eAssist mild-hybrid (LaCrosse 2012-16 / Regal 2012-14 / Malibu Eco 2013, 182hp engine + 15kW motor)", "power_hp": 182},
    "LSY": {"engine_type": "2.0 I4 Turbo (LSY: CT4/CT6 237 / XT4 235 / Envision 2021+ 228hp)", "displacement_cc": 1998, "power_hp": 237},
    "LE2": {"engine_type": "1.4 I4 Turbo Ecotec (LE2: Encore Sport Touring 153 / Cruze 153hp)", "displacement_cc": 1399, "power_hp": 153},
    "LCV": {"engine_type": "2.5 I4 Ecotec DI (LCV: Malibu 196 / Colorado-Blazer 193-200 / LaCrosse eAssist 194hp)"},
    "LZ9": {"engine_type": "3.9 V6 High-Value (LZ9: Terraza/Uplander 240 / Lucerne 2009-11 227hp)"},
    "LX9": {"engine_type": "3.5 V6 High-Value (LX9: Malibu/G6 200 / Terraza 196 / Rendezvous 195hp)", "power_hp": 200},
    "LD8": {"engine_type": "4.6 V8 Northstar (LD8: Cadillac DTS / Buick Lucerne CXS, 275hp)", "power_hp": 275},
    "LL8": {"engine_type": "4.2 I6 Vortec DOHC (LL8: TrailBlazer/Rainier, 275hp 04-05 / 291hp 06-07)", "power_hp": 291},
    "LM4": {"engine_type": "5.3 V8 Vortec (LM4, aluminum: Rainier 290 / trucks 290-294hp)", "power_hp": 290},
    "LH6": {"engine_type": "5.3 V8 Vortec AFM (LH6: Rainier 300 / trucks 295-310hp)", "power_hp": 300},
    "LF1": {"engine_type": "3.0 V6 DI (LF1: LaCrosse 2010-11 255 / CTS 270hp)", "power_hp": 270},
    "LEA": {"engine_type": "2.4 I4 Ecotec DI (LEA: Malibu/Regal 182 / Verano 180hp)"},
}

FUEL_FIX_BY_TARGET = {"LUK": "Petrol"}  # eAssist mild hybrids kept Petrol per DB convention (5 pre-existing LUK links)

IDENTITY = {  # pre-existing targets: {code: (fuel, cc)}
    "LY7": ("Petrol", 3600), "LLT": ("Petrol", 3600), "LFX": ("Petrol", 3564), "LGX": ("Petrol", 3600),
    "LF1": ("Petrol", 3000), "L36": ("Petrol", 3791), "L26": ("Petrol", 3800), "LG8": ("Petrol", 3135),
    "LA1": ("Petrol", 3350), "LX9": ("Petrol", 3498), "LZ9": ("Petrol", 3880), "LS4": ("Petrol", 5300),
    "LD8": ("Petrol", 4565), "LL8": ("Petrol", 4157), "LM4": ("Petrol", 5327), "LH6": ("Petrol", 5328),
    "LTG": ("Petrol", 1998), "LAF": ("Petrol", 2400), "LEA": ("Petrol", 2400), "LUK": ("Petrol", 2400),
    "LUV": ("Petrol", 1364), "LIH": ("Petrol", 1199), "L3T": ("Petrol", 1341), "LCV": ("Petrol", 2500),
    "LSY": ("Petrol", 2000),
}

# (MODEL-upper, y0, y1, cc, target, evidence, pfix)   cc=None = bare
R = [
    ("ALLURE", 2005, 2007, 3600, "LY7", "Allure (Canadian LaCrosse) 3.6 = LY7 240hp (DB pre-existing Allure LY7 links) [GMVOCAB][LACROSSE]", 240),
    ("ALLURE", 2005, 2007, 3800, "L26", "Allure 3.8 = L26 3800-III 200hp (DB pre-existing links) [GMVOCAB][ROW_FIX L26]", 200),
    ("CASCADA", 2016, 2019, None, "LWC", "Cascada = 1.6T LWC SIDI 200hp sole engine (C&D engine order code) [CASCADA][NEW]", 200),
    ("CENTURY", 2000, 2005, None, "LG8", "Century = 3.1 LG8 175hp sole engine [GMVOCAB]", 175),
    ("ENCLAVE", 2008, 2008, None, "LY7", "Enclave 2008 = 3.6 275hp sole (pre-LLT) [ENCLAVE][GMVOCAB]", 275),
    ("ENCLAVE", 2009, 2012, None, "LLT", "Enclave 2009-12 = 3.6 DI LLT 288hp sole [ENCLAVE][GMVOCAB]", 288),
    ("ENCLAVE", 2013, 2017, None, "LFX", "Enclave 2013-16 (incl. 2015 Conve/Leath/Premi trims) = 3.6 LFX 288hp sole [ENCLAVE][GMVOCAB]", 288),
    ("ENCLAVE", 2018, 2025, None, "LGX", "Enclave 2018+ gen2 = 3.6 310hp sole (LGX) [ENCLAVE][LACROSSE-family]", 310),
    ("ENCORE", 2013, 2022, None, "LUV", "Encore (2013/2020/2022 bare) = 1.4T 138hp (153hp LE2 killed for 2020) [ENCORE][GMVOCAB]", 138),
    ("ENCORE", 2014, 2021, 1400, "LUV", "Encore 1.4T (VIN8/B/M) = 138hp standard engine [ENCORE][GMVOCAB]", 138),
    ("ENCORE", 2020, 2025, 1200, "LIH", "Encore GX 1.2T (VIN2/P) = 137hp [ENCORE][GMVOCAB]", 137),
    ("ENCORE", 2020, 2025, 1300, "L3T", "Encore GX 1.3T (VINL + bare 2022-25) = 155hp [ENCORE][GMVOCAB]", 155),
    ("ENVISION", 2016, 2016, None, "LTG", "Envision 2016 launch = 2.0T 252hp sole [ENVISION][GMVOCAB]", 252),
    ("ENVISION", 2021, 2025, None, "ENVISION_X", "placeholder", None),  # replaced below
    ("ENVISTA", 2024, 2025, None, "LIH", "Envista = 1.2T 137hp sole [ENVISION-family][GMVOCAB]", 137),
    ("LACROSSE", 2010, 2011, 2400, "LAF", "LaCrosse 2010-11 base 2.4 DI = LAF 182hp [GMVOCAB]", 182),
    ("LACROSSE", 2012, 2013, 2400, "LUK", "LaCrosse eAssist (fuel col Hybrid) = 2.4 LUK 182 + motor; kept Petrol per DB eAssist convention [LACROSSE][ROW_FIX LUK]", 182),
    ("LACROSSE", 2012, 2016, 2400, "LUK", "LaCrosse (VINR) 2.4 eAssist = LUK 182hp [LACROSSE][GMVOCAB]", 182),
    ("LACROSSE", 2018, 2019, 2500, "LCV", "LaCrosse 2018-19 eAssist 2.5 = 194hp (fuel col Petrol, mild hybrid) [LACROSSE][ROW_FIX LCV]", 194),
    ("LACROSSE", 2010, 2010, 3000, "LF1", "LaCrosse 2010 CXS 3.0 = LF1 255hp [GMVOCAB][ROW_FIX LF1]", 255),
    ("LACROSSE", 2005, 2008, 3600, "LY7", "LaCrosse 2005-08 3.6 = LY7 240hp (Allure sibling) [GMVOCAB]", 240),
    ("LACROSSE", 2010, 2013, 3600, "LLT", "LaCrosse 2010-13 3.6 DI = LLT 280hp [LACROSSE][GMVOCAB]", 280),
    ("LACROSSE", 2014, 2016, 3600, "LFX", "LaCrosse 2014-16 3.6 = LFX 304hp [LACROSSE][GMVOCAB]", 304),
    ("LACROSSE", 2017, 2019, 3600, "LGX", "LaCrosse 2017-19 3.6 = LGX 310hp (gmauthority RPO) [LACROSSE]", 310),
    ("LACROSSE", 2005, 2009, 3800, "L26", "LaCrosse 2005-09 3.8 = L26 200hp [GMVOCAB][ROW_FIX L26]", 200),
    ("LACROSSE", 2008, 2009, 5300, "LS4", "LaCrosse Super 5.3 FWD = LS4 300hp (DB pre-existing Allure LS4 links) [GMVOCAB]", 300),
    ("LESABRE", 2000, 2005, None, "L36", "LeSabre = 3.8 3800-II 205hp sole [GMVOCAB]", 205),
    ("LUCERNE", 2006, 2008, 3800, "L26", "Lucerne 3.8 = 197hp (Edmunds) [LUCERNE][ROW_FIX L26]", 197),
    ("LUCERNE", 2009, 2011, 3900, "LZ9", "Lucerne 2009-11 3.9 = LZ9 227hp [LUCERNE][ROW_FIX LZ9]", 227),
    ("LUCERNE", 2006, 2011, 4600, "LD8", "Lucerne 4.6 Northstar = 275hp (DTS LD8 sibling) [LUCERNE][ROW_FIX LD8]", 275),
    ("PARK", 2000, 2005, None, "L36", "Park Avenue = 3.8 3800-II 205hp (Ultra L67 240 = trim-specific, not slugged) [GMVOCAB]", 205),
    ("RAINIER", 2004, 2005, 4200, "LL8", "Rainier 4.2 I6 2004-05 = LL8 275hp [RAINIER][ROW_FIX LL8]", 275),
    ("RAINIER", 2006, 2007, 4200, "LL8", "Rainier 4.2 I6 2006-07 = LL8 291hp (revised ECU) [RAINIER][ROW_FIX LL8]", 291),
    ("RAINIER", 2004, 2005, 5300, "LM4", "Rainier 5.3 V8 2004-05 = LM4 290hp [RAINIER][ROW_FIX LM4]", 290),
    ("RAINIER", 2006, 2007, 5300, "LH6", "Rainier 5.3 V8 2006-07 = LH6 AFM 300hp [RAINIER][ROW_FIX LH6]", 300),
    ("REGAL", 2000, 2004, None, "L36", "Regal 2000-04 base = 3.8 3800-II 195hp (GS L67 240 = trim-specific, not slugged) [GMVOCAB]", 195),
    ("REGAL", 2018, 2020, None, "LTG", "Regal 2018-20 (Sportback/TourX) = 2.0T 250hp standard [REGAL]", 250),
    ("REGAL", 2011, 2013, 2000, "2.0 Turbo (Regal 2011-13)", "Regal CXL Turbo 2.0T = 220hp (GS 270 same family; LNF-family RPO ambiguous) [REGAL][GSRPO][NEW]", 220),
    ("REGAL", 2014, 2017, 2000, "LTG", "Regal 2014-17 2.0T (VINX) = LTG 259hp single tune [REGAL][GMVOCAB]", 259),
    ("REGAL", 2018, 2020, 2000, "LTG", "Regal 2018-20 2.0T = 250hp [REGAL]", 250),
    ("REGAL", 2011, 2012, 2400, "LAF", "Regal 2011-12 base 2.4 = LAF 182hp (DB pre-existing Regal 2011 LAF link) [REGAL][GMVOCAB]", 182),
    ("REGAL", 2013, 2013, 2400, "LUK", "Regal eAssist 2013 (fuel col Hybrid) = 2.4 LUK 182; kept Petrol per DB convention [REGAL][ROW_FIX LUK]", 182),
    ("REGAL", 2017, 2017, 2400, "LEA", "Regal 2017 1SV 2.4 (VINK) = LEA 182hp [GMVOCAB][ROW_FIX LEA]", 182),
    ("REGAL", 2018, 2020, 3600, "LGX", "Regal GS 2018-20 = 3.6 V6 310hp [REGAL][LACROSSE-family]", 310),
    ("RENDEZVOUS", 2002, 2003, None, "LA1", "Rendezvous 2002-03 = 3.4 LA1 185hp sole [RENDEZVOUS][GMVOCAB]", 185),
    ("RENDEZVOUS", 2007, 2007, None, "LX9", "Rendezvous 2007 = 3.5 195hp sole (3.6/AWD dropped) [RENDEZVOUS][ROW_FIX LX9]", 195),
    ("RENDEZVOUS", 2004, 2005, 3400, "LA1", "Rendezvous 3.4 (3400CC) = LA1 185hp std [RENDEZVOUS]", 185),
    ("RENDEZVOUS", 2006, 2006, 3500, "LX9", "Rendezvous 3.5 (3500CC 2006) = LX9 195hp [RENDEZVOUS][ROW_FIX LX9]", 195),
    ("RENDEZVOUS", 2004, 2006, 3600, "LY7", "Rendezvous Ultra 3.6 = LY7 245hp [RENDEZVOUS][GMVOCAB]", 245),
    ("TERRAZA", 2005, 2005, None, "LX9", "Terraza 2005 = 3.5 LX9 196hp sole [TERRAZA][ROW_FIX LX9]", 196),
    ("TERRAZA", 2007, 2007, None, "LZ9", "Terraza 2007 = 3.9 LZ9 240hp std (3.5 dropped) [TERRAZA][ROW_FIX LZ9]", 240),
    ("TERRAZA", 2006, 2006, 3500, "LX9", "Terraza 2006 3.5 std = LX9 196hp [TERRAZA]", 196),
    ("TERRAZA", 2006, 2006, 3900, "LZ9", "Terraza 2006 3.9 opt = LZ9 240hp [TERRAZA]", 240),
    ("VERANO", 2012, 2017, None, "LEA", "Verano base (2012/2017 bare) = 2.4 180hp [VERANO][ROW_FIX LEA]", 180),
    ("VERANO", 2013, 2016, 2000, "LTG", "Verano Turbo 2.0T (VINV) = LTG 250hp [VERANO][GMVOCAB]", 250),
    ("VERANO", 2013, 2016, 2400, "LEA", "Verano 2.4 (VINK) = 180hp [VERANO][ROW_FIX LEA]", 180),
]
# fix the Envision 2021+ placeholder (kept separate for readability)
R = [r for r in R if r[4] != "ENVISION_X"]
R.append(("ENVISION", 2021, 2025, None, "LSY", "Envision 2021+ = 2.0T LSY 228hp sole [ENVISION][ROW_FIX LSY]", 228))
R.append(("ENVISION", 2017, 2020, 2000, "LTG", "Envision 2017-20 2.0T (2000CC) = LTG 252hp [ENVISION][GMVOCAB]", 252))
R.append(("ENVISION", 2017, 2020, 2500, "LCV", "Envision 2017-20 base 2.5 (2500CC) = LCV 197hp [ENVISION][ROW_FIX LCV]", 197))

def parse_code(code):
    m = re.match(r"^LEMON_BUICK_(.+)$", code)
    if not m: return None
    toks = m.group(1).split("_")
    yi = next((i for i, t in enumerate(toks) if re.fullmatch(r"(19|20)\d\d", t)), None)
    if yi is None: return None
    year = int(toks[yi])
    cc = None
    model_toks = []
    for t in toks[:yi]:
        if re.fullmatch(r"\d+CC", t): cc = int(t[:-2])
        elif not re.fullmatch(r"VIN[A-Z0-9]", t): model_toks.append(t)
    return " ".join(model_toks), year, cc

def decide(model, year, cc, code, fuel):
    mu = model.upper()
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands:
        return (None, f"no rule for Buick {model} {year} cc={cc}", None, None)
    r = cands[0]
    fuel_fix = FUEL_FIX_BY_TARGET.get(r[4])
    if fuel_fix and fuel == fuel_fix: fuel_fix = None
    return (r[4], r[5], fuel_fix, r[6])

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == 2689, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 2689 (workspace rewind?)"
    base_eng = cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0]
    assert base_eng == 8250, f"BASELINE MISMATCH: engines={base_eng}, expected 8250"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Buick' AND engine_code LIKE 'LEMON%' ORDER BY car_model, car_year, engine_code""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        p = parse_code(code)
        assert p, f"unparseable code: {code}"
        pm, py, cc = p
        assert pm.upper() == model.upper(), f"model parse mismatch {code} vs {model}"
        tgt, note, fuel_fix, pfix = decide(model, year, cc, code, fuel)
        if tgt is None: skips.append((vid, model, year, code, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix, pfix))
    print(f"Buick LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print(f"  SKIP: {s[1]} {s[2]} [{s[3]}] - {s[4]}")
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(30): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter((d[4], d[6]) for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"
    # batch-17 standing rule: existing target rows must match expected fuel/displacement
    for tgt, (efuel, ecc) in IDENTITY.items():
        cc_fix = ROW_FIXES.get(tgt, {}).get("displacement_cc")
        row = cur.execute("SELECT fuel, displacement_cc FROM engines WHERE engine_code=?", (tgt,)).fetchone()
        if row is None: continue
        if row[0] and efuel and row[0] != efuel:
            raise AssertionError(f"IDENTITY CONFLICT {tgt}: engines.fuel={row[0]}, expected {efuel}")
        if cc_fix and row[1] and row[1] != cc_fix:
            print(f"  identity: {tgt} cc {row[1]} junk -> queued ROW_FIX to {cc_fix}"); continue
        if row[1] and ecc and abs(row[1] - ecc) / ecc > 0.07:
            raise AssertionError(f"IDENTITY CONFLICT {tgt}: engines.cc={row[1]}, expected ~{ecc}")
    print("identity assert: OK")

    if not apply:
        with open("database_enriched/csv_exports/37_lemon_batch20_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
            for d in decisions: w.writerow([d[0],"Buick",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Buick",s[1],s[2],s[3],"","","SKIP",s[4]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step29_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP29_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
            print(f"  created {code}")
    for code, fixes in ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  row-fix {code}")

    lemon_retired = defaultdict(list)
    for vid, model, year, old, new, note, fuel_fix, pfix in decisions:
        cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=COALESCE(?, fuel) WHERE id=?", (new, fuel_fix, vid))
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=COALESCE(?, COALESCE(engine_power_hp,
            (SELECT power_hp FROM engines WHERE engine_code=?)),
            COALESCE((SELECT power_hp FROM engines WHERE engine_code=?), engine_power_hp)),
            engine_type=COALESCE(engine_type, (SELECT engine_type FROM engines WHERE engine_code=?)) WHERE id=?""",
            (pfix, new, new, new, vid))
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
    # sweep: batch targets with NULL variant power take engine power
    tgts = tuple(set(d[4] for d in decisions))
    cur.execute(f"""UPDATE vehicle_variants SET engine_power_hp=
        (SELECT power_hp FROM engines WHERE engine_code=vehicle_variants.engine_code)
        WHERE engine_code IN ({','.join('?'*len(tgts))}) AND engine_power_hp IS NULL""", tgts)

    with open("database_enriched/csv_exports/37_lemon_batch20_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
        for d in decisions: w.writerow([d[0],"Buick",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON Buick remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand='Buick' AND engine_code LIKE 'LEMON%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
