"""Step 33 (Step 5, batch 24): replace LEMON_LINCOLN codes with real Ford-family codes.
192 rows -> 189 mapped / 3 documented skips.
Key decodes (web-verified):
- MKS: 2009 bare = 3.5 NA 275; 2010-12 3500CC = 3.5 NA 273 volume-default (3.5 EB 355 shares
  bucket); 2010-12 3700CC = SKIP (3.7 not offered until 2013 - cc contradicts lineup);
  2013-16 3700CC = 3.7 300 / 3500CC = 3.5 EB 365 (only 3.5 left) [EDMUNDS13].
- MKT: 3.7 268 (2010-12) -> 300 (2013+); 3.5 EB 355 -> 365; 2000CC_VIN9 2013-16 = 2.0T 240
  livery-only special order [WIKIMKT].
- LS: V6 AJ30 210/220 (2002)/232 (2003+); V8 AJ35 252 -> 280; 2006 bare = V8 only [CARBUZZ]
  [CONSUMERGUIDE][WIKICARS].
- Town Car: 4.6 2V 200hp (2000-02) -> 239hp (2003+) [CARS.COM][FASTESTLAPS].
- MKZ: 3.5 263 (2007-12); 2.0T 240 (2013-16) -> 245 (2017+); 3.7 300; 3.0TT 350 FWD/400 AWD
  (volume-default 400) [USNEWS_MKZ][CARHP13]; Hybrid 2.5 191 (2011-12) -> 2.0 188 [CARHP13].
- MKX: 3.5 265 (2007-10) -> 3.7 305 (2011-14) -> 3.7 303 + 2.7TT 335 (2015-18).
- Nautilus: 2.0T 245 (2019) -> 250 (2020+) + 2.7TT 335 [AUTOPADRE].
- Corsair: 2.0T 250 / 2.3T 295 [USNEWSCORSAIR]; 2023+ 2500CC = Grand Touring PHEV 266
  combined (fuel col Petrol -> Hybrid fix) [MOTORTREND].
- Continental 2017-20: 3.7 305 / 2.7TT 335 / 3.0TT 400 [AUTOEVOLUTION]; 2000-02 = 4.6 DOHC 275.
- Aviator 2003-05 = 4.6 DOHC InTech 302 (new engine); 2020+ = 3.0TT 400 (Petrol rows,
  volume-default; Grand Touring PHEV 494 not fuel-flagged).
- Blackwood = 5.4 InTech 300; Mark LT = 5.4 Triton 3V 300; Zephyr 2006 = 3.0 Duratec 221.
"""
import step5_lemon_lib as lib

CIT = {
    "EDMUNDS13": "https://www.edmunds.com/lincoln/mks/2013/review/ (2013 MKS: 3.7 300hp up from 273, EB 365; KBB 2013 304-365)",
    "WIKIMKT": "https://en.wikipedia.org/wiki/Lincoln_MKT (3.7 268->303hp 2013, EB 355->365; 2.0 EcoBoost 240hp Town Car livery special-order 2013+; autopadre/KBB corroborate 268/355 and 300/365)",
    "CARBUZZ": "https://carbuzz.com/lincoln-ls-last-v8-powered-sports-sedan-rock-bottom-prices/ (LS: V6 210-220 -> 232hp 2003, V8 252 -> 280hp)",
    "CONSUMERGUIDE": "https://consumerguide.com/used/2000-02-lincoln-ls/ (LS V6 gained 10hp for 2002 = 220hp)",
    "WIKICARS": "https://wikicars.org/en/Lincoln_LS (2006 LS: V6 dropped with Zephyr introduction - V8 280 only)",
    "CARSTC": "https://cars.com/lincoln/town-car/2000/specifications (2000 Town Car 4.6 = 200hp SAE) + fastestlaps.com/models/lincoln-town-car (2005 = 239hp)",
    "AUTOEV": "https://www.autoevolution.com/lincoln/continental-1/ (2017-20 Continental: 3.7 NA 305 / 2.7TT 335 / 3.0TT 400 AWD)",
    "USNEWSMKZ": "https://cars.usnews.com/cars-trucks/lincoln/mkz/2017/performance (2017 MKZ: 2.0T 245, 3.0TT 350 FWD/400 AWD, Hybrid 188)",
    "USNEWSCORSAIR": "https://cars.usnews.com/cars-trucks/lincoln/corsair/2020/performance (Corsair 2.0T 250 / 2.3T 295) + motortrend.com (Grand Touring PHEV 266hp combined, 2021+)",
    "AUTOPADRE": "https://www.autopadre.com/horsepower-and-torque/lincoln-nautilus (Nautilus 2.0 245hp 2019 -> 250hp 2020+; 2.7 335)",
    "CARHP13": "https://carhp.com/lincoln/mkt-2013/specifications (2013 MKZ 2.0 240 / Hybrid 188; MKX 305hp)",
    "MOTORWEEK": "https://motorweek.org/road_tests/2020-lincoln-corsair/ (Corsair 250/295; 2.3 first used by Lincoln MKC)",
    "FORDVOCAB": "DB Ford-family codes: 2.0 T 16v Ecoboost (n=67), 2.3 EcoBoost, 2.7/3.0/3.5 EcoBoost, 3.5 Cyclone, 3.7 Ti-VCT, 4.6 V8, 3.0 V6, 2.5 I4 Hybrid 191, 2.0 Atkinson Hybrid 188, 5.4 InTech/Triton 3V, AJ30, 3.9 V8 (AJ35)",
    "LINHIST": "Lincoln US lineup history: MKC 2.0 240/2.3 285; Aviator 2003-05 302hp; Continental 2000-02 275hp; Blackwood 300hp; Mark LT 5.4 300hp; Zephyr 3.0 221hp; MKZ 2007-10 3.5 263hp; 2024-25 Nautilus 2.0T 250",
}

NE = {
    "4.6 V8 DOHC (InTech)": ("4.6 V8 DOHC 32v InTech (Aviator 2003-05 302hp / Continental FWD 2000-02 275hp / Marauder 302hp)", "Petrol", 4601, 302, 8),
    "2.5 I4 PHEV (Corsair Grand Touring)": ("2.5 I4 Atkinson PHEV eCVT (Corsair Grand Touring 2021+, 266hp combined)", "Hybrid", 2496, 266, 4),
}

R = [
    # Aviator
    ("AVIATOR", 2003, 2005, None, None, "4.6 V8 DOHC (InTech)", "Aviator 4.6 DOHC InTech 302hp sole engine [LINHIST][NEW]", 302),
    ("AVIATOR", 2020, 2025, None, None, "3.0 V6 EcoBoost", "Aviator 3.0TT 400hp standard (Grand Touring PHEV 494 not fuel-flagged; volume-default) [LINHIST][FORDVOCAB]", 400),
    # Blackwood
    ("BLACKWOOD", 2002, 2003, None, None, "5.4 InTech V8", "Blackwood 5.4 DOHC InTech 300hp sole (Navigator unit) [LINHIST][FORDVOCAB]", 300),
    # Continental
    ("CONTINENTAL", 2000, 2002, None, None, "4.6 V8 DOHC (InTech)", "Continental FWD 4.6 DOHC 32v 275hp sole [LINHIST][NEW]", 275),
    ("CONTINENTAL", 2017, 2020, 3700, None, "3.7 Ti-VCT V6", "Continental 3.7 NA 305hp standard [AUTOEV][FORDVOCAB]", 305),
    ("CONTINENTAL", 2017, 2018, 3700, "K", "3.7 Ti-VCT V6", "VIN K = Continental 3.7 305hp [AUTOEV]", 305),
    ("CONTINENTAL", 2017, 2020, 2700, "P", "2.7 EcoBoost", "VIN P = Continental 2.7TT 335hp [AUTOEV][FORDVOCAB]", 335),
    ("CONTINENTAL", 2017, 2020, 3000, "C", "3.0 V6 EcoBoost", "VIN C = Continental 3.0TT 400hp AWD [AUTOEV][FORDVOCAB]", 400),
    # Corsair
    ("CORSAIR", 2020, 2022, None, None, "2.0 T 16v Ecoboost", "Corsair base 2.0T 250hp volume-default [USNEWSCORSAIR][FORDVOCAB]", 250),
    ("CORSAIR", 2020, 2022, 2000, "9", "2.0 T 16v Ecoboost", "VIN 9 = Corsair 2.0T 250hp [USNEWSCORSAIR]", 250),
    ("CORSAIR", 2020, 2022, 2300, "H", "2.3 EcoBoost", "VIN H = Corsair 2.3T 295hp [USNEWSCORSAIR][MOTORWEEK]", 295),
    ("CORSAIR", 2023, 2025, 2000, None, "2.0 T 16v Ecoboost", "Corsair 2.0T 250hp (2023 refresh kept 2.0; 2.3 dropped) [USNEWSCORSAIR]", 250),
    ("CORSAIR", 2023, 2025, 2500, None, "2.5 I4 PHEV (Corsair Grand Touring)", "Corsair Grand Touring 2.5 PHEV 266hp combined (fuel col -> Hybrid) [USNEWSCORSAIR][NEW]", 266),
    # LS
    ("LS", 2000, 2001, 3000, None, "AJ30", "LS 3.0 V6 AJ30 210hp [CARBUZZ][FORDVOCAB]", 210),
    ("LS", 2002, 2002, 3000, None, "AJ30", "LS 3.0 V6 220hp (gained 10hp for 2002) [CONSUMERGUIDE]", 220),
    ("LS", 2003, 2005, 3000, None, "AJ30", "LS 3.0 V6 232hp (2003 breathing update) [CARBUZZ]", 232),
    ("LS", 2000, 2002, 3900, None, "3.9 V8 (AJ35)", "LS 3.9 V8 AJ35 252hp [CARBUZZ][FORDVOCAB]", 252),
    ("LS", 2003, 2005, 3900, None, "3.9 V8 (AJ35)", "LS 3.9 V8 280hp (2003 update) [CARBUZZ]", 280),
    ("LS", 2006, 2006, None, None, "3.9 V8 (AJ35)", "2006 LS = V8 only 280hp (V6 dropped for Zephyr) [WIKICARS]", 280),
    # MKC
    ("MKC", 2015, 2019, 2000, "9", "2.0 T 16v Ecoboost", "VIN 9 = MKC 2.0T 240hp [LINHIST][FORDVOCAB]", 240),
    ("MKC", 2015, 2019, 2000, None, "2.0 T 16v Ecoboost", "MKC 2.0T 240hp volume-default (bare rows) [LINHIST]", 240),
    ("MKC", 2015, 2019, 2300, "H", "2.3 EcoBoost", "VIN H = MKC 2.3T 285hp [LINHIST][MOTORWEEK][FORDVOCAB]", 285),
    # MKS
    ("MKS", 2009, 2009, None, None, "3.5 Cyclone V6", "2009 MKS 3.5 NA 275hp base (EB came MY2010) [EDMUNDS13][FORDVOCAB]", 275),
    ("MKS", 2010, 2012, 3500, None, "3.5 Cyclone V6", "MKS 3.5 NA 273hp volume-default (3.5 EB 355 shares 3.5 bucket) [EDMUNDS13]", 273),
    ("MKS", 2013, 2016, 3500, None, "3.5 V6 EcoBoost", "2013+ MKS: only 3.5 = EcoBoost 365hp (base moved to 3.7) [EDMUNDS13][FORDVOCAB]", 365),
    ("MKS", 2013, 2016, 3700, None, "3.7 Ti-VCT V6", "2013+ MKS base 3.7 300hp [EDMUNDS13][FORDVOCAB]", 300),
    # MKT
    ("MKT", 2010, 2012, 3700, None, "3.7 Ti-VCT V6", "MKT 3.7 268hp (2010-12) [WIKIMKT][FORDVOCAB]", 268),
    ("MKT", 2013, 2019, 3700, None, "3.7 Ti-VCT V6", "MKT 3.7 300hp (2013+) [WIKIMKT]", 300),
    ("MKT", 2010, 2012, 3500, None, "3.5 V6 EcoBoost", "MKT 3.5 EB 355hp (2010-12; sole 3.5) [WIKIMKT][FORDVOCAB]", 355),
    ("MKT", 2013, 2019, 3500, None, "3.5 V6 EcoBoost", "MKT 3.5 EB 365hp (2013+; sole 3.5) [WIKIMKT]", 365),
    ("MKT", 2013, 2013, 3500, "T", "3.5 V6 EcoBoost", "VIN T = MKT 3.5 EB 365hp (2013) [WIKIMKT]", 365),
    ("MKT", 2014, 2016, 3500, "T", "3.5 V6 EcoBoost", "VIN T = MKT 3.5 EB 365hp [WIKIMKT]", 365),
    ("MKT", 2013, 2016, 2000, "9", "2.0 T 16v Ecoboost", "VIN 9 = MKT Town Car livery 2.0T 240hp special-order [WIKIMKT][FORDVOCAB]", 240),
    # MKX
    ("MKX", 2007, 2010, None, None, "3.5 Cyclone V6", "MKX 3.5 265hp sole (2007-10) [LINHIST][FORDVOCAB]", 265),
    ("MKX", 2011, 2014, None, None, "3.7 Ti-VCT V6", "MKX 3.7 305hp sole (2011-14) [CARHP13][FORDVOCAB]", 305),
    ("MKX", 2016, 2018, 2700, "P", "2.7 EcoBoost", "VIN P = MKX 2.7TT 335hp [LINHIST][FORDVOCAB]", 335),
    ("MKX", 2016, 2018, 3700, "R", "3.7 Ti-VCT V6", "VIN R = MKX 3.7 303hp [LINHIST]", 303),
    # MKZ
    ("MKZ", 2007, 2010, None, None, "3.5 Cyclone V6", "MKZ 3.5 263hp sole petrol (2007-10) [LINHIST][FORDVOCAB]", 263),
    ("MKZ", 2012, 2012, None, None, "3.5 Cyclone V6", "2012 MKZ 3.5 263hp volume-default (2.0T/3.7 optional) [LINHIST]", 263),
    ("MKZ", 2013, 2016, 2000, "9", "2.0 T 16v Ecoboost", "VIN 9 = MKZ 2.0T 240hp [CARHP13][FORDVOCAB]", 240),
    ("MKZ", 2013, 2016, 3700, "K", "3.7 Ti-VCT V6", "VIN K = MKZ 3.7 300hp [CARHP13][FORDVOCAB]", 300),
    ("MKZ", 2011, 2011, None, None, "2.5 I4 Hybrid", "2011 MKZ Hybrid 2.5 Atkinson 191hp (fuel col Hybrid; sole 2011 row) [LINHIST][FORDVOCAB]", 191),
    ("MKZ", 2013, 2020, 2000, None, "2.0 Atkinson Hybrid", "MKZ Hybrid 2.0 Atkinson 188hp (fuel col Hybrid) [CARHP13][FORDVOCAB]", 188),
    ("MKZ", 2017, 2020, 2000, "9", "2.0 T 16v Ecoboost", "VIN 9 = MKZ 2.0T 245hp (2017+) [USNEWSMKZ]", 245),
    ("MKZ", 2019, 2019, 2000, None, "2.0 T 16v Ecoboost", "MKZ 2.0T 245hp (bare 2019 row, fuel col Petrol) [USNEWSMKZ]", 245),
    ("MKZ", 2017, 2020, 3000, "C", "3.0 V6 EcoBoost", "VIN C = MKZ 3.0TT 350 FWD/400 AWD (volume-default 400) [USNEWSMKZ][FORDVOCAB]", 400),
    # Mark LT
    ("MARK", 2006, 2008, None, None, "5.4 Triton 3V", "Mark LT 5.4 Triton 3V 300hp (F-150 unit) [LINHIST][FORDVOCAB]", 300),
    # Nautilus
    ("NAUTILUS", 2019, 2019, 2000, None, "2.0 T 16v Ecoboost", "Nautilus 2.0T 245hp (2019) [AUTOPADRE][FORDVOCAB]", 245),
    ("NAUTILUS", 2019, 2019, 2000, "9", "2.0 T 16v Ecoboost", "VIN 9 = Nautilus 2.0T 245hp (2019) [AUTOPADRE]", 245),
    ("NAUTILUS", 2020, 2023, 2000, None, "2.0 T 16v Ecoboost", "Nautilus 2.0T 250hp (2020+) [AUTOPADRE]", 250),
    ("NAUTILUS", 2020, 2023, 2000, "9", "2.0 T 16v Ecoboost", "VIN 9 = Nautilus 2.0T 250hp [AUTOPADRE]", 250),
    ("NAUTILUS", 2019, 2023, 2700, "P", "2.7 EcoBoost", "VIN P = Nautilus 2.7TT 335hp [AUTOPADRE][FORDVOCAB]", 335),
    ("NAUTILUS", 2020, 2023, 2700, None, "2.7 EcoBoost", "Nautilus 2.7TT 335hp (bare 2700CC rows) [AUTOPADRE]", 335),
    ("NAUTILUS", 2024, 2025, 2000, None, "2.0 T 16v Ecoboost", "2024+ Nautilus 2.0T 250hp sole petrol [LINHIST]", 250),
    # Town Car
    ("TOWN", 2000, 2002, None, None, "4.6 V8", "Town Car 4.6 2V 200hp (2000-02) [CARSTC][FORDVOCAB]", 200),
    ("TOWN", 2003, 2011, None, None, "4.6 V8", "Town Car 4.6 2V 239hp (2003+) [CARSTC][FORDVOCAB]", 239),
    # Zephyr
    ("ZEPHYR", 2006, 2006, None, None, "3.0 V6", "Zephyr 3.0 Duratec 221hp sole (Fusion-based) [LINHIST][FORDVOCAB]", 221),
]

TRIM = {
    ("MKX", 2015, "MKXAWD"): ("3.7 Ti-VCT V6", "2015 MKX AWD 3.7 303hp volume-default (2.7TT 335 optional; trim slug has no engine marker) [LINHIST]", 303, None),
    ("MKX", 2015, "MKXFWD"): ("3.7 Ti-VCT V6", "2015 MKX FWD 3.7 303hp volume-default [LINHIST]", 303, None),
}

SKIPS = {
    ("MKS", 2010, 3700, None, None): "3.7 not offered in MKS until 2013 (2010-12 = 3.5 NA 273 + 3.5 EB 355 only) - cc marker contradicts lineup [EDMUNDS13]",
    ("MKS", 2011, 3700, None, None): "3.7 not offered in MKS until 2013 - cc marker contradicts lineup [EDMUNDS13]",
    ("MKS", 2012, 3700, None, None): "3.7 not offered in MKS until 2013 - cc marker contradicts lineup [EDMUNDS13]",
}

IDENTITY = {
    "2.0 T 16v Ecoboost": ("Petrol", 2000), "2.3 EcoBoost": ("Petrol", 2261),
    "2.7 EcoBoost": ("Petrol", 2694), "3.0 V6 EcoBoost": ("Petrol", 2956),
    "3.5 Cyclone V6": ("Petrol", 3496), "3.5 V6 EcoBoost": ("Petrol", 3500),
    "3.7 Ti-VCT V6": ("Petrol", 3726), "4.6 V8": ("Petrol", 4600),
    "3.0 V6": ("Petrol", 3000), "2.5 I4 Hybrid": ("Hybrid", 2488),
    "2.0 Atkinson Hybrid": ("Hybrid", 1999), "5.4 InTech V8": ("Petrol", 5408),
    "5.4 Triton 3V": ("Petrol", 5408), "3.9 V8 (AJ35)": ("Petrol", 3902),
    "AJ30": ("Petrol", 3000),
}

lib.run_batch(lib.Cfg(
    brand="Lincoln", step_tag="step33", csv_num=41,
    lemon_baseline=1921, engines_baseline=7512,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, SKIP_NOTES=SKIPS, IDENTITY=IDENTITY,
    FUEL_FIX_BY_TARGET={"2.5 I4 PHEV (Corsair Grand Touring)": "Hybrid"},
    expect_mapped=189, expect_skipped=3,
))
