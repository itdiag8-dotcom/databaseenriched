'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');
const { DatabaseSync } = require('node:sqlite');

const ROOT = __dirname;
const DB_PATH = path.join(ROOT, 'car_database.db');
const DASH_PATH = path.join(ROOT, 'dashboard', 'index.html');
const BACKUP_DIR = path.join(ROOT, 'backups');
const PORT = Number(process.env.PORT || 3000);

fs.mkdirSync(BACKUP_DIR, { recursive: true });
const today = new Date().toISOString().slice(0, 10);
const dailyBackup = path.join(BACKUP_DIR, `car_database_backup_${today}.db`);
try {
  if (!fs.existsSync(dailyBackup)) fs.copyFileSync(DB_PATH, dailyBackup);
} catch (e) {
  console.error('Daily backup failed:', e.message);
}

const db = new DatabaseSync(DB_PATH);

const TABLES = {
  model: 'models',
  engine: 'engines',
  service: 'engine_service_specs',
  technical: 'engine_technical_specs',
  variants: 'vehicle_variants'
};
const PRIMARY_KEYS = {
  model: 'id',
  engine: 'engine_code',
  service: 'engine_code',
  technical: 'engine_code',
  variants: 'id'
};
const PK_EDITABLE = { engine: 1 }; // only engines.engine_code may be renamed
const ENGINE_CASCADE = ['engine_service_specs', 'engine_technical_specs', 'vehicle_variants'];
const ETHEREAL = new Set(['model']); // tables whose pk is not an engine_code

const COLUMN_CACHE = {};
function columns(key) {
  if (!COLUMN_CACHE[key]) {
    COLUMN_CACHE[key] = db.prepare(`PRAGMA table_info(${TABLES[key]})`).all().map(c => ({
      name: c.name, type: c.type || 'TEXT', notnull: !!c.notnull, pk: !!c.pk
    }));
  }
  return COLUMN_CACHE[key];
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

function sendFile(res) {
  if (!fs.existsSync(DASH_PATH)) return json(res, { error: 'dashboard/index.html missing' }, 500);
  const data = fs.readFileSync(DASH_PATH);
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Length': data.length });
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
    if (req.method === 'GET' && (p === '/' || p === '/index.html')) return sendFile(res);

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
      const rows = db.prepare(
        'SELECT id, model_name, production_start, production_end, years_span, total_variants, source, status, ' +
        '(SELECT COUNT(*) FROM vehicle_variants v WHERE v.car_brand=m.brand_name AND v.car_model=m.model_name) AS variant_count ' +
        'FROM models m WHERE brand_name=? ORDER BY model_name'
      ).all(brand);
      return json(res, rows);
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

server.listen(PORT, '127.0.0.1', () => {
  console.log('Car database dashboard running at  http://localhost:' + PORT);
  console.log('Database: ' + DB_PATH);
  console.log('Backups:  ' + BACKUP_DIR);
});