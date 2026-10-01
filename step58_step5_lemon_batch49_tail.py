"""Step 58 (Step 5, batch 49, FINAL): Nissan + Subaru + Lincoln + Mazda + Toyota + Honda — 21 rows.

The tail of the LEMON queue: six brands with one to seven rows each, and the last LEMON
placeholders in the database. Each row is decided by the same two signals the project has used
throughout - the crawl's oil fill, and the viscosity where it is diagnostic.

| Rows | Evidence | Target | hp |
|---|---|---|---|
| Nissan NV3500 2012-2013 | 6.51 L (the 4.0 V6 takes 5.1) | `VK56DE` 5.6 V8 | 317 |
| Nissan Titan 2017-2019 | 6.51 L, 0W-20 | `VK56VDE` 5.6 V8 DIG | 390 |
| Nissan Versa 2007-2008 | 3.92 L | `MR18DE` 1.8 | 122 |
| Subaru Baja 2005-2006, Legacy 2005-2007, Impreza 2.5 2005 | 3.97 L flat-four | `EJ253` 2.5 SOHC | 165-175 |
| Lincoln MKS `3700CC` 2010-2012 | 5.2 L, 5W-20 | `3.7 Ti-VCT V6` | 273 |
| Mazda 3 2019-2020 | 4.54 L, 0W-20 (the 2.0 takes 4.2) | new `PY-VPS` 2.5 Skyactiv-G | 186 |
| Toyota Crown 2025 | 4.25 L and **0W-8** | `A25A-FXS` 2.5 hybrid | 236 |
| Toyota Tundra 2020 | 8.04 L | `3UR-FE` 5.7 V8 | 381 |
| Honda CR-V 2025 | volume engine | `L15BE` 1.5 turbo | 190 |

Two notes. The Toyota Crown row is the batch's only fuel correction: **0W-8** is an oil grade
Toyota uses for its hybrid Dynamic Force fours and nothing else, so the row is the 2.5 hybrid
and its fuel goes from Petrol to Hybrid. And the Mazda is the last engine this project adds to
the database - the 2.5 Skyactiv-G, which had been missing while its 2.0 sibling was present.
"""
import step5_lemon_lib as lib

CIT = {
    "JPUS": "US model-year specifications: Nissan NV3500 5.6 V8 317hp and Titan 5.6 V8 DIG 390hp; Versa 1.8 122hp; Subaru Baja 2.5 SOHC 165hp, Legacy 2.5i 175hp, Impreza 2.5i 173hp; Lincoln MKS 3.7 V6 273hp; Mazda3 2.5 Skyactiv-G 186hp; Toyota Crown 2.5 hybrid 236hp and Tundra 5.7 V8 381hp; Honda CR-V 1.5 turbo 190hp",
    "LEMONFILL": "Oil fill and viscosity recorded by the crawl: 6.51 L on both Nissan trucks (the 4.0 V6 takes 5.1 L), 3.92 L on the Versa, 3.97 L on every Subaru row, 5.2 L of 5W-20 on the MKS, 4.54 L of 0W-20 on the Mazda3 (the 2.0 Skyactiv-G takes 4.2), 4.25 L of 0W-8 on the Crown, 8.04 L on the Tundra",
    "OW8": "0W-8 is specified by Toyota only for its hybrid Dynamic Force four-cylinders; no non-hybrid Toyota sold in the US takes it",
}

MAZDA25 = "PY-VPS"

NE = {
    MAZDA25: ("2.5 I4 Skyactiv-G (Mazda3/CX-5/Mazda6, 184-187hp)", "Petrol", 2488, 186, 4),
}

R = [
    ("NISSAN:NV3500", 2012, 2013, None, None, "VK56DE", "NV3500 2012-2013: the 6.51 L fill is the 5.6 V8 (317hp); the 4.0 V6 alternative takes 5.1 L [JPUS][LEMONFILL]", 317),
    ("NISSAN:TITAN", 2017, 2019, None, None, "VK56VDE", "Titan 2017-2019 = the direct-injection 5.6 V8, 390hp; 6.51 L of 0W-20 [JPUS][LEMONFILL]", 390),
    ("NISSAN:VERSA", 2007, 2008, None, None, "MR18DE", "Versa 2007-2008 = the 1.8 MR18DE, 122hp, its only US engine; 3.92 L fill [JPUS][LEMONFILL]", 122),
    ("SUBARU:BAJA", 2005, 2006, None, None, "EJ253", "Baja 2005-2006 = the 2.5 SOHC flat four, 165hp (the turbo Baja XT is a separate 227hp car); 3.97 L fill [JPUS][LEMONFILL]", 165),
    ("SUBARU:LEGACY", 2005, 2007, None, None, "EJ253", "Legacy 2.5i 2005-2007 = the 2.5 SOHC flat four, 175hp, the volume engine [JPUS][LEMONFILL]", 175),
    ("SUBARU:IMPREZA", 2005, 2005, 2500, None, "EJ253", "Impreza 2.5i 2005 = the 2.5 SOHC flat four, 173hp [JPUS][LEMONFILL]", 173),
    ("LINCOLN:MKS", 2010, 2012, 3700, None, "3.7 Ti-VCT V6", "MKS 3.7L 2010-2012 = the Cyclone Ti-VCT V6, 273hp in this application; 5.2 L of 5W-20 [JPUS][LEMONFILL]", 273),
    ("MAZDA:3", 2019, 2020, None, None, MAZDA25, "Mazda3 2019-2020: the 4.54 L fill is the 2.5 Skyactiv-G (186hp), not the 2.0, which takes 4.2 L [JPUS][LEMONFILL]", 186),
    ("TOYOTA:CROWN", 2025, 2025, None, None, "A25A-FXS", "Crown 2025 records 0W-8, a grade Toyota specifies only for its hybrid Dynamic Force fours, so this is the 2.5 hybrid (236hp) and the fuel is corrected from Petrol to Hybrid [OW8][JPUS][LEMONFILL]", 236),
    ("TOYOTA:TUNDRA", 2020, 2020, None, None, "3UR-FE", "Tundra 2020 = the 5.7 V8, 381hp; 8.04 L fill [JPUS][LEMONFILL]", 381),
    ("HONDA:CR V", 2025, 2025, None, None, "L15BE", "CR-V 2025 = the 1.5 VTEC Turbo, 190hp, the volume engine (LX/EX/EX-L) [JPUS]", 190),
]

IDENTITY = {
    "VK56DE": ("Petrol", 5550), "VK56VDE": ("Petrol", 5600), "MR18DE": ("Petrol", 1798),
    "EJ253": ("Petrol", 2500), "3.7 Ti-VCT V6": ("Petrol", 3726),
    "A25A-FXS": ("Hybrid", 2500), "3UR-FE": ("Petrol", 5700), "L15BE": ("Petrol", 1498),
}

ROW_FIXES = {
    "VK56VDE": {"engine_type": "5.6 V8 VK56VDE DIG (Titan 390 / Armada 390 / QX80 400hp)",
                "power_hp": 390, "cylinders": 8, "data_confidence": "STEP58_VERIFIED"},
    "MR18DE": {"engine_type": "1.8 I4 MR18DE (Versa/Cube/Tiida, 122hp US)",
               "cylinders": 4, "data_confidence": "STEP58_VERIFIED"},
    "3UR-FE": {"engine_type": "5.7 V8 3UR-FE i-FORCE (Tundra/Sequoia 381 / LX570 383hp)",
               "cylinders": 8, "data_confidence": "STEP58_VERIFIED"},
    "1UR-FE": {"engine_type": "4.6 V8 1UR-FE (GX460/LS460 rear-drive, 300-310hp)",
               "cylinders": 8, "data_confidence": "STEP58_VERIFIED"},
    "A25A-FXS": {"engine_type": "2.5 I4 Dynamic Force Atkinson hybrid A25A-FXS (Camry/RAV4/Crown, system 208-245hp)",
                 "cylinders": 4, "data_confidence": "STEP58_VERIFIED"},
    "L15BE": {"engine_type": "1.5 I4 VTEC Turbo DI L15BE (CR-V 2023+ / ADX 2025, 190hp)",
              "cylinders": 4, "data_confidence": "STEP58_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand=["Nissan", "Subaru", "Lincoln", "Mazda", "Toyota", "Honda"], step_tag="step58", csv_num=66,
    lemon_baseline=21, engines_baseline=5679,
    R=R, NEW_ENGINES=NE, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={"A25A-FXS": "Hybrid"},
    expect_mapped=21, expect_skipped=0,
))
