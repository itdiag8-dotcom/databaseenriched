"""Step 13b (step66b) - the rest of the MagicMotorsport enrichment.

step66 handles ECU maker/model on `vehicle_variants`. This one covers the other three things the
source can tell us, reusing step66's loader, normalisers and consensus rule:

  A. `engines.ecu_maker` / `engines.ecu_model` - 1,659 of 5,670 engine rows are NULL or 'Unknown'.
  B. `vehicle_variants.engine_code` - 89 rows have none. A code is only written when it already
     exists in `engines`, because engine_code is the join key: inventing one creates an orphan
     reference. Any engine row that gains or loses variants has `count_variants` recomputed.
  C. `engines.engine_type` - Step 12 rebuilt 250 junk descriptors into deliberately plain strings
     like "5.5 L Petrol", because the cylinder counts behind them were not trustworthy. The
     source carries a real description for many of those codes ("1.4L Turbo MultiAir"), which is
     strictly better. Only the Step-12 placeholders are replaced; descriptors that already say
     something specific are left alone.

Usage: python3 step66b_engines_codes_descriptors.py --source <file.csv> [--apply]
"""
import argparse
import csv
import importlib.util
import os
import re
import shutil
import sqlite3
from collections import Counter, defaultdict

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step66b_2026-10-01.db"
CSV_DIR = "database_enriched/csv_exports"

spec = importlib.util.spec_from_file_location("s66", "step66_magicmotorsport_import.py")
s66 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s66)

# a Step-12 placeholder descriptor: "5.5 L Petrol", optionally with a kept badge "(T5)"
PLACEHOLDER = re.compile(r"^\d+\.\d+ L (Petrol|Diesel|Hybrid|Electric|LPG|E85|CNG)(\s*\(.*\))?$", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = s66.load_source(args.source)
    by_brand_code, by_code, by_bmp, _tcm = s66.build_maps(rows)

    # descriptions, grouped the same way (independent of ECU, so TCM rows count here too)
    desc_by_code = defaultdict(set)
    code_by_bmp = defaultdict(set)
    for r in rows:
        c = s66.norm_code(r.get("engine_code"))
        d = (r.get("engine_model") or "").strip()
        if c and d:
            desc_by_code[c].add(d)
        if c:
            ps = s66.to_int(r.get("engine_power_ps"))
            if ps:
                code_by_bmp[(s66.norm_brand(r.get("brand_name")).lower(),
                             s66.norm_model(r.get("model_name")), ps)].add(c)

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    known = {}
    for (code,) in con.execute("SELECT engine_code FROM engines"):
        known.setdefault(s66.norm_code(code), code)

    decisions = []
    stats = Counter()

    # ---- A. ECU on the engines table ---------------------------------------
    for e in con.execute("""SELECT engine_code, brand_example, power_hp, ecu_maker, ecu_model
                            FROM engines""").fetchall():
        code = s66.norm_code(e["engine_code"])
        if not code:
            continue
        brand = (e["brand_example"] or "").lower()
        cands = by_brand_code.get((brand, code)) or by_code.get(code)
        if not cands:
            stats["engine_no_match"] += 1
            continue
        maker, ecu, how = s66.consensus(cands, ps=e["power_hp"])
        if not maker:
            stats["engine_ambiguous"] += 1
            continue
        had = e["ecu_model"] is not None and e["ecu_maker"] not in (None, "Unknown")
        if (e["ecu_maker"], e["ecu_model"]) == (maker, ecu):
            stats["engine_already_correct"] += 1
            continue
        if had:
            kind = s66.classify(e["ecu_maker"], e["ecu_model"], maker, ecu)
            if kind in ("identical", "maker_spelling", "ours_more_specific"):
                stats["engine_kept_" + kind] += 1
                continue
            stats["engine_overwrite"] += 1
        else:
            stats["engine_fill"] += 1
        decisions.append(dict(table="engines", ref=e["engine_code"], field="ecu",
                              action="OVERWRITE" if had else "FILL",
                              old=f"{e['ecu_maker']}/{e['ecu_model']}", new=f"{maker}/{ecu}",
                              evidence=how))

    # ---- B. engine_code on variants that have none --------------------------
    code_fills = []
    for v in con.execute("""SELECT id, car_brand, car_model, engine_power_hp FROM vehicle_variants
                            WHERE engine_code IS NULL""").fetchall():
        key = ((v["car_brand"] or "").lower(), s66.norm_model(v["car_model"]), v["engine_power_hp"])
        cands = code_by_bmp.get(key)
        if not cands or len(cands) != 1:
            stats["code_no_unanimous_match"] += 1
            continue
        norm = next(iter(cands))
        if norm not in known:
            # writing a code with no engine row would create an orphan reference
            stats["code_absent_from_engines"] += 1
            continue
        code_fills.append((v["id"], known[norm]))
        stats["code_fill"] += 1
        decisions.append(dict(table="vehicle_variants", ref=v["id"], field="engine_code",
                              action="FILL", old=None, new=known[norm],
                              evidence=f"brand+model+ps -> {v['car_brand']} {v['car_model']} {v['engine_power_hp']}ps"))

    # ---- C. upgrade the Step-12 placeholder descriptors ---------------------
    desc_updates = []
    PETROL_TECH = re.compile(r"\b(TFSI|TSI|FSI|GDI|VVTi|VTEC|MPI|T-Jet|EcoBoost|MultiAir)\b", re.I)
    DIESEL_TECH = re.compile(r"\b(TDI|CDI|CRDi|dCi|HDi|JTD|Multijet|TDCi|BlueTEC|Duratorq|SDI)\b", re.I)
    for e in con.execute("""SELECT engine_code, engine_type, fuel, displacement_cc FROM engines
                            WHERE engine_type IS NOT NULL""").fetchall():
        if not PLACEHOLDER.match(e["engine_type"]):
            continue
        cands = desc_by_code.get(s66.norm_code(e["engine_code"]))
        if not cands or len(cands) != 1:
            stats["desc_no_unanimous_match"] += 1
            continue
        src = next(iter(cands))
        # reject a description that is only a displacement ("2.0L"): it carries no more
        # information than the placeholder and would drop the fuel word we already have
        extra = re.sub(r"^\s*\d+[.,]?\d*\s*L\s*", "", src, flags=re.I).strip()
        if not re.search(r"[A-Za-z]", extra):
            stats["desc_source_says_nothing_new"] += 1
            continue
        # the description must not contradict what we already verified about this engine
        m = re.match(r"\s*(\d+)[.,](\d+)\s*L", src, re.I)
        if m and e["displacement_cc"]:
            litres = float(f"{m.group(1)}.{m.group(2)}")
            if abs(litres - e["displacement_cc"] / 1000) > 0.15:
                stats["desc_displacement_conflict"] += 1
                continue
        fuel = (e["fuel"] or "").lower()
        if (fuel == "diesel" and PETROL_TECH.search(src)) or (fuel == "petrol" and DIESEL_TECH.search(src)):
            stats["desc_fuel_tech_conflict"] += 1
            continue
        new = src
        if e["fuel"] and e["fuel"].lower() not in new.lower():
            new = f"{new} {e['fuel']}"          # keep the fuel the placeholder stated
        badge = re.search(r"\(([^)]+)\)$", e["engine_type"])   # the Step-12 brand badge
        if badge and badge.group(1).lower() not in new.lower():
            new = f"{new} ({badge.group(1)})"
        if s66.norm_ecu(new) == s66.norm_ecu(e["engine_type"]):
            continue
        desc_updates.append((e["engine_code"], e["engine_type"], new))
        stats["desc_upgrade"] += 1
        decisions.append(dict(table="engines", ref=e["engine_code"], field="engine_type",
                              action="UPGRADE", old=e["engine_type"], new=new,
                              evidence="source description, unanimous for this code"))

    print("outcomes:")
    for k, v in sorted(stats.items()):
        print(f"   {k:32} {v}")

    os.makedirs(CSV_DIR, exist_ok=True)
    out = f"{CSV_DIR}/78_engines_codes_descriptors_step66b{'' if args.apply else '_DRYRUN'}.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(decisions[0].keys()))
        w.writeheader(); w.writerows(decisions)
    print(f"  wrote {out} ({len(decisions)} rows)")

    if not args.apply:
        print("\nDRY RUN - no changes. Re-run with --apply")
        for d in decisions[:6]:
            print(f"   {d['table']:16} {str(d['ref'])[:16]:18} {d['field']:12} {str(d['old'])[:28]:30} -> {str(d['new'])[:34]}")
        print("   ... engine_code fills:")
        for d in [x for x in decisions if x["field"] == "engine_code"][:6]:
            print(f"      variant {d['ref']:<7} -> {d['new']:16} ({d['evidence']})")
        print("   ... descriptor upgrades:")
        for d in [x for x in decisions if x["field"] == "engine_type"][:8]:
            print(f"      {str(d['ref'])[:18]:20} '{d['old']}' -> '{d['new']}'")
        return

    shutil.copy2(DB, BACKUP)
    print(f"\nbackup -> {BACKUP}")
    for d in decisions:
        if d["field"] == "ecu":
            maker, ecu = d["new"].split("/", 1)
            con.execute("UPDATE engines SET ecu_maker=?, ecu_model=? WHERE engine_code=?",
                        (maker, ecu, d["ref"]))
    for vid, code in code_fills:
        con.execute("UPDATE vehicle_variants SET engine_code=? WHERE id=?", (code, vid))
    for code, _old, new in desc_updates:
        con.execute("UPDATE engines SET engine_type=? WHERE engine_code=?", (new, code))
    # engine_code changed on some variants, so the derived counter must be rebuilt
    con.execute("""UPDATE engines SET count_variants =
                   (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")
    con.commit()
    print(f"  applied {len(decisions)} updates and recomputed count_variants")

    g = lambda q: con.execute(q).fetchone()[0]
    print("\n--- verify ---")
    print("engines with NULL/Unknown ECU:", g("SELECT count(*) FROM engines WHERE ecu_model IS NULL OR ecu_maker='Unknown'"))
    print("variants with NULL engine_code:", g("SELECT count(*) FROM vehicle_variants WHERE engine_code IS NULL"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("engines:", g("SELECT count(*) FROM engines"), "| variants:", g("SELECT count(*) FROM vehicle_variants"))
    con.close()


if __name__ == "__main__":
    main()
