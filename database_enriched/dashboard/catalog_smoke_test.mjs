// Headless smoke test of the dashboard picture catalog.
//
//   node server.js &                                  # from database_enriched/
//   node dashboard/catalog_smoke_test.mjs
//
// Runs the dashboard's own JavaScript against the real HTTP API with a stubbed
// DOM and walks all four levels (brands -> models -> engine types -> engine
// codes), so a broken selector or template shows up without a browser.
import fs from 'node:fs';
import vm from 'node:vm';

const html = fs.readFileSync('dashboard/index.html', 'utf8');
const code = html.match(/<script>([\s\S]*)<\/script>/)[1];

const made = new Map();
function el(id) {
  if (made.has(id)) return made.get(id);
  const e = {
    id, innerHTML: '', textContent: '', value: '', checked: false, hidden: false,
    style: {}, dataset: {}, placeholder: '',
    classList: { toggle(){}, add(){}, remove(){}, contains(){ return false; } },
    addEventListener(){}, removeEventListener(){}, appendChild(){}, remove(){},
    querySelector: () => el(id + ' >'), querySelectorAll: () => [],
    getAttribute: () => null, setAttribute(){}, focus(){}, click(){},
    insertAdjacentHTML(){},
  };
  e.parentNode = e;
  made.set(id, e);
  return e;
}

const document = {
  querySelector: s => el(s), querySelectorAll: () => [],
  getElementById: s => el('#' + s),
  createElement: () => el('<tmp>'), addEventListener(){},
  body: el('body'),
};
const windowStub = { addEventListener(){}, scrollTo(){}, confirm: () => true, location: { href: '' } };

const BASE = 'http://127.0.0.1:3000';
const sandbox = {
  document, window: windowStub, console, setTimeout, clearTimeout, URL, Blob: class {},
  selBrand: el('#selBrand'), selModel: el('#selModel'), selEtype: el('#selEngineType'), selCode: el('#selCode'),
  localStorage: { getItem: () => null, setItem(){} },
};
sandbox.fetch = (u, o) => fetch(String(u).startsWith('http') ? u : BASE + u, o);
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(code.replace(/^\s*'use strict';/m, ''), sandbox, { timeout: 20000 });

sandbox.api = async (url, opts) => {
  const r = await fetch(BASE + url, opts);
  const d = await r.json();
  if (!r.ok || (d && d.error)) throw new Error(d.error || ('HTTP ' + r.status));
  return d;
};

const body = el('#catBody'), crumb = el('#catCrumb'), az = el('#catAz');
const must = (cond, msg) => { if (!cond) { console.error('FAIL:', msg); process.exit(1); } };

// level 1: brands
await sandbox.catGo('brands');
must(body.innerHTML.includes('grid brands'), 'brand grid rendered');
must(body.innerHTML.includes('BMW'), 'BMW tile present');
must(az.innerHTML.includes('>B<'), 'A-Z bar built');
const brandTiles = (body.innerHTML.match(/class="tile/g) || []).length;
console.log('brands level  :', brandTiles, 'tiles');

// level 2: models of BMW
await sandbox.catGo('models', 'BMW');
must(body.innerHTML.includes('grid models'), 'model grid rendered');
must(body.innerHTML.includes('/img?u='), 'pictures routed through the proxy');
must(body.innerHTML.includes('picture:'), 'match label shown');
must(crumb.innerHTML.includes('BMW'), 'breadcrumb shows brand');
console.log('models level  :', (body.innerHTML.match(/class="tile/g) || []).length, 'tiles,',
            (body.innerHTML.match(/<img /g) || []).length, 'pictures');

// level 3: engine types of one model
const first = body._rows.find(r => r.variant_count > 0 && r.image_url) || body._rows[0];
sandbox.catPickModel(body._rows.indexOf(first));
await new Promise(r => setTimeout(r, 400));
must(body.innerHTML.includes(first.model_name), 'model header card');
console.log('types level   :', first.model_name, '->',
            (body.innerHTML.match(/class="tile/g) || []).length, 'tiles');

// level 4: engine codes
const CAT = vm.runInContext('CAT', sandbox);
const etype = CAT.types[0] && CAT.types[0].engine_type;
await sandbox.catGo('codes', etype);
must(body.innerHTML.includes('edit &rsaquo;'), 'code tiles offer the editor');
console.log('codes level   :', etype, '->', CAT.codes.length, 'engine codes');

// wikidata brand carries attribution
await sandbox.catGo('models', 'Ferrari');
must(body.innerHTML.includes('wikidata'), 'wikidata source badge');
console.log('attribution   :', body.innerHTML.includes('class="credit"') ? 'credit line rendered' : 'no credits stored yet');
console.log('\nCATALOG SMOKE TEST OK');
