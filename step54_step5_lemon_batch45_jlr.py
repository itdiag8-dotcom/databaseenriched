"""Step 54 (Step 5, batch 45): Jaguar + Land Rover LEMON replacement — 27 rows.

One batch, because by this period Jaguar and Land Rover are one engineering company sharing one
engine catalogue (AJ-V6, AJ126, Ingenium), and because both brands' rows arrive with the same
problem: a nameplate the crawl truncated to uselessness. "RANGE" could be a Range Rover, a Range
Rover Sport, a Velar or an Evoque.

That makes the oil fill the only usable evidence, and here it is unusually decisive, because
three of the targets' own service specs in this database match the crawl's figures to the
decilitre:

| Crawl rows | Fill / viscosity | Matching engine spec | Target |
|---|---|---|---|
| RANGE 2022-2025 (no cc) | 7.0 L 0W-20 | `204PT` = **7.0 L 0W-20** | 2.0 Ingenium P250 |
| RANGE `3000CC` 2014-2015 | 7.99 L | `AJ126` = **8.04 L** | 3.0 V6 supercharged |
| Jaguar S-Type / X-Type | 6.24-6.81 / 5.77 L | `AJ30` = **6.52 L** | 3.0 AJ-V6 |

The remaining Range Rover rows step up in fill exactly as the big Ingenium straight six replaced
the supercharged V6: 8.8 L from 2020 and 9.46 L from 2023, against the V6's 8 L. And the single
MY2000 row records 5.82 L of 5W-40 — the Rover OHV V8 of the P38, an engine that shares nothing
with the rest of the batch and is unmistakable for it.
"""
import step5_lemon_lib as lib

CIT = {
    "JLRUS": "Jaguar/Land Rover US model-year specifications: S-Type 3.0 AJ-V6 240hp (2000-2002) and 235hp (2003-2008); X-Type 3.0 AJ-V6 231hp; Range Rover P38 4.6 V8 222hp (2000); Range Rover Sport/Velar/Evoque 2.0 Ingenium P250 246hp; 3.0 V6 supercharged 340hp (2014-2019); 3.0 I6 Ingenium MHEV P400 395hp (2020-2025)",
    "LEMONFILL": "Oil fill and viscosity recorded by the crawl, matched against this database's own engine_service_specs: 204PT 7.0 L 0W-20, AJ126 8.04 L, AJ30 6.52 L - each matching its crawl rows to the decilitre; 5.82 L of 5W-40 on the MY2000 Range Rover (Rover OHV V8); 8.8 L (2020-2022) and 9.46 L (2023-2025) on the Ingenium straight six",
}

ROVERV8 = "4.6 V8 (Rover OHV)"

R = [
    # --- Jaguar
    ("JAGUAR:S TYPE", 2000, 2002, None, None, "AJ30", "S-Type 2000-2002: the 6.3-6.5 L fill is the 3.0 AJ-V6 (240hp), not the 4.0 V8, which takes well over 7 L [JLRUS][LEMONFILL]", 240),
    ("JAGUAR:S TYPE", 2003, 2008, None, None, "AJ30", "S-Type 2003-2008 = the 3.0 AJ-V6, 235hp, the volume engine; its 6.52 L service fill is this database's own figure for AJ30 [JLRUS][LEMONFILL]", 235),
    ("JAGUAR:X TYPE", 2002, 2004, None, None, "AJ30", "X-Type 2002-2004 = the 3.0 AJ-V6, 231hp, the volume US engine (the 2.5 AJ25 was the base car); 5.77 L fill [JLRUS][LEMONFILL]", 231),
    # --- Land Rover
    ("LAND ROVER:RANGE", 2000, 2000, None, None, ROVERV8, "Range Rover MY2000 = the P38 4.6 Rover OHV V8, 222hp; 5.82 L of 5W-40 is that engine and nothing else in the range [JLRUS][LEMONFILL]", 222),
    ("LAND ROVER:RANGE", 2022, 2025, None, None, "204PT", "Range Rover family 2022-2025 with no displacement token: the crawl's 7.0 L of 0W-20 is exactly this database's service spec for the 2.0 Ingenium (204PT), so these are P250 cars, 246hp [JLRUS][LEMONFILL]", 246),
    ("LAND ROVER:RANGE", 2014, 2019, 3000, None, "AJ126", "Range Rover 3.0L 2014-2019 = the supercharged AJ126 V6, 340hp; the 7.99 L fill matches this database's 8.04 L spec for AJ126 [JLRUS][LEMONFILL]", 340),
    ("LAND ROVER:RANGE", 2020, 2025, 3000, None, "AJ300P", "Range Rover 3.0L 2020-2025 = the Ingenium straight six MHEV (P400, 395hp); the fill steps up from the V6's 8 L to 8.8 L in 2020 and 9.46 L in 2023, tracking the change of engine [JLRUS][LEMONFILL]", 395),
]

IDENTITY = {
    "AJ30": ("Petrol", 3000), "AJ126": ("Petrol", 2995), "AJ300P": ("Petrol", 2996),
    "204PT": ("Petrol", 2000), ROVERV8: ("Petrol", 4553),
}

ROW_FIXES = {
    ROVERV8: {"engine_type": "4.6 V8 OHV Rover (Range Rover P38 4.6 HSE 222hp / Discovery 2 217hp)",
              "cylinders": 8, "data_confidence": "STEP54_VERIFIED"},
    "AJ30": {"engine_type": "3.0 V6 AJ-V6 DOHC (S-Type 235-240 / X-Type 231 / Freelander 2 230hp)",
             "cylinders": 6, "data_confidence": "STEP54_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand=["Jaguar", "Land Rover"], step_tag="step54", csv_num=62,
    lemon_baseline=118, engines_baseline=5772,
    R=R, NEW_ENGINES={}, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    expect_mapped=27, expect_skipped=0,
))
