"""Step 11 (step64) - complete cylinders and displacement on the engines table, and repair the
rows where a model designation had leaked into the displacement column.

Three separate problems were hiding behind "104 NULL cylinders / 73 NULL displacement":

1. **Not actually missing (36 + 49 rows).** Electric and hydrogen rows - Leaf, i3, Bolt, Tesla,
   Mirai, the Ultium Hummer - have no cylinders and no displacement because an electric motor
   does not have them. NULL is the correct value. They are left alone and documented, exactly
   as the 147 zero-variant engine rows were in Step 10.

2. **Genuinely missing (68 cylinders + 24 displacements).** Overwhelmingly the same family
   stems and sales codes Step 8 gave a power figure to (`N52`, `M54`, `ESA`, `K24W9`, `DSFE`).
   Where the row's own `engine_type` names the layout ("6.2 V8 Supercharged", "4.0 H6 NA") the
   text decides; otherwise the figure comes from the engine family, as in Step 8.

3. **Present but wrong - a systematic bug.** Step 8 found `N53B3O0` recorded as **630cc**
   because the model designation 630i had leaked into the displacement column. It is not an
   isolated typo: 13 more rows have the same defect - `650i` -> 650cc, `740i` -> 740cc,
   `735i` -> 735cc, `725tds` -> 725cc, `CL600` -> 600cc. Every one of them states its real
   displacement in the same string ("650i 4800 V8"), so they repair themselves. Their cylinder
   counts were wrong too, having been derived from the bogus displacement (a 3.0 diesel six
   recorded as a 3-cylinder).

A fourth, smaller sweep rides along: 17 rows whose stored cylinder count contradicts an explicit
layout token in their own descriptor (`EZ36D` "3.6 H6" stored as 8 cylinders, `N74B66A` "6.6
V12" stored as 8). 16 are corrected; `D4FD-L` is excluded because there the *descriptor* is the
wrong half - it reads "3.0 -24 V6" on a 1685cc Hyundai 1.7 diesel, so it belongs to the
descriptor cleanup, not here.

Usage: python3 step64_step11_engine_attributes.py [--apply]
"""
import csv
import os
import re
import shutil
import sqlite3
import sys

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step64_2026-10-01.db"
CSV_OUT = "database_enriched/csv_exports/72_engine_attributes_step64.csv"
APPLY = "--apply" in sys.argv

EV_PAT = re.compile(r"electric|e-motor|fuel cell|battery|ultium|traction|fcev|hydrogen|drive unit", re.I)

# --------------------------------------------------------------------- cylinders for 68 rows
# Grouped by how the answer was reached.
CYL = {}
# (a) the row's own descriptor names the layout
for code, n in {"LT4": 8, "LS4": 8, "L26": 6, "J35Y1": 6, "LGW": 6, "MDW": 6, "MDJ": 4,
                "LZE": 6, "LE2": 4, "L15B7": 4, "DBPA": 4, "DHHA": 4, "DLRA": 4,
                "CXBA": 4, "CXBB": 4}.items():
    CYL[code] = (n, "layout stated in the row's own engine_type descriptor")
# (b) BMW family stems - same reasoning as Step 8
for code, n in {"N52": 6, "N51": 6, "N55": 6, "N54": 6, "N63": 8, "N62": 8, "N20": 4, "N26": 4,
                "M54": 6, "M56": 6, "M57": 6, "S63": 8}.items():
    CYL[code] = (n, "BMW family stem; the family's layout is fixed (N2x/N5x/M5x sixes and fours, "
                    "N6x/S63 V8s)")
# (c) FCA sales codes
for code, n in {"ESA": 8, "ESB": 8, "ESD": 8, "ESJ": 8, "EZL": 8, "ERC": 6, "ERF": 6, "ERG": 6,
                "EDE": 4, "EDD": 4, "ECK": 4}.items():
    CYL[code] = (n, "FCA sales code: ES*/EZ* are HEMI V8s, ER* the 3.6 Pentastar V6, ED*/EC* the "
                    "Tigershark fours")
CYL["ETL"] = CYL["ETM"] = (6, "Cummins 6.7 is a straight-six (see Step 8: their 11.35 L / 10W-30 "
                              "service spec identified them as Cummins diesels)")
# (d) Honda / VW / other codes, by engine family
for code, n in {"J35Y2": 6, "J35Z3": 6, "K24W9": 4, "K24V9": 4, "K24V1": 4, "L15BY": 4,
                "L15B1": 4, "L15B3": 4, "D17A1": 4, "LFB1": 4, "LFB2": 4}.items():
    CYL[code] = (n, "Honda family: J35 = 3.5 V6, K24 = 2.4 four, L15/LFB = 1.5-2.0 four")
for code, n in {"DDSA": 4, "DDSB": 4, "DTDA": 4, "DTEA": 4, "DSFE": 4, "DSFF": 4, "CNSA": 4,
                "BEA": 4, "CREH": 6}.items():
    CYL[code] = (n, "VW/Audi: EA888 2.0 and 1.8 TSI are fours; CREH is the 3.0 TFSI V6")
for code, n in {"B4204T12": 4, "B4204T43": 4, "G4EN": 4, "MZR": 4, "MA1": 6, "MDK": 6,
                "274": 4, "276": 6}.items():
    CYL[code] = (n, "B420 = Volvo's 2.0 four; G4EN/MZR fours; MA1/MDK are Porsche flat-sixes; "
                    "Mercedes M274 is a four and M276 a V6")

# --------------------------------------------------------------- displacement for 24 rows (cc)
DISP = {
    "N52": (2996, "BMW N52 is the 3.0 six"), "N51": (2996, "N51 is the SULEV N52 3.0"),
    "N55": (2979, "N55 3.0 TwinPower Turbo"),
    "M54": (2494, "stem; its model_example is the 325i, the 2.5 M54B25 - the same car Step 8 "
                  "used to set its 189hp"),
    "M56": (2497, "M56 is the SULEV M54B25 2.5"),
    "K24W9": (2356, "Honda K24 Earth Dreams 2.4"), "K24V1": (2356, "Honda K24 Earth Dreams 2.4"),
    "L15B1": (1498, "Honda L15B 1.5"), "L15B3": (1498, "Honda L15B 1.5"),
    "D17A1": (1668, "Honda D17 1.7 - DB's D17A2/D17A6 rows both read 1668"),
    "ERC": (3604, "3.6 Pentastar - DB's ERB row reads 3604"),
    "ERF": (3604, "3.6 Pentastar"), "EDE": (2360, "2.4 Tigershark - DB's ED8 row reads 2360"),
    "DDSA": (1984, "EA888 2.0 TSI"), "DDSB": (1984, "EA888 2.0 TSI"),
    "DTDA": (1984, "EA888 2.0 TSI"), "DTEA": (1984, "EA888 2.0 TSI"),
    "DSFE": (1984, "EA888 evo4 2.0, 1984cc per the engine-code index used in Step 8"),
    "DSFF": (1984, "EA888 evo4 2.0"),
    "B4204T43": (1969, "Volvo VEP4 2.0 - DB's other B4204T rows read 1969"),
    "CREH": (2995, "Audi 3.0 TFSI"), "MDK": (2981, "Porsche 992 3.0 flat-six"),
    "274": (1991, "Mercedes M274 2.0"), "276": (3498, "Mercedes M276 3.5 V6"),
}

# ------------------------------------------------ the leaked-designation repairs (cc, cylinders)
LEAKED = {
    "M275KE55LA": (5513, 12, "'CL600 5500 V8 TwinTurbo': 600 is the CL600 badge, not a "
                             "displacement. The M275 is a 5.5 V12 biturbo - the descriptor's "
                             "'V8' is wrong too"),
    "N62B48TU": (4799, 8, "'650i 4800 V8' - the 650i badge became 650cc"),
    "N62B36": (3600, 8, "'735i 3600 V8' - the 735i badge became 735cc"),
    "N62B40": (3999, 8, "'740i 4000 V8' - the 740i badge became 740cc"),
    "N62NB40": (3999, 8, "'740Li 4000 V8' - the 740Li badge became 740cc"),
    "M62TUB35": (3498, 8, "'735i 3500 V8' - badge became displacement"),
    "M62TUB44": (4398, 8, "'740i 4400 V8' - badge became displacement"),
    "M57D30A": (2993, 6, "'730d 3000 D' became 730cc, and the cylinder count was then derived "
                         "from it: a 3.0 straight-six diesel recorded as a 3-cylinder"),
    "M57TU2D30TOP": (2993, 6, "'635d 3000 D' became 635cc, cylinders derived as 3"),
    "M67D39": (3901, 8, "'740d 3900 D' became 740cc; the M67 is a V8 diesel, not a triple"),
    "M67TUD39": (3901, 8, "'740d 3900 D' became 740cc; M67 V8 diesel"),
    "M67D44": (4423, 8, "'745d 4400 D' became 745cc; M67 V8 diesel"),
    "M51D25S": (2497, 6, "'725tds 2500 D' became 725cc; the M51 is a 2.5 straight-six diesel"),
    "N53B3O0": (None, 6, "displacement already repaired in Step 8 (630i badge -> 630cc); its "
                         "cylinder count was still the 3 derived from the bogus 630cc"),
    "CSCA": (1582, 4, "829cc recorded for a row whose own descriptor says '1.6 CRDi'; the U2 "
                      "1.6 CRDi is 1582cc"),
}

# ---------------------------------- cylinder counts contradicted by an explicit token in the text
TOKEN_FIX = {"EZ36D": 6, "BGP": 5, "ETJ": 6, "N74B66A": 12, "OM612DE27LA": 5, "EGS": 6,
             "B3815KT0": 3, "N74B60A": 12, "CTNA": 12, "ETC": 6, "406PN": 6, "20K4F": 6,
             "1LR-GUE": 10, "VQ20DE": 6, "AM702": 12, "CFRA": 12}
TOKEN_SKIP = {"D4FD-L": "its descriptor ('3.0 -24 V6') belongs to a different engine than its "
                        "1685cc Hyundai 1.7 diesel body - the text is the wrong half, so this "
                        "belongs to the descriptor cleanup, not here"}


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    g = lambda q: con.execute(q).fetchone()[0]

    null_cyl = con.execute("SELECT engine_code, engine_type, fuel FROM engines WHERE cylinders IS NULL").fetchall()
    null_disp = con.execute("SELECT engine_code, engine_type, fuel FROM engines WHERE displacement_cc IS NULL").fetchall()
    is_ev = lambda r: bool(r["engine_type"] and EV_PAT.search(r["engine_type"])) or r["fuel"] == "Electric"
    ev_cyl = [r["engine_code"] for r in null_cyl if is_ev(r)]
    ev_disp = [r["engine_code"] for r in null_disp if is_ev(r)]
    need_cyl = [r["engine_code"] for r in null_cyl if not is_ev(r)]
    need_disp = [r["engine_code"] for r in null_disp if not is_ev(r)]
    print(f"NULL cylinders {len(null_cyl)} = {len(ev_cyl)} electric/FCEV (correct) + {len(need_cyl)} to fill")
    print(f"NULL displacement {len(null_disp)} = {len(ev_disp)} electric/FCEV (correct) + {len(need_disp)} to fill")

    missing = [c for c in need_cyl if c not in CYL] + [c for c in need_disp if c not in DISP]
    if missing:
        print("UNHANDLED:", sorted(set(missing)))
        sys.exit(1)

    rows = []
    for c in need_cyl:
        rows.append(dict(engine_code=c, action="FILL_CYL", column="cylinders", old=None,
                         new=CYL[c][0], evidence=CYL[c][1]))
    for c in need_disp:
        rows.append(dict(engine_code=c, action="FILL_DISP", column="displacement_cc", old=None,
                         new=DISP[c][0], evidence=DISP[c][1]))
    for code, (cc, cyl, why) in LEAKED.items():
        cur = con.execute("SELECT displacement_cc, cylinders FROM engines WHERE engine_code=?", (code,)).fetchone()
        if cc is not None and cur["displacement_cc"] != cc:
            rows.append(dict(engine_code=code, action="REPAIR_DISP", column="displacement_cc",
                             old=cur["displacement_cc"], new=cc, evidence=why))
        if cur["cylinders"] != cyl:
            rows.append(dict(engine_code=code, action="REPAIR_CYL", column="cylinders",
                             old=cur["cylinders"], new=cyl, evidence=why))
    for code, cyl in TOKEN_FIX.items():
        cur = g(f"SELECT cylinders FROM engines WHERE engine_code='{code}'")
        rows.append(dict(engine_code=code, action="TOKEN_CYL", column="cylinders", old=cur, new=cyl,
                         evidence="stored count contradicts the explicit layout token in the row's own descriptor"))
    for code, why in TOKEN_SKIP.items():
        rows.append(dict(engine_code=code, action="SKIP", column="cylinders", old=None, new=None, evidence=why))

    from collections import Counter
    print("  " + " | ".join(f"{k} {v}" for k, v in Counter(r["action"] for r in rows).items()))
    out = CSV_OUT if APPLY else CSV_OUT.replace(".csv", "_DRYRUN.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {out}")

    if not APPLY:
        print("\nDRY RUN - no changes. Re-run with --apply")
        for r in rows:
            if r["action"].startswith(("REPAIR", "TOKEN")):
                print(f"   {r['action']:11} {r['engine_code'][:20]:22} {r['column']:16} {r['old']} -> {r['new']}")
        return

    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    shutil.copy2(DB, BACKUP)
    print(f"\nbackup -> {BACKUP}")
    n = 0
    for r in rows:
        if r["new"] is None:
            continue
        con.execute(f"UPDATE engines SET {r['column']}=? WHERE engine_code=?", (r["new"], r["engine_code"]))
        n += 1
    # the M275 descriptor says V8 on a V12; correct it while we are here
    con.execute("""UPDATE engines SET engine_type='CL600 5.5 V12 TwinTurbo (M275)'
                   WHERE engine_code='M275KE55LA'""")
    con.commit()
    print(f"  applied {n} column updates (+1 descriptor correction on M275KE55LA)")

    print("\n--- verify ---")
    print("NULL cylinders:", g("SELECT count(*) FROM engines WHERE cylinders IS NULL"),
          "(all electric/FCEV by design)")
    print("NULL displacement:", g("SELECT count(*) FROM engines WHERE displacement_cc IS NULL"),
          "(all electric/FCEV by design)")
    print("non-EV rows still missing cylinders:", g("""SELECT count(*) FROM engines WHERE cylinders IS NULL
        AND fuel<>'Electric' AND (engine_type IS NULL OR engine_type NOT LIKE '%lectric%')"""))
    print("displacement < 1000cc with a 4-digit cc in its own text:", g("""SELECT count(*) FROM engines
        WHERE displacement_cc<1000 AND engine_type GLOB '*[1-9][0-9][0-9][0-9]*'"""))
    print("cylinders contradicting an explicit layout token:", g("""SELECT count(*) FROM engines
        WHERE (engine_type LIKE '%V12%' AND cylinders<>12) OR (engine_type LIKE '%V8%' AND cylinders<>8)
           OR (engine_type LIKE '%H6%' AND cylinders<>6) OR (engine_type LIKE '%I6%' AND cylinders<>6)
           OR (engine_type LIKE '%I5%' AND cylinders<>5) OR (engine_type LIKE '%I3%' AND cylinders<>3)"""),
          "(expected 1: D4FD-L, documented)")
    print("implausible cyl/cc combos:", g("""SELECT count(*) FROM engines WHERE displacement_cc>0 AND cylinders>0
        AND ((cylinders>=6 AND displacement_cc<1600) OR (cylinders<=3 AND displacement_cc>2500))"""))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("engines:", g("SELECT count(*) FROM engines"), "| variants:", g("SELECT count(*) FROM vehicle_variants"))
    con.close()


if __name__ == "__main__":
    main()
