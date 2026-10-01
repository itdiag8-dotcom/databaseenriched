"""Step 31 (user-plan Step 5, batch 22): replace LEMON_LAND_ROVER codes with real OEM codes.
194 rows, 7 truncated models (Defender/Discovery/Freelander/LR2/LR3/LR4/Range), MY2000-2025
-> 182 mapped / 12 documented skips.
CRITICAL decodes (Wikibooks LR VIN tables, US-market engine position):
- 1987-2016 (pos 6): 6=4.6 Rover V8 (P38 '00-'02/Disc '03), 9=4.6 (Disc '04), 5=4.0 Rover V8
  (Disc '00-'02), 2=KV6 (Freelander), 1=M62TUB44 (RR L322 '03-'05), 5=4.4 AJ41 (LR3/RR/RRS
  '05/06-'09), 4=4.0 Cologne V6 (LR3 US '05-'07, Canada-only '08-'09), 3=4.2 SC AJ33S, D=5.0 NA
  AJ133, E=5.0 SC AJ133S, K=3.0 Td6 diesel (RR/RRS '16), P/V/W=3.0 SCV6 AJ126 (W flex-fuel).
- LR2/DiscSport/Evoque (pos 8): N=3.2 Volvo SI6 (LR2 '08-'12), G=2.0 EcoBoost (LR2 '13-'15,
  DiscSport '15-'16, Evoque '12-'16).
- 2017+ (pos 8): E=5.0 SC, K=3.0 Td6 (Disc/RR/RRS '17-'20/21), N=2.0 diesel AJ20D (Velar D180
  '18-'19 - US-sold per C&D/CarGurus), U=3.0 I6 MHEV AJ300P (P360/P400), V=3.0 SCV6 AJ126,
  X=2.0 petrol AJ200P (P250/P300), Y=P400e 2.0 PHEV (RR/RRS '20-'21), 4=P440e/P550e 3.0 I6 PHEV
  ('23-), 7=4.4 N63TU3 P530 ('22-'23), 9=4.4 S68 MHEV P530 ('24-).
Model-bucket logic:
- 'Range' covers Range Rover + RR Sport + Evoque + Velar (2015 slug RANGEROVEREV = Evoque);
  engine resolved per-row via cc+VIN: bare 2013-2021 = 5.0 SC (sole unmarked), 2001-02 = P38 4.6,
  2003-05 = BMW 4.4, 2006-09 = 4.4 AJ41, 2010-12 = 5.0 NA.
- 'Discovery': 2000-02 = Discovery 2 4.0 Rover V8, 2003-04 = 4.6; 2015 SPO slug + bare 2016-25 =
  Discovery Sport 2.0 (full-size 3.0s all carry VIN letters); 2000CC 2021-25 = Discovery 5 P300;
  3000CC 2017-20 K/V = Td6/SCV6; 3000CC 2021-25 U = P360.
- LR3 2008-09 bare = 4.4 only (4.0 V6 US-dropped after '07, Wikibooks VIN table).
- Defender: 2000CC=P300 296, 3000CC=P400 395 (AJ300P), 5000CC=V8 518 (508PS).
Web-verified: 2024 Defender P300 2.0 still standard (KBB/CarBuzz/MotorTrend); Velar D180 180hp
US (C&D first drive + CarGurus listings); 2018 Velar P250 = 247hp (USNews); P400e 398hp combined.
Skips (12): RANGE 2000 bare (P38 4.0 SE 188 vs 4.6 HSE 222), RANGE 2022 bare (L405 5.0SC vs
L460 P530 transition), RANGE 3000CC bare x10 (SCV6/Td6/I6 without VIN letter).
"""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "WIKIVIN": "https://en.wikibooks.org/wiki/Vehicle_Identification_Numbers_(VIN_codes)/Land_Rover/VIN_Codes (US-market engine VIN tables: pos6 1987-2016, pos8 LR2/DiscSport/Evoque 2008-16 + all 2017-; K=3.0 Td6, P/V/W=3.0 SCV6 AJ126, D=5.0 NA, E=5.0 SC, N=3.2 SI6 LR2, G=2.0 EcoBoost, N=2.0D Velar, U=I6 MHEV, X=2.0 petrol, Y=P400e, 4=P440e/P550e, 7=N63TU3, 9=S68)",
    "DISCO3VIN": "https://www.disco3.co.uk/wiki/Vehicle_Identification_Number (LR3/RRS US VIN: pos5 engine 3=4.2 SC, 4=4.0 V6, 5=4.4 AJV8, D=5.0 NA, E=5.0 SC)",
    "DEF24": "https://www.kbb.com/land-rover/defender-110/2024/ + carbuzz.com/cars/land-rover/defender/2024/ (2024 Defender: P300 2.0 296hp standard 90/110 + P400 395 + V8 518; Velar-era P250)",
    "VELAR": "https://www.caranddriver.com/reviews/a15077365/2018-range-rover-velar-diesel-euro-spec-first-drive-review/ (US-spec Velar D180 180hp 2.0 Ingenium diesel confirmed) + cars.usnews.com (2018 Velar P250 247hp std) + cargurus.com D180 S listings",
    "LRVOCAB": "DB JLR vocabulary (Jaguar batch 16 + Euro catalog): 204PT 2.0 Si4 GTDI/Ingenium (n=49), 204DTD 2.0 Ingenium diesel 180 US, 306DT 3.0 TDV6/Td6, AJ126 3.0 SCV6, AJ133/508PN 5.0 NA, 508PS 5.0 SC, AJ300P 3.0 I6 MHEV 395, AJ41 4.4 NA (pre-linked RR 05-07), 428PS 4.2 SC (pre-linked RR), M62B44 BMW 4.4 (pre-linked RR 02-03), 406PN 4.0 V6 (pre-linked Discovery III), B6324S 3.2 SI6 (pre-linked Freelander 2), 25K4F KV6 2.5 (pre-linked Freelander)",
    "LRHIST": "US LR lineup history (L322 4.4 NA 305 + 4.2 SC 400 06-09 -> 5.0 NA/SC 10-12 -> L405 5.0SC 510; RR/RRS Td6 254hp US 2016-2019; SCV6 340; P400e 398hp combined; P440e 434hp 2023 / P550e 542hp 2024; P530 523hp; Defender V8 P525 518hp; DiscSport 2.0 240/237/246 by era; Discovery 5 P360 355)",
}

NEW_ENGINES = {
    "4.0 V8 (Rover OHV)": ("4.0 V8 Rover OHV (Discovery 2 2000-04 US 182hp / P38 4.0 SE 188)", "Petrol", 3948, 182, 8),
    "4.6 V8 (Rover OHV)": ("4.6 V8 Rover OHV (P38 4.6 HSE 222hp / Discovery 2 2003-04 217hp)", "Petrol", 4553, 217, 8),
    "P400e 2.0 PHEV (AJ200P + motor)": ("2.0 I4 Turbo Ingenium + 105kW motor (RR/RRS P400e PHEV, 398hp combined)", "Hybrid", 1995, 398, 4),
    "P440e/P550e 3.0 I6 PHEV": ("3.0 I6 Ingenium MHEV + motor (RR/RRS P440e 434hp 2023 / P550e 542hp 2024+)", "Hybrid", 2996, 434, 6),
    "P530 4.4 V8 TT (N63TU3)": ("4.4 V8 TwinTurbo BMW N63TU3 (RR L460/RRS P530 2022-23, 523hp)", "Petrol", 4395, 523, 8),
    "P530 MHEV 4.4 V8 TT (S68)": ("4.4 V8 TwinTurbo 48V BMW S68 (RR/RRS P530 2024+, 523hp)", "Petrol", 4395, 523, 8),
}

ROW_FIXES = {
    "M62B44": {"engine_type": "4.4 V8 BMW M62TUB44 (Range Rover L322 2003-05 282hp / BMW 540i/E38/E39)", "displacement_cc": 4398},
    "AJ41": {"engine_type": "4.4 V8 AJ-V8 NA (Range Rover L322 HSE 06-09 / LR3 05-09 / RRS, 305hp US)", "power_hp": 305},
    "428PS": {"engine_type": "4.2 V8 AJ-V8 Supercharged (Range Rover L322 SC 06-09 / RRS SC, 400hp US)", "power_hp": 400},
    "508PN": {"engine_type": "5.0 V8 AJ133 NA (LR4 10-13 / RR+RRS 10-12 375hp / Jaguar XK8-XF 380-385)", "power_hp": 375},
    "508PS": {"engine_type": "5.0 V8 AJ133S Supercharged (RR/RRS 510hp / Defender V8 P525 518hp / SVR 550-575)", "power_hp": 510},
    "306DT": {"engine_type": "3.0 V6 Td6/TDV6 diesel Ford-PSA Lion (RR/RRS/Discovery US Td6 254hp / Euro 211-256)", "power_hp": 254},
    "406PN": {"engine_type": "4.0 V6 Ford Cologne SOHC (LR3 2005-07, 216hp)", "power_hp": 216},
    "B6324S": {"engine_type": "3.2 I6 Volvo SI6 B6324S (LR2 2008-12, 230hp US)", "power_hp": 230},
    "25K4F": {"engine_type": "2.5 V6 Rover KV6 (Freelander 2002-05 US, 177hp)", "power_hp": 177},
    "204PT": {"engine_type": "2.0 I4 Turbo Si4 (Ford GTDI 240hp 12-17 / Ingenium P250 246 / P300 296 Defender-Discovery / Velar P250 247)"},
    "AJ300P": {"engine_type": "3.0 I6 Ingenium MHEV twin-turbo + e-supercharger (P400 395 RR/RRS/Defender / P360 355 Discovery-Velar / P340 335 Jaguar)"},
    "AJ126": {"engine_type": "3.0 V6 Supercharged AJ126 (XE/XF/XJ/F-Type 335-380 / LR4 14-16 + RR-RRS-Velar-Discovery SCV6 340hp)"},
}

FUEL_FIX_BY_TARGET = {
    "306DT": "Diesel", "204DTD": "Diesel",
    "P400e 2.0 PHEV (AJ200P + motor)": "Hybrid", "P440e/P550e 3.0 I6 PHEV": "Hybrid",
}

IDENTITY = {
    "M62B44": ("Petrol", 4398), "AJ41": ("Petrol", 4400), "428PS": ("Petrol", 4196),
    "508PN": ("Petrol", 5000), "508PS": ("Petrol", 5000), "306DT": ("Diesel", 2993),
    "406PN": ("Petrol", 4009), "B6324S": ("Petrol", 3200), "25K4F": ("Petrol", 2497),
    "204PT": ("Petrol", 2000), "AJ300P": ("Petrol", 2996), "AJ126": ("Petrol", 2995),
    "204DTD": ("Diesel", 1999),
}

# (MODEL-upper, y0, y1, cc, vin, target, evidence, pfix)  cc/vin None = wildcard-rows without marker
R = [
    # Defender L663
    ("DEFENDER", 2020, 2024, 2000, None, "204PT", "Defender P300 2.0 Si4 296hp (VINX + bare) [WIKIVIN][DEF24][LRVOCAB]", 296),
    ("DEFENDER", 2020, 2024, 3000, None, "AJ300P", "Defender P400 3.0 I6 MHEV 395hp (VINU + bare; 2024 P300-I6 same engine) [WIKIVIN][DEF24]", 395),
    ("DEFENDER", 2022, 2024, 5000, None, "508PS", "Defender V8 P525 5.0 SC 518hp [WIKIVIN][LRHIST]", 518),
    # Discovery 2 / Discovery Sport / Discovery 5
    ("DISCOVERY", 2000, 2002, None, None, "4.0 V8 (Rover OHV)", "Discovery 2 2000-02 = 4.0 Rover V8 182hp sole US [WIKIVIN][NEW]", 182),
    ("DISCOVERY", 2003, 2004, None, None, "4.6 V8 (Rover OHV)", "Discovery 2 2003-04 = 4.6 Rover V8 217hp sole US [WIKIVIN][NEW]", 217),
    ("DISCOVERY", 2016, 2016, None, None, "204PT", "Discovery Sport 2016 = 2.0 GTDI 240hp (bare rows = DiscSport; 2015 SPO slug precedent) [WIKIVIN][LRVOCAB]", 240),
    ("DISCOVERY", 2017, 2018, None, None, "204PT", "Discovery Sport 2017-18 = 2.0 GTDI 237hp [WIKIVIN][LRVOCAB]", 237),
    ("DISCOVERY", 2019, 2025, None, None, "204PT", "Discovery Sport 2019+ = 2.0 Ingenium P250 246hp [WIKIVIN][LRVOCAB]", 246),
    ("DISCOVERY", 2021, 2025, 2000, None, "204PT", "Discovery 5 P300 2.0 296hp (2000CC + VINX) [WIKIVIN][LRHIST]", 296),
    ("DISCOVERY", 2017, 2020, 3000, "K", "306DT", "Discovery 5 Td6 3.0 diesel 254hp (VINK; fuel col -> Diesel) [WIKIVIN][LRHIST]", 254),
    ("DISCOVERY", 2017, 2020, 3000, "V", "AJ126", "Discovery 5 Si6 3.0 SCV6 340hp (VINV) [WIKIVIN][LRVOCAB]", 340),
    ("DISCOVERY", 2021, 2025, 3000, None, "AJ300P", "Discovery 5 P360 3.0 I6 MHEV 355hp (VINU + bare 3.0 sole 2021+) [WIKIVIN][LRHIST]", 355),
    # Freelander 1
    ("FREELANDER", 2002, 2005, None, None, "25K4F", "Freelander US = 2.5 KV6 177hp sole (no US diesel) [WIKIVIN][LRVOCAB]", 177),
    # LR2 (Freelander 2)
    ("LR2", 2008, 2012, None, None, "B6324S", "LR2 2008-12 = 3.2 Volvo SI6 230hp [WIKIVIN][LRVOCAB]", 230),
    ("LR2", 2013, 2015, None, None, "204PT", "LR2 2013-15 (incl. 2015 Base/HSE/HSE LUX) = 2.0 EcoBoost 240hp [WIKIVIN][LRVOCAB]", 240),
    # LR3 (Discovery 3)
    ("LR3", 2005, 2007, 4000, None, "406PN", "LR3 4.0 Cologne V6 216hp (US 4.0 ended 2007) [WIKIVIN][LRVOCAB]", 216),
    ("LR3", 2005, 2007, 4400, None, "AJ41", "LR3 4.4 AJ-V8 NA 300hp [WIKIVIN][LRVOCAB][ROW_FIX AJ41]", 300),
    ("LR3", 2008, 2009, None, None, "AJ41", "LR3 2008-09 = 4.4 V8 only (4.0 V6 Canada-only from 08) [WIKIVIN][ROW_FIX AJ41]", 300),
    # LR4 (Discovery 4)
    ("LR4", 2010, 2013, None, None, "508PN", "LR4 2010-13 = 5.0 V8 NA 375hp sole [WIKIVIN][ROW_FIX 508PN]", 375),
    ("LR4", 2014, 2016, None, None, "AJ126", "LR4 2014-16 (incl. 2015 trims) = 3.0 SCV6 340hp sole [WIKIVIN][LRVOCAB]", 340),
    # Range bucket (Range Rover + Sport + Evoque + Velar)
    ("RANGE", 2001, 2002, None, None, "4.6 V8 (Rover OHV)", "Range Rover P38 2001-02 = 4.6 HSE 222hp sole [WIKIVIN][NEW]", 222),
    ("RANGE", 2003, 2005, None, None, "M62B44", "Range Rover L322 2003-05 = BMW 4.4 M62TUB44 282hp sole US [WIKIVIN][LRVOCAB]", 282),
    ("RANGE", 2006, 2009, None, None, "AJ41", "Range Rover L322 HSE 2006-09 = 4.4 AJ-V8 NA 305hp (SC = 4200CC rows) [WIKIVIN][ROW_FIX AJ41]", 305),
    ("RANGE", 2006, 2008, 4200, None, "428PS", "Range Rover L322 Supercharged 4.2 SC 400hp [WIKIVIN][ROW_FIX 428PS]", 400),
    ("RANGE", 2006, 2008, 4400, None, "AJ41", "Range Rover L322 4.4 NA 305hp [WIKIVIN][ROW_FIX AJ41]", 305),
    ("RANGE", 2010, 2012, None, None, "508PN", "Range Rover L322 2010-12 = 5.0 NA 375hp (SC = 5000CC rows) [WIKIVIN][ROW_FIX 508PN]", 375),
    ("RANGE", 2012, 2012, 5000, "D", "508PN", "L322/RRS 5.0 NA (VIND) 375hp [WIKIVIN][ROW_FIX 508PN]", 375),
    ("RANGE", 2012, 2022, 5000, "E", "508PS", "RR/RRS 5.0 SC (VINE) 510hp [WIKIVIN][ROW_FIX 508PS]", 510),
    ("RANGE", 2013, 2021, None, None, "508PS", "RR L405/RRS 2013-21 bare = 5.0 SC 510hp (sole unmarked engine) [WIKIVIN][LRHIST]", 510),
    ("RANGE", 2014, 2022, 5000, None, "508PS", "RR/RRS 5.0 SC 510hp (5000CC bare) [WIKIVIN][ROW_FIX 508PS]", 510),
    ("RANGE", 2014, 2020, 3000, "V", "AJ126", "RR/RRS/Velar 3.0 SCV6 340hp (VINV) [WIKIVIN][LRVOCAB]", 340),
    ("RANGE", 2014, 2014, 3000, "W", "AJ126", "RR/RRS 3.0 SCV6 flex-fuel 340hp (VINW) [WIKIVIN]", 340),
    ("RANGE", 2016, 2016, 3000, "P", "AJ126", "RR/RRS 3.0 SCV6 340hp (VINP) [WIKIVIN]", 340),
    ("RANGE", 2016, 2021, 3000, "K", "306DT", "RR/RRS Td6 3.0 diesel 254hp (VINK; fuel col -> Diesel) [WIKIVIN][LRHIST]", 254),
    ("RANGE", 2019, 2025, 3000, "U", "AJ300P", "RR/RRS 3.0 I6 P400 395hp (VINU; 2022+ L460 P400) [WIKIVIN][LRHIST]", 395),
    ("RANGE", 2023, 2023, 3000, "4", "P440e/P550e 3.0 I6 PHEV", "RR P440e 3.0 I6 PHEV 434hp (VIN4; fuel col -> Hybrid) [WIKIVIN][NEW]", 434),
    ("RANGE", 2024, 2024, 3000, "4", "P440e/P550e 3.0 I6 PHEV", "RR P550e 3.0 I6 PHEV 542hp (VIN4; fuel col -> Hybrid) [WIKIVIN][NEW]", 542),
    ("RANGE", 2018, 2019, 2000, "N", "204DTD", "Velar D180 2.0 Ingenium diesel 180hp (VINN; fuel col -> Diesel) [WIKIVIN][VELAR]", 180),
    ("RANGE", 2019, 2021, 2000, "Y", "P400e 2.0 PHEV (AJ200P + motor)", "RR/RRS P400e 2.0 PHEV 398hp combined (VINY; fuel col -> Hybrid) [WIKIVIN][NEW]", 398),
    ("RANGE", 2018, 2018, 2000, None, "204PT", "Velar P250 2.0 247hp (2018) [WIKIVIN][VELAR]", 247),
    ("RANGE", 2019, 2025, 2000, None, "204PT", "Evoque/Velar P250 2.0 Ingenium 246hp (VINX + bare) [WIKIVIN][LRVOCAB]", 246),
    ("RANGE", 2023, 2023, 4400, None, "P530 4.4 V8 TT (N63TU3)", "RR L460 P530 4.4 N63TU3 523hp (bare + VIN7) [WIKIVIN][NEW]", 523),
    ("RANGE", 2023, 2023, 4400, "7", "P530 4.4 V8 TT (N63TU3)", "RR L460 P530 4.4 N63TU3 523hp (VIN7) [WIKIVIN][NEW]", 523),
    ("RANGE", 2024, 2025, 4400, None, "P530 MHEV 4.4 V8 TT (S68)", "RR/RRS P530 4.4 S68 MHEV 523hp (bare 2024-25) [WIKIVIN][NEW]", 523),
    ("RANGE", 2024, 2025, 4400, "9", "P530 MHEV 4.4 V8 TT (S68)", "RR/RRS P530 4.4 S68 MHEV 523hp (VIN9) [WIKIVIN][NEW]", 523),
]

def parse_code(code):
    m = re.match(r"^LEMON_LAND_ROVER_(.+)$", code)
    if not m: return None
    toks = m.group(1).split("_")
    yi = next((i for i, t in enumerate(toks) if re.fullmatch(r"(19|20)\d\d", t)), None)
    if yi is None: return None
    year = int(toks[yi])
    cc = vin = None
    model_toks = []
    for t in toks[:yi]:
        if re.fullmatch(r"\d+CC", t): cc = int(t[:-2])
        elif re.fullmatch(r"VIN[A-Z0-9]", t): vin = t[3:]
        else: model_toks.append(t)
    return " ".join(model_toks), year, cc, vin, "_".join(toks[yi+1:])

def decide(model, year, cc, vin, code):
    mu, cu = model.upper(), code.upper()
    if cu.endswith("RANGEROVEREV"):
        return ("204PT", "Range Rover Evoque 2015 = 2.0 GTDI 240hp (trim slug; G code era) [WIKIVIN][LRVOCAB]", None, 240)
    if cu.endswith("DISCOVERYSPO"):
        return ("204PT", "Discovery Sport 2015 = 2.0 GTDI 240hp (trim slug; G code era) [WIKIVIN][LRVOCAB]", None, 240)
    if mu == "RANGE" and cc is None and 2023 <= year <= 2025:
        return (None, "L460 2023-25 bare: P400/P530/P440e-P550e all possible - every L460 engine appears VIN/cc-marked", None, None)
    if mu == "RANGE" and cc is None and year == 2000:
        return (None, "Range Rover P38 2000: 4.0 SE 188hp vs 4.6 HSE 222hp both offered (Wikibooks VIN 5/6 codes)", None, None)
    if mu == "RANGE" and cc is None and year == 2022:
        return (None, "2022 bare: L405 5.0 SC 510 vs L460 P530 4.4 523 transition year (VINE 2022 covers L405)", None, None)
    if mu == "RANGE" and cc == 3000 and vin is None:
        return (None, "Range 3000CC bare: SCV6 340 vs Td6 254 (vs I6 395 from 2019) - no VIN letter to disambiguate", None, None)
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc and (r[4] is None or r[4] == vin)]
    if not cands:
        return (None, f"no rule for Land Rover {model} {year} cc={cc} vin={vin}", None, None)
    cands.sort(key=lambda r: (r[4] is None, r[1] != year))  # vin-specific first, then nearest y0
    r = cands[0]
    fuel_fix = FUEL_FIX_BY_TARGET.get(r[5])
    if fuel_fix and vin is not None and r[4] is None and FUEL_FIX_BY_TARGET.get(r[5]):
        pass  # fuel fix logic below uses target; bare rows sharing a fixable target are fine only for diesel/PHEV groups where all rows fix
    return (r[5], r[6], fuel_fix, r[7])

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == 2285, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 2285 (workspace rewind?)"
    base_eng = cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0]
    assert base_eng == 7852, f"BASELINE MISMATCH: engines={base_eng}, expected 7852"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Land Rover' AND engine_code LIKE 'LEMON%' ORDER BY car_model, car_year, engine_code""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        p = parse_code(code)
        assert p, f"unparseable code: {code}"
        pm, py, cc, vin, post = p
        assert pm.upper() == model.upper(), f"model parse mismatch {code} vs {model}"
        tgt, note, fuel_fix, pfix = decide(model, year, cc, vin, code)
        if fuel_fix and fuel == fuel_fix: fuel_fix = None
        if tgt is None: skips.append((vid, model, year, code, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix, pfix))
    print(f"Land Rover LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print(f"  SKIP: {s[1]} {s[2]} [{s[3]}] - {s[4]}")
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(30): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter((d[4], d[6]) for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"
    for tgt, (efuel, ecc) in IDENTITY.items():
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

    if not apply:
        with open("database_enriched/csv_exports/39_lemon_batch22_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
            for d in decisions: w.writerow([d[0],"Land Rover",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Land Rover",s[1],s[2],s[3],"","","SKIP",s[4]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step31_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP31_VERIFIED')""",
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
    tgts = tuple(set(d[4] for d in decisions))
    cur.execute(f"""UPDATE vehicle_variants SET engine_power_hp=
        (SELECT power_hp FROM engines WHERE engine_code=vehicle_variants.engine_code)
        WHERE engine_code IN ({','.join('?'*len(tgts))}) AND engine_power_hp IS NULL""", tgts)

    with open("database_enriched/csv_exports/39_lemon_batch22_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
        for d in decisions: w.writerow([d[0],"Land Rover",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON Land Rover remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE car_brand='Land Rover' AND engine_code LIKE 'LEMON%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
