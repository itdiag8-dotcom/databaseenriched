"""Step 44 (Step 5, batch 35): Alfa Romeo LEMON replacement — 43 rows.

Alfa Romeo's second US era (MY2015-2025) sold four nameplates, and the crawl kept the
displacement on 40 of the 43 rows, so the batch is a clean displacement decode:

- **4C** (2015-2020) — one engine only, the all-aluminium **1750 TBi** (`960A1.000`, 1742cc),
  237hp in US tune. Three of the rows are MY2015 trim slugs (`4CBASE`, `4CSPIDER`,
  `4CLAUNCHEDIT`), which change the body and equipment, not the engine.
- **Giulia / Stelvio 2000CC** — the **2.0 GME-T4** turbo four, 280hp in Alfa tune (the same
  block Jeep/Dodge use at 268-270hp).
- **Giulia / Stelvio 2900CC** — the Quadrifoglio's **2.9 V6 twin-turbo** (type 690T, the
  Ferrari-derived F154 architecture with two cylinders removed), **505hp**. No 2.9 Alfa row
  existed, so this batch creates it.
- **Giulia / Stelvio 2025** (no displacement) — by then the US line-up is 2.0-only, since the
  Quadrifoglio left after MY2024.
- **Tonale 1300CC** (2024-2025, incl. one `VINW` row) — every US Tonale is the **Q4 plug-in
  hybrid**: 1.3 GSE turbo + rear e-axle, **285hp** system. The crawl files them as Petrol, so
  their variant fuel is corrected to Hybrid.
"""
import step5_lemon_lib as lib

CIT = {
    "ALFAUS": "Alfa Romeo USA model-year specifications: 4C/4C Spider 1750 TBi 237hp (its only engine, 2015-2020); Giulia and Stelvio 2.0 turbo 280hp (Base/Ti/Sprint/Veloce) and Quadrifoglio 2.9 V6 twin-turbo 505hp; Quadrifoglio withdrawn after MY2024, leaving the 2.0 as the only engine for MY2025; Tonale sold in the US exclusively as the Q4 plug-in hybrid, 1.3 turbo + 90 kW rear e-axle, 285hp combined",
    "ALFAVOCAB": "FCA engine rows already in the DB: '2.0 Turbo GME' 1995/268 (GME-T4), '1.3 GSE PHEV (Hornet R/T)' 1288/288 Hybrid (the Tonale's twin), '960A1.000' 1742/241 (the 4C's 1750 TBi, previously carrying a junk 'Rear side-section' descriptor)",
}

NE = {
    "690T 2.9 V6 TT (Quadrifoglio)": ("2.9 V6 twin-turbo (type 690T, Giulia/Stelvio Quadrifoglio, 505hp)",
                                      "Petrol", 2891, 505, 6),
}

GME = "2.0 Turbo GME"
QV = "690T 2.9 V6 TT (Quadrifoglio)"
PHEV = "1.3 GSE PHEV (Hornet R/T)"

R = [
    ("4C", 2016, 2020, None, None, "960A1.000", "4C/4C Spider = 1750 TBi all-aluminium turbo four (960A1.000), 237hp, its only engine [ALFAUS][ALFAVOCAB]", 237),
    ("GIULIA", 2017, 2024, 2000, None, GME, "Giulia 2000CC = 2.0 GME-T4 turbo four in Alfa tune, 280hp (Base/Ti/Sprint/Veloce) [ALFAUS]", 280),
    ("GIULIA", 2017, 2024, 2900, None, QV, "Giulia 2900CC = Quadrifoglio 2.9 V6 twin-turbo (690T), 505hp [ALFAUS]", 505),
    ("GIULIA", 2025, 2025, None, None, GME, "Giulia 2025 = 2.0 GME-T4 280hp; the Quadrifoglio left the US range after MY2024, so the 2.0 is the only engine [ALFAUS]", 280),
    ("STELVIO", 2018, 2024, 2000, None, GME, "Stelvio 2000CC = 2.0 GME-T4 turbo four, 280hp [ALFAUS]", 280),
    ("STELVIO", 2018, 2024, 2900, None, QV, "Stelvio 2900CC = Quadrifoglio 2.9 V6 twin-turbo (690T), 505hp [ALFAUS]", 505),
    ("STELVIO", 2025, 2025, None, None, GME, "Stelvio 2025 = 2.0 GME-T4 280hp, the only engine after the Quadrifoglio was withdrawn [ALFAUS]", 280),
    ("TONALE", 2024, 2025, 1300, None, PHEV, "Tonale is sold in the US only as the Q4 plug-in hybrid: 1.3 GSE turbo + rear e-axle, 285hp combined; crawl fuel Petrol corrected to Hybrid [ALFAUS]", 285),
    ("TONALE", 2025, 2025, 1300, "W", PHEV, "Tonale 2025 VIN W = the same 1.3 GSE Q4 plug-in hybrid, 285hp combined; crawl fuel Petrol corrected to Hybrid [ALFAUS]", 285),
]

_4C = "4C MY2015 (base, Spider and Launch Edition are body/equipment variants) = 1750 TBi 237hp, the only 4C engine [ALFAUS]"
TRIM = {
    ("4C", 2015, "4CBASE"): ("960A1.000", _4C, 237, None),
    ("4C", 2015, "4CSPIDER"): ("960A1.000", _4C, 237, None),
    ("4C", 2015, "4CLAUNCHEDIT"): ("960A1.000", _4C, 237, None),
}

IDENTITY = {
    GME: ("Petrol", 1995), PHEV: ("Hybrid", 1288), "960A1.000": ("Petrol", 1742),
}

ROW_FIXES = {
    "960A1.000": {"engine_type": "1.75 I4 Turbo 1750 TBi all-aluminium (Alfa 4C/4C Spider, 237hp US / 240hp EU)",
                  "cylinders": 4, "power_hp": 237, "data_confidence": "STEP44_VERIFIED"},
    GME: {"engine_type": "2.0 I4 Turbo GME-T4 (Giulia/Stelvio 280 / Wrangler-Cherokee 270 / Hornet 268hp)",
          "cylinders": 4, "data_confidence": "STEP44_VERIFIED"},
    PHEV: {"engine_type": "1.3 I4 GSE Turbo + 90kW rear e-axle PHEV (Tonale Q4 285 / Hornet R/T 288hp)",
           "cylinders": 4, "data_confidence": "STEP44_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Alfa Romeo", step_tag="step44", csv_num=52,
    lemon_baseline=476, engines_baseline=6117,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={PHEV: "Hybrid"},
    expect_mapped=43, expect_skipped=0,
))
