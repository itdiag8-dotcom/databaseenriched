'use strict';
const fs = require('fs');
const path = require('path');
const { DatabaseSync } = require('node:sqlite');

const ROOT = __dirname;
const DB_PATH = path.join(ROOT, 'database_enriched', 'car_database.db');
const CSV_DIR = path.join(ROOT, 'database_enriched', 'csv_exports');

// Simple, fast, robust CSV parser supporting quotes and escaped quotes
function parseCSV(content) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;
  let i = 0;
  const len = content.length;

  while (i < len) {
    const c = content[i];
    if (inQuotes) {
      if (c === '"') {
        if (i + 1 < len && content[i + 1] === '"') {
          field += '"';
          i += 2;
        } else {
          inQuotes = false;
          i++;
        }
      } else {
        field += c;
        i++;
      }
    } else {
      if (c === '"') {
        inQuotes = true;
        i++;
      } else if (c === ',') {
        row.push(field);
        field = '';
        i++;
      } else if (c === '\r') {
        i++;
      } else if (c === '\n') {
        row.push(field);
        field = '';
        if (row.length > 1 || row[0] !== '') {
          rows.push(row);
        }
        row = [];
        i++;
      } else {
        field += c;
        i++;
      }
    }
  }
  if (field !== '' || row.length > 0) {
    row.push(field);
    if (row.length > 1 || row[0] !== '') {
      rows.push(row);
    }
  }
  return rows;
}

function parseCSVFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  return parseCSV(content);
}

function numOrNull(val) {
  if (val === null || val === undefined || val === '') return null;
  const n = Number(val);
  return Number.isFinite(n) ? n : null;
}

function intOrNull(val) {
  if (val === null || val === undefined || val === '') return null;
  const n = Number(String(val).replace(/\s+/g, ''));
  return Number.isFinite(n) ? Math.trunc(n) : null;
}

function strOrNull(val) {
  if (val === null || val === undefined) return null;
  const s = String(val).trim();
  return s === '' ? null : s;
}

function initDatabase() {
  console.log('Initializing SQLite database at:', DB_PATH);
  const dir = path.dirname(DB_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

  const force = process.argv.includes('--force');
  if (fs.existsSync(DB_PATH) && !force) {
    console.log('Database already exists at ' + DB_PATH + ', keeping existing database.');
    return;
  }

  if (fs.existsSync(DB_PATH) && force) {
    fs.unlinkSync(DB_PATH);
  }

  const db = new DatabaseSync(DB_PATH);
  db.exec('PRAGMA foreign_keys = OFF;');

  // Schema creation
  db.exec(`
    CREATE TABLE brands (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE models (
      id INTEGER PRIMARY KEY,
      brand_id INTEGER NOT NULL,
      brand_name TEXT NOT NULL,
      model_name TEXT NOT NULL,
      production_start INTEGER,
      production_end INTEGER,
      years_span TEXT,
      total_variants INTEGER,
      source TEXT,
      status TEXT,
      image_url TEXT,
      image_local_path TEXT,
      image_source_page TEXT,
      image_match_name TEXT,
      image_match_score REAL,
      image_match_method TEXT,
      image_source TEXT,
      image_credit TEXT,
      image_license TEXT
    );

    CREATE TABLE engines (
      engine_code TEXT PRIMARY KEY,
      engine_type TEXT,
      fuel TEXT,
      displacement_cc INTEGER,
      power_hp INTEGER,
      cylinders INTEGER,
      ecu_maker TEXT,
      ecu_model TEXT,
      brand_example TEXT,
      model_example TEXT,
      year_example INTEGER,
      count_variants INTEGER,
      power_kw REAL,
      data_confidence TEXT
    );

    CREATE TABLE vehicle_variants (
      id INTEGER PRIMARY KEY,
      car_brand TEXT NOT NULL,
      car_model TEXT NOT NULL,
      car_year INTEGER,
      fuel TEXT,
      engine_power_hp INTEGER,
      engine_type TEXT,
      engine_code TEXT,
      ecu_maker TEXT,
      ecu_model TEXT,
      production_start INTEGER,
      production_end INTEGER,
      engine_power_kw REAL
    );

    CREATE TABLE engine_service_specs (
      engine_code TEXT PRIMARY KEY,
      engine_type TEXT,
      fuel TEXT,
      displacement_cc INTEGER,
      power_hp INTEGER,
      cylinders INTEGER,
      brand_example TEXT,
      model_example TEXT,
      year_example INTEGER,
      oil_viscosity TEXT,
      oil_standard TEXT,
      oil_acea TEXT,
      oil_oem_spec TEXT,
      oil_capacity_with_filter_l REAL,
      oil_capacity_without_filter_l REAL,
      oil_change_interval_km INTEGER,
      oil_change_interval_months INTEGER,
      coolant_type TEXT,
      coolant_spec TEXT,
      coolant_capacity_l REAL,
      coolant_change_interval_km INTEGER,
      coolant_change_interval_months INTEGER,
      timing_type TEXT,
      timing_belt_interval_km INTEGER,
      timing_belt_interval_months INTEGER,
      timing_chain_inspection_km INTEGER,
      air_filter_interval_km INTEGER,
      air_filter_interval_months INTEGER,
      fuel_filter_interval_km INTEGER,
      fuel_filter_interval_months INTEGER,
      brake_fluid_type TEXT,
      brake_fluid_change_months INTEGER,
      spark_plug_type TEXT,
      spark_plug_gap_mm TEXT,
      spark_plug_interval_km INTEGER,
      spark_plug_interval_months INTEGER,
      aux_belt_interval_km INTEGER,
      aux_belt_interval_months INTEGER,
      count_variants INTEGER,
      power_kw REAL,
      oil_spec_source TEXT,
      timing_source TEXT,
      coolant_source TEXT,
      data_confidence TEXT
    );

    CREATE TABLE engine_technical_specs (
      engine_code TEXT PRIMARY KEY,
      engine_type TEXT,
      fuel TEXT,
      displacement_cc INTEGER,
      cylinders INTEGER,
      bore_mm REAL,
      stroke_mm REAL,
      compression_ratio TEXT,
      compression_pressure_min_bar REAL,
      compression_pressure_max_bar REAL,
      compression_pressure_diff_max_bar REAL,
      fuel_system_type TEXT,
      fuel_pressure_low_bar REAL,
      fuel_pressure_high_bar REAL,
      fuel_octane_requirement TEXT,
      oil_pressure_idle_bar REAL,
      oil_pressure_2000rpm_bar REAL,
      idle_rpm INTEGER,
      valve_clearance_intake TEXT,
      valve_clearance_exhaust TEXT,
      ignition_timing TEXT,
      spark_plug_type TEXT,
      spark_plug_gap_mm TEXT,
      spark_plug_interval_km INTEGER,
      torque_nm INTEGER,
      torque_rpm INTEGER,
      power_hp INTEGER,
      power_rpm INTEGER,
      co_idle_percent TEXT,
      hc_idle_ppm TEXT,
      lambda TEXT,
      has_dpf TEXT,
      has_egr TEXT,
      has_adblue_scr TEXT,
      ecu_maker TEXT,
      ecu_model TEXT,
      brand_example TEXT,
      model_example TEXT,
      year_example INTEGER,
      power_kw REAL,
      oil_spec_source TEXT,
      timing_source TEXT,
      coolant_source TEXT,
      data_confidence TEXT,
      radiator_cap_min_bar REAL,
      radiator_cap_max_bar REAL,
      radiator_cap_raw TEXT,
      compression_raw TEXT,
      oil_pressure_raw TEXT,
      fuel_pressure_raw TEXT,
      tech_source TEXT
    );

    CREATE TABLE IF NOT EXISTS ecu_diagnostics (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      make TEXT NOT NULL,
      model TEXT NOT NULL,
      generation TEXT,
      variant TEXT,
      year_range TEXT,
      engine_code TEXT,
      ecu_id TEXT,
      ecu_maker TEXT,
      powertrain TEXT,
      mcu_architecture TEXT,
      obd_protocol TEXT,
      programming_method TEXT,
      obd_location TEXT,
      diagnostic_notes TEXT,
      origin_status TEXT
    );

    CREATE TABLE IF NOT EXISTS brand_logos (
      brand_name TEXT PRIMARY KEY,
      logo_url TEXT,
      logo_svg TEXT
    );
  `);

  db.exec('BEGIN TRANSACTION;');

  // 1. Models & Brands from 02_models.csv
  console.log('Loading models...');
  const modelsRows = parseCSVFile(path.join(CSV_DIR, '02_models.csv'));
  const modelHeader = modelsRows[0];
  const mCol = {};
  modelHeader.forEach((h, idx) => { mCol[h.trim()] = idx; });

  const brandsMap = new Map(); // brand_name -> brand_id
  const insBrand = db.prepare('INSERT OR IGNORE INTO brands (id, name) VALUES (?, ?)');
  const insModel = db.prepare(`
    INSERT INTO models (
      id, brand_id, brand_name, model_name, production_start, production_end,
      years_span, total_variants, source, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  for (let r = 1; r < modelsRows.length; r++) {
    const row = modelsRows[r];
    const id = intOrNull(row[mCol.id]);
    const brandId = intOrNull(row[mCol.brand_id]);
    const brandName = strOrNull(row[mCol.brand_name]);
    const modelName = strOrNull(row[mCol.model_name]);
    const prodStart = intOrNull(row[mCol.production_start]);
    const prodEnd = intOrNull(row[mCol.production_end]);
    const yearsSpan = strOrNull(row[mCol.years_span]);
    const totalVariants = intOrNull(row[mCol.total_variants]) || 0;
    const source = strOrNull(row[mCol.source]);
    const status = strOrNull(row[mCol.status]);

    if (!brandsMap.has(brandName) && brandId && brandName) {
      brandsMap.set(brandName, brandId);
      insBrand.run(brandId, brandName);
    }

    insModel.run(id, brandId, brandName, modelName, prodStart, prodEnd, yearsSpan, totalVariants, source, status);
  }

  // 2. Images from 90_7zap_model_images.csv
  const imagesCsv = path.join(CSV_DIR, '90_7zap_model_images.csv');
  if (fs.existsSync(imagesCsv)) {
    console.log('Loading 7zap model images...');
    const imgRows = parseCSVFile(imagesCsv);
    const imgHeader = imgRows[0];
    const iCol = {};
    imgHeader.forEach((h, idx) => { iCol[h.trim()] = idx; });

    const updModelImg = db.prepare(`
      UPDATE models SET
        image_url = ?,
        image_source_page = ?,
        image_match_name = ?,
        image_match_score = ?,
        image_match_method = ?,
        image_source = ?,
        image_credit = ?,
        image_license = ?
      WHERE id = ?
    `);

    for (let r = 1; r < imgRows.length; r++) {
      const row = imgRows[r];
      const modelId = intOrNull(row[iCol.model_id]);
      if (!modelId) continue;
      updModelImg.run(
        strOrNull(row[iCol.image_url]),
        strOrNull(row[iCol.image_source_page]),
        strOrNull(row[iCol.image_match_name]),
        numOrNull(row[iCol.image_match_score]),
        strOrNull(row[iCol.image_match_method]),
        strOrNull(row[iCol.image_source]),
        strOrNull(row[iCol.image_credit]),
        strOrNull(row[iCol.image_license]),
        modelId
      );
    }
  }

  // 3. Engines from 00_engines.csv
  console.log('Loading engines...');
  const enginesRows = parseCSVFile(path.join(CSV_DIR, '00_engines.csv'));
  const eHeader = enginesRows[0];
  const eCol = {};
  eHeader.forEach((h, idx) => { eCol[h.trim()] = idx; });

  const insEngine = db.prepare(`
    INSERT INTO engines (
      engine_code, engine_type, fuel, displacement_cc, power_hp, cylinders,
      ecu_maker, ecu_model, brand_example, model_example, year_example,
      count_variants, power_kw, data_confidence
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  for (let r = 1; r < enginesRows.length; r++) {
    const row = enginesRows[r];
    const code = strOrNull(row[eCol.engine_code]);
    if (!code) continue;
    insEngine.run(
      code,
      strOrNull(row[eCol.engine_type]),
      strOrNull(row[eCol.fuel]),
      intOrNull(row[eCol.displacement_cc]),
      intOrNull(row[eCol.power_hp]),
      intOrNull(row[eCol.cylinders]),
      strOrNull(row[eCol.ecu_maker]),
      strOrNull(row[eCol.ecu_model]),
      strOrNull(row[eCol.brand_example]),
      strOrNull(row[eCol.model_example]),
      intOrNull(row[eCol.year_example]),
      intOrNull(row[eCol.count_variants]) || 0,
      numOrNull(row[eCol.power_kw]),
      strOrNull(row[eCol.data_confidence])
    );
  }

  // 4. Vehicle Variants from 01_vehicle_variants.csv
  console.log('Loading vehicle variants...');
  const varRows = parseCSVFile(path.join(CSV_DIR, '01_vehicle_variants.csv'));
  const vHeader = varRows[0];
  const vCol = {};
  vHeader.forEach((h, idx) => { vCol[h.trim()] = idx; });

  const insVariant = db.prepare(`
    INSERT INTO vehicle_variants (
      id, car_brand, car_model, car_year, fuel, engine_power_hp,
      engine_type, engine_code, ecu_maker, ecu_model, production_start,
      production_end, engine_power_kw
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  for (let r = 1; r < varRows.length; r++) {
    const row = varRows[r];
    const id = intOrNull(row[vCol.id]);
    insVariant.run(
      id,
      strOrNull(row[vCol.car_brand]) || '',
      strOrNull(row[vCol.car_model]) || '',
      intOrNull(row[vCol.car_year]),
      strOrNull(row[vCol.fuel]),
      intOrNull(row[vCol.engine_power_hp]),
      strOrNull(row[vCol.engine_type]),
      strOrNull(row[vCol.engine_code]),
      strOrNull(row[vCol.ecu_maker]),
      strOrNull(row[vCol.ecu_model]),
      intOrNull(row[vCol.production_start]),
      intOrNull(row[vCol.production_end]),
      numOrNull(row[vCol.engine_power_kw])
    );
  }

  // 5. Engine Service Specs from 03_engine_service_specs.csv
  console.log('Loading service specs...');
  const srvRows = parseCSVFile(path.join(CSV_DIR, '03_engine_service_specs.csv'));
  const sHeader = srvRows[0];
  const sCol = {};
  sHeader.forEach((h, idx) => { sCol[h.trim()] = idx; });

  const insService = db.prepare(`
    INSERT INTO engine_service_specs (
      engine_code, engine_type, fuel, displacement_cc, power_hp, cylinders,
      brand_example, model_example, year_example, oil_viscosity, oil_standard,
      oil_acea, oil_oem_spec, oil_capacity_with_filter_l, oil_capacity_without_filter_l,
      oil_change_interval_km, oil_change_interval_months, coolant_type, coolant_spec,
      coolant_capacity_l, coolant_change_interval_km, coolant_change_interval_months,
      timing_type, timing_belt_interval_km, timing_belt_interval_months, timing_chain_inspection_km,
      air_filter_interval_km, air_filter_interval_months, fuel_filter_interval_km, fuel_filter_interval_months,
      brake_fluid_type, brake_fluid_change_months, spark_plug_type, spark_plug_gap_mm, spark_plug_interval_km,
      spark_plug_interval_months, aux_belt_interval_km, aux_belt_interval_months, count_variants, power_kw,
      oil_spec_source, timing_source, coolant_source, data_confidence
    ) VALUES (
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
      ?, ?, ?, ?
    )
  `);

  for (let r = 1; r < srvRows.length; r++) {
    const row = srvRows[r];
    const code = strOrNull(row[sCol.engine_code]);
    if (!code) continue;
    insService.run(
      code,
      strOrNull(row[sCol.engine_type]),
      strOrNull(row[sCol.fuel]),
      intOrNull(row[sCol.displacement_cc]),
      intOrNull(row[sCol.power_hp]),
      intOrNull(row[sCol.cylinders]),
      strOrNull(row[sCol.brand_example]),
      strOrNull(row[sCol.model_example]),
      intOrNull(row[sCol.year_example]),
      strOrNull(row[sCol.oil_viscosity]),
      strOrNull(row[sCol.oil_standard]),
      strOrNull(row[sCol.oil_acea]),
      strOrNull(row[sCol.oil_oem_spec]),
      numOrNull(row[sCol.oil_capacity_with_filter_l]),
      numOrNull(row[sCol.oil_capacity_without_filter_l]),
      intOrNull(row[sCol.oil_change_interval_km]),
      intOrNull(row[sCol.oil_change_interval_months]),
      strOrNull(row[sCol.coolant_type]),
      strOrNull(row[sCol.coolant_spec]),
      numOrNull(row[sCol.coolant_capacity_l]),
      intOrNull(row[sCol.coolant_change_interval_km]),
      intOrNull(row[sCol.coolant_change_interval_months]),
      strOrNull(row[sCol.timing_type]),
      intOrNull(row[sCol.timing_belt_interval_km]),
      intOrNull(row[sCol.timing_belt_interval_months]),
      intOrNull(row[sCol.timing_chain_inspection_km]),
      intOrNull(row[sCol.air_filter_interval_km]),
      intOrNull(row[sCol.air_filter_interval_months]),
      intOrNull(row[sCol.fuel_filter_interval_km]),
      intOrNull(row[sCol.fuel_filter_interval_months]),
      strOrNull(row[sCol.brake_fluid_type]),
      intOrNull(row[sCol.brake_fluid_change_months]),
      strOrNull(row[sCol.spark_plug_type]),
      strOrNull(row[sCol.spark_plug_gap_mm]),
      intOrNull(row[sCol.spark_plug_interval_km]),
      intOrNull(row[sCol.spark_plug_interval_months]),
      intOrNull(row[sCol.aux_belt_interval_km]),
      intOrNull(row[sCol.aux_belt_interval_months]),
      intOrNull(row[sCol.count_variants]) || 0,
      numOrNull(row[sCol.power_kw]),
      strOrNull(row[sCol.oil_spec_source]),
      strOrNull(row[sCol.timing_source]),
      strOrNull(row[sCol.coolant_source]),
      strOrNull(row[sCol.data_confidence])
    );
  }

  // 6. Engine Technical Specs from 04_engine_technical_specs.csv
  console.log('Loading technical specs...');
  const techRows = parseCSVFile(path.join(CSV_DIR, '04_engine_technical_specs.csv'));
  const tHeader = techRows[0];
  const tCol = {};
  tHeader.forEach((h, idx) => { tCol[h.trim()] = idx; });

  const insTech = db.prepare(`
    INSERT INTO engine_technical_specs (
      engine_code, engine_type, fuel, displacement_cc, cylinders, bore_mm, stroke_mm,
      compression_ratio, compression_pressure_min_bar, compression_pressure_max_bar,
      compression_pressure_diff_max_bar, fuel_system_type, fuel_pressure_low_bar,
      fuel_pressure_high_bar, fuel_octane_requirement, oil_pressure_idle_bar,
      oil_pressure_2000rpm_bar, idle_rpm, valve_clearance_intake, valve_clearance_exhaust,
      ignition_timing, spark_plug_type, spark_plug_gap_mm, spark_plug_interval_km,
      torque_nm, torque_rpm, power_hp, power_rpm, co_idle_percent, hc_idle_ppm,
      lambda, has_dpf, has_egr, has_adblue_scr, ecu_maker, ecu_model, brand_example,
      model_example, year_example, power_kw, oil_spec_source, timing_source, coolant_source,
      data_confidence, radiator_cap_min_bar, radiator_cap_max_bar, radiator_cap_raw,
      compression_raw, oil_pressure_raw, fuel_pressure_raw, tech_source
    ) VALUES (
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
  `);

  for (let r = 1; r < techRows.length; r++) {
    const row = techRows[r];
    const code = strOrNull(row[tCol.engine_code]);
    if (!code) continue;
    insTech.run(
      code,
      strOrNull(row[tCol.engine_type]),
      strOrNull(row[tCol.fuel]),
      intOrNull(row[tCol.displacement_cc]),
      intOrNull(row[tCol.cylinders]),
      numOrNull(row[tCol.bore_mm]),
      numOrNull(row[tCol.stroke_mm]),
      strOrNull(row[tCol.compression_ratio]),
      numOrNull(row[tCol.compression_pressure_min_bar]),
      numOrNull(row[tCol.compression_pressure_max_bar]),
      numOrNull(row[tCol.compression_pressure_diff_max_bar]),
      strOrNull(row[tCol.fuel_system_type]),
      numOrNull(row[tCol.fuel_pressure_low_bar]),
      numOrNull(row[tCol.fuel_pressure_high_bar]),
      strOrNull(row[tCol.fuel_octane_requirement]),
      numOrNull(row[tCol.oil_pressure_idle_bar]),
      numOrNull(row[tCol.oil_pressure_2000rpm_bar]),
      intOrNull(row[tCol.idle_rpm]),
      strOrNull(row[tCol.valve_clearance_intake]),
      strOrNull(row[tCol.valve_clearance_exhaust]),
      strOrNull(row[tCol.ignition_timing]),
      strOrNull(row[tCol.spark_plug_type]),
      strOrNull(row[tCol.spark_plug_gap_mm]),
      intOrNull(row[tCol.spark_plug_interval_km]),
      intOrNull(row[tCol.torque_nm]),
      intOrNull(row[tCol.torque_rpm]),
      intOrNull(row[tCol.power_hp]),
      intOrNull(row[tCol.power_rpm]),
      strOrNull(row[tCol.co_idle_percent]),
      strOrNull(row[tCol.hc_idle_ppm]),
      strOrNull(row[tCol.lambda]),
      strOrNull(row[tCol.has_dpf]),
      strOrNull(row[tCol.has_egr]),
      strOrNull(row[tCol.has_adblue_scr]),
      strOrNull(row[tCol.ecu_maker]),
      strOrNull(row[tCol.ecu_model]),
      strOrNull(row[tCol.brand_example]),
      strOrNull(row[tCol.model_example]),
      intOrNull(row[tCol.year_example]),
      numOrNull(row[tCol.power_kw]),
      strOrNull(row[tCol.oil_spec_source]),
      strOrNull(row[tCol.timing_source]),
      strOrNull(row[tCol.coolant_source]),
      strOrNull(row[tCol.data_confidence]),
      numOrNull(row[tCol.radiator_cap_min_bar]),
      numOrNull(row[tCol.radiator_cap_max_bar]),
      strOrNull(row[tCol.radiator_cap_raw]),
      strOrNull(row[tCol.compression_raw]),
      strOrNull(row[tCol.oil_pressure_raw]),
      strOrNull(row[tCol.fuel_pressure_raw]),
      strOrNull(row[tCol.tech_source])
    );
  }

  // 6b. Load Renault ECU & Diagnostics
  const renaultCsv = path.join(CSV_DIR, 'renault_ecu_diagnostics.csv');
  if (fs.existsSync(renaultCsv)) {
    console.log('Loading Renault ECU diagnostics...');
    const renRows = parseCSVFile(renaultCsv);
    const rHeader = renRows[0];
    const rCol = {};
    rHeader.forEach((h, idx) => { rCol[h.trim()] = idx; });

    const insEcuDiag = db.prepare(`
      INSERT INTO ecu_diagnostics (
        make, model, generation, variant, year_range, engine_code,
        ecu_id, ecu_maker, powertrain, mcu_architecture, obd_protocol,
        programming_method, obd_location, diagnostic_notes, origin_status
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    for (let r = 1; r < renRows.length; r++) {
      const row = renRows[r];
      insEcuDiag.run(
        strOrNull(row[rCol['Make']]) || 'Renault',
        strOrNull(row[rCol['Model']]),
        strOrNull(row[rCol['Generation']]),
        strOrNull(row[rCol['Variant']]),
        strOrNull(row[rCol['Year Range']]),
        strOrNull(row[rCol['Engine Code']]),
        strOrNull(row[rCol['ECU ID (Family)']]),
        strOrNull(row[rCol['ECU Manufacturer']]),
        strOrNull(row[rCol['Powertrain']]),
        strOrNull(row[rCol['MCU Architecture']]),
        strOrNull(row[rCol['OBD Protocol']]),
        strOrNull(row[rCol['Programming Method']]),
        strOrNull(row[rCol['OBD Location']]),
        strOrNull(row[rCol['Diagnostic Notes']]),
        strOrNull(row[rCol['Origin Status']])
      );
    }
  }

  // 7. Indexes & Views
  console.log('Creating indexes and views...');
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_models_brand ON models(brand_name);
    CREATE INDEX IF NOT EXISTS idx_vehicle_brand_model ON vehicle_variants(car_brand, car_model);
    CREATE INDEX IF NOT EXISTS idx_vehicle_engine ON vehicle_variants(engine_code);
    CREATE INDEX IF NOT EXISTS idx_engines_fuel ON engines(fuel);
    CREATE INDEX IF NOT EXISTS idx_ecu_diag_make_model ON ecu_diagnostics(make, model);
    CREATE INDEX IF NOT EXISTS idx_ecu_diag_code ON ecu_diagnostics(engine_code);

    CREATE VIEW IF NOT EXISTS v_engine_full AS
    SELECT
      e.engine_code,
      e.engine_type,
      e.fuel,
      e.displacement_cc,
      e.power_hp,
      e.cylinders,
      s.oil_viscosity, s.oil_standard, s.oil_oem_spec, s.oil_capacity_with_filter_l, s.oil_capacity_without_filter_l, s.oil_change_interval_km, s.oil_change_interval_months,
      s.coolant_type, s.coolant_capacity_l, s.coolant_change_interval_km, s.coolant_change_interval_months,
      s.timing_type, s.timing_belt_interval_km, s.timing_belt_interval_months, s.timing_chain_inspection_km,
      t.compression_ratio, t.compression_pressure_min_bar, t.compression_pressure_max_bar, t.compression_pressure_diff_max_bar,
      t.fuel_system_type, t.fuel_pressure_low_bar, t.fuel_pressure_high_bar,
      t.oil_pressure_idle_bar, t.oil_pressure_2000rpm_bar, t.idle_rpm,
      t.torque_nm, t.torque_rpm
    FROM engines e
    JOIN engine_service_specs s ON s.engine_code=e.engine_code
    JOIN engine_technical_specs t ON t.engine_code=e.engine_code;

    CREATE VIEW IF NOT EXISTS v_model_overview AS
    SELECT
      m.brand_name,
      m.model_name,
      m.production_start,
      m.production_end,
      m.years_span,
      m.total_variants,
      m.source,
      m.status,
      COUNT(v.id) as vehicle_variants_count
    FROM models m
    LEFT JOIN vehicle_variants v ON v.car_brand=m.brand_name AND v.car_model=m.model_name
    GROUP BY m.id;

    CREATE VIEW IF NOT EXISTS v_vehicle_with_service AS
    SELECT
      v.id as vehicle_id,
      v.car_brand,
      v.car_model,
      v.car_year,
      v.fuel,
      v.engine_power_hp,
      v.engine_type,
      v.engine_code,
      v.production_start,
      v.production_end,
      s.oil_viscosity,
      s.oil_oem_spec,
      s.oil_capacity_with_filter_l,
      s.timing_type,
      s.timing_belt_interval_km,
      t.compression_pressure_min_bar,
      t.compression_pressure_max_bar,
      t.fuel_pressure_high_bar,
      t.oil_pressure_idle_bar
    FROM vehicle_variants v
    JOIN engine_service_specs s ON s.engine_code=v.engine_code
    JOIN engine_technical_specs t ON t.engine_code=v.engine_code;
  `);

  db.exec('COMMIT;');
  console.log('Database initialization complete!');
  const stats = {
    brands: db.prepare('SELECT count(*) as c FROM brands').get().c,
    models: db.prepare('SELECT count(*) as c FROM models').get().c,
    engines: db.prepare('SELECT count(*) as c FROM engines').get().c,
    variants: db.prepare('SELECT count(*) as c FROM vehicle_variants').get().c,
    service: db.prepare('SELECT count(*) as c FROM engine_service_specs').get().c,
    technical: db.prepare('SELECT count(*) as c FROM engine_technical_specs').get().c,
  };
  console.log('Stats:', stats);
  db.close();
}

if (require.main === module) {
  initDatabase();
}

module.exports = { initDatabase };
