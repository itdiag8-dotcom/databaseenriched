#!/usr/bin/env python3
import re
import json
import time
import html
import urllib.request
import urllib.parse
import sqlite3
import pathlib
from collections import defaultdict

BASE = "https://lemon.dogeware.me"
HEADERS = {"User-Agent": "Mozilla/5.0 enrichment bot 1.0"}

def fetch_html(url):
    try:
        # ensure proper quoting? url already encoded, but urllib wants ascii
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"FAIL {url}: {e}")
        return ""

def extract_hrefs(html_text):
    # find <a href="...">text</a> where href starts with / or https://lemon
    pattern = re.compile(r'<a\s+href="([^"]+)">([^<]+)</a>')
    return pattern.findall(html_text)

def get_brands():
    html_text = fetch_html(BASE + "/")
    hrefs = extract_hrefs(html_text)
    brands = []
    for href, text in hrefs:
        # href like "Acura/" or "Alfa%20Romeo/" - relative
        if href.startswith("/") or href.startswith("http"):
            continue
        # decode text is brand name
        brands.append((html.unescape(text.strip()), urllib.parse.urljoin(BASE+"/", href)))
    # filter: only those that are directories and not about.html
    brands = [(t,u) for t,u in brands if not t.startswith("About")]
    print(f"Brands: {len(brands)} {brands[:5]}")
    return brands

def get_years(brand_url):
    html_text = fetch_html(brand_url)
    hrefs = extract_hrefs(html_text)
    years = []
    for href, text in hrefs:
        txt = text.strip()
        if txt.isdigit() and len(txt)==4:
            full = urllib.parse.urljoin(brand_url, href)
            years.append((int(txt), full))
    return years

def get_models(year_url):
    html_text = fetch_html(year_url)
    # The year page lists models with href like "/Toyota/2015/Camry%20LE/"
    # Need to find all <li><a href="/Brand/Year/Model/">...
    # Use regex for <a href="..."> to allow absolute path
    # We already have extract_hrefs which captures, but need absolute
    hrefs = extract_hrefs(html_text)
    models = []
    for href, text in hrefs:
        # href should contain year_url path segment and be deeper
        # For year page, hrefs are like "/Toyota/2015/Camry%20LE/"
        if year_url.split("/")[-2] in href or href.count("/") >=3:
            # ensure it's a model page: href ends with / and contains brand/year
            if href.startswith("/") and href.count("/") >= 4:
                full = urllib.parse.urljoin(BASE, href)
                # decode text as model trim
                models.append((html.unescape(text.strip()), full))
    # Remove duplicates by url
    seen=set()
    uniq=[]
    for t,u in models:
        if u not in seen:
            seen.add(u)
            uniq.append((t,u))
    return uniq

def parse_variant_string(s):
    """Parse model trim string e.g. 'Base, 2D Hatchback, 1.8L Eng VIN 0, Automatic Trans'"""
    out = {"raw": s}
    # displacement
    m = re.search(r'(\d+\.\d+)L\s+Eng', s)
    if m:
        out["displacement_l"] = float(m.group(1))
        out["displacement_cc"] = int(float(m.group(1))*1000)
    # VIN
    m = re.search(r'VIN\s+([A-Za-z0-9]+)', s)
    if m:
        out["vin_code"] = m.group(1)
    # Eng CD
    m = re.search(r'Eng\s+CD\s+([A-Za-z0-9\-]+)', s)
    if m:
        out["engine_code"] = m.group(1).strip()
    # Also handle "Eng CD CNTA" already
    # Transmission
    if "Automatic DCT" in s:
        out["trans"] = "Automatic DCT"
    elif "Automatic CVT" in s:
        out["trans"] = "Automatic CVT"
    elif "Automatic Trans" in s or "Automatic" in s:
        out["trans"] = "Automatic"
    elif "Standard Trans" in s or "Manual" in s:
        out["trans"] = "Manual"
    # Body / trim extraction: first part before comma is base model? Hard
    # We'll split by comma
    parts = [p.strip() for p in s.split(",")]
    out["parts"] = parts
    return out

def fetch_fluids(model_url):
    fluids_url = model_url.rstrip("/") + "/Repair%20and%20Diagnosis/Quick%20Lookups/Fluids/"
    html_text = fetch_html(fluids_url)
    if "FLUID CAPACITIES" not in html_text:
        return {}, fluids_url, html_text[:500]
    # Parse table rows: <td>...</td> sequences
    # Find tbody
    rows = re.findall(r'<tr>\s*(.*?)\s*</tr>', html_text, flags=re.DOTALL)
    fluids = []
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, flags=re.DOTALL)
        # strip tags inside?
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        # Need at least 6 columns
        if len(cells) >= 6:
            # First cell is Fluid Type, second Application, etc.
            # Header row has no td, only th, so we only process td rows
            # Check if first cell is Fluid Type header? but td rows are data
            fluid_type = cells[0]
            application = cells[1] if len(cells)>1 else ""
            standard = cells[3] if len(cells)>3 else ""
            metric = cells[4] if len(cells)>4 else ""
            spec = cells[5] if len(cells)>5 else ""
            if fluid_type and fluid_type != "Fluid Type":
                fluids.append({
                    "fluid_type": fluid_type,
                    "application": application,
                    "standard": standard,
                    "metric": metric,
                    "spec": spec,
                    "raw_cells": cells
                })
    return fluids, fluids_url, ""

def test_pilot():
    brands = get_brands()
    # pick Toyota, Fiat, VW
    target = {"Toyota": None, "Fiat": None, "Volkswagen": None}
    for t,u in brands:
        if t in target:
            target[t]=u
    for brand, brand_url in target.items():
        print(f"\n=== {brand} => {brand_url} ===")
        years = get_years(brand_url)
        years = [y for y in years if 2015 <= y[0] <= 2015]  # just 2015
        for y, yurl in years:
            models = get_models(yurl)
            print(f" Year {y}: {len(models)} models")
            for mt, murl in models[:3]:
                print(f"  {mt} -> {murl}")
                parsed = parse_variant_string(mt)
                print(f"    parsed {parsed}")
                fluids, furl, _ = fetch_fluids(murl)
                print(f"    fluids {len(fluids)} from {furl}")
                for fl in fluids[:3]:
                    print(f"      {fl['fluid_type']} | {fl['application']} | metric={fl['metric']} spec={fl['spec'][:60]}")
                time.sleep(0.3)
        time.sleep(0.5)

if __name__ == "__main__":
    test_pilot()
