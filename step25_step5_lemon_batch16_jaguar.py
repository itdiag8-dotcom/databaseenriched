"""Step 25 (user-plan Step 5, batch 16): replace LEMON_JAGUAR codes with real OEM engine codes.
258 rows, 19 models, MY2000-2025. Signals: cc + VIN engine letter (8th char) + year.
DB Jaguar vocabulary reused (AJ25/AJ30 Duratec V6, AJ34 4.2, AJ33S 4.2SC, AJ126 3.0SC V6,
AJ133 5.0 V8 family, AJ133S 5.0SC 550, 204PT 2.0 Si4). New: AJ27 4.0, AJ27S 4.0SC (DB-convention
code, AJ33S pattern - Wikipedia documents the 370hp Eaton-blown 4.0 without an official suffix),
204DTD 2.0 Ingenium diesel (20d), AJ300P 3.0 I6 MHEV (2021+ F-Pace P340/P400), I-Pace Electric.
US-market lineups web-verified: XE (Ford EcoBoost until 2017, diesel dropped 2020), XF X260
(20d 2017-19, P250/P300 only 2021+), F-Pace (20d/35t/S 2017; 25t 2018; 2021 = I6 MHEV replaces V6,
P250-only 2.0), X-Type (2.5 through 2004, 3.0-only 2005+). Skips: S-Type bare (V6-vs-V8 every year)
and X-Type 2002-04 bare (2.5-vs-3.0)."""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"

CIT = {
    "AJV8WIKI": "https://en.wikipedia.org/wiki/Jaguar_AJ-V8_engine (AJ26->AJ27 4.0 1998+ CVVT, NA 290hp XK8/XJ8; SC 370hp Eaton; AJ33 4.2 294hp 2003+; AJ33S SC 390hp, XKR/XJR/S-Type R 400hp; AJ126 3.0 SC V6 340/380hp; 5.0 family incl. NA 385 XK/XF, F-Type 495PS NA, SC 510/550/575)",
    "JAGCLUB": "https://en.jaguar-club.net/engine_detail.php?id=46 (AJ27 4.0 V8 3996cc from 1998; used on XJ X308 1999-2003 and XK X100 1999-2002)",
    "XEWIKI": "https://en.wikipedia.org/wiki/Jaguar_XE (2.0 Ford EcoBoost turbo until 2017, Ingenium petrol from 2018MY; 3.0 AJ126 V6 until 2019; 2.0 Ingenium diesel)",
    "XFWIKI": "https://en.wikipedia.org/wiki/Jaguar_XF_(X260) (US: P250 247hp standard, P300 296, P380 380 SC V6 S model)",
    "XF20D": "https://www.caranddriver.com/reviews/a15090527/2017-jaguar-xf-20d-awd-test-review/ + https://www.fueleconomy.gov/feg/bymodel/2017_Jaguar_XF.shtml (2017 XF 20d 2.0 Ingenium diesel 180hp US-standard engine)",
    "KBBXF18": "https://www.kbb.com/jaguar/xf/2018/ (2018 XF: 2.0 TD 180hp / 2.0T 247hp / 3.0 SC V6 340 and 380hp S)",
    "CD17FPACE": "https://www.caranddriver.com/reviews/a15095326/2017-jaguar-f-pace-35t-test-review/ + https://cars.usnews.com/cars-trucks/jaguar/f-pace/2017/specs (2017 F-Pace: 20d 2.0 TD 180 / 35t 340 SC V6 / S 380; 25t gas 2.0 added 2018)",
    "MT21FPACE": "https://www.motortrend.com/cars/jaguar/f-pace/2021 + https://consumerguide.com/jaguar/f-pace/ (2021: SC V6 replaced by 3.0 I6 MHEV P340 335hp / P400 395hp; 2.0 = P250 246hp only; SVR 5.0 SC V8 550hp; 2024 P550 542hp / 2025 P575 567hp per jaguarchesterfield.com)",
    "JDP21XF": "https://www.jdpower.com/cars/new-car-previews/2021-jaguar-xf-preview (2021 XF US: P250 246 / P300 296 turbo-four ONLY - no six, no diesel)",
    "CARS20XE": "https://www.cars.com/articles/2020-jaguar-xe-gets-updated-styling-drops-v-6-and-diesel-engines-1420757473811/ (2020 XE NA: V6 and diesel dropped; P250 247 / P300 296)",
    "CONCEPTCARZ18": "https://www.conceptcarz.com/a21945/ingenium-four-cylinder-engine-2018-jaguar-xe-xf-f-pace-models.aspx (18MY: 247hp 25t + new 296hp 30t Ingenium petrol for XE/XF/F-Pace)",
    "ENGINECODES": "https://www.enginecode.uk/jaguar + https://www.rangeroverenginespecialist.co.uk/blog/ingenium-engine-jlr-models-replacement-uk/ (Ingenium codes: 204PT petrol, 204DTD/D180 diesel; 306DT 3.0 V6 TD Lion)",
    "AJ300P": "https://enginefinders.co.uk/jaguar-land-rover-aj300p-petrol-engine + https://www.velocityap.com/product/jaguar-land-rover-3-0l-aj300-ingenium-ecu-tuning-2/ (AJ300P = 3.0 I6 Ingenium MHEV petrol P340/P360/P400; F-Pace P400)",
    "XTYPECG": "https://consumerguide.com/used/2002-08-jaguar-x-type/ + https://www.kbb.com/jaguar/x-type/2003/specs/ (X-Type 2.5 192hp + 3.0 227hp both sold through 2004; 2.5 dropped for 2005)",
    "CRAWL2015": "lemon_crawl_2015.jsonl Jaguar dirs (F-Type Base 3.0 VIN 7/T = 340hp, S VIN C/U = 380hp, R = 5.0 SC; XF 2.0T Premium oil 5.39L = Ford GTDI; XF/XJ Supercharged 5.0 VIN E/P/T; XFR VIN C/H; XJ 3.0 VIN 7/Z RWD + D AWD)",
    "DBLINKS": "DB Jaguar vocabulary rows reused: AJ25 (2.5 V6 197), AJ30 (3.0 V6 235, X-Type 227), AJ34 (4.2 V8 294), AJ33S (4.2 SC 390), AJ126 (3.0 SC V6 335), AJ133 (5.0 V8 542 family), AJ133S (5.0 SC 551), 204PT (2.0 16v T Si4 237)",
}

NEW_ENGINES = {
    "AJ27": ("4.0 V8 AJ-V8 NA (XK8/XJ8/S-Type 4.0 2000-03, 290hp)", "Petrol", 3996, 290, 8),
    "AJ27S": ("4.0 V8 AJ-V8 Supercharged (XKR/XJR 2000-03, 370hp Eaton)", "Petrol", 3996, 370, 8),
    "204DTD": ("2.0 I4 Ingenium Turbo Diesel (20d/D180, 180hp US; 163-180hp family)", "Diesel", 1999, 180, 4),
    "AJ300P": ("3.0 I6 Ingenium MHEV twin-turbo + e-supercharger (P340 335hp / P400 395hp)", "Petrol", 2996, 395, 6),
    "I-Pace Electric": ("Electric motors dual (I-Pace, 394hp)", "Electric", None, 394, None),
}

ROW_FIXES = {
    "AJ133": {"engine_type": "5.0 V8 AJ-V8 Gen III (NA 380-385hp XK/XF/XJ/F-Type 495; SC 510/550/575 R/XFR/XKR/SVR)"},
    "AJ133S": {"engine_type": "5.0 V8 Supercharged (XKR-S/XFR-S/XJR 550hp; XJR575 575hp; F-Type SVR)"},
    "AJ126": {"engine_type": "3.0 V6 Supercharged (340/380hp US 335/375; XE/XF/XJ/F-Type/F-Pace)"},
    "AJ33S": {"engine_type": "4.2 V8 Supercharged (390-420hp: S-Type R/XKR/XJR/SV8)"},
    "AJ34": {"engine_type": "4.2 V8 NA (294-300hp: XK8/XJ8/XF/S-Type 4.2)"},
    "AJ30": {"engine_type": "3.0 V6 AJ-V6 Duratec-derived (S-Type 235hp / X-Type 227hp)"},
    "204PT": {"engine_type": "2.0 I4 Turbo Si4 (Ford GTDI 240hp 2012-17 / Ingenium P250 247hp, P300 296hp 2018+)"},
}

FUEL_FIX_BY_TARGET = {"204DTD": "Diesel", "I-Pace Electric": "Electric"}

# (MODEL-upper, y0, y1, cc, vins-or-None, target, evidence, pfix)  cc=None = bare; vins=set() = no-vin page
R = [
    # E-Pace: US = 2.0 Ingenium petrol only (P250 246hp; P300 296hp from 2019); no PHEV in US
    ("E-PACE", 2018, 2024, None, None, "204PT", "US E-Pace 2.0 petrol only (P250 246hp; P300 296hp 2019+) [MT21FPACE-era lineup]", 246),
    # F-Pace 2.0: N = 20d diesel; X = 25t/P250 petrol; bare = remaining 2.0 (30t 296 by elimination 2018-19, P250 2021+)
    ("F-PACE", 2017, 2019, 2000, {"N"}, "204DTD", "F-Pace 20d 2.0 Ingenium diesel 180hp (VIN N = JLR diesel; US News 2017 20d) [CD17FPACE]", 180),
    ("F-PACE", 2018, 2019, 2000, {"X"}, "204PT", "F-Pace 25t 2.0 Ingenium petrol 247hp (VIN X; 2021+ X rows = P250-only year) [CONCEPTCARZ18][MT21FPACE]", 247),
    ("F-PACE", 2021, 2025, 2000, {"X"}, "204PT", "F-Pace P250 2.0 Ingenium petrol 246hp (2021+ four = P250 only) [MT21FPACE]", 246),
    ("F-PACE", 2018, 2019, 2000, None, "204PT", "F-Pace 2.0 petrol 30t 296hp (2018-19: N=diesel, X=P250, bare=30t by elimination) [CONCEPTCARZ18]", 296),
    ("F-PACE", 2020, 2020, 2000, None, "204PT", "F-Pace 2.0 petrol 247/296hp (US diesels gone 2020) [CARS20XE-era]", 247),
    ("F-PACE", 2021, 2023, 2000, None, "204PT", "F-Pace P250 2.0 petrol 246hp only (2021+) [MT21FPACE]", 246),
    # F-Pace 3.0: 2017-2020 SC V6 (35t 340 / S 380); 2021+ I6 MHEV (P340 335 / P400 395)
    ("F-PACE", 2017, 2020, 3000, None, "AJ126", "F-Pace 35t 3.0 SC V6 340hp (S 380hp minority) [CD17FPACE][KBBXF18 analogy]", 340),
    ("F-PACE", 2021, 2025, 3000, None, "AJ300P", "F-Pace 3.0 I6 MHEV P340 335 / P400 395hp (replaced SC V6 2021) [MT21FPACE][AJ300P]", None),
    # F-Pace 5.0: SVR only
    ("F-PACE", 2019, 2023, 5000, None, "AJ133S", "F-Pace SVR 5.0 SC V8 550hp [MT21FPACE]", 550),
    ("F-PACE", 2024, 2024, 5000, None, "AJ133S", "F-Pace P550 SVR 5.0 SC V8 542hp (2024) [MT21FPACE]", 542),
    ("F-PACE", 2025, 2025, 5000, None, "AJ133S", "F-Pace P575 SVR 5.0 SC V8 567hp (2025) [MT21FPACE]", 567),
    # F-Type: V6 3.0 SC (letters 6/7/T = base 340; C/U/V = S 380); 2.0 P300; 5.0 V8
    ("F-TYPE", 2018, 2021, 2000, None, "204PT", "F-Type P300 2.0 Ingenium petrol 296hp (2018+) [XEWIKI-era]", 296),
    ("F-TYPE", 2014, 2021, 3000, None, "AJ126", "F-Type 3.0 SC V6 (base 340 / S 380 / 400 Sport) [AJV8WIKI][CRAWL2015]", 340),
    ("F-TYPE", 2014, 2014, 5000, None, "AJ133", "F-Type V8 S 5.0 NA 495hp (2014) [AJV8WIKI]", 495),
    ("F-TYPE", 2015, 2017, 5000, None, "AJ133", "F-Type R 5.0 SC 550hp [AJV8WIKI]", 550),
    ("F-TYPE", 2018, 2021, 5000, None, "AJ133", "F-Type R 5.0 SC 575hp (2018 facelift) [AJV8WIKI]", 575),
    ("F-TYPE", 2022, 2024, None, None, "AJ133", "F-Type 5.0 SC (P450 444hp base; R 575hp) [AJV8WIKI]", 444),
    # I-Pace: EV only
    ("I-PACE", 2019, 2024, None, None, "I-Pace Electric", "I-Pace EV only (dual motor 394hp) [NEW][fuel fix Electric]", 394),
    # X-Type: 3.0-only from 2005 (2.5 sold 2002-04 -> skipped in decide)
    ("X-TYPE", 2005, 2008, None, None, "AJ30", "US X-Type 3.0 V6 only from 2005 (2.5 dropped) [XTYPECG]", 227),
    # XFR-S / XKR-S / XKR175 / XJR575
    ("XFR-S", 2013, 2015, None, None, "AJ133S", "XFR-S 5.0 SC 550hp [AJV8WIKI]", 550),
    ("XKR-S", 2012, 2015, None, None, "AJ133S", "XKR-S 5.0 SC 550hp [AJV8WIKI]", 550),
    ("XKR175", 2011, 2011, None, None, "AJ133", "XKR175 5.0 SC 510hp limited edition [AJV8WIKI]", 510),
    ("XJR575", 2018, 2019, None, None, "AJ133S", "XJR575 5.0 SC 575hp [AJV8WIKI]", 575),
    # XJ8 eras: X308 4.0 NA / X350 4.2 / X358 4.2 300hp
    ("XJ8", 2000, 2003, None, None, "AJ27", "XJ8 X308 4.0 V8 NA 290hp [AJV8WIKI][JAGCLUB]", 290),
    ("XJ8", 2004, 2007, None, None, "AJ34", "XJ8 X350 4.2 V8 NA 294hp [AJV8WIKI]", 294),
    ("XJ8", 2008, 2009, None, None, "AJ34", "XJ8 X358 4.2 V8 NA 300hp [AJV8WIKI]", 300),
    # XJR eras: X308 4.0 SC 370 / X350-X358 4.2 SC 400 / X351 5.0 SC 550
    ("XJR", 2000, 2003, None, None, "AJ27S", "XJR X308 4.0 SC 370hp Eaton [AJV8WIKI][NEW AJ27S]", 370),
    ("XJR", 2004, 2009, None, None, "AJ33S", "XJR X350/X358 4.2 SC 400hp [AJV8WIKI]", 400),
    ("XJR", 2014, 2017, None, None, "AJ133S", "XJR X351 5.0 SC 550hp [AJV8WIKI]", 550),
    # XK8 eras: X100 4.0 / X100 4.2 / X150 4.2 300hp
    ("XK8", 2000, 2002, None, None, "AJ27", "XK8 X100 4.0 V8 NA 290hp [AJV8WIKI][JAGCLUB]", 290),
    ("XK8", 2003, 2006, None, None, "AJ34", "XK8 X100 4.2 V8 NA 294hp (2003+) [AJV8WIKI]", 294),
    ("XK8", 2007, 2009, None, None, "AJ34", "XK X150 4.2 V8 NA 300hp [AJV8WIKI]", 300),
    # XKR eras: 4.0 SC 370 / 4.2 SC 390-400 / X150 4.2 SC 420 / 5.0 SC 510
    ("XKR", 2000, 2002, None, None, "AJ27S", "XKR X100 4.0 SC 370hp [AJV8WIKI][NEW AJ27S]", 370),
    ("XKR", 2003, 2006, None, None, "AJ33S", "XKR X100 4.2 SC 390-400hp [AJV8WIKI]", 400),
    ("XKR", 2007, 2009, None, None, "AJ33S", "XKR X150 4.2 SC 420hp [AJV8WIKI]", 420),
    ("XKR", 2010, 2015, None, None, "AJ133", "XKR 5.0 SC 510hp [AJV8WIKI]", 510),
    # XE: G = 2017 Ford EcoBoost 25t; N = 20d diesel; X = 25t/P250; bare 2019 = 30t
    ("XE", 2017, 2017, 2000, {"G"}, "204PT", "XE 25t 2.0 Ford EcoBoost GTDI (Si4) 240hp - Ford until 2017 [XEWIKI]", 240),
    ("XE", 2017, 2019, 2000, {"N"}, "204DTD", "XE 20d 2.0 Ingenium diesel 180hp (diesel dropped 2020) [XEWIKI][CARS20XE]", 180),
    ("XE", 2018, 2019, 2000, {"X"}, "204PT", "XE 25t 2.0 Ingenium petrol 247hp (2018+) [XEWIKI][CONCEPTCARZ18]", 247),
    ("XE", 2019, 2019, 2000, None, "204PT", "XE 2.0 petrol 30t 296hp (2019: N=diesel, X=P250, bare=30t by elimination) [CONCEPTCARZ18]", 296),
    ("XE", 2020, 2020, None, None, "204PT", "XE 2020: P250 247 / P300 296 only (V6+diesel dropped NA) [CARS20XE]", 247),
    ("XE", 2017, 2019, 3000, None, "AJ126", "XE 35t 3.0 SC V6 340hp (XE S 380hp from 2018) [XEWIKI]", 340),
    # XF X250: 4.2 NA 300 / 5.0 NA 385 / Supercharged 470 / 2.0T Ford 240
    ("XF", 2009, 2009, None, None, "AJ34", "XF X250 launch 4.2 NA 300hp (SV8 420hp minority) [AJV8WIKI]", 300),
    ("XF", 2010, 2010, 4200, None, "AJ34", "XF 4.2 NA 300hp base 2010 [AJV8WIKI]", 300),
    ("XF", 2010, 2012, 5000, None, "AJ133", "XF 5.0 NA 385hp base (Supercharged 470hp minority) [AJV8WIKI]", 385),
    ("XF", 2013, 2015, 5000, None, "AJ133", "XF Supercharged 5.0 SC 470hp (2013-15 trim, crawl 2015) [CRAWL2015]", 470),
    ("XF", 2013, 2015, 2000, None, "204PT", "XF 2.0T Ford EcoBoost GTDI (Si4) 240hp (oil 5.39L crawl) [XFWIKI-era][CRAWL2015]", 240),
    # XF X260: 2016 3.0 340 only; 2017-19 + 20d diesel; 2020 gas-only; 2021+ P250/P300 four only
    ("XF", 2016, 2016, None, None, "AJ126", "XF X260 2016 US launch 3.0 SC V6 340hp only [XFWIKI]", 340),
    ("XF", 2017, 2019, 2000, {"N"}, "204DTD", "XF 20d 2.0 Ingenium diesel 180hp (US 2017-19) [XF20D]", 180),
    ("XF", 2019, 2019, 2000, {"X"}, "204PT", "XF 25t 2.0 petrol 247hp [KBBXF18][CONCEPTCARZ18]", 247),
    ("XF", 2019, 2019, 2000, None, "204PT", "XF 2.0 petrol 30t 296hp (2019: N=diesel, X=P250, bare=30t by elimination) [CONCEPTCARZ18]", 296),
    ("XF", 2020, 2020, 2000, None, "204PT", "XF 2.0 petrol 247/296hp (US diesel gone 2020) [CARS20XE-era]", 247),
    ("XF", 2021, 2024, None, None, "204PT", "XF P250 246 / P300 296 turbo-four only (2021+) [JDP21XF]", 246),
    ("XF", 2013, 2020, 3000, None, "AJ126", "XF 3.0 SC V6 340hp (S 380hp from 2018) [KBBXF18][XFWIKI]", 340),
    # XFR (all 5000cc-ish rows 2010-2015 incl VIN C/H)
    ("XFR", 2010, 2012, 5000, None, "AJ133", "XFR 5.0 SC 510hp [AJV8WIKI]", 510),
    ("XFR", 2013, 2014, None, None, "AJ133", "XFR 5.0 SC 510hp [AJV8WIKI]", 510),
    ("XFR", 2015, 2015, 5000, None, "AJ133", "XFR 5.0 SC 510hp (VIN C/H crawl) [CRAWL2015]", 510),
    # XJ: 2002-03 X308 4.0 NA (XJR separate); 2010-12 5.0 NA 385 base; 2013-19 3.0 SC 340 / 5.0 SC 470
    ("XJ", 2002, 2003, None, None, "AJ27", "XJ X308 4.0 NA 290hp non-R (XJR rows separate) [AJV8WIKI][JAGCLUB]", 290),
    ("XJ", 2010, 2012, None, None, "AJ133", "XJ X351 5.0 NA 385hp base (Supercharged 470/Supersport 510 minority) [AJV8WIKI]", 385),
    ("XJ", 2013, 2019, 3000, None, "AJ126", "XJ 3.0 SC V6 340hp (VIN 7/Z RWD, D AWD) [CRAWL2015][AJV8WIKI]", 340),
    ("XJ", 2013, 2019, 5000, None, "AJ133", "XJ Supercharged 5.0 SC 470hp (VIN E/T crawl; Supersport 510 minority) [CRAWL2015]", 470),
    # XK 2010-2015: 5.0 NA only (XKR separate)
    ("XK", 2010, 2015, None, None, "AJ133", "XK 5.0 NA 385hp (XKR separate) [AJV8WIKI]", 385),
]

def decide(model, year, code, fuel):
    parts = code.replace("LEMON_JAGUAR_", "").split("_")
    segs = [p for p in parts[1:] if p != str(year)]
    cc, vin = None, None
    for s in segs:
        m = re.match(r"^(\d+)CC$", s)
        if m and int(m.group(1)) > 0: cc = int(m.group(1))
        if s.startswith("VIN") and len(s) > 3: vin = s[3:]
    mu = model.upper()
    # known-ambiguous bare rows -> skip
    if mu == "S-TYPE":
        return (None, f"S-Type {year} bare: 3.0 V6 (AJ30) vs 4.0/4.2 V8 both US-offered, no engine marker", None, None)
    if mu == "X-TYPE" and 2002 <= year <= 2004:
        return (None, f"X-Type {year} bare: 2.5 (AJ25) vs 3.0 (AJ30) both US-offered through 2004 [XTYPECG]", None, None)
    cands = [r for r in R if r[0] == mu and r[1] <= year <= r[2] and r[3] == cc
             and (r[4] is None or (vin is not None and vin in r[4]))]
    if not cands:
        return (None, f"no rule for {model} {year} cc={cc} vin={vin}", None, None)
    # prefer VIN-letter-specific rules over bare rules
    cands.sort(key=lambda r: 0 if r[4] is not None else 1)
    r = cands[0]
    if r[4] is not None and vin is None and any(x[4] is None and x[0] == mu and x[1] <= year <= x[2] and x[3] == cc for x in R):
        pass  # bare rule exists but this row HAS a vin not covered by a specific rule; still use bare rule
    pfix = r[7]
    # F-Type V6 tune by letter (crawl-verified trims)
    if mu == "F-TYPE" and cc == 3000 and vin in ("C", "U", "V"):
        pfix = 380
    fuel_fix = FUEL_FIX_BY_TARGET.get(r[5])
    return (r[5], r[6], fuel_fix, pfix)

def main():
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == 3781, f"BASELINE MISMATCH: LEMON={base_lemon}, expected 3781 (workspace rewind?)"
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand='Jaguar' AND engine_code LIKE 'LEMON_JAGUAR%' ORDER BY car_model, car_year, engine_code""").fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        tgt, note, fuel_fix, pfix = decide(model, year, code, fuel)
        if tgt is None: skips.append((vid, model, year, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix, pfix))
    print(f"Jaguar LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    for s in skips: print("  SKIP:", s[1], s[2], "-", s[3])
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(20): print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter(d[6] for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"

    if not apply:
        with open("database_enriched/csv_exports/33_lemon_batch16_decisions_DRYRUN.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
            for d in decisions: w.writerow([d[0],"Jaguar",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
            for s in skips: w.writerow([s[0],"Jaguar",s[1],s[2],"","","","SKIP",s[3]])
        print("\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step25_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP25_VERIFIED')""",
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

    with open("database_enriched/csv_exports/33_lemon_batch16_decisions.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","power_fill","evidence"])
        for d in decisions: w.writerow([d[0],"Jaguar",d[1],d[2],d[3],d[4],d[6] or "",d[7] if d[7] else "",d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print("LEMON_JAGUAR remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_JAGUAR%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    con.close()

if __name__ == "__main__":
    main()
