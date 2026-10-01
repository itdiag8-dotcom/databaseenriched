"""Step 50 (Step 5, batch 41): Suzuki LEMON replacement — 29 rows.

Suzuki's US range in its last decade was half its own engineering and half other people's: the
Forenza, Reno and Verona are Daewoos, the Equator is a Nissan Frontier, the second-generation
XL7 is a GM Theta with GM's High Feature V6. Each nameplate ran a single engine per generation,
and the crawl's oil fill confirms every one of them.

| Rows | Target | hp |
|---|---|---|
| Aerio 2005-2007 (3) | new `J23A` 2.3 I4 | 155 |
| Equator 2500CC / 4000CC 2009 | `QR25DE` / `VQ40DE` (Nissan Frontier) | 152 / 261 |
| Forenza 2005-2008, Reno 2005-2008 (8) | `T20SED` 2.0 Daewoo D-TEC | 126 |
| Grand Vitara 2005 | `H25A` 2.5 V6 | 165 |
| Grand Vitara 2006-2008 (3) | `H27A` 2.7 V6 | 185 |
| Grand Vitara 2400CC / 3200CC 2009 | `J24B` 2.4 I4 / `N32A` 3.2 V6 | 166 / 230 |
| SX4 2007-2009 (3) | `J20A` 2.0 I4 | 143 |
| Verona 2005-2006 (2) | `X25D1` 2.5 **inline-six** (Daewoo XK) | 155 |
| XL-7 2005-2006 (2) | `H27A` 2.7 V6 | 185 |
| XL7 2007-2009 (3) | `LY7` 3.6 V6 High Feature | 252 |

The Verona is the interesting one: a mid-size sedan with a transverse **straight six**, Daewoo's
XK, which the 6.43 L fill distinguishes from anything else Suzuki sold. The XL-7/XL7 split is
also a real engine change rather than a spelling change - the 2007 car moved from Suzuki's own
2.7 V6 (5.48 L) to GM's 3.6 (5.2 L).
"""
import step5_lemon_lib as lib

CIT = {
    "SUZUKIUS": "Suzuki US model-year specifications: Aerio 2.3 J23A 155hp (2004-2007); Equator = rebadged Nissan Frontier with the 2.5 QR25DE 152hp or 4.0 VQ40DE 261hp; Forenza and Reno = Daewoo Lacetti with the 2.0 D-TEC 126hp; Grand Vitara 2.5 V6 165hp (to 2005), 2.7 V6 185hp (2006-2008), then 2.4 I4 166hp / 3.2 V6 230hp (2009+); SX4 2.0 143hp; Verona 2.5 transverse inline-six 155hp; XL-7 2.7 V6 185hp (2004-2006) and XL7 3.6 V6 252hp (2007-2009)",
    "LEMONFILL": "Oil fill recorded by the crawl: 4.73 L on the Aerio, 4.63/5.11 L on the two Equators, 3.97 L on the Daewoo 2.0, 5.48 L on the 2.5/2.7 V6, 4.77 L on the 2.7 V6 and 2.4 I4, 6.0 L on the 3.2 V6, 4.44 L on the SX4, 6.43 L on the Verona's inline-six, 5.2 L on the GM 3.6",
}

NE = {
    "J23A": ("2.3 I4 DOHC 16v Suzuki J23A (Aerio 2004-2007, 155hp)", "Petrol", 2298, 155, 4),
}

R = [
    ("AERIO", 2005, 2007, None, None, "J23A", "Aerio 2005-2007 = 2.3 J23A, 155hp, its only engine [SUZUKIUS][LEMONFILL]", 155),
    ("EQUATOR", 2009, 2009, 2500, None, "QR25DE", "Equator = rebadged Nissan Frontier; the 2.5L is Nissan's QR25DE, 152hp [SUZUKIUS][LEMONFILL]", 152),
    ("EQUATOR", 2009, 2009, 4000, None, "VQ40DE", "Equator 4.0 = Nissan's VQ40DE V6, 261hp [SUZUKIUS][LEMONFILL]", 261),
    ("FORENZA", 2005, 2008, None, None, "T20SED", "Forenza = Daewoo Lacetti sedan/wagon: 2.0 D-TEC four, 126hp US; 3.97 L fill [SUZUKIUS][LEMONFILL]", 126),
    ("RENO", 2005, 2008, None, None, "T20SED", "Reno = the Lacetti hatchback, same 2.0 D-TEC, 126hp [SUZUKIUS][LEMONFILL]", 126),
    ("GRAND", 2005, 2005, None, None, "H25A", "Grand Vitara MY2005 (final year of the first generation) = 2.5 V6 H25A, 165hp; 5.48 L fill [SUZUKIUS][LEMONFILL]", 165),
    ("GRAND", 2006, 2008, None, None, "H27A", "Grand Vitara 2006-2008 = 2.7 V6 H27A, 185hp, its only engine; 4.77 L fill [SUZUKIUS][LEMONFILL]", 185),
    ("GRAND", 2009, 2009, 2400, None, "J24B", "Grand Vitara 2.4 MY2009 = J24B four, 166hp [SUZUKIUS][LEMONFILL]", 166),
    ("GRAND", 2009, 2009, 3200, None, "N32A", "Grand Vitara 3.2 MY2009 = N32A V6, 230hp; 6.0 L fill [SUZUKIUS][LEMONFILL]", 230),
    ("SX4", 2007, 2009, None, None, "J20A", "SX4 2007-2009 = 2.0 J20A, 143hp US, its only engine; 4.44 L fill [SUZUKIUS][LEMONFILL]", 143),
    ("VERONA", 2005, 2006, None, None, "X25D1", "Verona = Daewoo Magnus: a transverse 2.5 inline-SIX (XK/X25D1), 155hp; the 6.43 L fill matches nothing else Suzuki sold [SUZUKIUS][LEMONFILL]", 155),
    ("XL 7", 2005, 2006, None, None, "H27A", "XL-7 (first generation) = 2.7 V6 H27A, 185hp; 5.48 L fill [SUZUKIUS][LEMONFILL]", 185),
    ("XL 7", 2007, 2009, None, None, "LY7", "XL7 (second generation, GM Theta) = GM's 3.6 High Feature V6 LY7, 252hp; the fill drops to 5.2 L with the engine change [SUZUKIUS][LEMONFILL]", 252),
]

IDENTITY = {
    "QR25DE": ("Petrol", 2488), "VQ40DE": ("Petrol", 4000), "T20SED": ("Petrol", 1998),
    "H25A": ("Petrol", 2493), "H27A": ("Petrol", 2736), "J24B": ("Petrol", 2400),
    "N32A": ("Petrol", 3195), "J20A": ("Petrol", 1995), "X25D1": ("Petrol", 2500),
    "LY7": ("Petrol", 3600),
}

ROW_FIXES = {
    "H27A": {"engine_type": "2.7 V6 DOHC 24v Suzuki H27A (Grand Vitara / XL-7, 185hp US)",
             "power_hp": 185, "cylinders": 6, "data_confidence": "STEP50_VERIFIED"},
    "N32A": {"engine_type": "3.2 V6 DOHC Suzuki N32A (Grand Vitara 2009-2013, 230hp US)",
             "power_hp": 230, "data_confidence": "STEP50_VERIFIED"},
    "J24B": {"engine_type": "2.4 I4 DOHC VVT Suzuki J24B (Grand Vitara 166 / Kizashi 185hp)",
             "cylinders": 4, "power_hp": 166, "data_confidence": "STEP50_VERIFIED"},
    "J20A": {"engine_type": "2.0 I4 DOHC 16v Suzuki J20A (Grand Vitara 140 / SX4 143hp US)",
             "cylinders": 4, "data_confidence": "STEP50_VERIFIED"},
    "T20SED": {"engine_type": "2.0 I4 DOHC D-TEC (Daewoo Nubira/Lacetti; Suzuki Forenza/Reno 126hp US)",
               "data_confidence": "STEP50_VERIFIED"},
    "X25D1": {"engine_type": "2.5 I6 DOHC 24v transverse XK (Daewoo Magnus / Suzuki Verona, 155hp US)",
              "data_confidence": "STEP50_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Suzuki", step_tag="step50", csv_num=58,
    lemon_baseline=271, engines_baseline=5914,
    R=R, NEW_ENGINES=NE, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    expect_mapped=29, expect_skipped=0,
))
