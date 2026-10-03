'use strict';
// step96 - repair model picture links.
//
// 1. Rewrites oversized Wikimedia "original" URLs (…/commons/<a>/<ab>/<file>.jpg?utm_…original)
//    to the bounded thumbnail form, so a card never pulls a 10-14 MB file.
// 2. Links the picture files that already exist under database_enriched/model_images into
//    models.image_local_path, using the exact resolver the server uses (model_pictures.js).
//
// Dry run by default. Apply with:  node step96_repair_picture_links.js --apply
const { DatabaseSync } = require('node:sqlite');
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, 'database_enriched');
const DB_PATH = path.join(APP, 'car_database.db');
const LOG_PATH = path.join(APP, 'csv_exports', '96_picture_link_repairs.csv');
const BACKUP_DIR = path.join(APP, 'backups');
const { findLocalModelImage, boundedUrl } = require(path.join(APP, 'model_pictures.js'));

const APPLY = process.argv.includes('--apply');
const db = new DatabaseSync(DB_PATH);
db.exec('PRAGMA busy_timeout = 15000');

const log = [];
const bump = db.prepare(
  `UPDATE models
      SET image_url=?, image_source=COALESCE(image_source,'wikimedia'),
          image_match_method=COALESCE(image_match_method,'bounded_thumb')
    WHERE id=?`
);
const linkStmt = db.prepare(
  `UPDATE models
      SET image_local_path=?, image_source='local', image_match_method='local_file',
          image_match_score=?, image_match_name=?
    WHERE id=?`
);

const rows = db.prepare('SELECT id, brand_name, model_name, image_url, image_local_path, image_source FROM models').all();
console.log(`models scanned: ${rows.length} (apply=${APPLY})`);

const rel = p => path.relative(APP, p).split(path.sep).join('/');
let urlFixed = 0, linked = 0, alreadyLocal = 0, noPicture = 0;

for (const r of rows) {
  // 1. bound oversized remote urls
  if (r.image_url) {
    const bounded = boundedUrl(r.image_url);
    if (bounded !== r.image_url) {
      log.push([r.id, r.brand_name, r.model_name, 'url_to_thumbnail', r.image_url, bounded].join('\t'));
      if (APPLY) bump.run(bounded, r.id);
      urlFixed++;
    }
  }

  // 2. link an on-disk picture (same resolver the server uses at request time)
  const current = r.image_local_path;
  if (current && fs.existsSync(path.isAbsolute(current) ? current : path.join(APP, current))) {
    alreadyLocal++;
    continue;
  }
  const file = findLocalModelImage(r.brand_name, r.model_name, current);
  if (!file) { noPicture++; continue; }
  const store = rel(file);
  const exact = path.basename(file).toLowerCase().startsWith(`${r.brand_name}_${r.model_name}`.toLowerCase().replace(/[^a-z0-9]/g, ''));
  log.push([r.id, r.brand_name, r.model_name, current ? 'relink_local' : 'link_local', current || '', store, exact ? 100 : 80].join('\t'));
  if (APPLY) linkStmt.run(store, exact ? 100 : 80, path.basename(file, path.extname(file)), r.id);
  linked++;
}

console.log(`remote urls bounded : ${urlFixed}`);
console.log(`local links added   : ${linked}`);
console.log(`already linked      : ${alreadyLocal}`);
console.log(`no picture found    : ${noPicture}`);

if (APPLY) {
  fs.writeFileSync(LOG_PATH, 'id\tbrand\tmodel\taction\told\tnew\tscore\n' + log.join('\n') + '\n');
  console.log(`log written: ${LOG_PATH}`);
  console.log(db.prepare('PRAGMA integrity_check').get().integrity_check);
} else {
  console.log('\nDRY RUN - nothing written. Re-run with --apply to commit.');
  console.log(log.slice(0, 12).join('\n'));
}