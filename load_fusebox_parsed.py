#!/usr/bin/env python3
"""Load parsed startmycar fusebox JSON files into car_database.db.
Idempotent: re-running replaces existing generation rows (same make/model/gen/trim)."""
import json, sqlite3, sys, glob, os

DB = os.path.join(os.path.dirname(__file__), 'database_enriched', 'car_database.db')

def load(paths):
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys=ON")
    cur = con.cursor()
    n_gen = n_box = n_fuse = 0
    for p in paths:
        d = json.load(open(p, encoding='utf-8'))
        key = (d['make_slug'], d['model_slug'], d.get('generation_name'), d.get('trim_label'))
        cur.execute("""SELECT id FROM fusebox_generations
                       WHERE smc_make_slug=? AND smc_model_slug=?
                         AND generation_name IS ? AND trim_label IS ?""", key)
        row = cur.fetchone()
        if row:
            gid = row[0]
            cur.execute("DELETE FROM fusebox_fuses WHERE box_id IN (SELECT id FROM fusebox_boxes WHERE generation_id=?)", (gid,))
            cur.execute("DELETE FROM fusebox_boxes WHERE generation_id=?", (gid,))
            cur.execute("""UPDATE fusebox_generations SET model_id=?, brand_name=?, model_name=?,
                           generation_code=?, year_start=?, year_end=?, representative_year=?,
                           source_url=?, scraped_at=datetime('now') WHERE id=?""",
                        (d.get('model_id'), d['brand_db'], d['model_db_name'], d.get('generation_code'),
                         d.get('year_start'), d.get('year_end'), d.get('representative_year'),
                         d['source_url'], gid))
        else:
            cur.execute("""INSERT INTO fusebox_generations
                           (model_id, brand_name, model_name, smc_make_slug, smc_model_slug,
                            generation_name, generation_code, year_start, year_end, trim_label,
                            representative_year, source_url)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (d.get('model_id'), d['brand_db'], d['model_db_name'], d['make_slug'], d['model_slug'],
                         d.get('generation_name'), d.get('generation_code'), d.get('year_start'),
                         d.get('year_end'), d.get('trim_label'), d.get('representative_year'), d['source_url']))
            gid = cur.lastrowid
        n_gen += 1
        for box in d['boxes']:
            cur.execute("INSERT INTO fusebox_boxes (generation_id, box_index, box_name, image_url) VALUES (?,?,?,?)",
                        (gid, box['index'], box['name'], box.get('image_url')))
            bid = cur.lastrowid
            n_box += 1
            for f in box['fuses']:
                no, ftype, amps, desc = (f + ["", "", "", ""])[:4]
                cur.execute("INSERT INTO fusebox_fuses (box_id, position_no, element_type, amperage, description) VALUES (?,?,?,?,?)",
                            (bid, no, ftype, amps or None, desc))
                n_fuse += 1
    con.commit()
    print(f"Loaded {n_gen} generations, {n_box} boxes, {n_fuse} fuses/relays")

if __name__ == '__main__':
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(os.path.dirname(__file__), 'fusebox_scrape', 'parsed', '*.json')))
    load(paths)
