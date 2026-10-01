"""Step 53 (Step 5, batch 44): Hummer + Cadillac + GMC + Pontiac LEMON replacement — 28 rows.

The last GM brands in the queue, run together because they share one truck engine catalogue:
the Vortec 6000 under a Hummer H2 is the same LQ4 as under an Escalade, and the Atlas inline
fives under the H3 are the Colorado/Canyon engines.

| Rows | Target | hp |
|---|---|---|
| Hummer H2 2003-2007 (5) | `LQ4` 6.0 V8 Vortec | 325 |
| Hummer H2 2008-2009 (2) | `L92` 6.2 V8 | 393 |
| Hummer H3 2006 | `L52` 3.5 I5 Atlas | 220 |
| Hummer H3 2007 | `LLR` 3.7 I5 Atlas | 242 |
| Hummer H3/H3T `3700CC` 2008-2010 (5) | `LLR` 3.7 I5 Atlas | 239 |
| Hummer H3/H3T `5300CC` 2008-2010 (5) | `LH8` 5.3 V8 (H3 Alpha) | 300 |
| Cadillac Escalade 2002-2006 (5) | `LQ4` 6.0 V8 Vortec | 345 |
| Cadillac CTS `6200CC` 2015 | `LSA` 6.2 supercharged (CTS-V) | 556 |
| Cadillac STS 2011 | `LLT` 3.6 V6 DI | 302 |
| GMC Sierra `6000CC` VIN J 2012 | `LC8` 6.0 V8 gaseous-fuel capable | 306 |
| Pontiac Grand 2005 | `L61` 2.2 Ecotec | 140 |

The two rows previously parked as un-decodable both resolve here:

- **GMC Sierra 2012** carries VIN engine character **J**, which on a 2012 HD truck is the
  gaseous-fuel-capable 6.0 (`LC8`), not the 360hp `L96` - the VIN digit settles it without
  needing to know the trim.
- **Pontiac "GRAND" 2005** has a truncated nameplate that could be a Grand Am or a Grand Prix,
  but the question this database has to answer is the engine, and the 4.73 L (5 qt) fill only
  fits the 2.2 Ecotec; the 3.4 V6 and the 3800 both take 4.5 qt. The engine is decodable even
  though the model name is not, and the row is mapped with that caveat recorded.
"""
import step5_lemon_lib as lib

CIT = {
    "GMUS": "GM US model-year specifications: Hummer H2 6.0 Vortec LQ4 325hp (2003-2007) and 6.2 L92 393hp (2008-2009); H3 3.5 I5 220hp (2006), 3.7 I5 242hp (2007) and 239hp (2008-2010), 5.3 V8 LH8 300hp (H3/H3T Alpha); Escalade 6.0 LQ4 345hp (2002-2006); CTS-V 2015 6.2 supercharged LSA 556hp; STS 2011 3.6 V6 DI LLT 302hp; Sierra HD 6.0 gaseous-fuel-capable LC8; Pontiac Grand Am 2005 2.2 Ecotec L61 140hp",
    "GMVIN": "GM VIN engine character: J = the 6.0 L gaseous-fuel-capable V8 (LC8) on 2012 HD trucks, as against G/8 for the L96",
    "LEMONFILL": "Oil fill recorded by the crawl: 5.67 L (6 qt) across the V8 trucks and the Atlas inline fives, 4.73 L (5 qt) on the Pontiac - the 2.2 Ecotec's capacity, where the 3.4 V6 and the 3800 both take 4.5 qt",
}

R = [
    ("HUMMER:H2", 2003, 2007, None, None, "LQ4", "H2 2003-2007 = the 6.0 Vortec LQ4, 325hp [GMUS][LEMONFILL]", 325),
    ("HUMMER:H2", 2008, 2009, None, None, "L92", "H2 2008-2009 moved to the 6.2 L92, 393hp [GMUS]", 393),
    ("HUMMER:H3", 2006, 2006, None, None, "L52", "H3 2006 = the 3.5 Atlas inline five, 220hp [GMUS]", 220),
    ("HUMMER:H3", 2007, 2007, None, None, "LLR", "H3 2007 = the 3.7 Atlas inline five, 242hp [GMUS]", 242),
    ("HUMMER:H3", 2008, 2010, 3700, None, "LLR", "H3 3.7L 2008-2010 = the Atlas LLR inline five, 239hp [GMUS]", 239),
    ("HUMMER:H3", 2008, 2010, 5300, None, "LH8", "H3 Alpha 5.3L = the LH8 V8, 300hp [GMUS]", 300),
    ("HUMMER:H3T", 2009, 2010, 3700, None, "LLR", "H3T 3.7L = the Atlas LLR inline five, 239hp [GMUS]", 239),
    ("HUMMER:H3T", 2009, 2010, 5300, None, "LH8", "H3T Alpha 5.3L = the LH8 V8, 300hp [GMUS]", 300),
    ("CADILLAC:ESCALADE", 2002, 2006, None, None, "LQ4", "Escalade 2002-2006 = the 6.0 Vortec LQ4, 345hp, its signature engine (the 5.3 was the 2WD base) [GMUS][LEMONFILL]", 345),
    ("CADILLAC:CTS", 2015, 2015, 6200, None, "LSA", "CTS 6.2L 2015 = the supercharged LSA of the CTS-V, 556hp [GMUS]", 556),
    ("CADILLAC:STS", 2011, 2011, None, None, "LLT", "STS 2011 = the 3.6 V6 direct-injection LLT, 302hp [GMUS][LEMONFILL]", 302),
    ("GMC:SIERRA", 2012, 2012, 6000, "J", "LC8", "Sierra 2012 6.0L with VIN engine character J = the gaseous-fuel-capable LC8, not the 360hp L96 [GMVIN][GMUS]", 306),
    ("PONTIAC:GRAND", 2005, 2005, None, None, "L61", "Pontiac 'GRAND' 2005: the nameplate is truncated (Grand Am or Grand Prix) but the 4.73 L (5 qt) fill only fits the 2.2 Ecotec L61 - the 3.4 V6 and the 3800 both take 4.5 qt - so the engine is the 140hp Grand Am four [GMUS][LEMONFILL]", 140),
]

IDENTITY = {
    "LQ4": ("Petrol", 5967), "L92": ("Petrol", 6162), "L52": ("Petrol", 3460),
    "LLR": ("Petrol", 3653), "LH8": ("Petrol", 5328), "LSA": ("Petrol", 6162),
    "LLT": ("Petrol", 3600), "LC8": ("Petrol", 5967), "L61": ("Petrol", 2200),
}

ROW_FIXES = {
    "LH8": {"engine_type": "5.3 V8 OHV Vortec 5300 LH8 (H3 Alpha / H3T / Colorado, 300hp)",
            "power_hp": 300, "cylinders": 8, "data_confidence": "STEP53_VERIFIED"},
    "L92": {"engine_type": "6.2 V8 OHV Vortec 6200 L92 (H2 2008-09 393 / Escalade 403hp)",
            "cylinders": 8, "data_confidence": "STEP53_VERIFIED"},
    "LQ9": {"engine_type": "6.0 V8 OHV Vortec 6000 HO LQ9 (Escalade/Denali/SS, 345-349hp)",
            "cylinders": 8, "data_confidence": "STEP53_VERIFIED"},
    "L61": {"engine_type": "2.2 I4 DOHC Ecotec L61 (Grand Am 140 / Cobalt 145 / Cobalt 2006+ 148-182hp)",
            "cylinders": 4, "data_confidence": "STEP53_VERIFIED"},
}

lib.run_batch(lib.Cfg(
    brand=["Hummer", "Cadillac", "GMC", "Pontiac"], step_tag="step53", csv_num=61,
    lemon_baseline=146, engines_baseline=5800,
    R=R, NEW_ENGINES={}, IDENTITY=IDENTITY, ROW_FIXES=ROW_FIXES,
    expect_mapped=28, expect_skipped=0,
))
