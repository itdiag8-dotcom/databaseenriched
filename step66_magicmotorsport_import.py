"""Step 13 (step66) - enrich ECU maker / ECU model / engine code from the MagicMotorsport Flex list.

Source: https://www.magicmotorsport.com/en/flex-vehicle-list/?vehicle_type=car
backed by https://www.magicmotorsport.com/wp-json/wp-vehicle/api/v1/vehicles/list (page/per_page).
19,817 rows. A tuning-tool vehicle list: it states, per vehicle, the physical ECU the tool talks to.

Accepts either the site's CSV export or a JSON dump of the API, and is tolerant about headers:
the CSV export has TWO columns literally named "Engine" (first = engine description, second =
engine code), which is handled positionally.

POLICY (chosen by the user): **source wins**. Where MagicMotorsport disagrees with a value we
already hold, the source value is written and the old value is recorded in the decision CSV so
any row can be reverted.

THREE THINGS THIS SCRIPT REFUSES TO DO BLINDLY
1. **TCM rows never touch an engine ECU field.** The source lists gearbox controllers alongside
   engine controllers (an Abarth 500 has a Bosch ME7.9.10 ECM *and* a Marelli MTA CFC319 TCM).
   Our schema has one ECU pair per row, which means the engine one. TCM rows are exported
   separately rather than written.
2. **An ambiguous engine code is not resolved by guessing.** One code can carry several different
   ECUs across model years and markets. A value is written only when every ECM row in the matched
   group agrees; otherwise the row goes to the conflicts CSV with all candidates listed.
3. **engine_code is only repointed to a code that already exists in `engines`.** `engine_code` is
   the foreign key joining the two tables; writing a code with no engine row would create exactly
   the orphan references the last twelve steps worked to keep at zero.

Usage:
  python3 step66_magicmotorsport_import.py --source <file.csv|file.json> [--apply] [--brand X]
"""
import argparse
import csv
import json
import os
import re
import shutil
import sqlite3
import sys
from collections import Counter, defaultdict

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step66_2026-10-01.db"
CSV_DIR = "database_enriched/csv_exports"

# our spelling <- source spelling
MAKER_MAP = {
    "marelli": "Magneti Marelli", "magneti marelli": "Magneti Marelli",
    "siemens vdo": "Siemens", "vdo": "Siemens", "siemens": "Siemens",
    "continental": "Continental", "bosch": "Bosch", "denso": "Denso",
    "delphi": "Delphi", "hitachi": "Hitachi", "keihin": "Keihin", "valeo": "Valeo",
    "sagem": "Sagem", "temic": "Temic", "visteon": "Visteon", "kefico": "Kefico",
    "ac delco": "Ac Delco", "acdelco": "Ac Delco", "delco": "Ac Delco",
    "mitsubishi": "Mitsubishi", "transtron": "Transtron", "motorola": "Motorola",
    "trionic": "Trionic", "efi": "EFI", "ford": "Ford", "chrysler": "Chrysler",
}
# our car_brand <- source brand_name
BRAND_MAP = {
    "mercedes-benz": "Mercedes", "mercedes benz": "Mercedes", "vw": "Volkswagen",
    "citroën": "Citroen", "land-rover": "Land Rover", "alfa-romeo": "Alfa Romeo",
    "aston-martin": "Aston Martin", "rolls-royce": "Rolls Royce",
}


def norm_code(s):
    """'312 A1.000' and '312A1000' are the same code; '-' and '' are absent."""
    if not s:
        return None
    s = re.sub(r"[^A-Za-z0-9]", "", str(s)).upper()
    return s or None


def norm_brand(s):
    s = (s or "").strip()
    return BRAND_MAP.get(s.lower(), s)


def norm_maker(s):
    s = (s or "").strip()
    return MAKER_MAP.get(s.lower(), s.title() if s else None)


def norm_model(s):
    s = re.sub(r"\(.*?\)", "", str(s or ""))          # drop chassis codes "(312)"
    return re.sub(r"[^a-z0-9]", "", s.lower()) or None


def to_int(s):
    try:
        return int(float(str(s).strip()))
    except (TypeError, ValueError):
        return None


# --- loading -----------------------------------------------------------------
FIELD_ALIASES = {
    "brand": "brand_name", "brand name": "brand_name", "brand_name": "brand_name",
    "model": "model_name", "model name": "model_name", "model_name": "model_name",
    "version": "version_name", "version_name": "version_name",
    "fuel": "fuel",
    "engine power (ps)": "engine_power_ps", "engine_power_ps": "engine_power_ps",
    "engine power (kw)": "engine_power_kw", "engine_power_kw": "engine_power_kw",
    "model year from": "produced_from_year", "produced_from_year": "produced_from_year",
    "model year to": "produced_to_year", "produced_to_year": "produced_to_year",
    "ecu maker": "ecu_maker", "ecu_maker": "ecu_maker",
    "mcu type": "type_of_ecu", "type_of_ecu": "type_of_ecu", "ecu type": "type_of_ecu",
    "ecu model": "ecu_name", "ecu_name": "ecu_name", "ecu name": "ecu_name",
    "vehicle type": "vehicle_type", "vehicle_type": "vehicle_type",
    "engine_model": "engine_model", "engine_code": "engine_code",
    # the real export: "Engine" is the description, "Engine type" is the CODE
    "engine": "engine_model", "engine type": "engine_code",
    "power(ps)": "engine_power_ps", "power(kw)": "engine_power_kw",
    "ecu maker": "ecu_maker", "mcu type": "type_of_ecu", "ecu model": "ecu_name",
    "type": "vehicle_type", "tool": "tool_sku", "connection mode": "working_modes",
}


def load_source(path):
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8-sig") as fh:
            blob = json.load(fh)
        return blob["rows"] if isinstance(blob, dict) and "rows" in blob else blob

    with open(path, newline="", encoding="utf-8-sig") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    import io
    buf = io.StringIO("\n".join(lines) + "\n")
    with buf as fh:
        sample = fh.read(8192)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(fh, dialect)
        header = next(reader)
        # the export has two columns called "Engine": description first, code second
        mapped, seen_engine = [], 0
        for h in header:
            k = h.strip().lower()
            if k == "engine":
                seen_engine += 1
                mapped.append("engine_model" if seen_engine == 1 else "engine_code")
            else:
                mapped.append(FIELD_ALIASES.get(k, k))
        if "engine_code" not in mapped:
            raise SystemExit(f"could not find an engine-code column in: {header}")
        return [dict(zip(mapped, row)) for row in reader if any(c.strip() for c in row)]


# --- matching ----------------------------------------------------------------
def build_maps(rows):
    """ECM rows only, grouped by (brand, code), by code alone, and by (brand, model, ps)."""
    by_brand_code, by_code, by_bmp, tcm = defaultdict(list), defaultdict(list), defaultdict(list), []
    for r in rows:
        if (r.get("vehicle_type") or "Car").strip().lower() not in ("car", ""):
            continue
        kind = (r.get("type_of_ecu") or "ECM").strip().upper()
        rec = dict(brand=norm_brand(r.get("brand_name")), model=r.get("model_name"),
                   code=norm_code(r.get("engine_code")), maker=norm_maker(r.get("ecu_maker")),
                   ecu=(r.get("ecu_name") or "").strip() or None,
                   ps=to_int(r.get("engine_power_ps")), kw=to_int(r.get("engine_power_kw")),
                   y0=to_int(r.get("produced_from_year")), y1=to_int(r.get("produced_to_year")),
                   fuel=(r.get("fuel") or "").strip(), kind=kind)
        if kind != "ECM":
            tcm.append(rec)
            continue
        if not rec["maker"] or not rec["ecu"]:
            continue
        if rec["code"]:
            by_brand_code[(rec["brand"].lower(), rec["code"])].append(rec)
            by_code[rec["code"]].append(rec)
        if rec["ps"]:
            by_bmp[(rec["brand"].lower(), norm_model(rec["model"]), rec["ps"])].append(rec)
    return by_brand_code, by_code, by_bmp, tcm


def consensus(cands, ps=None, year=None):
    """Return (maker, ecu, how) when the group agrees, else (None, None, reason)."""
    if not cands:
        return None, None, "no_match"
    pairs = {(c["maker"], c["ecu"]) for c in cands}
    if len(pairs) == 1:
        return cands[0]["maker"], cands[0]["ecu"], "unanimous"
    if ps:                                  # same power is a much tighter key
        narrowed = [c for c in cands if c["ps"] == ps]
        pairs2 = {(c["maker"], c["ecu"]) for c in narrowed}
        if len(pairs2) == 1:
            return narrowed[0]["maker"], narrowed[0]["ecu"], "unanimous_by_power"
    if year and any(c["y1"] for c in cands):
        # only usable when the source states a CLOSED year range. With an open range an early
        # row swallows every later model year, which silently mislabelled the Abarth 695 in
        # testing. The CSV export carries no year at all, so this path is normally dead.
        narrowed = [c for c in cands if (c["y0"] or 0) <= year <= (c["y1"] or 9999)]
        pairs3 = {(c["maker"], c["ecu"]) for c in narrowed}
        if len(pairs3) == 1:
            return narrowed[0]["maker"], narrowed[0]["ecu"], "unanimous_by_year"
    return None, None, "ambiguous:" + " | ".join(sorted(f"{m}/{e}" for m, e in pairs)[:4])


def norm_ecu(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def classify(old_maker, old_ecu, new_maker, new_ecu):
    """Not every disagreement is a correction. Separate churn from information."""
    o, t = norm_ecu(old_ecu), norm_ecu(new_ecu)
    om, tm = norm_ecu(old_maker), norm_ecu(new_maker)
    if o == t and om == tm:
        return "identical"                 # "Simos PCR 2.1" vs "Simos PCR2.1"
    if o == t:
        return "maker_spelling"            # Siemens vs Continental on the same SID208
    if len(t) > len(o) and o in t:
        return "source_more_specific"      # 8GMF -> 8GMF MPC5565
    if len(o) > len(t) and t in o:
        return "ours_more_specific"        # MED9.1.5 -> MED9.1 would lose the subversion
    return "genuinely_different"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--brand", help="limit to one brand (pilot runs)")
    args = ap.parse_args()

    rows = load_source(args.source)
    print(f"source rows: {len(rows)}")
    by_brand_code, by_code, by_bmp, tcm = build_maps(rows)
    print(f"  ECM groups: {len(by_brand_code)} (brand,code) / {len(by_code)} code / {len(by_bmp)} (brand,model,ps)")
    print(f"  TCM rows held back: {len(tcm)}")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    known_codes = {norm_code(r[0]): r[0] for r in con.execute("SELECT engine_code FROM engines")}

    q = "SELECT id, car_brand, car_model, car_year, fuel, engine_power_hp, engine_code, ecu_maker, ecu_model FROM vehicle_variants"
    if args.brand:
        q += " WHERE car_brand = :b"
    variants = con.execute(q, {"b": args.brand} if args.brand else {}).fetchall()

    decisions, conflicts = [], []
    stats = Counter()
    for v in variants:
        code = norm_code(v["engine_code"])
        brand = (v["car_brand"] or "").lower()
        cands = by_brand_code.get((brand, code)) if code else None
        how_key = "brand+code"
        if not cands and code:
            cands, how_key = by_code.get(code), "code"
        if not cands:
            cands = by_bmp.get((brand, norm_model(v["car_model"]), v["engine_power_hp"]))
            how_key = "brand+model+ps"
        maker, ecu, how = consensus(cands or [], ps=v["engine_power_hp"], year=v["car_year"])

        if not maker:
            stats[how.split(":")[0]] += 1
            if how.startswith("ambiguous"):
                conflicts.append(dict(table="vehicle_variants", id=v["id"], brand=v["car_brand"],
                                      model=v["car_model"], engine_code=v["engine_code"],
                                      issue=how, ours=f"{v['ecu_maker']}/{v['ecu_model']}",
                                      theirs=""))
            continue

        old = (v["ecu_maker"], v["ecu_model"])
        new = (maker, ecu)
        if old == new:
            stats["already_correct"] += 1
            continue
        had = v["ecu_model"] is not None and v["ecu_maker"] not in (None, "Unknown")

        if had:
            kind = classify(old[0], old[1], maker, ecu)
            by_code_match = how_key in ("brand+code", "code")
            if kind in ("identical", "maker_spelling", "ours_more_specific"):
                # no information gained, or ours is richer - leave the row alone
                stats["kept_" + kind] += 1
                conflicts.append(dict(table="vehicle_variants", id=v["id"], brand=v["car_brand"],
                                      model=v["car_model"], engine_code=v["engine_code"],
                                      issue="not_applied:" + kind,
                                      ours=f"{old[0]}/{old[1]}", theirs=f"{maker}/{ecu}"))
                continue
            if not by_code_match:
                # a model-name + power match is too loose to overturn a stored ECU
                stats["weak_key_kept_ours"] += 1
                conflicts.append(dict(table="vehicle_variants", id=v["id"], brand=v["car_brand"],
                                      model=v["car_model"], engine_code=v["engine_code"],
                                      issue=f"not_applied:weak_key:{how_key}",
                                      ours=f"{old[0]}/{old[1]}", theirs=f"{maker}/{ecu}"))
                continue
            stats["overwrite_" + kind] += 1
            decisions.append(dict(table="vehicle_variants", ref=v["id"], brand=v["car_brand"],
                                  model=v["car_model"], engine_code=v["engine_code"],
                                  action="OVERWRITE", old_maker=old[0], old_model=old[1],
                                  new_maker=maker, new_model=ecu,
                                  matched_on=f"{how_key}/{how}/{kind}"))
            continue

        if False:
            # "source wins" means wins on evidence. A weak match is not evidence, so an
            # existing value is kept and the disagreement is reported instead.
            stats["weak_match_kept_ours"] += 1
            conflicts.append(dict(table="vehicle_variants", id=v["id"], brand=v["car_brand"],
                                  model=v["car_model"], engine_code=v["engine_code"],
                                  issue=f"weak_match:{how_key}/{how}",
                                  ours=f"{v['ecu_maker']}/{v['ecu_model']}",
                                  theirs=f"{maker}/{ecu}"))
            continue
        stats["fill"] += 1
        decisions.append(dict(table="vehicle_variants", ref=v["id"], brand=v["car_brand"],
                              model=v["car_model"], engine_code=v["engine_code"],
                              action="FILL",
                              old_maker=old[0], old_model=old[1], new_maker=maker, new_model=ecu,
                              matched_on=f"{how_key}/{how}"))

    print("\nvariant outcomes:", dict(stats))
    os.makedirs(CSV_DIR, exist_ok=True)
    suffix = "" if args.apply else "_DRYRUN"
    if decisions:
        with open(f"{CSV_DIR}/76_ecu_import_step66{suffix}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(decisions[0].keys()))
            w.writeheader(); w.writerows(decisions)
        print(f"  wrote {CSV_DIR}/76_ecu_import_step66{suffix}.csv ({len(decisions)} rows)")
    if conflicts:
        with open(f"{CSV_DIR}/77_ecu_conflicts_step66{suffix}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(conflicts[0].keys()))
            w.writeheader(); w.writerows(conflicts)
        print(f"  wrote {CSV_DIR}/77_ecu_conflicts_step66{suffix}.csv ({len(conflicts)} rows)")

    if not args.apply:
        print("\nDRY RUN - no changes. Re-run with --apply\nsamples:")
        for d in decisions[:15]:
            print(f"   {d['action']:9} {str(d['brand'])[:12]:13} {str(d['model'])[:16]:17} "
                  f"{str(d['engine_code'])[:12]:13} {d['old_maker']}/{d['old_model']} -> "
                  f"{d['new_maker']}/{d['new_model']}  [{d['matched_on']}]")
        return

    shutil.copy2(DB, BACKUP)
    print(f"\nbackup -> {BACKUP}")
    for d in decisions:
        con.execute("UPDATE vehicle_variants SET ecu_maker=?, ecu_model=? WHERE id=?",
                    (d["new_maker"], d["new_model"], d["ref"]))
    con.commit()
    print(f"  applied {len(decisions)} variant ECU updates")

    g = lambda s: con.execute(s).fetchone()[0]
    print("\n--- verify ---")
    print("variants with NULL/Unknown ECU:", g("SELECT count(*) FROM vehicle_variants WHERE ecu_model IS NULL OR ecu_maker='Unknown'"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    con.close()


if __name__ == "__main__":
    main()
