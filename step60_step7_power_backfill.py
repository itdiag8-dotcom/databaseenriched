"""Step 7 (step60) - backfill engine_power_hp on variants whose engine row already knows the answer.

535 variants carry no power figure. 342 of them sit on engine rows that are themselves blank
(a later step), 8 have no engine_code at all, and 185 sit on an engine row that DOES have a
power value. This step handles those 185.

It is NOT a blanket copy. Only 19 of the 55 engine codes involved have populated sibling
variants that unanimously agree with their engine row; for the other 36 the engine row's figure
is one tune among several, so each code was ruled on individually:

  COPY   - the engine row's figure is right for these cars (either siblings agree, or the row's
           descriptor names exactly this application).
  RULE   - the row's figure is wrong for some of these cars; an explicit per-year or per-model
           value is used instead, with the evidence recorded below.
  SKIP   - the "engine code" is a generic displacement descriptor shared by unrelated engines
           (`1.5 dCI`, `2.0 16v`, ...). The row's figure comes from some other manufacturer's
           car and there is no honest way to pick a number. Left NULL, documented.

engine_power_kw is filled alongside at the DB's own convention, kw = hp * 0.7355 (verified
against populated rows: 188hp -> 138.3kW), but only where it is currently NULL.

Usage: python3 step60_step7_power_backfill.py [--apply]
"""
import csv
import os
import shutil
import sqlite3
import sys

DB = "database_enriched/car_database.db"
BACKUP = "database_enriched/backups/car_database_backup_pre_step60_2026-10-01.db"
CSV_OUT = "database_enriched/csv_exports/68_power_backfill_step60_decisions.csv"
APPLY = "--apply" in sys.argv

# ---------------------------------------------------------------- COPY: engine row value stands
COPY = {
    # --- row figure confirmed by unanimous siblings on the same code ---
    "ED6":      "2.4 Tigershark MultiAir2; every populated sibling on this code (DART, ProMaster, Cherokee) reads 188",
    "L87":      "6.2 V8 EcoTec3, 420hp in Escalade/Tahoe/Yukon/Silverado - all 33 siblings read 420",
    "CXBA":     "US 1.8 TSI EA888 Gen3, 170hp across Golf/Jetta/Beetle/Passat - 22 siblings unanimous",
    "CXBB":     "sister code to CXBA, same US 1.8 TSI 170hp",
    "N26B20A":  "SULEV N20 in 228i/328i/428i; all four siblings read 245",
    "N52B30O0": "330i/530i N52 255hp; both siblings read 255",
    "N52B25O1": "325i N52 215hp; five siblings read 215",
    "N53B30U0": "325i N53 215hp; seven siblings read 215",
    "N52B30O1": "X5 3.0si N52 268hp; sibling reads 268",
    "N43B20O0": "320i N43 168hp; both siblings read 168",
    "N53B30O0": "330i N53 268hp; sibling reads 268",
    "M266E17":  "A/B-Class M266 1.7, 114hp; A-Class sibling reads 114",
    "S63B44A":  "X6 M S63 555hp - the NULL row IS an X6 and three siblings read 555",
    "CDMA":     "TTS 2.0 TFSI 265hp; both TT siblings read 265",
    "CGXB":     "3.0 TFSI 310hp; A6 and A7 siblings read 310",
    "CJWB":     "Q7 3.0 TFSI 333hp; Q7 sibling reads 333 - the NULL rows are Q7s too",
    "CJWE":     "Q7 3.0 TFSI 280hp detune; Q7 sibling reads 280",
    "CTWB":     "Q7 3.0 TFSI 280hp; Q7 sibling reads 280",
    "1.5 TDCi": "the only sibling is the same car - Ford C-Max 1.5 TDCi, 148hp",
    "3.0 dCI":  "Vel Satis and Espace share the 3.0 dCi V6; Espace sibling reads 178",
    # --- row figure within rounding of the siblings (metric PS vs hp conversions) ---
    "CAED":     "2.0 TFSI A4/A5/A6; siblings read 220-221 (162kW), row 221",
    "CPMB":     "2.0 TFSI quattro; siblings 217-220, row 217",
    "CPMA":     "2.0 TFSI FFV quattro; siblings 208-211, row 208",
    "CETA":     "TT 2.0 TFSI; siblings 208-211, row 208",
    "CNTA":     "Golf GTI 2.0 TSI; siblings 210-217, row 217",
    "CXCA":     "US GTI 2015-16 2.0 TSI 210hp - three GTI siblings read 210",
    "CPLA":     "Jetta 2.0 TSI; siblings 208-211, row 208",
    "CPPA":     "Jetta 2.0 TSI; siblings 210-211, row 211",
    "CBPA":     "Jetta 2.0; siblings 115-116, row 115",
    "CPNB":     "3.0 TDI Clean Diesel, US rating; siblings 236-240, row 236",
    "AWP":      "1.8T 20v 180hp - the TT 1.8T quattro and Mk4 GTI share this tune",
    "BHE":      "TT 3.2 V6, 250 PS = 247hp; row and one sibling read 247",
    "BGH":      "Phaeton 4.2 V8, 335 PS = 330hp; the 'Volkswagen Phaeton' sibling reads 330",
    "BGJ":      "sister code to BGH, same Phaeton 4.2 V8",
    "EDG":      "2.4 World engine in 200/Avenger; siblings 170-175, row 170",
    "D17A6":    "Civic VII 1.7; the CIVIC VII Saloon sibling reads 116",
    "ZY":       "Mazda2 1.5 MZR; same-model sibling reads 103",
    "Z16XE1":   "Zafira 1.6 Ecotec, 105 PS = 103hp; the Opel Zafira sibling reads 103",
    "Z16XEP":   "Astra 1.6 TwinPort; Opel Astra siblings read 102-103",
    "KFV (TU3A)": "206+ 1.4 8v, 75 PS = 74hp; 207 SW/Van siblings read 74",
    # --- row figure confirmed against the specific application, overriding a mixed sibling set ---
    "N57D30A":  "these are US-market 535d and X5 xDrive35d, both rated 255hp - the lower 204/245 "
                "siblings are European 325d/330d tunes of the same family",
    "L3B":      "2.7 Dual-Volute; 310hp is the CT4-badged rating (Premium Luxury/Sport). 325hp "
                "belongs to the CT4-V and nothing in these rows says V. Source: Cadillac Society "
                "2020-11-18 and the 2022/2023 CT4 trim tables",
    "N63B44 (ActiveHybrid)": "ActiveHybrid 7 combined output; the row's own 455hp figure is the "
                "code's defining rating",
}

# ---------------------------------------------------------------- RULE: explicit per-variant value
def rule_value(code, brand, model, year, engine_hp):
    """Return (hp, evidence) or None to fall through to COPY/SKIP."""
    if code == "ESH":
        # 6.4 HEMI 392: 470hp as the 2011-2014 SRT8, 485hp from 2015 as SRT 392 / Scat Pack.
        if year and year <= 2014:
            return 471, ("6.4 HEMI 392 in SRT8 trim (2011-2014) = 470hp; every populated sibling "
                         "of that era - Charger, 300, Durango, Grand Cherokee - reads 471")
        return 485, ("from 2015 the 392 was rerated to 485hp for SRT 392 / Scat Pack "
                     "(confirmed: ChallengerTalk SRT8-vs-392, AmericanMuscle 392-vs-Scat-Pack)")
    if code == "LF3":
        # The engine row's own descriptor documents both tunes of the 3.6 twin-turbo.
        if model.upper() == "XTS":
            return 410, "the row's descriptor states XTS 410hp for this twin-turbo 3.6"
        return 420, "the row's descriptor states CTS V-Sport 420hp for this twin-turbo 3.6"
    if code == "N20B20A":
        return 245, ("228i/328i/428i/X1 xDrive28i 2014-2016 all ran the 240hp SAE / 245 PS N20 "
                     "tune; the F22/F30/F32 siblings read 245. The row's 215hp (and its 2795cc) "
                     "describe a 125i and are wrong for these cars")
    if code == "N63B44A":
        if year and year >= 2014:
            return 449, "X6 xDrive50i 2014 ran the N63TU, 449 PS - an X6 sibling reads 449"
        return 407, ("550i/650i/750i of 2012 ran the pre-TU N63 at 407 PS; eight siblings of that "
                     "era (5 F10, 5 GT, 7 F01, X5 E70, X6 E71) read 407-408")
    if code == "M54B30":
        return 228, ("530i and X5 3.0i ran the M54B30 at 231 PS = 228hp; six BMW siblings read "
                     "228. The row's 276hp is an Alpina B3 3.3 figure")
    if code == "N52B30":
        return 261, ("130i ran 265 PS = 261hp, matching the Z4 3.0si siblings; the 215/218/227 "
                     "siblings are 120i/125i/128i tunes")
    return None

# ---------------------------------------------------------------- SKIP: generic descriptors
SKIP = {
    "1.5 dCI":  "generic descriptor shared by every Renault/Nissan 1.5 dCi from 56 to 109hp; the "
                "2009 Megane and Scenic were each sold in two tunes and nothing here says which",
    "1.8 16v":  "generic descriptor; the row's 130hp comes from a Chery Tiggo. The Caliber 1.8 is "
                "a GEMA World engine - a different engine entirely",
    "2.0 16v":  "generic descriptor spanning Ford, Renault, Subaru and Hyundai engines 114-173hp; "
                "the row's 134hp is a Citroen Jumpy figure, not a Grand Vitara one",
    "2.2 dCi":  "the row's 134hp is the Almera/X-Trail M9R tune; the Interstar is a Master-based "
                "van using the G9T at a much lower output",
    "2.4 16v":  "the row's 168hp is a Hyundai Sonata figure; the Grunder is a Galant with the "
                "Mitsubishi 4G69",
    "ZSD-422":  "2.2 TDCi Puma, sold in 100/125/155 PS tunes in the 2015 Transit alone; siblings "
                "spread 118-160",
}


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    todo = con.execute("""
        SELECT v.id, v.car_brand, v.car_model, v.car_year, v.engine_code, v.engine_power_kw,
               e.power_hp AS eng_hp, e.engine_type
        FROM vehicle_variants v JOIN engines e ON e.engine_code = v.engine_code
        WHERE v.engine_power_hp IS NULL AND e.power_hp IS NOT NULL
        ORDER BY v.engine_code, v.car_brand, v.car_year""").fetchall()
    print(f"candidates (variant power NULL, engine row has power): {len(todo)}")
    assert len(todo) == 185, f"baseline changed: expected 185, got {len(todo)}"

    rows, counts = [], {"RULE": 0, "COPY": 0, "SKIP": 0}
    unhandled = set()
    for v in todo:
        code = v["engine_code"]
        r = rule_value(code, v["car_brand"], v["car_model"] or "", v["car_year"], v["eng_hp"])
        if r:
            action, hp, ev = "RULE", r[0], r[1]
        elif code in SKIP:
            action, hp, ev = "SKIP", None, SKIP[code]
        elif code in COPY:
            action, hp, ev = "COPY", v["eng_hp"], COPY[code]
        else:
            unhandled.add(code)
            continue
        counts[action] += 1
        rows.append({"variant_id": v["id"], "action": action, "engine_code": code,
                     "brand": v["car_brand"], "model": v["car_model"], "year": v["car_year"],
                     "engine_row_hp": v["eng_hp"], "new_hp": hp,
                     "new_kw": round(hp * 0.7355, 1) if (hp and v["engine_power_kw"] is None) else None,
                     "evidence": ev})
    if unhandled:
        print("UNHANDLED CODES:", sorted(unhandled))
        sys.exit(1)

    print(f"  RULE {counts['RULE']} | COPY {counts['COPY']} | SKIP {counts['SKIP']}")
    out = CSV_OUT if APPLY else CSV_OUT.replace(".csv", "_DRYRUN.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {out}")

    if not APPLY:
        print("\nDRY RUN - no changes. Re-run with --apply")
        for a in ("RULE", "SKIP"):
            print(f"\n-- {a} --")
            for r in rows:
                if r["action"] == a:
                    print(f"   {r['engine_code']:22} {r['brand']} {r['model']} {r['year']} -> {r['new_hp']}")
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
    con.commit()
    print(f"  set engine_power_hp on {n_hp} variants, engine_power_kw on {n_kw}")

    g = lambda q: con.execute(q).fetchone()[0]
    print("\n--- verify ---")
    print("NULL-power variants remaining:", g("SELECT count(*) FROM vehicle_variants WHERE engine_power_hp IS NULL"))
    print("  of those, engine row also NULL:", g("""SELECT count(*) FROM vehicle_variants v JOIN engines e
        ON e.engine_code=v.engine_code WHERE v.engine_power_hp IS NULL AND e.power_hp IS NULL"""))
    print("  of those, no engine_code:", g("SELECT count(*) FROM vehicle_variants WHERE engine_power_hp IS NULL AND engine_code IS NULL"))
    print("  of those, documented skips:", g("""SELECT count(*) FROM vehicle_variants v JOIN engines e
        ON e.engine_code=v.engine_code WHERE v.engine_power_hp IS NULL AND e.power_hp IS NOT NULL"""))
    print("fuel conflicts:", g("SELECT count(*) FROM vehicle_variants v JOIN engines e ON e.engine_code=v.engine_code WHERE v.fuel<>e.fuel"))
    print("orphan refs:", g("""SELECT count(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL"""))
    print("count mismatches:", g("""SELECT count(*) FROM engines e WHERE e.count_variants<>
        (SELECT count(*) FROM vehicle_variants v WHERE v.engine_code=e.engine_code)"""))
    print("implausible power (<30 or >1200):", g("SELECT count(*) FROM vehicle_variants WHERE engine_power_hp<30 OR engine_power_hp>1200"))
    con.close()


if __name__ == "__main__":
    main()
