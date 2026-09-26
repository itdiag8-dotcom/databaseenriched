#!/usr/bin/env python3
"""
Crawler for https://lemon.dogeware.me/ to extract car data and enrich database.
Extracts: Brand, Year, Model/Trim, Engine, Fluid capacities, Common specs
Trusted source: lemon.dogeware.me (retrieved late 2025)
"""
import re
import json
import time
import pathlib
import urllib.request
import urllib.parse
from collections import defaultdict

BASE = "https://lemon.dogeware.me"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EnrichmentBot/1.0)"}

def fetch(url):
    """Fetch markdown content via urllib, return text"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read().decode('utf-8', errors='ignore')
            return data
    except Exception as e:
        print(f"FETCH FAIL {url}: {e}")
        return ""

def extract_links(markdown):
    """Extract markdown links [text](url)"""
    pattern = r'\[([^\]]+)\]\((https://lemon\.dogeware\.me[^\)]+)\)'
    return re.findall(pattern, markdown)

def parse_brand_home():
    md = fetch(BASE + "/")
    links = extract_links(md)
    brands = []
    for text, url in links:
        # url like https://lemon.dogeware.me/Toyota/
        # text is brand name
        brands.append((text.strip(), url))
    print(f"Found {len(brands)} brands")
    return brands

def parse_brand_years(brand_url):
    md = fetch(brand_url)
    links = extract_links(md)
    years = []
    for text, url in links:
        if text.strip().isdigit() and len(text.strip())==4:
            years.append((int(text.strip()), url))
    return years

def parse_year_models(year_url):
    md = fetch(year_url)
    links = extract_links(md)
    models = []
    for text, url in links:
        # text is model trim like "Camry LE" or "500 Pop, Automatic Trans"
        # url is .../Toyota/2015/Camry%20LE/
        models.append((text.strip(), url))
    return models

def parse_fluids(model_url):
    """Fetch Fluids page and parse fluid capacities table"""
    fluids_url = model_url.rstrip("/") + "/Repair%20and%20Diagnosis/Quick%20Lookups/Fluids/"
    # Need to encode properly: already encoded in url, but we need to ensure
    # Try fetching with encoded URL
    md = fetch(fluids_url)
    if "FLUID CAPACITIES" not in md and "Fluid Type" not in md:
        # Try alternative: try without encoding? Already handled
        # Try via fetch_page style: the site may need exact encoding
        # We'll try to fetch with urllib and handle 404
        pass
    # Parse table: look for lines starting with | Fluid Type
    fluids = {}
    # Extract table rows: pattern | Fluid Type | Application | ... | Standard | Metric | Fluid Spec |
    # We'll parse markdown table
    lines = md.split("\n")
    in_table = False
    for line in lines:
        if line.strip().startswith("| Fluid Type"):
            in_table = True
            continue
        if in_table and line.strip().startswith("| ---"):
            continue
        if in_table and line.strip().startswith("|"):
            # Split by |
            parts = [p.strip() for p in line.split("|")]
            # parts[0] empty, parts[1] Fluid Type, parts[2] Application, parts[3] blank, parts[4] Standard, parts[5] Metric, parts[6] Fluid Spec, parts[7] Note
            if len(parts) >= 7:
                fluid_type = parts[1]
                application = parts[2]
                standard = parts[4]
                metric = parts[5]
                spec = parts[6]
                if fluid_type and fluid_type != "Fluid Type":
                    key = f"{fluid_type}__{application}".strip("_")
                    fluids[key] = {"fluid_type": fluid_type, "application": application, "standard": standard, "metric": metric, "spec": spec}
        elif in_table and not line.strip().startswith("|"):
            # End of table
            if fluids:
                break
    return fluids, fluids_url

def parse_common_specs(model_url):
    """Fetch Common Specs page for compression, oil pressure etc."""
    # Try to find Common Specs link from Repair and Diagnosis page
    repair_url = model_url.rstrip("/") + "/Repair%20and%20Diagnosis/"
    md = fetch(repair_url)
    # Find Common Specs link
    links = extract_links(md)
    common_url = None
    for text, url in links:
        if "Common Specs" in text:
            common_url = url
            break
    if not common_url:
        return {}, None
    md2 = fetch(common_url)
    # Check if it's index or direct specs
    if "Expand All" in md2 or "Specifications Index" in md2:
        # Need to go deeper: find Common Specs & Procedures link
        links2 = extract_links(md2)
        for text2, url2 in links2:
            if "Common Specs" in text2 and "Procedures" in text2:
                common_url = url2
                md2 = fetch(common_url)
                break
    # Now md2 should contain specs table
    specs = {}
    # Look for patterns like Compression, Oil Pressure etc.
    # We'll search for lines containing specific keywords
    keywords = ["Compression", "Oil Pressure", "Fuel Pressure", "Radiator Cap", "Torque", "Axle Nut"]
    lines = md2.split("\n")
    for line in lines:
        for kw in keywords:
            if kw.lower() in line.lower():
                specs.setdefault(kw, []).append(line.strip())
    return specs, common_url

def pilot_crawl(brands_subset=None, years_subset=None, max_models_per_year=3):
    """Pilot crawl for subset"""
    brands = parse_brand_home()
    if brands_subset:
        brands = [(t,u) for t,u in brands if t in brands_subset]
    results = []
    for brand_text, brand_url in brands:
        print(f"\n=== Brand: {brand_text} ===")
        years = parse_brand_years(brand_url)
        # Filter years >=2000 and subset
        years = [(y,u) for y,u in years if y >= 2000]
        if years_subset:
            years = [(y,u) for y,u in years if y in years_subset]
        print(f" Years: {[y for y,_ in years][:5]} total {len(years)}")
        for year, year_url in years[:2]:  # limit to 2 years per brand for pilot
            print(f"  Year {year}: {year_url}")
            models = parse_year_models(year_url)
            print(f"   Models: {len(models)} found, sampling {max_models_per_year}")
            for model_text, model_url in models[:max_models_per_year]:
                print(f"    Model: {model_text} -> {model_url}")
                fluids, fluids_url = parse_fluids(model_url)
                specs, specs_url = parse_common_specs(model_url)
                print(f"     Fluids: {len(fluids)} entries from {fluids_url}")
                for k,v in list(fluids.items())[:3]:
                    print(f"       {k}: metric={v['metric']} spec={v['spec']}")
                print(f"     Specs: {len(specs)} keys from {specs_url}")
                for k,v in specs.items():
                    print(f"       {k}: {v[:1]}")
                results.append({
                    "brand": brand_text,
                    "year": year,
                    "model_trim": model_text,
                    "model_url": model_url,
                    "fluids": fluids,
                    "fluids_url": fluids_url,
                    "specs": specs,
                    "specs_url": specs_url
                })
                time.sleep(0.5)  # be polite
            time.sleep(0.5)
        time.sleep(1)
    return results

if __name__ == "__main__":
    # Pilot with 3 brands, 2 years each, 2 models each
    pilot = pilot_crawl(brands_subset=["Toyota","Fiat","Volkswagen"], years_subset=[2015,2020], max_models_per_year=2)
    out = pathlib.Path("/home/user/lemon_pilot.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(pilot, f, indent=2, ensure_ascii=False)
    print(f"\nPilot saved to {out} with {len(pilot)} entries")
    # Also save summary
    summary = defaultdict(int)
    for r in pilot:
        summary[r["brand"]] += 1
    print("Summary by brand:", dict(summary))
