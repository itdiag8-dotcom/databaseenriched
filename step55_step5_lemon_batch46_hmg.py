"""Step 55 (Step 5, batch 46): Kia + Hyundai LEMON replacement — 20 rows.

Hyundai and Kia share one engine catalogue (Nu, Gamma, Lambda, Smartstream), so they are run as
one batch. Three of the five targets are confirmed the same way the JLR batch was confirmed -
the crawl's fill and viscosity match this database's own stored service spec:

| Crawl rows | Fill / viscosity | Stored spec | Target |
|---|---|---|---|
| Forte Koup SX 2015, Forte5 2016-2017 | 4.49-4.54 / 5W-30 | `G4FJ` = **4.5 / 5W-30** | 1.6 T-GDI, 201hp |
| Forte 2014/2016, Forte5 2018 | 4.0 / 5W-20 | `G4NA`,`G4NC` = **4.0 / 5W-20** | 2.0 Nu |
| K5 2025 | 5.77 / 0W-20 | `G4KN` = **5.8** | 2.5 Smartstream, 191hp |
| Optima 2001 | 4.49 | `G6BV` = **4.51** (`G4JS` 2.4 = 4.25) | 2.5 V6 Delta, 170hp |

The Genesis sedan rows are the interesting ones. Their fill steps from 5.19 L to 5.69 L and
their viscosity from 5W-20 to 5W-30, which brackets the change from the 3.8 Lambda MPi to the
3.8 Lambda II GDI - but the two signals disagree about *when*: the viscosity changes for MY2012
and the fill only for MY2013. US model knowledge settles it, the GDI engine arriving for MY2012,
and the 2012 row's stale fill is recorded as a caveat rather than allowed to outvote it.
"""
import step5_lemon_lib as lib

CIT = {
    "HMGUS": "Hyundai/Kia US model-year specifications: Genesis sedan 3.8 Lambda MPi 290hp (2010-2011), 3.8 Lambda II GDI 333hp (2012-2014) and 311hp (2015-2016); Forte LX 1.8 Nu 148hp; Forte Koup SX and Forte5 SX 1.6 T-GDI 201hp; Forte5 2.0 GDI 173hp (2014) and 2.0 MPi 147hp (2018); Soul 2.0 GDI 161hp (the volume engine over the 1.6 base); K5 2.5 Smartstream 191hp; Optima 2001 2.5 V6 Delta 170hp",
    "LEMONSPEC": "Crawl fill/viscosity matched against this database's own engine_service_specs: G4FJ 4.5 L 5W-30, G4NA/G4NC 4.0 L 5W-20, G4KN 5.8 L, G6BV 4.51 L against the 2.4 four's 4.25 L",
}

R = [
    # --- Hyundai
    ("HYUNDAI:GENESIS", 2010, 2011, 3800, None, "G6DA (Hyundai)", "Genesis sedan 3.8 2010-2011 = the Lambda MPi V6, 290hp; 5.19 L of 5W-20 [HMGUS][LEMONSPEC]", 290),
    ("HYUNDAI:GENESIS", 2012, 2014, 3800, None, "G6DJ", "Genesis sedan 3.8 2012-2014 = the Lambda II GDI V6, 333hp; the viscosity changes to 5W-30 for MY2012 with the engine, the fill only catching up at MY2013 (the 2012 row's 5.19 L is stale) [HMGUS][LEMONSPEC]", 333),
    ("HYUNDAI:GENESIS", 2016, 2016, None, None, "G6DJ", "Genesis sedan MY2016 with no displacement token = the volume 3.8 GDI V6, 311hp [HMGUS][LEMONSPEC]", 311),
    # --- Kia
    ("KIA:FORTE", 2014, 2016, None, None, "G4NBB", "Forte sedan 2014-2016 = the 1.8 Nu of the volume LX trim, 148hp; 4.0 L fill, the Nu family's capacity [HMGUS][LEMONSPEC]", 148),
    ("KIA:FORTE5", 2014, 2014, None, None, "G4NC", "Forte5 2014 = the 2.0 GDI Nu, 173hp - the hatchback was never sold with the 1.8 [HMGUS]", 173),
    ("KIA:FORTE5", 2016, 2017, None, None, "G4FJ", "Forte5 2016-2017: the 4.49-4.54 L of 5W-30 is this database's own spec for the 1.6 T-GDI (4.5 L / 5W-30), the SX engine, 201hp [HMGUS][LEMONSPEC]", 201),
    ("KIA:FORTE5", 2018, 2018, None, None, "G4NA", "Forte5 2018 returns to 4.0 L of 5W-20 = the 2.0 Nu MPi, 147hp [HMGUS][LEMONSPEC]", 147),
    ("KIA:SOUL", 2016, 2019, None, None, "G4NA", "Soul 2016-2019 = the 2.0 Nu GDI, 161hp, the volume engine over the 1.6 base [HMGUS]", 161),
    ("KIA:K5", 2025, 2025, None, None, "G4KN", "K5 2025 = the 2.5 Smartstream, 191hp; 5.77 L against this database's 5.8 L spec for G4KN [HMGUS][LEMONSPEC]", 191),
    ("KIA:OPTIMA", 2001, 2001, None, None, "G6BV", "Optima 2001: the 4.49 L fill matches the 2.5 Delta V6 (4.51 L), not the 2.4 four (4.25 L), so 170hp [HMGUS][LEMONSPEC]", 170),
]

_KOUP = "Forte Koup SX 2015 = the 1.6 T-GDI, 201hp; 4.49 L of 5W-30 matches this database's G4FJ spec exactly [HMGUS][LEMONSPEC]"
TRIM = {
    ("FORTE", 2015, "FORTEKOUPSXA"): ("G4FJ", _KOUP, 201, None),
    ("FORTE", 2015, "FORTEKOUPSXS"): ("G4FJ", _KOUP, 201, None),
}

IDENTITY = {
    "G6DA (Hyundai)": ("Petrol", 3778), "G6DJ": ("Petrol", 3778), "G4NBB": ("Petrol", 1800),
    "G4NC": ("Petrol", 2000), "G4NA": ("Petrol", 1999), "G4FJ": ("Petrol", 1600),
    "G4KN": ("Petrol", 2500), "G6BV": ("Petrol", 2493),
}

ROW_FIXES = {
    "G4FJ": {"engine_type": "1.6 I4 Gamma T-GDI (Forte SX/Forte5 SX/Soul!/Veloster Turbo, 201hp US; 184hp EU)",
             "cylinders": 4, "data_confidence": "STEP55_VERIFIED"},
    "G4NBB": {"engine_type": "1.8 I4 Nu MPi (Forte LX / Elantra, 145-148hp)",
              "cylinders": 4, "data_confidence": "STEP55_VERIFIED"},
    "G4KN": {"engine_type": "2.5 I4 GDI Smartstream (K5/Sonata/Sportage/Tucson, 191-194hp)",
             "cylinders": 4, "data_confidence": "STEP55_VERIFIED"},
    "G6BV": {"engine_type": "2.5 V6 Delta (Optima 2001-2005 / Magentis, 170hp)",
             "cylinders": 6, "data_confidence": "STEP55_VERIFIED"},
    "G6DA (Hyundai)": {"engine_type": "3.8 V6 Lambda MPi (Genesis sedan 2009-11 290 / Azera 263hp)",
                       "cylinders": 6, "data_confidence": "STEP55_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand=["Kia", "Hyundai"], step_tag="step55", csv_num=63,
    lemon_baseline=91, engines_baseline=5745,
    R=R, NEW_ENGINES={}, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    expect_mapped=20, expect_skipped=0,
))
