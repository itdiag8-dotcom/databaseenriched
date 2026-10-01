// Step 83: uppercase all car model names and merge case-variant duplicate models.
// - models.model_name / vehicle_variants.car_model / remapping_queue.car_model -> UPPER(TRIM())
// - engines / engine_service_specs / engine_technical_specs .model_example -> UPPER (display field)
// - duplicate (brand, case-insensitive model) rows merged into one canonical row.
// ecu_model columns are ECU part numbers (e.g. ME7.9.10) and are intentionally untouched.
// Run: node step83_uppercase_model_names.js
// Backup expected: backups/car_database_backup_2026-10-01_pre_uppercase.db

const fs = require("fs");
const path = require("path");
const { DatabaseSync } = require("node:sqlite");

const ROOT = __dirname;
const DB_PATH = path.join(ROOT, "database_enriched", "car_database.db");
const DECISION_CSV = path.join(ROOT, "database_enriched", "csv_exports", "83_uppercase_model_names_merge.csv");

const STATUS_RANK = { existing: 0, active: 1, added_from_vivid: 2, added_missing: 3 };

function csvEscape(v) {
  if (v === null || v === undefined) return "";
  const s = String(v);
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function yearsSpan(ps, pe) {
  if (ps === null && pe === null) return null;
  if (ps !== null && pe !== null) return ps === pe ? String(ps) : `${ps}-${pe}`;
  return String(ps !== null ? ps : pe);
}

const db = new DatabaseSync(DB_PATH);
db.exec("PRAGMA foreign_keys=OFF");

const triggers = db.prepare("SELECT name FROM sqlite_master WHERE type='trigger'").all();
if (triggers.length) throw new Error("triggers present, aborting: " + JSON.stringify(triggers));

const before = {};
for (const t of ["brands", "models", "engines", "vehicle_variants", "engine_service_specs", "engine_technical_specs", "remapping_queue"]) {
  before[t] = db.prepare(`SELECT COUNT(*) n FROM "${t}"`).get().n;
}

db.exec("BEGIN");

// 1. find case-variant collision groups (brand + UPPER(TRIM(name)), >1 row)
const groups = db.prepare(`
  SELECT brand_name, UPPER(TRIM(model_name)) AS upkey, COUNT(*) AS c
  FROM models GROUP BY brand_name, upkey HAVING c > 1`).all();

const decisions = [];

for (const g of groups) {
  const rows = db.prepare(`
    SELECT id, model_name, production_start, production_end, years_span, total_variants, source, status
    FROM models WHERE brand_name = ? AND UPPER(TRIM(model_name)) = ?
    ORDER BY id`).all(g.brand_name, g.upkey);

  const rank = (r) => STATUS_RANK[r.status] !== undefined ? STATUS_RANK[r.status] : 9;
  const pick = (a, b) =>
    rank(a) - rank(b) ||
    (b.total_variants || 0) - (a.total_variants || 0) ||
    a.id - b.id;

  const canonical = rows.reduce((a, b) => (pick(a, b) <= 0 ? a : b));
  const victims = rows.filter((r) => r.id !== canonical.id);

  const starts = rows.map((r) => r.production_start).filter((v) => v !== null);
  const ends = rows.map((r) => r.production_end).filter((v) => v !== null);
  const ps = starts.length ? Math.min(...starts) : null;
  const pe = ends.length ? Math.max(...ends) : null;

  db.prepare(`UPDATE models SET production_start=?, production_end=?, years_span=? WHERE id=?`)
    .run(ps, pe, yearsSpan(ps, pe), canonical.id);

  for (const v of victims) {
    db.prepare("DELETE FROM models WHERE id=?").run(v.id);
    decisions.push({
      brand: g.brand_name, upkey: g.upkey,
      kept_id: canonical.id, kept_name: canonical.model_name, kept_source: canonical.source, kept_status: canonical.status,
      dropped_id: v.id, dropped_name: v.model_name, dropped_source: v.source, dropped_status: v.status,
      dropped_years: v.years_span, merged_start: ps, merged_end: pe,
    });
  }
}

// 2. uppercase all model-name fields
const upd = [];
upd.push(["models.model_name", db.prepare("UPDATE models SET model_name = UPPER(TRIM(model_name)) WHERE model_name <> UPPER(TRIM(model_name))").run().changes]);
upd.push(["vehicle_variants.car_model", db.prepare("UPDATE vehicle_variants SET car_model = UPPER(TRIM(car_model)) WHERE car_model <> UPPER(TRIM(car_model))").run().changes]);
upd.push(["remapping_queue.car_model", db.prepare("UPDATE remapping_queue SET car_model = UPPER(TRIM(car_model)) WHERE car_model <> UPPER(TRIM(car_model))").run().changes]);
upd.push(["remapping_queue.wrong_engine_model_example", db.prepare("UPDATE remapping_queue SET wrong_engine_model_example = UPPER(TRIM(wrong_engine_model_example)) WHERE wrong_engine_model_example IS NOT NULL AND wrong_engine_model_example <> UPPER(TRIM(wrong_engine_model_example))").run().changes]);
upd.push(["engines.model_example", db.prepare("UPDATE engines SET model_example = UPPER(TRIM(model_example)) WHERE model_example IS NOT NULL AND model_example <> UPPER(TRIM(model_example))").run().changes]);
upd.push(["engine_service_specs.model_example", db.prepare("UPDATE engine_service_specs SET model_example = UPPER(TRIM(model_example)) WHERE model_example IS NOT NULL AND model_example <> UPPER(TRIM(model_example))").run().changes]);
upd.push(["engine_technical_specs.model_example", db.prepare("UPDATE engine_technical_specs SET model_example = UPPER(TRIM(model_example)) WHERE model_example IS NOT NULL AND model_example <> UPPER(TRIM(model_example))").run().changes]);

// 3. refresh total_variants for every model from live variant counts
db.prepare(`UPDATE models SET total_variants = (
  SELECT COUNT(*) FROM vehicle_variants v WHERE v.car_brand = models.brand_name AND v.car_model = models.model_name)`).run();

// ---- verification (inside transaction: fail => rollback) ----
const q = (s) => db.prepare(s).get();
const fail = [];
const check = (label, bad) => { if (bad) fail.push(label); };

check("integrity_check", q("PRAGMA integrity_check").integrity_check !== "ok");
check("non-uppercase models remain", q("SELECT COUNT(*) n FROM models WHERE model_name <> UPPER(TRIM(model_name))").n > 0);
check("non-uppercase car_model remain", q("SELECT COUNT(*) n FROM vehicle_variants WHERE car_model <> UPPER(TRIM(car_model))").n > 0);
check("case-collision groups remain", q("SELECT COUNT(*) n FROM (SELECT 1 FROM models GROUP BY brand_name, UPPER(model_name) HAVING COUNT(*)>1)").n > 0);
check("variants without matching model row", q(`SELECT COUNT(*) n FROM vehicle_variants v
  WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.brand_name=v.car_brand AND m.model_name=v.car_model)`).n > 0);
check("total_variants drift", q(`SELECT COUNT(*) n FROM models m WHERE COALESCE(m.total_variants,-1) <>
  (SELECT COUNT(*) FROM vehicle_variants v WHERE v.car_brand=m.brand_name AND v.car_model=m.model_name)`).n > 0);

const after = {};
for (const t of Object.keys(before)) after[t] = db.prepare(`SELECT COUNT(*) n FROM "${t}"`).get().n;

if (fail.length) {
  db.exec("ROLLBACK");
  throw new Error("VERIFICATION FAILED, rolled back: " + fail.join("; "));
}
db.exec("COMMIT");

// ---- decision CSV ----
const header = ["brand", "merged_key", "kept_model_id", "kept_model_name", "kept_source", "kept_status",
  "dropped_model_id", "dropped_model_name", "dropped_source", "dropped_status", "dropped_years_span",
  "merged_production_start", "merged_production_end"];
const lines = [header.join(",")];
for (const d of decisions) {
  lines.push([d.brand, d.upkey, d.kept_id, d.kept_name, d.kept_source, d.kept_status,
    d.dropped_id, d.dropped_name, d.dropped_source, d.dropped_status, d.dropped_years,
    d.merged_start, d.merged_end].map(csvEscape).join(","));
}
fs.writeFileSync(DECISION_CSV, lines.join("\n") + "\n", "utf8");

console.log("=== rows updated ===");
for (const [col, n] of upd) console.log(`  ${col}: ${n}`);
console.log("=== models merged ===");
console.log(`  collision groups: ${groups.length}, rows dropped: ${decisions.length}`);
console.log("=== counts before -> after ===");
for (const t of Object.keys(before)) {
  const mark = before[t] !== after[t] ? "  <-- changed" : "";
  console.log(`  ${t}: ${before[t]} -> ${after[t]}${mark}`);
}
console.log("=== verification: ALL PASS ===");
console.log("decision log: " + DECISION_CSV);
