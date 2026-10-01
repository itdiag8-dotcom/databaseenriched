"""Step 45 (Step 5, batch 36): Audi LEMON replacement — 39 rows (31 mapped, 8 documented skips).

The Audi rows are bare nameplate+year with only three displacement tokens, so the decode leans on
a second signal the other batches have not used: **the oil fill volume the crawl recorded for each
row**, which separates Audi's engine families cleanly because the longitudinal 2.0 TFSI takes
4.6-4.7 L, the transverse MQB 2.0 TFSI 5.7 L, the 3.2 FSI V6 6.2-6.5 L, the supercharged 3.0 TFSI
6.8 L, the EA839 3.0 V6 7.6 L and the V8s 8.7-9.7 L.

| Rows | Crawl fill | Decode |
|---|---|---|
| A3 2016-2017, TT 2016-2017 | 5.5-5.7 L | MQB transverse **2.0 TFSI EA888 Gen3**, 220hp (new row) |
| A4 1800CC 2006 | 4.06 L | `AMB` 1.8T 20v, 170hp |
| A4 3000CC 2006 | 6.43 L | `AVK` 3.0 V6, 220hp (the A4 Cabriolet kept the 3.0 V6 into MY2006) |
| A5 2009 | 6.52 L | `CALA` 3.2 FSI V6, 265hp — the A5's only US engine in 2009 |
| A6 2014-2015 | 4.63 L | `CNCD` longitudinal 2.0 TFSI, 220hp |
| A6 2016-2018 | 4.73 L | `CYMC` B9-generation 2.0 TFSI, 252hp |
| A6 2020-2025 | 7.57 L | **EA839 3.0 V6 TFSI (55 TFSI)**, 335hp (new row) — far too large a fill for the 2.0 |
| Q5 2010 | 6.24 L | `CALB` 3.2 FSI V6, 270hp (the 2.0T Q5 only arrived for 2011) |
| Q5 3000CC 2013 (×2) | 6.81 L | `CTUC` supercharged 3.0 TFSI, 272hp |
| S5 2017 | 6.81 L | `CTWA` supercharged 3.0 TFSI, 333hp (MY2017 S5 is still B8.5) |
| TT 2000-2003 | 4.54 L | `ATC` 1.8T 20v, 180hp (the 225hp car was the quattro Sport) |
| RS 2013-2014 | 9.65 L | `4.2 V8 FSI (RS4/RS5)` — RS 5, 450hp |
| RS 2016-2017 | 8.70 / 7.09 L | `CRDB` 4.0 V8 biturbo — RS 7, 560hp; both rows carry an RS 7 source URL |

**Skips (8).** `RS 2018`-`RS 2025` are left as LEMON rows: from MY2018 Audi sold between two and
six different RS models in the US every year (RS 3 2.5 I5, RS 5 2.9 V6 TT, RS 6/RS 7/RS Q8 4.0 V8
TT, RS e-tron GT electric), the crawl truncated the nameplate to "RS" with no displacement or VIN
token, and unlike the 2016-2017 rows these carry no source URL naming the model. The recorded
0W-30 / 7.1-7.6 L fill is shared by several of those engines, so there is no honest decode.
"""
import step5_lemon_lib as lib

CIT = {
    "AUDIUS": "Audi of America model-year specifications: A4 1.8T 170hp and A4 Cabriolet 3.0 V6 220hp (2006); A5 3.2 FSI 265hp (2008-2011, its only US engine); Q5 3.2 FSI 270hp (2009-2012) with the 2.0T added for 2011; Q5 3.0T supercharged 272hp (2013); A6 2.0T 220hp (2012-2015) then 252hp (2016-2018); A6 55 TFSI 3.0 V6 335hp (C8); A3/TT 2.0 TFSI quattro 220hp; S5 B8.5 3.0 TFSI supercharged 333hp; Mk1 TT 1.8T 180hp base / 225hp Sport; RS 5 4.2 FSI V8 450hp (2013-2015); RS 7 4.0 TFSI V8 560hp (2014-2018)",
    "LEMONFILL": "Oil fill volume recorded by the crawl for each row, which separates the families: longitudinal 2.0 TFSI 4.6-4.7 L, transverse MQB 2.0 TFSI 5.7 L, 3.2 FSI V6 6.2-6.5 L, supercharged 3.0 TFSI 6.8 L, EA839 3.0 V6 7.6 L, 4.0 V8 biturbo 8.7 L, 4.2 FSI V8 9.65 L",
    "LEMONURL": "engine_technical_specs.tech_source for LEMON_AUDI_RS_2016 and LEMON_AUDI_RS_2017 points at lemon.dogeware.me/Audi/<year>/RS 7 Base/..., naming the model behind those two rows",
}

MQB20 = "2.0 TFSI EA888 Gen3 (A3 8V / TT 8S, 220hp)"
V6TFSI = "3.0 V6 TFSI EA839 (55 TFSI, A6/A7 335hp)"
RS5V8 = "4.2 V8 FSI (RS4/RS5)"

NE = {
    MQB20: ("2.0 I4 Turbo TFSI EA888 Gen3, transverse MQB (A3 8V / TT 8S quattro, 220hp)",
            "Petrol", 1984, 220, 4),
    V6TFSI: ("3.0 V6 TFSI EA839 turbo (A6/A7 C8 '55 TFSI', 335hp US)", "Petrol", 2995, 335, 6),
}

R = [
    ("A3", 2016, 2017, None, None, MQB20, "A3 8V 2.0 TFSI quattro, 220hp; the 5.5-5.7 L fill the crawl records is the transverse MQB EA888, not the 4.6 L longitudinal engine [AUDIUS][LEMONFILL]", 220),
    ("TT", 2016, 2017, None, None, MQB20, "TT 8S quattro (source URL 'TT Quattro Base'): 2.0 TFSI 220hp, 5.67 L fill [AUDIUS][LEMONFILL]", 220),
    ("TT", 2000, 2003, None, None, "ATC", "Mk1 TT 1.8T 20v, 180hp base car (the 225hp version was the quattro Sport); 4.54 L fill [AUDIUS][LEMONFILL]", 180),
    ("A4", 2006, 2006, 1800, None, "AMB", "A4 B7 1.8T 20v, 170hp US; 4.06 L fill matches the 1.8T [AUDIUS][LEMONFILL]", 170),
    ("A4", 2006, 2006, 3000, None, "AVK", "A4 3.0L for MY2006 = the 3.0 V6 (AVK), 220hp, which the A4 Cabriolet carried into 2006 after the sedan moved to the 3.2 FSI; 6.43 L fill [AUDIUS][LEMONFILL]", 220),
    ("A5", 2009, 2009, None, None, "CALA", "A5 2009 = 3.2 FSI V6, 265hp - the only US A5 engine until the 2.0T arrived for 2010; 6.52 L fill [AUDIUS][LEMONFILL]", 265),
    ("A6", 2014, 2015, None, None, "CNCD", "A6 2.0 TFSI longitudinal, 220hp; 4.63 L fill is the longitudinal EA888, ruling out the 3.0 supercharged V6 [AUDIUS][LEMONFILL]", 220),
    ("A6", 2016, 2018, None, None, "CYMC", "A6 2.0 TFSI (B9-generation engine), 252hp from MY2016; 4.73 L fill [AUDIUS][LEMONFILL]", 252),
    ("A6", 2020, 2025, None, None, V6TFSI, "A6 C8 with a 7.57 L fill = the EA839 3.0 V6 TFSI '55 TFSI', 335hp; the 2.0 45 TFSI takes ~5.7 L, so these rows are the V6 [AUDIUS][LEMONFILL]", 335),
    ("Q5", 2010, 2010, None, None, "CALB", "Q5 2010 = 3.2 FSI V6, 270hp - the 2.0T Q5 only reached the US for MY2011; 6.24 L fill [AUDIUS][LEMONFILL]", 270),
    ("Q5", 2013, 2013, 3000, None, "CTUC", "Q5 3.0T 2013 = supercharged 3.0 TFSI, 272hp; 6.81 L fill [AUDIUS][LEMONFILL]", 272),
    ("Q5", 2013, 2013, 3000, "G", "CTUC", "Q5 3.0L VIN G 2013 = the same supercharged 3.0 TFSI, 272hp [AUDIUS][LEMONFILL]", 272),
    ("S5", 2017, 2017, None, None, "CTWA", "S5 MY2017 is still the B8.5 car: supercharged 3.0 TFSI, 333hp (the 2.9 V6 TT B9 S5 arrived for 2018); 6.81 L fill [AUDIUS][LEMONFILL]", 333),
    ("RS", 2013, 2014, None, None, RS5V8, "'RS' 2013-2014 = RS 5: the 4.2 FSI high-revving V8, 450hp. The 9.65 L fill is far above the 8.7 L of the 4.0 V8 biturbo and matches the 4.2 FSI, and the RS 5 was the only RS Audi sold in the US for 2013 [AUDIUS][LEMONFILL]", 450),
    ("RS", 2016, 2017, None, None, "CRDB", "'RS' 2016-2017 = RS 7: both rows carry a source URL under 'RS 7 Base', and the engine is the 4.0 TFSI V8 biturbo, 560hp in US tune [AUDIUS][LEMONURL]", 560),
]

_A6_15 = "A6 MY2015 Premium/Premium Plus = the 2.0 TFSI longitudinal, 220hp (4.63 L fill); the trim slug only separates equipment levels [AUDIUS][LEMONFILL]"
TRIM = {
    ("A6", 2015, "A6PREMIUM"): ("CNCD", _A6_15, 220, None),
    ("A6", 2015, "A6PREMIUMPLU"): ("CNCD", _A6_15, 220, None),
}

_RSAMB = ("bare 'RS' nameplate: from MY2018 Audi sold 2-6 different RS models in the US each year "
          "(RS 3 2.5 I5 400hp, RS 5 2.9 V6 TT 444hp, RS 6/RS 7/RS Q8 4.0 V8 TT 591hp, RS e-tron GT "
          "electric) and this row has no displacement token, no VIN token and no source URL naming "
          "the model; the recorded 0W-30 / 7.1-7.6 L fill is shared by several of those engines, so "
          "no defensible mapping exists")
SKIP_NOTES = {("RS", y, None, None, None): _RSAMB for y in range(2018, 2026)}

IDENTITY = {
    "AMB": ("Petrol", 1781), "AVK": ("Petrol", 3000), "CALA": ("Petrol", 3200),
    "CALB": ("Petrol", 3200), "CNCD": ("Petrol", 2000), "CYMC": ("Petrol", 2000),
    "CTUC": ("Petrol", 2995), "CTWA": ("Petrol", 2995), "ATC": ("Petrol", 1800),
    "CRDB": ("Petrol", 4000), RS5V8: ("Petrol", 4163),
}

ROW_FIXES = {
    "CYMC": {"engine_type": "2.0 I4 Turbo TFSI EA888 Gen3B longitudinal (A4/A5/A6 B9, 252hp)",
             "power_hp": 252, "cylinders": 4, "data_confidence": "STEP45_VERIFIED"},
    "CNCD": {"engine_type": "2.0 I4 Turbo TFSI EA888 Gen3 longitudinal (A4/A6 2.0T, 220hp)",
             "cylinders": 4, "data_confidence": "STEP45_VERIFIED"},
    "CTUC": {"engine_type": "3.0 V6 TFSI supercharged (Q5 3.0T / A6 3.0T, 272hp)",
             "data_confidence": "STEP45_VERIFIED"},
    "CTWA": {"engine_type": "3.0 V6 TFSI supercharged (S4/S5 B8.5, 333hp)",
             "data_confidence": "STEP45_VERIFIED"},
    "CALB": {"engine_type": "3.2 V6 FSI (Q5 3.2 FSI quattro, 270hp US)", "power_hp": 270,
             "data_confidence": "STEP45_VERIFIED"},
    "CALA": {"engine_type": "3.2 V6 FSI (A4/A5 B8 3.2 FSI, 265hp US)", "power_hp": 265,
             "data_confidence": "STEP45_VERIFIED"},
    "CRDB": {"engine_type": "4.0 V8 TFSI biturbo (RS 6 C7 / RS 7 4G, 552hp EU / 560hp US)",
             "data_confidence": "STEP45_VERIFIED"},
    "ATC": {"engine_type": "1.8 I4 20v Turbo (TT 8N base, 180hp US)", "power_hp": 180,
            "data_confidence": "STEP45_VERIFIED"},
    "AMB": {"engine_type": "1.8 I4 20v Turbo (A4 B6/B7 1.8T, 170hp US)",
            "cylinders": 4, "data_confidence": "STEP45_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Audi", step_tag="step45", csv_num=53,
    lemon_baseline=433, engines_baseline=6075,
    R=R, NEW_ENGINES=NE, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES, SKIP_NOTES=SKIP_NOTES, TRIM_RULES=TRIM,
    expect_mapped=31, expect_skipped=8,
))
