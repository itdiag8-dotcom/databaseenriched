#!/usr/bin/env python3
"""Download fuse box diagram images into car_database.db (fusebox_boxes.image_blob).

The Arena sandbox cannot reach images.startmycar.com, so run this script on your
own machine:  python3 download_fusebox_images.py
Re-runnable: skips boxes that already have a blob."""
import sqlite3, urllib.request, time, os, sys

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database_enriched', 'car_database.db')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    rows = cur.execute("""SELECT id, image_url FROM fusebox_boxes
                          WHERE image_url IS NOT NULL AND image_blob IS NULL""").fetchall()
    print(f"{len(rows)} images to download")
    ok = err = 0
    for bid, url in rows:
        try:
            req = urllib.request.Request(url, headers=UA)
            data = urllib.request.urlopen(req, timeout=30).read()
            cur.execute("UPDATE fusebox_boxes SET image_blob=? WHERE id=?", (sqlite3.Binary(data), bid))
            con.commit()
            ok += 1
            print(f"ok  {bid}  {len(data):>8} bytes  {url}")
        except Exception as e:
            err += 1
            print(f"ERR {bid}  {url}  -> {e}", file=sys.stderr)
        time.sleep(0.5)  # be polite
    print(f"done: {ok} downloaded, {err} failed")

if __name__ == '__main__':
    main()
