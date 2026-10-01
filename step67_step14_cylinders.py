"""Step 14 (step67) - correct cylinder counts using the MagicMotorsport layout tokens.

Steps 11 and 12 both kept running into wrong cylinder counts but had no independent source to
adjudicate them. The MagicMotorsport descriptions supply one: 413 engine codes state a layout
explicitly ("3.6L Pentastar V6", "2.5L R5 TDI", "4.2L V8 TDI"). Comparing those against our
`cylinders` column produced **28 contradictions**, plus 5 of the 32 rows on the Step-12 suspect
worklist (`csv_exports/74_suspect_cylinders_worklist.csv`).

Every row below was adjudicated individually - the source is treated as evidence, not as an
oracle, because on two rows it is demonstrably wrong.

**The strongest single piece of evidence came from our own data.** The fifteen VW 2.5 TDI rows
carry the descriptor "2.5 10v TDI" while storing 6 cylinders. A 10-valve six does not exist:
10 valves at 2 per cylinder is a **five**-cylinder engine, which is exactly what VW's 2.5 R5 TDI
is, and exactly what the source says ("2.5L R5 TDI"). Our own descriptor contradicted our own
cylinder count, and nobody had noticed.

Rejected the source on:
  * `EDZ`  - source says "2.4L V6". Chrysler's EDZ is the 2.4 DOHC **inline-four** (Neon, Stratus,
             PT Cruiser); a 2.4 V6 never existed. Our own descriptor says "2.4 I4 DOHC 16v EDZ".
  * `G6DC`, `LFY`, `CYRB` - not a cylinder error at all but an identity mismatch: the source's
             engine for that code is a different engine from ours (source `G6DC` = 3.5 V6,
             ours = a 1,997 cc 2.0 TDCi). Changing the cylinder count would paper over the real
             problem, so they are exported for review instead.

Usage: python3 step67_step14_cylinders.py [--apply]
"""
import csv
import os
import shutil
import sqlite3
import sys

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step67_2026-10-01.db"
CSV_OUT = "database_enriched/csv_exports/80_cylinder_fixes_step67.csv"
APPLY = "--apply" in sys.argv

VW_R5 = "VW 2.5 R5 TDI: source says 'R5'; our own descriptor says '10v', and 10 valves at 2 per cylinder is a five"

# engine_code -> (new_cylinders, new_displacement_cc or None, evidence)
FIXES = {
    # --- VW/Audi 2.5 TDI inline-five, stored as six -------------------------
    "AXD": (5, None, VW_R5), "AXE": (5, None, VW_R5), "BNZ": (5, None, VW_R5),
    "BPC": (5, None, VW_R5), "CECA": (5, None, VW_R5), "CECB": (5, None, VW_R5),
    "CEBA": (5, None, VW_R5), "BBE": (5, None, VW_R5), "BBF": (5, None, VW_R5),
    "AVR": (5, None, VW_R5), "AJT": (5, None, VW_R5), "ANJ": (5, None, VW_R5),
    "APA": (5, None, VW_R5), "ACV": (5, None, VW_R5), "AUF": (5, None, VW_R5),
    # --- Mercedes OM642 3.0 V6 CDI, stored as four (displacement also corrupt)
    "OM642DE30LA": (6, 2987, "Mercedes OM642 is the 3.0 V6 CDI; source '3.0L ... CDI'. Stored cc 2873 is the leaked-designation bug from Step 11"),
    "OM642DE30LAR": (6, 2987, "Mercedes OM642 3.0 V6 CDI; stored cc 2444 is corrupt"),
    "OM642LSDE30LA": (6, 2987, "Mercedes OM642 3.0 V6 CDI; stored cc 3393 is corrupt"),
    # --- the rest, each corroborated by an explicit source layout token ------
    "ERB": (6, None, "source '3.6L Pentastar V6'; the Pentastar is a V6, stored as 8"),
    "MCT.LA": (6, None, "source '3.6L V6 Turbo'; VW-group 3.6 VR6, stored as 8"),
    "MCX.ZA": (6, None, "source '3.6L V6'; VW-group 3.6 VR6, stored as 8"),
    "N55B30": (6, 2979, "BMW N55 is the 3.0 straight-six; stored as 4 with a corrupt 2265 cc"),
    "M178.980": (8, None, "source '4.0L V8 AMG GT-R'; M178 is the AMG 4.0 V8 biturbo, stored as 6"),
    "N73B68A": (12, None, "source '6.8L V12'; BMW N73B68 is the 6,749 cc V12 (Phantom), stored as 8"),
    "CCFA": (8, None, "source '4.2L V8 TDI'; the Audi 4.2 TDI is a V8 - our own descriptor wrongly said V6"),
    # --- from the Step-12 suspect worklist -----------------------------------
    "1AR-FE": (4, None, "Toyota 1AR-FE is the 2.7 inline-four (Camry/RAV4); source '2.7L VVTi', 2671 cc, stored as 6"),
    "B5254T12": (5, None, "Volvo B5254 is the 2.5 inline-five; source '2.5L T5', stored as 6"),
    "B5254T4": (5, None, "Volvo B5254 is the 2.5 inline-five; source '2.5L R AWD', stored as 6"),
    "4G69S4N": (4, None, "Mitsubishi 4G69 is the 2.4 inline-four - the '4G6' family prefix means four, and source says '16V' (4 valves x 4), stored as 6"),
}

# descriptor repairs that ride along with a cylinder fix
DESC = {"CCFA": ("4.2 V6 TDI", "4.2 V8 TDI")}

# source disagrees but we are keeping our value - exported, not applied
REJECTED = {
    "EDZ": "source says '2.4L V6'; Chrysler EDZ is the 2.4 DOHC inline-four and our descriptor says 'I4'. Source is wrong.",
    "G6DC": "identity mismatch, not a cylinder error: source G6DC is a 3.5 V6, ours is a 1,997 cc 2.0 TDCi",
    "LFY": "identity mismatch: source LFY is a 3.6 V6, ours is an 1,800 cc 1.8 16v",
    "CYRB": "identity mismatch: source CYRB is a 2.0 TFSI petrol, ours is a 2,198 cc diesel",
}


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = []

    for code, (cyl, cc, why) in FIXES.items():
        e = con.execute("""SELECT engine_code, cylinders, displacement_cc, engine_type, count_variants
                           FROM engines WHERE engine_code=?""", (code,)).fetchone()
        if e is None:
            print(f"  !! {code} not found - skipped")
            continue
        if e["cylinders"] == cyl and (cc is None or e["displacement_cc"] == cc):
            continue
        rows.append(dict(engine_code=code, action="FIX", variants=e["count_variants"],
                         old_cylinders=e["cylinders"], new_cylinders=cyl,
                         old_cc=e["displacement_cc"], new_cc=cc if cc else e["displacement_cc"],
                         evidence=why))
    for code, why in REJECTED.items():
        e = con.execute("SELECT cylinders, displacement_cc, count_variants FROM engines WHERE engine_code=?",
                        (code,)).fetchone()
        if e:
            rows.append(dict(engine_code=code, action="KEEP_OURS", variants=e["count_variants"],
                             old_cylinders=e["cylinders"], new_cylinders=e["cylinders"],
                             old_cc=e["displacement_cc"], new_cc=e["displacement_cc"], evidence=why))

    fixes = [r for r in rows if r["action"] == "FIX"]
    print(f"cylinder/displacement fixes: {len(fixes)}  (variants riding on them: {sum(r['variants'] for r in fixes)})")
    print(f"source rejected, ours kept : {len(rows) - len(fixes)}")
    for r in fixes:
        cc = "" if r["old_cc"] == r["new_cc"] else f"  cc {r['old_cc']} -> {r['new_cc']}"
        print(f"   {r['engine_code'][:16]:17} cyl {r['old_cylinders']} -> {r['new_cylinders']}{cc}   (n={r['variants']})")

    os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
    out = CSV_OUT if APPLY else CSV_OUT.replace(".csv", "_DRYRUN.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"  wrote {out}")

    if not APPLY:
        print("\nDRY RUN - no changes. Re-run with --apply")
        return

    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    shutil.copy2(DB, BACKUP)
    print(f"\nbackup -> {BACKUP}")
    for r in fixes:
        con.execute("UPDATE engines SET cylinders=?, displacement_cc=? WHERE engine_code=?",
                    (r["new_cylinders"], r["new_cc"], r["engine_code"]))
    for code, (old, new) in DESC.items():
        con.execute("UPDATE engines SET engine_type=? WHERE engine_code=? AND engine_type=?",
                    (new, code, old))
        con.execute("UPDATE vehicle_variants SET engine_type=? WHERE engine_code=? AND engine_type=?",
                    (new, code, old))
    con.commit()
    print(f"  applied {len(fixes)} engine rows")

    g = lambda q: con.execute(q).fetchone()[0]
    print("\n--- verify ---")
    print("rows still contradicting a '10v' descriptor with 6 cylinders:",
          g("SELECT count(*) FROM engines WHERE engine_type LIKE '%10v%' AND cylinders=6"))
    print("implausible cc per cylinder (<250 or >1300, excl. known big diesels):",
          g("""SELECT count(*) FROM engines WHERE cylinders IS NOT NULL AND displacement_cc IS NOT NULL
               AND displacement_cc>400 AND (displacement_cc*1.0/cylinders<250 OR displacement_cc*1.0/cylinders>1300)"""))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("engines:", g("SELECT count(*) FROM engines"), "| variants:", g("SELECT count(*) FROM vehicle_variants"))
    con.close()


if __name__ == "__main__":
    main()
