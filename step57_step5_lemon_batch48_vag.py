"""Step 57 (Step 5, batch 48): Audi + Porsche + Volkswagen LEMON replacement — 19 rows.

The VAG remainder, including the **eight bare "RS" rows batch 36 deferred**. They were deferred
because "RS" alone identifies no car: Audi sold the RS 3, RS 5, RS 6, RS 7 and RS Q8 in the US
across these years. What resolves them now is that the eight rows carry only two fills, and
those two fills are nearly a quart apart and alternate by year:

| Fill | Rows | Engine |
|---|---|---|
| 7.09 L (7.5 qt) | 2018, 2020, 2024 | 2.5 TFSI five-cylinder (RS 3) |
| 7.57 L (8 qt) | 2019, 2021, 2022, 2023, 2025 | 2.9 V6 biturbo (RS 5) |

The 7.57 L figure is this project's established EA839 fingerprint (the 3.0 TFSI V6 was logged at
7.6 L back in the Audi batch), and the 2.9 is that engine family's biturbo version. Neither
value is anywhere near the 4.0 V8's nine-plus litres, which rules the RS 6/RS 7/RS Q8 out of all
eight rows. Both engines were missing from the database and are added here.

The Porsche rows split the same way - one nameplate, two engines, told apart by fill:

- Cayenne `3600CC` 2015 and 2017 record 8.49 L, the naturally aspirated 3.6 V6 (300hp); 2016 and
  2018 record 6.7 L, the twin-turbo 3.6 of the Cayenne S (420hp).
- 911 `3800CC` 2012-2013 with VIN D and 7.49 L of 0W-40 is the 991 Carrera S, 400hp.
- Macan `3000CC` 2020-2021 is the single-turbo 3.0 V6 Macan S, 348hp.

And the three Volkswagens are each unambiguous once the fill is read: 5.67 L of 0W-30 is the
EA888 of the Mk8 GTI, 5.96 L of 5W-40 the 2.8 V6 30v of the last Passat GLX, and 13.53 L of
5W-40 the **V10 TDI** of the Touareg - a diesel filed as Petrol, corrected here.
"""
import step5_lemon_lib as lib

CIT = {
    "VAGUS": "Audi/Porsche/VW US model-year specifications: RS 3 2.5 TFSI 394-401hp; RS 5 2.9 V6 biturbo 444hp; 911 991 Carrera S 3.8 400hp; Cayenne 3.6 V6 300hp and Cayenne S 3.6 biturbo 420hp; Macan S 3.0 V6 turbo 348hp; Golf GTI Mk8 2.0 TSI 241hp; Passat B5.5 GLX 2.8 V6 30v 190hp; Touareg 5.0 V10 TDI 310hp",
    "LEMONFILL": "Oil fill recorded by the crawl: the eight RS rows carry only two values, 7.09 L (2.5 five-cylinder) and 7.57 L (2.9 V6, matching this project's 7.6 L EA839 fingerprint), neither close to the 4.0 V8's 9+ L; Cayenne 8.49 L (3.6 NA) against 6.7 L (3.6 biturbo S); 13.53 L of 5W-40 on the Touareg V10 TDI",
}

RS3 = "2.5 TFSI EA855 evo (RS 3, 394-401hp)"
RS5 = "2.9 V6 TFSI biturbo (RS 4/RS 5, 444hp)"
PASSAT28 = "ATQ"
V10TDI = "5.0 V10 TDI (Touareg)"

NE = {
    RS3: ("2.5 I5 TFSI EA855 evo (RS 3 8V 394hp / 8Y 401hp US)", "Petrol", 2480, 394, 5),
    RS5: ("2.9 V6 TFSI biturbo EA839 (RS 4 B9 / RS 5 F5, 444hp)", "Petrol", 2894, 444, 6),
    PASSAT28: ("2.8 V6 30v (Passat B5.5 GLX US 2002-2005, 190hp)", "Petrol", 2771, 190, 6),
}

R = [
    # --- Audi: the eight bare "RS" rows deferred by batch 36
    ("AUDI:RS", 2018, 2018, None, None, RS3, "Bare 'RS' MY2018 with a 7.09 L (7.5 qt) fill = the 2.5 five-cylinder of the RS 3; the 2.9 V6 takes 8 qt and the 4.0 V8 over nine litres [VAGUS][LEMONFILL]", 394),
    ("AUDI:RS", 2020, 2020, None, None, RS3, "Bare 'RS' MY2020, 7.09 L = the RS 3's 2.5 five-cylinder, 394hp [VAGUS][LEMONFILL]", 394),
    ("AUDI:RS", 2024, 2024, None, None, RS3, "Bare 'RS' MY2024, 7.09 L = the RS 3 8Y's 2.5 five-cylinder, 401hp [VAGUS][LEMONFILL]", 401),
    ("AUDI:RS", 2019, 2019, None, None, RS5, "Bare 'RS' MY2019 with a 7.57 L fill = the 2.9 V6 biturbo of the RS 5, 444hp - 7.57 L is this project's EA839 fingerprint [VAGUS][LEMONFILL]", 444),
    ("AUDI:RS", 2021, 2023, None, None, RS5, "Bare 'RS' 2021-2023, 7.57 L = the RS 5's 2.9 V6 biturbo, 444hp [VAGUS][LEMONFILL]", 444),
    ("AUDI:RS", 2025, 2025, None, None, RS5, "Bare 'RS' MY2025, 7.57 L = the 2.9 V6 biturbo, 444hp [VAGUS][LEMONFILL]", 444),
    # --- Porsche
    ("PORSCHE:911", 2012, 2013, 3800, "D", "MA1.03", "911 991 Carrera S 2012-2013 (VIN D, 7.49 L of 0W-40) = the 3.8 flat six, 400hp US [VAGUS][LEMONFILL]", 400),
    ("PORSCHE:CAYENNE", 2015, 2015, 3600, None, "M46.20", "Cayenne 3.6 MY2015: the 8.49 L fill is the naturally aspirated V6, 300hp (the biturbo S takes 6.7 L) [VAGUS][LEMONFILL]", 300),
    ("PORSCHE:CAYENNE", 2017, 2017, 3600, None, "M46.20", "Cayenne 3.6 MY2017, 8.49 L = the naturally aspirated V6, 300hp [VAGUS][LEMONFILL]", 300),
    ("PORSCHE:CAYENNE", 2016, 2016, 3600, None, "MCU.RA", "Cayenne 3.6 MY2016: the fill drops to 6.7 L = the twin-turbo 3.6 of the Cayenne S, 420hp [VAGUS][LEMONFILL]", 420),
    ("PORSCHE:CAYENNE", 2018, 2018, 3600, None, "MCU.RA", "Cayenne 3.6 MY2018, 6.7 L = the twin-turbo 3.6 Cayenne S, 420hp [VAGUS][LEMONFILL]", 420),
    ("PORSCHE:MACAN", 2020, 2021, 3000, None, "MDC.NA", "Macan 3.0L 2020-2021 = the single-turbo 3.0 V6 of the Macan S, 348hp US [VAGUS][LEMONFILL]", 348),
    # --- Volkswagen
    ("VOLKSWAGEN:GOLF", 2025, 2025, None, None, "CXDA", "Golf MY2025 = the GTI Mk8's 2.0 TSI EA888, 241hp; 5.67 L of 0W-30 is the EA888's fill [VAGUS][LEMONFILL]", 241),
    ("VOLKSWAGEN:PASSAT", 2005, 2005, 2800, None, PASSAT28, "Passat 2.8L MY2005 = the 2.8 V6 30v of the GLX, 190hp; 5.96 L of 5W-40 [VAGUS][LEMONFILL]", 190),
    ("VOLKSWAGEN:TOUAREG", 2008, 2008, 5000, None, V10TDI, "Touareg 5.0L: 13.53 L of 5W-40 is the V10 TDI, 310hp - a diesel the crawl had filed as Petrol, corrected here [VAGUS][LEMONFILL]", 310),
]

IDENTITY = {
    "MA1.03": ("Petrol", 3800), "M46.20": ("Petrol", 3605), "MCU.RA": ("Petrol", 3604),
    "MDC.NA": ("Petrol", 3000), "CXDA": ("Petrol", 2000), V10TDI: ("Diesel", 4921),
}

ROW_FIXES = {
    "MA1.03": {"engine_type": "3.8 H6 DFI (911 991 Carrera S / 4S, 400hp US)",
               "cylinders": 6, "data_confidence": "STEP57_VERIFIED"},
    "M46.20": {"engine_type": "3.6 V6 DFI naturally aspirated (Cayenne 958/958.2, 300hp)",
               "cylinders": 6, "data_confidence": "STEP57_VERIFIED"},
    "MCU.RA": {"engine_type": "3.6 V6 twin-turbo (Cayenne S 958.2, 420hp)",
               "cylinders": 6, "data_confidence": "STEP57_VERIFIED"},
    "MDC.NA": {"engine_type": "3.0 V6 single-turbo (Macan S 2019-2021, 348hp US)",
               "cylinders": 6, "data_confidence": "STEP57_VERIFIED"},
    V10TDI: {"engine_type": "5.0 V10 TwinTurbo TDI (Touareg US 2006-2008, 310hp)",
             "cylinders": 10, "data_confidence": "STEP57_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand=["Audi", "Porsche", "Volkswagen"], step_tag="step57", csv_num=65,
    lemon_baseline=40, engines_baseline=5696,
    R=R, NEW_ENGINES=NE, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={V10TDI: "Diesel"},
    expect_mapped=19, expect_skipped=0,
))
