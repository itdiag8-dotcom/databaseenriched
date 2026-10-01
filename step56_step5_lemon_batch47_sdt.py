"""Step 56 (Step 5, batch 47): Smart + Tesla + Daewoo LEMON replacement — 31 rows.

Three small brands with no overlap in hardware, batched together because each is a handful of
rows and because they pose the same question in three different forms: what do you do when the
crawl's model name has lost the information you need?

- **Smart** keeps its information. One nameplate, one engine per generation, and the fill tracks
  the generation change: 3.31-3.4 L through the 451 (1.0 three-cylinder, 70hp US) and 3.59 L
  from 2016, the 453's 0.9 turbo (89hp). The MY2015 `FORTWOELECTR` trim row is the Electric
  Drive and is corrected from Petrol to Electric.
- **Daewoo** keeps its information too: Lanos, Nubira and Leganza each had exactly one US
  engine, and their fills (3.78 / 3.88-3.97 / 3.97 L) are consistent with the 1.6, the 2.0 and
  the 2.2 respectively.
- **Tesla** has lost it entirely. Every Model S, 3, X and Y truncates to `MODEL`, there is no
  displacement, no fill, no VIN, and one row per year - the crawl itself could not keep the four
  cars apart. What *is* knowable is that every Tesla ever built is battery-electric, and that is
  what these rows are given: a single explicit `BEV (Tesla, model unidentified)` engine with the
  fuel corrected from Petrol to Electric and power deliberately left NULL rather than invented.
  That is a smaller claim than the LEMON placeholders made, and unlike them it is true.
"""
import step5_lemon_lib as lib

CIT = {
    "SMARTUS": "smart USA: ForTwo 451 (2008-2015) 1.0 I3 naturally aspirated 70hp; ForTwo Electric Drive 2015 74hp; ForTwo 453 (2016-2017) 0.9 I3 turbo 89hp",
    "DAEWOOUS": "Daewoo Motor America 2000-2002: Lanos 1.6 DOHC 105hp; Nubira 2.0 DOHC 129hp; Leganza 2.2 DOHC 131hp - one engine per nameplate",
    "TESLABEV": "Every Tesla model is battery-electric; the crawl's 'MODEL' code cannot distinguish Model S, 3, X or Y, and carries no displacement, fill or VIN",
    "LEMONFILL": "Oil fill recorded by the crawl: Smart 3.31-3.4 L (451 1.0) stepping to 3.59 L (453 0.9 turbo); Daewoo 3.78 L (Lanos 1.6), 3.88-3.97 L (Nubira 2.0), 3.97 L (Leganza 2.2)",
}

SMART_ED = "Electric Drive (smart ForTwo ED)"
TESLA_BEV = "BEV (Tesla, model unidentified)"
X22SE = "X22SE"

NE = {
    SMART_ED: ("Battery-electric drive unit, 17.6 kWh (smart ForTwo Electric Drive 451, 74hp)", "Electric", None, 74, None),
    TESLA_BEV: ("Battery-electric drive unit - Tesla Model S/3/X/Y, not distinguishable from the crawl's truncated 'MODEL' code; power varies by model and trim and is left NULL rather than invented", "Electric", None, None, None),
    X22SE: ("2.2 I4 DOHC 16v Family II X22SE (Leganza US 2000-2002, 131hp)", "Petrol", 2198, 131, 4),
}

R = [
    ("SMART:FORTWO", 2008, 2015, None, None, "M132.910", "ForTwo 451 (2008-2015) = the 1.0 three-cylinder, 70hp US; 3.31-3.4 L fill [SMARTUS][LEMONFILL]", 70),
    ("SMART:FORTWO", 2016, 2017, None, None, "M281.910", "ForTwo 453 (2016-2017) = the 0.9 turbo three, 89hp; the fill steps to 3.59 L with the new generation [SMARTUS][LEMONFILL]", 89),
    ("TESLA:MODEL", 2016, 2025, None, None, TESLA_BEV, "Tesla 'MODEL' rows: the crawl truncated Model S/3/X/Y to one code and kept one row per year, so the car cannot be identified - but every Tesla is battery-electric, so the row is mapped to an explicit BEV engine with the fuel corrected from Petrol to Electric and power left NULL [TESLABEV]", None),
    ("DAEWOO:LANOS", 2000, 2002, None, None, "A16DMS", "Lanos US 2000-2002 = the 1.6 DOHC, 105hp, its only US engine; 3.78 L fill [DAEWOOUS][LEMONFILL]", 105),
    ("DAEWOO:NUBIRA", 2000, 2002, None, None, "X20SED", "Nubira US 2000-2002 = the 2.0 DOHC Family II, 129hp, its only US engine [DAEWOOUS][LEMONFILL]", 129),
    ("DAEWOO:LEGANZA", 2000, 2002, None, None, X22SE, "Leganza US 2000-2002 = the 2.2 DOHC Family II, 131hp, its only US engine [DAEWOOUS][LEMONFILL]", 131),
]

_451 = "ForTwo 451 MY2015 trim row = the 1.0 three-cylinder, 70hp [SMARTUS][LEMONFILL]"
TRIM = {
    ("FORTWO", 2015, "FORTWOELECTR"): (SMART_ED, "ForTwo Electric Drive MY2015 = the 17.6 kWh battery-electric drivetrain, 74hp; fuel corrected from Petrol to Electric [SMARTUS]", 74, "Electric"),
    ("FORTWO", 2015, "FORTWOPASSIO"): ("M132.910", _451, 70, None),
    ("FORTWO", 2015, "FORTWOPURE"): ("M132.910", _451, 70, None),
}

IDENTITY = {
    "M132.910": ("Petrol", 999), "M281.910": ("Petrol", 898),
    "A16DMS": ("Petrol", 1598), "X20SED": ("Petrol", 1998),
}

ROW_FIXES = {
    "M132.910": {"engine_type": "1.0 I3 M132 naturally aspirated (ForTwo 451, 70hp US / 61-71hp EU)",
                 "cylinders": 3, "data_confidence": "STEP56_VERIFIED"},
    "M281.910": {"engine_type": "0.9 I3 Turbo M281 (ForTwo/ForFour 453, 89-90hp)",
                 "cylinders": 3, "data_confidence": "STEP56_VERIFIED"},
    "A16DMS": {"engine_type": "1.6 I4 DOHC 16v A16DMS (Lanos/Nubira, 105hp US)",
               "cylinders": 4, "data_confidence": "STEP56_VERIFIED"},
    "X20SED": {"engine_type": "2.0 I4 DOHC 16v Family II X20SED (Nubira/Leganza US, 129hp)",
               "cylinders": 4, "data_confidence": "STEP56_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand=["Smart", "Tesla", "Daewoo"], step_tag="step56", csv_num=64,
    lemon_baseline=71, engines_baseline=5725,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={TESLA_BEV: "Electric", SMART_ED: "Electric"},
    expect_mapped=31, expect_skipped=0,
))
