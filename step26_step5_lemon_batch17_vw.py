"""Step 26 (user-plan Step 5, batch 17): replace LEMON_VOLKSWAGEN codes with real OEM engine codes.
237 rows, 19 models, MY2005-2025. Signals: cc + VIN engine letter + trim slugs (GOLFR*=Golf R,
JETTATDI*) + fuel column (12 rows Diesel/Hybrid, 8 more mislabeled Petrol rows need fuel fixes).
DB VW vocabulary reused (BPY/CCTA/CBFA 2.0T 200hp, AWP/AWV 1.8T, AVH 2.0 8v, BGP 2.5 I5, BEW/BRM
1.9 TDI, BHW 2.0 TDI PD, CVCA EA288 150, CZEA 1.4T, CXBA/CXBB 1.8T 170 NULL rows -> filled,
BKL/BUB/BFH VR6, BLV/CNNA 3.6 FSI, AXQ 4.2 V8). New: CYFB Golf R, DGUA Tiguan Budack, CGRA/CDVC
3.6 FSI, 5.0 V10 TDI, 3.0 TDI Touareg, 6.0 W12 Phaeton, 3.0 TSI Hybrid, EA888 Atlas/Arteon/174hp
rows, 1.5 TSI evo, e-Golf EV, 1.4 TSI Hybrid, Routan Chrysler 3.8/4.0 rebadge rows.
Skips: Passat 2005 2800cc (no 2.8 in B5.5 2005/B6-gap year), Touareg 2008 5000cc (V10 TDI cancelled
after MY2007 US), Golf 2025 bare (GTI 241 vs Golf R 328 unknown)."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "GTSCODES": "https://tunedbygts.com/ea888-gen3 (US Gen3 codes: CXCA 2015-16 GTI 210hp, CYFB 2015-18 Golf R 292hp, DGUA 2018+ Tiguan 184hp Budack)",
    "VR6GUIDE": "https://www.enginefinder.co.za/blog/volkswagen-vr6-engine-guide/ (24v 3.2: BFH R32 Mk4, BUB R32 Mk5 250hp, BKL Touareg 3.2; 3.6 EA390 family)",
    "MOTORREVIEWER36": "https://www.motorreviewer.com/engine.php?engine_id=121 (EA390 3.6 FSI: CGRA Touareg 280hp, CDVC Atlas/Teramont, BLV/BWS Passat)",
    "VWFORUM36": "https://volkswagenforum.com/forum/volkswagen-passat-cc-21/vr6-engine-37921/ (CNNA = Passat CC/CC 3.6 FSI 280hp NAR 2008-2016)",
    "VWMEDIA15": "https://media.vw.com/releases/344 (2015 Beetle: EA888 Gen3 1.8T 170hp; EA288 TDI 150hp replacing 140hp EA189)",
    "VWVORTEX288": "https://vwvortex.com/news/volkswagen-news/new-ea288-volkswagen-tdi-engine-to-debut-in-2015-golf-jetta-passat-and-beetle (all 2015 TDI = EA288 150hp)",
    "AUTOBLOGV10": "https://www.autoblog.com/features/touareg-v10-tdi-on-sale-now-in-u-s (2006 Touareg V10 TDI 310hp US) + green.fandom.com/wiki/Volkswagen_Touareg (V10 US 2006-07 then cancelled; 4.2 V8 310PS)",
    "JDPOWER19": "https://www.jdpower.com/cars/history/volkswagen/golf (2019 Golf drops 1.8T 170hp for 1.4T 147hp; GTI 220->228hp)",
    "VWCEO21": "https://media.vw.com/releases/1461 (MY2021 last US base Golf; base engine 1.8T 170 replaced by 1.4T in 2019)",
    "WIKIGOLF": "https://en.wikipedia.org/wiki/Volkswagen_Golf + /Volkswagen_Golf_Mk4 (Mk4.5 Brazilian Golf TDI PD sold in Canada as full 2006 MY; NA Mk5 Rabbit 2.5 150hp 2006-07)",
    "USNEWS21ATLAS": "https://cars.usnews.com/cars-trucks/volkswagen/atlas/2021/performance (2021 Atlas 2.0T 235hp / 3.6 276hp) + https://www.caranddriver.com/volkswagen/atlas-2024 (2024: 269hp four only, V6 dropped)",
    "USNEWSTAOS": "https://cars.usnews.com/cars-trucks/volkswagen/taos/2022/performance + https://maynardsgarage.com/2022/05/03/vw-taos-1-5t-sel-review/ (Taos = 1.5T EA211 Miller-cycle 158hp all trims)",
    "RWC": "https://www.rwcmotorsport.com/motors/tdi-comparison.php (TDI generations: ALH VP37, BEW/BRM Pumpe-Duse 100hp, CJAA EA189 CR 140hp, EA288 150hp CRUA-era)",
    "CARBUZZ": "https://carbuzz.com/important-final-golf-is-bargain-today/ (US Golf 2015-2018 1.8T 170hp; 2015 TDI EA288 150hp; 2019 1.4T 147hp)",
    "ROUTAN": "VW Routan (2009-2012) = Chrysler RT-platform minivan rebadge: 3.8 V6 EGJ 197hp / 4.0 V6 EGH 251hp (Chrysler powertrains)",
    "STRP": "https://strperformance.com/en/blog/details-conseils-technique/ea113-vs-ea888-gen1-to-gen4-complete-comparison-of-20-tfsi-vag-engines-codes-reliability-tuning-maintenance (CHHA/CHHB 220hp GTI Gen3; CXCA/CXCB US GTI codes)",
    "DBLINKS": "DB VW vocabulary rows reused: BPY/CCTA/CBFA (2.0T 200hp), AWP (1.8T 180), AWV (1.8T 150 NB), AWM (B5.5 1.8T), AVH (2.0 8v 115), BGP (2.5 I5), BEW/BRM (1.9 TDI PD), BHW (2.0 TDI PD), CVCA (EA288 150), CZEA (1.4T), CXBA/CXBB (1.8T 170 NULL rows), BKL/BUB (3.2 VR6), BLV/CNNA (3.6 FSI), AXQ (4.2 V8)",
}

NEW_ENGINES = {
    "CYFB": ("2.0 TSI EA888 Gen3 (US Golf R 2015-18, 292hp IS38)", "Petrol", 1984, 292, 4),
    "DGUA": ("2.0 TSI EA888 Gen3B Budack (Tiguan 2018+, 184hp)", "Petrol", 1984, 184, 4),
    "2.0 TSI EA888 (Atlas 2.0T)": ("2.0 TSI EA888 Gen3/evo4 (Atlas 2.0T, 235hp; 269hp 2024+)", "Petrol", 1984, 235, 4),
    "2.0 TSI EA888 Gen3 (Arteon)": ("2.0 TSI EA888 Gen3 (Arteon, 268hp)", "Petrol", 1984, 268, 4),
    "2.0 TSI EA888 low tune (174hp)": ("2.0 TSI EA888 Gen3 low tune (Beetle 2018-19 / Passat GT 2020-22, 174hp)", "Petrol", 1984, 174, 4),
    "1.5 TSI evo (Taos/Jetta)": ("1.5 TSI EA211 evo Miller (Taos 2022+ / Jetta 2022+, 158hp)", "Petrol", 1498, 158, 4),
    "CGRA": ("3.6 VR6 FSI (Touareg 3.6, 276-280hp US)", "Petrol", 3597, 280, 6),
    "CDVC": ("3.6 VR6 FSI (Atlas 3.6, 276hp US)", "Petrol", 3597, 276, 6),
    "5.0 V10 TDI (Touareg)": ("5.0 V10 TwinTurbo TDI (Touareg 2006-07 US, 310hp)", "Diesel", 4921, 310, 10),
    "3.0 V6 TDI (Touareg)": ("3.0 V6 TDI (Touareg 2009 221hp / 2013-16 240hp)", "Diesel", 2967, 240, 6),
    "6.0 W12 (Phaeton)": ("6.0 W12 (Phaeton, 420hp US)", "Petrol", 5998, 420, 12),
    "3.0 TSI Hybrid (Touareg)": ("3.0 V6 TSI Supercharged + electric (Touareg Hybrid, 380hp system)", "Hybrid", 2995, 380, 6),
    "e-Golf Electric": ("Electric motor (e-Golf, 134hp US)", "Electric", None, 134, None),
    "1.4 TSI Hybrid (Jetta)": ("1.4 TSI EA211 + electric (Jetta Hybrid, 170hp system)", "Hybrid", 1395, 170, 4),
    "2.8 VR6 24v (Mk4 GTI)": ("2.8 VR6 24v (Mk4 GTI/Jetta GLX 200hp US)", "Petrol", 2792, 200, 6),
    "3.8 V6 (Chrysler, Routan)": ("3.8 V6 OHV (Chrysler RT platform: Routan/T&C 2009-10, 197hp)", "Petrol", 3778, 197, 6),
    "4.0 V6 (Chrysler, Routan)": ("4.0 V6 OHV (Chrysler RT platform: Routan/T&C, 251hp)", "Petrol", 3952, 251, 6),
}

ROW_FIXES = {
    "CXBA": {"engine_type": "1.8 TSI EA888 Gen3 (US Golf/Jetta/Beetle/Passat 1.8T, 170hp)", "displacement_cc": 1798, "power_hp": 170},
    "CXBB": {"engine_type": "1.8 TSI EA888 Gen3 (US Golf/Jetta/Beetle/Passat 1.8T, 170hp)", "displacement_cc": 1798, "power_hp": 170},
    "BUB": {"engine_type": "3.2 VR6 24v (R32 Mk5 2008 / Eos 3.2, 250hp US)", "displacement_cc": 3189, "power_hp": 250},
    "BKL": {"engine_type": "3.2 VR6 24v (Touareg 3.2, 220hp US)", "displacement_cc": 3189, "power_hp": 220},
    "BGP": {"engine_type": "2.5 I5 (Jetta/Rabbit/Golf/Beetle 2.5, 150hp US)", "power_hp": 150},
    "AWM": {"engine_type": "1.8T 20v (Passat B5.5, 170hp US)", "power_hp": 170},
    "AWP": {"engine_type": "1.8T 20v (Mk4 GTI/GLI 1.8T, 180hp US)", "power_hp": 180},
    "AWV": {"engine_type": "1.8T 20v (New Beetle 1.8T, 150hp US)", "power_hp": 150},
    "AVH": {"engine_type": "2.0 8v (Mk4 Golf/Jetta/New Beetle, 115hp US)", "power_hp": 115},
    "BEW": {"engine_type": "1.9 TDI PD (Mk4 Golf/Jetta/New Beetle 2004-06, 100hp US)", "power_hp": 100},
    "BRM": {"engine_type": "1.9 TDI PD (Jetta Mk5 2005-06 / Golf Mk4.5 Canada 2006, 100hp US)", "power_hp": 100},
    "AXQ": {"engine_type": "4.2 V8 32v (Touareg/Cayenne, 306-310hp)", "power_hp": 306},
    "BLV": {"engine_type": "3.6 VR6 FSI (Passat B6 2006-08, 280hp US)", "power_hp": 280},
    "CNNA": {"engine_type": "3.6 VR6 FSI (CC 2009-17 / Passat NMS 3.6, 280hp)"},
    "CXCA": {"engine_type": "2.0 TSI EA888 Gen3 (US GTI 2015-16, 210hp)", "power_hp": 210},
    "CXCB": {"engine_type": "2.0 TSI EA888 Gen3 (US GTI 2017-21, 220hp)", "power_hp": 220},
    "CXDA": {"engine_type": "2.0 TSI EA888 Gen3/3B (GTI Mk8 241hp / GLI 2019+ 228hp)", "power_hp": 228},
    "CVCA": {"engine_type": "2.0 TDI EA288 CR (2015+ Golf/Jetta/Passat/Beetle TDI, 150hp US)"},
    "CCTA": {"engine_type": "2.0 TSI EA888 Gen1/2 (GTI/GLI/Passat/CC/Tiguan 2.0T, 200hp US; GLI 210hp 2014+)"},
    "CZEA": {"engine_type": "1.4 TSI EA211 (US Jetta 1.4T 150hp 2017-18 / 147hp 2019+; Golf 2019+, 147-150hp)"},
    "BHW": {"engine_type": "2.0 TDI PD (Passat B5.5 2004-05, 134hp US)"},
}

FUEL_FIX_BY_TARGET = {"BEW": "Diesel", "BRM": "Diesel", "BHW": "Diesel", "CVCA": "Diesel",
                      "5.0 V10 TDI (Touareg)": "Diesel", "3.0 V6 TDI (Touareg)": "Diesel",
                      "e-Golf Electric": "Electric"}

# (MODEL-upper, y0, y1, cc, vins-or-None, target, evidence, pfix)  cc=None = bare; vins=set() = no-vin page
R = [
    ("ARTEON", 2019, 2023, None, None, "2.0 TSI EA888 Gen3 (Arteon)", "Arteon 2.0T 268hp only US [USNEWS21ATLAS-era]", 268),
    ("ATLAS", 2018, 2023, 2000, None, "2.0 TSI EA888 (Atlas 2.0T)", "Atlas 2.0T 235hp (CA-market 2018+; US 2021+; VIN P/C) [USNEWS21ATLAS]", 235),
    ("ATLAS", 2024, 2025, None, None, "2.0 TSI EA888 (Atlas 2.0T)", "Atlas 2024+: 2.0T 269hp evo4 only, V6 dropped [USNEWS21ATLAS]", 269),
    ("ATLAS", 2018, 2023, 3600, None, "CDVC", "Atlas 3.6 VR6 276hp (VIN E/R) [USNEWS21ATLAS][NEW CDVC]", 276),
    # Beetle A5
    ("BEETLE", 2015, 2017, 1800, None, "CXBA", "Beetle 1.8T EA888 Gen3 170hp (VIN 0/1) [VWMEDIA15][ROW_FIX CXBA]", 170),
    ("BEETLE", 2015, 2017, 2000, None, "CCTA", "Beetle 2.0T 200hp (VIN S/T; R-Line 210hp minority) [VWMEDIA15-era]", 200),
    ("BEETLE", 2018, 2019, None, None, "2.0 TSI EA888 low tune (174hp)", "Beetle 2018-19 S/SE/Final Ed 2.0T 174hp [NEW]", 174),
    ("CC", 2009, 2009, 2000, None, "CCTA", "CC (Passat CC) 2.0T 200hp TSI [DB CC-family]", 200),
    ("CC", 2009, 2009, 3600, None, "CNNA", "CC 3.6 VR6 FSI 280hp (launch year) [VWFORUM36]", 280),
    ("CC", 2015, 2017, 2000, None, "CCTA", "CC 2.0T 200hp (VIN N/P) [DB CC-family]", 200),
    ("CC", 2015, 2015, 3600, None, "CNNA", "CC 3.6 VR6 280hp final years [VWFORUM36]", 280),
    ("CC", 2016, 2016, None, None, "CCTA", "CC 2016 base = 2.0T 200hp majority [DB CC-family]", 200),
    ("EOS", 2007, 2008, 2000, None, "BPY", "Eos 2.0T FSI 200hp [DB BPY]", 200),
    ("EOS", 2007, 2008, 3200, None, "BUB", "Eos 3.2 VR6 24v 250hp [VR6GUIDE][ROW_FIX BUB]", 250),
    ("EOS", 2009, 2009, None, None, "CCTA", "Eos 2.0T TSI 200hp [DB CCTA]", 200),
    ("EOS", 2015, 2016, 2000, None, "CCTA", "Eos 2.0T 200hp final edition (VIN D/W) [DB CCTA]", 200),
    ("GLI", 2008, 2008, None, None, "BPY", "Jetta GLI Mk5 2.0T FSI 200hp [DB BPY]", 200),
    ("GLI", 2009, 2009, None, None, "CCTA", "Jetta GLI Mk5 2.0T TSI 200hp [DB CCTA]", 200),
    ("GTI", 2005, 2006, 1800, None, "AWP", "Mk4 GTI 1.8T 180hp (2006 row = Mk4 carryover reg.) [ROW_FIX AWP]", 180),
    ("GTI", 2005, 2005, 2800, None, "2.8 VR6 24v (Mk4 GTI)", "Mk4 GTI VR6 24v 200hp final year [NEW][VR6GUIDE]", 200),
    ("GTI", 2006, 2006, 2000, None, "BPY", "Mk5 GTI 2.0T FSI 200hp launch [DB BPY]", 200),
    ("GTI", 2007, 2008, None, None, "BPY", "Mk5 GTI 2.0T FSI 200hp [DB BPY]", 200),
    ("GTI", 2009, 2009, None, None, "CCTA", "Mk5 GTI 2.0T TSI 200hp [DB CCTA]", 200),
    ("GTI", 2015, 2016, 2000, None, "CXCA", "Mk7 GTI 2.0T 210hp US (VIN 4/T) [GTSCODES][ROW_FIX CXCA]", 210),
    ("GTI", 2017, 2021, None, None, "CXCB", "Mk7.5 GTI 220hp US [ROW_FIX CXCB]", 220),
    ("GTI", 2022, 2024, None, None, "CXDA", "Mk8 GTI 241hp US [ROW_FIX CXDA]", 241),
    # Golf
    ("GOLF", 2005, 2005, 1900, None, "BEW", "Mk4 Golf TDI 1.9 PD 100hp final US year (fuel label wrong -> Diesel) [RWC]", 100),
    ("GOLF", 2006, 2006, 1900, None, "BRM", "Golf Mk4.5 TDI PD 100hp (Canada full-2006 MY; fuel label wrong -> Diesel) [WIKIGOLF]", 100),
    ("GOLF", 2005, 2006, 2000, None, "AVH", "Mk4 Golf 2.0 8v 115hp [ROW_FIX AVH]", 115),
    ("GOLF", 2007, 2009, None, None, "BGP", "Rabbit-era Golf 2.5 I5 150hp [WIKIGOLF][ROW_FIX BGP]", 150),
    ("GOLF", 2015, 2015, 2000, None, "CVCA", "Mk7 Golf TDI EA288 150hp (fuel col already Diesel) [CARBUZZ][VWVORTEX288]", 150),
    ("GOLF", 2016, 2018, None, None, "CXBA", "Mk7 Golf 1.8T 170hp [CARBUZZ][ROW_FIX CXBA]", 170),
    ("GOLF", 2019, 2021, 1400, None, "CZEA", "Golf 1.4T 147hp (2019 adopted Jetta engine; VIN 5) [JDPOWER19][ROW_FIX CZEA]", 147),
    ("GOLF", 2019, 2021, None, None, "CZEA", "Golf 2019-21 base = 1.4T 147hp only (2021 = last US Golf) [JDPOWER19][VWCEO21]", 147),
    # Jetta
    ("JETTA", 2005, 2005, 1800, None, "AWP", "Mk4 Jetta GLI/GLS 1.8T 180hp [ROW_FIX AWP]", 180),
    ("JETTA", 2005, 2005, 1900, None, "BEW", "Mk4 Jetta TDI 1.9 PD 100hp (fuel label wrong -> Diesel) [RWC]", 100),
    ("JETTA", 2005, 2005, 2000, None, "AVH", "Mk4 Jetta 2.0 8v 115hp GL [ROW_FIX AVH]", 115),
    ("JETTA", 2005, 2009, 2500, None, "BGP", "Jetta 2.5 I5 150hp (Mk5 2005.5+) [ROW_FIX BGP]", 150),
    ("JETTA", 2006, 2006, 1900, None, "BRM", "Jetta Mk5 TDI 1.9 PD 100hp (fuel col already Diesel) [RWC]", 100),
    ("JETTA", 2006, 2008, 2000, None, "BPY", "Jetta GLI 2.0T FSI 200hp [DB BPY]", 200),
    ("JETTA", 2009, 2009, 2000, None, "CCTA", "Jetta GLI 2.0T TSI 200hp [DB CCTA]", 200),
    ("JETTA", 2015, 2016, 1400, None, "1.4 TSI Hybrid (Jetta)", "Jetta Hybrid 1.4T + e-motor 170hp system (fuel col Hybrid) [NEW]", 170),
    ("JETTA", 2015, 2016, 1800, None, "CXBA", "Jetta 1.8T EA888 Gen3 170hp (VIN 0/1) [VWMEDIA15-era][ROW_FIX CXBA]", 170),
    ("JETTA", 2015, 2015, None, None, "CVCA", "Jetta TDI 2015 = EA288 150hp (TDI slug trims; fuel col Diesel) [VWVORTEX288]", 150),
    ("JETTA", 2016, 2016, 2000, None, "CCTA", "Jetta GLI 2.0T 210hp (VIN T) [DB CCTA]", 210),
    ("JETTA", 2017, 2018, 1400, None, "CZEA", "Jetta 1.4T 150hp (VIN 6/B) [ROW_FIX CZEA]", 150),
    ("JETTA", 2017, 2017, 1800, None, "CXBA", "Jetta 1.8T 170hp [ROW_FIX CXBA]", 170),
    ("JETTA", 2017, 2017, 2000, None, "CCTA", "Jetta GLI 2.0T 210hp [DB CCTA]", 210),
    ("JETTA", 2019, 2020, 1400, None, "CZEA", "Jetta 1.4T 147hp Mk7 (VIN 5/B) [ROW_FIX CZEA]", 147),
    ("JETTA", 2019, 2025, 2000, None, "CXDA", "Jetta GLI Mk7 2.0T 228hp [ROW_FIX CXDA]", 228),
    ("JETTA", 2021, 2021, 1400, None, "CZEA", "Jetta 1.4T 147hp [ROW_FIX CZEA]", 147),
    ("JETTA", 2022, 2025, 1500, None, "1.5 TSI evo (Taos/Jetta)", "Jetta 1.5T 158hp (replaced 1.4T 2022) [NEW][USNEWSTAOS]", 158),
    # New Beetle (Mk4-based)
    ("NEW", 2005, 2005, 1800, None, "AWV", "New Beetle 1.8T 150hp [ROW_FIX AWV]", 150),
    ("NEW", 2005, 2005, 1900, None, "BEW", "New Beetle TDI 1.9 PD 100hp (fuel label wrong -> Diesel) [RWC]", 100),
    ("NEW", 2005, 2005, 2000, None, "AVH", "New Beetle 2.0 8v 115hp [ROW_FIX AVH]", 115),
    ("NEW", 2006, 2006, 1900, None, "BRM", "New Beetle TDI 1.9 PD 100hp (fuel col already Diesel) [RWC]", 100),
    ("NEW", 2006, 2009, 2500, None, "BGP", "New Beetle 2.5 I5 150hp [ROW_FIX BGP]", 150),
    ("NEW", 2007, 2009, None, None, "BGP", "New Beetle 2.5 I5 150hp only [ROW_FIX BGP]", 150),
    # Passat
    ("PASSAT", 2005, 2005, 1800, None, "AWM", "Passat B5.5 1.8T 170hp [ROW_FIX AWM]", 170),
    ("PASSAT", 2005, 2005, 2000, None, "BHW", "Passat B5.5 TDI 2.0 PD 134hp (fuel label wrong -> Diesel) [RWC][ROW_FIX BHW]", 134),
    ("PASSAT", 2006, 2007, 2000, None, "BPY", "Passat B6 2.0T FSI 200hp [DB BPY]", 200),
    ("PASSAT", 2008, 2008, 2000, None, "CCTA", "Passat B6 2.0T TSI 200hp [DB CCTA]", 200),
    ("PASSAT", 2006, 2008, 3600, None, "BLV", "Passat B6 3.6 VR6 FSI 280hp [MOTORREVIEWER36][ROW_FIX BLV]", 280),
    ("PASSAT", 2009, 2009, None, None, "CCTA", "Passat 2009 base 2.0T 200hp [DB CCTA]", 200),
    ("PASSAT", 2015, 2017, 1800, None, "CXBA", "Passat NMS 1.8T 170hp (VIN S/T) [ROW_FIX CXBA]", 170),
    ("PASSAT", 2015, 2015, 2000, None, "CVCA", "Passat NMS TDI EA288 150hp (fuel col Diesel) [VWVORTEX288]", 150),
    ("PASSAT", 2015, 2018, 3600, None, "CNNA", "Passat NMS 3.6 VR6 280hp (VIN M) [VWFORUM36]", 280),
    ("PASSAT", 2018, 2018, 2000, None, "2.0 TSI EA888 low tune (174hp)", "Passat GT 2.0T 174hp (VIN A) [NEW]", 174),
    ("PASSAT", 2018, 2018, None, None, "CXBA", "Passat 2018 base 1.8T 170hp [ROW_FIX CXBA]", 170),
    ("PASSAT", 2022, 2022, None, None, "2.0 TSI EA888 low tune (174hp)", "Passat 2020-22 2.0T 174hp only [NEW]", 174),
    ("PHAETON", 2005, 2006, 6000, None, "6.0 W12 (Phaeton)", "Phaeton 6.0 W12 420hp US [NEW]", 420),
    ("R32", 2008, 2008, None, None, "BUB", "Golf R32 Mk5 3.2 VR6 250hp [VR6GUIDE][ROW_FIX BUB]", 250),
    ("RABBIT", 2006, 2009, None, None, "BGP", "Rabbit Mk5 2.5 I5 150hp [WIKIGOLF][ROW_FIX BGP]", 150),
    ("ROUTAN", 2009, 2010, 3800, None, "3.8 V6 (Chrysler, Routan)", "Routan 3.8 V6 Chrysler 197hp (RT-platform rebadge) [ROUTAN][NEW]", 197),
    ("ROUTAN", 2009, 2010, 4000, None, "4.0 V6 (Chrysler, Routan)", "Routan 4.0 V6 Chrysler 251hp [ROUTAN][NEW]", 251),
    ("TAOS", 2022, 2025, None, None, "1.5 TSI evo (Taos/Jetta)", "Taos 1.5T 158hp all trims [USNEWSTAOS][NEW]", 158),
    ("TIGUAN", 2009, 2017, None, None, "CCTA", "Tiguan 2.0T 200hp EA888 (2009 launch - 2017) [DB CCTA]", 200),
    ("TIGUAN", 2018, 2024, None, None, "DGUA", "Tiguan MQB 2.0T 184hp Budack [GTSCODES][NEW DGUA]", 184),
    ("TOUAREG", 2005, 2006, 3200, None, "BKL", "Touareg 3.2 VR6 220hp [VR6GUIDE][ROW_FIX BKL]", 220),
    ("TOUAREG", 2006, 2009, 3600, None, "CGRA", "Touareg 3.6 VR6 FSI 276hp (2006.5+) [MOTORREVIEWER36][NEW CGRA]", 276),
    ("TOUAREG", 2005, 2009, 4200, None, "AXQ", "Touareg 4.2 V8 306hp [ROW_FIX AXQ]", 306),
    ("TOUAREG", 2006, 2007, 5000, None, "5.0 V10 TDI (Touareg)", "Touareg V10 TDI 310hp US 2006-07 (fuel label wrong -> Diesel) [AUTOBLOGV10][NEW]", 310),
    ("TOUAREG", 2009, 2009, 3000, None, "3.0 V6 TDI (Touareg)", "Touareg 3.0 TDI 221hp US launch (fuel label wrong -> Diesel) [NEW]", 221),
    ("TOUAREG", 2015, 2015, 3000, None, "3.0 TSI Hybrid (Touareg)", "Touareg Hybrid 3.0 SC V6 + e-motor 380hp system (fuel col Hybrid) [NEW]", 380),
    ("TOUAREG", 2015, 2015, 3600, None, "CGRA", "Touareg 3.6 FSI 280hp [MOTORREVIEWER36][NEW CGRA]", 280),
    ("TOUAREG", 2016, 2016, None, None, "3.0 V6 TDI (Touareg)", "Touareg TDI 3.0 240hp (fuel col Diesel) [NEW]", 240),
    ("TOUAREG", 2017, 2017, None, None, "CGRA", "Touareg 2017 US final year = 3.6 FSI 280hp only [NEW CGRA]", 280),
    ("E-GOLF", 2015, 2017, None, None, "e-Golf Electric", "e-Golf EV 134hp (fuel label wrong -> Electric) [NEW]", 134),
]

def decide(model, year, code, fuel):
    parts = code.replace("LEMON_VOLKSWAGEN_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc, vin = None, None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
        if s.startswith("VIN") and len(s) > 3: vin = s[3:]
    mu = model.upper()
    cu = code.upper()
    # trim-slug decodes
    if mu == "GOLF" and "GOLFR" in cu.replace("LEMON_VOLKSWAGEN_", ""):
        return ("CYFB", "Golf R 2.0T 292hp US (GOLF R trim slug) [GTSCODES][NEW CYFB]", None, 292)
    if mu == "JETTA" and year == 2015 and fuel == "Diesel":
        return ("CVCA", "Jetta TDI EA288 150hp (TDI trim slug, fuel col Diesel) [VWVORTEX288]", None, 150)
    # Beetle 2015 2000cc: fuel column decides TDI (EA288) vs 2.0T petrol
    if mu == "BEETLE" and year == 2015 and cc == 2000:
        if fuel == "Diesel":
            return ("CVCA", "Beetle TDI 2015 = EA288 150hp (fuel col Diesel) [VWMEDIA15]", None, 150)
        return ("CCTA", "Beetle 2.0T 200hp petrol (VIN S/T; R-Line 210hp minority) [VWMEDIA15-era]", None, 200)
    # known-ambiguous/anomalous rows -> skip
    if mu == "PASSAT" and cc == 2800 and year == 2005:
        return (None, "Passat 2005 2800cc: anomalous (no 2.8 V6 in MY2005 B5.5/B6-gap; B5 2.8 ended MY2000)", None, None)
    if mu == "TOUAREG" and cc == 5000 and year == 2008:
        return (None, "Touareg 2008 5000cc: V10 TDI cancelled in US after MY2007 [AUTOBLOGV10]", None, None)
    if mu == "GOLF" and cc is None and year >= 2022:
        return (None, f"Golf {year} bare: GTI 241hp vs Golf R 328hp unknown (US Golf = GTI/R only)", None, None)
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc
             and (r[4] is None or (vin is not None and vin in r[4]))]
    if not cands:
        return (None, f"no rule for {model} {year} cc={cc} vin={vin}", None, None)
    cands.sort(key=lambda r: 0 if r[4] is not None else 1)
    r = cands[0]
    fuel_fix = FUEL_FIX_BY_TARGET.get(r[5])
    # fuel fix only needed when current label is wrong (Petrol-labeled diesels/EVs)
    if fuel_fix and fuel == fuel_fix: fuel_fix = None
    return (r[5], r[6], fuel_fix, r[7])

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == 3535, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 3535 (workspace rewind?)"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Volkswagen' AND engine_code LIKE 'LEMON_VOLKSWAGEN%' ORDER BY car_model, car_year, engine_code""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        tgt, note, fuel_fix, pfix = decide(model, year, code, fuel)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix, pfix))
    print(f"VW LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(25): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter(d[6] for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"

    if not apply:
        with open("database_enriched/csv_exports/34_lemon_batch17_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
            for d in decisions: w.writerow([d[0],"Volkswagen",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Volkswagen",s[1],s[2],"","","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step26_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP26_VERIFIED')""",
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

    with open("database_enriched/csv_exports/34_lemon_batch17_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
        for d in decisions: w.writerow([d[0],"Volkswagen",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_VOLKSWAGEN remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_VOLKSWAGEN%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
