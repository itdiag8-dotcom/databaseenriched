"""Step 35 (Step 5, batch 26): replace LEMON_ACURA codes with real Honda/Acura engine codes.

180 rows. All US/Canada-market petrol or hybrid (Acura never sold a diesel in North America),
so every decode is lineup + displacement + VIN-engine-digit driven:

- Legacy C/D/J engines: 1.6EL D16Y8 127 (CA), 1.7EL D17A2 127 (CA), 3.2CL/3.2TL J32A1 225,
  3.5RL C35A5 210, NSX/NSX-T C32B 290, Integra (DC) B18B1 140 volume-default, RSX K20A3 160
  volume-default (Type-S K20A2/K20Z1 optional), CSX K20Z2 155 (Type-S K20Z3 optional).
- MDX: J35A3 240 ('01-02) -> J35A5 265 ('03-06) -> J37A1 300 ('07-13) -> J35Y5 290 ('14-25),
  J30Y1 3.0 Sport Hybrid 321 combined ('17-20 = the Hybrid-fuel rows), J30AC 3.0T Type S 355 ('22+).
- RDX: K23A1 2.3T 240 ('07-12) -> J35Z2 273 ('13-15) / 279 ('16-18) -> K20C4 2.0T 272 ('19+).
- TL: J32A1 225 ('99-03 as "3.2TL") -> J32A3 270 ('04-06) / 258 ('07-08) -> J35Z6 280 ('09-14).
- TSX: K24A2 200/205 ('04-08) -> K24Z3 201 ('09-14) + J35Z6 280 V6 (3500CC rows).
- TLX: K24W7 206 / J35Y6 290 ('15-20) -> K20C6 2.0T 272 / J30AC 3.0T 355 ('21-25).
- ILX: R20A5 150 (2.0) / K24Z7 201 (2.4) / LEA1 1.5 IMA 111 ('13-15) -> K24V7 201 ('16-22).
- Integra (DE): L15CA 200 (1500CC) / K20C8 Type S 320 (2000CC).
- RL: J35A8 300 ('05-08) -> J37A2 300 ('09-12).  ZDX: J37A5 300.  RLX: J35Y4 310 + SH 377.
- ADX 2025: L15BE 1.5T 190.  NSX (NC1): JNC1 3.5TT hybrid 573 ('17-21) / 600 (Type S '22).

VIN digit tokens in the crawl codes (ILX 1/2/6, MDX 2/YD2, RDX TB1/TB2/3/4, TSX 2/4) are
drivetrain/chassis discriminators within one displacement, so displacement alone resolves them;
they are retained in the evidence strings for traceability.
"""
import step5_lemon_lib as lib

CIT = {
    "ACNEWS15": "https://acuranews.com/en-US/releases/release-0d5860f808ceb9825e662cfd5a076ff9-acura-15-liter-turbo-engine (official Acura engine release: Integra 2023+ = L15CA 200hp @6000; 2025 ADX = L15BE 1.5T; Integra Type S = 2.0T 320hp)",
    "ACHYB": "https://acuranews.com/en-US/releases/release-9cc3a6ebff00753bc08baae86a053159-acura-sport-hybrid-super-handling-all-wheel-drive (official: RLX Sport Hybrid 2014-2020 3.5 V6 = 377hp total; MDX Sport Hybrid 2017-2020 3.0 V6 = 321hp total; NSX 2017-2021 3.5TT = 573hp, 2022 Type S = 600hp)",
    "PRRJ": "https://powerrevracing.com/pages/j-engine-codes (US J-series map: J35A3 = 2001-02 MDX; J35A5 = 2003-06 MDX; J35A8 = 2005-08 RL + 2007-08 TL Type-S; J35Y4 = 2014-16 RLX; J35Y5 = 2014-16 MDX; J37A1 = 2007-13 MDX; J37A2 = 2009-12 RL; J30AC = 2021-25 TLX Type S + 2022-25 MDX Type S)",
    "WIKIJ": "https://en.wikipedia.org/wiki/Honda_J_engine (J35Z2: 2013-2018 Acura RDX, 273hp 2013-15 / 279hp 2016-18; J35Y6: 2015-2020 Acura TLX 290hp @6200)",
    "WIKIMDX": "https://en.wikipedia.org/wiki/Acura_MDX (gen1 J35A3/J35A5 240->265; gen2 J37A1 3.7; gen3 J35Y5 3.5 290 + J30Y1 3.0 hybrid 321 combined; gen4 J35Y5 + J30AC turbo Type S)",
    "WIKIRDX": "https://en.wikipedia.org/wiki/Acura_RDX (gen1 2.3 K23A1 turbo 240hp; gen2 3.5 J35Z2 273hp, 2016 facelift 279hp; gen3 2.0 K20C4 turbo 272hp)",
    "WIKITLX": "https://en.wikipedia.org/wiki/Acura_TLX (gen1 UB1 2.4 K24W7 206hp / UB2-UB3 3.5 J35Y6 290hp; gen2 UB5-UB6 2.0 K20C6 turbo 272hp / UB7 Type S 3.0 J30AC turbo 355hp)",
    "WIKIILX": "https://en.wikipedia.org/wiki/Acura_ILX (1.5 LEA IMA hybrid 111hp 2013-14; 2.0 R20A 150hp 5AT 2013-15; 2.4 K24Z7 201hp 6MT 2013-15; 2.4 K24V7 201hp 8DCT 2016-22)",
    "WIKIINT": "https://en.wikipedia.org/wiki/Acura_Integra_(2023) (DE4 = 1.5 L15CA 200hp; DE5 Type S = 2.0 K20C8 320hp)",
    "RPMRONS": "https://www.rpmrons.com/Acurakits1.html (rebuild-kit application table: RDX K20C4 2019-2022 1996cc; ILX R20A5 2013-2015 1997cc; RSX K20A3 2002-2006; RDX K23A1 2007-2012 2300cc; ILX K24Z7 2013-2015; TSX K24Z3 2009-2014)",
    "TROUBLE": "https://www.troublecodes.net/acura/rdx-2-3l-tl-3-23-5l-tsx-2-4l-2004-2009/ (OBD engine identification: RDX 2.3 2007-09 = K23A1; TL 3.2 2004-08 = J32A3; TL 3.5 2007-08 = J35A8; TSX 2.4 2004-09 = K24A2; MDX 3.5 2000-06 = J35A3/5; MDX 3.7 2007-09 = J37A1)",
    "DNJ": "https://www.refmariogarcia.com/wp-content/uploads/2024/12/DNJ_PDF_CATALOG_7-27-2023-2.pdf (TLX 2015-20 2.4L = K24V7/K24W7, 3.5L = J35Y4/J35Y5/J35Y6; TLX Turbo 2021-22 2.0L = K20C6, 3.0L = J30AC; MDX 03-06 = J35A5; MDX 07-09 = J37A1; MDX 2010-13 = J37A1/J37A2/J37A4)",
    "AUTOPIAN": "https://www.theautopian.com/the-acura-ilx-is-now-a-dirt-cheap-luxury-civic-with-extra-power-and-an-available-dct/ (Acura 1.6EL = D16Y8 127hp; CSX = K20Z2 155hp base / K20Z3 197hp Type-S, 2006-2011)",
    "ELWIKI": "https://acura.fandom.com/wiki/Acura_EL + https://grokipedia.com/page/Acura_EL (1.6EL 1997-2000 D16Y8 127hp@6600; 1.7EL 2001-2005 1.7 SOHC VTEC 127hp@6300 / 114 lb-ft, D17A2-family)",
    "MDXERS": "https://www.mdxers.org/threads/2010-mdx-engine-destroyed.104898/page-3 (J37A1 2007-2013 MDX 3664cc 295-300hp; J37A2 2009-2012 RL; J37A4 2009-2014 TL SH-AWD 305hp; J37A5 2010-2013 Acura ZDX)",
    "ULTRLX": "https://www.ultimatespecs.com/car-specs/Acura/124490/Acura-RLX-2018-35-V6-Sport-Hybrid-SH-AWD.html (RLX Sport Hybrid engine code Honda J35Y4 - VCM Earth Dreams, 3471cc, 377hp total system)",
    "RLXPR": "https://acurazine.com/forums/3g-rlx-2013-412/acura-rlx-reviews-sport-hybrid-reviews-pg-21-a-875410/page35/ (Acura PR: RLX P-AWS 3.5 DI SOHC i-VTEC = 310hp SAE net / 272 lb-ft; Sport Hybrid = 377hp total)",
    "ACVOCAB": "DB Honda/Acura vocabulary already present: J32A1 3210/224, J35A3 3471, J35A5 3471, J35A8 3471, J37A2 3664, C35A5 3474/208, D16Y8 1590/127, D17A2 1668, K20A3 1998/160, K20Z2 1998/155, K24A2 2354, K24Z3 2354/201, K24Z7 2354, R20A5 1997, LEA1 1497 Hybrid, J35Z2 3471/271, K20C4 1996, L15BE 1500",
    "LINEUP": "US/Canada Acura lineup volume-defaults: 3.2CL/3.2TL base 3.2 V6 225hp (Type-S 260 optional); 3.5RL sole 3.5 210hp; Integra (DC) LS/GS 1.8 140hp volume (GS-R 170 / Type R 195 optional); RSX base 160hp volume (Type-S optional); CSX base 155hp volume (Type-S 197 optional); NSX 6MT 3.2 290hp volume (3.0 automatic dropped before 2000-MY rows); TSX 2.4 200hp 2004-05 / 205hp 2006-08; TL 3.2 270hp 2004-06 / 258hp (SAE-revised) 2007-08; RL 300hp 2005-12; ZDX 3.7 300hp",
}

# code -> (engine_type, fuel, cc, hp, cylinders)
NE = {
    "K24V7": ("2.4 I4 DOHC i-VTEC Earth Dreams DI (ILX 2016-2022, 201hp, 8DCT)", "Petrol", 2356, 201, 4),
    "B18B1": ("1.8 I4 DOHC (Integra LS/GS/SE 1994-2001, 140hp)", "Petrol", 1834, 140, 4),
    "L15CA": ("1.5 I4 VTEC Turbo DI (Integra DE4 2023+ / Civic Si, 200hp)", "Petrol", 1498, 200, 4),
    "K20C8": ("2.0 I4 VTEC Turbo DI (Integra Type S DE5 2024+, 320hp; FL5 Civic Type R K20C1 derivative)", "Petrol", 1996, 320, 4),
    "J37A1": ("3.7 V6 SOHC VTEC (MDX 2007-2013, 300hp)", "Petrol", 3664, 300, 6),
    "J35Y5": ("3.5 V6 SOHC i-VTEC Earth Dreams DI + VCM (MDX 2014-2025, 290hp)", "Petrol", 3471, 290, 6),
    "J30Y1": ("3.0 V6 SOHC i-VTEC Sport Hybrid SH-AWD (MDX Sport Hybrid 2017-2020, 321hp total system)", "Hybrid", 2997, 321, 6),
    "J30AC": ("3.0 V6 DOHC twin-scroll turbo DI Type S (TLX Type S 2021-25 / MDX Type S 2022-25, 355hp)", "Petrol", 2997, 355, 6),
    "C32B": ("3.2 V6 DOHC VTEC (NSX / NSX-T 6MT 1997-2005, 290hp)", "Petrol", 3179, 290, 6),
    "JNC1": ("3.5 V6 DOHC twin-turbo Sport Hybrid SH-AWD (NSX NC1 2017-2022, 573hp / 600hp Type S)", "Hybrid", 3493, 573, 6),
    "K23A1": ("2.3 I4 DOHC i-VTEC Turbo (RDX 2007-2012, 240hp)", "Petrol", 2300, 240, 4),
    "J35Y4": ("3.5 V6 SOHC i-VTEC Earth Dreams DI (RLX P-AWS 2014-2020, 310hp)", "Petrol", 3471, 310, 6),
    "J35Y4 SH (Sport Hybrid)": ("3.5 V6 DI + 3-motor Sport Hybrid SH-AWD (RLX Sport Hybrid 2014-2020, 377hp total system)", "Hybrid", 3471, 377, 6),
    "J32A3": ("3.2 V6 SOHC VTEC (TL 2004-2008, 270hp / 258hp SAE-revised 2007-08)", "Petrol", 3210, 270, 6),
    "J35Z6": ("3.5 V6 SOHC i-VTEC (TL 2009-2014 FWD / TSX V6 2010-2014, 280hp)", "Petrol", 3471, 280, 6),
    "K24W7": ("2.4 I4 DOHC i-VTEC Earth Dreams DI (TLX 2015-2020, 206hp, 8DCT)", "Petrol", 2356, 206, 4),
    "J35Y6": ("3.5 V6 SOHC i-VTEC Earth Dreams DI + VCM (TLX 2015-2020, 290hp)", "Petrol", 3471, 290, 6),
    "K20C6": ("2.0 I4 VTEC Turbo DI (TLX 2021-2025 non-Type-S, 272hp)", "Petrol", 1996, 272, 4),
    "J37A5": ("3.7 V6 SOHC VTEC (ZDX 2010-2013, 300hp)", "Petrol", 3664, 300, 6),
}

# (MODEL, y0, y1, cc, vin, target, evidence, power_fill)
R = [
    # --- Canada-only compacts ---
    ("1.6EL", 2000, 2000, None, None, "D16Y8", "Acura 1.6EL (CA, Domani/Civic-based) = D16Y8 1.6 SOHC VTEC 127hp sole engine [ELWIKI][AUTOPIAN][ACVOCAB]", 127),
    ("1.7EL", 2003, 2004, None, None, "D17A2", "Acura 1.7EL (CA) = 1.7 SOHC VTEC 127hp@6300 sole engine, D17A2 family [ELWIKI][AUTOPIAN][ACVOCAB]", 127),
    ("CSX", 2006, 2009, None, None, "K20Z2", "CSX (CA) base = K20Z2 2.0 i-VTEC 155hp volume-default (Type-S K20Z3 197 optional) [AUTOPIAN][LINEUP][ACVOCAB]", 155),
    # --- 1st-gen nameplates ---
    ("3.2CL", 2001, 2003, None, None, "J32A1", "2001-03 CL 3.2 V6 225hp volume-default (Type-S J32A2 260 optional) [LINEUP][ACVOCAB]", 225),
    ("3.2TL", 2000, 2003, None, None, "J32A1", "1999-2003 TL (UA5) 3.2 V6 J32A1 225hp volume-default (Type-S 260 from 2002) [LINEUP][ACVOCAB]", 225),
    ("3.5RL", 2000, 2004, None, None, "C35A5", "3.5RL (KA9) = C35A5 3.5 SOHC V6 210hp sole engine [LINEUP][ACVOCAB]", 210),
    ("INTEGRA", 2000, 2001, None, None, "B18B1", "Integra (DC) LS/GS 1.8 DOHC B18B1 140hp volume-default (GS-R B18C1 170 / Type R B18C5 195 optional) [LINEUP][NEW]", 140),
    ("RSX", 2002, 2006, None, None, "K20A3", "RSX base = K20A3 2.0 i-VTEC 160hp volume-default (Type-S K20A2 200 / K20Z1 210 optional) [RPMRONS][LINEUP][ACVOCAB]", 160),
    ("NSX", 2000, 2005, None, None, "C32B", "NSX 6MT 1997-2005 = C32B 3.2 V6 DOHC VTEC 290hp [LINEUP][NEW]", 290),
    ("NSX-T", 2000, 2003, None, None, "C32B", "NSX-T targa shares C32B 3.2 290hp with coupe [LINEUP][NEW]", 290),
    # --- NSX NC1 ---
    ("NSX", 2017, 2021, None, None, "JNC1", "NSX NC1 = JNC1 3.5 twin-turbo V6 + 3-motor Sport Hybrid SH-AWD, 573hp total (fuel -> Hybrid) [ACHYB][NEW]", 573),
    ("NSX", 2022, 2022, None, None, "JNC1", "2022 NSX Type S = JNC1 600hp total system (final year, Type S only) [ACHYB][NEW]", 600),
    # --- ILX ---
    ("ILX", 2013, 2015, 2000, None, "R20A5", "ILX 2.0 (VIN 1) = R20A5 150hp 5AT, 2013-2015 only [WIKIILX][RPMRONS][ACVOCAB]", 150),
    ("ILX", 2013, 2015, 2400, None, "K24Z7", "ILX 2.4 (VIN 2/6) = K24Z7 201hp 6MT, 2013-2015 (Civic Si engine) [WIKIILX][RPMRONS][ACVOCAB]", 201),
    ("ILX", 2013, 2014, 1500, None, "LEA1", "ILX Hybrid = 1.5 LEA IMA 111hp combined, 2013-2014 only (Civic Hybrid powertrain) [WIKIILX][ACVOCAB]", 111),
    ("ILX", 2016, 2022, None, None, "K24V7", "ILX 2016-2022 = sole K24V7 2.4 Earth Dreams DI 201hp + 8DCT (2.0 and hybrid dropped) [WIKIILX][NEW]", 201),
    # --- Integra DE ---
    ("INTEGRA", 2023, 2023, None, None, "L15CA", "2023 Integra bare = L15CA 1.5T 200hp (sole engine; Type S arrived MY2024) [ACNEWS15][WIKIINT][NEW]", 200),
    ("INTEGRA", 2024, 2025, 1500, None, "L15CA", "Integra DE4 1.5T = L15CA 200hp@6000 [ACNEWS15][WIKIINT][NEW]", 200),
    ("INTEGRA", 2024, 2025, 2000, None, "K20C8", "Integra Type S DE5 2.0T = K20C8 320hp@6500 [ACNEWS15][WIKIINT][NEW]", 320),
    # --- MDX ---
    ("MDX", 2001, 2002, None, None, "J35A3", "MDX YD1 2001-02 = J35A3 3.5 SOHC VTEC 240hp [WIKIMDX][PRRJ][TROUBLE][ACVOCAB]", 240),
    ("MDX", 2003, 2006, None, None, "J35A5", "MDX YD1 2003-06 = J35A5 3.5 265hp (+20hp update) [WIKIMDX][PRRJ][TROUBLE][ACVOCAB]", 265),
    ("MDX", 2007, 2013, None, None, "J37A1", "MDX YD2 2007-2013 = J37A1 3.7 SOHC VTEC 300hp sole engine [WIKIMDX][PRRJ][MDXERS][NEW]", 300),
    ("MDX", 2013, 2013, 3700, None, "J37A1", "2013 MDX 3700CC (VIN 2 / YD2) = J37A1 3.7 300hp [WIKIMDX][DNJ][NEW]", 300),
    ("MDX", 2014, 2022, None, None, "J35Y5", "MDX YD3 petrol = J35Y5 3.5 Earth Dreams DI 290hp volume engine [WIKIMDX][PRRJ][NEW]", 290),
    ("MDX", 2023, 2025, 3500, None, "J35Y5", "MDX YD9/YE1 2022+ 3500CC = J35Y5 3.5 290hp [WIKIMDX][NEW]", 290),
    ("MDX", 2023, 2025, 3000, None, "J30AC", "MDX Type S 3000CC = J30AC 3.0 twin-scroll turbo V6 355hp [WIKIMDX][PRRJ][DNJ][NEW]", 355),
    # --- RDX ---
    ("RDX", 2007, 2012, None, None, "K23A1", "RDX TB1/TB2 2007-2012 = K23A1 2.3 i-VTEC turbo 240hp sole engine [WIKIRDX][TROUBLE][RPMRONS][NEW]", 240),
    ("RDX", 2012, 2012, 2300, None, "K23A1", "2012 RDX 2300CC (VIN TB1 FWD / TB2 AWD) = K23A1 240hp [WIKIRDX][RPMRONS][NEW]", 240),
    ("RDX", 2013, 2015, None, None, "J35Z2", "RDX TB3/TB4 2013-2015 = J35Z2 3.5 V6 273hp [WIKIJ][WIKIRDX][ACVOCAB]", 273),
    ("RDX", 2013, 2013, 3500, None, "J35Z2", "2013 RDX 3500CC (VIN 3 FWD / 4 AWD) = J35Z2 273hp [WIKIJ][ACVOCAB]", 273),
    ("RDX", 2016, 2018, None, None, "J35Z2", "RDX 2016-2018 facelift = same J35Z2 revised to 279hp (VCM gen3) [WIKIJ][WIKIRDX][ACVOCAB]", 279),
    ("RDX", 2019, 2025, None, None, "K20C4", "RDX TC1/TC2 2019+ = K20C4 2.0 VTEC Turbo DI 272hp sole engine [WIKIRDX][RPMRONS][ACVOCAB]", 272),
    # --- RL / RLX ---
    ("RL", 2005, 2008, None, None, "J35A8", "RL KB1 2005-2008 = J35A8 3.5 V6 300hp sole engine [PRRJ][TROUBLE][ACVOCAB]", 300),
    ("RL", 2009, 2012, None, None, "J37A2", "RL KB2 2009-2012 = J37A2 3.7 V6 300hp sole engine [PRRJ][MDXERS][ACVOCAB]", 300),
    ("RLX", 2014, 2020, None, None, "J35Y4", "RLX P-AWS = J35Y4 3.5 DI SOHC i-VTEC 310hp [PRRJ][RLXPR][NEW]", 310),
    ("ZDX", 2010, 2013, None, None, "J37A5", "ZDX 2010-2013 = J37A5 3.7 V6 300hp sole engine [MDXERS][NEW]", 300),
    # --- TL ---
    ("TL", 2004, 2006, None, None, "J32A3", "TL UA6/UA7 2004-2006 = J32A3 3.2 V6 270hp [TROUBLE][NEW]", 270),
    ("TL", 2007, 2008, None, None, "J32A3", "TL 2007-2008 = J32A3 3.2, 258hp under revised SAE rating (Type-S J35A8 286 optional) [TROUBLE][LINEUP][NEW]", 258),
    ("TL", 2009, 2014, None, None, "J35Z6", "TL UA8/UA9 2009-2014 FWD = J35Z6 3.5 V6 280hp volume engine (SH-AWD J37A4 305 optional) [MDXERS][LINEUP][NEW]", 280),
    # --- TSX ---
    ("TSX", 2004, 2005, None, None, "K24A2", "TSX CL9 2004-2005 = K24A2 2.4 i-VTEC 200hp sole engine [TROUBLE][ACVOCAB]", 200),
    ("TSX", 2006, 2008, None, None, "K24A2", "TSX CL9 2006-2008 = K24A2 2.4 revised to 205hp [TROUBLE][LINEUP][ACVOCAB]", 205),
    ("TSX", 2009, 2014, None, None, "K24Z3", "TSX CU2 2009-2014 bare = K24Z3 2.4 201hp volume engine [RPMRONS][ACVOCAB]", 201),
    ("TSX", 2012, 2013, 2400, None, "K24Z3", "TSX 2400CC (VIN 2) = K24Z3 2.4 201hp [RPMRONS][ACVOCAB]", 201),
    ("TSX", 2012, 2013, 3500, None, "J35Z6", "TSX V6 3500CC (VIN 4) = J35Z6 3.5 280hp (2010-2014 sedan only) [MDXERS][LINEUP][NEW]", 280),
    # --- TLX ---
    ("TLX", 2015, 2020, 2400, None, "K24W7", "TLX UB1 2.4 = K24W7 Earth Dreams DI 206hp + 8DCT [WIKITLX][DNJ][NEW]", 206),
    ("TLX", 2015, 2020, 3500, None, "J35Y6", "TLX UB2/UB3 3.5 = J35Y6 290hp@6200 + 9AT [WIKITLX][WIKIJ][NEW]", 290),
    ("TLX", 2021, 2021, None, None, "K20C6", "2021 TLX bare = K20C6 2.0T 272hp volume engine (Type S arrived later in MY2021) [WIKITLX][DNJ][NEW]", 272),
    ("TLX", 2022, 2025, 2000, None, "K20C6", "TLX UB5/UB6 2.0T = K20C6 272hp [WIKITLX][DNJ][NEW]", 272),
    ("TLX", 2022, 2025, 3000, None, "J30AC", "TLX Type S UB7 3.0T = J30AC 355hp [WIKITLX][PRRJ][DNJ][NEW]", 355),
    # --- ADX ---
    ("ADX", 2025, 2025, None, None, "L15BE", "2025 ADX = L15BE 1.5T 190hp@6000 sole engine [ACNEWS15][ACVOCAB]", 190),
]

# (MODEL, year|None, POST) -> (target, evidence, power_fill, fuel_fix)
TRIM = {
    ("MDX", 2015, "MDXBASE"): ("J35Y5", "2015 MDX base FWD = J35Y5 3.5 290hp [WIKIMDX][PRRJ]", 290, None),
    ("MDX", 2015, "MDXSHAWD"): ("J35Y5", "2015 MDX SH-AWD = same J35Y5 290hp (AWD is a driveline option, not an engine) [WIKIMDX][PRRJ]", 290, None),
    ("RDX", 2015, "RDXFWD"): ("J35Z2", "2015 RDX FWD = J35Z2 3.5 273hp [WIKIJ][WIKIRDX]", 273, None),
    ("RDX", 2015, "RDXAWD"): ("J35Z2", "2015 RDX AWD = same J35Z2 273hp [WIKIJ][WIKIRDX]", 273, None),
    ("RLX", 2015, "RLX"): ("J35Y4", "2015 RLX (P-AWS trim slug) = J35Y4 3.5 310hp [PRRJ][RLXPR]", 310, None),
}


def extra(model, year, cc, vin, post, code):
    """Hybrid-fuel rows in the crawl identify Acura's Sport Hybrid variants, which carry a
    different engine from the same-year petrol row (MDX 3.0 J30Y1 / RLX 3.5 J35Y4 SH)."""
    mu = lib.norm_model(model)
    if mu == "MDX" and 2017 <= year <= 2020 and HYB.get((mu, year)):
        return ("J30Y1", "MDX Sport Hybrid (crawl fuel=Hybrid) = J30Y1 3.0 V6 + 3 motors, 321hp total [ACHYB][WIKIMDX][NEW]", "Hybrid", 321)
    if mu == "RLX" and 2014 <= year <= 2020 and HYB.get((mu, year)):
        return ("J35Y4 SH (Sport Hybrid)", "RLX Sport Hybrid (crawl fuel=Hybrid) = J35Y4-based 3.5 DI + 3 motors, 377hp total [ACHYB][ULTRLX][NEW]", "Hybrid", 377)
    return None


# rows whose crawl fuel column already reads Hybrid (Sport Hybrid trims)
HYB = {("MDX", 2018): True, ("MDX", 2020): True, ("RLX", 2016): True}

IDENTITY = {
    "D16Y8": ("Petrol", 1590), "D17A2": ("Petrol", 1668), "K20Z2": ("Petrol", 1998),
    "J32A1": ("Petrol", 3210), "C35A5": ("Petrol", 3474), "K20A3": ("Petrol", 1998),
    "R20A5": ("Petrol", 1997), "K24Z7": ("Petrol", 2354), "LEA1": ("Hybrid", 1497),
    "J35A3": ("Petrol", 3471), "J35A5": ("Petrol", 3471), "J35A8": ("Petrol", 3471),
    "J35Z2": ("Petrol", 3471), "K20C4": ("Petrol", 1996), "J37A2": ("Petrol", 3664),
    "K24A2": ("Petrol", 2354), "K24Z3": ("Petrol", 2354), "L15BE": ("Petrol", 1500),
}

ROW_FIXES = {
    # junk/placeholder engine_type strings and a wrong cylinder count on rows this batch now owns
    "J35A3": {"engine_type": "3.5 V6 SOHC VTEC (MDX 2001-2002, 240hp)", "power_hp": 240,
              "data_confidence": "STEP35_VERIFIED"},
    "J35A5": {"engine_type": "3.5 V6 SOHC VTEC (MDX 2003-2006, 265hp)", "power_hp": 265,
              "data_confidence": "STEP35_VERIFIED"},
    "J37A2": {"engine_type": "3.7 V6 SOHC VTEC (RL 2009-2012, 300hp)", "cylinders": 6,
              "power_hp": 300, "data_confidence": "STEP35_VERIFIED"},
    "L15BE": {"engine_type": "1.5 I4 VTEC Turbo DI (ADX 2025 190hp / CR-V 1.5T)", "power_hp": 190,
              "cylinders": 4, "displacement_cc": 1498, "data_confidence": "STEP35_VERIFIED"},
    "D16Y8": {"engine_type": "1.6 I4 SOHC VTEC (Acura 1.6EL 1997-2000 / Civic EX, 127hp)"},
    "D17A2": {"engine_type": "1.7 I4 SOHC VTEC (Acura 1.7EL 2001-2005 / Civic EX, 125-127hp)"},
    "R20A5": {"engine_type": "2.0 I4 SOHC i-VTEC (ILX 2013-2015 150hp / Civic 155hp)"},
    "K23A1": {},  # created below; placeholder keeps the code visible in the audit trail
}
ROW_FIXES.pop("K23A1")

lib.run_batch(lib.Cfg(
    brand="Acura", step_tag="step35", csv_num=43,
    lemon_baseline=1548, engines_baseline=7148,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    extra_decide=extra,
    FUEL_FIX_BY_TARGET={"JNC1": "Hybrid", "J30Y1": "Hybrid",
                        "J35Y4 SH (Sport Hybrid)": "Hybrid", "LEA1": "Hybrid"},
    expect_mapped=180, expect_skipped=0,
))
