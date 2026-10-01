"""Step 40 (Step 5, batch 31): BMW LEMON replacement — 83 rows.

These rows are the hardest shape in the queue: the crawl recorded **no displacement, no VIN and
no trim** for almost all of them, just nameplate + model year (`LEMON_BMW_X5_2013`), and it
truncates sub-brand names, so `M` is the Z3 M / Z4 M roadster-coupe (an `M3` row would have kept
its digit) and `ACTIVEHYBRID` is the ActiveHybrid 3/5 sedan.

Decode is therefore nameplate generation + the US-market volume engine for that model year,
which for BMW is well defined because the US lineup per nameplate is narrow:

- X3: E83 3.0i M54 225 -> 3.0si/xDrive30i N52 260 -> F25 xDrive28i N52 240 -> G01 xDrive30i B48 248
- X4: G02 xDrive30i B48 248
- X5: E53 4.4i M62 282 (MY2000 was 4.4i-only) -> E70/F15 xDrive35i N55 300 -> G05 xDrive40i B58 335
- X6: E71/F16 xDrive35i N55 300 -> G06 xDrive40i B58 335
- X1/X2: B48 four (X2 xDrive28i 228, U11 X1 xDrive28i 241)
- Z3: 2.3 M52TU 170 -> 2.5i M54 184; Z4: E85 2.5i 184 -> 3.0i N52 215 -> E89 sDrive30i N52 255
  -> G29 sDrive30i B48 255
- M roadster/coupe: S52 240 (MY2000) -> S54 315 (E36/7-8) -> Z4 M S54 330
- 535i/550i 2017: the F07 5 Series GT, the last US cars to wear those badges (N55 300, N63 445)

The five ActiveHybrid rows are the one place the crawl's own `fuel` column helps: all are
Hybrid, and every US ActiveHybrid of MY2012-2016 (ActiveHybrid 5 from MY2012, ActiveHybrid 3
from MY2013) pairs the N55 300hp inline-six with a 55hp motor for **335hp combined**
[BMWPR_AH5][BMWPR_AH3][CD_AH3].
"""
import step5_lemon_lib as lib

CIT = {
    "BMWPR_AH5": "https://www.press.bmwgroup.com/usa/article/detail/T0122070EN_US/the-bmw-activehybrid-5 (2012 ActiveHybrid 5, based on the 535i: 3.0 TwinPower Turbo inline-6 300hp + 55hp synchronous motor in the 8-speed automatic = 335hp combined, 330 lb-ft)",
    "BMWPR_AH3": "https://www.press.bmwgroup.com/usa/article/detail/T0128325EN_US/the-all-new-bmw-activehybrid-3 (2013 ActiveHybrid 3: same 300hp N55 inline-6 as the 335i + 55hp motor = 335hp combined; 'the second hybrid model from BMW - after the BMW ActiveHybrid 5 - to use an in-line 6-cylinder engine')",
    "CD_AH3": "https://www.caranddriver.com/reviews/a15114142/2013-bmw-activehybrid-3-test-review/ (specification box: turbocharged DOHC 24-valve 3.0 inline-6, 300hp; AC synchronous motor 55hp; combined 335hp; 1.3 kWh pack)",
    "BMWUSSPEC": "BMW of North America model-year specifications by nameplate: X5 MY2000 = 4.4i only (M62TU 282hp), xDrive35i N55 300hp (E70 LCI/F15), xDrive40i B58 335hp (G05); X6 xDrive35i 300hp (E71/F16), xDrive40i 335hp (G06); X3 3.0i 225hp (E83 2004-06), 3.0si/xDrive30i 260hp (E83 2007-10), xDrive28i 240hp (F25 N52, 2011-12), xDrive30i 248hp (G01 B48); X4 xDrive30i 248hp; X2 xDrive28i 228hp; X1 xDrive28i 241hp (U11); Z3 2.3 170hp and 2.5i 184hp; Z4 2.5i 184hp, 3.0i 215hp (E85 N52), sDrive30i 255hp (E89 N52 and G29 B48); M roadster/coupe 240hp (S52, through MY2000) and 315hp (S54, 2001-02); Z4 M 330hp (S54); X5 M F85 567hp (S63B44T2); 535i 300hp (N55) and 550i 445hp (N63TU), both still sold as the F07 5 Series GT for MY2017",
    "BMWVOCAB": "BMW engine rows already in the DB: M52B25(256S4) 2494/170, M54B25(256S5) 2494/192, M54B30(306S3) 2979/222, M62B44(448S2) 4398/286, N52B30A 2996/258, N55B30A 2979/302, N63B44B 4395/449, 'B48B20 (30i)' 1998/255, 'B58B30 (40i)' 2998/335, S52B32US 3200/240, S54B32US 3200/334, S54B32 3200/338, 'S63B44T2 (M5 F90/M8)' 4394/600",
}

NE = {
    "N55B30 (ActiveHybrid)": ("3.0 I6 TwinPower Turbo + 55hp e-motor (ActiveHybrid 3/5, 335hp combined)",
                              "Hybrid", 2979, 335, 6),
}

R = [
    ("535I", 2017, 2017, None, None, "N55B30A", "2017 535i = the F07 5 Series GT, the last US 535i: N55 3.0 TwinPower Turbo I6, 300hp [BMWUSSPEC]", 300),
    ("550I", 2017, 2017, None, None, "N63B44B", "2017 550i = F07 5 Series GT xDrive: N63TU 4.4 V8 TwinTurbo, 445hp [BMWUSSPEC]", 445),
    ("ACTIVEHYBRID", 2012, 2016, None, None, "N55B30 (ActiveHybrid)", "Every US ActiveHybrid of MY2012-2016 (AH5 from 2012, AH3 from 2013) = N55 3.0 I6 300hp + 55hp motor = 335hp combined [BMWPR_AH5][BMWPR_AH3][CD_AH3]", 335),
    ("M", 2000, 2000, None, None, "S52B32US", "'M' MY2000 = M roadster/M coupe (E36/7-8), US-spec S52B32 3.2 I6, 240hp - the S54 arrived for 2001 [BMWUSSPEC]", 240),
    ("M", 2001, 2002, None, None, "S54B32US", "'M' MY2001-2002 = M roadster/M coupe with the S54B32 3.2 I6, 315hp in US tune [BMWUSSPEC]", 315),
    ("M", 2006, 2008, None, None, "S54B32", "'M' MY2006-2008 = Z4 M roadster/coupe, S54B32 3.2 I6, 330hp [BMWUSSPEC]", 330),
    ("X1", 2024, 2025, None, None, "B48B20 (30i)", "X1 (U11) 2024-2025 = xDrive28i, B48 2.0 TwinPower Turbo I4, 241hp - its only US engine [BMWUSSPEC]", 241),
    ("X2", 2018, 2023, None, None, "B48B20 (30i)", "X2 (F39) = xDrive28i/sDrive28i, B48 2.0 turbo I4, 228hp - its only non-M US engine [BMWUSSPEC]", 228),
    ("X3", 2004, 2006, None, None, "M54B30(306S3)", "X3 (E83) 2004-2006 = 3.0i, M54B30 3.0 I6, 225hp; the 2.5i was not sold in the US [BMWUSSPEC]", 225),
    ("X3", 2007, 2010, None, None, "N52B30A", "X3 (E83 LCI) 2007-2010 = 3.0si/xDrive30i, N52 3.0 I6 magnesium block, 260hp, its only US engine [BMWUSSPEC]", 260),
    ("X3", 2012, 2012, None, None, "N52B30A", "X3 (F25) 2012 = xDrive28i, still the N52 3.0 I6 at 240hp (the N20 four replaced it for 2013); volume model over the xDrive35i [BMWUSSPEC]", 240),
    ("X3", 2020, 2024, None, None, "B48B20 (30i)", "X3 (G01) 2020-2024 = xDrive30i, B48 2.0 turbo I4, 248hp base volume engine [BMWUSSPEC]", 248),
    ("X4", 2020, 2025, None, None, "B48B20 (30i)", "X4 (G02) = xDrive30i, B48 2.0 turbo I4, 248hp base volume engine [BMWUSSPEC]", 248),
    ("X5", 2000, 2000, None, None, "M62B44(448S2)", "X5 MY2000 (E53) was launched as the 4.4i only: M62TU 4.4 V8, 282hp (the 3.0i followed for 2001) [BMWUSSPEC]", 282),
    ("X5", 2010, 2014, None, None, "N55B30A", "X5 2010-2014 (E70 LCI / F15) = xDrive35i, N55 3.0 TwinPower Turbo I6, 300hp, the volume US engine [BMWUSSPEC]", 300),
    ("X5", 2016, 2018, None, None, "N55B30A", "X5 2016-2018 (F15) = xDrive35i, N55 3.0 I6, 300hp, the volume US engine [BMWUSSPEC]", 300),
    ("X5", 2020, 2025, None, None, "B58B30 (40i)", "X5 2020-2025 (G05) = xDrive40i, B58 3.0 I6, 335hp, the volume US engine [BMWUSSPEC]", 335),
    ("X6", 2010, 2014, None, None, "N55B30A", "X6 2010-2014 (E71) = xDrive35i, N55 3.0 I6, 300hp base volume engine [BMWUSSPEC]", 300),
    ("X6", 2016, 2019, None, None, "N55B30A", "X6 2016-2019 (F16) = xDrive35i, N55 3.0 I6, 300hp base volume engine [BMWUSSPEC]", 300),
    ("X6", 2020, 2023, None, None, "B58B30 (40i)", "X6 2020-2023 (G06) = xDrive40i, B58 3.0 I6, 335hp base volume engine [BMWUSSPEC]", 335),
    ("Z3", 2000, 2000, None, None, "M52B25(256S4)", "Z3 MY2000 volume model = the 2.3 (M52TU 2.5-litre detuned), 170hp [BMWUSSPEC]", 170),
    ("Z3", 2001, 2002, None, None, "M54B25(256S5)", "Z3 2001-2002 base = 2.5i, M54B25 I6, 184hp in US tune (the 3.0i was the step-up model) [BMWUSSPEC]", 184),
    ("Z4", 2003, 2005, None, None, "M54B25(256S5)", "Z4 (E85) 2003-2005 base = 2.5i, M54B25 I6, 184hp [BMWUSSPEC]", 184),
    ("Z4", 2006, 2008, None, None, "N52B30A", "Z4 (E85 LCI) 2006-2008 base = 3.0i, N52 I6, 215hp (the 3.0si made 255hp) [BMWUSSPEC]", 215),
    ("Z4", 2009, 2011, None, None, "N52B30A", "Z4 (E89) 2009-2011 = sDrive30i, N52 3.0 I6, 255hp base volume engine [BMWUSSPEC]", 255),
    ("Z4", 2019, 2019, None, None, "B48B20 (30i)", "Z4 (G29) 2019 = sDrive30i, B48 2.0 turbo I4, 255hp base volume engine [BMWUSSPEC]", 255),
]

TRIM = {
    ("X5", 2015, "X5M"): ("S63B44T2 (M5 F90/M8)",
                          "2015 X5 M (F85) = S63B44T2 4.4 V8 TwinTurbo, 567hp [BMWUSSPEC]", 567, None),
    ("X5", 2015, "X5XDRIVE50I"): ("N63B44B",
                                  "2015 X5 xDrive50i (F15) = N63TU 4.4 V8 TwinTurbo, 445hp [BMWUSSPEC]", 445, None),
    ("ACTIVEHYBRID", 2015, "ACTIVEHYBRID"): ("N55B30 (ActiveHybrid)",
                                             "2015 ActiveHybrid 3/5 = N55 3.0 I6 + 55hp motor, 335hp combined [BMWPR_AH3][CD_AH3]", 335, None),
}

IDENTITY = {
    "N55B30A": ("Petrol", 2979), "N63B44B": ("Petrol", 4395),
    "S52B32US": ("Petrol", 3200), "S54B32US": ("Petrol", 3200), "S54B32": ("Petrol", 3200),
    "B48B20 (30i)": ("Petrol", 1998), "B58B30 (40i)": ("Petrol", 2998),
    "M54B30(306S3)": ("Petrol", 2979), "N52B30A": ("Petrol", 2996),
    "M62B44(448S2)": ("Petrol", 4398), "M52B25(256S4)": ("Petrol", 2494),
    "M54B25(256S5)": ("Petrol", 2494), "S63B44T2 (M5 F90/M8)": ("Petrol", 4394),
}

ROW_FIXES = {
    "N55B30A": {"engine_type": "3.0 I6 TwinPower Turbo (N55: 335i/535i/X5-X6 xDrive35i, 300-306hp)",
                "cylinders": 6, "data_confidence": "STEP40_VERIFIED"},
    "S52B32US": {"engine_type": "3.2 I6 S52B32 US-spec (M3 / M roadster / M coupe 1996-2000, 240hp)",
                 "cylinders": 6, "data_confidence": "STEP40_VERIFIED"},
    "S54B32US": {"engine_type": "3.2 I6 S54B32 US-spec (M3 E46 333hp / M roadster-coupe 315hp)",
                 "cylinders": 6, "data_confidence": "STEP40_VERIFIED"},
    "S54B32": {"engine_type": "3.2 I6 S54B32 (Z4 M 330hp / M3 E46 343hp)",
               "cylinders": 6, "data_confidence": "STEP40_VERIFIED"},
    "S63B44T2 (M5 F90/M8)": {"engine_type": "4.4 V8 TwinTurbo S63B44T2 (X5 M/X6 M F85-F86 567 / F90 M5 600 / M8 617hp)",
                             "cylinders": 8, "data_confidence": "STEP40_VERIFIED"},
    "M62B44(448S2)": {"engine_type": "4.4 V8 M62TU (X5 4.4i 282 / 540i 282 / 740i 286hp)",
                      "cylinders": 8, "data_confidence": "STEP40_VERIFIED"},
    "N52B30A": {"engine_type": "3.0 I6 N52 magnesium-alloy (330i 255-258 / X3 3.0si 260 / Z4 3.0i 215-255hp)",
                "cylinders": 6, "data_confidence": "STEP40_VERIFIED"},
    "M54B25(256S5)": {"engine_type": "2.5 I6 M54B25 (525i 192 / Z3-Z4 2.5i 184hp)",
                      "cylinders": 6, "data_confidence": "STEP40_VERIFIED"},
    "M52B25(256S4)": {"engine_type": "2.5 I6 M52TU B25 (323i 170 / Z3 2.3 170hp)",
                      "cylinders": 6, "data_confidence": "STEP40_VERIFIED"},
    "M54B30(306S3)": {"engine_type": "3.0 I6 M54B30 (330i 231 / X5 3.0i 225 / X3 3.0i 225hp)",
                      "cylinders": 6, "data_confidence": "STEP40_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="BMW", step_tag="step40", csv_num=48,
    lemon_baseline=741, engines_baseline=6371,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    expect_mapped=83, expect_skipped=0,
))
