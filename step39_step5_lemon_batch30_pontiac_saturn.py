"""Step 39 (Step 5, batch 30): merged Pontiac + Saturn LEMON replacement — 134 rows (85 + 49).

Pontiac and Saturn were GM's badge-engineered divisions in exactly the same years as these rows
(2005-2010) and shared one engine catalogue with Chevrolet/Buick/Opel, platform for platform:

- Epsilon:   G6 = Aura = Malibu           -> 2.4 LE5, 3.5 LX9/LZ4, 3.6 LY7, 3.9 LZ9
- Delta:     G5 = Pursuit = Cobalt        -> 2.2 L61/LAP, 2.4 LE5
- Kappa:     Solstice = Sky               -> 2.4 LE5, 2.0 LNF turbo
- Theta:     Torrent = Equinox = Vue      -> 3.4 LNJ, 3.6 LY7, 2.2 L61, 2.4 LE5/LAT
- Lambda:    Outlook = Acadia = Enclave   -> 3.6 LY7 then LLT
- U-body:    Montana SV6 = Relay = Uplander -> 3.5 LX9, 3.9 LZ9
- Zeta/GM-DAT/Opel: G8 = Holden Commodore, G3/Wave = Aveo, Astra = Opel Astra H, Vibe = Matrix

Every target therefore comes from the GM vocabulary already verified in steps 27/36 (the
GMC+Chevrolet batch) plus three codes this batch creates. Decode is nameplate + crawl
displacement + the model-year SAE rating, which for the Epsilon cars changed three times
(2006 -> 2007 VVT -> 2008 SAE re-rating) [WIKIG6].

Two findings worth the batch:
- The 2005-2007 Saturn Vue 3.5 V6 is not a GM engine at all: it is Honda's J35S1/J35A3, bought
  in and catalogued by GM as **L66**, 250hp [WIKIVUE][CG_VUE].
- `LEMON_SATURN_VUE_2400CC_2007` can only be the Vue Green Line: 2.4 was never offered on the
  first-generation Vue except as the BAS mild-hybrid, so that row is hybrid, not petrol [WIKIVUE].
"""
import step5_lemon_lib as lib

CIT = {
    "WIKIG6": "https://en.wikipedia.org/wiki/Pontiac_G6 (2005 = 3.5 pushrod V6 200hp only; 2006 adds 2.4 DOHC 169hp base and the GTP's 3.9 VVT 240hp, 227hp on the convertible; 2007: GT 3.5 gains VVT 200->224hp, 3.9 = 227hp auto / 240hp manual, GTP gets the 3.6 DOHC VVT 252hp; 2008: GXP replaces GTP, 3.9 down to 222hp, SAE re-ratings drop the 2.4 to 164hp and the 3.5 to 219hp)",
    "WIKIVUE": "https://en.wikipedia.org/wiki/Saturn_Vue (first-gen engines: 2.2 L61 I4, 2.4 LAT mild-hybrid I4 (Green Line, 2007 only), 3.0 L81 V6, 3.5 L66 V6; 'starting in 2004, all six-cylinder Vues were equipped with Honda's 250-horsepower J35A3 engine and a Honda transmission'; engine table '2004-2007 3.5 L GM L66 (J35S1) V6 250 hp')",
    "CG_VUE": "https://consumerguide.com/used/2002-07-saturn-vue/ (Vue 2.2 I4 143hp; 2.4 I4 170hp; original 3.0 V6 181hp; Honda-supplied 3.5 V6 250hp from 2004)",
    "GMLINEUP": "GM US/Canada lineup ratings by model year for the Pontiac and Saturn badges: Aztek 3.4 LA1 185hp; Bonneville SE/SLE 3.8 L36 205hp and GXP 4.6 Northstar LD8 275hp; G3/Wave (Aveo) 1.6 103-106hp; G5/Pursuit/Cobalt 2.2 145hp (L61) -> 148hp (LAP 2007-09) -> 155hp (2010), 2.4 LE5 171-173hp; G8 3.6 LY7 256hp, 6.0 L76 361hp, GXP 6.2 LS3 415hp; GTO 6.0 LS2 400hp; Grand Prix 3.8 L26 200hp and GXP 5.3 LS4 303hp; Montana SV6/Relay/Uplander 3.5 LX9 200hp then 3.9 LZ9 240hp; Solstice/Sky 2.4 LE5 177hp and 2.0 LNF turbo 260hp; Sunfire/ION 2.2 Ecotec 140-145hp, ION 2.4 175hp; Torrent 3.4 LNJ 185hp and GXP 3.6 LY7 264hp; Vibe/Matrix 1.8 1ZZ-FE 126hp (2003-08), 1.8 2ZR-FE 132hp and 2.4 2AZ-FE 158hp (2009-10); Astra 1.8 Z18XER 138hp; Aura XE 2.4 169/164hp, 3.5 224/219hp, XR 3.6 252hp; L300 3.0 L81 182hp; Outlook 3.6 LY7 275hp (2007-08) then 3.6 LLT DI 288hp (2009-10); Vue 2.2 L61 143hp, 2.4 LE5 169hp (2008+), 3.5 LZ4 219hp (2008+), 3.6 LY7 257hp",
    "GMVOCAB": "GM engine rows verified in steps 27/36: LA1 3350/188, L36 3791, L26 3800/200, LS4 5300/303, LD8 4565/275, L61 2200, LAP 2198/149, LE5 2400, LX9 3498/200, LZ4 3498, LZ9 3880/240, LY7 3600/255, LLT 3600/304, LNJ 3350/185, LNF 1998/264, L76 5967/354, LS2 5967/405, LS3 6162/430, L91 1598/105, F16D3 1600/107, Z18XER 1800/138, 1ZZ-FE 1794, 2ZR-FE 1800/135, 2AZ-FE 2400/165",
}

NE = {
    "L66": ("3.5 V6 SOHC 24v (GM L66 = Honda J35S1/J35A3, Saturn Vue 2004-2007, 250hp)",
            "Petrol", 3471, 250, 6),
    "L81": ("3.0 V6 DOHC 24v (Saturn L-series/Vue, Opel-derived, 182hp)", "Petrol", 2962, 182, 6),
    "LAT": ("2.4 I4 Ecotec BAS mild hybrid (Saturn Vue/Aura Green Line, 170hp)",
            "Hybrid", 2384, 170, 4),
}

R = [
    # ======================= PONTIAC =======================
    ("AZTEK", 2005, 2005, None, None, "LA1", "Aztek 2005 = 3.4 V6 OHV LA1 185hp, its only engine [GMLINEUP][GMVOCAB]", 185),
    ("BONNEVILLE", 2005, 2005, 3800, None, "L36", "Bonneville SE/SLE 2005 3800CC = 3.8 V6 3800 Series III L36 205hp [GMLINEUP]", 205),
    ("BONNEVILLE", 2005, 2005, 4600, None, "LD8", "Bonneville GXP 2004-05 4600CC = 4.6 Northstar V8 LD8 275hp, the only 4.6 offered [GMLINEUP][GMVOCAB]", 275),
    ("G3", 2009, 2010, None, None, "L91", "Pontiac G3 (Canadian/US Aveo) 2009-2010 = 1.6 DOHC L91 106hp, its only engine [GMLINEUP]", 106),
    ("G5", 2006, 2006, 2200, None, "L61", "G5 2006 2200CC = 2.2 Ecotec L61 145hp (Cobalt base engine) [GMLINEUP]", 145),
    ("G5", 2007, 2009, 2200, None, "LAP", "G5 2007-2009 2200CC = 2.2 Ecotec VVT LAP 148hp [GMLINEUP][GMVOCAB]", 148),
    ("G5", 2010, 2010, None, None, "LAP", "G5 2010 = 2.2 Ecotec VVT LAP 155hp, the only engine in its final year [GMLINEUP]", 155),
    ("G5", 2006, 2007, 2400, None, "LE5", "G5 GT 2006-2007 2400CC = 2.4 Ecotec LE5 171hp [GMLINEUP]", 171),
    ("G5", 2008, 2008, 2400, None, "LE5", "G5 GT 2008 2400CC = 2.4 Ecotec LE5 173hp (revised SAE rating) [GMLINEUP]", 173),
    ("G6", 2005, 2005, None, None, "LX9", "G6 2005 = 3.5 pushrod V6 LX9 200hp; both trims used it and no I4 was offered yet [WIKIG6]", 200),
    ("G6", 2006, 2007, 2400, None, "LE5", "G6 base/SE 2006-2007 2400CC = 2.4 DOHC LE5 169hp [WIKIG6]", 169),
    ("G6", 2008, 2010, 2400, None, "LE5", "G6 2008-2010 2400CC = 2.4 LE5, SAE re-rated to 164hp [WIKIG6]", 164),
    ("G6", 2006, 2006, 3500, None, "LX9", "G6 GT 2006 3500CC = 3.5 V6 LX9 200hp (pre-VVT) [WIKIG6]", 200),
    ("G6", 2007, 2007, 3500, None, "LZ4", "G6 GT 2007 3500CC = 3.5 V6 with VVT (LZ4), raised from 200 to 224hp [WIKIG6]", 224),
    ("G6", 2008, 2010, 3500, None, "LZ4", "G6 2008-2010 3500CC = 3.5 LZ4, SAE re-rated to 219hp [WIKIG6]", 219),
    ("G6", 2007, 2010, 3600, None, "LY7", "G6 GTP/GXP 2007-2010 3600CC = 3.6 DOHC 24v VVT LY7 252hp @6300 [WIKIG6]", 252),
    ("G6", 2006, 2006, 3900, None, "LZ9", "G6 GTP 2006 3900CC = 3.9 V6 VVT LZ9 240hp [WIKIG6]", 240),
    ("G6", 2007, 2007, 3900, None, "LZ9", "G6 GT 2007 3900CC = 3.9 LZ9 227hp with the automatic (240hp manual, dropped mid-year) [WIKIG6]", 227),
    ("G6", 2008, 2010, 3900, None, "LZ9", "G6 2008-2010 3900CC = 3.9 LZ9, convertible-only option, 222hp [WIKIG6]", 222),
    ("G8", 2008, 2009, 3600, None, "LY7", "G8 (Holden Commodore VE) 3600CC = 3.6 LY7 256hp base engine [GMLINEUP][GMVOCAB]", 256),
    ("G8", 2008, 2009, 6000, None, "L76", "G8 GT 6000CC = 6.0 V8 L76 with AFM, 361hp [GMLINEUP][GMVOCAB]", 361),
    ("G8", 2009, 2009, 6200, None, "LS3", "G8 GXP 2009 6200CC = 6.2 V8 LS3 415hp [GMLINEUP][GMVOCAB]", 415),
    ("GTO", 2005, 2006, None, None, "LS2", "GTO 2005-2006 = 6.0 V8 LS2 400hp, its only engine [GMLINEUP][GMVOCAB]", 400),
    ("GRAND", 2005, 2008, 3800, None, "L26", "Grand Prix 3800CC = 3.8 V6 3800 Series III L26 200hp, the base/GT engine (supercharged L32 260hp only on the GTP) [GMLINEUP]", 200),
    ("GRAND", 2005, 2008, 5300, None, "LS4", "Grand Prix GXP 5300CC = 5.3 V8 LS4 FWD 303hp, the only V8 offered [GMLINEUP][GMVOCAB]", 303),
    ("MONTANA", 2005, 2005, None, None, "LA1", "Montana 2005 (short-wheelbase, final year) = 3.4 V6 LA1 185hp, its only engine [GMLINEUP]", 185),
    ("MONTANA", 2006, 2006, 3500, None, "LX9", "Montana SV6 2006 3500CC = 3.5 V6 LX9 200hp base engine [GMLINEUP]", 200),
    ("MONTANA", 2006, 2006, 3900, None, "LZ9", "Montana SV6 2006 3900CC = 3.9 V6 LZ9 240hp [GMLINEUP]", 240),
    ("MONTANA", 2007, 2009, None, None, "LZ9", "Montana SV6 2007-2009 (Canada only) = 3.9 V6 LZ9 240hp standard after the 3.5 was dropped [GMLINEUP]", 240),
    ("PURSUIT", 2005, 2005, 2200, None, "L61", "Pontiac Pursuit (Canadian Cobalt) 2200CC = 2.2 Ecotec L61 145hp base engine [GMLINEUP]", 145),
    ("PURSUIT", 2005, 2005, 2400, None, "LE5", "Pursuit GT 2400CC = 2.4 Ecotec LE5 171hp, the only 2.4 in the Delta range [GMLINEUP]", 171),
    ("SOLSTICE", 2006, 2006, None, None, "LE5", "Solstice 2006 = 2.4 Ecotec LE5 177hp, its only engine (the GXP turbo arrived for 2007) [GMLINEUP]", 177),
    ("SOLSTICE", 2007, 2010, 2000, None, "LNF", "Solstice GXP 2000CC = 2.0 Ecotec turbo DI LNF 260hp [GMLINEUP][GMVOCAB]", 260),
    ("SOLSTICE", 2007, 2010, 2400, None, "LE5", "Solstice base 2400CC = 2.4 Ecotec LE5 177hp [GMLINEUP]", 177),
    ("SUNFIRE", 2005, 2005, None, None, "L61", "Sunfire 2005 (final year) = 2.2 Ecotec L61 140hp, its only engine [GMLINEUP]", 140),
    ("TORRENT", 2006, 2007, None, None, "LNJ", "Torrent 2006-2007 = 3.4 V6 LNJ 185hp, its only engine [GMLINEUP][GMVOCAB]", 185),
    ("TORRENT", 2008, 2009, 3400, None, "LNJ", "Torrent 2008-2009 3400CC = 3.4 V6 LNJ 185hp base engine [GMLINEUP][GMVOCAB]", 185),
    ("TORRENT", 2008, 2009, 3600, None, "LY7", "Torrent GXP 3600CC = 3.6 V6 DOHC LY7 264hp [GMLINEUP]", 264),
    ("VIBE", 2005, 2008, None, None, "1ZZ-FE", "Vibe (NUMMI Toyota Matrix twin) 2005-2008 bare = 1.8 1ZZ-FE 126hp base volume engine (the GT's 2ZZ-GE 164hp was a low-volume option) [GMLINEUP]", 126),
    ("VIBE", 2009, 2010, 1800, None, "2ZR-FE", "Vibe 2009-2010 1800CC = 1.8 2ZR-FE Dual VVT-i 132hp [GMLINEUP]", 132),
    ("VIBE", 2009, 2010, 2400, None, "2AZ-FE", "Vibe GT/AWD 2009-2010 2400CC = 2.4 2AZ-FE 158hp [GMLINEUP]", 158),
    ("WAVE", 2005, 2008, None, None, "F16D3", "Pontiac Wave (Canadian Aveo, GM-DAT) 2005-2008 = 1.6 E-TEC II F16D3 103hp, its only engine [GMLINEUP][GMVOCAB]", 103),

    # ======================= SATURN =======================
    ("ASTRA", 2008, 2009, None, None, "Z18XER", "Saturn Astra (Opel Astra H) 2008-2009 = 1.8 Ecotec Z18XER 138hp, the only engine sold in the US [GMLINEUP][GMVOCAB]", 138),
    ("AURA", 2007, 2007, 2400, None, "LE5", "Aura XE 2007 2400CC = 2.4 Ecotec LE5 169hp (Epsilon twin of the G6) [WIKIG6][GMLINEUP]", 169),
    ("AURA", 2008, 2009, 2400, None, "LE5", "Aura 2008-2009 2400CC = 2.4 LE5, SAE re-rated to 164hp [WIKIG6][GMLINEUP]", 164),
    ("AURA", 2007, 2007, 3500, None, "LZ4", "Aura XE 2007 3500CC = 3.5 V6 VVT LZ4 224hp [WIKIG6][GMLINEUP]", 224),
    ("AURA", 2008, 2008, 3500, None, "LZ4", "Aura 2008 3500CC = 3.5 LZ4, SAE re-rated to 219hp [WIKIG6][GMLINEUP]", 219),
    ("AURA", 2007, 2009, 3600, None, "LY7", "Aura XR 3600CC = 3.6 V6 DOHC VVT LY7 252hp [WIKIG6][GMLINEUP]", 252),
    ("ION", 2005, 2005, None, None, "L61", "ION 2005 bare = 2.2 Ecotec L61 140hp base volume engine (2.0 supercharged LSJ only on the Red Line) [GMLINEUP]", 140),
    ("ION", 2006, 2007, None, None, "L61", "ION 2006-2007 bare = 2.2 Ecotec L61 145hp base volume engine [GMLINEUP]", 145),
    ("ION", 2006, 2007, 2200, None, "L61", "ION 2006-2007 2200CC = 2.2 Ecotec L61 145hp [GMLINEUP]", 145),
    ("ION", 2006, 2006, 2400, None, "LE5", "ION 2006 2400CC = 2.4 Ecotec LE5 175hp (optional on the ION 2/3) [GMLINEUP]", 175),
    ("ION", 2007, 2007, 2400, None, "LE5", "ION 2007 2400CC = 2.4 Ecotec LE5 173hp (revised SAE rating, final year) [GMLINEUP]", 173),
    ("L300", 2005, 2005, None, None, "L81", "Saturn L300 2005 = 3.0 V6 DOHC L81 182hp, the V6 L-series' only engine [GMLINEUP][CG_VUE]", 182),
    ("OUTLOOK", 2007, 2008, None, None, "LY7", "Outlook (Lambda) 2007-2008 = 3.6 V6 VVT LY7 275hp, its only engine [GMLINEUP]", 275),
    ("OUTLOOK", 2009, 2010, None, None, "LLT", "Outlook 2009-2010 = 3.6 V6 direct-injection LLT 288hp [GMLINEUP][GMVOCAB]", 288),
    ("RELAY", 2005, 2005, None, None, "LX9", "Relay 2005 = 3.5 V6 LX9 200hp, its only engine at launch [GMLINEUP]", 200),
    ("RELAY", 2006, 2007, None, None, "LZ9", "Relay 2006-2007 = 3.9 V6 LZ9 240hp, standard after the 3.5 was dropped [GMLINEUP]", 240),
    ("SKY", 2007, 2010, 2000, None, "LNF", "Sky Red Line 2000CC = 2.0 Ecotec turbo DI LNF 260hp (Kappa twin of the Solstice GXP) [GMLINEUP][GMVOCAB]", 260),
    ("SKY", 2007, 2010, 2400, None, "LE5", "Sky base 2400CC = 2.4 Ecotec LE5 177hp [GMLINEUP]", 177),
    ("VUE", 2005, 2007, 2200, None, "L61", "Vue (first gen) 2200CC = 2.2 Ecotec L61 143hp base engine [WIKIVUE][CG_VUE]", 143),
    ("VUE", 2007, 2007, 2400, None, "LAT", "Vue 2007 2400CC can only be the Green Line: the 2.4 LAT BAS mild hybrid, 170hp, was the sole 2.4 offered on the first-generation Vue and only in 2007 [WIKIVUE][CG_VUE]", 170),
    ("VUE", 2008, 2010, 2400, None, "LE5", "Vue (second gen) 2008-2010 2400CC = 2.4 Ecotec LE5 169hp base engine [GMLINEUP]", 169),
    ("VUE", 2005, 2007, 3500, None, "L66", "Vue 2004-2007 3500CC = GM L66, i.e. Honda's J35S1/J35A3 V6 with a Honda 5-speed, 250hp - the only GM vehicle to use a Honda engine [WIKIVUE][CG_VUE]", 250),
    ("VUE", 2008, 2010, 3500, None, "LZ4", "Vue XE 2008-2010 3500CC = 3.5 V6 LZ4 219hp [GMLINEUP]", 219),
    ("VUE", 2008, 2010, 3600, None, "LY7", "Vue XR 2008-2010 3600CC = 3.6 V6 DOHC VVT LY7 257hp [GMLINEUP]", 257),
]

TRIM = {}


def extra_decide(model, year, cc, vin, post, code, brand=None):
    """The bare 2005 'GRAND' row is unresolvable: Pontiac sold both the Grand Prix (3.8 V6) and
    the Grand Am (2.2 I4 / 3.4 V6) in 2005, the crawl truncates both to 'Grand', and this row
    carries no displacement to separate them. The displacement-bearing 2005 Grand rows are
    handled by the Grand Prix rules; only the bare one is skipped."""
    if lib.norm_model(model) == "GRAND" and cc is None:
        return (None, "ambiguous nameplate: 2005 'Grand' with no displacement could be Grand Prix "
                      "(3.8 L26 200hp) or Grand Am (2.2 L61 140hp / 3.4 LA1 170hp) - both were "
                      "sold in 2005 and the crawl truncates both names; left as LEMON", None, None)
    return None


IDENTITY = {
    "LA1": ("Petrol", 3350), "L36": ("Petrol", 3791), "LD8": ("Petrol", 4565),
    "L91": ("Petrol", 1598), "L61": ("Petrol", 2200), "LAP": ("Petrol", 2198),
    "LE5": ("Petrol", 2400), "LX9": ("Petrol", 3498), "LZ4": ("Petrol", 3498),
    "LY7": ("Petrol", 3600), "LZ9": ("Petrol", 3880), "L76": ("Petrol", 5967),
    "LS2": ("Petrol", 5967), "LS3": ("Petrol", 6162), "L26": ("Petrol", 3800),
    "LS4": ("Petrol", 5300), "LNJ": ("Petrol", 3350), "LNF": ("Petrol", 1998),
    "1ZZ-FE": ("Petrol", 1794), "2ZR-FE": ("Petrol", 1800), "2AZ-FE": ("Petrol", 2400),
    "F16D3": ("Petrol", 1600), "Z18XER": ("Petrol", 1800), "LLT": ("Petrol", 3600),
}

ROW_FIXES = {
    "L36": {"engine_type": "3.8 V6 OHV 3800 Series II/III (Buick-GM L36: Bonneville/LeSabre/Park Avenue 205hp; row also holds Holden Ecotec L36 3.8 207hp rows)",
            "cylinders": 6, "data_confidence": "STEP39_VERIFIED"},
    "L61": {"engine_type": "2.2 I4 DOHC Ecotec L61 (Cobalt/G5/Pursuit/ION/Sunfire/Vue 140-145hp; row also holds Alfa Romeo 2.2 JTS rows)",
            "cylinders": 4, "data_confidence": "STEP39_VERIFIED"},
    "LE5": {"engine_type": "2.4 I4 DOHC Ecotec VVT LE5 (G6/Aura/Malibu 164-169, Solstice/Sky 177, Cobalt SS/G5 GT 171-173hp)",
            "cylinders": 4, "data_confidence": "STEP39_VERIFIED"},
    "LZ4": {"engine_type": "3.5 V6 OHV High-Value VVT LZ4 (G6/Aura 219-224 / Vue 219 / Impala 211hp)",
            "power_hp": 219, "cylinders": 6, "data_confidence": "STEP39_VERIFIED"},
    "LNF": {"engine_type": "2.0 I4 Ecotec turbo direct-injection LNF (Solstice GXP / Sky Red Line / HHR SS 260-264hp)",
            "cylinders": 4, "data_confidence": "STEP39_VERIFIED"},
    "LS2": {"engine_type": "6.0 V8 OHV LS2 (GTO 400 / Corvette 400 / Trailblazer SS 395hp)",
            "cylinders": 8, "data_confidence": "STEP39_VERIFIED"},
    "LS3": {"engine_type": "6.2 V8 OHV LS3 (G8 GXP 415 / Corvette 430 / Camaro SS 426hp)",
            "cylinders": 8, "data_confidence": "STEP39_VERIFIED"},
    "L91": {"engine_type": "1.6 I4 DOHC E-TEC II L91 (Aveo/G3/Wave 2009-2011, 106hp)",
            "cylinders": 4, "data_confidence": "STEP39_VERIFIED"},
    "1ZZ-FE": {"engine_type": "1.8 I4 DOHC VVT-i 1ZZ-FE (Corolla/Matrix/Vibe 126-130hp; also Lotus Elise base)",
               "cylinders": 4, "data_confidence": "STEP39_VERIFIED"},
    "2AZ-FE": {"engine_type": "2.4 I4 DOHC VVT-i 2AZ-FE (Camry/RAV4/Matrix-Vibe 158-166hp)",
               "cylinders": 4, "data_confidence": "STEP39_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand=["Pontiac", "Saturn"], step_tag="step39", csv_num=47,
    lemon_baseline=874, engines_baseline=6501,
    R=R, NEW_ENGINES=NE, TRIM_RULES=TRIM, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    FUEL_FIX_BY_TARGET={"LAT": "Hybrid"},
    extra_decide=extra_decide,
    expect_mapped=133, expect_skipped=1,
))
