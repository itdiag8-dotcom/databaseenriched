"""Step 43 (Step 5, batch 34): Scion LEMON replacement — 44 rows.

Scion was Toyota's US youth channel (MY2004-2016) and never had an engine of its own: every car
is a rebadged Toyota, Subaru or Mazda, and every nameplate was sold with exactly one engine in
a given generation, so nameplate + year is a complete decode.

| Nameplate | Donor car | Engine |
|---|---|---|
| xA 2005-06, xB 2005-06 (NCP) | Toyota ist / bB | 1.5 `1NZ-FE`, 103hp |
| xB 2008-15 (AZE151) | Toyota Corolla Rumion | 2.4 `2AZ-FE`, 158hp |
| xD 2008-14 | Toyota ist / Urban Cruiser | 1.8 `2ZR-FE`, 128hp |
| tC 2005-10 (AT10) | Avensis platform | 2.4 `2AZ-FE`, 161hp |
| tC 2011-16 (AT20) | Camry/RAV4 engine | 2.5 `2AR-FE`, 179hp |
| iQ 2012-15 | Toyota iQ | 1.33 `1NR-FE`, 94hp |
| iM 2016 | Toyota Auris / Corolla iM | 1.8 `2ZR-FAE` Valvematic, 137hp |
| iA 2016 | **Mazda2 sedan** | 1.5 Skyactiv-G (P5), 106hp |
| FR-S 2013-16 | Subaru BRZ | 2.0 Boxer `FA20` D-4S, 200hp |

Two of those are worth stating explicitly because they are not Toyota engines at all: the FR-S
runs Subaru's FA20 flat-four (Toyota calls it 4U-GSE) and the iA is a Mazda2 with Mazda's
1.5 Skyactiv-G, the only engine in this batch that needed a new row.

Seven rows are MY2015 trim slugs (`..._2015_TCAUTOMATICT`); since each nameplate had one engine
the trim only distinguishes the transmission, so they map to the same targets as their year.
"""
import step5_lemon_lib as lib

CIT = {
    "SCIONUS": "Toyota/Scion US model-year specifications: xA and first-generation xB = 1.5 1NZ-FE 103hp; second-generation xB (2008-2015) = 2.4 2AZ-FE 158hp; xD = 1.8 2ZR-FE 128hp; tC 2005-2010 = 2.4 2AZ-FE 161hp; tC 2011-2016 = 2.5 2AR-FE 179hp; iQ = 1.33 1NR-FE 94hp; iM 2016 = 1.8 2ZR-FAE Valvematic 137hp; iA 2016 = Mazda2 sedan with the 1.5 Skyactiv-G 106hp; FR-S = Subaru FA20 2.0 flat-four D-4S 200hp (shared with the BRZ and the Toyota 86)",
    "TOYVOCAB": "Toyota/Subaru/Mazda engine rows already in the DB: 1NZ-FE 1500/109, 2AZ-FE 2400 (corrected to 4 cylinders in step 39), 2ZR-FE 1800/135, 2ZR-FAE 1800/145, 2AR-FE 2494, 1NR-FE 1300/98, FA20 2000/200 (Boxer D-4S), 'Skyactiv-G 2.0 (PE)' 1998/155",
}

NE = {
    "Skyactiv-G 1.5 (P5)": ("1.5 I4 Skyactiv-G (Mazda2/Demio, Scion iA / Yaris iA, 106hp)",
                            "Petrol", 1496, 106, 4),
}

R = [
    ("FR S", 2013, 2016, None, None, "FA20", "FR-S = the Subaru BRZ twin: FA20 2.0 flat-four D-4S, 200hp, its only engine [SCIONUS][TOYVOCAB]", 200),
    ("IA", 2016, 2016, None, None, "Skyactiv-G 1.5 (P5)", "Scion iA 2016 = the Mazda2 sedan, built by Mazda with the 1.5 Skyactiv-G, 106hp - the only non-Toyota-group petrol engine Scion sold [SCIONUS]", 106),
    ("IM", 2016, 2016, None, None, "2ZR-FAE", "Scion iM 2016 = Toyota Auris/Corolla iM: 1.8 2ZR-FAE Valvematic, 137hp, its only engine [SCIONUS]", 137),
    ("IQ", 2012, 2014, None, None, "1NR-FE", "Scion iQ = Toyota iQ: 1.33 1NR-FE Dual VVT-i, 94hp, its only engine [SCIONUS]", 94),
    ("TC", 2005, 2010, None, None, "2AZ-FE", "tC (AT10) 2005-2010 = 2.4 2AZ-FE, 161hp, its only engine [SCIONUS]", 161),
    ("TC", 2011, 2016, None, None, "2AR-FE", "tC (AT20) 2011-2016 = 2.5 2AR-FE, 179hp, its only engine [SCIONUS]", 179),
    ("XA", 2005, 2006, None, None, "1NZ-FE", "xA 2005-2006 = 1.5 1NZ-FE VVT-i, 103hp, its only engine [SCIONUS]", 103),
    ("XB", 2005, 2006, None, None, "1NZ-FE", "xB (first generation, NCP31) 2005-2006 = 1.5 1NZ-FE, 103hp [SCIONUS]", 103),
    ("XB", 2008, 2014, None, None, "2AZ-FE", "xB (second generation, AZE151) 2008-2014 = 2.4 2AZ-FE, 158hp, its only engine [SCIONUS]", 158),
    ("XD", 2008, 2014, None, None, "2ZR-FE", "xD 2008-2014 = 1.8 2ZR-FE Dual VVT-i, 128hp, its only engine [SCIONUS]", 128),
]

TRIM = {
    ("FR S", 2015, "FRSAUTOMATIC"): ("FA20", "2015 FR-S automatic = FA20 2.0 flat-four, 200hp [SCIONUS]", 200, None),
    ("FR S", 2015, "FRSSTANDARDT"): ("FA20", "2015 FR-S manual = FA20 2.0 flat-four, 200hp [SCIONUS]", 200, None),
    ("TC", 2015, "TCAUTOMATICT"): ("2AR-FE", "2015 tC automatic = 2.5 2AR-FE, 179hp [SCIONUS]", 179, None),
    ("TC", 2015, "TCSTANDARDTR"): ("2AR-FE", "2015 tC manual = 2.5 2AR-FE, 179hp [SCIONUS]", 179, None),
    ("XB", 2015, "XBAUTOMATICT"): ("2AZ-FE", "2015 xB automatic = 2.4 2AZ-FE, 158hp [SCIONUS]", 158, None),
    ("XB", 2015, "XBSTANDARDTR"): ("2AZ-FE", "2015 xB manual = 2.4 2AZ-FE, 158hp [SCIONUS]", 158, None),
    ("IQ", 2015, "IQ"): ("1NR-FE", "2015 iQ = 1.33 1NR-FE, 94hp, its only engine [SCIONUS]", 94, None),
}

IDENTITY = {
    "FA20": ("Petrol", 2000), "2AR-FE": ("Petrol", 2494), "2AZ-FE": ("Petrol", 2400),
    "1NZ-FE": ("Petrol", 1500), "2ZR-FE": ("Petrol", 1800), "2ZR-FAE": ("Petrol", 1800),
    "1NR-FE": ("Petrol", 1300),
}

ROW_FIXES = {
    "FA20": {"engine_type": "2.0 Boxer F4 D-4S (Subaru FA20 / Toyota 4U-GSE: BRZ, FR-S/86, 200hp)",
             "cylinders": 4, "data_confidence": "STEP43_VERIFIED"},
    "2AR-FE": {"engine_type": "2.5 I4 DOHC Dual VVT-i 2AR-FE (Camry 178 / RAV4 179 / Scion tC 179hp)",
               "cylinders": 4, "data_confidence": "STEP43_VERIFIED"},
    "2ZR-FAE": {"engine_type": "1.8 I4 DOHC Valvematic 2ZR-FAE (Auris/Corolla iM 137 / Avensis 145hp)",
                "cylinders": 4, "data_confidence": "STEP43_VERIFIED"},
    "1NR-FE": {"engine_type": "1.33 I4 DOHC Dual VVT-i 1NR-FE (Yaris/iQ, 94-99hp)",
               "cylinders": 4, "data_confidence": "STEP43_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Scion", step_tag="step43", csv_num=51,
    lemon_baseline=520, engines_baseline=6160,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    expect_mapped=44, expect_skipped=0,
))
