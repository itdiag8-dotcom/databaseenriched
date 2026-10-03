const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Picture sources. server.js serves /model_images/* out of this folder (ROOT = __dirname),
// so that is the primary location; the repo-root folder is kept as a fallback because the
// older download pipeline wrote there.
const ROOT = __dirname;
const LEGACY_ROOT = path.join(__dirname, '..');
const IMAGE_ROOTS = [
  path.join(ROOT, 'model_images'),
  path.join(LEGACY_ROOT, 'model_images')
];
const CACHE_DIRS = IMAGE_ROOTS.map(r => path.join(r, '_cache'));

for (const dir of CACHE_DIRS) fs.mkdirSync(dir, { recursive: true });

function generateCarModelSVG(brand, model, gen) {
  const bEsc = String(brand || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const mEsc = String(model || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const gEsc = gen ? String(gen).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';

  const mLower = (model || '').toLowerCase();
  let bodyPath = "M15,48 Q28,48 35,38 L55,22 Q65,16 85,16 L115,18 Q135,20 148,34 L158,40 Q168,48 152,48 L136,48 A14,14 0 0,1 108,48 L64,48 A14,14 0 0,1 36,48 Z";
  let bodyType = "SERIES / MODEL";

  if (mLower.includes("suv") || mLower.includes("cross") || mLower.includes("x1") || mLower.includes("x3") || mLower.includes("x5") || mLower.includes("q3") || mLower.includes("q5") || mLower.includes("q7") || mLower.includes("kuga") || mLower.includes("tucson") || mLower.includes("tiguan") || mLower.includes("duster") || mLower.includes("captur") || mLower.includes("kadjar")) {
    bodyPath = "M12,48 Q22,48 28,36 L48,16 Q58,10 88,10 L128,12 Q142,14 150,28 L158,36 Q168,48 152,48 L136,48 A14,14 0 0,1 108,48 L64,48 A14,14 0 0,1 36,48 Z";
    bodyType = "SUV / CROSSOVER";
  } else if (mLower.includes("van") || mLower.includes("transit") || mLower.includes("transporter") || mLower.includes("master") || mLower.includes("trafic") || mLower.includes("boxer") || mLower.includes("caddy") || mLower.includes("sprinter") || mLower.includes("kangoo") || mLower.includes("berlingo")) {
    bodyPath = "M10,48 L10,22 Q12,12 30,10 L135,10 Q152,12 158,26 L164,36 Q168,48 152,48 L136,48 A14,14 0 0,1 108,48 L64,48 A14,14 0 0,1 36,48 Z";
    bodyType = "COMMERCIAL / VAN";
  } else if (mLower.includes("spider") || mLower.includes("cabrio") || mLower.includes("roadster") || mLower.includes("mx-5") || mLower.includes("slk") || mLower.includes("tt") || mLower.includes("z4") || mLower.includes("wind")) {
    bodyPath = "M15,48 Q28,48 35,38 L65,30 Q80,28 105,28 L122,30 Q138,32 148,38 L158,42 Q168,48 152,48 L136,48 A14,14 0 0,1 108,48 L64,48 A14,14 0 0,1 36,48 Z";
    bodyType = "ROADSTER / CABRIO";
  } else if (mLower.includes("gt") || mLower.includes("rs") || mLower.includes("911") || mLower.includes("ferrari") || mLower.includes("lamborghini") || mLower.includes("m3") || mLower.includes("m5") || mLower.includes("amg")) {
    bodyPath = "M12,48 Q24,48 32,38 L58,20 Q72,14 100,16 L124,20 Q142,26 152,36 L162,42 Q168,48 152,48 L136,48 A14,14 0 0,1 108,48 L64,48 A14,14 0 0,1 36,48 Z";
    bodyType = "PERFORMANCE / GT";
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="320" height="180">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#0d1b2a"/>
        <stop offset="100%" stop-color="#050a12"/>
      </linearGradient>
      <linearGradient id="glow" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.30"/>
        <stop offset="100%" stop-color="#0284c7" stop-opacity="0.02"/>
      </linearGradient>
      <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
        <feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#000" flood-opacity="0.6"/>
      </filter>
    </defs>
    <rect width="320" height="180" rx="10" fill="url(#bg)"/>
    <circle cx="160" cy="72" r="65" fill="url(#glow)"/>
    
    <!-- Vehicle Silhouette -->
    <g transform="translate(70, 36)" filter="url(#shadow)">
      <path d="${bodyPath}" fill="none" stroke="#38bdf8" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="50" cy="48" r="9" fill="#0b1322" stroke="#38bdf8" stroke-width="3"/>
      <circle cx="122" cy="48" r="9" fill="#0b1322" stroke="#38bdf8" stroke-width="3"/>
    </g>

    <!-- Title Banner -->
    <rect y="130" width="320" height="50" fill="#081321" opacity="0.95"/>
    <line x1="0" y1="130" x2="320" y2="130" stroke="#1e293b" stroke-width="1"/>
    <text x="160" y="150" fill="#f8fafc" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="800" text-anchor="middle" letter-spacing="0.5">${bEsc} ${mEsc}</text>
    <text x="160" y="167" fill="#38bdf8" font-family="system-ui, -apple-system, sans-serif" font-size="10" font-weight="700" text-anchor="middle" letter-spacing="1">${gEsc || bodyType}</text>
  </svg>`;
}

const IMAGE_EXTS = ['.jpg', '.jpeg', '.webp', '.png', '.gif'];
const clean = s => String(s || '').replace(/[^a-zA-Z0-9]/g, '');
const reEsc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// Boundary-safe: "20" must not match "Peugeot_206", but "206" must match
// "Peugeot_206" and "Peugeot_206_SW".
function fileMatchesModel(baseName, brand, model) {
  const b = clean(brand);
  const m = clean(model);
  if (!m) return false;
  if (clean(baseName) === b + m) return true;
  const withBrand = new RegExp('^' + reEsc(b) + '[\\s_.-]*' + reEsc(m) + '($|[\\s_.-])', 'i');
  if (b && withBrand.test(baseName)) return true;
  const noBrand = new RegExp('^' + reEsc(m) + '($|[\\s_.-])', 'i');
  return noBrand.test(baseName);
}

function findLocalModelImage(brand, model, localPath) {
  // 1. Explicit local path from the database (relative paths may or may not include model_images\)
  if (localPath) {
    const rel = String(localPath).replace(/^.*model_images[\\/]/i, '');
    for (const root of [ROOT, LEGACY_ROOT]) {
      for (const cand of [
        path.isAbsolute(localPath) ? localPath : null,
        path.join(root, localPath),
        path.join(root, 'model_images', rel)
      ]) {
        if (cand && fs.existsSync(cand) && fs.statSync(cand).isFile()) return cand;
      }
    }
  }

  // 2. Name-based lookup across every image root: <root>/<brand>/<Brand_Model>.<ext>
  const cleanBrand = clean(brand).toLowerCase();
  const cleanModel = clean(model).toLowerCase();
  let best = null;
  let bestRank = -1;

  for (const root of IMAGE_ROOTS) {
    const brandDirs = new Set([root, path.join(root, cleanBrand)]);
    for (const dir of brandDirs) {
      let entries;
      try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { continue; }
      for (const e of entries) {
        if (!e.isFile()) continue;
        const ext = path.extname(e.name).toLowerCase();
        if (!IMAGE_EXTS.includes(ext)) continue;
        const base = e.name.slice(0, e.name.length - ext.length);
        if (!fileMatchesModel(base, brand, model)) continue;
        const full = path.join(dir, e.name);
        let size = 0;
        try { size = fs.statSync(full).size; } catch { continue; }
        const exact = clean(base.toLowerCase()) === cleanBrand + cleanModel ? 1 : 0;
        const rank = exact * 1e12 + size;
        if (rank > bestRank) { bestRank = rank; best = full; }
      }
    }
  }
  return best;
}

const THUMB_WIDTH = Number(process.env.PIC_THUMB_WIDTH) || 640;
const MAX_IMAGE_BYTES = Number(process.env.PIC_MAX_BYTES) || 1572864;
const FETCH_TIMEOUT_MS = Number(process.env.PIC_FETCH_TIMEOUT_MS) || 5000;
const typeForExt = e => e === '.webp' ? 'image/webp' : e === '.png' ? 'image/png' : e === '.gif' ? 'image/gif' : 'image/jpeg';

// Outbound picture hosts are sometimes unreachable (blocked/ throttled). Never let a card
// render block on them: abort quickly and fall through to the next candidate.
async function fetchWithTimeout(url, options = {}, ms = FETCH_TIMEOUT_MS) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(url, { ...options, signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
  }
}

// Circuit breaker for the Wikimedia search API: after a few failures stop probing for a while,
// so a brand grid full of picture-less models cannot queue dozens of doomed requests.
const wiki = { fails: 0, pausedUntil: 0 };
function wikiUsable() { return Date.now() >= wiki.pausedUntil; }
function wikiOk() { wiki.fails = 0; wiki.pausedUntil = 0; }
function wikiFailed() {
  wiki.fails++;
  if (wiki.fails >= 3) {
    wiki.pausedUntil = Date.now() + 10 * 60 * 1000;
    wiki.fails = 0;
  }
}

// Wikimedia "original" files are routinely 10-14 MB, which is unusable as a card image.
// Rewrite them to the bounded thumbnail path and drop tracking params.
function boundedUrl(rawUrl, width = THUMB_WIDTH) {
  let u;
  try { u = new URL(rawUrl); } catch { return rawUrl; }
  for (const key of [...u.searchParams.keys()]) {
    if (/^utm_/i.test(key)) u.searchParams.delete(key);
  }
  if (/(\.|)wikimedia\.org$/i.test(u.hostname) && !/\/thumb\//i.test(u.pathname)) {
    const m = u.pathname.match(/^\/wikipedia\/commons\/([0-9a-f])\/([0-9a-f]{2})\/([^/]+)$/i);
    if (m) {
      const [, a, ab, file] = m;
      const thumbName = /\.svg$/i.test(file) ? file + '.png' : file;
      u.pathname = `/wikipedia/commons/thumb/${a}/${ab}/${file}/${width}px-${thumbName}`;
      u.search = '';
    }
  }
  return u.toString();
}

async function fetchWikimediaCarImage(brand, model) {
  if (!wikiUsable()) return null;
  try {
    const q = encodeURIComponent(`${brand} ${model} car`);
    const url = `https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch=${q}&gsrlimit=1&prop=imageinfo&iiprop=url|mime&iiurlwidth=${THUMB_WIDTH}&format=json`;
    const res = await fetchWithTimeout(url, { headers: { 'User-Agent': 'car-database-dashboard/1.0 (model picture search)' } })
      .then(r => r.json());
    if (res.query && res.query.pages) {
      const page = Object.values(res.query.pages)[0];
      const info = page && page.imageinfo && page.imageinfo[0];
      if (info) { wikiOk(); return boundedUrl(info.thumburl || info.url); }
    }
    wikiOk();
  } catch (e) {
    wikiFailed();
  }
  return null;
}

async function getModelPicture(brand, model, gen, db) {
  if (!brand || !model) {
    return { contentType: 'image/svg+xml; charset=utf-8', buffer: Buffer.from(generateCarModelSVG('Car', 'Model', gen)) };
  }

  // 1. Look up image_url & image_local_path in models table (exact name first,
  //    then prefix matches, preferring rows that actually carry a picture)
  const WHERE =
    "WHERE (LOWER(brand_name)=LOWER(?) OR LOWER(brand_name) LIKE LOWER(?) || '%') " +
    "AND (LOWER(model_name)=LOWER(?) OR LOWER(model_name) LIKE LOWER(?) || '%')";
  let row = db.prepare(
    "SELECT image_url, image_local_path FROM models " + WHERE +
    "ORDER BY (image_url IS NOT NULL AND image_url<>'') DESC, " +
    "         (image_local_path IS NOT NULL AND image_local_path<>'') DESC LIMIT 1"
  ).get(brand, brand, model, model);
  if (!row || (!row.image_url && !row.image_local_path)) {
    const exact = db.prepare(
      "SELECT image_url, image_local_path FROM models " +
      "WHERE LOWER(brand_name)=LOWER(?) AND LOWER(model_name)=LOWER(?) LIMIT 1"
    ).get(brand, model);
    if (exact) row = exact;
  }

  let rawUrl = row ? row.image_url : null;
  let localPath = row ? row.image_local_path : null;

  // 2. First check if a local image file exists in model_images/ folder on disk
  const existingLocalFile = findLocalModelImage(brand, model, localPath);
  if (existingLocalFile) {
    const buf = fs.readFileSync(existingLocalFile);
    const ext = path.extname(existingLocalFile).toLowerCase();
    const ct = ext === '.webp' ? 'image/webp' : ext === '.png' ? 'image/png' : ext === '.gif' ? 'image/gif' : 'image/jpeg';
    return { contentType: ct, buffer: buf };
  }

  // 3. If no image_url in DB, try live fetch from Wikimedia Commons & persist
  if (!rawUrl) {
    const fetchedUrl = await fetchWikimediaCarImage(brand, model);
    if (fetchedUrl) {
      rawUrl = fetchedUrl;
      try {
        db.prepare(
          "UPDATE models SET image_url=?, image_source='wikimedia' " +
          "WHERE (LOWER(brand_name)=LOWER(?) OR LOWER(brand_name) LIKE LOWER(?) || '%') " +
          "AND (LOWER(model_name)=LOWER(?) OR LOWER(model_name) LIKE LOWER(?) || '%')"
        ).run(fetchedUrl, brand, brand, model, model);
      } catch (e) {
        // Ignore DB update errors
      }
    }
  }

  const isWikimedia = u => /(^|\.)wikimedia\.org$/i.test(u.hostname);

  // 4. If image_url exists, proxy it (bounded size) and store it in the first _cache folder.
  //    A rewritten Wikimedia thumbnail is never retried as the full original: that is how a
  //    single card ends up pulling 12 MB. Oversized payloads are dropped for the SVG fallback.
  if (rawUrl) {
    const bounded = boundedUrl(rawUrl);
    const candidates = bounded === rawUrl ? [rawUrl] : [bounded];
    for (const url of candidates) {
      let wikimedia = false;
      try { wikimedia = isWikimedia(new URL(url)); } catch { /* keep false */ }
      if (wikimedia && !wikiUsable()) break;
      try {
        const extMatch = url.match(/\.(webp|png|jpe?g|gif)/i);
        const ext = extMatch ? '.' + extMatch[1].toLowerCase() : '.img';
        const key = crypto.createHash('sha1').update(url).digest('hex');

        // Already downloaded by the /img proxy or an earlier run? Reuse whichever folder has it.
        for (const dir of CACHE_DIRS) {
          const hit = path.join(dir, key + ext);
          if (fs.existsSync(hit)) {
            const stat = fs.statSync(hit);
            if (stat.size <= MAX_IMAGE_BYTES) return { contentType: typeForExt(ext), buffer: fs.readFileSync(hit) };
          }
        }

        const headers = { 'User-Agent': 'car-database-dashboard/1.0 (local model picture proxy)' };
        if (url.includes('7zap.com')) headers.Referer = 'https://7zap.com/en/';
        const r = await fetchWithTimeout(url, { headers, redirect: 'follow' });
        if (r.ok) {
          const buf = Buffer.from(await r.arrayBuffer());
          if (wikimedia) wikiOk();
          if (buf.length > MAX_IMAGE_BYTES) continue;
          fs.writeFileSync(path.join(CACHE_DIRS[0], key + ext), buf);
          return { contentType: typeForExt(ext), buffer: buf };
        }
        if (wikimedia) wikiFailed();
      } catch (e) {
        if (wikimedia) wikiFailed();
        // try the next candidate, then the SVG fallback
      }
    }
  }

  // 5. Fallback: High-resolution SVG vehicle card
  return {
    contentType: 'image/svg+xml; charset=utf-8',
    buffer: Buffer.from(generateCarModelSVG(brand, model, gen))
  };
}

module.exports = {
  getModelPicture,
  findLocalModelImage,
  generateCarModelSVG,
  fetchWikimediaCarImage,
  boundedUrl,
  typeForExt,
  fetchWithTimeout
};
