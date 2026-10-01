"""Step 46 (Step 5, batch 37): Isuzu LEMON replacement — 35 rows.

Isuzu's last US decade splits cleanly in two: the cars it engineered itself (Amigo, Rodeo,
Trooper, VehiCROSS, Axiom) and the ones it rebadged from GM (Hombre = S-10, Ascender =
TrailBlazer/Envoy, i-280/290/350/370 = Colorado/Canyon). The crawl kept displacement tokens on
the Rodeo/Amigo/Ascender rows and the recorded oil fills corroborate every remaining decode.

Isuzu's own engines:

- **X22SE** 2.2 DOHC I4, 130hp — Amigo and Rodeo 2200CC rows (4.54 L fill). New row.
- **6VD1** 3.2 V6, 205hp — Amigo and Rodeo 3200CC rows (4.73 L fill). New row.
- **6VE1** 3.5 V6 — Trooper and VehiCROSS at 215hp, Axiom at 230hp (250hp for 2004) and the
  MY2004 Rodeo at 250hp, by which point the 3.5 was the Rodeo's only engine.

GM-sourced:

- **Hombre** 2000 (4.16 L fill) = the S-10's `LN2` 2.2 I4, 120hp.
- **Ascender** 4200CC and the bare 2003/2007/2008 rows (6.62 L fill) = `LL8` 4.2 I6 Atlas, 275hp
  through 2005 and 291hp from 2006; the 5300CC rows (5.67 L fill) = the Vortec 5300 V8, `LM4`
  (290hp) for 2004 and `LH6` with Displacement on Demand (300hp) for 2005-2006.
- **i-280** = `LK5` 2.8 I4 175hp, **i-290** = `LLV` 2.9 I4 185hp, **i-350** = `L52` 3.5 I5 220hp,
  **i-370** = `LLR` 3.7 I5 242hp — the Colorado/Canyon Atlas family, 4.73 L for the fours and
  5.67 L for the fives, exactly as recorded.
"""
import step5_lemon_lib as lib

CIT = {
    "ISUZUUS": "Isuzu US model-year specifications: Amigo/Rodeo 2.2 DOHC X22SE 130hp and 3.2 V6 6VD1 205hp (2000-2003); Rodeo MY2004 3.5 V6 6VE1 250hp (its only engine that year); Trooper and VehiCROSS 3.5 V6 215hp; Axiom 3.5 V6 230hp (2002-2003) and 250hp (2004); Hombre = rebadged Chevrolet S-10, 2.2 I4 120hp base; Ascender = rebadged TrailBlazer/Envoy with the 4.2 I6 (275hp to 2005, 291hp from 2006) and the 5.3 V8 (LM4 290hp 2004, LH6 300hp 2005-2006); i-280 2.8 I4 175hp, i-290 2.9 I4 185hp, i-350 3.5 I5 220hp, i-370 3.7 I5 242hp (rebadged Colorado/Canyon)",
    "LEMONFILL": "Oil fill recorded by the crawl per row: 4.54 L on the 2.2 I4 rows, 4.73 L on the 3.2/3.5 V6 and the Atlas fours, 4.16 L on the Hombre (GM 2200), 5.67 L on the Atlas fives and the Vortec 5300, 6.62 L on the 4.2 I6 Atlas",
}

NE = {
    "X22SE": ("2.2 I4 DOHC 16v (Isuzu X22SE: Amigo/Rodeo 2000-2003, 130hp)", "Petrol", 2198, 130, 4),
    "6VD1": ("3.2 V6 DOHC 24v (Isuzu 6VD1: Amigo/Rodeo/Trooper, 205hp US)", "Petrol", 3165, 205, 6),
}

R = [
    ("AMIGO", 2000, 2000, 2200, None, "X22SE", "Amigo 2.2 = X22SE DOHC four, 130hp; 4.54 L fill [ISUZUUS][LEMONFILL]", 130),
    ("AMIGO", 2000, 2000, 3200, None, "6VD1", "Amigo 3.2 = 6VD1 V6, 205hp; 4.73 L fill [ISUZUUS][LEMONFILL]", 205),
    ("RODEO", 2000, 2003, 2200, None, "X22SE", "Rodeo 2.2 = X22SE DOHC four, 130hp [ISUZUUS][LEMONFILL]", 130),
    ("RODEO", 2000, 2003, 3200, None, "6VD1", "Rodeo 3.2 = 6VD1 V6, 205hp [ISUZUUS][LEMONFILL]", 205),
    ("RODEO", 2004, 2004, None, None, "6VE1", "Rodeo MY2004: the 3.5 V6 6VE1 at 250hp was the only engine left in its final year [ISUZUUS]", 250),
    ("AXIOM", 2002, 2003, None, None, "6VE1", "Axiom 2002-2003 = 3.5 V6 6VE1, 230hp, its only engine [ISUZUUS]", 230),
    ("AXIOM", 2004, 2004, None, None, "6VE1", "Axiom 2004 = the revised 3.5 V6 6VE1, 250hp [ISUZUUS]", 250),
    ("TROOPER", 2000, 2002, None, None, "6VE1", "Trooper = 3.5 V6 6VE1, 215hp US, its only engine [ISUZUUS]", 215),
    ("VEHICROSS", 2000, 2001, None, None, "6VE1", "VehiCROSS = the Trooper's 3.5 V6 6VE1, 215hp [ISUZUUS]", 215),
    ("HOMBRE", 2000, 2000, None, None, "LN2", "Hombre = rebadged Chevrolet S-10; the 4.16 L fill is the GM 2200 (LN2) 2.2 I4, 120hp, the base engine [ISUZUUS][LEMONFILL]", 120),
    ("ASCENDER", 2003, 2003, None, None, "LL8", "Ascender 2003 = rebadged TrailBlazer/Envoy; 6.62 L fill = 4.2 I6 Atlas (LL8), 275hp [ISUZUUS][LEMONFILL]", 275),
    ("ASCENDER", 2004, 2005, 4200, None, "LL8", "Ascender 4.2 = LL8 I6 Atlas, 275hp through MY2005 [ISUZUUS][LEMONFILL]", 275),
    ("ASCENDER", 2006, 2006, 4200, None, "LL8", "Ascender 4.2 MY2006 = LL8 I6 Atlas uprated to 291hp [ISUZUUS]", 291),
    ("ASCENDER", 2004, 2004, 5300, None, "LM4", "Ascender 5.3 MY2004 = LM4 Vortec 5300 aluminium-block V8, 290hp (Displacement on Demand arrived for 2005); 5.67 L fill [ISUZUUS][LEMONFILL]", 290),
    ("ASCENDER", 2005, 2006, 5300, None, "LH6", "Ascender 5.3 MY2005-2006 = LH6 Vortec 5300 with Displacement on Demand, 300hp [ISUZUUS][LEMONFILL]", 300),
    ("ASCENDER", 2007, 2008, None, None, "LL8", "Ascender 2007-2008: only the 4.2 I6 (LL8, 291hp) remained; 6.62 L fill confirms the I6 [ISUZUUS][LEMONFILL]", 291),
    ("I 280", 2006, 2006, None, None, "LK5", "i-280 = rebadged Colorado: 2.8 I4 Atlas (LK5), 175hp; 4.73 L fill [ISUZUUS][LEMONFILL]", 175),
    ("I 290", 2007, 2008, None, None, "LLV", "i-290 = 2.9 I4 Atlas (LLV), 185hp [ISUZUUS][LEMONFILL]", 185),
    ("I 350", 2006, 2006, None, None, "L52", "i-350 = 3.5 I5 Atlas (L52), 220hp; 5.67 L fill [ISUZUUS][LEMONFILL]", 220),
    ("I 370", 2007, 2008, None, None, "LLR", "i-370 = 3.7 I5 Atlas (LLR), 242hp [ISUZUUS][LEMONFILL]", 242),
]

IDENTITY = {
    "6VE1": ("Petrol", 3498), "LN2": ("Petrol", 2200), "LK5": ("Petrol", 2770),
    "LLV": ("Petrol", 2921), "L52": ("Petrol", 3460), "LLR": ("Petrol", 3653),
    "LL8": ("Petrol", 4157), "LM4": ("Petrol", 5327), "LH6": ("Petrol", 5328),
}

ROW_FIXES = {
    "6VE1": {"engine_type": "3.5 V6 DOHC 24v (Isuzu 6VE1: Trooper/VehiCROSS 215, Axiom 230-250, Rodeo 2004 250hp)",
             "cylinders": 6, "data_confidence": "STEP46_VERIFIED"},
    "LLV": {"engine_type": "2.9 I4 DOHC Atlas (Colorado/Canyon/i-290, 185hp)", "cylinders": 4,
            "power_hp": 185, "data_confidence": "STEP46_VERIFIED"},
    "LLR": {"engine_type": "3.7 I5 DOHC Atlas (Colorado/Canyon/i-370/H3, 242hp)", "cylinders": 5,
            "power_hp": 242, "data_confidence": "STEP46_VERIFIED"},
    "L52": {"engine_type": "3.5 I5 DOHC Atlas (Colorado/Canyon/i-350/H3, 220hp)", "cylinders": 5,
            "data_confidence": "STEP46_VERIFIED"},
    "LK5": {"engine_type": "2.8 I4 DOHC Atlas (Colorado/Canyon/i-280, 175hp)", "cylinders": 4,
            "data_confidence": "STEP46_VERIFIED"},
    "LH6": {"engine_type": "5.3 V8 Vortec 5300 with Displacement on Demand (TrailBlazer/Envoy/Ascender, 300hp)",
            "data_confidence": "STEP46_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Isuzu", step_tag="step46", csv_num=54,
    lemon_baseline=402, engines_baseline=6047,
    R=R, NEW_ENGINES=NE, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    expect_mapped=35, expect_skipped=0,
))
