"""Step 34 (Step 5, batch 25): replace LEMON_VOLVO codes with real B-codes.
184 rows -> 184 mapped / 0 skips. All rows US-market petrol (diesels never crawled).
Engine decode via official Volvo VIN engine codes (pos 4-5):
- P3 2015-2017: 40/26/27 = B4204T11 T5 2.0 Drive-E 240hp (emissions variants); 49 = B4204T9
  T6 2.0 twincharged 302; 61 = B5254T12 T5 2.5 I5 250; 90 + bare 3000CC = B6304T4 T6 3.0 300;
  94/95 = 3.2 NA 240 (B6324S5).
- SPA 2017-2022: 10/98 = B4204T23 T5 250; 99/A2 = B4204T27 T6 316; BR/BC = B4204TSH T8 PHEV
  400; H6 = T8 Extended Range 455; BK = T8 Polestar Engineered 415.
- MHEV era: B5 247 (L1: S60/V60/XC60 '22-25, XC90 '23-24), B6 295 (06: S90/V90CC '22-26,
  XC60/XC90 '23+), XC40: T4 187 (2019-22) -> B4 194 (2023+).
- P2/P1: 2.4i B5244S 168 volume; 2.5T B5254T2 208; T5 P1 218/227 (B5254T3/T7); 2.9 T6 272
  (B6294T); 4.4 V8 311 (B8444S); 3.2 235 (B6324S); S80 T6 3.0 281 (new B6304T2).
"""
import step5_lemon_lib as lib

CIT = {
    "WIKIVIN": "https://en.wikibooks.org/wiki/Vehicle_Identification_Numbers_(VIN_codes)/Volvo/VIN_Codes (pos 4-5 engine codes 2010+: 40=B4204T11 T5 Drive-E, 49=B4204T9 T6 Drive-E 302, 61/90/94/95, 98=B4204T23 '18 S90 T5, 99=B4204T27 '18 S90 T6, 10=B4204T23 T5 '16-'22 XC90/'17-'19 S90/'18-'21 V90+XC60/'19-'21 S60+V60, A2=B4204T27 T6 '17-'21 S90/'18-'21 XC60/'19-'21 S60+V60, H6=B4204T57/TSH T8 ER '22-, BK=T8 Polestar, L1=B5 MHEV '22-'25 S60/'22-24 XC60/'23-'26 V60CC/'23- XC40+XC90, 06=B4204TE B6 '22-'25 S90/'22-'26 V90CC/'22-'23 XC60/'23- XC90, M1=B5 '25-)",
    "VOVIN19": "https://vpic.nhtsa.dot.gov/mid/home/displayfile/c428dbd5-42ec-49c1-a3e9-2849b9b2afd9 (Volvo MY2019 VIN decoder: 10=B4204T MP 250 T5, 16=248 XC40 T5, A2=B4204TS 316 T6, AC=187 XC40 T4, BR=B4204TSH T8 313+87=400)",
    "VOVIN22": "https://cdn.volvotechinfo.com/vin/Volvo%20MY%202022%20VIN%20Decoder.pdf (06=B4204TE B6 295, BK=T8 PE 328+87=415, L1=B5 247)",
    "WIKIVEA": "https://en.wikipedia.org/wiki/Volvo_Engine_Architecture (B4204T11 = 2015-2018 S60/V60 T5; B4204T9 = T6 twincharged)",
    "IPD": "https://www.ipdusa.com/Articles/1084/Which-T5-or-T6-engine-does-my-P3-Volvo-have (P3 2014-2018 2.0 T5/T6 overlap: B4204T9/T10/T11/T12/T43; 2.5 B5254T; 3.0 B6304T)",
    "XC40_23": "https://www.caranddriver.com/reviews/a42152512/2023-volvo-xc40-b5-ultimate-by-the-numbers/ + motortrend.com/cars/volvo/xc40/2023 + kbb.com (2023 XC40: B4 194 FWD base / B5 247 AWD; T4 187/T5 248 2019-22)",
    "VOLVOHIST": "US Volvo lineup history: S40/V50 2.4i 168 volume (T5 opt); C30/C70 T5 227 (218 06-07); P2 S60 2.5T 208 volume (T5 257/R 300 opt); P2 V70 2.4i 168 volume; P2 XC70 2.5T 208 sole; P3 V70/XC70 3.2 235 sole 08-09; S80 2.5T/2.9T6 272 (05-06); S80 3.2 235/4.4 V8 311/T6 3.0 281 (07-09); XC90 2.5T/2.9T6/V8/3.2; S80 15-16 T6 3.0 300; XC90 2016 T6 316 volume (T5 late-16), 2017-22 T5 250 volume, 2023-25 B5 247 volume (B6 295 opt); S60 2016-18 T5 2.0 240 volume; V90 22-25 rows = V90CC B6 (regular V90 US ended MY2021)",
    "DBVOCAB": "DB Volvo B-code vocab: B5244S 168, B5254T2 209, B5254T3 220, B5254T7 227, B5254T12 254, B6294T 272, B8444S 307, B6324S 230, B6324S5 243, B6304T4 305, B4204T11 245, B4204T9 306, B4204T27 321",
}

NE = {
    "B4204T23 (T5 2.0 SPA)": ("2.0 I4 Turbo VEP4 (SPA/P3-late T5, 250hp US 2016-2022)", "Petrol", 1969, 250, 4),
    "B6304T2 (3.0 T6 I6)": ("3.0 I6 Turbo (P3 T6, 281hp US 2008-2010: S80 T6)", "Petrol", 2953, 281, 6),
    "B4204T (XC40 T4)": ("2.0 I4 Turbo VEP4 (XC40 T4, 187hp US 2019-2022)", "Petrol", 1969, 187, 4),
    "B4204T MHEV (B4 XC40)": ("2.0 I4 Turbo MHEV 48V (XC40 B4, 194hp US 2023+)", "Petrol", 1969, 194, 4),
    "B4204T MHEV (B5)": ("2.0 I4 Turbo MHEV 48V (B5, 247hp US: S60/V60 2022+, XC60 2022-24, XC90 2023-24)", "Petrol", 1969, 247, 4),
    "B4204TE MHEV (B6)": ("2.0 I4 Twincharged MHEV 48V (B6, 295hp US: S90 2022+, V90 CC 2022+, XC60/XC90 2023+)", "Petrol", 1969, 295, 4),
    "B4204TSH (T8 PHEV)": ("2.0 I4 Twincharged PHEV (T8: 400hp Recharge / 415hp Polestar Engineered / 455hp Extended Range)", "Hybrid", 1969, 400, 4),
}

R = [
    # P1
    ("C30", 2008, 2009, None, None, "B5254T7", "C30 T5 2.5 227hp sole US [VOLVOHIST][DBVOCAB]", 227),
    ("C70", 2006, 2007, None, None, "B5254T3", "C70 T5 2.5 218hp (2006-07) [VOLVOHIST][DBVOCAB]", 218),
    ("C70", 2008, 2009, None, None, "B5254T7", "C70 T5 2.5 227hp (2008+) [VOLVOHIST][DBVOCAB]", 227),
    ("S40", 2005, 2009, None, None, "B5244S", "S40 2.4i 168hp volume-default (T5 optional) [VOLVOHIST][DBVOCAB]", 168),
    ("V50", 2005, 2009, None, None, "B5244S", "V50 2.4i 168hp volume-default [VOLVOHIST][DBVOCAB]", 168),
    # P2
    ("S60", 2005, 2009, None, None, "B5254T2", "P2 S60 2.5T 208hp volume-default (T5 257/R 300 optional) [VOLVOHIST][DBVOCAB]", 208),
    ("V70", 2005, 2007, None, None, "B5244S", "P2 V70 2.4i 168hp volume-default (2.5T opt) [VOLVOHIST]", 168),
    ("V70", 2008, 2009, None, None, "B6324S", "P3 V70 3.2 235hp volume-default [VOLVOHIST][DBVOCAB]", 235),
    ("XC70", 2005, 2007, None, None, "B5254T2", "P2 XC70 2.5T 208hp sole [VOLVOHIST][DBVOCAB]", 208),
    ("XC70", 2008, 2009, None, None, "B6324S", "P3 XC70 3.2 235hp sole [VOLVOHIST][DBVOCAB]", 235),
    ("S80", 2005, 2005, 2500, None, "B5254T2", "P2 S80 2.5T 208hp [VOLVOHIST][DBVOCAB]", 208),
    ("S80", 2005, 2005, 2900, None, "B6294T", "P2 S80 T6 2.9 272hp [VOLVOHIST][DBVOCAB]", 272),
    ("S80", 2006, 2006, None, None, "B5254T2", "2006 S80 2.5T 208hp sole [VOLVOHIST]", 208),
    ("S80", 2007, 2009, 3200, None, "B6324S", "P3 S80 3.2 235hp [VOLVOHIST][DBVOCAB]", 235),
    ("S80", 2007, 2009, 4400, None, "B8444S", "S80 4.4 V8 Yamaha 311hp [VOLVOHIST][DBVOCAB]", 311),
    ("S80", 2008, 2009, 3000, None, "B6304T2 (3.0 T6 I6)", "S80 T6 3.0 281hp [VOLVOHIST][NEW]", 281),
    ("XC90", 2005, 2006, 2500, None, "B5254T2", "XC90 2.5T 208hp [VOLVOHIST][DBVOCAB]", 208),
    ("XC90", 2005, 2005, 2900, None, "B6294T", "XC90 T6 2.9 272hp (last year) [VOLVOHIST][DBVOCAB]", 272),
    ("XC90", 2005, 2009, 4400, None, "B8444S", "XC90 4.4 V8 311hp [VOLVOHIST][DBVOCAB]", 311),
    ("XC90", 2007, 2009, 3200, None, "B6324S", "XC90 3.2 235hp [VOLVOHIST][DBVOCAB]", 235),
    # P3 2015-2016 (VIN codes)
    ("S60", 2015, 2017, 2000, "49", "B4204T9", "VIN 49 = B4204T9 T6 2.0 twincharged Drive-E 302hp [WIKIVIN][IPD][DBVOCAB]", 302),
    ("S60", 2015, 2017, 2000, None, "B4204T11", "VIN 26/27/40 + bare 2000CC = B4204T11 T5 2.0 Drive-E 240hp (emissions variants) [WIKIVIN][IPD][DBVOCAB]", 240),
    ("S60", 2015, 2016, 2500, "61", "B5254T12", "VIN 61 = T5 2.5 I5 250hp [WIKIVIN][DBVOCAB]", 250),
    ("S60", 2015, 2016, 3000, None, "B6304T4", "VIN 90 + bare 3000CC = T6 3.0 I6 300hp [WIKIVIN][DBVOCAB]", 300),
    ("S60", 2016, 2018, None, None, "B4204T11", "P3 S60 bare 2016-18 = T5 2.0 240hp volume-default [VOLVOHIST][IPD]", 240),
    ("S60", 2019, 2021, None, None, "B4204T23 (T5 2.0 SPA)", "SPA S60 bare = T5 2.0 250hp volume-default [WIKIVIN(10)]['19-'21 S60 T5][VOVIN19]", 250),
    ("S60", 2022, 2025, None, None, "B4204T MHEV (B5)", "2022+ S60 bare = B5 MHEV 247hp (sole non-T8 petrol) [WIKIVIN(L1)][VOVIN22]", 247),
    ("S60", 2022, 2022, 2000, "BR", "B4204TSH (T8 PHEV)", "VIN BR = T8 Recharge PHEV 400hp combined (fuel col -> Hybrid) [VOVIN19][VOVIN22]", 400),
    ("S60", 2022, 2022, 2000, "H6", "B4204TSH (T8 PHEV)", "VIN H6 = T8 Extended Range PHEV 455hp combined [WIKIVIN][VOVIN22]", 455),
    ("S60", 2022, 2022, 2000, "BK", "B4204TSH (T8 PHEV)", "VIN BK = T8 Polestar Engineered 415hp combined [VOVIN22]", 415),
    ("V60", 2015, 2016, 2000, "49", "B4204T9", "VIN 49 = T6 2.0 Drive-E 302hp [WIKIVIN][IPD]", 302),
    ("V60", 2015, 2016, 2000, None, "B4204T11", "VIN 26/40 + bare = T5 2.0 240hp [WIKIVIN][IPD]", 240),
    ("V60", 2015, 2016, 2500, "61", "B5254T12", "VIN 61 = T5 2.5 250hp [WIKIVIN]", 250),
    ("V60", 2015, 2016, 3000, None, "B6304T4", "VIN 90 + bare 3000CC = T6 3.0 300hp [WIKIVIN]", 300),
    ("V60", 2016, 2018, None, None, "B4204T11", "P3 V60 bare 2016-18 = T5 2.0 240hp volume-default [VOLVOHIST][IPD]", 240),
    ("V60", 2019, 2021, None, None, "B4204T23 (T5 2.0 SPA)", "SPA V60 bare = T5 250hp volume-default [WIKIVIN(10)]", 250),
    ("V60", 2022, 2025, None, None, "B4204T MHEV (B5)", "2022+ V60 bare = B5 247hp [WIKIVIN(L1)]", 247),
    ("V60", 2022, 2022, 2000, "BK", "B4204TSH (T8 PHEV)", "VIN BK = T8 Polestar Engineered 415hp [WIKIVIN][VOVIN22]", 415),
    ("V60", 2022, 2022, 2000, "H6", "B4204TSH (T8 PHEV)", "VIN H6 = T8 Extended Range 455hp [WIKIVIN]", 455),
    ("XC60", 2015, 2016, 2000, "49", "B4204T9", "VIN 49 = T6 2.0 Drive-E 302hp [WIKIVIN][IPD]", 302),
    ("XC60", 2015, 2017, 2000, None, "B4204T11", "VIN 26/27/40 + bare 2000CC = T5 2.0 240hp [WIKIVIN][IPD]", 240),
    ("XC60", 2015, 2016, 2500, "61", "B5254T12", "VIN 61 = T5 2.5 250hp [WIKIVIN]", 250),
    ("XC60", 2015, 2016, 3000, None, "B6304T4", "VIN 90 + bare 3000CC = T6 3.0 300hp [WIKIVIN]", 300),
    ("XC60", 2015, 2015, 3200, None, "B6324S5", "VIN 94/95 = 3.2 NA 240hp [WIKIVIN][DBVOCAB]", 240),
    ("XC60", 2016, 2017, None, None, "B4204T11", "P3 XC60 bare 2016-17 = T5 2.0 240hp volume-default (3.2 dropped 2016) [VOLVOHIST][IPD]", 240),
    ("XC60", 2018, 2021, None, None, "B4204T23 (T5 2.0 SPA)", "SPA XC60 bare = T5 250hp volume-default [WIKIVIN(10)]", 250),
    ("XC60", 2022, 2025, None, None, "B4204T MHEV (B5)", "2022+ XC60 bare = B5 247hp [WIKIVIN(L1)]", 247),
    ("XC60", 2022, 2022, 2000, "BR", "B4204TSH (T8 PHEV)", "VIN BR = T8 Recharge 400hp [VOVIN19][VOVIN22]", 400),
    ("XC60", 2022, 2022, 2000, "H6", "B4204TSH (T8 PHEV)", "VIN H6 = T8 Extended Range 455hp [WIKIVIN]", 455),
    ("XC60", 2022, 2022, 2000, "BK", "B4204TSH (T8 PHEV)", "VIN BK = T8 Polestar Engineered 415hp [VOVIN22]", 415),
    ("XC70", 2015, 2016, 2000, None, "B4204T11", "VIN 40 + bare 2000CC = T5 2.0 Drive-E 240hp [WIKIVIN][IPD]", 240),
    ("XC70", 2015, 2015, 3200, None, "B6324S5", "VIN 94/95 = 3.2 NA 240hp [WIKIVIN][DBVOCAB]", 240),
    ("XC70", 2015, 2015, 3000, None, "B6304T4", "XC70 T6 3.0 300hp [VOLVOHIST][DBVOCAB]", 300),
    ("XC70", 2016, 2016, 2500, "61", "B5254T12", "VIN 61 = T5 2.5 250hp AWD [WIKIVIN]", 250),
    ("S80", 2015, 2016, 2000, None, "B4204T11", "VIN 26/40 + bare 2000CC = T5 2.0 Drive-E 240hp [WIKIVIN][IPD]", 240),
    ("S80", 2015, 2015, 3000, None, "B6304T4", "S80 T6 3.0 300hp [VOLVOHIST][DBVOCAB]", 300),
    # SPA
    ("S90", 2017, 2017, None, None, "B4204T23 (T5 2.0 SPA)", "2017 S90 bare = T5 250hp volume-default [WIKIVIN(10)]", 250),
    ("S90", 2019, 2021, None, None, "B4204T23 (T5 2.0 SPA)", "S90 bare = T5 250hp volume-default [WIKIVIN(10)]", 250),
    ("S90", 2022, 2025, None, None, "B4204TE MHEV (B6)", "2022+ S90 bare = B6 295hp sole non-T8 petrol [WIKIVIN(06)]", 295),
    ("S90", 2018, 2018, 2000, "98", "B4204T23 (T5 2.0 SPA)", "VIN 98 = B4204T23 T5 250hp [WIKIVIN]", 250),
    ("S90", 2018, 2018, 2000, "10", "B4204T23 (T5 2.0 SPA)", "VIN 10 = B4204T23 T5 250hp [WIKIVIN][VOVIN19]", 250),
    ("S90", 2018, 2018, 2000, "99", "B4204T27", "VIN 99 = B4204T27 T6 316hp [WIKIVIN]", 316),
    ("S90", 2018, 2018, 2000, "A2", "B4204T27", "VIN A2 = B4204T27 T6 316hp [WIKIVIN][VOVIN19]", 316),
    ("S90", 2018, 2018, 2000, "BC", "B4204TSH (T8 PHEV)", "VIN BC = 2018 T8 PHEV 400hp combined (fuel col -> Hybrid) [WIKIVIN pattern 98/99/BC=T5/T6/T8]", 400),
    ("S90", 2018, 2022, 2000, "BR", "B4204TSH (T8 PHEV)", "VIN BR = T8 Recharge PHEV 400hp combined [VOVIN19][VOVIN22]", 400),
    ("S90", 2022, 2022, 2000, "H6", "B4204TSH (T8 PHEV)", "VIN H6 = T8 Extended Range 455hp [WIKIVIN]", 455),
    ("V90", 2017, 2021, None, None, "B4204T23 (T5 2.0 SPA)", "V90 bare = T5 250hp volume-default [WIKIVIN(10) '18-'21 V90 T5]", 250),
    ("V90", 2022, 2025, None, None, "B4204TE MHEV (B6)", "2022+ V90 rows = V90 CC B6 295hp (regular V90 US ended MY2021) [WIKIVIN(06)]", 295),
    ("XC40", 2019, 2022, None, None, "B4204T (XC40 T4)", "XC40 bare = T4 187hp FWD volume-default (T5 248 opt) [VOVIN19(AC)][VOLVOHIST]", 187),
    ("XC40", 2023, 2025, None, None, "B4204T MHEV (B4 XC40)", "XC40 bare = B4 MHEV 194hp FWD volume-default (B5 247 opt) [XC40_23]", 194),
    ("XC90", 2016, 2016, None, None, "B4204T27", "2016 XC90 bare = T6 316hp volume-default (T5 FWD late-2016 addition) [WIKIVIN(A2-era)][VOLVOHIST]", 316),
    ("XC90", 2017, 2022, None, None, "B4204T23 (T5 2.0 SPA)", "XC90 bare = T5 250hp volume-default [WIKIVIN(10) '16-'22 XC90 T5]", 250),
    ("XC90", 2023, 2025, None, None, "B4204T MHEV (B5)", "2023+ XC90 bare = B5 247hp volume-default (B6 295 opt) [WIKIVIN(L1/M1)]", 247),
    ("XC90", 2022, 2022, 2000, "BR", "B4204TSH (T8 PHEV)", "VIN BR = T8 Recharge 400hp [VOVIN22]", 400),
    ("XC90", 2022, 2022, 2000, "H6", "B4204TSH (T8 PHEV)", "VIN H6 = T8 Extended Range 455hp [WIKIVIN]", 455),
]

TRIM = {
    ("V60", 2015, "V60CROSSCOUN"): ("B5254T12", "V60 Cross Country 2015 = T5 2.5 I5 AWD 250hp [VOLVOHIST]", 250, None),
}

IDENTITY = {
    "B5244S": ("Petrol", 2400), "B5254T2": ("Petrol", 2500), "B5254T3": ("Petrol", 2500),
    "B5254T7": ("Petrol", 2500), "B5254T12": ("Petrol", 2500), "B6294T": ("Petrol", 2900),
    "B8444S": ("Petrol", 4400), "B6324S": ("Petrol", 3200), "B6324S5": ("Petrol", 3200),
    "B6304T4": ("Petrol", 2953), "B4204T11": ("Petrol", 1969), "B4204T9": ("Petrol", 1969),
    "B4204T27": ("Petrol", 1969),
}

lib.run_batch(lib.Cfg(
    brand="Volvo", step_tag="step34", csv_num=42,
    lemon_baseline=1732, engines_baseline=7325,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY,
    ROW_FIXES={"B4204T27": {"engine_type": "2.0 I4 Twincharged (T6 316hp US: XC90 2016 / S90-XC60-S60-V60 2017-21)", "power_hp": 316}},
    FUEL_FIX_BY_TARGET={"B4204TSH (T8 PHEV)": "Hybrid"},
    expect_mapped=184, expect_skipped=0,
))
