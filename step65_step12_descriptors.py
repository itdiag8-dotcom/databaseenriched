"""Step 12 (step65) - clean the engine_type descriptor column.

Two problems, deliberately solved differently.

**A. The `(est.)` / `(corr.)` markers (540 engine rows, 506 variants).**
These are provenance notes living inside a human-readable description. The database already has
a column for provenance - `data_confidence` - and the two disagree constantly: 281 rows marked
"(corr.)" are `TRUSTED_AFTERMARKET`, 88 marked "(est.)" are `TRUSTED_AFTERMARKET`, and 4
"(corr.)" rows are `OEM_VERIFIED`. A marker that contradicts the provenance column is worse than
no marker. They are stripped from the text; `data_confidence` is left untouched and remains the
single source of truth for how reliable a row is.

**B. 254 descriptors that say nothing about the engine.**
These came in from the aftermarket catalogue and are a mix of other cars' model names
("GAZELLE" on a Mercedes M157 5.5 V8, "HHR" on an M156, "NEDCAR", "MATERIA (M4_)"), bare trim
letters ("T5", "M", "Cooper S"), stray numbers ("3 (est.)") and literal workshop operations
("Make centre right seat functional", "Repair seating frame", "without tensioner pulley damper",
"Radiator grille touch-up paint (stage 3)"). None of them describes an engine.

They are replaced with a descriptor built from the row's own verified numbers, in the form
**"5.5 L Petrol"**. The original text is preserved in the decision CSV.

**Why no cylinder count in the rebuilt text.** The obvious format is "5.5 V8 Petrol", but these
rows' cylinder counts cannot be trusted: 78 of the 254 carry an implausible count (`1AR-FE`, a
Toyota 2.7 four, says 6; `B5254T12`, a Volvo 2.5 five, says 6; `BARRA245T`, a Ford straight-six,
says 8) - unsurprising, since the junk descriptor and the junk cylinder count came from the same
bad import. Writing them into prose would launder a numeric error into text. Instead the
displacement and fuel - both corroborated elsewhere in this campaign - carry the descriptor, and
the 78 suspect rows are exported as the next worklist.

Usage: python3 step65_step12_descriptors.py [--apply]
"""
import csv
import os
import re
import shutil
import sqlite3
import sys

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step65_2026-10-01.db"
CSV_OUT = "database_enriched/csv_exports/73_descriptors_step65.csv"
CSV_CYL = "database_enriched/csv_exports/74_suspect_cylinders_worklist.csv"
APPLY = "--apply" in sys.argv

MARKER = re.compile(r"\s*\((?:est\.|corr\.)\)", re.I)
# a descriptor is "real" if it mentions a displacement, a layout, or a known engine technology.
# `\d,\d` catches European decimals ("3,0"), which are a displacement, not junk.
SIGNAL = re.compile(r"\d\.\d|\d,\d|\d{3,4}\s*(cc)?|\b[VIHWR]\d\b|TDI|TSI|CRD|HDI|dCi|VTEC|HEMI|"
                    r"Electric|Hybrid|EcoBoost|Turbo", re.I)

# A badge is worth keeping only when it belongs to the brand that actually uses it. "T5" on a
# Volvo is that car's own output badge; "HHR" on a Mercedes is another manufacturer's model name
# that leaked in from the catalogue. Brand is checked against the row's own brand_example.
BADGES = [
    (re.compile(r"^[TD][3-8]$"), ("volvo",)),
    (re.compile(r"^(Cooper|Cooper S|Cooper D|One|One D)$", re.I), ("mini", "bmw")),
    (re.compile(r"\bAMG\b"), ("mercedes", "mercedes-benz")),
]


def badge(text, brand):
    b = (brand or "").strip().lower()
    for pat, brands in BADGES:
        if pat.search(text) and any(b.startswith(x) for x in brands):
            return text
    return None


def rebuilt(cc, fuel, suffix=None):
    if not cc:
        return None
    return f"{cc / 1000:.1f} L {fuel}" + (f" ({suffix})" if suffix else "")


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    g = lambda q: con.execute(q).fetchone()[0]

    engines = con.execute("""SELECT engine_code, engine_type, displacement_cc, cylinders, fuel,
                                    count_variants, data_confidence, brand_example
                             FROM engines WHERE engine_type IS NOT NULL""").fetchall()
    rows, cyl_worklist = [], []
    n_mark = n_junk = n_unfixable = 0

    for e in engines:
        old = e["engine_type"]
        junk = not SIGNAL.search(old)
        if junk:
            keep = badge(MARKER.sub("", old).strip(), e["brand_example"])
            new = rebuilt(e["displacement_cc"], e["fuel"], keep)
            if new is None:
                n_unfixable += 1
                rows.append(dict(table="engines", ref=e["engine_code"], action="SKIP_NO_DATA",
                                 old=old, new=None,
                                 note="no displacement recorded, so nothing factual to build from"))
                continue
            n_junk += 1
            rows.append(dict(table="engines", ref=e["engine_code"], action="REBUILD", old=old,
                             new=new, note="kept the brand's own badge" if keep
                             else "descriptor carried no engine information"))
            cc, cy = e["displacement_cc"], e["cylinders"]
            if cy and ((cy >= 6 and cc < 2300) or (cy <= 4 and cc > 3200) or (cy >= 8 and cc < 3500)
                       or (cy == 6 and 2350 <= cc <= 2700)):
                cyl_worklist.append(dict(engine_code=e["engine_code"], displacement_cc=cc,
                                         cylinders=cy, fuel=e["fuel"], variants=e["count_variants"],
                                         old_descriptor=old, cc_per_cyl=round(cc / cy)))
        elif MARKER.search(old):
            new = MARKER.sub("", old).strip()
            if not SIGNAL.search(new):
                new2 = rebuilt(e["displacement_cc"], e["fuel"])
                if new2:
                    n_junk += 1
                    rows.append(dict(table="engines", ref=e["engine_code"], action="REBUILD",
                                     old=old, new=new2,
                                     note="nothing left once the marker was stripped"))
                    continue
            n_mark += 1
            rows.append(dict(table="engines", ref=e["engine_code"], action="STRIP_MARKER", old=old,
                             new=new, note=f"provenance stays in data_confidence={e['data_confidence']}"))

    # variants: strip markers, and resync any variant repeating its engine row's junk text
    new_by_code = {r["ref"]: r["new"] for r in rows if r["action"] == "REBUILD"}
    for v in con.execute("""SELECT v.id, v.engine_code, v.engine_type, e.engine_type AS eng_text
                            FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code = v.engine_code
                            WHERE v.engine_type IS NOT NULL""").fetchall():
        old = v["engine_type"]
        if v["engine_code"] in new_by_code and old == v["eng_text"]:
            rows.append(dict(table="vehicle_variants", ref=v["id"], action="REBUILD", old=old,
                             new=new_by_code[v["engine_code"]],
                             note="variant repeated its engine row's junk descriptor"))
        elif MARKER.search(old):
            rows.append(dict(table="vehicle_variants", ref=v["id"], action="STRIP_MARKER", old=old,
                             new=MARKER.sub("", old).strip(), note="provenance stays in data_confidence"))

    from collections import Counter
    c = Counter((r["table"], r["action"]) for r in rows)
    for k, n in sorted(c.items()):
        print(f"  {k[0]:17} {k[1]:14} {n}")
    print(f"  suspect cylinder rows exported for the next step: {len(cyl_worklist)}")

    out = CSV_OUT if APPLY else CSV_OUT.replace(".csv", "_DRYRUN.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {out}")
    if cyl_worklist:
        with open(CSV_CYL, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(cyl_worklist[0].keys()))
            w.writeheader()
            w.writerows(sorted(cyl_worklist, key=lambda r: -r["variants"]))
        print(f"  wrote {CSV_CYL}")

    if not APPLY:
        print("\nDRY RUN - no changes. Re-run with --apply\nsample rebuilds:")
        for r in [x for x in rows if x["action"] == "REBUILD" and x["table"] == "engines"][:12]:
            print(f"   {r['ref'][:22]:24} '{r['old'][:38]}' -> '{r['new']}'")
        print("sample marker strips:")
        for r in [x for x in rows if x["action"] == "STRIP_MARKER" and x["table"] == "engines"][:6]:
            print(f"   {r['ref'][:22]:24} '{r['old'][:38]}' -> '{r['new']}'")
        return

    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    shutil.copy2(DB, BACKUP)
    print(f"\nbackup -> {BACKUP}")
    n = 0
    for r in rows:
        if r["new"] is None:
            continue
        if r["table"] == "engines":
            con.execute("UPDATE engines SET engine_type=? WHERE engine_code=?", (r["new"], r["ref"]))
        else:
            con.execute("UPDATE vehicle_variants SET engine_type=? WHERE id=?", (r["new"], r["ref"]))
        n += 1
    con.commit()
    print(f"  applied {n} descriptor updates")

    print("\n--- verify ---")
    print("engines still carrying (est.)/(corr.):", g("""SELECT count(*) FROM engines
        WHERE engine_type LIKE '%(est.)%' OR engine_type LIKE '%(corr.)%'"""))
    print("variants still carrying (est.)/(corr.):", g("""SELECT count(*) FROM vehicle_variants
        WHERE engine_type LIKE '%(est.)%' OR engine_type LIKE '%(corr.)%'"""))
    left = [r["engine_code"] for r in con.execute("SELECT engine_code, engine_type FROM engines WHERE engine_type IS NOT NULL")
            if not SIGNAL.search(r["engine_type"])]
    print("engine rows with no engine information in their descriptor:", len(left), left[:5])
    print("empty descriptors:", g("SELECT count(*) FROM engines WHERE trim(coalesce(engine_type,''))=''"))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("engines:", g("SELECT count(*) FROM engines"), "| variants:", g("SELECT count(*) FROM vehicle_variants"))
    con.close()


if __name__ == "__main__":
    main()
