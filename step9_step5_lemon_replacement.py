#!/usr/bin/env python3
"""
STEP 9 = USER-PLAN STEP 5 (batch 1): LEMON synthetic engine-code replacement.
Scope: US trucks / full-size SUVs / vans (GM, Ford, Lincoln, Dodge/Ram).

Replaces LEMON_* synthetic engine codes with real OEM engine codes using:
  (brand, model, year, displacement_cc, VIN-8th char, fuel) -> real code
Every mapping family is backed by a web citation (see CITATIONS).

What the script does per mapped variant:
  1. vehicle_variants.engine_code  -> real code (+ fuel fix where lemon mislabeled diesels as Petrol)
  2. Fills variant engine_power_hp / engine_type from verified engine row when NULL
  3. Migrates engine_service_specs + engine_technical_specs from LEMON code to the
     real code (merge-fill NULL fields, keep existing target values), preserving
     the crawled lemon fluid data; deletes retired LEMON rows
  4. Creates real engine rows where missing (specs from cited references),
     merges/updates existing rows (count_variants, spec fills, junk engine_type fixes)
  5. Deletes retired LEMON engine rows

Gated: run with --apply to write; default is dry-run.
Backup: backups/car_database_backup_pre_step9_<date>.db
"""
import sqlite3, sys, re, shutil, csv, os
from datetime import date
from collections import defaultdict

DB = "database_enriched/car_database.db"
APPLY = "--apply" in sys.argv

CITATIONS = {
    "LS": "https://en.wikipedia.org/wiki/General_Motors_LS-based_small-block_engine",
    "DURAMAX": "https://en.wikipedia.org/wiki/Duramax_V8_engine",
    "VINCHART": "https://www.silveradosierra.com/threads/which-engine-is-in-my-silverado-or-sierra.743113/",
    "LMG0": "https://carpartplanet.com/engines/chevrolet/silverado_1500/2009/5.3l-vin-0-8th-digit-opt-lmg",
    "L84D": "https://carpartplanet.com/engines/chevrolet/silverado_1500/2019/new-style-mirrors-mount-on-door-skin-5.3l-opt-l84-vin-d-8th-digit",
    "L96G": "https://carpartplanet.com/engines/chevrolet/silverado_2500/2016/6.0l-gasoline-vin-g-8th-digit-opt-l96",
    "COLORADO": "https://gmauthority.com/blog/gm/chevrolet/colorado/",
    "CANYON": "https://gmauthority.com/blog/gm/gmc/canyon/",
    "GMA19": "https://gmauthority.com/blog/2018/04/2019-silverado-engines-power-and-torque-ratings-revealed/",
    "MODULAR": "https://en.wikipedia.org/wiki/Ford_Modular_engine",
    "SUPERDUTY": "https://en.wikipedia.org/wiki/Ford_Super_Duty",
    "V10": "https://www.dieselhub.com/gas/ford-6.8-triton-v10.html",
    "F150VIN": "https://engineoiljournal.com/ford-f150-vin-engine-code-chart/",
    "VEHQ": "https://vehq.com/how-to-tell-what-engine-is-in-my-ford-f150/",
    "F150LAB": "https://f150lab.com/how-to-tell-what-engine-is-in-my-ford-f150/",
    "FORDVIN": "https://fordmasterx.com/ford-vin-number-decoding-chart/",
    "NAVIGATOR": "https://en.wikipedia.org/wiki/Lincoln_Navigator",
    "RAMVIN": "https://truckguider.com/dodge-ram-engine-codes-by-year-chart/",
    "RAM14": "https://www.ramtrucks.com/assets/pdf/brochures/14MY_Ram_Commercial_eBrochure.pdf",
    "RAMOIL": "https://www.jcofontario.com/service-department/service-and-parts-tips/ram-2500-oil-type/",
    "LEMON2015": "lemon_crawl_2015.jsonl (primary crawl: F-150 2.7L VIN P / 3.5L VIN 8 NA / 3.5L VIN G EcoBoost / 5.0L VIN F; E-series 5.4L VIN L / 6.8L VIN S; HEMI 5.7L VIN T; Pentastar 3.6L VIN G)",
}

# engine rows to create when missing: code -> (engine_type, fuel, cc, hp, cyl)
NEW_ENGINES = {
    # GM
    "L3B": ("2.7 Turbo I4", "Petrol", 2700, None, 4),
    "LM2": ("3.0 I6 Duramax turbodiesel", "Diesel", 2993, 277, 6),
    "LZ0": ("3.0 I6 Duramax turbodiesel", "Diesel", 2993, 305, 6),
    "LV3": ("4.3 V6 EcoTec3", "Petrol", 4300, 285, 6),
    "LV1": ("4.3 V6 EcoTec3 (van)", "Petrol", 4300, 265, 6),
    "LK5": ("2.8 I4 Atlas", "Petrol", 2770, 175, 4),
    "LGZ": ("3.6 V6", "Petrol", 3564, 308, 6),
    "LWN": ("2.8 I4 Duramax turbodiesel", "Diesel", 2776, 181, 4),
    "LH9": ("5.3 V8 Vortec", "Petrol", 5328, 300, 8),
    "LMF": ("5.3 V8 Vortec (van 1500)", "Petrol", 5328, 310, 8),
    "L8B": ("5.3 V8 EcoTec3 eAssist mild hybrid", "Hybrid", 5328, 355, 8),
    "L86": ("6.2 V8 EcoTec3", "Petrol", 6162, 420, 8),
    "L83": ("5.3 V8 EcoTec3", "Petrol", 5327, 355, 8),
    "L31": ("5.7 V8 Vortec", "Petrol", 5733, 255, 8),
    "L29": ("7.4 V8 Vortec", "Petrol", 7446, 290, 8),
    "L30": ("5.0 V8 Vortec", "Petrol", 4997, 220, 8),
    "LGH": ("6.6 V8 Duramax turbodiesel", "Diesel", 6596, 335, 8),
    "LR4": ("4.8 V8 Vortec", "Petrol", 4806, 275, 8),
    # Ford
    "2.7 EcoBoost": ("2.7 V6 EcoBoost twin-turbo", "Petrol", 2694, 325, 6),
    "3.0 Power Stroke": ("3.0 V6 Power Stroke turbodiesel", "Diesel", 2956, 250, 6),
    "3.2 Power Stroke": ("3.2 I5 Power Stroke turbodiesel", "Diesel", 3198, 185, 5),
    "3.3 Ti-VCT V6": ("3.3 V6 Ti-VCT", "Petrol", 3317, 290, 6),
    "3.5 Cyclone V6": ("3.5 V6 Cyclone", "Petrol", 3496, 282, 6),
    "3.5 PowerBoost": ("3.5 V6 PowerBoost hybrid", "Hybrid", 3496, 430, 6),
    "3.7 Ti-VCT V6": ("3.7 V6 Ti-VCT", "Petrol", 3726, 302, 6),
    "5.0 Coyote V8": ("5.0 V8 Coyote", "Petrol", 4951, 395, 8),
    "5.2 Predator V8": ("5.2 V8 Predator supercharged", "Petrol", 5163, 700, 8),
    "6.2 Boss V8": ("6.2 V8 SOHC (Boss)", "Petrol", 6200, 385, 8),
    "4.6 Triton 2V": ("4.6 V8 Triton SOHC 2V", "Petrol", 4601, 231, 8),
    "5.4 Triton 2V": ("5.4 V8 Triton SOHC 2V", "Petrol", 5408, 260, 8),
    "5.4 Triton 3V": ("5.4 V8 Triton SOHC 3V", "Petrol", 5408, 300, 8),
    "5.4 InTech V8": ("5.4 V8 InTech DOHC 32V", "Petrol", 5408, 300, 8),
    "6.8 Triton V10 2V": ("6.8 V10 Triton SOHC 2V", "Petrol", 6760, 305, 10),
    "6.8 Triton V10 3V": ("6.8 V10 Triton SOHC 3V", "Petrol", 6760, 362, 10),
    "6.0 Power Stroke": ("6.0 V8 Power Stroke turbodiesel", "Diesel", 5936, 325, 8),
    "6.4 Power Stroke": ("6.4 V8 Power Stroke turbodiesel", "Diesel", 6401, 350, 8),
    "6.7 Power Stroke": ("6.7 V8 Power Stroke turbodiesel", "Diesel", 6651, 390, 8),
    "7.3 Power Stroke": ("7.3 V8 Power Stroke turbodiesel", "Diesel", 7276, 250, 8),
    "7.3 Godzilla V8": ("7.3 V8 OHV (Godzilla)", "Petrol", 7300, 350, 8),
    "6.8 Godzilla V8": ("6.8 V8 OHV", "Petrol", 6810, 405, 8),
    # Mopar
    "3.9 Magnum V6": ("3.9 V6 Magnum", "Petrol", 3906, 175, 6),
    "5.2 Magnum V8": ("5.2 V8 Magnum", "Petrol", 5211, 230, 8),
    "5.9 Magnum V8": ("5.9 V8 Magnum", "Petrol", 5889, 245, 8),
    "5.9 Cummins ISB": ("5.9 I6 Cummins turbodiesel", "Diesel", 5923, None, 6),
    "6.7 Cummins ISB": ("6.7 I6 Cummins turbodiesel", "Diesel", 6690, None, 6),
    "8.0 V10 Magnum": ("8.0 V10 Magnum", "Petrol", 8028, 305, 10),
    "8.3 V10 SRT": ("8.3 V10 SRT", "Petrol", 8277, 500, 10),
    "3.6 Pentastar": ("3.6 V6 Pentastar", "Petrol", 3604, None, 6),
}

# cosmetic engine-row fixes on EXISTING rows (junk engine_type / fuel)
ROW_FIXES = {
    "LFA": {"engine_type": "6.0 V8 hybrid (two-mode)"},
    "L18": {"engine_type": "8.1 V8 Vortec"},
    "L5P": {"fuel": "Diesel", "engine_type": "6.6 V8 Duramax turbodiesel"},
    "L8T": {"power_hp": 401, "displacement_cc": 6564, "engine_type": "6.6 V8 gas", "fuel": "Petrol"},
    "L86": {"engine_type": "6.2 V8 EcoTec3", "displacement_cc": 6162, "power_hp": 420, "cylinders": 8},
}

GM_VAN_MODELS = {"Express", "Savana", "Cab", "Cutaway", "RV"}
GM_TRUCK_MODELS = {"Silverado", "Sierra", "Pickup", "Colorado", "Canyon", "F-250", "F-350"}
GM_SUV_MODELS = {"Suburban", "Tahoe", "Yukon", "Avalanche", "Escalade"}

TARGETS = {
    "Chevrolet": {"Silverado","Suburban","Tahoe","Avalanche","Colorado","Express","Pickup","Cab","Cutaway","RV"},
    "GMC": {"Sierra","Yukon","Savana","Canyon","Pickup","Cab","Cutaway","RV"},
    "Cadillac": {"Escalade"},
    "Ford": {"F-150","Pickup","Econoline","E-150","E-250","E-350","E-450","E450","E-550","Cab","Cutaway","RV",
             "Expedition","Excursion","F-250","F-350","F-450","F-550","Transit-150","Transit-250","Transit-350"},
    "Lincoln": {"Navigator"},
    "Dodge": {"Pickup","ProMaster","Cab"},
    "Ram": {"Ram","2500","3500"},
}

_RE_CC_VIN = re.compile(r"LEMON_(.+?)_(\d+)CC_VIN([A-Z0-9]+)_(\d{4})(?:_([A-Z0-9]+))?$")
_RE_CC     = re.compile(r"LEMON_(.+?)_(\d+)CC_(\d{4})(?:_([A-Z0-9]+))?$")
_RE_VIN    = re.compile(r"LEMON_(.+?)_VIN([A-Z0-9]+)_(\d{4})(?:_([A-Z0-9]+))?$")
_RE_BARE   = re.compile(r"LEMON_(.+)_(\d{4})(?:_([A-Z0-9]+))?$")

def parse_code(code):
    """LEMON_{...}_{cc}CC_[VIN{c}_]{YYYY}[_TRIM] -> (cc, vin, year, trim).
    Numeric model names (2500/3500/E-150) require ordered regexes + greedy fallback."""
    m = _RE_CC_VIN.match(code)
    if m: return (int(m.group(2)), m.group(3), int(m.group(4)), m.group(5))
    m = _RE_CC.match(code)
    if m: return (int(m.group(2)), None, int(m.group(3)), m.group(4))
    m = _RE_VIN.match(code)
    if m: return (None, m.group(2), int(m.group(3)), m.group(4))
    m = _RE_BARE.match(code)
    if m: return (None, None, int(m.group(2)), m.group(3))
    return None

def decide(brand, model, year, cc, vin, fuel, trim):
    """Return (new_code, note) or (None, reason)."""
    is_van = model in GM_VAN_MODELS
    is_suv = model in GM_SUV_MODELS
    f = (fuel or "").lower()
    diesel = "diesel" in f
    hybrid = "hybrid" in f

    # ---------------- GM ----------------
    if brand in ("Chevrolet", "GMC", "Cadillac"):
        # --- GM 2.7 L3B ---
        if cc == 2700 and year >= 2019 and (vin == "K" or not vin):
            return ("L3B", "2.7L only engine of that size 2019+; VIN K = L3B [VINCHART]")
        # --- GM midsize (Colorado/Canyon) ---
        if model in ("Colorado", "Canyon"):
            if cc == 2500: return ("LCV", "2.5 I4 LCV 2015+ [COLORADO]")
            if cc == 2700 and vin == "C" and year >= 2023: return ("L3B", "2.7 L3B Turbo (VIN C) 2023+ Colorado [GMA19]")
            if cc == 2800 and (vin == "1" or year >= 2015): return ("LWN", "2.8 Duramax LWN 2016+ [CANYON]")
            if cc == 2800 and year <= 2006: return ("LK5", "2.8 I4 LK5 2004-2006 [COLORADO]")
            if cc == 2900: return ("LLV", "2.9 I4 LLV 2007-2012 [COLORADO]")
            if cc == 3500 and year <= 2006: return ("L52", "3.5 I5 L52 2004-2006 [COLORADO]")
            if cc == 3700: return ("LLR", "3.7 I5 LLR 2007-2012 [COLORADO]")
            if cc == 3600 and (vin == "3" or (not vin and year <= 2016)): return ("LFX", "3.6 V6 LFX 2015-2016 [CANYON]")
            if cc == 3600 and (vin == "N" or (not vin and year >= 2017)): return ("LGZ", "3.6 V6 LGZ 2017+ [CANYON]")
            if cc == 5300 and year == 2009: return ("LH8", "5.3 V8 LH8 2009 Colorado [LS]")
            if cc == 5300 and year >= 2010: return ("LH9", "5.3 V8 LH9 2010-2012 Colorado [LS]")
            if not cc and year >= 2023: return ("L3B", "Colorado/Canyon 2023+ only gas engine = 2.7 L3B [GMA19]")
            return (None, "colorado combo unmatched")
        # --- GM 4.3 V6 ---
        if cc == 4300:
            if vin == "H" and year >= 2014: return ("LV3", "4.3 EcoTec3 LV3 = VIN H [VINCHART][LS]")
            if vin == "P" and year >= 2018: return ("LV1", "4.3 EcoTec3 van LV1 2018+ [LS]")
            if vin == "X": return ("LU3", "4.3 Vortec LU3 = VIN X (2012-2014) [VINCHART]")
            if not vin and 2002 <= year <= 2017:
                return ("LU3" if not is_van or year <= 2014 else "LV1",
                        "4.3 Vortec LU3 by years [LS]")
            if not vin and is_van and year >= 2018: return ("LV1", "van 4.3 LV1 2018+ [LS]")
            return (None, "4.3 pre-2002 (L35 era) not verified")
        # --- GM 4.8 V8 ---
        if cc == 4800:
            if vin == "A": return ("L20", "4.8 L20 = VIN A [VINCHART]")
            if vin == "F" and is_van: return ("L20", "only 4.8 in 2015-2017 vans = L20 [LS]")
            if not vin:
                if year <= 2006: return ("LR4", "4.8 Vortec LR4 1999-2006 [LS]")
                if year <= 2009: return ("LY2", "4.8 Vortec LY2 2007-2009 [LS]")
                return ("L20", "4.8 Vortec L20 2010+ [LS]")
        # --- GM 5.0 van ---
        if cc == 5000 and is_van: return ("L30", "5.0 Vortec L30 (vans 2000-2002) [LS family/Gen-I SBC]")
        # --- GM 5.3 ---
        if cc == 5300 and model == "Escalade":
            return ("LM7", "Escalade 2WD 5.3 = LM7 2002-2005 [LS]")
        if cc == 5300:
            if vin == "C" and year <= 2020: return ("L83", "5.3 EcoTec3 L83 = VIN C (2014-2020) [LS][VINCHART]")
            if vin == "D" and year >= 2019: return ("L84", "5.3 L84 = VIN D 2019+ [L84D][VINCHART]")
            if vin == "F": return (None, "5.3 VIN F: L82 vs L84 sources conflict - skipped")
            if vin == "0": return ("LMG", "5.3 flex LMG = VIN 0 [LMG0][LS]")
            if vin == "7" or vin == "3": return ("LC9", "5.3 alum flex LC9 = VIN 3/7 [VINCHART][LS]")
            if vin == "R" and 2016 <= year <= 2018: return ("L8B", "5.3 eAssist L8B = VIN R, 2016-2018 [VINCHART][LS]")
            if vin == "4" and is_van: return ("LMF", "Express/Savana 1500 5.3 = LMF 2008-2014 [LS]")
            if not vin:
                if is_van:
                    if 2003 <= year <= 2007: return ("LM7", "van 5.3 LM7 2003-2007 [LS]")
                    if 2008 <= year <= 2014: return ("LMF", "Express/Savana 1500 5.3 = LMF 2008-2014 [LS]")
                if year <= 2006: return ("LM7", "5.3 Vortec LM7 1999-2006 (L59 flex variant possible, base assumed) [LS]")
                if year <= 2009: return ("LY5", "5.3 Vortec LY5 2007-2009 (LMG/LC9 flex variants possible, base assumed) [LS]")
                if year <= 2013: return ("LC9", "5.3 LC9/LMG era 2010-2013 (LC9 assumed) [LS]")
                if year <= 2018: return ("L83", "5.3 EcoTec3 L83 only 5.3 in K2XX [LS]")
                if year >= 2022: return ("L84", "5.3 L84 = VIN D era [L84D]")
                return (None, "5.3 2019-2021 without VIN: L82 vs L84 ambiguous")
        # --- GM 5.7 / 6.5 / 7.4 (GMT400 leftovers; vans kept 5.7 through 2002) ---
        if cc == 5700 and (year <= 2000 or (is_van and year <= 2002)): return ("L31", "5.7 Vortec L31 [LS family/Gen-I SBC]")
        if cc == 7400 and year <= 2000: return ("L29", "7.4 Vortec L29 GMT400 2000 [Chevrolet big-block]")
        if cc == 6500: return (None, "6.5 diesel mislabeled Petrol - skipped")
        # --- GM van 2.8 Duramax ---
        if cc == 2800 and (vin == "1" or (is_van and year >= 2015)): return ("LWN", "2.8 Duramax LWN (only 2.8) [CANYON]")
        # --- GM 6.0 ---
        if cc == 6000:
            if model == "Escalade":
                if hybrid or year <= 2006:  # non-hybrid 2002-2006 = LQ9
                    if hybrid:
                        return ("LFA" if year <= 2009 else "LZ1", "Escalade Hybrid 6.0 [LS]")
                    return ("LQ9", "Escalade AWD/2WD 6.0 = LQ9 2002-2006 [LS]")
                return (None, "escalade 6000 combo unmatched")
            if vin == "B" and year >= 2012: return ("LC8", "6.0 bi-fuel CNG LC8 = VIN B (L96=VIN G confirmed; LC8 the other 6.0) [L96G]")
            if vin == "G" and year >= 2012: return ("L96", "6.0 L96 = VIN G [L96G][LS]")
            if vin == "J": return (None, "6.0 VIN J 2012 identity unverified - skipped")
            if hybrid:
                return ("LFA" if year <= 2009 else "LZ1", "two-mode hybrid 6.0 LFA/LZ1 [LS]")
            if not vin:
                if is_van:
                    if 2003 <= year <= 2007: return ("LQ4", "van 6.0 LQ4 2003-2007 [LS]")
                    if year <= 2009: return ("LY6", "van 6.0 LY6 2008-2009 [LS]")
                    return ("L96", "van 6.0 L96 2010+ [LS]")
                if year <= 2006: return ("LQ4", "6.0 LQ4 1999-2006 [LS]")
                if year <= 2009: return ("LY6", "6.0 LY6 2007-2009 (L76 VortecMAX 1500 possible, HD assumed) [LS]")
                return ("L96", "6.0 L96 2010-2019 [LS]")
        # --- GM 6.2 ---
        if cc == 6200:
            if vin == "L" and year >= 2019: return ("L87", "6.2 L87 = VIN L 2019+ [VINCHART][GMA19]")
            if vin == "J" and 2014 <= year <= 2020: return ("L86", "6.2 L86 = VIN J 2014+ [VINCHART]")
            if vin == "2": return ("L9H", "6.2 L9H 2010-2013 (VIN 2 era) [LS]")
            if vin == "F": return ("L9H", "Yukon XL Denali 6.2 L9H 2012-2014 [LS]")
            if not vin:
                if year <= 2009: return ("L92", "6.2 L92 2007-2009 [LS]")
                if year <= 2013: return ("L9H", "6.2 L9H 2010-2013 [LS]")
                if year == 2014: return ("L9H" if is_suv else "L86",
                                          "2014: GMT900 SUVs kept L9H; K2XX trucks got L86 [LS]")
                if year <= 2018: return ("L86", "6.2 L86 K2XX [GMA19]")
                return ("L87", "6.2 L87 T1XX [GMA19]")
        # --- GM 6.6 (diesel L-series + gas L8T); lemon sometimes mislabels diesels as Petrol ---
        if cc == 6600:
            if vin == "7": return ("L8T", "6.6 gas L8T = VIN 7 (2020+) [VINCHART][LS]")
            if vin == "L": return ("LGH", "6.6 Duramax LGH = VIN L [DURAMAX]")
            if vin == "8" and year <= 2016: return ("LML", "6.6 LML = VIN 8 2011-2016 [DURAMAX]")
            if vin == "Y" and year >= 2017: return ("L5P", "6.6 L5P 2017+ (engine code Y) [DURAMAX]")
            if year >= 2020 and not vin: return ("L8T", "6.6 gas L8T 2020+ [VINCHART]")
            # no VIN: Duramax by year (only 6.6 engines 2001-2016)
            if year <= 2004: return ("LB7", "6.6 LB7 2001-2004 [DURAMAX]")
            if year == 2005: return ("LLY", "6.6 LLY 2004-2005 [DURAMAX]")
            if year == 2006: return ("LBZ" if not is_van else "LLY", "6.6 2006: LBZ trucks / LLY vans [DURAMAX]")
            if 2007 <= year <= 2009: return ("LMM", "6.6 LMM 2007-2010 [DURAMAX]")
            if year == 2010: return ("LMM" if not is_van else "LGH", "6.6 2010: LMM pickups / LGH vans [DURAMAX]")
            if year == 2011: return ("LML" if not is_van else "LGH", "6.6 2011: LML pickups / LGH chassis+vans [DURAMAX]")
            if year <= 2016: return ("LML", "6.6 LML 2011-2016 [DURAMAX]")
            return ("L5P", "6.6 L5P 2017+ [DURAMAX]")
        # --- GM 8.1 ---
        if cc == 8100: return ("L18", "8.1 Vortec L18 2001-2007 [Chevrolet big-block]")
        # --- GM 3.0 Duramax ---
        if cc == 3000:
            if vin == "T": return ("LM2" if year <= 2022 else "LZ0", "3.0 Duramax LM2 = VIN T; LZ0 2023+ [VINCHART]")
            if vin == "8" and year >= 2023: return ("LZ0", "3.0 Duramax LZ0 2023+ (only 3.0 in Silverado; lemon fuel mislabeled) [VINCHART]")
            return (None, "3000 combo unmatched")
        # --- SUV/pickup bare rows by year (single-engine model years) ---
        if cc is None and not trim and model in ("Tahoe", "Suburban", "Avalanche"):
            if 2015 <= year <= 2020: return ("L83", "Tahoe/Suburban 2015-2020 only engine = 5.3 L83 [LS]")
            if 2000 <= year <= 2006: return ("LM7", "5.3 LM7 era (L59 flex possible, base assumed) [LS]")
            if 2007 <= year <= 2009: return ("LY5", "5.3 LY5 era (LMG/LC9 flex possible, base assumed) [LS]")
            if 2010 <= year <= 2013: return ("LC9", "5.3 LC9/LMG era 2010-2013 (LC9 assumed) [LS]")
            if year == 2014: return ("LMG", "GMT900 2014 Tahoe/Suburban 5.3 = LMG [LS]")
        if cc is None and not trim and model == "Escalade":
            if year <= 2000: return ("L31", "2000 Escalade 5.7 Vortec L31 [LS family]")
            if 2007 <= year <= 2009: return ("L92", "Escalade 6.2 L92 2007-2009 [LS]")
            if 2010 <= year <= 2013: return ("L9H", "Escalade 6.2 L9H 2010-2013 [LS]")
            if 2015 <= year <= 2020: return ("L86", "Escalade 6.2 L86 only 2015-2020 [LS]")
            if year >= 2021 and not diesel: return ("L87", "Escalade 6.2 L87 2021+ [GMA19]")
            if year >= 2021 and diesel: return ("LZ0", "Escalade 3.0 Duramax LZ0 2021+ [VINCHART]")
        # --- TRIM-coded 2015 rows ---
        if trim:
            t = trim.upper()
            if model == "Escalade" and year == 2015: return ("L86", "Escalade 2015 only engine 6.2 L86 [LS]")
            if model == "Tahoe" and year == 2015: return ("L83", "Tahoe 2015 only engine 5.3 L83 [LS]")
            if model == "Suburban" and year == 2015: return ("L83", "Suburban 2015 only engine 5.3 L83 [LS]")
            if model == "Yukon" and year == 2015:
                if "DENALI" in t: return ("L86", "Yukon Denali 2015 6.2 L86 [LS]")
                return ("L83", "Yukon SLE/SLT 2015 5.3 L83 [LS]")
        return (None, "gm combo unmatched")

    # ---------------- Ford / Lincoln ----------------
    if brand in ("Ford", "Lincoln"):
        # E-series / vans / chassis
        eseries = model in ("Econoline", "E-150", "E-250", "E-350", "E-450", "E450", "E-550", "Cutaway", "RV")
        if model == "Navigator" and cc is None:
            if year <= 2002: return ("5.4 InTech V8", "Navigator 98-02 5.4 InTech DOHC 300hp [NAVIGATOR]")
            if year <= 2014: return ("5.4 Triton 3V", "Navigator 03-14 5.4 3V SOHC 300hp [NAVIGATOR]")
            return ("3.5 V6 EcoBoost", "Navigator 2015+ 3.5 EcoBoost only [NAVIGATOR]")
        if model == "Expedition" and cc is None:
            if 2011 <= year <= 2014: return ("5.4 Triton 3V", "Expedition 2011-2014 only engine 5.4 3V [MODULAR]")
            if year >= 2015: return ("3.5 V6 EcoBoost", "Expedition 2015+ 3.5 EcoBoost only [MODULAR]")
            return (None, "Expedition bare 2005-2010: 4.6/5.4 ambiguous")
        if model == "Expedition" and cc == 5400:
            if year <= 2002: return ("5.4 Triton 2V", "Expedition 97-02 5.4 2V [MODULAR]")
            return (None, "Expedition 5.4 2003-2004: 2V vs 3V unverified - skipped")
        if model == "Expedition" and cc == 4600: return ("4.6 Triton 2V", "Expedition base 4.6 2V [MODULAR]")
        if model == "Expedition" and cc == 3500 and year >= 2023:
            return ("3.5 V6 EcoBoost", "Expedition 2023 3.5 EcoBoost (VIN 8/G) [VEHQ]")
        if model == "Excursion":
            if cc == 5400: return ("5.4 Triton 2V" if year <= 2004 else "5.4 Triton 3V", "Excursion 5.4 [SUPERDUTY]")
            if cc == 6800: return ("6.8 Triton V10 2V" if year <= 2004 else "6.8 Triton V10 3V", "Excursion V10 [SUPERDUTY][V10]")
            if cc == 7300: return ("7.3 Power Stroke", "Excursion 7.3 PSD 2000-2003 (fuel mislabeled) [MODULAR]")
            if cc == 6000: return ("6.0 Power Stroke", "Excursion 6.0 PSD 2003-2005 (fuel mislabeled) [MODULAR]")
        # Super Duty 2013+ (F-250..F-550)
        if model in ("F-250", "F-350", "F-450", "F-550"):
            if cc == 6200 and vin == "6": return ("6.2 Boss V8", "SD 6.2 SOHC = VIN 6 [F150VIN][SUPERDUTY]")
            if cc == 6700: return ("6.7 Power Stroke", "SD 6.7 PSD only 6.7 (some rows fuel mislabeled) [MODULAR]")
            if cc == 6800 and vin == "A" and year >= 2023: return ("6.8 Godzilla V8", "2023+ SD 6.8 gas = VIN A [SUPERDUTY]")
            if cc == 6800 and vin == "Y": return ("6.8 Triton V10 3V", "chassis-cab V10 3V through 2019 [V10]")
            if cc == 7300 and vin == "N" and year >= 2020: return ("7.3 Godzilla V8", "SD 7.3 gas 2020+ = VIN N [VEHQ][SUPERDUTY]")
            return (None, "SD combo unmatched")
        # Transit (big van)
        if model in ("Transit-150", "Transit-250", "Transit-350"):
            if cc == 3700 and vin == "M": return ("3.7 Ti-VCT V6", "Transit 3.7 = VIN M [LEMON2015]")
            if cc == 3200 and vin == "V": return ("3.2 Power Stroke", "Transit 3.2 PSD only 3.2 [MODULAR]")
            if cc == 3500 and vin == "G": return ("3.5 V6 EcoBoost", "Transit 3.5 EB = VIN G [FORDVIN]")
            if cc == 3500 and vin == "8" and year >= 2020: return ("3.5 Cyclone V6", "3.5 NA Cyclone = VIN 8 [F150LAB]")
            return (None, "transit combo unmatched")
        # generic Ford truck/van by displacement
        if cc == 3500 and not vin:
            if 2013 <= year <= 2014: return ("3.5 V6 EcoBoost", "2013-2014 F-150 3.5 = EcoBoost only (3.5 NA not offered 2009-2014) [F150VIN]")
            if 2018 <= year <= 2020: return ("3.5 V6 EcoBoost", "2018-2020 F-150 3.5 = EcoBoost only (base was 3.3; PB from 2021) [VEHQ]")
            return (None, "3.5 no-VIN NA vs EB (2015-17) or EB vs PowerBoost (2021+) ambiguous")
        if cc == 5000 and not vin and year >= 2011: return ("5.0 Coyote V8", "only 5.0 engine in F-150 2011+ [F150VIN]")
        if cc == 3500 and vin == "T" and 2011 <= year <= 2014: return ("3.5 V6 EcoBoost", "3.5 EB = VIN T 2011-2014 [F150VIN]")
        if cc == 3500 and vin == "G": return ("3.5 V6 EcoBoost", "3.5 EB = VIN G 2015+ [LEMON2015][FORDVIN]")
        if cc == 3500 and vin == "8" and 2015 <= year <= 2017: return ("3.5 Cyclone V6", "3.5 NA = VIN 8 2015-2017 (2018+ VIN8 ambiguous, skipped) [LEMON2015][F150LAB]")
        if cc == 3500 and vin == "D" and year >= 2021: return ("3.5 PowerBoost", "PowerBoost = VIN D 2021+ [VEHQ][F150VIN]")
        if cc == 2700 and vin == "P": return ("2.7 EcoBoost", "2.7 EB = VIN P [LEMON2015][VEHQ]")
        if cc == 3000 and vin == "1": return ("3.0 Power Stroke", "3.0 PSD = VIN 1 through 2021 [VEHQ]")
        if cc == 3300 and vin == "B": return ("3.3 Ti-VCT V6", "3.3 = VIN B 2018+ [VEHQ][F150LAB]")
        if cc == 3700 and (vin == "M" or year <= 2012): return ("3.7 Ti-VCT V6", "3.7 = VIN M 2011-2014 [F150VIN]")
        if cc == 5000 and vin == "F" and year <= 2017: return ("5.0 Coyote V8", "5.0 Coyote = VIN F 2011-2017 [LEMON2015][FORDVIN]")
        if cc == 5000 and vin == "5" and year >= 2018: return ("5.0 Coyote V8", "5.0 gen3 = VIN 5 2018+ [F150LAB]")
        if cc == 5000 and not vin and year == 2011: return ("5.0 Coyote V8", "only 5.0 in 2011 F-150 [F150VIN]")
        if cc == 5200 and vin == "J": return ("5.2 Predator V8", "5.2 Raptor R = VIN J [VEHQ]")
        if cc == 6200: return ("6.2 Boss V8", "6.2 SOHC (Boss) = only 6.2 in F-Series gas; VIN 6 [F150VIN][SUPERDUTY]")
        if cc == 4200: return ("ESG-642", "4.2 Essex V6 (existing DB code) [MODULAR]")
        if cc == 4600:
            if vin == "W": return ("4.6 Triton 2V", "4.6 2V = VIN W (E-series) [LEMON2015]")
            return ("4.6 Triton 2V", "4.6 2V base (3V optional 2006+ F-150, base assumed) [MODULAR]")
        if cc == 5400:
            if eseries: return ("5.4 Triton 2V", "E-series 5.4 2V = VIN L throughout [LEMON2015][MODULAR]")
            if year <= 2003: return ("5.4 Triton 2V", "5.4 2V through 2003 [MODULAR]")
            if model == "Cab":  # SD chassis cab
                return ("5.4 Triton 2V" if year <= 2004 else "5.4 Triton 3V", "SD 5.4 2V/3V split 2005 [SUPERDUTY]")
            return ("5.4 Triton 3V", "F-150 5.4 3V 2004+ [MODULAR]")
        if cc == 6000: return ("6.0 Power Stroke", "6.0 PSD 2003-2007 (fuel mislabeled) [MODULAR]")
        if cc == 6400: return ("6.4 Power Stroke", "6.4 PSD 2008-2010 [MODULAR]")
        if cc == 6700: return ("6.7 Power Stroke", "6.7 PSD 2011+ (fuel mislabeled) [MODULAR]")
        if cc == 6800:
            if vin == "S": return ("6.8 Triton V10 2V", "E-series V10 2V = VIN S [LEMON2015][V10]")
            if model == "Cab":  # SD chassis cab V10
                return ("6.8 Triton V10 2V" if year <= 2004 else "6.8 Triton V10 3V", "SD V10 2V/3V split 2005 [SUPERDUTY][V10]")
            if eseries or model in ("RV",): return ("6.8 Triton V10 2V", "E-series V10 2V [V10]")
            return ("6.8 Triton V10 2V" if year <= 2004 else "6.8 Triton V10 3V", "SD V10 2V/3V split 2005 [SUPERDUTY][V10]")
        if cc == 7300:
            if vin in ("N", "K") and year >= 2020: return ("7.3 Godzilla V8", "7.3 gas 2020+ [VEHQ][SUPERDUTY]")
            return ("7.3 Power Stroke", "7.3 PSD 2000-2003 (fuel mislabeled) [MODULAR]")
        if model == "Pickup" and cc == 3500 and not vin and year == 2011: return (None, "3.5 NA vs EB ambiguous")
        return (None, "ford combo unmatched")

    # ---------------- Dodge / Ram ----------------
    if brand in ("Dodge", "Ram"):
        if model == "ProMaster":
            if cc == 3600: return ("3.6 Pentastar", "ProMaster 3.6 Pentastar = VIN G [LEMON2015][RAMVIN]")
            if cc == 3000: return ("EXL", "ProMaster 3.0 EcoDiesel = VIN D [LEMON2015]")
            if cc == 2400: return ("ED6", "ProMaster City 2.4 TigerShark = VIN B / Eng CD ED6 [LEMON2015]")
            if trim and "CIT" in trim.upper(): return ("ED6", "ProMaster City 2.4 only engine [LEMON2015]")
            if cc is None and not trim:
                if diesel: return ("EXL", "ProMaster diesel = 3.0 EcoDiesel only [LEMON2015]")
                return ("3.6 Pentastar", "ProMaster gas = 3.6 Pentastar only [LEMON2015][RAMVIN]")
            return (None, "promaster combo unmatched")
        if cc == 3900: return ("3.9 Magnum V6", "3.9 Magnum V6 94-01 [RAMVIN]")
        if cc == 5200: return ("5.2 Magnum V8", "5.2 Magnum V8 94-2003 [RAMVIN]")
        if cc == 5900:
            if diesel: return ("5.9 Cummins ISB", "5.9 Cummins ISB (VIN 6/C) [RAMVIN]")
            if year <= 2003: return ("5.9 Magnum V8", "5.9 Magnum V8 through 2003 [RAMVIN]")
            return (None, "5.9 petrol after 2003 = fuel/code conflict - skipped")
        if cc == 3700: return ("EKG", "3.7 PowerTech V6 2002-2012 = VIN K [RAMVIN]")
        if cc == 4700: return ("EVA", "4.7 PowerTech V8 = VIN N/P [RAMVIN]")
        if cc == 5700:
            if year <= 2008: return ("EZD", "5.7 HEMI EZD 2003-2008 [RAMVIN]")
            return ("EZH", "5.7 HEMI EZH 2009+ [RAMVIN]")
        if cc == 6400 and year >= 2014: return ("ESA", "6.4 HEMI (ESA) available 2014+ HD [RAM14][RAMOIL]")
        if cc == 6700: return ("6.7 Cummins ISB", "6.7 Cummins ISB 2007.5+ (fuel mislabeled) [RAMVIN]")
        if cc == 8000: return ("8.0 V10 Magnum", "8.0 V10 Magnum 94-2003 [RAMVIN]")
        if cc == 8300: return ("8.3 V10 SRT", "8.3 V10 SRT-10 2004-2006 [RAMVIN]")
        if model in ("2500", "3500") and cc is None:
            if diesel: return ("6.7 Cummins ISB", "only diesel in Ram HD 2013+ [RAMVIN]")
            if year == 2013: return ("EZH", "2013 Ram HD gas = 5.7 HEMI EZH [RAMOIL]")
            if 2014 <= year <= 2018: return (None, "Ram HD gas 2014-2018: 5.7 vs 6.4 ambiguous [RAMOIL]")
            if year >= 2019: return ("ESA", "6.4 HEMI sole gas engine 2019+ [RAMOIL][RAM14]")
        return (None, "dodge/ram combo unmatched")

    return (None, "brand not in scope")

# fuel fixes: rows whose real engine is diesel but lemon labeled Petrol
DIESEL_CODES = {"6.0 Power Stroke","6.4 Power Stroke","6.7 Power Stroke","7.3 Power Stroke",
                "6.7 Cummins ISB","5.9 Cummins ISB","3.0 Power Stroke","3.2 Power Stroke",
                "LB7","LLY","LBZ","LMM","LML","L5P","LGH","LM2","LZ0","LWN","EXL"}

def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys=ON")

    rows = list(cur.execute("""SELECT id, car_brand, car_model, car_year, fuel, engine_code
        FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'"""))
    print(f"LEMON variants total: {len(rows)}")

    decisions = []      # (variant_id, brand, model, year, old_code, new_code, note, fuel_fix)
    unmapped = []
    for vid, brand, model, year, fuel, code in rows:
        if model not in TARGETS.get(brand, set()):
            continue
        p = parse_code(code)
        if not p:
            unmapped.append((vid, brand, model, year, code, "unparseable"))
            continue
        cc, vin, ycode, trim = p
        new_code, note = decide(brand, model, year, cc, vin, fuel, trim)
        if not new_code:
            unmapped.append((vid, brand, model, year, code, note))
            continue
        fuel_fix = "Diesel" if new_code in DIESEL_CODES and fuel and "diesel" not in (fuel or "").lower() else None
        # sanity: petrol->diesel fix only for known-certain diesel engines (by construction above)
        decisions.append((vid, brand, model, year, code, new_code, note, fuel_fix))

    print(f"in-scope mapped: {len(decisions)} | unmapped/skipped: {len(unmapped)}")

    # group unmapped reasons for review
    reasons = defaultdict(list)
    for vid, brand, model, year, code, why in unmapped:
        reasons[(brand, model, why)].append((year, code))
    print("\n=== UNMAPPED (skipped) groups ===")
    for k in sorted(reasons, key=lambda k: -len(reasons[k])):
        print(f"  {k}: {len(reasons[k])} rows  e.g. {reasons[k][:3]}")

    if not APPLY:
        print("\nDRY RUN - no changes. Re-run with --apply.")
        # dump decisions preview
        with open("database_enriched/csv_exports/17_lemon_replacement_decisions_DRYRUN.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions:
                w.writerow(list(d[:5]) + [d[5], d[7] or "", d[6]])
        print("dry-run decisions written to csv_exports/17_lemon_replacement_decisions_DRYRUN.csv")
        con.close()
        return

    # ---------- APPLY ----------
    # fail-fast: every target must exist or be created
    existing = {r[0] for r in cur.execute("SELECT engine_code FROM engines")}
    all_targets = {d[5] for d in decisions}
    missing = all_targets - existing - set(NEW_ENGINES.keys())
    if missing:
        print("FATAL: targets missing from engines and NEW_ENGINES:", missing)
        sys.exit(1)
    bak = f"database_enriched/backups/car_database_backup_pre_step9_{date.today().isoformat()}.db"
    shutil.copy(DB, bak)
    print(f"backup: {bak}")

    # ensure new engine rows exist
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,))
        if not cur.fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, brand_example, model_example, year_example, count_variants, power_kw, data_confidence)
                VALUES (?,?,?,?,?,?,NULL,NULL,NULL,0,NULL,'STEP9_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
    # engine-row fixes
    for code, fixes in ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))

    # map variant -> new code; collect lemon codes retired
    lemon_retired = defaultdict(list)   # lemon_code -> [(variant_id, year, brand, model)]
    for vid, brand, model, year, old, new, note, fuel_fix in decisions:
        cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=COALESCE(?, fuel) WHERE id=?",
                    (new, fuel_fix, vid))
        # fill variant power/type from engine row
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=COALESCE(engine_power_hp,
                        (SELECT power_hp FROM engines WHERE engine_code=?)),
                        engine_type=COALESCE(engine_type, (SELECT engine_type FROM engines WHERE engine_code=?))
                        WHERE id=?""", (new, new, vid))
        lemon_retired[old].append((vid, year, brand, model))

    # migrate specs from each retired lemon code to its (single) target
    spec_cols_s = [c[1] for c in cur.execute("PRAGMA table_info(engine_service_specs)")]
    spec_cols_t = [c[1] for c in cur.execute("PRAGMA table_info(engine_technical_specs)")]
    def merge_specs(table, cols, lemon_code, target):
        cols = [c for c in cols if c not in ("engine_code",)]
        cur.execute(f"SELECT {','.join(cols)} FROM {table} WHERE engine_code=?", (lemon_code,))
        src = cur.fetchone()
        cur.execute(f"SELECT 1 FROM {table} WHERE engine_code=?", (target,))
        if src is None:
            return
        if cur.fetchone():
            sets = ", ".join(f"{c}=COALESCE({c}, ?)" for c in cols)
            cur.execute(f"UPDATE {table} SET {sets} WHERE engine_code=?", (*src, target))
        else:
            cur.execute(f"""INSERT INTO {table} (engine_code, {','.join(cols)})
                            VALUES (?, {','.join('?'*len(cols))})""", (target, *src))
        cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (lemon_code,))

    migrated = 0
    for lemon_code, vs in sorted(lemon_retired.items(), key=lambda kv: kv[1][0][1]):
        target = cur.execute("SELECT engine_code FROM vehicle_variants WHERE id=?", (vs[0][0],)).fetchone()[0]
        merge_specs("engine_service_specs", spec_cols_s, lemon_code, target)
        merge_specs("engine_technical_specs", spec_cols_t, lemon_code, target)
        # engines row: merge then delete lemon row
        cur.execute("SELECT count_variants FROM engines WHERE engine_code=?", (lemon_code,))
        r = cur.fetchone()
        n = r[0] if r else 0
        # fill NULL engine fields from lemon row before deleting (displacement/fuel)
        cur.execute("""UPDATE engines SET
              displacement_cc=COALESCE(displacement_cc, (SELECT displacement_cc FROM engines WHERE engine_code=?)),
              fuel=COALESCE(fuel, (SELECT fuel FROM engines WHERE engine_code=?))
              WHERE engine_code=?""", (lemon_code, lemon_code, target))
        cur.execute("UPDATE engines SET count_variants=count_variants+? WHERE engine_code=?", (n, target))
        cur.execute("DELETE FROM engines WHERE engine_code=?", (lemon_code,))
        migrated += 1

    con.commit()
    print(f"variants remapped: {len(decisions)} | lemon engine codes retired: {migrated}")

    # decisions CSV
    with open("database_enriched/csv_exports/17_lemon_replacement_decisions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions:
            w.writerow(list(d[:5]) + [d[5], d[7] or "", d[6]])

    # verification
    print("\n=== VERIFY ===")
    print("remaining LEMON in scope:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'
        AND car_brand||'|'||car_model IN (%s)""" % ",".join(f"'{b}|{m}'" for b in TARGETS for m in TARGETS[b])).fetchone()[0])
    print("total LEMON remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    print("engines count:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("variants:", cur.execute("SELECT COUNT(*) FROM vehicle_variants").fetchone()[0])
    print("v_vehicle_with_service:", cur.execute("SELECT COUNT(*) FROM v_vehicle_with_service").fetchone()[0])
    bad = cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0]
    print("orphan variant->engine refs:", bad)
    con.close()

if __name__ == "__main__":
    main()
