"""Step 16 (user-plan Step 5, batch 7): replace LEMON_AUDI codes with real OEM engine codes.
576 rows, 31 models. Signal: cc in code + occasional VIN char; mostly one engine per (model, year, cc).
US-market facts web-verified; DB's VAG vocabulary (APB, AUK, CAEB, CTUA, CTWA, CTGA...) reused.
Junk-labeled rows CTNA (W12 6.3) and CTGA (A8 4.0T) relabeled; NULL rows DBPA/DHHA/DLRA completed."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "CDA8D5": "https://www.caranddriver.com/audi/a8-2020 (A8 D5 US: 55 TFSI 3.0T 335hp, 60 TFSI 4.0T 453hp, 60 TFSI e PHEV 443hp)",
    "TRUECARA8": "https://truecar.com/audi/a8/2020 (60 TFSI = turbo 4.0 V8 453hp; 60 TFSI e = 3.0 V6 PHEV 443hp)",
    "AD8CDRA": "https://www.auto-data.net/en/audi-a8-d4-4h-4.2-fsi-v8-372hp-quattro-tiptronic-20337 (A8 D4 4.2 FSI = CDRA 372hp)",
    "MOTORINSEL8": "https://www.motorinsel.eu/audi-a8-d4-4h (A8 D4 4.0 TFSI = CEU 420hp 2012-13, CTG 435hp 2013-17)",
    "ACR_TTRS": "https://www.australiancar.reviews/audi-8j-tt-rs-cepa-cepb-2-5-tfsi-engine/ (TT RS 8J = CEPA 335hp, TT RS Plus CEPB 360hp)",
    "TTFORUM": "https://www.ttforum.co.uk/threads/tt-rs-new-engine-code.191229/ (TT RS CEPB 360hp from 5/2011)",
    "MOTORINSELR8": "https://www.motorinsel.uk/audi-r8-42 (R8 4.2 FSI = BYH 420hp 2007-10; V10 plus = CTP 549hp)",
    "ETKA": "https://vag-codes.info/files/engines/audi-engines.pdf (CYFB 292hp S3/TTS; engine code registry)",
    "CARPARTS": "https://www.carparts.com/blog/a-guide-to-audis-tfsi-engines/ (CYFB = US 292hp S3 8V)",
    "BARTEK": "https://www.bar-tek.com/ea888-engine-codes (EA888 gen3 codes: CYFB 292hp S3 8V etc.)",
    "GMAGM": "placeholder-unused",
}

NEW_ENGINES = {
    "ATW": ("1.8 T 20v (A4 B5 US, 150hp)", "Petrol", 1781, 150, 4),
    "2.0 TFSI (S3 8V, 292hp)": ("2.0 I4 Turbo (EA888, S3 8V 292hp US)", "Petrol", 1984, 292, 4),
    "2.0 TFSI (S3 8Y, 315hp)": ("2.0 I4 Turbo (EA888 evo4, S3 8Y 315hp)", "Petrol", 1984, 315, 4),
    "5.2 V10 FSI (S6 C6, 435hp)": ("5.2 V10 FSI (S6 C6 435hp)", "Petrol", 5204, 435, 10),
    "5.2 V10 FSI (S8 D3, 450hp)": ("5.2 V10 FSI (S8 D3 450hp)", "Petrol", 5204, 450, 10),
    "4.0 V8 TFSI (S8 D5, 563hp)": ("4.0 V8 TwinTurbo (S8 D5 563hp)", "Petrol", 3993, 563, 8),
    "4.2 V8 FSI (RS4/RS5)": ("4.2 V8 FSI high-rev (RS4 B7 420hp / RS5 B8 450hp)", "Petrol", 4163, 450, 8),
    "5.2 V10 FSI (R8 42, 525hp)": ("5.2 V10 FSI (R8 type 42, 525hp US)", "Petrol", 5204, 525, 10),
    "5.2 V10 FSI (R8 4S)": ("5.2 V10 FSI (R8 type 4S, 532hp; performance 602hp)", "Petrol", 5204, 532, 10),
    "2.0 TFSI (TTS 8J, 265hp)": ("2.0 I4 Turbo (TTS 8J 265hp)", "Petrol", 1984, 265, 4),
    "2.5 TFSI (TT RS 8S, 394hp)": ("2.5 I5 Turbo (TT RS 8S 394hp)", "Petrol", 2480, 394, 5),
    "3.0 V6 TDI (Q7 US, 225hp)": ("3.0 V6 TDI (US Q7 TDI 225hp)", "Diesel", 2967, 225, 6),
    "4.0 V8 TFSI (SQ7/SQ8, 500hp)": ("4.0 V8 TwinTurbo (SQ7/SQ8 500hp US)", "Petrol", 3993, 500, 8),
    "Q4 e-tron Electric": ("Electric motors (Q4 e-tron 40/50)", "Electric", None, 201, None),
    "e-tron Electric": ("Electric motors (e-tron 55 / Q8 e-tron, 355hp)", "Electric", None, 355, None),
    "4.0 V8 TFSI (A8 D5 60 TFSI)": ("4.0 V8 TwinTurbo (A8 D5 60 TFSI 453hp US)", "Petrol", 3993, 453, 8),
}

ROW_FIXES = {
    "CTNA": {"engine_type": "6.3 W12 FSI quattro (A8 D4, 500hp US)", "power_hp": 500},
    "CTGA": {"engine_type": "4.0 V8 TFSI quattro (A8 D4 4.0T, 420/435hp)"},
    "DBPA": {"engine_type": "2.0 TFSI quattro (B9 45 TFSI, 248/252hp)", "power_hp": 252},
    "DHHA": {"engine_type": "2.0 TFSI (TT Mk3 45 TFSI, 245hp)", "power_hp": 245},
    "DLRA": {"engine_type": "2.0 TFSI quattro (TTS Mk3, 288hp)", "power_hp": 288},
}

# (MODEL, y0, y1, cc, target, evidence)  cc=None = bare row
R = [
    # A3
    ("A3", 2006, 2009, 2000, "AXX", "A3 8P 2.0T 200hp US (AXX family) [DB family]"),
    ("A3", 2006, 2009, 3200, "BDB", "A3 8P 3.2 VR6 250hp [DB family]"),
    ("A3", 2010, 2013, None, "BGB", "A3 8P FL 2.0T only US (200-211hp; CBFA/BWA family) [DB family]"),
    ("A3", 2012, 2013, 2000, "BGB", "A3 2.0T (VIN E/F both 2.0T) [DB family]"),
    ("A3", 2015, 2015, 1800, "CNSB", "A3 8V 1.8T FWD 170hp [DB family]"),
    ("A3", 2015, 2016, 2000, "CWZA", "A3 8V 2.0T quattro 220hp (VIN 8) [DB family, note 228hp Euro row]"),
    ("A3", 2016, 2016, 1800, "CNSB", "A3 1.8T 170hp (VIN 7) [DB family]"),
    ("A3", 2018, 2020, None, "CWZA", "2018-20 A3 = 2.0T only (220hp) [DB family]"),
    ("A3", 2022, 2025, None, "CWZA", "A3 8Y 2.0T 40 TFSI 201hp [DB family]"),
    # A4
    ("A4", 2000, 2001, 1800, "ATW", "A4 B5 1.8T 150hp US [NEW ATW]"),
    ("A4", 2000, 2001, 2800, "APR", "A4 B5 2.8 30v 190hp [DB family]"),
    ("A4", 2002, 2005, 1800, "AMB", "A4 B6 1.8T 170hp US [DB family]"),
    ("A4", 2002, 2005, 3000, "AVK", "A4 B6 3.0 220hp US [DB family]"),
    ("A4", 2005, 2009, 2000, "BGB", "A4 B7 2.0T 200hp US [DB family]"),
    ("A4", 2005, 2009, 3200, "AUK", "A4 B7 3.2 FSI 255hp US [DB family]"),
    ("A4", 2010, 2014, None, "CAEB", "A4 B8 2.0T only 211hp [DB family]"),
    ("A4", 2015, 2016, None, "CNCD", "A4 B8.5 2.0T 220hp [DB family]"),
    ("A4", 2018, 2025, None, "DBPA", "A4 B9 2.0T 45 TFSI 248/252hp [ROW_FIX DBPA]"),
    ("A4", 2021, 2025, 2000, "DBPA", "A4 B9 2.0T (VIN A/B = two calibrations, same engine) [ROW_FIX DBPA]"),
    # A5
    ("A5", 2008, 2008, None, "AUK", "2008 A5 = 3.2 FSI only [DB family]"),
    ("A5", 2010, 2010, 2000, "CAEB", "A5 2.0T 211hp [DB family]"),
    ("A5", 2010, 2012, 3200, "AUK", "A5 3.2 FSI 265hp [DB family]"),
    ("A5", 2011, 2014, None, "CAEB", "2011+ A5 = 2.0T only [DB family]"),
    ("A5", 2016, 2016, 2000, "CNCD", "A5 FL 2.0T 220hp (VIN 2/G) [DB family]"),
    ("A5", 2018, 2025, None, "DBPA", "A5 B9 2.0T 45 TFSI [ROW_FIX DBPA]"),
    ("A5", 2021, 2025, 2000, "DBPA", "A5 B9 2.0T (VIN A/B) [ROW_FIX DBPA]"),
    # A6
    ("A6", 2000, 2004, 2700, "APB", "A6 C5 2.7T 250hp US [DB family]"),
    ("A6", 2000, 2001, 2800, "APR", "A6 C5 2.8 30v 190hp [DB family]"),
    ("A6", 2002, 2004, 3000, "AVK", "A6 C5 3.0 220hp [DB family]"),
    ("A6", 2000, 2004, 4200, "BAS", "A6 C5 4.2 300hp US (BAS 295 Euro row) [DB family]"),
    ("A6", 2005, 2011, 3200, "AUK", "A6 C6 3.2 FSI 255hp [DB family]"),
    ("A6", 2005, 2011, 4200, "BAR", "A6 C6 4.2 FSI 350hp US (BAR 345 Euro row) [DB family]"),
    ("A6", 2009, 2011, 3000, "CTUA", "A6 C6 3.0T 300hp US 2010-11 [DB family]"),
    ("A6", 2012, 2018, 2000, "CNCD", "A6 C7 2.0T 220hp [DB family]"),
    ("A6", 2012, 2015, 3000, "CTUA", "A6 C7 3.0T 310hp [DB family]"),
    ("A6", 2016, 2018, 3000, "CTWA", "A6 C7 3.0T 333hp [DB family]"),
    ("A6", 2016, 2018, 2000, "CNCD", "A6 C7 2.0T (VIN 8) [DB family]"),
    ("A6", 2019, 2025, 2000, "DBPA", "A6 C8 2.0T 45 TFSI 248hp (VIN 3/8) [ROW_FIX DBPA]"),
    ("A6", 2019, 2025, 3000, "CTWA", "A6 C8 3.0T 55 TFSI 335hp US [DB family]"),
    # A7 / A8
    ("A7", 2012, 2014, None, "CTUA", "A7 C7 3.0T only 310hp [DB family]"),
    ("A7", 2018, 2025, None, "CTWA", "A7 C8 3.0T 55 TFSI 335hp [DB family]"),
    ("A8", 2000, 2004, None, "BAS", "A8 D2 4.2 300hp US [DB family]"),
    ("A8", 2010, 2011, None, "CDRA", "A8 D4 4.2 FSI 372hp [AD8CDRA]"),
    ("A8", 2005, 2009, 4200, "BFM", "A8 D3 4.2 335hp US (BFM 330 Euro row) [DB family]"),
    ("A8", 2005, 2009, 6000, "BHT", "A8 D3 W12 450hp US [DB family]"),
    ("A8", 2012, 2012, 4200, "CDRA", "A8 D4 4.2 FSI 372hp (VIN V) [AD8CDRA]"),
    ("A8", 2012, 2016, 6300, "CTNA", "A8 D4 W12 6.3 500hp US (VIN 4) [ROW_FIX CTNA]"),
    ("A8", 2013, 2018, 4000, "CTGA", "A8 D4 4.0T 420/435hp (VIN 2/3) [MOTORINSEL8][ROW_FIX CTGA]"),
    ("A8", 2013, 2016, 3000, "CTUA", "A8 D4 3.0T 310hp (VIN G) [DB family]"),
    ("A8", 2017, 2018, 3000, "CTWA", "A8 D4 3.0T 333hp [DB family]"),
    ("A8", 2019, 2021, 3000, "CTWA", "A8 D5 55 TFSI 3.0T 335hp (VIN D) [CDA8D5]"),
    ("A8", 2019, 2021, 4000, "4.0 V8 TFSI (A8 D5 60 TFSI)", "A8 D5 60 TFSI 4.0T 453hp (VIN E) [CDA8D5][TRUECARA8]"),
    ("A8", 2020, 2025, None, "CTWA", "A8 D5 55 TFSI 3.0T 335hp base [CDA8D5]"),
    # allroad
    ("Allroad", 2001, 2005, 2700, "APB", "Allroad C5 2.7T only 250hp [DB family]"),
    ("Allroad", 2001, 2002, None, "APB", "Allroad = 2.7T only [DB family]"),
    ("Allroad", 2003, 2005, 4200, "BAS", "Allroad 4.2 300hp [DB family]"),
    ("Allroad", 2013, 2016, None, "CNCD", "A4 Allroad B8 2.0T 220hp [DB family]"),
    # Q3 / Q4 / Q5 / Q7 / Q8
    ("Q3", 2015, 2018, None, "BGB", "Q3 8U 2.0T 200hp US [DB family]"),
    ("Q3", 2019, 2025, None, "CWZA", "Q3 8S? 2.0T 228hp US [DB family]"),
    ("Q3", 2023, 2025, 2000, "CWZA", "Q3 2.0T 40/45 TFSI 201/228hp (VIN E/U) [DB family]"),
    ("Q4", 2022, 2025, None, "Q4 e-tron Electric", "US Q4 = e-tron only (no gas Q4) [NEW]"),
    ("Q5", 2009, 2009, None, "AUK", "2009 Q5 = 3.2 FSI only (launch year) [DB family]"),
    ("Q5", 2011, 2012, 2000, "CAEB", "Q5 2.0T 211hp [DB family]"),
    ("Q5", 2011, 2012, 3200, "AUK", "Q5 3.2 FSI 270hp [DB family]"),
    ("Q5", 2013, 2017, 2000, "CNCD", "Q5 2.0T 220hp (VIN F) [DB family]"),
    ("Q5", 2014, 2017, 3000, "CTUD", "Q5 3000cc petrol = 3.0T (SQ5-family 354hp, VIN G/7 match 3.0 TFSI) [DB family]"),
    ("Q5", 2018, 2025, None, "CWZA", "Q5 FY 2.0T 45 TFSI 248hp [DB family]"),
    ("Q5", 2023, 2025, 2000, "CWZA", "Q5 2.0T 45 TFSI (VIN A/B) [DB family]"),
    ("Q7", 2007, 2010, 3600, "BHK", "Q7 3.6 FSI 280hp US [DB family]"),
    ("Q7", 2007, 2010, 4200, "BAR", "Q7 4.2 FSI 350hp US [DB family]"),
    ("Q7", 2009, 2010, 3000, "3.0 V6 TDI (Q7 US, 225hp)", "Q7 3.0 TDI 225hp US [NEW]"),
    ("Q7", 2011, 2015, None, "CRCA", "Q7 2011-2015 US = 3.0 TDI only 240hp [DB family]"),
    ("Q7", 2013, 2013, 3000, "CRCA", "Q7 3.0 TDI 240hp US 2013 (fuel fixed) [DB family]"),
    ("Q7", 2017, 2019, 2000, "CYPA", "Q7 4M 2.0T 252hp (VIN H) [DB family]"),
    ("Q7", 2020, 2022, 2000, "CYPA", "Q7 2.0T 45 TFSI 248hp (VIN J) [DB family]"),
    ("Q7", 2023, 2025, 2000, "CYPA", "Q7 2.0T 261hp (VIN C) [DB family]"),
    ("Q7", 2017, 2025, 3000, "CREC", "Q7 3.0T 329/335hp (VIN A/X/V) [DB family]"),
    ("Q8", 2019, 2025, None, "CTWA", "Q8 3.0T 55 TFSI 335hp only US [DB family]"),
    # R8
    ("R8", 2008, 2009, None, "BYH", "R8 4.2 FSI 420hp only 2008-09 [MOTORINSELR8]"),
    ("R8", 2010, 2015, 4200, "BYH", "R8 4.2 FSI 420/430hp (VIN U) [MOTORINSELR8]"),
    ("R8", 2010, 2015, 5200, "5.2 V10 FSI (R8 42, 525hp)", "R8 V10 5.2 525hp US (VIN N) [MOTORINSELR8 family]"),
    ("R8", 2018, 2018, None, "5.2 V10 FSI (R8 4S)", "R8 4S 5.2 532hp [MOTORINSELR8 family]"),
    ("R8", 2021, 2021, None, "5.2 V10 FSI (R8 4S)", "2021 R8 = 5.2 V10 only [MOTORINSELR8 family]"),
    ("R8", 2021, 2021, 5200, "5.2 V10 FSI (R8 4S)", "R8 4S V10 562/602hp (VIN A/E) [MOTORINSELR8 family]"),
    # S/RS
    ("RS", 2003, 2003, None, "BCY", "RS 2003 = RS6 C5 4.2TT 450hp [DB BCY=Rs6 link]"),
    ("RS", 2007, 2008, None, "4.2 V8 FSI (RS4/RS5)", "RS 2007-08 = RS4 B7 4.2 FSI 420hp [NEW]"),
    ("RS 5", 2015, 2015, None, "4.2 V8 FSI (RS4/RS5)", "RS5 B8 4.2 FSI 450hp [NEW]"),
    ("RS 7", 2015, 2015, None, "CRDB", "RS7 4.0T 560hp US [DB family]"),
    ("S3", 2015, 2020, None, "2.0 TFSI (S3 8V, 292hp)", "S3 8V 2.0T 292hp (CYFB family) [CARPARTS][ETKA]"),
    ("S3", 2022, 2025, None, "2.0 TFSI (S3 8Y, 315hp)", "S3 8Y 2.0T 315hp [CARPARTS family]"),
    ("S4", 2000, 2002, None, "APB", "S4 B5 2.7TT 250hp [DB family]"),
    ("S4", 2004, 2008, None, "BBK", "S4 B6/B7 4.2 340hp [DB family]"),
    ("S4", 2009, 2016, None, "CTWA", "S4 B8 3.0T 333hp [DB family]"),
    ("S4", 2018, 2025, None, "CTUD", "S4 B9 3.0T 354hp [DB family]"),
    ("S5", 2008, 2009, None, "BAR", "S5 4.2 FSI 354hp US [DB family]"),
    ("S5", 2010, 2012, 3000, "CTWA", "S5 3.0T 333hp [DB family]"),
    ("S5", 2010, 2012, 4200, "BAR", "S5 4.2 FSI [DB family]"),
    ("S5", 2013, 2016, None, "CTWA", "S5 3.0T 333hp [DB family]"),
    ("S5", 2018, 2025, None, "CTUD", "S5 B9 3.0T 354hp [DB family]"),
    ("S6", 2002, 2003, None, "ANK", "S6 C5 4.2 340hp [DB family]"),
    ("S6", 2007, 2011, None, "5.2 V10 FSI (S6 C6, 435hp)", "S6 C6 5.2 V10 435hp [NEW]"),
    ("S6", 2013, 2025, None, "CTGE", "S6 4.0T 420/450/444hp US [DB family]"),
    ("S7", 2013, 2025, None, "CTGE", "S7 4.0T 420/450hp US [DB family]"),
    ("S8", 2001, 2003, None, "AVP", "S8 D2 4.2 360hp US [DB family]"),
    ("S8", 2007, 2009, None, "5.2 V10 FSI (S8 D3, 450hp)", "S8 D3 5.2 V10 450hp [NEW]"),
    ("S8", 2013, 2018, None, "CTFA", "S8 D4 4.0T 520hp US [DB family]"),
    ("S8", 2020, 2025, None, "4.0 V8 TFSI (S8 D5, 563hp)", "S8 D5 4.0T 563hp [NEW]"),
    ("SQ5", 2014, 2025, None, "CTUD", "SQ5 3.0T 349/354hp US [DB family]"),
    ("SQ7", 2020, 2025, None, "4.0 V8 TFSI (SQ7/SQ8, 500hp)", "SQ7 4.0T 500hp US [NEW]"),
    ("SQ8", 2020, 2025, None, "4.0 V8 TFSI (SQ7/SQ8, 500hp)", "SQ8 4.0T 500hp US [NEW]"),
    # TT
    ("Tt", 2008, 2009, 2000, "BGB", "TT 2.0T 200hp [DB family]"),
    ("Tt", 2008, 2009, 3200, "BDB", "TT 3.2 VR6 250hp [DB family]"),
    ("Tt", 2010, 2012, None, "BGB", "TT 2.0T only 2010+ (200-211hp) [DB family]"),
    ("Tt", 2013, 2013, 2000, "BGB", "TT 2.0T 211hp [DB family]"),
    ("Tt", 2013, 2013, 2500, "CZGB", "TT RS 2.5 360hp US (CEPB family) [ACR_TTRS][TTFORUM]"),
    ("Tt", 2015, 2015, None, "DHHA", "TT Mk3 base 2.0T 245hp (TTQUATTROBAS slug) [ROW_FIX DHHA]"),
    ("Tt", 2018, 2018, 2000, "DHHA", "TT Mk3 2.0T 245hp [ROW_FIX DHHA]"),
    ("Tt", 2018, 2022, 2500, "2.5 TFSI (TT RS 8S, 394hp)", "TT RS 8S 2.5 394hp [ACR_TTRS family]"),
    ("Tts", 2013, 2013, None, "2.0 TFSI (TTS 8J, 265hp)", "TTS 8J 2.0T 265hp [NEW]"),
    # e-tron
    ("e-tron", 2019, 2024, None, "e-tron Electric", "e-tron/Q8 e-tron electric 355hp [NEW]"),
]

FUEL_FIX = {
    "3.0 V6 TDI (Q7 US, 225hp)": "Diesel", "CRCA": "Diesel",
    "Q4 e-tron Electric": "Electric", "e-tron Electric": "Electric",
}

def decide(model, year, code):
    parts = code.replace("LEMON_AUDI_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc = None
    for s in segs:
        m = re.match(r"^(\d{4})CC$", s)
        if m: cc = int(m.group(1))
    mu = model.upper()
    # TTS slug row (2015 TTQUATTROS2D)
    if mu == "A3" and "QUATTROPRE" in code:
        return ("CWZA", "A3 2015 2.0T quattro premium 220hp [DB family]", None)
    if mu == "TT" and "TTQUATTROS" in code:
        return ("DLRA", "TTS Mk3 2.0T 288hp [ROW_FIX DLRA]", None)
    cands = [r for r in R if r[0].upper() == mu and r[1] <= year <= r[2] and r[3] == cc]
    if not cands and cc is not None:
        return (None, f"{model} {year} {cc}cc: no cc rule (bare rule would be ambiguous)", None)
    if not cands:
        return (None, f"no rule for {model} {year} (bare)", None)
    r = cands[0]
    return (r[4], r[5], FUEL_FIX.get(r[4]))

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code FROM vehicle_variants
        WHERE car_brand='Audi' AND engine_code LIKE 'LEMON_AUDI%' ORDER BY car_model, car_year""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code in rows:
        tgt, note, fuel_fix = decide(model, year, code)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix))
    print(f"Audi LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    print("\nskips by reason:")
    for (m, n), c in Counter((s[1], s[3]) for s in skips).most_common(40): print(f"  {c:3} {m}: {n}")
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(15): print(f"  {c:3} {t}")

    if not apply:
        with open("database_enriched/csv_exports/24_lemon_batch7_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],"Audi",d[1],d[2],d[3],d[4],d[5] or "",d[6] or ""])
            for s in skips: w.writerow([s[0],"Audi",s[1],s[2],"","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step16_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP16_VERIFIED')""",
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

    with open("database_enriched/csv_exports/24_lemon_batch7_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],"Audi",d[1],d[2],d[3],d[4],d[5] or "",d[6] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_AUDI remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_AUDI%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
