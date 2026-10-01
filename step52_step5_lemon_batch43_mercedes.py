"""Step 52 (Step 5, batch 43): Mercedes-Benz LEMON replacement — 37 rows.

Mercedes names its cars after their engines, so 19 of the 37 rows decode straight from the
nameplate (C280 = 2.8 V6, S500 = 5.0 V8, SLK55 = 5.5 V8 AMG, ...). The 18 Sprinter rows have no
such clue, and there the oil fill does the work: 10-12.5 L of 5W-30 is a commercial diesel, and
the step from 12.5 L to 10.5 L marks the change from the 3.0 V6 OM642 to the 2.0 four OM654.

| Rows | Target | hp |
|---|---|---|
| C230 2000, 2002 | new `M111 2.3 Kompressor (C230K, 192hp)` | 192 |
| C280 2000 | new `M112 2.8 V6 (C280, 194hp)` | 194 |
| C350 2015 (2 trim rows) | new `M276 3.5 V6 (C350/GLE350, 302hp)` | 302 |
| CLA45 2019 | `M133.980` 2.0 turbo AMG | 375 |
| E550 2017, SL550 2020 | new `M278 4.7 V8 BiTurbo` | 402 / 449 |
| GLA250 2020 | `M260 2.0T` | 221 |
| GLE450 2016 | new `M276 3.0 V6 BiTurbo (GLE450/E400)` | 362 |
| GT 2024 | `M177.980` 4.0 V8 BiTurbo | 577 |
| Maybach 2021 / 2022-2023 | `M279.980` V12 / `M176 4.0 V8 BiTurbo` | 621 / 496 |
| R350 2008 | `M272.980` 3.5 V6 | 268 |
| S350 2006, S500 2006 | `M112.972` 3.7 V6 / `M113.966` 5.0 V8 | 245 / 302 |
| SLK300 2016 | new `M274 2.0 Turbo (SLK300/SLC300, 241hp)` | 241 |
| SLK55 2016 | `M152 5.5 V8 NA` | 415 |
| Sprinter 2010-2023 bare (12) | new `OM642 3.0 V6 CDI (Sprinter)` | 188 |
| Sprinter 2000CC 2019-2022, 2024-2025 (6) | new `OM654 2.0 I4 CDI (Sprinter)` | 161 / 168 |

All 18 Sprinter rows are corrected from Petrol to **Diesel**.

The Maybach pair is the one place where the fill separates two cars wearing the same badge: the
MY2021 row records 9.5 L, which is the V12's sump, while 2022-2023 record 8.51 L - the 4.0 V8 of
the Maybach S580, the V12 having left the range.
"""
import step5_lemon_lib as lib

CIT = {
    "MBUS": "Mercedes-Benz USA model-year specifications: C230 Kompressor 2.3 192hp; C280 2.8 V6 194hp; C350 3.5 V6 302hp; CLA45 AMG 2.0 turbo 375hp (2019); E550 4.7 V8 biturbo 402hp and SL550 449hp; GLA250 2.0 turbo 221hp; GLE450 AMG 3.0 V6 biturbo 362hp; AMG GT 63 4.0 V8 biturbo 577hp; Maybach S650 6.0 V12 621hp (through 2021) and Maybach S580 4.0 V8 496hp; R350 and ML350 3.5 V6 268hp; S350 (W220) 3.7 V6 245hp; S500 (W220) 5.0 V8 302hp; SLK300 2016 2.0 turbo 241hp; SLK55 AMG 5.5 V8 415hp; Sprinter 3.0 V6 CDI 188hp and 2.0 I4 CDI 161hp (168hp from 2024)",
    "LEMONFILL": "Oil fill recorded by the crawl: 12.5 L on the pre-2019 Sprinter (OM642 V6), 10.5-10.6 L on the later Sprinter, 10.03 L on the 2024-2025 Sprinter, 9.5 L on the MY2021 Maybach (V12 sump) versus 8.51 L on the 2022-2023 cars (4.0 V8), 8.04 L on the big V6/V8 saloons, 6.3-6.5 L on the 3.5 V6 and 2.0 turbo, 5.5-5.8 L on the four-cylinder AMG and the M260",
}

M111K = "M111 2.3 Kompressor (C230K, 192hp)"
M112_28 = "M112 2.8 V6 (C280, 194hp)"
M276_35 = "M276 3.5 V6 (C350/GLE350, 302hp)"
M276_30T = "M276 3.0 V6 BiTurbo (GLE450/E400, 362hp)"
M278_47 = "M278 4.7 V8 BiTurbo (E550/SL550)"
M274_20 = "M274 2.0 Turbo (SLK300/SLC300, 241hp)"
OM642S = "OM642 3.0 V6 CDI (Sprinter, 188hp)"
OM654S = "OM654 2.0 I4 CDI (Sprinter, 161-168hp)"

NE = {
    M111K: ("2.3 I4 16v Kompressor M111 (C230 Kompressor, 192hp US)", "Petrol", 2295, 192, 4),
    M112_28: ("2.8 V6 18v M112 E28 (C280/CLK280, 194hp US)", "Petrol", 2799, 194, 6),
    M276_35: ("3.5 V6 DOHC M276 DE35 (C350/E350/GLE350/SLK350, 302hp US)", "Petrol", 3498, 302, 6),
    M276_30T: ("3.0 V6 BiTurbo M276 DE30 LA (GLE450 AMG/E400/C450, 362hp)", "Petrol", 2996, 362, 6),
    M278_47: ("4.7 V8 BiTurbo M278 (E550 402 / S550 449 / SL550 449hp US)", "Petrol", 4663, 402, 8),
    M274_20: ("2.0 I4 Turbo M274 DE20 AL (SLK300/SLC300/C300, 241hp US)", "Petrol", 1991, 241, 4),
    OM642S: ("3.0 V6 CDI turbodiesel OM642 (Sprinter 2500/3500, 188hp)", "Diesel", 2987, 188, 6),
    OM654S: ("2.0 I4 CDI turbodiesel OM654 (Sprinter, 161hp; 168hp from 2024)", "Diesel", 1950, 161, 4),
}

R = [
    ("C230", 2000, 2002, None, None, M111K, "C230 Kompressor = the supercharged 2.3 M111, 192hp US [MBUS]", 192),
    ("C280", 2000, 2000, None, None, M112_28, "C280 = 2.8 V6 M112 E28, 194hp; 7.47 L fill is the M112 [MBUS][LEMONFILL]", 194),
    ("CLA45", 2019, 2019, None, None, "M133.980", "CLA45 AMG 2019 = the hand-built 2.0 turbo M133, 375hp US; 5.48 L of 5W-40 [MBUS][LEMONFILL]", 375),
    ("E550", 2017, 2017, None, None, M278_47, "E550 = 4.7 V8 biturbo M278, 402hp [MBUS][LEMONFILL]", 402),
    ("SL550", 2020, 2020, None, None, M278_47, "SL550 = the same 4.7 V8 biturbo M278 in its 449hp tune [MBUS][LEMONFILL]", 449),
    ("GLA250", 2020, 2020, None, None, "M260 2.0T", "GLA250 = transverse 2.0 turbo M260, 221hp [MBUS][LEMONFILL]", 221),
    ("GLE450", 2016, 2016, None, None, M276_30T, "GLE450 AMG 2016 = 3.0 V6 biturbo M276, 362hp [MBUS][LEMONFILL]", 362),
    ("GT", 2024, 2024, None, None, "M177.980", "AMG GT 2024 = the 4.0 V8 biturbo M177 in GT 63 tune, 577hp; 8.51 L fill [MBUS][LEMONFILL]", 577),
    ("MAYBACH", 2021, 2021, None, None, "M279.980", "Maybach MY2021 records a 9.5 L fill - the V12 sump - so this row is the S650, 621hp; the V8 cars take 8.5 L [MBUS][LEMONFILL]", 621),
    ("MAYBACH", 2022, 2023, None, None, "M176 4.0 V8 BiTurbo", "Maybach 2022-2023 = S580 with the 4.0 V8 biturbo M176, 496hp; the V12 had left the range and the fill drops to 8.51 L [MBUS][LEMONFILL]", 496),
    ("R350", 2008, 2008, None, None, "M272.980", "R350 = 3.5 V6 M272, 268hp US [MBUS][LEMONFILL]", 268),
    ("S350", 2006, 2006, None, None, "M112.972", "S350 (W220) 2006 = the 3.7 V6 M112 E37, 245hp [MBUS][LEMONFILL]", 245),
    ("S500", 2006, 2006, None, None, "M113.966", "S500 (W220) 2006 = 5.0 V8 M113, 302hp US [MBUS][LEMONFILL]", 302),
    ("SLK300", 2016, 2016, None, None, M274_20, "SLK300 MY2016 = the 2.0 turbo M274, 241hp (the SLK300 badge replaced the SLK250 with the four-cylinder turbo, not a V6); 6.34 L fill [MBUS][LEMONFILL]", 241),
    ("SLK55", 2016, 2016, None, None, "M152 5.5 V8 NA", "SLK55 AMG = the naturally aspirated 5.5 V8 M152, 415hp; 9.46 L of 5W-40 [MBUS][LEMONFILL]", 415),
    ("SPRINTER", 2010, 2023, None, None, OM642S, "Sprinter with no displacement token: 10.6-12.5 L of 5W-30 is the 3.0 V6 OM642 turbodiesel, 188hp; fuel corrected from Petrol to Diesel [MBUS][LEMONFILL]", 188),
    ("SPRINTER", 2019, 2022, 2000, None, OM654S, "Sprinter 2.0L = the OM654 four-cylinder turbodiesel, 161hp; fuel corrected to Diesel [MBUS][LEMONFILL]", 161),
    ("SPRINTER", 2024, 2025, None, None, OM654S, "Sprinter 2024-2025: the V6 has gone, leaving the 2.0 OM654 at 168hp, and the fill drops to 10.03 L; fuel corrected to Diesel [MBUS][LEMONFILL]", 168),
]

_C350 = "C350 MY2015 (base and 4MATIC are drivetrain trims) = 3.5 V6 M276, 302hp; 6.52 L fill [MBUS][LEMONFILL]"
TRIM = {
    ("C350", 2015, "C350BASE"): (M276_35, _C350, 302, None),
    ("C350", 2015, "C3504MATIC"): (M276_35, _C350, 302, None),
}

IDENTITY = {
    "M133.980": ("Petrol", 1991), "M260 2.0T": ("Petrol", 1991),
    "M152 5.5 V8 NA": ("Petrol", 5461), "M176 4.0 V8 BiTurbo": ("Petrol", 3982),
    "M177.980": ("Petrol", 3982), "M272.980": ("Petrol", 3498),
}

ROW_FIXES = {
    "M133.980": {"engine_type": "2.0 I4 Turbo AMG M133 (A45/CLA45/GLA45, 355-381hp)",
                 "cylinders": 4, "data_confidence": "STEP52_VERIFIED"},
    "M177.980": {"engine_type": "4.0 V8 BiTurbo AMG M177 (63-series: E63/GT 63/S63, 469-603hp)",
                 "cylinders": 8, "data_confidence": "STEP52_VERIFIED"},
    "M279.980": {"engine_type": "6.0 V12 BiTurbo M279 (S600 / S65 AMG / Maybach S650, 523-630hp)",
                 "cylinders": 12, "data_confidence": "STEP52_VERIFIED"},
    "M272.980": {"engine_type": "3.5 V6 DOHC M272 (R350/ML350/C350/E350, 268-272hp)",
                 "cylinders": 6, "data_confidence": "STEP52_VERIFIED"},
    "M112.972": {"engine_type": "3.7 V6 18v M112 E37 (S350 W220 / ML350, 245hp)",
                 "displacement_cc": 3724, "cylinders": 6, "data_confidence": "STEP52_VERIFIED"},
    "M113.966": {"engine_type": "5.0 V8 24v M113 (S500/E500/CL500 W220-W211, 302-306hp)",
                 "cylinders": 8, "data_confidence": "STEP52_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Mercedes", step_tag="step52", csv_num=60,
    lemon_baseline=183, engines_baseline=5829,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={OM642S: "Diesel", OM654S: "Diesel"},
    expect_mapped=37, expect_skipped=0,
))
