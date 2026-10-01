"""Step 14b (step67b) - cylinder counts that contradict their own valve count.

Step 14's verification asked a narrow question ("are there still '10v' rows stored as six
cylinders?") and got 14 hits, which meant the trick generalised. A valve count constrains the
cylinder count, because engines have 2, 3, 4 or 5 valves per cylinder and nothing else:
a 20-valve engine is a 5-cylinder (4 valves) or a 4-cylinder (5 valves), never a six.

Sweeping every descriptor for a valve token and testing it against the stored cylinder count
found **129 impossible rows** covering 561 variants - all from our own data, no external source.

Two refinements were needed first, both learned from false positives:
  * **"48V" in "2.0 I4 Turbo MHEV 48V" is a battery voltage, not a valve count.** Mild-hybrid
    descriptors are excluded.
  * **5 valves per cylinder is real.** The VW/Audi 1.8 20v is a *four* (4x5) and the Audi 4.2 V8
    40v is an *eight* (8x5). Treating 20v as "must be five cylinders" wrongly flagged them.

A contradiction alone does not say which of the two numbers is wrong, so a fix is applied only
when a **second independent signal** agrees - the engine code's own family prefix:

  * `B5xxx` / `D5xxx`  Volvo: the 5 denotes five cylinders (B5244S, D5244T)
  * `M5x` / `N5x`      BMW: the M52/M54/N51/N52/N53 families are straight-sixes
  * `4Mxx` / `4Gxx`    Mitsubishi: the leading 4 denotes four cylinders (4M41)
  * `10v` anything - 5 cylinders by elimination (13 VW 2.5 TDI + the Fiat/Alfa 2.4 JTD)
  * VW/Audi 2.5 20v and Fiat/Alfa 2.4 JTD 20v - both five-cylinder engines, confirmed by
    displacement (2,400-2,521 cc at ~480-500 cc per cylinder)

Everything else is exported for review rather than guessed - including `B10D1`, where the stored
3 cylinders are right and the descriptor's "16v" is the wrong half.

Usage: python3 step67b_valve_count_cylinders.py [--apply]
"""
import csv
import os
import re
import shutil
import sqlite3
import sys

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step67b_2026-10-01.db"
CSV_OUT = "database_enriched/csv_exports/81_valve_cylinder_fixes_step67b.csv"
APPLY = "--apply" in sys.argv

VOLTAGE = re.compile(r"MHEV|mild|hybrid|EQ Boost|BSG|ISG", re.I)
VALVE = re.compile(r"(?<![0-9.])(\d{2})\s?v\b", re.I)


def possible(v):
    """cylinder counts compatible with a valve total, at 2-5 valves per cylinder"""
    return {v // k for k in (2, 3, 4, 5) if v % k == 0}


def rule(code, cc, brand, valves, ours):
    c, b = (code or "").upper(), (brand or "").lower()
    if valves == 10:
        # 10 valves is 5 cylinders by elimination: the only other arithmetic option is a
        # two-cylinder with five valves each, which no manufacturer has ever built.
        return 5, "10 valves can only be 5 cylinders x 2; a 2-cylinder 5-valve engine does not exist"
    if re.match(r"^[BD]5\d{3}", c) and valves == 20:
        return 5, "Volvo B5/D5 code prefix denotes five cylinders; 20v = 5 x 4"
    if re.match(r"^[MN]5[1-4]", c) and valves == 24:
        return 6, "BMW M5x/N5x is a straight-six; 24v = 6 x 4"
    if re.match(r"^4[MG]\d", c) and valves == 16:
        return 4, "Mitsubishi 4M/4G code prefix denotes four cylinders; 16v = 4 x 4"
    if valves == 20 and cc and 2435 <= cc <= 2525 and any(
            b.startswith(x) for x in ("volkswagen", "audi", "seat", "skoda", "vw")):
        return 5, "VW/Audi 2.5 is the inline-five; 20v = 5 x 4 and 2.5 L / 5 = ~500 cc per cylinder"
    if valves == 20 and cc and 2380 <= cc <= 2400 and any(
            b.startswith(x) for x in ("fiat", "alfa", "lancia")):
        return 5, "Fiat/Alfa 2.4 JTD is the inline-five; 20v = 5 x 4"
    return None, None


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    fixes, review = [], []

    for e in con.execute("""SELECT engine_code, engine_type, cylinders, displacement_cc,
                                   brand_example, count_variants
                            FROM engines WHERE engine_type IS NOT NULL AND cylinders IS NOT NULL"""):
        t = e["engine_type"]
        if VOLTAGE.search(t):
            continue
        mt = VALVE.search(t)
        if not mt:
            continue
        v = int(mt.group(1))
        ok = possible(v)
        if e["cylinders"] in ok:
            continue
        new, why = rule(e["engine_code"], e["displacement_cc"], e["brand_example"], v, e["cylinders"])
        row = dict(engine_code=e["engine_code"], brand=e["brand_example"], descriptor=t,
                   valves=v, old_cylinders=e["cylinders"], possible=" or ".join(map(str, sorted(ok))),
                   displacement_cc=e["displacement_cc"], variants=e["count_variants"])
        if new and new in ok:
            row.update(action="FIX", new_cylinders=new, evidence=why)
            fixes.append(row)
        else:
            row.update(action="REVIEW", new_cylinders="",
                       evidence="valve count and cylinders disagree, but no second signal says which is wrong")
            review.append(row)

    print(f"impossible rows: {len(fixes) + len(review)}   fixing {len(fixes)} "
          f"({sum(r['variants'] for r in fixes)} variants), {len(review)} to review")
    seen = {}
    for r in fixes:
        seen.setdefault(r["evidence"].split(";")[0], []).append(r)
    for k, v in seen.items():
        print(f"\n   {k}  ({len(v)} rows)")
        for r in v[:4]:
            print(f"      {str(r['engine_code'])[:16]:17} {r['old_cylinders']} -> {r['new_cylinders']}"
                  f"   {str(r['descriptor'])[:30]:32} n={r['variants']}")

    os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
    out = CSV_OUT if APPLY else CSV_OUT.replace(".csv", "_DRYRUN.csv")
    allrows = fixes + review
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(allrows[0].keys()))
        w.writeheader(); w.writerows(allrows)
    print(f"\n  wrote {out}")

    if not APPLY:
        print("DRY RUN - no changes. Re-run with --apply")
        return

    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    shutil.copy2(DB, BACKUP)
    print(f"backup -> {BACKUP}")
    for r in fixes:
        con.execute("UPDATE engines SET cylinders=? WHERE engine_code=?",
                    (r["new_cylinders"], r["engine_code"]))
    con.commit()
    print(f"  applied {len(fixes)} cylinder corrections")

    g = lambda q: con.execute(q).fetchone()[0]
    print("\n--- verify ---")
    left = 0
    for e in con.execute("SELECT engine_type, cylinders FROM engines WHERE engine_type IS NOT NULL AND cylinders IS NOT NULL"):
        if VOLTAGE.search(e["engine_type"]):
            continue
        mt = VALVE.search(e["engine_type"])
        if mt and e["cylinders"] not in possible(int(mt.group(1))):
            left += 1
    print("rows still contradicting their own valve count:", left, "(all exported for review)")
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("engines:", g("SELECT count(*) FROM engines"), "| variants:", g("SELECT count(*) FROM vehicle_variants"))
    con.close()


if __name__ == "__main__":
    main()
