#!/usr/bin/env python3
import re, json, time, urllib.request, urllib.parse, html, pathlib, concurrent.futures, sqlite3, os
from collections import defaultdict

BASE="https://lemon.dogeware.me"
HEADERS={"User-Agent":"Mozilla/5.0 (EnrichmentBot 1.0; +https://example.com/bot)"}
TIMEOUT=20

def fetch_html(url):
    try:
        req=urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        # print(f"fail {url} {e}")
        return ""

def extract_hrefs(html_text):
    return re.findall(r'<a\s+href="([^"]+)">([^<]+)</a>', html_text)

def get_brands():
    html_text=fetch_html(BASE+"/")
    hrefs=extract_hrefs(html_text)
    brands=[]
    for href, txt in hrefs:
        if href.startswith("/") or href.startswith("http"): 
            continue
        if txt.strip().lower() in ("about dogeware lemon mirror",): 
            continue
        # filter only dirs ending with /
        if href.endswith("/"):
            full=urllib.parse.urljoin(BASE+"/", href)
            brands.append((html.unescape(txt.strip()), full))
    # dedup
    seen=set()
    uniq=[]
    for t,u in brands:
        if u not in seen:
            seen.add(u)
            uniq.append((t,u))
    return uniq

def get_years(brand_url):
    html_text=fetch_html(brand_url)
    hrefs=extract_hrefs(html_text)
    years=[]
    for href, txt in hrefs:
        if txt.strip().isdigit() and len(txt.strip())==4:
            full=urllib.parse.urljoin(brand_url, href)
            years.append((int(txt.strip()), full))
    years.sort()
    return years

def get_models(year_url):
    html_text=fetch_html(year_url)
    hrefs=extract_hrefs(html_text)
    models=[]
    for href, txt in hrefs:
        # href like /Toyota/2015/Camry%20LE/
        if href.startswith("/") and href.count("/")>=4:
            # ensure href contains year as segment
            # decode href path to check year
            try:
                # extract brand/year prefix
                parts=href.strip("/").split("/")
                # parts[0]=Brand, parts[1]=Year, parts[2]=ModelDir
                if len(parts)>=3 and parts[1].isdigit():
                    full=urllib.parse.urljoin(BASE, href)
                    # use href decoded as model name? use text? Use href decoded for full variant name
                    # decoded href model segment is more complete
                    model_dir=urllib.parse.unquote(parts[2])
                    # text is suffix like "LE" or "Pop, Automatic Trans" but href has full "Camry LE"
                    # We'll store both
                    models.append((txt.strip(), model_dir, full))
            except: pass
    # dedup by full url
    seen=set()
    uniq=[]
    for txt, md, full in models:
        if full not in seen:
            seen.add(full)
            uniq.append((txt, md, full))
    return uniq

def parse_fluids_html(html_text):
    if "FLUID CAPACITIES" not in html_text:
        return []
    rows=re.findall(r'<tr>\s*(.*?)\s*</tr>', html_text, flags=re.DOTALL|re.IGNORECASE)
    fluids=[]
    for row in rows:
        cells=re.findall(r'<td[^>]*>(.*?)</td>', row, flags=re.DOTALL|re.IGNORECASE)
        if not cells:
            continue
        # strip inner tags
        cells=[re.sub(r'<[^>]+>','',c).strip() for c in cells]
        cells=[html.unescape(c).strip() for c in cells]
        if len(cells)>=6:
            ft=cells[0]
            app=cells[1]
            std=cells[3] if len(cells)>3 else ""
            met=cells[4] if len(cells)>4 else ""
            spec=cells[5] if len(cells)>5 else ""
            note=cells[6] if len(cells)>6 else ""
            if ft and ft!="Fluid Type" and ft!="FLUID CAPACITIES":
                fluids.append({"fluid_type":ft,"application":app,"extra":cells[2],"standard":std,"metric":met,"spec":spec,"note":note,"raw_cells":cells})
    return fluids

def parse_metric(metric_str):
    # metric like "4.25 L" or "7.28 L" or "0.45 KG" or "N/A"
    if not metric_str or metric_str=="N/A":
        return None
    m=re.search(r'([\d\.]+)', metric_str)
    if m:
        try:
            return float(m.group(1))
        except: return None
    return None

def parse_variant(model_dir):
    # model_dir decoded like "Camry XLE, 2.5L Eng VIN F" or "Beetle Base, 2D Hatchback, 1.8L Eng VIN 0, Automatic Trans"
    out={"raw":model_dir}
    # displacement
    m=re.search(r'(\d+\.\d+)L\s+Eng', model_dir)
    if m:
        out["displacement_l"]=float(m.group(1))
        out["displacement_cc"]=int(float(m.group(1))*1000)
    # VIN
    m=re.search(r'VIN\s+([A-Za-z0-9]+)', model_dir)
    if m:
        out["vin_code"]=m.group(1)
    # Eng CD
    m=re.search(r'Eng\s+CD\s+([A-Za-z0-9\-]+)', model_dir)
    if m:
        out["engine_code"]=m.group(1)
    # Transmission
    if "Automatic DCT" in model_dir: out["trans"]="Automatic DCT"
    elif "Automatic CVT" in model_dir: out["trans"]="Automatic CVT"
    elif "Automatic Trans" in model_dir: out["trans"]="Automatic"
    elif "Standard Trans" in model_dir: out["trans"]="Manual"
    # Model base extraction heuristic: first part before comma
    # e.g., "Camry XLE" -> split comma first segment
    first_segment=model_dir.split(",")[0].strip()
    # base model is first token(s) - we will later match known models, but here approximate as first word or first two if Land etc
    tokens=first_segment.split()
    if len(tokens)>=2 and tokens[0]=="Land" and tokens[1]=="Cruiser":
        out["base_model_guess"]="Land Cruiser"
    elif len(tokens)>=2 and tokens[0]=="Grand" and tokens[1]=="Cherokee":
        out["base_model_guess"]="Grand Cherokee"
    elif len(tokens)>=2 and first_segment.startswith("500"):
        # handle 500, 500L, 500X, 500 c
        if first_segment.startswith("500L"): out["base_model_guess"]="500L"
        elif first_segment.startswith("500X"): out["base_model_guess"]="500X"
        elif first_segment.startswith("500 c"): out["base_model_guess"]="500 c"
        else: out["base_model_guess"]="500"
    else:
        out["base_model_guess"]=tokens[0] if tokens else first_segment
    out["first_segment"]=first_segment
    return out

def fetch_fluids(model_url):
    fluids_url=model_url.rstrip("/")+"/Repair%20and%20Diagnosis/Quick%20Lookups/Fluids/"
    h=fetch_html(fluids_url)
    fluids=parse_fluids_html(h)
    return fluids, fluids_url

# ---------------- CRAWL WITH THREADPOOL ----------------
import threading
import queue

def crawl_year(brand_name, brand_url, year, year_url, max_models=None, delay=0.2):
    models=get_models(year_url)
    if max_models:
        models=models[:max_models]
    print(f"[{brand_name} {year}] {len(models)} models")
    results=[]
    # Use ThreadPool for fluids
    def job(item):
        txt, model_dir, model_url = item
        variant=parse_variant(model_dir)
        fluids, fluids_url = fetch_fluids(model_url)
        # also extract identical variants note? parse model_url page for identical list
        # fetch model page html to get identical variants
        model_html=fetch_html(model_url)
        identical=[]
        if "identical to the manual for the following model variants" in model_html:
            # capture <li> list after that phrase
            # crude: find <li> entries after that phrase until </ul>
            sect=model_html.split("identical to the manual for the following model variants")[1].split("</ul>")[0]
            lis=re.findall(r'<li>([^<]+)', sect)
            identical=[html.unescape(l.strip()) for l in lis if l.strip()]
        # enrich fluids with parsed metrics
        enriched_fluids=[]
        for fl in fluids:
            # parse engine code from application field
            app=fl["application"]
            # look for Eng CD
            m=re.search(r'Eng\s+CD\s+([A-Za-z0-9\-]+)', app)
            eng_cd=m.group(1) if m else None
            # displacement in application
            m2=re.search(r'(\d+\.\d+)L\s+Eng', app)
            disp_app=float(m2.group(1)) if m2 else None
            metric_val=parse_metric(fl["metric"])
            enriched_fluids.append({**fl, "engine_cd_from_app":eng_cd, "displacement_l_from_app":disp_app, "metric_value":metric_val})
        time.sleep(delay)
        return {
            "brand":brand_name,
            "year":year,
            "model_dir":model_dir,
            "model_text":txt,
            "model_url":model_url,
            "fluids_url":fluids_url,
            "variant_parsed":variant,
            "fluids":enriched_fluids,
            "identical_variants":identical
        }
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures={ex.submit(job, item): item for item in models}
        for fut in concurrent.futures.as_completed(futures):
            try:
                res=fut.result()
                results.append(res)
                if len(results)%20==0:
                    print(f"  {brand_name} {year} progress {len(results)}/{len(models)}")
            except Exception as e:
                print(f"  job fail {e}")
    return results

def crawl_all(years_range, brands_filter=None, max_models_per_year=None, output_path="/home/user/lemon_crawl.jsonl"):
    brands=get_brands()
    if brands_filter:
        brands=[(t,u) for t,u in brands if t in brands_filter]
    print(f"Crawling {len(brands)} brands, years {years_range}")
    all_results=[]
    # ensure output dir
    pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    # open file for incremental writing
    with open(output_path, "w", encoding="utf-8") as f:
        for brand_name, brand_url in brands:
            years=get_years(brand_url)
            years=[(y,u) for y,u in years if y in years_range]
            print(f"\n=== {brand_name} years {[y for y,_ in years]} ===")
            for y, yurl in years:
                try:
                    res=crawl_year(brand_name, brand_url, y, yurl, max_models=max_models_per_year)
                    for r in res:
                        f.write(json.dumps(r, ensure_ascii=False)+"\n")
                        all_results.append(r)
                    print(f"  -> {brand_name} {y}: {len(res)} variants, total {len(all_results)}")
                except Exception as e:
                    print(f" fail {brand_name} {y}: {e}")
                time.sleep(0.5)
    print(f"Done crawl {len(all_results)} total -> {output_path}")
    return all_results

if __name__=="__main__":
    import sys
    # Example: crawl 2015 and 2017 for all brands, no limit
    # For quick test, limit to 2015 only across all brands
    # We'll do years 2015-2017 inclusive for all brands
    years=set([2016,2017])
    # Uncomment to do full 2000-2017 after test
    # years=set(range(2000,2018))
    res=crawl_all(years_range=years, brands_filter=None, max_models_per_year=None, output_path="/home/user/lemon_crawl_2016_2017.jsonl")
