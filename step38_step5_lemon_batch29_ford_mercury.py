"""Step 38 (Step 5, batch 29): merged Ford + Mercury LEMON replacement — 148 rows (85 + 63).

Mercury was a trim-and-badge division: every Mercury here is a Ford twin (Mariner=Escape,
Milan=Fusion, Montego=Five Hundred, Monterey=Freestar, Mountaineer=Explorer, Sable=Taurus,
Grand Marquis=Crown Victoria, Cougar/Mystique=Contour), so the two brands share one engine
catalogue and are decoded in a single batch with brand-neutral rule keys.

Decode is by nameplate generation + the crawl displacement, using the Ford engine families
already verified in earlier steps (Triton V8/V10, Duratec, Cyclone, EcoBoost, Power Stroke):

- E-series / Super Duty chassis (`Cutaway`, `E450`, `F450`, `F550`): 5.4 Triton 255-260 and the
  6.8 Triton V10 305, which was the standard engine on E-450 and F-450/F-550.
- Taurus/Sable: 3.0 Vulcan OHV 155 -> 3.5 Cyclone 263 -> 288; Five Hundred/Montego 3.0 Duratec 203.
- Escape/Mariner and Fusion/Milan: 2.3 Duratec 153/160, 2.5 Duratec 171/175, 3.0 Duratec
  200 -> 240 (Escape family) and 221 -> 240 (Fusion family).
- Explorer/Mountaineer: 4.0 SOHC 210, 4.6 Triton 3V 292, 5.0 OHV 215, then 3.5 Cyclone 290.
- Mustang: 3.8 Essex 190 -> 2.3 EcoBoost 310/315, plus the 5.2 Voodoo GT350.
- Police/fleet rows: the Taurus-based Special Service Sedan (2.0 EcoBoost 240) and the
  Fusion Energi-based SSV Plug-In Hybrid Sedan (2.0 Atkinson PHEV 188, fuel -> Hybrid).
"""
import step5_lemon_lib as lib

CIT = {
    "WIKITAURUS6": "https://en.wikipedia.org/wiki/Ford_Taurus_(sixth_generation) (Police Interceptor Sedan / Special Service Police Sedan engine table: 2.0 EcoBoost I4 240hp = 'Special Service Sedan, designed only for detective and administrative uses'; 3.5 Ti-VCT 288hp; 3.5 EcoBoost 365hp; 3.7 Ti-VCT 305hp)",
    "KBB_TAURUS": "https://www.kbb.com/ford/taurus/ + caranddriver.com/ford/taurus (2019 Taurus standard engine = 3.5 V6 288hp @6500; 'this arrangement has been around since 2010, although the engine made just 263 horsepower back then')",
    "AUTOBLOG_SSV": "https://www.autoblog.com/2017/11/20/ford-special-service-plug-in-hybrid-police/ + https://www.carsaver.com/make/Ford/model/2020-special_service_plug-in_hybrid-32562 (Ford Special Service Plug-In Hybrid Sedan = Fusion Energi for non-pursuit duty, 2.0L Atkinson-cycle I4 plug-in hybrid, eCVT, 7.6 kWh battery, 21 miles electric range; sold MY2019-2020)",
    "FORDLINEUP": "Ford/Mercury US lineup ratings by model year: E-350/E-450 cutaway 5.4 Triton 255hp and 6.8 V10 305hp (V10 standard on E-450 and F-450/F-550 chassis cabs, 7.3 Power Stroke optional); Excursion 5.4 260hp; Expedition 5.4 3V 300hp (2005+); Explorer 4.0 SOHC 210hp, 5.0 OHV 215hp, 3.5 Cyclone 290hp (2011); Edge 3.5 285hp; Flex 3.5 262hp (2009-12) and 287hp (2013+); Focus 2.0 Zetec 130hp (2000-04) then 2.0 Duratec 20 136hp (2005-07); Freestar 3.9 Essex 193hp base / 4.2 Essex 201hp; Monterey 4.2 Essex 201hp; Windstar 3.8 Essex 200hp; Mustang 3.8 190hp (1999-2004), 2.3 EcoBoost 310hp (2015-23) / 315hp (2024); Ranger Raptor 3.0 EcoBoost 405hp (2024); Transit Connect 2.0 Duratec 136hp; Transit 3.7 Ti-VCT 275hp (2015-19), 3.5 Ti-VCT 275hp (2020+), 3.5 EcoBoost 310hp; F-150 3.5 Ti-VCT 282hp (2015-17) and 3.3 Ti-VCT 290hp (2018+); Crown Victoria/Grand Marquis 4.6 2V 200-215hp (2000-02) and 224hp (2003+, 239hp with dual exhaust); Escape/Mariner 2.3 153hp, 2.5 171hp, 3.0 200hp (2005-07) and 240hp (2008+); Fusion/Milan 2.3 160hp, 2.5 175hp, 3.0 221hp (2006-09) and 240hp (2010+); Five Hundred/Montego 3.0 Duratec 203hp; Explorer/Mountaineer 4.6 Triton 3V 292hp; Taurus/Sable 3.0 Vulcan OHV 155hp and 3.5 Cyclone 263hp; Villager 3.3 Nissan VG33E 170hp",
    "FDVOCAB": "DB Ford vocabulary already verified in steps 9/12/23: '4.6 Triton 2V' 4601/231, '5.4 Triton 2V' 5408/260, '5.4 Triton 3V' 5408/300, '6.8 Triton V10 2V' 6760/305, '3.5 Cyclone V6' 3496/282, '3.3 Ti-VCT V6' 3317/290, '3.5 V6 EcoBoost' 3500/365, '3.0 V6 EcoBoost' 2956/400, '2.3 EcoBoost' 2261/310, '2.0 T 16v Ecoboost' 2000/236, '2.5 I4 (Duratec 25)' 2488/170, '3.9 V6 (Essex)' 3905/190, '5.2 V8 (Voodoo)' 5163/526, '2.0 Energi (PHEV)' 1999/188 Hybrid, '3.0 V6' (Duratec 30) 3000/207, '4.0 V6' 4000/207, '5.0 V8' 5000/212, '3.8 V6' 3800, '2.3 16v' 2300/152, '2.0 Zetec' 2000/130, '2.0 Duratec' 2000/143, '2.5 V6 Duratec' 2500/168, 'VG33E' 3275/168",
}

NE = {
    "3.0 V6 (Vulcan)": ("3.0 V6 OHV Vulcan (Taurus/Sable 2000-2007, 155hp)", "Petrol", 2986, 155, 6),
    "4.2 V6 (Essex)": ("4.2 V6 OHV Essex (Freestar/Monterey 2004-2007, 201hp)", "Petrol", 4195, 201, 6),
    "4.6 Triton 3V": ("4.6 V8 Triton SOHC 3V (Explorer/Mountaineer/Mustang GT, 292-300hp)", "Petrol", 4601, 292, 8),
    "3.7 Ti-VCT V6 (Cyclone)": ("3.7 V6 Cyclone Ti-VCT (Transit/Mustang/Police Interceptor, 275-305hp)", "Petrol", 3726, 275, 6),
}

R = [
    # ================= FORD =================
    ("CUTAWAY", 2000, 2000, None, None, "5.4 Triton 2V", "E-350 cutaway chassis 2000 = 5.4 Triton 2V 255hp, the standard V8 [FORDLINEUP][FDVOCAB]", 255),
    ("CUTAWAY", 2008, 2012, None, None, "5.4 Triton 3V", "E-350/E-450 cutaway 2008-2012 = 5.4 Triton 3V 255hp [FORDLINEUP][FDVOCAB]", 255),
    ("E450", 2000, 2005, None, None, "6.8 Triton V10 2V", "E-450 = 6.8 Triton V10 305hp, the standard engine (7.3 Power Stroke optional) [FORDLINEUP][FDVOCAB]", 305),
    ("F450", 2000, 2004, None, None, "6.8 Triton V10 2V", "F-450 Super Duty = 6.8 Triton V10 305hp standard [FORDLINEUP][FDVOCAB]", 305),
    ("F550", 2000, 2004, None, None, "6.8 Triton V10 2V", "F-550 Super Duty = 6.8 Triton V10 305hp standard [FORDLINEUP][FDVOCAB]", 305),
    ("EDGE", 2011, 2011, None, None, "3.5 Cyclone V6", "2011 Edge = 3.5 Cyclone V6 285hp base volume engine [FORDLINEUP][FDVOCAB]", 285),
    ("ESCAPE", 2006, 2008, None, None, "2.3 16v", "Escape 2006-2008 bare = 2.3 Duratec I4 153hp base volume engine (3.0 V6 optional) [FORDLINEUP]", 153),
    ("EXCURSION", 2001, 2001, None, None, "5.4 Triton 2V", "2001 Excursion = 5.4 Triton 2V 260hp standard V8 (6.8 V10 and 7.3 PSD optional) [FORDLINEUP]", 260),
    ("EXPEDITION", 2005, 2006, None, None, "5.4 Triton 3V", "Expedition 2005-2006 = 5.4 Triton 3V 300hp, its only engine [FORDLINEUP][FDVOCAB]", 300),
    ("EXPLORER", 2001, 2001, None, None, "4.0 V6", "2001 Explorer = 4.0 SOHC V6 210hp base volume engine (5.0 V8 optional) [FORDLINEUP]", 210),
    ("EXPLORER", 2011, 2011, None, None, "3.5 Cyclone V6", "2011 Explorer (U502) = 3.5 Cyclone V6 290hp base volume engine [FORDLINEUP]", 290),
    ("F150", 2016, 2017, 3500, None, "3.5 Cyclone V6", "F-150 3500CC 2016-2017 = 3.5 Ti-VCT Cyclone 282hp, the standard (non-EcoBoost) V6 [FORDLINEUP][FDVOCAB]", 282),
    ("F150", 2022, 2024, None, None, "3.3 Ti-VCT V6", "F-150 2022-2024 bare = 3.3 Ti-VCT V6 290hp, the standard engine [FORDLINEUP][FDVOCAB]", 290),
    ("FLEX", 2010, 2012, None, None, "3.5 Cyclone V6", "Flex 2010-2012 = 3.5 Cyclone V6 262hp base volume engine (3.5 EcoBoost optional) [FORDLINEUP]", 262),
    ("FLEX", 2019, 2019, None, None, "3.5 Cyclone V6", "2019 Flex = 3.5 Cyclone V6 287hp base volume engine [FORDLINEUP]", 287),
    ("FOCUS", 2000, 2004, None, None, "2.0 Zetec", "Focus 2000-2004 = 2.0 Zetec 130hp volume engine (2.0 SPI 110hp on base LX) [FORDLINEUP]", 130),
    ("FOCUS", 2000, 2004, 2000, None, "2.0 Zetec", "Focus 2000CC 2004 = 2.0 Zetec 130hp [FORDLINEUP]", 130),
    ("FOCUS", 2005, 2007, None, None, "2.0 Duratec", "Focus 2005-2007 = 2.0 Duratec 20 136hp, the only engine after the Zetec was dropped [FORDLINEUP]", 136),
    ("FREESTAR", 2004, 2007, None, None, "3.9 V6 (Essex)", "Freestar = 3.9 Essex V6 193hp base volume engine (4.2 Essex 201hp optional) [FORDLINEUP][FDVOCAB]", 193),
    ("MUSTANG", 2000, 2000, None, None, "3.8 V6", "2000 Mustang = 3.8 Essex V6 190hp base volume engine (4.6 GT optional) [FORDLINEUP]", 190),
    ("MUSTANG", 2020, 2020, 5200, None, "5.2 V8 (Voodoo)", "2020 Mustang 5200CC = 5.2 Voodoo flat-plane V8, Shelby GT350, 526hp [FORDLINEUP][FDVOCAB]", 526),
    ("MUSTANG", 2021, 2023, None, None, "2.3 EcoBoost", "Mustang 2021-2023 bare = 2.3 EcoBoost 310hp base volume engine (5.0 GT optional) [FORDLINEUP]", 310),
    ("MUSTANG", 2024, 2024, None, None, "2.3 EcoBoost", "2024 Mustang (S650) bare = 2.3 EcoBoost 315hp base volume engine [FORDLINEUP]", 315),
    ("RANGER", 2024, 2024, 3000, None, "3.0 V6 EcoBoost", "2024 Ranger 3000CC = 3.0 EcoBoost V6 405hp (Ranger Raptor) [FORDLINEUP][FDVOCAB]", 405),
    ("SSV", 2019, 2020, None, None, "2.0 Energi (PHEV)", "Ford SSV Plug-In Hybrid Sedan (Fusion Energi for non-pursuit fleet duty) = 2.0 Atkinson PHEV 188hp (fuel -> Hybrid) [AUTOBLOG_SSV]", 188),
    ("SPECIAL", 2014, 2018, None, None, "2.0 T 16v Ecoboost", "Ford Special Service (Police) Sedan, Taurus-based = 2.0 EcoBoost I4 240hp [WIKITAURUS6]", 240),
    ("TAURUS", 2000, 2001, 3000, None, "3.0 V6 (Vulcan)", "Taurus 3000CC 2000-2001 = 3.0 Vulcan OHV 155hp, the base engine (Duratec 30 200hp optional) [FORDLINEUP][NEW]", 155),
    ("TAURUS", 2002, 2005, None, None, "3.0 V6 (Vulcan)", "Taurus 2002-2005 bare = 3.0 Vulcan OHV 155hp base volume engine [FORDLINEUP][NEW]", 155),
    ("TAURUS", 2010, 2012, None, None, "3.5 Cyclone V6", "Taurus 2010-2012 = 3.5 Cyclone V6 263hp base volume engine (SHO 3.5 EcoBoost optional) [KBB_TAURUS]", 263),
    ("TAURUS", 2018, 2019, None, None, "3.5 Cyclone V6", "Taurus 2018-2019 = 3.5 Cyclone V6 288hp standard engine [KBB_TAURUS][WIKITAURUS6]", 288),
    ("TRANSIT", 2010, 2013, None, None, "2.0 Duratec", "'Transit' 2010-2013 in the US = Transit Connect, 2.0 Duratec 136hp sole engine [FORDLINEUP]", 136),
    ("TRANSIT", 2017, 2018, None, None, "3.7 Ti-VCT V6 (Cyclone)", "Transit 2017-2018 = 3.7 Ti-VCT V6 275hp base volume engine [FORDLINEUP][NEW]", 275),
    ("TRANSIT", 2023, 2023, None, None, "3.5 Cyclone V6", "2023 Transit = 3.5 Ti-VCT PFDI V6 275hp base volume engine [FORDLINEUP]", 275),
    ("TRANSIT-350", 2015, 2015, 3500, None, "3.5 V6 EcoBoost", "Transit-350 3500CC 2015 = 3.5 EcoBoost V6 310hp (Transit tune) [FORDLINEUP][FDVOCAB]", 310),
    ("WINDSTAR", 2001, 2003, None, None, "3.8 V6", "Windstar = 3.8 Essex V6 200hp, its only engine [FORDLINEUP]", 200),

    # ================= MERCURY =================
    ("COUGAR", 2000, 2000, 2000, None, "2.0 Zetec", "Cougar 2000CC = 2.0 Zetec 125hp [FORDLINEUP]", 125),
    ("COUGAR", 2000, 2000, 2500, None, "2.5 V6 Duratec", "Cougar 2500CC = 2.5 Duratec V6 170hp [FORDLINEUP]", 170),
    ("MYSTIQUE", 2000, 2000, 2000, None, "2.0 Zetec", "Mystique 2000CC = 2.0 Zetec 125hp [FORDLINEUP]", 125),
    ("MYSTIQUE", 2000, 2000, 2500, None, "2.5 V6 Duratec", "Mystique 2500CC = 2.5 Duratec V6 170hp [FORDLINEUP]", 170),
    ("GRAND", 2000, 2000, None, None, "4.6 Triton 2V", "Grand Marquis 2000 = 4.6 Triton 2V 215hp [FORDLINEUP][FDVOCAB]", 215),
    ("GRAND", 2005, 2011, None, None, "4.6 Triton 2V", "Grand Marquis 2005-2011 = 4.6 Triton 2V 224hp (239hp with the dual-exhaust handling package) [FORDLINEUP]", 224),
    ("MARINER", 2005, 2008, 2300, None, "2.3 16v", "Mariner 2300CC = 2.3 Duratec I4 153hp [FORDLINEUP]", 153),
    ("MARINER", 2009, 2011, 2500, None, "2.5 I4 (Duratec 25)", "Mariner 2500CC = 2.5 Duratec 171hp [FORDLINEUP][FDVOCAB]", 171),
    ("MARINER", 2005, 2007, 3000, None, "3.0 V6", "Mariner 3000CC 2005-2007 = 3.0 Duratec V6 200hp [FORDLINEUP]", 200),
    ("MARINER", 2008, 2011, 3000, None, "3.0 V6", "Mariner 3000CC 2008-2011 = 3.0 Duratec V6 240hp (revised engine) [FORDLINEUP]", 240),
    ("MILAN", 2006, 2009, 2300, None, "2.3 16v", "Milan 2300CC = 2.3 Duratec I4 160hp (Fusion tune) [FORDLINEUP]", 160),
    ("MILAN", 2010, 2011, 2500, None, "2.5 I4 (Duratec 25)", "Milan 2500CC = 2.5 Duratec 175hp [FORDLINEUP][FDVOCAB]", 175),
    ("MILAN", 2006, 2009, 3000, None, "3.0 V6", "Milan 3000CC 2006-2009 = 3.0 Duratec V6 221hp [FORDLINEUP]", 221),
    ("MILAN", 2010, 2011, 3000, None, "3.0 V6", "Milan 3000CC 2010-2011 = 3.0 Duratec V6 240hp [FORDLINEUP]", 240),
    ("MONTEGO", 2005, 2007, None, None, "3.0 V6", "Montego (Five Hundred twin) = 3.0 Duratec V6 203hp, its only engine [FORDLINEUP]", 203),
    ("MONTEREY", 2005, 2007, None, None, "4.2 V6 (Essex)", "Monterey (Freestar twin) = 4.2 Essex V6 201hp, its only engine [FORDLINEUP][NEW]", 201),
    ("MOUNTAINEER", 2000, 2010, 4000, None, "4.0 V6", "Mountaineer 4000CC = 4.0 SOHC V6 210hp [FORDLINEUP]", 210),
    ("MOUNTAINEER", 2005, 2010, 4600, None, "4.6 Triton 3V", "Mountaineer 4600CC = 4.6 Triton 3V 292hp [FORDLINEUP][NEW]", 292),
    ("MOUNTAINEER", 2000, 2000, 5000, None, "5.0 V8", "Mountaineer 5000CC 2000 = 5.0 OHV V8 215hp [FORDLINEUP]", 215),
    ("SABLE", 2000, 2005, None, None, "3.0 V6 (Vulcan)", "Sable 2000-2005 = 3.0 Vulcan OHV 155hp base volume engine [FORDLINEUP][NEW]", 155),
    ("SABLE", 2008, 2009, None, None, "3.5 Cyclone V6", "Sable 2008-2009 (Taurus twin) = 3.5 Cyclone V6 263hp, its only engine [KBB_TAURUS]", 263),
    ("VILLAGER", 2000, 2000, None, None, "VG33E", "Villager (Nissan Quest twin) = 3.3 V6 VG33E 170hp, its only engine [FORDLINEUP][FDVOCAB]", 170),
]

TRIM = {
    ("SPECIAL", 2015, "SPECIALSERVI"): ("2.0 T 16v Ecoboost",
        "2015 Special Service Sedan = 2.0 EcoBoost I4 240hp [WIKITAURUS6]", 240, None),
}

IDENTITY = {
    "5.4 Triton 2V": ("Petrol", 5408), "5.4 Triton 3V": ("Petrol", 5408),
    "6.8 Triton V10 2V": ("Petrol", 6760), "4.6 Triton 2V": ("Petrol", 4601),
    "3.5 Cyclone V6": ("Petrol", 3496), "3.3 Ti-VCT V6": ("Petrol", 3317),
    "3.5 V6 EcoBoost": ("Petrol", 3500), "3.0 V6 EcoBoost": ("Petrol", 2956),
    "2.3 EcoBoost": ("Petrol", 2261), "2.0 T 16v Ecoboost": ("Petrol", 2000),
    "2.5 I4 (Duratec 25)": ("Petrol", 2488), "3.9 V6 (Essex)": ("Petrol", 3905),
    "5.2 V8 (Voodoo)": ("Petrol", 5163), "3.0 V6": ("Petrol", 3000),
    "4.0 V6": ("Petrol", 4000), "5.0 V8": ("Petrol", 5000), "3.8 V6": ("Petrol", 3800),
    "2.3 16v": ("Petrol", 2300), "2.0 Zetec": ("Petrol", 2000), "2.0 Duratec": ("Petrol", 2000),
    "2.5 V6 Duratec": ("Petrol", 2500), "VG33E": ("Petrol", 3275),
}

ROW_FIXES = {
    "2.0 Zetec": {"engine_type": "2.0 I4 DOHC Zetec (Focus 130 / Contour-Cougar-Mystique 125hp)",
                  "cylinders": 4, "data_confidence": "STEP38_VERIFIED"},
    "2.0 Duratec": {"engine_type": "2.0 I4 DOHC Duratec 20 (Focus 2005-07 136 / Transit Connect 136hp)",
                    "cylinders": 4, "data_confidence": "STEP38_VERIFIED"},
    "2.5 V6 Duratec": {"engine_type": "2.5 V6 DOHC Duratec 25 (Contour/Cougar/Mystique, 170hp)",
                       "power_hp": 170, "cylinders": 6, "data_confidence": "STEP38_VERIFIED"},
    "2.3 16v": {"engine_type": "2.3 I4 DOHC Duratec 23 / MZR (Escape-Mariner 153 / Fusion-Milan 160 / Ranger 143hp)",
                "cylinders": 4, "data_confidence": "STEP38_VERIFIED"},
    "3.8 V6": {"engine_type": "3.8 V6 OHV (Ford Essex: Mustang 190 / Windstar 200hp; row also holds Chrysler EGT 3.8 Wrangler rows)",
               "cylinders": 6, "data_confidence": "STEP38_VERIFIED"},
    "4.0 V6": {"engine_type": "4.0 V6 SOHC Cologne (Explorer/Mountaineer/Ranger/Mustang, 207-210hp)",
               "cylinders": 6, "data_confidence": "STEP38_VERIFIED"},
    "5.0 V8": {"engine_type": "5.0 V8 OHV Windsor 302 (Explorer/Mountaineer 2000-2001, 215hp)",
               "cylinders": 8, "data_confidence": "STEP38_VERIFIED"},
    "2.0 T 16v Ecoboost": {"engine_type": "2.0 I4 EcoBoost turbo (Edge/Explorer/Escape 240-245 / Special Service Sedan 240hp)",
                           "cylinders": 4, "data_confidence": "STEP38_VERIFIED"},
    "VG33E": {"engine_type": "3.3 V6 OHV Nissan VG33E (Quest/Villager 170 / Pathfinder-QX4 168hp)",
              "data_confidence": "STEP38_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand=["Ford", "Mercury"], step_tag="step38", csv_num=46,
    lemon_baseline=1022, engines_baseline=6645,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={"2.0 Energi (PHEV)": "Hybrid"},
    expect_mapped=148, expect_skipped=0,
))
