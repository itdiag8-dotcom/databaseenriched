const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.join(__dirname, '..');
const modelImagesDir = path.join(ROOT, 'model_images');
const cacheDir = path.join(modelImagesDir, '_cache');

fs.mkdirSync(modelImagesDir, { recursive: true });
fs.mkdirSync(cacheDir, { recursive: true });

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

function findLocalModelImage(brand, model, localPath) {
  // 1. Explicit local path from database if given
  if (localPath) {
    const p = path.isAbsolute(localPath) ? localPath : path.join(ROOT, localPath);
    if (fs.existsSync(p) && fs.statSync(p).isFile()) return p;
  }

  const cleanBrand = String(brand || '').replace(/[^a-zA-Z0-9_\-]/g, '_');
  const cleanModel = String(model || '').replace(/[^a-zA-Z0-9_\-]/g, '_');
  const exts = ['.jpg', '.jpeg', '.webp', '.png', '.gif'];

  // 2. Direct folder structures: model_images/<brand>/<model>.<ext> or model_images/<cleanBrand>_<cleanModel>.<ext>
  for (const ext of exts) {
    const candidates = [
      path.join(modelImagesDir, brand, `${model}${ext}`),
      path.join(modelImagesDir, brand, `${cleanModel}${ext}`),
      path.join(modelImagesDir, cleanBrand, `${cleanModel}${ext}`),
      path.join(modelImagesDir, `${cleanBrand}_${cleanModel}${ext}`),
      path.join(modelImagesDir, `${cleanModel}${ext}`)
    ];
    for (const cand of candidates) {
      if (fs.existsSync(cand) && fs.statSync(cand).isFile()) {
        return cand;
      }
    }
  }

  return null;
}

async function fetchWikimediaCarImage(brand, model) {
  try {
    const q = encodeURIComponent(`${brand} ${model} car`);
    const url = `https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch=${q}&gsrlimit=1&prop=imageinfo&iiprop=url|mime&format=json`;
    const res = await fetch(url, { headers: { 'User-Agent': 'car-database-dashboard/1.0 (model picture search)' } }).then(r => r.json());
    if (res.query && res.query.pages) {
      const page = Object.values(res.query.pages)[0];
      if (page && page.imageinfo && page.imageinfo[0]) {
        return page.imageinfo[0].url;
      }
    }
  } catch (e) {
    // Ignore fetch errors
  }
  return null;
}

async function getModelPicture(brand, model, gen, db) {
  if (!brand || !model) {
    return { contentType: 'image/svg+xml; charset=utf-8', buffer: Buffer.from(generateCarModelSVG('Car', 'Model', gen)) };
  }

  // 1. Look up image_url & image_local_path in models table
  let row = db.prepare(
    "SELECT image_url, image_local_path FROM models " +
    "WHERE (LOWER(brand_name)=LOWER(?) OR LOWER(brand_name) LIKE LOWER(?) || '%') " +
    "AND (LOWER(model_name)=LOWER(?) OR LOWER(model_name) LIKE LOWER(?) || '%') " +
    "LIMIT 1"
  ).get(brand, brand, model, model);

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

  // 4. If image_url exists, proxy and save directly to model_images/_cache
  if (rawUrl) {
    try {
      const key = crypto.createHash('sha1').update(rawUrl).digest('hex');
      const extMatch = rawUrl.match(/\.(webp|png|jpe?g|gif)/i);
      const ext = extMatch ? '.' + extMatch[1].toLowerCase() : '.img';
      const file = path.join(cacheDir, key + ext);

      if (fs.existsSync(file)) {
        const buf = fs.readFileSync(file);
        const ct = ext === '.webp' ? 'image/webp' : ext === '.png' ? 'image/png' : ext === '.gif' ? 'image/gif' : 'image/jpeg';
        return { contentType: ct, buffer: buf };
      }

      // Fetch from source and save to disk
      const headers = { 'User-Agent': 'car-database-dashboard/1.0 (local model picture proxy)' };
      if (rawUrl.includes('7zap.com')) headers.Referer = 'https://7zap.com/en/';
      const r = await fetch(rawUrl, { headers, redirect: 'follow' });
      if (r.ok) {
        const buf = Buffer.from(await r.arrayBuffer());
        fs.writeFileSync(file, buf);
        const ct = ext === '.webp' ? 'image/webp' : ext === '.png' ? 'image/png' : ext === '.gif' ? 'image/gif' : 'image/jpeg';
        return { contentType: ct, buffer: buf };
      }
    } catch (e) {
      // Proxy failed, proceed to SVG fallback
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
  fetchWikimediaCarImage
};
