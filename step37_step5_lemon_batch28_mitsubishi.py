"""Step 37 (Step 5, batch 28): Mitsubishi LEMON replacement — 138 rows.

US/Canada Mitsubishi is a small, well-documented lineup, and the crawl rows carry displacement
on almost every multi-engine nameplate, so the decode is nameplate generation + displacement:

- Eclipse: 3G `2005` = 4G64 2.4 147 / 6G72 3.0 200; 4G `2006-12` = 4G69 2.4 162 / 6G75 3.8 263
  (265 from 2009). The `2018-25` "Eclipse" rows are the **Eclipse Cross** = 4B40 1.5 turbo 152.
- Galant/Endeavor/Montero: the PS-platform 3.8 6G75 at its three factory ratings (Galant 230,
  Endeavor 225, Montero 215) plus the 2.4 4G69 160 in the Galant.
- Lancer: 4G94 2.0 120 (`2005-07`) -> 4B11 2.0 152 (`2008-15`) / 148 (`2016-17`, VIN U) and
  4B12 2.4 168 (VIN W).
- Outlander: 4G69 160 (`2005-06`) -> 4B12 2.4 168 (`2007-13`) / 166 (`2014-20`) and 6B31 3.0
  220 (`2007-13`) / 224 (`2014-20`); the `2000CC` rows are the **Outlander Sport** (RVR) 4B11 148;
  `2021-25` is the 4th-gen CMF-C car with the Nissan-derived PR25DD 2.5 181.
- Mirage: 3A92 1.2 74 (`2014-16`) -> 78 (`2017-24`, facelift).
- Raider: a rebadged Dodge Dakota - EKG 3.7 V6 210 and the `4700CC` rows EVA 4.7 V8 230.
- i-MiEV: Y4F1 traction motor, fuel corrected Petrol -> **Electric**.
"""
import step5_lemon_lib as lib

CIT = {
    "MMPR06": "https://media.mitsubishicars.com/en-US/releases/release-379f633c714ed65dd27d29ce4b06fc27-2006-mitsubishi-eclipse-powertrain (Mitsubishi press kit: 2006 Eclipse GS = 4G69 2.4 MIVEC 162hp @6000; GT = 6G75 3.8 SOHC MIVEC V6, 3828cc, 263hp @5750 / 260 lb-ft)",
    "WIKIECL": "https://en.wikipedia.org/wiki/Mitsubishi_Eclipse (4th gen DK2A/DK4A: 2.4 4G69 162hp, 3.8 6G75 263hp; 2009-2012 V6 uprated to 265hp with the revised fascia and dual exhaust)",
    "DRVCHI05": "https://drivechicago.com/reviews/article/352/open-top-smile (2006 Eclipse GS 162hp 'up from 147 in 2005'; 'the 2005 Eclipse GT featured a 3.0-litre V6 generating 200 horses')",
    "CD_OLS": "https://www.caranddriver.com/mitsubishi/outlander-sport + cars.com 2023 Outlander Sport (Outlander Sport engines: 148-hp 2.0 4B11 / 168-hp 2.4; 2.4 = 2360cc, 168hp @6000, 167 lb-ft @4100)",
    "TRUECAR_OLS": "https://www.truecar.com/overview/mitsubishi/outlander-sport/ (OEM engine code listed for the 148hp 2.0 Outlander Sport: 4B11)",
    "MMLINEUP": "US/Canada Mitsubishi lineup ratings by model year: Galant 2.4 4G69 160hp / 3.8 6G75 230hp GTS (258hp in Ralliart tune); Endeavor 3.8 6G75 225hp sole engine 2004-2011; Montero 3.8 6G75 215hp 2003-2006; Lancer 2.0 4G94 120hp 2002-2007, 2.0 4B11 152hp 2008-2015 and 148hp 2016-2017, 2.4 4B12 168hp; Outlander 2.4 168hp 2007-2013 and 166hp 2014-2020, 3.0 6B31 220hp 2007-2013 and 224hp 2014-2020; Mirage 1.2 3A92 74hp 2014-2016 and 78hp from the 2017 facelift; Eclipse Cross 1.5 turbo 4B40 152hp 2018-2025; Outlander 2022+ PR25DD 2.5 181hp",
    "RAIDER": "Mitsubishi Raider (2006-2009) is a rebadged Dodge Dakota built at Warren Truck: 3.7 V6 (RPO EKG) 210hp standard, 4.7 V8 (EVA) 230hp optional - the same two engines the Dakota offered in those years.",
    "IMIEV": "Mitsubishi i-MiEV (US 2012-2017): rear-mounted Y4F1 permanent-magnet synchronous traction motor, 49 kW (66hp) / 145 lb-ft, 16 kWh lithium-ion pack - a battery electric vehicle, recorded as Petrol by the crawl.",
    "MMVOCAB": "DB Mitsubishi vocabulary already present: 4G64 2400, 4G69 2378/160, 6G72 3000, 6G75 3800/244, 4B11 2000/145, 4B12 2359/170, 6B31 2998/241, 3A92 1193/78, 4G94 2000/113, Y4F1 (Electric), EKG 3700, EVA 4701, PR25DD 2488/188",
}

NE = {
    "4B40": ("1.5 I4 DOHC MIVEC turbo DI (Eclipse Cross 2018-2025, 152hp)", "Petrol", 1498, 152, 4),
}

R = [
    # --- Eclipse (3G 2005, 4G 2006-2012) ---
    ("ECLIPSE", 2005, 2005, 2400, None, "4G64", "2005 Eclipse GS = 4G64 2.4 147hp (pre-MIVEC) [DRVCHI05][MMVOCAB]", 147),
    ("ECLIPSE", 2005, 2005, 3000, None, "6G72", "2005 Eclipse GT = 6G72 3.0 V6 200hp [DRVCHI05][MMVOCAB]", 200),
    ("ECLIPSE", 2006, 2012, 2400, None, "4G69", "Eclipse GS 2006-2012 = 4G69 2.4 MIVEC 162hp [MMPR06][WIKIECL]", 162),
    ("ECLIPSE", 2006, 2008, 3800, None, "6G75", "Eclipse GT 2006-2008 = 6G75 3.8 MIVEC V6 263hp [MMPR06][WIKIECL]", 263),
    ("ECLIPSE", 2009, 2012, 3800, None, "6G75", "Eclipse GT 2009-2012 = 6G75 3.8 V6 265hp (revised fascia + dual exhaust) [WIKIECL]", 265),
    ("ECLIPSE", 2011, 2011, None, None, "4G69", "2011 Eclipse bare = 4G69 2.4 162hp, the GS volume engine [MMPR06][MMLINEUP]", 162),
    # --- Eclipse Cross (the 2018+ "Eclipse" rows) ---
    ("ECLIPSE", 2018, 2025, None, None, "4B40", "2018-2025 'Eclipse' = Eclipse Cross, sole engine 4B40 1.5 turbo 152hp [MMLINEUP][NEW]", 152),
    # --- Endeavor / Montero / Galant ---
    ("ENDEAVOR", 2005, 2011, None, None, "6G75", "Endeavor = 6G75 3.8 V6 225hp, its only engine 2004-2011 [MMLINEUP]", 225),
    ("MONTERO", 2005, 2006, None, None, "6G75", "Montero (final US years) = 6G75 3.8 V6 215hp [MMLINEUP]", 215),
    ("GALANT", 2005, 2009, 2400, None, "4G69", "Galant 2400CC = 4G69 2.4 MIVEC 160hp [MMLINEUP][MMVOCAB]", 160),
    ("GALANT", 2005, 2009, 3800, None, "6G75", "Galant 3800CC = 6G75 3.8 V6 230hp (GTS volume rating; the Ralliart tune was 258hp) [MMLINEUP]", 230),
    ("GALANT", 2010, 2012, None, None, "4G69", "Galant 2010-2012 bare = 4G69 2.4 160hp, the only engine left after the V6 was dropped [MMLINEUP]", 160),
    # --- Lancer ---
    ("LANCER", 2005, 2007, None, None, "4G94", "Lancer 2005-2007 bare = 4G94 2.0 120hp (ES/OZ volume engine) [MMLINEUP][MMVOCAB]", 120),
    ("LANCER", 2008, 2008, None, None, "4B11", "2008 Lancer bare = 4B11 2.0 MIVEC 152hp, the new CY platform base engine [MMLINEUP]", 152),
    ("LANCER", 2009, 2015, 2000, None, "4B11", "Lancer 2000CC 2009-2015 = 4B11 2.0 152hp [MMLINEUP][TRUECAR_OLS]", 152),
    ("LANCER", 2016, 2017, 2000, None, "4B11", "Lancer 2000CC (VIN U) 2016-2017 = 4B11 2.0 148hp (revised rating) [MMLINEUP][CD_OLS]", 148),
    ("LANCER", 2009, 2017, 2400, None, "4B12", "Lancer 2400CC (VIN W where present) = 4B12 2.4 168hp [MMLINEUP][CD_OLS]", 168),
    # --- Mirage ---
    ("MIRAGE", 2014, 2016, None, None, "3A92", "Mirage 2014-2016 = 3A92 1.2 three-cylinder 74hp [MMLINEUP][MMVOCAB]", 74),
    ("MIRAGE", 2017, 2024, None, None, "3A92", "Mirage 2017-2024 (facelift) = 3A92 1.2 78hp [MMLINEUP][MMVOCAB]", 78),
    # --- Outlander / Outlander Sport ---
    ("OUTLANDER", 2005, 2006, None, None, "4G69", "Outlander (1st gen) 2005-2006 = 4G69 2.4 160hp sole engine [MMLINEUP][MMVOCAB]", 160),
    ("OUTLANDER", 2007, 2007, None, None, "4B12", "2007 Outlander bare = 4B12 2.4 168hp base volume engine (3.0 6B31 optional) [MMLINEUP]", 168),
    ("OUTLANDER", 2008, 2013, 2400, None, "4B12", "Outlander 2400CC 2008-2013 = 4B12 2.4 MIVEC 168hp [MMLINEUP][CD_OLS]", 168),
    ("OUTLANDER", 2014, 2020, 2400, None, "4B12", "Outlander 2400CC 2014-2020 = 4B12 2.4 166hp (3rd gen rating) [MMLINEUP]", 166),
    ("OUTLANDER", 2008, 2013, 3000, None, "6B31", "Outlander 3000CC 2008-2013 = 6B31 3.0 V6 220hp [MMLINEUP][MMVOCAB]", 220),
    ("OUTLANDER", 2014, 2020, 3000, None, "6B31", "Outlander 3000CC 2014-2020 = 6B31 3.0 V6 224hp [MMLINEUP][MMVOCAB]", 224),
    ("OUTLANDER", 2015, 2019, 2000, None, "4B11", "Outlander 2000CC (VIN U) = Outlander Sport 4B11 2.0 148hp [CD_OLS][TRUECAR_OLS]", 148),
    ("OUTLANDER", 2015, 2016, 2400, "W", "4B12", "Outlander 2400CC VIN W = Outlander Sport 2.4 4B12 168hp [CD_OLS]", 168),
    ("OUTLANDER", 2011, 2014, None, None, "4B12", "Outlander 2011-2014 bare = 4B12 2.4 168hp base volume engine [MMLINEUP]", 168),
    ("OUTLANDER", 2018, 2020, None, None, "4B12", "Outlander 2018-2020 bare = 4B12 2.4 166hp base volume engine [MMLINEUP]", 166),
    ("OUTLANDER", 2021, 2025, None, None, "PR25DD", "Outlander 2021-2025 (4th gen, CMF-C) = PR25DD 2.5 181hp, the sole combustion engine [MMLINEUP][MMVOCAB]", 181),
    # --- Raider (rebadged Dodge Dakota) ---
    ("RAIDER", 2006, 2009, None, None, "EKG", "Raider bare = EKG 3.7 V6 210hp, the Dakota's standard engine [RAIDER][MMVOCAB]", 210),
    ("RAIDER", 2006, 2007, 4700, None, "EVA", "Raider 4700CC = EVA 4.7 V8 230hp [RAIDER][MMVOCAB]", 230),
    # --- i-MiEV ---
    ("I MIEV", 2012, 2017, None, None, "Y4F1", "i-MiEV = Y4F1 PM synchronous traction motor, 49 kW / 66hp (fuel -> Electric) [IMIEV]", 66),
]

TRIM = {
    ("MIRAGE", 2015, "MIRAGEDEAUTO"): ("3A92", "2015 Mirage DE automatic = 3A92 1.2 74hp (trim, one engine only) [MMLINEUP]", 74, None),
    ("MIRAGE", 2015, "MIRAGEDESTAN"): ("3A92", "2015 Mirage DE manual = 3A92 1.2 74hp [MMLINEUP]", 74, None),
    ("MIRAGE", 2015, "MIRAGEESAUTO"): ("3A92", "2015 Mirage ES automatic = 3A92 1.2 74hp [MMLINEUP]", 74, None),
    ("MIRAGE", 2015, "MIRAGEESSTAN"): ("3A92", "2015 Mirage ES manual = 3A92 1.2 74hp [MMLINEUP]", 74, None),
    ("MIRAGE", 2015, "MIRAGERF"): ("3A92", "2015 Mirage RF = 3A92 1.2 74hp [MMLINEUP]", 74, None),
    ("OUTLANDER", 2015, "OUTLANDERSPO"): ("4B11", "2015 Outlander Sport = 4B11 2.0 148hp base volume engine [CD_OLS][TRUECAR_OLS]", 148, None),
}

IDENTITY = {
    "4G64": ("Petrol", 2400), "6G72": ("Petrol", 3000), "4G69": ("Petrol", 2378),
    "6G75": ("Petrol", 3800), "4B11": ("Petrol", 2000), "4B12": ("Petrol", 2359),
    "6B31": ("Petrol", 2998), "3A92": ("Petrol", 1193), "4G94": ("Petrol", 2000),
    "EKG": ("Petrol", 3700), "EVA": ("Petrol", 4701), "PR25DD": ("Petrol", 2488),
}

ROW_FIXES = {
    # inline-four and V6 engines recorded with the wrong cylinder count / placeholder descriptors
    "4G69": {"engine_type": "2.4 I4 SOHC 16v MIVEC (Eclipse GS 162 / Galant-Outlander 160hp)",
             "cylinders": 4, "brand_example": "Mitsubishi", "model_example": "Eclipse",
             "year_example": 2006, "data_confidence": "STEP37_VERIFIED"},
    "4B12": {"engine_type": "2.4 I4 DOHC 16v MIVEC (Outlander 166-168 / Lancer-Outlander Sport 168hp)",
             "cylinders": 4, "data_confidence": "STEP37_VERIFIED"},
    "4B11": {"engine_type": "2.0 I4 DOHC 16v MIVEC (Lancer 152 / Lancer-Outlander Sport 148hp)",
             "cylinders": 4, "data_confidence": "STEP37_VERIFIED"},
    "6G75": {"engine_type": "3.8 V6 SOHC 24v MIVEC (Eclipse GT 263-265 / Galant 230-258 / Endeavor 225 / Montero 215hp)",
             "cylinders": 6, "data_confidence": "STEP37_VERIFIED"},
    "6B31": {"engine_type": "3.0 V6 SOHC 24v MIVEC (Outlander 220hp 2007-13 / 224hp 2014-20)",
             "cylinders": 6, "data_confidence": "STEP37_VERIFIED"},
    "3A92": {"engine_type": "1.2 I3 DOHC 12v MIVEC (Mirage/Space Star, 74hp 2014-16 / 78hp 2017+)",
             "cylinders": 3, "data_confidence": "STEP37_VERIFIED"},
    "4G94": {"engine_type": "2.0 I4 SOHC 16v (Lancer ES/OZ 2002-2007, 120hp)",
             "cylinders": 4, "data_confidence": "STEP37_VERIFIED"},
    "4G64": {"engine_type": "2.4 I4 SOHC 16v (Eclipse GS 2000-2005 147hp / Galant 2.4)",
             "cylinders": 4, "data_confidence": "STEP37_VERIFIED"},
    "EKG": {"engine_type": "3.7 V6 SOHC PowerTech (Dakota/Raider/Liberty, 210hp)", "cylinders": 6,
            "data_confidence": "STEP37_VERIFIED"},
    "EVA": {"engine_type": "4.7 V8 SOHC PowerTech (Dakota/Raider 230hp / Grand Cherokee 235hp)",
            "cylinders": 8, "data_confidence": "STEP37_VERIFIED"},
    "Y4F1": {"engine_type": "Permanent-magnet synchronous traction motor (i-MiEV: 47 kW/64PS JDM, 49 kW/66hp US), 16 kWh pack",
             "power_hp": 66, "cylinders": None, "data_confidence": "STEP37_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Mitsubishi", step_tag="step37", csv_num=45,
    lemon_baseline=1160, engines_baseline=6782,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={"Y4F1": "Electric"},
    expect_mapped=138, expect_skipped=0,
))
