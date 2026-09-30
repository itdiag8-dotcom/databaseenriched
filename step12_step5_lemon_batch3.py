#!/usr/bin/env python3
"""
STEP 12 = USER-PLAN STEP 5 (batch 3): LEMON synthetic engine-code replacement, ALL FORD.
Scope: every remaining LEMON_FORD_* variant (~743) - cars, crossovers, trucks, vans, 2000-2024.

Method identical to steps 9/10: (model, year, cc, VIN-8th char, fuel, trim slug) -> real OEM
code, web-verified (see CITATIONS). Specs migrate onto real codes (ESTIMATE sources skipped);
LEMON rows retired; count_variants recomputed (step-11b lesson).
Gated: --apply to write. Backup: backups/car_database_backup_pre_step12_<date>.db
"""
import sqlite3, sys, re, shutil, csv
from datetime import date
from collections import defaultdict

DB = "database_enriched/car_database.db"
APPLY = "--apply" in sys.argv

CIT = {
    "FORDPRO14": "https://content.fordpro.com/content/dam/fordpro/ca/en-ca/pdf/fleet-vehicles/vin-lookup-and-guides/VIN2014.pdf (Ford fleet VIN guide, pos 8: 8 = 3.5L Ti-VCT V6 288hp; T = 3.5L GTDI V6 365hp)",
    "FORDPRO22": "https://content.fordpro.com/content/dam/fordpro/us/en-us/pdf/fleet-vehicles/vin-lookup-and-guides/2022-vin-guide.pdf (2022: H = 2.3L EcoBoost I-4; G = 3.5L GTDI High Output)",
    "FORDMASTERX": "https://fordmasterx.com/ford-vin-number-decoding-chart/ (8 = Cyclone 3.5 NA - F-150/Edge/Explorer; T = 3.5 EcoBoost TT - Transit/Police Interceptor; H = 2.3 EB I4 - Mustang/Ranger/Explorer; 9 = 2.0 EB I4 - Escape/Fusion/Edge; P = 2.7 Nano EB; F = Coyote 5.0)",
    "FTE35": "https://www.ford-trucks.com/forums/1783509-3-5-ho-or-non-ho.html (2019: standard 375hp 3.5 GTDI = VIN 4; 450hp HO = VIN T)",
    "F150VIN8": "https://www.ebay.com/itm/377236896659 + https://www.ebay.com/itm/177134021151 (F-150 2021-2023 3.5L EcoBoost turbo = VIN 8, 8th digit; VIN 1FTFW1E84MFA97848; Expedition 2022 3.5 = VIN T; Raptor = VIN G)",
    "MSTD": "https://www.ebay.com/itm/146838089143 (Mustang 2020-2023 2.3L VIN D, EcoBoost; VIN 1FA6P8TD3L5114302)",
    "MSTH": "https://www.americanmuscle.com/vin-basics.html (Mustang EcoBoost coupe P8T, engine code H = 2.3L 4-cyl)",
    "GOPARTS33": "https://www.go-parts.com/garage/ford-cyclone-engine-ford-explorer-ford-police-interceptor-utility-2020-2024 (2020-2024 Explorer/PIU 3.3: non-hybrid = VIN B; Hybrid = VIN W)",
    "PIU21": "https://www.futureford.com/models/2021/Ford/Police%20Interceptor%20Utility/ (2021 PIU: 3.3 V6 hybrid standard; 3.3 NA FFV; 3.0 EcoBoost 400hp; VINs 1FM5K8AC..=3.0EB, 1FM5K8AW..=hybrid)",
    "EXPL18": "https://fordauthority.com/fmc/ford/ford-explorer/2018-ford-explorer/2018-ford-explorer-engine/ (gen-5 Explorer: 3.5 NA 290 / 2.3 EB 280 XLT-Limited / 3.5 EB 365 Sport-Platinum; PIU 3.7 + 3.5 EB)",
    "EXPLAE": "https://www.autoevolution.com/cars/ford-explorer-2015.html (Explorer 2.3 EcoBoost 280hp replaced the 2.0 EB from 2016)",
    "TC19": "https://www.akinsford.com/blog/2020-ford-transit-connect-engine-options/ + https://www.automotive-fleet.com/327919/2019-ford-transit-connect (2019+ Transit Connect: 2.0 GDI 162hp std, 2.5 iVCT fleet/CNG, 1.5 diesel cancelled)",
    "VULCAN": "https://en.wikipedia.org/wiki/Ford_Vulcan_engine + https://en.wikipedia.org/wiki/Ford_Taurus_(fourth_generation) (2006-2007 Taurus = 3.0 Vulcan only)",
    "TAURUS58": "https://en.wikipedia.org/wiki/Ford_Taurus_(fifth_generation) (2008-2009 Taurus = 3.5 Duratec only)",
    "FREESTAR": "https://en.wikipedia.org/wiki/Ford_Windstar (Freestar 2004-2007: 3.9 and 4.2 both offered - ambiguous without cc)",
    "EXPED": "https://en.wikipedia.org/wiki/Ford_Expedition (3rd gen 2007-2014 = 5.4 Triton 24V V8 only; 3.5 EB 2015+)",
    "E24": "https://fordauthority.com/2023/02/2024-ford-e-series-drops-7-3l-v8-economy-engine/ (2024 E-Series = 7.3 Godzilla V8 325hp only)",
    "CV": "https://en.wikipedia.org/wiki/Ford_Crown_Victoria (Crown Victoria 1998-2011 = 4.6 V8 only)",
    "TBIRD": "https://en.wikipedia.org/wiki/Ford_Thunderbird_(eleventh_generation) (2002-2005 = 3.9 AJ35 V8 252-280hp)",
    "FGT": "https://en.wikipedia.org/wiki/Ford_GT (2005-2006 = 5.4 supercharged V8 550hp)",
    "F500": "https://en.wikipedia.org/wiki/Ford_Five_Hundred (2005-2007 Five Hundred + Freestyle = 3.0 Duratec V6 only)",
    "ESCORT": "https://en.wikipedia.org/wiki/Ford_Escort#North_America (1997-2002 Escort sedan/wagon = 2.0 SPI 8v; ZX2 = 2.0 Zetec 16v)",
    "FOCUS": "https://en.wikipedia.org/wiki/Ford_Focus (US Focus: 2008-2011 = 2.0 Duratec only; 2012-2018 = 2.0 GDI base, ST 2.0 EB, RS 2.3 EB 350hp, Focus Electric)",
    "MAV": "https://en.wikipedia.org/wiki/Ford_Maverick_(pickup_truck) (2022+: 2.5 I4 hybrid std, 2.0 EcoBoost opt)",
    "BRONCO": "https://en.wikipedia.org/wiki/Ford_Bronco_(2021) + https://en.wikipedia.org/wiki/Ford_Bronco_Sport (Bronco 2.3/2.7 EB, Raptor 3.0 EB; Bronco Sport 1.5/2.0 EB)",
    "ETRANSIT": "https://en.wikipedia.org/wiki/Ford_E-Transit (E-Transit 2022+ = electric, 266hp)",
    "ESCAPE": "https://en.wikipedia.org/wiki/Ford_Escape (Escape: 2.0 Zetec 01-04, 2.3 05-08 (+hybrid 2.3 05-08), 3.0 V6 01-12, 2.5 09-12 (+hybrid 2.5 09-12), 1.6/2.0/2.5 13-19, 1.5/2.0/2.5-hybrid 20+)",
    "MST4": "https://en.wikipedia.org/wiki/Ford_Mustang_(fourth_generation) (3.8 V6 94-04 (3.9 in 04); 4.6 GT)",
    "MST5": "https://en.wikipedia.org/wiki/Ford_Mustang_(fifth_generation) (4.0 V6 + 4.6 3V 05-10; 3.7 + 5.0 11-14; GT500 5.4 SC 07-12 500/550hp)",
    "MST6": "https://en.wikipedia.org/wiki/Ford_Mustang_(sixth_generation) (2.3 EB; 5.0; GT350 5.2 Voodoo 526hp 15-20; GT500 5.2 SC 760hp 20+; 5.8 SC GT500 13-14 662hp)",
    "RANGER": "https://en.wikipedia.org/wiki/Ford_Ranger_(North_America) (2.3 Duratec 01-11, 2.5 00-01, 3.0 Vulcan, 4.0 SOHC; 2019+ = 2.3 EcoBoost only, 2024 adds 2.7 EB)",
    "FIESTA": "https://en.wikipedia.org/wiki/Ford_Fiesta (US 2011-2019: 1.6 Ti-VCT base, 1.0 EB, ST 1.6 EB)",
    "EDGE": "https://en.wikipedia.org/wiki/Ford_Edge (Edge: 3.5 only 07-10; Sport 3.7 11-14; 2.0 EB 12-18; 2.7 EB Sport/ST 15+; 19+ = 2.0 EB only)",
    "FUSION": "https://en.wikipedia.org/wiki/Ford_Fusion_(Americas) (Fusion: 2.3 06-09, 3.0 06-12? (2.5 10+), 3.5 10-12, 1.6/1.5/2.0 EB 13+, 2.7 Sport 17+)",
    "FLEX": "https://en.wikipedia.org/wiki/Ford_Flex (Flex: 3.5 09+, EcoBoost 3.5 10+)",
    "ECO": "https://en.wikipedia.org/wiki/Ford_EcoSport (US 2018+: 1.0 EB / 2.0)",
    "CMAX": "https://en.wikipedia.org/wiki/Ford_C-Max (US C-Max 2013-2018 = Hybrid 2.0 Atkinson or Energi PHEV only)",
    "PI": "https://en.wikipedia.org/wiki/Ford_Police_Interceptor (Sedan 2013-19: 3.5 NA + 3.5 EB; Utility 13-19: 3.7 + 3.5 EB; 2020+: 3.3 NA/hybrid + 3.0 EB; Police Responder Hybrid Sedan 2019 = Fusion 2.0 hybrid)",
    "CONTOUR": "https://en.wikipedia.org/wiki/Ford_Contour (2000: 2.0 Zetec / 2.5 Duratec V6)",
    "WIND": "https://en.wikipedia.org/wiki/Ford_Windstar (Windstar: 3.0 + 3.8 V6)",
    "TCTRIM": "https://en.wikipedia.org/wiki/Ford_Transit_Connect (2014-2018 TC: 2.5 std, 1.6 EB opt; 2.5 Duratec family)",
}

# new engine rows: code -> (engine_type, fuel, cc, hp, cyl)
NEW_ENGINES = {
    "2.3 EcoBoost": ("2.3 I4 EcoBoost turbo", "Petrol", 2261, 310, 4),
    "1.6 EcoBoost": ("1.6 I4 EcoBoost turbo", "Petrol", 1596, 178, 4),
    "1.5 EcoBoost": ("1.5 I4 EcoBoost turbo", "Petrol", 1497, 181, 4),
    "1.0 EcoBoost": ("1.0 I3 EcoBoost turbo", "Petrol", 999, 123, 3),
    "2.5 I4 (Duratec 25)": ("2.5 I4 Duratec 25", "Petrol", 2488, 170, 4),
    "2.5 I4 Hybrid": ("2.5 I4 Atkinson hybrid (eCVT)", "Hybrid", 2488, 191, 4),
    "2.5 OHC (Lima)": ("2.5 I4 OHC (Lima)", "Petrol", 2500, 119, 4),
    "2.0 Duratec GDI": ("2.0 I4 Duratec GDI", "Petrol", 1999, 160, 4),
    "2.0 Atkinson Hybrid": ("2.0 I4 Atkinson hybrid (eCVT)", "Hybrid", 1999, 188, 4),
    "2.0 Energi (PHEV)": ("2.0 I4 Atkinson plug-in hybrid (Energi)", "Hybrid", 1999, 188, 4),
    "3.3 V6 Hybrid": ("3.3 V6 Ti-VCT hybrid (eCVT)", "Hybrid", 3317, 318, 6),
    "3.0 V6 EcoBoost": ("3.0 V6 EcoBoost twin-turbo", "Petrol", 2956, 400, 6),
    "3.9 V8 (AJ35)": ("3.9 V8 DOHC (Jaguar AJ35)", "Petrol", 3902, 280, 8),
    "3.9 V6 (Essex)": ("3.9 V6 OHV (Essex)", "Petrol", 3905, 190, 6),
    "5.4 V8 Supercharged (GT500)": ("5.4 V8 supercharged (Shelby GT500)", "Petrol", 5409, 550, 8),
    "5.8 V8 Supercharged (GT500)": ("5.8 V8 supercharged (Shelby GT500)", "Petrol", 5811, 662, 8),
    "5.2 V8 (Voodoo)": ("5.2 V8 flat-plane (Voodoo, GT350)", "Petrol", 5163, 526, 8),
    "5.4 V8 Supercharged (Ford GT)": ("5.4 V8 supercharged (Ford GT)", "Petrol", 5409, 550, 8),
    "2.0 SPI 8v": ("2.0 I4 SPI 8v (Split Port)", "Petrol", 1986, 110, 4),
    "E-Transit Electric": ("Electric motor (RWD)", "Electric", None, 266, None),
    "Focus Electric": ("Electric motor (FWD)", "Electric", None, 143, None),
}

FUEL_FIX = {
    "2.5 I4 Hybrid": "Hybrid", "3.3 V6 Hybrid": "Hybrid", "2.0 Energi (PHEV)": "Hybrid",
    "2.0 Atkinson Hybrid": "Hybrid", "E-Transit Electric": "Electric", "Focus Electric": "Electric",
}

RE_CC = re.compile(r"^LEMON_FORD_(.+?)_(\d{4})CC(?:_VIN(\w))?_(\d{4})$")
RE_BARE = re.compile(r"^LEMON_FORD_(.+?)_(\d{4})$")

def parse_code(code):
    """LEMON_FORD_* -> (cc, vin, code_year, trim_slug) using tail-anchored regex."""
    m = RE_CC.match(code)
    if m:
        return int(m.group(2)), m.group(3), int(m.group(4)), None
    m = re.match(r"^LEMON_FORD_(.+)_(\d{4})_([A-Z0-9]+)$", code)   # trim-slug tail
    if m:
        return None, None, int(m.group(2)), m.group(3)
    m = RE_BARE.match(code)
    if m:
        return None, None, int(m.group(2)), None
    return None

def decide(model, year, cc, vin, fuel, trim, code):
    """Return (new_code, note) or (None, reason)."""
    f = (fuel or "").lower()
    hybrid = "hybrid" in f

    # ================= MUSTANG =================
    if model == "Mustang":
        if cc == 3800: return ("3.8 V6", "Mustang 3.8 V6 Essex 2000-2004 [MST4]")
        if cc == 3900: return ("3.9 V6 (Essex)", "Mustang 3.9 V6 (2004 only, bored 3.8) [MST4]")
        if cc == 4000: return ("4.0 V6", "Mustang 4.0 SOHC V6 2005-2010 [MST5]")
        if cc == 4600: return ("4.6 V8", "Mustang 4.6 V8 (2V 99-04 / 3V 05-10) [MST4/MST5]")
        if cc == 5400: return ("5.4 V8 Supercharged (GT500)", "GT500 5.4 SC 500hp(07-09)/550hp(10-12) [MST5]")
        if cc == 5800: return ("5.8 V8 Supercharged (GT500)", "GT500 5.8 SC 662hp 2013-2014 [MST6]")
        if cc == 3700: return ("3.7 Ti-VCT V6", "Mustang 3.7 Cyclone 2011-2017 [MST6]")
        if cc == 5000: return ("5.0 Coyote V8", "Mustang GT 5.0 Coyote 2011+ [MST6]")
        if cc == 5200:
            if year == 2020: return (None, "2020 5.2 = GT350 (Voodoo) or GT500 (Predator) - ambiguous")
            if year <= 2020: return ("5.2 V8 (Voodoo)", "GT350 5.2 Voodoo NA (through 2020) [MST6]")
            return ("5.2 Predator V8", "GT500 5.2 SC 760hp 2020+ [MST6]")
        if cc == 2300:
            if vin == "D": return ("2.3 EcoBoost", "Mustang 2.3 EcoBoost = VIN D 2020-2023 [MSTD]")
            if vin == "H": return ("2.3 EcoBoost", "Mustang 2.3 EcoBoost = VIN H (P8T) [MSTH][FORDMASTERX]")
            return ("2.3 EcoBoost", "Mustang 2.3 EcoBoost 2015+ (only 4cyl) [MST6]")
        return (None, f"Mustang bare {year} (3.8/4.6 pre-11 or 2.3/5.0/Mach-E 21+) - ambiguous")

    # ================= ESCAPE =================
    if model == "Escape":
        if cc == 3000: return ("3.0 V6", "Escape 3.0 V6 Duratec 30 2001-2012 [ESCAPE]")
        if cc == 2000:
            if year <= 2004: return ("2.0 16v", "Escape 2.0 Zetec 2001-2004 [ESCAPE]")
            if year >= 2013: return ("2.0 T 16v Ecoboost", "Escape 2.0 EcoBoost = VIN 9 2013+ [FORDMASTERX][ESCAPE]")
            return (None, f"Escape 2.0 {year} - no NA 2.0 offered 2005-2012")
        if cc == 2300 and not hybrid: return ("2.3 16v", "Escape 2.3 Duratec base 2005-2008 [ESCAPE]")
        if cc == 2500:
            if hybrid or year >= 2020: return ("2.5 I4 Hybrid", "Escape 2.5 hybrid (09-12 HEV; 2020+ FHEV) [ESCAPE]")
            return ("2.5 I4 (Duratec 25)", "Escape 2.5 I4 = VIN 7 2009-2019 [ESCAPE][FORDMASTERX]")
        if cc == 1600: return ("1.6 EcoBoost", "Escape 1.6 EcoBoost = VIN X 2013-2016 [FORDMASTERX][ESCAPE]")
        if cc == 1500: return ("1.5 EcoBoost", "Escape 1.5 EcoBoost = VIN D(17-19)/6(20-22) [ESCAPE]")
        return (None, f"Escape bare {year} (2.3/3.0/hybrid) - ambiguous")

    # ================= EXPLORER =================
    if model == "Explorer":
        if cc == 4000: return ("4.0 V6", "Explorer 4.0 SOHC V6 2000-2010 [DB sibling]")
        if cc == 4600: return ("4.6 V8", "Explorer 4.6 V8 2002-2010 [DB sibling]")
        if cc == 5000: return ("5.0 V8", "Explorer 5.0 Windsor 2000-2001 [DB sibling]")
        if cc == 3500: return ("3.5 Cyclone V6", "Explorer 3.5 Ti-VCT = VIN 8 2011-2019 [FORDPRO14][EXPL18]")
        if cc == 3700: return ("3.7 Ti-VCT V6", "Explorer PIU 3.7 2013+ [EXPL18]")
        if cc == 2300: return ("2.3 EcoBoost", "Explorer 2.3 EcoBoost = VIN H, 280hp, 2016-2024 (replaced 2.0 EB 2016) [EXPLAE][EXPL18][FORDMASTERX]")
        if cc == 2000: return ("2.0 T 16v Ecoboost", "Explorer 2.0 EcoBoost = VIN 9, 2012-2015 [EXPLAE][FORDMASTERX]")
        if cc == 3300:
            if vin == "W" or hybrid: return ("3.3 V6 Hybrid", "Explorer 3.3 hybrid = VIN W 2020+ [GOPARTS33]")
            return ("3.3 Ti-VCT V6", "Explorer 3.3 NA = VIN B 2020+ [GOPARTS33]")
        if cc == 3000 and year >= 2020: return ("3.0 V6 EcoBoost", "Explorer ST / PIU 3.0 EcoBoost 400hp = VIN C 2020+ [PIU21]")
        return (None, f"Explorer bare {year} (4.0/4.6 or 3.5/EB) - ambiguous")

    # ================= EDGE =================
    if model == "Edge":
        if cc == 3500: return ("3.5 Cyclone V6", "Edge 3.5 Ti-VCT = VIN 8/C [FORDPRO14][EDGE]")
        if cc == 3700: return ("3.7 Ti-VCT V6", "Edge Sport 3.7 2011-2014 [EDGE]")
        if cc == 2000: return ("2.0 T 16v Ecoboost", "Edge 2.0 EcoBoost = VIN 9 2012-2018; 2019+ only gas engine [EDGE][FORDMASTERX]")
        if cc == 2700: return ("2.7 EcoBoost", "Edge Sport/ST 2.7 EcoBoost = VIN P 2015+ [EDGE][FORDMASTERX]")
        if cc is None:
            if 2007 <= year <= 2010: return ("3.5 Cyclone V6", "Edge 3.5 only 2007-2010 [EDGE]")
        return (None, f"Edge bare {year} (3.5 vs 3.7 Sport) - ambiguous")

    # ================= FUSION =================
    if model == "Fusion":
        if cc == 2300: return ("2.3 16v", "Fusion 2.3 Duratec 2006-2009 [FUSION]")
        if cc == 3000: return ("3.0 V6", "Fusion 3.0 Duratec 30 2006-2012 [FUSION]")
        if cc == 2500: return ("2.5 I4 (Duratec 25)", "Fusion 2.5 Duratec = VIN 7/A 2010-2020 [FUSION]")
        if cc == 3500: return ("3.5 Cyclone V6", "Fusion Sport 3.5 2010-2012 [FUSION]")
        if cc == 1600: return ("1.6 EcoBoost", "Fusion 1.6 EcoBoost = VIN R 2013-2015 [FUSION]")
        if cc == 1500: return ("1.5 EcoBoost", "Fusion 1.5 EcoBoost = VIN D 2014-2020 [FUSION]")
        if cc == 2000: return ("2.0 T 16v Ecoboost", "Fusion 2.0 EcoBoost = VIN 9 2013-2020 [FUSION][FORDMASTERX]")
        if cc == 2700: return ("2.7 EcoBoost", "Fusion Sport 2.7 EcoBoost 2017-2019 [FUSION]")
        return (None, "fusion unmatched")

    # ================= TAURUS =================
    if model == "Taurus":
        if cc == 3500:
            if vin == "T": return ("3.5 V6 EcoBoost", "Taurus SHO 3.5 EcoBoost = VIN T GTDI [FORDPRO14]")
            return ("3.5 Cyclone V6", "Taurus 3.5 Ti-VCT = VIN 8 2008+ [TAURUS58][FORDPRO14]")
        if cc == 3700: return ("3.7 Ti-VCT V6", "3.7 (PIU application) = VIN K [EXPL18]")
        if cc == 2000: return ("2.0 T 16v Ecoboost", "Taurus 2.0 EcoBoost = VIN 9 2013+ [FORDMASTERX]")
        if cc == 3000: return (None, "Taurus 3.0 2000-2005: Vulcan vs Duratec - ambiguous")
        if cc is None:
            if 2006 <= year <= 2007: return ("3.0 V6", "Taurus 2006-2007 fleet: 3.0 Vulcan only [VULCAN]")
            if 2008 <= year <= 2009: return ("3.5 Cyclone V6", "Taurus 2008-2009: 3.5 only [TAURUS58]")
        return (None, f"Taurus bare {year} (3.0 Vulc/Duratec or 3.5/SHO/2.0) - ambiguous")

    # ================= POLICE =================
    if model == "Police":
        if cc == 3500:
            if vin == "T": return ("3.5 V6 EcoBoost", "Taurus PI 3.5 EcoBoost = VIN T GTDI [PI][FORDPRO14]")
            return ("3.5 Cyclone V6", "Taurus PI 3.5 NA = VIN 8 [PI][FORDPRO14]")
        if cc == 3700: return ("3.7 Ti-VCT V6", "PIU 3.7 = VIN K/R 2013-2019 [PI][EXPL18]")
        if cc == 3300:
            if vin == "W": return ("3.3 V6 Hybrid", "PIU 3.3 hybrid = VIN W 2020+ [GOPARTS33][PIU21]")
            return ("3.3 Ti-VCT V6", "PIU 3.3 NA = VIN B 2020+ [GOPARTS33][PIU21]")
        if cc == 3000 and vin == "C": return ("3.0 V6 EcoBoost", "PIU 3.0 EcoBoost 400hp = VIN C 2020+ [PIU21]")
        if cc is None and hybrid:
            if year == 2019: return ("2.0 Atkinson Hybrid", "Police Responder Hybrid Sedan 2019 = Fusion 2.0 hybrid [PI]")
            return ("3.3 V6 Hybrid", "PIU hybrid 2020 = 3.3 [PI][PIU21]")
        return (None, "police unmatched")

    # ================= RANGER =================
    if model == "Ranger":
        if cc == 2300:
            if year <= 2011: return ("2.3 16v", "Ranger 2.3 Duratec 23 2001-2011 [RANGER]")
            return ("2.3 EcoBoost", "Ranger 2019+ = 2.3 EcoBoost only = VIN H [RANGER][FORDMASTERX]")
        if cc == 2500: return ("2.5 OHC (Lima)", "Ranger 2.5 OHC 1998-2001 [RANGER]")
        if cc == 3000:
            if year <= 2008: return ("3.0 V6", "Ranger 3.0 Vulcan 2000-2008 [RANGER]")
            return (None, "Ranger 3.0 petrol 2024 - not offered (intl diesel is Diesel) - skipped")
        if cc == 4000: return ("4.0 V6", "Ranger 4.0 SOHC 2000-2011 [RANGER]")
        if cc == 2700 and vin == "P": return ("2.7 EcoBoost", "Ranger 2.7 EcoBoost = VIN P 2024 [RANGER]")
        if cc is None and year >= 2019: return ("2.3 EcoBoost", "Ranger 2019+ only gas engine = 2.3 EcoBoost [RANGER]")
        return (None, "ranger unmatched")

    # ================= F-150 / PICKUP =================
    if model in ("F-150", "Pickup"):
        if cc == 3500:
            if vin == "4": return ("3.5 V6 EcoBoost", "F-150 3.5 EcoBoost std = VIN 4 (2019-2020) [FTE35]")
            if vin == "8" and year >= 2021: return ("3.5 V6 EcoBoost", "F-150 3.5 EcoBoost = VIN 8 (2021-2024) [F150VIN8]")
            if hybrid: return ("3.5 PowerBoost", "F-150 3.5 PowerBoost hybrid [FORDMASTERX]")
            if year >= 2021: return ("3.5 V6 EcoBoost", "F-150 3.5: petrol = EcoBoost (PB would be Hybrid) [F150VIN8]")
            if model == "Pickup" and year == 2011: return ("3.5 V6 EcoBoost", "2011 F-150 3.5 = EcoBoost only (NA 3.5 from 2015) [FORDMASTERX]")
            return (None, f"F-150 3.5 {year} no-VIN: NA vs EcoBoost - ambiguous")
        return (None, f"F-150 bare {year} (no engine signal) - skipped")

    # ================= BRONCO (incl. Bronco Sport rows) =================
    if model == "Bronco":
        if cc == 2300: return ("2.3 EcoBoost", "Bronco 2.3 EcoBoost = VIN H 2021+ [BRONCO][FORDMASTERX]")
        if cc == 2700: return ("2.7 EcoBoost", "Bronco 2.7 EcoBoost = VIN P 2021+ [BRONCO]")
        if cc == 3000 and year >= 2022: return ("3.0 V6 EcoBoost", "Bronco Raptor 3.0 EcoBoost 2022+ [BRONCO]")
        if cc == 1500: return ("1.5 EcoBoost", "Bronco Sport 1.5 EcoBoost 2021+ [BRONCO]")
        if cc == 2000: return ("2.0 T 16v Ecoboost", "Bronco Sport 2.0 EcoBoost 2021+ [BRONCO]")
        return (None, "bronco unmatched")

    # ================= MAVERICK =================
    if model == "Maverick":
        if cc == 2000: return ("2.0 T 16v Ecoboost", "Maverick 2.0 EcoBoost = VIN 9 [MAV][FORDMASTERX]")
        if cc == 2500: return ("2.5 I4 Hybrid", "Maverick 2.5 hybrid = VIN 3 [MAV]")
        return (None, "maverick unmatched")

    # ================= FLEX =================
    if model == "Flex":
        if cc == 3500:
            if vin == "T": return ("3.5 V6 EcoBoost", "Flex EcoBoost 3.5 = VIN T GTDI [FORDPRO14][FLEX]")
            return ("3.5 Cyclone V6", "Flex 3.5 Ti-VCT = VIN 8/C [FORDPRO14][FLEX]")
        if cc is None and year == 2009: return ("3.5 Cyclone V6", "Flex 2009 = 3.5 only (EB from 2010) [FLEX]")
        return (None, f"Flex bare {year} (3.5 vs EcoBoost) - ambiguous")

    # ================= TRANSIT / TRANSIT-350 =================
    if model == "Transit":
        if cc == 1600: return ("1.6 EcoBoost", "Transit Connect 1.6 EcoBoost = VIN X 2014-2016 [TCTRIM]")
        if cc == 2000 and year >= 2019: return ("2.0 Duratec GDI", "Transit Connect 2.0 GDI 162hp = VIN 2 2019+ [TC19]")
        if cc == 2500: return ("2.5 I4 (Duratec 25)", "Transit Connect 2.5 iVCT (fleet/CNG) = VIN 7 [TC19]")
        return (None, "Transit bare (Connect vs full-size mixed) - skipped")
    if model == "Transit-350":
        return (None, "Transit-350 3.5 2015: NA vs EcoBoost vs 3.2d - ambiguous")

    # ================= ECOSPORT / FIESTA / FOCUS =================
    if model == "Ecosport":
        if cc == 1000: return ("1.0 EcoBoost", "Ecosport 1.0 EcoBoost = VIN E [ECO]")
        if cc == 2000: return ("2.0 Duratec", "Ecosport 2.0 = VIN L (DB sibling row) [ECO]")
        return (None, "ecosport unmatched")
    if model == "Fiesta":
        if cc == 1000: return ("1.0 EcoBoost", "Fiesta 1.0 EcoBoost = VIN E [FIESTA]")
        if cc == 1600: return ("1.6 16v", "Fiesta 1.6 Ti-VCT = VIN J (Sigma DOHC) [FIESTA]")
        if cc is None: return ("1.6 16v", "US Fiesta base = 1.6 only (ST would be trim-coded) [FIESTA]")
        return (None, "fiesta unmatched")
    if model == "Focus":
        if cc == 1000: return ("1.0 EcoBoost", "Focus 1.0 EcoBoost = VIN E [FOCUS]")
        if cc == 1600: return (None, "Focus 1.6 - not US engine, check")
        if cc == 2000:
            if year <= 2004: return (None, "Focus 2.0 2000-2004: Zetec vs SPI - ambiguous")
            if year >= 2012: return ("2.0 Duratec GDI", "Focus 2.0 GDI = VIN 2 2012-2018 [FOCUS]")
            return (None, f"Focus 2.0 {year} - unexpected")
        if cc == 2300:
            if year == 2004: return ("2.3 16v", "Focus 2.3 PZEV Duratec 23 2004 [FOCUS]")
            if year >= 2016: return ("2.3 EcoBoost", "Focus RS 2.3 EcoBoost 350hp 2016-2018 [FOCUS]")
            return (None, f"Focus 2.3 {year} - unexpected")
        if trim and "ELECTRI" in trim: return ("Focus Electric", "Focus Electric trim [FOCUS]")
        if cc is None:
            if 2008 <= year <= 2011: return ("2.0 Duratec", "US Focus 2008-2011 = 2.0 Duratec only [FOCUS]")
            if 2012 <= year <= 2018: return ("2.0 Duratec GDI", "US Focus 2012-2018 base = 2.0 GDI (ST/EV/RS trim-coded) [FOCUS]")
        return (None, f"Focus bare {year} (Zetec/SPI/Duratec) - ambiguous")

    # ================= C-MAX =================
    if model == "C-Max":
        if hybrid or (trim and "HYBRID" in trim): return ("2.0 Atkinson Hybrid", "C-Max Hybrid 2.0 Atkinson [CMAX]")
        if trim and "ENERGI" in trim: return ("2.0 Energi (PHEV)", "C-Max Energi PHEV trim [CMAX]")
        return ("2.0 Energi (PHEV)", "US C-Max = Hybrid or Energi only; petrol-labelled row = Energi [CMAX]")

    # ================= single-engine classics =================
    if model == "Crown": return ("4.6 V8", "Crown Victoria = 4.6 V8 only 1998-2011 [CV]")
    if model == "Thunderbird" and 2002 <= year <= 2005: return ("3.9 V8 (AJ35)", "Thunderbird 11th gen = 3.9 AJ35 V8 only [TBIRD]")
    if model == "GT" and 2005 <= year <= 2006: return ("5.4 V8 Supercharged (Ford GT)", "Ford GT = 5.4 SC V8 550hp only [FGT]")
    if model == "Five" and 2005 <= year <= 2007: return ("3.0 V6", "Five Hundred 2005-2007 = 3.0 Duratec only [F500]")
    if model == "Freestyle" and 2005 <= year <= 2007: return ("3.0 V6", "Freestyle 2005-2007 = 3.0 Duratec only [F500]")
    if model == "Contour" and year == 2000:
        if cc == 2000: return ("2.0 16v", "Contour 2.0 Zetec [CONTOUR]")
        if cc == 2500: return ("2.5 V6", "Contour 2.5 Duratec V6 [CONTOUR]")
        return (None, "contour unmatched")
    if model == "ZX2": return ("2.0 16v", "Escort ZX2 = 2.0 Zetec only [ESCORT]")
    if model == "Escort" and cc is None: return ("2.0 SPI 8v", "US Escort sedan/wagon = 2.0 SPI only 2000-2002 (ZX2 separate model) [ESCORT]")
    if model == "Windstar":
        if cc == 3000: return ("3.0 V6", "Windstar 3.0 Vulcan [WIND]")
        if cc == 3800: return ("3.8 V6", "Windstar 3.8 Essex [WIND]")
        return (None, "Windstar bare (3.0 vs 3.8) - ambiguous")
    if model == "Freestar": return (None, "Freestar 3.9 vs 4.2 both offered - ambiguous [FREESTAR]")
    if model == "Excursion": return (None, "Excursion 5.4/6.8/7.3/6.0 - ambiguous")
    if model == "Expedition":
        if cc == 5400 and year <= 2004: return ("5.4 Triton 2V", "Expedition 5.4 2V through 2004 [EXPED]")
        if cc is None and year >= 2007: return ("5.4 Triton 3V", "Expedition 3rd gen 2007+ = 5.4 Triton 24V only [EXPED]")
        return (None, f"Expedition {year} (4.6 vs 5.4) - ambiguous")

    # ================= E-series / Super Duty =================
    if model == "Cutaway": return (None, "E-Series Cutaway 5.4/6.8/7.3/6.0 - ambiguous")
    if model in ("E450", "E550"):
        if cc == 6800: return ("6.8 Triton V10 2V", "E-550 6.8 V10 2002-2003 [DB sibling]")
        if cc == 7300: return ("7.3 Power Stroke", "E-550 7.3 PSD 2002-2003 [DB sibling]")
        return (None, "E-450/E-550 bare 5.4/6.8/7.3/6.0 - ambiguous")
    if model in ("E-350", "E-450") and cc is None and year >= 2024:
        return ("7.3 Godzilla V8", "2024 E-Series cutaway = 7.3 Godzilla V8 only 325hp [E24]")
    if model == "E-Transit": return ("E-Transit Electric", "E-Transit 2022+ = electric only [ETRANSIT]")
    if model in ("F450", "F550"):
        if cc == 7300: return ("7.3 Power Stroke", "Super Duty 7.3 PSD 2000-2003 [DB sibling]")
        if cc == 6000: return ("6.0 Power Stroke", "Super Duty 6.0 PSD 2003-2007 [DB sibling]")
        if cc == 6400: return ("6.4 Power Stroke", "Super Duty 6.4 PSD 2008-2010 [DB sibling]")
        if cc == 6800: return ("6.8 Triton V10 2V", "Super Duty 6.8 V10 2V 2005-2012 [DB sibling]")
        if cc == 6700: return ("6.7 Power Stroke", "Super Duty 6.7 PSD 2011+ [DB sibling]")
        return (None, "F-450/F-550 bare (6.8 vs 7.3) - ambiguous")
    if model in ("Special", "SSV"): return (None, "Special Service Vehicle - model unknown (Explorer/F-150/Expedition) - skipped")

    return (None, f"UNHANDLED model {model!r} cc={cc} vin={vin} year={year}")


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys=ON")

    rows = list(cur.execute("""SELECT id, car_brand, car_model, car_year, fuel, engine_code
        FROM vehicle_variants WHERE engine_code LIKE 'LEMON_FORD%'""").fetchall())
    print(f"LEMON_FORD variants in scope: {len(rows)}")
    decisions, unmapped = [], []
    for vid, brand, model, year, fuel, code in rows:
        p = parse_code(code)
        if not p:
            unmapped.append((vid, brand, model, year, code, "unparseable")); continue
        cc, vin, ycode, trim = p
        new_code, note = decide(model, year, cc, vin, fuel, trim, code)
        if not new_code:
            unmapped.append((vid, brand, model, year, code, note)); continue
        ff = FUEL_FIX.get(new_code)
        if ff and (fuel or "").lower() != ff.lower():
            fuel_fix = ff
        else:
            fuel_fix = None
        decisions.append((vid, brand, model, year, code, new_code, note, fuel_fix))

    print(f"mapped: {len(decisions)} | skipped: {len(unmapped)}")
    print("=== SKIPPED groups ===")
    reasons = defaultdict(list)
    for vid, brand, model, year, code, why in unmapped:
        reasons[(model, why)].append((year, code))
    for k in sorted(reasons, key=lambda k: -len(reasons[k])):
        print(f"  {k}: {len(reasons[k])} rows  e.g. {reasons[k][:3]}")

    # sanity: all targets exist or are new
    existing = {r[0] for r in cur.execute("SELECT engine_code FROM engines")}
    missing = {d[5] for d in decisions} - existing - set(NEW_ENGINES.keys())
    if missing:
        print("FATAL: targets missing from engines and NEW_ENGINES:", missing); sys.exit(1)

    if not APPLY:
        with open("database_enriched/csv_exports/20_lemon_batch3_decisions_DRYRUN.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["variant_id", "brand", "model", "year", "old_engine_code", "new_engine_code", "fuel_fix", "evidence"])
            for d in decisions:
                w.writerow([d[0], d[1], d[2], d[3], d[4], d[5], d[7] or "", d[6]])
        print("DRY RUN - no changes. Re-run with --apply.")
        con.close(); return

    # ---------- APPLY ----------
    bak = f"database_enriched/backups/car_database_backup_pre_step12_{date.today().isoformat()}.db"
    shutil.copy(DB, bak)
    print(f"backup: {bak}")

    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,))
        if not cur.fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP12_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
            print(f"  created engine row {code}")

    lemon_retired = defaultdict(list)
    for vid, brand, model, year, old, new, note, fuel_fix in decisions:
        cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=COALESCE(?, fuel) WHERE id=?", (new, fuel_fix, vid))
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=COALESCE(engine_power_hp,
                        (SELECT power_hp FROM engines WHERE engine_code=?)),
                        engine_type=COALESCE(engine_type, (SELECT engine_type FROM engines WHERE engine_code=?))
                        WHERE id=?""", (new, new, vid))
        lemon_retired[old].append((vid, year, brand, model))

    spec_cols_s = [c[1] for c in cur.execute("PRAGMA table_info(engine_service_specs)")]
    spec_cols_t = [c[1] for c in cur.execute("PRAGMA table_info(engine_technical_specs)")]

    def merge_specs(table, cols, lemon_code, target):
        cols = [c for c in cols if c != "engine_code"]
        cur.execute(f"SELECT {','.join(cols)} FROM {table} WHERE engine_code=?", (lemon_code,))
        src = cur.fetchone()
        if src is None:
            return
        # don't propagate ESTIMATE placeholder specs
        if table == "engine_service_specs":
            cur.execute("SELECT oil_spec_source FROM engine_service_specs WHERE engine_code=?", (lemon_code,))
            srow = cur.fetchone()
            if srow and srow[0] and "ESTIMATE" in srow[0].upper():
                cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (lemon_code,))
                return
        cur.execute(f"SELECT 1 FROM {table} WHERE engine_code=?", (target,))
        if cur.fetchone():
            sets = ", ".join(f"{c}=COALESCE({c}, ?)" for c in cols)
            cur.execute(f"UPDATE {table} SET {sets} WHERE engine_code=?", (*src, target))
        else:
            cur.execute(f"INSERT INTO {table} (engine_code, {','.join(cols)}) VALUES (?, {','.join('?'*len(cols))})", (target, *src))
        cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (lemon_code,))

    migrated = 0
    for lemon_code, vs in sorted(lemon_retired.items(), key=lambda kv: kv[1][0][1]):
        target = cur.execute("SELECT engine_code FROM vehicle_variants WHERE id=?", (vs[0][0],)).fetchone()[0]
        merge_specs("engine_service_specs", spec_cols_s, lemon_code, target)
        merge_specs("engine_technical_specs", spec_cols_t, lemon_code, target)
        cur.execute("""UPDATE engines SET displacement_cc=COALESCE(displacement_cc,
              (SELECT displacement_cc FROM engines WHERE engine_code=?)),
              fuel=COALESCE(fuel, (SELECT fuel FROM engines WHERE engine_code=?)) WHERE engine_code=?""",
              (lemon_code, lemon_code, target))
        cur.execute("DELETE FROM engines WHERE engine_code=?", (lemon_code,))
        migrated += 1

    # recompute count_variants from actual links (step-11b lesson)
    cur.execute("""UPDATE engines SET count_variants =
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")
    con.commit()
    print(f"variants remapped: {len(decisions)} | LEMON engine codes retired: {migrated}")

    print("=== VERIFY ===")
    print("LEMON_FORD remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_FORD%'").fetchone()[0])
    print("LEMON total remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e
        ON e.engine_code=v.engine_code WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM (SELECT e.engine_code FROM engines e
        LEFT JOIN vehicle_variants v ON v.engine_code=e.engine_code
        GROUP BY e.engine_code HAVING e.count_variants != COUNT(v.id))""").fetchone()[0])
    print("engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("top targets:")
    for r in cur.execute("""SELECT engine_code, COUNT(*) FROM vehicle_variants
        WHERE engine_code IN (SELECT engine_code FROM vehicle_variants) GROUP BY 1
        ORDER BY 2 DESC LIMIT 15"""):
        pass  # placeholder
    from collections import Counter
    cnt = Counter(d[5] for d in decisions)
    for code, n in cnt.most_common(25):
        print(f"   {n:3}  {code}")

    with open("database_enriched/csv_exports/20_lemon_batch3_decisions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant_id", "brand", "model", "year", "old_engine_code", "new_engine_code", "fuel_fix", "evidence"])
        for d in decisions:
            w.writerow([d[0], d[1], d[2], d[3], d[4], d[5], d[7] or "", d[6]])
    con.close()
    print("decisions CSV: database_enriched/csv_exports/20_lemon_batch3_decisions.csv")


main()
