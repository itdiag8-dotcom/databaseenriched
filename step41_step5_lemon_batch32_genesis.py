"""Step 41 (Step 5, batch 32): Genesis LEMON replacement — 74 rows.

Genesis is the newest marque in the queue and the easiest to decode precisely: the brand has
only existed since MY2017, every US model year offers one or two engines, and the crawl kept
the displacement on 68 of the 74 rows. The whole brand runs on four Hyundai powertrain families:

- Lambda II V6: 3.8 GDI **311hp** (G6DJ, G80 2017-2020) and 3.3 T-GDI **365hp** (G6DP,
  G70/G80/G90/Stinger)
- Tau V8: 5.0 GDI **420hp** (G90/G80 Sport 2017-2022)
- Theta II FR turbo: 2.0 T-GDI **252hp** (G4KL - the longitudinal RWD version of the 2.0T,
  used only by the G70, the DH G80 and the Stinger) [WIKI_THETA]
- Smartstream: 2.5 T-GDI **300hp** (G4KR) and 3.5 T-GDI V6 **375hp** (G6DT), which replaced the
  older engines across the 2021+ G80/GV80/GV70/G90 range [AUTOFILES_G4KR][MR_SMART]

The three `ELECTRIFIED` rows and the three `GV60` rows are battery-electric cars that the crawl
recorded as `fuel='Petrol'`; their variant fuel is corrected to Electric.
"""
import step5_lemon_lib as lib

CIT = {
    "WIKI_THETA": "https://en.wikipedia.org/wiki/Hyundai_Theta_engine ('2.0L FR Turbo GDI (G4KL): for the RWD based applications ... develops 252-255 PS (249-252 hp) at 6,200 rpm ... Genesis G70 (2017-2023), Genesis G80 (DH) (2017-2020), Kia Stinger (2017-2023)'; the transverse G4KH is the FWD Sonata/Santa Fe engine)",
    "AUTOFILES_G4KR": "https://autofiles.com/engine-type/hyundai/smartstream/g4kr-turbo/ (Smartstream G2.5 T-GDi 'G4KR Turbo' = 300 hp, petrol, fitted to Genesis G80 2021-2023, Genesis GV80 2021-2023 and Kia Stinger 2020-2022)",
    "MR_SMART": "https://www.motorreviewer.com/engine.php?engine_id=19 (Hyundai/Kia engine family index: Smartstream G2.5 T-GDi = G4KP/G4KR, Smartstream G3.5 MPi/GDi = G6DU/G6DT, Theta II 2.0T = G4KH/G4KL)",
    "GENESISUS": "Genesis Motor America model-year specifications: G70 2.0T 252hp (2019-2023), 2.5T 300hp (2024-25), 3.3T 365hp; G80 3.8 GDI 311hp and 5.0 V8 420hp (2017-2020), 3.3T 365hp (2018-2020), then 2.5T 300hp / 3.5T 375hp (2021+); G90 3.3T 365hp and 5.0 420hp (2017-2022), 3.5T 375hp standard from 2023 (409hp with the e-supercharger on the long-wheelbase); GV80 and GV70 2.5T 300hp / 3.5T 375hp; GV60 Advanced AWD 314hp (Performance 429hp); Electrified G80 365hp and Electrified GV70 429hp, both E-GMP dual-motor AWD",
    "GENVOCAB": "Hyundai-group engine rows already in the DB: G6DP 3342/365 (3.3 Lambda II T-GDI), G6DJ 3778 (3.8 Lambda II GDI), 'Tau 5.0 GDI (K900/Equus)' 5038/420, G4KN 2500/194 (Smartstream 2.5 NA), G6DH 3342/292, 'G6DA (Hyundai)' 3778/266",
}

NE = {
    "G4KL": ("2.0 I4 Theta II FR T-GDI (G70/G80 DH/Stinger RWD, 252hp)", "Petrol", 1998, 252, 4),
    "G4KR": ("2.5 I4 Smartstream T-GDI (G80/GV80/GV70/G70/Stinger, 300hp)", "Petrol", 2497, 300, 4),
    "G6DT": ("3.5 V6 Smartstream T-GDI (G80/G90/GV80/GV70, 375-409hp)", "Petrol", 3470, 375, 6),
    "GV60 Electric (E-GMP AWD)": ("E-GMP dual-motor AWD (GV60 Advanced 314hp / Performance 429hp)",
                                  "Electric", None, 314, None),
    "E-GMP Dual Motor (Genesis Electrified)": ("E-GMP dual-motor AWD (Electrified G80 365hp / Electrified GV70 429hp)",
                                               "Electric", None, 365, None),
}

R = [
    ("ELECTRIFIED", 2023, 2025, None, None, "E-GMP Dual Motor (Genesis Electrified)",
     "'Electrified' = the Electrified G80 and Electrified GV70, both E-GMP dual-motor AWD BEVs sold in the US 2023-2025; the crawl truncates the nameplate so the shared powertrain row is used (G80 365hp / GV70 429hp) and the row's fuel is corrected from Petrol to Electric [GENESISUS]", 365),
    ("G70", 2019, 2023, 2000, None, "G4KL", "G70 2.0T 2019-2023 = Theta II FR T-GDI G4KL, 252hp [WIKI_THETA][GENESISUS]", 252),
    ("G70", 2024, 2025, 2500, None, "G4KR", "G70 2.5T 2024-2025 = Smartstream G4KR, 300hp (it replaced the 2.0T for MY2024) [AUTOFILES_G4KR][GENESISUS]", 300),
    ("G70", 2019, 2025, 3300, None, "G6DP", "G70 3.3T = Lambda II T-GDI G6DP, 365hp [GENESISUS][GENVOCAB]", 365),
    ("G80", 2017, 2020, 3800, None, "G6DJ", "G80 3.8 2017-2020 = Lambda II GDI G6DJ, 311hp, the base engine [GENESISUS]", 311),
    ("G80", 2017, 2020, 5000, None, "Tau 5.0 GDI (K900/Equus)", "G80 5.0 Ultimate/Sport 2017-2020 = Tau 5.0 V8 GDI, 420hp [GENESISUS][GENVOCAB]", 420),
    ("G80", 2018, 2020, 3300, None, "G6DP", "G80 Sport 3.3T 2018-2020 = Lambda II T-GDI G6DP, 365hp [GENESISUS]", 365),
    ("G80", 2021, 2025, 2500, None, "G4KR", "G80 (RG3) 2.5T 2021-2025 = Smartstream G4KR, 300hp base engine [AUTOFILES_G4KR]", 300),
    ("G80", 2021, 2025, 3500, None, "G6DT", "G80 (RG3) 3.5T 2021-2025 = Smartstream G3.5 T-GDI G6DT, 375hp [MR_SMART][GENESISUS]", 375),
    ("G90", 2017, 2022, 3300, None, "G6DP", "G90 3.3T 2017-2022 = Lambda II T-GDI G6DP, 365hp base engine [GENESISUS]", 365),
    ("G90", 2017, 2022, 5000, None, "Tau 5.0 GDI (K900/Equus)", "G90 5.0 Ultimate 2017-2022 = Tau 5.0 V8 GDI, 420hp [GENESISUS][GENVOCAB]", 420),
    ("G90", 2023, 2025, None, None, "G6DT", "G90 (RS4) 2023-2025 = 3.5T Smartstream G6DT, 375hp standard (409hp with the 48V e-supercharger on the long wheelbase) [GENESISUS]", 375),
    ("GV60", 2023, 2025, None, None, "GV60 Electric (E-GMP AWD)", "GV60 is battery-electric only; US cars are dual-motor AWD, Advanced 314hp (Performance 429hp) - crawl fuel Petrol corrected to Electric [GENESISUS]", 314),
    ("GV70", 2022, 2025, 2500, None, "G4KR", "GV70 2.5T = Smartstream G4KR, 300hp base engine [AUTOFILES_G4KR]", 300),
    ("GV70", 2022, 2025, 3500, None, "G6DT", "GV70 3.5T = Smartstream G3.5 T-GDI G6DT, 375hp [MR_SMART][GENESISUS]", 375),
    ("GV80", 2021, 2025, 2500, None, "G4KR", "GV80 2.5T = Smartstream G4KR, 300hp base engine [AUTOFILES_G4KR]", 300),
    ("GV80", 2021, 2025, 3500, None, "G6DT", "GV80 3.5T = Smartstream G3.5 T-GDI G6DT, 375hp [MR_SMART][GENESISUS]", 375),
]

IDENTITY = {
    "G6DP": ("Petrol", 3342), "G6DJ": ("Petrol", 3778),
    "Tau 5.0 GDI (K900/Equus)": ("Petrol", 5038),
}

ROW_FIXES = {
    "G6DJ": {"engine_type": "3.8 V6 Lambda II GDI (Genesis G80 311 / Equus-Genesis sedan 333hp)",
             "cylinders": 6, "power_hp": 311, "data_confidence": "STEP41_VERIFIED"},
    "G6DP": {"engine_type": "3.3 V6 Lambda II T-GDI (G70/G80 Sport/G90/Stinger GT/K900, 365hp)",
             "cylinders": 6, "data_confidence": "STEP41_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Genesis", step_tag="step41", csv_num=49,
    lemon_baseline=658, engines_baseline=6290,
    R=R, NEW_ENGINES=NE, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={"GV60 Electric (E-GMP AWD)": "Electric",
                        "E-GMP Dual Motor (Genesis Electrified)": "Electric"},
    expect_mapped=74, expect_skipped=0,
))
