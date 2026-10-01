"""Step 8 (step61) - give the 83 blank engine rows a power figure, and unblock the 342 variants
sitting behind them.

Step 7 filled every variant whose engine row already knew the answer. What is left is the harder
half: variants whose engine row is blank too. 85 engine rows carry no `power_hp`; 83 of them have
variants hanging off them.

The dominant pattern, and the reason this is tractable: **most of these rows are truncated
duplicates of rows the database has already filled in.** `N52`, `N63`, `M54`, `S63`, `N20` are
family stems, not engine codes - and the DB holds fully specified `N52B30O1`, `N63B44`,
`M54B25`, `S63B44B`, `N20B20 (328i/28i US)` rows with power, displacement and an application
descriptor. Where the stem's variant names the car (`BMW 550i`, `BMW 328i`, `Ram 2500`), the
right figure is whatever the DB already says for that same car. That is the primary evidence
used here, and it keeps the table internally consistent instead of importing a second opinion.

Three rows were decided by oil data instead, the `[LEMONFILL]` signal from the LEMON campaign:
`ETL` and `ETM` are recorded as 6700cc **petrol** Ram 3500 engines, which does not exist. Their
`engine_service_specs` rows read 11.35 L of 10W-30 - the Cummins 6.7's 12-quart fill and its
10W-30 spec. They are diesels, and are corrected as such. `M57` is likewise a diesel family
stem filed as Petrol.

Usage: python3 step61_step8_engine_power.py [--apply]
"""
import csv
import os
import shutil
import sqlite3
import sys

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step61_2026-10-01.db"
CSV_OUT = "database_enriched/csv_exports/69_engine_power_step61_decisions.csv"
APPLY = "--apply" in sys.argv

M = lambda v: (v["car_model"] or "").upper()
Y = lambda v: v["car_year"] or 0

# --------------------------------------------------------------------------- per-variant rules
# code -> (hp | callable(variant) -> hp, evidence). A callable returning None skips that row.
RULES = {
    # ===== BMW family stems: resolved against the DB's own fully-suffixed rows =====
    "N52": (lambda v: 268 if M(v) in ("530I", "X5") else (258 if M(v) == "X3" else 233),
            "N52 stem. 128i/328i/328xi are the US 230hp SAE cars - DB's N51B30US and "
            "N52B25O1NUS both read 233 for exactly these. 530i and X5 3.0si = DB's N52B30O1 "
            "(X5 30si) 268. X3 = DB's N52B30A 258, whose descriptor covers X3 3.0si"),
    "N51": (233, "N51 stem; the SULEV N52. DB's N51B30US reads 233 for the same 128i/328i/328xi"),
    "N63": (407, "N63 stem. Every variant here is 2008-2013, i.e. pre-N63TU - DB's N63B44 row "
                 "reads 407 and its descriptor names 750i/550i. The 449hp TU arrived for 2014"),
    "N55": (302, "N55 stem; all six cars are X1/X3/X5/X6 xDrive35i - DB's N55B30A reads 302 and "
                 "its descriptor names X5-X6 xDrive35i"),
    "N54": (302, "N54 stem; X6 xDrive35i and Z4 sDrive35i - DB's N54B30O0 (335i) reads 302"),
    "N62": (355, "N62 stem; the 2007-2010 X5 on a 4.8 V8 is the X5 4.8i - DB's N62B48 row is "
                 "literally 'X5 48is 4800 V8', 355"),
    "N20": (240, "N20 stem; 328i/X1 28i/Z4 28i of 2012-13 - DB's 'N20B20 (328i/28i US)' reads 240"),
    "N26": (245, "N26 stem; the SULEV N20 in the 328i - DB's N26B20A reads 245"),
    "M54": (lambda v: 231 if M(v) == "530I" else 189,
            "M54 stem. 530i = DB's M54306S3 231. 325i = DB's M54B25 (325Ci) 189"),
    "M56": (189, "M56 is the SULEV M54B25 fitted to the 325i - DB's M54B25 reads 189"),
    "M57": (265, "M57 stem, and a DIESEL filed as Petrol. The 2009-2012 X5 on an M57 is the US "
                 "X5 xDrive35d, rated 265hp SAE"),
    "S63": (552, "S63 stem; F10 M5 and F12/F13 M6 - DB's S63B44B ('M5 4400 V8') reads 552"),
    "N54B30": (lambda v: 335 if "M SERIES" in M(v) else 302,
               "descriptor says 135i: DB's N54B30O0 (335i/135i) reads 302. The M-Series car is "
               "the 1M - DB's N54B30A reads 335"),
    "N57D30T": (255, "same US 535d and X5 xDrive35d that Step 7 settled at 255 on N57D30A"),
    "N53B25U0": (190, "descriptor '523i 2500 24v' - DB's N53B25A (523i) reads 190"),
    "N53B30": (272, "descriptor 'X1 xDrive28i 3000 24v'; the row's own populated sibling reads 272"),
    "N53B3O0": (268, "descriptor '630i 3000 24v'; the 630i's N52B30 is 272 PS = 268hp, matching "
                     "DB's N53B30O0US (530i) 268"),
    "N52B25": (lambda v: 204 if "5 SERIES" in M(v) else 177,
               "descriptor '323i 2500 24v' - DB's N52NB25A (323i) reads 177; the 5-Series car is "
               "a 523i, DB's N52B25A reads 204"),
    "N51B30": (233, "descriptor '128i 3000 24v' - DB's N51B30US reads 233"),
    "S65B40": (420, "descriptor 'M3 4000 V8' - DB's S65B40A reads 420"),
    "S65B44": (450, "descriptor 'M3 4400 V8', the E92 M3 GTS - DB's S65B44A reads 450"),

    # ===== Ram / FCA sales codes =====
    "ESA": (lambda v: 470 if v["car_brand"] == "Jeep" else 410,
            "6.4 HEMI. In the Ram 2500/3500 HD it is rated 410hp; the Jeep Wrangler Rubicon 392 "
            "(2021+) runs the same block at 470hp"),
    "ESB": (410, "6.4 HEMI in the 2014-2015 Ram HD, 410hp"),
    "6.7 Cummins ISB": (lambda v: 350 if Y(v) <= 2012 else 370,
            "Cummins 6.7 standard output by era: 350hp 2007.5-2012, 370hp from 2013 (68RFE). The "
            "385/400/420hp ratings are Aisin-only high-output options on the 3500, and nothing "
            "in these rows distinguishes the transmission, so the standard rating is used"),
    "ETL": (370, "recorded as a 6700cc PETROL Ram 3500 engine, which does not exist. Its service "
                 "spec is 11.35 L of 10W-30 - the Cummins 6.7's 12-quart fill and viscosity. It "
                 "is the 2019+ Cummins at 370hp standard output"),
    "ETM": (370, "sister code to ETL; same 11.35 L / 10W-30 Cummins service spec"),
    "EZL": (395, "5.7 HEMI eTorque in the 2019+ Ram 1500 DT, 395hp"),
    "ERC": (lambda v: 287 if v["car_brand"] == "Chrysler" else 285,
            "3.6 Pentastar: 287hp in the Pacifica, 285hp in the Wrangler JL"),
    "ERF": (287, "3.6 Pentastar in the 2017 Pacifica, 287hp"),
    "ERG": (285, "3.6 Pentastar in the Wrangler JL, 285hp"),
    "EDE": (180, "2.4 Tigershark MultiAir2 in the Compass MP, 180hp - DB's ED8 descriptor records "
                 "the same 180hp Compass/500X tune"),
    "EDD": (180, "2.4 Tigershark in the 2017 Compass, 180hp"),
    "ECK": (160, "2.0 Tigershark in the 2015 Dart, 160hp"),

    # ===== Honda =====
    "J35Y2": (278, "3.5 V6 i-VTEC in the 2013-2017 Accord, 278hp"),
    "J35Z3": (271, "3.5 V6 in the 2012 Accord, 271hp"),
    "K24W9": (185, "2.4 Earth Dreams in the 2015+ CR-V, 185hp - DB's K24W (Accord/CR-V 2013-17) "
                   "reads 189 for the same family"),
    "K24V1": (185, "2.4 Earth Dreams in the 2015-2016 CR-V, 185hp"),
    "K24V9": (184, "2.4 Earth Dreams in the 2017-2019 CR-V, 184hp"),
    "L15BY": (lambda v: 190 if "CR-V" in M(v) else 174,
              "1.5 VTEC Turbo: 174hp in the Civic, 190hp in the CR-V - DB's L15B7 descriptor "
              "records exactly that 174-190 spread"),
    "L15B1": (130, "1.5 SOHC i-VTEC in the 2016-17 Fit - DB's L15B2 (Fit 2015-20) reads 130"),
    "L15B3": (130, "sister code to L15B1, same Fit 1.5"),
    "LFB1": (212, "Accord Hybrid 2018: 212hp total system output (2.0 Atkinson + e-motor), the "
                  "same system-output convention used for the Toyota hybrids in Step 6"),
    "LFB2": (212, "sister code to LFB1, same Accord Hybrid system"),
    "D17A1": (115, "1.7 SOHC VTEC in the 2001-02 Civic LX/DX, 115hp - DB's D17A6 reads 116"),
    "N22A2": (140, "2.2 i-CTDi Accord; the row's own siblings read 138-140 and DB's N22A1 reads 140"),

    # ===== VW / Audi =====
    "DDSA": (174, "2.0 TSI in the 2019-2020 US Passat, 174hp"),
    "DDSB": (174, "2.0 TSI in the 2019-2021 US Passat, 174hp"),
    "DTDA": (174, "2.0 TSI in the 2021 US Passat, 174hp"),
    "DTEA": (184, "2.0 TSI in the 2021 Tiguan, 184hp"),
    "DSFE": (320, "EA888 evo4 in the Golf R Mk8, 235kW = 320hp (autoparts-24 engine-code index; "
                  "the US rating is quoted as 315hp)"),
    "DSFF": (320, "sister code to DSFE, same Golf R Mk8 EA888 evo4"),
    "CNSA": (170, "1.8 TSI EA888 Gen3 in the US Golf - DB's CXBA/CXBB read 170 for the same car"),
    "CREH": (333, "3.0 TFSI supercharged V6 in the A6/A7, 333hp"),

    # ===== everyone else =====
    "M266E20": (136, "A200/B200 2.0 - DB's M266.960 (A 200) reads 136"),
    "M266E20AL": (193, "A200 Turbo - DB's M266.980 (B 200 TURBO) reads 193"),
    "M266E15": (95, "A150 1.5 - DB's M266.920 (A 150) reads 95"),
    "274": (188, "stub code; the 2023 Sprinter's petrol M274 2.0 turbo is rated 188hp"),
    "276": (302, "stub code; the 2014 E350's M276 3.5 V6 is rated 302hp"),
    "MA1": (394, "991 Carrera S 3.8 - DB's MA1.03 reads 394 for exactly that car"),
    "G4EN": (187, "2.5 Smartstream MPI in the 2023+ Tucson, 187hp"),
    "B4204T12": (245, "S60 T5 2.0 - DB's B4204T11 (T5) reads 245"),
    "B4204T43": (306, "S60 T6 2.0 twincharged - DB's B4204T9 (T6) reads 306"),
    "4M41IT": (170, "3.2 DI-D - DB's 4M41GVIT reads 170 for the same early DI-D"),
    "4D56IT": (115, "2.5 TD - DB's 4D56T reads 115"),
    "4JK1-TC (HI)": (136, "2.5 TD in the MU-X, 136hp"),
    "DT20C": (241, "3.0 HDi V6; the row's own siblings read 241"),
    "MZR": (103, "Mazda2 1.5 MZR - DB's ZY row reads 103 for the same car"),
    "2.5 MZR-CD": (141, "the row's own sibling, the same Mazda 2.5 MZR-CD, reads 141"),
    "2.8 V6": (224, "Signum 2.8 V6 turbo; the row's own Signum siblings read 224"),
    "1.7 CRDi": (115, "Sportage 1.7 CRDi, a single 115hp tune - the row's own sibling reads 115"),
    "1.7 16v CRDI": (141, "Optima 1.7 CRDi, a single 141hp tune"),
}

# --------------------------------------------------------------------------- deliberate skips
SKIP = {
    "BEV (Tesla, model unidentified)":
        "by design - this row is the catch-all for Teslas whose model could not be identified, "
        "and Tesla outputs range from 283hp to 1,020hp. Already a documented NULL-by-design row",
    "2.0 TDCi": "generic descriptor; the 2015 Ford range offered the 2.0 TDCi in six tunes and "
                "the row's own siblings spread 129-161",
    "2.5 TD": "generic descriptor shared by Ford, Mazda, Nissan and Mahindra engines; siblings "
              "spread 109-131",
    "1.9 dCi": "generic descriptor; the Interstar's siblings read 80 and 99",
    "3.0 dCi": "generic descriptor, no year on the variant",
    "2.5 TDI": "generic descriptor on a GWM Hover with no year recorded",
    "1.6 16v CRDI": "the 2010 Cee'd 1.6 CRDi was sold at 90, 115 and 128hp",
    "ESD": "2020 Charger on the supercharged 6.2 (confirmed by its 6.62 L / 0W-40 Hellcat service "
           "spec), but that year offered both the 717hp Hellcat and the 797hp Redeye and nothing "
           "separates ESD from ESJ",
    "ESJ": "sister code to ESD - same 6.2 supercharged service spec, same 717-vs-797 ambiguity",
    "MDK": "2020 911; its 8.28 L / 0W-40 spec confirms a 992 but not whether it is the 385hp "
           "Carrera or the 450hp Carrera S",
    "BEA": "2004-06 Audi TT 1.8T; the 4.54 L / 0W-30 fill is common to the 150, 180 and 225hp "
           "tunes of that engine",
}

# --------------------------------------------------------- engine rows: power + obvious repairs
# code -> power for the engines row itself (defaults to the most common variant value).
ENGINE_ROW_POWER = {"ESA": 410, "6.7 Cummins ISB": 370, "ERC": 285, "N52": 233, "M54": 189,
                    "L15BY": 174}
# code -> (column, value, why) for displacement/fuel repairs spotted while filling power.
ROW_FIXES = [
    ("N54B30", "displacement_cc", 2979, "row said 1200cc for a 3.0 TwinTurbo"),
    ("N53B3O0", "displacement_cc", 2996, "row said 630cc - the model designation leaked into cc"),
    ("N51B30", "displacement_cc", 2996, "row said 1300cc for a 3.0 six"),
    ("N52B25", "displacement_cc", 2497, "row said 1300cc for a 2.5 six"),
    ("M266E20", "displacement_cc", 2034, "row said 1300cc for the 2.0 A200"),
    ("M266E20AL", "displacement_cc", 2034, "row said 1200cc for the 2.0 A200 Turbo"),
    ("M266E15", "displacement_cc", 1498, "row said 1300cc for the 1.5 A150"),
    ("ETL", "displacement_cc", 6690, "6700 -> the Cummins 6.7's actual 6690cc"),
    ("ETM", "displacement_cc", 6690, "6700 -> the Cummins 6.7's actual 6690cc"),
]
# engine rows whose fuel is wrong, with the variants that must move with them.
ENG_FUEL_FIX = {
    "M57": ("Diesel", "the M57 is BMW's 3.0 straight-six turbodiesel; the row and its four X5 "
                      "variants were all filed as Petrol"),
    "ETL": ("Diesel", "11.35 L of 10W-30 is the Cummins 6.7 diesel service spec, not a petrol V8"),
    "ETM": ("Diesel", "same Cummins 6.7 service spec as ETL"),
}


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    todo = con.execute("""
        SELECT v.id, v.car_brand, v.car_model, v.car_year, v.engine_code, v.engine_power_kw, v.fuel
        FROM vehicle_variants v JOIN engines e ON e.engine_code = v.engine_code
        WHERE v.engine_power_hp IS NULL AND e.power_hp IS NULL
        ORDER BY v.engine_code, v.car_brand, v.car_year""").fetchall()
    print(f"candidates (variant power NULL, engine row NULL too): {len(todo)}")
    assert len(todo) == 342, f"baseline changed: expected 342, got {len(todo)}"

    rows, unhandled, filled, skipped = [], set(), 0, 0
    for v in todo:
        code = v["engine_code"]
        if code in SKIP:
            rows.append(dict(variant_id=v["id"], action="SKIP", engine_code=code,
                             brand=v["car_brand"], model=v["car_model"], year=v["car_year"],
                             new_hp=None, new_kw=None, evidence=SKIP[code]))
            skipped += 1
            continue
        if code not in RULES:
            unhandled.add(code)
            continue
        spec, ev = RULES[code]
        hp = spec(v) if callable(spec) else spec
        rows.append(dict(variant_id=v["id"], action="FILL", engine_code=code,
                         brand=v["car_brand"], model=v["car_model"], year=v["car_year"],
                         new_hp=hp, new_kw=round(hp * 0.7355, 1) if v["engine_power_kw"] is None else None,
                         evidence=ev))
        filled += 1
    if unhandled:
        print("UNHANDLED CODES:", sorted(unhandled))
        sys.exit(1)
    print(f"  FILL {filled} | SKIP {skipped} | engine rows to fill: "
          f"{len({r['engine_code'] for r in rows if r['action'] == 'FILL'})}")

    out = CSV_OUT if APPLY else CSV_OUT.replace(".csv", "_DRYRUN.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {out}")

    if not APPLY:
        print("\nDRY RUN - no changes. Re-run with --apply")
        seen = {}
        for r in rows:
            if r["action"] == "FILL":
                seen.setdefault(r["engine_code"], set()).add(r["new_hp"])
        for c in sorted(seen):
            print(f"   {c:26} -> {sorted(seen[c])}")
        return

    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    shutil.copy2(DB, BACKUP)
    print(f"\nbackup -> {BACKUP}")

    n_hp = n_kw = 0
    for r in rows:
        if r["new_hp"] is None:
            continue
        con.execute("UPDATE vehicle_variants SET engine_power_hp=? WHERE id=?", (r["new_hp"], r["variant_id"]))
        n_hp += 1
        if r["new_kw"] is not None:
            con.execute("UPDATE vehicle_variants SET engine_power_kw=? WHERE id=?", (r["new_kw"], r["variant_id"]))
            n_kw += 1
    print(f"  variants: hp set on {n_hp}, kW on {n_kw}")

    # engine rows: power = explicit override, else the single value used for its variants
    by_code = {}
    for r in rows:
        if r["action"] == "FILL":
            by_code.setdefault(r["engine_code"], []).append(r["new_hp"])
    n_eng = 0
    for code, vals in by_code.items():
        hp = ENGINE_ROW_POWER.get(code, max(set(vals), key=vals.count))
        con.execute("UPDATE engines SET power_hp=?, power_kw=? WHERE engine_code=?",
                    (hp, round(hp * 0.7355, 1), code))
        n_eng += 1
    print(f"  engine rows: power set on {n_eng}")

    for code, col, val, why in ROW_FIXES:
        con.execute(f"UPDATE engines SET {col}=? WHERE engine_code=?", (val, code))
        print(f"  row fix {code}.{col} = {val} ({why})")
    for code, (fuel, why) in ENG_FUEL_FIX.items():
        con.execute("UPDATE engines SET fuel=? WHERE engine_code=?", (fuel, code))
        n = con.execute("UPDATE vehicle_variants SET fuel=? WHERE engine_code=?", (fuel, code)).rowcount
        print(f"  fuel fix {code} -> {fuel} (+{n} variants): {why}")
    con.commit()

    g = lambda q: con.execute(q).fetchone()[0]
    print("\n--- verify ---")
    print("NULL-power variants remaining:", g("SELECT count(*) FROM vehicle_variants WHERE engine_power_hp IS NULL"))
    print("  documented skips:", g("""SELECT count(*) FROM vehicle_variants v JOIN engines e
        ON e.engine_code=v.engine_code WHERE v.engine_power_hp IS NULL AND e.power_hp IS NULL"""))
    print("  no engine_code:", g("SELECT count(*) FROM vehicle_variants WHERE engine_power_hp IS NULL AND engine_code IS NULL"))
    print("  engine row has power (step7 skips):", g("""SELECT count(*) FROM vehicle_variants v JOIN engines e
        ON e.engine_code=v.engine_code WHERE v.engine_power_hp IS NULL AND e.power_hp IS NOT NULL"""))
    print("engine rows with NULL power:", g("SELECT count(*) FROM engines WHERE power_hp IS NULL"))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("engines:", g("SELECT count(*) FROM engines"), "| variants:", g("SELECT count(*) FROM vehicle_variants"))
    con.close()


if __name__ == "__main__":
    main()
