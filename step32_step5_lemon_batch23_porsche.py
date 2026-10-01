"""Step 32 (Step 5, batch 23): replace LEMON_PORSCHE codes with real OEM codes.
193 rows -> 185 mapped / 8 documented skips. (Rebuild after workspace rewind; all
decisions identical to the verified first pass - see session record.)
Key decodes: youcanic VIN pos-5 engine letters (997 A=3.6 C/B=3.8 S-GTS/D=Turbo-TS;
991 A=3.4/B=3.8/D=Turbo; 981 A=base/B=S; 92A Cayenne B=S/D=GTS/C=Turbo; 95B Macan B=3.0 S/F=3.6);
2015 rows carry EPA trim slugs (lemon crawl); fuel column disambiguates Cayenne E3
3000/4000CC 2019-2023 hybrid vs petrol rows.
Skips (8): 911 3800CC_VIND 2012+2013 (pos5-D merges 997.2 Turbo 500 + Turbo S 530);
Cayenne 3600CC 2015-18 x4 (958.2 3.6 bucket = base NA 300 / S TT 420 / GTS TT 440);
Macan 3000CC 2020+2021 (no 3.0L petrol Macan those years - S/GTS/Turbo all 2.9TT).
"""
import step5_lemon_lib as lib

CIT = {
    "YOUCAINIC": "https://www.youcanic.com/repair_guide/porsche-vin-decoder (pos-5 engine letters per platform)",
    "W997": "https://en.wikipedia.org/wiki/Porsche_997", "W991": "https://en.wikipedia.org/wiki/Porsche_991",
    "W992": "https://en.wikipedia.org/wiki/Porsche_992", "W987": "https://en.wikipedia.org/wiki/Porsche_987",
    "W981": "https://en.wikipedia.org/wiki/Porsche_981", "W718": "https://en.wikipedia.org/wiki/Porsche_718",
    "WCAY": "https://en.wikipedia.org/wiki/Porsche_Cayenne", "WPAN": "https://en.wikipedia.org/wiki/Porsche_Panamera",
    "WMAC": "https://en.wikipedia.org/wiki/Porsche_Macan",
    "E3": "2019 Cayenne E3 lineup: base 3.0T 335 / S 2.9TT 434 / E-Hybrid PHEV 455 combined / Turbo 4.0TT 541 (Porsche Newsroom + truecar + Car and Driver)",
    "PA9712": "2021+ Panamera 971.2: base 2.9TT 325 / 4S 443 / GTS 473 / Turbo discontinued -> Turbo S 620 / 4S E-Hybrid 552 / 4 E-Hybrid 455 (Porsche press)",
    "CY550": "2009-10 Cayenne 955.2/957 US: base 3.6 290 / S 4.8 385 / GTS 405 / Turbo 500 / Turbo S 550",
    "MT13": "MotorTrend 2012-13 911 US lineup (991 CS 400 / 997.2 Turbo/S sold through MY2013)",
    "CRAWL15": "lemon.dogeware.me crawl 2015 (EPA trim strings + oil data, 64 Porsche entries)",
    "DBVOCAB": "DB Porsche M-code vocabulary (MA1.22 981 base / MA1.23 981 S / M48.52 Turbo 493 / MDA.BA 532=540PS / MCF.TB 512=520PS etc.)",
    "LNENG": "https://docs.lnengineering.com/article/31-porsche-engine-oil-capacities-and-specifications (982 2.5 C40 5.7L; 982 4.0 C40 8L; 95B 2.9 C30 7.5L)",
    "NHTSA": "https://static.nhtsa.gov/odi/tsbs/2020/MC-10172079-0001.pdf (Porsche A40=0W-40, C40=0W-40/5W-40, C30=0W/5W-30, C20=0W-20)",
    "COSTAOIL": "https://costaoils.com/2021-porsche-panamera-2-9l-oil-change-guide-3/ (2021 Panamera 2.9 = 0W-30 Porsche C30)",
}

NE = {  # code: (engine_type, fuel, cc, hp, cyl, oil_vis, oil_cap_L, oil_note)
    "3.8 H6 (991.1 Carrera GTS)": ("3.8 H6 NA (911 Carrera GTS / 4 GTS 991.1, 430hp US)", "Petrol", 3800, 430, 6, "0W-40", 7.49, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "3.8T H6 (991.1 Turbo S)": ("3.8 H6 TT (911 Turbo S 991.1 560hp US; Turbo 520 = MA1.71)", "Petrol", 3800, 560, 6, "0W-40", 7.49, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "3.0T H6 (991.2 Carrera)": ("3.0 H6 TT (911 Carrera 991.2 370hp US base; S 420)", "Petrol", 3000, 370, 6, "0W-40", 7.52, "lemon.dogeware.me LEMON variant-majority [CRAWL15]"),
    "3.0T H6 (992.1 Carrera)": ("3.0 H6 TT (911 Carrera 992.1 379hp US; S 443)", "Petrol", 3000, 379, 6, "0W-20", 8.09, "Porsche C20 0W-20 [NHTSA]; cap lemon crawl [CRAWL15]"),
    "3.7T H6 (992.1 Turbo)": ("3.7 H6 TT (911 Turbo 992.1 572hp US; Turbo S 640)", "Petrol", 3700, 572, 6, "0W-20", 8.09, "Porsche C20 0W-20 [NHTSA]; cap lemon crawl [CRAWL15]"),
    "4.0 H6 (992.1 GT3)": ("4.0 H6 NA (911 GT3 992.1 502hp US; RS 518)", "Petrol", 4000, 502, 6, "0W-20", 8.09, "Porsche C20 0W-20 [NHTSA]; cap lemon crawl [CRAWL15]"),
    "3.4 H6 (981 GTS)": ("3.4 H6 NA (Boxster/Cayman GTS 981, 330/340hp US)", "Petrol", 3400, 335, 6, "0W-40", 7.5, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "2.0T H4 (718 base)": ("2.0 H4 Turbo (718 Boxster/Cayman base 300hp US 2017+)", "Petrol", 2000, 300, 4, "0W-40", 4.68, "lemon.dogeware.me LEMON variant-majority [CRAWL15]"),
    "2.9TT V6 (Cayenne S / Macan GTS)": ("2.9 V6 TT (Cayenne S 434hp E3 2019+ / Macan GTS 434)", "Petrol", 2894, 434, 6, "0W-30", 7.61, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "2.9TT V6 (Macan S)": ("2.9 V6 TT (Macan S 375hp US 2020+)", "Petrol", 2894, 375, 6, "0W-30", 7.5, "95B 2.9 C30 0W-30 7.5L [LNENG][NHTSA]"),
    "3.0T V6 PHEV (Cayenne E-Hybrid)": ("3.0 V6 TT + e-motor (Cayenne E-Hybrid E3, 455hp combined)", "Hybrid", 2995, 455, 6, "0W-20", 7.19, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "3.0T V6 (Cayenne base E3)": ("3.0 V6 TT (Cayenne base E3 335hp US 2019+)", "Petrol", 2995, 335, 6, "0W-20", 7.61, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "4.0T V8 (Cayenne Turbo)": ("4.0 V8 TT (Cayenne Turbo E3 541hp US)", "Petrol", 3996, 541, 8, "0W-40", 9.51, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "4.0T V8 (Cayenne GTS)": ("4.0 V8 TT (Cayenne GTS E3 453hp US 2022+)", "Petrol", 3996, 453, 8, "0W-40", 9.51, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "4.0T V8 PHEV (Cayenne Turbo S E-Hybrid)": ("4.0 V8 TT + e-motor (Cayenne Turbo S E-Hybrid 670hp combined)", "Hybrid", 3996, 670, 8, "0W-40", 8.99, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "3.0TT V6 (Panamera 971.1 base)": ("3.0 V6 TT (Panamera base 971.1 330hp US)", "Petrol", 2995, 330, 6, "0W-20", 7.19, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "2.9TT V6 PHEV (Panamera 4 E-Hybrid)": ("2.9 V6 TT + e-motor (Panamera 4 E-Hybrid 462hp combined)", "Hybrid", 2894, 462, 6, "0W-30", 6.81, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "2.9TT V6 (Panamera 971.2 base)": ("2.9 V6 TT (Panamera base 971.2 325hp US 2021+)", "Petrol", 2894, 325, 6, "0W-30", 8.59, "2021 Panamera 2.9 0W-30 C30 [COSTAOIL]; cap lemon crawl [CRAWL15]"),
    "4.0T V8 (Panamera Turbo)": ("4.0 V8 TT (Panamera Turbo 971 550hp US 2017-20)", "Petrol", 3996, 550, 8, "0W-40", 9.49, "lemon.dogeware.me LEMON 2015 [CRAWL15]"),
    "4.0T V8 (Panamera GTS)": ("4.0 V8 TT (Panamera GTS 971 473hp US 2021+)", "Petrol", 3996, 473, 8, "0W-40", 11.0, "kin Panamera Turbo 0W-40 [CRAWL15]"),
}

R = [
    # 718
    ("718", 2017, 2017, None, None, "2.0T H4 (718 base)", "718 base 2.0T 300hp sole 2017 [W718]", 300),
    ("718", 2018, 2024, 2000, None, "2.0T H4 (718 base)", "718 base 2.0T 300hp US [W718]", 300),
    ("718", 2018, 2021, 2500, None, "MDJ", "718 S 2.5T 350hp US (GTS 365 same bucket, S volume) [W718][DBVOCAB]", 350),
    ("718", 2020, 2024, 4000, None, "MDW", "718 GTS 4.0 394hp volume-default (GT4/Spyder 394-414 rare) [W718][DBVOCAB]", 394),
    # 911
    ("911", 2005, 2008, None, None, "M96.05", "997.1 Carrera 3.6 325hp US (bare + 3600CC 2008) [W997][DBVOCAB]", 325),
    ("911", 2008, 2008, 3600, None, "M96.05", "997.1 Carrera 3.6 325hp [W997]", 325),
    ("911", 2009, 2011, None, None, "MA1.02", "997.2 Carrera 3.6 345hp (direct-injection) [W997][DBVOCAB]", 345),
    ("911", 2012, 2012, 3600, "A", "MA1.02", "VIN pos5 A = 997.2 Carrera 3.6 345hp (991 launched MY2012, 997.2 runout) [YOUCAINIC][W991]", 345),
    ("911", 2012, 2014, None, None, "MA1.04", "991.1 Carrera 3.4 350hp US [W991][DBVOCAB]", 350),
    ("911", 2012, 2012, 3400, None, "MA1.04", "991.1 Carrera 3.4 350hp [W991]", 350),
    ("911", 2012, 2013, 3800, None, "MA1.03", "991.1 Carrera S 3.8 400hp volume-default (CS/4S = THE 3.8 of 2012-13) [W991][MT13]", 400),
    ("911", 2012, 2012, 3800, "B", "MA1.01S", "VIN pos5 B = 997.2 Carrera GTS 3.8 408hp (MY2011-12; 991 CS took bare row) [YOUCAINIC][DBVOCAB]", 408),
    ("911", 2016, 2019, None, None, "3.0T H6 (991.2 Carrera)", "991.2 Carrera 3.0T 370hp base-default (S 420 same bucket) [W991]", 370),
    ("911", 2017, 2017, 3000, None, "3.0T H6 (991.2 Carrera)", "991.2 Carrera 3.0T 370hp [W991]", 370),
    ("911", 2017, 2017, 3800, None, "MDA.BA", "991.2 Turbo 3.8TT 540hp volume-default (Turbo S 580 = MDB.CA separate; MDA.BA 532=540PS) [W991][DBVOCAB]", 540),
    ("911", 2021, 2021, None, None, "3.0T H6 (992.1 Carrera)", "992.1 Carrera 3.0T 379hp US [W992]", 379),
    ("911", 2022, 2023, 3000, None, "3.0T H6 (992.1 Carrera)", "992.1 Carrera 379hp (S 443/GTS 473 same bucket) [W992]", 379),
    ("911", 2022, 2023, 3700, None, "3.7T H6 (992.1 Turbo)", "992 Turbo 3.7T 572hp volume-default (Turbo S 640 same bucket) [W992]", 572),
    ("911", 2022, 2023, 4000, None, "4.0 H6 (992.1 GT3)", "992 GT3 4.0 502hp volume-default (GT3 RS 518 rare) [W992]", 502),
    # Carrera GT anomalous model row
    ("CARRERA", 2005, 2005, None, None, "M96.05", "911 Carrera 2005 3.6 325hp (M96.05 already carries 911 Carrera 2005 rows; NOT Carrera GT which is 5.7 V10 M80.01) [DBVOCAB]", 325),
    # Boxster
    ("BOXSTER", 2005, 2006, None, None, "M97.20", "987.1 Boxster 2.7 240hp [W987][DBVOCAB]", 240),
    ("BOXSTER", 2007, 2008, None, None, "M97.20", "987.1 facelift Boxster 2.7 245hp [W987]", 245),
    ("BOXSTER", 2009, 2012, None, None, "MA1.20", "987.2 Boxster 2.9 255hp [W987][DBVOCAB]", 255),
    ("BOXSTER", 2013, 2014, None, None, "MA1.22", "981 Boxster 2.7 265hp [W981][DBVOCAB]", 265),
    ("BOXSTER", 2016, 2016, None, None, "MA1.22", "981 Boxster 2.7 265hp [W981]", 265),
    # Cayman
    ("CAYMAN", 2006, 2008, None, None, "M97.20", "987.1 Cayman 2.7 245hp [W987][DBVOCAB]", 245),
    ("CAYMAN", 2009, 2012, None, None, "MA1.20", "987.2 Cayman 2.9 265hp [W987][DBVOCAB]", 265),
    ("CAYMAN", 2014, 2014, None, None, "MA1.22", "981 Cayman 2.7 275hp [W981][DBVOCAB]", 275),
    ("CAYMAN", 2016, 2016, None, None, "MA1.22", "981 Cayman 2.7 275hp [W981]", 275),
    # Cayenne
    ("CAYENNE", 2005, 2006, None, None, "M02.2Y", "955 base 3.2 VR6 247hp [WCAY][DBVOCAB]", 247),
    ("CAYENNE", 2008, 2008, None, None, "M55.01", "957 base 3.6 290hp [WCAY][DBVOCAB]", 290),
    ("CAYENNE", 2011, 2012, None, None, "M55.02", "958 base 3.6 300hp [WCAY][DBVOCAB]", 300),
    ("CAYENNE", 2009, 2010, 3600, None, "M55.01", "Cayenne 955.2/957 base 3.6 290hp sole 3.6 [CY550][DBVOCAB]", 290),
    ("CAYENNE", 2011, 2012, 3600, None, "M55.02", "958 base 3.6 300hp sole 3.6 (S = 4.8 until MY2015) [DBVOCAB]", 300),
    ("CAYENNE", 2013, 2014, 3600, None, "M55.02", "958 base 3.6 300hp sole 3.6 (S/GTS = 4.8 until MY2015) [DBVOCAB]", 300),
    ("CAYENNE", 2009, 2010, 4800, None, "M48.01", "957 Cayenne S 4.8 385hp [CY550][DBVOCAB]", 385),
    ("CAYENNE", 2014, 2014, 4800, None, "M48.02", "958.1 Cayenne S 4.8 400hp volume-default [DBVOCAB]", 400),
    ("CAYENNE", 2013, 2013, 4800, None, "M48.52", "958.1 Cayenne Turbo 4.8 500hp volume-default (unlettered bucket; M48.52 493=500PS) [DBVOCAB]", 500),
    ("CAYENNE", 2013, 2013, 4800, "B", "M48.02", "VIN pos5 B = Cayenne S 4.8 400hp [YOUCAINIC][DBVOCAB]", 400),
    ("CAYENNE", 2013, 2013, 4800, "D", "M48.02", "VIN pos5 D = Cayenne GTS 4.8 420hp (958.1 GTS 420PS; M48.02 stores 414=420PS) [YOUCAINIC][DBVOCAB]", 420),
    ("CAYENNE", 2015, 2018, 4800, None, "MCF.TB", "958.2 Cayenne Turbo 4.8 520hp (MCF.TB 512=520PS; S/GTS = 3.6TT) [WCAY][DBVOCAB]", 520),
    ("CAYENNE", 2013, 2016, 3000, None, "MCR.CA", "Cayenne Diesel 3.0 TDI 240hp (fuel col Diesel) [WCAY][DBVOCAB]", 240),
    ("CAYENNE", 2017, 2018, 3000, None, "MCG.EA", "958.2 Cayenne S E-Hybrid 3.0SC PHEV 413hp combined (fuel col Hybrid) [WCAY][DBVOCAB]", 413),
    ("CAYENNE", 2019, 2019, 3000, None, "3.0T V6 PHEV (Cayenne E-Hybrid)", "E3 Cayenne E-Hybrid 3.0T PHEV 455hp combined (fuel col Hybrid) [E3]", 455),
    ("CAYENNE", 2021, 2021, 3000, None, "3.0T V6 PHEV (Cayenne E-Hybrid)", "E3 Cayenne E-Hybrid PHEV 455hp (fuel col Hybrid; 2020 row = Petrol base) [E3]", 455),
    ("CAYENNE", 2020, 2023, 3000, None, "3.0T V6 (Cayenne base E3)", "E3 Cayenne base 3.0T 335hp sole 3.0 petrol (fuel col Petrol: 2020/2022/2023) [E3]", 335),
    ("CAYENNE", 2019, 2023, 2900, None, "2.9TT V6 (Cayenne S / Macan GTS)", "E3 Cayenne S 2.9TT 434hp [E3]", 434),
    ("CAYENNE", 2019, 2019, 4000, None, "4.0T V8 (Cayenne Turbo)", "E3 Cayenne Turbo 4.0TT 541hp (2019 sole 4.0 petrol) [E3]", 541),
    ("CAYENNE", 2021, 2021, 4000, None, "4.0T V8 (Cayenne Turbo)", "E3 Cayenne Turbo 4.0TT 541hp (fuel col Petrol; GTS launched mid-2021) [E3]", 541),
    ("CAYENNE", 2022, 2023, 4000, None, "4.0T V8 (Cayenne GTS)", "E3 Cayenne GTS 4.0 453hp volume-default (Turbo 541/Turbo GT 631 same bucket) [E3]", 453),
    ("CAYENNE", 2020, 2020, 4000, None, "4.0T V8 PHEV (Cayenne Turbo S E-Hybrid)", "Cayenne Turbo S E-Hybrid 4.0 PHEV 670hp combined (fuel col Hybrid) [E3-era]", 670),
    # Macan
    ("MACAN", 2017, 2018, 2000, None, "MCY.PA", "Macan 2.0T 252hp [WMAC][DBVOCAB]", 252),
    ("MACAN", 2019, 2021, 2000, None, "MCY.PA", "Macan 2.0T 248hp (2019 re-rate) [WMAC]", 248),
    ("MACAN", 2022, 2024, 2000, None, "MCY.PA", "Macan 2.0T 261hp (2022+) [WMAC]", 261),
    ("MACAN", 2015, 2018, 3000, None, "MCT.MA", "Macan S 3.0TT 340hp [WMAC][DBVOCAB]", 340),
    ("MACAN", 2019, 2019, 3000, None, "MCT.MA", "Macan S 3.0TT 348hp (2019 re-rate) [WMAC]", 348),
    ("MACAN", 2015, 2016, 3600, None, "MCT.LA", "Macan Turbo 3.6TT 400hp [WMAC][DBVOCAB]", 400),
    ("MACAN", 2020, 2024, 2900, None, "2.9TT V6 (Macan S)", "Macan S 2.9TT 375hp (2020+; GTS 434 same bucket, S volume) [WMAC]", 375),
    # Panamera
    ("PANAMERA", 2010, 2012, None, None, "M46.20", "Panamera 3.6 300hp [WPAN][DBVOCAB]", 300),
    ("PANAMERA", 2013, 2013, 3600, None, "M46.20", "Panamera 3.6 300hp [WPAN]", 300),
    ("PANAMERA", 2014, 2016, 3600, None, "M46.20", "Panamera 3.6 310hp (2014+) [WPAN]", 310),
    ("PANAMERA", 2012, 2013, 3000, None, "MCG.EA", "Panamera S Hybrid 3.0SC PHEV 375hp combined (fuel col Hybrid) [WPAN][DBVOCAB]", 375),
    ("PANAMERA", 2014, 2016, 3000, None, "MCW.DA", "970.2 Panamera S/4S 3.0TT 420hp (replaced 4.8 S) [WPAN][DBVOCAB]", 420),
    ("PANAMERA", 2017, 2020, 3000, None, "3.0TT V6 (Panamera 971.1 base)", "971.1 Panamera base 3.0TT 330hp [WPAN]", 330),
    ("PANAMERA", 2017, 2020, 2900, None, "2.9TT V6 PHEV (Panamera 4 E-Hybrid)", "971 Panamera 4 E-Hybrid 2.9TT PHEV 462hp combined (fuel col Hybrid) [WPAN]", 462),
    ("PANAMERA", 2021, 2023, 2900, None, "2.9TT V6 (Panamera 971.2 base)", "971.2 Panamera base 2.9TT 325hp volume-default (4S 443 same bucket) [PA9712]", 325),
    ("PANAMERA", 2017, 2020, 4000, None, "4.0T V8 (Panamera Turbo)", "971 Panamera Turbo 4.0TT 550hp [WPAN]", 550),
    ("PANAMERA", 2021, 2023, 4000, None, "4.0T V8 (Panamera GTS)", "971.2 Panamera GTS 4.0 473hp volume-default (plain Turbo discontinued; Turbo S 620) [PA9712]", 473),
    ("PANAMERA", 2013, 2013, 4800, None, "M48.40", "970.1 Panamera S 4.8 400hp [WPAN][DBVOCAB]", 400),
    ("PANAMERA", 2014, 2016, 4800, None, "MCW.BA", "970.2 Panamera Turbo 4.8 520hp (MCW.BA 512=520PS) [WPAN][DBVOCAB]", 520),
]

TRIM = {  # 2015 EPA trim slugs (post-year token)
    ("911", 2015, "911CARRERA2D"): ("MA1.04", "911 Carrera 2D 3.4 350hp [CRAWL15]", 350, None),
    ("911", 2015, "911CARRERA42"): ("MA1.04", "911 Carrera 4 2D 3.4 350hp [CRAWL15]", 350, None),
    ("911", 2015, "911TARGA4AUT"): ("MA1.04", "911 Targa 4 AT 3.4 350hp [CRAWL15]", 350, None),
    ("911", 2015, "911TARGA4STA"): ("MA1.04", "911 Targa 4 MT 3.4 350hp [CRAWL15]", 350, None),
    ("911", 2015, "911CARRERA4S"): ("MA1.03", "911 Carrera 4S 3.8 400hp [CRAWL15]", 400, None),
    ("911", 2015, "911CARRERAS2"): ("MA1.03", "911 Carrera S 2D 3.8 400hp [CRAWL15]", 400, None),
    ("911", 2015, "911TARGA4SAU"): ("MA1.03", "911 Targa 4S AT 3.8 400hp [CRAWL15]", 400, None),
    ("911", 2015, "911TARGA4SST"): ("MA1.03", "911 Targa 4S MT 3.8 400hp [CRAWL15]", 400, None),
    ("911", 2015, "911CARRERA4G"): ("3.8 H6 (991.1 Carrera GTS)", "911 Carrera 4 GTS 3.8 430hp [CRAWL15]", 430, None),
    ("911", 2015, "911CARRERAGT"): ("3.8 H6 (991.1 Carrera GTS)", "911 Carrera GTS 3.8 430hp [CRAWL15]", 430, None),
    ("911", 2015, "911GT3"): ("MA1.75", "911 GT3 3.8 475hp [CRAWL15][DBVOCAB]", 475, None),
    ("911", 2015, "911TURBO2DCO"): ("MA1.71", "911 Turbo 2D Coupe 3.8TT 520hp [CRAWL15][DBVOCAB]", 520, None),
    ("911", 2015, "911TURBOS2DC"): ("3.8T H6 (991.1 Turbo S)", "911 Turbo S 2D Coupe 3.8TT 560hp [CRAWL15]", 560, None),
    ("BOXSTER", 2015, "BOXSTERBASEA"): ("MA1.22", "Boxster base AT 2.7 265hp [CRAWL15]", 265, None),
    ("BOXSTER", 2015, "BOXSTERBASES"): ("MA1.22", "Boxster base MT 2.7 265hp [CRAWL15]", 265, None),
    ("BOXSTER", 2015, "BOXSTERSAUTO"): ("MA1.23", "Boxster S AT 3.4 315hp [CRAWL15][DBVOCAB]", 315, None),
    ("BOXSTER", 2015, "BOXSTERSSTAN"): ("MA1.23", "Boxster S MT 3.4 315hp [CRAWL15][DBVOCAB]", 315, None),
    ("BOXSTER", 2015, "BOXSTERGTSAU"): ("3.4 H6 (981 GTS)", "Boxster GTS AT 3.4 330hp [CRAWL15]", 330, None),
    ("BOXSTER", 2015, "BOXSTERGTSST"): ("3.4 H6 (981 GTS)", "Boxster GTS MT 3.4 330hp [CRAWL15]", 330, None),
    ("CAYMAN", 2015, "CAYMANBASEAU"): ("MA1.22", "Cayman base AT 2.7 275hp [CRAWL15]", 275, None),
    ("CAYMAN", 2015, "CAYMANBASEST"): ("MA1.22", "Cayman base MT 2.7 275hp [CRAWL15]", 275, None),
    ("CAYMAN", 2015, "CAYMANSAUTOM"): ("MA1.23", "Cayman S AT 3.4 325hp [CRAWL15][DBVOCAB]", 325, None),
    ("CAYMAN", 2015, "CAYMANSSTAND"): ("MA1.23", "Cayman S MT 3.4 325hp [CRAWL15][DBVOCAB]", 325, None),
    ("CAYMAN", 2015, "CAYMANGTSAUT"): ("3.4 H6 (981 GTS)", "Cayman GTS AT 3.4 340hp [CRAWL15]", 340, None),
    ("CAYMAN", 2015, "CAYMANGTSSTA"): ("3.4 H6 (981 GTS)", "Cayman GTS MT 3.4 340hp [CRAWL15]", 340, None),
}

SKIPS = {
    ("911", 2012, 3800, "D", None): "pos5-D bucket merges 997.2 Turbo 500 + Turbo S 530 - source letter cannot distinguish [YOUCAINIC]",
    ("911", 2013, 3800, "D", None): "pos5-D bucket merges 997.2 Turbo 500 + Turbo S 530 (997 Turbo/S still sold MY2013 per MT) [YOUCAINIC][MT13]",
    ("CAYENNE", 2015, 3600, None, None): "958.2 3.6 bucket = base NA 300 / S TT 420 / GTS TT 440 - no volume leader, undecidable [WCAY]",
    ("CAYENNE", 2016, 3600, None, None): "958.2 3.6 bucket = base NA 300 / S TT 420 / GTS TT 440 - undecidable",
    ("CAYENNE", 2017, 3600, None, None): "958.2 3.6 bucket = base NA 300 / S TT 420 / GTS TT 440 - undecidable",
    ("CAYENNE", 2018, 3600, None, None): "958.2 3.6 bucket = base NA 300 / S TT 420 / GTS TT 440 - undecidable",
    ("MACAN", 2020, 3000, None, None): "no 3.0L petrol Macan 2020-21 (S/GTS/Turbo all 2.9TT) - cc marker contradicts every candidate [WMAC]",
    ("MACAN", 2021, 3000, None, None): "no 3.0L petrol Macan 2020-21 (S/GTS/Turbo all 2.9TT) - cc marker contradicts every candidate [WMAC]",
}

IDENTITY = {
    "M96.05": ("Petrol", 3600), "MA1.02": ("Petrol", 3600), "MA1.04": ("Petrol", 3400),
    "MA1.03": ("Petrol", 3800), "MA1.01S": ("Petrol", 3800), "MA1.75": ("Petrol", 3800),
    "MA1.71": ("Petrol", 3800), "MDA.BA": ("Petrol", 3800), "M97.20": ("Petrol", 2700),
    "MA1.20": ("Petrol", 2900), "MA1.22": ("Petrol", 2700), "MA1.23": ("Petrol", 3400),
    "MDJ": ("Petrol", 2500), "MDW": ("Petrol", 4000), "M02.2Y": ("Petrol", 3200),
    "M55.01": ("Petrol", 3600), "M55.02": ("Petrol", 3600), "MCR.CA": ("Diesel", 3000),
    "MCG.EA": ("Petrol", 3000), "M48.01": ("Petrol", 4800), "M48.02": ("Petrol", 4800),
    "M48.52": ("Petrol", 4800), "MCF.TB": ("Petrol", 4800), "M46.20": ("Petrol", 3605),
    "MCW.DA": ("Petrol", 3000), "MCW.BA": ("Petrol", 4800), "M48.40": ("Petrol", 4800),
    "MCT.MA": ("Petrol", 3000), "MCT.LA": ("Petrol", 3600), "MCY.PA": ("Petrol", 2000),
}

lib.run_batch(lib.Cfg(
    brand="Porsche", step_tag="step32", csv_num=40,
    lemon_baseline=2106, engines_baseline=7679,
    R=R, NEW_ENGINES=NE,
    ROW_FIXES={
        "MDW": {"engine_type": "4.0 H6 NA (718 GTS 394hp 2020+ / GT4-Spyder 394-414)", "power_hp": 394},
        "MDJ": {"engine_type": "2.5 H4 Turbo (718 Boxster/Cayman S 350hp US, 2017-24)", "power_hp": 350},
    },
    ENG_FUEL_FIX={"MCG.EA": "Hybrid"},
    IDENTITY=IDENTITY, TRIM_RULES=TRIM, SKIP_NOTES=SKIPS,
    expect_mapped=185, expect_skipped=8,
))
