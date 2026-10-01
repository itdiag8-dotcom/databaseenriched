"""Step 15 (user-plan Step 5, batch 6): replace LEMON_CHEVROLET codes with real OEM engine codes.
653 rows, 49 models. Signal: cc in code (nearly always) + sometimes VIN 8th char.
Cars/SUVs keyed on (model, year, cc); generic 'Chevy' truck/van rows on (cc, year) -> Vortec family.
All splits web-verified where uncertain (see CIT)."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "SLOPPYVIN": "https://sites.google.com/site/sloppywiki/everything-ls/truck-engine-vin-decoder (GM truck VIN: 4.3 X/W, 4.8 V, 5.3 T=LM7 Z=L59, 6.0 U=LQ4 N=LQ9)",
    "ITRUNSVIN": "https://itstillruns.com/determine-code-vin-chevrolet-truck-5813150.html (GM VIN 8th: F=6.5D G=8.1 J=7.4 K=5.7 S=4.2 X/W=4.3 1/2=6.6D)",
    "CAMARO5VIN": "https://www.camaro5.com/forums/showthread.php?t=348140 (Camaro 8th VIN: W=LS3 manual, J=L99 auto, V=LLT, 3=LFX, P=LSA)",
    "USEALSID": "https://ussealparts.com/american-muscle/engine-id-guide (W=LS3, J=L99 AFM, P=LSA)",
    "CDTRAVERSE": "https://www.caranddriver.com/chevrolet/traverse/specs/2013/chevrolet_traverse_chevrolet-traverse_2013 (2013 Traverse engine order code LLT)",
    "AMSOTRAV": "https://www.amsoil.com/lookup/auto-and-light-truck/2013/chevrolet/traverse/3-6l-6-cyl-engine-code-d-llt-6/ (2013 Traverse 3.6 = LLT)",
    "GMAEQ": "https://gmauthority.com/blog/gm/chevrolet/equinox/2018-chevrolet-equinox/2018-chevrolet-equinox-specifications/ (2018 Equinox RPO: 1.5T=LYX, 2.0T=LTG, 1.6TD=LH7)",
    "NHTSAEQ": "https://static.nhtsa.gov/odi/tsbs/2017/MC-10116567-9999.pdf (2018 Equinox 1.6L Turbo Diesel RPO LH7, dexos2)",
    "GMALFV": "https://gmauthority.com/blog/gm/gm-engines/lfv/ (1.5T LFV debuted 2016 Malibu 163hp)",
    "GMACRUZD": "https://gmauthority.com/blog/gm/chevrolet/cruze/2014-cruze/2014-cruze-diesel/ (2014-15 Cruze 2.0TD = LUZ 151hp)",
    "REMANLM4": "https://reman-engine.com/remanufactured-engines/chevrolet/trailblazer_ext/2004/5.3l-vin-p-8th-digit (TrailBlazer EXT 5.3 = LM4, VIN P)",
    "ADTBEXT": "https://www.auto-data.net/en/chevrolet-trailblazer-i-5.3-i-v8-16v-4wd-294hp-14410 (TrailBlazer 5.3 V8 = LM4 294hp)",
    "GORDLIH": "https://www.gordonchevy.com/chevrolet-1-2l-lih-ecotec-turbo-engine-overview/ (Trailblazer 2021-24 1.2T = LIH 137hp)",
    "GORDL3T": "https://www.gordonchevy.com/chevrolet-1-3l-l3t-ecotec-turbo-engine-overview/ (Trailblazer 1.3T = L3T 155hp, VIN L per Weber Brothers listing)",
    "WEBERL3T": "https://www.weberbrothersauto.com/product/engine-assembly-1000876039-xb431/ (TRAILBLAZER 21-23 1.3L VIN L, opt L3T)",
}

NEW_ENGINES = {
    "LSJ":        ("2.0 I4 Supercharged (Cobalt SS)", "Petrol", 1998, 205, 4),
    "LD9":        ("2.4 I4 Twin Cam (LD9)", "Petrol", 2392, 150, 4),
    "LFV":        ("1.5 I4 Turbo (LFV Ecotec)", "Petrol", 1490, 163, 4),
    "LYX":        ("1.5 I4 Turbo (LYX Ecotec)", "Petrol", 1490, 170, 4),
    "LH7":        ("1.6 I4 Turbo Diesel (LH7)", "Diesel", 1598, 136, 4),
    "LZ9":        ("3.9 V6 High-Value (LZ9)", "Petrol", 3880, 240, 6),
    "LT2":        ("6.2 V8 (LT2, C8 Corvette)", "Petrol", 6162, 460, 8),
    "LT6":        ("5.5 V8 Flat-Plane (LT6, C8 Z06)", "Petrol", 5495, 670, 8),
    "LM4":        ("5.3 V8 Vortec (LM4, aluminum)", "Petrol", 5327, 294, 8),
    "LG8":        ("3.1 V6 3100 SFI (LG8)", "Petrol", 3135, 175, 6),
    "L77":        ("6.0 V8 (L77, Caprice PPV)", "Petrol", 5967, 301, 8),
    "LUZ":        ("2.0 I4 Turbo Diesel (LUZ)", "Diesel", 1998, 151, 4),
    "6.5 TD V8 (L65)": ("6.5 V8 Turbo Diesel (Vortec)", "Diesel", 6494, 215, 8),
    "MR20DD 2.0 (City Express)": ("2.0 I4 (Nissan MR20, City Express)", "Petrol", 1997, 131, 4),
    "Voltec 1.4 EREV (Volt)": ("1.4 I4 EREV + electric (Voltec Gen1)", "Hybrid", 1398, 149, 4),
    "Voltec 1.5 EREV (Volt)": ("1.5 I4 EREV + electric (Voltec Gen2)", "Hybrid", 1490, 149, 4),
    "Bolt EV Electric": ("Electric motor (Bolt EV, 60/66 kWh)", "Electric", None, 200, None),
    "Spark EV Electric": ("Electric motor (Spark EV)", "Electric", None, 140, None),
    "1.8 I4 Hybrid (Malibu)": ("1.8 I4 Hybrid (Malibu Hybrid)", "Hybrid", 1796, 182, 4),
    "1.4 16v (Spark US)": ("1.4 I4 16v (US Spark 2016+, 98hp; verify RPO LVV)", "Petrol", 1399, 98, 4),
}

ROW_FIXES = {
    "1ZZ-FE": {"displacement_cc": 1794, "power_hp": 130},
    "LL8": {"engine_type": "4.2 I6 Vortec (LL8)"},
    "LS1": {"engine_type": "5.7 V8 (LS1)"},
    "LS4": {"engine_type": "5.3 V8 (LS4, FWD)", "power_hp": 303},
    "LZ4": {"engine_type": "3.5 V6 High-Value (LZ4)", "power_hp": 211, "displacement_cc": 3498},
    "LZE": {"engine_type": "3.5 V6 High-Value Flex (LZE)", "power_hp": 201, "displacement_cc": 3498},
    "L82": {"engine_type": "5.3 V8 EcoTec3 (L82, DFM)", "power_hp": 355},
    "J20A": {"engine_type": "2.0 I4 16v (Suzuki J20A)"},
    "LNJ": {"engine_type": "3.4 V6 (LNJ)", "power_hp": 185, "displacement_cc": 3350},
}

# generic 'Chevy' truck/van: (cc, y0, y1) -> (code, note)
CHEVY_CC = [
    (4300, 2000, 2002, "L35", "4.3 Vortec V6 2000-02 (L35, VIN X/W) [SLOPPYVIN]"),
    (4300, 2003, 2012, "LU3", "4.3 Vortec V6 2003+ (LU3, VIN X) [SLOPPYVIN]"),
    (4800, 2000, 2003, "LR4", "4.8 Vortec V8 (LR4, VIN V) [SLOPPYVIN]"),
    (4800, 2004, 2006, "LY2", "4.8 Vortec V8 (LY2) [SLOPPYVIN family]"),
    (4800, 2007, 2012, "L20", "4.8 Vortec V8 (L20, VIN A) [SLOPPYVIN family]"),
    (5000, 2000, 2002, "L30", "5.0 Vortec V8 (L30) [ITRUNSVIN family]"),
    (5300, 2000, 2006, "LM7", "5.3 Vortec V8 (LM7, VIN T) [SLOPPYVIN]"),
    (5300, 2007, 2009, "LY5", "5.3 Vortec V8 (LY5) [SLOPPYVIN family]"),
    (5300, 2010, 2013, "LMG", "5.3 Vortec V8 flex (LMG era; LMF if van) [SLOPPYVIN family]"),
    (5700, 2000, 2002, "L31", "5.7 Vortec V8 (L31, VIN K/R) [ITRUNSVIN]"),
    (6000, 2000, 2006, "LQ4", "6.0 Vortec V8 (LQ4, VIN U) [SLOPPYVIN]"),
    (6000, 2007, 2009, "LY6", "6.0 Vortec V8 (LY6) [SLOPPYVIN family]"),
    (6000, 2010, 2012, "L96", "6.0 Vortec V8 (L96, VIN G) [SLOPPYVIN family]"),
    (6500, 2000, 2002, "6.5 TD V8 (L65)", "6.5 V8 TD (VIN F) [ITRUNSVIN]"),
    (6600, 2006, 2006, "LBZ", "6.6 Duramax (LBZ from 2006) [ITRUNSVIN family]"),
    (6600, 2007, 2010, "LMM", "6.6 Duramax (LMM 2007-10) [ITRUNSVIN family]"),
    (6600, 2011, 2012, "LML", "6.6 Duramax (LML 2011+, VIN L) [ITRUNSVIN]"),
    (7400, 2000, 2002, "L29", "7.4 Vortec V8 (L29, VIN J) [ITRUNSVIN]"),
    (8100, 2001, 2006, "L18", "8.1 Vortec V8 (L18, VIN G) [ITRUNSVIN]"),
]

# (MODEL, y0, y1, cc, target, evidence); cc=None = bare row w/o cc expected
R = [
    # cars
    ("MALIBU", 2000, 2003, None, "LG8", "Malibu 2000-03 = 3.1 V6 only [LG8 3100 SFI]"),
    ("MALIBU", 2004, 2008, 2200, "L61", "2.2 Ecotec (L61) [DB family]"),
    ("MALIBU", 2004, 2010, 3500, "LX9", "3.5 V6 (LX9) [DB family]"),
    ("MALIBU", 2006, 2007, 3900, "LZ9", "3.9 V6 (LZ9 240hp) [NEW, GM HV family]"),
    ("MALIBU", 2008, 2009, 3500, "LX9", "3.5 V6 fleet (LX9) [GM family]"),
    ("MALIBU", 2008, 2012, 2400, "LE5", "2.4 Ecotec (LE5; 2012 VIN 0/1/U same engine) [DB family]"),
    ("MALIBU", 2008, 2011, 3600, "LY7", "3.6 V6 HF (LY7) [DB family]"),
    ("MALIBU", 2013, 2013, 2400, "LUK", "2013 Malibu Eco 2.4 eAssist (LUK) [DB LUK eAssist family]"),
    ("MALIBU", 2013, 2015, 2500, "LCV", "2.5 SIDI (LCV/LKW) [DB family]"),
    ("MALIBU", 2013, 2022, 2000, "LTG", "2.0T (LTG) [GMAEQ family]"),
    ("MALIBU", 2016, 2022, 1500, "LFV", "1.5T (LFV 163hp, debut 2016 Malibu) [GMALFV]"),
    ("MALIBU", 2016, 2019, 1800, "1.8 I4 Hybrid (Malibu)", "Malibu Hybrid 1.8 + e-motor 182hp [GM family]"),
    ("MALIBU", 2023, 2025, None, "LFV", "2023+ Malibu = 1.5T only [GMALFV]"),
    ("IMPALA", 2000, 2005, 3400, "LA1", "3.4 V6 (LA1) [DB family]"),
    ("IMPALA", 2000, 2005, 3800, "L36", "3.8 V6 3800 II [DB family]"),
    ("IMPALA", 2006, 2011, 3500, "LZ4", "3.5 V6 (LZ4 211hp) [GM HV family]"),
    ("IMPALA", 2006, 2011, 3900, "LZ9", "3.9 V6 (LZ9) [NEW]"),
    ("IMPALA", 2006, 2009, 5300, "LS4", "Impala SS 5.3 FWD (LS4 303hp) [GM family]"),
    ("IMPALA", 2012, 2013, None, "LFX", "2012+ Impala = 3.6 LFX [GM family]"),
    ("IMPALA", 2014, 2014, 2400, "LUK", "2014 Impala 2.4 eAssist (LUK) [DB LUK family]"),
    ("IMPALA", 2014, 2019, 2500, "LCV", "2.5 SIDI (LCV/LKW) [DB family]"),
    ("IMPALA", 2014, 2019, 3600, "LFX", "3.6 SIDI (LFX, VIN 3/N) [CAMARO5VIN]"),
    ("IMPALA", 2015, 2015, None, "LFX", "Impala Limited 2015 = 3.6 only [GM family]"),
    ("MONTE", 2000, 2005, 3400, "LA1", "3.4 V6 (LA1) [DB family]"),
    ("MONTE", 2000, 2005, 3800, "L36", "3.8 V6 3800 II [DB family]"),
    ("MONTE", 2006, 2006, 3500, "LZ4", "Monte LT 3.5 (LZ4) [GM family]"),
    ("MONTE", 2006, 2006, 3900, "LZ9", "Monte 3.9 (LZ9) [NEW]"),
    ("MONTE", 2006, 2007, 5300, "LS4", "Monte SS 5.3 FWD (LS4) [GM family]"),
    ("LUMINA", 2000, 2001, None, "LG8", "Lumina 2000-01 = 3.1 V6 only [LG8]"),
    ("VENTURE", 2000, 2005, None, "LA1", "Venture = 3.4 V6 only (LA1) [DB family]"),
    ("UPLANDER", 2005, 2005, None, "LX9", "2005 Uplander 3.5 (LX9) [GM family]"),
    ("UPLANDER", 2006, 2009, 3500, "LZE", "3.5 V6 flex (LZE) [GM family]"),
    ("UPLANDER", 2006, 2006, 3900, "LZ9", "3.9 V6 (LZ9) [NEW]"),
    ("UPLANDER", 2007, 2009, None, "LZE", "2007+ Uplander = 3.5 only [GM family]"),
    ("CAVALIER", 2000, 2005, 2200, "LN2", "2.2 OHV (LN2) [DB family]"),
    ("CAVALIER", 2003, 2005, None, "LN2", "2003+ Cavalier = 2.2 only [DB family]"),
    ("CAVALIER", 2000, 2002, 2400, "LD9", "2.4 Twin Cam (LD9) [GM family]"),
    ("CLASSIC", 2004, 2005, None, "L61", "Malibu Classic = 2.2 (L61) [GM family]"),
    ("COBALT", 2005, 2010, 2200, "L61", "2.2 Ecotec (L61) [DB family]"),
    ("COBALT", 2005, 2010, 2400, "LE5", "2.4 Ecotec (LE5/LEA) [DB family]"),
    ("COBALT", 2005, 2007, 2000, "LSJ", "Cobalt SS SC 2.0 (LSJ 205hp) [NEW, GM family]"),
    ("COBALT", 2008, 2010, 2000, "LNF", "Cobalt SS Turbo 2.0T (LNF) [DB family]"),
    ("HHR", 2006, 2011, 2200, "L61", "2.2 Ecotec (L61) [DB family]"),
    ("HHR", 2006, 2011, 2400, "LE5", "2.4 Ecotec (LE5/LEA) [DB family]"),
    ("HHR", 2009, 2010, 2000, "LNF", "HHR SS 2.0T (LNF) [DB family]"),
    ("AVEO", 2004, 2011, None, "L91", "Aveo = 1.6 (L91) [DB family]"),
    ("CRUZE", 2011, 2016, 1800, "LUW", "1.8 16v (LUW; US base/Canada LS) [DB family]"),
    ("CRUZE", 2011, 2016, 1400, "LUH", "1.4T (LUH) [DB family]"),
    ("CRUZE", 2016, 2019, None, "LUV", "2016+ US Cruze = 1.4T only [DB family]"),
    ("CRUZE", 2017, 2019, 1400, "LUV", "1.4T (LUV, VIN M) [DB family]"),
    ("CRUZE", 2014, 2015, 2000, "LUZ", "2.0TD (LUZ 151hp) [GMACRUZD]"),
    ("CRUZE", 2017, 2019, 1600, "LH7", "1.6TD (LH7 137hp, VIN E) [NHTSAEQ family]"),
    ("SONIC", 2012, 2020, 1400, "LUH", "1.4T (LUH, VIN B; LUV later) [DB family]"),
    ("SONIC", 2012, 2018, 1800, "LUW", "1.8 16v (LUW, VIN G/H) [DB family]"),
    ("SONIC", 2019, 2020, None, "LUH", "2019-20 Sonic = 1.4T only [DB family]"),
    ("SPARK", 2013, 2015, None, "LMU", "1.2 (LMU 84hp) [DB family]"),
    ("SPARK", 2016, 2022, None, "1.4 16v (Spark US)", "US Spark 2016+ = 1.4 98hp only [GM family; verify RPO LVV]"),
    ("PRIZM", 2000, 2002, None, "1ZZ-FE", "Prizm = Corolla twin, 1ZZ-FE 1.8 [Toyota family]"),
    ("VOLT", 2011, 2015, None, "Voltec 1.4 EREV (Volt)", "Volt Gen1 Voltec 1.4 EREV [GM family]"),
    ("VOLT", 2016, 2019, None, "Voltec 1.5 EREV (Volt)", "Volt Gen2 Voltec 1.5 EREV [GM family]"),
    ("BOLT", 2017, 2023, None, "Bolt EV Electric", "Bolt EV electric 200hp [GM family]"),
    # pony cars / Corvette
    ("CAMARO", 2000, 2002, 3800, "L36", "3.8 3800 II (L36) [DB family]"),
    ("CAMARO", 2000, 2002, 5700, "LS1", "5.7 V8 (LS1) [DB family]"),
    ("CAMARO", 2012, 2015, 6200, None, "VIN decides: J=L99 W=LS3"),
    ("CAMARO", 2014, 2014, 3600, "LFX", "3.6 (LFX, VIN 3) [CAMARO5VIN]"),
    ("CAMARO", 2014, 2014, 7000, "LS7", "Z/28 7.0 (LS7) [DB family]"),
    ("CAMARO", 2016, 2023, 2000, "LTG", "2.0T (LTG, VIN X) [GMAEQ family]"),
    ("CORVETTE", 2000, 2000, None, "LS1", "2000 Corvette = LS1 only [DB family]"),
    ("CORVETTE", 2005, 2007, None, "LS2", "C6 base 6.0 (LS2) [DB family]"),
    ("CORVETTE", 2006, 2007, 6000, "LS2", "C6 6.0 (LS2) [DB family]"),
    ("CORVETTE", 2006, 2013, 7000, "LS7", "Z06 7.0 (LS7) [DB family]"),
    ("CORVETTE", 2008, 2013, 6200, "LS3", "6.2 (LS3) [DB family]"),
    ("CORVETTE", 2014, 2019, None, "LT1", "C7 6.2 (LT1) [DB family]"),
    ("CORVETTE", 2020, 2023, None, "LT2", "C8 6.2 (LT2) [NEW]"),
    ("CORVETTE", 2023, 2025, 5500, "LT6", "Z06 5.5 FPC (LT6 670hp) [NEW]"),
    ("CORVETTE", 2023, 2025, 6200, "LT2", "Stingray/E-Ray 6.2 (LT2; E-Ray adds front e-motor) [NEW]"),
    ("SS", 2014, 2017, None, "LS3", "SS sedan 6.2 (LS3 415hp) [DB family]"),
    ("SSR", 2005, 2006, None, "LS2", "SSR 2005-06 = 6.0 LS2 [DB family]"),
    ("CAPRICE", 2011, 2017, 6000, "L77", "Caprice PPV 6.0 (L77 301hp, VIN 2) [NEW]"),
    ("CAPRICE", 2012, 2017, 3600, "LFX", "Caprice PPV 3.6 (LFX, VIN 3) [CAMARO5VIN]"),
    ("CAPRICE", 2011, 2011, None, "L77", "2011 Caprice PPV = 6.0 only [NEW]"),
    # SUVs/crossovers
    ("EQUINOX", 2005, 2009, 3400, "LNJ", "3.4 V6 (LNJ) [DB family]"),
    ("EQUINOX", 2005, 2007, None, "LNJ", "Equinox 2005-07 = 3.4 only [DB family]"),
    ("EQUINOX", 2008, 2009, 3600, "LY7", "Equinox Sport 3.6 (LY7) [DB family]"),
    ("EQUINOX", 2010, 2017, 2400, "LEA", "2.4 SIDI (LEA, VIN K) [DB family]"),
    ("EQUINOX", 2010, 2012, 3000, "LF1", "3.0 SIDI (LF1) [DB family]"),
    ("EQUINOX", 2013, 2017, 3600, "LFX", "3.6 SIDI (LFX, VIN 3) [CAMARO5VIN]"),
    ("EQUINOX", 2018, 2020, 1500, "LYX", "1.5T (LYX 170hp, VIN V) [GMAEQ]"),
    ("EQUINOX", 2018, 2019, 1600, "LH7", "1.6TD (LH7 136hp, VIN U) [GMAEQ][NHTSAEQ]"),
    ("EQUINOX", 2018, 2020, 2000, "LTG", "2.0T (LTG, VIN X) [GMAEQ]"),
    ("EQUINOX", 2021, 2025, None, "LYX", "2021+ Equinox = 1.5T only [GMAEQ family]"),
    ("EQUINOX", 2019, 2020, None, "LYX", "base 1.5T (cc rows separate) [GMAEQ family]"),
    ("TRAVERSE", 2009, 2017, None, "LLT", "Traverse 3.6 (LLT all gen-1 years; 2013 order code LLT) [CDTRAVERSE][AMSOTRAV]"),
    ("TRAVERSE", 2018, 2019, 2000, "LTG", "2.0T (LTG) [GMAEQ family]"),
    ("TRAVERSE", 2018, 2025, 3600, "LGX", "3.6 (LGX 310hp, VIN W) [DB family]"),
    ("TRAVERSE", 2020, 2025, None, "LGX", "2020+ Traverse = 3.6 only [DB family]"),
    ("TRAX", 2015, 2022, 1400, "LUJ", "1.4T (LUJ/LUV, VIN B/M) [DB family]"),
    ("TRAX", 2015, 2022, None, "LUJ", "Trax 2015-22 = 1.4T only [DB family]"),
    ("TRAX", 2024, 2025, None, "LIH", "2024+ Trax = 1.2T LIH only [GORDLIH]"),
    ("BLAZER", 2019, 2023, 2500, "LCV", "2.5 SIDI (LCV/LKW, VIN A) [DB family]"),
    ("BLAZER", 2019, 2025, 3600, "LGX", "3.6 (LGX, VIN S) [DB family]"),
    ("BLAZER", 2020, 2025, 2000, "LTG", "2.0T (LTG, VIN 4) [GMAEQ family]"),
    ("BLAZER", 2000, 2002, None, "L35", "S-10 Blazer 2000-02 = 4.3 only (L35) [SLOPPYVIN]"),
    ("BLAZER", 2003, 2005, None, "LU3", "S-10 Blazer 2003-05 = 4.3 only (LU3) [SLOPPYVIN]"),
    ("TRAILBLAZER", 2002, 2002, None, "LL8", "2002 TrailBlazer = 4.2 I6 (LL8) [DB family]"),
    ("TRAILBLAZER", 2003, 2009, 4200, "LL8", "4.2 I6 Vortec (LL8) [DB family]"),
    ("TRAILBLAZER", 2003, 2008, 5300, "LM4", "TB EXT 5.3 V8 (LM4, VIN P, 294hp) [REMANLM4][ADTBEXT]"),
    ("TRAILBLAZER", 2006, 2009, 6000, "LS2", "TB SS 6.0 (LS2) [DB family]"),
    ("TRAILBLAZER", 2021, 2025, 1200, "LIH", "1.2T (LIH 137hp, VIN 2/P) [GORDLIH]"),
    ("TRAILBLAZER", 2021, 2025, 1300, "L3T", "1.3T (L3T 155hp, VIN L) [GORDL3T][WEBERL3T]"),
    # trucks/vans
    ("ASTRO", 2000, 2002, None, "L35", "Astro 4.3 (L35) [SLOPPYVIN]"),
    ("ASTRO", 2003, 2005, None, "LU3", "Astro 4.3 (LU3) [SLOPPYVIN]"),
    ("S10", 2000, 2002, 2200, "LN2", "2.2 OHV (LN2) [DB family]"),
    ("S10", 2000, 2002, 4300, "L35", "4.3 Vortec (L35) [SLOPPYVIN]"),
    ("S10", 2003, 2003, 2200, "LN2", "2.2 OHV (LN2) [DB family]"),
    ("S10", 2003, 2003, 4300, "LU3", "4.3 Vortec (LU3) [SLOPPYVIN]"),
    ("SILVERADO", 2000, 2001, 4300, "L35", "4.3 Vortec (L35) [SLOPPYVIN]"),
    ("SILVERADO", 2012, 2012, 6000, "L96", "2012 6.0 (L96; VIN J noted) [SLOPPYVIN family]"),
    ("SILVERADO", 2022, 2022, 5300, "L82", "2022 5.3 EcoTec3 (L82; VIN F noted) [ROW_FIX L82]"),
    ("TAHOE", 2021, 2021, 5300, "L82", "2021 Tahoe 5.3 (L82) [ROW_FIX L82]"),
    ("SUBURBAN", 2021, 2021, 5300, "L82", "2021 Suburban 5.3 (L82) [ROW_FIX L82]"),
    ("C3500", 2000, 2002, 6500, "6.5 TD V8 (L65)", "C3500 6.5 TD (VIN F) [ITRUNSVIN]"),
    ("C3500", 2000, 2000, 7400, "L29", "7.4 Vortec (L29, VIN J) [ITRUNSVIN]"),
    ("C3500", 2001, 2002, 8100, "L18", "8.1 Vortec (L18, VIN G) [ITRUNSVIN]"),
    ("CUTAWAY", 2001, 2002, 6500, "6.5 TD V8 (L65)", "Express Cutaway 6.5 TD [ITRUNSVIN]"),
    ("CAB", 2000, 2000, 6500, "6.5 TD V8 (L65)", "C-series cab 6.5 TD [ITRUNSVIN]"),
    ("PICKUP", 2000, 2000, 6500, "6.5 TD V8 (L65)", "pickup 6.5 TD [ITRUNSVIN]"),
    # niche
    ("TRACKER", 2000, 2004, 2000, "J20A", "Tracker 2.0 (Suzuki J20A) [DB family]"),
    ("TRACKER", 2001, 2003, 2500, "H25A", "Tracker 2.5 V6 (Suzuki H25A) [DB family]"),
    ("CAPTIVA", 2012, 2015, 2400, "LE5", "Captiva Sport 2.4 (LE5/LE9, VIN K) [DB family]"),
    ("CAPTIVA", 2012, 2013, 3000, "LF1", "Captiva Sport 3.0 SIDI (LF1, VIN 5) [DB family]"),
    ("CITY", 2015, 2018, None, "MR20DD 2.0 (City Express)", "City Express = Nissan NV200 2.0 MR20 [NEW]"),
]

FUEL_FIX = {
    "LUZ": "Diesel", "LH7": "Diesel",
    "Voltec 1.4 EREV (Volt)": "Hybrid", "Voltec 1.5 EREV (Volt)": "Hybrid",
    "1.8 I4 Hybrid (Malibu)": "Hybrid",
    "Bolt EV Electric": "Electric", "Spark EV Electric": "Electric",
}

def decide(model, year, code):
    parts = code.replace("LEMON_CHEVROLET_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc, vin = None, None
    for s in segs:
        m = re.match(r"^(\d{4})CC$", s)
        if m: cc = int(m.group(1))
        m = re.match(r"^VIN(.+)$", s)
        if m: vin = m.group(1).upper()
    mu = model.upper()

    if "SPARKEV" in code:
        return ("Spark EV Electric", "Spark EV = electric (140hp) [GM family]", "Electric")
    if mu == "CHEVY":
        if cc is None: return (None, "generic 'Chevy' row without cc", None)
        for c0, y0, y1, tgt, note in CHEVY_CC:
            if c0 == cc and y0 <= year <= y1: return (tgt, note, "Diesel" if "TD" in tgt or "Duramax" in tgt else None)
        return (None, f"generic 'Chevy' {cc}cc {year}: no rule", None)

    if mu == "CAMARO" and cc == 6200:
        if vin == "J": return ("L99", "6.2 (L99 AFM auto, VIN J) [CAMARO5VIN][USEALSID]", None)
        if vin == "W": return ("LS3", "6.2 (LS3 manual, VIN W) [CAMARO5VIN][USEALSID]", None)
        return (None, "Camaro 6.2 without VIN (LS3 vs L99 vs LSA)", None)

    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands:
        cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] is None and cc is None]
    if not cands:
        return (None, f"no rule for {model} {year}" + (f" {cc}cc" if cc else " (bare)"), None)
    r = cands[0]
    return (r[4], r[5], FUEL_FIX.get(r[4]))

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code FROM vehicle_variants
        WHERE car_brand='Chevrolet' AND engine_code LIKE 'LEMON_CHEVROLET%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code in rows:
        tgt, note, fuel_fix = decide(model, year, code)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"Chevrolet LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    print("\nskips by reason:")
    for (m, n), c in Counter((s[1], s[3]) for s in skips).most_common(40): print(f"  {c:3} {m}: {n}")
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(15): print(f"  {c:3} {t}")

    if not apply:
        with open("database_enriched/csv_exports/23_lemon_batch6_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"Chevrolet",d[1],d[2],d[3],d[4],d[5] or "",d[6] or ""])
            for s in skips: w.writerow([s[0],"Chevrolet",s[1],s[2],"","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step15_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP15_VERIFIED')""",
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

    with open("database_enriched/csv_exports/23_lemon_batch6_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"Chevrolet",d[1],d[2],d[3],d[4],d[5] or "",d[6] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_CHEVROLET remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_CHEVROLET%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
