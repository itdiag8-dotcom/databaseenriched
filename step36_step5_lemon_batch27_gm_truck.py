"""Step 36 (Step 5, batch 27): merged GMC + Chevrolet LEMON replacement (GM truck/CUV family).

209 rows (GMC 156 + Chevrolet 53). These two divisions share one RPO engine catalogue
(Vortec/EcoTec3 V8s, Atlas I6, High Feature V6, Ecotec I4, Duramax/6.5 diesels), so they are
decoded together as a single engine-family batch; rule keys are brand-qualified ("GMC:SIERRA")
only where a model name would otherwise be ambiguous.

Decode is by RPO code, which GM publishes per model year and which the crawl's displacement +
VIN 8th digit pin down almost everywhere:

- Atlas I6 / Vortec V8 SUVs: Envoy 4.2 LL8 (275hp 02-05 -> 291hp 06-09), Envoy Denali 5.3
  LM4 290 (03-05) -> LH6 300 w/ DoD (06-09); Jimmy/Safari/Sonoma/S10 4.3 LU3 190, 2.2 LN2 120.
- Lambda/C1 crossovers: Acadia 3.6 LY7 275 ('07) -> LLT 288 ('08-12) -> LFX 288 ('13-16) ->
  LGX 310 ('17-23); 2.5 LCV 193; 2.0T LSY 230/228; 2.5T LK0 328 ('24-25).
- Terrain: 2.4 LAF/LEA 182 (VIN K), 3.0 LFW 264 (VIN 5), 3.6 LFX 301 (VIN 3), then 1.5T LYX
  170/175 (VIN V), 2.0T LTG 252 (VIN X), 1.6 LH7 turbodiesel 137 (VIN U, fuel -> Diesel).
- Full-size: Yukon/Sierra/Silverado 5.3 L83 355 ('16-18) -> L82 355 ('19) -> L84 355 ('21-25);
  C3500 7.4 L29 290 and 8.1 L18 340; 6.5 L65 turbodiesel 195 for every 6500CC chassis row
  (C3500 / CAB / PICKUP / SAVANA / RV) - those rows are mis-flagged Petrol in the crawl.
- Hummer EV: GM Ultium e4WD tri-motor, 1000hp, fuel -> Electric.
- Chevrolet cars: Corvette LS1 350, Camaro LLT 312 / LFX 323, Cobalt+HHR 2.2 LAP, Impala 2.5 LKW,
  Malibu LFX 252 / LUK eAssist 182 / 1.5T LFV 160, Cavalier LN2 115, SSR 5.3 LM4 300,
  Captiva Sport 2.4 LEA 182, Blazer 2.0T LSY 228, plus the Canada-only Daewoo-built
  Optra/Optra5 2.0 D-TEC T20SED 119 and Epica 2.5 I6 X25D1 155, Metro 1.3 G13BB 79,
  Tracker 1.6 G16B 97 / 2.5 V6 H25A 165.
"""
import step5_lemon_lib as lib

CIT = {
    "GMA_LK0": "https://gmauthority.com/blog/gm/gm-engines/lk0/ + https://gmauthority.com/blog/2024/05/here-are-the-2024-gmc-acadia-epa-fuel-economy-ratings/ (2024+ Acadia = turbo 2.5L I4 LK0, 328hp/326 lb-ft, sole engine; 2023 Acadia = LSY 228hp or LGX 310hp; naturally aspirated 2.5L LCV dropped after MY2021)",
    "GMA_BLAZER": "https://gmauthority.com/blog/gm/chevrolet/blazer/2024-chevrolet-blazer/ (2024 Blazer powertrains: 2.0L I4 LSY turbo 228hp @5000 standard on 2LT/3LT/Premier; 3.6L V6 LGX 308hp @6700 standard on RS only)",
    "CPP_TERRAIN": "https://carpartplanet.com/engines/gmc/terrain/2017/2.4l-vin-k-8th-digit-opt-lea + ebay OEM listings (Terrain VIN 8th digit: K = 2.4L LAF/LEA, 5 = 3.0L LFW, 3 = 3.6L LFX, V = 1.5L LYX gasoline, U = 1.6L LH7 diesel, X = 2.0L LTG turbo)",
    "TCC_ENVOY": "https://www.thecarconnection.com/specifications/gmc_envoy_2006 (2006 Envoy Denali: Engine Order Code LH6, 5.3L V8, 300hp @5200) + https://www.cars.com/research/gmc-envoy-2006/ (4.2 I6 291hp for 2006, up from 275hp; V8 gains Displacement on Demand for 2006) + https://www.velocityjournal.com/models/10962/configurations (2005 Envoy Denali 5.3 V8 290bhp)",
    "JDP_ENVOY": "https://www.jdpower.com/cars/history/gmc/envoy (Envoy I6 270hp at launch rising to 285-291hp; V8 power debuted on the conventional-wheelbase Envoy for 2005 with a 300hp 5.3L using Displacement on Demand; Envoy ended after MY2009)",
    "CD_HUMMER": "https://www.caranddriver.com/gmc/hummer-ev-2023 + /hummer-ev-2024 + https://www.motortrend.com/reviews/gmc-hummer-ev-pickup-0-60-mph-quarter-mile-acceleration (Hummer EV: tri-motor e4WD 1000hp/1200 lb-ft combined, 205 kWh Ultium pack; dual-motor 570-625hp on later EV2/EV2X trims)",
    "OPTRA": "https://chevycamaro.fandom.com/wiki/Chevrolet_Optra + https://www.autotrader.ca/research/chevrolet/optra/2005/ + https://www.auto123.com/en/new-cars/technical-specs/chevrolet/optra/2004/5/base/ (Canada-only Optra / Optra5 / Optra Wagon, 2004-2008, all powered by the 2.0L D-TEC inline-four, 119hp @5400 / 126 lb-ft @4000, GM-DAT Korea)",
    "EPICA": "https://ca.finance.yahoo.com/news/10-canadian-cars-you-can-t-buy-in-the-u-s-.html (Chevrolet Epica, Canada 2004-2006, 2.5-litre inline-six mounted transversely, FWD - the Suzuki Verona sibling)",
    "GMVOCAB": "DB GM RPO vocabulary already present: LU3 4300, LN2 2200/120, LL8 4157/291, LFX 3564, LLT 3600/304, LGX 3600, LCV 2500/196, LSY 1998/237, LTG 1998, LAF 2400/182, LEA 2400/182, LUK 2400/182 eAssist, LFW 2997/273, L96 5967/360, LQ4 5967, L18 8128/345, LS1 5665, X25D1 2500/154, T20SED 1998/128, L82 5300/355, L84 5300, L99 6162, LS3 6162",
    "GMLINEUP": "US/Canada GM lineup volume-defaults and per-year ratings: Vortec 4300 LU3 = 190hp in S/T-platform SUVs and pickups, 200hp in full-size vans/pickups; 2.2 OHV LN2 = 115-120hp (Cavalier/S10/Sonoma); Envoy 4.2 = 270hp '02, 275hp '03-05, 291hp '06-09; Acadia 3.6 = 275 ('07 LY7), 288 ('08-16 LLT/LFX), 310 ('17-23 LGX); Terrain 2.4 = 182, 3.0 = 264, 3.6 = 301, 1.5T = 170 ('18-20) / 175 ('21-25), 2.0T = 252; full-size 5.3 EcoTec3 = 355hp throughout; Corvette C5 base LS1 = 350hp '01-04 (Z06 LS6 optional); Camaro V6 = 312hp '10-11 LLT / 323hp '12-13 LFX (SS V8 optional); Impala 2.5 LKW = 195-197hp base (3.6 LFX 305 optional); Malibu 2016+ 1.5T LFV = 160hp base; Metro 1.3 = 79hp volume (1.0 I3 55hp 3-door only); Tracker = 1.6 97hp / 2.5 V6 165hp",
    "GM65": "GM 6.5L Detroit Diesel V8 (RPO L65 turbo, 195hp @3400 / 430 lb-ft) was the only 6500cc engine GM fitted to C/K3500, chassis-cab, Savana/Express and P-chassis motorhome platforms through 2002; the crawl records these rows as Petrol, which is corrected to Diesel here.",
    "GM74": "GM big-block: 7.4L L29 Vortec 7400 = 290hp @4400 (final year 2000 on C/K3500), replaced for 2001 by the 8.1L L18 Vortec 8100 = 340hp @4200; the 8.1L was also the sole gas engine of the GM P32 motorhome chassis after the 6.5 diesel was dropped.",
}

# code -> (engine_type, fuel, cc, hp, cylinders)
NE = {
    "L65": ("6.5 V8 OHV turbodiesel (Detroit Diesel; C/K3500, chassis cab, Savana/Express, P-chassis, 195hp)", "Diesel", 6500, 195, 8),
    "L29": ("7.4 V8 OHV Vortec 7400 big-block (C/K2500-3500 1996-2000, 290hp)", "Petrol", 7400, 290, 8),
    "LY7": ("3.6 V6 DOHC High Feature VVT (Acadia/Outlook/Enclave 2007, 275hp)", "Petrol", 3564, 275, 6),
    "LM4": ("5.3 V8 Vortec 5300 aluminium block (Envoy XL/Denali + SSR 2003-2005, 290-300hp)", "Petrol", 5328, 300, 8),
    "LH6": ("5.3 V8 Vortec 5300 w/ Displacement on Demand (Envoy Denali 2006-2009, 300hp)", "Petrol", 5328, 300, 8),
    "L83": ("5.3 V8 EcoTec3 DI + AFM (Silverado/Sierra/Tahoe/Yukon 2014-2019, 355hp)", "Petrol", 5328, 355, 8),
    "LAP": ("2.2 I4 Ecotec VVT (Cobalt/HHR/G5 2007-2010, 148-155hp)", "Petrol", 2198, 149, 4),
    "LKW": ("2.5 I4 Ecotec DI (Impala 2014-2020, 195-197hp)", "Petrol", 2457, 196, 4),
    "LFV": ("1.5 I4 Ecotec Turbo DI (Malibu/Equinox 2016+, 160-163hp)", "Petrol", 1490, 160, 4),
    "LYX": ("1.5 I4 Ecotec Turbo DI (Terrain/Equinox 2018-2025, 170hp / 175hp from 2021)", "Petrol", 1490, 170, 4),
    "LH7": ("1.6 I4 turbodiesel (Terrain/Equinox 2018-2019, 137hp)", "Diesel", 1598, 137, 4),
    "LK0": ("2.5 I4 Turbo DI, Cylinder Set Strategy (Acadia/Traverse 2024+, 328hp)", "Petrol", 2500, 328, 4),
    "G13BB": ("1.3 I4 SOHC 16v Suzuki (Chevrolet/Geo Metro 1998-2001, 79hp)", "Petrol", 1298, 79, 4),
    "G16B": ("1.6 I4 SOHC 16v Suzuki (Chevrolet Tracker 1999-2004, 97hp)", "Petrol", 1590, 97, 4),
    "H25A": ("2.5 V6 DOHC Suzuki (Chevrolet Tracker LT 2001-2004, 165hp)", "Petrol", 2493, 165, 6),
    "Ultium e4WD (Hummer EV)": ("GM Ultium tri-motor e4WD, 205 kWh (Hummer EV 2022-2025, 1000hp combined)", "Electric", None, 1000, None),
}

# (MODEL, y0, y1, cc, vin, target, evidence, power_fill)
R = [
    # ===================== GMC =====================
    # --- Acadia (Lambda / C1) ---
    ("ACADIA", 2007, 2007, None, None, "LY7", "2007 Acadia (launch year) = LY7 3.6 High Feature V6 275hp [GMLINEUP][NEW]", 275),
    ("ACADIA", 2008, 2012, None, None, "LLT", "Acadia 2008-2012 = LLT 3.6 V6 direct injection 288hp [GMLINEUP][GMVOCAB]", 288),
    ("ACADIA", 2013, 2016, None, None, "LFX", "Acadia 2013-2016 = LFX 3.6 V6 288hp (Lambda tune) [GMLINEUP][GMVOCAB]", 288),
    ("ACADIA", 2017, 2017, None, None, "LCV", "2017 Acadia bare = LCV 2.5 I4 193hp base volume engine (3.6 LGX optional) [GMA_LK0][GMVOCAB]", 193),
    ("ACADIA", 2017, 2021, 2500, None, "LCV", "Acadia 2500CC (VIN A) = LCV 2.5 Ecotec DI 193hp [GMA_LK0][GMVOCAB]", 193),
    ("ACADIA", 2017, 2023, 3600, None, "LGX", "Acadia 3600CC (VIN S) = LGX 3.6 V6 310hp [GMA_LK0][GMVOCAB]", 310),
    ("ACADIA", 2020, 2021, 2000, None, "LSY", "Acadia 2000CC (VIN 4) 2020-21 = LSY 2.0 turbo 230hp [GMA_LK0][GMVOCAB]", 230),
    ("ACADIA", 2022, 2023, 2000, None, "LSY", "Acadia 2000CC 2022-23 = LSY 2.0 turbo 228hp (revised rating) [GMA_LK0][GMVOCAB]", 228),
    ("ACADIA", 2024, 2025, None, None, "LK0", "Acadia 2024-2025 = LK0 2.5 turbo 328hp, sole engine (V6 dropped) [GMA_LK0][NEW]", 328),
    # --- C3500 / chassis cab / pickup (6500 diesel + big blocks) ---
    ("C3500", 2000, 2002, 6500, None, "L65", "C3500 6500CC = L65 6.5 V8 turbodiesel 195hp (fuel -> Diesel) [GM65][NEW]", 195),
    ("C3500", 2000, 2000, 7400, None, "L29", "C3500 7400CC = L29 7.4 Vortec big-block 290hp (final year 2000) [GM74][NEW]", 290),
    ("C3500", 2001, 2002, 8100, None, "L18", "C3500 8100CC = L18 8.1 Vortec 8100 340hp (replaced the 7.4 for 2001) [GM74][GMVOCAB]", 340),
    ("CAB", 2000, 2000, 6500, None, "L65", "GMC chassis-cab 6500CC = L65 6.5 turbodiesel 195hp (fuel -> Diesel) [GM65][NEW]", 195),
    ("PICKUP", 2000, 2000, 6500, None, "L65", "GMC pickup 6500CC = L65 6.5 turbodiesel 195hp (fuel -> Diesel) [GM65][NEW]", 195),
    # --- Envoy ---
    ("ENVOY", 2000, 2000, None, None, "LU3", "2000 Envoy (GMT330 Jimmy-based trim) = LU3 4.3 Vortec V6 190hp [GMLINEUP][GMVOCAB]", 190),
    ("ENVOY", 2002, 2002, None, None, "LL8", "2002 Envoy (GMT360) = LL8 4.2 Atlas I6 270hp [JDP_ENVOY][GMVOCAB]", 270),
    ("ENVOY", 2003, 2005, None, None, "LL8", "Envoy bare 2003-2005 = LL8 4.2 Atlas I6 275hp [TCC_ENVOY][GMVOCAB]", 275),
    ("ENVOY", 2003, 2005, 4200, None, "LL8", "Envoy 4200CC 2003-2005 = LL8 4.2 I6 275hp [TCC_ENVOY][GMVOCAB]", 275),
    ("ENVOY", 2006, 2009, 4200, None, "LL8", "Envoy 4200CC 2006-2009 = LL8 4.2 I6 291hp (revised) [TCC_ENVOY][GMVOCAB]", 291),
    ("ENVOY", 2003, 2005, 5300, None, "LM4", "Envoy XL/Denali 5300CC 2003-2005 = LM4 5.3 Vortec 290hp [TCC_ENVOY][JDP_ENVOY][NEW]", 290),
    ("ENVOY", 2006, 2009, 5300, None, "LH6", "Envoy Denali 5300CC 2006-2009 = LH6 5.3 Vortec w/ Displacement on Demand 300hp [TCC_ENVOY][NEW]", 300),
    # --- Hummer EV ---
    ("HUMMER", 2022, 2025, None, None, "Ultium e4WD (Hummer EV)", "GMC Hummer EV = Ultium tri-motor e4WD 1000hp combined (fuel -> Electric; dual-motor 570-625hp trims from 2023 are a detune of the same unit) [CD_HUMMER][NEW]", 1000),
    # --- S/T platform ---
    ("JIMMY", 2000, 2005, None, None, "LU3", "Jimmy = LU3 4.3 Vortec V6 190hp sole engine [GMLINEUP][GMVOCAB]", 190),
    ("SAFARI", 2000, 2005, None, None, "LU3", "Safari van = LU3 4.3 Vortec V6 190hp sole engine [GMLINEUP][GMVOCAB]", 190),
    ("SONOMA", 2000, 2003, 2200, None, "LN2", "Sonoma 2200CC = LN2 2.2 OHV 120hp [GMLINEUP][GMVOCAB]", 120),
    ("SONOMA", 2000, 2003, 4300, None, "LU3", "Sonoma 4300CC = LU3 4.3 Vortec V6 190hp [GMLINEUP][GMVOCAB]", 190),
    ("SONOMA", 2004, 2004, None, None, "LN2", "2004 Sonoma bare (final year) = LN2 2.2 120hp base volume engine [GMLINEUP][GMVOCAB]", 120),
    # --- Savana ---
    ("SAVANA", 2000, 2001, 4300, None, "LU3", "Savana 4300CC = LU3 4.3 Vortec V6 200hp (van rating) [GMLINEUP][GMVOCAB]", 200),
    ("SAVANA", 2000, 2002, 6500, None, "L65", "Savana 6500CC = L65 6.5 turbodiesel 195hp (fuel -> Diesel) [GM65][NEW]", 195),
    ("SAVANA", 2003, 2003, None, None, "LU3", "2003 Savana bare = LU3 4.3 Vortec V6 200hp base volume engine [GMLINEUP][GMVOCAB]", 200),
    # --- Sierra ---
    ("SIERRA", 2000, 2001, 4300, None, "LU3", "Sierra 1500 4300CC = LU3 4.3 Vortec V6 200hp base engine [GMLINEUP][GMVOCAB]", 200),
    ("SIERRA", 2019, 2019, None, None, "L82", "2019 Sierra bare = L82 5.3 EcoTec3 355hp volume engine (T1 launch year) [GMLINEUP][GMVOCAB]", 355),
    ("SIERRA", 2022, 2022, 5300, None, "L84", "2022 Sierra 5300CC (VIN F) = L84 5.3 EcoTec3 DFM 355hp [GMLINEUP][GMVOCAB]", 355),
    ("SIERRA", 2024, 2025, None, None, "L84", "Sierra 2024-2025 bare = L84 5.3 EcoTec3 DFM 355hp volume engine [GMLINEUP][GMVOCAB]", 355),
    # --- Terrain ---
    ("TERRAIN", 2010, 2011, 2400, None, "LAF", "Terrain 2400CC 2010-2011 (VIN K) = LAF 2.4 Ecotec DI 182hp [CPP_TERRAIN][GMVOCAB]", 182),
    ("TERRAIN", 2012, 2017, 2400, None, "LEA", "Terrain 2400CC 2012-2017 (VIN K) = LEA 2.4 Ecotec DI 182hp [CPP_TERRAIN][GMVOCAB]", 182),
    ("TERRAIN", 2010, 2012, 3000, None, "LFW", "Terrain 3000CC (VIN 5) = LFW 3.0 V6 264hp [CPP_TERRAIN][GMVOCAB]", 264),
    ("TERRAIN", 2013, 2017, 3600, None, "LFX", "Terrain 3600CC (VIN 3) = LFX 3.6 V6 301hp [CPP_TERRAIN][GMVOCAB]", 301),
    ("TERRAIN", 2018, 2020, 1500, None, "LYX", "Terrain 1500CC (VIN V) = LYX 1.5 turbo 170hp [CPP_TERRAIN][NEW]", 170),
    ("TERRAIN", 2018, 2019, 1600, None, "LH7", "Terrain 1600CC (VIN U) = LH7 1.6 turbodiesel 137hp (fuel -> Diesel) [CPP_TERRAIN][NEW]", 137),
    ("TERRAIN", 2018, 2020, 2000, None, "LTG", "Terrain 2000CC (VIN X) = LTG 2.0 turbo 252hp [CPP_TERRAIN][GMVOCAB]", 252),
    ("TERRAIN", 2021, 2025, None, None, "LYX", "Terrain 2021-2025 = LYX 1.5 turbo 175hp, sole engine (2.0T dropped after 2020) [CPP_TERRAIN][NEW]", 175),
    # --- Yukon ---
    ("YUKON", 2016, 2018, None, None, "L83", "Yukon 2016-2018 = L83 5.3 EcoTec3 355hp volume engine (6.2 L86 on Denali) [GMLINEUP][NEW]", 355),
    ("YUKON", 2019, 2020, None, None, "L82", "Yukon 2019-2020 = L82 5.3 EcoTec3 355hp volume engine [GMLINEUP][GMVOCAB]", 355),
    ("YUKON", 2021, 2021, 5300, None, "L84", "2021 Yukon 5300CC = L84 5.3 EcoTec3 DFM 355hp [GMLINEUP][GMVOCAB]", 355),

    # ===================== Chevrolet =====================
    ("BLAZER", 2024, 2025, None, None, "LSY", "Blazer 2024-2025 bare = LSY 2.0 turbo 228hp, standard on 2LT/3LT/Premier (3.6 LGX 308 only on RS) [GMA_BLAZER][GMVOCAB]", 228),
    ("CAMARO", 2010, 2011, None, None, "LLT", "Camaro 2010-2011 base = LLT 3.6 V6 312hp volume engine (SS 6.2 optional) [GMLINEUP][GMVOCAB]", 312),
    ("CAMARO", 2012, 2013, None, None, "LFX", "Camaro 2012-2013 base = LFX 3.6 V6 323hp volume engine (SS 6.2 optional) [GMLINEUP][GMVOCAB]", 323),
    ("CAPTIVA", 2014, 2015, None, None, "LEA", "Captiva Sport (fleet-only Theta) = LEA 2.4 Ecotec DI 182hp volume engine [GMVOCAB]", 182),
    ("CAVALIER", 2001, 2001, None, None, "LN2", "2001 Cavalier = LN2 2.2 OHV 115hp base volume engine [GMLINEUP][GMVOCAB]", 115),
    ("COBALT", 2008, 2008, None, None, "LAP", "2008 Cobalt = LAP 2.2 Ecotec VVT 148hp base volume engine [GMLINEUP][NEW]", 148),
    ("CORVETTE", 2001, 2004, None, None, "LS1", "Corvette C5 2001-2004 = LS1 5.7 V8 350hp base (Z06 LS6 385-405 optional) [GMLINEUP][GMVOCAB]", 350),
    ("CUTAWAY", 2003, 2005, None, None, "LQ4", "Express/G-series cutaway chassis = LQ4 6.0 Vortec V8 300hp standard engine [GMLINEUP][GMVOCAB]", 300),
    ("EPICA", 2004, 2006, None, None, "X25D1", "Chevrolet Epica (Canada only, Daewoo Magnus/Suzuki Verona sibling) = 2.5 transverse inline-six 155hp [EPICA][GMVOCAB]", 155),
    ("HHR", 2008, 2008, None, None, "LAP", "2008 HHR = LAP 2.2 Ecotec VVT 149hp base volume engine (2.4 LE5 172 optional) [GMLINEUP][NEW]", 149),
    ("IMPALA", 2014, 2020, None, None, "LKW", "Impala (10th gen) = LKW 2.5 Ecotec DI 196hp base volume engine (3.6 LFX 305 optional) [GMLINEUP][NEW]", 196),
    ("MALIBU", 2012, 2012, 3600, None, "LFX", "2012 Malibu 3600CC (VIN 7) = LFX 3.6 V6 252hp [GMLINEUP][GMVOCAB]", 252),
    ("MALIBU", 2014, 2014, 2400, None, "LUK", "2014 Malibu 2400CC = LUK 2.4 eAssist mild hybrid 182hp [GMVOCAB]", 182),
    ("MALIBU", 2016, 2016, None, None, "LFV", "2016 Malibu bare = LFV 1.5 turbo 160hp base volume engine (2.0T LTG optional) [GMLINEUP][NEW]", 160),
    ("METRO", 2000, 2001, None, None, "G13BB", "Chevrolet Metro = 1.3 Suzuki G13BB 79hp volume engine (1.0 I3 55hp 3-door only) [GMLINEUP][NEW]", 79),
    ("OPTRA", 2004, 2008, None, None, "T20SED", "Chevrolet Optra (Canada only, Daewoo Lacetti) = 2.0 D-TEC I4 119hp sole engine [OPTRA][GMVOCAB]", 119),
    ("OPTRA5", 2004, 2008, None, None, "T20SED", "Chevrolet Optra5 hatchback (Canada only) = same 2.0 D-TEC I4 119hp [OPTRA][GMVOCAB]", 119),
    ("RV", 2001, 2002, 6500, None, "L65", "GM P-chassis motorhome 6500CC = L65 6.5 turbodiesel 195hp (fuel -> Diesel) [GM65][NEW]", 195),
    ("RV", 2003, 2005, None, None, "L18", "GM P32 motorhome chassis 2003-2005 = L18 8.1 Vortec 8100 340hp, sole engine after the 6.5 diesel was dropped [GM74][GMVOCAB]", 340),
    ("S10", 2000, 2004, None, None, "LN2", "S-10 bare = LN2 2.2 OHV 120hp base volume engine (4.3 LU3 optional) [GMLINEUP][GMVOCAB]", 120),
    ("SSR", 2003, 2004, None, None, "LM4", "SSR 2003-2004 = LM4 5.3 Vortec V8 300hp (6.0 LS2 arrived 2005) [GMLINEUP][NEW]", 300),
    ("SILVERADO", 2019, 2019, None, None, "L82", "2019 Silverado bare = L82 5.3 EcoTec3 355hp volume engine (T1 launch year) [GMLINEUP][GMVOCAB]", 355),
    ("SILVERADO", 2024, 2025, None, None, "L84", "Silverado 2024-2025 bare = L84 5.3 EcoTec3 DFM 355hp volume engine [GMLINEUP][GMVOCAB]", 355),
    ("TRACKER", 2000, 2000, 1600, None, "G16B", "Tracker 1600CC = Suzuki G16B 1.6 97hp base engine [GMLINEUP][NEW]", 97),
    ("TRACKER", 2004, 2004, None, None, "H25A", "2004 Tracker bare (final year, LT only) = H25A 2.5 V6 165hp [GMLINEUP][NEW]", 165),
]

TRIM = {
    ("ACADIA", 2015, "ACADIADENALI"): ("LFX", "2015 Acadia Denali = LFX 3.6 V6 288hp (trim, not an engine change) [GMLINEUP]", 288, None),
    ("ACADIA", 2015, "ACADIASLTAWD"): ("LFX", "2015 Acadia SLT AWD = LFX 3.6 288hp [GMLINEUP]", 288, None),
    ("ACADIA", 2015, "ACADIASLTFWD"): ("LFX", "2015 Acadia SLT FWD = LFX 3.6 288hp [GMLINEUP]", 288, None),
    ("ACADIA", 2015, "ACADIASLEAWD"): ("LFX", "2015 Acadia SLE AWD = LFX 3.6 288hp [GMLINEUP]", 288, None),
    ("ACADIA", 2015, "ACADIASLEFWD"): ("LFX", "2015 Acadia SLE FWD = LFX 3.6 288hp [GMLINEUP]", 288, None),
    ("CAPTIVA", 2015, "CAPTIVASPORT"): ("LEA", "2015 Captiva Sport = LEA 2.4 182hp [GMVOCAB]", 182, None),
}

SKIPS = {
    ("SIERRA", 2012, 6000, "J", None):
        "2012 Sierra 6000CC VIN J: GM reused VIN digit J across the 6.0L gaseous-fuel LC8 and the "
        "6.2L L86 of later years; for MY2012 HD the 6.0L could be either L96 (360hp petrol) or LC8 "
        "(306hp bi-fuel CNG/LPG) and no source consulted resolves digit J for that year - left LEMON "
        "rather than guess between two engines that differ by 54hp and by fuel type.",
}

IDENTITY = {
    "LU3": ("Petrol", 4300), "LN2": ("Petrol", 2200), "LL8": ("Petrol", 4157),
    "LFX": ("Petrol", 3564), "LLT": ("Petrol", 3600), "LGX": ("Petrol", 3600),
    "LCV": ("Petrol", 2500), "LSY": ("Petrol", 1998), "LTG": ("Petrol", 1998),
    "LAF": ("Petrol", 2400), "LEA": ("Petrol", 2400), "LUK": ("Petrol", 2400),
    "LFW": ("Petrol", 2997), "LQ4": ("Petrol", 5967), "L18": ("Petrol", 8128),
    "LS1": ("Petrol", 5665), "X25D1": ("Petrol", 2500), "T20SED": ("Petrol", 1998),
    "L82": ("Petrol", 5300), "L84": ("Petrol", 5300),
}

ROW_FIXES = {
    # cylinder counts recorded as 8 on engines that are not V8s
    "LU3": {"engine_type": "4.3 V6 OHV Vortec 4300 (S/T-platform 190hp / full-size van-pickup 200hp)",
            "cylinders": 6, "data_confidence": "STEP36_VERIFIED"},
    "LL8": {"engine_type": "4.2 I6 DOHC Atlas (TrailBlazer/Envoy/Rainier: 270hp '02, 275hp '03-05, 291hp '06-09)",
            "cylinders": 6, "data_confidence": "STEP36_VERIFIED"},
    "LFX": {"engine_type": "3.6 V6 DI High Feature (Camaro 323 / Terrain-Equinox 301 / Acadia-Traverse 288 / Malibu 252hp)",
            "cylinders": 6, "data_confidence": "STEP36_VERIFIED"},
    "L84": {"engine_type": "5.3 V8 EcoTec3 DI + Dynamic Fuel Management (Silverado/Sierra/Tahoe/Yukon 2019+, 355hp)",
            "power_hp": 355, "cylinders": 8, "data_confidence": "STEP36_VERIFIED"},
    "LCV": {"cylinders": 4}, "LSY": {"cylinders": 4}, "LTG": {"cylinders": 4},
    "LGX": {"cylinders": 6}, "LEA": {"cylinders": 4}, "LAF": {"cylinders": 4},
    "LUK": {"cylinders": 4}, "L82": {"cylinders": 8},
}

lib.run_batch(lib.Cfg(
    brand=["GMC", "Chevrolet"], step_tag="step36", csv_num=44,
    lemon_baseline=1368, engines_baseline=6986,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, SKIP_NOTES=SKIPS,
    IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={"L65": "Diesel", "LH7": "Diesel",
                        "Ultium e4WD (Hummer EV)": "Electric"},
    expect_mapped=208, expect_skipped=1,
))
