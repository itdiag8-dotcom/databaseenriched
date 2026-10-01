"""Step 42 (Step 5, batch 33): Fiat LEMON replacement — 64 rows.

Fiat's US re-entry (MY2012-2025) sold five nameplates — 500, 500c, 500L, 500X, 124 Spider —
plus the 500e, and the whole range runs on three FCA engines and two electric drives. This is
the first batch where the crawl's **VIN engine digit** does most of the work: 7 rows carry
`VIN<x>`, and the Fiat VIN position-8 table resolves them exactly [WIKIBOOKS_FIATVIN]:

| VIN 8 | Engine | Applications |
|---|---|---|
| `R` | 1.4 I4 MultiAir **naturally aspirated** (EAB), 101hp | Fiat 500 2012-2017 |
| `H` | 1.4 I4 MultiAir **Turbo** (EAF/EAM), 135-160hp | 500 Abarth/Turbo, 500L 2014-20, 500X 2017-18 |
| `E` | 83 kW electric motor | 500e 2013-2019 |

The remaining rows are nameplate + year, and the US line-up per nameplate is single-engined in
almost every year: 500L = 1.4 Turbo only; 500X = 1.4 Turbo or 2.4 Tigershark (2016-18) then the
1.3 GSE Turbo (2019+); 124 Spider = 1.4 Turbo only; 500/500c = the 101hp NA 1.4 unless the trim
says Turbo or Abarth.

21 of the 64 rows are MY2015 trim-slug rows (`..._2015_500ABARTHAUT`), which is exactly what the
trim table is for: Abarth = 160hp (157 with the automatic), Turbo = 135hp, Pop/Sport/Lounge/
Easy/Trekking/Urbana = the base engine for that nameplate.

Six rows are electric cars the crawl recorded as `fuel='Petrol'`: `500E` 2013/2014 (83 kW,
111hp), `500E` 2025 and `500` 2024 (the new-generation 500e, 117hp - the only Fiat 500 sold in
the US for MY2024). Their variant fuel is corrected to Electric.
"""
import step5_lemon_lib as lib

CIT = {
    "WIKIBOOKS_FIATVIN": "https://en.wikibooks.org/wiki/Vehicle_Identification_Numbers_(VIN_codes)/Fiat/VIN_Codes (Fiat passenger-car position-8 engine codes: H = 1.4L I4 Turbo IC MultiAir FIRE - EAF: 500 Abarth '12-'17, 500 Turbo '13-'16, 500 GQ '14; EAM: 500/500 Abarth '18-'19; light-truck table EAM: 500L '14-'20, 500X '17-'18. R = 1.4L I4 MultiAir FIRE naturally aspirated (EAB), Fiat 500 '12-'17)",
    "FIAT500USA_VIN": "https://www.fiat500usa.com/2013/08/decoding-fiat-500-vin.html ('Character 8 Engine: E = 83 KW Electric Motor (E99); H = 1.4L 4 CYL Gasoline Turbo (EAF); R = 1.4L 4 CYL Gasoline Non-Turbo (EAB, EAC, EAE, EAJ, EAK)'; US 1.4 MultiAir Turbo rated 160hp for the Abarth)",
    "KBB_500_2013": "https://www.kbb.com/fiat/500/2013/specs/ (2013 Fiat 500 trim table: Pop/Sport/Lounge/Gucci 101hp @6500, Turbo 135hp @5500, Abarth 160hp @5500)",
    "WR_500T": "https://windingroad.com/articles/reviews/update-2013-fiat-500-turbo/ ('The 500T packs the same 1.4-liter, turbocharged, MultiAir four-cylinder found in the Abarth ... output is down from 160 horsepower and 170 pound-feet to 135 horsepower and 150 pound-feet')",
    "FIATUS": "Fiat Chrysler US model-year specifications: 500 Abarth 160hp manual / 157hp automatic (2015+); 500L 1.4 MultiAir Turbo 160hp (2014-2020, its only engine); 500X 1.4 MultiAir Turbo 160hp or 2.4 Tigershark MultiAir2 180hp (2016-2018), then 1.3 GSE Turbo 177hp with 9-speed automatic (2019-2023); 124 Spider 1.4 MultiAir Turbo 160hp (164hp Abarth); 500e 83 kW / 111hp (2013-2019) and 87 kW / 117hp (2024-2025)",
    "FIATVOCAB": "FCA engine rows already in the DB: '1.4 MultiAir Turbo (Dart/Renegade)' 1368/160, 'ED8' 2.4 Tigershark MultiAir2 2360/184, '1.3 GSE Turbo (Renegade)' 1288/177",
}

NE = {
    "1.4 MultiAir NA (500/500c)": ("1.4 I4 MultiAir FIRE naturally aspirated (EAB, Fiat 500/500c, 101hp)",
                                   "Petrol", 1368, 101, 4),
    "500e Electric (83 kW)": ("Electric motor 83 kW (Fiat 500e 2013-2019, 111hp)", "Electric", None, 111, None),
    "500e Electric (87 kW)": ("Electric motor 87 kW (Fiat 500e 2024-2025, 117hp)", "Electric", None, 117, None),
}

TURBO = "1.4 MultiAir Turbo (Dart/Renegade)"
NA14 = "1.4 MultiAir NA (500/500c)"

R = [
    ("124", 2017, 2020, None, None, TURBO, "124 Spider 2017-2020 = 1.4 MultiAir Turbo 160hp, its only engine (164hp in Abarth tune) [FIATUS][FIATVOCAB]", 160),
    ("500", 2012, 2014, None, None, NA14, "Fiat 500 bare rows 2012-2014 = the 101hp NA 1.4 MultiAir, the base engine on Pop/Sport/Lounge [KBB_500_2013]", 101),
    ("500", 2016, 2019, None, None, NA14, "Fiat 500 bare rows 2016-2019 = the 101hp NA 1.4 MultiAir base engine [KBB_500_2013][FIATUS]", 101),
    ("500", 2013, 2014, 1400, "H", TURBO, "VIN position 8 = H -> 1.4L MultiAir Turbo (EAF), i.e. the 500 Abarth 160hp / 500 Turbo 135hp; recorded at the Abarth's 160hp [WIKIBOOKS_FIATVIN][FIAT500USA_VIN]", 160),
    ("500", 2013, 2014, 1400, "R", NA14, "VIN position 8 = R -> 1.4L MultiAir naturally aspirated (EAB), 101hp [WIKIBOOKS_FIATVIN][FIAT500USA_VIN]", 101),
    ("500", 2024, 2024, None, None, "500e Electric (87 kW)", "The only Fiat 500 sold in the US for MY2024 is the new-generation 500e BEV, 87 kW / 117hp; crawl fuel Petrol corrected to Electric [FIATUS]", 117),
    ("500C", 2016, 2019, None, None, NA14, "500c (cabrio) 2016-2019 = the 101hp NA 1.4 MultiAir base engine [FIATUS]", 101),
    ("500L", 2014, 2020, None, None, TURBO, "500L 2014-2020 = 1.4 MultiAir Turbo 160hp, its only US engine [FIATUS][WIKIBOOKS_FIATVIN]", 160),
    ("500X", 2016, 2016, 1400, "W", TURBO, "500X 2016 1400CC = 1.4 MultiAir Turbo 160hp (manual-only in that year) [FIATUS]", 160),
    ("500X", 2017, 2018, 1400, "H", TURBO, "VIN position 8 = H -> 1.4L MultiAir Turbo (EAM), 500X 2017-2018, 160hp [WIKIBOOKS_FIATVIN]", 160),
    ("500X", 2016, 2018, 2400, None, "ED8", "500X 2400CC 2016-2018 = 2.4 Tigershark MultiAir2, 180hp, the automatic-only engine [FIATUS][FIATVOCAB]", 180),
    ("500X", 2016, 2016, 2400, "T", "ED8", "500X 2016 2400CC VIN T = 2.4 Tigershark MultiAir2, 180hp [FIATUS][FIATVOCAB]", 180),
    ("500X", 2017, 2018, 2400, "B", "ED8", "500X 2017-2018 2400CC VIN B = 2.4 Tigershark MultiAir2, 180hp [FIATUS][FIATVOCAB]", 180),
    ("500X", 2019, 2023, None, None, "1.3 GSE Turbo (Renegade)", "500X 2019-2023 = 1.3 GSE Turbo 177hp with the 9-speed automatic, its only engine after the 1.4/2.4 were dropped [FIATUS][FIATVOCAB]", 177),
    ("500E", 2013, 2014, None, None, "500e Electric (83 kW)", "500e 2013-2014 = 83 kW electric motor, 111hp (VIN position 8 = E); crawl fuel Petrol corrected to Electric [FIAT500USA_VIN][FIATUS]", 111),
    ("500E", 2025, 2025, None, None, "500e Electric (87 kW)", "500e 2025 = new-generation 87 kW motor, 117hp; crawl fuel Petrol corrected to Electric [FIATUS]", 117),
]

_ABARTH = "500 Abarth 2015 = 1.4 MultiAir Turbo, 160hp manual / 157hp automatic [KBB_500_2013][FIATUS]"
_TURBO = "500 Turbo 2015 = the Abarth's 1.4 MultiAir Turbo detuned to 135hp [WR_500T][KBB_500_2013]"
_NA = "2015 Fiat 500/500c Pop/Sport/Lounge = the 101hp NA 1.4 MultiAir base engine [KBB_500_2013]"
_500L = "500L 2015 (Easy/Pop/Lounge/Trekking/Urbana) = 1.4 MultiAir Turbo 160hp, the only 500L engine [FIATUS]"

TRIM = {
    ("500", 2015, "500ABARTHAUT"): (TURBO, _ABARTH, 157, None),
    ("500", 2015, "500ABARTHCAB"): (TURBO, _ABARTH, 160, None),
    ("500", 2015, "500ABARTHSTA"): (TURBO, _ABARTH, 160, None),
    ("500", 2015, "500TURBOAUTO"): (TURBO, _TURBO, 135, None),
    ("500", 2015, "500TURBOSTAN"): (TURBO, _TURBO, 135, None),
    ("500", 2015, "500LOUNGE"): (NA14, _NA, 101, None),
    ("500", 2015, "500POPAUTOMA"): (NA14, _NA, 101, None),
    ("500", 2015, "500POPSTANDA"): (NA14, _NA, 101, None),
    ("500", 2015, "500SPORTAUTO"): (NA14, _NA, 101, None),
    ("500", 2015, "500SPORTSTAN"): (NA14, _NA, 101, None),
    ("500C", 2015, "500CLOUNGE"): (NA14, _NA, 101, None),
    ("500C", 2015, "500CPOPAUTOM"): (NA14, _NA, 101, None),
    ("500C", 2015, "500CPOPSTAND"): (NA14, _NA, 101, None),
    ("500L", 2015, "500LEASYAUTO"): (TURBO, _500L, 160, None),
    ("500L", 2015, "500LEASYSTAN"): (TURBO, _500L, 160, None),
    ("500L", 2015, "500LLOUNGE"): (TURBO, _500L, 160, None),
    ("500L", 2015, "500LPOPAUTOM"): (TURBO, _500L, 160, None),
    ("500L", 2015, "500LPOPSTAND"): (TURBO, _500L, 160, None),
    ("500L", 2015, "500LTREKKING"): (TURBO, _500L, 160, None),
    ("500L", 2015, "500LURBANAAU"): (TURBO, _500L, 160, None),
    ("500L", 2015, "500LURBANAST"): (TURBO, _500L, 160, None),
}

IDENTITY = {
    TURBO: ("Petrol", 1368), "ED8": ("Petrol", 2360), "1.3 GSE Turbo (Renegade)": ("Petrol", 1288),
}

ROW_FIXES = {
    TURBO: {"engine_type": "1.4 I4 MultiAir Turbo FIRE (500 Abarth 160 / 500 Turbo 135 / 500L-500X 160 / 124 Spider 160 / Dart-Renegade 160hp)",
            "cylinders": 4, "data_confidence": "STEP42_VERIFIED"},
    "ED8": {"engine_type": "2.4 I4 Tigershark MultiAir2 (500X 180 / Dart R-T 184 / Cherokee-Renegade 180hp)",
            "cylinders": 4, "data_confidence": "STEP42_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand="Fiat", step_tag="step42", csv_num=50,
    lemon_baseline=584, engines_baseline=6221,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={"500e Electric (83 kW)": "Electric", "500e Electric (87 kW)": "Electric"},
    expect_mapped=64, expect_skipped=0,
))
