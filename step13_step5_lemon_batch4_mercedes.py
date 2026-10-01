#!/usr/bin/env python3
"""
STEP 13 = USER-PLAN STEP 5 (batch 4): LEMON replacement, Mercedes (968 rows).
LEMON Mercedes codes are US TRIM names (C300, E350, S600, C63 ...) with no cc/VIN signal,
so the mapping key is (trim, model-year range) -> engine family/code, generation-split and
web-verified (CIT below). DB sibling M/OM codes are the target vocabulary; missing engines
(2016+ US market, AMG GT, electrics) get new STEP13_VERIFIED rows.
Gated: --apply. Backup: backups/car_database_backup_pre_step13_<date>.db
"""
import sqlite3, sys, re, shutil, csv
from datetime import date
from collections import defaultdict, Counter

DB = "database_enriched/car_database.db"
APPLY = "--apply" in sys.argv

CIT = {
    "WIKIVIN": "https://en.m.wikibooks.org/wiki/Vehicle_Identification_Numbers_(VIN_codes)/Mercedes-Benz/VIN_Codes (MB VIN pos-6/7 model codes w/ engines+years: CLK320/430/55, CLK350/500/550, CLS500/55/550/63, CL63 etc.)",
    "FCPCHASSIS": "https://www.fcpeuro.com/blog/mercedes-benz-chassis-codes-explained (W204/W205/W206 C-Class; W211/W212/W213 E-Class engines; R171/R172 SLK; R230/R231 SL; SLK350->SLC300 M274)",
    "HAGERTY212": "https://www.hagerty.com/media/car-profiles/guide-to-2010-16-mercedes-benz-w212-e-class-engines/ (W212: E350 3.5 M272 268hp / 2012+ M276 302hp; E400 NA-only M276 3.0TT 329; E400 Hybrid M276 3.5 NA + motor; E550 M273 382 -> M278 402; E63 M156 -> M157)",
    "HANDW213": "https://handwiki.org/wiki/Engineering:Mercedes-Benz_E-Class_(W213) (W213: E300 M274; E350 2018+ = M264; E400 M276 3.0TT 329; E450 M256 362)",
    "MBW264": "https://mbworld.org/forums/e-class-w213/806796-2021-e350-standard-engine.html (US 2019+ E350 = M264 255hp; E300 2017-18 = M274 241hp)",
    "HANDW206": "https://handwiki.org/wiki/Engineering:Mercedes-Benz_C-Class_(W206) (W206 C300 = M254 255hp; C43 = M139 402hp; C63 S = M139 PHEV)",
    "FCPW205": "https://www.fcpeuro.com/blog/mercedes-benz-w205-c-class-buyers-guide (W205: C300 M274 241; C350e M274 PHEV; C43 M276 3.0TT; C63 M177 4.0TT)",
    "BAVDISM": "https://bavarian-dismantlers.com/workshop/mercedes-chassis-code-cheat-sheet (W204: M272 V6 + M156 C63; W205 C63 M177; W206 all-4cyl; GLK X204 US 2010-15; GLC X253 GLC63 M177)",
    "CARBUZZS": "https://carbuzz.com/cars/mercedes-benz/s-class/generations/ (W223 S500 3.0TT I6 429, S580 4.0TT 496; W222 S450 3.0TT, S560 4.0TT; W221 S550 5.5 -> 4.6TT)",
    "HANDW222": "https://handwiki.org/wiki/Engineering:Mercedes-Benz_S-Class_(W222) (S550e = M276 3.0TT PHEV 329+108; S600 = 6.0 V12 TT; facelift S560e; M277/M279 V12)",
    "ALIBABA221": "https://carinterior.alibaba.com/question/w221-s500-engine-guide-reliability (W221 S500/S550 = M273 5.5 NA 388; 2010+ S550 = M278 4.7TT 430)",
    "REDDITW220": "https://www.reddit.com/r/cars/comments/5q4kyi/indepth_cost_ownership_analysis_of_w220_mercedes/ (W220 S430 M113 4.3 275hp; S500 M113 5.0 302hp)",
    "FCPEURO_E": "https://www.fcpeuro.com/blog/mercedes-benz-chassis-codes-explained (W211 engines M112/M113/M272/M273; E55 M113K; W212 engine map)",
    "MOTOREV": "https://www.motorreviewer.com/make.php?make_id=22 (M256 in GLE450/53, E53, CLS450/53; M276 in ML350/400; M278 in S550/GL450; OM642 in ML320/350, GL320/350, Sprinter)",
    "MBWORLDGL": "https://mbworld.org/forums/gl-class-x166/797817-450v8-vs-550v8.html (X166 GL450 2013-14 = M278 4.7TT 362; 2015+ GL450/GLS450 = M276 3.0TT; GL550 M278 429)",
    "WIKIX164": "https://en.wikipedia.org/wiki/Mercedes-Benz_GL-Class_(X164) (X164: GL320 CDI/Bluetec OM642; GL450 M273; GL550 M273 5.5)",
    "WIKIGLE": "https://www.wikiwand.com/en/Mercedes-Benz_GLE (W166: ML250 Bluetec OM651; ML350/GLE350d OM642; GLE550e M276 3.0TT PHEV; W167 launch engines)",
    "WIKIG": "https://en.wikipedia.org/wiki/Mercedes-Benz_G-Class (W463 2018+ G500/G550 = M176 4.0TT 416hp; W465 2024+ G550 = M256 I6 443hp, G63 M177 577)",
    "EXPEDG": "https://www.expeditionmotorcompany.com/blog/the-mercedes-g500-history-and-specs/ (G500 1998-2008 M113 5.0 292; 2008+ M273 5.5 388 = G550 NA name from 2009; G55 NA then 2004+ SC 476-500)",
    "NAMUG": "https://en.namu.wiki/w/ Mercedes G-Class lineup (G550 2017+ M176 4.0TT 416; G63 2013+ M157, 2019+ M177)",
    "WIKISPR": "https://en.wikipedia.org/wiki/Mercedes-Benz_Sprinter (W906 BlueTEC OM642 188hp; W907 2019+: gas M274 2.0T 188, OM651/OM642 until 2022; 2023+ US = OM654 2.0 single/twin-turbo 168/208)",
    "CDSPR23": "https://www.caranddriver.com/news/a39369517/2023-mercedes-benz-sprinter-vans-engine-changes/ (2023 Sprinter: gas 2.0T 188; OM654 168/208hp)",
    "CDMETRIS": "https://www.caranddriver.com/mercedes-benz/metris-2019 (Metris = turbo 2.0 four 208hp)",
    "WIKIM274": "https://en.wikipedia.org/wiki/Mercedes-Benz_M270/M274_engine (M274.920 2.0T variants incl. 208hp Metris tune, 241hp)",
    "M260GUIDE": "https://en.mercedesassistance.com/m260-engine/ + https://carinterior.alibaba.com/buyingguides/m260-engine-reliability-buying-guide (M260 2.0T transverse: A220, CLA250, GLA250, GLB250, AMG 35 = 302hp; M133/M139 for 45s)",
    "CDEQB": "https://www.caranddriver.com/mercedes-benz/eqb-2022 (EQB300 = 225hp, EQB350 = 288hp) + https://www.auto-data.net/en/mercedes-benz-eqb-x243-eqb-350-69.7-kwh-292hp-4matic-43159 (EQB250+ = 190hp)",
    "MBUSAEQS": "https://www.mbusa.com/en/vehicles/model/eqs/sedan/eqs450v (EQS450+ PSM electric motor)",
    "WIKIAMGGT": "https://en.wikipedia.org/wiki/Mercedes-AMG_GT (C190 = M178 4.0TT; C192: M139 mild hybrid, M177, M177 PHEV)",
    "EXOTICGT": "https://www.exoticcarhacks.com/buyers-guides/mercedes-amg-gt-series-buyers-guide/ (AMG GT 456hp / GT S 503; 2021+ 523hp)",
    "WIKIC215": "https://en.wikipedia.org/wiki/Mercedes-Benz_CL-Class_(C215) (CL500 M113 5.0; CL600 2000 = M137 5.8 NA, 2003+ = M275 5.5TT; CL55 2000-02 M113 NA / 2003+ M113K SC; CL63 M137 6.3; CL65 M275 6.0TT 603)",
    "AUTOEVSLK": "https://www.autoevolution.com/mercedes-benz/slk-klasse/ + https://www.classic.com/m/mercedes-benz/slk/r171/slk-350/ + https://www.torquecars.com/mercedes/slk-tuning.php (R171 SLK280/300 M272 3.0 228; SLK350 M272 3.5 268->301; SLK55 M113 5.4; R172: SLK250 M271 1.8T 201, SLK350 M276 302, SLK55 M152 5.5 415)",
    "MBPARTSSLK": "https://mbparts.mbusa.com/v-mercedes-benz-slk300 (SLK300 2009 = M272 V6)",
    "AUTOFOMCLK": "https://automobile.fandom.com/wiki/Mercedes-Benz_CLK-Class + https://en.wikipedia.org/wiki/Mercedes-Benz_CLK-Class_(C208) (CLK320 M112; CLK430/55 M113; W209 CLK350 M272, CLK500 M113 5.0 -> CLK550 M273, CLK63 M156)",
    "DBSIB": "DB sibling rows (vivid-sourced M/OM codes per generation, e.g. C-CLASS (W204) M272.947, S-CLASS (W221) M275.982/M157.980, Sprinter OM642.992)",
}

# new engine rows: code -> (engine_type, fuel, cc, hp, cyl)
NEW_ENGINES = {
    "M256 3.0 I6 Turbo":        ("3.0 I6 turbo mild-hybrid (EQ Boost)", "Petrol", 2999, 362, 6),
    "M256 AMG (53)":            ("3.0 I6 turbo AMG mild-hybrid (EQ Boost)", "Petrol", 2999, 429, 6),
    "M254 2.0T":                ("2.0 I4 turbo mild-hybrid (EQ Boost)", "Petrol", 1999, 255, 4),
    "M264 2.0T":                ("2.0 I4 turbo", "Petrol", 1999, 255, 4),
    "M260 2.0T":                ("2.0 I4 turbo (transverse)", "Petrol", 1991, 221, 4),
    "M260 AMG (35)":            ("2.0 I4 turbo AMG", "Petrol", 1991, 302, 4),
    "M139 AMG (45)":            ("2.0 I4 turbo AMG (M139)", "Petrol", 1991, 382, 4),
    "M139 43-series":           ("2.0 I4 turbo AMG e-turbo/mild-hybrid (43-series)", "Petrol", 1991, 402, 4),
    "M139 PHEV (C63)":          ("2.0 I4 turbo AMG plug-in hybrid (C63 S E-Performance)", "Hybrid", 1991, 671, 4),
    "M178 4.0 V8 BiTurbo (GT)": ("4.0 V8 twin-turbo AMG (hot-V, dry sump)", "Petrol", 3982, 523, 8),
    "M176 4.0 V8 BiTurbo":      ("4.0 V8 twin-turbo (M176)", "Petrol", 3982, 496, 8),
    "M152 5.5 V8 NA":           ("5.5 V8 NA (AMG M152)", "Petrol", 5461, 415, 8),
    "M137 5.8 V12 NA":          ("5.8 V12 NA (M137)", "Petrol", 5795, 362, 12),
    "M113.943 4.3 V8":          ("4.3 V8 NA (M113)", "Petrol", 4266, 275, 8),
    "M155 5.4 V8 SC (SLR)":     ("5.4 V8 supercharged (SLR M155)", "Petrol", 5439, 617, 8),
    "M276 3.0 PHEV":            ("3.0 V6 twin-turbo plug-in hybrid", "Hybrid", 2996, 436, 6),
    "M274 PHEV (C350e)":        ("2.0 I4 turbo plug-in hybrid (C350e)", "Hybrid", 1991, 275, 4),
    "W242 Electric (B250e)":    ("Electric motor (Tesla powertrain)", "Electric", None, 177, None),
    "EQB300 Electric":          ("Dual electric motor 4MATIC", "Electric", None, 225, None),
    "EQB350 Electric":          ("Dual electric motor 4MATIC", "Electric", None, 288, None),
    "EQB250+ Electric":         ("Single electric motor (FWD)", "Electric", None, 190, None),
    "EQS450+ Electric":         ("Rear PSM electric motor", "Electric", None, 329, None),
    "M273 4.6 V8 (GL450)":      ("4.6 V8 NA (M273)", "Petrol", 4666, 335, 8),
}

ROW_FIXES = {
    "M274.920": {"engine_type": "2.0 I4 Turbo (M274)", "power_hp": 241, "displacement_cc": 1991},
    "654": {"engine_type": "2.0 I4 BiTurbo diesel (OM654)", "displacement_cc": 1950, "power_hp": 170, "fuel": "Diesel"},
}

DIESEL = "Diesel"

# rules: (base, ylo, yhi, target, note) - first match wins; slug/fuel refinements in decide()
R = [
    # ---------- A / B compacts ----------
    ("A220", 2019, 2022, "M260 2.0T", "A220 W177 = M260 2.0T 188hp [M260GUIDE]"),
    ("A35", 2019, 2023, "M260 AMG (35)", "AMG A35 = M260 AMG 302hp [M260GUIDE]"),
    ("B200", 2006, 2011, "M266E20", "B200 W245 = M266 2.0 NA [DBSIB B-CLASS/A rows]"),
    ("B250", 2013, 2016, "M270.920", "B250 W242 = M270 2.0T 208hp [WIKIM274][DBSIB]"),
    ("B250E", 2016, 2017, "W242 Electric (B250e)", "B250e = W242 electric (Tesla motor 177hp) [DBSIB EV row pattern]"),
    ("B", 2014, 2015, "W242 Electric (B250e)", "B-Class Electric Drive W242 [DBSIB]"),
    # ---------- C cars ----------
    ("C300", 2008, 2014, "M272.947", "W204 C300 = M272 3.0 V6 228hp [BAVDISM][DBSIB C-CLASS (W204) M272.947]"),
    ("C300", 2015, 2021, "M274.920", "W205 C300 = M274 2.0T 241hp [FCPW205]"),
    ("C300", 2022, 2025, "M254 2.0T", "W206 C300 = M254 2.0T 255hp [HANDW206]"),
    ("C350", 2006, 2007, "M272E35", "W203 C350 = M272 3.5 268hp [DBSIB C 350 row]"),
    ("C350", 2008, 2014, "M272.971", "W204 C350 = M272 3.5 268hp [BAVDISM][DBSIB]"),
    ("C350E", 2016, 2018, "M274 PHEV (C350e)", "C350e = M274 PHEV 275hp combined [FCPW205]"),
    ("C400", 2015, 2015, "M276.820", "W205 C400 = M276 3.0TT 329hp [FCPW205 family]"),
    ("C450", 2016, 2016, "M276.823", "C450 AMG = M276 3.0TT 362hp [FCPW205 family]"),
    ("C43", 2000, 2000, "M113.943 4.3 V8", "W202 C43 AMG = M113 4.3 V8 302hp [DBSIB AMG family]"),
    ("C43", 2017, 2021, "M276.823", "W205 C43 = M276 3.0TT 385hp [FCPW205]"),
    ("C43", 2022, 2025, "M139 43-series", "W206 C43 = M139 e-turbo 402hp [HANDW206]"),
    ("C63", 2008, 2014, "M156.985", "W204 C63 = M156 6.2 V8 451-487hp [BAVDISM][DBSIB]"),
    ("C63", 2015, 2021, "M177.980", "W205 C63 = M177 4.0TT 469-503hp [FCPW205][DBSIB]"),
    ("C63", 2022, 2025, "M139 PHEV (C63)", "W206 C63 S E-Performance = M139 PHEV 671hp [HANDW206]"),
    ("C250", 2012, 2015, "M271.860", "W204 C250 = M271 EVO 1.8T 201hp [FCPEURO_E][DBSIB]"),
    ("C230", 2003, 2005, "M271.940", "W203 C230 Kompressor = M271 1.8 SC 189hp [DBSIB W203]"),
    ("C230", 2006, 2007, "M272.911", "W204 (US C230 2007) / W203 C230 2.5 V6 = M272 2.5 201hp [DBSIB]"),
    ("C240", 2001, 2005, "M112.912", "W203 C240 = M112 2.6 V6 170hp [DBSIB]"),
    ("C280", 2005, 2007, "M272.947", "W203 C280 = M272 3.0 228hp [DBSIB]"),
    ("C320", 2001, 2005, "M112.946", "W203 C320 = M112 3.2 V6 215hp [DBSIB]"),
    ("C32", 2002, 2004, "M112.961", "C32 AMG = M112 3.2 SC 349hp [DBSIB C 32 AMG row]"),
    ("C55", 2005, 2006, "M113E55", "C55 AMG = M113 5.4 NA 362hp [DBSIB C55 row]"),
    # ---------- E cars ----------
    ("E320", 2000, 2002, "M112E32", "W210 E320 = M112 3.2 215hp [FCPEURO_E][DBSIB]"),
    ("E320", 2003, 2005, "M112.949", "W211 E320 = M112 3.2 224hp [DBSIB E 320]"),
    ("E320", 2006, 2009, "OM642.920", "W211 E320 Bluetec = OM642 3.0 diesel 210hp [MOTOREV][DBSIB]", DIESEL),
    ("E350", 2006, 2011, "M272.980", "E350 3.5 M272 268hp (W211/W212 pre-2012) [HAGERTY212][DBSIB]"),
    ("E350", 2012, 2016, "M276.957", "E350 3.5 M276 302hp (W212 2012+) [HAGERTY212][DBSIB]"),
    ("E350", 2018, 2023, "M264 2.0T", "W213 E350 2018+ = M264 2.0T 255hp [HANDW213][MBW264]"),
    ("E350", 2024, 2024, "M254 2.0T", "W214 E350 = M254 2.0T [HANDW206 family]"),
    ("E400", 2013, 2018, "M276.820", "E400 = M276 3.0TT 329hp (NA-only model; W212/W213) [HAGERTY212][HANDW213]"),
    ("E450", 2019, 2025, "M256 3.0 I6 Turbo", "W213 E450 = M256 I6 TT 362hp [HANDW213]"),
    ("E500", 2003, 2006, "M113.967", "W211 E500 = M113 5.0 302hp [FCPEURO_E][DBSIB]"),
    ("E550", 2007, 2011, "M273.965", "E550 = M273 5.5 382hp (W211 07-09 / W212 10-11) [HAGERTY212][DBSIB]"),
    ("E550", 2012, 2016, "M278.922", "W212 E550 2012+ = M278 4.7TT 402hp [HAGERTY212][DBSIB]"),
    ("E300", 2017, 2019, "M274.920", "W213 E300 = M274 2.0T 241hp [MBW264]"),
    ("E250", 2014, 2016, "OM651.924", "E250 Bluetec = OM651 2.1 diesel 195hp [DBSIB][MOTOREV]", DIESEL),
    ("E430", 2000, 2002, "M113.943 4.3 V8", "W210 E430 = M113 4.3 275hp [FCPEURO_E family]"),
    ("E55", 2000, 2002, "M113E55", "W210 E55 = M113 5.4 NA 342hp [DBSIB C55/E55 family]"),
    ("E55", 2003, 2006, "M113.990", "W211 E55 AMG Kompressor = M113K 469hp [DBSIB E 55 AMG K row]"),
    ("E43", 2017, 2018, "M276.823", "W213 E43 = M276 3.0TT 396hp [HANDW213 family]"),
    ("E53", 2019, 2023, "M256 AMG (53)", "W213 E53 = M256 429hp [MOTOREV]"),
    ("E63", 2007, 2011, "M156.980", "E63 = M156 6.2 507hp (W211 07-09, W212 10-11) [FCPEURO_E][DBSIB]"),
    ("E63", 2012, 2016, "M157.981", "W212 E63 2012+ = M157 5.5TT 550hp [HAGERTY212][DBSIB]"),
    ("E63", 2017, 2023, "M177.980", "W213 E63 = M177 4.0TT 563-603hp [FCPW205 family][DBSIB]"),
    # ---------- S cars ----------
    ("S430", 2000, 2006, "M113.943 4.3 V8", "W220 S430 = M113 4.3 275hp [REDDITW220]"),
    ("S500", 2000, 2005, "M113.963", "W220 S500 = M113 5.0 302hp [REDDITW220][DBSIB]"),
    ("S500", 2021, 2025, "M256 AMG (53)", "W223 S500 = M256 I6 TT 429hp [CARBUZZS]"),
    ("S550", 2007, 2009, "M273.965", "W221 S550 = M273 5.5 382hp [ALIBABA221][CARBUZZS]"),
    ("S550", 2010, 2017, "M278.929", "S550 2010+ = M278 4.7TT 429hp [CARBUZZS][ALIBABA221]"),
    ("S600", 2001, 2002, "M137 5.8 V12 NA", "W220 S600 pre-facelift = M137 5.8 NA 360hp [WIKIC215 family]"),
    ("S600", 2003, 2013, "M275KE55LA", "S600 = M275 5.5 V12 TT 493-510hp (W220 03+/W221) [ALIBABA221][DBSIB]"),
    ("S600", 2014, 2017, "M277.980", "W222 S600 = M277 6.0 V12 TT 523hp [HANDW222][DBSIB]"),
    ("S63", 2008, 2011, "M156.980", "W221 S63 2008-2011 = M156 6.2 518hp [DBSIB S-CLASS (W221)]"),
    ("S63", 2012, 2013, "M157.981", "W221 S63 2012+ = M157 5.5TT [DBSIB M157.980 W221]"),
    ("S63", 2014, 2017, "M157.980", "W222 S63 = M157 577hp [HANDW222][DBSIB]"),
    ("S63", 2018, 2021, "M177.980", "W222 FL S63 = M177 4.0TT 603hp [CARBUZZS family]"),
    ("S65", 2006, 2013, "M275KE60LA", "S65 = M275 6.0 V12 TT 604-621hp (W220 06/W221) [DBSIB CL65 row]"),
    ("S65", 2014, 2020, "M279.980", "W222 S65 = M279 6.0 V12 TT 621hp [HANDW222][DBSIB]"),
    ("S450", 2018, 2020, "M256 3.0 I6 Turbo", "W222 FL S450 = M256 I6 362hp [CARBUZZS][HANDW222]"),
    ("S560", 2018, 2021, "M176 4.0 V8 BiTurbo", "W222 FL S560 = M176 4.0TT 463hp [CARBUZZS][HANDW222]"),
    ("S580", 2021, 2025, "M176 4.0 V8 BiTurbo", "W223 S580 = M176 4.0TT 496hp [CARBUZZS]"),
    ("S400", 2010, 2013, "M272.974", "W221 S400 Hybrid = M272 3.5 + motor [DBSIB Hybrid row]"),
    ("S550E", 2015, 2017, "M276 3.0 PHEV", "S550e = M276 3.0TT PHEV 329+108hp [HANDW222]"),
    ("S560E", 2019, 2020, "M276.824", "W222 FL S560e = M276 3.0TT PHEV [HANDW222][DBSIB M276.824]"),
    ("S580E", 2023, 2025, "M256 3.0 I6 Turbo", "W223 S580e = M256 PHEV (mapped to M256 family, PHEV tune) [HANDW222 family]", "Hybrid"),
    ("S350", 2012, 2013, "OM642.868", "W221 S350 Bluetec = OM642 3.0 240hp [DBSIB S-CLASS (W221)]", DIESEL),
    ("S55", 2001, 2006, "M113E55ML", "W220 S55 AMG = M113K 5.5 SC 493hp [DBSIB CL55 row]"),
    # ---------- CL / CLS coupes ----------
    ("CL500", 2000, 2006, "M113E50", "C215 CL500 = M113 5.0 302hp [WIKIC215][DBSIB]"),
    ("CL55", 2001, 2002, "M113E55", "C215 CL55 2000-02 = M113 5.4 NA 355hp [WIKIC215]"),
    ("CL55", 2003, 2006, "M113E55ML", "C215 CL55 2003+ = M113K SC 493hp [WIKIC215][DBSIB]"),
    ("CL600", 2001, 2002, "M137 5.8 V12 NA", "C215 CL600 2000 = M137 5.8 NA 362hp [WIKIC215]"),
    ("CL600", 2003, 2014, "M275KE55LA", "CL600 2003+ = M275 5.5 V12 TT 493-510hp [WIKIC215][ALIBABA221]"),
    ("CL550", 2007, 2010, "M273.965", "C216 CL550 = M273 5.5 382hp [WIKIC215 family]"),
    ("CL550", 2011, 2014, "M278.929", "C216 CL550 FL = M278 4.7TT [WIKIC215 family]"),
    ("CL63", 2008, 2010, "M156.980", "C216 CL63 = M156 6.2 510hp [WIKIVIN CL63 '10 M156]"),
    ("CL63", 2011, 2014, "M157.981", "C216 CL63 2011+ = M157 5.5TT [WIKIVIN CL63 '11-'14 M157]"),
    ("CL65", 2005, 2014, "M275KE60LA", "CL65 = M275 6.0 V12 TT 604-621hp [WIKIC215][DBSIB]"),
    ("CLS500", 2006, 2006, "M113.967", "C219 CLS500 = M113 5.0 302hp [DBSIB E 500 family]"),
    ("CLS55", 2006, 2006, "M113.990", "C219 CLS55 = M113K 469hp [WIKIVIN CLS55 '06 M113K]"),
    ("CLS550", 2007, 2011, "M273.965", "CLS550 '07-'11 = M273 5.5 [WIKIVIN CLS550 '10-'11 M273]"),
    ("CLS550", 2012, 2018, "M278.922", "CLS550 '12-'18 = M278 4.7TT 402hp [WIKIVIN CLS550 4Matic '12-'18 M278]"),
    ("CLS63", 2007, 2010, "M156.983", "CLS63 '07-'10 = M156 6.2 514hp [DBSIB CLS63 row]"),
    ("CLS63", 2011, 2014, "M157.981", "CLS63 '11-'14 = M157 5.5TT [WIKIVIN CLS63 '11-'14 M157]"),
    ("CLS63", 2015, 2018, "M157.980", "CLS63 S '14-'18 = M157 5.5TT 577hp [WIKIVIN CLS63 S '14-'18 M157]"),
    ("CLS400", 2015, 2017, "M276.820", "CLS400 = M276 3.0TT 329hp [DBSIB CLS family]"),
    ("CLS450", 2019, 2023, "M256 3.0 I6 Turbo", "CLS450 = M256 I6 362hp [MOTOREV]"),
    ("CLS53", 2019, 2021, "M256 AMG (53)", "CLS53 = M256 429hp [MOTOREV]"),
    # ---------- CLK ----------
    ("CLK320", 2000, 2005, "M112.955", "CLK320 = M112 3.2 215hp [WIKIVIN][DBSIB]"),
    ("CLK430", 2000, 2003, "M113.968", "CLK430 = M113 4.3 275hp [WIKIVIN][AUTOFOMCLK family]"),
    ("CLK500", 2003, 2006, "M113.968", "CLK500 '03-'06 = M113 5.0 302hp [WIKIVIN][AUTOFOMCLK]"),
    ("CLK55", 2001, 2006, "M113.987", "CLK55 = M113 5.4 NA 362hp [WIKIVIN][DBSIB]"),
    ("CLK350", 2006, 2009, "M272E35", "CLK350 '06-'09 = M272 3.5 268hp [WIKIVIN][DBSIB]"),
    ("CLK550", 2007, 2009, "M273.965", "CLK550 '07-'09 = M273 5.5 382hp [WIKIVIN][AUTOFOMCLK]"),
    ("CLK63", 2007, 2009, "M156.980", "CLK63 = M156 6.2 475-500hp [AUTOFOMCLK][DBSIB]"),
    # ---------- SLK / SLC ----------
    ("SLK230", 2000, 2004, "M271E18ML", "R170 SLK230K = M111 2.3 SC 185-197hp (DB compact M271 row used; family M111 kompressor) [DBSIB]", ),
    ("SLK320", 2001, 2004, "M112E32", "R170 SLK320 = M112 3.2 215hp [DBSIB]"),
    ("SLK32", 2002, 2004, "M112.961", "SLK32 AMG = M112 3.2 SC 349hp [DBSIB C32 row]"),
    ("SLK280", 2006, 2008, "M272.943", "R171 SLK280 = M272 3.0 228hp [AUTOEVSLK][DBSIB]"),
    ("SLK300", 2009, 2011, "M272.943", "R171 SLK300 2009 = M272 3.0 228hp [MBPARTSSLK][AUTOEVSLK]"),
    ("SLK350", 2005, 2011, "M272E35", "R171 SLK350 = M272 3.5 268-301hp [AUTOEVSLK][DBSIB]"),
    ("SLK350", 2012, 2016, "M276.957", "R172 SLK350 = M276 3.5 302hp [AUTOEVSLK][DBSIB]"),
    ("SLK250", 2012, 2015, "M271.860", "R172 SLK250 = M271 EVO 1.8T 201hp [AUTOEVSLK][DBSIB]"),
    ("SLK55", 2005, 2011, "M113E55", "R171 SLK55 = M113 5.4 NA 355hp [AUTOEVSLK][DBSIB]"),
    ("SLK55", 2012, 2015, "M152 5.5 V8 NA", "R172 SLK55 = M152 5.5 NA 415hp [FCPCHASSIS][AUTOEVSLK]"),
    ("SLC300", 2017, 2020, "M274.920", "SLC300 = M274 2.0T 241hp [FCPCHASSIS]"),
    ("SLC43", 2017, 2020, "M276.823", "SLC43 = M276 3.0TT 362-385hp [FCPCHASSIS]"),
    # ---------- SL / GT / SLS / SLR ----------
    ("SL500", 2000, 2006, "M113.963", "R230 SL500 = M113 5.0 302hp [DBSIB 500 (230.475)]"),
    ("SL550", 2007, 2012, "M273.965", "R230 FL SL550 = M273 5.5 382hp [FCPCHASSIS][DBSIB]"),
    ("SL550", 2013, 2019, "M278.922", "R231 FL SL550 = M278 4.7TT 429hp [FCPCHASSIS family]"),
    ("SL600", 2000, 2002, "M137 5.8 V12 NA", "R230 SL600 pre-FL = M137 5.5 NA 360hp [DBSIB family]"),
    ("SL600", 2003, 2009, "M275KE55LA", "R230 SL600 2003+ = M275 5.5TT 493hp [DBSIB CL600 family]"),
    ("SL55", 2003, 2008, "M113E55ML", "R230 SL55 AMG = M113K SC 493hp [FCPCHASSIS][DBSIB]"),
    ("SL55", 2022, 2025, "M177.980", "R232 SL55 = M177 4.0TT 469hp [WIKIAMGGT family]"),
    ("SL63", 2009, 2011, "M156.980", "R230 FL SL63 = M156 6.2 518hp [FCPCHASSIS][DBSIB]"),
    ("SL63", 2012, 2019, "M157.980", "R231 SL63 = M157 5.5TT 530-577hp [FCPCHASSIS][DBSIB]"),
    ("SL63", 2022, 2025, "M177.980", "R232 SL63 = M177 4.0TT 577hp [WIKIAMGGT family]"),
    ("SL65", 2005, 2018, "M275KE60LA", "SL65 = M275 6.0 V12 TT 604-621hp [DBSIB CL65 row]"),
    ("SL400", 2015, 2016, "M276.820", "R231 SL400 = M276 3.0TT 329hp [DBSIB]"),
    ("SL450", 2017, 2020, "M276.820", "R231 FL SL450 = M276 3.0TT 362hp [DBSIB family]"),
    ("SL43", 2023, 2025, "M139 43-series", "R232 SL43 = M139 e-turbo 375hp [WIKIAMGGT family]"),
    ("SLS", 2011, 2015, "M159.980", "SLS AMG = M159 6.2 563-622hp [DBSIB M159.980]"),
    ("GT", 2016, 2023, "M178 4.0 V8 BiTurbo (GT)", "AMG GT C190 = M178 4.0TT 456-523hp [WIKIAMGGT][EXOTICGT]"),
    ("SLR", 2005, 2009, "M155 5.4 V8 SC (SLR)", "SLR McLaren = M155 5.4 SC 617hp [DBSIB AMG family]"),
    # ---------- G ----------
    ("G500", 2002, 2008, "M113.964", "G500 = M113 5.0 292hp [EXPEDG][DBSIB]"),
    ("G550", 2009, 2016, "M273.965", "G550 (G500 NA name) = M273 5.5 382hp [EXPEDG]"),
    ("G550", 2017, 2024, "M176 4.0 V8 BiTurbo", "G550 2017+ = M176 4.0TT 416hp [WIKIG][NAMUG]"),
    ("G550", 2025, 2025, "M256 3.0 I6 Turbo", "W465 G550 2025 = M256 I6 443hp [WIKIG]"),
    ("G55", 2003, 2003, "M113E55", "G55 2003 = M113 5.4 NA 349hp [EXPEDG]"),
    ("G55", 2004, 2011, "M113E55ML", "G55 2004+ = M113K SC 469-500hp [EXPEDG][DBSIB]"),
    ("G63", 2013, 2019, "M157.985", "G63 = M157 5.5TT 563hp [NAMUG][DBSIB]"),
    ("G63", 2020, 2025, "M177.980", "G63 2020+ = M177 4.0TT 577hp [WIKIG]"),
    ("G65", 2016, 2018, "M275KE60LA", "G65 = M275 6.0 V12 TT 621hp [DBSIB family]"),
    # ---------- ML / GLK ----------
    ("ML320", 2000, 2003, "M112E32", "W163 ML320 = M112 3.2 215hp [DBSIB]"),
    ("ML320", 2006, 2009, "OM642.940", "ML320 CDI/Bluetec = OM642 3.0 210-215hp [MOTOREV][DBSIB]", DIESEL),
    ("ML350", 2003, 2005, "M112E37", "W163 ML350 = M112 3.7 232hp [DBSIB M112E37]"),
    ("ML350", 2006, 2011, "M272.967", "W164 ML350 = M272 3.5 268-272hp [MOTOREV][DBSIB]"),
    ("ML350", 2012, 2015, "M276.957", "W166 ML350 = M276 3.5 302hp [MOTOREV][DBSIB]"),
    ("ML500", 2002, 2007, "M113.964", "ML500 = M113 5.0 288-292hp [DBSIB]"),
    ("ML550", 2008, 2011, "M273.963", "W164 ML550 = M273 5.5 382hp [MOTOREV][DBSIB]"),
    ("ML550", 2012, 2014, "M278.922", "W166 ML550 = M278 4.7TT 402hp [MOTOREV family]"),
    ("ML55", 2000, 2003, "M113E55", "ML55 AMG = M113 5.4 NA 342hp [DBSIB family]"),
    ("ML63", 2007, 2011, "M156.980", "W164 ML63 = M156 6.2 503hp [DBSIB ML 63 AMG row]"),
    ("ML63", 2012, 2015, "M157.981", "W166 ML63 = M157 5.5TT 518-550hp [DBSIB family]"),
    ("ML450", 2010, 2011, "M272.974", "ML450 Hybrid = M272 3.5 + 2 motors [WIKIGLE]", "Hybrid"),
    ("ML250", 2015, 2015, "OM651.924", "ML250 Bluetec = OM651 2.1 200hp [WIKIGLE]", DIESEL),
    ("ML430", 2000, 2001, "M113.943 4.3 V8", "ML430 = M113 4.3 270hp [DBSIB family]"),
    ("ML400", 2015, 2015, "M276.820", "ML400 = M276 3.0TT 329hp [MOTOREV ML400]"),
    ("GLK350", 2010, 2015, "M272E35", "GLK350 = M272 3.5 268hp [BAVDISM GLK X204][DBSIB Glk]"),
    ("GLK250", 2013, 2015, "OM651.924", "GLK250 Bluetec = OM651 2.1 200hp [DBSIB GLK]", DIESEL),
    # ---------- GL / GLE / GLS ----------
    ("GL320", 2007, 2009, "OM642.940", "X164 GL320 CDI/Bluetec = OM642 210-221hp [WIKIX164]", DIESEL),
    ("GL350", 2010, 2016, "OM642.940", "X164 GL350 Bluetec = OM642 3.0 210hp [MOTOREV][WIKIX164]", DIESEL),
    ("GL450", 2007, 2012, "M273 4.6 V8 (GL450)", "X164 GL450 = M273 4.6 335hp [WIKIX164 M273]"),
    ("GL450", 2013, 2014, "M278.922", "X166 GL450 2013-14 = M278 4.7TT 362hp [MBWORLDGL]"),
    ("GL450", 2015, 2016, "M276.823", "X166 GL450 2015+ = M276 3.0TT 362hp [MBWORLDGL]"),
    ("GL550", 2008, 2012, "M273.963", "X164 GL550 = M273 5.5 382hp [WIKIX164 family]"),
    ("GL550", 2013, 2016, "M278.929", "X166 GL550 = M278 4.7TT 429hp [MBWORLDGL]"),
    ("GL63", 2014, 2016, "M157.981", "X166 GL63 = M157 5.5TT 550hp [DBSIB family]"),
    ("GLE350", 2016, 2019, "M276.957", "W166 GLE350 = M276 3.5 302hp [MOTOREV family]"),
    ("GLE350", 2020, 2025, "M264 2.0T", "W167 GLE350 = M264 2.0T 255hp [WIKIGLE W167]"),
    ("GLE400", 2016, 2019, "M276.820", "W166 GLE400 = M276 3.0TT 329hp [DBSIB family]"),
    ("GLE450", 2019, 2025, "M256 3.0 I6 Turbo", "W167 GLE450 = M256 I6 362hp [MOTOREV]"),
    ("GLE580", 2020, 2025, "M176 4.0 V8 BiTurbo", "W167 GLE580 = M176 4.0TT 510hp [WIKIG family]"),
    ("GLE63", 2016, 2019, "M157.980", "W166 GLE63 = M157 5.5TT 577hp [DBSIB family]"),
    ("GLE63", 2020, 2025, "M177.980", "W167 GLE63 = M177 4.0TT [WIKIGLE family]"),
    ("GLE300D", 2016, 2016, "OM642.872", "GLE300d = OM642 3.0 240hp [WIKIGLE family]", DIESEL),
    ("GLE550E", 2016, 2018, "M276 3.0 PHEV", "GLE550e = M276 3.0TT PHEV 436hp [WIKIGLE]", "Hybrid"),
    ("GLE43", 2017, 2019, "M276.823", "GLE43 = M276 3.0TT 390hp [DBSIB family]"),
    ("GLE53", 2021, 2025, "M256 AMG (53)", "W167 GLE53 = M256 429hp [MOTOREV]"),
    ("GLS450", 2017, 2019, "M276.823", "X166 GLS450 = M276 3.0TT 362hp [MBWORLDGL family]"),
    ("GLS450", 2020, 2025, "M256 3.0 I6 Turbo", "X167 GLS450 = M256 362hp [WIKIGLE family]"),
    ("GLS550", 2017, 2019, "M278.929", "X166 GLS550 = M278 4.7TT 449hp [MBWORLDGL family]"),
    ("GLS580", 2020, 2025, "M176 4.0 V8 BiTurbo", "X167 GLS580 = M176 4.0TT [WIKIG family]"),
    ("GLS63", 2017, 2019, "M157.980", "X166 GLS63 = M157 577hp [DBSIB family]"),
    ("GLS63", 2020, 2025, "M177.980", "X167 GLS63 = M177 4.0TT [WIKIG family]"),
    ("GLS350D", 2017, 2017, "OM642.868", "X166 GLS350d = OM642 3.0 255hp [DBSIB family]", DIESEL),
    # ---------- R ----------
    ("R320", 2007, 2009, "OM642.940", "R320 Bluetec = OM642 3.0 210hp [MOTOREV family]", DIESEL),
    ("R350", 2006, 2007, "M272.967", "W251 R350 = M272 3.5 268hp [DBSIB]"),
    ("R350", 2009, 2012, "OM642.940", "R350 Bluetec = OM642 210hp [MOTOREV family]", DIESEL),
    ("R500", 2006, 2007, "M113.971", "R500 = M113 5.0 302hp [DBSIB R 500 row]"),
    ("R63", 2007, 2007, "M156.980", "R63 AMG = M156 6.2 503hp [DBSIB family]"),
    # ---------- CLA / GLA / GLB / EQB ----------
    ("CLA250", 2014, 2018, "M270.920", "W117 CLA250 = M270 2.0T 208hp [M260GUIDE family]"),
    ("CLA250", 2019, 2025, "M260 2.0T", "C118 CLA250 = M260 2.0T 221hp [M260GUIDE]"),
    ("CLA45", 2014, 2018, "M133.980", "W117 CLA45 = M133 2.0T 355-375hp [M260GUIDE][DBSIB]"),
    ("CLA45", 2020, 2023, "M139 AMG (45)", "C118 CLA45 = M139 382hp [M260GUIDE]"),
    ("CLA35", 2020, 2025, "M260 AMG (35)", "CLA35 = M260 AMG 302hp [M260GUIDE]"),
    ("GLA250", 2015, 2019, "M270.920", "X156 GLA250 = M270 2.0T 208hp [M260GUIDE family]"),
    ("GLA250", 2021, 2025, "M260 2.0T", "H247 GLA250 = M260 2.0T 221hp [M260GUIDE]"),
    ("GLA45", 2015, 2019, "M133.980", "X156 GLA45 = M133 2.0T 355-375hp [M260GUIDE][DBSIB]"),
    ("GLA45", 2021, 2025, "M139 AMG (45)", "H247 GLA45 = M139 382hp [M260GUIDE]"),
    ("GLA35", 2021, 2025, "M260 AMG (35)", "GLA35 = M260 AMG 302hp [M260GUIDE]"),
    ("GLB250", 2020, 2025, "M260 2.0T", "X247 GLB250 = M260 2.0T 221hp [M260GUIDE]"),
    ("GLB35", 2021, 2025, "M260 AMG (35)", "GLB35 = M260 AMG 302hp [M260GUIDE]"),
    ("EQB300", 2022, 2025, "EQB300 Electric", "EQB300 = 225hp dual motor [CDEQB]", "Electric"),
    ("EQB350", 2022, 2025, "EQB350 Electric", "EQB350 = 288hp dual motor [CDEQB]", "Electric"),
    ("EQB250+", 2023, 2025, "EQB250+ Electric", "EQB250+ = 190hp single motor FWD [CDEQB]", "Electric"),
    ("EQS450+", 2023, 2023, "EQS450+ Electric", "EQS450+ = rear PSM electric [MBUSAEQS]", "Electric"),
    # ---------- vans ----------
    ("METRIS", 2016, 2023, "M274.920", "Metris = M274 2.0T 208hp [CDMETRIS][WIKIM274]"),
    # ---------- GLC ----------
    ("GLC300", 2016, 2019, "M274.920", "X253 GLC300 = M274 2.0T 241hp [BAVDISM GLC][DBSIB]"),
    ("GLC300", 2020, 2025, "M254 2.0T", "X254 GLC300 = M254 2.0T 255hp [BAVDISM family]"),
    ("GLC43", 2017, 2023, "M276.823", "GLC43 = M276 3.0TT 385hp [BAVDISM][DBSIB]"),
    ("GLC63", 2018, 2021, "M177.980", "GLC63 = M177 4.0TT 469-503hp [BAVDISM][DBSIB]"),
    ("GLC350E", 2018, 2020, "M274 PHEV (C350e)", "GLC350e = M274 PHEV [DBSIB family]", "Hybrid"),
]

def decide(base, year, fuel, slug, cc, vin, code):
    f = (fuel or "").lower()
    # E400 hybrid slug -> hybrid engine
    if base == "E400" and ("HYBRID" in (slug or "").upper() or "hybrid" in f):
        return ("M276.960", "E400 Hybrid = M276 3.5 NA + 27hp motor [HAGERTY212][DBSIB M276.960]", "Hybrid")
    # SPRINTER: cc-bearing rows + 3500 slug
    if base == "SPRINTER":
        if cc == 3000:
            return ("OM642.992", "Sprinter 3.0 = OM642 V6 diesel 188hp [WIKISPR][DBSIB Sprinter rows]", DIESEL)
        if cc in (2100, 2200):
            return ("OM651.955", "Sprinter 2.1 = OM651 4cyl diesel 161hp [WIKISPR OM651 until 2022][DBSIB]", DIESEL)
        if slug and "3500" in slug:
            if year <= 2022:
                return ("OM642.992", "Sprinter 3500 = OM642 3.0 diesel 188hp (2010-2022) [WIKISPR]", DIESEL)
            return ("654", "2023+ Sprinter = OM654 2.0 diesel 168/208hp [CDSPR23]", DIESEL)
        return (None, "Sprinter bare (2500 gas/diesel, 4cyl/6cyl unknown) - skipped", None)
    for (b, ylo, yhi, target, note, *ff) in R:
        if b == base and ylo <= year <= yhi:
            fuel_fix = ff[0] if ff else None
            return (target, note, fuel_fix)
    if base == "MAYBACH":
        return (None, "Maybach base model unknown (S580 vs GLS600) - skipped", None)
    if base == "GT" and year == 2024:
        return (None, "2024 AMG GT = C192 (43 M139 / 55-63 M177) - ambiguous", None)
    if base == "SL55" and 2009 <= year <= 2021:
        return (None, "SL55 not offered 2009-2021 (likely SL550 mislabel) - skipped", None)
    if base == "S350" and year < 2012:
        return (None, "S350 pre-2012 not a US model - skipped", None)
    if base == "C280" and year <= 2004:
        return (None, "C280 2000-2004 = W202 M104 I6 - no clean DB row - skipped", None)
    if base == "C230" and year <= 2002:
        return (None, "C230 2000-2002 = W202 2.3 Kompressor - skipped", None)
    if base == "E350" and year == 2017:
        return (None, "2017 W213 had E400 (no E350) - skipped", None)
    if base == "R350" and year == 2008:
        return (None, "R350 2008: gas vs Bluetec both offered - skipped", None)
    if base == "E320" and 2000 <= year <= 2002 and False:
        pass
    return (None, f"no rule for {base} {year}", None)

RE_CC = re.compile(r"^LEMON_MERCEDES_(.+?)_(\d{4})CC(?:_VIN(\w))?_(\d{4})$")
RE_BARE = re.compile(r"^LEMON_MERCEDES_(.+?)_(\d{4})$")
RE_SLUG = re.compile(r"^LEMON_MERCEDES_(.+?)_(\d{4})_([A-Z0-9\+]+)$")

def parse_code(code):
    m = RE_CC.match(code)
    if m: return m.group(1), int(m.group(2)), m.group(3), int(m.group(4)), None
    m = RE_SLUG.match(code)
    if m: return m.group(1), None, None, int(m.group(2)), m.group(3)
    m = RE_BARE.match(code)
    if m: return m.group(1), None, None, int(m.group(2)), None
    return None

def main():
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    rows = list(cur.execute("""SELECT id, car_brand, car_model, car_year, fuel, engine_code
        FROM vehicle_variants WHERE engine_code LIKE 'LEMON_MERCEDES%'"""))
    print(f"LEMON_MERCEDES variants: {len(rows)}")
    decisions, unmapped = [], []
    for vid, brand, model, year, fuel, code in rows:
        p = parse_code(code)
        if not p:
            unmapped.append((vid, model, year, code, "unparseable")); continue
        base, cc, vin, ycode, slug = p
        target, note, fuel_fix = decide(base, year, fuel, slug, cc, vin, code)
        if not target:
            unmapped.append((vid, model, year, code, note)); continue
        decisions.append((vid, brand, model, year, code, target, note, fuel_fix))

    print(f"mapped: {len(decisions)} | skipped: {len(unmapped)}")
    reasons = defaultdict(list)
    for vid, model, year, code, why in unmapped:
        reasons[(model, why)].append((year, code))
    print("=== SKIPPED groups ===")
    for k in sorted(reasons, key=lambda k: -len(reasons[k])):
        print(f"  {k}: {len(reasons[k])}  e.g. {reasons[k][:3]}")

    existing = {r[0] for r in cur.execute("SELECT engine_code FROM engines")}
    missing = {d[5] for d in decisions} - existing - set(NEW_ENGINES)
    if missing:
        print("FATAL missing targets:", missing); sys.exit(1)

    if not APPLY:
        with open("database_enriched/csv_exports/21_lemon_batch4_decisions_DRYRUN.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
            for d in decisions: w.writerow([d[0],d[1],d[2],d[3],d[4],d[5],d[7] or "",d[6]])
        print("DRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_step13_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, (etype, fuel, cc, hp, cyl) in NEW_ENGINES.items():
        cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,))
        if not cur.fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,'STEP13_VERIFIED')""",
                (code, etype, fuel, cc, hp, cyl))
            print(f"  created {code}")
    for code, fixes in ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  row-fix {code}: {fixes}")

    lemon_retired = defaultdict(list)
    for vid, brand, model, year, old, new, note, fuel_fix in decisions:
        cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=COALESCE(?, fuel) WHERE id=?", (new, fuel_fix, vid))
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=COALESCE(engine_power_hp,
            (SELECT power_hp FROM engines WHERE engine_code=?)),
            engine_type=COALESCE(engine_type, (SELECT engine_type FROM engines WHERE engine_code=?)) WHERE id=?""", (new, new, vid))
        lemon_retired[old].append((vid, year, brand, model))

    spec_cols_s = [c[1] for c in cur.execute("PRAGMA table_info(engine_service_specs)")]
    spec_cols_t = [c[1] for c in cur.execute("PRAGMA table_info(engine_technical_specs)")]

    def merge_specs(table, cols, lc, target):
        cols = [c for c in cols if c != "engine_code"]
        cur.execute(f"SELECT {','.join(cols)} FROM {table} WHERE engine_code=?", (lc,))
        src = cur.fetchone()
        if src is None: return
        if table == "engine_service_specs":
            srow = cur.execute("SELECT oil_spec_source FROM engine_service_specs WHERE engine_code=?", (lc,)).fetchone()
            if srow and srow[0] and "ESTIMATE" in srow[0].upper():
                cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (lc,)); return
        cur.execute(f"SELECT 1 FROM {table} WHERE engine_code=?", (target,))
        if cur.fetchone():
            sets = ", ".join(f"{c}=COALESCE({c}, ?)" for c in cols)
            cur.execute(f"UPDATE {table} SET {sets} WHERE engine_code=?", (*src, target))
        else:
            cur.execute(f"INSERT INTO {table} (engine_code, {','.join(cols)}) VALUES (?, {','.join('?'*len(cols))})", (target, *src))
        cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (lc,))

    migrated = 0
    for lc, vs in sorted(lemon_retired.items(), key=lambda kv: kv[1][0][1]):
        target = cur.execute("SELECT engine_code FROM vehicle_variants WHERE id=?", (vs[0][0],)).fetchone()[0]
        merge_specs("engine_service_specs", spec_cols_s, lc, target)
        merge_specs("engine_technical_specs", spec_cols_t, lc, target)
        cur.execute("""UPDATE engines SET displacement_cc=COALESCE(displacement_cc,
            (SELECT displacement_cc FROM engines WHERE engine_code=?)),
            fuel=COALESCE(fuel, (SELECT fuel FROM engines WHERE engine_code=?)) WHERE engine_code=?""", (lc, lc, target))
        cur.execute("DELETE FROM engines WHERE engine_code=?", (lc,))
        migrated += 1

    cur.execute("""UPDATE engines SET count_variants =
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")
    con.commit()
    print(f"\nvariants remapped: {len(decisions)} | LEMON codes retired: {migrated}")
    print("=== VERIFY ===")
    print("LEMON_MERCEDES remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON_MERCEDES%'").fetchone()[0])
    print("LEMON total remaining:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e
        ON e.engine_code=v.engine_code WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM (SELECT e.engine_code FROM engines e
        LEFT JOIN vehicle_variants v ON v.engine_code=e.engine_code
        GROUP BY e.engine_code HAVING e.count_variants != COUNT(v.id))""").fetchone()[0])
    print("engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    cnt = Counter(d[5] for d in decisions)
    print("top targets:")
    for code, n in cnt.most_common(30): print(f"   {n:3}  {code}")
    with open("database_enriched/csv_exports/21_lemon_batch4_decisions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["variant_id","brand","model","year","old_engine_code","new_engine_code","fuel_fix","evidence"])
        for d in decisions: w.writerow([d[0],d[1],d[2],d[3],d[4],d[5],d[7] or "",d[6]])
    con.close(); print("decisions CSV written")

main()
