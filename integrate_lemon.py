#!/usr/bin/env python3
import json, sqlite3, pathlib, re, html, urllib.parse
from collections import defaultdict, Counter

LEMON_JSONL = "/home/user/lemon_crawl_2016_2017.jsonl"
DB_PATH = "/home/user/database_enriched/car_database.db"

def normalize_brand(lemon_brand, model_dir=""):
    # map lemon brand to DB car_brand
    lb = lemon_brand.strip()
    # Special cases
    if lb == "Dodge and Ram":
        # decide based on model_dir
        md = model_dir.lower()
        if md.startswith("ram") or " ram " in md:
            return "Ram"
        else:
            return "Dodge"
    if lb == "Nissan-Datsun":
        return "Nissan"
    if lb == "Mercedes Benz":
        return "Mercedes"
    if lb == "General Motors":
        return "GMC"  # or Chevrolet? but we keep as GMC
    # Most others map directly
    return lb

def parse_oil_visc(spec):
    # spec like "Genuine ACURA Motor Oil API Premium-grade SAE 0W-20 Detergent Oil."
    # extract SAE viscosity
    m = re.search(r'SAE\s+([0-9W\-\/]+)', spec, re.IGNORECASE)
    if m:
        return m.group(1)
    # also look for 5W-30 etc without SAE prefix
    m = re.search(r'(\d+W-\d+)', spec)
    if m:
        return m.group(1)
    return None

def extract_engine_key(entry):
    # entry has variant_parsed, fluids
    vp = entry['variant_parsed']
    fluids = entry['fluids']
    # 1) variant engine_code
    if 'engine_code' in vp and vp['engine_code']:
        # ensure uppercase
        return vp['engine_code'].strip().upper(), "variant_cd", vp
    # 2) fluid engine_cd most common
    codes = [fl['engine_cd_from_app'] for fl in fluids if fl['engine_cd_from_app']]
    if codes:
        # most common
        cnt = Counter(codes)
        top = cnt.most_common(1)[0][0]
        return top.strip().upper(), "fluid_cd", vp
    # 3) variant displacement+vin
    if 'displacement_cc' in vp and 'vin_code' in vp:
        key = f"LEMON_{normalize_brand(entry['brand'], entry['model_dir']).upper().replace(' ','_')}_{vp.get('base_model_guess','MODEL').upper().replace(' ','_')}_{vp['displacement_cc']}CC_VIN{vp['vin_code']}_{entry['year']}"
        return key, "variant_disp_vin", vp
    if 'displacement_cc' in vp:
        key = f"LEMON_{normalize_brand(entry['brand'], entry['model_dir']).upper().replace(' ','_')}_{vp.get('base_model_guess','MODEL').upper().replace(' ','_')}_{vp['displacement_cc']}CC_{entry['year']}"
        return key, "variant_disp", vp
    # 4) fluid displacement
    disp_vals = [fl['displacement_l_from_app'] for fl in fluids if fl['displacement_l_from_app']]
    if disp_vals:
        disp = disp_vals[0]
        cc = int(disp*1000)
        key = f"LEMON_{normalize_brand(entry['brand'], entry['model_dir']).upper().replace(' ','_')}_{vp.get('base_model_guess','MODEL').upper().replace(' ','_')}_{cc}CC_{entry['year']}"
        return key, "fluid_disp", vp
    # 5) fallback brand_model_year - deduplicate per brand/model/year (share engine across trims)
    base = vp.get('base_model_guess','MODEL').upper().replace(' ','_').replace('-','_')
    brand_norm = normalize_brand(entry['brand'], entry['model_dir']).upper().replace(' ','_')
    key = f"LEMON_{brand_norm}_{base}_{entry['year']}"
    return key, "fallback", vp

def extract_capacities(entry):
    fluids = entry['fluids']
    # oil
    oil_w = None
    oil_wo = None
    oil_spec = None
    oil_visc = None
    coolant_cap = None
    coolant_spec = None
    coolant_total = None
    coolant_drain = None
    for fl in fluids:
        if fl['fluid_type'] == "Engine Oil":
            extra = fl.get('extra','') or ""
            if "w/Filter" in extra:
                oil_w = fl['metric_value']
                oil_spec = fl['spec']
                oil_visc = parse_oil_visc(fl['spec'])
            elif "w/o Filter" in extra:
                oil_wo = fl['metric_value']
            # also fallback if no w/Filter marker but single entry
            if oil_w is None and fl['metric_value']:
                # if only one oil entry and extra blank, treat as w/Filter
                pass
        if fl['fluid_type'] == "Engine Coolant":
            extra = fl.get('extra','') or ""
            if "Total Capacity" in extra:
                coolant_total = fl['metric_value']
                coolant_spec = fl['spec']
            elif "Drain and Refill" in extra:
                coolant_drain = fl['metric_value']
                if not coolant_spec:
                    coolant_spec = fl['spec']
            else:
                # generic coolant
                if coolant_drain is None:
                    coolant_drain = fl['metric_value']
                    coolant_spec = fl['spec']
    # choose coolant capacity: prefer Total, else Drain
    coolant_cap = coolant_total if coolant_total else coolant_drain
    # if still none, try any coolant metric
    if not coolant_cap:
        for fl in fluids:
            if fl['fluid_type']=="Engine Coolant" and fl['metric_value']:
                coolant_cap=fl['metric_value']
                coolant_spec=fl['spec']
                break
    # oil fallback: if oil_w not found but there is a single oil entry with blank extra, use it
    if oil_w is None:
        for fl in fluids:
            if fl['fluid_type']=="Engine Oil" and fl['metric_value']:
                # if extra blank or contains Drain and Refill
                oil_w = fl['metric_value']
                oil_spec = fl['spec']
                oil_visc = parse_oil_visc(fl['spec'])
                break
    return {
        "oil_with_filter_l": oil_w,
        "oil_without_filter_l": oil_wo,
        "oil_spec": oil_spec,
        "oil_visc": oil_visc,
        "coolant_capacity_l": coolant_cap,
        "coolant_spec": coolant_spec,
        "coolant_total": coolant_total,
        "coolant_drain": coolant_drain
    }

def main():
    db = pathlib.Path(DB_PATH)
    con = sqlite3.connect(db)
    con.execute("PRAGMA foreign_keys=ON")
    cur = con.cursor()
    # load existing data for dedup
    cur.execute("SELECT engine_code FROM engines")
    existing_engines = set(r[0] for r in cur.fetchall())
    cur.execute("SELECT brand_name, model_name FROM models")
    existing_models = set((r[0].lower(), r[1].lower()) for r in cur.fetchall())
    cur.execute("SELECT car_brand, car_model, car_year, engine_code FROM vehicle_variants")
    existing_variants = set((r[0].lower(), r[1].lower(), r[2], r[3]) for r in cur.fetchall() if r[3])
    # also need variant without engine_code dedup?
    cur.execute("SELECT car_brand, car_model, car_year FROM vehicle_variants")
    existing_variants_no_code = set((r[0].lower(), r[1].lower(), r[2]) for r in cur.fetchall())

    # brand id map
    cur.execute("SELECT id, name FROM brands")
    brand_id_map = {name.lower():bid for bid,name in cur.fetchall()}

    # stats
    stats = defaultdict(int)
    new_engines = 0
    updated_engines = 0
    new_models = 0
    new_variants = 0
    trusted_updates = 0

    with open(LEMON_JSONL, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except: continue
            brand_raw = entry['brand']
            model_dir = entry['model_dir']
            year = entry['year']
            base_model = entry['variant_parsed'].get('base_model_guess','UNKNOWN')
            # normalize brand and base model for DB
            brand_norm = normalize_brand(brand_raw, model_dir)
            # fix brand case: keep as per mapping, but ensure title case for DB?
            # DB has brands like "Chevrolet", "Dodge", etc.
            # Keep as normalized
            base_model_clean = base_model.strip()
            # Some base models like "500" need special handling: keep as "500"
            # For models like "MDX", already fine

            # engine key
            engine_code, key_type, vp = extract_engine_key(entry)
            caps = extract_capacities(entry)
            # only process entries with at least one capacity (oil or coolant) – most have
            if not caps['oil_with_filter_l'] and not caps['coolant_capacity_l']:
                stats['skipped_no_capacity'] += 1
                continue

            # Determine displacement_cc for engines table
            disp_cc = vp.get('displacement_cc')
            if not disp_cc:
                # try fluid displacement
                for fl in entry['fluids']:
                    if fl['displacement_l_from_app']:
                        disp_cc = int(fl['displacement_l_from_app']*1000)
                        break
                # also try to infer from oil capacity? not reliable
            # Determine fuel? not in lemon, infer from spec or variant? Keep as None or Petrol default
            # For now, try to detect diesel from model_dir or spec
            fuel = None
            # Heuristic: if model_dir contains TDI, Diesel, or spec contains diesel etc.
            md_lower = model_dir.lower()
            spec_lower = (caps['oil_spec'] or "").lower() + " " + (caps['coolant_spec'] or "").lower()
            if "tdi" in md_lower or "diesel" in md_lower or "diesel" in spec_lower:
                fuel = "Diesel"
            elif "hybrid" in md_lower:
                fuel = "Hybrid"
            else:
                fuel = "Petrol"

            # Check existing engine
            is_new_engine = engine_code not in existing_engines
            # For synthetic keys, we may want to ensure not too many duplicates per brand_model_year
            # We'll create engine if not exists
            if is_new_engine:
                # Insert into engines
                # Need to handle that synthetic keys may be long, ensure primary key uniqueness
                # Insert minimal required fields
                try:
                    cur.execute("""INSERT INTO engines (engine_code, engine_type, fuel, displacement_cc, power_hp, cylinders, ecu_maker, ecu_model, brand_example, model_example, year_example, count_variants, power_kw, data_confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (engine_code, None, fuel, disp_cc, None, None, None, None, brand_norm, base_model_clean, year, 1, None, "TRUSTED_LEMON"))
                    new_engines += 1
                    existing_engines.add(engine_code)
                    stats[f'new_engine_{key_type}'] += 1
                except sqlite3.IntegrityError as e:
                    # duplicate due to race? skip
                    stats['engine_insert_fail'] += 1
                    continue
                # Also insert service specs
                try:
                    cur.execute("""INSERT INTO engine_service_specs (
                        engine_code, engine_type, fuel, displacement_cc, power_hp, cylinders,
                        brand_example, model_example, year_example,
                        oil_viscosity, oil_standard, oil_acea, oil_oem_spec,
                        oil_capacity_with_filter_l, oil_capacity_without_filter_l,
                        oil_change_interval_km, oil_change_interval_months,
                        coolant_type, coolant_spec, coolant_capacity_l,
                        coolant_change_interval_km, coolant_change_interval_months,
                        timing_type, timing_belt_interval_km, timing_belt_interval_months,
                        timing_chain_inspection_km,
                        air_filter_interval_km, air_filter_interval_months,
                        fuel_filter_interval_km, fuel_filter_interval_months,
                        brake_fluid_type, brake_fluid_change_months,
                        spark_plug_type, spark_plug_gap_mm, spark_plug_interval_km, spark_plug_interval_months,
                        aux_belt_interval_km, aux_belt_interval_months,
                        count_variants, power_kw, oil_spec_source, timing_source, coolant_source, data_confidence
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (engine_code, None, fuel, disp_cc, None, None,
                     brand_norm, base_model_clean, year,
                     caps['oil_visc'], None, None, caps['oil_spec'],
                     caps['oil_with_filter_l'], caps['oil_without_filter_l'],
                     None, None,
                     None, caps['coolant_spec'], caps['coolant_capacity_l'],
                     None, None,
                     None, None, None, None,
                     None, None,
                     None, None,
                     None, None,
                     None, None, None, None,
                     None, None,
                     1, None, "lemon.dogeware.me LEMON 2015", None, "lemon.dogeware.me LEMON 2015", "TRUSTED_LEMON"))
                    stats['new_service_trusted'] += 1
                except Exception as e:
                    stats['service_insert_fail'] += 1
                    # print(e)
            else:
                # Update existing engine's service specs if trusted capacities are better or confidence is ESTIMATE
                cur.execute("SELECT data_confidence, oil_capacity_with_filter_l, coolant_capacity_l FROM engine_service_specs WHERE engine_code=?", (engine_code,))
                row = cur.fetchone()
                if row:
                    existing_conf, existing_oil, existing_coolant = row
                    # if existing confidence is ESTIMATE and we have lemon trusted, upgrade
                    # also if oil/coolant differ, update to trusted value
                    should_update = False
                    if existing_conf in ("ESTIMATE", "ESTIMATE (heuristic, not OEM) — vivid new engine, verify with handbook — LN Engineering: OEM approval mandatory"):
                        should_update = True
                    else:
                        # if existing is TRUSTED or OEM but values differ significantly, we keep existing? But lemon is trusted, we could still update if delta >0.1
                        if caps['oil_with_filter_l'] and existing_oil and abs(caps['oil_with_filter_l']-existing_oil)>0.05:
                            # decide to update to lemon if lemon is more precise
                            pass
                        # For now, only update if ESTIMATE
                    if should_update and (caps['oil_with_filter_l'] or caps['coolant_capacity_l']):
                        # Build update
                        updates = []
                        params = []
                        if caps['oil_with_filter_l']:
                            updates.append("oil_capacity_with_filter_l=?")
                            params.append(caps['oil_with_filter_l'])
                        if caps['oil_without_filter_l']:
                            updates.append("oil_capacity_without_filter_l=?")
                            params.append(caps['oil_without_filter_l'])
                        if caps['oil_visc']:
                            updates.append("oil_viscosity=?")
                            params.append(caps['oil_visc'])
                        if caps['oil_spec']:
                            updates.append("oil_oem_spec=?")
                            params.append(caps['oil_spec'])
                            updates.append("oil_spec_source=?")
                            params.append("lemon.dogeware.me LEMON 2015")
                        if caps['coolant_capacity_l']:
                            updates.append("coolant_capacity_l=?")
                            params.append(caps['coolant_capacity_l'])
                        if caps['coolant_spec']:
                            updates.append("coolant_spec=?")
                            params.append(caps['coolant_spec'])
                            updates.append("coolant_source=?")
                            params.append("lemon.dogeware.me LEMON 2015")
                        updates.append("data_confidence=?")
                        params.append("TRUSTED_LEMON")
                        params.append(engine_code)
                        sql = f"UPDATE engine_service_specs SET {', '.join(updates)} WHERE engine_code=?"
                        cur.execute(sql, params)
                        # also update engine_technical_specs? we could update similar
                        cur.execute("UPDATE engine_technical_specs SET data_confidence=? WHERE engine_code=?", ("TRUSTED_LEMON", engine_code))
                        updated_engines += 1
                        trusted_updates += 1
                        stats['updated_existing'] += 1
                else:
                    # engine exists but no service spec? insert
                    try:
                        cur.execute("""INSERT INTO engine_service_specs (
                            engine_code, engine_type, fuel, displacement_cc, power_hp, cylinders,
                            brand_example, model_example, year_example,
                            oil_viscosity, oil_standard, oil_acea, oil_oem_spec,
                            oil_capacity_with_filter_l, oil_capacity_without_filter_l,
                            oil_change_interval_km, oil_change_interval_months,
                            coolant_type, coolant_spec, coolant_capacity_l,
                            coolant_change_interval_km, coolant_change_interval_months,
                            timing_type, timing_belt_interval_km, timing_belt_interval_months,
                            timing_chain_inspection_km,
                            air_filter_interval_km, air_filter_interval_months,
                            fuel_filter_interval_km, fuel_filter_interval_months,
                            brake_fluid_type, brake_fluid_change_months,
                            spark_plug_type, spark_plug_gap_mm, spark_plug_interval_km, spark_plug_interval_months,
                            aux_belt_interval_km, aux_belt_interval_months,
                            count_variants, power_kw, oil_spec_source, timing_source, coolant_source, data_confidence
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (engine_code, None, fuel, disp_cc, None, None,
                         brand_norm, base_model_clean, year,
                         caps['oil_visc'], None, None, caps['oil_spec'],
                         caps['oil_with_filter_l'], caps['oil_without_filter_l'],
                         None, None,
                         None, caps['coolant_spec'], caps['coolant_capacity_l'],
                         None, None,
                         None, None, None, None,
                         None, None,
                         None, None,
                         None, None,
                         None, None, None, None,
                         None, None,
                         1, None, "lemon.dogeware.me LEMON 2015", None, "lemon.dogeware.me LEMON 2015", "TRUSTED_LEMON"))
                    except:
                        pass

            # Handle models
            model_key = (brand_norm.lower(), base_model_clean.lower())
            if model_key not in existing_models:
                # Need brand_id
                bid = brand_id_map.get(brand_norm.lower())
                if not bid:
                    # insert brand
                    cur.execute("INSERT OR IGNORE INTO brands (name) VALUES (?)", (brand_norm,))
                    cur.execute("SELECT id FROM brands WHERE name=?", (brand_norm,))
                    bid = cur.fetchone()[0]
                    brand_id_map[brand_norm.lower()] = bid
                # insert model
                try:
                    cur.execute("""INSERT INTO models (brand_id, brand_name, model_name, production_start, production_end, years_span, total_variants, source, status)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (bid, brand_norm, base_model_clean, year, year, str(year), 1, "lemon.dogeware.me LEMON 2015", "active"))
                    new_models += 1
                    existing_models.add(model_key)
                except:
                    pass
            else:
                # update production start/end if needed
                cur.execute("SELECT production_start, production_end FROM models WHERE brand_name=? AND model_name=?", (brand_norm, base_model_clean))
                row = cur.fetchone()
                if row:
                    ps, pe = row
                    new_ps = min(ps, year) if ps else year
                    new_pe = max(pe, year) if pe else year
                    if new_ps != ps or new_pe != pe:
                        cur.execute("UPDATE models SET production_start=?, production_end=? WHERE brand_name=? AND model_name=?", (new_ps, new_pe, brand_norm, base_model_clean))

            # Handle vehicle_variants
            # Deduplicate by car_brand, car_model, car_year, engine_code
            variant_key = (brand_norm.lower(), base_model_clean.lower(), year, engine_code)
            if variant_key not in existing_variants:
                # Also check without code dedup to avoid duplicate synthetic if same model/year already exists with different engine code synthetic?
                # For synthetic, we use engine_code includes model/year, so key is unique enough
                try:
                    cur.execute("""INSERT INTO vehicle_variants (car_brand, car_model, car_year, fuel, engine_power_hp, engine_type, engine_code, ecu_maker, ecu_model, production_start, production_end, engine_power_kw)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (brand_norm, base_model_clean, year, fuel, None, None, engine_code, None, None, year, year, None))
                    new_variants += 1
                    existing_variants.add(variant_key)
                except Exception as e:
                    stats['variant_insert_fail'] += 1
            else:
                stats['variant_duplicate'] += 1

            stats['processed'] += 1
            if stats['processed'] %500==0:
                print(f"processed {stats['processed']} new_eng {new_engines} upd {updated_engines} new_models {new_models} new_vars {new_variants}")

    con.commit()
    print(f"\n=== LEMON INTEGRATION DONE ===")
    print(f"processed {stats['processed']}")
    print(f"new_engines {new_engines} updated {updated_engines} trusted_updates {trusted_updates}")
    print(f"new_models {new_models} new_variants {new_variants}")
    print(f"stats {dict(stats)}")
    # Verify counts
    cur.execute("SELECT COUNT(*) FROM vehicle_variants")
    print("vehicle_variants", cur.fetchone())
    cur.execute("SELECT COUNT(*) FROM engines")
    print("engines", cur.fetchone())
    cur.execute("SELECT COUNT(*) FROM models")
    print("models", cur.fetchone())
    cur.execute("SELECT data_confidence, COUNT(*) FROM engine_service_specs GROUP BY data_confidence")
    print("service conf", cur.fetchall())
    cur.execute("SELECT data_confidence, COUNT(*) FROM engines GROUP BY data_confidence")
    print("engines conf", cur.fetchall())
    con.close()

if __name__=="__main__":
    main()
