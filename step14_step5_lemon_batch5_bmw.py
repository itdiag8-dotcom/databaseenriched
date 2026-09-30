"""Step 14 (user-plan Step 5, batch 5): replace LEMON_BMW codes with real OEM engine codes.
780 rows, 91 models. Rules keyed on (model, year range), with cc signal (e.g. LEMON_BMW_X5_3000CC_2016)
required for X3/X4/X5/X6/X7/Z4. All generation splits web-verified (see CIT).
Bare rows with no engine signal (X2, Z3, 'M', ActiveHybrid, no-cc X/Z, X1 2024+) skipped by design.
"""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "WIKIF01": "https://en.wikipedia.org/wiki/BMW_7_Series_(F01) (740i/Li N54->N55 at 2013 FL, 315hp; 750i/Li N63->N63TU 2013; AH7 N63->N55)",
    "BMWLOG740": "https://www.bmwblog.com/2010/05/18/first-drive-2011-bmw-740i/ (2011 740Li = N54TT 315hp)",
    "USPG11": "https://www.ultimatespecs.com/car-specs/BMW/115898/BMW-G11-LCI-7-Series--750i-xDrive.html (G11 LCI 2019+ 750i = 523hp N63TU2; 2016-18 = 445hp)",
    "DRIVE760": "https://www.thedrive.com/car-reviews/2023-bmw-760i-xdrive-review-specs-price-options-impressions (2023+ G70 760i = S68 4.4TT 536hp)",
    "BMWLOG760": "https://www.bmwblog.com/2023/08/15/2023-bmw-760i-xdrive-review/ (760i S68 536hp)",
    "AUTOEV540D": "https://www.autoevolution.com/news/bmw-530d-coming-to-the-us-as-540d-for-2018-model-year-117362.html (US 540d = B57D30 261hp)",
    "CARS540D": "https://www.cars.com/research/bmw-540d-2018/specs/ (540d 261hp 3.0TT I6 diesel)",
    "HPSB7": "https://www.horsepowerspecs.com/model/bmw-alpina-b7/ (Alpina B7: 2011-12 500hp, 2013-15 540hp, 2017-20 600hp)",
    "CDB7": "https://www.caranddriver.com/reviews/a15115507/2013-bmw-alpina-b7-lwb-xdrive-test-review/ (2013 B7 = N63TU-based 540hp)",
    "EDMB7": "https://www.edmunds.com/bmw/alpina-b7/2011/review/ (2011 B7 = 500hp TT 4.4 V8)",
    "MMXB7": "https://www.motormatchup.com/catalog/BMW/ALPINA-XB7/2021/ALPINA-XB7 (2021+ XB7 = 612hp)",
    "CARBUZZM2": "https://carbuzz.com/cars/bmw/m2/generations/ (M2: 2016-18 N55 365hp, 2019-21 Comp S55 405hp, 2023+ G87 S58 453hp)",
    "CDX5M50I": "https://www.caranddriver.com/reviews/a30864883/2020-bmw-x5-m50i-by-the-numbers/ (2020+ M50i 523hp vs 50i 456hp)",
    "KBBX5": "https://www.kbb.com/bmw/x5/2024/specs/ (2024 X5 40i 375hp, M60i 523hp)",
    "KBBX1": "https://www.kbb.com/bmw/x1/2023/ (2023 X1 US = xDrive28i only, 241hp)",
    "CDX1": "https://www.carandriver.com/bmw/x1-2024 (X1 28i 241hp; M35i 312hp from 2024)",
    "CARI3": "https://www.thecarconnection.com/overview/bmw_i3_2014 (i3 = 170hp electric motor)",
    "AEVI3": "https://www.autoevolution.com/bmw/i3/ (i3 170hp all years; i3s 184hp)",
    "AEV323I": "https://www.auto-data.net/en/bmw-3-series-sedan-e90-lci-facelift-2008-323i-200hp-steptronic-43747 (E90 323i = N52B25 200hp)",
    "EBAY323": "https://www.ebay.com/itm/306980391568 (2006-2011 323i = N52B25)",
    "WIKIN20": "https://en.wikipedia.org/wiki/BMW_N20_engine (N20B20 2.0T: 240hp US 28i/328i tune)",
    "WIKIN55": "https://en.wikipedia.org/wiki/BMW_N55_engine (N55B30 300hp 335i/535i/640i; M235i 320hp; M2 N55B30T0 365hp)",
    "WIKIS55": "https://en.wikipedia.org/wiki/BMW_S55_engine (S55 M3/M4 425-444hp; M2 Comp 405hp; M2 CS 444hp)",
    "WIKIS58": "https://en.wikipedia.org/wiki/BMW_S58_engine (S58 G80 M3/G82 M4 473/503hp; G87 M2 453hp)",
    "WIKIN63": "https://en.wikipedia.org/wiki/BMW_N63_engine (N63 400hp; N63TU 445hp; N63TU2 523hp M550i/M850i/M50i)",
    "WIKIM54": "https://en.wikipedia.org/wiki/BMW_M54_engine (M54B25 184hp US, M54B30 225hp US)",
    "WIKIN52": "https://en.wikipedia.org/wiki/BMW_N52_engine (N52B25 215hp US 525i; N52B30 255hp US 330i; N51 US SULEV 230hp)",
    "WIKIN62": "https://en.wikipedia.org/wiki/BMW_N62_engine (N62B44 325hp 545i/745i/645Ci; E53 X5 4.4i 2004+ N62 315hp)",
    "WIKIM62": "https://en.wikipedia.org/wiki/BMW_M62_engine (M62B44TU 282hp 540i/740i/X5 4.4i)",
    "WIKIS62": "https://en.wikipedia.org/wiki/BMW_S62_engine (S62B50 394hp E39 M5/Z8)",
    "WIKIS54": "https://en.wikipedia.org/wiki/BMW_S54_engine (S54B32US 333hp E46 M3)",
    "WIKIS65": "https://en.wikipedia.org/wiki/BMW_S65_engine (S65B40 414hp E9x M3)",
    "WIKIS85": "https://en.wikipedia.org/wiki/BMW_S85_engine (S85B50 500hp E60 M5/E63 M6)",
    "WIKIS63": "https://en.wikipedia.org/wiki/BMW_S63_engine (S63B44 F10 M5/M6 560hp; F90 M5/M8 600-617hp)",
    "WIKIN73": "https://en.wikipedia.org/wiki/BMW_N73_engine (N73B60 438hp E65 760i)",
    "WIKIN74": "https://en.wikipedia.org/wiki/BMW_N74_engine (N74B60 535hp F01 760Li; N74B66 601hp M760i)",
    "WIKIM73": "https://en.wikipedia.org/wiki/BMW_M73_engine (M73B54 322hp E38 750iL)",
    "WIKII8": "https://en.wikipedia.org/wiki/BMW_i8 (i8 = B38 1.5 I3 turbo PHEV, 357hp combined; 2019+ 369hp)",
    "WIKIX5E53": "https://en.wikipedia.org/wiki/BMW_X5_(E53) (E53: 3.0i M54 225, 4.4i M62TU->N62 2004, 4.6is M62B46 340, 4.8is N62B48 355)",
    "WIKIX5F15": "https://en.wikipedia.org/wiki/BMW_X5_(F15) (F15: 35i N55 300, 50i N63TU 445, 40e N20 PHEV 308)",
    "WIKIX5G05": "https://en.wikipedia.org/wiki/BMW_X5_(G05) (G05: 40i B58 335, M50i N63TU2 523, 2024 LCI 40i 375/M60i)",
    "WIKIX3G01": "https://en.wikipedia.org/wiki/BMW_X3 (F25 28i N20/35i N55; G01 30i B48 248, M40i B58 355-382)",
    "WIKIX7": "https://en.wikipedia.org/wiki/BMW_X7 (G07: 40i B58 335, xDrive50i 456, M50i/M60i 523)",
    "WIKIZ4": "https://en.wikipedia.org/wiki/BMW_Z4_(G29) (G29 sDrive30i B48 255, M40i B58 382; E89 sDrive28i N20/sDrive35i N55)",
    "WIKI340": "https://en.wikipedia.org/wiki/BMW_3_Series_(F30) (F30: 328i N20 240, 320i 180, 335i N55, 340i B58 320, 330i 2017+ B48 248)",
    "WIKI3G20": "https://en.wikipedia.org/wiki/BMW_3_Series_(G20) (G20: 330i B48 255, M340i B58 382, 330e 288)",
    "WIKI5G30": "https://en.wikipedia.org/wiki/BMW_5_Series_(G30) (G30: 530i B48 248, 540i B58 335, M550i N63TU2, 530e 248/288)",
    "WIKI5E60": "https://en.wikipedia.org/wiki/BMW_5_Series_(E60) (E60: 525i/530i M54 2004-05 -> N52 2006+, 528i N52 230, 535i N54 300, 550i N62B48 360)",
    "WIKI5F10": "https://en.wikipedia.org/wiki/BMW_5_Series_(F10) (F10: 528i N20 240, 535i N55 300, 550i N63 400/445, M5 S63 560)",
    "WIKI7E65": "https://en.wikipedia.org/wiki/BMW_7_Series_(E65) (E65: 745i N62B44 325, 750i N62B48 360, 760i N73 438)",
    "WIKI6E63": "https://en.wikipedia.org/wiki/BMW_6_Series_(E63) (E63: 645Ci N62B44 325, 650i N62B48 360; M6 S85)",
    "WIKI6F12": "https://en.wikipedia.org/wiki/BMW_6_Series_(F12) (F12/13/06: 640i N55 315, 650i N63 400/445, M6 S63 560)",
    "WIKI8": "https://en.wikipedia.org/wiki/BMW_8_Series_(G15) (G15: 840i B58 335, M850i N63TU2 523, M8 S63 600/617)",
    "WIKI2F22": "https://en.wikipedia.org/wiki/BMW_2_Series_(F22) (F22: 228i N20/B48 228-241, M235i N55 320, M240i B58 335)",
    "WIKI2G42": "https://en.wikipedia.org/wiki/BMW_2_Series_(G42) (G42: 230i B48 255, M240i B58 382)",
    "WIKI1M": "https://en.wikipedia.org/wiki/BMW_1_Series_M (1M = N54B30 335hp)",
    "WIKIX1F48": "https://en.wikipedia.org/wiki/BMW_X1 (F48 X1 28i = B46/B48 228hp)",
    "WIKIX2": "https://en.wikipedia.org/wiki/BMW_X2 (F39: 228i B48 228, M35i B48A20T1 301 - trim unknown on bare rows)",
    "WIKIN47": "https://en.wikipedia.org/wiki/BMW_N47_engine (N47D20 US 328d 180hp)",
    "WIKIM57": "https://en.wikipedia.org/wiki/BMW_M57_engine (M57D30T2 US 335d 265hp; N57 535d 255hp)",
    "AMSOILX5": "https://www.amsoil.com/lookup/auto-and-light-truck/2016/bmw/x5/2-0l-4-cyl-engine-code-n20-b/ (X5 xDrive40e 2.0 PHEV)",
}

# new engines: code -> (engine_type, fuel, cc, hp, cylinders)
NEW_ENGINES = {
    "N20B20 (328i/28i US)":        ("2.0 I4 Turbo (N20, US 240hp)", "Petrol", 1997, 240, 4),
    "N20 2.0 PHEV (X5 40e)":       ("2.0 I4 Turbo PHEV (X5 xDrive40e)", "Hybrid", 1997, 308, 4),
    "B48B20 (30i)":                ("2.0 I4 Turbo (B48, 30i 248-255hp)", "Petrol", 1998, 255, 4),
    "B48 2.0 PHEV (30e)":          ("2.0 I4 Turbo PHEV (330e/530e)", "Hybrid", 1998, 288, 4),
    "B48 2.0 PHEV (740e)":         ("2.0 I4 Turbo PHEV (740e)", "Hybrid", 1998, 322, 4),
    "B58 3.0 PHEV (745e)":         ("3.0 I6 Turbo PHEV (745e)", "Hybrid", 2998, 389, 6),
    "B58B30 (40i)":                ("3.0 I6 Turbo (B58, 40i 320-375hp)", "Petrol", 2998, 335, 6),
    "B58B30 (M40i/M340i)":         ("3.0 I6 Turbo (B58, M40i/M340i 355-382hp)", "Petrol", 2998, 382, 6),
    "S58B30 (M3/M4)":              ("3.0 I6 TwinTurbo (S58, G80/G82)", "Petrol", 2999, 473, 6),
    "S58B30 (M2)":                 ("3.0 I6 TwinTurbo (S58, G87 M2)", "Petrol", 2999, 453, 6),
    "S55B30 (M2 Comp)":            ("3.0 I6 TwinTurbo (S55, M2 Comp/CS)", "Petrol", 2979, 405, 6),
    "N55B30 (M2)":                 ("3.0 I6 Turbo (N55B30T0, M2 365hp)", "Petrol", 2979, 365, 6),
    "N55B30 (M235i/135is)":        ("3.0 I6 Turbo (N55, M235i/135is 320hp)", "Petrol", 2979, 320, 6),
    "B48 2.0T (M235i GC)":         ("2.0 I4 Turbo (B48A20T1, M235i Gran Coupe 301hp)", "Petrol", 1998, 301, 4),
    "S63B44T2 (M5 F90/M8)":        ("4.4 V8 TwinTurbo (S63B44T2, F90 M5/G15 M8)", "Petrol", 4394, 600, 8),
    "N63B44TU2 (523hp)":           ("4.4 V8 TwinTurbo (N63TU2, M550i/M850i/M50i/M60i/750i)", "Petrol", 4395, 523, 8),
    "S68 4.4 V8 BiTurbo":          ("4.4 V8 TwinTurbo 48V (S68, G70 760i)", "Petrol", 4395, 536, 8),
    "B57D30 (540d)":               ("3.0 I6 TT Diesel (B57, US 540d)", "Diesel", 2993, 261, 6),
    "N47D20 (328d)":               ("2.0 I4 TT Diesel (N47, US 328d 180hp)", "Diesel", 1995, 180, 4),
    "i3 Electric (I01)":           ("Electric motor (i3, 170hp; i3s 184hp)", "Electric", None, 170, None),
    "Alpina B7 (E65) 4.4 SC":      ("4.4 V8 Supercharged (Alpina B7 E65)", "Petrol", 4398, 500, 8),
    "Alpina B7/B6 (F01/F06) 4.4TT":("4.4 V8 TwinTurbo (Alpina B7/B6)", "Petrol", 4395, 540, 8),
    "Alpina B7 (G12) 4.4TT":       ("4.4 V8 TwinTurbo (Alpina B7 G12)", "Petrol", 4395, 600, 8),
    "Alpina B7/XB7/B8 (G12) 4.4TT":("4.4 V8 TwinTurbo (Alpina B7/XB7/B8)", "Petrol", 4395, 612, 8),
}

ROW_FIXES = {
    "B3815KT0": {"engine_type": "1.5 I3 Turbo PHEV (i8, 357hp comb.)", "fuel": "Hybrid", "displacement_cc": 1499, "power_hp": 357},
    "M62B44TU": {"displacement_cc": 4398},
    "N62B44":   {"displacement_cc": 4398},
    "M52TUB28": {"displacement_cc": 2793, "power_hp": 193},
    "M52TUB25": {"displacement_cc": 2494, "power_hp": 170},
    "N52B25U1": {"displacement_cc": 2497, "power_hp": 200},
    "N51B30US": {"displacement_cc": 2996},
    "N54B30O0": {"displacement_cc": 2979},
    "N55B30A":  {"displacement_cc": 2979},
    "M57D30T2": {"displacement_cc": 2993},
    "N63B44B":  {"engine_type": "4.4 V8 TwinTurbo (N63TU)", "displacement_cc": 4395},
    "N62B48B":  {"engine_type": "4.8 V8 (N62)"},
    "N74B60A":  {"engine_type": "6.0 V12 TwinTurbo (N74)"},
    "N74B66A":  {"engine_type": "6.6 V12 TwinTurbo (N74)"},
}

N20US = "N20B20 (328i/28i US)"
B30I = "B48B20 (30i)"
B5840 = "B58B30 (40i)"
B58M40 = "B58B30 (M40i/M340i)"
N63TU = "N63B44B"
N63TU2 = "N63B44TU2 (523hp)"
S63T2 = "S63B44T2 (M5 F90/M8)"
PHEV30E = "B48 2.0 PHEV (30e)"

# (model, y0, y1, cc, target, evidence)  cc=None = no cc signal required/expected
R = [
    # ---- 3 Series ----
    ("328I", 2000, 2000, None, "M52TUB28", "E46 328i = M52TUB28 2.8 193hp [WIKIM62]"),
    ("328I", 2014, 2014, None, N20US, "F30 328i = N20B20 240hp [WIKI340][WIKIN20]"),
    ("328CI", 2000, 2000, None, "M52TUB28", "E46 328Ci = M52TUB28 [WIKIM62]"),
    ("323CI", 2000, 2000, None, "M52TUB25", "E46 323Ci = M52TUB25 170hp [WIKIM62]"),
    ("323I", 2000, 2000, None, "M52TUB25", "E46 323i = M52TUB25 170hp [WIKIM62]"),
    ("323I", 2006, 2011, None, "N52B25U1", "E90 323i (CA) = N52B25 200hp [AEV323I][EBAY323]"),
    ("325I", 2001, 2005, None, "M54B25", "E46 325i = M54B25 184hp [WIKIM54]"),
    ("325I", 2006, 2006, None, "N52B25A", "E90 325i 2006 = N52B25 215hp [WIKIN52]"),
    ("325XI", 2001, 2005, None, "M54B25", "E46 325xi = M54B25 [WIKIM54]"),
    ("325XI", 2006, 2006, None, "N52B25A", "E90 325xi 2006 = N52B25 215hp [WIKIN52]"),
    ("325CI", 2001, 2006, None, "M54B25", "E46 325Ci = M54B25 [WIKIM54]"),
    ("330I", 2001, 2005, None, "M54B30(306S3)", "E46 330i = M54B30 225hp [WIKIM54]"),
    ("330I", 2006, 2006, None, "N52B30A", "E90 330i 2006 = N52B30 255hp [WIKIN52]"),
    ("330I", 2017, 2025, None, B30I, "F30 330i 2017-18 B48 248hp; G20 330i 2019+ B48 255hp [WIKI340][WIKI3G20]"),
    ("330XI", 2001, 2005, None, "M54B30(306S3)", "E46 330xi = M54B30 [WIKIM54]"),
    ("330XI", 2006, 2006, None, "N52B30A", "E90 330xi 2006 = N52B30 255hp [WIKIN52]"),
    ("330CI", 2001, 2006, None, "M54B30(306S3)", "E46 330Ci = M54B30 225hp [WIKIM54]"),
    ("330E", 2016, 2024, None, PHEV30E, "330e = B48 PHEV (F30 248hp, G20 288hp) [WIKI3G20]"),
    ("335I", 2007, 2010, None, "N54B30O0", "E9x 335i 2007-10 = N54B30 300hp [WIKIN55 family]"),
    ("335I", 2011, 2016, None, "N55B30A", "335i 2011+ = N55B30 300hp [WIKIN55][WIKI340]"),
    ("335XI", 2007, 2010, None, "N54B30O0", "335xi 2007-10 = N54 [WIKIN55 family]"),
    ("335XI", 2011, 2013, None, "N55B30A", "335xi 2011-13 = N55 [WIKIN55]"),
    ("335IS", 2011, 2013, None, "N54B30O0", "335is = N54 320hp tune [WIKIN55 family]"),
    ("335D", 2009, 2011, None, "M57D30T2", "335d = M57D30T2 265hp US [WIKIM57]"),
    ("328D", 2014, 2018, None, "N47D20 (328d)", "328d = N47D20 180hp [WIKIN47]"),
    ("320I", 2013, 2018, None, "N20B20B", "F30 320i = N20B20 180hp US [WIKI340][WIKIN20]"),
    ("320XI", 2013, 2013, None, "N20B20B", "F30 320xi = N20B20 180hp [WIKI340]"),
    ("340I", 2016, 2019, None, B5840, "F30 340i = B58 320hp [WIKI340]"),
    # ---- 4 Series ----
    ("430I", 2017, 2025, None, B30I, "430i = B48 (F32 248hp 2017-20, G22 255hp 2021+) [WIKI340 family]"),
    ("435I", 2014, 2016, None, "N55B30A", "435i = N55 300hp [WIKIN55]"),
    ("440I", 2017, 2020, None, B5840, "440i = B58 320hp [WIKI340 family]"),
    ("M440I", 2021, 2024, None, B58M40, "G22 M440i = B58 382hp [WIKI2G42 family]"),
    ("840I", 2020, 2025, None, B5840, "G15 840i = B58 335hp [WIKI8]"),
    # ---- 1/2 Series ----
    ("135I", 2008, 2010, None, "N54B30O0", "135i 2008-10 = N54 300hp [WIKI1M family]"),
    ("135I", 2011, 2013, None, "N55B30A", "135i 2011-13 = N55 300hp [WIKIN55]"),
    ("135IS", 2013, 2013, None, "N55B30 (M235i/135is)", "135is = N55 320hp [WIKIN55]"),
    ("1M", 2011, 2011, None, "N54B30A", "1M = N54B30 335hp [WIKI1M]"),
    ("228I", 2020, 2024, None, "B48B20", "228i Gran Coupe = B48 228hp [WIKI2F22 family]"),
    ("230I", 2017, 2024, None, B30I, "230i = B48 (F22 248hp, G42 255hp) [WIKI2F22][WIKI2G42]"),
    ("M235I", 2014, 2016, None, "N55B30 (M235i/135is)", "M235i = N55 320hp [WIKI2F22]"),
    ("M235I", 2020, 2024, None, "B48 2.0T (M235i GC)", "M235i Gran Coupe = B48A20T1 301hp [WIKI2F22 family]"),
    ("M240I", 2017, 2020, None, B5840, "F22 M240i = B58 335hp [WIKI2F22]"),
    ("M240I", 2021, 2024, None, B58M40, "G42 M240i = B58 382hp [WIKI2G42]"),
    ("M2", 2016, 2018, None, "N55B30 (M2)", "M2 = N55B30T0 365hp [CARBUZZM2]"),
    ("M2", 2019, 2021, None, "S55B30 (M2 Comp)", "M2 Comp = S55 405hp [CARBUZZM2][WIKIS55]"),
    ("M2", 2023, 2024, None, "S58B30 (M2)", "G87 M2 = S58 453hp [CARBUZZM2][WIKIS58]"),
    # ---- M cars ----
    ("M3", 2001, 2006, None, "S54B32US", "E46 M3 = S54B32US 333hp [WIKIS54]"),
    ("M3", 2008, 2013, None, "S65B40A", "E9x M3 = S65B40 414hp [WIKIS65]"),
    ("M3", 2015, 2018, None, "S55B30", "F80 M3 = S55 425hp [WIKIS55]"),
    ("M3", 2021, 2025, None, "S58B30 (M3/M4)", "G80 M3 = S58 473hp [WIKIS58]"),
    ("M4", 2015, 2020, None, "S55B30", "F82 M4 = S55 425hp [WIKIS55]"),
    ("M4", 2021, 2025, None, "S58B30 (M3/M4)", "G82 M4 = S58 473hp [WIKIS58]"),
    ("M5", 2000, 2003, None, "S62B50", "E39 M5 = S62B50 394hp [WIKIS62]"),
    ("M5", 2006, 2010, None, "S85B50A", "E60 M5 = S85B50 500hp [WIKIS85]"),
    ("M5", 2013, 2016, None, "S63B44B", "F10 M5 = S63B44 560hp [WIKIS63]"),
    ("M5", 2018, 2023, None, S63T2, "F90 M5 = S63B44T2 600hp [WIKIS63]"),
    ("M6", 2006, 2010, None, "S85B50A", "E63/64 M6 = S85B50 500hp [WIKIS85]"),
    ("M6", 2012, 2019, None, "S63B44B", "F06/12/13 M6 = S63B44 560hp [WIKIS63]"),
    ("M8", 2020, 2025, None, S63T2, "G15 M8 = S63 600/617hp [WIKI8][WIKIS63]"),
    ("M850I", 2019, 2025, None, N63TU2, "M850i = N63TU2 523hp [WIKI8][WIKIN63]"),
    ("M550I", 2018, 2023, None, N63TU2, "M550i = N63TU2 (456hp 2018-19, 523hp 2020+) [WIKI5G30][WIKIN63]"),
    ("M760I", 2017, 2022, None, "N74B66A", "M760i = N74B66 V12 601hp [WIKIN74]"),
    ("M340I", 2020, 2025, None, B58M40, "G20 M340i = B58 382hp [WIKI3G20]"),
    # ---- 5 Series ----
    ("525I", 2001, 2005, None, "M54B25", "E39/E60 525i 2001-05 = M54B25 184hp [WIKIM54][WIKI5E60]"),
    ("525I", 2006, 2007, None, "N52B25A", "E60 525i 2006+ = N52B25 215hp [WIKI5E60][WIKIN52]"),
    ("525XI", 2006, 2007, None, "N52B25A", "E60 525xi = N52B25 [WIKI5E60]"),
    ("528I", 2000, 2000, None, "M52TUB28", "E39 528i 2000 = M52TUB28 193hp [WIKIM62 family]"),
    ("528I", 2008, 2011, None, "N51B30US", "E60 528i = N52/N51 3.0 NA 230hp (2011 row = late E60, 6.52L sump matches 2010 not F10's 5.01L) [WIKI5E60][WIKIN52]"),
    ("528I", 2012, 2016, None, N20US, "F10 528i = N20B20 240hp [WIKI5F10][WIKIN20]"),
    ("528XI", 2008, 2010, None, "N51B30US", "E60 528xi = N52/N51 230hp [WIKI5E60]"),
    ("528XI", 2012, 2013, None, N20US, "F10 528xi = N20 240hp [WIKI5F10]"),
    ("530I", 2001, 2005, None, "M54B30(306S3)", "E39/E60 530i 2001-05 = M54B30 225hp [WIKIM54][WIKI5E60]"),
    ("530I", 2017, 2024, None, B30I, "G30 530i = B48 248hp (G60 2024 255hp) [WIKI5G30]"),
    ("530XI", 2006, 2007, None, "N52B30A", "E60 530xi = N52B30 255hp [WIKI5E60]"),
    ("530E", 2018, 2023, None, PHEV30E, "G30 530e = B48 PHEV 248/288hp [WIKI5G30]"),
    ("535I", 2008, 2010, None, "N54B30O0", "E60 535i = N54 300hp [WIKI5E60]"),
    ("535I", 2011, 2016, None, "N55B30A", "F10 535i = N55 300hp [WIKI5F10][WIKIN55]"),
    ("535XI", 2008, 2010, None, "N54B30O0", "E60 535xi = N54 [WIKI5E60]"),
    ("535XI", 2011, 2013, None, "N55B30A", "F10 535xi = N55 [WIKI5F10]"),
    ("535D", 2014, 2016, None, "N57D30O1", "F10 535d = N57 3.0TT 255hp [WIKIM57]"),
    ("540I", 2000, 2003, None, "M62B44TU", "E39 540i = M62B44TU 282hp [WIKIM62]"),
    ("540I", 2017, 2024, None, B5840, "G30 540i = B58 335hp (G60 2024 375hp) [WIKI5G30]"),
    ("540D", 2018, 2018, None, "B57D30 (540d)", "G30 540d xDrive = B57D30 261hp [AUTOEV540D][CARS540D]"),
    ("545I", 2004, 2005, None, "N62B44", "E60 545i = N62B44 325hp [WIKIN62][WIKI5E60]"),
    ("550I", 2006, 2010, None, "N62B48B", "E60 550i = N62B48 360hp [WIKI5E60][WIKIN62]"),
    ("550I", 2011, 2012, None, "N63B44", "F10 550i = N63 400hp [WIKI5F10][WIKIN63]"),
    ("550I", 2013, 2016, None, N63TU, "F10 550i 2013+ = N63TU 445hp [WIKI5F10][WIKIN63]"),
    ("550XI", 2010, 2012, None, "N63B44", "F10 550xi = N63 400hp [WIKIN63]"),
    ("550XI", 2013, 2013, None, N63TU, "F10 550xi 2013 = N63TU 445hp [WIKIN63]"),
    # ---- 6 Series ----
    ("645CI", 2004, 2005, None, "N62B44", "E63 645Ci = N62B44 325hp [WIKI6E63][WIKIN62]"),
    ("650I", 2006, 2010, None, "N62B48B", "E63 650i = N62B48 360hp [WIKI6E63][WIKIN62]"),
    ("650I", 2012, 2012, None, "N63B44", "F12 650i = N63 400hp [WIKI6F12][WIKIN63]"),
    ("650I", 2013, 2019, None, N63TU, "F12/13 650i 2013+ = N63TU 445hp [WIKI6F12][WIKIN63]"),
    ("650XI", 2012, 2012, None, "N63B44", "F13 650xi = N63 400hp [WIKIN63]"),
    ("650XI", 2013, 2013, None, N63TU, "F13 650xi 2013 = N63TU 445hp [WIKIN63]"),
    ("640I", 2012, 2017, None, "N55B30A", "F06/12/13 640i = N55 315hp [WIKI6F12][WIKIN55]"),
    ("640I", 2018, 2019, None, B5840, "G32 640i Gran Turismo = B58 335hp [WIKI6F12 family]"),
    # ---- 7 Series ----
    ("740I", 2000, 2001, None, "M62B44TU", "E38 740i = M62B44TU 282hp [WIKIM62]"),
    ("740I", 2011, 2012, None, "N54B30O0", "F01 740i = N54 315hp [WIKIF01][BMWLOG740]"),
    ("740I", 2013, 2015, None, "N55B30A", "F01 740i 2013+ = N55 315hp [WIKIF01]"),
    ("740I", 2016, 2022, None, B5840, "G11 740i = B58 320hp [WIKIN63 family/G11]"),
    ("740IL", 2000, 2001, None, "M62B44TU", "E38 740iL = M62B44TU 282hp [WIKIM62]"),
    ("740LI", 2011, 2012, None, "N54B30O0", "F02 740Li = N54 315hp [WIKIF01][BMWLOG740]"),
    ("740LI", 2013, 2015, None, "N55B30A", "F02 740Li 2013+ = N55 315hp [WIKIF01]"),
    ("740LXI", 2013, 2013, None, "N55B30A", "F02 740Lxi = N55 315hp [WIKIF01]"),
    ("740LD", 2015, 2015, None, "N57D30O1", "F02 740Ld xDrive = N57 255hp [WIKIM57]"),
    ("740E", 2017, 2019, None, "B48 2.0 PHEV (740e)", "G11 740e xDrive = B48 PHEV 322hp [WIKIF01 family/G11]"),
    ("745E", 2020, 2022, None, "B58 3.0 PHEV (745e)", "G11 745e = B58 PHEV 389hp [G11 LCI]"),
    ("745I", 2002, 2005, None, "N62B44", "E65 745i = N62B44 325hp [WIKI7E65][WIKIN62]"),
    ("745LI", 2002, 2005, None, "N62B44", "E66 745Li = N62B44 325hp [WIKI7E65]"),
    ("750I", 2006, 2008, None, "N62B48B", "E65 750i = N62B48 360hp [WIKI7E65][WIKIN62]"),
    ("750I", 2009, 2012, None, "N63B44", "F01 750i = N63 400hp [WIKIF01][WIKIN63]"),
    ("750I", 2013, 2018, None, N63TU, "F01 750i 2013+ = N63TU 445hp [WIKIF01][WIKIN63]"),
    ("750I", 2019, 2022, None, N63TU2, "G11 LCI 750i = N63TU2 523hp [USPG11][WIKIN63]"),
    ("750LI", 2006, 2008, None, "N62B48B", "E66 750Li = N62B48 360hp [WIKI7E65]"),
    ("750LI", 2009, 2012, None, "N63B44", "F02 750Li = N63 400hp [WIKIF01]"),
    ("750LI", 2013, 2015, None, N63TU, "F02 750Li 2013+ = N63TU 445hp [WIKIF01]"),
    ("750XI", 2010, 2012, None, "N63B44", "F01 750xi = N63 400hp [WIKIN63]"),
    ("750XI", 2013, 2013, None, N63TU, "F01 750xi 2013 = N63TU 445hp [WIKIN63]"),
    ("750LXI", 2010, 2012, None, "N63B44", "F02 750Lxi = N63 400hp [WIKIN63]"),
    ("750LXI", 2013, 2013, None, N63TU, "F02 750Lxi 2013 = N63TU 445hp [WIKIN63]"),
    ("750IL", 2000, 2001, None, "M73B54", "E38 750iL = M73B54 V12 322hp [WIKIM73]"),
    ("760I", 2004, 2006, None, "N73B60A", "E65/66 760i = N73B60 438hp [WIKIN73][WIKI7E65]"),
    ("760I", 2024, 2025, None, "S68 4.4 V8 BiTurbo", "G70 760i = S68 536hp [DRIVE760][BMWLOG760]"),
    ("760LI", 2003, 2008, None, "N73B60A", "E66 760Li = N73B60 438hp [WIKIN73]"),
    ("760LI", 2010, 2015, None, "N74B60A", "F02 760Li = N74B60 535hp [WIKIN74]"),
    # ---- roadsters / i ----
    ("Z8", 2000, 2003, None, "S62B50", "Z8 = S62B50 394hp [WIKIS62]"),
    ("I3", 2014, 2021, None, "i3 Electric (I01)", "i3 = 170hp electric (i3s 184hp) [CARI3][AEVI3]"),
    ("I8", 2014, 2020, None, "B3815KT0", "i8 = B38 1.5 I3 PHEV 357hp (2019+ 369hp) [WIKII8]"),
    # ---- Alpina ----
    ("ALPINA", 2007, 2008, None, "Alpina B7 (E65) 4.4 SC", "Alpina B7 E65 = SC 4.4 V8 500hp [EDMB7]"),
    ("ALPINA", 2011, 2016, None, "Alpina B7/B6 (F01/F06) 4.4TT", "Alpina B7/B6 = N63-based 4.4TT (2011-12 500hp, 2013+ 540hp) [HPSB7][CDB7]"),
    ("ALPINA", 2017, 2020, None, "Alpina B7 (G12) 4.4TT", "Alpina B7 G12 = 4.4TT 600hp [HPSB7]"),
    ("ALPINA", 2021, 2023, None, "Alpina B7/XB7/B8 (G12) 4.4TT", "Alpina B7/XB7/B8 = 4.4TT 612hp [MMXB7][HPSB7]"),
    # ---- X5 (cc required) ----
    ("X5", 2001, 2006, 3000, "M54B30(306S3)", "E53 3.0i = M54B30 225hp [WIKIX5E53][WIKIM54]"),
    ("X5", 2001, 2003, 4400, "M62B44TU", "E53 4.4i = M62B44TU 282hp [WIKIX5E53][WIKIM62]"),
    ("X5", 2004, 2006, 4400, "N62B44", "E53 4.4i 2004+ = N62 315hp [WIKIX5E53][WIKIN62]"),
    ("X5", 2002, 2003, 4600, "M62B46", "E53 4.6is = M62B46 340hp [WIKIX5E53]"),
    ("X5", 2004, 2006, 4800, "N62B48A", "E53 4.8is = N62B48 355hp [WIKIX5E53][WIKIN62]"),
    ("X5", 2016, 2018, 2000, "N20 2.0 PHEV (X5 40e)", "F15 xDrive40e = N20 PHEV 308hp [WIKIX5F15][AMSOILX5]"),
    ("X5", 2016, 2018, 3000, "N55B30A", "F15 xDrive35i = N55 300hp [WIKIX5F15]"),
    ("X5", 2016, 2019, 4400, N63TU, "F15/G05 50i = N63TU 445hp (2019 456hp) [WIKIX5F15][CDX5M50I]"),
    ("X5", 2019, 2023, 3000, B5840, "G05 40i = B58 335hp [WIKIX5G05]"),
    ("X5", 2024, 2025, 3000, B5840, "G05 LCI 40i = B58 375hp [KBBX5]"),
    ("X5", 2020, 2025, 4400, N63TU2, "G05 M50i/M60i = N63TU2/S68 523hp [CDX5M50I][KBBX5]"),
    # ---- X3 ----
    ("X3", 2013, 2017, 2000, N20US, "F25 xDrive28i = N20 240hp [WIKIX3G01][WIKIN20]"),
    ("X3", 2018, 2024, 2000, B30I, "G01 xDrive30i = B48 248hp [WIKIX3G01]"),
    ("X3", 2013, 2017, 3000, "N55B30A", "F25 xDrive35i = N55 300hp [WIKIX3G01]"),
    ("X3", 2018, 2024, 3000, B58M40, "G01 M40i = B58 355/382hp [WIKIX3G01]"),
    # ---- X4 ----
    ("X4", 2015, 2018, 2000, N20US, "F26 xDrive28i = N20 240hp [WIKIX3G01 family]"),
    ("X4", 2019, 2025, 2000, B30I, "G02 xDrive30i = B48 248hp [WIKIX3G01 family]"),
    ("X4", 2015, 2025, 3000, B58M40, "F26/G02 M40i = B58 355/382hp [WIKIX3G01 family]"),
    # ---- X6 ----
    ("X6", 2014, 2019, 3000, "N55B30A", "E71/F16 xDrive35i = N55 300hp [WIKIX3G01 family]"),
    ("X6", 2020, 2024, 3000, B5840, "G06 xDrive40i = B58 335hp [WIKIX5G05 family]"),
    ("X6", 2015, 2019, 4400, N63TU, "F16 xDrive50i = N63TU 445hp [WIKIN63]"),
    ("X6", 2020, 2024, 4400, N63TU2, "G06 M50i = N63TU2 523hp [WIKIN63][CDX5M50I family]"),
    # ---- X7 ----
    ("X7", 2019, 2025, 3000, B5840, "G07 xDrive40i = B58 335hp (2024+ 375hp) [WIKIX7][KBBX5 family]"),
    ("X7", 2019, 2019, 4400, N63TU, "G07 xDrive50i 2019 = N63TU 456hp [WIKIX7][CDX5M50I family]"),
    ("X7", 2020, 2025, 4400, N63TU2, "G07 M50i/M60i = 523hp [WIKIX7][CDX5M50I family]"),
    # ---- Z4 ----
    ("Z4", 2013, 2016, 2000, N20US, "E89 sDrive28i = N20 240hp [WIKIZ4 family][WIKIN20]"),
    ("Z4", 2020, 2024, 2000, B30I, "G29 sDrive30i = B48 255hp [WIKIZ4]"),
    ("Z4", 2013, 2016, 3000, "N55B30A", "E89 sDrive35i = N55 300hp [WIKIZ4 family]"),
    ("Z4", 2020, 2024, 3000, B58M40, "G29 M40i = B58 382hp [WIKIZ4]"),
    # ---- X1 / X2 ----
    ("X1", 2016, 2022, None, "B48B20", "F48 X1 28i = B46A20B 228hp (B48 family row) [WIKIX1F48]"),
    ("X1", 2023, 2023, None, B30I, "U11 X1 2023 US = xDrive28i only, B48 241hp [KBBX1][CDX1]"),
]

CC_MODELS = {"X5", "X3", "X4", "X6", "X7", "Z4"}

def decide(model, year, code):
    parts = code.replace("LEMON_BMW_", "").split("_")
    extras = parts[1:-1] if len(parts) > 2 else []
    cc = None
    for e in extras:
        m = re.match(r"^(\d{4})CC$", e)
        if m: cc = int(m.group(1))
    mu = model.upper()
    if mu in ("Z3",):  return (None, "Z3 bare: 2.5i/3.0i/M unknown, no cc/trim signal", None)
    if mu == "M":      return (None, "bare 'M': M3/M5/M6/Z3M/Z4M unknown", None)
    if mu == "X2":     return (None, "X2 bare: 228i vs M35i unknown (228 vs 301hp)", None)
    if mu == "ACTIVEHYBRID": return (None, "ActiveHybrid model unknown (3/5/7/X6 different engines)", None)
    if mu == "535I" and year == 2017: return (None, "535i 2017: no US 535i (F10 ended 2016, G30 = 540i)", None)
    if mu == "550I" and year == 2017: return (None, "550i 2017: no US 550i (G30 M550i from 2018)", None)
    if mu == "X1" and year >= 2024: return (None, "X1 2024+: 28i vs M35i unknown", None)
    if mu in CC_MODELS and cc is None:
        return (None, f"{model} no-cc row: trim unknown", None)
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if mu in CC_MODELS and not cands and cc is not None:
        return (None, f"{model} {cc}cc {year}: no rule", None)
    if not cands:
        cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] is None]
    if not cands:
        return (None, f"no rule for {model} {year}", None)
    r = cands[0]
    tgt, ev = r[4], r[5]
    fuel_fix = None
    if tgt in ("N47D20 (328d)", "N57D30O1", "B57D30 (540d)", "M57D30T2"): fuel_fix = "Diesel"
    if tgt in (PHEV30E, "B48 2.0 PHEV (740e)", "B58 3.0 PHEV (745e)", "N20 2.0 PHEV (X5 40e)", "B3815KT0"): fuel_fix = "Hybrid"
    if tgt == "i3 Electric (I01)": fuel_fix = "Electric"
    return (tgt, ev, fuel_fix)

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code FROM vehicle_variants
        WHERE car_brand='BMW' AND engine_code LIKE 'LEMON_BMW%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code in rows:
        tgt, note, fuel_fix = decide(model, year, code)
        if tgt is None:
            skips.append((vid, model, year, code, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"BMW LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    from collections import Counter
    print("\nskips by reason:")
    for (m, n), c in Counter((s[1], s[4]) for s in skips).most_common(40): print(f"  {c:3} {m}: {n}")
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(15): print(f"  {c:3} {t}")

    if not apply:
        with open("database_enriched/csv_exports/22_lemon_batch5_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"BMW",d[1],d[2],d[3],d[4],d[5] or "",d[6] or ""])
            for s in skips: w.writerow([s[0],"BMW",s[1],s[2],s[3],"SKIP","",s[4]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step14_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP14_VERIFIED')""",
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

    with open("database_enriched/csv_exports/22_lemon_batch5_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"BMW",d[1],d[2],d[3],d[4],d[5] or "",d[6] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_BMW remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_BMW%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
