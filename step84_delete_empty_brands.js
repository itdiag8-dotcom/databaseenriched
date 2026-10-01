// Step 84: delete all brand rows that have zero car models.
// - A brand is kept only if at least one row in models references it (brand_id or name).
// - Verified beforehand: no vehicle_variants.car_brand / engines.brand_example reference
//   any of the deleted brand names, so the removal cannot orphan anything.
// Run: node step84_delete_empty_brands.js
// Backup expected: backups/car_database_backup_2026-10-01_pre_delete_empty_brands.db

const fs = require("fs");
const path = require("path");
const { DatabaseSync } = require("node:sqlite");

const ROOT = __dirname;
const DB_PATH = path.join(ROOT, "database_enriched", "car_database.db");
const DECISION_CSV = path.join(ROOT, "database_enriched", "csv_exports", "84_deleted_empty_brands.csv");

const db = new DatabaseSync(DB_PATH);
db.exec("PRAGMA foreign_keys=OFF");

const q = (s, ...a) => db.prepare(s).get(...a);
const before = {
  brands: q("SELECT COUNT(*) n FROM brands").n,
  models: q("SELECT COUNT(*) n FROM models").n,
  variants: q("SELECT COUNT(*) n FROM vehicle_variants").n,
};

const doomed = db.prepare(`
  SELECT b.id, b.name FROM brands b
  WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.brand_id = b.id OR m.brand_name = b.name)
  ORDER BY b.name`).all();

const refs = {
  variants: q(`SELECT COUNT(*) n FROM vehicle_variants v
    WHERE v.car_brand IN (SELECT name FROM brands WHERE id IN (${doomed.map(() => "?").join(",") || "-1"}))`, ...doomed.map(d => d.id)).n,
  engines: q(`SELECT COUNT(*) n FROM engines e
    WHERE e.brand_example IN (SELECT name FROM brands WHERE id IN (${doomed.map(() => "?").join(",") || "-1"}))`, ...doomed.map(d => d.id)).n,
};
if (refs.variants || refs.engines) {
  throw new Error(`ABORT: doomed brands still referenced (variants=${refs.variants}, engines=${refs.engines})`);
}

db.exec("BEGIN");
db.prepare(`DELETE FROM brands WHERE id IN (${doomed.map(() => "?").join(",")})`).run(...doomed.map(d => d.id));

const after = {
  brands: q("SELECT COUNT(*) n FROM brands").n,
  models: q("SELECT COUNT(*) n FROM models").n,
  variants: q("SELECT COUNT(*) n FROM vehicle_variants").n,
};

const fail = [];
if (q("PRAGMA integrity_check").integrity_check !== "ok") fail.push("integrity_check");
if (q("SELECT COUNT(*) n FROM brands b WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.brand_id=b.id)").n > 0) fail.push("empty brands remain");
if (q("SELECT COUNT(*) n FROM models m LEFT JOIN brands b ON b.id=m.brand_id WHERE b.name IS NULL").n > 0) fail.push("orphan model->brand");
if (after.models !== before.models) fail.push("models count changed");
if (after.variants !== before.variants) fail.push("variants count changed");

if (fail.length) {
  db.exec("ROLLBACK");
  throw new Error("VERIFICATION FAILED, rolled back: " + fail.join("; "));
}
db.exec("COMMIT");

const header = ["brand_id", "brand_name"];
const lines = [header.join(","), ...doomed.map(d => `${d.id},${/["\n,]/.test(d.name) ? '"' + d.name.replace(/"/g, '""') + '"' : d.name}`)];
fs.writeFileSync(DECISION_CSV, lines.join("\n") + "\n", "utf8");

console.log(`brands deleted: ${doomed.length}  (${before.brands} -> ${after.brands})`);
console.log(`models: ${before.models} -> ${after.models}  (unchanged)`);
console.log(`vehicle_variants: ${before.variants} -> ${after.variants}  (unchanged)`);
console.log("verification: ALL PASS");
console.log("decision log: " + DECISION_CSV);
