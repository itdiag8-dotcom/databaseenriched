"""Step 47 (Step 5, batch 38): Saab LEMON replacement — 34 rows.

By the years this batch covers, "Saab" was three different engineering teams: Trollhattan's own
9-3 and 9-5, two badge-engineered GM products (9-7X = TrailBlazer, 9-4X = Cadillac SRX) and one
badge-engineered Subaru (9-2X = Impreza). The displacement tokens and the crawl's oil fills keep
the three apart — 3.97 L on the Subaru boxers, 3.88 L on the Saab B235, 5.96-6.38 L on the B207,
and the familiar GM 5.67 / 6.62 L on the 9-7X.

| Rows | Target | hp |
|---|---|---|
| 9-2X 2000CC 2005 | `EJ205` 2.0 boxer turbo (9-2X Aero) | 227 |
| 9-2X 2500CC 2005 | `EJ253` 2.5 boxer SOHC (9-2X Linear) | 165 |
| 9-2X 2006 (bare) | `EJ253`, volume default — see below | 173 |
| 9-3 2000CC 2005-2008, 9-3 and 9-3X 2011-2012 | `B207R US` 2.0 turbo | 210 |
| 9-3 2800CC 2006-2007 / 2008 | `B284L EU/RW/US` 2.8 V6 turbo (Aero) | 250 / 255 |
| 9-4X 2011 | `LF1` 3.0 V6 DI (9-4X 3.0i) | 265 |
| 9-5 2005-2008 | new `B235E US (9-5 2.3T, 220hp)` | 220 |
| 9-5 2011 | `A20NHT` 2.0 turbo (Insignia-based 9-5) | 220 |
| 9-7X 4200CC 2005 / 2006-2009 | `LL8` 4.2 I6 Atlas | 275 / 291 |
| 9-7X 5300CC 2005-2009 | `LH6` 5.3 V8 with Displacement on Demand | 300 |
| 9-7X 6000CC 2008-2009 | `LS2` 6.0 V8 (9-7X Aero) | 390 |

**Volume defaults (2).** The MY2006 9-2X row has no displacement token and both of that year's
cars are 2.5-litre - Linear (EJ253, 173hp) and Aero (EJ255 turbo, 230hp) - so it takes the
higher-volume Linear engine. The 9-4X 2011 row is likewise the volume 3.0i rather than the
Aero 2.8T. Both are flagged in the decision CSV.
"""
import step5_lemon_lib as lib

CIT = {
    "SAABUS": "Saab US model-year specifications: 9-2X Aero 2.0 turbo 227hp and Linear 2.5 165hp (2005), both cars 2.5-litre for 2006 (Linear 173hp, Aero 2.5 turbo 230hp); 9-3 2.0T 210hp throughout 2003-2012 including the 9-3X; 9-3 Aero 2.8 V6 turbo 250hp (2006-2007) and 255hp (2008); 9-4X 3.0i 265hp with an Aero 2.8T 300hp above it; 9-5 2.3T 220hp (2005-2009) with the Aero at 260hp; new 9-5 2.0T 220hp (2010-2011); 9-7X 4.2 I6 275hp (2005) then 291hp, 5.3 V8 300hp, and the 9-7X Aero 6.0 V8 390hp (2008-2009)",
    "LEMONFILL": "Oil fill recorded by the crawl per row: 3.97 L on the 9-2X (Subaru boxer), 3.88 L on the 9-5 2.3T (Saab B235), 5.96-6.38 L on the 9-3 B207/B284, 5.67 L on the 9-4X, the new 9-5 and the GM V8s, 6.62 L on the 9-7X 4.2 I6",
}

B207 = "B207R US"
B284 = "B284L EU/RW/US"
B235US = "B235E US (9-5 2.3T, 220hp)"

NE = {
    B235US: ("2.3 I4 16v Turbo (US 9-5 2.3t/2.3T Linear-Arc-Aero base tune, 220hp)",
             "Petrol", 2290, 220, 4),
}

R = [
    ("9-2X", 2005, 2005, 2000, None, "EJ205", "9-2X Aero 2005 = the WRX's EJ205 2.0 boxer turbo, 227hp in Saab tune; 3.97 L fill is the Subaru boxer [SAABUS][LEMONFILL]", 227),
    ("9-2X", 2005, 2005, 2500, None, "EJ253", "9-2X Linear 2005 = EJ253 2.5 SOHC boxer, 165hp [SAABUS][LEMONFILL]", 165),
    ("9-2X", 2006, 2006, None, None, "EJ253", "9-2X MY2006 has no displacement token and both cars are 2.5-litre (Linear EJ253 173hp, Aero EJ255 turbo 230hp); VOLUME DEFAULT to the Linear's EJ253, 173hp [SAABUS]", 173),
    ("9-3", 2005, 2008, 2000, None, B207, "9-3 2.0T = B207R in US tune, 210hp, the volume engine of the car [SAABUS][LEMONFILL]", 210),
    ("9-3", 2006, 2007, 2800, None, B284, "9-3 Aero 2.8 V6 turbo (B284L), 250hp [SAABUS]", 250),
    ("9-3", 2008, 2008, 2800, None, B284, "9-3 Aero 2.8 V6 turbo MY2008 uprated to 255hp [SAABUS]", 255),
    ("9-3", 2011, 2012, None, None, B207, "9-3 2011-2012 = the same B207R 2.0 turbo, 210hp; Saab built no other US 9-3 engine in its last two years [SAABUS]", 210),
    ("9-3", 2011, 2012, 2000, None, B207, "9-3 2.0L 2012 (VIN R and VIN Z emissions variants) = B207R 2.0 turbo, 210hp [SAABUS]", 210),
    ("9-3X", 2011, 2012, None, None, B207, "9-3X = the lifted XWD 9-3 wagon, 2.0T B207R, 210hp [SAABUS]", 210),
    ("9-4X", 2011, 2011, None, None, "LF1", "9-4X 2011 = Cadillac SRX twin; VOLUME DEFAULT to the 3.0i's LF1 3.0 V6 direct-injection, 265hp, over the Aero 2.8T; 5.67 L fill [SAABUS][LEMONFILL]", 265),
    ("9-5", 2005, 2008, None, None, B235US, "9-5 2005-2008 = the 2.3T B235 in its 220hp base tune (the Aero ran 260hp); 3.88 L fill is the Saab 2.3, not a GM engine [SAABUS][LEMONFILL]", 220),
    ("9-5", 2011, 2011, None, None, "A20NHT", "9-5 2011 = the Insignia-based second-generation car: A20NHT 2.0 turbo, 220hp US; 5.67 L fill [SAABUS][LEMONFILL]", 220),
    ("9-7X", 2005, 2005, 4200, None, "LL8", "9-7X 4.2 MY2005 = LL8 I6 Atlas, 275hp; 6.62 L fill [SAABUS][LEMONFILL]", 275),
    ("9-7X", 2006, 2009, 4200, None, "LL8", "9-7X 4.2 MY2006-2009 = LL8 I6 Atlas uprated to 291hp [SAABUS][LEMONFILL]", 291),
    ("9-7X", 2005, 2009, 5300, None, "LH6", "9-7X 5.3 V8 = LH6 Vortec 5300 with Displacement on Demand, 300hp; 5.67 L fill [SAABUS][LEMONFILL]", 300),
    ("9-7X", 2008, 2009, 6000, None, "LS2", "9-7X Aero 2008-2009 = the 6.0 V8 LS2, 390hp in this application [SAABUS]", 390),
]

IDENTITY = {
    "EJ205": ("Petrol", 1994), "EJ253": ("Petrol", 2500), B207: ("Petrol", 2000),
    B284: ("Petrol", 2800), "LF1": ("Petrol", 2997), "A20NHT": ("Petrol", 2000),
    "LL8": ("Petrol", 4157), "LH6": ("Petrol", 5328), "LS2": ("Petrol", 5967),
}

ROW_FIXES = {
    "A20NHT": {"engine_type": "2.0 I4 Turbo ecoFLEX A20NHT (Insignia/Regal GS 220-250hp; Saab 9-5 2.0T 220hp US)",
               "cylinders": 4, "data_confidence": "STEP47_VERIFIED"},
    B207: {"engine_type": "2.0 I4 16v Turbo B207R, US tune (9-3 2.0T / 9-3X, 210hp)",
           "power_hp": 210, "data_confidence": "STEP47_VERIFIED"},
    B284: {"engine_type": "2.8 V6 24v Turbo B284L (9-3 Aero, 250hp US / 255hp from 2008)",
           "power_hp": 250, "data_confidence": "STEP47_VERIFIED"},
    "LS2": {"engine_type": "6.0 V8 OHV LS2 (GTO/Corvette 400 / TrailBlazer SS 395 / Saab 9-7X Aero 390hp)",
            "data_confidence": "STEP47_VERIFIED"},
    "LF1": {"engine_type": "3.0 V6 DI (LF1: LaCrosse 255 / CTS 270 / SRX and Saab 9-4X 265hp)",
            "data_confidence": "STEP47_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Saab", step_tag="step47", csv_num=55,
    lemon_baseline=367, engines_baseline=6014,
    R=R, NEW_ENGINES=NE, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    expect_mapped=34, expect_skipped=0,
))
