"""Generic LEMON-replacement batch engine for Step 5 (batches 23+).
Clones the proven step13-31 pipeline: parse -> decide (trim rules / skip notes / R rules)
-> identity assert -> dry-run CSV -> --apply (backup, new engines, row fixes, relink,
spec-first merge+retire, count recompute, power backfill) -> verify block.
Per-brand scripts supply only data. Usage in brand script:

    import step5_lemon_lib as lib
    lib.run_batch(lib.Cfg(...))
"""
import sqlite3, csv, shutil, sys, re
from collections import defaultdict, Counter
from datetime import date

DB = "database_enriched/car_database.db"


class Cfg:
    def __init__(self, brand, step_tag, csv_num, lemon_baseline, engines_baseline,
                 R, NEW_ENGINES=None, ROW_FIXES=None, FUEL_FIX_BY_TARGET=None,
                 ENG_FUEL_FIX=None, IDENTITY=None, TRIM_RULES=None, SKIP_NOTES=None,
                 extra_decide=None, expect_mapped=None, expect_skipped=None):
        self.brand = brand                      # car_brand value
        self.step_tag = step_tag                # e.g. "step32"
        self.csv_num = csv_num                  # e.g. 40
        self.lemon_baseline = lemon_baseline    # total LEMON rows before apply
        self.engines_baseline = engines_baseline
        self.R = R                              # (MODEL, y0, y1, cc, vin, target, evidence, pfix)
        self.NEW_ENGINES = NEW_ENGINES or {}    # code -> (etype, fuel, cc, hp, cyl, oil_vis, oil_cap, oil_note)
        self.ROW_FIXES = ROW_FIXES or {}        # code -> {col: val}
        self.FUEL_FIX_BY_TARGET = FUEL_FIX_BY_TARGET or {}
        self.ENG_FUEL_FIX = ENG_FUEL_FIX or {}  # code -> fuel (engines table)
        self.IDENTITY = IDENTITY or {}          # code -> (fuel, cc)
        self.TRIM_RULES = TRIM_RULES or {}      # (MODEL, year|None, POST) -> (target, evidence, pfix, fuel_fix|None)
        self.SKIP_NOTES = SKIP_NOTES or {}      # (MODEL, year, cc, vin, post) -> note (None fields = wildcard)
        self.extra_decide = extra_decide        # fn(model, year, cc, vin, post, code) -> tuple|None
        self.expect_mapped = expect_mapped
        self.expect_skipped = expect_skipped


def parse_code(code, prefix):
    m = re.match(r"^" + re.escape(prefix) + r"_(.+)$", code)
    if not m:
        return None
    toks = m.group(1).split("_")
    yi = next((i for i, t in enumerate(toks) if re.fullmatch(r"(19|20)\d\d", t)), None)
    if yi is None:
        return None
    year = int(toks[yi])
    cc = vin = None
    model_toks = []
    for t in toks[:yi]:
        if re.fullmatch(r"\d+CC", t):
            cc = int(t[:-2])
        elif re.fullmatch(r"VIN[A-Z0-9]", t):
            vin = t[3:]
        else:
            model_toks.append(t)
    return " ".join(model_toks), year, cc, vin, "_".join(toks[yi + 1:])


def decide(cfg, model, year, cc, vin, post, code):
    mu, pu = model.upper(), (post or "").upper()
    # explicit skip notes
    for (sm, sy, sc, sv, sp), note in cfg.SKIP_NOTES.items():
        if (sm == mu and (sy is None or sy == year) and (sc is None or sc == cc)
                and (sv is None or sv == vin) and (sp is None or sp == pu or pu.endswith(sp))):
            return (None, note, None, None)
    # trim rows: POST present -> trim rules only (never fall through to cc rules)
    if pu:
        for (tm, ty, tp), (tgt, note, pfix, ffix) in cfg.TRIM_RULES.items():
            if tm == mu and (ty is None or ty == year) and (tp == pu or pu.endswith(tp)):
                return (tgt, note, ffix, pfix)
        if cfg.extra_decide:
            r = cfg.extra_decide(model, year, cc, vin, post, code)
            if r is not None:
                return r
        return (None, f"unknown trim slug '{post}' - no TRIM rule", None, None)
    if cfg.extra_decide:
        r = cfg.extra_decide(model, year, cc, vin, post, code)
        if r is not None:
            return r
    cands = [r for r in cfg.R if r[0] == mu and r[1] <= year <= r[2]
             and r[3] == cc and (r[4] is None or r[4] == vin)]
    if not cands:
        return (None, f"no rule for {cfg.brand} {model} {year} cc={cc} vin={vin}", None, None)
    cands.sort(key=lambda r: (r[4] is None, r[1] != year))  # vin-specific first, then nearest y0
    r = cands[0]
    return (r[5], r[6], cfg.FUEL_FIX_BY_TARGET.get(r[5]), r[7])


def run_batch(cfg):
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB); cur = con.cursor()
    base_lemon = cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0]
    assert base_lemon == cfg.lemon_baseline, \
        f"BASELINE MISMATCH: LEMON={base_lemon}, expected {cfg.lemon_baseline} (workspace rewind?)"
    base_eng = cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0]
    assert base_eng == cfg.engines_baseline, \
        f"BASELINE MISMATCH: engines={base_eng}, expected {cfg.engines_baseline}"
    prefix = "LEMON_" + cfg.brand.upper().replace(" ", "_")
    rows = cur.execute("""SELECT id, car_model, car_year, engine_code, fuel FROM vehicle_variants
        WHERE car_brand=? AND engine_code LIKE ? ORDER BY car_model, car_year, engine_code""",
        (cfg.brand, prefix + "%")).fetchall()
    decisions, skips = [], []
    for vid, model, year, code, fuel in rows:
        p = parse_code(code, prefix)
        assert p, f"unparseable code: {code}"
        pm, py, cc, vin, post = p
        assert pm.upper() == model.upper(), f"model parse mismatch {code} vs {model}"
        tgt, note, fuel_fix, pfix = decide(cfg, model, year, cc, vin, post, code)
        if fuel_fix and fuel == fuel_fix:
            fuel_fix = None
        if tgt is None:
            skips.append((vid, model, year, code, note)); continue
        decisions.append((vid, model, year, code, tgt, note, fuel_fix, pfix))
    print(f"{cfg.brand} LEMON rows: {len(rows)} | mapped: {len(decisions)} | skipped: {len(skips)}")
    if cfg.expect_mapped is not None:
        assert len(decisions) == cfg.expect_mapped, f"expected {cfg.expect_mapped} mapped, got {len(decisions)}"
    if cfg.expect_skipped is not None:
        assert len(skips) == cfg.expect_skipped, f"expected {cfg.expect_skipped} skips, got {len(skips)}"
    for s in skips:
        print(f"  SKIP: {s[1]} {s[2]} [{s[3]}] - {s[4]}")
    print("\ntop targets:")
    for t, c in Counter(d[4] for d in decisions).most_common(40):
        print(f"  {c:3} {t}")
    print("\nfuel fixes:", Counter((d[4], d[6]) for d in decisions if d[6]))
    missing = set(d[4] for d in decisions) - set(r[0] for r in cur.execute("SELECT engine_code FROM engines")) - set(cfg.NEW_ENGINES)
    assert not missing, f"targets missing from engines+NEW_ENGINES: {missing}"
    for tgt, (efuel, ecc) in cfg.IDENTITY.items():
        cc_fix = cfg.ROW_FIXES.get(tgt, {}).get("displacement_cc")
        row = cur.execute("SELECT fuel, displacement_cc FROM engines WHERE engine_code=?", (tgt,)).fetchone()
        if row is None:
            continue
        if row[0] and efuel and row[0] != efuel and tgt not in cfg.ENG_FUEL_FIX:
            raise AssertionError(f"IDENTITY CONFLICT {tgt}: engines.fuel={row[0]}, expected {efuel}")
        if cc_fix and row[1] and row[1] != cc_fix:
            print(f"  identity: {tgt} cc {row[1]} junk -> queued ROW_FIX to {cc_fix}"); continue
        if row[1] and ecc and abs(row[1] - ecc) / ecc > 0.07:
            raise AssertionError(f"IDENTITY CONFLICT {tgt}: engines.cc={row[1]}, expected ~{ecc}")
    print("identity assert: OK")

    csv_path = f"database_enriched/csv_exports/{cfg.csv_num}_lemon_{cfg.step_tag}_decisions" + ("" if apply else "_DRYRUN") + ".csv"
    if not apply:
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["variant_id", "brand", "model", "year", "old_engine_code", "new_engine_code", "fuel_fix", "power_fill", "evidence"])
            for d in decisions:
                w.writerow([d[0], cfg.brand, d[1], d[2], d[3], d[4], d[6] or "", d[7] if d[7] else "", d[5] or ""])
            for s in skips:
                w.writerow([s[0], cfg.brand, s[1], s[2], s[3], "", "", "SKIP", s[4]])
        print(f"\nDRY RUN - no changes. Re-run with --apply."); con.close(); return

    bak = f"database_enriched/backups/car_database_backup_pre_{cfg.step_tag}_{date.today().isoformat()}.db"
    shutil.copy(DB, bak); print(f"backup: {bak}")
    for code, spec in cfg.NEW_ENGINES.items():
        etype, fuel, cc, hp, cyl = spec[0], spec[1], spec[2], spec[3], spec[4]
        oil = spec[5:] if len(spec) > 5 else ()
        if not cur.execute("SELECT 1 FROM engines WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp,
                cylinders, count_variants, data_confidence) VALUES (?,?,?,?,?,?,0,?)""",
                (code, etype, fuel, cc, hp, cyl, cfg.step_tag.upper() + "_VERIFIED"))
            print(f"  created {code}")
        if oil and len(oil) >= 3 and not cur.execute("SELECT 1 FROM engine_service_specs WHERE engine_code=?", (code,)).fetchone():
            cur.execute("""INSERT INTO engine_service_specs (engine_code, oil_viscosity, oil_capacity_with_filter_l, oil_spec_source)
                VALUES (?,?,?,?)""", (code, oil[0], oil[1], oil[2]))
    for code, fixes in cfg.ROW_FIXES.items():
        sets = ", ".join(f"{k}=?" for k in fixes)
        cur.execute(f"UPDATE engines SET {sets} WHERE engine_code=?", (*fixes.values(), code))
        print(f"  row-fix {code}: {fixes}")
    for code, fuel in cfg.ENG_FUEL_FIX.items():
        cur.execute("UPDATE engines SET fuel=? WHERE engine_code=?", (fuel, code))
        print(f"  eng-fuel-fix {code} -> {fuel}")

    lemon_retired = defaultdict(list)
    for vid, model, year, old, new, note, fuel_fix, pfix in decisions:
        cur.execute("UPDATE vehicle_variants SET engine_code=?, fuel=COALESCE(?, fuel) WHERE id=?", (new, fuel_fix, vid))
        cur.execute("""UPDATE vehicle_variants SET engine_power_hp=COALESCE(?, COALESCE(engine_power_hp,
            (SELECT power_hp FROM engines WHERE engine_code=?)),
            COALESCE((SELECT power_hp FROM engines WHERE engine_code=?), engine_power_hp)),
            engine_type=COALESCE(engine_type, (SELECT engine_type FROM engines WHERE engine_code=?)) WHERE id=?""",
            (pfix, new, new, new, vid))
        lemon_retired[old].append((vid, year, model))

    spec_cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_service_specs)")]
    tech_cols = [c[1] for c in cur.execute("PRAGMA table_info(engine_technical_specs)")]

    def merge_specs(table, cols, lc, target):
        cols = [c for c in cols if c != "engine_code"]
        cur.execute(f"SELECT {','.join(cols)} FROM {table} WHERE engine_code=?", (lc,))
        src = cur.fetchone()
        if src is None:
            return
        if table == "engine_service_specs":
            srow = cur.execute("SELECT oil_spec_source FROM engine_service_specs WHERE engine_code=?", (lc,)).fetchone()
            if srow and srow[0] and "ESTIMATE" in srow[0].upper():
                cur.execute(f"DELETE FROM {table} WHERE engine_code=?", (lc,)); return
        if cur.execute(f"SELECT 1 FROM {table} WHERE engine_code=?", (target,)).fetchone():
            sets = ", ".join(f"{c}=COALESCE({c}, ?)" for c in cols)
            cur.execute(f"UPDATE {table} SET {sets} WHERE engine_code=?", (*src, target))
        else:
            cur.execute(f"INSERT INTO {table} (engine_code, {','.join(cols)}) VALUES (?{',?'*len(cols)})", (target, *src))

    for lc, vids in lemon_retired.items():
        tgt = cur.execute("SELECT engine_code FROM vehicle_variants WHERE id=?", (vids[0][0],)).fetchone()[0]
        merge_specs("engine_service_specs", spec_cols, lc, tgt)
        merge_specs("engine_technical_specs", tech_cols, lc, tgt)
        cur.execute("DELETE FROM engine_service_specs WHERE engine_code=?", (lc,))
        cur.execute("DELETE FROM engine_technical_specs WHERE engine_code=?", (lc,))
        cur.execute("DELETE FROM engines WHERE engine_code=?", (lc,))

    cur.execute("""UPDATE engines SET count_variants =
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code = engines.engine_code)""")
    tgts = tuple(set(d[4] for d in decisions))
    cur.execute(f"""UPDATE vehicle_variants SET engine_power_hp=
        (SELECT power_hp FROM engines WHERE engine_code=vehicle_variants.engine_code)
        WHERE engine_code IN ({','.join('?'*len(tgts))}) AND engine_power_hp IS NULL""", tgts)

    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variant_id", "brand", "model", "year", "old_engine_code", "new_engine_code", "fuel_fix", "power_fill", "evidence"])
        for d in decisions:
            w.writerow([d[0], cfg.brand, d[1], d[2], d[3], d[4], d[6] or "", d[7] if d[7] else "", d[5] or ""])
    con.commit()

    print("\n--- verify ---")
    print(f"LEMON {cfg.brand} remaining:", cur.execute(
        "SELECT COUNT(*) FROM vehicle_variants WHERE car_brand=? AND engine_code LIKE 'LEMON%'",
        (cfg.brand,)).fetchone()[0])
    print("orphan refs:", cur.execute("""SELECT COUNT(*) FROM vehicle_variants v LEFT JOIN engines e ON e.engine_code=v.engine_code
        WHERE v.engine_code IS NOT NULL AND e.engine_code IS NULL""").fetchone()[0])
    print("count mismatches:", cur.execute("""SELECT COUNT(*) FROM engines WHERE count_variants !=
        (SELECT COUNT(*) FROM vehicle_variants v WHERE v.engine_code=engines.engine_code)""").fetchone()[0])
    print("total engines:", cur.execute("SELECT COUNT(*) FROM engines").fetchone()[0])
    print("LEMON total:", cur.execute("SELECT COUNT(*) FROM vehicle_variants WHERE engine_code LIKE 'LEMON%'").fetchone()[0])
    print(f"{cfg.brand} fuels:", dict(cur.execute(
        "SELECT fuel, COUNT(*) FROM vehicle_variants WHERE car_brand=? GROUP BY fuel", (cfg.brand,)).fetchall()))
    con.close()
