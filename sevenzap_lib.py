"""Shared helpers for the 7zap.com model-picture pipeline.

The pipeline has three stages (see step90/step91/step92 scripts):

    step90_fetch_7zap_catalog.py   crawl 7zap.com  -> database_enriched/7zap/catalog_models.jsonl
    step91_match_7zap_images.py    match catalog   -> models.image_url / image_* columns
    step92_download_7zap_images.py download files  -> database_enriched/model_images/...

This module holds everything the three stages share: HTML/markdown parsing of
7zap catalog pages, brand-name normalisation and the model-name normalisation
used by the fuzzy matcher.
"""

from __future__ import annotations

import html as html_mod
import json
import os
import re
import unicodedata
from dataclasses import dataclass, asdict, field

BASE = "https://7zap.com"
CATALOG_URL = BASE + "/en/catalog/cars/{slug}/"
IMG_HOST = "img.7zap.com"

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(REPO_ROOT, "database_enriched", "7zap")
CATALOG_JSONL = os.path.join(DATA_DIR, "catalog_models.jsonl")
BRANDS_JSON = os.path.join(DATA_DIR, "brands.json")
IMAGE_DIR = os.path.join(REPO_ROOT, "database_enriched", "model_images")
DB_PATH = os.path.join(REPO_ROOT, "database_enriched", "car_database.db")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


# --------------------------------------------------------------------------
# data model
# --------------------------------------------------------------------------
@dataclass
class CatalogModel:
    """One model card scraped from a 7zap brand catalog page."""

    brand_slug: str          # "bmw"
    brand_label: str         # "BMW"
    model_name: str          # "1' E82"
    year_from: int | None    # 2007
    year_to: int | None      # 2011
    years_text: str          # "(2007 - 2011)"
    page_url: str            # https://7zap.com/en/catalog/cars/bmw/1-series-e82-parts-catalog/
    image_url: str           # https://img.7zap.com/images/oem/models/BMW_1-series_E82.webp
    slug: str = ""           # 1-series-e82-parts-catalog
    source: str = "7zap"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


# --------------------------------------------------------------------------
# year parsing
# --------------------------------------------------------------------------
YEAR_RANGE_RE = re.compile(r"(19\d{2}|20\d{2})\s*(?:-|–|—|to)?\s*(19\d{2}|20\d{2})?")


def parse_years(text: str) -> tuple[int | None, int | None]:
    """'(2007 - 2011)' -> (2007, 2011);  '2017' -> (2017, 2017)."""
    if not text:
        return None, None
    m = YEAR_RANGE_RE.search(text)
    if not m:
        return None, None
    y1 = int(m.group(1))
    y2 = int(m.group(2)) if m.group(2) else y1
    return y1, y2


def parse_span(span: str) -> tuple[int | None, int | None]:
    """Parse the `models.years_span` column ('2007-2011', '2016', '')."""
    return parse_years(span or "")


# --------------------------------------------------------------------------
# HTML parsing (used by the live crawler)
# --------------------------------------------------------------------------
MODEL_HREF_RE = re.compile(r"/(?:en|de|fr|es|ru)/catalog/(?:cars|moto)/([^/\"#?]+)/([^/\"#?]+)/")
IMG_SRC_RE = re.compile(
    r'(?:src|data-src|data-lazy|data-original|srcset)="(https?://' + IMG_HOST.replace(".", r"\.") + r'/[^"\s]+)',
    re.I,
)
TAG_RE = re.compile(r"<[^>]+>")
ANCHOR_RE = re.compile(r"<a\b[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.S | re.I)


def _clean_text(fragment: str) -> str:
    txt = TAG_RE.sub("\n", fragment)
    txt = html_mod.unescape(txt)
    lines = [l.strip() for l in txt.splitlines()]
    return "\n".join(l for l in lines if l)


def parse_catalog_html(html: str, brand_slug: str, brand_label: str = "") -> list[CatalogModel]:
    """Extract the model cards from a 7zap brand catalog page (raw HTML)."""
    out: dict[str, CatalogModel] = {}
    for href, inner in ANCHOR_RE.finditer(html):
        m = MODEL_HREF_RE.search(href)
        if not m or m.group(1) != brand_slug:
            continue
        slug = m.group(2)
        if slug in {"", "#"} or not slug.endswith("parts-catalog"):
            # brand-level/series-level links carry no unique model
            continue
        img = IMG_SRC_RE.search(inner)
        if not img:
            continue
        text = _clean_text(inner)
        # the card text is: <title>\n<name>\n<years>; the title line repeats the
        # name and ends with the marketing suffix, so drop it.
        lines = [l for l in text.split("\n") if "OEM Parts" not in l and "Genuine Parts" not in l]
        name = lines[0] if lines else slug.replace("-parts-catalog", "").replace("-", " ").upper()
        years_text = ""
        for l in lines[1:]:
            if re.search(r"(19|20)\d{2}", l):
                years_text = l
                break
        y1, y2 = parse_years(years_text)
        page = href if href.startswith("http") else BASE + href
        cm = CatalogModel(
            brand_slug=brand_slug,
            brand_label=brand_label or brand_slug.replace("-", " ").title(),
            model_name=name,
            year_from=y1,
            year_to=y2,
            years_text=years_text,
            page_url=page.split("#")[0],
            image_url=img.group(1),
            slug=slug,
        )
        out.setdefault(slug, cm)
    return list(out.values())


# --------------------------------------------------------------------------
# Markdown parsing (used to ingest pages captured through a reader/proxy)
# --------------------------------------------------------------------------
MD_CARD_RE = re.compile(
    r"\[(?P<title>[^\]]*?)\\*\s*!\[[^\]]*\]\((?P<img>https://img\.7zap\.com/[^)]+)\)"
    r"(?P<tail>.*?)\]\((?P<url>https://7zap\.com/[^)\s]+)",
    re.S,
)


def parse_catalog_markdown(md: str, brand_slug: str, brand_label: str = "") -> list[CatalogModel]:
    """Extract model cards from the markdown rendering of a catalog page."""
    out: dict[str, CatalogModel] = {}
    for m in MD_CARD_RE.finditer(md):
        url = m.group("url")
        hm = MODEL_HREF_RE.search(url)
        if not hm or hm.group(1) != brand_slug:
            continue
        slug = hm.group(2)
        if not slug.endswith("parts-catalog"):
            continue
        tail = m.group("tail").replace("\\", "")
        lines = [l.strip() for l in tail.split("\n") if l.strip()]
        name = lines[0] if lines else slug.replace("-parts-catalog", "")
        years_text = next((l for l in lines[1:] if re.search(r"(19|20)\d{2}", l)), "")
        y1, y2 = parse_years(years_text)
        out.setdefault(
            slug,
            CatalogModel(
                brand_slug=brand_slug,
                brand_label=brand_label or brand_slug.replace("-", " ").title(),
                model_name=name,
                year_from=y1,
                year_to=y2,
                years_text=years_text,
                page_url=url.split("#")[0],
                image_url=m.group("img"),
                slug=slug,
            ),
        )
    return list(out.values())


def model_slug(name: str) -> str:
    """7zap catalog slug for a model name: "3' G20 Saloon LCI" -> 3-series-g20-saloon-lci-parts-catalog."""
    s = strip_accents(name or "").lower()
    s = s.replace("'", "-series ").replace("’", "-series ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return f"{s}-parts-catalog" if s else ""


def parse_catalog_tsv(tsv: str, brand_slug: str, brand_label: str = "") -> list[CatalogModel]:
    """Ingest a condensed capture: name<TAB>years<TAB>image-filename[<TAB>slug].

    Used to seed the catalog from pages read through a text proxy when a direct
    HTTP crawl is not available. The catalog slug is derived from the name when
    the optional 4th column is missing.
    """
    out: list[CatalogModel] = []
    for raw in tsv.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) < 3:
            continue
        name, years, img = parts[0], parts[1], parts[2]
        slug = parts[3] if len(parts) > 3 and parts[3] else model_slug(name)
        y1, y2 = parse_years(years)
        out.append(
            CatalogModel(
                brand_slug=brand_slug,
                brand_label=brand_label or brand_slug.replace("-", " ").title(),
                model_name=name,
                year_from=y1,
                year_to=y2,
                years_text=years,
                page_url=f"{BASE}/en/catalog/cars/{brand_slug}/{slug}/",
                image_url=f"https://{IMG_HOST}/images/oem/models/{img}",
                slug=slug,
            )
        )
    return out


# --------------------------------------------------------------------------
# catalog persistence
# --------------------------------------------------------------------------
def load_catalog(path: str = CATALOG_JSONL) -> list[CatalogModel]:
    rows: list[CatalogModel] = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(CatalogModel(**json.loads(line)))
    return rows


def save_catalog(rows: list[CatalogModel], path: str = CATALOG_JSONL, merge: bool = True) -> int:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = {(r.brand_slug, r.slug): r for r in (load_catalog(path) if merge else [])}
    for r in rows:
        existing[(r.brand_slug, r.slug)] = r
    ordered = sorted(existing.values(), key=lambda r: (r.brand_slug, r.model_name))
    with open(path, "w", encoding="utf-8") as fh:
        for r in ordered:
            fh.write(r.to_json() + "\n")
    return len(ordered)


# --------------------------------------------------------------------------
# brand mapping: database brand_name -> 7zap brand slug
# --------------------------------------------------------------------------
# display labels for slugs whose Title-casing is wrong ("Bmw", "Gmc", ...)
BRAND_LABELS = {
    "bmw": "BMW", "gmc": "GMC", "mg": "MG", "ds": "DS", "byd": "BYD", "gaz": "GAZ",
    "uaz": "UAZ", "zaz": "ZAZ", "vaz": "VAZ", "mercedes": "Mercedes-Benz",
    "mini": "MINI", "alfa-romeo": "Alfa Romeo", "land-rover": "Land Rover",
    "rolls-royce": "Rolls-Royce", "aston-martin": "Aston Martin", "ram": "RAM",
    "seat": "SEAT", "ssangyong": "SsangYong", "great-wall": "Great Wall",
}


def brand_label_for(slug: str) -> str:
    return BRAND_LABELS.get(slug, slug.replace("-", " ").title())


BRAND_ALIASES = {
    "mercedes": "mercedes",
    "mercedes-benz": "mercedes",
    "vw": "volkswagen",
    "land rover": "land-rover",
    "alfa romeo": "alfa-romeo",
    "rolls-royce": "rolls-royce",
    "rolls royce": "rolls-royce",
    "aston martin": "aston-martin",
    "great wall": "great-wall",
    "mini": "mini",
    "ram": "ram",
    "gmc": "gmc",
    "mg": "mg",
    "ds": "ds",
    "byd": "byd",
    "gaz": "gaz",
    "uaz": "uaz",
    "zaz": "zaz",
    "lada": "vaz",
    "vaz": "vaz",
    "ssangyong": "ssangyong",
    "renault samsung": "renault-samsung",
    "lynk & co": "lynk-co",
    "mitsubishi fuso": "fuso",
    "renault trucks": "renault-trucks",
    "citroen": "citroen",
    "skoda": "skoda",
    "seat": "seat",
    "cupra": "cupra",
    "genesis": "genesis",
    "hyundai": "hyundai",
    "kia": "kia",
}


def brand_to_slug(brand_name: str, known_slugs: set[str] | None = None) -> str | None:
    key = (brand_name or "").strip().lower()
    if not key:
        return None
    slug = BRAND_ALIASES.get(key)
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", key).strip("-")
    if known_slugs is not None and slug not in known_slugs:
        return slug if slug in known_slugs else None
    return slug


# --------------------------------------------------------------------------
# model-name normalisation + chassis codes (matcher)
# --------------------------------------------------------------------------
NOISE_WORDS = {
    "SERIES", "CLASS", "SALOON", "SEDAN", "BERLINE", "HATCHBACK", "COUPE", "CABRIO",
    "CABRIOLET", "CONVERTIBLE", "ESTATE", "TOURING", "TOURER", "WAGON", "VAN", "BOX",
    "PLATFORM", "CHASSIS", "PICKUP", "SPORTBACK", "AVANT", "LIMOUSINE", "ALLROAD",
    "FACELIFT", "LCI", "MK", "GEN", "TYPE", "TYP", "THE", "NEW", "MODEL", "CAR",
}

PAREN_RE = re.compile(r"\(([^)]*)\)")
# chassis / platform codes: E82, F20, W204, 8P, 1J2, 2H_, 312, 937, G20...
CODE_RE = re.compile(r"\b([A-Z]{1,3}\d{1,3}[A-Z]?|\d{1,2}[A-Z]{1,2}\d?)\b")


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def normalize_name(name: str) -> str:
    """Upper-cased, punctuation-free form used for comparison."""
    s = strip_accents(name or "").upper()
    s = s.replace("'", " ").replace("’", " ")
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def core_tokens(name: str) -> list[str]:
    toks = [t for t in normalize_name(name).split() if t and t not in NOISE_WORDS]
    return toks


def chassis_codes(name: str) -> set[str]:
    """Codes found in a model name, e.g. 'C-CLASS (W204)' -> {'W204'}."""
    s = strip_accents(name or "").upper()
    codes: set[str] = set()
    for chunk in PAREN_RE.findall(s):
        for part in re.split(r"[,/;]+", chunk):
            part = part.strip().strip("_")
            if not part:
                continue
            for c in CODE_RE.findall(part):
                codes.add(c)
    # codes outside parentheses, e.g. 'A3 TYP 8P', '1 SERIES - F20/F21'
    outside = PAREN_RE.sub(" ", s)
    for part in re.split(r"[\s,/;–—-]+", outside):
        part = part.strip("_ ")
        if len(part) >= 2 and re.fullmatch(r"[A-Z]\d{2,3}[A-Z]?|\d[A-Z]\d?|[A-Z]{2}\d{2,3}", part):
            codes.add(part)
    return {c for c in codes if len(c) >= 2}


def family_key(brand: str, model: str) -> str | None:
    """Collapse an engine/trim row to its model family.

    BMW '116I' -> '1 SERIES', Mercedes 'C240' -> 'C CLASS', Audi 'A4 2.0 TDI' -> 'A4'.
    Returns None when no brand rule applies.
    """
    b = (brand or "").strip().lower()
    n = normalize_name(model)
    if not n:
        return None
    toks = n.split()
    first = toks[0] if toks else ""
    if b in {"bmw", "alpina"}:
        # catalog style: "1' E82" -> "1 E82";  database style: "116I", "1 SERIES"
        if re.fullmatch(r"[1-8]", first):
            return f"{first} SERIES"
        m = re.fullmatch(r"([1-8])\d{2}[A-Z]*", first)
        if m:
            return f"{m.group(1)} SERIES"
        m = re.fullmatch(r"M(\d)\d{0,2}[A-Z]*", first)   # M140i, M235i, M3, M5...
        if m and m.group(1) in "12345678":
            return f"{m.group(1)} SERIES"
        m = re.fullmatch(r"([XZI])(\d)[A-Z]*", first)
        if m:
            return f"{m.group(1)}{m.group(2)}"
        m = re.fullmatch(r"I(X\d)", first)      # iX1/iX2/iX3 share the X1/X2/X3 body
        if m:
            return m.group(1)
        if first in {"IX", "XM", "I3", "I4", "I7", "I8"}:
            return first
    if b in {"mercedes", "mercedes-benz", "maybach"}:
        m = re.match(r"^([A-Z]{1,3})\s+CLASS\b", n)
        if m:
            return f"{m.group(1)} CLASS"
        m = re.fullmatch(r"([A-Z]{1,3})\s?\d{2,3}[A-Z]*", first if len(toks) == 1 else n)
        if m and m.group(1) not in {"AMG", "GT", "SL", "SLK", "SLC"}:
            return f"{m.group(1)} CLASS"
        if first in {"SL", "SLK", "SLC", "SLS", "CLK", "CLS", "CLA", "GLA", "GLB", "GLC",
                     "GLE", "GLS", "GLK", "EQA", "EQB", "EQC", "EQE", "EQS", "VITO", "SPRINTER"}:
            return first
    if b == "audi":
        m = re.match(r"^((?:RS\s?Q?|SQ|S|Q)?\d|TT|R8|E TRON)\b", n)
        if m:
            return m.group(1).replace(" ", "")
    if b in {"volkswagen", "seat", "skoda", "ford", "opel", "vauxhall", "renault", "peugeot",
             "citroen", "toyota", "nissan", "honda", "mazda", "kia", "hyundai"}:
        toks = core_tokens(n)
        if toks:
            return toks[0]
    toks = core_tokens(n)
    return toks[0] if toks else None


# families that have no catalog entry of their own and borrow the picture of a
# closely related family (electric derivatives, badge-engineered twins, ...)
ALT_FAMILIES = {
    "bmw": {"I5": "5 SERIES", "I7": "7 SERIES", "I3": "1 SERIES", "I4": "4 SERIES",
            "IX": "X5", "XM": "X7", "Z8": "Z4"},
    "mercedes": {"EQA": "A CLASS", "EQB": "B CLASS", "EQC": "GLC", "EQE": "E CLASS",
                 "EQS": "S CLASS", "EQV": "V CLASS"},
    "audi": {"ETRON": "Q8"},
}


# badge/trim words: a candidate carrying one that the query does not should not
# win on name similarity alone (a 316d must not inherit the M3 photo)
VARIANT_TOKENS = {
    "M", "M1", "M2", "M3", "M4", "M5", "M6", "M8", "AMG", "RS", "GTI", "GT", "GTS",
    "HYBRID", "CS", "CSL", "COMPETITION", "SRT", "NISMO", "ST", "RALLIART", "ABARTH",
    "QUATTRO", "COUPE", "CONVERTIBLE", "CABRIO", "TOURING", "GRAN",
}


def variant_mismatch(query: str, candidate: str) -> int:
    """How many badge/trim words the candidate adds that the query never asked for."""
    q = set(normalize_name(query).split())
    c = set(normalize_name(candidate).split())
    return len((c - q) & VARIANT_TOKENS)


def alt_family(brand: str, fam: str | None) -> str | None:
    if not fam:
        return None
    return ALT_FAMILIES.get((brand or "").strip().lower(), {}).get(fam)
