"""Step 49 (Step 5, batch 40): Mini LEMON replacement — 31 rows, all badged "Cooper".

Every row is the same nameplate, so the decode is driven by the displacement tokens the crawl
kept on 18 of them and by the oil fill on the rest. Mini's US engine history across these years
is four families, and their fills do not overlap:

| Years | Engine | Fill |
|---|---|---|
| 2005-2006 (R50/R53) | Tritec `W10B16` 1.6 NA, 115hp | 4.54 L, 5W-40 |
| 2011-2013, 2015 1600CC (R56 LCI) | `N16B16A` 1.6 NA, 121hp | 4.20-4.25 L, 5W-30 |
| 2014, 2016, 1500CC 2017-2024 (F56) | `B38A15A` 1.5 **three-cylinder** turbo, 134hp | 4.21-4.63 L, 0W-20 |
| 2000CC 2017-2024 and the bare 2020-2024 rows | `B46A20A` 2.0 turbo Cooper S, 189hp | 5.25 L, 0W-20 |
| 2025 (F66) | `B48A20A` 2.0 turbo Cooper S, 201hp | 5.25 L, 0W-20 |

The bare 2020-2024 rows are not ambiguous despite having no displacement token: their 5.25 L fill
is the Cooper S 2.0, a litre more than any three-cylinder car. The MY2025 row is the restyled F66
Cooper S, which moved to the B48 at 201hp.
"""
import step5_lemon_lib as lib

CIT = {
    "MINIUS": "Mini USA model-year specifications: Cooper R50/R53 1.6 Tritec 115hp (Cooper S supercharged 168hp); Cooper R56 LCI 1.6 N16 121hp; Cooper F56 1.5 three-cylinder turbo B38 134hp; Cooper S F56 2.0 turbo B46 189hp; Cooper S F66 (2025) 2.0 turbo B48 201hp",
    "LEMONFILL": "Oil fill and viscosity recorded by the crawl: 4.54 L of 5W-40 on the Tritec cars, 4.20-4.25 L of 5W-30 on the N16, 4.21-4.63 L of 0W-20 on the B38 three-cylinder, 5.25 L of 0W-20 on every 2.0 Cooper S row",
}

W10 = "W10B16 (Cooper, 115hp)"
NE = {
    W10: ("1.6 I4 16v Tritec W10B16 (Mini Cooper R50/R52/R53, 115hp)", "Petrol", 1598, 115, 4),
}

R = [
    ("COOPER", 2005, 2006, None, None, W10, "Cooper R50/R53 = the naturally aspirated 1.6 Tritec, 115hp (the supercharged 168hp car was badged Cooper S); 4.54 L of 5W-40 [MINIUS][LEMONFILL]", 115),
    ("COOPER", 2011, 2013, None, None, "N16B16A", "Cooper R56 LCI = 1.6 N16 naturally aspirated, 121hp; 4.2 L of 5W-30 [MINIUS][LEMONFILL]", 121),
    ("COOPER", 2015, 2015, 1600, None, "N16B16A", "Cooper 1.6L MY2015 = the N16 1.6, 121hp - the F56 car is 1.5 or 2.0, so a 1600CC row is the outgoing engine [MINIUS][LEMONFILL]", 121),
    ("COOPER", 2014, 2014, None, None, "B38A15A", "Cooper F56 2014 = the new 1.5 three-cylinder turbo B38, 134hp [MINIUS][LEMONFILL]", 134),
    ("COOPER", 2016, 2016, None, None, "B38A15A", "Cooper F56 2016 = 1.5 three-cylinder turbo B38, 134hp; 4.21 L of 0W-20 [MINIUS][LEMONFILL]", 134),
    ("COOPER", 2017, 2024, 1500, None, "B38A15A", "Cooper 1.5L = B38 three-cylinder turbo, 134hp [MINIUS][LEMONFILL]", 134),
    ("COOPER", 2017, 2024, 2000, None, "B46A20A", "Cooper 2.0L = Cooper S, B46 turbo four, 189hp US [MINIUS][LEMONFILL]", 189),
    ("COOPER", 2020, 2024, None, None, "B46A20A", "Cooper 2020-2024 with no displacement token: the 5.25 L fill is the Cooper S 2.0 (B46, 189hp), a full litre above any three-cylinder row [MINIUS][LEMONFILL]", 189),
    ("COOPER", 2025, 2025, None, None, "B48A20A", "Cooper MY2025 = the restyled F66 Cooper S, which moved to the B48 2.0 turbo at 201hp; 5.25 L fill [MINIUS][LEMONFILL]", 201),
]

IDENTITY = {
    "N16B16A": ("Petrol", 1598), "B38A15A": ("Petrol", 1499),
    "B46A20A": ("Petrol", 1998), "B48A20A": ("Petrol", 1998),
}

ROW_FIXES = {
    "B38A15A": {"engine_type": "1.5 I3 Turbo B38A15A (Mini Cooper F55/F56/F57, 134hp US / 136hp EU)",
                "cylinders": 3, "power_hp": 134, "data_confidence": "STEP49_VERIFIED"},
    "B46A20A": {"engine_type": "2.0 I4 Turbo B46A20A (Mini Cooper S F55/F56/F57, 189hp US)",
                "power_hp": 189, "data_confidence": "STEP49_VERIFIED"},
    "B48A20A": {"engine_type": "2.0 I4 Turbo B48A20A (Mini Cooper S, 192hp; F66 2025 201hp US)",
                "data_confidence": "STEP49_VERIFIED"},
    "N16B16A": {"engine_type": "1.6 I4 16v N16B16A naturally aspirated (Mini Cooper R56 LCI, 121hp US)",
                "power_hp": 121, "data_confidence": "STEP49_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Mini", step_tag="step49", csv_num=57,
    lemon_baseline=302, engines_baseline=5950,
    R=R, NEW_ENGINES=NE, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    expect_mapped=31, expect_skipped=0,
))
