"""Step 51 (Step 5, batch 42): Dodge + Jeep + Chrysler LEMON replacement — 59 rows.

The three FCA brands are run as one batch because they are one engine catalogue: the same EDZ
2.4, EGA 3.3, World Engine, Pentastar, Hemi and Cummins rows serve all three, and splitting them
would mean maintaining the same vocabulary three times.

The decisive signal is again the crawl's oil fill, which separates Chrysler's families cleanly:

| Fill | Engine |
|---|---|
| 4.25-4.56 L (4.5-4.8 qt) | `EDZ` 2.4 I4, `ECN`/`ED3` World Engine, `420A` 2.0 |
| 4.73 L (5 qt) | `EGA` 3.3 V6, `EGL` 3.8 V6, new `EGW` 3.2 V6, 2.0 GME 4xe |
| 5.2 L | `EGF` 3.5 V6 |
| 5.67 L (6 qt) | `3.6 Pentastar` |
| 6.62 L (7 qt) | `5.7 HEMI eTorque` |
| 11.35 L, 15W-40 | `ETH` 5.9 Cummins turbodiesel |

Highlights:

- The 2000-2001 LH cars (Concorde, Intrepid) record exactly 5 qt, which is the **3.2 V6** - the
  2.7 takes 6 qt and the 3.5 5.5 qt - so this batch adds the missing `EGW` row.
- The four `5900CC` Ram rows are the only non-petrol rows in the batch: 11.35 L of 15W-40 is the
  5.9 Cummins, and their fuel is corrected from Petrol to Diesel.
- The Journey walks through three engines in three years (3.5 V6 2009, 2.4 I4 2010, Pentastar
  2011) and the fills track it exactly: 5.2 → 4.25 → 5.67 L.
- Grand Cherokee 2025 records 5 qt, which is the 2.0 GME of the **4xe plug-in hybrid**, not the
  Pentastar's 6 qt; that row's fuel is corrected to Hybrid.
"""
import step5_lemon_lib as lib

CIT = {
    "FCAUS": "Chrysler/Dodge/Jeep US model-year specifications: 2.4 EDZ 150hp (Cirrus/Stratus/Sebring); 3.2 V6 225hp and 3.5 V6 in the 2000-2001 LH cars; 3.3 EGA 180hp (Caravan/Town & Country); 3.8 EGL 197hp (Pacifica); 2.0 ECN 158hp (Caliber) and 2.4 ED3 172hp World Engine (Compass/Patriot/Journey); 3.5 EGF 235hp (Journey 2009); 3.6 Pentastar 283hp (Journey 2011) and 293hp (Grand Cherokee WL); 5.7 Hemi eTorque 392hp (Wagoneer); 2.0 GME 4xe plug-in hybrid 375hp (Grand Cherokee 4xe); 5.9 Cummins HO turbodiesel 325hp (Ram HD); 2.0 420A 140hp (Avenger coupe)",
    "LEMONFILL": "Oil fill recorded by the crawl: 4.25-4.56 L on the 2.0/2.4 fours, 4.73 L (5 qt) on the 3.2/3.3/3.8 V6 and the 2.0 GME, 5.2 L on the 3.5 EGF, 5.67 L (6 qt) on the Pentastar, 6.62 L (7 qt) on the 5.7 Hemi, 11.35 L of 15W-40 on the Cummins",
}

PENTA = "3.6 Pentastar"
GME4XE = "2.0 Turbo GME (4xe)"
HEMI57 = "5.7 HEMI V8 eTorque (Wagoneer)"

NE = {
    "EGW": ("3.2 V6 SOHC 24v (Chrysler LH: Concorde LXi / Intrepid ES, 225hp)", "Petrol", 3231, 225, 6),
    "420A": ("2.0 I4 DOHC 16v 420A (Neon/Avenger/Sebring coupe, 140hp)", "Petrol", 1996, 140, 4),
}

R = [
    # --- Chrysler
    ("CHRYSLER:CIRRUS", 2000, 2000, None, None, "EDZ", "Cirrus 2000 = 2.4 EDZ four, 150hp, the volume engine; 4.25 L fill [FCAUS][LEMONFILL]", 150),
    ("CHRYSLER:CONCORDE", 2000, 2001, None, None, "EGW", "Concorde 2000-2001: the 4.73 L (5 qt) fill is the 3.2 V6 - the 2.7 takes 6 qt and the 3.5 5.5 qt - so 225hp [FCAUS][LEMONFILL]", 225),
    ("CHRYSLER:PACIFICA", 2008, 2008, 3800, None, "EGL", "Pacifica 3.8L 2008 = EGL V6, 197hp [FCAUS][LEMONFILL]", 197),
    ("CHRYSLER:SEBRING", 2000, 2003, None, None, "EDZ", "Sebring 2000-2003 = 2.4 EDZ four, 150hp, the volume engine of both the sedan and the convertible [FCAUS][LEMONFILL]", 150),
    ("CHRYSLER:TOWN", 2000, 2007, None, None, "EGA", "Town & Country = 3.3 EGA V6, 180hp, the volume minivan engine; 5 qt fill [FCAUS][LEMONFILL]", 180),
    # --- Dodge
    ("DODGE:AVENGER", 2000, 2000, None, None, "420A", "Avenger coupe 2000 = the 2.0 420A four, 140hp, its base engine; 4.25 L fill [FCAUS][LEMONFILL]", 140),
    ("DODGE:STRATUS", 2000, 2003, None, None, "EDZ", "Stratus 2000-2003 = 2.4 EDZ four, 150hp, the volume engine [FCAUS][LEMONFILL]", 150),
    ("DODGE:INTREPID", 2000, 2000, None, None, "EGW", "Intrepid 2000: 5 qt fill = the 3.2 V6, 225hp (Intrepid ES) [FCAUS][LEMONFILL]", 225),
    ("DODGE:CALIBER", 2007, 2012, None, None, "ECN", "Caliber = 2.0 ECN World Engine, 158hp, the volume engine; 4.25 L of 5W-20 [FCAUS][LEMONFILL]", 158),
    ("DODGE:GRAND", 2001, 2007, None, None, "EGA", "Grand Caravan = 3.3 EGA V6, 180hp, the volume minivan engine [FCAUS][LEMONFILL]", 180),
    ("DODGE:JOURNEY", 2009, 2009, None, None, "EGF", "Journey 2009: the 5.2 L fill is the 3.5 EGF V6, 235hp, not the 4.25 L 2.4 four [FCAUS][LEMONFILL]", 235),
    ("DODGE:JOURNEY", 2010, 2010, None, None, "ED3", "Journey 2010: the fill drops to 4.25 L = the 2.4 ED3 World Engine, 173hp [FCAUS][LEMONFILL]", 173),
    ("DODGE:JOURNEY", 2011, 2011, None, None, PENTA, "Journey 2011: 5.67 L (6 qt) = the new 3.6 Pentastar, 283hp [FCAUS][LEMONFILL]", 283),
    ("DODGE:CAB", 2004, 2004, 5900, None, "ETH", "Ram HD 5.9L: 11.35 L of 15W-40 is the Cummins turbodiesel (ETH, 325hp); fuel corrected from Petrol to Diesel [FCAUS][LEMONFILL]", 325),
    ("DODGE:PICKUP", 2004, 2009, 5900, None, "ETH", "Ram pickup 5.9L = the Cummins I6 turbodiesel, 325hp, on 15W-40 and an 11.35 L fill; fuel corrected to Diesel [FCAUS][LEMONFILL]", 325),
    # --- Jeep
    ("JEEP:COMPASS", 2007, 2016, None, None, "ED3", "Compass = 2.4 ED3 World Engine, 172hp, the volume engine (the 2.0 was FWD-only base); 4.25 L of 5W-20 [FCAUS][LEMONFILL]", 172),
    ("JEEP:PATRIOT", 2007, 2016, None, None, "ED3", "Patriot = 2.4 ED3 World Engine, 172hp, the volume engine [FCAUS][LEMONFILL]", 172),
    ("JEEP:GRAND CHEROKEE", 2022, 2022, None, None, PENTA, "Grand Cherokee WL 2022: 5.67 L (6 qt) = 3.6 Pentastar, 293hp [FCAUS][LEMONFILL]", 293),
    ("JEEP:GRAND CHEROKEE", 2025, 2025, None, None, GME4XE, "Grand Cherokee 2025 records 4.73 L (5 qt), which is the 2.0 GME of the 4xe plug-in hybrid, not the Pentastar's 6 qt; 375hp combined, fuel corrected to Hybrid [FCAUS][LEMONFILL]", 375),
    ("JEEP:WAGONEER", 2023, 2023, None, None, HEMI57, "Wagoneer 2023: 6.62 L (7 qt) = the 5.7 Hemi eTorque, 392hp [FCAUS][LEMONFILL]", 392),
]

IDENTITY = {
    "EDZ": ("Petrol", 2400), "EGA": ("Petrol", 3301), "EGL": ("Petrol", 3778),
    "ED3": ("Petrol", 2360), "ECN": ("Petrol", 1998), "EGF": ("Petrol", 3518),
    PENTA: ("Petrol", 3604), GME4XE: ("Hybrid", 1995), HEMI57: ("Petrol", 5654),
    "ETH": ("Diesel", 5923),
}

ROW_FIXES = {
    "EDZ": {"engine_type": "2.4 I4 DOHC 16v EDZ (Cirrus/Stratus/Sebring/PT Cruiser, 150hp US)",
            "power_hp": 150, "cylinders": 4, "data_confidence": "STEP51_VERIFIED"},
    "EGA": {"engine_type": "3.3 V6 OHV EGA (Caravan/Grand Caravan/Town & Country, 180hp US)",
            "power_hp": 180, "cylinders": 6, "data_confidence": "STEP51_VERIFIED"},
    "EGL": {"engine_type": "3.8 V6 OHV EGL (Pacifica/Grand Caravan/Wrangler, 197-202hp)",
            "power_hp": 197, "cylinders": 6, "data_confidence": "STEP51_VERIFIED"},
    "ED3": {"engine_type": "2.4 I4 World Engine ED3 (Compass/Patriot 172 / Journey 173 / Sebring 173hp)",
            "power_hp": 172, "cylinders": 4, "data_confidence": "STEP51_VERIFIED"},
    "ECN": {"engine_type": "2.0 I4 World Engine ECN (Caliber/Compass/Patriot, 158hp)",
            "power_hp": 158, "cylinders": 4, "data_confidence": "STEP51_VERIFIED"},
    "EGF": {"engine_type": "3.5 V6 SOHC 24v EGF (Journey/Sebring/Avenger/Charger, 235hp)",
            "power_hp": 235, "cylinders": 6, "data_confidence": "STEP51_VERIFIED"},
    "EGG": {"engine_type": "3.5 V6 SOHC 24v EGG (LH cars: 300M/Concorde Limited/Intrepid R-T, 242-253hp)",
            "cylinders": 6, "data_confidence": "STEP51_VERIFIED"},
    "ETH": {"engine_type": "5.9 I6 Cummins 24v HO turbodiesel (Ram HD 2001-2007, 305-325hp)",
            "power_hp": 325, "cylinders": 6, "data_confidence": "STEP51_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand=["Dodge", "Jeep", "Chrysler"], step_tag="step51", csv_num=59,
    lemon_baseline=242, engines_baseline=5886,
    R=R, NEW_ENGINES=NE, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={"ETH": "Diesel", GME4XE: "Hybrid"},
    expect_mapped=59, expect_skipped=0,
))
