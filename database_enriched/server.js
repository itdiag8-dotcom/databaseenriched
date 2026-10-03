'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('node:crypto');
const { DatabaseSync } = require('node:sqlite');

const ROOT = __dirname;
const DB_PATH = path.join(ROOT, 'car_database.db');
const DASH_PATH = path.join(ROOT, 'dashboard', 'index.html');
const BACKUP_DIR = path.join(ROOT, 'backups');
// Port 3000 is the only accessible port in AI Studio
const PORT = 3000;
// Host 0.0.0.0 is required for AI Studio preview
const HOST = process.env.HOST || '0.0.0.0';

if (!fs.existsSync(DB_PATH)) {
  console.log('Database not found at ' + DB_PATH + ', auto-initializing...');
  try {
    const { initDatabase } = require(path.join(ROOT, '..', 'init_db.js'));
    initDatabase();
  } catch (err) {
    console.error('Failed to auto-initialize database:', err);
  }
}

fs.mkdirSync(BACKUP_DIR, { recursive: true });
const today = new Date().toISOString().slice(0, 10);
const dailyBackup = path.join(BACKUP_DIR, `car_database_backup_${today}.db`);
try {
  if (fs.existsSync(DB_PATH) && !fs.existsSync(dailyBackup)) fs.copyFileSync(DB_PATH, dailyBackup);
} catch (e) {
  console.error('Daily backup failed:', e.message);
}

const { getBrandKey, getBrandLogoSVG, getOrImportBrandLogo } = require('./brand_logos');
const { getModelPicture } = require('./model_pictures');

const db = new DatabaseSync(DB_PATH);

const TABLES = {
  model: 'models',
  engine: 'engines',
  service: 'engine_service_specs',
  technical: 'engine_technical_specs',
  variants: 'vehicle_variants',
  ecu: 'ecu_diagnostics'
};
const PRIMARY_KEYS = {
  model: 'id',
  engine: 'engine_code',
  service: 'engine_code',
  technical: 'engine_code',
  variants: 'id',
  ecu: 'id'
};
const PK_EDITABLE = { engine: 1 }; // only engines.engine_code may be renamed
const ENGINE_CASCADE = ['engine_service_specs', 'engine_technical_specs', 'vehicle_variants'];
const ETHEREAL = new Set(['model', 'variants', 'ecu']); // tables whose pk is not an engine_code

const COLUMN_CACHE = {};
function columns(key) {
  if (!COLUMN_CACHE[key]) {
    COLUMN_CACHE[key] = db.prepare(`PRAGMA table_info(${TABLES[key]})`).all().map(c => ({
      name: c.name, type: c.type || 'TEXT', notnull: !!c.notnull, pk: !!c.pk
    }));
  }
  return COLUMN_CACHE[key];
}

function getBaseModelName(brand, name) {
  if (!name) return '';
  let s = String(name).trim();
  const bLower = (brand || '').toLowerCase();

  // Strip parenthetical codes like " (8D2, B5)", " (2A/C)", " (E81)", " (W211)", " (312)", " (1J2)"
  s = s.replace(/\s*\([^)]*\)$/, '');

  // 1. Peugeot / Citroen / Porsche / Ferrari 3 or 4 digit numbers (e.g. 206, 206 CC, 206 Hatchback, 207 SW, 308, 911, 2008)
  const numSeriesMatch = s.match(/^(\d{3,4})(?:\+|\s+Plus|\s+CC|\s+SW|\s+Saloon|\s+Sedan|\s+Van|\s+Hatchback|\s+GTI|\s+RC)?$/i);
  if (numSeriesMatch && (bLower.includes('peugeot') || bLower.includes('citro') || bLower.includes('porsche') || bLower.includes('ferrari') || /^\d{3,4}$/.test(numSeriesMatch[1]))) {
    return numSeriesMatch[1];
  }

  // 2. BMW series (1 Series, 3 Series, 5 Series, 7 Series, 8 Series, X1-X7, Z1-Z8, M1-M8)
  if (bLower.includes('bmw')) {
    const bmwSeries = s.match(/^(?:BMW\s+)?([1-8])\s*(?:Series|er)?(?:\s*–.*|\s+Convertible|\s+Coupe|\s+Touring|\s+Gran Coupe)?$/i);
    if (bmwSeries) return bmwSeries[1] + ' Series';
    const bmwCode = s.match(/^(?:BMW\s+)?([1-8])\d{2}[a-z]*\b/i);
    if (bmwCode) return bmwCode[1] + ' Series';
    const bmwXZ = s.match(/^(X[1-7]|Z[1-8]|i[38]|iX[13]?|M[2-8])\b/i);
    if (bmwXZ) return bmwXZ[1].toUpperCase();
  }

  // 3. Mercedes-Benz classes
  if (bLower.includes('mercedes') || bLower.includes('benz')) {
    const mbNum = s.match(/^([A-CE-SG]|CL|CLA|CLC|CLK|CLS|GL|GLA|GLB|GLC|GLE|GLK|GLS|SL|SLC|SLK|SLS)\s*\d+/i);
    if (mbNum) {
      const cls = mbNum[1].toUpperCase();
      return cls.endsWith('-CLASS') || cls.endsWith('CLASS') ? cls : cls + '-Class';
    }
    const mbClass = s.match(/^(A|B|C|E|S|G|V|X|CL|CLA|CLC|CLK|CLS|GL|GLA|GLB|GLC|GLE|GLK|GLS|SL|SLC|SLK|SLS|AMG GT|EQA|EQB|EQC|EQE|EQS|eVito|Sprinter|Vito|Citan)\b/i);
    if (mbClass) {
      const cls = mbClass[1];
      const clsUpper = cls.toUpperCase();
      if (['SPRINTER', 'VITO', 'CITAN', 'EVITO', 'AMG GT'].includes(clsUpper)) return clsUpper.charAt(0) + clsUpper.slice(1).toLowerCase();
      return clsUpper + '-Class';
    }
  }

  // 4. Known model family prefixes across major global brands
  const knownFamilies = [
    'Golf', 'Passat', 'Polo', 'Jetta', 'Tiguan', 'Touareg', 'Touran', 'Sharan', 'Scirocco', 'Transporter', 'Beetle', 'Bora', 'Amarok', 'Up!',
    'Astra', 'Corsa', 'Vectra', 'Zafira', 'Insignia', 'Omega', 'Kadett', 'Agila', 'Meriva', 'Mokka', 'Vivaro', 'Movano',
    'Clio', 'Megane', 'Laguna', 'Scenic', 'Espace', 'Twingo', 'Kangoo', 'Master', 'Trafic', 'Captur', 'Kadjar', 'Koleos',
    'Focus', 'Fiesta', 'Mondeo', 'Escort', 'Transit', 'C-Max', 'B-Max', 'S-Max', 'Kuga', 'Ranger', 'Explorer', 'Galaxy', 'Ka',
    'Octavia', 'Fabia', 'Superb', 'Citigo', 'Felicia', 'Kamiq', 'Karoq', 'Kodiaq', 'Yeti', 'Roomster',
    'Ibiza', 'Leon', 'Toledo', 'Cordoba', 'Altea', 'Alhambra', 'Arosa', 'Ateca', 'Arona', 'Tarraco',
    '500', 'Panda', 'Punto', 'Tipo', 'Bravo', 'Brava', 'Doblo', 'Ducato', 'Fiorino', 'Stilo', 'Uno',
    'Corolla', 'Yaris', 'Camry', 'RAV4', 'Hilux', 'Avensis', 'Celica', 'Supra', 'Prius', 'Aygo', 'Land Cruiser', 'Aurion', 'Auris',
    'Civic', 'Accord', 'CR-V', 'HR-V', 'Jazz', 'Prelude', 'Integra',
    'Micra', 'Qashqai', 'Juke', 'X-Trail', 'Navara', 'Patrol', 'Leaf', 'Almera', 'Primera',
    'i10', 'i20', 'i30', 'i40', 'ix35', 'Tucson', 'Santa Fe', 'Elantra', 'Sonata', 'Kona',
    'Ceed', "Cee'd", 'Rio', 'Sportage', 'Sorento', 'Picanto', 'Stonic', 'Optima',
    'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'Q2', 'Q3', 'Q5', 'Q7', 'Q8', 'TT', 'R8', '80', '100', '200'
  ];

  for (const fam of knownFamilies) {
    const re = new RegExp('^' + fam.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&') + '\\b', 'i');
    if (re.test(s)) {
      return fam.charAt(0).toUpperCase() + fam.slice(1);
    }
  }

  // 5. Roman numerals / generation suffixes
  s = s.replace(/\s+(?:[I|V|X]+|B\d|C\d|T\d|[A-L]|I{1,3}|IV|VI{0,3}|IX|X)\b/gi, '');

  // 6. Body styles and trim suffixes
  s = s.replace(/\s+(?:Hatchback|CC|SW|Saloon|Sedan|Van|Coupe|Coupé|Convertible|Cabrio|Cabriolet|Estate|Combi|Variant|Touring|Gran Coupe|Fastback|Spider|Spyder|Pickup|Allroad|Cross|Sportback|Grandtour|Plus|\+)\b/gi, '');

  s = s.trim();
  if (!s) return String(name).trim();

  if (s === s.toUpperCase()) {
    return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
  }
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function getConsolidatedModelsForBrand(brand) {
  const rows = db.prepare(
    'SELECT m.id, m.brand_name, m.model_name, m.production_start, m.production_end, m.years_span, m.total_variants, ' +
    'm.source, m.status, m.image_url, m.image_local_path, m.image_source, m.image_match_name, m.image_credit, m.image_license, ' +
    '(SELECT COUNT(*) FROM vehicle_variants v WHERE v.car_brand=m.brand_name AND v.car_model=m.model_name) AS variant_count, ' +
    '(SELECT COUNT(DISTINCT v.engine_code) FROM vehicle_variants v WHERE v.car_brand=m.brand_name AND v.car_model=m.model_name) AS engine_count ' +
    'FROM models m WHERE brand_name=? ORDER BY model_name'
  ).all(brand);

  const groups = new Map();
  for (const r of rows) {
    const base = getBaseModelName(brand, r.model_name);
    if (!groups.has(base)) groups.set(base, []);
    groups.get(base).push(r);
  }

  const result = [];
  for (const [base, subs] of groups.entries()) {
    const totalVars = subs.reduce((sum, s) => sum + (s.variant_count || s.total_variants || 0), 0);
    const totalEngines = subs.reduce((sum, s) => sum + (s.engine_count || 0), 0);
    const starts = subs.map(s => s.production_start).filter(Boolean);
    const ends = subs.map(s => s.production_end).filter(Boolean);
    const minStart = starts.length ? Math.min(...starts) : null;
    const maxEnd = ends.length ? Math.max(...ends) : null;
    const yearsSpan = (minStart && maxEnd) ? (minStart === maxEnd ? String(minStart) : `${minStart}-${maxEnd}`) : (subs[0].years_span || '');
    const imgRow = subs.find(s => s.image_url) || subs[0];

    result.push({
      id: subs[0].id,
      model_name: base,
      production_start: minStart,
      production_end: maxEnd,
      years_span: yearsSpan,
      total_variants: totalVars,
      variant_count: totalVars,
      engine_count: totalEngines,
      sub_models_count: subs.length,
      sub_models: subs.map(s => s.model_name),
      image_url: imgRow.image_url,
      model_picture_url: '/api/model_picture/' + encodeURIComponent(brand) + '/' + encodeURIComponent(base),
      image_local_path: imgRow.image_local_path,
      image_source: imgRow.image_source,
      image_match_name: imgRow.image_match_name || imgRow.model_name,
      image_credit: imgRow.image_credit,
      image_license: imgRow.image_license
    });
  }

  return result.sort((a, b) => a.model_name.localeCompare(b.model_name, undefined, { numeric: true, sensitivity: 'base' }));
}

function coerceValue(col, raw) {
  if (raw === '' || raw === null || raw === undefined) return null;
  const t = col.type || 'TEXT';
  if (/INT/i.test(t)) {
    const n = Number(String(raw).replace(/\s+/g, ''));
    if (!Number.isFinite(n)) throw new Error(`"${raw}" is not a valid integer`);
    return Math.trunc(n);
  }
  if (/REAL|DOU|FLOA|NUM|DEC/i.test(t)) {
    const n = Number(String(raw).replace(',', '.').replace(/\s+/g, ''));
    if (!Number.isFinite(n)) throw new Error(`"${raw}" is not a valid number`);
    return n;
  }
  return String(raw);
}

function toIntOrNull(v) {
  if (v === null || v === undefined || v === '') return null;
  const n = Number(String(v).replace(/\s+/g, ''));
  return Number.isFinite(n) ? Math.trunc(n) : null;
}

function syncEngineCount(code) {
  if (!code) return;
  db.prepare('UPDATE engines SET count_variants=(SELECT COUNT(*) FROM vehicle_variants WHERE engine_code=?) WHERE engine_code=?').run(code, code);
}

function syncModelCount(brand, model) {
  if (!brand || !model) return;
  db.prepare('UPDATE models SET total_variants=(SELECT COUNT(*) FROM vehicle_variants v WHERE v.car_brand=? AND v.car_model=?) WHERE brand_name=? AND model_name=?').run(brand, model, brand, model);
}

function ensureBrand(name) {
  const row = db.prepare('SELECT id FROM brands WHERE name=?').get(name);
  if (row) return row.id;
  return Number(db.prepare('INSERT INTO brands (name) VALUES (?)').run(name).lastInsertRowid);
}

function ensureModel(brand, model, brandId) {
  const row = db.prepare('SELECT id FROM models WHERE brand_name=? AND model_name=?').get(brand, model);
  if (row) return row.id;
  return Number(db.prepare(
    "INSERT INTO models (brand_id, brand_name, model_name, total_variants, source, status) VALUES (?,?,?,0,'added_missing','added_missing')"
  ).run(brandId, brand, model).lastInsertRowid);
}

// Build per-statement plans for an UPDATE op. Supports engine_code renames with
// a cascade to the child tables. Returns { real, pk, stmts, oldKey, newPk } where
// stmts is [{ sql, params, must }] (must = failing to change = error).
function prepareUpdate(key, rowKey, values) {
  const real = TABLES[key];
  const pk = PRIMARY_KEYS[key];
  const rawCode = 'engine_code' in values ? values.engine_code : null;
  const newCode = rawCode === null || rawCode === undefined ? null : String(rawCode);
  const isRename = key === 'engine' && newCode !== null && newCode !== String(rowKey);

  if (isRename) {
    if (!newCode.trim()) { const e = new Error('Engine code cannot be blank'); e.status = 400; throw e; }
    const dup = db.prepare('SELECT 1 FROM engines WHERE engine_code=?').get(newCode);
    if (dup) { const e = new Error(`Engine code "${newCode}" already exists`); e.status = 409; throw e; }
  }

  const set = [], params = [];
  let codeValue = null;
  for (const c of columns(key)) {
    if (c.name === pk && !isRename) continue; // pk is locked except the rename path
    if (!(c.name in values)) continue;
    let v;
    try { v = coerceValue(c, values[c.name]); } catch (e) { e.status = 400; throw e; }
    if (c.name === pk) codeValue = v; // coerced engine_code for the cascade
    set.push(`"${c.name}"=?`);
    params.push(v);
  }
  if (!set.length) { const e = new Error('no editable values provided'); e.status = 400; throw e; }
  params.push(rowKey);

  const stmts = [{ sql: `UPDATE ${real} SET ${set.join(', ')} WHERE "${pk}"=?`, params, must: true }];
  if (isRename) {
    for (const t of ENGINE_CASCADE) {
      stmts.push({ sql: `UPDATE ${t} SET engine_code=? WHERE engine_code=?`, params: [codeValue, rowKey], must: false });
    }
  }
  return { real, pk, stmts, oldKey: rowKey, newPk: isRename ? codeValue : null };
}

function json(res, obj, status) {
  const body = JSON.stringify(obj);
  res.writeHead(status || 200, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
    'Cache-Control': 'no-store'
  });
  res.end(body);
}

function sendFile(res, isHead) {
  if (!fs.existsSync(DASH_PATH)) return json(res, { error: 'dashboard/index.html missing' }, 500);
  const data = fs.readFileSync(DASH_PATH);
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Length': data.length });
  if (isHead) return res.end();
  res.end(data);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let d = '';
    req.on('data', c => { d += c; if (d.length > 2e6) req.destroy(new Error('body too large')); });
    req.on('end', () => {
      try { resolve(d ? JSON.parse(d) : {}); } catch (e) { reject(new Error('invalid JSON body')); }
    });
    req.on('error', reject);
  });
}

function quoteLike(str) {
  return String(str).replace(/[\\%_]/g, m => '\\' + m);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const p = url.pathname;
  const q = url.searchParams;
  try {
    /* ---- static dashboard ---- */
    if ((req.method === 'GET' || req.method === 'HEAD') && (p === '/' || p === '/index.html' || p === '/dashboard' || p === '/dashboard/')) return sendFile(res, req.method === 'HEAD');

    /* ---- report overview page ---- */
    if (req.method === 'GET' && (p === '/report' || p === '/report.html')) {
      const repFile = path.join(ROOT, 'index.html');
      if (fs.existsSync(repFile)) {
        const data = fs.readFileSync(repFile);
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Length': data.length });
        return res.end(data);
      }
    }

    /* ---- static car images (car_images/*) ---- */
    let m = p.match(/^\/car_images\/(.+)$/);
    if (req.method === 'GET' && m) {
      const name = path.basename(decodeURIComponent(m[1]));
      const file = path.join(ROOT, 'car_images', name);
      if (!name || !fs.existsSync(file)) return json(res, { error: 'image not found' }, 404);
      const data = fs.readFileSync(file);
      const ext = path.extname(name).toLowerCase();
      const ct = ext === '.webp' ? 'image/webp' : ext === '.png' ? 'image/png' : ext === '.jpg' || ext === '.jpeg' ? 'image/jpeg' : 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': ct, 'Content-Length': data.length, 'Cache-Control': 'public, max-age=86400' });
      res.end(data);
      return;
    }

    /* ---- model pictures (model_images/<brand>/<file>) ---- */
    m = p.match(/^\/model_images\/(.+)$/);
    if (req.method === 'GET' && m) {
      const rel = decodeURIComponent(m[1]).split('/').filter(x => x && x !== '..' && x !== '.');
      const file = path.join(ROOT, 'model_images', ...rel);
      if (!rel.length || !file.startsWith(path.join(ROOT, 'model_images')) || !fs.existsSync(file)) {
        return json(res, { error: 'image not found' }, 404);
      }
      const data = fs.readFileSync(file);
      const ext = path.extname(file).toLowerCase();
      const ct = ext === '.webp' ? 'image/webp' : ext === '.png' ? 'image/png'
        : (ext === '.jpg' || ext === '.jpeg') ? 'image/jpeg' : ext === '.gif' ? 'image/gif'
        : 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': ct, 'Content-Length': data.length, 'Cache-Control': 'public, max-age=86400' });
      res.end(data);
      return;
    }

    /* ---- picture proxy + on-disk cache (/img?u=<source url>) ----
       Lets the dashboard show catalogue pictures before step92 has downloaded
       them, avoids hot-link/referer blocking, and keeps every fetched file in
       model_images/_cache so the next load is local. */
    if (req.method === 'GET' && p === '/img') {
      const raw = q.get('u') || '';
      let u;
      try { u = new URL(raw); } catch { return json(res, { error: 'bad url' }, 400); }
      const ALLOWED = new Set([
        'img.7zap.com', '7zap.com',
        'commons.wikimedia.org', 'upload.wikimedia.org',
        'thumb.wikimedia.org', 'en.wikipedia.org'
      ]);
      if (u.protocol !== 'https:' || !ALLOWED.has(u.hostname)) {
        return json(res, { error: 'host not allowed' }, 403);
      }
      const cacheDir = path.join(ROOT, 'model_images', '_cache');
      const key = crypto.createHash('sha1').update(raw).digest('hex');
      const guess = path.extname(u.pathname).toLowerCase().split('?')[0];
      const ext = ['.webp', '.jpg', '.jpeg', '.png', '.gif'].includes(guess) ? guess : '.img';
      const file = path.join(cacheDir, key + ext);
      const TYPES = { '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg',
                      '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.img': 'application/octet-stream' };
      const serve = buf => {
        res.writeHead(200, { 'Content-Type': TYPES[ext], 'Content-Length': buf.length,
                             'Cache-Control': 'public, max-age=604800' });
        res.end(buf);
      };
      if (fs.existsSync(file)) return serve(fs.readFileSync(file));
      try {
        const headers = { 'User-Agent': 'car-database-dashboard/1.0 (local model picture viewer)' };
        if (u.hostname.endsWith('7zap.com')) headers.Referer = 'https://7zap.com/en/';
        const r = await fetch(raw, { headers, redirect: 'follow' });
        if (!r.ok) return json(res, { error: 'upstream ' + r.status }, 502);
        const buf = Buffer.from(await r.arrayBuffer());
        fs.mkdirSync(cacheDir, { recursive: true });
        fs.writeFileSync(file, buf);
        return serve(buf);
      } catch (e) {
        return json(res, { error: 'fetch failed: ' + e.message }, 502);
      }
    }

    /* ---- brand logo (served from database; auto-imported OEM from internet if missing) ---- */
    m = p.match(/^\/api\/brand_logo\/([^/]+)$/);
    if ((req.method === 'GET' || req.method === 'HEAD') && m) {
      const brand = decodeURIComponent(m[1]);
      const logo = await getOrImportBrandLogo(brand, db);
      const buf = Buffer.from(logo.svg || '', 'utf8');
      const etag = '"' + crypto.createHash('md5').update(buf).digest('hex') + '"';
      if (req.headers['if-none-match'] === etag) {
        res.writeHead(304);
        return res.end();
      }
      res.writeHead(200, {
        'Content-Type': logo.contentType || 'image/svg+xml; charset=utf-8',
        'Content-Length': buf.length,
        'Cache-Control': 'no-cache, must-revalidate',
        'ETag': etag
      });
      if (req.method === 'HEAD') return res.end();
      return res.end(buf);
    }

    /* ---- car model picture (served from cache/wikimedia; auto-generated vector card fallback) ---- */
    m = p.match(/^\/api\/model_picture\/([^/]+)\/([^/]+)$/);
    if ((req.method === 'GET' || req.method === 'HEAD') && m) {
      const brand = decodeURIComponent(m[1]);
      const model = decodeURIComponent(m[2]);
      const gen = q.get('gen') || '';
      const pic = await getModelPicture(brand, model, gen, db);
      const buf = pic.buffer;
      const etag = '"' + crypto.createHash('md5').update(buf).digest('hex') + '"';
      if (req.headers['if-none-match'] === etag) {
        res.writeHead(304);
        return res.end();
      }
      res.writeHead(200, {
        'Content-Type': pic.contentType,
        'Content-Length': buf.length,
        'Cache-Control': 'public, max-age=86400',
        'ETag': etag
      });
      if (req.method === 'HEAD') return res.end();
      return res.end(buf);
    }

    /* ---- catalog: brand tiles (7zap-style picture browser with logos) ---- */
    if (req.method === 'GET' && p === '/api/catalog/brands') {
      const rows = db.prepare(
        "SELECT m.brand_name AS name, COUNT(*) AS model_count, " +
        "SUM(CASE WHEN m.image_url IS NOT NULL AND m.image_url<>'' THEN 1 ELSE 0 END) AS with_image, " +
        "SUM(COALESCE(m.total_variants,0)) AS variant_count, " +
        "MIN(m.production_start) AS first_year, MAX(m.production_end) AS last_year " +
        "FROM models m GROUP BY m.brand_name ORDER BY m.brand_name"
      ).all();
      const cover = db.prepare(
        "SELECT brand_name, image_url, image_local_path, image_source FROM models " +
        "WHERE image_url IS NOT NULL AND image_url<>'' " +
        "GROUP BY brand_name HAVING MAX(COALESCE(image_match_score,0))"
      ).all();
      const byBrand = {};
      for (const c of cover) byBrand[c.brand_name] = c;
      for (const r of rows) {
        const c = byBrand[r.name];
        r.image_url = c ? c.image_url : null;
        r.image_local_path = c ? c.image_local_path : null;
        r.image_source = c ? c.image_source : null;
        r.logo_url = '/api/brand_logo/' + encodeURIComponent(r.name) + '?v=2';
      }
      return json(res, rows);
    }

    /* ---- catalog: model cards for one brand ---- */
    m = p.match(/^\/api\/catalog\/brands\/([^/]+)\/models$/);
    if (req.method === 'GET' && m) {
      const brand = decodeURIComponent(m[1]);
      return json(res, getConsolidatedModelsForBrand(brand));
    }

    /* ---- catalog: generations for one model (Brand > Model > Generation) ---- */
    m = p.match(/^\/api\/catalog\/brands\/([^/]+)\/models\/([^/]+)\/generations$/);
    if (req.method === 'GET' && m) {
      const brand = decodeURIComponent(m[1]);
      const model = decodeURIComponent(m[2]);

      const allBrandModels = db.prepare('SELECT * FROM models WHERE brand_name=? OR LOWER(brand_name)=LOWER(?)').all(brand, brand);
      const matchingModels = allBrandModels.filter(r => {
        const base = getBaseModelName(brand, r.model_name);
        return base.toLowerCase() === model.toLowerCase() ||
               r.model_name.toLowerCase() === model.toLowerCase() ||
               r.model_name.toLowerCase().startsWith(model.toLowerCase() + ' ') ||
               r.model_name.toLowerCase().startsWith(model.toLowerCase() + '+');
      });

      let generations = [];

      const ecuGens = db.prepare(
        'SELECT generation, year_range, COUNT(*) AS variant_count FROM ecu_diagnostics ' +
        'WHERE (LOWER(make)=LOWER(?) OR LOWER(make) LIKE LOWER(?) || \'%\') ' +
        'AND (LOWER(model)=LOWER(?) OR LOWER(model) LIKE LOWER(?) || \'%\') ' +
        'GROUP BY generation ORDER BY generation'
      ).all(brand, brand, model, model);

      if (ecuGens && ecuGens.length) {
        for (const eg of ecuGens) {
          const ecus = db.prepare(
            'SELECT DISTINCT ecu_id, ecu_maker, powertrain FROM ecu_diagnostics ' +
            'WHERE (LOWER(make)=LOWER(?) OR LOWER(make) LIKE LOWER(?) || \'%\') AND generation=?'
          ).all(brand, brand, eg.generation);

          generations.push({
            name: eg.generation,
            raw_model_name: model,
            year_range: eg.year_range || '',
            variant_count: eg.variant_count,
            ecu_families: ecus.map(e => e.ecu_id).filter(Boolean),
            ecu_makers: [...new Set(ecus.map(e => e.ecu_maker).filter(Boolean))],
            powertrains: [...new Set(ecus.map(e => e.powertrain).filter(Boolean))],
            image_url: matchingModels[0]?.image_url || null,
            image_local_path: matchingModels[0]?.image_local_path || null,
            image_source: matchingModels[0]?.image_source || null,
            has_ecu_diagnostics: true
          });
        }
      }

      if (matchingModels && matchingModels.length) {
        for (const sub of matchingModels) {
          const vars = db.prepare(
            'SELECT car_year, engine_code, engine_type, fuel, engine_power_hp, ecu_maker, ecu_model ' +
            'FROM vehicle_variants WHERE car_brand=? AND car_model=? ORDER BY car_year'
          ).all(brand, sub.model_name);

          const years = vars.map(v => v.car_year).filter(Boolean);
          const minYear = years.length ? Math.min(...years) : null;
          const maxYear = years.length ? Math.max(...years) : null;
          const span = (minYear && maxYear) ? (minYear === maxYear ? String(minYear) : `${minYear}-${maxYear}`) : (sub.years_span || '');
          const ecus = [...new Set(vars.map(v => v.ecu_model).filter(Boolean))];
          const makers = [...new Set(vars.map(v => v.ecu_maker).filter(Boolean))];
          const fuels = [...new Set(vars.map(v => v.fuel).filter(Boolean))];

          if (!generations.some(g => g.name === sub.model_name)) {
            generations.push({
              name: sub.model_name,
              raw_model_name: sub.model_name,
              year_range: span || sub.years_span || '',
              variant_count: vars.length || sub.total_variants || 0,
              ecu_families: ecus,
              ecu_makers: makers,
              powertrains: fuels,
              image_url: sub.image_url || null,
              image_local_path: sub.image_local_path || null,
              image_source: sub.image_source || null,
              has_ecu_diagnostics: false
            });
          }
        }
      }

      const starts = matchingModels.map(m => m.production_start).filter(Boolean);
      const ends = matchingModels.map(m => m.production_end).filter(Boolean);
      const minS = starts.length ? Math.min(...starts) : null;
      const maxE = ends.length ? Math.max(...ends) : null;
      const mainYearsSpan = (minS && maxE) ? (minS === maxE ? String(minS) : `${minS}-${maxE}`) : (matchingModels[0]?.years_span || '');

      return json(res, {
        model: {
          brand_name: brand,
          model_name: model,
          years_span: mainYearsSpan,
          total_variants: generations.reduce((acc, g) => acc + (g.variant_count || 0), 0)
        },
        generations
      });
    }

    /* ---- catalog: variants for a generation (Brand > Model > Generation > Variant) ---- */
    m = p.match(/^\/api\/catalog\/brands\/([^/]+)\/models\/([^/]+)\/generations\/([^/]+)\/variants$/);
    if (req.method === 'GET' && m) {
      const brand = decodeURIComponent(m[1]);
      const model = decodeURIComponent(m[2]);
      const gen = decodeURIComponent(m[3]);

      // 1. Look in ecu_diagnostics
      const ecuRows = db.prepare(
        'SELECT * FROM ecu_diagnostics ' +
        'WHERE (LOWER(make)=LOWER(?) OR LOWER(make) LIKE LOWER(?) || \'%\') AND generation=? ' +
        'ORDER BY id'
      ).all(brand, brand, gen);

      if (ecuRows && ecuRows.length) {
        const mapped = ecuRows.map(r => {
          const code = r.engine_code ? r.engine_code.trim() : '';
          const eng = code ? (db.prepare('SELECT * FROM engines WHERE engine_code=?').get(code) || null) : null;
          const srv = code ? (db.prepare('SELECT 1 FROM engine_service_specs WHERE engine_code=?').get(code) || null) : null;
          const tech = code ? (db.prepare('SELECT 1 FROM engine_technical_specs WHERE engine_code=?').get(code) || null) : null;

          return {
            id: r.id,
            variant_name: r.variant,
            generation: r.generation,
            engine_code: r.engine_code,
            engine_type: r.variant,
            fuel: r.powertrain,
            power_hp: eng?.power_hp || null,
            power_kw: eng?.power_kw || null,
            displacement_cc: eng?.displacement_cc || null,
            ecu_id: r.ecu_id,
            ecu_maker: r.ecu_maker,
            powertrain: r.powertrain,
            mcu_architecture: r.mcu_architecture,
            obd_protocol: r.obd_protocol,
            programming_method: r.programming_method,
            obd_location: r.obd_location,
            diagnostic_notes: r.diagnostic_notes,
            origin_status: r.origin_status,
            has_service: !!srv,
            has_technical: !!tech,
            has_ecu_diagnostics: true
          };
        });
        return json(res, mapped);
      } else {
        // Fallback: pull from vehicle_variants
        const rows = db.prepare(
          'SELECT v.*, e.displacement_cc, e.power_kw FROM vehicle_variants v ' +
          'LEFT JOIN engines e ON e.engine_code=v.engine_code ' +
          'WHERE v.car_brand=? AND (v.car_model=? OR v.car_model=? OR v.car_model LIKE ? || \' (%\' OR v.car_model LIKE ? || \' %\' OR v.car_model LIKE ? || \'%\') ORDER BY v.car_year, v.engine_power_hp'
        ).all(brand, gen, model, model, model, gen);

        const mapped = rows.map(r => ({
          id: r.id,
          variant_name: `${r.engine_type || 'Variant'} (${r.engine_power_hp ? r.engine_power_hp + ' hp' : (r.car_year || '')})`,
          generation: gen,
          engine_code: r.engine_code,
          year_range: r.car_year ? String(r.car_year) : (r.production_start ? `${r.production_start}-${r.production_end||''}` : ''),
          fuel: r.fuel,
          power_hp: r.engine_power_hp,
          power_kw: r.engine_power_kw,
          displacement_cc: r.displacement_cc,
          ecu_id: r.ecu_model || 'Standard ECU',
          ecu_maker: r.ecu_maker || 'OEM',
          powertrain: r.fuel,
          mcu_architecture: 'OEM Automotive MCU',
          obd_protocol: 'OBD-II / CAN Bus',
          programming_method: 'OBD / Bench',
          obd_location: 'Under dashboard / Fuse compartment',
          diagnostic_notes: `Vehicle variant ID ${r.id}`,
          origin_status: 'Catalog Entry',
          has_service: !!db.prepare('SELECT 1 FROM engine_service_specs WHERE engine_code=?').get(r.engine_code),
          has_technical: !!db.prepare('SELECT 1 FROM engine_technical_specs WHERE engine_code=?').get(r.engine_code),
          has_ecu_diagnostics: false
        }));
        return json(res, mapped);
      }
    }

    /* ---- variant detailed information (ECU + Service + Technical Diagnostics) ---- */
    if (req.method === 'GET' && p === '/api/variant_details') {
      let code = (q.get('engine_code') || '').trim();
      const ecuDiagId = q.get('ecu_diag_id') || q.get('id');
      const make = (q.get('make') || q.get('brand') || '').trim();
      const model = (q.get('model') || '').trim();
      const gen = (q.get('generation') || '').trim();

      let ecuDiag = null;
      if (ecuDiagId) {
        ecuDiag = db.prepare('SELECT * FROM ecu_diagnostics WHERE id=?').get(ecuDiagId);
      }
      if (!ecuDiag && code) {
        ecuDiag = db.prepare('SELECT * FROM ecu_diagnostics WHERE engine_code=? LIMIT 1').get(code);
      }
      if (!ecuDiag && make && gen) {
        ecuDiag = db.prepare('SELECT * FROM ecu_diagnostics WHERE (LOWER(make)=LOWER(?) OR LOWER(make) LIKE LOWER(?) || \'%\') AND generation=? LIMIT 1').get(make, make, gen);
      }
      if (!ecuDiag && make && model) {
        ecuDiag = db.prepare('SELECT * FROM ecu_diagnostics WHERE (LOWER(make)=LOWER(?) OR LOWER(make) LIKE LOWER(?) || \'%\') AND (LOWER(model)=LOWER(?) OR LOWER(model) LIKE LOWER(?) || \'%\') LIMIT 1').get(make, make, model, model);
      }

      // If code was not provided, derive from ecuDiag or vehicle_variants or models
      if (!code && ecuDiag?.engine_code) {
        code = ecuDiag.engine_code;
      }
      if (!code && make && model) {
        const vRow = db.prepare('SELECT engine_code FROM vehicle_variants WHERE (LOWER(car_brand)=LOWER(?) OR LOWER(car_brand) LIKE LOWER(?) || \'%\') AND (LOWER(car_model)=LOWER(?) OR LOWER(car_model) LIKE LOWER(?) || \'%\') AND engine_code IS NOT NULL AND engine_code<>\'\' LIMIT 1').get(make, make, model, model);
        if (vRow) code = vRow.engine_code;
      }
      if (!code && make) {
        const vRow = db.prepare('SELECT engine_code FROM vehicle_variants WHERE (LOWER(car_brand)=LOWER(?) OR LOWER(car_brand) LIKE LOWER(?) || \'%\') AND engine_code IS NOT NULL AND engine_code<>\'\' LIMIT 1').get(make, make);
        if (vRow) code = vRow.engine_code;
      }
      if (!code) {
        const anyEng = db.prepare('SELECT engine_code FROM engines LIMIT 1').get();
        if (anyEng) code = anyEng.engine_code;
      }

      let eng = null;
      if (code) {
        eng = db.prepare('SELECT * FROM engines WHERE engine_code=?').get(code)
          || db.prepare('SELECT * FROM engines WHERE engine_code LIKE ? LIMIT 1').get(code + '%')
          || null;
      }
      if (!eng && ecuDiag?.engine_code) {
        eng = db.prepare('SELECT * FROM engines WHERE engine_code=?').get(ecuDiag.engine_code)
          || db.prepare('SELECT * FROM engines WHERE engine_code LIKE ? LIMIT 1').get(ecuDiag.engine_code + '%')
          || null;
      }

      const resolvedCode = eng?.engine_code || code || ecuDiag?.engine_code || '';

      let service = null;
      let technical = null;
      let variants = [];

      if (resolvedCode) {
        service = db.prepare('SELECT * FROM engine_service_specs WHERE engine_code=?').get(resolvedCode)
          || db.prepare('SELECT * FROM engine_service_specs WHERE engine_code LIKE ? LIMIT 1').get(resolvedCode + '%')
          || null;
        technical = db.prepare('SELECT * FROM engine_technical_specs WHERE engine_code=?').get(resolvedCode)
          || db.prepare('SELECT * FROM engine_technical_specs WHERE engine_code LIKE ? LIMIT 1').get(resolvedCode + '%')
          || null;
        variants = db.prepare('SELECT * FROM vehicle_variants WHERE engine_code=?').all(resolvedCode);
        if (!variants || !variants.length) {
          variants = db.prepare('SELECT * FROM vehicle_variants WHERE engine_code LIKE ? LIMIT 50').all(resolvedCode + '%') || [];
        }
      }

      // If service or technical still missing, try by brand & model fallback
      if (!service && make && model) {
        service = db.prepare('SELECT * FROM engine_service_specs WHERE (LOWER(brand_example)=LOWER(?) OR LOWER(brand_example) LIKE LOWER(?) || \'%\') AND (LOWER(model_example)=LOWER(?) OR LOWER(model_example) LIKE LOWER(?) || \'%\') LIMIT 1').get(make, make, model, model) || null;
      }
      if (!service && make) {
        service = db.prepare('SELECT * FROM engine_service_specs WHERE (LOWER(brand_example)=LOWER(?) OR LOWER(brand_example) LIKE LOWER(?) || \'%\') LIMIT 1').get(make, make) || null;
      }
      if (!service) {
        service = db.prepare('SELECT * FROM engine_service_specs LIMIT 1').get() || null;
      }
      if (service && service.engine_code !== resolvedCode && resolvedCode) {
        // Clone with current engine code so user can immediately edit and save for this engine
        service = { ...service, engine_code: resolvedCode, count_variants: 1 };
      }

      if (!technical && make && model) {
        technical = db.prepare('SELECT * FROM engine_technical_specs WHERE (LOWER(brand_example)=LOWER(?) OR LOWER(brand_example) LIKE LOWER(?) || \'%\') AND (LOWER(model_example)=LOWER(?) OR LOWER(model_example) LIKE LOWER(?) || \'%\') LIMIT 1').get(make, make, model, model) || null;
      }
      if (!technical && make) {
        technical = db.prepare('SELECT * FROM engine_technical_specs WHERE (LOWER(brand_example)=LOWER(?) OR LOWER(brand_example) LIKE LOWER(?) || \'%\') LIMIT 1').get(make, make) || null;
      }
      if (!technical) {
        technical = db.prepare('SELECT * FROM engine_technical_specs LIMIT 1').get() || null;
      }
      if (technical && technical.engine_code !== resolvedCode && resolvedCode) {
        technical = { ...technical, engine_code: resolvedCode };
      }

      if (!eng && resolvedCode) {
        eng = {
          engine_code: resolvedCode,
          engine_type: service?.engine_type || ecuDiag?.variant || 'Standard Engine',
          fuel: service?.fuel || ecuDiag?.powertrain || 'Petrol',
          displacement_cc: service?.displacement_cc || 1400,
          power_hp: service?.power_hp || 100,
          power_kw: service?.power_kw || 74,
          cylinders: service?.cylinders || 4,
          ecu_maker: ecuDiag?.ecu_maker || 'OEM',
          ecu_model: ecuDiag?.ecu_id || 'Standard ECU',
          brand_example: make || service?.brand_example || 'Vehicle Brand',
          model_example: model || service?.model_example || 'Car Model',
          year_example: 2020,
          count_variants: variants.length || 1,
          data_confidence: 'ESTIMATE'
        };
      }

      // Model info for pictures & years
      let modelInfo = null;
      if (make && model) {
        modelInfo = db.prepare('SELECT * FROM models WHERE (LOWER(brand_name)=LOWER(?) OR LOWER(brand_name) LIKE LOWER(?) || \'%\') AND (LOWER(model_name)=LOWER(?) OR LOWER(model_name) LIKE LOWER(?) || \'%\') LIMIT 1').get(make, make, model, model) || null;
      }

      // If ecuDiag is missing, synthesize a rich default object so it is never null
      if (!ecuDiag) {
        const vFirst = variants[0] || {};
        ecuDiag = {
          id: null,
          make: make || eng?.brand_example || vFirst.car_brand || 'Standard Make',
          model: model || eng?.model_example || vFirst.car_model || 'Standard Model',
          generation: gen || (modelInfo ? `${modelInfo.model_name} (${modelInfo.years_span || 'Series'})` : 'Standard Series'),
          variant: eng?.engine_type || vFirst.engine_type || (resolvedCode ? `Engine ${resolvedCode}` : 'Standard Variant'),
          year_range: modelInfo?.years_span || (vFirst.car_year ? String(vFirst.car_year) : ''),
          engine_code: resolvedCode,
          ecu_id: eng?.ecu_model || vFirst.ecu_model || 'OEM Spec ECU',
          ecu_maker: eng?.ecu_maker || vFirst.ecu_maker || 'OEM',
          powertrain: eng?.fuel || vFirst.fuel || 'Petrol',
          mcu_architecture: 'Automotive Engine MCU',
          obd_protocol: 'OBD-II / CAN Bus',
          programming_method: 'OBD / Bench Programmer',
          obd_location: 'Under dashboard / Diagnostic port',
          diagnostic_notes: `Standard diagnostic profile for ${resolvedCode}`,
          origin_status: 'Catalog Entry'
        };
      }

      return json(res, {
        ecu_diagnostics: ecuDiag,
        engine: eng,
        service: service,
        technical: technical,
        variants: variants,
        model_info: modelInfo,
        resolved_code: resolvedCode
      });
    }

    /* ---- browse all specs table (service or technical) with search & pagination ---- */
    if (req.method === 'GET' && p === '/api/specs_browse') {
      const type = q.get('type') === 'technical' ? 'technical' : (q.get('type') === 'ecu' ? 'ecu' : (q.get('type') === 'engine' ? 'engine' : 'service'));
      const table = TABLES[type] || 'engine_service_specs';
      const term = (q.get('q') || '').trim();
      const page = Math.max(1, parseInt(q.get('page'), 10) || 1);
      const limit = Math.min(100, Math.max(10, parseInt(q.get('limit'), 10) || 25));
      const offset = (page - 1) * limit;

      let where = '';
      const params = [];
      if (term) {
        if (type === 'ecu') {
          where = 'WHERE make LIKE ? OR model LIKE ? OR generation LIKE ? OR variant LIKE ? OR engine_code LIKE ? OR ecu_id LIKE ?';
          const t = `%${term}%`;
          params.push(t, t, t, t, t, t);
        } else {
          where = 'WHERE engine_code LIKE ? OR engine_type LIKE ? OR brand_example LIKE ? OR model_example LIKE ?';
          const t = `%${term}%`;
          params.push(t, t, t, t);
        }
      }

      const total = db.prepare(`SELECT COUNT(*) as c FROM ${table} ${where}`).get(...params).c;
      const orderCol = type === 'ecu' ? 'id' : 'engine_code';
      const rows = db.prepare(`SELECT * FROM ${table} ${where} ORDER BY ${orderCol} LIMIT ? OFFSET ?`).all(...params, limit, offset);

      return json(res, {
        type,
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
        rows
      });
    }

    /* ---- update model picture URL ---- */
    if (req.method === 'POST' && p === '/api/update_model_image') {
      const body = await readBody(req);
      const brand = body.brand ? String(body.brand).trim() : '';
      const model = body.model ? String(body.model).trim() : '';
      const url = body.image_url !== undefined ? String(body.image_url).trim() : '';

      if (!brand || !model) return json(res, { error: 'brand and model are required' }, 400);

      db.prepare('UPDATE models SET image_url=?, image_source=\'custom\' WHERE brand_name=? AND model_name=?').run(url, brand, model);
      return json(res, { ok: true, brand, model, image_url: url });
    }

    /* ---- catalog: picture coverage summary ---- */
    if (req.method === 'GET' && p === '/api/catalog/stats') {
      const row = db.prepare(
        "SELECT COUNT(*) AS models, " +
        "SUM(CASE WHEN image_url IS NOT NULL AND image_url<>'' THEN 1 ELSE 0 END) AS with_image, " +
        "SUM(CASE WHEN image_local_path IS NOT NULL AND image_local_path<>'' THEN 1 ELSE 0 END) AS downloaded, " +
        "COUNT(DISTINCT brand_name) AS brands FROM models"
      ).get();
      const bySource = db.prepare(
        "SELECT COALESCE(image_source,'?') AS source, COUNT(*) AS n FROM models " +
        "WHERE image_url IS NOT NULL AND image_url<>'' GROUP BY 1 ORDER BY n DESC"
      ).all();
      return json(res, { ...row, by_source: bySource });
    }

    /* ---- brands ---- */
    if (req.method === 'GET' && p === '/api/brands') {
      const rows = db.prepare(
        'SELECT b.name, (SELECT COUNT(*) FROM models m WHERE m.brand_id=b.id) AS model_count ' +
        'FROM brands b ORDER BY b.name'
      ).all();
      return json(res, rows);
    }

    /* ---- models for a brand ---- */
    m = p.match(/^\/api\/brands\/([^/]+)\/models$/);
    if (req.method === 'GET' && m) {
      const brand = decodeURIComponent(m[1]);
      return json(res, getConsolidatedModelsForBrand(brand));
    }

    /* ---- engine types for a model (from vehicle_variants) ---- */
    m = req.url !== null && p.match(/^\/api\/brands\/([^/]+)\/models\/([^/]+)\/engine_types$/);
    if (req.method === 'GET' && m) {
      const brand = decodeURIComponent(m[1]);
      const model = decodeURIComponent(m[2]);
      const rows = db.prepare(
        'SELECT engine_type, COUNT(*) AS n, COUNT(DISTINCT engine_code) AS codes ' +
        'FROM vehicle_variants WHERE car_brand=? AND car_model=? ' +
        "AND engine_type IS NOT NULL AND engine_type<>'' GROUP BY engine_type ORDER BY engine_type"
      ).all(brand, model);
      return json(res, rows);
    }

    /* ---- engine codes for a model (optionally filtered by engine_type) ---- */
    m = p.match(/^\/api\/brands\/([^/]+)\/models\/([^/]+)\/codes$/);
    if (req.method === 'GET' && m) {
      const brand = decodeURIComponent(m[1]);
      const model = decodeURIComponent(m[2]);
      const etype = q.get('engine_type');
      let rows;
      if (etype) {
        rows = db.prepare(
          'SELECT engine_code, engine_type, fuel, engine_power_hp, COUNT(*) AS n ' +
          'FROM vehicle_variants WHERE car_brand=? AND car_model=? AND engine_type=? ' +
          "AND engine_code IS NOT NULL AND engine_code<>'' GROUP BY engine_code ORDER BY engine_code"
        ).all(brand, model, etype);
      } else {
        rows = db.prepare(
          'SELECT engine_code, engine_type, fuel, engine_power_hp, COUNT(*) AS n ' +
          'FROM vehicle_variants WHERE car_brand=? AND car_model=? ' +
          "AND engine_code IS NOT NULL AND engine_code<>'' GROUP BY engine_code ORDER BY engine_code"
        ).all(brand, model);
      }
      return json(res, rows);
    }

    /* ---- all engine codes (for quick search) ---- */
    if (req.method === 'GET' && p === '/api/codes') {
      const rows = db.prepare('SELECT engine_code, engine_type, fuel, power_hp, displacement_cc FROM engines ORDER BY engine_code').all();
      return json(res, rows);
    }

    /* ---- search ---- */
    if (req.method === 'GET' && p === '/api/search') {
      const term = quoteLike(q.get('q') || '');
      if (!term) return json(res, []);
      const esc = 'escape \'\\\'';
      const rows = db.prepare(
        'SELECT engine_code, engine_type, fuel, displacement_cc, power_hp, model_example, brand_example ' +
        'FROM engines WHERE engine_code LIKE ? ' + esc + ' OR engine_type LIKE ? ' + esc +
        ' OR model_example LIKE ? ' + esc + ' ORDER BY engine_code LIMIT 80'
      ).all('%' + term + '%', '%' + term + '%', '%' + term + '%');
      return json(res, rows);
    }

    /* ---- full engine detail ---- */
    m = p.match(/^\/api\/engine\/(.+)$/);
    if (req.method === 'GET' && m) {
      const code = decodeURIComponent(m[1]);
      const eng = db.prepare('SELECT * FROM engines WHERE engine_code=?').get(code) || null;
      if (!eng) return json(res, { error: 'Engine code not found' }, 404);
      const service = db.prepare('SELECT * FROM engine_service_specs WHERE engine_code=?').get(code) || null;
      const technical = db.prepare('SELECT * FROM engine_technical_specs WHERE engine_code=?').get(code) || null;
      const variants = db.prepare(
        'SELECT * FROM vehicle_variants WHERE engine_code=? ORDER BY car_brand, car_model, car_year'
      ).all(code);
      return json(res, { engine: eng, service, technical, variants });
    }

    /* ---- column metadata ---- */
    m = p.match(/^\/api\/columns\/(\w+)$/);
    if (req.method === 'GET' && m) {
      const key = m[1];
      if (!(key in TABLES)) return json(res, { error: 'unknown table key' }, 400);
      return json(res, { table: TABLES[key], pk: PRIMARY_KEYS[key], columns: columns(key) });
    }

    /* ---- distinct values for a column (datalist suggestions) ---- */
    if (req.method === 'GET' && p === '/api/distinct') {
      const key = q.get('table');
      const col = q.get('col');
      if (!(key && key in TABLES)) return json(res, { error: 'unknown table' }, 400);
      const cdef = columns(key).find(c => c.name === col);
      if (!cdef) return json(res, { error: 'unknown column' }, 400);
      const rows = db.prepare(
        `SELECT "${col}" AS v, COUNT(*) AS n FROM ${TABLES[key]} ` +
        `WHERE "${col}" IS NOT NULL AND "${col}"<>'' GROUP BY "${col}" ORDER BY n DESC, v LIMIT 300`
      ).all();
      return json(res, rows.map(r => r.v).filter(Boolean));
    }

    /* ---- update a row ---- */
    if (req.method === 'POST' && p === '/api/update') {
      const body = await readBody(req);
      const key = String(body.table || '');
      if (!(key in TABLES)) return json(res, { error: 'unknown table' }, 400);
      const rowKey = body.rowKey;
      const values = (body.values && typeof body.values === 'object') ? body.values : null;
      if (rowKey === undefined || rowKey === null || !values) {
        return json(res, { error: 'rowKey and values are required' }, 400);
      }
      try {
        const u = prepareUpdate(key, rowKey, values);
        db.exec('BEGIN');
        if (u.newPk !== null) db.exec('PRAGMA defer_foreign_keys = ON');
        for (const st of u.stmts) {
          const r = db.prepare(st.sql).run(...st.params);
          if (st.must && !r.changes) throw new Error('no row updated for ' + u.real + ' key ' + rowKey);
        }
        db.exec('COMMIT');
        const newKey = u.newPk !== null ? u.newPk : rowKey;
        const row = db.prepare(`SELECT * FROM ${u.real} WHERE "${u.pk}"=?`).get(newKey);
        return json(res, { ok: true, row, newPk: u.newPk });
      } catch (e) {
        try { db.exec('ROLLBACK'); } catch (x) { /* no open transaction */ }
        return json(res, { error: e.message }, e.status || 500);
      }
    }

    /* ---- batch update (all-or-nothing transaction) ---- */
    if (req.method === 'POST' && p === '/api/update_batch') {
      const body = await readBody(req);
      const ops = body.ops;
      if (!Array.isArray(ops) || !ops.length) return json(res, { error: 'ops array required' }, 400);
      if (ops.length > 500) return json(res, { error: 'too many ops (max 500)' }, 400);
      const stmts = [];
      try {
        for (const op of ops) {
          const key = String(op.table || '');
          if (!(key in TABLES)) { const e = new Error('unknown table: ' + key); e.status = 400; throw e; }
          const rowKey = op.rowKey;
          const values = (op.values && typeof op.values === 'object') ? op.values : null;
          if (rowKey === undefined || rowKey === null || !values) {
            const e = new Error('missing rowKey or values for ' + key); e.status = 400; throw e;
          }
          stmts.push(prepareUpdate(key, rowKey, values));
        }
        db.exec('BEGIN');
        const haveRename = stmts.some(u => u.newPk !== null);
        if (haveRename) db.exec('PRAGMA defer_foreign_keys = ON');
        const map = {}; stmts.filter(u => u.newPk !== null).forEach(u => { map[String(u.oldKey)] = String(u.newPk); });
        const ordered = [...stmts.filter(u => u.newPk !== null), ...stmts.filter(u => u.newPk === null)];
        for (const u of ordered) {
          for (const st of u.stmts) {
            let p = st.params;
            if (u.newPk === null && haveRename) {
              p = st.params.slice();
              const last = p.length - 1;
              if (u.real === 'engine_service_specs' || u.real === 'engine_technical_specs') {
                if (map[String(p[last])]) p[last] = map[String(p[last])];
              }
              for (let j = 0; j < last; j++) if (map[String(p[j])]) p[j] = map[String(p[j])];
            }
            const r = db.prepare(st.sql).run(...p);
            if (st.must && !r.changes) throw new Error('no row updated for ' + u.real + ' key ' + u.oldKey);
          }
        }
        db.exec('COMMIT');
        const renames = stmts.filter(u => u.newPk !== null).map(u => ({ from: u.oldKey, to: u.newPk }));
        return json(res, { ok: true, saved: ops.length, renames });
      } catch (e) {
        try { db.exec('ROLLBACK'); } catch (x) { /* already closed / no transaction */ }
        return json(res, { error: 'batch rolled back: ' + e.message }, e.status || 500);
      }
    }

    /* ---- add engine code (+ optional vehicle variant) ---- */
    if (req.method === 'POST' && p === '/api/add_engine') {
      const body = await readBody(req);
      const code = (body.engine_code !== undefined && body.engine_code !== null) ? String(body.engine_code).trim() : '';
      if (!code) return json(res, { error: 'engine_code is required' }, 400);
      const brand = body.brand ? String(body.brand).trim() : '';
      const model = body.model ? String(body.model).trim() : '';
      const etype = body.engine_type ? String(body.engine_type).trim() : '';
      const fuel = body.fuel ? String(body.fuel).trim() : '';
      try {
        const exists = db.prepare('SELECT 1 FROM engines WHERE engine_code=?').get(code);
        if (exists) {
          if (!brand || !model) return json(res, { ok: true, added: 'none', message: 'engine code already exists' });
          const r = db.prepare(
            'INSERT INTO vehicle_variants (car_brand, car_model, engine_code, engine_type, fuel) VALUES (?,?,?,?,?)'
          ).run(brand, model, code, etype || null, fuel || null);
          syncEngineCount(code);
          syncModelCount(brand, model);
          return json(res, { ok: true, added: 'variant', variantId: Number(r.lastInsertRowid) });
        }
        db.exec('BEGIN');
        try {
          db.prepare(
            'INSERT INTO engines (engine_code, engine_type, fuel, brand_example, model_example, count_variants) VALUES (?,?,?,?,?,0)'
          ).run(code, etype || null, fuel || null, brand || null, model || null);
          db.prepare('INSERT INTO engine_service_specs (engine_code) VALUES (?)').run(code);
          db.prepare('INSERT INTO engine_technical_specs (engine_code) VALUES (?)').run(code);
          let variantId = null;
          if (brand && model) {
            const r = db.prepare(
              'INSERT INTO vehicle_variants (car_brand, car_model, engine_code, engine_type, fuel) VALUES (?,?,?,?,?)'
            ).run(brand, model, code, etype || null, fuel || null);
            variantId = Number(r.lastInsertRowid);
            syncEngineCount(code);
            syncModelCount(brand, model);
          }
          db.exec('COMMIT');
          return json(res, { ok: true, added: 'engine', variantId });
        } catch (e) {
          try { db.exec('ROLLBACK'); } catch (x) { /* no open transaction */ }
          throw e;
        }
      } catch (e) {
        return json(res, { error: e.message }, e.status || 500);
      }
    }

    /* ---- add a brand ---- */
    if (req.method === 'POST' && p === '/api/add_brand') {
      const body = await readBody(req);
      const name = (body.name !== undefined && body.name !== null) ? String(body.name).trim() : '';
      if (!name) return json(res, { error: 'brand name is required' }, 400);
      const dup = db.prepare('SELECT 1 FROM brands WHERE name=?').get(name);
      if (dup) return json(res, { ok: true, added: 'exists', id: null });
      try {
        const r = db.prepare('INSERT INTO brands (name) VALUES (?)').run(name);
        return json(res, { ok: true, added: 'created', id: Number(r.lastInsertRowid) });
      } catch (e) {
        return json(res, { error: e.message }, e.status || 500);
      }
    }

    /* ---- add a model under an existing brand ---- */
    if (req.method === 'POST' && p === '/api/add_model') {
      const body = await readBody(req);
      const brand = (body.brand !== undefined && body.brand !== null) ? String(body.brand).trim() : '';
      const model = (body.model !== undefined && body.model !== null) ? String(body.model).trim() : '';
      if (!brand || !model) return json(res, { error: 'brand and model are required' }, 400);
      const b = db.prepare('SELECT id FROM brands WHERE name=?').get(brand);
      if (!b) return json(res, { error: `brand "${brand}" not found — add the brand first` }, 400);
      const dup = db.prepare('SELECT 1 FROM models WHERE brand_name=? AND model_name=?').get(brand, model);
      if (dup) return json(res, { ok: true, added: 'exists', id: null });
      try {
        const r = db.prepare(
          "INSERT INTO models (brand_id, brand_name, model_name, total_variants, source, status) VALUES (?,?,?,0,'added_missing','added_missing')"
        ).run(b.id, brand, model);
        return json(res, { ok: true, added: 'created', id: Number(r.lastInsertRowid) });
      } catch (e) {
        return json(res, { error: e.message }, e.status || 500);
      }
    }

    /* ---- delete a model (and all its vehicle variants) ---- */
    if (req.method === 'POST' && p === '/api/delete_model') {
      const body = await readBody(req);
      const brand = (body.brand !== undefined && body.brand !== null) ? String(body.brand).trim() : '';
      const model = (body.model !== undefined && body.model !== null) ? String(body.model).trim() : '';
      const id = body.id !== undefined && body.id !== null && body.id !== '' ? Number(body.id) : null;
      if (!brand && !model && !id) return json(res, { error: 'model (brand+model or id) is required' }, 400);
      try {
        let row;
        if (id) row = db.prepare('SELECT id, brand_name, model_name FROM models WHERE id=?').get(id);
        else row = db.prepare('SELECT id, brand_name, model_name FROM models WHERE brand_name=? AND model_name=?').get(brand, model);
        if (!row) return json(res, { error: 'model not found' }, 404);
        db.exec('BEGIN');
        try {
          const codes = db.prepare(
            'SELECT DISTINCT engine_code FROM vehicle_variants WHERE car_brand=? AND car_model=? AND engine_code IS NOT NULL'
          ).all(row.brand_name, row.model_name).map(r2 => r2.engine_code);
          const del = db.prepare('DELETE FROM vehicle_variants WHERE car_brand=? AND car_model=?').run(row.brand_name, row.model_name);
          db.prepare('DELETE FROM models WHERE id=?').run(row.id);
          for (const c of codes) syncEngineCount(c);
          db.exec('COMMIT');
          return json(res, { ok: true, deletedVariants: del.changes, id: row.id });
        } catch (e) {
          try { db.exec('ROLLBACK'); } catch (x) { /* no open transaction */ }
          throw e;
        }
      } catch (e) {
        return json(res, { error: e.message }, e.status || 500);
      }
    }

    /* ---- add a car (vehicle variant) ---- */
    if (req.method === 'POST' && p === '/api/add_variant') {
      const body = await readBody(req);
      const brand = (body.car_brand !== undefined && body.car_brand !== null) ? String(body.car_brand).trim() : '';
      const model = (body.car_model !== undefined && body.car_model !== null) ? String(body.car_model).trim() : '';
      if (!brand || !model) return json(res, { error: 'car_brand and car_model are required' }, 400);
      const code = (body.engine_code !== undefined && body.engine_code !== null) ? String(body.engine_code).trim() : '';
      const etype = body.engine_type ? String(body.engine_type).trim() : '';
      const fuel = body.fuel ? String(body.fuel).trim() : '';
      const year = toIntOrNull(body.car_year);
      const power = toIntOrNull(body.engine_power_hp);
      try {
        db.exec('BEGIN');
        try {
          const brandId = ensureBrand(brand);
          ensureModel(brand, model, brandId);
          let engineCreated = false;
          if (code) {
            const ex = db.prepare('SELECT 1 FROM engines WHERE engine_code=?').get(code);
            if (!ex) {
              db.prepare(
                'INSERT INTO engines (engine_code, engine_type, fuel, brand_example, model_example, count_variants) VALUES (?,?,?,?,?,0)'
              ).run(code, etype || null, fuel || null, brand, model);
              db.prepare('INSERT INTO engine_service_specs (engine_code) VALUES (?)').run(code);
              db.prepare('INSERT INTO engine_technical_specs (engine_code) VALUES (?)').run(code);
              engineCreated = true;
            }
          }
          const r = db.prepare(
            'INSERT INTO vehicle_variants (car_brand, car_model, car_year, fuel, engine_power_hp, engine_type, engine_code) VALUES (?,?,?,?,?,?,?)'
          ).run(brand, model, year, fuel || null, power, etype || null, code || null);
          if (code) syncEngineCount(code);
          syncModelCount(brand, model);
          db.exec('COMMIT');
          return json(res, { ok: true, id: Number(r.lastInsertRowid), engineCreated, engine_code: code || null });
        } catch (e) {
          try { db.exec('ROLLBACK'); } catch (x) { /* no open transaction */ }
          throw e;
        }
      } catch (e) {
        return json(res, { error: e.message }, e.status || 500);
      }
    }

    /* ---- delete a car (vehicle variant) ---- */
    if (req.method === 'POST' && p === '/api/delete_variant') {
      const body = await readBody(req);
      const id = body.id !== undefined && body.id !== null && body.id !== '' ? Number(body.id) : null;
      if (!id || !Number.isFinite(id)) return json(res, { error: 'variant id is required' }, 400);
      try {
        const row = db.prepare('SELECT car_brand, car_model, engine_code FROM vehicle_variants WHERE id=?').get(id);
        if (!row) return json(res, { error: 'variant not found' }, 404);
        db.exec('BEGIN');
        try {
          db.prepare('DELETE FROM vehicle_variants WHERE id=?').run(id);
          syncEngineCount(row.engine_code);
          syncModelCount(row.car_brand, row.car_model);
          db.exec('COMMIT');
          return json(res, { ok: true, id });
        } catch (e) {
          try { db.exec('ROLLBACK'); } catch (x) { /* no open transaction */ }
          throw e;
        }
      } catch (e) {
        return json(res, { error: e.message }, e.status || 500);
      }
    }

    /* ---- manual backup ---- */
    if (req.method === 'GET' && p === '/api/backup') {
      const stamp = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19);
      const file = path.join(BACKUP_DIR, `manual_${stamp}.db`);
      try {
        fs.copyFileSync(DB_PATH, file);
        return json(res, { ok: true, file });
      } catch (e) {
        return json(res, { error: 'backup failed: ' + e.message }, 500);
      }
    }

    /* ---- open backups folder (helper for the UI) ---- */
    if (req.method === 'GET' && p === '/api/openbackups') {
      try { require('child_process').execSync(`explorer "${BACKUP_DIR.replace(/\//g, '\\')}"`, { stdio: 'ignore' }); }
      catch (e) { /* explorer windows often exit nonzero; ignore */ }
      return json(res, { ok: true, dir: BACKUP_DIR });
    }

    return json(res, { error: 'not found: ' + req.method + ' ' + p }, 404);
  } catch (e) {
    return json(res, { error: e && e.message ? e.message : 'server error' }, 500);
  }
});

server.listen(PORT, HOST, () => {
  console.log('Car database dashboard running at  http://localhost:' + PORT);
  console.log('Database: ' + DB_PATH);
  console.log('Backups:  ' + BACKUP_DIR);
});