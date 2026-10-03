'use strict';

const path = require('path');
const { DatabaseSync } = require('node:sqlite');

const DB_PATH = path.join(__dirname, 'car_database.db');
let _dbInstance = null;

function getDb(customDb) {
  const db = customDb || (_dbInstance || (_dbInstance = new DatabaseSync(DB_PATH)));
  try {
    db.prepare('ALTER TABLE brand_logos ADD COLUMN content_type TEXT').run();
  } catch (e) {}
  return db;
}

const USER_AGENT = 'CarDatabaseApp/1.0 (contact@cardatabase.org)';

// Standard brand aliases mapping to canonical names
const BRAND_ALIASES = {
  'mercedes': 'Mercedes-Benz',
  'mercedes benz': 'Mercedes-Benz',
  'citroen': 'Citroën',
  'skoda': 'Škoda',
  'seat': 'SEAT',
  'vw': 'Volkswagen',
  'gwm': 'Great Wall',
  'saic mg': 'MG',
  'renault samsung': 'Renault',
  'mitsubishi fuso': 'Mitsubishi',
  'infiniti': 'Infiniti',
  'alfa': 'Alfa Romeo',
  'landrover': 'Land Rover',
  'aston': 'Aston Martin'
};

// Neutral, clean vehicle mark for non-brand or unbranded entries
const NEUTRAL_CAR_ICON = `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" rx="16" fill="#0f172a" stroke="#1e293b" stroke-width="2"/>
  <path d="M22 62 L26 50 C28 44 34 38 42 38 L58 38 C66 38 72 44 74 50 L78 62 C80 63 82 65 82 68 L82 72 C82 74 80 76 78 76 L76 76 C76 78 74 80 72 80 L68 80 C66 80 64 78 64 76 L36 76 C36 78 34 80 32 80 L28 80 C26 80 24 78 24 76 L22 76 C20 76 18 74 18 72 L18 68 C18 65 20 63 22 62 Z M30 52 L70 52 L66 44 C65 42 62 40 58 40 L42 40 C38 40 35 42 34 44 Z" fill="#64748b"/>
</svg>`;

function getBrandKey(brand) {
  if (!brand) return '';
  return String(brand).trim().toLowerCase().replace(/[^a-z0-9]/g, '');
}

/**
 * Fetch a brand logo from the SQLite database.
 * If missing, attempts to import OEM logo from the internet and store it into SQLite.
 */
async function getOrImportBrandLogo(brandName, customDb) {
  if (!brandName || typeof brandName !== 'string') {
    return { svg: NEUTRAL_CAR_ICON, contentType: 'image/svg+xml; charset=utf-8', source: 'neutral' };
  }

  const db = getDb(customDb);
  const trimmed = brandName.trim();
  const lower = trimmed.toLowerCase();

  // 1. Direct query from database
  let row = db.prepare('SELECT brand_name, logo_url, logo_svg, content_type FROM brand_logos WHERE brand_name = ? COLLATE NOCASE').get(trimmed);
  if (row && row.logo_svg) {
    return {
      svg: row.logo_svg,
      contentType: row.content_type || 'image/svg+xml; charset=utf-8',
      url: row.logo_url,
      source: 'database'
    };
  }

  // 2. Check alias in database
  const canonical = BRAND_ALIASES[lower] || BRAND_ALIASES[trimmed];
  if (canonical) {
    row = db.prepare('SELECT brand_name, logo_url, logo_svg, content_type FROM brand_logos WHERE brand_name = ? COLLATE NOCASE').get(canonical);
    if (row && row.logo_svg) {
      // Cache alias into database
      try {
        db.prepare('INSERT OR REPLACE INTO brand_logos (brand_name, logo_url, logo_svg, content_type) VALUES (?, ?, ?, ?)').run(
          trimmed, row.logo_url, row.logo_svg, row.content_type
        );
      } catch (e) {}
      return {
        svg: row.logo_svg,
        contentType: row.content_type || 'image/svg+xml; charset=utf-8',
        url: row.logo_url,
        source: 'database_alias'
      };
    }
  }

  // 3. Brand not in database - attempt dynamic OEM import from internet
  console.log(`[brand_logos] Missing logo in database for "${trimmed}", attempting OEM import from internet...`);
  try {
    const imported = await importBrandLogoFromInternet(trimmed, db);
    if (imported && imported.svg) {
      return imported;
    }
  } catch (err) {
    console.warn(`[brand_logos] On-the-fly import failed for ${trimmed}:`, err.message);
  }

  // 4. Fallback neutral automotive icon
  return { svg: NEUTRAL_CAR_ICON, contentType: 'image/svg+xml; charset=utf-8', source: 'neutral' };
}

/**
 * Synchronous logo retrieval from database (with fallback to neutral)
 */
function getBrandLogoSVG(brandName, customDb) {
  if (!brandName || typeof brandName !== 'string') return NEUTRAL_CAR_ICON;
  const db = getDb(customDb);
  const trimmed = brandName.trim();
  const lower = trimmed.toLowerCase();

  let row = db.prepare('SELECT logo_svg FROM brand_logos WHERE brand_name = ? COLLATE NOCASE').get(trimmed);
  if (row && row.logo_svg) return row.logo_svg;

  const canonical = BRAND_ALIASES[lower] || BRAND_ALIASES[trimmed];
  if (canonical) {
    row = db.prepare('SELECT logo_svg FROM brand_logos WHERE brand_name = ? COLLATE NOCASE').get(canonical);
    if (row && row.logo_svg) return row.logo_svg;
  }

  // Trigger background import if brand seems like a valid name
  if (!trimmed.startsWith('hernr_')) {
    setImmediate(() => {
      importBrandLogoFromInternet(trimmed, db).catch(() => {});
    });
  }

  return NEUTRAL_CAR_ICON;
}

/**
 * Dynamically import an OEM brand logo from the internet and save it to SQLite.
 */
async function importBrandLogoFromInternet(brandName, customDb) {
  const db = getDb(customDb);
  const slug = brandName.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
  const cleanSlug = brandName.toLowerCase().replace(/[^a-z0-9]/g, '');

  const candidates = [
    `https://cdn.jsdelivr.net/npm/car-brand-logos@1.0.0/${slug}-logo.svg`,
    `https://cdn.jsdelivr.net/npm/car-brand-logos@1.0.0/${cleanSlug}-logo.svg`,
    `https://cdn.jsdelivr.net/npm/car-brand-logos@1.0.0/${slug}-logo.png`,
    `https://cdn.jsdelivr.net/npm/car-brand-logos@1.0.0/${cleanSlug}-logo.png`,
    `https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/${cleanSlug}.svg`
  ];

  for (const url of candidates) {
    try {
      const res = await fetch(url, { headers: { 'User-Agent': USER_AGENT } });
      if (!res.ok) continue;

      const ct = res.headers.get('content-type') || '';
      const isSvg = url.endsWith('.svg') || ct.includes('svg');
      let finalSvg = '';
      let finalCt = 'image/svg+xml; charset=utf-8';

      if (isSvg) {
        finalSvg = await res.text();
      } else {
        const buf = Buffer.from(await res.arrayBuffer());
        const b64 = buf.toString('base64');
        const mime = ct.includes('jpeg') || ct.includes('jpg') ? 'image/jpeg' : 'image/png';
        finalSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%"><image href="data:${mime};base64,${b64}" width="160" height="160" preserveAspectRatio="xMidYMid meet"/></svg>`;
      }

      if (finalSvg && finalSvg.includes('<svg')) {
        db.prepare(`
          INSERT INTO brand_logos (brand_name, logo_url, logo_svg, content_type)
          VALUES (?, ?, ?, ?)
          ON CONFLICT(brand_name) DO UPDATE SET logo_url=excluded.logo_url, logo_svg=excluded.logo_svg, content_type=excluded.content_type
        `).run(brandName, url, finalSvg, finalCt);
        console.log(`[brand_logos] Successfully imported OEM logo for ${brandName} from ${url} into database!`);
        return { svg: finalSvg, contentType: finalCt, url, source: 'imported' };
      }
    } catch (e) {}
  }

  // Try Wikimedia Commons search
  try {
    const q = encodeURIComponent(brandName + ' logo');
    const searchUrl = `https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=${q}&gsrnamespace=6&gsrlimit=3&prop=imageinfo&iiprop=url|mime&format=json`;
    const sRes = await fetch(searchUrl, { headers: { 'User-Agent': USER_AGENT } }).then(r => r.json());
    if (sRes.query && sRes.query.pages) {
      const pages = Object.values(sRes.query.pages);
      const svgPage = pages.find(p => p.title.toLowerCase().endsWith('.svg') && p.imageinfo && p.imageinfo[0]);
      if (svgPage) {
        const fileUrl = svgPage.imageinfo[0].url;
        const fRes = await fetch(fileUrl, { headers: { 'User-Agent': USER_AGENT } });
        if (fRes.ok) {
          const finalSvg = await fRes.text();
          if (finalSvg && finalSvg.includes('<svg')) {
            const finalCt = 'image/svg+xml; charset=utf-8';
            db.prepare(`
              INSERT INTO brand_logos (brand_name, logo_url, logo_svg, content_type)
              VALUES (?, ?, ?, ?)
              ON CONFLICT(brand_name) DO UPDATE SET logo_url=excluded.logo_url, logo_svg=excluded.logo_svg, content_type=excluded.content_type
            `).run(brandName, fileUrl, finalSvg, finalCt);
            console.log(`[brand_logos] Successfully imported OEM logo for ${brandName} from Wikimedia into database!`);
            return { svg: finalSvg, contentType: finalCt, url: fileUrl, source: 'wikimedia' };
          }
        }
      }
    }
  } catch (e) {}

  return null;
}

module.exports = {
  getBrandKey,
  getBrandLogoSVG,
  getOrImportBrandLogo,
  importBrandLogoFromInternet
};
