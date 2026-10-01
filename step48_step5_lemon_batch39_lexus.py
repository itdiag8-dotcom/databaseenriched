"""Step 48 (Step 5, batch 39): Lexus LEMON replacement — 31 rows.

Every row is a bare nameplate+year (ES, IS, RC 2016-2025 plus one SC 2000), so the decode runs
on the oil fill and viscosity the crawl recorded, which track Toyota's engine families precisely:

| Fill / viscosity | Engine |
|---|---|
| 4.35 L, 0W-20 | `2AR-FXE` 2.5 hybrid (ES 300h) |
| 4.54 L, **0W-16** | `A25A-FKS` 2.5 Dynamic Force — 0W-16 is unique to that family |
| 4.63 L, 0W-20 | `8AR-FTS` 2.0 turbo (IS/RC 200t-300) |
| 5.39 L, 0W-20 | `2GR-FKS` 3.5 V6 in the ES 350 |
| 5.67-6.43 L, 0W-20 | `2GR-FKS` 3.5 V6 in the IS/RC |
| 6.05 L, 0W-20 | `2GR-FE` 3.5 V6 (pre-2018 ES 350) |
| 5.20 L, 5W-30 | `2JZ-GE` 3.0 I6 (SC 300) |

That gives:

- **ES** 2016-2017 `2GR-FE` 268hp → 2018 `2AR-FXE` hybrid (the fill drops to 4.35 L, so this row
  is the ES 300h, and its fuel is corrected to Hybrid) → 2019-2020 `2GR-FKS` 302hp → 2021-2025
  `A25A-FKS` 203hp, where the 0W-16 spec marks the Dynamic Force four.
- **IS / RC** 2016-2017 `8AR-FTS` 241hp, then the 3.5 V6 `2GR-FKS` at 311hp from 2018.
- **SC** 2000 `2JZ-GE`, 225hp: 5.2 L is the SC 300's straight six, not the SC 400's 4.0 V8.

**Volume defaults (12).** From MY2018 the IS and RC ranges also contain a V8 halo car (RC F from
2018, IS 500 from 2022, both `2UR-GSE` 472hp). Their fills overlap the V6's, so the 2018-2025 IS
and RC rows take the volume 350 V6; this is flagged in the decision CSV.
"""
import step5_lemon_lib as lib

CIT = {
    "LEXUSUS": "Lexus USA model-year specifications: ES 350 3.5 V6 268hp (2013-2018, 2GR-FE) and 302hp (2019+, 2GR-FKS); ES 300h 2.5 hybrid 200hp system (2AR-FXE) and 215hp (A25A-FXS from 2019); ES 250 2.5 Dynamic Force 203hp (A25A-FKS, 2021-2024); IS 200t/300 2.0 turbo 241hp (8AR-FTS); IS 350 and RC 350 3.5 V6 311hp (2GR-FKS); RC F 2018+ and IS 500 2022+ 5.0 V8 472hp (2UR-GSE); SC 300 3.0 I6 225hp and SC 400 4.0 V8 290hp (final year 2000)",
    "LEMONFILL": "Oil fill and viscosity recorded by the crawl per row: 4.35 L on the 2AR-FXE hybrid, 4.54 L with 0W-16 on the A25A Dynamic Force four, 4.63 L on the 8AR-FTS 2.0 turbo, 5.39 L on the ES 350 2GR-FKS, 5.67-6.43 L on the IS/RC V6, 6.05 L on the 2GR-FE, 5.20 L on the SC 300's 2JZ-GE",
}

R = [
    ("ES", 2016, 2017, None, None, "2GR-FE", "ES 350 2016-2017 = 3.5 V6 2GR-FE, 268hp; 6.05 L fill is the 2GR-FE, well above the hybrid's 4.35 L [LEXUSUS][LEMONFILL]", 268),
    ("ES", 2018, 2018, None, None, "2AR-FXE", "ES MY2018 records a 4.35 L fill - the 2AR-FXE 2.5 hybrid of the ES 300h, not the 5.7 L 2GR-FKS of the ES 350; 200hp system output, and the crawl's Petrol flag is corrected to Hybrid [LEXUSUS][LEMONFILL]", 200),
    ("ES", 2019, 2020, None, None, "2GR-FKS", "ES 350 2019-2020 = 3.5 V6 2GR-FKS, 302hp; 5.39 L fill [LEXUSUS][LEMONFILL]", 302),
    ("ES", 2021, 2025, None, None, "A25A-FKS", "ES 2021-2025 records 4.54 L of 0W-16 - the signature of the 2.5 Dynamic Force four (ES 250, 203hp); the V6 takes 5.39 L of 0W-20 [LEXUSUS][LEMONFILL]", 203),
    ("IS", 2016, 2017, None, None, "8AR-FTS", "IS 200t 2016-2017 = 2.0 turbo 8AR-FTS, 241hp; 4.63 L fill [LEXUSUS][LEMONFILL]", 241),
    ("IS", 2018, 2025, None, None, "2GR-FKS", "IS 2018-2025 = 3.5 V6 2GR-FKS, 311hp (IS 350 / IS 300 AWD); VOLUME DEFAULT over the IS 500's 5.0 V8, which joined the range for 2022 [LEXUSUS][LEMONFILL]", 311),
    ("RC", 2016, 2017, None, None, "8AR-FTS", "RC 200t/300 2016-2017 = 2.0 turbo 8AR-FTS, 241hp; 4.63 L fill [LEXUSUS][LEMONFILL]", 241),
    ("RC", 2018, 2025, None, None, "2GR-FKS", "RC 350 2018-2025 = 3.5 V6 2GR-FKS, 311hp; VOLUME DEFAULT over the RC F's 5.0 V8 [LEXUSUS][LEMONFILL]", 311),
    ("SC", 2000, 2000, None, None, "2JZ-GE", "SC MY2000: the 5.2 L fill is the SC 300's 3.0 I6 2JZ-GE, 225hp; the SC 400's 1UZ-FE V8 takes 5.6 L [LEXUSUS][LEMONFILL]", 225),
]

IDENTITY = {
    "2GR-FE": ("Petrol", 3500), "2GR-FKS": ("Petrol", 3456), "8AR-FTS": ("Petrol", 1998),
    "2AR-FXE": ("Hybrid", 2493), "A25A-FKS": ("Petrol", 2500), "2JZ-GE": ("Petrol", 2997),
}

ROW_FIXES = {
    "2AR-FXE": {"engine_type": "2.5 I4 Atkinson + e-motors, hybrid (Camry Hybrid / ES 300h, 200hp system)",
                "cylinders": 4, "data_confidence": "STEP48_VERIFIED"},
    "2GR-FE": {"engine_type": "3.5 V6 DOHC VVT-i 2GR-FE (RX 350 / ES 350 268-275hp)",
               "data_confidence": "STEP48_VERIFIED"},
    "A25A-FKS": {"engine_type": "2.5 I4 Dynamic Force A25A-FKS (Camry/RAV4 203hp; Lexus ES 250 203hp)",
                 "cylinders": 4, "data_confidence": "STEP48_VERIFIED"},
    "2GR-FKS": {"engine_type": "3.5 V6 D-4S 2GR-FKS (IS 350/RC 350 311 / ES 350 302 / Camry 301hp)",
                "data_confidence": "STEP48_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Lexus", step_tag="step48", csv_num=56,
    lemon_baseline=333, engines_baseline=5981,
    R=R, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={"2AR-FXE": "Hybrid"},
    expect_mapped=31, expect_skipped=0,
))
