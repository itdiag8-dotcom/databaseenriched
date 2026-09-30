"""Step 28 (user-plan Step 5, batch 19 = MOPAR group): replace LEMON codes with real OEM codes.
441 rows: Dodge 207 + Chrysler 136 + Jeep 98 (single grouped batch per user directive).
Signals: cc markers (2400CC/VINB...), VIN letters (VINT 5.7, VINP 3.0 Hurricane, VINJ 6.4, VINX 3.2,
VINH/VINW 1.4T, VIN1 1.3), fuel column (Pacifica PHEV, Sprinter diesel), trim slugs (TOWNCOUNTRY*,
CVTRADESMAN, GRANDCARAVAN, VIPERBASE/GT/GTS, COMPASSLIMIT, PATRIOTLIMIT).
DB Mopar vocabulary (batch-2 + Euro catalog) reused: EZC/EZH 5.7, ESG 6.4 471, ETC/ETH Cummins,
Pentastars, EDZ/ED3/ECN/ED8 4cyl family, EGA/EGH/EGF/EGG/EER V6s, 6G72(SOHC24V), 4.0 I6 (AMC),
EKG 3.7, EXL EcoDiesel, 2.0 Turbo GME, 3.0 Hurricane I6, 8.3/8.4 V10s, 3.5 V6 (LX).
Web-verified: GW/Wagoneer powertrain table (Wiki WS); V8s dropped for 2024 (carscoops); Hornet GT
2.0 268 / R/T PHEV 1.3 288 (topspeed/lumsdodge); 2023+ Compass 2.0T 200hp (petersen/dealer guides);
Pacifica PHEV 260hp total (Stellantis media); Viper SR II 8.0 450hp (Wiki); LH 3.2 220hp (motales);
Cummins 5.9 CR 305 -> 325hp at 2004.5 (dieselpowerproducts/purediesel); Dart 1.4T/2.0/2.4 =
160/160/184 (Stellantis press); Sebring 2007 2.4/2.7/3.5 = 173/189/235 (edmunds); Neon 2.0 132
(wiki); T&C 2008 3.3/3.8/4.0 = 175/197/251 (edmunds); Sprinter 03-06 2.7 I5 diesel / 07+ 3.5 V6
254 petrol (moparpartsgiant/kbb).
Skips (58): bare rows with 2-engine ambiguity (T&C 00-07 3.3/3.8, Grand Caravan 01-07, Compass/
Patriot 07-16 2.0/2.4, Sebring/Stratus/Avenger/Cirrus/Concorde/Intrepid/Journey/Caliber bare,
Wagoneer 2023 5.7-vs-Hurricane, GC 2022/2025), Pacifica 3.8 2008 (4.0-only year), Ram 5.9 2004
(mid-year 305/325 split), 5.9 2008-09 (engine ended 2007.5 - impossible).
"""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "GWWIKI": "https://en.wikipedia.org/wiki/Jeep_Grand_Wagoneer_(WS) (Wagoneer 5.7 eTorque 392hp 2022-23, Hurricane SO 420hp 2023-25; Grand Wagoneer 6.4 471hp 2022-23, Hurricane H.O. 510hp 2022-24, 540hp for 2025)",
    "V8DROP": "carscoops.com 2023/09 fleet-guide coverage (V8s dropped from 2024 Wagoneer/Grand Wagoneer - Hurricane I6 only, 420/510) + moparinsiders.com (Hurricane SO added to 2023 Wagoneer base)",
    "VINP": "ebay 2023 Grand Wagoneer L engine listing (VIN 8th digit P = 3.0 Hurricane I6) - VIN decode for VINP rows",
    "GCNOTHURR": "roadandtrack.com (Grand Cherokee gets Hurricane only MY2028 -> GC rows are not Hurricane) - separates JEEP_GRAND (Grand Wagoneer) from GRAND_CHEROKEE",
    "HORNET": "topspeed.com 2024 Dodge Hornet + lumsdodge.com (Hornet GT = 2.0 Hurricane4 268hp AWD; R/T PHEV = 1.3 GSE turbo + 90kW motor 15.5kWh = 288hp net, R/T = 2024 MY)",
    "COMPASS25": "https://www.drivepetersen.com/jeep-compass/ (2023-2025 Compass standard 2.0L turbo I4 200hp, replacing 2.4)",
    "PACHPHEV": "https://stellantis-na-product-media.info/chrysler/pacifica-hybrid (Pacifica PHEV 3.6 Pentastar Atkinson + eFlite EVT = 260hp total system) + https://www.kbb.com/car-news/chrysler-pacifica-hybrid-how-it-works/",
    "VIPERSRII": "https://en.wikipedia.org/wiki/Dodge_Viper_(SR_II) (RT/10 1998-2002 and GTS = 8.0 V10 450hp; ACR 460)",
    "VIPERGENV": "Dodge Viper Gen V (2013-17) = 8.4 V10 640hp, 645hp for 2016-17 (allpar/Viper spec sheets; DB '8.4 V10 SRT10' 599hp row covers Gen IV 2008-10 600hp)",
    "LH32": "https://www.motales.com/engines/V8/V6-32.php (1998 Intrepid/Concorde 3.2 V6 = 220hp; LH 3.5 = 214-250) + fraserengineco.com/3-2l-chrysler-dodge-engine/ (3.2 = 3195cc DOHC 24v)",
    "CUMMINS": "https://dieselpowerproducts.com/blogs/blogs/2003-2004-5-9-cummins-buyer-s-guide-specs-problems-upgrades + https://puredieselpower.com/blog/post/3rd-gen-cummins-overview (5.9 CR: 2003-early04 SO 305hp; 2004.5-07 HO 325hp; 6.7 from 2007.5)",
    "DART": "https://media.stellantisnorthamerica.com/newsrelease.do?id=11858 (2013 Dart: 1.4 MultiAir Turbo 160hp / Tigershark 2.0 160hp / Tigershark 2.4 MultiAir2 184hp) + thecarconnection.com/overview/dodge_dart_2013",
    "SEBRING07": "https://www.edmunds.com/chrysler/sebring/2007/review/ (2007 Sebring 2.4 173 / 2.7 189 / 3.5 235hp) - JS 3.5 -> EGF row",
    "NEON": "https://automobile.fandom.com/wiki/Dodge_Neon (2nd-gen 2000-05 US sole engine 2.0 SOHC 132hp; SRT-4 2.4T 215/230hp)",
    "TC08": "https://www.edmunds.com/chrysler/town-and-country/2008/review/ (2008 T&C 3.3 175 / 3.8 197 / 4.0 251hp) + https://carbuzz.com/cars/chrysler/town-country/2008/",
    "SPRINTER": "https://www.moparpartsgiant.com/dodge-sprinter_3500-parts.html (Sprinter 2003-06 2.7 I5 OM612 turbodiesel; 2007+ 3.5 gas V6 254hp + 3.0 OM642 TD) + https://www.kbb.com/dodge/sprinter/2007/",
    "MOPARVOCAB": "DB Mopar vocabulary (batch 2 + Euro catalog): EDZ 2.4 150 (PT/Sebring RG), ED3 2.4 World GEMA 172-173 (Caliber/200), ECN 2.0 World 158, ED8 2.4 NULL-junk (fill: Tigershark 184), EGA 3.3, EGH 3.8, EGF 3.5 JS 238, EGG 3.5 LH 252, EER 2.7, EKG 3.7 PowerTech, EZC/EZH 5.7 HEMI, ESG 6.4 471 (SRT8), ETC/ETH 5.9 Cummins SO/HO, 6G72(SOHC24V) 3.0 Mitsu, 4.0 I6 (AMC) 190, 3.2/3.6 Pentastar, 2.0 Turbo GME 268, 3.0 Hurricane I6 420, 8.3 V10 SRT 500, 8.4 V10 SRT10 599, 3.5 V6 (LX) 250, '2.4 16v Turbo SRT-4' (Neon 2003 link), '4.0 V6 (Chrysler, Routan)' 4.0 OHV 251",
    "MOPARHIST": "US Mopar model history (300M/LHS/Prowler 3.5-only; Crossfire 3.2 M112-only; PT 2.4-only; Neon 2.0-only; Sebring/Stratus coupe 3.0 6G72 200hp; minivan 3.0 6G72 150hp 2000; Dakota 3.7 from 2005; Nitro 4.0 SOHC 260; Pacifica 3.5/3.8/4.0 253; Ram HD gas 5.7-only 2006+; Ram Chassis Cab 5.9 Cummins 5900cc; Journey 2019-20 2.4-only; Renegade 2021+ 1.3T-only US; Hornet 2023 GT-only)",
}

NEW_ENGINES = {
    "1.8 World Engine (GEMA)": ("1.8 I4 World Engine GEMA (Caliber, 148hp)", "Petrol", 1798, 148, 4),
    "2.0 SOHC 16v (Neon)": ("2.0 I4 SOHC 16v (Neon 2000-05, 132hp)", "Petrol", 1996, 132, 4),
    "1.4 MultiAir Turbo (Dart/Renegade)": ("1.4 I4 MultiAir Turbo (Dart 2013-16 / Renegade 2015-18, 160hp)", "Petrol", 1368, 160, 4),
    "2.0 TigerShark (Dart)": ("2.0 I4 TigerShark 16v (Dart 2013-16, 160hp)", "Petrol", 1998, 160, 4),
    "1.3 GSE Turbo (Renegade)": ("1.3 I4 GSE Turbo (Renegade 2019-23, 177hp)", "Petrol", 1288, 177, 4),
    "1.3 GSE PHEV (Hornet R/T)": ("1.3 I4 GSE Turbo + 90kW motor (Hornet R/T PHEV, 288hp net)", "Hybrid", 1288, 288, 4),
    "3.2 V6 (LH)": ("3.2 V6 DOHC 24v LH (Intrepid/Concorde 1998-2001, 220hp)", "Petrol", 3232, 220, 6),
    "8.0 V10 (Viper Gen II)": ("8.0 V10 (Viper SR II RT/10+GTS 2000-02, 450hp)", "Petrol", 7990, 450, 10),
    "8.4 V10 (Viper Gen V)": ("8.4 V10 (Viper Gen V 2013-17, 640hp / 645hp 2016-17)", "Petrol", 8382, 640, 10),
    "3.0 Hurricane I6 H.O. (Grand Wagoneer)": ("3.0 I6 Hurricane H.O. twin-turbo (Grand Wagoneer, 510hp / 540hp 2025)", "Petrol", 2996, 510, 6),
    "5.7 HEMI V8 eTorque (Wagoneer)": ("5.7 V8 HEMI eTorque mild-hybrid (Wagoneer 2022-23, 392hp)", "Petrol", 5654, 392, 8),
    "3.6 V6 Pentastar PHEV (Pacifica Hybrid)": ("3.6 V6 Pentastar Atkinson + eFlite EVT dual-motor (Pacifica PHEV, 260hp total)", "Hybrid", 3604, 260, 6),
}

ROW_FIXES = {
    "ED8": {"engine_type": "2.4 I4 Tigershark MultiAir2 (Dart R/T / Cherokee / Compass 2017+ / Renegade / 200 2015+, 180-184hp)", "displacement_cc": 2360, "power_hp": 184},
    "EGS": {"engine_type": "4.0 V6 SOHC (Nitro R/T 260hp / Pacifica 2007-08 253hp)"},
    "4.0 V6 (Chrysler, Routan)": {"engine_type": "4.0 V6 OHV (Chrysler minivans: T&C/Grand Caravan 2008-10 + Routan, 251hp)"},
    "ETH": {"engine_type": "5.9 I6 Cummins HO Turbo Diesel (Ram HD: 2001-02 VP44 245hp US / 2004.5-07 common-rail 325hp)"},
    "OM612DE27LA": {"displacement_cc": 2685, "engine_type": "2.7 I5 turbodiesel OM612 (Dodge Sprinter 2003-06 154hp / C270 CDI, 154-170hp)"},
    "6G72(SOHC24V)": {"engine_type": "3.0 V6 6G72 SOHC 24v (Mitsubishi family: Magna/Pajero; Chrysler Sebring/Stratus coupe 200hp; minivans 2000 150hp)"},
    "2.4 16v Turbo SRT-4": {"engine_type": "2.4 I4 DOHC Turbo (Neon SRT-4 A855, 215hp 2003 / 230hp 2004-05)", "power_hp": 230},
}

FUEL_FIX_BY_TARGET = {"1.3 GSE PHEV (Hornet R/T)": "Hybrid", "ETH": "Diesel", "OM612DE27LA": "Diesel"}

IDENTITY = {  # pre-existing targets: {code: (fuel, cc)} - batch-17 standing rule
    "EDZ": ("Petrol", 2400), "ED3": ("Petrol", 2360), "ECN": ("Petrol", 2000), "ED8": ("Petrol", 2360),
    "EGA": ("Petrol", 3300), "EGH": ("Petrol", 3778), "EGF": ("Petrol", 3500), "EGG": ("Petrol", 3500),
    "EGX": ("Petrol", 3200), "EER": ("Petrol", 2700), "EKG": ("Petrol", 3700), "EZC": ("Petrol", 5700),
    "EZH": ("Petrol", 5654), "ESG": ("Petrol", 6400), "EGS": ("Petrol", 3952), "ETH": ("Diesel", 5900),
    "6G72(SOHC24V)": ("Petrol", 3000), "2.4 16v Turbo SRT-4": ("Petrol", 2400), "3.5 V6 (LX)": ("Petrol", 3500),
    "8.3 V10 SRT": ("Petrol", 8300), "8.4 V10 SRT10": ("Petrol", 8400), "4.0 I6 (AMC)": ("Petrol", 3956),
    "3.2 Pentastar": ("Petrol", 3239), "3.6 Pentastar": ("Petrol", 3604), "3.0 Hurricane I6": ("Petrol", 2996),
    "2.0 Turbo GME": ("Petrol", 2000), "OM612DE27LA": ("Diesel", 2700), "M272E35": ("Petrol", 3500),
    "4.0 V6 (Chrysler, Routan)": ("Petrol", 3952),
}

# (brand, MODEL-upper, y0, y1, cc, target, evidence, pfix)   cc=None = bare (no CC marker)
R = [
    # --- Chrysler ---
    ("Chrysler", "200", 2011, 2011, 2400, "ED3", "200 2011 2.4 = World GEMA 173hp (Tigershark came 2015) [MOPARVOCAB]", 173),
    ("Chrysler", "200", 2014, 2014, 2400, "ED3", "200 2012-14 2.4 (VINB) = World GEMA 173hp (DB links 2012-14 ED3) [MOPARVOCAB]", 173),
    ("Chrysler", "200", 2011, 2017, 3600, "3.6 Pentastar", "200 3.6 (VING) = Pentastar 283hp [MOPARVOCAB]", 283),
    ("Chrysler", "300M", 2000, 2004, None, "EGG", "300M = 3.5 SOHC only, 250hp [MOPARHIST][MOPARVOCAB]", 250),
    ("Chrysler", "CONCORDE", 2002, 2004, 2700, "EER", "Concorde 2.7 = EER 200hp [MOPARVOCAB]", 200),
    ("Chrysler", "CONCORDE", 2002, 2004, 3500, "EGG", "Concorde LXi/Limited 3.5 = EGG 250hp [MOPARHIST]", 250),
    ("Chrysler", "CROSSFIRE", 2004, 2008, None, "EGX", "Crossfire = 3.2 M112 only, 215hp (DB EGX row = Crossfire) [MOPARVOCAB]", 215),
    ("Chrysler", "GRAND", 2000, 2000, 3000, "6G72(SOHC24V)", "Grand Voyager 3.0 2000 = Mitsubishi 6G72, 150hp [MOPARHIST][MOPARVOCAB]", 150),
    ("Chrysler", "GRAND", 2000, 2000, 3300, "EGA", "Grand Voyager 3.3 2000 = EGA 180hp [MOPARVOCAB]", 180),
    ("Chrysler", "LHS", 2000, 2001, None, "EGG", "LHS = 3.5 SOHC only, 250hp [MOPARHIST]", 250),
    ("Chrysler", "PACIFICA", 2004, 2004, None, "EGG", "Pacifica 2004 launch = 3.5 250hp [MOPARHIST]", 250),
    ("Chrysler", "PACIFICA", 2020, 2025, None, "3.6 Pentastar", "Pacifica gas 2017+ = 3.6 Pentastar 287hp [MOPARHIST]", 287),
    ("Chrysler", "PACIFICA", 2005, 2006, 3500, "EGG", "Pacifica 3.5 = 250hp [MOPARHIST]", 250),
    ("Chrysler", "PACIFICA", 2005, 2007, 3800, "EGH", "Pacifica 3.8 = 215hp [MOPARHIST][MOPARVOCAB]", 215),
    ("Chrysler", "PACIFICA", 2007, 2008, 4000, "EGS", "Pacifica 4.0 2007-08 = SOHC 4.0, 253hp [MOPARHIST][ROW_FIX EGS]", 253),
    ("Chrysler", "PROWLER", 2001, 2002, None, "EGG", "Prowler = 3.5 SOHC only, 250hp [MOPARHIST]", 250),
    ("Chrysler", "PT", 2001, 2010, None, "EDZ", "PT Cruiser base = 2.4 EDZ 150hp [NEON][MOPARVOCAB]", 150),
    ("Chrysler", "SEBRING", 2001, 2006, 2400, "EDZ", "Sebring JR 2.4 = EDZ 150hp [MOPARVOCAB]", 150),
    ("Chrysler", "SEBRING", 2007, 2010, 2400, "ED3", "Sebring JS 2.4 = World GEMA 173hp [SEBRING07][MOPARVOCAB]", 173),
    ("Chrysler", "SEBRING", 2001, 2006, 2700, "EER", "Sebring JR 2.7 = 200hp [MOPARVOCAB]", 200),
    ("Chrysler", "SEBRING", 2007, 2010, 2700, "EER", "Sebring JS 2.7 = 189hp [SEBRING07]", 189),
    ("Chrysler", "SEBRING", 2001, 2005, 3000, "6G72(SOHC24V)", "Sebring coupe 3.0 = 6G72 200hp (Mitsubishi-platform) [MOPARHIST][MOPARVOCAB]", 200),
    ("Chrysler", "SEBRING", 2007, 2010, 3500, "EGF", "Sebring JS 3.5 = 235hp (DB EGF row = JS 3.5) [SEBRING07][MOPARVOCAB]", 235),
    ("Chrysler", "TOWN", 2008, 2010, 3300, "EGA", "T&C 2008-10 3.3 = 175hp [TC08]", 175),
    ("Chrysler", "TOWN", 2008, 2010, 3800, "EGH", "T&C 2008-10 3.8 = 197hp [TC08]", 197),
    ("Chrysler", "TOWN", 2008, 2010, 4000, "4.0 V6 (Chrysler, Routan)", "T&C 2008-10 4.0 OHV = 251hp [TC08][ROW_FIX]", 251),
    ("Chrysler", "TOWN", 2011, 2016, None, "3.6 Pentastar", "T&C 2011-16 (incl. 2015 L/S/T trims) = Pentastar 283hp [MOPARHIST]", 283),
    ("Chrysler", "VOYAGER", 2020, 2025, None, "3.6 Pentastar", "Voyager 2020+ = Pentastar 287hp [MOPARHIST]", 287),
    ("Chrysler", "VOYAGER", 2000, 2003, 2400, "EDZ", "Voyager 2.4 = EDZ 150hp [MOPARVOCAB]", 150),
    ("Chrysler", "VOYAGER", 2000, 2000, 3000, "6G72(SOHC24V)", "Voyager 3.0 2000 = 6G72 150hp [MOPARHIST]", 150),
    ("Chrysler", "VOYAGER", 2000, 2003, 3300, "EGA", "Voyager 3.3 = EGA 180hp [MOPARVOCAB]", 180),
    # --- Dodge ---
    ("Dodge", "AVENGER", 2008, 2011, 2400, "ED3", "Avenger 2.4 = World GEMA 173hp [SEBRING07-family][MOPARVOCAB]", 173),
    ("Dodge", "AVENGER", 2008, 2010, 2700, "EER", "Avenger 2.7 = 189hp [SEBRING07-family]", 189),
    ("Dodge", "AVENGER", 2008, 2010, 3500, "EGF", "Avenger 3.5 = 235hp [SEBRING07-family][MOPARVOCAB]", 235),
    ("Dodge", "AVENGER", 2011, 2014, 3600, "3.6 Pentastar", "Avenger 3.6 (VING) = Pentastar 283hp [MOPARVOCAB]", 283),
    ("Dodge", "CAB", 2006, 2008, None, "EZC", "Ram Chassis Cab gas = 5.7 HEMI only 2006-08 = EZC 345hp [MOPARHIST][MOPARVOCAB]", 345),
    ("Dodge", "CAB", 2010, 2010, None, "EZH", "Ram Chassis Cab 2010 gas = 5.7 VCT 390hp [MOPARHIST][MOPARVOCAB]", 390),
    ("Dodge", "CAB", 2005, 2005, 5900, "ETH", "Chassis Cab 5900cc 2005 = 5.9 Cummins CR HO 325hp (fuel col wrong; 5.9 gas ended 2003) [CUMMINS][MOPARHIST]", 325),
    ("Dodge", "CALIBER", 2008, 2009, 1800, "1.8 World Engine (GEMA)", "Caliber 1.8 = World GEMA 148hp [NEW][MOPARHIST]", 148),
    ("Dodge", "CALIBER", 2008, 2010, 2000, "ECN", "Caliber 2.0 = World GEMA 158hp (DB ECN row) [MOPARVOCAB]", 158),
    ("Dodge", "CALIBER", 2008, 2010, 2400, "ED3", "Caliber 2.4 = World GEMA 172hp (DB ED3 = Caliber-linked) [MOPARVOCAB]", 172),
    ("Dodge", "CARAVAN", 2000, 2007, 2400, "EDZ", "Caravan 2.4 = EDZ 150hp [MOPARVOCAB]", 150),
    ("Dodge", "CARAVAN", 2000, 2000, 3000, "6G72(SOHC24V)", "Caravan 3.0 2000 = 6G72 150hp [MOPARHIST]", 150),
    ("Dodge", "CARAVAN", 2000, 2007, 3300, "EGA", "Caravan 3.3 = EGA 180hp [MOPARVOCAB]", 180),
    ("Dodge", "CHALLENGER", 2008, 2008, None, "3.5 V6 (LX)", "Challenger 2008 SE = 3.5 V6 250hp (DB LX row) [MOPARHIST][MOPARVOCAB]", 250),
    ("Dodge", "DAKOTA", 2004, 2004, 3700, "EKG", "Dakota 3.7 PowerTech 210hp (3.7 from 2005 MY; lemon year off by one) [MOPARHIST][MOPARVOCAB]", 210),
    ("Dodge", "DART", 2013, 2016, 1400, "1.4 MultiAir Turbo (Dart/Renegade)", "Dart 1.4 MultiAir Turbo (VINH) = 160hp [DART][NEW]", 160),
    ("Dodge", "DART", 2013, 2016, 2000, "2.0 TigerShark (Dart)", "Dart 2.0 TigerShark (VINA) = 160hp [DART][NEW]", 160),
    ("Dodge", "DART", 2013, 2014, 2400, "ED8", "Dart 2.4 Tigershark MultiAir2 (VINB) = 184hp [DART][ROW_FIX ED8]", 184),
    ("Dodge", "GRAND", 2000, 2000, 3000, "6G72(SOHC24V)", "Grand Caravan 3.0 2000 = 6G72 150hp [MOPARHIST]", 150),
    ("Dodge", "GRAND", 2000, 2000, 3300, "EGA", "Grand Caravan 3.3 2000 = EGA 180hp [MOPARVOCAB]", 180),
    ("Dodge", "GRAND", 2008, 2010, 3300, "EGA", "Grand Caravan 3.3 2008-10 = 175hp [TC08]", 175),
    ("Dodge", "GRAND", 2000, 2000, 3800, "EGH", "Grand Caravan 3.8 2000 = 215hp [MOPARHIST]", 215),
    ("Dodge", "GRAND", 2008, 2010, 3800, "EGH", "Grand Caravan 3.8 2008-10 = 197hp [TC08]", 197),
    ("Dodge", "GRAND", 2008, 2010, 4000, "4.0 V6 (Chrysler, Routan)", "Grand Caravan 4.0 2008-10 OHV = 251hp [TC08][ROW_FIX]", 251),
    ("Dodge", "GRAND", 2011, 2020, None, "3.6 Pentastar", "Grand Caravan 2011-20 (incl. 2015 trim + C/V) = Pentastar 283hp [MOPARHIST]", 283),
    ("Dodge", "C/V", 2012, 2015, None, "3.6 Pentastar", "Grand Caravan C/V cargo (incl. 2015 CV Tradesman) = Pentastar 283hp sole engine [MOPARHIST]", 283),
    ("Dodge", "HORNET", 2023, 2025, None, "2.0 Turbo GME", "Hornet 2023 = GT 2.0 Hurricane4 only (R/T PHEV = 2024 MY), 268hp [HORNET][MOPARVOCAB]", 268),
    ("Dodge", "HORNET", 2024, 2025, 2000, "2.0 Turbo GME", "Hornet GT 2.0 Hurricane4 = 268hp (DB GME row 268) [HORNET][MOPARVOCAB]", 268),
    ("Dodge", "HORNET", 2024, 2025, 1300, "1.3 GSE PHEV (Hornet R/T)", "Hornet R/T PHEV = 1.3 GSE + 90kW, 288hp net (fuel col -> Hybrid) [HORNET][NEW]", 288),
    ("Dodge", "INTREPID", 2001, 2004, 2700, "EER", "Intrepid 2.7 = EER 200hp [MOPARVOCAB]", 200),
    ("Dodge", "INTREPID", 2001, 2001, 3200, "3.2 V6 (LH)", "Intrepid 3.2 (1998-2001) = LH 3.2 220hp [LH32][NEW]", 220),
    ("Dodge", "INTREPID", 2001, 2004, 3500, "EGG", "Intrepid 3.5 = EGG 250hp (R/T HO) [MOPARHIST]", 250),
    ("Dodge", "JOURNEY", 2020, 2020, None, "ED3", "Journey 2019-20 US = 2.4 only, 173hp [MOPARHIST]", 173),
    ("Dodge", "JOURNEY", 2012, 2019, 2400, "ED3", "Journey 2.4 (VINB) = World GEMA 173hp [MOPARVOCAB]", 173),
    ("Dodge", "JOURNEY", 2012, 2019, 3600, "3.6 Pentastar", "Journey 3.6 (VING) = Pentastar 283hp [MOPARVOCAB]", 283),
    ("Dodge", "NEON", 2000, 2005, None, "2.0 SOHC 16v (Neon)", "Neon 2000-05 = 2.0 SOHC 132hp sole engine [NEON][NEW]", 132),
    ("Dodge", "NITRO", 2007, 2011, 4000, "EGS", "Nitro R/T 4.0 SOHC = 260hp (DB EGS 3952cc 260) [MOPARHIST][ROW_FIX EGS]", 260),
    ("Dodge", "PICKUP", 2005, 2007, 5900, "ETH", "Ram 5900cc 2005-07 = 5.9 Cummins CR HO 325hp (fuel col wrong; 5.9 gas ended 2003) [CUMMINS][MOPARHIST]", 325),
    ("Dodge", "SRT 4", 2003, 2003, None, "2.4 16v Turbo SRT-4", "Neon SRT-4 2003 = 2.4T 215hp [NEON][ROW_FIX]", 215),
    ("Dodge", "SRT 4", 2004, 2005, None, "2.4 16v Turbo SRT-4", "Neon SRT-4 2004-05 = 2.4T 230hp [NEON][ROW_FIX]", 230),
    ("Dodge", "STRATUS", 2003, 2006, 2400, "EDZ", "Stratus 2.4 = EDZ 150hp [MOPARVOCAB]", 150),
    ("Dodge", "STRATUS", 2003, 2006, 2700, "EER", "Stratus 2.7 = EER 200hp [MOPARVOCAB]", 200),
    ("Dodge", "STRATUS", 2003, 2005, 3000, "6G72(SOHC24V)", "Stratus coupe R/T 3.0 = 6G72 200hp [MOPARHIST][MOPARVOCAB]", 200),
    ("Dodge", "VIPER", 2000, 2002, None, "8.0 V10 (Viper Gen II)", "Viper SR II 2000-02 = 8.0 V10 450hp [VIPERSRII][NEW]", 450),
    ("Dodge", "VIPER", 2003, 2006, None, "8.3 V10 SRT", "Viper ZB I 2003-06 = 8.3 V10 500hp (DB row) [MOPARVOCAB]", 500),
    ("Dodge", "VIPER", 2008, 2010, None, "8.4 V10 SRT10", "Viper ZB II 2008-10 = 8.4 V10 600hp (DB row 599 Euro) [MOPARVOCAB]", 600),
    ("Dodge", "VIPER", 2013, 2015, None, "8.4 V10 (Viper Gen V)", "Viper Gen V 2013-15 (incl. 2015 Base/GT/GTS) = 8.4 640hp [VIPERGENV][NEW]", 640),
    ("Dodge", "VIPER", 2016, 2017, None, "8.4 V10 (Viper Gen V)", "Viper Gen V 2016-17 = 8.4 645hp [VIPERGENV][NEW]", 645),
    # --- Jeep ---
    ("Jeep", "CHEROKEE", 2001, 2001, None, "4.0 I6 (AMC)", "Cherokee XJ 2001 = 4.0 I6 190hp sole engine [MOPARHIST][MOPARVOCAB]", 190),
    ("Jeep", "CHEROKEE", 2018, 2022, 3200, "3.2 Pentastar", "Cherokee KL 3.2 (VINX) = Pentastar 271hp [MOPARVOCAB]", 271),
    ("Jeep", "COMPASS", 2018, 2022, None, "ED8", "Compass MP 2018-22 = 2.4 Tigershark 180hp sole engine [MOPARHIST][ROW_FIX ED8]", 180),
    ("Jeep", "COMPASS", 2023, 2025, None, "2.0 Turbo GME", "Compass 2023-25 = 2.0T GME 200hp standard (2.4 dropped) [COMPASS25]", 200),
    ("Jeep", "COMPASS", 2013, 2017, 2000, "ECN", "Compass 2.0 (VINA) = World GEMA 158hp [MOPARVOCAB]", 158),
    ("Jeep", "COMPASS", 2013, 2016, 2400, "ED3", "Compass 2.4 (VINB) = World GEMA 172hp [MOPARVOCAB]", 172),
    ("Jeep", "PATRIOT", 2013, 2017, 2000, "ECN", "Patriot 2.0 (VINA) = World GEMA 158hp [MOPARVOCAB]", 158),
    ("Jeep", "PATRIOT", 2013, 2017, 2400, "ED3", "Patriot 2.4 (VINB) = World GEMA 172hp [MOPARVOCAB]", 172),
    ("Jeep", "RENEGADE", 2022, 2023, None, "1.3 GSE Turbo (Renegade)", "Renegade 2021+ US = 1.3T only 177hp (2.4 dropped 2021) [MOPARHIST][NEW]", 177),
    ("Jeep", "RENEGADE", 2019, 2021, 1300, "1.3 GSE Turbo (Renegade)", "Renegade 1.3 GSE (VIN1) = 177hp [MOPARHIST][NEW]", 177),
    ("Jeep", "RENEGADE", 2015, 2018, 1400, "1.4 MultiAir Turbo (Dart/Renegade)", "Renegade 1.4 MultiAir Turbo (VINH/W) = 160hp [DART-family][NEW]", 160),
    ("Jeep", "RENEGADE", 2015, 2021, 2400, "ED8", "Renegade 2.4 (VINB/T) = Tigershark 180hp [MOPARHIST][ROW_FIX ED8]", 180),
    ("Jeep", "WAGONEER", 2022, 2022, None, "5.7 HEMI V8 eTorque (Wagoneer)", "Wagoneer 2022 = 5.7 eTorque 392hp only [GWWIKI][NEW]", 392),
    ("Jeep", "WAGONEER", 2024, 2025, None, "3.0 Hurricane I6", "Wagoneer 2024-25 = Hurricane SO only (V8 dropped), 420hp [V8DROP][GWWIKI]", 420),
    ("Jeep", "WAGONEER", 2023, 2025, 3000, "3.0 Hurricane I6", "Wagoneer 3.0 (VINP) = Hurricane SO 420hp (SO added 2023) [GWWIKI][V8DROP][VINP]", 420),
    ("Jeep", "WAGONEER", 2023, 2023, 5700, "5.7 HEMI V8 eTorque (Wagoneer)", "Wagoneer 5.7 (VINT) = eTorque 392hp [GWWIKI][VINP-family][NEW]", 392),
    ("Jeep", "GRAND", 2022, 2024, 3000, "3.0 Hurricane I6 H.O. (Grand Wagoneer)", "Grand Wagoneer 3.0 (VINP) = Hurricane H.O. 510hp (2022 row = early GW L) [GWWIKI][VINP][NEW]", 510),
    ("Jeep", "GRAND", 2025, 2025, 3000, "3.0 Hurricane I6 H.O. (Grand Wagoneer)", "Grand Wagoneer 2025 Hurricane H.O. = 540hp [GWWIKI][NEW]", 540),
    ("Jeep", "GRAND", 2022, 2023, 6400, "ESG", "Grand Wagoneer 6.4 (VINJ) = HEMI 471hp (DB ESG row) [GWWIKI][MOPARVOCAB]", 471),
]

SKIP_REASONS = {  # explicit skip documentation for known-ambiguous groups (printed in dry-run)
    ("Chrysler", "CIRRUS"): "2000 Cirrus: 2.0/2.4/2.5 all offered - cannot resolve bare row",
    ("Chrysler", "CONCORDE"): "2000-01 bare: 2.7/3.2/3.5 all offered",
    ("Chrysler", "PACIFICA"): "2008 3800cc: 2008 Pacifica was 4.0-only (3.8 impossible)",
    ("Chrysler", "SEBRING"): "2000/2002/2003 bare: 2.4/2.7/3.0 (sedan/conv/coupe) all offered",
    ("Chrysler", "TOWN"): "2000-07 bare: 3.3 vs 3.8 both offered (cc rows cover 2008-10)",
    ("Dodge", "AVENGER"): "2000 bare: 2.0/2.5 coupe both offered",
    ("Dodge", "CAB"): "2004 5900cc: Cummins mid-year split (SO 305 early / HO 325 from 2004.5)",
    ("Dodge", "CALIBER"): "2007/2011/2012 bare: 1.8/2.0/2.4 all offered",
    ("Dodge", "GRAND"): "2001-07 bare: 3.3 vs 3.8 both offered (cc rows cover 2008-10)",
    ("Dodge", "INTREPID"): "2000 bare: 2.7/3.2/3.5 all offered",
    ("Dodge", "JOURNEY"): "2009-11 bare: 2.4 vs 3.5 both offered (2019-20 = 2.4-only, mapped)",
    ("Dodge", "PICKUP"): "2004 5900cc: Cummins mid-year split (305/325); 2008-09 5900cc: 5.9 ended 2007.5 (impossible - 6.7 would be 6700cc)",
    ("Dodge", "STRATUS"): "2000-03 bare: 2.0/2.4/2.5 (coupe/sedan) all offered",
    ("Jeep", "COMPASS"): "2007-16 bare: 2.0 vs 2.4 both offered (2018+ 2.4-only, 2023+ 2.0T-only, mapped)",
    ("Jeep", "PATRIOT"): "2007-16 bare: 2.0 vs 2.4 both offered",
    ("Jeep", "WAGONEER"): "2023 bare: 5.7 eTorque vs Hurricane SO both offered (V8 dropped for 2024)",
    ("Jeep", "GRAND CHEROKEE"): "2022/2025 bare: 3.6/5.7/4xe (2022) or 3.6/4xe (2025) - ambiguous",
}

def parse_code(code):
    m = re.match(r"^LEMON_(CHRYSLER|DODGE|JEEP)_(.+)$", code)
    if not m: return None
    brand, rest = m.group(1), m.group(2)
    toks = rest.split("_")
    yi = next((i for i, t in enumerate(toks) if re.fullmatch(r"(19|20)\d\d", t)), None)
    if yi is None: return None
    year = int(toks[yi])
    pre, post = toks[:yi], toks[yi+1:]
    cc = vin = None
    model_toks = []
    for t in pre:
        if re.fullmatch(r"\d+CC", t): cc = int(t[:-2])
        elif re.fullmatch(r"VIN[A-Z0-9]", t): vin = t
        else: model_toks.append(t)
    return brand, " ".join(model_toks), year, cc, vin, "_".join(post)

def decide(brand, model, year, cc, vin, code, fuel):
    mu, cu = model.upper(), code.upper()
    # intercepts first (fuel column / trim slugs)
    if mu == "SPRINTER":
        if year <= 2006:
            ff = "Diesel" if fuel != "Diesel" else None
            return ("OM612DE27LA", "Sprinter 2003-06 = 2.7 I5 OM612 turbodiesel 154hp (only engine; 2003-04 fuel col wrong) [SPRINTER][MOPARVOCAB]", ff, 154)
        if fuel == "Petrol":
            return ("M272E35", "Sprinter 2007-09 3.5 V6 (VQ? no - M272) petrol 254hp [SPRINTER][MOPARVOCAB]", None, 254)
        return (None, "Sprinter 2007+ diesel 3.0 OM642 vs petrol 3.5 - fuel col neither/unknown", None, None)
    if mu == "PACIFICA" and fuel == "Hybrid" and 2017 <= year <= 2024:
        return ("3.6 V6 Pentastar PHEV (Pacifica Hybrid)", "Pacifica Hybrid (fuel col Hybrid) = 3.6 Atkinson + eFlite EVT, 260hp total [PACHPHEV][NEW]", None, 260)
    if cu.endswith("COMPASSLIMIT"):
        return ("ED3", "Compass Limited 2015 = 2.4 std (2.0 was base FWD only) [MOPARHIST][MOPARVOCAB]", None, 172)
    if cu.endswith("PATRIOTLIMIT"):
        return ("ED3", "Patriot Limited 2015 = 2.4 std [MOPARHIST][MOPARVOCAB]", None, 172)
    cands = [r for r in R if r[0] == brand and r[1] == mu and r[2] <= year <= r[3] and r[4] == cc]
    if not cands:
        return (None, SKIP_REASONS.get((brand, mu), f"no rule for {brand} {model} {year} cc={cc}"), None, None)
    r = cands[0]
    fuel_fix = FUEL_FIX_BY_TARGET.get(r[5])
    if fuel_fix and fuel == fuel_fix: fuel_fix = None
    return (r[5], r[6], fuel_fix, r[7])

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == 3071, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 3071 (workspace rewind?)"
    base_eng = cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0]
    assert base_eng == 8620, f"BASELINE MISMATCH: engines={base_eng}, expected 8620"
    rows = cur.execute("""SELECT id, car_brand, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand IN ('Dodge','Chrysler','Jeep') AND engine_code LIKE 'LEMON%' ORDER BY car_brand, car_model, car_year, engine_code""").fetchall()
    decisions, skips = [], []
    for vid, brand, model, year, code, fuel in rows:
        p = parse_code(code)
        assert p, f"unparseable code: {code}"
        pb, pm, py, cc, vin, post = p
        assert pb.upper() == brand.upper(), f"brand parse mismatch {code} vs {brand}"
        tgt, note, fuel_fix, pfix = decide(brand, pm, year, cc, vin, code, fuel)
        if tgt is None: skips.append((vid, brand, model, year, code, note)); continue
        decisions.append((vid, brand, model, year, code, tgt, note, fuel_fix, pfix))
    print(f"Mopar LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print(f"  SKIP: {s[1]} {s[2]} {s[3]} [{s[4]}] - {s[5]}")
    print("\ntop targets:")
    for t, c in Counter(d[5] for d in decisions).most_common(30): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter((d[5], d[7]) for d in decisions if d[7]))
    missing = set(d[5] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"
    # batch-17 standing rule: existing target rows must match expected fuel/displacement
    for tgt, (efuel, ecc) in IDENTITY.items():
        # queued cc corrections (pre-known junk values, e.g. OM612 2184->2685) bypass the cc check
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
    # pre-existing Viper 2013-17 links sitting on the Gen IV 8.4 V10 SRT10 row -> will relink to Gen V
    stale_viper = cur.execute("""SELECT id, car_model, car_year FROM vehicle_variants
        WHERE engine_code='8.4 V10 SRT10' AND car_model LIKE '%iper%' AND car_year>=2013""").fetchall()
    print(f"pre-existing Viper 2013+ variants on '8.4 V10 SRT10' (relink to Gen V): {len(stale_viper)}")

    if not apply:
        with open("database_enriched/csv_exports/36_lemon_batch19_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
            for d in decisions: w.writerow([d[0],d[1],d[2],d[3],d[4],d[5],d[7] or "",d[8] if d[8] else "",d[6] or ""])
            for s in skips: w.writerow([s[0],s[1],s[2],s[3],s[4],"","","SKIP",s[5]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step28_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP28_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
            print(f"  created {code}")
    # 3.6 Pentastar NULL power -> mode of linked variant powers (fallback 283)
    mode = cur.execute("""SELECT engine_power_hp, COUNT(*) c FROM vehicle_variants
        WHERE engine_code='3.6 Pentastar' AND engine_power_hp IS NOT NULL GROUP BY 1 ORDER BY c DESC LIMIT 1""").fetchone()
    penta_hp = mode[0] if mode and mode[0] else 283
    print(f"  3.6 Pentastar power fill: {penta_hp} (mode of linked variants)")
    ROW_FIXES["3.6 Pentastar"] = {"power_hp": penta_hp}
    for code, fixes in ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  row-fix {code}")

    # relink stale Gen V Viper variants
    cur.execute("""UPDATE vehicle_variants SET engine_code='8.4 V10 (Viper Gen V)',
        engine_power_hp=CASE WHEN car_year>=2016 THEN 645 ELSE 640 END
        WHERE engine_code='8.4 V10 SRT10' AND car_model LIKE '%iper%' AND car_year>=2013""")
    print(f"  relinked {cur.rowcount} stale Gen V Viper variants")

    lemon_retired = defaultdict(list)
    for vid, brand, model, year, old, new, note, fuel_fix, pfix in decisions:
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
    # sweep: variants newly on ED8/3.6 Pentastar with NULL power take engine power
    for t in ("ED8", "3.6 Pentastar"):
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=
            (SELECT power_hp FROM engines WHERE engine_code=?)
            WHERE engine_code=? AND engine_power_hp IS NULL""", (t, t))

    with open("database_enriched/csv_exports/36_lemon_batch19_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
        for d in decisions: w.writerow([d[0],d[1],d[2],d[3],d[4],d[5],d[7] or "",d[8] if d[8] else "",d[6] or ""])
    con.commit()

    print("\n--- verify ---")
    for b in ("Dodge", "Chrysler", "Jeep"):
        print(f"LEMON {b} remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand=? AND engine_code LIKE 'LEMON%'", (b,)).fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'", ).fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
