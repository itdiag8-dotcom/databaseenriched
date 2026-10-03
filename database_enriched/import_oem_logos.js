'use strict';

const fs = require('fs');
const path = require('path');
const { DatabaseSync } = require('node:sqlite');

const DB_PATH = path.join(__dirname, 'car_database.db');
const db = new DatabaseSync(DB_PATH);

try {
  db.prepare('ALTER TABLE brand_logos ADD COLUMN content_type TEXT').run();
} catch (e) {}

const USER_AGENT = 'CarDatabaseApp/1.0 (contact@cardatabase.org)';

// Fallback direct CDN vector SVGs for top automotive marks
const SIMPLE_ICONS_MAP = {
  'porsche': 'porsche',
  'peugeot': 'peugeot',
  'mazda': 'mazda',
  'nissan': 'nissan',
  'subaru': 'subaru',
  'suzuki': 'suzuki',
  'opel': 'opel',
  'seat': 'seat',
  'skoda': 'skoda',
  'mitsubishi': 'mitsubishi',
  'maserati': 'maserati',
  'mclaren': 'mclaren',
  'lotus': 'lotus',
  'saab': 'saab',
  'smart': 'smart',
  'polestar': 'polestar',
  'vauxhall': 'vauxhall',
  'pontiac': 'generalmotors',
  'bentley': 'bentley',
  'jaguar': 'jaguar',
  'alfa romeo': 'alfaromeo',
  'aston martin': 'astonmartin',
  'cupra': 'cupra',
  'infiniti': 'infiniti',
  'lamborghini': 'lamborghini',
  'ferrari': 'ferrari',
  'rolls-royce': 'rollsroyce',
  'tata': 'tatamotors',
  'citroen': 'citroen',
  'citroën': 'citroen',
  'chevrolet': 'chevrolet',
  'cadillac': 'cadillac',
  'chrysler': 'chrysler',
  'dodge': 'dodge',
  'fiat': 'fiat',
  'ford': 'ford',
  'honda': 'honda',
  'hyundai': 'hyundai',
  'jeep': 'jeep',
  'kia': 'kia',
  'land rover': 'landrover',
  'lexus': 'lexus',
  'mercedes': 'mercedes',
  'mercedes-benz': 'mercedes',
  'mini': 'mini',
  'renault': 'renault',
  'tesla': 'tesla',
  'toyota': 'toyota',
  'volkswagen': 'volkswagen',
  'volvo': 'volvo',
  'byd': 'byd',
  'genesis': 'genesis'
};

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function fetchBuffer(url) {
  const res = await fetch(url, {
    headers: { 'User-Agent': USER_AGENT },
    redirect: 'follow'
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} from ${url}`);
  const ct = res.headers.get('content-type') || '';
  const buf = Buffer.from(await res.arrayBuffer());
  return { buf, ct };
}

async function main() {
  console.log('=== Starting Enhanced OEM Brand Logo Import ===');

  let cblManifest = {};
  try {
    const res = await fetch('https://cdn.jsdelivr.net/npm/car-brand-logos@1.0.0/brands.json');
    if (res.ok) cblManifest = await res.json();
    console.log(`Loaded car-brand-logos manifest (${Object.keys(cblManifest).length} brands).`);
  } catch (err) {
    console.warn('Could not load car-brand-logos manifest:', err.message);
  }

  const dbBrands = db.prepare("SELECT name FROM brands WHERE name NOT LIKE 'hernr_%' ORDER BY name").all().map(r => r.name);
  console.log(`Auditing ${dbBrands.length} distinct automotive brands in database.`);

  const upsertStmt = db.prepare(`
    INSERT INTO brand_logos (brand_name, logo_url, logo_svg, content_type)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(brand_name) DO UPDATE SET
      logo_url=excluded.logo_url,
      logo_svg=excluded.logo_svg,
      content_type=excluded.content_type
  `);

  let importedCount = 0;

  for (const brand of dbBrands) {
    const existing = db.prepare('SELECT logo_svg FROM brand_logos WHERE brand_name=?').get(brand);
    if (existing && existing.logo_svg && existing.logo_svg.length > 50) {
      console.log(`✓ ${brand} already stored (${existing.logo_svg.length} chars)`);
      importedCount++;
      continue;
    }

    let candidateUrls = [];

    // 1. Check car-brand-logos manifest
    const bKey = Object.keys(cblManifest).find(k =>
      k.toLowerCase() === brand.toLowerCase() ||
      k.toLowerCase() === brand.replace(/[-_]/g, ' ').toLowerCase() ||
      k.toLowerCase() === brand.replace(/ë/g, 'e').toLowerCase()
    );
    if (bKey) {
      const file = cblManifest[bKey];
      candidateUrls.push({
        url: `https://cdn.jsdelivr.net/npm/car-brand-logos@1.0.0/${file}`,
        isSvg: file.endsWith('.svg'),
        source: 'car-brand-logos'
      });
    }

    // 2. Check simple-icons CDN
    const siSlug = SIMPLE_ICONS_MAP[brand.toLowerCase()] || brand.toLowerCase().replace(/[^a-z0-9]/g, '');
    candidateUrls.push({
      url: `https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/${siSlug}.svg`,
      isSvg: true,
      source: 'simple-icons'
    });

    let success = false;
    for (const cand of candidateUrls) {
      try {
        const { buf, ct } = await fetchBuffer(cand.url);
        let finalSvg = '';
        let finalCt = ct;

        if (cand.isSvg || ct.includes('svg') || buf.slice(0, 100).toString('utf8').includes('<svg')) {
          finalSvg = buf.toString('utf8');
          finalCt = 'image/svg+xml';
        } else {
          const mime = ct.includes('png') ? 'image/png' : (ct.includes('jpeg') || ct.includes('jpg') ? 'image/jpeg' : 'image/png');
          const b64 = buf.toString('base64');
          finalSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%"><image href="data:${mime};base64,${b64}" width="160" height="160" preserveAspectRatio="xMidYMid meet"/></svg>`;
          finalCt = 'image/svg+xml';
        }

        if (finalSvg && finalSvg.includes('<svg')) {
          upsertStmt.run(brand, cand.url, finalSvg, finalCt);
          console.log(`✓ Stored OEM logo for ${brand} via ${cand.source} (${finalSvg.length} chars)`);
          importedCount++;
          success = true;
          break;
        }
      } catch (e) {
        // try next candidate
      }
    }

    if (!success) {
      console.log(`? No direct CDN match for: ${brand}`);
    }
  }

  // Ensure common aliases are synced
  const ALIASES = {
    'Mercedes': 'Mercedes-Benz',
    'Citroen': 'Citroën',
    'Skoda': 'Škoda',
    'Seat': 'SEAT',
    'VW': 'Volkswagen'
  };

  for (const [alias, canonical] of Object.entries(ALIASES)) {
    const row = db.prepare('SELECT logo_url, logo_svg, content_type FROM brand_logos WHERE brand_name=?').get(canonical) ||
      db.prepare('SELECT logo_url, logo_svg, content_type FROM brand_logos WHERE brand_name=?').get(alias);
    if (row && row.logo_svg) {
      upsertStmt.run(alias, row.logo_url, row.logo_svg, row.content_type);
      upsertStmt.run(canonical, row.logo_url, row.logo_svg, row.content_type);
      console.log(`✓ Synced alias pair ${alias} <=> ${canonical}`);
    }
  }

  const finalTotal = db.prepare('SELECT COUNT(*) as c FROM brand_logos').get().c;
  console.log(`=== OEM Brand Logo Import Complete: ${finalTotal} brand logos now in SQLite database! ===`);
}

main().catch(console.error);
